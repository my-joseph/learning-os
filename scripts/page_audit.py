"""Check Notion Topic/Chapter/Unit pages against the v4 page standard (rules/02 §7a, §7b). Read-only.

Every agent gets the same verdict, so "is this page up to standard?" is a script, not a judgement call.
FAIL = a required part is missing (fix it with `python -m notion_sync.unit_page ... --mode add` / `--set`);
WARN = worth a look (an agent decides). Empty pages of units not started yet are listed, not failed.

    python -m scripts.page_audit MTH-T02              # the topic, its chapters and units
    python -m scripts.page_audit MTH-T02-C01-U03      # one page
    python -m scripts.page_audit MTH-T02 --only-problems
"""

from __future__ import annotations

import argparse
import json
import re
import sys

UNIT_RE = re.compile(r"-C\d+-U\d+$")
CHAPTER_RE = re.compile(r"-T\d+-C\d+$")
TOPIC_RE = re.compile(r"^[A-Z]+-T\d+$")

UNIT_SECTIONS = [
    ("1", "Core Concepts"),
    ("2", "Key Formulas"),
    ("3", "Worked Examples"),
    ("4", "Practice Guide"),
    ("5", "Active Recall"),
    ("6", "My Implementation"),
    ("7", "Completion Checklist"),
]
PRG_UNIT_SECTIONS = [
    ("1", "Core Concepts|Mental Model|Internal Model|Type System Semantics|Engineering Strategy"),
    (
        "2",
        "Core Patterns|Code & Structure Examples|Code & Implementation Examples|Code Examples & Engineering Patterns|"
        "Core Terminal Commands|Production Package Manifest|Core Git Workflow|Branch Operations|Remote Commands|"
        "Production Documentation",
    ),
    ("3", "Worked Code Examples|Worked Examples"),
    ("4", "Practice Guide|Practical Exercise"),
    ("5", "Active Recall"),
    ("6", "My Implementation"),
    ("7", "Completion Checklist"),
]
CHAPTER_SECTIONS = [
    ("1", "Chapter Role"),
    ("2", "Core Invariants|Core Mathematical Concepts"),  # older chapter pages use the second wording
    ("3", "Look-Alike"),
    ("4", "Practice Guide"),
    ("5", "Cross-Unit Active Recall"),
    ("6", "Summary"),
]
PRG_CHAPTERS_WITH_LAB = {
    "PRG-T01-C01",
    "PRG-T01-C02",
    "PRG-T01-C03",
    "PRG-T01-C04",
    "PRG-T02-C01",
    "PRG-T02-C02",
    "PRG-T02-C03",
    "PRG-T02-C04",
    "PRG-T02-C05",
    "PRG-T02-C06",
    "PRG-T03-C01",
    "PRG-T03-C02",
    "PRG-T03-C03",
    "PRG-T04-C02",
    "PRG-T04-C03",
    "PRG-T05-C01",
    "PRG-T05-C02",
    "PRG-T06-C01",
    "PRG-T08-C01",
    "PRG-T08-C02",
}
UNRESOLVED_MENTION_RE = re.compile(r"\[\[[A-Z0-9-]+\]\]")
UNIT_PROPS = ("Learning Objective", "Expected Output", "Resources")
CHAPTER_PROPS = ("Objective", "Completion Criteria", "Resources")
TOPIC_PROPS = ("Goal", "Resources")
HEADINGS = ("heading_1", "heading_2", "heading_3")


def kind_of(code: str) -> str | None:
    if UNIT_RE.search(code):
        return "unit"
    if CHAPTER_RE.search(code):
        return "chapter"
    if TOPIC_RE.match(code):
        return "topic"
    return None


def _rich(block: dict) -> list[dict]:
    return (block.get(block.get("type", ""), {}) or {}).get("rich_text", []) or []


def text_of(block: dict) -> str:
    return "".join(r.get("plain_text") or r.get("text", {}).get("content", "") for r in _rich(block))


def is_blank(block: dict) -> bool:
    return block.get("type") == "paragraph" and not block.get("has_children") and not text_of(block).strip()


def sections(blocks: list[dict]) -> dict[str, list[dict]]:
    """Top-level blocks grouped under each heading_2 (keyed by heading text)."""
    out: dict[str, list[dict]] = {}
    cur = None
    for b in blocks:
        if b.get("type") == "heading_2":
            cur = text_of(b)
            out[cur] = []
        elif cur is not None:
            out[cur].append(b)
    return out


