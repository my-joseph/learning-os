import json
import re

from apply_rules_and_test_pages import (
    bullet,
    callout_block,
    divider_block,
    eq_block,
    h2,
    h3,
    num_item,
    p_block,
    replace_page_blocks,
    todo_item,
    toggle_block,
    validate_blocks_clean,
)
from mth_t01_batch2_data import CHAPTER_DATA
from mth_t01_batch2_units import UNIT_DATA
from notion_sync.client import get_all_blocks, load_env, notion_request
from page_audit import audit_page  # noqa: F401  (re-export for finish_batch2_and_audit.py)


def build_chapter_blocks(ch_code, ch_data, id_map, preserved_drill_logs):
    units_mentions = " ".join(f"[[{u}]]" for u in ch_data["units"])
    blocks = [
        # Callout Header
        callout_block(
            f"**Chapter Objective:** {ch_data['objective']}\n\n"
            f"**Parent Topic:** [[MTH-T01]] | **Resource:** [[R035]] | **Level:** Prealgebra Foundation | **Units:** {len(ch_data['units'])} Units ({units_mentions})",
            id_map,
            color="blue_background",
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
    blocks.append(
        p_block(
            "Complete the Units in ascending numerical order. Master each unit's definitions, properties, and practice guides:",
            id_map,
        )
    )
    for u in ch_data["units"]:
        u_info = UNIT_DATA.get(u, {})
        u_title = u_info.get("title", id_map.get(u, {}).get("title", ""))
        u_obj = u_info.get("objective", "")
        blocks.append(num_item(f"**[[{u}]] — {u_title}:** {u_obj}", id_map))
    blocks.append(divider_block())

    # Section 4: Level 2 Chapter Practice Guide
    pg = ch_data["practice_guide"]
    blocks.extend(
        [
            h2("Practice Guide", id_map),
            p_block(
                "This Chapter Practice Guide directs AI drill engines and independent review across 4 core competencies:",
                id_map,
            ),
            h3("1. Conceptual Check", id_map),
        ]
    )
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
    blocks.extend(
        [
            h2("Active Recall Questions", id_map),
            p_block(
                "Attempt each synthesis question mentally or on scratch paper before expanding the toggle:", id_map
            ),
        ]
    )
    for ar in ch_data["active_recall"]:
        blocks.append(toggle_block(ar["q"], [f"**Reference Solution:** {ar['a']}"], id_map))
    blocks.append(divider_block())

    # Section 6: Chapter Synthesis & Problem-Solving Challenge
    blocks.extend(
        [
            h2("Chapter Synthesis & Problem-Solving Challenge", id_map),
            todo_item(
                f"Synthesize the core invariants of {ch_data['title']} and explain their connection to [[MTH-T01]].",
                id_map,
            ),
            todo_item(
                "Complete all 4 categories in the Practice Guide and evaluate performance in the Practice Hub.", id_map
            ),
            divider_block(),
            # Section 7: Chapter Review & Spaced Retention Guide
            h2("Chapter Review & Spaced Retention Guide", id_map),
            bullet(
                "Keep 'Status' (initial completion) separate from 'Mastery (0-4)' (long-term recall and problem-solving fluency).",
                id_map,
            ),
            bullet(
                "When reviewing this Chapter, inspect the 'My Implementation & Mistake Log' inside each Unit first to target past calculation, sign, or algebraic trap errors.",
                id_map,
            ),
        ]
    )

    # Append preserved drill logs
    if preserved_drill_logs:
        for b in preserved_drill_logs:
            bt = b["type"]
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": b[bt]["rich_text"]},
                }
            )

    return blocks


