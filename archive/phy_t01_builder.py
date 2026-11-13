# -*- coding: utf-8 -*-
"""
Builder module for PHY-T01 (Physics High School):
Focus: Phase 1 — Prealgebra-Compatible Classical Mechanics (Chapters C01–C04: 13 Units).
Populates complete Gold Standard curriculum:
- PHY-T01 (Topic)
- PHY-T01-C01 through C04 (4 Chapters)
- PHY-T01-C01-U01 through C04-U04 (13 Units)
Strict adherence to:
- Central Rules (Complete 4-dimension Practice Guides, Zero static problem dump)
- Two-way @page mentions (zero plain-text entity codes)
- Proper property population (Objectives, Expected Outputs, XP, Resources relation to R037)
"""
import json
import time
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
    bullet,
    num_item,
    todo_item,
    toggle_block,
    divider_block,
    eq_block,
    replace_page_blocks,
)
from phy_t01_data import PHY_TOPIC_DATA, PHY_CHAPTERS_DATA, PHY_UNITS_DATA

def build_phy_topic_blocks(id_map):
    top = PHY_TOPIC_DATA
    blocks = [
        callout_block(
            f"**Topic Goal:** {top['goal']}\n"
            f"**Prerequisites:** [[MTH-T01]] (specifically [[MTH-T01-C01]], [[MTH-T01-C03]], [[MTH-T01-C07]], [[MTH-T01-C08]], [[MTH-T01-C10]], [[MTH-T01-C11]], [[MTH-T01-C12]], [[MTH-T01-C14]]) | "
            f"**Cross-Disciplinary:** [[PRG-T01]] | "
            f"**Primary Resource:** [[{top['source_id']}]] ({top['source_label']})",
            id_map,
            color="blue_background",
        ),
        h2("1. Overview & Physical Context", id_map),
    ]
    for p in top["overview"]:
        blocks.append(p_block(p, id_map))

    blocks.append(divider_block())
    blocks.append(h2("2. Measurable Learning Outcomes", id_map))
    for o in top["outcomes"]:
        blocks.append(bullet(o, id_map))

    blocks.append(divider_block())
    blocks.append(h2("3. Chapter Architecture & Learning Sequence (C01–C23)", id_map))
    blocks.append(p_block(
        "Follow the 23 Chapters in ascending Order. Note the two deliberate mathematical phases: **Phase 1 (C01–C04)** is 100% Prealgebra-ready, while **Phase 2 (C05–C23)** extends to 2D vectors and higher physics after completing [[MTH-T02]] (Algebra & Trigonometry):",
        id_map
    ))
    for cid, title, count, summary in top["chapters_summary"]:
        blocks.append(num_item(f"[[{cid}]] — {title} ({count} Units): {summary}", id_map))

    blocks.append(divider_block())
    blocks.append(h2("4. Source Attribution & Verification Status", id_map))
    blocks.append(bullet(
        "OpenStax — Physics (https://openstax.org/books/physics/pages/preface) | Status: URL Accessible | Content Accessible | Content Verified (HTTP 200). Linked as primary resource [[R037]].",
        id_map
    ))

    blocks.append(divider_block())
    blocks.append(h2("5. Topic Synthesis & Final Review", id_map))
    for item in top["final_review"]:
        blocks.append(todo_item(item, id_map))

    return blocks

