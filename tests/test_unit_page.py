"""notion_sync.unit_page: build pages from a spec; extend sections without touching the learner's workspace."""

import pytest

from notion_sync import unit_page as up


def _h(level, text, bid):
    t = f"heading_{level}"
    return {"id": bid, "type": t, t: {"rich_text": [{"plain_text": text}]}}


def _p(bid):
    return {"id": bid, "type": "paragraph", "paragraph": {"rich_text": []}}


PAGE = [
    _h(2, "3. Worked Examples", "h3"),
    _p("e1"),
    _h(3, "Example 1", "x1"),
    _p("e2"),
    _h(2, "6. My Implementation & Mistake Log", "h6"),
    _p("note"),
    _h(2, "7. Completion Checklist", "h7"),
]


def test_section_end_spans_subheadings_and_stops_at_same_level():
    assert up.section_end(PAGE, "Worked Examples") == "e2"
    assert up.section_end(PAGE, "Mistake Log") == "note"
    assert up.section_end(PAGE, "Completion") == "h7"
    assert up.section_end(PAGE, "Missing") is None


def test_spec_to_blocks_types_and_mentions():
    spec = [
        {"type": "h2", "text": "1. Core Concepts"},
        {"type": "toggle", "text": "Why this works", "children": [{"type": "eq", "expr": "\\frac{a}{b}"}]},
        {"type": "bullet", "text": "See [[U1]]"},
    ]
    blocks = up.spec_to_blocks(spec, {"U1": {"id": "abc", "title": "Unit 1"}})
    assert [b["type"] for b in blocks] == ["heading_2", "toggle", "bulleted_list_item"]
    assert blocks[1]["toggle"]["children"][0]["equation"]["expression"] == "\\frac{a}{b}"
    with pytest.raises(ValueError, match="unknown block type"):
        up.spec_to_blocks([{"type": "table"}], {})


@pytest.fixture
def fake_notion(monkeypatch):
    calls = []
    monkeypatch.setattr(up, "get_all_blocks", lambda pid, tok: list(PAGE) if pid == "full" else [])

    def req(method, endpoint, token, payload=None):
        calls.append(payload)
        return {"results": [{"id": f"new{len(calls)}"}]}

    monkeypatch.setattr(up, "notion_request", req)
    return calls


ID_MAP = {"FULL": {"id": "full"}, "EMPTY": {"id": "empty"}}
SPEC = [{"type": "p", "text": "Example 3"}]


def test_new_mode_only_on_empty_pages(fake_notion):
    assert "wrote 1 blocks" in up.write_page("EMPTY", SPEC, "new", None, "t", ID_MAP)
    assert "after" not in fake_notion[0]
    with pytest.raises(ValueError, match="never rewrite"):
        up.write_page("FULL", SPEC, "new", None, "t", ID_MAP)


def test_add_mode_inserts_at_section_end_and_protects_learner_section(fake_notion):
    up.write_page("FULL", SPEC, "add", "Worked Examples", "t", ID_MAP)
    assert fake_notion[0]["after"] == "e2"
    with pytest.raises(ValueError, match="never edited"):
        up.write_page("FULL", SPEC, "add", "My Implementation", "t", ID_MAP)
    with pytest.raises(ValueError, match="no heading"):
        up.write_page("FULL", SPEC, "add", "Nope", "t", ID_MAP)


def test_section_end_stays_above_a_closing_divider():
    page = [
        _h(2, "2. Key Formulas", "h2"),
        _p("f1"),
        {"id": "d", "type": "divider", "divider": {}},
        _h(2, "3. Worked", "h3"),
    ]
    assert up.section_end(page, "Key Formulas") == "f1"


def test_check_target_is_shared_by_dry_run():
    assert up.check_target("X", "new", None, []) is None
    assert up.check_target("X", "add", "Worked Examples", PAGE) == "e2"
    with pytest.raises(ValueError, match="never edited"):
        up.check_target("X", "add", "My Implementation", PAGE)


def test_set_properties_types_and_mastery_guard(monkeypatch):
    sent = []

    def req(method, endpoint, token, payload=None):
        if method == "GET":
            return {"properties": {"Learning Objective": {"type": "rich_text"}, "Status": {"type": "status"}}}
        sent.append(payload)
        return {}

    monkeypatch.setattr(up, "notion_request", req)
    ids = {"U": {"id": "p"}}
    assert up.set_properties("U", {"Learning Objective": "Solve", "Status": "In progress"}, "t", ids) == [
        "Learning Objective",
        "Status",
    ]
    assert sent[0]["properties"]["Status"] == {"status": {"name": "In progress"}}
    with pytest.raises(ValueError, match="Mastery"):
        up.set_properties("U", {"Mastery (0-4)": "3"}, "t", ids)
    with pytest.raises(ValueError, match="no property"):
        up.set_properties("U", {"Nope": "x"}, "t", ids)


def test_escaped_dollar_is_money_not_a_math_delimiter():
    """`$\\$15$` and `\\$83` in drill text (the ingest gate accepts them) must not split math wrongly."""
    from notion_sync.blocks import parse_rt

    runs = parse_rt("A fee of $\\$15$, plus \\$83 in total and $x$.", {})
    got = [(r["type"], r.get("equation", {}).get("expression") or r.get("text", {}).get("content")) for r in runs]
    assert got == [
        ("text", "A fee of "),
        ("equation", "\\$15"),
        ("text", ", plus $83 in total and "),
        ("equation", "x"),
        ("text", "."),
    ]
