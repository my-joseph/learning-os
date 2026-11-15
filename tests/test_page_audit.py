"""scripts/page_audit.py: v4 page checks (rules/02 §7a), read-only and the same verdict for every agent."""

from scripts import page_audit as pa


def _rt(text, mention=False):
    if mention:
        return {"type": "mention", "plain_text": text}
    return {"type": "text", "plain_text": text, "text": {"content": text}}


def blk(kind, text="", mention=False):
    return {"type": kind, kind: {"rich_text": [_rt(text, mention)] if text else []}}


def unit_page(example2="Example 2 (L2 — Reverse): find the input", figure=True, recall=4, why=True):
    callout = {"type": "callout", "callout": {"rich_text": [_rt("Resource: "), _rt("OpenStax", mention=True)]}}
    blocks = [callout, blk("heading_2", "1. Core Concepts & Intuition"), blk("paragraph", "idea")]
    if figure:
        blocks.append({"type": "image", "image": {}})
    blocks += [blk("heading_2", "2. Key Formulas & Decision Rules"), blk("paragraph", "f")]
    if why:
        blocks.append(blk("toggle", "Why this works"))
    blocks += [
        blk("heading_2", "3. Worked Examples"),
        blk("heading_3", "Example 1 (L1 — Direct): a"),
        blk("heading_3", example2),
        blk("heading_3", "Example 3 (L3 — Trap Contrast): c"),
        blk("heading_2", "4. Unit Practice Guide"),
        blk("heading_2", "5. Active Recall Questions"),
        *[blk("toggle", f"Q{i}") for i in range(recall)],
        blk("heading_2", "6. My Implementation & Mistake Log"),
        blk("heading_2", "7. Completion Checklist & Mastery Review"),
    ]
    return blocks


PROPS = {
    "Learning Objective": {"type": "rich_text", "rich_text": [{"plain_text": "x"}]},
    "Expected Output": {"type": "rich_text", "rich_text": [{"plain_text": "y"}]},
    "Resources": {"type": "relation", "relation": [{"id": "r"}]},
    "Status": {"type": "status", "status": {"name": "In progress"}},
}


def test_complete_unit_page_passes():
    assert pa.audit_page("MTH-T09-C01-U01", unit_page(), PROPS) == ("content", [])


def test_unit_page_problems_are_named():
    props = {**PROPS, "Resources": {"type": "relation", "relation": []}}
    page = unit_page(example2="Example 2 (L2 — Multi-Step): longer", figure=False, recall=2, why=False)
    _, found = pa.audit_page("MTH-T09-C01-U01", page, props)
    msgs = " | ".join(m for _, m in found)
    assert "property 'Resources' is empty" in msgs
    assert "an L2 example must be Reverse or Translation" in msgs
    assert "no 'Why this works' toggle" in msgs
    assert "2 Active Recall toggles" in msgs
    assert any(level == "WARN" and "no figure in section 1" in m for level, m in found)


def test_older_pages_with_untagged_examples_and_old_headings_are_accepted():
    page = unit_page()
    page[page.index(next(b for b in page if pa.text_of(b).startswith("Example 1")))] = blk(
        "heading_3", "Example 1: Multiplying roots"
    )
    assert pa.audit_page("MTH-T09-C01-U01", page, PROPS)[1] == []


def test_empty_pages_fail_only_when_started():
    blank = [{"type": "paragraph", "paragraph": {"rich_text": []}}]
    assert pa.audit_page(
        "MTH-T09-C01-U02", blank, {"Status": {"type": "status", "status": {"name": "Not started"}}}
    ) == (
        "empty",
        [],
    )
    state, found = pa.audit_page("MTH-T09-C01-U02", blank, PROPS)
    assert state == "empty" and "run the start-unit skill" in found[0][1]


def test_chapter_sections_and_scope():
    page = [
        {"type": "callout", "callout": {"rich_text": [_rt("T", mention=True)]}},
        blk("heading_2", "1. Chapter Role"),
        blk("heading_2", "2. Core Mathematical Concepts & Formulas"),
        blk("heading_2", "Look-Alike Problems Across Units"),
        blk("heading_2", "5. Chapter Practice Guide"),
        blk("heading_2", "Cross-Unit Active Recall"),
        *[blk("toggle", "q") for _ in range(3)],
        blk("heading_2", "6. Summary & Spaced Review Guide"),
        blk("paragraph", "see [[MTH-X]]"),
    ]
    _, found = pa.audit_page("MTH-T09-C01", page, {})
    assert [m for _, m in found] == ["unresolved [[...]] text in 1 block(s): 'see [[MTH-X]]'"]
    ids = {"MTH-T09": {"id": "a"}, "MTH-T09-C01": {"id": "b"}, "MTH-T09-C01-U01": {"id": "c"}, "MTH-T10": {"id": "d"}}
    assert pa.codes_in_scope("MTH-T09", ids) == ["MTH-T09", "MTH-T09-C01", "MTH-T09-C01-U01"]


def test_caption_with_plain_text_math_fails():
    page = unit_page()
    img = next(b for b in page if b["type"] == "image")
    img["image"] = {"caption": [{"type": "text", "plain_text": "Squaring sqrt(x + 2) = x gives x^2"}]}
    _, found = pa.audit_page("MTH-T09-C01-U01", page, PROPS)
    assert any("image 1 caption has math as plain text" in m and "--recaption 1=" in m for _, m in found)
    img["image"] = {"caption": [{"type": "text", "plain_text": "Squaring "}, {"type": "equation", "plain_text": "x^2"}]}
    assert pa.audit_page("MTH-T09-C01-U01", page, PROPS)[1] == []
