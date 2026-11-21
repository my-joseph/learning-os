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


@pytest.mark.parametrize("text", ["", "   ", None])
def test_toggle_requires_nonempty_label_before_rendering(text):
    with pytest.raises(ValueError, match="toggle block 1 requires non-empty text"):
        up.spec_to_blocks([{"type": "toggle", "text": text, "children": []}], {})


def test_toggle_labels_are_validated_before_figure_upload():
    uploads = []
    spec = [
        {"type": "figure", "figure": {"type": "unknown"}},
        {"type": "toggle", "text": "", "children": []},
    ]
    with pytest.raises(ValueError, match="toggle block 2 requires non-empty text"):
        up.spec_to_blocks(spec, {}, uploader=lambda svg, name: uploads.append(name) or "file-id")
    assert uploads == []


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
    insert_calls = []

    def fake_req(method, endpoint, token, payload=None):
        if method == "POST" and endpoint == "databases/db1/query":
            return {"results": []}
        if method == "POST" and endpoint == "pages":
            return {"id": "drill-page-1"}
        return {"results": []}

    def fake_insert_after(parent_id, after_id, blocks, token):
        insert_calls.append((parent_id, after_id, blocks))
        for block in blocks:
            body = block[block["type"]]
            unit_blocks.append(
                {
                    "id": f"log-{len(insert_calls)}",
                    "type": block["type"],
                    block["type"]: {
                        "rich_text": [
                            {
                                **item,
                                **(
                                    {"plain_text": item.get("text", {}).get("content", "")}
                                    if item.get("type") == "text"
                                    else {}
                                ),
                            }
                            for item in body.get("rich_text", [])
                        ]
                    },
                }
            )

    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "tok"})
    monkeypatch.setattr(drill_sync, "notion_request", fake_req)
    monkeypatch.setattr(up, "notion_request", fake_req)
    monkeypatch.setattr(up, "insert_after", fake_insert_after)
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
    second_res = drill_sync._sync_drill_to_notion_inner(doc, "drills/data/PRG-T00-C02-U01/DRL-PRG-T00-C02-U01-01.json")
    assert res["ok"] is True
    assert second_res["ok"] is True
    assert len(insert_calls) == 1
    assert insert_calls[0][1] == "note-last"


def test_fix_text_guards_and_preserves_equations(monkeypatch):
    blocks = {
        "page-1": [
            _h(2, "2. Key Formulas", "h2"),
            {
                "id": "b-formula",
                "type": "paragraph",
                "has_children": False,
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "For odd p, "}, "plain_text": "For odd p, "},
                        {"type": "equation", "equation": {"expression": "u^{p/q}=k"}, "plain_text": "u^{p/q}=k"},
                        {
                            "type": "text",
                            "text": {"content": " gives one real solution."},
                            "plain_text": " gives one real solution.",
                        },
                    ]
                },
            },
            {
                "id": "b-dup1",
                "type": "paragraph",
                "has_children": False,
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "dup phrase"}, "plain_text": "dup phrase"}]
                },
            },
            {
                "id": "b-dup2",
                "type": "paragraph",
                "has_children": False,
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "dup phrase"}, "plain_text": "dup phrase"}]
                },
            },
            {
                "id": "b-eq",
                "type": "equation",
                "has_children": False,
                "equation": {"expression": r"\text{if } p \text{ is odd}"},
            },
            _h(2, "6. My Implementation & Mistake Log", "h6"),
            {
                "id": "b-learner",
                "type": "paragraph",
                "has_children": False,
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "my personal note"}, "plain_text": "my personal note"}
                    ]
                },
            },
        ]
    }
    patches = []

    def fake_get_blocks(pid, tok):
        return list(blocks.get(pid, []))

    def fake_req(method, endpoint, token, payload=None):
        patches.append((method, endpoint, payload))
        return {}

    monkeypatch.setattr(up, "get_all_blocks", fake_get_blocks)
    monkeypatch.setattr(up, "notion_request", fake_req)
    ids = {"U3": {"id": "page-1"}}

    # 1. Refuses missing text
    with pytest.raises(ValueError, match="not found"):
        up.fix_text("U3", "missing text", "new", "tok", ids)

    # 2. Refuses duplicate matches
    with pytest.raises(ValueError, match="found 2 times"):
        up.fix_text("U3", "dup phrase", "new", "tok", ids)

    # 3. Refuses section 6 (My Implementation & Mistake Log)
    with pytest.raises(ValueError, match="learner's section"):
        up.fix_text("U3", "my personal note", "edited", "tok", ids)

    # 4. Dry-run sends nothing
    dry = up.fix_text("U3", "gives one real solution", "requires k >= 0 when q is even", "tok", ids, dry_run=True)
    assert "dry run" in dry and patches == []

    # 5. Real apply edits only that block's rich_text and keeps equations as equations
    res = up.fix_text("U3", "gives one real solution", "requires k >= 0 when q is even", "tok", ids, dry_run=False)
    assert "fixed text" in res and len(patches) == 1
    method, endpoint, payload = patches[0]
    assert method == "PATCH" and endpoint == "blocks/b-formula"
    rt = payload["paragraph"]["rich_text"]
    assert rt[1] == {"type": "equation", "equation": {"expression": "u^{p/q}=k"}}
    assert rt[2]["text"]["content"] == " requires k >= 0 when q is even."

    # 6. Equation block fix
    res_eq = up.fix_text(
        "U3",
        r"\text{if } p \text{ is odd}",
        r"\text{if } p \text{ is odd (} k \ge 0 \text{ if } q \text{ is even)}",
        "tok",
        ids,
    )
    assert "fixed text in equation block b-eq" in res_eq
    assert patches[-1] == (
        "PATCH",
        "blocks/b-eq",
        {"equation": {"expression": r"\text{if } p \text{ is odd (} k \ge 0 \text{ if } q \text{ is even)}"}},
    )


