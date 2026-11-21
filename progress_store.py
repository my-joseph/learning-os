# -*- coding: utf-8 -*-
"""Learner progress, stored apart from drill content.

Drill files (`drills/data/<UNIT>/<DRILL_ID>.json`) hold content only and change when
the problems change. Everything that changes when the learner practises lives in
`progress/<DRILL_ID>.json` (gitignored; override the folder with PROGRESS_DIR):

    {
      "drillId": "...", "unitCode": "...", "updatedAt": "...",
      "sessionSummary": {...},
      "problems": {"Q01": {<problem state>}, ...}
    }

The Studio mirrors this layout in practice-studio/src/lib/progress.ts.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

PROGRESS_FIELDS_DOC = ("sessionSummary",)
PROGRESS_FIELDS_PROBLEM = ("state",)
_ISO_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def pilot_mode() -> bool:
    """True when LEARNINGOS_PILOT is enabled ('1', 'true', 'yes')."""
    return os.environ.get("LEARNINGOS_PILOT", "").strip().lower() in ("1", "true", "yes")


def find_repo_root(start: str | os.PathLike[str] | None = None) -> str:
    """Find this checkout from any working directory using the repository marker."""
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "id_map.json").is_file():
            return str(candidate)
    return str(current)


def progress_root(repo_root: str | None = None) -> str:
    """PROGRESS_DIR, else `pilot/progress/` in pilot mode, else `progress/` relative to `repo_root`."""
    if os.environ.get("PROGRESS_DIR"):
        return os.environ["PROGRESS_DIR"]
    sub = os.path.join("pilot", "progress") if pilot_mode() else "progress"
    return os.path.join(repo_root or find_repo_root(), sub)


def workspace_root(repo_root: str | None = None) -> str:
    """`pilot/workspace/` in pilot mode, else `drills/workspace/` relative to `repo_root`."""
    sub = os.path.join("pilot", "workspace") if pilot_mode() else os.path.join("drills", "workspace")
    return os.path.join(repo_root or find_repo_root(), sub)


def labs_root(repo_root: str | None = None) -> str:
    """LABS_DIR, else `pilot/labs/` in pilot mode, else `labs/` relative to `repo_root`."""
    if os.environ.get("LABS_DIR"):
        return os.environ["LABS_DIR"]
    sub = os.path.join("pilot", "labs") if pilot_mode() else "labs"
    return os.path.join(repo_root or find_repo_root(), sub)


def progress_path(drill_id: str, repo_root: str | None = None) -> str:
    return os.path.join(progress_root(repo_root), f"{drill_id}.json")


def review_schedule_path(repo_root: str | None = None) -> str:
    """Path to `_review_schedule.json` inside the active progress directory (respects LEARNINGOS_PILOT)."""
    return os.path.join(progress_root(repo_root), "_review_schedule.json")


def review_items_path(repo_root: str | None = None) -> str:
    """Path to `review_items.json` inside the active progress directory (respects LEARNINGOS_PILOT)."""
    return os.path.join(progress_root(repo_root), "review_items.json")


def load_review_schedule(repo_root: str | None = None) -> dict[str, dict[str, Any]]:
    """Read the local unit review-schedule cache, or `{}` if missing or invalid."""
    path = review_schedule_path(repo_root)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, dict)}


def write_review_schedule(schedule: dict[str, dict[str, Any]], repo_root: str | None = None) -> str:
    """Atomically write the full unit review-schedule cache to `_review_schedule.json`."""
    path = review_schedule_path(repo_root)
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".review_schedule_", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return path


def merge_review_schedule(updates: dict[str, dict[str, Any]], repo_root: str | None = None) -> str:
    """Merge unit review-schedule entries into `_review_schedule.json` atomically."""
    schedule = load_review_schedule(repo_root)
    for unit_code, vals in updates.items():
        if not isinstance(unit_code, str) or not isinstance(vals, dict):
            continue
        prev = schedule.get(unit_code) or {}
        entry: dict[str, Any] = {
            "mastery": vals.get("mastery"),
            "lastReviewed": vals.get("lastReviewed"),
            "nextReview": vals.get("nextReview"),
        }
        title = vals.get("title") or prev.get("title")
        if title:
            entry["title"] = title
        if isinstance(vals.get("masteryCap"), dict):
            entry["masteryCap"] = {
                "capped": bool(vals["masteryCap"].get("capped")),
                "reason": str(vals["masteryCap"].get("reason") or ""),
            }
        schedule[unit_code] = entry
    return write_review_schedule(schedule, repo_root)


def extract_progress(drill_doc: dict[str, Any]) -> dict[str, Any]:
    """The learner-owned part of a (merged) drill document."""
    return {
        "drillId": drill_doc.get("drillId"),
        "unitCode": drill_doc.get("unitCode"),
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "sessionSummary": drill_doc.get("sessionSummary") or {},
        "problems": {p["id"]: p["state"] for p in drill_doc.get("problems", []) if p.get("id") and p.get("state")},
    }


def _iter_problem_states(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Return problem state dicts from either a drill document (`problems: list`) or a progress file (`problems: dict`)."""
    problems = doc.get("problems")
    if isinstance(problems, dict):
        return [st for st in problems.values() if isinstance(st, dict)]
    if isinstance(problems, list):
        return [p.get("state") or {} for p in problems if isinstance(p, dict)]
    return []


