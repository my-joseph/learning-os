# -*- coding: utf-8 -*-
"""Post-write audit of a Notion page: counts live @page mentions and finds curriculum
codes (MTH-/PHY-/PRG-/Rnnn) left as plain text instead of links (05_qa: unlinked = 0)."""

import re

from notion_sync.client import get_all_blocks


def audit_page(page_id, code, id_map, token):
    blocks = get_all_blocks(page_id, token)
    code_pattern = re.compile(
        r"\b(MTH-T\d+(?:-C\d+(?:-U\d+)?)?|PHY-T\d+(?:-C\d+(?:-U\d+)?)?|PRG-T\d+(?:-C\d+(?:-U\d+)?)?|R\d{3})\b"
    )

    mentions = 0
    unlinked = []

    for b in blocks:
        bt = b["type"]
        rt = b.get(bt, {}).get("rich_text", [])
        for t in rt:
            if t.get("type") == "mention" and t.get("mention", {}).get("type") == "page":
                mentions += 1
            elif t.get("type") == "text":
                for m in code_pattern.finditer(t.get("plain_text", "")):
                    unlinked.append((m.group(1), b["id"]))

    status = "PASS" if len(unlinked) == 0 else "FAIL"
    print(f"[{status}] {code:<16} Blocks={len(blocks):<2} | Mentions={mentions:<2} | Unlinked={len(unlinked)}")
    if unlinked:
        print(f"  Unlinked tokens: {unlinked}")
    return len(unlinked) == 0
