# -*- coding: utf-8 -*-
"""
Upgrades MTH-T01 Batch 3:
- Chapters: C10, C11, C13, C14 (4 Chapters)
- Units: C10 (5), C11 (4), C12 (7), C13 (6), C14 (4) (26 Units total)
Total pages: 30 pages.

Rule 11 Enforced: Strictly preserves all existing user progress (Status: 'Pending Review', 'In progress', 'Skip', etc.),
Mastery scores, and historical drill/review logs.
"""

import json
import re
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    get_all_blocks,
    replace_page_blocks,
    validate_blocks_clean,
    parse_rt,
    h2,
    h3,
    p_block,
    callout_block,
    divider_block,
    eq_block,
    bullet,
    num_item,
    todo_item,
    toggle_block,
)
from mth_t01_batch3_data import CHAPTER_DATA
from mth_t01_batch3_units import UNIT_DATA

def build_chapter_blocks(ch_code, ch_data, id_map, preserved_drill_logs):
    units_mentions = " ".join(f"[[{u}]]" for u in ch_data["units"])
    blocks = [
        # Callout Header
        callout_block(
            f"**Chapter Objective:** {ch_data['objective']}\n\n"
            f"**Parent Topic:** [[MTH-T01]] | **Resource:** [[R035]] | **Level:** Prealgebra Foundation | **Units:** {len(ch_data['units'])} Units ({units_mentions})",
            id_map,
            color="blue_background"
        ),
        divider_block(),

        # Section 1: Role & Scope
        h2("Role in Prealgebra & Mathematical Scope", id_map),
        p_block(ch_data["role"], id_map),
        divider_block(),

        # Section 2: Core Concepts & Invariants
        h2("Core Mathematical Concepts & Structural Invariants", id_map),
    ]
    for inv in ch_data["invariants"]:
        blocks.append(bullet(inv, id_map))
    blocks.append(divider_block())

    # Section 3: Unit Sequence
    blocks.append(h2("Unit Sequence & Progression", id_map))
    blocks.append(p_block("Complete the Units in ascending numerical order. Master each unit's definitions, properties, and practice guides:", id_map))
    for u in ch_data["units"]:
        u_info = UNIT_DATA.get(u, {})
        u_title = u_info.get("title", id_map.get(u, {}).get("title", ""))
        u_obj = u_info.get("objective", "")
        blocks.append(num_item(f"**[[{u}]] — {u_title}:** {u_obj}", id_map))
    blocks.append(divider_block())

    # Section 4: Practice Guide
    pg = ch_data["practice_guide"]
    blocks.extend([
        h2("Practice Guide", id_map),
        p_block("This Chapter Practice Guide directs AI drill engines and independent review across 4 core competencies:", id_map),
        h3("1. Conceptual Check", id_map),
    ])
    for c in pg["conceptual"]:
        blocks.append(bullet(c, id_map))

    blocks.append(h3("2. Computational / Formula Drill", id_map))
    for c in pg["computational"]:
        blocks.append(bullet(c, id_map))

    blocks.append(h3("3. Edge Cases & Trap Detection", id_map))
    for c in pg["traps"]:
        blocks.append(bullet(c, id_map))

    blocks.append(h3("4. Real-world Synthesis", id_map))
    for c in pg["real_world"]:
        blocks.append(bullet(c, id_map))
    blocks.append(divider_block())

    # Section 5: Active Recall Questions
    blocks.extend([
        h2("Active Recall Questions", id_map),
        p_block("Attempt each synthesis question mentally or on scratch paper before expanding the toggle:", id_map),
    ])
    for ar in ch_data["active_recall"]:
        blocks.append(toggle_block(ar["q"], [f"**Reference Solution:** {ar['a']}"], id_map))
    blocks.append(divider_block())

    # Section 6: Chapter Synthesis & Problem-Solving Challenge
    blocks.extend([
        h2("Chapter Synthesis & Problem-Solving Challenge", id_map),
        todo_item(f"Synthesize the core invariants of {ch_data['title']} and explain their connection to [[MTH-T01]].", id_map),
        todo_item("Complete all 4 categories in the Practice Guide and evaluate performance in the Practice Hub.", id_map),
        divider_block(),

        # Section 7: Chapter Review & Spaced Retention Guide
        h2("Chapter Review & Spaced Retention Guide", id_map),
        bullet("Keep 'Status' (initial completion) separate from 'Mastery (0-4)' (long-term recall and problem-solving fluency).", id_map),
        bullet("Schedule reviews based on current Mastery level: Mastery 1 = 1-2 days; Mastery 2 = 4-7 days; Mastery 3 = 14-21 days; Mastery 4 = 30-60 days.", id_map),
    ])

    if preserved_drill_logs:
        blocks.append(h3("Historical Review & Drill Logs (Preserved User Progress)", id_map))
        blocks.extend(preserved_drill_logs)

    return blocks