def has_practice(drill_doc: dict[str, Any]) -> bool:
    """True if the document or progress payload carries anything a learner did (not just pristine defaults)."""
    summary = drill_doc.get("sessionSummary") or {}
    if summary.get("attemptDate") or summary.get("score") or summary.get("syncedToNotionAt"):
        return True
    for st in _iter_problem_states(drill_doc):
        if st.get("attempts") or st.get("userInput") or st.get("score") is not None or st.get("skipped"):
            return True
        if (
            st.get("mistakes")
            or st.get("mistakeNote")
            or st.get("revisitNote")
            or st.get("userCode")
            or st.get("reviews")
            or st.get("lastTestReport")
            or st.get("testRuns")
        ):
            return True
        if (
            st.get("setupRevealedBeforeAnswer")
            or st.get("solutionRevealedBeforeAnswer")
            or st.get("hintsRevealed")
            or st.get("durationMs")
            or st.get("variants")
            or st.get("exampleViewedAt")
        ):
            return True
    return False


def load_progress(drill_id: str, repo_root: str | None = None) -> dict[str, Any] | None:
    path = progress_path(drill_id, repo_root)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_progress(drill_doc: dict[str, Any], progress: dict[str, Any] | None) -> dict[str, Any]:
    """Overlay saved progress onto a content document (in place) and return it."""
    if not progress:
        return drill_doc
    if progress.get("sessionSummary"):
        drill_doc["sessionSummary"] = progress["sessionSummary"]
    states = progress.get("problems") or {}
    for p in drill_doc.get("problems", []):
        if p.get("id") in states:
            p["state"] = states[p["id"]]
    return drill_doc


def _is_empty_value(val: Any) -> bool:
    return val is None or val == "" or (isinstance(val, list) and len(val) == 0)


def _max_iso_timestamp(a: Any, b: Any) -> str | None:
    sa = a.strip() if isinstance(a, str) and a.strip() else None
    sb = b.strip() if isinstance(b, str) and b.strip() else None
    if sa and sb:
        return sa if sa > sb else sb
    return sa or sb


def _attempt_key(item: dict[str, Any]) -> str:
    ts = item.get("ts")
    if isinstance(ts, str) and ts:
        return f"ts:{ts}"
    return f"raw:{json.dumps(item, sort_keys=True, separators=(',', ':'))}"


def _merge_attempts(prev_raw: Any, next_raw: Any) -> list[dict[str, Any]] | None:
    prev = [a for a in prev_raw if isinstance(a, dict)] if isinstance(prev_raw, list) else []
    nxt = [a for a in next_raw if isinstance(a, dict)] if isinstance(next_raw, list) else []
    if not prev and not nxt:
        if isinstance(next_raw, list) or isinstance(prev_raw, list):
            return []
        return None
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for item in prev:
        key = _attempt_key(item)
        if key not in seen:
            seen.add(key)
            merged.append(item)
    added_from_next = False
    for item in nxt:
        key = _attempt_key(item)
        if key not in seen:
            seen.add(key)
            merged.append(item)
            added_from_next = True
    if (
        added_from_next
        and prev
        and all(isinstance(a.get("ts"), str) and _ISO_DATE_PREFIX_RE.match(a["ts"]) for a in merged)
    ):
        merged.sort(key=lambda a: str(a["ts"]))
    return merged


def _review_key(item: Any) -> str:
    if isinstance(item, dict):
        rid = item.get("id")
        if isinstance(rid, str) and rid:
            return f"id:{rid}"
        ts = item.get("at") if isinstance(item.get("at"), str) and item.get("at") else ""
        if not ts:
            ts = item.get("ts") if isinstance(item.get("ts"), str) and item.get("ts") else ""
        verdict = item.get("verdict") if isinstance(item.get("verdict"), str) else ""
        attempt_val = item.get("attempt")
        attempt = str(attempt_val) if isinstance(attempt_val, int) and not isinstance(attempt_val, bool) else ""
        if ts:
            return f"ts:{ts}|attempt:{attempt}|verdict:{verdict}"
        if attempt:
            return f"attempt:{attempt}|hash:{item.get('codeHash') or ''}|verdict:{verdict}"
    return f"raw:{json.dumps(item, sort_keys=True, separators=(',', ':'))}"


