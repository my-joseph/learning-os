"""Write or extend a Unit/Chapter page from a JSON spec, without ever touching the learner's workspace.

Pages follow `rules/02_pedagogy.md` §7a (MTH/PHY) and §7b (PRG). Two modes:
- `new`: the page must be empty (0 blocks); the whole spec is appended.
- `add`: blocks are inserted at the end of the section whose heading contains `--after`. Nothing is deleted.
  The learner's section ("My Implementation & Mistake Log") can never be the target.

Spec: a JSON list of blocks, each `{"type": ..., "text": ..., "children": [...]}` with types
h2, h3, p, bullet, num, todo, callout, quote, eq (`"expr"` instead of `text`), code (`"code"` and `"lang"`),
toggle (`children` = answer blocks), divider and figure (`"fn"` + `"args"` of a `math_engine.figure_builder`
builder, or a ready `"figure"` spec, plus an optional `"caption"`; rendered to SVG and uploaded to Notion, see
`notion_sync.figures`). Text supports `**bold**`, inline `$math$`, `` `code` `` and `[[CODE]]` page mentions
(resolved via id_map.json; `[[...]]` inside `code` blocks is never resolved). Write the spec as JSON, never as
Python strings (LaTeX backslashes).

    python -m notion_sync.unit_page --code MTH-T02-C01-U02 --spec scratch/pages/U02.json --mode new
    python -m notion_sync.unit_page --code MTH-T01-C04-U04 --spec ex3.json --mode add --after "Worked Example"
    python -m notion_sync.unit_page --code MTH-T02-C01-U02 --set "Learning Objective=..." --set "Status=In progress"
    ... --dry-run   # validate the blocks and the target (page empty / heading exists), send nothing
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys

from math_engine.figure_svg import figure_to_svg
from notion_sync.blocks import (
    bullet,
    callout_block,
    code_block,
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
from notion_sync.figures import (
    Uploader,
    caption_rich_text,
    check_plain_math,
    dry_run_uploader,
    figure_block,
    figure_from_spec,
    upload_svg,
)

LEARNER_SECTION = "My Implementation"
HEADINGS = ("heading_1", "heading_2", "heading_3")


def spec_to_blocks(
    spec: list[dict], id_map: dict, uploader: Uploader = dry_run_uploader, prefix: str = "fig"
) -> list[dict]:
    """Notion blocks for a page spec. Figures are rendered and handed to `uploader` (default: nothing sent)."""
    out = []
    count = [0]

    def upload(svg: str, filename: str) -> str:
        count[0] += 1
        return uploader(svg, f"{prefix}-{count[0]}.svg")

    for item in spec:
        kind, text = item.get("type"), item.get("text", "")
        check_plain_math(text, f"{kind} block")
        kids = spec_to_blocks(item.get("children", []), id_map, upload, prefix) if item.get("children") else None
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
        elif kind == "code":
            out.append(code_block(item["code"], item.get("lang", "plain text")))
        elif kind == "toggle":
            out.append(toggle_block(text, kids or [], id_map))
        elif kind == "divider":
            out.append(divider_block())
        elif kind == "figure":
            out.append(figure_block(item, upload, id_map=id_map))
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
    # A section that closes with a divider: insert above the divider, so new blocks stay inside the section.
    while end > start and blocks[end].get("type") == "divider":
        end -= 1
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


def set_properties(code: str, values: dict[str, str], token: str, id_map: dict) -> list[str]:
    """Set page properties by name: text (rich_text/title), status, select, number, or relation (comma-separated
    id_map codes such as `Resources=R036`; added to the existing links, never replacing them). `Mastery (0-4)`
    is refused (drill sync sets it from evidence). Returns the names that were set."""
    if any(name.startswith("Mastery") for name in values):
        raise ValueError("Mastery is set from drill evidence, never by hand (rules/01 §9)")
    page_id = id_map[code]["id"]
    props = notion_request("GET", f"pages/{page_id}", token).get("properties", {})
    patch = {}
    for name, value in values.items():
        if name not in props:
            raise ValueError(f"{code} has no property {name!r}; it has {sorted(props)}")
        kind = props[name]["type"]
        if kind in ("rich_text", "title"):
            patch[name] = {kind: [{"type": "text", "text": {"content": value[:1900]}}]}
        elif kind in ("status", "select"):
            patch[name] = {kind: {"name": value}}
        elif kind == "number":
            patch[name] = {"number": float(value)}
        elif kind == "relation":
            codes = [c.strip() for c in value.split(",") if c.strip()]
            unknown = [c for c in codes if not isinstance(id_map.get(c), dict)]
            if unknown:
                raise ValueError(
                    f"{name}: {unknown} not in id_map.json (look up the code, e.g. the OpenStax book's R0xx)"
                )
            current = [r["id"] for r in props[name].get("relation", [])]
            norm = {i.replace("-", "") for i in current}
            added = [id_map[c]["id"] for c in codes if id_map[c]["id"].replace("-", "") not in norm]
            patch[name] = {"relation": [{"id": i} for i in current + added]}
        else:
            raise ValueError(f"property {name!r} is of type {kind}; this tool cannot set it (log a tool-gap)")
    notion_request("PATCH", f"pages/{page_id}", token, {"properties": patch})
    return list(patch)


def is_blank(block: dict) -> bool:
    """An empty paragraph (what Notion leaves on a page someone clicked into) is not content."""
    if block.get("type") != "paragraph" or block.get("has_children"):
        return False
    rich = block.get("paragraph", {}).get("rich_text") or []
    return not "".join(r.get("plain_text") or r.get("text", {}).get("content", "") for r in rich).strip()


def check_target(code: str, mode: str, after: str | None, existing: list[dict]) -> str | None:
    """Validate the target before writing (also used by --dry-run). Returns the block to insert after."""
    if mode == "new":
        content = [b for b in existing if not is_blank(b)]
        if content:
            raise ValueError(f"{code} already has {len(content)} blocks; use --mode add (never rewrite a page)")
        return None  # an empty paragraph Notion leaves on a fresh page counts as empty; it is kept, not deleted
    if not after:
        raise ValueError("--mode add needs --after <heading text>")
    if LEARNER_SECTION.lower() in after.lower():
        raise ValueError("the learner's section is never edited by agents (rules/02 §7a)")
    anchor = section_end(existing, after)
    if anchor is None:
        raise ValueError(f"no heading containing {after!r} on {code}")
    return anchor


def _image_at(code: str, number: int, token: str, id_map: dict) -> dict:
    """The page's `number`-th top-level image (1-based); refuses one in the learner's section."""
    blocks = get_all_blocks(id_map[code]["id"], token)
    learner = next((i for i, b in enumerate(blocks) if LEARNER_SECTION.lower() in heading_text(b).lower()), None)
    images = [(i, b) for i, b in enumerate(blocks) if b.get("type") == "image"]
    if not 1 <= number <= len(images):
        raise ValueError(f"{code} has {len(images)} image(s); --recaption number must be 1..{len(images)}")
    idx, block = images[number - 1]
    if (
        learner is not None
        and idx > learner
        and not any(blocks[j].get("type") == "heading_2" for j in range(learner + 1, idx))
    ):
        raise ValueError("that image is in the learner's section; agents never edit it (rules/02 §7a)")
    return block


def recaption(code: str, number: int, caption: str, token: str, id_map: dict, dry_run: bool = False) -> str:
    """Replace the caption of the page's `number`-th top-level image (1-based). Only image captions can be
    edited this way, never an image in the learner's section; the image itself is kept."""
    rich = caption_rich_text(caption, id_map)
    block = _image_at(code, number, token, id_map)
    if dry_run:
        return f"dry run: would recaption image {number} of {code}"
    notion_request("PATCH", f"blocks/{block['id']}", token, {"image": {"caption": rich}})
    return f"recaptioned image {number} of {code}"


