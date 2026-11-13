# -*- coding: utf-8 -*-
"""
RETIRED: rules are no longer synced to Notion (local rules/*.md are the only copy).
Kept for reference. Former Local-First Auto-Sync to Notion:
Synchronizes modular rules from local Markdown files (`rules/*.md`)
into Notion Master Rules Hub and its 7 specialized Sub-Pages.
"""

import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

from notion_sync import blocks as _blocks
from notion_sync.blocks import (
    callout_block,
    divider_block,
    h2,
    mention_page,
    p_block,
    replace_page_blocks,
    rt,
    validate_blocks_clean,
)
from notion_sync.client import get_all_blocks, load_env, notion_request, require_token
from md_blocks import md_to_notion_blocks
from page_audit import audit_page

# Support double-backtick code spans in markdown (e.g. in 00_core.md)
_blocks.INNER_TOKEN_RE = re.compile(r"(\[\[[A-Z0-9\-]+\]\]|\$[^\$]+\$|``(?:.+?)``|`[^`]+`)")
orig_parse_rt = _blocks.parse_rt


def _safe_parse_rt(text, id_map):
    bold_chunks = _blocks.BOLD_SPLIT_RE.split(text)
    out = []
    for chunk in bold_chunks:
        if not chunk:
            continue
        is_bold = False
        inner_str = chunk
        if chunk.startswith("**") and chunk.endswith("**") and len(chunk) > 4:
            is_bold = True
            inner_str = chunk[2:-2]

        parts = _blocks.INNER_TOKEN_RE.split(inner_str)
        for p in parts:
            if not p:
                continue
            if p.startswith("[[") and p.endswith("]]"):
                fid = p[2:-2]
                if fid not in id_map:
                    raise ValueError(f"Unknown Full ID in [[{fid}]] within text: {text}")
                out.append(_blocks.mention_page(id_map[fid]["id"], bold=is_bold))
            elif p.startswith("$") and p.endswith("$") and len(p) > 2:
                out.append(_blocks.eq_inline(p[1:-1], bold=is_bold))
            elif p.startswith("``") and p.endswith("``") and len(p) >= 4:
                out.append(_blocks.rt(p[2:-2].strip(), bold=is_bold, code=True))
            elif p.startswith("`") and p.endswith("`") and len(p) > 2:
                out.append(_blocks.rt(p[1:-1], bold=is_bold, code=True))
            else:
                if "[[" in p or "]]" in p:
                    raise ValueError(f"Unparsed bracket token in '{p}' within text: {text}")
                out.append(_blocks.rt(p, bold=is_bold))
    return out if out else [_blocks.rt("")]


_blocks.parse_rt = _safe_parse_rt

MASTER_RULES_PID = "40c3818f-8ba0-8002-92f1-e971793125e3"
RULES_DIR = "rules"
RULES_MAP_FILE = os.path.join("archive", "rules_map.json")  # rules sync retired; kept for reference

SUB_MODULES = [
    {
        "key": "01_ARCH",
        "title": "01_ARCH — Learning Architecture, Database Relations & Progress Tracking",
        "file": os.path.join(RULES_DIR, "01_arch.md"),
        "desc": "Topic ➔ Chapter ➔ Unit hierarchy, database properties & completeness, Status vs. Mastery (0-4), inline @page mentions.",
    },
    {
        "key": "02_PEDAGOGY",
        "title": "02_PEDAGOGY — Curriculum Design, Active Recall & Practice Guides",
        "file": os.path.join(RULES_DIR, "02_pedagogy.md"),
        "desc": "Reference structures, 4-tier Practice Guides (Anti-Dump rule), Active Recall toggles, learner's personal workspace & mistake log.",
    },
    {
        "key": "03_STEM",
        "title": "03_STEM — Mathematics, Physics & Parametric Visual Standards",
        "file": os.path.join(RULES_DIR, "03_stem.md"),
        "desc": "Vertical LaTeX derivations, KaTeX formatting, parametric SVG educational diagrams, native Notion file upload API.",
    },
    {
        "key": "04_CODE",
        "title": "04_CODE — Programming Practice, Test Suites & Terminal Labs",
        "file": os.path.join(RULES_DIR, "04_code.md"),
        "desc": "Next.js Practice Studio schemas, 5-tier milestone taxonomy, 8-step authoring pipeline, terminal telemetry engine (submit_lab.py).",
    },
    {
        "key": "05_QA",
        "title": "05_QA — Implementation Workflow, Quality Assurance & Audit Protocol",
        "file": os.path.join(RULES_DIR, "05_qa.md"),
        "desc": "10-step implementation workflow, 5-dimension QA checklist, scripted Notion API audit, implementation reporting.",
    },
    {
        "key": "06_TEMPLATE_CONTRACT",
        "title": "06_TEMPLATE_CONTRACT — Problem Template & Quality Gate Engineering Contract",
        "file": os.path.join(RULES_DIR, "06_template_contract.md"),
        "desc": "L1–L4 taxonomy, trap provenance & operational derivations, machine verification gates G1–G6, verification levels, reporting protocol.",
    },
    {
        "key": "07_PROBLEM_GENERATION",
        "title": "07_PROBLEM_GENERATION — Drill Composition, Weak-Spot Targeting, Progression & AI-Written Problem Verification",
        "file": os.path.join(RULES_DIR, "07_problem_generation.md"),
        "desc": "Drill composition (sequence of drills), weak-spot targeting (trapMatched signals), progression rules, AI-written problem verification (V1–V3).",
    },
]


