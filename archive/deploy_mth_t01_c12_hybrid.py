import json
import re
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    get_all_blocks,
    replace_page_blocks
)
from mth_t01_c12_hybrid_builder import (
    build_mth_t01_c12_blocks,
    build_mth_t01_c12_u03_blocks,
    validate_blocks_clean
)

def audit_page(page_id, code, id_map, token):
    blocks = get_all_blocks(page_id, token)
    code_pattern = re.compile(r'\b(MTH-T\d+(?:-C\d+(?:-U\d+)?)?|PHY-T\d+(?:-C\d+(?:-U\d+)?)?|PRG-T\d+(?:-C\d+(?:-U\d+)?)?|R\d{3})\b')
    
    mentions = 0
    images = 0
    equations = 0
    unlinked = []
    
    for b in blocks:
        bt = b["type"]
        if bt == "image":
            images += 1
        elif bt == "equation":
            equations += 1
        rt = b.get(bt, {}).get("rich_text", [])
        for t in rt:
            if t.get("type") == "mention" and t.get("mention", {}).get("type") == "page":
                mentions += 1
            elif t.get("type") == "text":
                for m in code_pattern.finditer(t.get("plain_text", "")):
                    unlinked.append((m.group(1), b["id"]))
                    
    print(f"[{'PASS' if len(unlinked) == 0 else 'FAIL'}] {code:<15} Blocks={len(blocks):<2} | Images={images} | Equations={equations:<2} | Mentions={mentions:<2} | Unlinked={len(unlinked)}")
    if unlinked:
        print(f"  Unlinked tokens: {unlinked}")
    return len(unlinked) == 0

def main():
    env = load_env()
    token = env["NOTION_TOKEN"]
    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)
    with open("uploaded_image_ids.json", "r", encoding="utf-8") as f:
        img_map = json.load(f)
    with open("uploaded_param_ids.json", "r", encoding="utf-8") as f:
        param_img_map = json.load(f)

    # 1. MTH-T01-C12
    pid_c12 = id_map["MTH-T01-C12"]["id"]
    print(f"\n--- Processing MTH-T01-C12 ({pid_c12}) ---")
    c12_existing = get_all_blocks(pid_c12, token)
    
    # Extract historical drill logs
    drill_logs = []
    for b in c12_existing:
        bt = b["type"]
        txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
        if "Score " in txt and "Drill" in txt:
            drill_logs.append(b)
    print(f"Preserved {len(drill_logs)} historical user drill logs from MTH-T01-C12.")

    c12_blocks = build_mth_t01_c12_blocks(id_map, drill_logs, img_map, param_img_map=param_img_map)
    validate_blocks_clean(c12_blocks, label="MTH-T01-C12")
    replace_page_blocks(pid_c12, c12_blocks, label="MTH-T01-C12", token=token)
    print(f"MTH-T01-C12 updated with BOTH Baseline and Parametric diagrams ({len(c12_blocks)} blocks)!")

    # 2. Audit
    print("\n--- Running Final Notion API Audit Verification ---")
    pass_c12 = audit_page(pid_c12, "MTH-T01-C12", id_map, token)

    if pass_c12:
        print("\nMTH-T01-C12 UPDATED WITH COMPARISON VIEW AND VERIFIED 100% CLEAN!")
    else:
        print("\nWARNING: Audit detected issues!")

if __name__ == "__main__":
    main()
