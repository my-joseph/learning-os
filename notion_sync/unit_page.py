"""Write or extend a Unit/Chapter page from a JSON spec, without ever touching the learner's workspace.

Pages follow `rules/02_pedagogy.md` §7a (v4). Two modes:
- `new`: the page must be empty (0 blocks); the whole spec is appended.
- `add`: blocks are inserted at the end of the section whose heading contains `--after`. Nothing is deleted.
  The learner's section ("My Implementation & Mistake Log") can never be the target.

Spec: a JSON list of blocks, each `{"type": ..., "text": ..., "children": [...]}` with types
h2, h3, p, bullet, num, todo, callout, quote, eq (`"expr"` instead of `text`), toggle (`children` = answer
blocks) and divider. Text supports `**bold**`, inline `$math$` and `[[CODE]]` page mentions (resolved via
id_map.json). Write the spec as JSON, never as Python strings (LaTeX backslashes).

    python -m notion_sync.unit_page --code MTH-T02-C01-U02 --spec scratch/pages/U02.json --mode new
    python -m notion_sync.unit_page --code MTH-T01-C04-U04 --spec ex3.json --mode add --after "Worked Example"
    ... --dry-run   # build and validate the blocks, print a summary, send nothing
"""

from __future__ import annotations

import argparse
import json
import sys

from notion_sync.blocks import (
    bullet,
    callout_block,
    divider_block,
    eq_block,
    h2,
    h3,
    num_item,
    p_block,
    quote_block,
    todo_item,
    toggle_block,
    validate_blocks_clean,
)
from notion_sync.client import get_all_blocks, load_env, notion_request, require_token

LEARNER_SECTION = "My Implementation"
HEADINGS = ("heading_1", "heading_2", "heading_3")


def spec_to_blocks(spec: list[dict], id_map: dict) -> list[dict]:
    out = []
    for item in spec:
        kind, text = item.get("type"), item.get("text", "")
        kids = spec_to_blocks(item.get("children", []), id_map) if item.get("children") else None
        if kind == "h2":
            out.append(h2(text, id_map))
        elif kind == "h3":
            out.append(h3(text, id_map))
        elif kind == "p":
            out.append(p_block(text, id_map))
        elif kind == "bullet":
            out.append(bullet(text, id_map, kids))
        elif kind == "num":
            out.append(num_item(text, id_map, kids))
        elif kind == "todo":
            out.append(todo_item(text, id_map, bool(item.get("checked"))))
        elif kind == "callout":
            out.append(callout_block(text, id_map, item.get("color", "gray_background")))
        elif kind == "quote":
            out.append(quote_block(text, id_map))
        elif kind == "eq":
            out.append(eq_block(item["expr"]))
        elif kind == "toggle":
            out.append(toggle_block(text, kids or [], id_map))
        elif kind == "divider":
            out.append(divider_block())
        else:
            raise ValueError(f"unknown block type {kind!r}")
    return out


def heading_text(block: dict) -> str:
    t = block.get("type")
    if t not in HEADINGS:
        return ""
    return "".join(r.get("plain_text") or r.get("text", {}).get("content", "") for r in block[t].get("rich_text", []))


def section_end(blocks: list[dict], heading_contains: str) -> str | None:
    """Id of the last top-level block in the section whose heading contains the text (the heading itself
    if the section is empty), or None if there is no such heading. A section ends at the next heading of
    the same or a higher level."""
    start = next((i for i, b in enumerate(blocks) if heading_contains.lower() in heading_text(b).lower()), None)
    if start is None:
        return None
    level = HEADINGS.index(blocks[start]["type"])
    end = start
    for i in range(start + 1, len(blocks)):
        t = blocks[i].get("type")
        if t in HEADINGS and HEADINGS.index(t) <= level:
            break
        end = i
    return blocks[end]["id"]


def insert_after(parent_id: str, after_id: str | None, blocks: list[dict], token: str, chunk: int = 50) -> None:
    """Insert blocks in order after `after_id` (append at the end when None)."""
    for i in range(0, len(blocks), chunk):
        payload: dict = {"children": blocks[i : i + chunk]}
        if after_id:
            payload["after"] = after_id
        res = notion_request("PATCH", f"blocks/{parent_id}/children", token, payload)
        results = res.get("results") or []
        if after_id and results:
            after_id = results[-1]["id"]


def write_page(code: str, spec: list[dict], mode: str, after: str | None, token: str, id_map: dict) -> str:
    entry = id_map.get(code)
    if not isinstance(entry, dict):
        raise ValueError(f"{code} is not in id_map.json")
    blocks = spec_to_blocks(spec, id_map)
    validate_blocks_clean(blocks, code)
    existing = get_all_blocks(entry["id"], token)
    if mode == "new":
        if existing:
            raise ValueError(f"{code} already has {len(existing)} blocks; use --mode add (never rewrite a page)")
        insert_after(entry["id"], None, blocks, token)
        return f"wrote {len(blocks)} blocks to empty page {code}"
    if not after:
        raise ValueError("--mode add needs --after <heading text>")
    if LEARNER_SECTION.lower() in after.lower():
        raise ValueError("the learner's section is never edited by agents (rules/02 §7a)")
    anchor = section_end(existing, after)
    if anchor is None:
        raise ValueError(f"no heading containing {after!r} on {code}")
    insert_after(entry["id"], anchor, blocks, token)
    return f"inserted {len(blocks)} blocks into section {after!r} of {code}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m notion_sync.unit_page", description=__doc__.split("\n\n")[0])
    ap.add_argument("--code", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--mode", choices=("new", "add"), required=True)
    ap.add_argument("--after", help="heading text of the section to extend (mode add)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    with open("id_map.json", encoding="utf-8") as f:
        id_map = json.load(f)
    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    if args.dry_run:
        blocks = spec_to_blocks(spec, id_map)
        validate_blocks_clean(blocks, args.code)
        print(f"dry run: {len(blocks)} top-level blocks for {args.code} ({args.mode}); nothing sent")
        return 0
    try:
        print(write_page(args.code, spec, args.mode, args.after, require_token(load_env().get("NOTION_TOKEN")), id_map))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
