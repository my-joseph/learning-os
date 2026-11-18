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
import tempfile
from pathlib import Path
from typing import Any

PROGRESS_FIELDS_DOC = ("sessionSummary",)
PROGRESS_FIELDS_PROBLEM = ("state",)


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
        if st.get("mistakes") or st.get("mistakeNote") or st.get("userCode") or st.get("reviews"):
            return True
        if (
            st.get("setupRevealedBeforeAnswer")
            or st.get("solutionRevealedBeforeAnswer")
            or st.get("hintsRevealed")
            or st.get("durationMs")
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


def save_progress(
    drill_doc: dict[str, Any],
    repo_root: str | None = None,
    *,
    allow_reset: bool = False,
) -> str:
    """Write the learner-owned part of `drill_doc` to progress/<DRILL_ID>.json. Never touches drill content.

    Refuses to overwrite an existing practised progress file with empty state unless `allow_reset=True`.
    """
    drill_id = drill_doc.get("drillId")
    if not drill_id:
        raise ValueError("Missing drillId")
    path = progress_path(drill_id, repo_root)
    if not allow_reset and os.path.exists(path):
        existing = load_progress(drill_id, repo_root)
        if existing and has_practice(existing) and not has_practice(drill_doc):
            raise ValueError(
                f"Refusing to overwrite practised progress for '{drill_id}' with empty state "
                "(pass allow_reset=True to reset)"
            )
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(extract_progress(drill_doc), f, ensure_ascii=False, indent=2)
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


def item_score(state: dict[str, Any]) -> tuple[float, bool]:
    """Return (score, assisted) for a math problem state, matching Studio's applyCheckResult.

    - Skipped -> (0.0, assisted)
    - First substantive attempt is 'correct' and unassisted -> (1.0, False)
    - Correct after a wrong/partial attempt or assisted -> (0.5, assisted)
    - Otherwise -> (0.0, assisted), or (-1.0, assisted) if unattempted.
    """
    attempts = state.get("attempts") or []
    assisted = bool(
        state.get("setupRevealedBeforeAnswer")
        or state.get("solutionRevealedBeforeAnswer")
        or (state.get("hintsRevealed") or 0) > 0
    )
    assisted = assisted or any(a.get("setupRevealed") or a.get("solutionRevealed") for a in attempts)
    if state.get("skipped"):
        return 0.0, assisted
    substantive = [a for a in attempts if a.get("verdict") not in _NON_SUBSTANTIVE_VERDICTS]
    if substantive:
        first = substantive[0].get("verdict")
        if first == "correct" and not assisted:
            return 1.0, assisted
        if any(a.get("verdict") in ("correct", "equivalent_not_in_form", "partial") for a in substantive):
            return 0.5, assisted
        return 0.0, assisted
    score = state.get("score")
    if score is None:
        return -1.0, assisted  # not attempted
    return (min(float(score), 0.5) if assisted else float(score)), assisted
