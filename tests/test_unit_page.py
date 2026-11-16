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


def test_set_relation_adds_codes_without_dropping_links(monkeypatch):
    calls = []

    def fake(method, endpoint, token, payload=None):
        calls.append((method, payload))
        return {"properties": {"Resources": {"type": "relation", "relation": [{"id": "old-1"}]}}}

    monkeypatch.setattr(up, "notion_request", fake)
    ids = {"U": {"id": "page"}, "R036": {"id": "r-36"}}
    assert up.set_properties("U", {"Resources": "R036"}, "t", ids) == ["Resources"]
    assert calls[-1][1] == {"properties": {"Resources": {"relation": [{"id": "old-1"}, {"id": "r-36"}]}}}
    with pytest.raises(ValueError, match="not in id_map"):
        up.set_properties("U", {"Resources": "R999"}, "t", ids)


def test_code_blocks_top_level_and_in_toggles_with_language_whitelist():
    from notion_sync.blocks import validate_blocks_clean

    spec = [
        {"type": "code", "code": "const x: number = sqrt(4); // [[PRG-T01]]", "lang": "typescript"},
        {
            "type": "toggle",
            "text": "Why this works",
            "children": [
                {"type": "code", "code": "SELECT * FROM users WHERE id = $1;", "lang": "SQL"},
                {"type": "code", "code": "unknown_lang()", "lang": "not-a-notion-lang"},
            ],
        },
    ]
    blocks = up.spec_to_blocks(spec, {})
    assert blocks[0]["type"] == "code"
    assert blocks[0]["code"]["language"] == "typescript"
    assert blocks[0]["code"]["rich_text"] == [
        {
            "type": "text",
            "text": {"content": "const x: number = sqrt(4); // [[PRG-T01]]"},
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            },
        }
    ]
    assert blocks[1]["toggle"]["children"][0]["code"]["language"] == "sql"
    assert blocks[1]["toggle"]["children"][1]["code"]["language"] == "plain text"
    validate_blocks_clean(blocks, "PRG-TEST")


def _bot_h2(text, bid):
    return {
        "id": bid,
        "type": "heading_2",
        "has_children": False,
        "last_edited_by": {"object": "user", "id": "bot", "type": "bot"},
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}, "plain_text": text}]},
    }


def _todo(text, bid, checked=False, edited_by="bot", has_children=False):
    return {
        "id": bid,
        "type": "to_do",
        "has_children": has_children,
        "last_edited_by": {"object": "user", "id": edited_by, "type": edited_by},
        "to_do": {
            "rich_text": [{"type": "text", "text": {"content": text}, "plain_text": text}],
            "checked": checked,
        },
    }


def _prg_broken_page():
    return [
        _bot_h2("1. Terminal Architecture & Mental Model", "h1"),
        _bot_h2("2. Core Terminal Commands", "h2"),
        _bot_h2("3. Worked Code Examples", "h3"),
        _bot_h2("3. Complete Practice Guide", "h4"),
        _bot_h2("4. Active Recall Questions", "h5"),
        _bot_h2("7. Completion Checklist", "h7"),
        _todo("Run first drill", "t1", checked=False, has_children=True),
        _bot_h2("5. My Implementation & Mistake Log", "h6"),
        {"id": "note1", "type": "paragraph", "has_children": False, "paragraph": {"rich_text": []}},
    ]