def load_rules_map(rules_map_path=RULES_MAP_FILE):
    """Loads existing rules_map.json safely."""
    if os.path.exists(rules_map_path):
        try:
            with open(rules_map_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def get_or_create_sub_pages(master_pid, token, dry_run=False, rules_map_path=RULES_MAP_FILE):
    """
    Verifies or creates Notion Sub-Pages under Master Rule Hub.
    In live mode: merges results into rules_map.json (preserving all existing entries).
    In dry-run mode: returns in-memory merged map without calling Notion API or writing rules_map.json.
    """
    existing_rules_map = load_rules_map(rules_map_path)
    rules_map = dict(existing_rules_map)
    rules_map["MASTER"] = master_pid
    rules_map["00_CORE"] = os.path.join(RULES_DIR, "00_core.md")

    if dry_run:
        # In dry run mode: no API calls and no file writes
        for mod in SUB_MODULES:
            key = mod["key"]
            target_title = mod["title"]
            existing_entry = rules_map.get(key)
            pid = None
            if isinstance(existing_entry, dict):
                pid = existing_entry.get("id")
                rules_map[key] = {
                    **existing_entry,
                    "title": target_title,
                    "file": mod["file"],
                }
                if pid:
                    rules_map[key]["id"] = pid
            else:
                rules_map[key] = {
                    "id": pid,
                    "title": target_title,
                    "file": mod["file"],
                }
        return rules_map

    master_blocks = get_all_blocks(master_pid, token)
    existing_children = {}
    for b in master_blocks:
        if b["type"] == "child_page":
            title = b["child_page"].get("title", "")
            existing_children[title] = b["id"]

    print("\nVerifying/Creating Sub-Pages under Master Rule Hub...")
    for mod in SUB_MODULES:
        key = mod["key"]
        target_title = mod["title"]
        pid = None
        for title, cid in existing_children.items():
            if target_title == title or key in title:
                pid = cid
                break

        if not pid:
            print(f"  Creating new Notion Child Page for: {target_title}...")
            payload = {
                "parent": {"page_id": master_pid},
                "properties": {"title": [{"type": "text", "text": {"content": target_title}}]},
            }
            res = notion_request("POST", "pages", token, payload)
            pid = res["id"]
            print(f"    Created with ID: {pid}")
        else:
            print(f"  Found existing Sub-Page for {key}: {pid}")

        existing_entry = rules_map.get(key)
        if isinstance(existing_entry, dict):
            rules_map[key] = {
                **existing_entry,
                "id": pid,
                "title": target_title,
                "file": mod["file"],
            }
        else:
            rules_map[key] = {
                "id": pid,
                "title": target_title,
                "file": mod["file"],
            }

    with open(rules_map_path, "w", encoding="utf-8") as f:
        json.dump(rules_map, f, indent=2, ensure_ascii=False)
    print(f"Saved merged rules map to {rules_map_path}")
    return rules_map


def validate_blocks_clean_rule(blocks, label=""):
    dumped = json.dumps(blocks, ensure_ascii=False)
    unresolved_match = re.search(r"\[\[[A-Z0-9\-]+\]\]", dumped)
    if unresolved_match:
        raise AssertionError(f"[{label}] Found unresolved ID token {unresolved_match.group(0)} in generated blocks!")
    if label != "06_TEMPLATE_CONTRACT":
        thai_match = re.search(r"[\u0E00-\u0E7F]+", dumped)
        if thai_match:
            raise AssertionError(
                f"[{label}] Found non-English (Thai) text '{thai_match.group(0)}' in generated blocks!"
            )


def update_child_page(pid, file_path, label, id_map, token):
    with open(file_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    blocks = md_to_notion_blocks(md_text, id_map)
    validate_blocks_clean_rule(blocks, label=label)

    print(f"\nSyncing {label} ({file_path}) ➔ Notion Page {pid} ({len(blocks)} blocks)...")
    replace_page_blocks(pid, blocks, label, token)
    print(f"  {label} synced successfully ({len(blocks)} blocks)!")


def update_master_page(master_pid, rules_map, id_map, token):
    print(f"\nSyncing Master Rule Hub ➔ Notion Page {master_pid}...")

    # Read 00_core.md
    with open(os.path.join(RULES_DIR, "00_core.md"), "r", encoding="utf-8") as f:
        core_md = f.read()
    core_blocks = md_to_notion_blocks(core_md, id_map)

    # Build Header and Navigation Blocks
    nav_blocks = [
        callout_block(
            "**Modular Context-Aware Rule Architecture:**\n\n"
            "To maximize token efficiency and prevent instruction dilution across large workflows, rules are split into decoupled modules. "
            "AI agents and developers inspect only the module relevant to their active task rather than consuming the entire rulebook in context.",
            id_map,
            color="blue_background",
        ),
        divider_block(),
        h2("Specialized Rule Modules & Navigation Hub", id_map),
        p_block(
            "Access the domain-specific rule modules below. Each module is maintained Local-First in `rules/*.md` and synced directly to Notion:",
            id_map,
        ),
    ]

    for mod in SUB_MODULES:
        key = mod["key"]
        sub_info = rules_map[key]
        sub_id = sub_info.get("id") or "00000000-0000-0000-0000-000000000000"
        # We construct rich_text with mention_page directly
        rt_parts = [
            mention_page(sub_id, bold=True),
            rt(f" (`{mod['file']}`): {mod['desc']}"),
        ]
        nav_blocks.append(
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": rt_parts},
            }
        )

    nav_blocks.append(divider_block())
    nav_blocks.append(h2("Universal Core Governance & Safety Invariants", id_map))
    nav_blocks.append(
        p_block(
            "The following core invariants apply universally to all tasks and agents across the workspace:",
            id_map,
        )
    )

    # Combine: nav_blocks + core_blocks (skipping title of core_blocks if duplicate)
    combined_blocks = nav_blocks
    for b in core_blocks:
        if b["type"] == "heading_1":
            continue
        combined_blocks.append(b)

    validate_blocks_clean(combined_blocks, label="MasterHub")

    # Clean existing non-child_page blocks from Master Page
    master_blocks = get_all_blocks(master_pid, token)
    to_delete = [b["id"] for b in master_blocks if b["type"] != "child_page"]
    print(f"  Cleaning {len(to_delete)} existing non-child blocks from Master Page (PRESERVING child_page blocks)...")

    def del_m_block(b_id):
        try:
            notion_request("DELETE", f"blocks/{b_id}", token)
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(del_m_block, to_delete))

    # Append new blocks in chunks of 50
    for i in range(0, len(combined_blocks), 50):
        chunk = combined_blocks[i : i + 50]
        notion_request("PATCH", f"blocks/{master_pid}/children", token, {"children": chunk})

    print(f"  Master Rule Hub synced successfully ({len(combined_blocks)} blocks)!")


