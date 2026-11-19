"""Per-item spaced-review schedule (`progress/review_items.json`).

Each practised problem (`drillId/qid`) is tracked with its `commonTrapTag` and `archetypeKey`
across 5 review levels with intervals of 1, 3, 7, 16, and 35 days:
- correct without hint (unassisted) -> level + 1 (max 5), due in INTERVALS[new_level] days
- correct with hints / assisted     -> same level, due in INTERVALS[level] days
- wrong / skipped                   -> level halved (floor, min 1), due next day (+1 day)

Backfilled from existing `progress/<DRILL_ID>.json` (`attempts[]`, `reviews[]`, `hintsRevealed`,
`score`, `lastCheck`, `skipped`, `revisitNote`) by reusing `scripts.weak_spots.load_items`.
Read-only unless `--rebuild` is passed.

    python -m scripts.review_items [--due [--limit N]] [--rebuild] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections import Counter
from datetime import date, timedelta
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

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NON_SUBSTANTIVE_VERDICTS = ("invalid input", "parse_error")


def item_key(drill_id: str, qid: str) -> str:
    """Canonical key `<drillId>/<qid>` for a review item."""
    return f"{drill_id}/{qid}"


def _normalize_date(raw: str | None, fallback: str | None = None) -> str:
    cand = (raw or "").strip()[:10]
    if _DATE_RE.match(cand):
        return cand
    fb = (fallback or "").strip()[:10]
    if _DATE_RE.match(fb):
        return fb
    return date.today().isoformat()


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
    fallback_date = _normalize_date(fallback_ts)
    state_assisted = bool(
        state.get("setupRevealedBeforeAnswer")
        or state.get("solutionRevealedBeforeAnswer")
        or (state.get("hintsRevealed") or 0) > 0
    )

    attempts = state.get("attempts") or []
    substantive = [a for a in attempts if isinstance(a, dict) and a.get("verdict") not in _NON_SUBSTANTIVE_VERDICTS]
    events: list[dict[str, Any]] = []
    if substantive:
        single_half_score = (
            len(substantive) == 1 and substantive[0].get("verdict") == "correct" and state.get("score") == 0.5
        )
        for att in substantive:
            ev_date = _normalize_date(str(att.get("ts") or ""), fallback_date)
            verdict = str(att.get("verdict") or "")
            correct = verdict == "correct"
            has_explicit_hint = any(k in att for k in ("hintsUsed", "assisted", "hintsRevealed"))
            att_revealed = bool(att.get("setupRevealed") or att.get("solutionRevealed"))
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
            ev_date = _normalize_date(str(rev.get("at") or ""), fallback_date)
            verdict = str(rev.get("verdict") or "")
            correct = verdict == "pass"
            has_explicit_hint = any(k in rev for k in ("hintsUsed", "assisted", "hintsRevealed"))
            if has_explicit_hint:
                assisted = bool(rev.get("hintsUsed") or rev.get("assisted") or (rev.get("hintsRevealed") or 0) > 0)
            else:
                assisted = state_assisted
            events.append({"date": ev_date, "correct": correct, "assisted": assisted})
        return events

    if state.get("skipped"):
        return [{"date": fallback_date, "correct": False, "assisted": state_assisted}]

    last_check = state.get("lastCheck")
    if isinstance(last_check, dict) and last_check.get("verdict") not in (
        None,
        "",
        *_NON_SUBSTANTIVE_VERDICTS,
    ):
        verdict = str(last_check.get("verdict") or "")
        correct = verdict == "correct"
        assisted = state_assisted or (correct and state.get("score") == 0.5)
        return [{"date": fallback_date, "correct": correct, "assisted": assisted}]

    if state.get("score") is not None:
        try:
            sc = float(state["score"])
        except (TypeError, ValueError):
            return []
        correct = sc > 0
        assisted = state_assisted or (0 < sc < 1.0)
        return [{"date": fallback_date, "correct": correct, "assisted": assisted}]

    return []


def replay_events(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Replay chronological review events starting from Level 1."""
    if not events:
        return None
    level = MIN_LEVEL
    last_reviewed = ""
    due_date = ""
    last_wrong_date: str | None = None

    for ev in events:
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
    }