def test_fix_text_resolves_page_tokens_to_native_mentions(monkeypatch):
    block = {
        "id": "callout-1",
        "type": "callout",
        "has_children": False,
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": "Prerequisite: OLD"}, "plain_text": "Prerequisite: OLD"}]
        },
    }
    patches = []
    monkeypatch.setattr(up, "get_all_blocks", lambda *_: [block])
    monkeypatch.setattr(up, "notion_request", lambda *args: patches.append(args) or {})
    ids = {"U": {"id": "page-u"}, "PRG-T01-C01-U06": {"id": "page-prereq"}}

    result = up.fix_text("U", "OLD", "[[PRG-T01-C01-U06]]", "tok", ids)

    assert result.startswith("fixed text")
    rich = patches[0][3]["callout"]["rich_text"]
    assert rich[0]["text"]["content"] == "Prerequisite: "
    assert rich[1]["type"] == "mention"
    assert rich[1]["mention"] == {"type": "page", "page": {"id": "page-prereq"}}


def test_fix_text_parses_inline_math_as_native_equation(monkeypatch):
    block = {
        "id": "toggle-1",
        "type": "toggle",
        "has_children": False,
        "toggle": {"rich_text": [{"type": "text", "text": {"content": "Solve x <= 0"}, "plain_text": "Solve x <= 0"}]},
    }
    patches = []
    monkeypatch.setattr(up, "get_all_blocks", lambda *_: [block])
    monkeypatch.setattr(up, "notion_request", lambda *args: patches.append(args) or {})

    up.fix_text("U", "x <= 0", "$x \\le 0$", "tok", {"U": {"id": "page-u"}})

    rich = patches[0][3]["toggle"]["rich_text"]
    assert rich[0]["text"]["content"] == "Solve "
    assert rich[1]["type"] == "equation"
    assert rich[1]["equation"]["expression"] == "x \\le 0"


def test_fix_text_can_replace_retired_page_mention_by_visible_title(monkeypatch):
    block = {
        "id": "retired-link",
        "type": "paragraph",
        "has_children": False,
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": "Connection: "}, "plain_text": "Connection: "},
                {
                    "type": "mention",
                    "mention": {"type": "page", "page": {"id": "retired-id"}},
                    "plain_text": "[Retired] Error Handling",
                },
            ]
        },
    }
    patches = []
    monkeypatch.setattr(up, "get_all_blocks", lambda *_: [block])
    monkeypatch.setattr(up, "notion_request", lambda *args: patches.append(args) or {})

    up.fix_text(
        "U",
        "[Retired] Error Handling",
        "[[PRG-T01-C01-U08]]",
        "tok",
        {"U": {"id": "page-u"}, "PRG-T01-C01-U08": {"id": "active-id"}},
    )

    rich = patches[0][3]["paragraph"]["rich_text"]
    assert rich[0]["text"]["content"] == "Connection: "
    assert rich[1]["type"] == "mention"
    assert rich[1]["mention"]["page"]["id"] == "active-id"