def test_renumber_dry_run_and_real_with_fake_client(monkeypatch):
    pages = {
        "u1": [
            _bot_h2("1. Terminal Architecture & Mental Model", "h1"),
            _bot_h2("2. Core Terminal Commands", "h2"),
            _bot_h2("3. Worked Code Examples", "h3"),
            _bot_h2("3. Complete Practice Guide", "h4"),
            _bot_h2("4. Active Recall Questions", "h5"),
            _bot_h2("5. My Implementation & Mistake Log", "h6"),
            _bot_h2("7. Completion Checklist", "h7"),
        ]
    }
    calls = []
    monkeypatch.setattr(up, "get_all_blocks", lambda pid, tok: list(pages[pid]))

    def fake_req(method, endpoint, token, payload=None):
        calls.append((method, endpoint, payload))
        if method == "PATCH" and endpoint.startswith("blocks/h"):
            bid = endpoint.split("/")[1]
            for b in pages["u1"]:
                if b["id"] == bid:
                    b["heading_2"]["rich_text"] = payload["heading_2"]["rich_text"]
        return {}

    monkeypatch.setattr(up, "notion_request", fake_req)
    ids = {"PRG-T00-C02-U01": {"id": "u1"}}

    dry = up.renumber_headings("PRG-T00-C02-U01", "t", ids, dry_run=True)
    assert "would renumber 3 heading(s)" in dry
    assert calls == []

    real = up.renumber_headings("PRG-T00-C02-U01", "t", ids, dry_run=False)
    assert "renumbered 3 heading(s)" in real
    assert len(calls) == 3
    assert [up.heading_text(b) for b in pages["u1"]] == [
        "1. Terminal Architecture & Mental Model",
        "2. Core Terminal Commands",
        "3. Worked Code Examples",
        "4. Complete Practice Guide",
        "5. Active Recall Questions",
        "6. My Implementation & Mistake Log",
        "7. Completion Checklist",
    ]
    calls.clear()
    assert "already numbered" in up.renumber_headings("PRG-T00-C02-U01", "t", ids, dry_run=False)
    assert calls == []


def test_renumber_refuses_wrong_section_count_and_lists_missing(monkeypatch):
    incomplete = [
        _bot_h2("1. Terminal Architecture", "h1"),
        _bot_h2("2. Core Terminal Commands", "h2"),
        _bot_h2("5. My Implementation & Mistake Log", "h6"),
    ]
    monkeypatch.setattr(up, "get_all_blocks", lambda pid, tok: list(incomplete))
    ids = {"PRG-T00-C02-U01": {"id": "u1"}}
    with pytest.raises(ValueError, match="expected 7") as exc:
        up.renumber_headings("PRG-T00-C02-U01", "t", ids)
    msg = str(exc.value)
    assert "missing:" in msg
    assert "3. Worked Code Examples" in msg
    assert "7. Completion Checklist" in msg


def test_move_section_to_end_appends_children_verifies_then_deletes(monkeypatch):
    page = _prg_broken_page()
    children = {
        "t1": [
            {
                "id": "sub1",
                "type": "paragraph",
                "has_children": False,
                "last_edited_by": {"type": "bot"},
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "Sub-note"}, "plain_text": "Sub-note"}]
                },
            }
        ]
    }
    ops = []

    def fake_get(pid, tok):
        if pid == "u1":
            return list(page)
        return list(children.get(pid, []))

    def fake_req(method, endpoint, token, payload=None):
        ops.append((method, endpoint, payload))
        if method == "PATCH" and endpoint == "blocks/u1/children":
            created = []
            for i, b in enumerate(payload["children"]):
                nb = dict(b, id=f"new-{len(page) + i}")
                page.append(nb)
                created.append(nb)
            return {"results": created}
        if method == "DELETE":
            bid = endpoint.split("/")[1]
            assert bid not in ("h6", "note1")
            page[:] = [b for b in page if b["id"] != bid]
            return {}
        return {}

    monkeypatch.setattr(up, "get_all_blocks", fake_get)
    monkeypatch.setattr(up, "notion_request", fake_req)
    ids = {"PRG-T00-C02-U01": {"id": "u1"}}

    dry = up.move_section_to_end("PRG-T00-C02-U01", "Completion Checklist", "t", ids, dry_run=True)
    assert "dry run: would move 2 top-level block(s)" in dry
    assert ops == []

    res = up.move_section_to_end("PRG-T00-C02-U01", "Completion Checklist", "t", ids, dry_run=False)
    assert "moved 2 top-level block(s)" in res

    methods = [m for m, _, _ in ops]
    assert methods == ["PATCH", "DELETE", "DELETE"]
    patched_children = ops[0][2]["children"]
    assert patched_children[1]["to_do"]["children"][0]["paragraph"]["rich_text"][0]["text"]["content"] == "Sub-note"
    h2_titles = [up.heading_text(b) for b in page if b.get("type") == "heading_2"]
    assert h2_titles[-2:] == ["5. My Implementation & Mistake Log", "7. Completion Checklist"]