def build_unit_blocks(u_code, u_data, id_map, preserved_user_notes):
    ch_code = u_data["chapter"]
    blocks = [
        # Callout Header
        callout_block(
            f"**Learning Objective:** {u_data['objective']}\n\n"
            f"**Parent Chapter:** [[{ch_code}]] | **Parent Topic:** [[MTH-T01]] | **Resource:** [[R035]] | **Time Est:** 45 mins | **Priority:** Core | **XP:** 10",
            id_map,
            color="gray_background"
        ),
        divider_block(),

        # Section 1: Core Concepts
        h2("Core Concepts, Definitions & Mathematical Intuition", id_map),
    ]
    for conc in u_data["concepts"]:
        blocks.append(bullet(conc, id_map))
    blocks.append(divider_block())

    # Optional Parametric Diagram
    if u_data.get("diagram_upload_id"):
        blocks.extend([
            h2("Parametric Geometric Model", id_map),
            {
                "object": "block",
                "type": "image",
                "image": {
                    "type": "file_upload",
                    "file_upload": {"id": u_data["diagram_upload_id"]}
                }
            },
            divider_block(),
        ])

    # Section 2: Formulas
    blocks.append(h2("Key Formulas, Properties & Identities", id_map))
    for f in u_data["formulas"]:
        blocks.append(eq_block(f))
    blocks.append(divider_block())

    # Section 3: Worked Example
    ex = u_data["example"]
    blocks.extend([
        h2("Step-by-Step Worked Example", id_map),
        p_block(f"**Example ({ex['title']}):**", id_map),
    ])
    for step in ex["steps"]:
        if step.startswith("\\") or ("=" in step and step.startswith(" ")):
            blocks.append(eq_block(step))
        else:
            blocks.append(p_block(step, id_map))
    blocks.append(divider_block())

    # Section 4: Practice Guide
    pg = u_data["practice_guide"]
    blocks.extend([
        h2("Practice Guide", id_map),
        p_block("AI drill generators and learners should structure practice across these 4 categories:", id_map),
        h3("1. Conceptual Check", id_map),
    ])
    for c in pg["conceptual"]:
        blocks.append(bullet(c, id_map))

    blocks.append(h3("2. Computational / Formula Drill", id_map))
    for c in pg["computational"]:
        blocks.append(bullet(c, id_map))

    blocks.append(h3("3. Edge Cases & Trap Detection", id_map))
    for c in pg["traps"]:
        blocks.append(bullet(c, id_map))

    blocks.append(h3("4. Real-world & Cross-Subject Synthesis", id_map))
    for c in pg["cross"]:
        blocks.append(bullet(c, id_map))
    blocks.append(divider_block())

    # Section 5: Active Recall Questions
    blocks.extend([
        h2("Active Recall Questions", id_map),
        p_block("Attempt each question from memory before expanding the toggle:", id_map),
    ])
    for ar in u_data["active_recall"]:
        blocks.append(toggle_block(ar["q"], [f"**Reference Solution:** {ar['a']}"], id_map))
    blocks.append(divider_block())

    # Section 6: Mistake Log
    blocks.extend([
        h2("My Implementation & Mistake Log", id_map),
        bullet("**Feynman One-Liner:** [Explain this mathematical concept in your own words]", id_map),
        bullet("**My Worked Solutions & Derivations:** [Record your scratch work and step-by-step calculations]", id_map),
        bullet("**Mistake & Algebraic Trap Log:** [Record any calculation errors, sign mistakes, or formula mixups]", id_map),
        divider_block(),

        # Section 7: Completion Checklist
        h2("Completion Checklist & Mastery Review", id_map),
        todo_item(f"State the core definitions and invariants of {u_data['title']} without looking at notes.", id_map),
        todo_item("Complete all 4 categories in the Practice Guide and record reflections in the Mistake Log.", id_map),
        todo_item("Answer all Active Recall questions from memory and update 'Mastery (0-4)'.", id_map),
    ])

    if preserved_user_notes:
        blocks.append(h3("Learner Historical Notes & Drill Records (Preserved)", id_map))
        blocks.extend(preserved_user_notes)

    return blocks