def _bot_p(text, bid, editor_id="bot", editor_type="bot"):
    return {
        "id": bid,
        "type": "paragraph",
        "has_children": False,
        "last_edited_by": {"object": "user", "id": editor_id, "type": editor_type},
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}, "plain_text": text}]},
    }


def test_dedupe_section_removes_template_duplicate_and_keeps_divider(monkeypatch):
    page = [
        _bot_h2("5. Active Recall Questions", "h5"),
        _bot_h2("6. My Implementation & Mistake Log", "h6a"),
        _bot_p("Feynman One-Liner: Prompt", "p6a"),
        _bot_h2("6. My Implementation & Mistake Log", "h6b"),
        _bot_p("Feynman One-Liner: Prompt", "p6b"),
        {"id": "div6", "type": "divider", "divider": {}},
        _bot_h2("7. Completion Checklist", "h7"),
    ]
    deleted = []

    def fake_req(method, endpoint, token, payload=None):
        if method == "GET" and endpoint == "users/me":
            return {"id": "bot", "type": "bot"}
        if method == "DELETE":
            bid = endpoint.split("/")[1]
            deleted.append(bid)
            page[:] = [b for b in page if b["id"] != bid]
        return {}

    monkeypatch.setattr(up, "get_all_blocks", lambda pid, tok: list(page))
    monkeypatch.setattr(up, "notion_request", fake_req)
    ids = {"PRG-T01-C02-U08": {"id": "u8"}}

    dry = up.dedupe_section("PRG-T01-C02-U08", "My Implementation", "tok", ids, dry_run=True)
    assert "dry run: would remove 1 duplicate section(s) (2 top-level block(s))" in dry
    assert deleted == []

    res = up.dedupe_section("PRG-T01-C02-U08", "My Implementation", "tok", ids, dry_run=False)
    assert "removed 1 duplicate section(s) (2 top-level block(s))" in res
    assert deleted == ["h6b", "p6b"]
    assert [b["id"] for b in page] == ["h5", "h6a", "p6a", "div6", "h7"]
    assert "nothing to dedupe" in up.dedupe_section("PRG-T01-C02-U08", "My Implementation", "tok", ids)


def test_dedupe_section_guards_learner_content_and_keeps_edited_copy(monkeypatch):
    ids = {"U8": {"id": "u8"}}

    # 1. Copy 1 has learner note (different user id); Copy 2 is template-only -> remove Copy 2, keep Copy 1
    page_keep_first = [
        _bot_h2("6. My Implementation & Mistake Log", "h6a"),
        _bot_p("Feynman One-Liner: Prompt", "p6a"),
        _bot_p("Learner personal reflection", "p6a-note", editor_id="learner-1", editor_type="person"),
        _bot_h2("6. My Implementation & Mistake Log", "h6b"),
        _bot_p("Feynman One-Liner: Prompt", "p6b"),
    ]
    deleted = []

    def fake_req(method, endpoint, token, payload=None):
        if method == "GET" and endpoint == "users/me":
            return {"id": "bot", "type": "bot"}
        if method == "DELETE":
            deleted.append(endpoint.split("/")[1])
        return {}

    monkeypatch.setattr(up, "get_all_blocks", lambda pid, tok: list(page_keep_first))
    monkeypatch.setattr(up, "notion_request", fake_req)
    up.dedupe_section("U8", "My Implementation", "tok", ids)
    assert deleted == ["h6b", "p6b"]

    # 2. Both copies have learner edits -> refuse
    page_both_edited = [
        _bot_h2("6. My Implementation & Mistake Log", "h6a"),
        _bot_p("Learner note A", "p6a", editor_id="learner-1", editor_type="person"),
        _bot_h2("6. My Implementation & Mistake Log", "h6b"),
        _bot_p("Learner note B", "p6b", editor_id="learner-1", editor_type="person"),
    ]
    monkeypatch.setattr(up, "get_all_blocks", lambda pid, tok: list(page_both_edited))
    with pytest.raises(ValueError, match="multiple sections"):
        up.dedupe_section("U8", "My Implementation", "tok", ids)

    # 3. Two different template blocks without learner metadata -> refuse
    page_divergent = [
        _bot_h2("6. My Implementation & Mistake Log", "h6a"),
        _bot_p("Prompt A", "p6a"),
        _bot_h2("6. My Implementation & Mistake Log", "h6b"),
        _bot_p("Prompt B", "p6b"),
    ]
    monkeypatch.setattr(up, "get_all_blocks", lambda pid, tok: list(page_divergent))
    with pytest.raises(ValueError, match="unique block"):
        up.dedupe_section("U8", "My Implementation", "tok", ids)


