import json
import re
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    get_all_blocks,
    replace_page_blocks,
    validate_blocks_clean
)
from mth_t01_batch2_data import CHAPTER_DATA
from mth_t01_batch2_units import UNIT_DATA
from upgrade_mth_t01_batch2 import build_unit_blocks, audit_page

def main():
    env = load_env()
    token = env["NOTION_TOKEN"]
    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    u_code = "MTH-T01-C09-U06"
    u_data = UNIT_DATA[u_code]
    pid = id_map[u_code]["id"]
    print(f"Finishing Unit: {u_code} ({u_data['title']})...")
    
    u_blocks = build_unit_blocks(u_code, u_data, id_map, preserved_user_notes=[])
    validate_blocks_clean(u_blocks, label=u_code)
    replace_page_blocks(pid, u_blocks, label=u_code, token=token)

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
    print(f"  Unit {u_code} updated successfully ({len(u_blocks)} blocks)!")

    # Final Audit across all 35 pages
    batch2_chapters = ["MTH-T01-C05", "MTH-T01-C06", "MTH-T01-C07", "MTH-T01-C08", "MTH-T01-C09"]
    print("\n========================================================")
    print("RUNNING FINAL NOTION API AUDIT (35 PAGES)")
    print("========================================================")
    all_passed = True
    for ch_code in batch2_chapters:
        passed = audit_page(id_map[ch_code]["id"], ch_code, id_map, token)
        if not passed:
            all_passed = False
        for u in CHAPTER_DATA[ch_code]["units"]:
            passed_u = audit_page(id_map[u]["id"], u, id_map, token)
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