def refigure(code: str, number: int, item: dict, token: str, id_map: dict, dry_run: bool = False) -> str:
    """Redraw the page's `number`-th image from a figure spec item (`{"fn": ..., "args": ...}` or
    `{"figure": {...}}`, optional `title`, `caption`): the new SVG replaces the file in the same block, so the
    block keeps its place. The caption is kept unless the item gives one."""
    check_plain_math(item.get("caption", ""), "figure caption")
    svg = figure_to_svg(figure_from_spec(item))  # build before touching anything
    block = _image_at(code, number, token, id_map)
    if dry_run:
        return f"dry run: would redraw image {number} of {code}"
    # An update names the new file only; Notion refuses "type" on PATCH.
    payload: dict = {"file_upload": {"id": upload_svg(svg, f"{code}-fig{number}.svg", token)}}
    payload["caption"] = (
        caption_rich_text(item["caption"], id_map) if item.get("caption") else block["image"].get("caption", [])
    )
    notion_request("PATCH", f"blocks/{block['id']}", token, {"image": payload})
    return f"redrew image {number} of {code}"


def write_page(code: str, spec: list[dict], mode: str, after: str | None, token: str, id_map: dict) -> str:
    entry = id_map.get(code)
    if not isinstance(entry, dict):
        raise ValueError(f"{code} is not in id_map.json")
    validate_blocks_clean(spec_to_blocks(spec, id_map), code)  # every figure builds before anything is uploaded
    existing = get_all_blocks(entry["id"], token)
    anchor = check_target(code, mode, after, existing)
    blocks = spec_to_blocks(spec, id_map, lambda svg, name: upload_svg(svg, name, token), code)
    insert_after(entry["id"], anchor, blocks, token)
    if mode == "new":
        return f"wrote {len(blocks)} blocks to empty page {code}"
    return f"inserted {len(blocks)} blocks into section {after!r} of {code}"