def build_phy_chapter_blocks(cid, ch, id_map):
    blocks = [
        callout_block(
            f"**Chapter Objective:** {ch['objective']}\n"
            f"**Completion Criteria:** {ch['criteria']}\n"
            f"**Parent Topic:** [[PHY-T01]] | "
            f"**Prerequisites:** {ch['prereqs']} | "
            f"**Source:** [[R037]] ({ch['source_section']})",
            id_map,
            color="blue_background",
        ),
        h2("1. Role in Physics & Physical Scope", id_map),
        p_block(ch["role"], id_map),
        divider_block(),
        h2("2. Core Physical Principles & Invariants", id_map),
    ]
    for c in ch["concepts"]:
        blocks.append(bullet(c, id_map))

    blocks.append(divider_block())
    blocks.append(h2("3. Unit Sequence & Progression", id_map))
    blocks.append(p_block(
        "Complete the Units in ascending Order. Track completion via the 'Units' relation and 'Rollup' properties:",
        id_map
    ))
    for uid, utitle, usummary in ch["units"]:
        blocks.append(num_item(f"[[{uid}]] — {utitle}: {usummary}", id_map))

    blocks.append(divider_block())
    blocks.append(h2("4. Chapter Synthesis Challenge", id_map))
    for challenge_item in ch["challenge"]:
        blocks.append(todo_item(challenge_item, id_map))

    blocks.append(divider_block())
    blocks.append(h2("5. Chapter Practice Guide", id_map))
    blocks.append(p_block(
        "Use this chapter blueprint to generate mixed multi-unit problem sets and review physical calculation pitfalls:",
        id_map
    ))
    pg = ch["practice"]
    blocks.extend([
        bullet("**1. Chapter Mixed Practice (Multi-Unit Synthesis):**", id_map, children=[
            bullet(pg["mixed"], id_map)
        ]),
        bullet("**2. Combine with Prior Chapters:**", id_map, children=[
            bullet(pg["combine"], id_map)
        ]),
        bullet("**3. Chapter-Wide Traps:**", id_map, children=[
            bullet(pg["traps"], id_map)
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Physics & Code):**", id_map, children=[
            bullet(pg["cross"], id_map)
        ]),
    ])

    blocks.append(divider_block())
    blocks.append(h2("6. Chapter Review & Spaced Retention Guide", id_map))
    blocks.append(bullet("Keep 'Status' (initial study completion) separate from 'Mastery (0-4)' (spontaneous problem-solving fluency without notes).", id_map))
    blocks.append(bullet("When reviewing this Chapter, inspect the 'My Implementation & Mistake Log' inside each Unit first to diagnose recurring unit slips or sign confusions.", id_map))

    return blocks

def build_phy_unit_blocks(uid, u, id_map):
    blocks = [
        callout_block(
            f"**Learning Objective:** {u['obj']}\n"
            f"**Expected Output:** {u['out']}\n"
            f"**Parent:** [[PHY-T01]] → [[{u['chapter']}]] | "
            f"**Prerequisites:** {u['prereq']} | "
            f"**Next Unit:** {u['next']} | "
            f"**Source:** [[R037]] ({u['source']})",
            id_map,
            color="gray_background",
        ),
        h2("1. Core Concepts, Definitions & Physical Intuition", id_map),
    ]
    for c in u["concepts"]:
        blocks.append(bullet(c, id_map))

    blocks.append(divider_block())
    blocks.append(h2("2. Key Formulas, Units & Dimensions", id_map))
    for f in u["formulas"]:
        blocks.append(eq_block(f))

    blocks.append(divider_block())
    blocks.append(h2("3. Step-by-Step Worked Example", id_map))
    blocks.append(p_block(u["worked"], id_map))

    blocks.append(divider_block())
    blocks.append(h2("4. Practice Guide", id_map))
    blocks.append(p_block(
        "Use this blueprint to generate targeted practice problems for this Unit and diagnose calculation slips in Section 6:",
        id_map
    ))
    pg = u["practice"]
    blocks.extend([
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet(pg["core"], id_map)
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet(pg["combine"], id_map)
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet(pg["traps"], id_map)
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Math ↔ Physics ↔ Code):**", id_map, children=[
            bullet(pg["cross"], id_map)
        ]),
    ])

    blocks.append(divider_block())
    blocks.append(h2("5. Active Recall Questions", id_map))
    blocks.append(p_block(
        "Attempt each question from memory on scratch paper before expanding the toggle to verify your reasoning.",
        id_map
    ))
    for q, a in u["recall"]:
        blocks.append(toggle_block(q, [f"**Reference Solution:** {a}"], id_map))

    blocks.append(divider_block())
    blocks.append(h2("6. My Implementation & Mistake Log", id_map))
    blocks.append(p_block("Personal Workspace (Complete after working the practice problems above):", id_map))
    blocks.append(bullet("**Feynman One-Liner (Explain this physical law in your own words):** [Write your 1–2 sentence summary here]", id_map))
    blocks.append(bullet("**My Calculation Slippage & Conceptual Traps:** [Record any unit slips, sign confusions, or formulas you initially mixed up during practice]", id_map))
    blocks.append(bullet("**Experimental Observation / Real-World Analogy:** [Describe a real-world scenario or computer simulation where this physics law manifested]", id_map))

    blocks.append(divider_block())
    blocks.append(h2("7. Completion Checklist & Mastery Review", id_map))
    blocks.append(todo_item(f"State the core definitions and formulas of {u['title']} without looking at notes.", id_map))
    blocks.append(todo_item("Perform the dimensional analysis check for all derived units.", id_map))
    blocks.append(todo_item("Solve all Practice Guide problem types and verify zero sign slips.", id_map))
    blocks.append(todo_item("Answer all Active Recall questions and update 'Mastery (0-4)', 'Last Reviewed', and 'Next Review'.", id_map))

    return blocks

