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


def extract_progress(drill_doc: dict[str, Any]) -> dict[str, Any]:
    """The learner-owned part of a (merged) drill document."""
    return {
        "drillId": drill_doc.get("drillId"),
        "unitCode": drill_doc.get("unitCode"),
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "sessionSummary": drill_doc.get("sessionSummary") or {},
        "problems": {p["id"]: p["state"] for p in drill_doc.get("problems", []) if p.get("id") and p.get("state")},
    }


def has_practice(drill_doc: dict[str, Any]) -> bool:
    """True if the document carries anything a learner did (not just pristine defaults)."""
    summary = drill_doc.get("sessionSummary") or {}
    if summary.get("attemptDate") or summary.get("score") or summary.get("syncedToNotionAt"):
        return True
    for p in drill_doc.get("problems", []):
        st = p.get("state") or {}
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


def save_progress(drill_doc: dict[str, Any], repo_root: str | None = None) -> str:
    """Write the learner-owned part of `drill_doc` to progress/<DRILL_ID>.json. Never touches drill content."""
    drill_id = drill_doc.get("drillId")
    if not drill_id:
        raise ValueError("Missing drillId")
    path = progress_path(drill_id, repo_root)
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
