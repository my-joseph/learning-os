# -*- coding: utf-8 -*-
"""
Pristine Project Lab synchronization to Notion (`Learning Practice & Drills`).

Reuses `notion_sync.client`, `notion_sync.blocks`, and `notion_sync.drill_sync`
without creating a second Notion client.

Usage:
    python -m notion_sync.lab_sync <lab_dir> [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from notion_sync.blocks import bullet, callout_block, divider_block, h2, toggle_block
from notion_sync.client import MissingNotionToken, load_env, notion_request, replace_page_content, require_token
from notion_sync.drill_sync import _mention_or_code
from notion_sync.id_map import save_id_map


def _extract_id(entry: Any) -> str | None:
    if isinstance(entry, dict):
        return entry.get("id")
    if isinstance(entry, str):
        return entry
    return None


def sync_lab_to_notion(
    lab_dir: Path,
    *,
    id_map_path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create or update a pristine Notion record for a project lab.

    Returns ``{"synced": True, "pageId": ..., "labId": ...}`` or
    ``{"synced": False, "degraded": True, "error": ...}`` on token/network failure.
    A partial page write returns ``synced: False``, ``partial: True`` and ``failedSteps``.
    When ``dry_run=True`` or ``NOTION_DRY_RUN=1``, validates config and builds the
    payload without calling Notion or modifying ``id_map.json``.
    """
    cfg_path = lab_dir / "lab.config.json"
    if not cfg_path.is_file():
        return {"synced": False, "degraded": True, "error": f"lab.config.json not found in {lab_dir}"}
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    lab_id = cfg["labId"]

    is_dry_run = dry_run or os.environ.get("NOTION_DRY_RUN", "").lower() in ("1", "true", "yes")

    im_path = id_map_path or Path("id_map.json")
    id_map = json.loads(im_path.read_text(encoding="utf-8")) if im_path.exists() else {}

    chapter_code = cfg.get("chapterCode", "")
    topic_code = cfg.get("topicCode") or ("-".join(chapter_code.split("-")[:2]) if chapter_code else "")
    units_used = cfg.get("unitsUsed") or []
    milestones = cfg.get("milestones") or []
    kind = cfg.get("kind", "chapter-lab")
    domain = cfg.get("domain", lab_id)
    level = cfg.get("level", 3)
    title = cfg.get("title") or f"{chapter_code} — {domain} ({kind}, L{level})"
    scope_name = "Unit Drill" if len(units_used) == 1 else "Chapter Mixed"

    props: dict[str, Any] = {
        "Drill": {"title": [{"type": "text", "text": {"content": title[:200]}}]},
        "Drill ID": {"rich_text": [{"type": "text", "text": {"content": lab_id}}]},
        "Scope Level": {"select": {"name": scope_name}},
        "Format": {"select": {"name": "Code Test Suite"}},
        "Difficulty Mode": {"select": {"name": f"Level {level} - Project Lab"}},
        "Question Count": {"number": len(milestones)},
        "Practice Status": {"select": {"name": "Ready"}},
        "Score": {"number": 0},
        "Max Score": {"number": len(milestones)},
        "Mistake Categories": {"multi_select": []},
        "Diverged Steps Summary": {"rich_text": [{"type": "text", "text": {"content": "Ready to start."}}]},
        "Local File Path": {"rich_text": [{"type": "text", "text": {"content": str(lab_dir)}}]},
    }
    unit_ids = [uid for u in units_used if (uid := _extract_id(id_map.get(u)))]
    if unit_ids:
        props["Units"] = {"relation": [{"id": uid} for uid in unit_ids]}
    if cid := _extract_id(id_map.get(chapter_code)):
        props["Chapters"] = {"relation": [{"id": cid}]}
    if tid := _extract_id(id_map.get(topic_code)):
        props["Topics"] = {"relation": [{"id": tid}]}

    unit_mentions = ", ".join(_mention_or_code(u, id_map) for u in units_used) or chapter_code
    blocks: list[dict[str, Any]] = [
        callout_block(
            f"Project Lab ({lab_id}) · {kind} · Level {level}\n"
            f"Domain: {domain} | Units: {unit_mentions}\n"
            f"Local Workspace: {lab_dir}",
            id_map,
            color="blue_background",
        ),
        divider_block(),
        h2("Milestones", id_map),
    ]
    for ms in milestones:
        mid = ms.get("id", "M?")
        mtitle = ms.get("title", "")
        goal = ms.get("goal", "")
        qcs = ", ".join(ms.get("qualityChecks") or [])
        children = [
            bullet(f"**Goal:** {goal}", id_map),
            bullet(f"**Units:** {', '.join(_mention_or_code(u, id_map) for u in (ms.get('units') or []))}", id_map),
            bullet(f"**Rubric:** `{qcs}`", id_map),
        ]
        blocks.append(toggle_block(f"[{mid}] {mtitle}", children, id_map))

    if is_dry_run:
        return {
            "synced": True,
            "degraded": False,
            "dryRun": True,
            "pageId": f"mock-{lab_id}",
            "labId": lab_id,
            "blockCount": len(blocks),
        }

    env = load_env()
    try:
        token = require_token(env.get("NOTION_TOKEN") or os.environ.get("NOTION_TOKEN"))
    except MissingNotionToken as exc:
        return {"synced": False, "degraded": True, "labId": lab_id, "error": str(exc)}

    drills_db_id = _extract_id(id_map.get("DRILLS_DB"))
    if not drills_db_id:
        return {"synced": False, "degraded": True, "labId": lab_id, "error": "DRILLS_DB not found in id_map.json"}

    try:
        q = notion_request(
            "POST",
            f"databases/{drills_db_id}/query",
            token,
            {"filter": {"property": "Drill ID", "rich_text": {"equals": lab_id}}},
        )
        results = q.get("results", [])

        icon_payload = {"type": "icon", "icon": {"name": "code", "color": "blue"}}
        if results:
            page_id = results[0]["id"]
            notion_request("PATCH", f"pages/{page_id}", token, {"icon": icon_payload, "properties": props})
        else:
            created = notion_request(
                "POST",
                "pages",
                token,
                {"parent": {"database_id": drills_db_id}, "icon": icon_payload, "properties": props},
            )
            page_id = created["id"]

        id_map[lab_id] = {"id": page_id, "title": title}
        save_id_map(id_map, im_path)

    except Exception as exc:  # noqa: BLE001
        return {"synced": False, "degraded": True, "labId": lab_id, "error": str(exc)}

    result = {"synced": True, "degraded": False, "pageId": page_id, "labId": lab_id}
    try:
        failed_step = "blockCleanup" if replace_page_content(page_id, blocks, token) else None
    except (OSError, RuntimeError):
        failed_step = "pageContent"
    if failed_step:
        result.update(synced=False, partial=True, failedSteps=[failed_step])
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m notion_sync.lab_sync",
        description="Sync a pristine project lab record to Notion (Learning Practice & Drills).",
    )
    parser.add_argument("lab_dir", type=Path, help="Path to the project lab directory containing lab.config.json")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate lab.config.json and build the Notion payload without writing to Notion or id_map.json",
    )
    args = parser.parse_args(argv)
    res = sync_lab_to_notion(args.lab_dir, dry_run=args.dry_run)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("synced") else 1


if __name__ == "__main__":
    raise SystemExit(main())