def _expected_sections(code: str) -> list[tuple[str, str]]:
    from scripts.page_audit import CHAPTER_SECTIONS, PRG_UNIT_SECTIONS, UNIT_SECTIONS, kind_of

    kind = kind_of(code)
    if kind == "unit":
        return PRG_UNIT_SECTIONS if code.startswith("PRG-") else UNIT_SECTIONS
    if kind == "chapter":
        return CHAPTER_SECTIONS
    raise ValueError(f"{code} is not a unit or chapter page (cannot determine expected section count)")


def _renumber_rich_text(rich: list[dict], idx: int) -> list[dict]:
    """Return a copy of `rich` with any leading 'N. ' replaced by '{idx}. '."""
    if not rich:
        return [{"type": "text", "text": {"content": f"{idx}. "}, "plain_text": f"{idx}. "}]
    out = [copy.deepcopy(r) for r in rich]
    first = out[0]
    if first.get("type", "text") != "text":
        return [{"type": "text", "text": {"content": f"{idx}. "}, "plain_text": f"{idx}. "}] + out
    content = first.get("text", {}).get("content")
    if content is None:
        content = first.get("plain_text", "")
    m = re.match(r"^\d+\.\s*", content)
    if m:
        rest = content[m.end() :]
        updated = f"{idx}. " + rest
        if not rest and len(out) > 1 and out[1].get("type", "text") == "text":
            next_content = out[1].get("text", {}).get("content")
            if next_content is None:
                next_content = out[1].get("plain_text", "")
            trimmed = next_content.lstrip()
            out[1].setdefault("text", {})["content"] = trimmed
            if "plain_text" in out[1]:
                out[1]["plain_text"] = trimmed
    else:
        updated = f"{idx}. " + content.lstrip()
    first["type"] = "text"
    first.setdefault("text", {})["content"] = updated
    if "plain_text" in first:
        first["plain_text"] = updated
    return out


