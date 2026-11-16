"""PRG Curriculum v2 migration script (Option A renumber).

Default mode is DRY-RUN: reads Notion and local files, prints the full plan,
and makes zero writes.

Usage:
    python -m scripts.prg_migrate
    python -m scripts.prg_migrate --topic PRG-T00
    python -m scripts.prg_migrate --all --apply --i-have-reviewed-the-dry-run
    python -m scripts.prg_migrate --all --apply --i-have-reviewed-the-dry-run --resume migrations/prg_v2_<timestamp>.json
    python -m scripts.prg_migrate --rollback migrations/prg_v2_<timestamp>.json
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from notion_sync.client import get_all_blocks, load_env, notion_request, require_token
from notion_sync.id_map import (
    CHAPTERS_DB,
    DRILLS_DB,
    TOPICS_DB,
    UNITS_DB,
    get_title_text,
    prop_text,
    prop_val,
    query_all,
    rebuild_id_map,
    save_id_map,
)

MAP_PATH = Path("docs/prg_migration_map.json")
ID_MAP_PATH = Path("id_map.json")
MIGRATIONS_DIR = Path("migrations")

LAB_OLD_ID = "LAB-PRG-T03-C01-01"
LAB_NEW_ID = "LAB-PRG-T01-C04-02"
LAB_NEW_UNIT = "PRG-T01-C04-U06"
LAB_NEW_CHAPTER = "PRG-T01-C04"
LAB_NEW_TOPIC = "PRG-T01"

DB_BY_LEVEL = {
    "topic": TOPICS_DB,
    "chapter": CHAPTERS_DB,
    "unit": UNITS_DB,
}

TITLE_PROP_BY_LEVEL = {
    "topic": "Topic",
    "chapter": "Title",
    "unit": "Unit",
}

OBJECTIVE_PROP_BY_LEVEL = {
    "topic": "Goal",
    "chapter": "Objective",
    "unit": "Learning Objective",
}

PARENT_RELATIONS_BY_LEVEL: dict[str, tuple[str, ...]] = {
    "topic": (),
    "chapter": ("Topics",),
    "unit": ("Learning Topics", "Learning Chapters"),
}

RETIRE_DATE = "2026-11-16"
THROTTLE_SECONDS = 0.35  # ~2.85 req/s to stay under Notion's ~3 req/s rate limit
_last_notion_call_ts: float = 0.0

RELATION_PROPS_CHECK = ("Chapters", "Units", "Topics", "Learning Topics", "Learning Chapters")


def _throttle() -> None:
    """Sleep if needed to respect Notion's ~3 req/s rate limit."""
    global _last_notion_call_ts
    if THROTTLE_SECONDS <= 0:
        return
    now = time.monotonic()
    elapsed = now - _last_notion_call_ts
    if _last_notion_call_ts > 0 and elapsed < THROTTLE_SECONDS:
        time.sleep(THROTTLE_SECONDS - elapsed)
    _last_notion_call_ts = time.monotonic()


def _retire_title(old_title: str) -> str:
    if old_title.startswith("[Retired] "):
        return old_title
    if old_title.startswith("[RETIRED] "):
        return f"[Retired] {old_title[len('[RETIRED] ') :]}"
    return f"[Retired] {old_title}"


def _retire_pointer(target: str) -> str:
    return f"Retired {RETIRE_DATE}: merged into {target}" if target else f"Retired {RETIRE_DATE}."


def _prepend_retire_pointer(old_text: str, pointer: str) -> str:
    if old_text.startswith(pointer):
        return old_text
    if old_text.strip():
        return f"{pointer}\n\n{old_text}"
    return pointer


@dataclass
class PlannedOp:
    """A single planned Notion or local operation."""

    kind: str  # update | create | retire | temp_rename | drill_update | local_move | local_edit
    level: str  # topic | chapter | unit | drill | local
    code: str
    old_code: str | None = None
    page_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def op_key(self) -> str:
        return f"{self.kind}:{self.level}:{self.code}:{self.page_id or ''}"


@dataclass
class Refusal:
    """A page that the migration refused to retire."""

    code: str
    page_id: str
    reason: str


@dataclass
class PreFlightResult:
    """Results of pre-flight validation before any Notion or local write."""

    resolved_page_ids: dict[str, str]
    final_code_to_page: dict[str, str]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stray_relations: dict[str, dict[str, list[str]]] = field(default_factory=dict)


def _rt(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text[:1900]}}]


def _split_code(code: str) -> tuple[str, str | None, str | None]:
    """Return (Txx, Cyy, Uzz) parts from PRG-Txx[-Cyy[-Uzz]]."""
    parts = code.split("-")
    t = parts[1] if len(parts) > 1 else ""
    c = parts[2] if len(parts) > 2 else None
    u = parts[3] if len(parts) > 3 else None
    return t, c, u


def _block_text(block: dict) -> str:
    bt = block.get("type", "")
    inner = block.get(bt)
    if not isinstance(inner, dict):
        return ""
    rich = inner.get("rich_text")
    if not isinstance(rich, list):
        return ""
    return "".join(r.get("plain_text") or r.get("text", {}).get("content", "") for r in rich)


def has_learner_implementation_content(blocks: list[dict]) -> bool:
    """Return True if the 'My Implementation' section contains learner-written content."""
    in_section = False
    for b in blocks:
        bt = b.get("type", "")
        txt = _block_text(b).strip()
        if bt in ("heading_1", "heading_2", "heading_3"):
            if "my implementation" in txt.lower():
                in_section = True
                continue
            if in_section and bt in ("heading_1", "heading_2"):
                break
        if not in_section:
            continue
        if bt == "divider":
            continue
        if bt == "paragraph" and not txt and not b.get("has_children"):
            continue
        if bt == "to_do":
            if b.get("to_do", {}).get("checked"):
                return True
            # Unchecked template to_do items are not learner content.
            continue
        return True
    return False


def check_retire_safety(code: str, page: dict, blocks: list[dict]) -> str | None:
    """Return a refusal reason if a page must not be retired, else None."""
    props = page.get("properties", {})
    status = prop_val(props.get("Status"))
    if status in ("Done", "In progress"):
        return f"Status is {status!r}"
    if has_learner_implementation_content(blocks):
        return "My Implementation section has learner content"
    return None