def build_unit_blocks(u_code, u_data, id_map, preserved_user_notes):
    ch_code = u_data["chapter"]
    blocks = [
        # Callout Header
        callout_block(
            f"**Learning Objective:** {u_data['objective']}\n\n"
            f"**Parent Chapter:** [[{ch_code}]] | **Parent Topic:** [[MTH-T01]] | **Resource:** [[R035]] | **Time Est:** 45 mins | **Priority:** Core | **XP:** 10",
            id_map,
            color="gray_background",
        ),
        divider_block(),
        # Section 1: Core Concepts
        h2("Core Concepts, Definitions & Mathematical Intuition", id_map),
    ]
    for conc in u_data["concepts"]:
        blocks.append(bullet(conc, id_map))
    blocks.append(divider_block())

    # Section 2: Formulas
    blocks.append(h2("Key Formulas, Properties & Identities", id_map))
    for f in u_data["formulas"]:
        blocks.append(eq_block(f))
    blocks.append(divider_block())

    # Section 3: Worked Example
    ex = u_data["example"]
    blocks.extend(
        [
            h2("Step-by-Step Worked Example", id_map),
            p_block(f"**Example ({ex['title']}):**", id_map),
        ]
    )
    for step in ex["steps"]:
        if step.startswith("\\") or ("=" in step and step.startswith(" ")):
            blocks.append(eq_block(step))
        else:
            blocks.append(p_block(step, id_map))
    blocks.append(divider_block())

    # Section 4: Level 1 Unit Practice Guide
    pg = u_data["practice_guide"]
    blocks.extend(
        [
            h2("Practice Guide", id_map),
            p_block("AI drill generators and learners should structure practice across these 4 categories:", id_map),
            h3("1. Conceptual Check", id_map),
        ]
    )
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
    blocks.extend(
        [
            h2("Active Recall Questions", id_map),
            p_block("Attempt each question from memory before expanding the toggle:", id_map),
        ]
    )
    for ar in u_data["active_recall"]:
        blocks.append(toggle_block(ar["q"], [f"**Reference Solution:** {ar['a']}"], id_map))
    blocks.append(divider_block())

    # Section 6: Mistake Log
    blocks.extend(
        [
            h2("My Implementation & Mistake Log", id_map),
            bullet("**Feynman One-Liner:** [Explain this mathematical concept in your own words]", id_map),
            bullet(
                "**My Worked Solutions & Derivations:** [Record your scratch work and step-by-step calculations]",
                id_map,
            ),
            bullet(
                "**Mistake & Algebraic Trap Log:** [Record any calculation errors, sign mistakes, or formula mixups]",
                id_map,
            ),
            divider_block(),
            # Section 7: Completion Checklist
            h2("Completion Checklist & Mastery Review", id_map),
            todo_item(
                f"State the core definitions and invariants of {u_data['title']} without looking at notes.", id_map
            ),
            todo_item(
                "Complete all 4 categories in the Practice Guide and record reflections in the Mistake Log.", id_map
            ),
            todo_item("Answer all Active Recall questions from memory and update 'Mastery (0-4)'.", id_map),
        ]
    )

    return blocks


def main():
    env = load_env()
    token = env["NOTION_TOKEN"]
    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    batch2_chapters = ["MTH-T01-C05", "MTH-T01-C06", "MTH-T01-C07", "MTH-T01-C08", "MTH-T01-C09"]

    print("\n========================================================")
    print("UPGRADING MTH-T01 BATCH 2 (CHAPTERS C05–C09: 35 PAGES)")
    print("========================================================")

    # 1. Process Chapters
    for ch_code in batch2_chapters:
        ch_data = CHAPTER_DATA[ch_code]
        pid = id_map[ch_code]["id"]
        print(f"\nProcessing Chapter: {ch_code} ({ch_data['title']})...")

        # Check preserved logs
        existing = get_all_blocks(pid, token)
        drill_logs = []
        for b in existing:
            bt = b["type"]
            txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
            if "Score " in txt and "Drill" in txt:
                drill_logs.append(b)

        ch_blocks = build_chapter_blocks(ch_code, ch_data, id_map, drill_logs)
        validate_blocks_clean(ch_blocks, label=ch_code)
        replace_page_blocks(pid, ch_blocks, label=ch_code, token=token)

        # Update Objective property without touching user Status
        notion_request(
            "PATCH",
            f"pages/{pid}",
            token,
            {"properties": {"Objective": {"rich_text": [{"type": "text", "text": {"content": ch_data["objective"]}}]}}},
        )
        print(f"  Chapter {ch_code} updated successfully ({len(ch_blocks)} blocks)!")

    # 2. Process Units
    unit_codes = sorted(list(UNIT_DATA.keys()))
    print(f"\nProcessing {len(unit_codes)} Units across Batch 2...")
    for u_code in unit_codes:
        u_data = UNIT_DATA[u_code]
        pid = id_map[u_code]["id"]
        print(f"  Upgrading Unit: {u_code} ({u_data['title']})...")

        u_blocks = build_unit_blocks(u_code, u_data, id_map, preserved_user_notes=[])
        validate_blocks_clean(u_blocks, label=u_code)
        replace_page_blocks(pid, u_blocks, label=u_code, token=token)

        # Update instructional properties (DO NOT touch Status or Mastery)
        notion_request(
            "PATCH",
            f"pages/{pid}",
            token,
            {
                "properties": {
                    "Learning Objective": {"rich_text": [{"type": "text", "text": {"content": u_data["objective"]}}]},
                    "Expected Output": {
                        "rich_text": [{"type": "text", "text": {"content": u_data["expected_output"]}}]
                    },
                    "Priority": {"select": {"name": "Core"}},
                    "XP": {"number": 10},
                }
            },
        )

    # 3. Final Audit across all 35 pages
    print("\n========================================================")
    print("RUNNING FINAL NOTION API AUDIT (35 PAGES)")
    print("========================================================")
    all_passed = True
    for ch_code in batch2_chapters:
        passed = audit_page(id_map[ch_code]["id"], ch_code, id_map, token)
        if not passed:
            all_passed = False
        for u_code in CHAPTER_DATA[ch_code]["units"]:
            passed_u = audit_page(id_map[u_code]["id"], u_code, id_map, token)
            if not passed_u:
                all_passed = False

    print("\n--------------------------------------------------------")
    if all_passed:
        print("ALL 35 PAGES OF MTH-T01 BATCH 2 AUDITED AND VERIFIED 100% CLEAN AND PASSING!")
    else:
        print("WARNING: Some pages had audit warnings!")
    print("--------------------------------------------------------\n")


if __name__ == "__main__":
    main()