def update_topic(token, id_map):
    print("=== Populating Topic PHY-T01 ===")
    top = PHY_TOPIC_DATA
    pid = id_map["PHY-T01"]["id"]

    # 1. Update properties
    notion_request("PATCH", f"pages/{pid}", token, {
        "properties": {
            "Goal": {"rich_text": parse_rt(top["goal"], id_map)},
            "Resources": {"relation": [{"id": id_map["R037"]["id"]}]},
        }
    })

    # 2. Replace page blocks
    blocks = build_phy_topic_blocks(id_map)
    replace_page_blocks(pid, blocks, "PHY-T01", token)
    print("  Topic PHY-T01 populated successfully!")

def update_chapters(token, id_map):
    print("\n=== Populating Chapters PHY-T01-C01 through C04 ===")
    r037_id = id_map["R037"]["id"]

    for cid, ch in PHY_CHAPTERS_DATA.items():
        pid = id_map[cid]["id"]
        print(f"  [{cid}] {ch['title']}...")

        # 1. Update properties
        notion_request("PATCH", f"pages/{pid}", token, {
            "properties": {
                "Objective": {"rich_text": parse_rt(ch["objective"], id_map)},
                "Completion Criteria": {"rich_text": parse_rt(ch["criteria"], id_map)},
                "Priority": {"select": {"name": "Core"}},
                "Resources": {"relation": [{"id": r037_id}]},
            }
        })

        # 2. Replace page blocks
        blocks = build_phy_chapter_blocks(cid, ch, id_map)
        replace_page_blocks(pid, blocks, cid, token)
        print(f"    [{cid}] Populated {len(blocks)} blocks successfully!")

def update_units(token, id_map):
    print("\n=== Populating Units PHY-T01-C01-U01 through C04-U04 (13 Units) ===")
    r037_id = id_map["R037"]["id"]

    for uid, u in PHY_UNITS_DATA.items():
        pid = id_map[uid]["id"]
        print(f"  [{uid}] {u['title']}...")

        # 1. Update properties
        notion_request("PATCH", f"pages/{pid}", token, {
            "properties": {
                "Learning Objective": {"rich_text": parse_rt(u["obj"], id_map)},
                "Expected Output": {"rich_text": parse_rt(u["out"], id_map)},
                "Priority": {"select": {"name": "Core"}},
                "XP": {"number": 10},
                "Resources": {"relation": [{"id": r037_id}]},
            }
        })

        # 2. Replace page blocks
        blocks = build_phy_unit_blocks(uid, u, id_map)
        replace_page_blocks(pid, blocks, uid, token)
        print(f"    [{uid}] Populated {len(blocks)} blocks successfully!")
        time.sleep(0.1) # Smooth pacing

def main():
    env = load_env()
    token = env.get("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN not set!")

    with open("id_map.json") as f:
        id_map = json.load(f)

    # 1. Populate Topic PHY-T01
    update_topic(token, id_map)

    # 2. Populate Chapters C01 - C04
    update_chapters(token, id_map)

    # 3. Populate Units C01-U01 - C04-U04 (13 Units)
    update_units(token, id_map)

    print("\n=== ALL PHY-T01 PREALGEBRA-COMPATIBLE PAGES POPULATED SUCCESSFULLY! ===")

if __name__ == "__main__":
    main()
