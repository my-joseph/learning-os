# -*- coding: utf-8 -*-
"""
Local-First Auto-Sync to Notion:
Synchronizes modular rules from local Markdown files (`rules/*.md`)
into Notion Master Rules Hub and its 5 specialized Sub-Pages.
"""

import json
import os
import re
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    get_all_blocks,
    replace_page_blocks,
    validate_blocks_clean,
    parse_rt,
    mention_page,
    rt,
    callout_block,
    divider_block,
    h2,
    p_block,
    bullet,
)
from test_md_parser import md_to_notion_blocks
from upgrade_mth_t01_batch2 import audit_page

from concurrent.futures import ThreadPoolExecutor

MASTER_RULES_PID = "40c3818f-8ba0-8002-92f1-e971793125e3"
RULES_DIR = "rules"
RULES_MAP_FILE = os.path.join(RULES_DIR, "rules_map.json")

SUB_MODULES = [
    {
        "key": "01_ARCH",
        "title": "01_ARCH — Learning Architecture, Database Relations & Progress Tracking",
        "file": os.path.join(RULES_DIR, "01_arch.md"),
        "desc": "Topic ➔ Chapter ➔ Unit hierarchy, database properties & completeness, Status vs. Mastery (0-4), inline @page mentions."
    },
    {
        "key": "02_PEDAGOGY",
        "title": "02_PEDAGOGY — Curriculum Design, Active Recall & Practice Guides",
        "file": os.path.join(RULES_DIR, "02_pedagogy.md"),
        "desc": "Reference structures, 4-tier Practice Guides (Anti-Dump rule), Active Recall toggles, learner's personal workspace & mistake log."
    },
    {
        "key": "03_STEM",
        "title": "03_STEM — Mathematics, Physics & Parametric Visual Standards",
        "file": os.path.join(RULES_DIR, "03_stem.md"),
        "desc": "Vertical LaTeX derivations, KaTeX formatting, parametric SVG educational diagrams, native Notion file upload API."
    },
    {
        "key": "04_CODE",
        "title": "04_CODE — Programming Practice, Test Suites & Terminal Labs",
        "file": os.path.join(RULES_DIR, "04_code.md"),
        "desc": "Next.js Practice Studio schemas, 5-tier milestone taxonomy, 8-step authoring pipeline, terminal telemetry engine (submit_lab.py)."
    },
    {
        "key": "05_QA",
        "title": "05_QA — Implementation Workflow, Quality Assurance & Audit Protocol",
        "file": os.path.join(RULES_DIR, "05_qa.md"),
        "desc": "10-step implementation workflow, 5-dimension QA checklist, scripted Notion API audit, implementation reporting."
    }
]

def get_or_create_sub_pages(master_pid, token):
    master_blocks = get_all_blocks(master_pid, token)
    existing_children = {}
    for b in master_blocks:
        if b["type"] == "child_page":
            title = b["child_page"].get("title", "")
            existing_children[title] = b["id"]

    rules_map = {
        "MASTER": master_pid,
        "00_CORE": os.path.join(RULES_DIR, "00_core.md")
    }

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
                "properties": {
                    "title": [{"type": "text", "text": {"content": target_title}}]
                }
            }
            res = notion_request("POST", "pages", token, payload)
            pid = res["id"]
            print(f"    Created with ID: {pid}")
        else:
            print(f"  Found existing Sub-Page for {key}: {pid}")
            
        rules_map[key] = {
            "id": pid,
            "title": target_title,
            "file": mod["file"]
        }

    with open(RULES_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(rules_map, f, indent=2, ensure_ascii=False)
    print(f"Saved rules map to {RULES_MAP_FILE}")
    return rules_map

def update_child_page(pid, file_path, label, id_map, token):
    with open(file_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    blocks = md_to_notion_blocks(md_text, id_map)
    validate_blocks_clean(blocks, label=label)

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
            color="blue_background"
        ),
        divider_block(),
        h2("Specialized Rule Modules & Navigation Hub", id_map),
        p_block("Access the domain-specific rule modules below. Each module is maintained Local-First in `rules/*.md` and synced directly to Notion:", id_map),
    ]

    for mod in SUB_MODULES:
        key = mod["key"]
        sub_info = rules_map[key]
        sub_id = sub_info["id"]
        # Use page mention
        bullet_text = f"**[[{sub_id}]]** (`{mod['file']}`): {mod['desc']}"
        # We can construct rich_text with mention_page directly
        rt_parts = [
            mention_page(sub_id, bold=True),
            rt(f" (`{mod['file']}`): {mod['desc']}")
        ]
        nav_blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": rt_parts}
        })

    nav_blocks.append(divider_block())
    nav_blocks.append(h2("Universal Core Governance & Safety Invariants", id_map))
    nav_blocks.append(p_block("The following core invariants apply universally to all tasks and agents across the workspace:", id_map))

    # Combine: nav_blocks + core_blocks (skipping title of core_blocks if duplicate)
    combined_blocks = nav_blocks
    for b in core_blocks:
        # Skip the top heading_1 since master page already has title
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
        chunk = combined_blocks[i:i+50]
        notion_request("PATCH", f"blocks/{master_pid}/children", token, {"children": chunk})

    print(f"  Master Rule Hub synced successfully ({len(combined_blocks)} blocks)!")

def main():
    env = load_env()
    token = env["NOTION_TOKEN"]
    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    print("\n========================================================")
    print("STARTING LOCAL-FIRST AUTO-SYNC OF MODULAR RULES TO NOTION")
    print("========================================================")

    # 1. Get or create child pages under Master Rule Hub
    rules_map = get_or_create_sub_pages(MASTER_RULES_PID, token)

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
        print("ALL RULE PAGES (MASTER + 5 SUB-PAGES) VERIFIED 100% CLEAN AND PASSING!")
    else:
        print("WARNING: Some rule pages had audit warnings!")
    print("--------------------------------------------------------\n")

if __name__ == "__main__":
    main()