def test_snapshot_page_omits_learner_section_and_renders_children(monkeypatch):
    blocks = [
        {
            "id": "c1",
            "type": "callout",
            "has_children": False,
            "callout": {"rich_text": [{"plain_text": "Objective: Test"}]},
        },
        _bot_h2("1. Core Concepts", "h1"),
        {
            "id": "code1",
            "type": "code",
            "has_children": False,
            "code": {"language": "typescript", "rich_text": [{"plain_text": "const x = 1;"}]},
        },
        {
            "id": "tog1",
            "type": "toggle",
            "has_children": True,
            "toggle": {"rich_text": [{"plain_text": "Why this works"}]},
        },
        _bot_h2("6. My Implementation & Mistake Log", "h6"),
        _bot_p("Private learner notes must not leak", "p6"),
        _bot_h2("7. Completion Checklist", "h7"),
        _todo("Review notes", "td1", checked=False),
    ]
    children = {"tog1": [_bot_p("Because invariants hold", "tp1")]}

    def fake_get(pid, tok):
        if pid == "u1":
            return list(blocks)
        return list(children.get(pid, []))

    def fake_req(method, endpoint, token, payload=None):
        return {
            "properties": {
                "Learning Objective": {"type": "rich_text", "rich_text": [{"plain_text": "Understand snapshots"}]}
            }
        }

    monkeypatch.setattr(up, "get_all_blocks", fake_get)
    monkeypatch.setattr(up, "notion_request", fake_req)
    md = up.snapshot_page("PRG-T01-C02-U08", "tok", {"PRG-T01-C02-U08": {"id": "u1", "title": "Strict Mode"}})
    assert "# PRG-T01-C02-U08: Strict Mode" in md
    assert "**Learning Objective:** Understand snapshots" in md
    assert "```typescript\nconst x = 1;\n```" in md
    assert "<details><summary>Why this works</summary>" in md
    assert "Because invariants hold" in md
    assert "Private learner notes must not leak" not in md
    assert "## 7. Completion Checklist" in md


def test_unit_page_honors_notion_dry_run_env(monkeypatch, tmp_path):
    import json

    monkeypatch.setenv("NOTION_DRY_RUN", "1")
    writes = []
    monkeypatch.setattr(up, "get_all_blocks", lambda pid, tok: [] if pid == "empty" else list(PAGE))

    def fake_req(method, endpoint, token, payload=None):
        if method != "GET":
            writes.append((method, endpoint, payload))
        if method == "GET" and endpoint == "pages/full":
            return {"properties": {"Status": {"type": "status"}}}
        return {"results": []}

    monkeypatch.setattr(up, "notion_request", fake_req)
    monkeypatch.setattr(
        up,
        "upload_svg",
        lambda *a, **kw: writes.append(("UPLOAD", a, kw)) or "file-id",
    )

    ids = {"EMPTY": {"id": "empty"}, "FULL": {"id": "full"}}
    res_write = up.write_page("EMPTY", [{"type": "p", "text": "Hello"}], "new", None, "tok", ids)
    assert "dry run" in res_write
    res_set = up.set_properties("FULL", {"Status": "In progress"}, "tok", ids)
    assert res_set == ["Status"]
    res_fix = up.fix_text("FULL", "Example 1", "Example 1A", "tok", ids)
    assert "dry run" in res_fix

    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps([{"type": "p", "text": "Hi"}]), encoding="utf-8")
    id_map_file = tmp_path / "id_map.json"
    id_map_file.write_text(json.dumps(ids), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(up, "load_env", lambda: {"NOTION_TOKEN": "tok"})
    assert up.main(["--code", "EMPTY", "--spec", str(spec_file), "--mode", "new", "--set", "Status=In progress"]) == 0
    assert writes == [], f"NOTION_DRY_RUN=1 must prevent writes, got {writes}"
