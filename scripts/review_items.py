"""Per-item spaced-review schedule (`progress/review_items.json`).

Each practised problem (`drillId/qid`) is tracked with its `commonTrapTag` and `archetypeKey`
across 5 review levels with intervals of 1, 3, 7, 16, and 35 days:
- correct without hint (unassisted) -> level + 1 (max 5), due in INTERVALS[new_level] days
- correct with hints / assisted     -> same level, due in INTERVALS[level] days
- wrong / skipped                   -> level halved (floor, min 1), due next day (+1 day)

Backfilled from existing `progress/<DRILL_ID>.json` (`attempts[]`, `reviews[]`, `hintsRevealed`,
`score`, `lastCheck`, `skipped`, `revisitNote`) by reusing `scripts.weak_spots.load_items`.
Read-only unless `--rebuild` is passed.

    python -m scripts.review_items [--due [--limit N]] [--scope KIND:VALUE] [--rebuild] [--json]
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import tempfile
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any

from progress_store import find_repo_root, progress_root, review_items_path
from scripts import weak_spots

REVIEW_INTERVALS: dict[int, int] = {
    1: 1,
    2: 3,
    3: 7,
    4: 16,
    5: 35,
}
MIN_LEVEL = 1
MAX_LEVEL = 5
DEFAULT_ITEM_DURATION_MS = 90_000  # 1.5 minutes fallback per item

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_SAFE_TRAP_RE = re.compile(r"^[A-Za-z0-9@._/-]{1,128}$")
_NON_SUBSTANTIVE_VERDICTS = ("invalid input", "parse_error")
_LEGACY_UNDATED = "1970-01-01"


def _round_half_up(value: float) -> int:
    """Round non-negative numbers half-up to match JavaScript Math.round."""
    return int(math.floor(value + 0.5))


def parse_scope(raw: str | None) -> tuple[str, str] | None:
    """Parse and validate a review scope filter (`subject:MTH|PRG`, `unit:<code>`, `chapter:<code>`, `trap:<tag>`, `drill:<id>`)."""
    if raw is None or not raw.strip():
        return None
    text = raw.strip()
    if ":" not in text:
        raise ValueError(f"Invalid scope {raw!r}: expected '<kind>:<value>'")
    kind, value = text.split(":", 1)
    kind = kind.strip().lower()
    value = value.strip()
    if not value:
        raise ValueError(f"Invalid scope {raw!r}: missing value")
    if kind == "subject":
        upper = value.upper()
        if upper not in ("MTH", "PRG"):
            raise ValueError(f"Invalid subject scope {raw!r}: expected MTH or PRG")
        return ("subject", upper)
    if kind in ("unit", "chapter", "drill"):
        if not _SAFE_ID_RE.match(value):
            raise ValueError(f"Invalid {kind} scope value: {value!r}")
        return (kind, value)
    if kind == "trap":
        if not _SAFE_TRAP_RE.match(value) or ".." in value:
            raise ValueError(f"Invalid trap scope value: {value!r}")
        return ("trap", value)
    raise ValueError(f"Unknown scope kind {kind!r}")


def matches_scope(item: dict[str, Any], parsed_scope: tuple[str, str] | None) -> bool:
    """Return True when `item` matches `parsed_scope` (or when `parsed_scope` is None)."""
    if parsed_scope is None:
        return True
    kind, value = parsed_scope
    if kind == "subject":
        return str(item.get("subject") or "").upper() == value
    if kind == "unit":
        return str(item.get("unitCode") or "") == value
    if kind == "chapter":
        unit = str(item.get("unitCode") or "")
        return unit == value or unit.startswith(f"{value}-U")
    if kind == "trap":
        return item.get("commonTrapTag") == value
    if kind == "drill":
        return str(item.get("drillId") or "") == value
    return False


def item_key(drill_id: str, qid: str) -> str:
    """Canonical key `<drillId>/<qid>` for a review item."""
    return f"{drill_id}/{qid}"


def _normalize_date(raw: str | None, fallback: str | None = None) -> str:
    def local_date(value: str | None) -> str:
        text = (value or "").strip()
        if _DATE_RE.match(text):
            return text
        if not text:
            return ""
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed.astimezone().date().isoformat()
        except ValueError:
            return ""

    cand = local_date(raw)
    if cand:
        return cand
    fb = local_date(fallback)
    if fb:
        return fb
    return date.today().isoformat()


def _cycle_started_after_evidence(state: dict[str, Any], evidence_date: str) -> bool:
    cycle = state.get("cycleStartedAt")
    if not isinstance(cycle, str) or not cycle:
        return False

    def instant(value: Any) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.astimezone()
        except ValueError:
            return None

    cycle_at = instant(cycle)
    evidence_at = []
    for field, time_field in (("attempts", "ts"), ("reviews", "at")):
        records = state.get(field) or []
        if not isinstance(records, list):
            continue
        evidence_at.extend(
            parsed
            for record in records
            if isinstance(record, dict)
            if field != "attempts" or record.get("kind") != "variant"
            if (parsed := instant(record.get(time_field)))
        )
    if cycle_at and evidence_at:
        return cycle_at > max(evidence_at)
    return _normalize_date(cycle) > evidence_date


def add_days(date_str: str, days: int) -> str:
    """Return `YYYY-MM-DD` shifted by `days` calendar days."""
    base = date.fromisoformat(_normalize_date(date_str))
    return (base + timedelta(days=int(days))).isoformat()


def clamp_level(level: int | float | None) -> int:
    if level is None:
        return MIN_LEVEL
    return max(MIN_LEVEL, min(MAX_LEVEL, int(level)))


def step_schedule(
    current_level: int,
    *,
    correct: bool,
    assisted: bool = False,
    review_date: str,
) -> dict[str, Any]:
    """Apply one review outcome to `current_level` on `review_date` (`YYYY-MM-DD`)."""
    lvl = clamp_level(current_level)
    rev_date = _normalize_date(review_date)
    if correct and not assisted:
        next_level = min(MAX_LEVEL, lvl + 1)
        due_date = add_days(rev_date, REVIEW_INTERVALS[next_level])
    elif correct and assisted:
        next_level = lvl
        due_date = add_days(rev_date, REVIEW_INTERVALS[next_level])
    else:
        next_level = max(MIN_LEVEL, lvl // 2)
        due_date = add_days(rev_date, 1)
    return {
        "level": next_level,
        "lastReviewed": rev_date,
        "dueDate": due_date,
    }


def extract_review_events(state: dict[str, Any], fallback_ts: str = "") -> list[dict[str, Any]]:
    """Extract chronological review events from a problem's progress `state`."""
    if not isinstance(state, dict):
        return []
    # Old records without event timestamps are due immediately and never drift with updatedAt.
    fallback_date = _LEGACY_UNDATED
    raw_example_at = state.get("exampleViewedAt")
    example_viewed_at = raw_example_at.strip() if isinstance(raw_example_at, str) and raw_example_at.strip() else ""
    state_assisted = bool(
        state.get("setupRevealedBeforeAnswer")
        or state.get("solutionRevealedBeforeAnswer")
        or (state.get("hintsRevealed") or 0) > 0
    )
    state_assisted_with_example = state_assisted or bool(example_viewed_at)

    attempts = state.get("attempts") or []
    substantive = [
        a
        for a in attempts
        if isinstance(a, dict) and a.get("kind") != "variant" and a.get("verdict") not in _NON_SUBSTANTIVE_VERDICTS
    ]
    events: list[dict[str, Any]] = []
    if substantive:
        single_half_score = (
            len(substantive) == 1 and substantive[0].get("verdict") == "correct" and state.get("score") == 0.5
        )
        for att in substantive:
            att_ts = str(att.get("ts") or "").strip()
            ev_date = _normalize_date(att_ts) if att_ts else _LEGACY_UNDATED
            verdict = str(att.get("verdict") or "")
            correct = verdict == "correct"
            has_explicit_hint = any(k in att for k in ("hintsUsed", "assisted", "hintsRevealed"))
            after_example = bool(
                att.get("exampleViewed") or (example_viewed_at and (not att_ts or att_ts >= example_viewed_at))
            )
            att_revealed = bool(att.get("setupRevealed") or att.get("solutionRevealed") or after_example)
            if has_explicit_hint:
                assisted = bool(
                    att.get("hintsUsed") or att.get("assisted") or (att.get("hintsRevealed") or 0) > 0 or att_revealed
                )
            else:
                assisted = state_assisted or att_revealed or single_half_score
            events.append({"date": ev_date, "correct": correct, "assisted": assisted})
        return events

    reviews = state.get("reviews") or []
    valid_reviews = [r for r in reviews if isinstance(r, dict) and r.get("verdict")]
    if valid_reviews:
        for rev in valid_reviews:
            rev_at = str(rev.get("at") or "")
            ev_date = _normalize_date(rev_at) if rev_at else _LEGACY_UNDATED
            verdict = str(rev.get("verdict") or "")
            correct = verdict == "pass"
            has_explicit_hint = any(k in rev for k in ("hintsUsed", "assisted", "hintsRevealed"))
            if has_explicit_hint:
                assisted = bool(rev.get("hintsUsed") or rev.get("assisted") or (rev.get("hintsRevealed") or 0) > 0)
            else:
                assisted = state_assisted_with_example
            events.append({"date": ev_date, "correct": correct, "assisted": assisted})
        return events

    if state.get("skipped"):
        return [{"date": fallback_date, "correct": False, "assisted": state_assisted_with_example}]

    last_check = state.get("lastCheck")
    if isinstance(last_check, dict) and last_check.get("verdict") not in (
        None,
        "",
        *_NON_SUBSTANTIVE_VERDICTS,
    ):
        verdict = str(last_check.get("verdict") or "")
        correct = verdict == "correct"
        assisted = state_assisted_with_example or (correct and state.get("score") == 0.5)
        return [{"date": fallback_date, "correct": correct, "assisted": assisted}]

    if state.get("score") is not None:
        try:
            sc = float(state["score"])
        except (TypeError, ValueError):
            return []
        correct = sc > 0
        assisted = state_assisted_with_example or (0 < sc < 1.0)
        return [{"date": fallback_date, "correct": correct, "assisted": assisted}]

    return []