def plan_sync(master_pid, rules_map, id_map):
    """
    Dry-run mode: prints detailed plan without calling Notion API or writing rules_map.json.
    """
    print("\n========================================================")
    print("DRY-RUN SYNC PLAN: LOCAL-FIRST MODULAR RULES ➔ NOTION")
    print("========================================================")
    print(f"Master Page ID: {master_pid}")
    print("Mode: Dry-Run (No Notion API calls, rules_map.json untouched)\n")

    # 1. Plan for Sub-Pages
    print("--- Sub-Page Sync Plan ---")
    sub_plans = []
    for mod in SUB_MODULES:
        key = mod["key"]
        sub_info = rules_map.get(key, {})
        sub_id = sub_info.get("id") if isinstance(sub_info, dict) else None
        file_path = mod["file"]

        with open(file_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        blocks = md_to_notion_blocks(md_text, id_map)
        validate_blocks_clean_rule(blocks, label=key)
        block_count = len(blocks)

        if sub_id:
            action = "REPLACE (แทนที่)"
            target = f"Existing Notion Page {sub_id}"
        else:
            action = "CREATE (สร้างใหม่)"
            target = f"New Child Page under Master Hub ({master_pid})"

        sub_plans.append(
            {
                "key": key,
                "action": action,
                "title": mod["title"],
                "file": file_path,
                "target": target,
                "block_count": block_count,
                "id": sub_id,
            }
        )
        print(f"  [{action}] {key}: {mod['title']}")
        print(f"      Target: {target}")
        print(f"      File:   {file_path} ({block_count} Notion blocks)")

    # 2. Plan for Master Page
    print("\n--- Master Page Sync Plan ---")
    with open(os.path.join(RULES_DIR, "00_core.md"), "r", encoding="utf-8") as f:
        core_md = f.read()
    core_blocks = md_to_notion_blocks(core_md, id_map)
    core_content_blocks = [b for b in core_blocks if b.get("type") != "heading_1"]

    nav_block_count = 7 + len(SUB_MODULES)  # Header callout, divider, h2, p, sub-module bullets, divider, h2, p
    master_total_blocks = nav_block_count + len(core_content_blocks)

    print(f"  [REPLACE (แทนที่)] Master Rule Hub: Page {master_pid}")
    print(f"      Navigation Hub: {nav_block_count} blocks (Header + {len(SUB_MODULES)} Sub-Page mentions)")
    print(f"      Core Governance (00_core.md): {len(core_content_blocks)} blocks")
    print(f"      Total Blocks to Append: {master_total_blocks} blocks")
    print("      Child Pages: Preserved (only non-child_page blocks replaced)")

    # 3. Summary
    print("\n--- Summary ---")
    to_create = sum(1 for p in sub_plans if "CREATE" in p["action"])
    to_replace = sum(1 for p in sub_plans if "REPLACE" in p["action"]) + 1  # +1 for master hub
    print(
        f"Pages to Create:  {to_create} ({', '.join(p['key'] for p in sub_plans if 'CREATE' in p['action']) or 'None'})"
    )
    print(
        f"Pages to Replace: {to_replace} (Master Hub + {sum(1 for p in sub_plans if 'REPLACE' in p['action'])} Sub-Pages)"
    )
    print("rules_map.json:   Unchanged (Dry-run mode, 0 API calls made)")
    print("========================================================\n")
    return {
        "sub_plans": sub_plans,
        "master_total_blocks": master_total_blocks,
        "to_create": to_create,
        "to_replace": to_replace,
    }


def main(dry_run=False):
    env = load_env()
    token = env.get("NOTION_TOKEN") or os.environ.get("NOTION_TOKEN")
    if dry_run:
        token = token or "dummy-dry-run-token"
    else:
        require_token(token)  # clear error instead of a 401 from a placeholder token

    id_map = {}
    if os.path.exists("id_map.json"):
        with open("id_map.json", "r", encoding="utf-8") as f:
            id_map = json.load(f)

    if dry_run:
        rules_map = get_or_create_sub_pages(MASTER_RULES_PID, token, dry_run=True)
        return plan_sync(MASTER_RULES_PID, rules_map, id_map)

    print("\n========================================================")
    print("STARTING LOCAL-FIRST AUTO-SYNC OF MODULAR RULES TO NOTION")
    print("========================================================")

    # 1. Get or create child pages under Master Rule Hub (merged)
    rules_map = get_or_create_sub_pages(MASTER_RULES_PID, token, dry_run=False)

    # Update id_map with sub-page IDs so parse_rt can resolve them if needed
    for key, info in rules_map.items():
        if isinstance(info, dict) and "id" in info:
            id_map[info["id"]] = {"id": info["id"], "title": info["title"]}
            id_map[key] = {"id": info["id"], "title": info["title"]}

    # 2. Sync each child page
    for mod in SUB_MODULES:
        key = mod["key"]
        sub_info = rules_map[key]
        update_child_page(sub_info["id"], sub_info["file"], key, id_map, token)

    # 3. Sync Master Page
    update_master_page(MASTER_RULES_PID, rules_map, id_map, token)

    # 4. Final Audit
    print("\n========================================================")
    print("RUNNING FINAL NOTION API AUDIT FOR ALL RULE PAGES")
    print("========================================================")
    all_passed = True
    master_passed = audit_page(MASTER_RULES_PID, "RULES-MASTER", id_map, token)
    if not master_passed:
        all_passed = False

    for mod in SUB_MODULES:
        key = mod["key"]
        sub_info = rules_map[key]
        passed = audit_page(sub_info["id"], key, id_map, token)
        if not passed:
            all_passed = False

    print("\n--------------------------------------------------------")
    if all_passed:
        print(f"ALL RULE PAGES (MASTER + {len(SUB_MODULES)} SUB-PAGES) VERIFIED 100% CLEAN AND PASSING!")
    else:
        print("WARNING: Some rule pages had audit warnings!")
    print("--------------------------------------------------------\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local-First Auto-Sync of modular rules to Notion.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print sync plan without calling Notion API or writing rules_map.json"
    )
    parsed_args = parser.parse_args()
    is_dry = parsed_args.dry_run or (os.environ.get("NOTION_DRY_RUN", "").lower() in ("1", "true", "yes"))
    main(dry_run=is_dry)