def _section(secs: dict[str, list[dict]], needle: str) -> list[dict] | None:
    """The section whose heading contains the needle (alternatives separated by `|`)."""
    alts = [n.lower() for n in needle.split("|")]
    return next((v for k, v in secs.items() if any(a in k.lower() for a in alts)), None)


def prop_empty(prop: dict) -> bool:
    kind = prop.get("type")
    val = prop.get(kind)
    if kind in ("rich_text", "title"):
        return not "".join(r.get("plain_text", "") for r in val or []).strip()
    if kind == "relation":
        return not val
    return val in (None, "", [])


def _common(blocks: list[dict], props: dict, required_props: tuple[str, ...], wanted: list) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for name in required_props:
        if name in props and prop_empty(props[name]):
            found.append(("FAIL", f"property '{name}' is empty"))
    secs = sections(blocks)
    for num, needle in wanted:
        if _section(secs, needle) is None:
            found.append(("FAIL", f"missing section {num}. {needle.split('|')[0]}"))
    callouts = [b for b in blocks[:3] if b.get("type") == "callout"]
    if not callouts:
        found.append(("FAIL", "no callout at the top (objective, prerequisites, resource)"))
    elif not any(r.get("type") == "mention" for r in _rich(callouts[0])):
        found.append(("WARN", "top callout has no page mentions; write prerequisites and the Resource as [[CODE]]"))
    from notion_sync.figures import check_plain_math

    for n, img in enumerate([b for b in blocks if b.get("type") == "image"], 1):
        cap = img.get("image", {}).get("caption", [])
        plain = "".join(r.get("plain_text", "") for r in cap if r.get("type") == "text")
        try:
            check_plain_math(plain)
        except ValueError:
            found.append(
                ("FAIL", f"image {n} caption has math as plain text: {plain[:50]!r}; fix with --recaption {n}=...")
            )
    raw = [text_of(b) for b in blocks if b.get("type") != "code" and UNRESOLVED_MENTION_RE.search(text_of(b))]
    if raw:
        found.append(("FAIL", f"unresolved [[...]] text in {len(raw)} block(s): {raw[0][:60]!r}"))
    return found


def _has_code_block(blocks: list[dict]) -> bool:
    for b in blocks:
        btype = b.get("type")
        if btype == "code":
            return True
        children = (b.get(btype, {}) or {}).get("children") or []
        if children and _has_code_block(children):
            return True
    return False


def audit_unit(blocks: list[dict], props: dict, *, prg: bool = False) -> list[tuple[str, str]]:
    wanted = PRG_UNIT_SECTIONS if prg else UNIT_SECTIONS
    found = _common(blocks, props, UNIT_PROPS, wanted)
    secs = sections(blocks)
    core = _section(secs, wanted[0][1]) or []
    if prg:
        if core and not _has_code_block(core):
            found.append(("WARN", "no code block in section 1; add a runnable snippet or trace"))
    elif core and not any(b.get("type") == "image" for b in core):
        found.append(
            (
                "WARN",
                "no figure in section 1; a graph, shape, number line or complex plane belongs here unless the unit "
                "is pure symbol work (page figures are decided apart from the drills' figureNone, rules/02 §7a)",
            )
        )
    sec2 = _section(secs, wanted[1][1])
    if sec2 is not None and not any(b.get("type") == "toggle" and "why this works" in text_of(b).lower() for b in sec2):
        found.append(("FAIL", "section 2 has no 'Why this works' toggle"))
    examples = _section(secs, wanted[2][1])
    if examples is not None:
        if prg and not _has_code_block(examples):
            found.append(("WARN", "no code block in section 3; worked examples should include code blocks"))
        titles = [text_of(b) for b in examples if b.get("type") == "heading_3"]
        if prg:
            checks = [
                ("L1", ("direct", "example"), "Direct"),
                ("L2", ("edge case", "refactor"), "Edge Case or Refactor"),
                ("L3", ("bug contrast",), "Bug Contrast"),
            ]
        else:
            checks = [
                ("L1", ("direct", "example"), "Direct"),
                ("L2", ("reverse", "translation"), "Reverse or Translation"),
                ("L3", ("trap",), "Trap Contrast"),
            ]
        for level, words, kind in checks:
            match = [t for t in titles if f"({level}" in t]
            if level == "L1" and not match:
                match = [t for t in titles if not re.search(r"\(L\d", t)]  # older pages: untagged = direct
            if not match:
                found.append(("FAIL", f"no {level} worked example (heading 'Example N ({level} — {kind}): ...')"))
            elif not any(any(w in t.lower() for w in words) for t in match):
                rule_ref = "rules/02 §7b" if prg else "rules/02 §7a"
                found.append(
                    ("FAIL", f"{level} example is '{match[0][:60]}'; an {level} example must be {kind} ({rule_ref})")
                )
    recall = _section(secs, "Active Recall")
    if recall is not None:
        n = sum(b.get("type") == "toggle" for b in recall)
        if not 3 <= n <= 4:
            found.append(("FAIL" if n < 3 else "WARN", f"section 5 has {n} Active Recall toggles (want 3-4)"))
    return found