def _target_properties(entry: dict, parent_ids: dict[str, str]) -> dict[str, Any]:
    """Build Notion properties dict for an active v2 Topic/Chapter/Unit entry."""
    level = entry["level"]
    code = entry["newCode"]
    t_part, c_part, u_part = _split_code(code)
    title_prop = TITLE_PROP_BY_LEVEL[level]
    props: dict[str, Any] = {
        title_prop: {"title": _rt(entry["title"])},
        "Full ID": {"rich_text": _rt(code)},
        "Topic ID": {"rich_text": _rt(t_part)},
        "Order": {"number": entry["order"]},
    }
    if level == "topic":
        if entry.get("objective"):
            props["Goal"] = {"rich_text": _rt(entry["objective"])}
    elif level == "chapter":
        props["Chapter ID"] = {"rich_text": _rt(c_part or "")}
        props["Priority"] = {"select": {"name": "Extended" if entry["extended"] else "Core"}}
        if entry.get("objective"):
            props["Objective"] = {"rich_text": _rt(entry["objective"])}
        if entry["parent"] and entry["parent"] in parent_ids:
            props["Topics"] = {"relation": [{"id": parent_ids[entry["parent"]]}]}
    elif level == "unit":
        props["Chapter ID"] = {"rich_text": _rt(c_part or "")}
        props["Unit ID"] = {"rich_text": _rt(u_part or "")}
        props["Priority"] = {"select": {"name": "Extended" if entry["extended"] else "Core"}}
        if entry.get("objective"):
            props["Learning Objective"] = {"rich_text": _rt(entry["objective"])}
        if entry.get("expectedOutput"):
            props["Expected Output"] = {"rich_text": _rt(entry["expectedOutput"])}
        topic_code = f"PRG-{t_part}"
        if topic_code in parent_ids:
            props["Learning Topics"] = {"relation": [{"id": parent_ids[topic_code]}]}
        if entry["parent"] and entry["parent"] in parent_ids:
            props["Learning Chapters"] = {"relation": [{"id": parent_ids[entry["parent"]]}]}
    return props


def _props_differ(current_props: dict, desired_props: dict) -> bool:
    """Return True if any property in desired_props differs from current_props."""
    for name, desired in desired_props.items():
        cur = current_props.get(name)
        if "title" in desired:
            want = "".join(x["text"]["content"] for x in desired["title"])
            if prop_text(cur) != want:
                return True
        elif "rich_text" in desired:
            want = "".join(x["text"]["content"] for x in desired["rich_text"])
            if prop_text(cur) != want:
                return True
        elif "number" in desired:
            if prop_val(cur) != desired["number"]:
                return True
        elif "select" in desired:
            if prop_val(cur) != desired["select"]["name"]:
                return True
        elif "status" in desired:
            if prop_val(cur) != desired["status"]["name"]:
                return True
        elif "relation" in desired:
            want_ids = {x["id"].replace("-", "") for x in desired["relation"]}
            cur_ids = {x.replace("-", "") for x in (prop_val(cur) or [])}
            if want_ids != cur_ids:
                return True
    return False


