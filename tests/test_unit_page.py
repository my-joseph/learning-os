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
