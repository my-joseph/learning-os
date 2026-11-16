"""Rebuild id_map.json from Notion databases using the shared notion_sync.client."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from notion_sync.client import notion_request

TOPICS_DB = "4003818f-8ba0-8029-b434-e25399e46ef0"
CHAPTERS_DB = "4003818f-8ba0-8031-8336-f7852e0de01b"
UNITS_DB = "4003818f-8ba0-804e-a812-f0251efb8978"
RESOURCES_DB = "40c3818f-8ba0-8098-93cf-c2fcb655f510"
DRILLS_DB = "40d3818f-8ba0-8125-8cae-ea0de6183186"
CONCEPT_VAULT_DB = "4103818f-8ba0-8164-aa0d-eeb2d6cb65b0"


def prop_text(prop: dict | None) -> str:
    """Extract plain text from a Notion title or rich_text property."""
    if not prop:
        return ""
    ptype = prop.get("type")
    val = prop.get(ptype)
    if not isinstance(val, list):
        return ""
    return "".join(t.get("plain_text", "") for t in val)


def prop_val(prop: dict | None) -> Any:
    """Extract a simple Python value from a Notion property."""
    if not prop:
        return None
    ptype = prop.get("type")
    val = prop.get(ptype)
    if val is None:
        return None
    if ptype in ("title", "rich_text"):
        return "".join(t.get("plain_text", "") for t in val)
    if ptype in ("select", "status"):
        return val.get("name")
    if ptype == "relation":
        return [x.get("id") for x in val]
    if ptype == "url":
        return val
    return val


def get_title_text(props: dict) -> str:
    """Return the plain text of whichever property has type == 'title'."""
    for v in props.values():
        if v.get("type") == "title":
            return prop_text(v)
    return ""


def query_all(db_id: str, token: str, filter_obj: dict | None = None) -> list[dict]:
    """Query all pages in a Notion database with pagination."""
    results: list[dict] = []
    cursor: str | None = None
    while True:
        payload: dict[str, Any] = {}
        if filter_obj is not None:
            payload["filter"] = filter_obj
        if cursor:
            payload["start_cursor"] = cursor
        res = notion_request("POST", f"databases/{db_id}/query", token, payload)
        results.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
    return results


def rebuild_id_map(token: str, existing: dict | None = None) -> dict[str, dict]:
    """Rebuild id_map.json from Notion Topics, Chapters, Units, Resources, Concept Vault, and Drills DBs."""
    existing = existing or {}
    out: dict[str, dict] = {}

    # Preserve static DB entries
    for key in ("DRILLS_DB", "CONCEPT_VAULT_DB"):
        if key in existing:
            out[key] = existing[key]

    # Topics, Chapters, Units
    for db_id in (TOPICS_DB, CHAPTERS_DB, UNITS_DB):
        for page in query_all(db_id, token):
            if page.get("archived"):
                continue
            props = page.get("properties", {})
            full_id = prop_text(props.get("Full ID")).strip()
            if not full_id or full_id.startswith("RETIRED-"):
                continue
            out[full_id] = {"id": page["id"], "title": get_title_text(props)}

    # Resources
    for page in query_all(RESOURCES_DB, token):
        if page.get("archived"):
            continue
        props = page.get("properties", {})
        rid = prop_text(props.get("Resource ID")).strip()
        if not rid:
            continue
        entry: dict[str, Any] = {"id": page["id"], "title": get_title_text(props)}
        url = prop_val(props.get("URL"))
        if url:
            entry["url"] = url
        out[rid] = entry

    # Concept Vault (preserve CON-* key names by page id, refresh titles)
    con_by_id = {
        v["id"].replace("-", ""): k
        for k, v in existing.items()
        if k.startswith("CON-") and isinstance(v, dict) and "id" in v
    }
    for page in query_all(CONCEPT_VAULT_DB, token):
        if page.get("archived"):
            continue
        pid_norm = page["id"].replace("-", "")
        key = con_by_id.get(pid_norm)
        if key:
            out[key] = {"id": page["id"], "title": get_title_text(page.get("properties", {}))}

    # Drills DB
    for page in query_all(DRILLS_DB, token):
        if page.get("archived"):
            continue
        props = page.get("properties", {})
        did = prop_text(props.get("Drill ID")).strip()
        if did:
            out[did] = {"id": page["id"], "title": get_title_text(props)}

    return out


def save_id_map(id_map: dict[str, dict], path: Path = Path("id_map.json")) -> None:
    """Write id_map.json with deterministic formatting."""
    path.write_text(json.dumps(id_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
