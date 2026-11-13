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
from typing import Any

PROGRESS_FIELDS_DOC = ("sessionSummary",)
PROGRESS_FIELDS_PROBLEM = ("state",)


def progress_root(repo_root: str | None = None) -> str:
    """PROGRESS_DIR, else `progress/` relative to `repo_root` (default: current directory)."""
    if os.environ.get("PROGRESS_DIR"):
        return os.environ["PROGRESS_DIR"]
    return os.path.join(repo_root, "progress") if repo_root else "progress"


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
        if st.get("mistakes") or st.get("mistakeNote") or st.get("userCode"):
            return True
        if st.get("setupRevealedBeforeAnswer") or st.get("hintsRevealed") or st.get("durationMs"):
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
