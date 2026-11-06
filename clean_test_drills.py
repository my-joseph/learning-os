# -*- coding: utf-8 -*-
"""
Script to clean up all old test drills both locally and in Notion.
Preserves ONLY DRL-MTH-T01-C12-04.
"""
import glob
import json
import os
import shutil
from apply_rules_and_test_pages import load_env, notion_request

DRILLS_DB_ID = "40d3818f-8ba0-8125-8cae-ea0de6183186"
KEEP_DRILL_ID = "DRL-MTH-T01-C12-04"

def clean_notion_drills(token):
    print("--- 1. CLEANING NOTION DRILLS DATABASE ---")
    res = notion_request("POST", f"databases/{DRILLS_DB_ID}/query", token, {})
    results = res.get("results", [])
    archived_count = 0
    kept_count = 0

    for r in results:
        pid = r["id"]
        drill_id_list = r["properties"].get("Drill ID", {}).get("rich_text", [])
        drill_id = drill_id_list[0].get("plain_text", "") if drill_id_list else ""

        if drill_id == KEEP_DRILL_ID:
            print(f"  [KEEP] Preserving {drill_id} (Page ID: {pid})")
            kept_count += 1
        else:
            print(f"  [ARCHIVE] Deleting test drill {drill_id} (Page ID: {pid})...", end="", flush=True)
            notion_request("PATCH", f"pages/{pid}", token, {"archived": True})
            print(" DONE")
            archived_count += 1

    print(f"Notion Clean Summary: {archived_count} test drills archived, {kept_count} kept.")

def clean_local_drills():
    print("\n--- 2. CLEANING LOCAL DRILL FILES & WORKSPACES ---")
    deleted_files = 0
    deleted_workspaces = 0

    # 1. Clean drills/data
    for fpath in glob.glob("drills/data/**/*.json", recursive=True):
        fname = os.path.basename(fpath)
        if KEEP_DRILL_ID in fname:
            print(f"  [KEEP] Preserving data file: {fpath}")
        else:
            print(f"  [DELETE] Removing test data file: {fpath}")
            os.remove(fpath)
            deleted_files += 1

    # Remove empty directories in drills/data
    for root, dirs, files in os.walk("drills/data", topdown=False):
        for d in dirs:
            dirpath = os.path.join(root, d)
            if not os.listdir(dirpath):
                print(f"  [REMOVE EMPTY DIR] {dirpath}")
                os.rmdir(dirpath)

    # 2. Clean drills/workspace
    if os.path.exists("drills/workspace"):
        for item in os.listdir("drills/workspace"):
            wpath = os.path.join("drills/workspace", item)
            if os.path.isdir(wpath):
                if item == KEEP_DRILL_ID:
                    print(f"  [KEEP] Preserving workspace: {wpath}")
                else:
                    print(f"  [DELETE] Removing test workspace: {wpath}")
                    shutil.rmtree(wpath)
                    deleted_workspaces += 1

    print(f"Local Clean Summary: {deleted_files} files deleted, {deleted_workspaces} workspaces deleted.")

def clean_id_map():
    print("\n--- 3. CLEANING ID_MAP.JSON ---")
    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    keys_to_remove = []
    for k in id_map:
        if (k.startswith("DRL-") or k.startswith("LAB-")) and k != KEEP_DRILL_ID:
            keys_to_remove.append(k)

    for k in keys_to_remove:
        print(f"  [REMOVE] id_map key: {k}")
        del id_map[k]

    with open("id_map.json", "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)

    print(f"id_map Clean Summary: {len(keys_to_remove)} keys removed.")

def main():
    env = load_env(".env")
    token = env["NOTION_TOKEN"]

    clean_notion_drills(token)
    clean_local_drills()
    clean_id_map()
    print("\n🎉 ALL TEST DRILLS CLEANED SUCCESSFULLY (Only DRL-MTH-T01-C12-04 preserved)!")

if __name__ == "__main__":
    main()
