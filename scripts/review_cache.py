"""Rebuild or inspect the local unit review-schedule cache (`progress/_review_schedule.json`).

Reads unit pages from Notion via `notion_sync.client` (read-only; never writes to Notion)
and writes `{unitCode: {mastery, lastReviewed, nextReview, title?}}` atomically to
`progress/_review_schedule.json` (or `pilot/progress/_review_schedule.json` when
`LEARNINGOS_PILOT=1`).

    python -m scripts.review_cache --rebuild
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from notion_sync.client import load_env, notion_request
from notion_sync.id_map import UNITS_DB, get_title_text, prop_text
from progress_store import load_review_schedule, review_schedule_path, write_review_schedule


def _query_all_units(token: str, db_id: str = UNITS_DB) -> list[dict[str, Any]]:
    """Read all pages from the Notion Units database (paginated, read-only)."""
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        payload: dict[str, Any] = {}
        if cursor:
            payload["start_cursor"] = cursor
        res = notion_request("POST", f"databases/{db_id}/query", token, payload)
        results.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
    return results


def _date_part(prop: dict[str, Any] | None) -> str | None:
    date_obj = (prop or {}).get("date")
    if not isinstance(date_obj, dict):
        return None
    start = date_obj.get("start")
    if not isinstance(start, str) or not start.strip():
        return None
    return start.strip()[:10]


def rebuild_review_cache(
    token: str,
    *,
    db_id: str = UNITS_DB,
    repo_root: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Fetch unit pages from Notion and rebuild `_review_schedule.json` atomically (no Notion writes)."""
    schedule: dict[str, dict[str, Any]] = {}
    for page in _query_all_units(token, db_id=db_id):
        if page.get("archived"):
            continue
        props = page.get("properties") or {}
        unit_code = prop_text(props.get("Full ID")).strip()
        if not unit_code or unit_code.startswith("RETIRED-"):
            continue
        mastery_raw = (props.get("Mastery (0-4)") or {}).get("number")
        mastery = int(mastery_raw) if isinstance(mastery_raw, (int, float)) else None
        last_reviewed = _date_part(props.get("Last Reviewed"))
        next_review = _date_part(props.get("Next Review"))
        if next_review is None and last_reviewed is None and (mastery is None or mastery == 0):
            continue
        entry: dict[str, Any] = {
            "mastery": mastery,
            "lastReviewed": last_reviewed,
            "nextReview": next_review,
        }
        title = get_title_text(props).strip()
        if title:
            entry["title"] = title
        schedule[unit_code] = entry

    write_review_schedule(schedule, repo_root=repo_root)
    return schedule


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `python -m scripts.review_cache`."""
    ap = argparse.ArgumentParser(
        prog="python -m scripts.review_cache",
        description="Inspect or rebuild the local unit review-schedule cache from Notion (read-only).",
    )
    ap.add_argument(
        "--rebuild",
        action="store_true",
        help="Read all unit pages from Notion and atomically rebuild _review_schedule.json",
    )
    args = ap.parse_args(argv)

    if args.rebuild:
        env = load_env()
        token = os.environ.get("NOTION_TOKEN") or env.get("NOTION_TOKEN")
        if not token:
            print("NOTION_TOKEN not found in .env or environment.", file=sys.stderr)
            return 1
        schedule = rebuild_review_cache(token)
        print(
            json.dumps(
                {"ok": True, "path": review_schedule_path(), "units": len(schedule)},
                ensure_ascii=False,
            )
        )
        return 0

    schedule = load_review_schedule()
    print(
        json.dumps(
            {"ok": True, "path": review_schedule_path(), "units": len(schedule)},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