def _review_slot_key(item: Any) -> str | None:
    if not isinstance(item, dict):
        return None
    ts = item.get("at") if isinstance(item.get("at"), str) and item.get("at") else ""
    if not ts:
        ts = item.get("ts") if isinstance(item.get("ts"), str) and item.get("ts") else ""
    attempt_val = item.get("attempt")
    attempt = str(attempt_val) if isinstance(attempt_val, int) and not isinstance(attempt_val, bool) else ""
    return f"ts:{ts}|attempt:{attempt}" if ts and attempt else None


def _disputed_count(review: dict[str, Any]) -> int:
    findings = review.get("findings")
    if not isinstance(findings, list):
        return 0
    return sum(1 for f in findings if isinstance(f, dict) and f.get("disputed"))


def _merge_review_record(prev_rec: Any, next_rec: Any) -> Any:
    """Merge two copies of the same review record monotonically.

    Preserves server `explain`/`disputed` against stale overwrites while still allowing
    `scripts/review_record.py` (`set_explain`, `dispute_finding`) to add explain or disputes.
    """
    if not isinstance(prev_rec, dict) or not isinstance(next_rec, dict):
        return prev_rec
    merged = dict(prev_rec)
    for text_key in ("explain", "explainQuestion"):
        next_val = next_rec.get(text_key)
        if isinstance(next_val, str) and next_val.strip():
            merged[text_key] = next_val
    if _disputed_count(next_rec) > _disputed_count(prev_rec):
        merged["findings"] = next_rec.get("findings")
        if next_rec.get("verdict") is not None:
            merged["verdict"] = next_rec["verdict"]
    return merged


def _merge_reviews(prev_raw: Any, next_raw: Any) -> list[Any] | None:
    prev = list(prev_raw) if isinstance(prev_raw, list) else []
    nxt = list(next_raw) if isinstance(next_raw, list) else []
    if not prev and not nxt:
        if isinstance(next_raw, list) or isinstance(prev_raw, list):
            return []
        return None
    index_by_key: dict[str, int] = {}
    index_by_slot: dict[str, int] = {}
    merged: list[Any] = []
    for item in prev:
        key = _review_key(item)
        if key not in index_by_key:
            idx = len(merged)
            index_by_key[key] = idx
            slot = _review_slot_key(item)
            if slot is not None:
                index_by_slot[slot] = idx
            merged.append(item)
    for item in nxt:
        key = _review_key(item)
        if key in index_by_key:
            idx = index_by_key[key]
            merged[idx] = _merge_review_record(merged[idx], item)
            continue
        slot = _review_slot_key(item)
        if slot is not None and slot in index_by_slot:
            idx = index_by_slot[slot]
            prev_item = merged[idx]
            if isinstance(prev_item, dict) and isinstance(item, dict):
                prev_disp = _disputed_count(prev_item)
                next_disp = _disputed_count(item)
                if prev_disp != next_disp:
                    merged[idx] = _merge_review_record(prev_item, item)
                    index_by_key[_review_key(merged[idx])] = idx
                    continue
        idx = len(merged)
        index_by_key[key] = idx
        if slot is not None:
            index_by_slot[slot] = idx
        merged.append(item)
    return merged


def _derive_variant_lists(
    variants: Any,
    existing_seen: list[Any],
    existing_attempted: list[Any],
) -> tuple[list[str], list[str]]:
    seen: list[str] = []
    seen_set: set[str] = set()
    for x in existing_seen:
        if isinstance(x, str) and x and x not in seen_set:
            seen_set.add(x)
            seen.append(x)

    attempted: list[str] = []
    attempted_set: set[str] = set()
    for x in existing_attempted:
        if isinstance(x, str) and x and x not in attempted_set:
            attempted_set.add(x)
            attempted.append(x)

    if isinstance(variants, dict):
        for rec in variants.values():
            if not isinstance(rec, dict):
                continue
            vid = rec.get("variantId")
            if not isinstance(vid, str) or not vid:
                continue
            atts = rec.get("attempts") if isinstance(rec.get("attempts"), list) else []
            if bool(rec.get("servedAt")) or len(atts) > 0:
                if vid not in seen_set:
                    seen_set.add(vid)
                    seen.append(vid)
            if any(isinstance(a, dict) and _is_substantive_verdict(a.get("verdict")) for a in atts):
                if vid not in attempted_set:
                    attempted_set.add(vid)
                    attempted.append(vid)

    return seen, attempted


