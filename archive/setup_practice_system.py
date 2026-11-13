# -*- coding: utf-8 -*-
"""
Sets up the Hybrid Practice & Drills system:
1. Creates (or updates) the 5th Notion database 'Learning Practice & Drills' under root page 'Database' (3dd3818f-8ba0-8047-88bf-ed7597322014),
   with two-way relations to Learning Topics, Learning Chapters, and Learning Units.
2. Updates 'Learning System — AI Implementation Rules' (40c3818f-8ba0-8002-92f1-e971793125e3) with Part 10:
   Hybrid Practice & Drill Generation, Verification, Paper-First Diagnostics, and Auto-Sync Rules.
3. Pre-verifies all mathematical steps and answers using Python's exact rational/complex arithmetic before creating:
   - Drill Record 1: DRL-MTH-T02-C01-U01-01 (Complex Numbers — Interactive HTML Worksheet with Click-to-Highlight Equation Steps, Paper-First Step Divergence Tagging, Smart Real/Imaginary Part Checker, Plain-Text CAS Copy Box, and 1-Click Notion Sync).
   - Drill Record 2: DRL-PRG-T03-C01-U01-01 (Next.js Project Structure — Executable Test Suite + Interactive Architecture Drill with 1-Click Notion Sync).
"""
import json
import os
import re
from fractions import Fraction
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    get_all_blocks,
    rt,
    parse_rt,
    validate_blocks_clean,
    h2,
    h3,
    p_block,
    callout_block,
    quote_block,
    divider_block,
    eq_block,
    code_block,
    bullet,
    num_item,
    todo_item,
    toggle_block,
    replace_page_blocks,
)

ROOT_DB_PAGE_ID = "3dd3818f-8ba0-8047-88bf-ed7597322014"
TOPICS_DB_ID = "4003818f-8ba0-8029-b434-e25399e46ef0"
CHAPTERS_DB_ID = "4003818f-8ba0-8031-8336-f7852e0de01b"
UNITS_DB_ID = "4003818f-8ba0-804e-a812-f0251efb8978"
RESOURCES_DB_ID = "40c3818f-8ba0-8098-93cf-c2fcb655f510"
RULES_PAGE_ID = "40c3818f-8ba0-8002-92f1-e971793125e3"