def renumber_headings(code: str, token: str, id_map: dict, dry_run: bool = False) -> str:
    """Rewrite only the leading 'N. ' of every heading_2 so numbers follow page order 1..n.
    Refuses if the page does not match the standard's section count or is missing required sections."""
    entry = id_map.get(code)
    if not isinstance(entry, dict):
        raise ValueError(f"{code} is not in id_map.json")
    wanted = _expected_sections(code)
    blocks = get_all_blocks(entry["id"], token)
    h2s = [b for b in blocks if b.get("type") == "heading_2"]
    titles = [heading_text(b) for b in h2s]
    missing = [
        f"{num}. {needle.split('|')[0]}"
        for num, needle in wanted
        if not any(any(alt in t.lower() for alt in needle.lower().split("|")) for t in titles)
    ]
    if missing or len(h2s) != len(wanted):
        parts = [f"{code} has {len(h2s)} heading_2 section(s), expected {len(wanted)}"]
        if missing:
            parts.append(f"missing: {', '.join(missing)}")
        else:
            parts.append(f"headings: {titles}")
        raise ValueError("; ".join(parts))

    changes: list[tuple[str, str, str, list[dict]]] = []
    for idx, b in enumerate(h2s, 1):
        old_title = heading_text(b)
        rich = b.get("heading_2", {}).get("rich_text") or []
        new_rich = _renumber_rich_text(rich, idx)
        new_title = "".join(r.get("plain_text") or r.get("text", {}).get("content", "") for r in new_rich)
        if new_title != old_title:
            changes.append((b["id"], old_title, new_title, new_rich))

    if dry_run:
        if not changes:
            return f"dry run: {code} headings already numbered 1..{len(h2s)}"
        lines = [f"dry run: would renumber {len(changes)} heading(s) on {code}:"]
        lines.extend(f"  {old!r} -> {new!r}" for _, old, new, _ in changes)
        return "\n".join(lines)

    for bid, _, _, new_rich in changes:
        notion_request("PATCH", f"blocks/{bid}", token, {"heading_2": {"rich_text": new_rich}})
    if not changes:
        return f"{code} headings already numbered 1..{len(h2s)}"
    lines = [f"renumbered {len(changes)} heading(s) on {code}:"]
    lines.extend(f"  {old!r} -> {new!r}" for _, old, new, _ in changes)
    return "\n".join(lines)


def _section_span(blocks: list[dict], heading_needle: str) -> tuple[int, int]:
    """Return (start_idx, end_idx) slice indices for the section whose heading contains `heading_needle`."""
    start = next((i for i, b in enumerate(blocks) if heading_needle.lower() in heading_text(b).lower()), None)
    if start is None:
        raise ValueError(f"no heading containing {heading_needle!r}")
    level = HEADINGS.index(blocks[start]["type"])
    end = len(blocks)
    for i in range(start + 1, len(blocks)):
        t = blocks[i].get("type")
        if t in HEADINGS and HEADINGS.index(t) <= level:
            end = i
            break
    return start, end


def _collect_children(blocks: list[dict], token: str) -> dict[str, list[dict]]:
    """Fetch nested children for any block in `blocks` with has_children=True."""
    children_map: dict[str, list[dict]] = {}
    for b in blocks:
        if b.get("has_children"):
            kids = get_all_blocks(b["id"], token)
            children_map[b["id"]] = kids
            children_map.update(_collect_children(kids, token))
    return children_map


def _check_no_learner_content(blocks: list[dict], children_map: dict[str, list[dict]]) -> None:
    """Refuse if any block in the section (or its descendants) was edited by a person or is a checked to_do."""
    for b in blocks:
        editor = b.get("last_edited_by") or {}
        if editor.get("type") == "person":
            raise ValueError(f"refusing to move section: block {b.get('id', '?')} was last edited by a person")
        if b.get("type") == "to_do" and (b.get("to_do") or {}).get("checked"):
            raise ValueError(f"refusing to move section: to_do block {b.get('id', '?')} is checked")
        kids = children_map.get(b.get("id", ""), [])
        if kids:
            _check_no_learner_content(kids, children_map)


