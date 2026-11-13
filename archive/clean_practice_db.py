# -*- coding: utf-8 -*-
"""
Cleans up the Notion 'Learning Practice & Drills' database:
1. Removes temporary/duplicate test drills.
2. Resets canonical drills/labs to a clean initial state (Score: 0, Status: 'Ready', Mistake Categories: []).
3. Updates id_map.json accordingly.
"""
import json
from apply_rules_and_test_pages import load_env, notion_request

DRILLS_DB_ID = "40d3818f-8ba0-8125-8cae-ea0de6183186"

CANONICAL_KEEP = {
    "DRL-MTH-T02-C01-U01-01": {"max_score": 5, "q_count": 5},
    "DRL-PRG-T01-C01-01": {"max_score": 5, "q_count": 5},
    "DRL-PRG-T01-C03-01": {"max_score": 3, "q_count": 3},
    "DRL-PRG-T03-C01-U01-01": {"max_score": 10, "q_count": 10},
    "LAB-PRG-T03-C01-01": {"max_score": 100, "q_count": 4},
}

def clean_database():
    env = load_env()
    token = env.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN not set")

    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    print("=== Fetching all records from 'Learning Practice & Drills' ===")
    res = notion_request("POST", f"databases/{DRILLS_DB_ID}/query", token, {"page_size": 100})
    records = res.get("results", [])
    print(f"Found {len(records)} records in database.")

    for r in records:
        pid = r["id"]
        props = r["properties"]
        drill_id_list = props.get("Drill ID", {}).get("rich_text", [])
        drill_id = drill_id_list[0]["plain_text"] if drill_id_list else ""

        if drill_id in CANONICAL_KEEP:
            cfg = CANONICAL_KEEP[drill_id]
            print(f"  [RESET] Resetting canonical drill/lab: {drill_id} ({pid})")
            patch_payload = {
                "properties": {
                    "Practice Status": {"select": {"name": "Ready"}},
                    "Score": {"number": 0},
                    "Max Score": {"number": cfg["max_score"]},
                    "Mistake Categories": {"multi_select": []},
                    "Diverged Steps Summary": {"rich_text": [{"type": "text", "text": {"content": "Fresh drill session ready to begin."}}]},
                    "Attempt Date": {"date": None},
                }
            }
            notion_request("PATCH", f"pages/{pid}", token, patch_payload)
            id_map[drill_id] = {"id": pid, "title": props.get("Drill", {}).get("title", [{}])[0].get("plain_text", drill_id)}
        else:
            print(f"  [DELETE] Deleting temporary test drill: {drill_id} ({pid})")
            notion_request("DELETE", f"blocks/{pid}", token)
            if drill_id in id_map:
                del id_map[drill_id]

    with open("id_map.json", "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)

    print("✔ Practice database successfully cleaned and sanitized!")

if __name__ == "__main__":
    clean_database()