def _merge_problem_state(prev: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge incoming problem state with existing disk state (mirrors TS `writeProgress`).

    Server-owned fields (`variants`, `similarSlots`, `variantsSeen`, `variantsAttempted`,
    `exampleViewedAt`, `cycleStartedAt`, `reviewSetupRevealedAt`, `reviewStepsRevealedAt`)
    come from disk / monotonic max; append-only arrays (`attempts`, `reviews`, `testRuns`)
    are unioned so redacted or stale payloads never wipe server progress.
    """
    st = dict(incoming)
    incoming_cycle = (
        st.get("cycleStartedAt").strip()
        if isinstance(st.get("cycleStartedAt"), str) and st.get("cycleStartedAt").strip()
        else None
    )
    prev_cycle = (
        prev.get("cycleStartedAt").strip()
        if isinstance(prev, dict) and isinstance(prev.get("cycleStartedAt"), str) and prev.get("cycleStartedAt").strip()
        else None
    )

    if isinstance(prev, dict):
        merged_attempts = _merge_attempts(prev.get("attempts"), st.get("attempts"))
        if merged_attempts is not None:
            st["attempts"] = merged_attempts

        merged_reviews = _merge_reviews(prev.get("reviews"), st.get("reviews"))
        if merged_reviews is not None:
            st["reviews"] = merged_reviews

        merged_test_runs = _merge_attempts(prev.get("testRuns"), st.get("testRuns"))
        if merged_test_runs is not None:
            st["testRuns"] = merged_test_runs

        prev_report = prev.get("lastTestReport")
        if isinstance(prev_report, dict):
            is_newer_cycle = bool(incoming_cycle and (not prev_cycle or incoming_cycle > prev_cycle))
            next_report = st.get("lastTestReport")
            if next_report is None:
                if not is_newer_cycle:
                    st["lastTestReport"] = prev_report
            elif isinstance(next_report, dict):
                prev_ts = prev_report.get("ts")
                next_ts = next_report.get("ts")
                if isinstance(prev_ts, str) and prev_ts and isinstance(next_ts, str) and next_ts and prev_ts > next_ts:
                    st["lastTestReport"] = prev_report

        for key in ("mistakes", "mistakeNote", "revisitNote"):
            if _is_empty_value(st.get(key)) and not _is_empty_value(prev.get(key)):
                st[key] = prev[key]

        max_rev_setup = _max_iso_timestamp(prev.get("reviewSetupRevealedAt"), st.get("reviewSetupRevealedAt"))
        if max_rev_setup:
            st["reviewSetupRevealedAt"] = max_rev_setup
        max_rev_steps = _max_iso_timestamp(prev.get("reviewStepsRevealedAt"), st.get("reviewStepsRevealedAt"))
        if max_rev_steps:
            st["reviewStepsRevealedAt"] = max_rev_steps

    # Server-authoritative variant session fields
    if isinstance(prev, dict) and isinstance(prev.get("variants"), dict):
        st["variants"] = prev["variants"]
    elif isinstance(st.get("variants"), dict):
        entries = list(st["variants"].values())
        if entries and all(
            not isinstance(e, dict) or not isinstance(e.get("variantId"), str) or not e.get("variantId")
            for e in entries
        ):
            st.pop("variants", None)

    if isinstance(prev, dict) and isinstance(prev.get("similarSlots"), list):
        st["similarSlots"] = prev["similarSlots"]
    elif isinstance(st.get("similarSlots"), list) and not isinstance(st.get("variants"), dict):
        st.pop("similarSlots", None)

    st.pop("activeVariant", None)

    if isinstance(prev, dict) and isinstance(prev.get("exampleViewedAt"), str) and prev["exampleViewedAt"]:
        st["exampleViewedAt"] = prev["exampleViewedAt"]

    max_cycle = _max_iso_timestamp(
        prev.get("cycleStartedAt") if isinstance(prev, dict) else None, st.get("cycleStartedAt")
    )
    if max_cycle:
        st["cycleStartedAt"] = max_cycle

    prev_seen = (
        prev.get("variantsSeen") if isinstance(prev, dict) and isinstance(prev.get("variantsSeen"), list) else []
    )
    st_seen = st.get("variantsSeen") if isinstance(st.get("variantsSeen"), list) else []
    prev_att = (
        prev.get("variantsAttempted")
        if isinstance(prev, dict) and isinstance(prev.get("variantsAttempted"), list)
        else []
    )
    st_att = st.get("variantsAttempted") if isinstance(st.get("variantsAttempted"), list) else []
    derived_seen, derived_att = _derive_variant_lists(
        st.get("variants"),
        [*prev_seen, *st_seen],
        [*prev_att, *st_att],
    )
    if derived_seen:
        st["variantsSeen"] = derived_seen
    else:
        st.pop("variantsSeen", None)
    if derived_att:
        st["variantsAttempted"] = derived_att
    else:
        st.pop("variantsAttempted", None)

    return st


def _merge_progress_payload(
    existing: dict[str, Any] | None,
    extracted: dict[str, Any],
) -> dict[str, Any]:
    existing_problems = (
        existing.get("problems") if isinstance(existing, dict) and isinstance(existing.get("problems"), dict) else {}
    )
    merged_problems: dict[str, Any] = dict(existing_problems)
    for pid, incoming in (extracted.get("problems") or {}).items():
        if not isinstance(incoming, dict):
            continue
        prev = existing_problems.get(pid)
        merged_problems[pid] = _merge_problem_state(prev if isinstance(prev, dict) else None, incoming)

    incoming_summary = extracted.get("sessionSummary")
    existing_summary = (
        existing.get("sessionSummary")
        if isinstance(existing, dict) and isinstance(existing.get("sessionSummary"), dict)
        else {}
    )
    session_summary = incoming_summary if isinstance(incoming_summary, dict) and incoming_summary else existing_summary

    return {
        "drillId": extracted.get("drillId"),
        "unitCode": extracted.get("unitCode") or (existing.get("unitCode") if isinstance(existing, dict) else None),
        "updatedAt": extracted.get("updatedAt"),
        "sessionSummary": session_summary,
        "problems": merged_problems,
    }


def save_progress(
    drill_doc: dict[str, Any],
    repo_root: str | None = None,
    *,
    allow_reset: bool = False,
) -> str:
    """Write the learner-owned part of `drill_doc` to progress/<DRILL_ID>.json. Never touches drill content.

    Merges against existing disk progress (preserving server-owned variant fields and unioning
    append-only arrays) and refuses to overwrite practised progress with empty state unless
    `allow_reset=True`.
    """
    drill_id = drill_doc.get("drillId")
    if not drill_id:
        raise ValueError("Missing drillId")
    path = progress_path(drill_id, repo_root)
    existing: dict[str, Any] | None = None
    if not allow_reset and os.path.exists(path):
        existing = load_progress(drill_id, repo_root)
        if existing and has_practice(existing) and not has_practice(drill_doc):
            raise ValueError(
                f"Refusing to overwrite practised progress for '{drill_id}' with empty state "
                "(pass allow_reset=True to reset)"
            )
    extracted = extract_progress(drill_doc)
    payload = extracted if allow_reset else _merge_progress_payload(existing, extracted)
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{drill_id}_", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return path


def strip_progress(drill_doc: dict[str, Any]) -> dict[str, Any]:
    """Remove learner-owned fields from a drill document (in place) and return it."""
    for key in PROGRESS_FIELDS_DOC:
        drill_doc.pop(key, None)
    for p in drill_doc.get("problems", []):
        for key in PROGRESS_FIELDS_PROBLEM:
            p.pop(key, None)
    return drill_doc


_NON_SUBSTANTIVE_VERDICTS = ("invalid input", "parse_error")


def _is_in_cycle(ts: Any, cycle_started_at: str | None) -> bool:
    """Return True when `ts` falls at or after `cycle_started_at` (absent boundary includes all history)."""
    if not cycle_started_at:
        return True
    return isinstance(ts, str) and len(ts) > 0 and ts >= cycle_started_at


def _is_substantive_verdict(verdict: Any) -> bool:
    return isinstance(verdict, str) and len(verdict) > 0 and verdict not in _NON_SUBSTANTIVE_VERDICTS


def _finite_num(val: Any) -> float | None:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return None
    f = float(val)
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def _clamp_score_value(val: Any) -> float | None:
    num = _finite_num(val)
    if num is None:
        return None
    if num >= 1.0:
        return 1.0
    if num > 0.0:
        return 0.5
    return 0.0


def _normalise_report(raw: Any, cycle_started_at: str | None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"hasData": False, "allPassed": False, "ts": None}
    raw_ts = raw.get("ts")
    ts = raw_ts.strip() if isinstance(raw_ts, str) and raw_ts.strip() else None
    if ts and cycle_started_at and not _is_in_cycle(ts, cycle_started_at):
        return {"hasData": False, "allPassed": False, "ts": None}

    passed = _finite_num(raw.get("passedCount"))
    if passed is None:
        passed = _finite_num(raw.get("passed"))
    total = _finite_num(raw.get("totalCount"))
    if total is None:
        total = _finite_num(raw.get("total"))
    raw_failed = raw.get("failed")
    failed_count = float(len(raw_failed)) if isinstance(raw_failed, list) else _finite_num(raw_failed)

    all_passed = False
    if isinstance(raw.get("allPassed"), bool):
        all_passed = bool(raw["allPassed"]) and (total is None or total > 0)
    elif passed is not None and total is not None:
        all_passed = total > 0 and passed == total and (failed_count is None or failed_count == 0)

    return {"hasData": True, "allPassed": all_passed, "ts": ts}


def _review_ts(review: dict[str, Any]) -> str:
    for key in ("at", "ts"):
        val = review.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _review_tests_pass(review: dict[str, Any]) -> bool | None:
    tests = review.get("tests")
    if not isinstance(tests, dict):
        return None
    total = _finite_num(tests.get("total"))
    if total is None:
        return None
    passed = _finite_num(tests.get("passed")) or 0.0
    raw_failed = tests.get("failed")
    failed_count = float(len(raw_failed)) if isinstance(raw_failed, list) else (_finite_num(raw_failed) or 0.0)
    return total > 0 and passed == total and failed_count == 0


def _extract_cycle_data(
    state: dict[str, Any],
    *,
    test_report: dict[str, Any] | None = None,
    has_test_report_override: bool = False,
    cycle_started_at: str | None = None,
    has_cycle_override: bool = False,
    is_variant: bool = False,
) -> dict[str, Any]:
    raw_cycle = cycle_started_at if has_cycle_override else state.get("cycleStartedAt")
    eff_cycle = raw_cycle if isinstance(raw_cycle, str) and raw_cycle else None

    raw_attempts = state.get("attempts") if isinstance(state.get("attempts"), list) else []
    all_orig_attempts = [a for a in raw_attempts if isinstance(a, dict) and (is_variant or a.get("kind") != "variant")]
    cycle_atts = [a for a in all_orig_attempts if _is_in_cycle(a.get("ts"), eff_cycle)]
    substantive_atts = [a for a in cycle_atts if _is_substantive_verdict(a.get("verdict"))]

    raw_reviews = state.get("reviews") if isinstance(state.get("reviews"), list) else []
    all_reviews = [r for r in raw_reviews if isinstance(r, dict) and r.get("verdict")]
    cycle_revs = [r for r in all_reviews if _is_in_cycle(_review_ts(r), eff_cycle)]

    raw_test_runs = state.get("testRuns") if isinstance(state.get("testRuns"), list) else []
    all_test_runs = [tr for tr in raw_test_runs if isinstance(tr, dict)]
    cycle_test_runs = [tr for tr in all_test_runs if _is_in_cycle(tr.get("ts"), eff_cycle)]

    raw_report = test_report if has_test_report_override else state.get("lastTestReport")
    report_info = _normalise_report(raw_report, eff_cycle)

    example_viewed_in_cycle = bool(
        state.get("exampleViewedAt") and _is_in_cycle(state.get("exampleViewedAt"), eff_cycle)
    )
    review_help_in_cycle = bool(
        (state.get("reviewSetupRevealedAt") and _is_in_cycle(state.get("reviewSetupRevealedAt"), eff_cycle))
        or (state.get("reviewStepsRevealedAt") and _is_in_cycle(state.get("reviewStepsRevealedAt"), eff_cycle))
    )
    hints_val = _finite_num(state.get("hintsRevealed")) or 0.0
    used_help = bool(
        hints_val > 0
        or state.get("setupRevealedBeforeAnswer")
        or state.get("solutionRevealedBeforeAnswer")
        or example_viewed_in_cycle
        or review_help_in_cycle
        or any(a.get("setupRevealed") or a.get("solutionRevealed") or a.get("exampleViewed") for a in cycle_atts)
    )

    has_prior_history = bool(all_orig_attempts or all_reviews or all_test_runs)
    has_current_cycle_record = bool(cycle_atts or cycle_revs or cycle_test_runs or report_info["hasData"])
    is_stale_prev_cycle = bool(eff_cycle and has_prior_history and not has_current_cycle_record)

    return {
        "cycleStartedAt": eff_cycle,
        "allOrigAttempts": all_orig_attempts,
        "cycleAtts": cycle_atts,
        "substantiveAtts": substantive_atts,
        "cycleRevs": cycle_revs,
        "cycleTestRuns": cycle_test_runs,
        "reportInfo": report_info,
        "usedHelp": used_help,
        "isStalePrevCycle": is_stale_prev_cycle,
    }


def _resolve_prg_latest_tests_status(
    report_info: dict[str, Any],
    cycle_revs: list[dict[str, Any]],
    cycle_test_runs: list[dict[str, Any]],
) -> str:
    latest_rev = cycle_revs[-1] if cycle_revs else None
    latest_rev_at = _review_ts(latest_rev) if latest_rev else ""
    rev_test_pass = _review_tests_pass(latest_rev) if latest_rev else None

    if report_info["hasData"] and latest_rev:
        if report_info["ts"] and latest_rev_at and latest_rev_at > report_info["ts"] and rev_test_pass is not None:
            return "pass" if rev_test_pass else "fail"
        return "pass" if report_info["allPassed"] else "fail"
    if report_info["hasData"]:
        return "pass" if report_info["allPassed"] else "fail"
    if latest_rev:
        if rev_test_pass is not None:
            return "pass" if rev_test_pass else "fail"
        return "pass" if latest_rev.get("verdict") == "pass" else "unknown"
    if cycle_test_runs:
        return "pass" if cycle_test_runs[-1].get("allPassed") else "fail"
    return "unknown"


def _apply_lower_only_self_score(
    auto_score: float,
    auto_outcome: str,
    first_try: bool,
    used_help: bool,
    state: dict[str, Any],
    *,
    ignore_state_score: bool,
    is_variant: bool,
) -> dict[str, Any]:
    if ignore_state_score or is_variant:
        return {"score": auto_score, "outcome": auto_outcome, "firstTry": first_try, "usedHelp": used_help}
    self_score = _clamp_score_value(state.get("score"))
    if self_score is not None and self_score < auto_score:
        if self_score == 0.0:
            return {"score": 0.0, "outcome": "wrong", "firstTry": False, "usedHelp": used_help}
        return {"score": 0.5, "outcome": "assisted", "firstTry": False, "usedHelp": used_help}
    return {"score": auto_score, "outcome": auto_outcome, "firstTry": first_try, "usedHelp": used_help}


def score_problem(
    state: dict[str, Any] | None,
    *,
    is_prg: bool = False,
    test_report: dict[str, Any] | None = None,
    has_test_report_override: bool = False,
    cycle_started_at: str | None = None,
    has_cycle_override: bool = False,
    is_variant: bool = False,
    ignore_state_score: bool = False,
) -> dict[str, Any]:
    """Canonical scoring & classification rule (exact parity with `practice-studio/src/lib/scoring.ts`).

    Returns `{"score": 1.0 | 0.5 | 0.0 | None, "outcome": str, "firstTry": bool, "usedHelp": bool}`.
    """
    _ = is_prg  # PRG path is auto-detected from reviews/test reports/test runs; in-browser PRG uses attempts.
    if not isinstance(state, dict):
        return {"score": None, "outcome": "notTried", "firstTry": False, "usedHelp": False}

    data = _extract_cycle_data(
        state,
        test_report=test_report,
        has_test_report_override=has_test_report_override,
        cycle_started_at=cycle_started_at,
        has_cycle_override=has_cycle_override,
        is_variant=is_variant,
    )
    substantive_atts = data["substantiveAtts"]
    cycle_revs = data["cycleRevs"]
    cycle_test_runs = data["cycleTestRuns"]
    report_info = data["reportInfo"]
    used_help = data["usedHelp"]

    if data["isStalePrevCycle"]:
        return {"score": None, "outcome": "notTried", "firstTry": False, "usedHelp": used_help}

    if state.get("skipped") is True:
        return {"score": 0.0, "outcome": "skipped", "firstTry": False, "usedHelp": used_help}

    # PRG workspace / lab path: tests + code reviews.
    has_prg_evidence = bool(cycle_revs or report_info["hasData"] or cycle_test_runs)
    if has_prg_evidence:
        latest_tests_status = _resolve_prg_latest_tests_status(report_info, cycle_revs, cycle_test_runs)
        latest_rev = cycle_revs[-1] if cycle_revs else None

        if latest_tests_status == "fail":
            return {"score": 0.0, "outcome": "wrong", "firstTry": False, "usedHelp": used_help}
        if not latest_rev:
            return {"score": None, "outcome": "notTried", "firstTry": False, "usedHelp": used_help}
        if latest_rev.get("verdict") != "pass":
            return {"score": 0.0, "outcome": "wrong", "firstTry": False, "usedHelp": used_help}

        had_earlier_revise = any(r.get("verdict") != "pass" for r in cycle_revs)
        had_earlier_failed_test_run = (
            any(not tr.get("allPassed") for tr in cycle_test_runs)
            or (report_info["hasData"] and not report_info["allPassed"])
            or any(_review_tests_pass(r) is False for r in cycle_revs)
        )
        if not used_help and not had_earlier_revise and not had_earlier_failed_test_run:
            return {"score": 1.0, "outcome": "correct", "firstTry": True, "usedHelp": False}
        return {"score": 0.5, "outcome": "assisted", "firstTry": False, "usedHelp": used_help}

    # Math / choice / in-browser PRG path: substantive check attempts in current cycle.
    if substantive_atts:
        first_correct_idx = next((i for i, a in enumerate(substantive_atts) if a.get("verdict") == "correct"), -1)
        if first_correct_idx == 0:
            auto_score = 0.5 if used_help else 1.0
            auto_outcome = "assisted" if used_help else "correct"
            return _apply_lower_only_self_score(
                auto_score,
                auto_outcome,
                not used_help,
                used_help,
                state,
                ignore_state_score=ignore_state_score,
                is_variant=is_variant,
            )
        if first_correct_idx > 0:
            return _apply_lower_only_self_score(
                0.5,
                "assisted",
                False,
                used_help,
                state,
                ignore_state_score=ignore_state_score,
                is_variant=is_variant,
            )
        latest_verdict = substantive_atts[-1].get("verdict")
        if latest_verdict == "skipped":
            return {"score": 0.0, "outcome": "skipped", "firstTry": False, "usedHelp": used_help}
        if latest_verdict in ("partial", "equivalent_not_in_form"):
            return _apply_lower_only_self_score(
                0.5,
                "assisted",
                False,
                used_help,
                state,
                ignore_state_score=ignore_state_score,
                is_variant=is_variant,
            )
        return {"score": 0.0, "outcome": "wrong", "firstTry": False, "usedHelp": used_help}

    # Fallback for lightweight state carrying a substantive `lastCheck` without `attempts[]`.
    last_check = state.get("lastCheck")
    if isinstance(last_check, dict) and _is_substantive_verdict(last_check.get("verdict")):
        v = last_check.get("verdict")
        if v == "skipped":
            return {"score": 0.0, "outcome": "skipped", "firstTry": False, "usedHelp": used_help}
        if v == "correct":
            auto_score = 0.5 if used_help else 1.0
            auto_outcome = "assisted" if used_help else "correct"
            return _apply_lower_only_self_score(
                auto_score,
                auto_outcome,
                not used_help,
                used_help,
                state,
                ignore_state_score=ignore_state_score,
                is_variant=is_variant,
            )
        if v in ("partial", "equivalent_not_in_form"):
            return _apply_lower_only_self_score(
                0.5,
                "assisted",
                False,
                used_help,
                state,
                ignore_state_score=ignore_state_score,
                is_variant=is_variant,
            )
        return {"score": 0.0, "outcome": "wrong", "firstTry": False, "usedHelp": used_help}

    # Unverified item with manual self-score.
    if not is_variant and not ignore_state_score:
        manual = _clamp_score_value(state.get("score"))
        if manual is not None:
            if manual == 1.0:
                if used_help:
                    return {"score": 0.5, "outcome": "assisted", "firstTry": False, "usedHelp": True}
                return {"score": 1.0, "outcome": "correct", "firstTry": True, "usedHelp": False}
            if manual == 0.5:
                return {"score": 0.5, "outcome": "assisted", "firstTry": False, "usedHelp": used_help}
            return {"score": 0.0, "outcome": "wrong", "firstTry": False, "usedHelp": used_help}

    return {"score": None, "outcome": "notTried", "firstTry": False, "usedHelp": used_help}


def score_variant(record: dict[str, Any] | None, cycle_started_at: str | None = None) -> dict[str, Any]:
    """Score a variant session record using the exact same rule as the main question."""
    if not isinstance(record, dict):
        return {"score": None, "outcome": "notTried", "firstTry": False, "usedHelp": False}
    served_at = record.get("servedAt")
    in_current_cycle = not cycle_started_at or (
        isinstance(served_at, str) and len(served_at) > 0 and served_at >= cycle_started_at
    )
    adapted: dict[str, Any] = {
        "attempts": record.get("attempts") if isinstance(record.get("attempts"), list) else [],
        "hintsRevealed": record.get("hintsRevealed", 0) if in_current_cycle else 0,
        "setupRevealedBeforeAnswer": bool(record.get("setupRevealed")) if in_current_cycle else False,
        "solutionRevealedBeforeAnswer": bool(record.get("stepsRevealed")) if in_current_cycle else False,
        "cycleStartedAt": cycle_started_at,
    }
    return score_problem(
        adapted,
        cycle_started_at=cycle_started_at,
        has_cycle_override=True,
        is_variant=True,
        ignore_state_score=True,
    )


def is_awaiting_review(
    state: dict[str, Any] | None,
    *,
    test_report: dict[str, Any] | None = None,
    has_test_report_override: bool = False,
    cycle_started_at: str | None = None,
    has_cycle_override: bool = False,
) -> bool:
    """Return True for a PRG item whose latest test run in the current cycle passed with no review yet."""
    if not isinstance(state, dict) or state.get("skipped") is True:
        return False
    data = _extract_cycle_data(
        state,
        test_report=test_report,
        has_test_report_override=has_test_report_override,
        cycle_started_at=cycle_started_at,
        has_cycle_override=has_cycle_override,
    )
    if data["isStalePrevCycle"] or data["cycleRevs"]:
        return False
    if not (data["reportInfo"]["hasData"] or data["cycleTestRuns"]):
        return False
    return _resolve_prg_latest_tests_status(data["reportInfo"], data["cycleRevs"], data["cycleTestRuns"]) == "pass"


def is_locked_after_correct(
    state: dict[str, Any] | None,
    *,
    cycle_started_at: str | None = None,
    has_cycle_override: bool = False,
    is_variant: bool = False,
) -> bool:
    """Return True once a math/choice/in-browser/variant problem has a correct substantive check
    in the current cycle (mirror of `practice-studio/src/lib/scoring.ts:isLockedAfterCorrect`).
    """
    if not isinstance(state, dict):
        return False
    data = _extract_cycle_data(
        state,
        cycle_started_at=cycle_started_at,
        has_cycle_override=has_cycle_override,
        is_variant=is_variant,
    )
    if data["isStalePrevCycle"]:
        return False
    if any(a.get("verdict") == "correct" for a in data["substantiveAtts"]):
        return True
    last_check = state.get("lastCheck")
    if len(data["allOrigAttempts"]) == 0 and isinstance(last_check, dict) and last_check.get("verdict") == "correct":
        return True
    return False


def item_score(state: dict[str, Any], *, is_prg: bool = False) -> tuple[float, bool]:
    """Return (score, used_help) for a problem state using the canonical `score_problem` rule.

    Returns `(-1.0, used_help)` when the item has no score yet (not tried / awaiting review).
    """
    res = score_problem(state, is_prg=is_prg)
    sc = res["score"]
    return (-1.0 if sc is None else float(sc)), bool(res["usedHelp"])