def _clone_block(block: dict, children_map: dict[str, list[dict]]) -> dict:
    """Convert an existing Notion block (and its nested children) into a create-block payload."""
    btype = block.get("type")
    if not btype:
        raise ValueError(f"block {block.get('id', '?')} has no type")
    payload = copy.deepcopy(block.get(btype) or {})
    if btype == "image" and payload.get("type") == "file":
        raise ValueError(f"cannot move uploaded file image block {block.get('id', '?')} (expiring URL)")
    kids = children_map.get(block.get("id", ""), [])
    if kids:
        payload["children"] = [_clone_block(k, children_map) for k in kids]
    return {"object": "block", "type": btype, btype: payload}


def move_section_to_end(code: str, heading_needle: str, token: str, id_map: dict, dry_run: bool = False) -> str:
    """Move a non-learner section (heading + blocks + nested children) to the end of the page.
    Appends copies first, verifies they landed, then deletes the originals."""
    entry = id_map.get(code)
    if not isinstance(entry, dict):
        raise ValueError(f"{code} is not in id_map.json")
    if LEARNER_SECTION.lower() in heading_needle.lower():
        raise ValueError("the learner's section is never edited or moved by agents (rules/02 §7a)")
    page_id = entry["id"]
    existing = get_all_blocks(page_id, token)
    start, end = _section_span(existing, heading_needle)
    title = heading_text(existing[start])
    if LEARNER_SECTION.lower() in title.lower():
        raise ValueError("the learner's section is never edited or moved by agents (rules/02 §7a)")

    if all(is_blank(b) for b in existing[end:]):
        return f"section {title!r} is already at the end of {code}"

    section_blocks = existing[start:end]
    children_map = _collect_children(section_blocks, token)
    _check_no_learner_content(section_blocks, children_map)
    cloned = [_clone_block(b, children_map) for b in section_blocks]

    if dry_run:
        return f"dry run: would move {len(section_blocks)} top-level block(s) of {title!r} to end of {code}"

    insert_after(page_id, None, cloned, token)
    after_append = get_all_blocks(page_id, token)
    if len(after_append) < len(existing) + len(cloned) or not any(
        heading_text(b) == title for b in after_append[len(existing) :]
    ):
        raise RuntimeError(f"append verification failed for {title!r} on {code}; original blocks kept")

    failed = []
    for b in section_blocks:
        try:
            notion_request("DELETE", f"blocks/{b['id']}", token)
        except Exception as exc:  # noqa: BLE001
            failed.append((b["id"], str(exc)[:200]))
    if failed:
        raise RuntimeError(
            f"moved {title!r} to end of {code}, but failed to delete {len(failed)} original block(s): {failed[0]}"
        )
    return f"moved {len(section_blocks)} top-level block(s) of {title!r} to end of {code}"


def _rt_text(rt: dict) -> str:
    if "plain_text" in rt:
        return rt["plain_text"]
    rtype = rt.get("type", "text")
    if rtype == "equation":
        return (rt.get("equation") or {}).get("expression", "")
    if rtype == "text":
        return (rt.get("text") or {}).get("content", "")
    return ""


def _clean_rt_for_patch(rt: dict) -> dict:
    return {k: v for k, v in rt.items() if k not in ("plain_text", "href")}