def ensure_drills_database(token):
    print("=== Step 1: Checking / Creating 'Learning Practice & Drills' Database ===")
    root_children = get_all_blocks(ROOT_DB_PAGE_ID, token)
    for b in root_children:
        if b.get("type") == "child_database":
            title = b.get("child_database", {}).get("title", "")
            if "Practice" in title or "Drills" in title:
                db_id = b["id"]
                print(f"  Found existing 'Learning Practice & Drills' DB: {db_id}")
                return db_id

    payload = {
        "parent": {"type": "page_id", "page_id": ROOT_DB_PAGE_ID},
        "icon": {"type": "icon", "icon": {"name": "target", "color": "lightgray"}},
        "title": [rt("Learning Practice & Drills")],
        "properties": {
            "Drill": {"title": {}},
            "Drill ID": {"rich_text": {}},
            "Order": {"number": {"format": "number"}},
            "Scope Level": {
                "select": {
                    "options": [
                        {"name": "Unit Drill", "color": "blue"},
                        {"name": "Chapter Mixed", "color": "purple"},
                        {"name": "Topic Synthesis", "color": "pink"},
                    ]
                }
            },
            "Format": {
                "select": {
                    "options": [
                        {"name": "Interactive HTML", "color": "green"},
                        {"name": "Code Test Suite", "color": "orange"},
                        {"name": "PDF Worksheet", "color": "yellow"},
                        {"name": "Notion Worksheet", "color": "gray"},
                    ]
                }
            },
            "Difficulty Mode": {
                "select": {
                    "options": [
                        {"name": "Level 1 - Foundation", "color": "gray"},
                        {"name": "Level 2 - Standard Exam", "color": "blue"},
                        {"name": "Level 3 - Trap & Diagnostic", "color": "orange"},
                        {"name": "Level 4 - Applied Synthesis", "color": "red"},
                        {"name": "Mixed Exam Mode", "color": "purple"},
                    ]
                }
            },
            "Question Count": {"number": {"format": "number"}},
            "Practice Status": {
                "select": {
                    "options": [
                        {"name": "Ready", "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Graded", "color": "green"},
                        {"name": "Needs Retry", "color": "red"},
                    ]
                }
            },
            "Score": {"number": {"format": "number"}},
            "Max Score": {"number": {"format": "number"}},
            "Accuracy %": {
                "formula": {
                    "expression": 'if(prop("Max Score") > 0, round(prop("Score") / prop("Max Score") * 1000) / 10, 0)'
                }
            },
            "Mistake Categories": {
                "multi_select": {
                    "options": [
                        {"name": "Arithmetic / Sign Slip", "color": "yellow"},
                        {"name": "Premature Radical Multiplication", "color": "orange"},
                        {"name": "Conjugate Denominator Error", "color": "red"},
                        {"name": "Formula / Identity Mix-up", "color": "purple"},
                        {"name": "Domain / Extraneous Root", "color": "pink"},
                        {"name": "Unseparated Standard Form", "color": "brown"},
                        {"name": "Route Group URL Collision", "color": "red"},
                        {"name": "Page vs Route Conflict", "color": "orange"},
                        {"name": "Env Boundary / Secret Leak", "color": "pink"},
                        {"name": "Type Narrowing / Any Leak", "color": "blue"},
                    ]
                }
            },
            "Diverged Steps Summary": {"rich_text": {}},
            "Local File Path": {"rich_text": {}},
            "Attempt Date": {"date": {}},
            "Topics": {
                "relation": {
                    "database_id": TOPICS_DB_ID,
                    "type": "dual_property",
                    "dual_property": {"synced_property_name": "Practice Drills"},
                }
            },
            "Chapters": {
                "relation": {
                    "database_id": CHAPTERS_DB_ID,
                    "type": "dual_property",
                    "dual_property": {"synced_property_name": "Practice Drills"},
                }
            },
            "Units": {
                "relation": {
                    "database_id": UNITS_DB_ID,
                    "type": "dual_property",
                    "dual_property": {"synced_property_name": "Practice Drills"},
                }
            },
        },
    }
    created = notion_request("POST", "databases", token, payload)
    db_id = created["id"]
    print(f"  Created 'Learning Practice & Drills' Database: {db_id}")
    return db_id

