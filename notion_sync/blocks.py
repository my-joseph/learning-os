# -*- coding: utf-8 -*-
"""Notion block builders: rich text with [[ID]] mentions, inline/display math, headings,
callouts, code, lists and toggles, plus a validated page-content replace.

Pure data builders except `replace_page_blocks`, which writes through notion_sync.client.
"""

import json
import re

from notion_sync.client import replace_page_content


def default_annotations(bold=False, italic=False, code=False, color="default"):
    return {
        "bold": bold,
        "italic": italic,
        "strikethrough": False,
        "underline": False,
        "code": code,
        "color": color,
    }


def rt(text, bold=False, italic=False, code=False, color="default"):
    return {
        "type": "text",
        "text": {"content": text},
        "annotations": default_annotations(bold=bold, italic=italic, code=code, color=color),
    }


def mention_page(page_id, bold=False):
    return {
        "type": "mention",
        "mention": {"type": "page", "page": {"id": page_id}},
        "annotations": default_annotations(bold=bold),
    }


def eq_inline(expr, bold=False):
    return {
        "type": "equation",
        "equation": {"expression": expr},
        "annotations": default_annotations(bold=bold),
    }


BOLD_SPLIT_RE = re.compile(r"(\*\*[^\*]+\*\*)")
INNER_TOKEN_RE = re.compile(r"(\[\[[A-Z0-9\-]+\]\]|\$[^\$]+\$|`[^`]+`)")


def parse_rt(text, id_map):
    """
    Two-pass rich text parser:
    1. Splits by **bold** segments so tokens inside **...** (such as [[ID]], $math$, or `code`)
       are still parsed into native Notion page mentions, inline equations, or inline code!
    2. Raises ValueError immediately if any [[ID]] is unknown or if any raw [[ or ]] remains.
    """
    bold_Chunks = BOLD_SPLIT_RE.split(text)
    out = []
    for chunk in bold_Chunks:
        if not chunk:
            continue
        is_bold = False
        inner_str = chunk
        if chunk.startswith("**") and chunk.endswith("**") and len(chunk) > 4:
            is_bold = True
            inner_str = chunk[2:-2]

        parts = INNER_TOKEN_RE.split(inner_str)
        for p in parts:
            if not p:
                continue
            if p.startswith("[[") and p.endswith("]]"):
                fid = p[2:-2]
                if fid not in id_map:
                    raise ValueError(f"Unknown Full ID in [[{fid}]] within text: {text}")
                out.append(mention_page(id_map[fid]["id"], bold=is_bold))
            elif p.startswith("$") and p.endswith("$") and len(p) > 2:
                out.append(eq_inline(p[1:-1], bold=is_bold))
            elif p.startswith("`") and p.endswith("`") and len(p) > 2:
                out.append(rt(p[1:-1], bold=is_bold, code=True))
            else:
                if "[[" in p or "]]" in p:
                    raise ValueError(f"Unparsed bracket token in '{p}' within text: {text}")
                out.append(rt(p, bold=is_bold))
    return out if out else [rt("")]


def auto_link_concepts(text, id_map, max_per_concept=1):
    """
    Final-Pass Auto-Linker:
    Scans generated text for registered Concept Vault terms (prefixed with CON-)
    and automatically wraps matching terms in [[CON-<KEY>]] tokens if not already linked.
    """
    if not text:
        return text

    # Extract all registered Concept Vault items
    concept_entries = []
    for k, v in id_map.items():
        if k.startswith("CON-") and isinstance(v, dict):
            title = v.get("title", "")
            terms = {title}
            if "(" in title and ")" in title:
                short = title.split("(")[0].strip()
                inside = title.split("(")[1].split(")")[0].strip()
                if len(short) >= 3:
                    terms.add(short)
                if len(inside) >= 4:
                    terms.add(inside)
            # Also split by '&' or '/'
            if "&" in title:
                for part in title.split("&"):
                    if len(part.strip()) >= 3:
                        terms.add(part.strip())
            if "/" in title:
                for part in title.split("/"):
                    if len(part.strip()) >= 3:
                        terms.add(part.strip())
            if " 3-Way " in title:
                terms.add(title.replace(" 3-Way ", " "))
            # Iteratively capture leading words if title ends in Protocol, Anatomy, Architecture, etc.
            curr = title
            for _ in range(3):
                matched = False
                for suffix in [" Protocol", " Anatomy", " Architecture", " System"]:
                    if curr.endswith(suffix):
                        curr = curr[: -len(suffix)].strip()
                        if len(curr) >= 3:
                            terms.add(curr)
                        matched = True
                if not matched:
                    break
            for t in terms:
                concept_entries.append((k, t))

    # Sort descending by length so longer phrases match before substrings
    concept_entries.sort(key=lambda x: len(x[1]), reverse=True)

    result = text
    for c_key, term in concept_entries:
        token = f"[[{c_key}]]"
        if token in result:
            continue
        pattern = rf"(?<!\[\[)(?<!`)\b{re.escape(term)}\b(?!\]\])(?!`)"
        result = re.sub(pattern, token, result, count=max_per_concept)

    return result


