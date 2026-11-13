import json
import re

from apply_rules_and_test_pages import parse_rt, validate_blocks_clean


def md_to_notion_blocks(md_text, id_map):
    lines = md_text.splitlines()
    blocks = []
    i = 0
    n = len(lines)

    while i < n:
        raw_line = lines[i]
        line = raw_line.strip()

        if not line:
            i += 1
            continue

        # Divider
        if line == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            i += 1
            continue

        # Block Equation ($$ ... $$)
        if line.startswith("$$"):
            if line.endswith("$$") and len(line) > 4:
                expr = line[2:-2].strip()
                blocks.append({"object": "block", "type": "equation", "equation": {"expression": expr}})
                i += 1
                continue
            else:
                eq_lines = []
                first = line[2:].strip()
                if first:
                    eq_lines.append(first)
                i += 1
                while i < n and not lines[i].strip().endswith("$$"):
                    eq_lines.append(lines[i])
                    i += 1
                if i < n:
                    last = lines[i].strip()[:-2].strip()
                    if last:
                        eq_lines.append(last)
                    i += 1
                expr = "\n".join(eq_lines)
                blocks.append({"object": "block", "type": "equation", "equation": {"expression": expr}})
                continue

        # Code block (``` ... ```)
        if line.startswith("```"):
            lang = line[3:].strip() or "plain text"
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < n:
                i += 1
            code_content = "\n".join(code_lines)
            blocks.append(
                {
                    "object": "block",
                    "type": "code",
                    "code": {"language": lang, "rich_text": [{"type": "text", "text": {"content": code_content}}]},
                }
            )
            continue

        # Headings
        if raw_line.startswith("### "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": parse_rt(raw_line[4:].strip(), id_map)},
                }
            )
            i += 1
            continue
        if raw_line.startswith("## "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": parse_rt(raw_line[3:].strip(), id_map)},
                }
            )
            i += 1
            continue
        if raw_line.startswith("# "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": parse_rt(raw_line[2:].strip(), id_map)},
                }
            )
            i += 1
            continue

        # Callout block (> ...)
        if line.startswith("> "):
            callout_text = line[2:].strip()
            # If multi-line callout
            i += 1
            while i < n and lines[i].strip().startswith("> "):
                callout_text += "\n" + lines[i].strip()[2:].strip()
                i += 1
            blocks.append(
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {"rich_text": parse_rt(callout_text, id_map), "color": "blue_background"},
                }
            )
            continue

        # To Do (- [ ] or - [x])
        if line.startswith("- [ ] ") or line.startswith("- [x] "):
            chk = line.startswith("- [x] ")
            txt = line[6:].strip()
            blocks.append(
                {"object": "block", "type": "to_do", "to_do": {"checked": chk, "rich_text": parse_rt(txt, id_map)}}
            )
            i += 1
            continue

        # Bullet list item (- ...)
        if line.startswith("- ") or line.startswith("* "):
            txt = line[2:].strip()
            # Check for sub-bullets
            children = []
            i += 1
            while i < n and (
                lines[i].startswith("    - ") or lines[i].startswith("  - ") or lines[i].startswith("\t- ")
            ):
                sub_txt = lines[i].strip()[2:].strip()
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": parse_rt(sub_txt, id_map)},
                    }
                )
                i += 1
            b = {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": parse_rt(txt, id_map)},
            }
            if children:
                b["bulleted_list_item"]["children"] = children
            blocks.append(b)
            continue

        # Numbered list item (1. ...)
        num_m = re.match(r"^(\d+)\.\s+(.*)$", line)
        if num_m:
            txt = num_m.group(2).strip()
            # Check for sub-bullets or sub-items
            children = []
            i += 1
            while i < n and (lines[i].startswith("    ") or lines[i].startswith("\t")):
                sub_line = lines[i].strip()
                if sub_line.startswith("- "):
                    children.append(
                        {
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {"rich_text": parse_rt(sub_line[2:].strip(), id_map)},
                        }
                    )
                elif re.match(r"^\d+\.\s+", sub_line):
                    sub_txt = re.sub(r"^\d+\.\s+", "", sub_line)
                    children.append(
                        {
                            "object": "block",
                            "type": "numbered_list_item",
                            "numbered_list_item": {"rich_text": parse_rt(sub_txt, id_map)},
                        }
                    )
                i += 1
            b = {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": parse_rt(txt, id_map)},
            }
            if children:
                b["numbered_list_item"]["children"] = children
            blocks.append(b)
            continue

        # Fallback to paragraph
        blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": parse_rt(line, id_map)}})
        i += 1

    return blocks


def test():
    with open("id_map.json") as f:
        id_map = json.load(f)

    files = [
        "rules/00_core.md",
        "rules/01_arch.md",
        "rules/02_pedagogy.md",
        "rules/03_stem.md",
        "rules/04_code.md",
        "rules/05_qa.md",
    ]

    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        blocks = md_to_notion_blocks(content, id_map)
        validate_blocks_clean(blocks, label=fp)
        print(f"[{fp}] Parsed {len(blocks)} blocks cleanly!")


if __name__ == "__main__":
    test()