def build_schedule_from_progress(
    data_root: str | None = None,
    progress_dir: str | None = None,
    labs_root: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Build the full review schedule map (`{ "<drillId>/<qid>": ReviewItem }`) from progress via `weak_spots.load_items`."""
    loaded = weak_spots.load_items(data_root=data_root, progress_dir=progress_dir, labs_root=labs_root)
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
            }
        )
    return dict(sorted(schedule.items()))


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
    schedule = build_schedule_from_progress(
        data_root=data_root,
        progress_dir=resolved_progress,
        labs_root=labs_root,
    )
    write_review_items(schedule, progress_dir=resolved_progress, repo_root=repo_root)
    return schedule


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
    saved = load_saved_review_items(progress_dir=resolved_progress, repo_root=repo_root)
    if not saved:
        return backfilled
    merged: dict[str, dict[str, Any]] = dict(backfilled)
    for key, saved_entry in saved.items():
        entry = dict(saved_entry)
        bf_entry = backfilled.get(key)
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


def _base_sort_key(item: dict[str, Any]) -> tuple[str, int, str, str, str]:
    return (
        str(item.get("dueDate") or ""),
        int(item.get("level") or 1),
        str(item.get("unitCode") or ""),
        str(item.get("drillId") or ""),
        str(item.get("qid") or ""),
    )


def interleave_due_items(items: list[dict[str, Any]], limit: int | None = None) -> list[dict[str, Any]]:
    """Interleave due items so no two consecutive items share a unit when avoidable, mixing MTH and PRG."""
    remaining = [redact_review_item(it) for it in items]
    remaining.sort(key=_base_sort_key)

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
                *_base_sort_key(it),
            ),
        )
        remaining.remove(chosen)
        result.append(chosen)
        last_unit = chosen["unitCode"]
        last_subject = chosen["subject"]

    if limit is not None and limit >= 0:
        return result[:limit]
    return result


def get_due_items(
    *,
    today: str | None = None,
    limit: int | None = None,
    data_root: str | None = None,
    progress_dir: str | None = None,
    labs_root: str | None = None,
    repo_root: str | None = None,
) -> list[dict[str, Any]]:
    """Return due review items (`dueDate <= today`), interleaved across units and subjects (read-only)."""
    today_str = _normalize_date(today)
    schedule = get_review_items_schedule(
        data_root=data_root,
        progress_dir=progress_dir,
        labs_root=labs_root,
        repo_root=repo_root,
    )
    due = [it for it in schedule.values() if it["dueDate"] <= today_str]
    return interleave_due_items(due, limit=limit)


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
            "unitCode": "",
            "subject": "PRG" if drill_id.startswith(("DRL-PRG-", "LAB-")) else "MTH",
            "commonTrapTag": None,
            "archetypeKey": None,
            "revisitNote": None,
        }
    )
    base["level"] = step["level"]
    base["lastReviewed"] = step["lastReviewed"]
    base["dueDate"] = step["dueDate"]
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
        "--rebuild",
        action="store_true",
        help="Rebuild progress/review_items.json from existing progress/<DRILL_ID>.json files",
    )
    ap.add_argument("--json", action="store_true", dest="as_json", help="Output JSON instead of plain text")
    ap.add_argument("--today", default=None, help="Override today's date (YYYY-MM-DD)")
    ap.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR") or None)
    ap.add_argument("--progress-dir", default=None)
    args = ap.parse_args(argv)

    repo_root = find_repo_root()
    resolved_progress = args.progress_dir or progress_root(repo_root)
    today_str = _normalize_date(args.today)

    if args.rebuild:
        schedule = rebuild_review_items(
            data_root=args.data_root,
            progress_dir=resolved_progress,
            repo_root=repo_root,
        )
    else:
        schedule = get_review_items_schedule(
            data_root=args.data_root,
            progress_dir=resolved_progress,
            repo_root=repo_root,
        )

    due_items = interleave_due_items(
        [it for it in schedule.values() if it["dueDate"] <= today_str],
        limit=args.limit,
    )

    if args.due:
        if args.as_json:
            print(
                json.dumps(
                    {
                        "today": today_str,
                        "count": len(due_items),
                        "items": due_items,
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(_format_text_report(due_items, due_only=True, today=today_str))
        return 0

    all_items = list(schedule.values())
    if args.limit is not None and args.limit >= 0:
        all_items = all_items[: args.limit]
    if args.as_json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "today": today_str,
                    "path": _store_path(resolved_progress, repo_root),
                    "count": len(schedule),
                    "dueCount": len(due_items),
                    "items": all_items,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(_format_text_report(all_items, due_only=False, today=today_str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