def _replace_in_rich_text(rich: list[dict], old: str, new: str) -> list[dict]:
    """Replace the single occurrence of `old` with `new` in `rich_text`, keeping equations as equations."""
    pieces = [_rt_text(rt) for rt in rich]
    joined = "".join(pieces)
    start = joined.find(old)
    if start < 0:
        raise ValueError(f"old text not found in block: {old!r}")
    end = start + len(old)

    out: list[dict] = []
    pos = 0
    replaced = False
    for rt, txt in zip(rich, pieces):
        item_start, item_end = pos, pos + len(txt)
        pos = item_end
        if item_end <= start or item_start >= end:
            out.append(_clean_rt_for_patch(rt))
            continue

        rtype = rt.get("type", "text")
        rel_start = max(0, start - item_start)
        rel_end = min(len(txt), end - item_start)

        if rtype == "equation":
            if item_start <= start and end <= item_end:
                item = copy.deepcopy(_clean_rt_for_patch(rt))
                expr = (item.get("equation") or {}).get("expression", txt)
                item["equation"] = {"expression": expr[:rel_start] + new + expr[rel_end:]}
                out.append(item)
                replaced = True
                continue
            raise ValueError("old text spans across an inline equation; narrow the substring")

        if rtype != "text":
            raise ValueError(f"old text spans across a {rtype} segment; narrow the substring")

        item = copy.deepcopy(_clean_rt_for_patch(rt))
        content = (item.get("text") or {}).get("content", txt)
        insert = new if not replaced else ""
        replaced = True
        new_content = content[:rel_start] + insert + content[rel_end:]
        if new_content:
            text_obj = dict(item.get("text") or {})
            text_obj["content"] = new_content
            item["text"] = text_obj
            out.append(item)
    return out