def validate_blocks_clean(blocks, label=""):
    dumped = json.dumps(blocks, ensure_ascii=False)
    unresolved_match = re.search(r"\[\[[A-Z0-9\-]+\]\]", dumped)
    if unresolved_match:
        raise AssertionError(f"[{label}] Found unresolved ID token {unresolved_match.group(0)} in generated blocks!")
    thai_match = re.search(r"[\u0E00-\u0E7F]+", dumped)
    if thai_match:
        raise AssertionError(f"[{label}] Found non-English (Thai) text '{thai_match.group(0)}' in generated blocks!")


def h2(text, id_map):
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": parse_rt(text, id_map)}}


def h3(text, id_map):
    return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": parse_rt(text, id_map)}}


def p_block(text, id_map):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": parse_rt(text, id_map)}}


def callout_block(text, id_map, color="gray_background"):
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": parse_rt(text, id_map),
            "color": color,
        },
    }


def quote_block(text, id_map):
    return {"object": "block", "type": "quote", "quote": {"rich_text": parse_rt(text, id_map)}}


def divider_block():
    return {"object": "block", "type": "divider", "divider": {}}


def eq_block(expr):
    return {"object": "block", "type": "equation", "equation": {"expression": expr}}


NOTION_VALID_LANGUAGES = {
    "abap",
    "abc",
    "agda",
    "arduino",
    "ascii art",
    "assembly",
    "bash",
    "basic",
    "bnf",
    "c",
    "c#",
    "c++",
    "clojure",
    "coffeescript",
    "coq",
    "css",
    "dart",
    "dhall",
    "diff",
    "docker",
    "ebnf",
    "elixir",
    "elm",
    "erlang",
    "f#",
    "flow",
    "fortran",
    "gherkin",
    "glsl",
    "go",
    "graphql",
    "groovy",
    "haskell",
    "hcl",
    "html",
    "idris",
    "java",
    "javascript",
    "json",
    "julia",
    "kotlin",
    "latex",
    "less",
    "lisp",
    "livescript",
    "llvm ir",
    "lua",
    "makefile",
    "markdown",
    "markup",
    "matlab",
    "mathematica",
    "mermaid",
    "nix",
    "notion formula",
    "objective-c",
    "ocaml",
    "pascal",
    "perl",
    "php",
    "plain text",
    "powershell",
    "prolog",
    "protobuf",
    "purescript",
    "python",
    "r",
    "racket",
    "reason",
    "ruby",
    "rust",
    "sass",
    "scala",
    "scheme",
    "scss",
    "shell",
    "smalltalk",
    "solidity",
    "sql",
    "swift",
    "toml",
    "typescript",
    "vb.net",
    "verilog",
    "vhdl",
    "visual basic",
    "webassembly",
    "xml",
    "yaml",
    "java/c/c++/c#",
}


def code_block(code_str, lang="typescript"):
    norm_lang = (lang or "plain text").lower()
    if norm_lang not in NOTION_VALID_LANGUAGES:
        norm_lang = "plain text"
    return {
        "object": "block",
        "type": "code",
        "code": {
            "language": norm_lang,
            "rich_text": [rt(code_str)],
        },
    }


def bullet(text, id_map, children=None):
    b = {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": parse_rt(text, id_map),
        },
    }
    if children:
        b["bulleted_list_item"]["children"] = children
    return b


def num_item(text, id_map, children=None):
    b = {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {
            "rich_text": parse_rt(text, id_map),
        },
    }
    if children:
        b["numbered_list_item"]["children"] = children
    return b


def todo_item(text, id_map, checked=False):
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": parse_rt(text, id_map),
            "checked": checked,
        },
    }


def toggle_block(question_text, answer_blocks, id_map):
    children = []
    for item in answer_blocks:
        if isinstance(item, str):
            children.append(p_block(item, id_map))
        else:
            children.append(item)
    return {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": parse_rt(question_text, id_map),
            "children": children,
        },
    }


def replace_page_blocks(page_id, new_blocks, label, token):
    validate_blocks_clean(new_blocks, label=label)
    replace_page_content(page_id, new_blocks, token, label=label)