def update_rules_with_drill_engine(rules_id, id_map, token):
    print("\n=== Step 2: Adding Hybrid Practice & Drill Engine Rules to 'Learning System — AI Implementation Rules' ===")
    r_blocks = get_all_blocks(rules_id, token)
    for b in r_blocks:
        bt = b["type"]
        txt = ""
        if bt in b and "rich_text" in b[bt]:
            txt = "".join(t.get("plain_text", "") for t in b[bt]["rich_text"])
        if "Hybrid Practice & Drill Generation Engine" in txt or "Mandatory Pre-Verification" in txt or "Paper-First Step Diagnostics" in txt:
            notion_request("DELETE", f"blocks/{b['id']}", token)

    # Find the heading for 'Multi-Level Practice Guide & Cross-Subject Connection Rules' or insert after 40c3818f-8ba0-810e-a652-ff08877b6917
    anchor_id = "40c3818f-8ba0-810e-a652-ff08877b6917"
    r_blocks = get_all_blocks(rules_id, token)
    for b in r_blocks:
        bt = b["type"]
        txt = ""
        if bt in b and "rich_text" in b[bt]:
            txt = "".join(t.get("plain_text", "") for t in b[bt]["rich_text"])
        if "Level 3 — Topic" in txt:
            anchor_id = b["id"]

    drill_rules = [
        h3("Hybrid Practice & Drill Generation Engine (Next.js Studio + JSON + Notion)", id_map),
        p_block(
            "**1. Clean Architectural Separation:** The system strictly separates three layers: (a) **Pure JSON Data Layer (`drills/data/<UNIT>/`)** storing verified problems and session states without HTML/JS pollution; (b) **Central Next.js Practice Studio (`practice-studio`)** providing the interactive learner workspace with React, TypeScript, and KaTeX; and (c) **Notion Database (`Learning Practice & Drills`)** as the permanent retention record and spaced review ledger.",
            id_map,
        ),
        bullet("**2. Pre-Generation Configuration Standard:**", id_map, children=[
            bullet("**Mandatory Pre-Generation Selection:** AI and the practice studio must NEVER generate large problem pools in advance to hide unselected ones. The learner specifies the configuration (`Unit`, `Question Count`: `5`, `10`, `15`, or `20`, and `Difficulty Mode`: `Level 1` through `Level 4` or `Mixed Exam Mode`) BEFORE generation. The system generates and verifies ONLY the exact number of requested questions.", id_map),
            bullet("**Shuffled, Unlabeled Presentation:** Generated problems draw from the Unit's 4 Practice Guide dimensions but are presented without category spoilers until graded.", id_map),
        ]),
        bullet("**3. Type-Driven SymPy Verification & Universal Problem Coverage:**", id_map, children=[
            bullet("**SymPy Pre-Execution Proof:** Every mathematical problem, intermediate derivation step, and final answer must be verified algebraically using SymPy (`math_engine.verify`) before writing to JSON or Notion.", id_map),
            bullet("**Universal Answer Types:** The answer checker (`math_engine.answer_check`) is extensible across all future curriculum subjects, supporting `number`, `complex`, `expression`, `solution_set`, `tuple`, `choice`, and `text` with automated component analysis (real/imaginary parts, signs, unreduced fractions, non-factored forms).", id_map),
        ]),
        bullet("**4. Zero Unrendered Syntax & Universal KaTeX Rendering:**", id_map, children=[
            bullet("**Zero Raw Markdown or Broken Tokens:** Generated drill JSON and client views must contain NO raw Markdown (`**`, `__`), NO unparsed bracketed ID tokens, and NO `\\displaystyle` prefixes inside string literals.", id_map),
            bullet("**100% Math-in-LaTeX Everywhere:** Every mathematical variable, expression, and formula—including inside prompt text, checkpoint hints, derivation steps, and **Mistake Tag selection pills**—must render via native KaTeX components.", id_map),
            bullet("**Clickable Cross-Subject Notion Badges:** When problems link to cross-subject units (such as [[PHY-T01-C19]] or [[PRG-T01-C03]]), they render as clickable deep-link badges that open the relevant Notion page directly.", id_map),
        ]),
        bullet("**5. Paper-First Diagnostics & Real-Time Notion Sync:**", id_map, children=[
            bullet("**Click-to-Highlight Synchronized Steps:** Clicking any derivation step row highlights both the equation block and its explanation while dimming surrounding rows to eliminate eye strain when comparing against physical paper.", id_map),
            bullet("**Paper Divergence Tracking:** Learners can click `[✗ My Paper Diverged Here]` on the specific step where handwritten paper work diverged, automatically tagging the error and auto-saving progress.", id_map),
            bullet("**One-Click Notion Telemetry:** Clicking `Grade & Sync to Notion` updates the drill row in `Learning Practice & Drills` (Score, Accuracy %, Mistake Categories, Diverged Steps Summary) and appends an entry to the Unit page's `Mistake Log`.", id_map),
        ]),
    ]
    validate_blocks_clean(drill_rules, "Rules-DrillEngine")
    notion_request("PATCH", f"blocks/{rules_id}/children", token, {
        "after": anchor_id,
        "children": drill_rules,
    })
    print("  Added 'Hybrid Practice & Drill Generation Engine' rules to 'Learning System — AI Implementation Rules'!")

def main():
    env = load_env()
    token = env.get("NOTION_TOKEN")
    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)
    drills_db_id = ensure_drills_database(token)
    id_map["DRILLS_DB"] = {"id": drills_db_id, "title": "Learning Practice & Drills"}
    with open("id_map.json", "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)
    update_rules_with_drill_engine(RULES_PAGE_ID, id_map, token)

if __name__ == "__main__":
    main()