def order_renames_safely(renames: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """Order (page_id, current_code, target_code) so no target_code is occupied when written.

    Breaks cycles by inserting a temporary `TMP-<current_code>` step.
    """
    # Filter out no-op code renames (current_code == target_code)
    moving = [(pid, cur, tgt) for pid, cur, tgt in renames if cur != tgt]
    unchanged = [(pid, cur, tgt) for pid, cur, tgt in renames if cur == tgt]

    occupied_by: dict[str, str] = {cur: pid for pid, cur, _ in moving}
    pending: dict[str, tuple[str, str, str]] = {pid: (pid, cur, tgt) for pid, cur, tgt in moving}
    ordered: list[tuple[str, str, str]] = []

    while pending:
        # Find a move whose target is not currently occupied by any other pending page
        ready = [item for item in pending.values() if item[2] not in occupied_by or occupied_by[item[2]] == item[0]]
        if ready:
            ready.sort(key=lambda x: x[1])
            for pid, cur, tgt in ready:
                ordered.append((pid, cur, tgt))
                occupied_by.pop(cur, None)
                occupied_by[tgt] = pid
                pending.pop(pid)
        else:
            # Break cycle: move the lexicographically first pending item to TMP-<cur>
            pid, cur, tgt = min(pending.values(), key=lambda x: x[1])
            tmp_code = f"TMP-{cur}"
            ordered.append((pid, cur, tmp_code))
            occupied_by.pop(cur, None)
            occupied_by[tmp_code] = pid
            pending[pid] = (pid, tmp_code, tgt)

    return ordered + unchanged


def _entry_in_topic(entry: dict, topic: str | None) -> bool:
    if not topic:
        return True
    if entry["newCode"]:
        return entry["newCode"] == topic or entry["newCode"].startswith(topic + "-")
    return any(c == topic or c.startswith(topic + "-") for c in entry["oldCodes"])


def fetch_notion_prg_state(token: str) -> tuple[dict[str, dict], list[dict]]:
    """Read-only fetch of all PRG pages (Topics/Chapters/Units) and Drills from Notion."""
    pages_by_id: dict[str, dict] = {}
    for db_id in (TOPICS_DB, CHAPTERS_DB, UNITS_DB):
        for prefix in ("PRG-", "RETIRED-PRG-", "TMP-PRG-"):
            for page in query_all(db_id, token, {"property": "Full ID", "rich_text": {"starts_with": prefix}}):
                if not page.get("archived"):
                    pages_by_id[page["id"].replace("-", "")] = page
    drills = [p for p in query_all(DRILLS_DB, token) if not p.get("archived")]
    return pages_by_id, drills


def _resolve_page_ids(
    entries: list[dict],
    id_map: dict[str, dict],
    pages_by_id: dict[str, dict],
) -> tuple[dict[str, str], dict[str, dict]]:
    """Resolve active newCode -> Notion page_id and index live pages by Full ID."""
    old_code_pids = {id_map[oc]["id"] for e in entries for oc in e["oldCodes"] if oc in id_map}
    resolved_page_ids: dict[str, str] = {}
    for e in entries:
        nc = e["newCode"]
        if nc is None:
            continue
        if e["oldCodes"]:
            oc = e["oldCodes"][0]
            if oc in id_map and id_map[oc]["id"].replace("-", "") in pages_by_id:
                resolved_page_ids[nc] = id_map[oc]["id"]
            elif nc in id_map and id_map[nc]["id"].replace("-", "") in pages_by_id:
                resolved_page_ids[nc] = id_map[nc]["id"]
        elif nc in id_map and id_map[nc]["id"].replace("-", "") in pages_by_id:
            if id_map[nc]["id"] not in old_code_pids:
                resolved_page_ids[nc] = id_map[nc]["id"]

    by_full_id: dict[str, dict] = {}
    for page in pages_by_id.values():
        fid = prop_text(page.get("properties", {}).get("Full ID")).strip()
        if fid:
            by_full_id[fid] = page

    for e in entries:
        nc = e["newCode"]
        if nc and nc not in resolved_page_ids and nc in by_full_id:
            if by_full_id[nc]["id"] not in old_code_pids:
                resolved_page_ids[nc] = by_full_id[nc]["id"]

    return resolved_page_ids, by_full_id


def run_preflight(
    entries: list[dict],
    id_map: dict[str, dict],
    pages_by_id: dict[str, dict],
) -> PreFlightResult:
    """Validate final code->page uniqueness, unmapped PRG pages, and stray relations."""
    resolved_page_ids, by_full_id = _resolve_page_ids(entries, id_map, pages_by_id)
    final_code_to_page: dict[str, str] = {}
    page_to_final_code: dict[str, str] = {}
    errors: list[str] = []
    warnings: list[str] = []
    stray_relations: dict[str, dict[str, list[str]]] = {}

    for e in entries:
        nc = e["newCode"]
        if nc is None:
            continue
        if e["oldCodes"]:
            oc = e["oldCodes"][0]
            pid = (
                (id_map.get(oc) or {}).get("id")
                or (by_full_id.get(oc) or {}).get("id")
                or resolved_page_ids.get(nc)
                or f"<new:{nc}>"
            )
        else:
            pid = resolved_page_ids.get(nc) or f"<new:{nc}>"
        if nc in final_code_to_page and final_code_to_page[nc] != pid:
            errors.append(f"Duplicate final code {nc!r}: held by both {final_code_to_page[nc]} and {pid}")
        else:
            final_code_to_page[nc] = pid
        if not pid.startswith("<new:"):
            pid_norm = pid.replace("-", "")
            if pid_norm in page_to_final_code and page_to_final_code[pid_norm] != nc:
                errors.append(f"Page {pid} mapped to multiple final codes: {page_to_final_code[pid_norm]!r} and {nc!r}")
            else:
                page_to_final_code[pid_norm] = nc

    # Collect every page_id known to the migration map (primary, merged, retired, or already at newCode)
    mapped_pids_norm: set[str] = {pid.replace("-", "") for pid in resolved_page_ids.values()}
    for e in entries:
        for oc in e["oldCodes"]:
            if oc in id_map:
                mapped_pids_norm.add(id_map[oc]["id"].replace("-", ""))
            if oc in by_full_id:
                mapped_pids_norm.add(by_full_id[oc]["id"].replace("-", ""))

    id_map_pids_norm: set[str] = {
        v["id"].replace("-", "") for v in id_map.values() if isinstance(v, dict) and "id" in v
    }

    for pid_norm, page in sorted(pages_by_id.items()):
        props = page.get("properties", {})
        fid = prop_text(props.get("Full ID")).strip()
        if fid.startswith("RETIRED-"):
            continue
        if pid_norm not in mapped_pids_norm and (fid.startswith("PRG-") or fid.startswith("TMP-PRG-")):
            errors.append(f"Unmapped Notion page {page['id']} holds PRG code {fid!r} (title={get_title_text(props)!r})")
            continue
        if pid_norm in mapped_pids_norm:
            for rel_prop in RELATION_PROPS_CHECK:
                rel_ids = prop_val(props.get(rel_prop)) or []
                for rid in rel_ids:
                    rid_norm = rid.replace("-", "")
                    if rid_norm not in id_map_pids_norm and rid_norm not in mapped_pids_norm:
                        stray_relations.setdefault(pid_norm, {}).setdefault(rel_prop, []).append(rid)
                        warnings.append(
                            f"Stray relation on {fid or page['id']} ({page['id']}).{rel_prop} -> {rid} "
                            f"(not in id_map; will leave {rid} untouched and remove from {rel_prop})"
                        )

    return PreFlightResult(
        resolved_page_ids=resolved_page_ids,
        final_code_to_page=final_code_to_page,
        errors=errors,
        warnings=warnings,
        stray_relations=stray_relations,
    )


def plan_local_operations(
    entries: list[dict],
    root: Path = Path("."),
    topic: str | None = None,
) -> list[PlannedOp]:
    """Plan all local file renames and JSON/text updates."""
    unit_map = {old: e["newCode"] for e in entries if e["level"] == "unit" and e["newCode"] for old in e["oldCodes"]}
    chap_map = {old: e["newCode"] for e in entries if e["level"] == "chapter" and e["newCode"] for old in e["oldCodes"]}
    ops: list[PlannedOp] = []

    def in_scope(old_code: str, new_code: str | None = None) -> bool:
        if not topic:
            return True
        return (new_code or old_code).startswith(topic)

    # 1. Reasoning vaults
    vault_dir = root / "code_engine" / "reasoning_vault"
    if vault_dir.exists():
        for vp in sorted(vault_dir.glob("PRG-*.json")):
            old_chap = vp.stem
            new_chap = chap_map.get(old_chap, old_chap)
            if not in_scope(old_chap, new_chap):
                continue
            if new_chap != old_chap:
                ops.append(
                    PlannedOp(
                        kind="local_move",
                        level="local",
                        code=new_chap,
                        old_code=old_chap,
                        details={"src": str(vp), "dst": str(vault_dir / f"{new_chap}.json"), "update_unitCode": True},
                    )
                )

    # 2. Drills + progress + workspace
    drills_dir = root / "drills" / "data"
    if drills_dir.exists():
        for chap_dir in sorted(drills_dir.glob("PRG-*")):
            if not chap_dir.is_dir():
                continue
            old_chap = chap_dir.name
            new_chap = chap_map.get(old_chap, old_chap)
            if not in_scope(old_chap, new_chap):
                continue
            for df in sorted(chap_dir.glob("DRL-PRG-*.json")):
                old_did = df.stem
                new_did = old_did.replace(old_chap, new_chap, 1) if new_chap != old_chap else old_did
                if new_chap != old_chap:
                    ops.append(
                        PlannedOp(
                            kind="local_move",
                            level="local",
                            code=new_did,
                            old_code=old_did,
                            details={
                                "src": str(df),
                                "dst": str(drills_dir / new_chap / f"{new_did}.json"),
                                "old_chap": old_chap,
                                "new_chap": new_chap,
                                "unit_map": unit_map,
                            },
                        )
                    )
                    prog_src = root / "progress" / f"{old_did}.json"
                    if prog_src.exists():
                        ops.append(
                            PlannedOp(
                                kind="local_move",
                                level="local",
                                code=new_did,
                                old_code=old_did,
                                details={
                                    "src": str(prog_src),
                                    "dst": str(root / "progress" / f"{new_did}.json"),
                                    "old_chap": old_chap,
                                    "new_chap": new_chap,
                                },
                            )
                        )
                    ws_src = root / "drills" / "workspace" / old_did
                    if ws_src.exists():
                        ops.append(
                            PlannedOp(
                                kind="local_move",
                                level="local",
                                code=new_did,
                                old_code=old_did,
                                details={
                                    "src": str(ws_src),
                                    "dst": str(root / "drills" / "workspace" / new_did),
                                    "is_dir": True,
                                },
                            )
                        )

    # 3. Lab (LAB-PRG-T03-C01-01 -> LAB-PRG-T01-C04-02 per §8.2)
    if in_scope("PRG-T01", LAB_NEW_TOPIC):
        lab_src = root / "labs" / LAB_OLD_ID
        if lab_src.exists():
            ops.append(
                PlannedOp(
                    kind="local_move",
                    level="local",
                    code=LAB_NEW_ID,
                    old_code=LAB_OLD_ID,
                    details={
                        "src": str(lab_src),
                        "dst": str(root / "labs" / LAB_NEW_ID),
                        "is_dir": True,
                        "lab_rename": True,
                    },
                )
            )
        ref_src = root / "labs" / "_reference" / LAB_OLD_ID
        if ref_src.exists():
            ops.append(
                PlannedOp(
                    kind="local_move",
                    level="local",
                    code=LAB_NEW_ID,
                    old_code=LAB_OLD_ID,
                    details={
                        "src": str(ref_src),
                        "dst": str(root / "labs" / "_reference" / LAB_NEW_ID),
                        "is_dir": True,
                    },
                )
            )

    # 4. Templates (prg_t01_c03.py -> prg_t01_c04.py)
    tpl_src = root / "code_engine" / "templates" / "prg_t01_c03.py"
    if in_scope("PRG-T01", "PRG-T01") and tpl_src.exists():
        ops.append(
            PlannedOp(
                kind="local_move",
                level="local",
                code="PRG-T01-C04",
                old_code="PRG-T01-C03",
                details={
                    "src": str(tpl_src),
                    "dst": str(root / "code_engine" / "templates" / "prg_t01_c04.py"),
                    "replace": [("PRG-T01-C03", "PRG-T01-C04")],
                },
            )
        )

    # 5. Text/code references (CI workflow, docs, rules, scripts, tests)
    ci_file = root / ".github" / "workflows" / "ci.yml"
    if in_scope("PRG-T01", LAB_NEW_TOPIC) and ci_file.exists():
        txt = ci_file.read_text(encoding="utf-8")
        if LAB_OLD_ID in txt:
            ops.append(
                PlannedOp(
                    kind="local_edit",
                    level="local",
                    code=LAB_NEW_ID,
                    old_code=LAB_OLD_ID,
                    details={"path": str(ci_file), "replace": [(LAB_OLD_ID, LAB_NEW_ID)]},
                )
            )

    return ops


def _clean_stray_relations(
    desired: dict[str, Any],
    page: dict | None,
    stray_for_page: dict[str, list[str]],
) -> dict[str, Any]:
    """Remove non-id_map stray relation IDs from a mapped page's relations without touching the stray pages."""
    if not page or not stray_for_page:
        return desired
    props = page.get("properties", {})
    for rel_prop, stray_ids in stray_for_page.items():
        if rel_prop in desired:
            continue
        cur_ids = prop_val(props.get(rel_prop)) or []
        stray_set = {s.replace("-", "") for s in stray_ids}
        cleaned = [rid for rid in cur_ids if rid.replace("-", "") not in stray_set]
        desired[rel_prop] = {"relation": [{"id": rid} for rid in cleaned]}
    return desired


def build_migration_plan(
    entries: list[dict],
    id_map: dict[str, dict],
    pages_by_id: dict[str, dict],
    drills: list[dict],
    token: str,
    topic: str | None = None,
    preflight: PreFlightResult | None = None,
) -> tuple[list[PlannedOp], list[Refusal]]:
    """Build an ordered, collision-free migration plan and collect any retire refusals."""
    scoped = [e for e in entries if _entry_in_topic(e, topic)]
    if preflight is None:
        preflight = run_preflight(entries, id_map, pages_by_id)
    resolved_page_ids = preflight.resolved_page_ids
    _, by_full_id = _resolve_page_ids(entries, id_map, pages_by_id)

    ops: list[PlannedOp] = []
    refusals: list[Refusal] = []

    # Collect renames (for collision-safe ordering) and retires
    renames: list[tuple[str, str, str]] = []
    entry_by_pid: dict[str, dict] = {}
    retire_items: list[tuple[str, str, str | None]] = []  # (page_id, old_code, target_code)

    for e in scoped:
        if e["action"] == "retire":
            oc = e["oldCodes"][0]
            pid = (id_map.get(oc) or {}).get("id") or (by_full_id.get(oc) or {}).get("id")
            if pid:
                retire_items.append((pid, oc, e.get("retireTarget")))
            continue

        nc = e["newCode"]
        assert nc is not None
        if e["oldCodes"]:
            oc = e["oldCodes"][0]
            pid = (id_map.get(oc) or {}).get("id") or (by_full_id.get(oc) or {}).get("id") or resolved_page_ids.get(nc)
            if pid:
                page = pages_by_id.get(pid.replace("-", ""))
                cur_fid = prop_text(page.get("properties", {}).get("Full ID")).strip() if page else oc
                renames.append((pid, cur_fid, nc))
                entry_by_pid[pid] = e
            for merged_oc in e["oldCodes"][1:]:
                m_pid = (id_map.get(merged_oc) or {}).get("id") or (by_full_id.get(merged_oc) or {}).get("id")
                if m_pid:
                    retire_items.append((m_pid, merged_oc, nc))

    # 1. Check retire safety and plan retires first (vacates old Full IDs)
    for pid, oc, target in retire_items:
        page = pages_by_id.get(pid.replace("-", ""))
        if not page:
            continue
        cur_fid = prop_text(page.get("properties", {}).get("Full ID")).strip()
        if cur_fid == f"RETIRED-{oc}":
            continue  # already retired (idempotent)
        blocks = get_all_blocks(pid, token)
        reason = check_retire_safety(oc, page, blocks)
        if reason:
            refusals.append(Refusal(code=oc, page_id=pid, reason=reason))
            continue
        level = "topic" if oc.count("-") == 1 else ("chapter" if oc.count("-") == 2 else "unit")
        props = page.get("properties", {})
        old_title = get_title_text(props)
        obj_prop = OBJECTIVE_PROP_BY_LEVEL[level]
        pointer = _retire_pointer(target or "")
        ops.append(
            PlannedOp(
                kind="retire",
                level=level,
                code=f"RETIRED-{oc}",
                old_code=oc,
                page_id=pid,
                details={
                    "target": target or "",
                    "old_title": old_title,
                    "new_title": _retire_title(old_title),
                    "objective_prop": obj_prop,
                    "pointer": pointer,
                    "cleared_relations": list(PARENT_RELATIONS_BY_LEVEL[level]),
                },
            )
        )

    # 2. Order renames safely (with TMP- cycle-breaking)
    ordered_renames = order_renames_safely(renames)
    for pid, cur_fid, tgt_fid in ordered_renames:
        if tgt_fid.startswith("TMP-"):
            e = entry_by_pid[pid]
            ops.append(
                PlannedOp(
                    kind="temp_rename",
                    level=e["level"],
                    code=tgt_fid,
                    old_code=cur_fid,
                    page_id=pid,
                    details={"title": e["title"]},
                )
            )
        else:
            e = entry_by_pid[pid]
            page = pages_by_id.get(pid.replace("-", ""))
            desired = _target_properties(e, resolved_page_ids)
            desired = _clean_stray_relations(desired, page, preflight.stray_relations.get(pid.replace("-", ""), {}))
            if page and not _props_differ(page.get("properties", {}), desired):
                continue  # already up-to-date (idempotent)
            ops.append(
                PlannedOp(
                    kind="update",
                    level=e["level"],
                    code=e["newCode"],
                    old_code=e["oldCodes"][0],
                    page_id=pid,
                    details={"entry": e, "desired_props": desired},
                )
            )

    # 3. Creates (new entries & second half of split) AFTER renames
    vacated_pids = {pid for pid, _, _ in renames} | {pid for pid, _, _ in retire_items}
    for e in scoped:
        if e["oldCodes"]:
            continue
        nc = e["newCode"]
        assert nc is not None
        existing_page = by_full_id.get(nc)
        if existing_page and existing_page["id"] not in vacated_pids:
            desired = _target_properties(e, resolved_page_ids)
            if _props_differ(existing_page.get("properties", {}), desired):
                ops.append(
                    PlannedOp(
                        kind="update",
                        level=e["level"],
                        code=nc,
                        old_code=None,
                        page_id=existing_page["id"],
                        details={"entry": e, "desired_props": desired},
                    )
                )
            continue
        ops.append(
            PlannedOp(
                kind="create",
                level=e["level"],
                code=nc,
                old_code=e.get("splitFrom"),
                page_id=None,
                details={"entry": e, "desired_props": _target_properties(e, resolved_page_ids)},
            )
        )

    # 4. Drills DB updates
    chap_map = {old: e["newCode"] for e in entries if e["level"] == "chapter" and e["newCode"] for old in e["oldCodes"]}
    for d in drills:
        props = d.get("properties", {})
        did = prop_text(props.get("Drill ID")).strip()
        if not did.startswith("DRL-PRG-"):
            continue
        m_c = re.match(r"DRL-(PRG-T\d{2}-C\d{2})-\d{2}$", did)
        if not m_c:
            continue
        old_chap = m_c.group(1)
        new_chap = chap_map.get(old_chap, old_chap)
        if topic and not new_chap.startswith(topic):
            continue
        if new_chap == old_chap:
            continue
        new_did = did.replace(old_chap, new_chap, 1)
        new_topic = new_chap.rsplit("-", 1)[0]
        new_path = f"drills/data/{new_chap}/{new_did}.json"
        ops.append(
            PlannedOp(
                kind="drill_update",
                level="drill",
                code=new_did,
                old_code=did,
                page_id=d["id"],
                details={
                    "new_path": new_path,
                    "new_topic": new_topic,
                    "new_chap": new_chap,
                    "topic_id": resolved_page_ids.get(new_topic),
                    "chap_id": resolved_page_ids.get(new_chap),
                },
            )
        )

    return ops, refusals


def _throttled_request(method: str, endpoint: str, token: str, payload: dict | None = None) -> dict:
    _throttle()
    return notion_request(method, endpoint, token, payload)


def _write_log(log_path: Path, log_records: list[dict]) -> None:
    log_path.write_text(json.dumps(log_records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_plan(
    ops: list[PlannedOp],
    local_ops: list[PlannedOp],
    token: str,
    entries: list[dict],
    id_map: dict[str, dict],
    resume_log: Path | None = None,
) -> tuple[list[dict], Path]:
    """Execute planned Notion + local operations with per-op checkpointing and write a rollback log."""
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    if resume_log is not None:
        log_path = resume_log
        log_records: list[dict] = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        log_path = MIGRATIONS_DIR / f"prg_v2_{ts}.json"
        log_records = []

    completed_keys: set[str] = {r["op_key"] for r in log_records if "op_key" in r}
    created_ids: dict[str, str] = {
        r["code"]: r["page_id"] for r in log_records if r.get("kind") == "create" and "code" in r and "page_id" in r
    }

    def _checkpoint(rec: dict[str, Any]) -> None:
        log_records.append(rec)
        _write_log(log_path, log_records)

    total_notion = len(ops)
    for idx, op in enumerate(ops, 1):
        okey = op.op_key
        if okey in completed_keys:
            print(f"[{idx}/{total_notion}] SKIP (resumed) {op.kind} {op.code}", flush=True)
            continue
        label = f"{op.old_code} -> {op.code}" if op.old_code else op.code
        print(f"[{idx}/{total_notion}] {op.kind.upper()} {label}", flush=True)

        if op.kind == "retire":
            assert op.page_id is not None
            page = _throttled_request("GET", f"pages/{op.page_id}", token)
            old_props = page.get("properties", {})
            title_prop = TITLE_PROP_BY_LEVEL[op.level]
            obj_prop = OBJECTIVE_PROP_BY_LEVEL[op.level]
            old_title = get_title_text(old_props)
            new_title = _retire_title(old_title)
            old_obj = prop_text(old_props.get(obj_prop))
            target = op.details.get("target", "")
            pointer = _retire_pointer(target)
            new_obj = _prepend_retire_pointer(old_obj, pointer)
            old_relations: dict[str, list[str]] = {}
            patch: dict[str, Any] = {
                "Full ID": {"rich_text": _rt(op.code)},
                title_prop: {"title": _rt(new_title)},
                obj_prop: {"rich_text": _rt(new_obj)},
            }
            for rel_prop in PARENT_RELATIONS_BY_LEVEL[op.level]:
                old_relations[rel_prop] = list(prop_val(old_props.get(rel_prop)) or [])
                patch[rel_prop] = {"relation": []}
            _throttled_request("PATCH", f"pages/{op.page_id}", token, {"properties": patch})
            _checkpoint(
                {
                    "op_key": okey,
                    "kind": "retire",
                    "page_id": op.page_id,
                    "level": op.level,
                    "old_full_id": op.old_code,
                    "new_full_id": op.code,
                    "target": target,
                    "old_title": old_title,
                    "objective_prop": obj_prop,
                    "old_objective": old_obj,
                    "old_relations": old_relations,
                }
            )
        elif op.kind == "temp_rename":
            assert op.page_id is not None
            page = _throttled_request("GET", f"pages/{op.page_id}", token)
            old_fid = prop_text(page.get("properties", {}).get("Full ID"))
            _throttled_request(
                "PATCH", f"pages/{op.page_id}", token, {"properties": {"Full ID": {"rich_text": _rt(op.code)}}}
            )
            _checkpoint({"op_key": okey, "kind": "temp_rename", "page_id": op.page_id, "old_full_id": old_fid})
        elif op.kind == "update":
            assert op.page_id is not None
            page = _throttled_request("GET", f"pages/{op.page_id}", token)
            old_props = copy.deepcopy(page.get("properties", {}))
            desired = dict(op.details["desired_props"])
            # Resolve any newly created parent IDs
            e = op.details["entry"]
            if e["level"] == "unit" and e["parent"] in created_ids:
                desired["Learning Chapters"] = {"relation": [{"id": created_ids[e["parent"]]}]}
            _throttled_request("PATCH", f"pages/{op.page_id}", token, {"properties": desired})
            update_rec: dict[str, Any] = {
                "op_key": okey,
                "kind": "update",
                "page_id": op.page_id,
                "level": op.level,
                "code": op.code,
                "old_properties": old_props,
            }
            if len(e["oldCodes"]) > 1:
                update_rec["merged_from"] = e["oldCodes"][1:]
            _checkpoint(update_rec)
        elif op.kind == "create":
            e = op.details["entry"]
            desired = dict(op.details["desired_props"])
            if e["level"] == "unit" and e["parent"] in created_ids:
                desired["Learning Chapters"] = {"relation": [{"id": created_ids[e["parent"]]}]}
            res = _throttled_request(
                "POST",
                "pages",
                token,
                {"parent": {"database_id": DB_BY_LEVEL[op.level]}, "properties": desired},
            )
            created_ids[op.code] = res["id"]
            _checkpoint({"op_key": okey, "kind": "create", "page_id": res["id"], "code": op.code})
        elif op.kind == "drill_update":
            assert op.page_id is not None
            page = _throttled_request("GET", f"pages/{op.page_id}", token)
            old_props = copy.deepcopy(page.get("properties", {}))
            patch = {
                "Drill ID": {"rich_text": _rt(op.code)},
                "Local File Path": {"rich_text": _rt(op.details["new_path"])},
            }
            if op.details.get("topic_id"):
                patch["Topics"] = {"relation": [{"id": op.details["topic_id"]}]}
            if op.details.get("chap_id"):
                patch["Chapters"] = {"relation": [{"id": op.details["chap_id"]}]}
            _throttled_request("PATCH", f"pages/{op.page_id}", token, {"properties": patch})
            _checkpoint({"op_key": okey, "kind": "drill_update", "page_id": op.page_id, "old_properties": old_props})

    # Regenerate id_map.json once, only after all Notion ops succeeded
    print("Rebuilding id_map.json from Notion...", flush=True)
    new_id_map = rebuild_id_map(token, id_map)
    save_id_map(new_id_map, ID_MAP_PATH)

    # Apply local file operations after id_map regeneration
    total_local = len(local_ops)
    for idx, lop in enumerate(local_ops, 1):
        okey = lop.op_key
        if okey in completed_keys:
            print(f"[local {idx}/{total_local}] SKIP (resumed) {lop.kind} {lop.code}", flush=True)
            continue
        print(f"[local {idx}/{total_local}] {lop.kind.upper()} {lop.code}", flush=True)
        if lop.kind == "local_move":
            src = Path(lop.details["src"])
            dst = Path(lop.details["dst"])
            if not src.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            if lop.details.get("is_dir"):
                shutil.move(str(src), str(dst))
                if lop.details.get("lab_rename"):
                    _update_lab_files(dst)
                _checkpoint({"op_key": okey, "kind": "local_move", "src": str(src), "dst": str(dst), "is_dir": True})
            else:
                old_text = src.read_text(encoding="utf-8")
                new_text = _transform_local_file(old_text, lop)
                dst.write_text(new_text, encoding="utf-8")
                if dst != src:
                    src.unlink()
                _checkpoint(
                    {
                        "op_key": okey,
                        "kind": "local_move",
                        "src": str(src),
                        "dst": str(dst),
                        "old_text": old_text,
                        "is_dir": False,
                    }
                )
        elif lop.kind == "local_edit":
            p = Path(lop.details["path"])
            if not p.exists():
                continue
            old_text = p.read_text(encoding="utf-8")
            new_text = old_text
            for a, b in lop.details["replace"]:
                new_text = new_text.replace(a, b)
            p.write_text(new_text, encoding="utf-8")
            _checkpoint({"op_key": okey, "kind": "local_edit", "path": str(p), "old_text": old_text})

    _write_log(log_path, log_records)
    return log_records, log_path


def _transform_local_file(text: str, op: PlannedOp) -> str:
    if op.details.get("update_unitCode"):
        data = json.loads(text)
        data["unitCode"] = op.code
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if "unit_map" in op.details:
        data = json.loads(text)
        old_chap = op.details["old_chap"]
        data["unitCode"] = op.details["new_chap"]
        umap = op.details["unit_map"]
        for prob in data.get("problems", []):
            u = prob.get("unit")
            if u and f"{old_chap}-{u}" in umap:
                prob["unit"] = umap[f"{old_chap}-{u}"].rsplit("-", 1)[-1]
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if "old_chap" in op.details and "new_chap" in op.details:
        data = json.loads(text)
        data["drillId"] = op.code
        data["unitCode"] = op.details["new_chap"]
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    for a, b in op.details.get("replace", []):
        text = text.replace(a, b)
    return text


def _update_lab_files(lab_dir: Path) -> None:
    cfg_path = lab_dir / "lab.config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["labId"] = LAB_NEW_ID
        cfg["unitCode"] = LAB_NEW_UNIT
        cfg["chapterCode"] = LAB_NEW_CHAPTER
        cfg["topicCode"] = LAB_NEW_TOPIC
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pkg_path = lab_dir / "package.json"
    if pkg_path.exists():
        txt = pkg_path.read_text(encoding="utf-8")
        txt = txt.replace(LAB_OLD_ID.lower(), LAB_NEW_ID.lower()).replace(LAB_OLD_ID, LAB_NEW_ID)
        pkg_path.write_text(txt, encoding="utf-8")


def _restore_props_payload(old_props: dict) -> dict[str, Any]:
    """Convert stored Notion GET properties back into a PATCH properties payload."""
    patch: dict[str, Any] = {}
    for name, val in old_props.items():
        ptype = val.get("type")
        if ptype == "title":
            patch[name] = {"title": _rt(prop_text(val))}
        elif ptype == "rich_text":
            patch[name] = {"rich_text": _rt(prop_text(val))}
        elif ptype == "number":
            patch[name] = {"number": val.get("number")}
        elif ptype == "select" and val.get("select"):
            patch[name] = {"select": {"name": val["select"]["name"]}}
        elif ptype == "status" and val.get("status"):
            patch[name] = {"status": {"name": val["status"]["name"]}}
        elif ptype == "relation":
            patch[name] = {"relation": [{"id": r["id"]} for r in val.get("relation", [])]}
    return patch


def rollback_from_log(log_path: Path, token: str, dry_run: bool = False) -> list[str]:
    """Rollback Notion and local changes recorded in a migration log."""
    records = json.loads(log_path.read_text(encoding="utf-8"))
    actions: list[str] = []
    for rec in reversed(records):
        kind = rec["kind"]
        if kind == "create":
            actions.append(f"rollback create (archive): {rec['code']} ({rec['page_id']})")
            if not dry_run:
                _throttled_request("PATCH", f"pages/{rec['page_id']}", token, {"archived": True})
        elif kind in ("update", "drill_update"):
            actions.append(f"rollback {kind}: {rec['page_id']}")
            if not dry_run:
                _throttled_request(
                    "PATCH",
                    f"pages/{rec['page_id']}",
                    token,
                    {"properties": _restore_props_payload(rec["old_properties"])},
                )
        elif kind == "temp_rename":
            actions.append(f"rollback temp_rename: {rec['page_id']} -> {rec['old_full_id']}")
            if not dry_run:
                _throttled_request(
                    "PATCH",
                    f"pages/{rec['page_id']}",
                    token,
                    {"properties": {"Full ID": {"rich_text": _rt(rec["old_full_id"])}}},
                )
        elif kind == "retire":
            actions.append(f"rollback retire: {rec['page_id']} -> {rec['old_full_id']}")
            if not dry_run:
                title_prop = TITLE_PROP_BY_LEVEL[rec["level"]]
                obj_prop = rec.get("objective_prop") or OBJECTIVE_PROP_BY_LEVEL[rec["level"]]
                patch: dict[str, Any] = {
                    "Full ID": {"rich_text": _rt(rec["old_full_id"])},
                    title_prop: {"title": _rt(rec["old_title"])},
                    obj_prop: {"rich_text": _rt(rec.get("old_objective", ""))},
                }
                for rel_prop, rel_ids in rec.get("old_relations", {}).items():
                    patch[rel_prop] = {"relation": [{"id": rid} for rid in rel_ids]}
                _throttled_request("PATCH", f"pages/{rec['page_id']}", token, {"properties": patch})
        elif kind == "local_move":
            actions.append(f"rollback local_move: {rec['dst']} -> {rec['src']}")
            if not dry_run:
                src, dst = Path(rec["src"]), Path(rec["dst"])
                if rec.get("is_dir") and dst.exists():
                    shutil.move(str(dst), str(src))
                elif not rec.get("is_dir"):
                    src.parent.mkdir(parents=True, exist_ok=True)
                    src.write_text(rec["old_text"], encoding="utf-8")
                    if dst != src and dst.exists():
                        dst.unlink()
        elif kind == "local_edit":
            actions.append(f"rollback local_edit: {rec['path']}")
            if not dry_run:
                Path(rec["path"]).write_text(rec["old_text"], encoding="utf-8")
    return actions


def format_preflight_report(preflight: PreFlightResult) -> str:
    """Format pre-flight check summary, errors, and warnings."""
    status = "ABORT" if preflight.errors else "PASS"
    lines = [
        "--- Pre-Flight Check ---",
        f"Status: {status}",
        f"Final code->page entries: {len(preflight.final_code_to_page)}",
        f"Errors: {len(preflight.errors)}",
        f"Warnings (stray relations): {len(preflight.warnings)}",
    ]
    for err in preflight.errors:
        lines.append(f"  [ERROR] {err}")
    for warn in preflight.warnings:
        lines.append(f"  [WARN]  {warn}")
    return "\n".join(lines) + "\n"


def format_dry_run_report(
    entries: list[dict],
    ops: list[PlannedOp],
    local_ops: list[PlannedOp],
    refusals: list[Refusal],
    topic: str | None = None,
    preflight: PreFlightResult | None = None,
) -> str:
    """Format a readable dry-run summary + detailed operation list."""
    scoped = [e for e in entries if _entry_in_topic(e, topic)]
    by_action: dict[str, int] = {}
    by_topic: dict[str, dict[str, int]] = {}
    for e in scoped:
        act = e["action"]
        by_action[act] = by_action.get(act, 0) + 1
        t = (e["newCode"] or e["oldCodes"][0]).split("-")[1]
        t_key = f"PRG-{t}"
        by_topic.setdefault(t_key, {})
        by_topic[t_key][act] = by_topic[t_key].get(act, 0) + 1

    op_counts: dict[str, int] = {}
    for op in ops:
        op_counts[op.kind] = op_counts.get(op.kind, 0) + 1

    lines = [
        "=== PRG Curriculum v2 Migration — DRY-RUN ===",
        f"Scope: {topic or 'ALL (PRG-T00..PRG-T10)'}",
        f"Map entries in scope: {len(scoped)}",
        f"Counts by map action: {json.dumps(by_action, sort_keys=True)}",
        f"Planned Notion ops: {json.dumps(op_counts, sort_keys=True)}",
        f"Planned Local ops: {len(local_ops)}",
        f"Refusals: {len(refusals)}",
        "",
        "--- Counts per Topic ---",
    ]
    for t_key in sorted(by_topic):
        lines.append(f"  {t_key}: {json.dumps(by_topic[t_key], sort_keys=True)}")

    if preflight is not None:
        lines.append("")
        lines.append(format_preflight_report(preflight).rstrip("\n"))

    if refusals:
        lines.append("")
        lines.append("--- REFUSALS (Aborted Pages) ---")
        for r in refusals:
            lines.append(f"  REFUSE {r.code} ({r.page_id}): {r.reason}")

    lines.append("")
    lines.append("--- Planned Notion Operations ---")
    for op in ops:
        if op.kind == "retire":
            rels = ", ".join(f"{r}=[]" for r in op.details.get("cleared_relations", [])) or "none"
            obj_prop = op.details.get("objective_prop", "")
            pointer = op.details.get("pointer", "")
            lines.append(
                f"  [RETIRE] {op.old_code} -> {op.code} ({op.level}, page={op.page_id}) | "
                f"title={op.details.get('new_title')!r} | clear({rels}) | "
                f"{obj_prop}+={pointer!r} | Status=unchanged"
            )
        elif op.kind == "temp_rename":
            lines.append(f"  [TMP]    {op.old_code} -> {op.code} (page={op.page_id})")
        elif op.kind == "update":
            e = op.details["entry"]
            lines.append(f"  [UPDATE] {op.old_code} -> {op.code} ({e['level']}) | {e['title']} (page={op.page_id})")
        elif op.kind == "create":
            e = op.details["entry"]
            lines.append(f"  [CREATE] {op.code} ({e['level']}) | {e['title']}")
        elif op.kind == "drill_update":
            lines.append(f"  [DRILL]  {op.old_code} -> {op.code} ({op.details['new_path']})")

    lines.append("")
    lines.append("--- Planned Local Operations ---")
    for lop in local_ops:
        if lop.kind == "local_move":
            lines.append(f"  [MOVE]   {lop.details['src']} -> {lop.details['dst']}")
        elif lop.kind == "local_edit":
            lines.append(f"  [EDIT]   {lop.details['path']} ({lop.old_code} -> {lop.code})")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m scripts.prg_migrate", description=__doc__.split("\n\n")[0])
    ap.add_argument("--topic", help="Scope to a single topic (dry-run/reading only).")
    ap.add_argument(
        "--all", action="store_true", help="Run the whole migration across all topics (required with --apply)."
    )
    ap.add_argument("--apply", action="store_true", help="Apply changes to Notion and local files.")
    ap.add_argument(
        "--i-have-reviewed-the-dry-run",
        action="store_true",
        help="Explicit confirmation required to run with --apply.",
    )
    ap.add_argument("--resume", metavar="LOG", help="Resume an interrupted --apply run from a migration log JSON file.")
    ap.add_argument("--rollback", metavar="LOG", help="Rollback changes using a migration log JSON file.")
    args = ap.parse_args(argv)

    if args.apply and not args.rollback:
        if args.topic:
            print("Error: --topic is for dry-run/reading only; use --all with --apply.", file=sys.stderr)
            return 2
        if not args.all:
            print("Error: --apply requires --all (whole migration in one run).", file=sys.stderr)
            return 2
    if args.apply and not args.i_have_reviewed_the_dry_run:
        print("Error: --apply requires --i-have-reviewed-the-dry-run.", file=sys.stderr)
        return 2

    token = require_token(load_env().get("NOTION_TOKEN"))

    if args.rollback:
        actions = rollback_from_log(Path(args.rollback), token, dry_run=not args.apply)
        for act in actions:
            print(act)
        return 0

    entries = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    id_map = json.loads(ID_MAP_PATH.read_text(encoding="utf-8"))
    pages_by_id, drills = fetch_notion_prg_state(token)
    preflight = run_preflight(entries, id_map, pages_by_id)
    ops, refusals = build_migration_plan(
        entries, id_map, pages_by_id, drills, token, topic=args.topic, preflight=preflight
    )
    local_ops = plan_local_operations(entries, Path("."), topic=args.topic)

    if not args.apply:
        print(format_dry_run_report(entries, ops, local_ops, refusals, topic=args.topic, preflight=preflight), end="")
        return 0

    print(format_preflight_report(preflight), end="", flush=True)
    if preflight.errors:
        print("Aborting --apply due to pre-flight errors. Zero writes performed.", file=sys.stderr)
        return 1

    resume_log = Path(args.resume) if args.resume else None
    records, log_path = apply_plan(ops, local_ops, token, entries, id_map, resume_log=resume_log)
    print(f"Applied {len(records)} operations. Rollback log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