def test_move_section_to_end_guards_learner_content_and_section_6(monkeypatch):
    ids = {"PRG-T00-C02-U01": {"id": "u1"}}

    monkeypatch.setattr(up, "get_all_blocks", lambda pid, tok: _prg_broken_page())
    with pytest.raises(ValueError, match="never edited or moved"):
        up.move_section_to_end("PRG-T00-C02-U01", "My Implementation", "t", ids)

    checked_page = _prg_broken_page()
    checked_page[6]["to_do"]["checked"] = True
    monkeypatch.setattr(up, "get_all_blocks", lambda pid, tok: checked_page if pid == "u1" else [])
    with pytest.raises(ValueError, match="checked"):
        up.move_section_to_end("PRG-T00-C02-U01", "Completion Checklist", "t", ids)

    person_page = _prg_broken_page()
    monkeypatch.setattr(
        up,
        "get_all_blocks",
        lambda pid, tok: person_page if pid == "u1" else [_todo("Child", "c1", edited_by="person")],
    )
    with pytest.raises(ValueError, match="person"):
        up.move_section_to_end("PRG-T00-C02-U01", "Completion Checklist", "t", ids)


def test_drill_sync_inserts_at_end_of_section_6_when_section_7_follows(monkeypatch, tmp_path):
    import json

    from notion_sync import drill_sync

    monkeypatch.chdir(tmp_path)
    (tmp_path / "id_map.json").write_text(
        json.dumps(
            {
                "DRILLS_DB": {"id": "db1"},
                "PRG-T00": {"id": "t0"},
                "PRG-T00-C02": {"id": "c2"},
                "PRG-T00-C02-U01": {"id": "u1"},
            }
        ),
        encoding="utf-8",
    )

    unit_blocks = [
        _bot_h2("5. Active Recall Questions", "h5"),
        _bot_h2("6. My Implementation & Mistake Log", "h6"),
        {"id": "note-last", "type": "paragraph", "paragraph": {"rich_text": []}},
        _bot_h2("7. Completion Checklist", "h7"),
        _todo("Done", "t1"),
    ]
    patch_calls = []

    def fake_req(method, endpoint, token, payload=None):
        if method == "POST" and endpoint == "databases/db1/query":
            return {"results": []}
        if method == "POST" and endpoint == "pages":
            return {"id": "drill-page-1"}
        if method == "PATCH" and endpoint == "blocks/u1/children":
            patch_calls.append(payload)
            return {"results": [{"id": "log-1"}]}
        return {"results": []}

    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "tok"})
    monkeypatch.setattr(drill_sync, "notion_request", fake_req)
    monkeypatch.setattr(up, "notion_request", fake_req)
    monkeypatch.setattr(drill_sync, "replace_page_blocks", lambda *a, **kw: None)
    monkeypatch.setattr(drill_sync, "update_unit_reviews", lambda *a, **kw: {})
    monkeypatch.setattr(drill_sync, "get_all_blocks", lambda pid, tok: list(unit_blocks))

    doc = {
        "drillId": "DRL-PRG-T00-C02-U01-01",
        "subject": "PRG",
        "unitCode": "PRG-T00-C02-U01",
        "chapterCode": "PRG-T00-C02",
        "topicCode": "PRG-T00",
        "unitTitle": "Terminal & Shell",
        "config": {"questionCount": 1, "difficultyMode": "Mixed"},
        "sessionSummary": {
            "attemptDate": "2026-11-16",
            "score": 1,
            "maxScore": 1,
            "accuracyPct": 100,
            "practiceStatus": "Completed",
        },
        "problems": [],
    }
    res = drill_sync._sync_drill_to_notion_inner(doc, "drills/data/PRG-T00-C02-U01/DRL-PRG-T00-C02-U01-01.json")
    assert res["ok"] is True
    assert len(patch_calls) == 1
    assert patch_calls[0]["after"] == "note-last"