def replay_events(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Replay chronological review events starting from Level 1 (ignoring kind == 'variant' events)."""
    if not events:
        return None
    item_events = [ev for ev in events if isinstance(ev, dict) and ev.get("kind") != "variant"]
    if not item_events:
        return None
    level = MIN_LEVEL
    last_reviewed = ""
    due_date = ""
    last_wrong_date: str | None = None

    for ev in item_events:
        ev_date = _normalize_date(str(ev.get("date") or ""))
        correct = bool(ev.get("correct"))
        assisted = bool(ev.get("assisted"))
        if not correct:
            step = step_schedule(level, correct=False, assisted=assisted, review_date=ev_date)
            level = step["level"]
            last_reviewed = step["lastReviewed"]
            due_date = step["dueDate"]
            last_wrong_date = ev_date
        elif last_wrong_date == ev_date:
            # In-session retry on the same day after a wrong attempt keeps the halved level and next-day due date.
            last_reviewed = ev_date
        else:
            step = step_schedule(level, correct=True, assisted=assisted, review_date=ev_date)
            level = step["level"]
            last_reviewed = step["lastReviewed"]
            due_date = step["dueDate"]

    return {
        "level": level,
        "lastReviewed": last_reviewed,
        "dueDate": due_date,
        "lastWrong": not bool(item_events[-1].get("correct")),
    }


def _clean_revisit_note(raw: Any) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def redact_review_item(entry: dict[str, Any]) -> dict[str, Any]:
    """Return a strictly redacted review item (metadata + schedule + revisitNote only; never answers/steps)."""
    subj = "PRG" if str(entry.get("subject") or "").upper() == "PRG" else "MTH"
    return {
        "drillId": str(entry.get("drillId") or ""),
        "qid": str(entry.get("qid") or ""),
        "unitCode": str(entry.get("unitCode") or entry.get("unit") or ""),
        "subject": subj,
        "commonTrapTag": entry.get("commonTrapTag")
        if isinstance(entry.get("commonTrapTag"), str) and entry.get("commonTrapTag")
        else None,
        "archetypeKey": entry.get("archetypeKey")
        if isinstance(entry.get("archetypeKey"), str) and entry.get("archetypeKey")
        else None,
        "level": clamp_level(entry.get("level")),
        "lastReviewed": _normalize_date(entry.get("lastReviewed")),
        "dueDate": _normalize_date(entry.get("dueDate")),
        "revisitNote": _clean_revisit_note(entry.get("revisitNote")),
        "lastWrong": bool(entry.get("lastWrong", False)),
    }


def _build_schedule_from_loaded(loaded: list[weak_spots.Item]) -> dict[str, dict[str, Any]]:
    schedule: dict[str, dict[str, Any]] = {}
    for item in loaded:
        if not item.drill or not item.pid:
            continue
        events = extract_review_events(item.state, fallback_ts=item.ts)
        if not events:
            # Fallback to item summary if load_items produced an Item without raw state events
            events = [
                {
                    "date": _normalize_date(item.ts),
                    "correct": item.score > 0 and not item.skipped,
                    "assisted": bool(item.assisted or (0 < item.score < 1.0)),
                }
            ]
        replayed = replay_events(events)
        if not replayed:
            continue
        if _cycle_started_after_evidence(item.state, replayed["lastReviewed"]):
            continue
        trap_tag = item.trap or (item.matched[-1] if item.matched else None)
        key = item_key(item.drill, item.pid)
        schedule[key] = redact_review_item(
            {
                "drillId": item.drill,
                "qid": item.pid,
                "unitCode": item.unit,
                "subject": "PRG" if item.subject == "PRG" else "MTH",
                "commonTrapTag": trap_tag,
                "archetypeKey": item.archetype,
                "level": replayed["level"],
                "lastReviewed": replayed["lastReviewed"],
                "dueDate": replayed["dueDate"],
                "revisitNote": item.revisit_note,
                "lastWrong": replayed["lastWrong"],
            }
        )
    return dict(sorted(schedule.items()))


def build_schedule_from_progress(
    data_root: str | None = None,
    progress_dir: str | None = None,
    labs_root: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Build the full review schedule map (`{ "<drillId>/<qid>": ReviewItem }`) from progress via `weak_spots.load_items`."""
    loaded = weak_spots.load_items(data_root=data_root, progress_dir=progress_dir, labs_root=labs_root)
    return _build_schedule_from_loaded(loaded)


def get_open_weak_traps(loaded: list[weak_spots.Item]) -> set[str]:
    """Return the set of open weak-spot trap/check tags from `weak_spots.trap_status`."""
    status = weak_spots.trap_status(loaded)
    return {tag for tag, info in status.items() if info.get("open")}


def estimate_median_duration_ms(
    loaded: list[weak_spots.Item],
    *,
    subject: str | None = None,
) -> int:
    """Compute median positive `durationMs` across past attempts (fallback 1.5 min = 90_000 ms)."""
    all_durations: list[float] = []
    by_subject: dict[str, list[float]] = {"MTH": [], "PRG": []}

    for item in loaded:
        state = item.state if isinstance(item.state, dict) else {}
        subj = "PRG" if item.subject == "PRG" else "MTH"
        attempts = state.get("attempts") or []
        per_attempt: list[float] = []
        for att in attempts:
            if not isinstance(att, dict):
                continue
            if att.get("kind") == "variant":
                continue
            if att.get("verdict") in _NON_SUBSTANTIVE_VERDICTS:
                continue
            dur = att.get("durationMs")
            if isinstance(dur, (int, float)) and not isinstance(dur, bool) and math.isfinite(dur) and dur > 0:
                per_attempt.append(float(dur))
        if per_attempt:
            all_durations.extend(per_attempt)
            by_subject[subj].extend(per_attempt)
        else:
            state_dur = state.get("durationMs")
            if (
                isinstance(state_dur, (int, float))
                and not isinstance(state_dur, bool)
                and math.isfinite(state_dur)
                and state_dur > 0
            ):
                all_durations.append(float(state_dur))
                by_subject[subj].append(float(state_dur))

    pool = by_subject[subject] if subject in ("MTH", "PRG") and by_subject[subject] else all_durations
    if not pool:
        return DEFAULT_ITEM_DURATION_MS
    pool.sort()
    mid = len(pool) // 2
    if len(pool) % 2 == 1:
        return _round_half_up(pool[mid])
    return _round_half_up((pool[mid - 1] + pool[mid]) / 2.0)


def estimate_review_minutes(item_count: int, median_duration_ms: int = DEFAULT_ITEM_DURATION_MS) -> int:
    """Estimate total review minutes for `item_count` items using `median_duration_ms` (min 1 when count > 0)."""
    if item_count <= 0:
        return 0
    ms = median_duration_ms if median_duration_ms > 0 else DEFAULT_ITEM_DURATION_MS
    return max(1, _round_half_up((item_count * ms) / 60_000.0))


def _store_path(progress_dir: str | None = None, repo_root: str | None = None) -> str:
    if progress_dir:
        return os.path.join(progress_dir, "review_items.json")
    return review_items_path(repo_root)


def load_saved_review_items(
    progress_dir: str | None = None,
    repo_root: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Read `review_items.json` from disk, or `{}` if absent/invalid (read-only)."""
    path = _store_path(progress_dir, repo_root)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    source = raw.get("items") if isinstance(raw.get("items"), dict) else raw
    out: dict[str, dict[str, Any]] = {}
    for k, val in source.items():
        if not isinstance(k, str) or not isinstance(val, dict):
            continue
        if not val.get("drillId") or not val.get("qid"):
            continue
        redacted = redact_review_item(val)
        out[item_key(redacted["drillId"], redacted["qid"])] = redacted
    return out


def write_review_items(
    schedule: dict[str, dict[str, Any]],
    progress_dir: str | None = None,
    repo_root: str | None = None,
) -> str:
    """Atomically write `schedule` to `progress/review_items.json` (or `pilot/progress/review_items.json`)."""
    path = _store_path(progress_dir, repo_root)
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    cleaned = {
        item_key(v["drillId"], v["qid"]): redact_review_item(v)
        for v in schedule.values()
        if isinstance(v, dict) and v.get("drillId") and v.get("qid")
    }
    fd, tmp_path = tempfile.mkstemp(prefix=".review_items_", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return path


def rebuild_review_items(
    data_root: str | None = None,
    progress_dir: str | None = None,
    labs_root: str | None = None,
    repo_root: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Rebuild the review schedule from progress files and persist to `review_items.json`."""
    resolved_progress = progress_dir or progress_root(repo_root)
    backfilled = build_schedule_from_progress(
        data_root=data_root,
        progress_dir=resolved_progress,
        labs_root=labs_root,
    )
    saved = load_saved_review_items(progress_dir=resolved_progress, repo_root=repo_root)
    schedule = _merge_saved_schedule(backfilled, _prune_saved_items(saved, data_root, resolved_progress, labs_root))
    write_review_items(schedule, progress_dir=resolved_progress, repo_root=repo_root)
    return schedule


def _merge_saved_schedule(
    backfilled: dict[str, dict[str, Any]],
    saved: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not saved:
        return backfilled
    merged: dict[str, dict[str, Any]] = dict(backfilled)
    for key, saved_entry in saved.items():
        entry = dict(saved_entry)
        bf_entry = backfilled.get(key)
        if bf_entry and str(bf_entry.get("lastReviewed") or "") > str(entry.get("lastReviewed") or ""):
            # A newer attempt in a normal drill session wins over an older saved review result.
            merged[key] = bf_entry
            continue
        if bf_entry:
            if bf_entry.get("revisitNote") is not None:
                entry["revisitNote"] = bf_entry["revisitNote"]
            if not entry.get("unitCode") and bf_entry.get("unitCode"):
                entry["unitCode"] = bf_entry["unitCode"]
            if not entry.get("commonTrapTag") and bf_entry.get("commonTrapTag"):
                entry["commonTrapTag"] = bf_entry["commonTrapTag"]
            if not entry.get("archetypeKey") and bf_entry.get("archetypeKey"):
                entry["archetypeKey"] = bf_entry["archetypeKey"]
        merged[key] = redact_review_item(entry)
    return dict(sorted(merged.items()))


def _prune_saved_items(
    saved: dict[str, dict[str, Any]],
    data_root: str | None,
    progress_dir: str | None,
    labs_root: str | None,
) -> dict[str, dict[str, Any]]:
    """Ignore cached results for retired problems or problems reset after their last evidence."""
    repo_root = find_repo_root()
    drill_root = data_root or os.environ.get("DRILLS_DATA_DIR") or os.path.join(repo_root, "drills", "data")
    lab_root = labs_root or os.path.join(repo_root, "labs")
    progress_root_dir = progress_dir or progress_root(repo_root)
    problem_ids: dict[str, set[str]] = {}
    for pattern in (os.path.join(drill_root, "**", "*.json"), os.path.join(lab_root, "LAB-*", "lab.config.json")):
        for file_path in glob.glob(pattern, recursive=True):
            try:
                with open(file_path, encoding="utf-8") as file:
                    doc = json.load(file)
                drill_id = str(doc.get("drillId") or doc.get("labId") or "")
                problems = doc.get("problems") or doc.get("milestones") or []
                ids = {str(problem.get("id") or "") for problem in problems if isinstance(problem, dict)}
                if drill_id:
                    problem_ids[drill_id] = ids
            except (OSError, ValueError):
                continue

    active: dict[str, dict[str, Any]] = {}
    for key, item in saved.items():
        drill_id, _, qid = key.partition("/")
        if qid not in problem_ids.get(drill_id, set()):
            continue
        progress_path = os.path.join(progress_root_dir, f"{drill_id}.json")
        try:
            with open(progress_path, encoding="utf-8") as file:
                progress_doc = json.load(file)
            state = (progress_doc.get("problems") or {}).get(qid) or {}
            if _cycle_started_after_evidence(state, item.get("lastReviewed", "")):
                continue
        except (OSError, ValueError, AttributeError):
            pass
        active[key] = item
    return active


def _lookup_problem_unit(drill_id: str, qid: str, data_root: str | None = None, labs_root: str | None = None) -> str:
    """Resolve unit metadata for a newly reviewed item, including never-practised problems."""
    repo_root = find_repo_root()
    drill_root = data_root or os.environ.get("DRILLS_DATA_DIR") or os.path.join(repo_root, "drills", "data")
    lab_root = labs_root or os.path.join(repo_root, "labs")
    candidates = glob.glob(os.path.join(drill_root, "**", "*.json"), recursive=True)
    candidates += glob.glob(os.path.join(lab_root, "LAB-*", "lab.config.json"))
    for file_path in candidates:
        try:
            with open(file_path, encoding="utf-8") as file:
                doc = json.load(file)
            if str(doc.get("drillId") or doc.get("labId") or "") != drill_id:
                continue
            problems = doc.get("problems") or doc.get("milestones") or []
            for problem in problems:
                if isinstance(problem, dict) and problem.get("id") == qid:
                    units = problem.get("units") or []
                    return str(
                        problem.get("unitCode")
                        or (units[0] if units else "")
                        or doc.get("unitCode")
                        or doc.get("chapterCode")
                        or ""
                    )
        except (OSError, ValueError):
            continue
    return ""


def get_review_items_schedule(
    data_root: str | None = None,
    progress_dir: str | None = None,
    labs_root: str | None = None,
    repo_root: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Return the active review schedule without writing to disk (read-only).

    Reads `review_items.json` when present and merges any backfilled items and updated `revisitNote`
    values from `progress/<DRILL_ID>.json` in memory.
    """
    resolved_progress = progress_dir or progress_root(repo_root)
    backfilled = build_schedule_from_progress(
        data_root=data_root,
        progress_dir=resolved_progress,
        labs_root=labs_root,
    )
    saved = _prune_saved_items(
        load_saved_review_items(progress_dir=resolved_progress, repo_root=repo_root),
        data_root,
        resolved_progress,
        labs_root,
    )
    return _merge_saved_schedule(backfilled, saved)


def _priority_sort_key(
    item: dict[str, Any],
    open_weak_traps: set[str] | frozenset[str] | None = None,
) -> tuple[int, int, str, int, str, str, str]:
    traps = open_weak_traps or frozenset()
    tag = item.get("commonTrapTag")
    return (
        0 if item.get("lastWrong") else 1,
        0 if (isinstance(tag, str) and tag in traps) else 1,
        str(item.get("dueDate") or ""),
        int(item.get("level") or 1),
        str(item.get("unitCode") or ""),
        str(item.get("drillId") or ""),
        str(item.get("qid") or ""),
    )


def prioritize_due_items(
    items: list[dict[str, Any]],
    *,
    open_weak_traps: set[str] | frozenset[str] | None = None,
) -> list[dict[str, Any]]:
    """Sort due items by priority: (a) wrong on last attempt, (b) open weak spot trap, (c) most overdue."""
    cleaned = [redact_review_item(it) for it in items]
    cleaned.sort(key=lambda it: _priority_sort_key(it, open_weak_traps))
    return cleaned


def interleave_due_items(
    items: list[dict[str, Any]],
    limit: int | None = None,
    *,
    open_weak_traps: set[str] | frozenset[str] | None = None,
) -> list[dict[str, Any]]:
    """Pick the highest-priority `limit` items first, then interleave across units and subjects."""
    remaining = prioritize_due_items(items, open_weak_traps=open_weak_traps)
    if limit is not None and limit >= 0:
        remaining = remaining[:limit]

    result: list[dict[str, Any]] = []
    last_unit: str | None = None
    last_subject: str | None = None

    while remaining:
        unit_counts = Counter(it["unitCode"] for it in remaining)
        total = len(remaining)

        diff_unit = [it for it in remaining if it["unitCode"] != last_unit]
        pool = diff_unit if diff_unit else remaining

        max_count = max(unit_counts[it["unitCode"]] for it in pool)
        if max_count > total // 2:
            pool = [it for it in pool if unit_counts[it["unitCode"]] == max_count]

        if last_subject is not None:
            diff_subj = [it for it in pool if it["subject"] != last_subject]
            if diff_subj:
                pool = diff_subj

        chosen = min(
            pool,
            key=lambda it: (
                -unit_counts[it["unitCode"]],
                *_priority_sort_key(it, open_weak_traps),
            ),
        )
        remaining.remove(chosen)
        result.append(chosen)
        last_unit = chosen["unitCode"]
        last_subject = chosen["subject"]

    return result


def get_due_items(
    *,
    today: str | None = None,
    limit: int | None = None,
    scope: str | None = None,
    data_root: str | None = None,
    progress_dir: str | None = None,
    labs_root: str | None = None,
    repo_root: str | None = None,
) -> list[dict[str, Any]]:
    """Return due review items (`dueDate <= today`), prioritized, scoped, and interleaved (read-only)."""
    parsed_scope = parse_scope(scope)
    today_str = _normalize_date(today)
    resolved_progress = progress_dir or progress_root(repo_root)
    loaded = weak_spots.load_items(data_root=data_root, progress_dir=resolved_progress, labs_root=labs_root)
    open_weak_traps = get_open_weak_traps(loaded)
    backfilled = _build_schedule_from_loaded(loaded)
    saved = _prune_saved_items(
        load_saved_review_items(progress_dir=resolved_progress, repo_root=repo_root),
        data_root,
        resolved_progress,
        labs_root,
    )
    schedule = _merge_saved_schedule(backfilled, saved)
    due = [it for it in schedule.values() if it["dueDate"] <= today_str and matches_scope(it, parsed_scope)]
    return interleave_due_items(due, limit=limit, open_weak_traps=open_weak_traps)


def record_review_result(
    drill_id: str,
    qid: str,
    *,
    correct: bool,
    hints_used: bool | int = False,
    review_date: str | None = None,
    data_root: str | None = None,
    progress_dir: str | None = None,
    labs_root: str | None = None,
    repo_root: str | None = None,
) -> dict[str, Any]:
    """Record one review outcome `{drillId, qid, correct, hintsUsed}` and persist to `review_items.json`."""
    resolved_progress = progress_dir or progress_root(repo_root)
    schedule = get_review_items_schedule(
        data_root=data_root,
        progress_dir=resolved_progress,
        labs_root=labs_root,
        repo_root=repo_root,
    )
    key = item_key(drill_id, qid)
    existing = schedule.get(key)
    current_level = existing["level"] if existing else MIN_LEVEL
    assisted = (
        (hints_used > 0) if isinstance(hints_used, int) and not isinstance(hints_used, bool) else bool(hints_used)
    )
    rev_date = _normalize_date(review_date)
    step = step_schedule(current_level, correct=bool(correct), assisted=assisted, review_date=rev_date)

    base = (
        dict(existing)
        if existing
        else {
            "drillId": drill_id,
            "qid": qid,
            "unitCode": _lookup_problem_unit(drill_id, qid, data_root, labs_root),
            "subject": "PRG" if drill_id.startswith(("DRL-PRG-", "LAB-")) else "MTH",
            "commonTrapTag": None,
            "archetypeKey": None,
            "revisitNote": None,
        }
    )
    base["level"] = step["level"]
    base["lastReviewed"] = step["lastReviewed"]
    base["dueDate"] = step["dueDate"]
    base["lastWrong"] = not bool(correct)
    updated = redact_review_item(base)
    schedule[key] = updated
    write_review_items(schedule, progress_dir=resolved_progress, repo_root=repo_root)
    return updated


def _format_text_report(items: list[dict[str, Any]], *, due_only: bool, today: str) -> str:
    if not items:
        return f"No review items due on {today}." if due_only else "No review items yet."
    header = (
        f"Due review items ({len(items)} due on or before {today}):"
        if due_only
        else f"Review items ({len(items)} total):"
    )
    lines = [header]
    for it in items:
        tag = it.get("commonTrapTag") or it.get("archetypeKey") or "-"
        note = f"  note: {it['revisitNote']}" if it.get("revisitNote") else ""
        lines.append(
            f"  {it['drillId']}/{it['qid']}  [{it['subject']}]  {it['unitCode']}  "
            f"L{it['level']}  due {it['dueDate']}  ({tag}){note}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m scripts.review_items",
        description="Inspect or rebuild the per-item review schedule (read-only unless --rebuild).",
    )
    ap.add_argument("--due", action="store_true", help="List only items due on or before today, interleaved")
    ap.add_argument("--limit", type=int, default=None, help="Maximum number of due items to return")
    ap.add_argument(
        "--scope",
        default=None,
        help="Optional scope filter: subject:MTH|PRG, unit:<code>, chapter:<code>, trap:<tag>, drill:<id>",
    )
    ap.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild progress/review_items.json from existing progress/<DRILL_ID>.json files",
    )
    ap.add_argument("--json", action="store_true", dest="as_json", help="Output JSON instead of plain text")
    ap.add_argument("--today", default=None, help="Override today's date (YYYY-MM-DD)")
    ap.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR") or None)
    ap.add_argument("--progress-dir", default=None)
    args = ap.parse_args(argv)

    try:
        parsed_scope = parse_scope(args.scope)
    except ValueError as exc:
        ap.error(str(exc))

    repo_root = find_repo_root()
    resolved_progress = args.progress_dir or progress_root(repo_root)
    today_str = _normalize_date(args.today)

    loaded = weak_spots.load_items(data_root=args.data_root, progress_dir=resolved_progress)
    open_weak_traps = get_open_weak_traps(loaded)
    backfilled = _build_schedule_from_loaded(loaded)

    if args.rebuild:
        saved = _prune_saved_items(
            load_saved_review_items(progress_dir=resolved_progress, repo_root=repo_root),
            args.data_root,
            resolved_progress,
            None,
        )
        schedule = _merge_saved_schedule(backfilled, saved)
        write_review_items(schedule, progress_dir=resolved_progress, repo_root=repo_root)
    else:
        saved = _prune_saved_items(
            load_saved_review_items(progress_dir=resolved_progress, repo_root=repo_root),
            args.data_root,
            resolved_progress,
            None,
        )
        schedule = _merge_saved_schedule(backfilled, saved)

    all_due = [it for it in schedule.values() if it["dueDate"] <= today_str]
    by_subject = {
        "MTH": sum(1 for it in all_due if it["subject"] == "MTH"),
        "PRG": sum(1 for it in all_due if it["subject"] == "PRG"),
    }
    scoped_due = [it for it in all_due if matches_scope(it, parsed_scope)]
    due_items = interleave_due_items(
        scoped_due,
        limit=args.limit,
        open_weak_traps=open_weak_traps,
    )
    scope_subject = parsed_scope[1] if parsed_scope and parsed_scope[0] == "subject" else None
    median_ms = estimate_median_duration_ms(loaded, subject=scope_subject)
    estimated_minutes = estimate_review_minutes(len(scoped_due), median_ms)

    if args.due:
        if args.as_json:
            payload: dict[str, Any] = {
                "today": today_str,
                "count": len(due_items),
                "totalDue": len(scoped_due),
                "bySubject": by_subject,
                "medianDurationMs": median_ms,
                "estimatedMinutes": estimated_minutes,
                "items": due_items,
            }
            if parsed_scope is not None:
                payload["scope"] = f"{parsed_scope[0]}:{parsed_scope[1]}"
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(_format_text_report(due_items, due_only=True, today=today_str))
        return 0

    all_items = [it for it in schedule.values() if matches_scope(it, parsed_scope)]
    if args.limit is not None and args.limit >= 0:
        all_items = all_items[: args.limit]
    if args.as_json:
        payload = {
            "ok": True,
            "today": today_str,
            "path": _store_path(resolved_progress, repo_root),
            "count": len(all_items) if parsed_scope is not None else len(schedule),
            "dueCount": len(due_items),
            "totalDue": len(scoped_due),
            "bySubject": by_subject,
            "medianDurationMs": median_ms,
            "estimatedMinutes": estimated_minutes,
            "items": all_items,
        }
        if parsed_scope is not None:
            payload["scope"] = f"{parsed_scope[0]}:{parsed_scope[1]}"
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(_format_text_report(all_items, due_only=False, today=today_str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