def fix_text(code: str, old: str, new: str, token: str, id_map: dict, dry_run: bool = False) -> str:
    """Replace an exact substring in one non-learner block's rich_text, keeping equations as equations."""
    if not old:
        raise ValueError("old text must not be empty")
    entry = id_map.get(code)
    if not isinstance(entry, dict):
        raise ValueError(f"{code} is not in id_map.json")

    top_blocks = get_all_blocks(entry["id"], token)
    children_map = _collect_children(top_blocks, token)

    matches: list[tuple[dict, str, list[dict] | str, bool, int]] = []
    current_section = ""

    def _scan(block: dict, in_learner: bool) -> None:
        btype = block.get("type", "")
        body = block.get(btype) or {}
        if btype == "equation":
            expr = body.get("expression", "")
            cnt = expr.count(old)
            if cnt > 0:
                matches.append((block, btype, expr, in_learner, cnt))
        else:
            rich = body.get("rich_text")
            if isinstance(rich, list):
                joined = "".join(_rt_text(rt) for rt in rich)
                cnt = joined.count(old)
                if cnt > 0:
                    matches.append((block, btype, rich, in_learner, cnt))
        for kid in children_map.get(block.get("id", ""), []):
            _scan(kid, in_learner)

    for b in top_blocks:
        if b.get("type") == "heading_2":
            current_section = heading_text(b)
        in_learner = LEARNER_SECTION.lower() in current_section.lower()
        _scan(b, in_learner)

    total = sum(m[4] for m in matches)
    if total == 0:
        raise ValueError(f"old text not found on {code}: {old!r}")
    if total != 1:
        raise ValueError(f"old text found {total} times on {code} (expected exactly 1): {old!r}")

    block, btype, content_or_rich, in_learner, _ = matches[0]
    if in_learner:
        raise ValueError("refused: target block is in the learner's section (My Implementation & Mistake Log)")

    if btype == "equation":
        assert isinstance(content_or_rich, str)
        updated_expr = content_or_rich.replace(old, new, 1)
        if dry_run:
            return f"dry run: would fix text in {btype} block {block['id']} of {code}: {old!r} -> {new!r}"
        notion_request("PATCH", f"blocks/{block['id']}", token, {"equation": {"expression": updated_expr}})
        return f"fixed text in {btype} block {block['id']} of {code}"

    assert isinstance(content_or_rich, list)
    updated_rich = _replace_in_rich_text(content_or_rich, old, new)
    if dry_run:
        return f"dry run: would fix text in {btype} block {block['id']} of {code}: {old!r} -> {new!r}"
    notion_request("PATCH", f"blocks/{block['id']}", token, {btype: {"rich_text": updated_rich}})
    return f"fixed text in {btype} block {block['id']} of {code}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m notion_sync.unit_page",
        description=__doc__.split("\n\n")[0],
        epilog="Text syntax (also figure captions): **bold** (no * inside), $inline math$ (math outside $...$ such as sqrt(x) or x^2 is refused), `code`, [[CODE]] page mentions. "
        "No italic or links. Block types: h2 h3 p bullet num todo callout quote eq code toggle divider figure. "
        'Figure: {"type": "figure", "fn": "build_function_graph_figure", "args": {"expr": "(x-1)^2-4"}, '
        '"caption": "..."}; builders: build_function_graph_figure, build_number_line_figure, '
        "build_complex_plane_figure, build_mapping_diagram_figure, build_cartesian_*, build_rectangle/right_triangle/circle/cone/... (figure_builder).",
    )
    ap.add_argument("--code", required=True)
    ap.add_argument("--spec", help="JSON spec of blocks (optional when only --set is used)")
    ap.add_argument("--mode", choices=("new", "add"))
    ap.add_argument("--after", help="heading text of the section to extend (mode add)")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE", help="set a page property")
    ap.add_argument(
        "--recaption",
        action="append",
        default=[],
        metavar="N=CAPTION",
        help="replace the caption of the page's N-th image (1-based, top level); $math$ and [[CODE]] work",
    )
    ap.add_argument(
        "--refigure",
        action="append",
        default=[],
        metavar="N=FILE.json",
        help="redraw the page's N-th image from a JSON figure item (fn+args or figure, optional title/caption)",
    )
    ap.add_argument(
        "--move-section-to-end",
        metavar="HEADING",
        help="move a non-learner section (no checked to_do, no person edits) to the end of the page",
    )
    ap.add_argument(
        "--renumber",
        action="store_true",
        help="rewrite leading 'N. ' of every heading_2 to 1..n (refuses if section count != standard)",
    )
    ap.add_argument(
        "--fix-text",
        nargs=2,
        action="append",
        default=[],
        metavar=("OLD", "NEW"),
        help="replace an exact substring in one non-learner block (keeps equations as equations)",
    )
    ap.add_argument("--dry-run", action="store_true", help="validate blocks and target; send nothing")
    args = ap.parse_args(argv)
    with open("id_map.json", encoding="utf-8") as f:
        id_map = json.load(f)
    if not isinstance(id_map.get(args.code), dict):
        print(f"Error: {args.code} is not in id_map.json", file=sys.stderr)
        return 2
    values = dict(v.split("=", 1) for v in args.set)
    try:
        token = require_token(load_env().get("NOTION_TOKEN"))
        if args.spec:
            if not args.mode:
                raise ValueError("--spec needs --mode new|add")
            with open(args.spec, encoding="utf-8") as f:
                spec = json.load(f)
            if args.dry_run:
                blocks = spec_to_blocks(spec, id_map)
                validate_blocks_clean(blocks, args.code)
                existing = get_all_blocks(id_map[args.code]["id"], token)
                check_target(args.code, args.mode, args.after, existing)
                print(f"dry run: {len(blocks)} top-level blocks for {args.code} ({args.mode}); target ok; nothing sent")
            else:
                print(write_page(args.code, spec, args.mode, args.after, token, id_map))
        if args.move_section_to_end:
            print(move_section_to_end(args.code, args.move_section_to_end, token, id_map, args.dry_run))
        if args.renumber:
            print(renumber_headings(args.code, token, id_map, args.dry_run))
        for old_txt, new_txt in args.fix_text:
            print(fix_text(args.code, old_txt, new_txt, token, id_map, args.dry_run))
        for item in args.refigure:
            num, _, path = item.partition("=")
            with open(path, encoding="utf-8") as f:
                print(refigure(args.code, int(num), json.load(f), token, id_map, args.dry_run))
        for item in args.recaption:
            num, _, cap = item.partition("=")
            print(recaption(args.code, int(num), cap, token, id_map, args.dry_run))
        if values:
            if args.dry_run:
                print(f"dry run: would set {sorted(values)}")
            else:
                print(f"set {set_properties(args.code, values, token, id_map)}")
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