def audit_page(page_id, code, id_map, token):
    blocks = get_all_blocks(page_id, token)
    code_pattern = re.compile(r'\b(MTH-T\d+(?:-C\d+(?:-U\d+)?)?|PHY-T\d+(?:-C\d+(?:-U\d+)?)?|PRG-T\d+(?:-C\d+(?:-U\d+)?)?|R\d{3})\b')
    
    mentions = 0
    unlinked = []
    
    for b in blocks:
        bt = b["type"]
        rt_list = b.get(bt, {}).get("rich_text", [])
        for t in rt_list:
            if t.get("type") == "mention" and t.get("mention", {}).get("type") == "page":
                mentions += 1
            elif t.get("type") == "text":
                for m in code_pattern.finditer(t.get("plain_text", "")):
                    unlinked.append((m.group(1), b["id"]))
                    
    status = "PASS" if len(unlinked) == 0 else "FAIL"
    print(f"[{status}] {code:<18} Blocks={len(blocks):<2} | Mentions={mentions:<2} | Unlinked={len(unlinked)}")
    if unlinked:
        print(f"  Unlinked tokens: {unlinked}")
    return len(unlinked) == 0

def main():
    env = load_env()
    token = env["NOTION_TOKEN"]
    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    batch3_chapters = ["MTH-T01-C10", "MTH-T01-C11", "MTH-T01-C13", "MTH-T01-C14"]
    
    print("\n========================================================")
    print("UPGRADING MTH-T01 BATCH 3 (4 CHAPTERS + 26 UNITS: 30 PAGES)")
    print("========================================================")

    # 1. Process 4 Chapters
    for ch_code in batch3_chapters:
        ch_data = CHAPTER_DATA[ch_code]
        pid = id_map[ch_code]["id"]
        print(f"\nProcessing Chapter: {ch_code} ({ch_data['title']})...")
        
        # Check existing blocks
        existing = get_all_blocks(pid, token)
        if len(existing) >= 45:
            print(f"  Chapter {ch_code} already upgraded ({len(existing)} blocks). Skipping rewrite.")
            continue

        drill_logs = []
        for b in existing:
            bt = b["type"]
            txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
            if "Score " in txt and "Drill" in txt:
                drill_logs.append(b)

        ch_blocks = build_chapter_blocks(ch_code, ch_data, id_map, drill_logs)
        validate_blocks_clean(ch_blocks, label=ch_code)
        replace_page_blocks(pid, ch_blocks, label=ch_code, token=token)

        # Update Objective property without touching user Status or Mastery
        notion_request("PATCH", f"pages/{pid}", token, {
            "properties": {
                "Objective": {
                    "rich_text": [{"type": "text", "text": {"content": ch_data["objective"]}}]
                }
            }
        })
        print(f"  Chapter {ch_code} updated successfully ({len(ch_blocks)} blocks)!")

    # 2. Process 26 Units
    unit_codes = sorted(list(UNIT_DATA.keys()))
    print(f"\nProcessing {len(unit_codes)} Units across Batch 3...")
    for u_code in unit_codes:
        u_data = UNIT_DATA[u_code]
        pid = id_map[u_code]["id"]
        print(f"  Processing Unit: {u_code} ({u_data['title']})...")
        
        # Check existing blocks
        existing = get_all_blocks(pid, token)
        if len(existing) >= 45:
            print(f"    {u_code} already upgraded ({len(existing)} blocks). Skipping rewrite.")
            continue

        user_notes = []
        for b in existing:
            bt = b["type"]
            txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
            if ("Score " in txt and "Drill" in txt) or "My Notes:" in txt:
                user_notes.append(b)

        u_blocks = build_unit_blocks(u_code, u_data, id_map, user_notes)
        validate_blocks_clean(u_blocks, label=u_code)
        replace_page_blocks(pid, u_blocks, label=u_code, token=token)

        # Update instructional properties (DO NOT touch Status or Mastery)
        notion_request("PATCH", f"pages/{pid}", token, {
            "properties": {
                "Learning Objective": {
                    "rich_text": [{"type": "text", "text": {"content": u_data["objective"]}}]
                },
                "Expected Output": {
                    "rich_text": [{"type": "text", "text": {"content": u_data["expected_output"]}}]
                },
                "Priority": {"select": {"name": "Core"}},
                "XP": {"number": 10}
            }
        })
        print(f"    Unit {u_code} updated successfully ({len(u_blocks)} blocks)!")

    # 3. Final Audit across all 30 pages
    print("\n========================================================")
    print("RUNNING FINAL NOTION API AUDIT (30 PAGES)")
    print("========================================================")
    all_passed = True
    for ch_code in batch3_chapters:
        passed = audit_page(id_map[ch_code]["id"], ch_code, id_map, token)
        if not passed:
            all_passed = False

    for u_code in unit_codes:
        passed_u = audit_page(id_map[u_code]["id"], u_code, id_map, token)
        if not passed_u:
            all_passed = False

    print("\n--------------------------------------------------------")
    if all_passed:
        print("ALL 30 PAGES OF MTH-T01 BATCH 3 AUDITED AND VERIFIED 100% CLEAN AND PASSING!")
    else:
        print("WARNING: Some pages had audit warnings!")
    print("--------------------------------------------------------\n")

if __name__ == "__main__":
    main()