def audit_chapter(blocks: list[dict], props: dict, *, code: str = "") -> list[tuple[str, str]]:
    found = _common(blocks, props, CHAPTER_PROPS, CHAPTER_SECTIONS)
    secs = sections(blocks)
    recall = _section(secs, "Cross-Unit Active Recall")
    if recall is not None and sum(b.get("type") == "toggle" for b in recall) < 3:
        found.append(("FAIL", "section 5 has fewer than 3 Cross-Unit Active Recall toggles"))
    if code in PRG_CHAPTERS_WITH_LAB and _section(secs, "Chapter Lab") is None:
        found.append(("WARN", "missing 'Chapter Lab' section (curriculum v2 §4)"))
    return found


def audit_topic(blocks: list[dict], props: dict) -> list[tuple[str, str]]:
    found = [("FAIL", f"property '{n}' is empty") for n in TOPIC_PROPS if n in props and prop_empty(props[n])]
    if not any(b.get("type") == "callout" for b in blocks[:3]):
        found.append(("WARN", "no callout at the top"))
    return found


AUDITS = {"unit": audit_unit, "chapter": audit_chapter, "topic": audit_topic}


def audit_page(code: str, blocks: list[dict], props: dict) -> tuple[str, list[tuple[str, str]]]:
    """(state, findings): state is 'empty' for a page with no content yet, else 'content'."""
    content = [b for b in blocks if not is_blank(b)]
    if not content:
        status = ((props.get("Status") or {}).get("status") or {}).get("name", "")
        if status and status != "Not started":
            return "empty", [("FAIL", f"page is empty but Status is '{status}'; run the start-unit skill")]
        return "empty", []
    kind = kind_of(code)
    if kind == "unit":
        return "content", audit_unit(content, props, prg=code.startswith("PRG-"))
    if kind == "chapter":
        return "content", audit_chapter(content, props, code=code)
    return "content", AUDITS[kind](content, props)


def codes_in_scope(scope: str, id_map: dict) -> list[str]:
    return sorted(
        c for c, v in id_map.items() if isinstance(v, dict) and (c == scope or c.startswith(scope + "-")) and kind_of(c)
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m scripts.page_audit", description=__doc__.split("\n\n")[0])
    ap.add_argument("scope", help="topic, chapter or unit code, e.g. MTH-T02")
    ap.add_argument("--only-problems", action="store_true", help="hide pages that pass and empty pages")
    args = ap.parse_args(argv)

    from notion_sync.client import get_all_blocks, load_env, notion_request, require_token

    with open("id_map.json", encoding="utf-8") as f:
        id_map = json.load(f)
    codes = codes_in_scope(args.scope, id_map)
    if not codes:
        print(f"No pages for {args.scope} in id_map.json", file=sys.stderr)
        return 2
    token = require_token(load_env().get("NOTION_TOKEN"))
    fails = 0
    empty = []
    for code in codes:
        pid = id_map[code]["id"]
        props = notion_request("GET", f"pages/{pid}", token).get("properties", {})
        state, findings = audit_page(code, get_all_blocks(pid, token), props)
        fails += sum(level == "FAIL" for level, _ in findings)
        if state == "empty" and not findings:
            empty.append(code)
            continue
        if args.only_problems and not findings:
            continue
        print(f"{code}  {'OK' if not findings else ''}")
        for level, msg in findings:
            print(f"  {level}  {msg}")
    if empty and not args.only_problems:
        print(f"\nNot started (empty): {len(empty)} page(s): {', '.join(empty)}")
    print(f"\n{fails} FAIL(s) across {len(codes)} page(s).")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
