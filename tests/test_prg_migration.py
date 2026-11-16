"""Hermetic tests for PRG curriculum v2 migration map, planner, safety, rollback, and local renames."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

from scripts import prg_migrate

MAP_PATH = Path("docs/prg_migration_map.json")
ID_MAP_PATH = Path("id_map.json")


def _notion_page(
    page_id: str,
    full_id: str,
    title: str,
    level: str = "unit",
    status: str = "Not started",
) -> dict:
    title_prop = prg_migrate.TITLE_PROP_BY_LEVEL[level]
    return {
        "id": page_id,
        "archived": False,
        "properties": {
            title_prop: {"type": "title", "title": [{"plain_text": title}]},
            "Full ID": {"type": "rich_text", "rich_text": [{"plain_text": full_id}]},
            "Status": {"type": "status", "status": {"name": status}},
        },
    }


def test_migration_map_covers_every_v1_code_once():
    entries = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    id_map = json.loads(ID_MAP_PATH.read_text(encoding="utf-8"))
    v1_prg = sorted(k for k in id_map if k.startswith("PRG-"))

    seen_old: list[str] = []
    for e in entries:
        seen_old.extend(e["oldCodes"])

    assert len(seen_old) == len(v1_prg)
    assert sorted(seen_old) == v1_prg


def test_migration_map_no_duplicate_new_codes_and_no_lab_expected_output():
    entries = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    new_codes = [e["newCode"] for e in entries if e["newCode"] is not None]
    assert len(new_codes) == len(set(new_codes))

    for e in entries:
        if e["level"] == "unit":
            assert not (e["expectedOutput"] or "").startswith("Lab "), f"{e['newCode']} has Lab expectedOutput"


def test_migration_map_prereqs_point_strictly_backwards():
    entries = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    units = [e for e in entries if e["level"] == "unit"]
    pos = {e["newCode"]: i for i, e in enumerate(units)}

    for i, u in enumerate(units):
        for pre in u["prereqs"]:
            assert pre in pos, f"Unknown prereq {pre} on {u['newCode']}"
            assert pos[pre] < i, f"Prereq {pre} on {u['newCode']} does not point backwards"


def test_swap_ordering_never_collides_including_cycles():
    # Direct 2-cycle (C02 <-> C03) + chain (C04 -> C05, new C04)
    renames = [
        ("pid-c02", "PRG-T00-C02", "PRG-T00-C03"),
        ("pid-c03", "PRG-T00-C03", "PRG-T00-C02"),
        ("pid-t01c03", "PRG-T01-C03", "PRG-T01-C04"),
        ("pid-t08c01", "PRG-T08-C01", "PRG-T01-C04-MERGED"),
    ]
    ordered = prg_migrate.order_renames_safely(renames)

    occupied = {cur: pid for pid, cur, _ in renames}
    for pid, cur, tgt in ordered:
        assert occupied.get(cur) == pid
        assert tgt not in occupied or occupied[tgt] == pid, f"Collision writing {tgt} while occupied by {occupied[tgt]}"
        del occupied[cur]
        occupied[tgt] = pid

    for pid, _, final_tgt in renames:
        assert occupied[final_tgt] == pid


def test_retire_refuses_done_in_progress_and_learner_content():
    p_done = _notion_page("p1", "PRG-T00-C02-U03", "Old Unit", status="Done")
    assert "Done" in (prg_migrate.check_retire_safety("PRG-T00-C02-U03", p_done, []) or "")

    p_prog = _notion_page("p2", "PRG-T00-C02-U04", "Old Unit", status="In progress")
    assert "In progress" in (prg_migrate.check_retire_safety("PRG-T00-C02-U04", p_prog, []) or "")

    p_not_started = _notion_page("p3", "PRG-T00-C02-U05", "Old Unit", status="Not started")
    template_only_blocks = [
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "5. My Implementation & Mistake Log"}]}},
        {"type": "to_do", "to_do": {"checked": False, "rich_text": [{"plain_text": "Template task"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": []}},
    ]
    assert prg_migrate.check_retire_safety("PRG-T00-C02-U05", p_not_started, template_only_blocks) is None

    learner_blocks = [
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "5. My Implementation & Mistake Log"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "My notes here"}]}},
    ]
    assert "learner content" in (
        prg_migrate.check_retire_safety("PRG-T00-C02-U05", p_not_started, learner_blocks) or ""
    )


def test_dry_run_makes_zero_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "prg_migration_map.json").write_text(
        json.dumps(
            [
                {
                    "level": "topic",
                    "order": 0,
                    "newCode": "PRG-T00",
                    "oldCodes": ["PRG-T00"],
                    "action": "keep",
                    "title": "Foundation Audit",
                    "objective": "Obj",
                    "expectedOutput": None,
                    "practiceType": None,
                    "prereqs": [],
                    "parent": None,
                    "extended": False,
                }
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "id_map.json").write_text(
        json.dumps({"PRG-T00": {"id": "pid-t00", "title": "Old"}}),
        encoding="utf-8",
    )

    def fake_notion(method, endpoint, token, payload=None):
        assert method == "POST" and endpoint.endswith("/query"), f"Unexpected write: {method} {endpoint}"
        if (
            "4003818f-8ba0-8029" in endpoint
            and payload.get("filter", {}).get("rich_text", {}).get("starts_with") == "PRG-"
        ):
            return {"results": [_notion_page("pid-t00", "PRG-T00", "Old", level="topic")], "has_more": False}
        return {"results": [], "has_more": False}

    monkeypatch.setattr(prg_migrate, "load_env", lambda: {"NOTION_TOKEN": "fake-token"})
    monkeypatch.setattr(prg_migrate, "notion_request", fake_notion)
    monkeypatch.setattr(
        prg_migrate,
        "query_all",
        lambda db, tok, flt=None: fake_notion("POST", f"databases/{db}/query", tok, {"filter": flt} if flt else {})[
            "results"
        ],
    )

    with mock.patch("shutil.move") as m_move, mock.patch("pathlib.Path.write_text") as m_write:
        rc = prg_migrate.main(["--topic", "PRG-T00"])
        assert rc == 0
        m_move.assert_not_called()
        m_write.assert_not_called()


def test_apply_requires_all_and_review_flag():
    assert prg_migrate.main(["--apply", "--i-have-reviewed-the-dry-run"]) == 2
    assert prg_migrate.main(["--topic", "PRG-T00", "--apply", "--i-have-reviewed-the-dry-run"]) == 2
    assert prg_migrate.main(["--all", "--apply"]) == 2


def test_local_rename_moves_workspace_and_progress_together_and_rollback_restores(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    entries = [
        {
            "level": "chapter",
            "order": 2,
            "newCode": "PRG-T00-C03",
            "oldCodes": ["PRG-T00-C02"],
            "action": "renumber",
            "title": "JS Baseline",
            "objective": "",
            "expectedOutput": None,
            "practiceType": None,
            "prereqs": [],
            "parent": "PRG-T00",
            "extended": False,
        },
        {
            "level": "unit",
            "order": 1,
            "newCode": "PRG-T00-C03-U01",
            "oldCodes": ["PRG-T00-C02-U01"],
            "action": "renumber",
            "title": "Vars",
            "objective": "Obj",
            "expectedOutput": "Out",
            "practiceType": "drill: predict-output",
            "prereqs": [],
            "parent": "PRG-T00-C03",
            "extended": False,
        },
    ]

    # Set up local vault, drill, progress, workspace
    (tmp_path / "code_engine" / "reasoning_vault").mkdir(parents=True)
    (tmp_path / "code_engine" / "reasoning_vault" / "PRG-T00-C02.json").write_text(
        json.dumps({"unitCode": "PRG-T00-C02", "archetypes": []}), encoding="utf-8"
    )
    (tmp_path / "drills" / "data" / "PRG-T00-C02").mkdir(parents=True)
    (tmp_path / "drills" / "data" / "PRG-T00-C02" / "DRL-PRG-T00-C02-02.json").write_text(
        json.dumps({"unitCode": "PRG-T00-C02", "problems": [{"unit": "U01"}]}), encoding="utf-8"
    )
    (tmp_path / "progress").mkdir()
    (tmp_path / "progress" / "DRL-PRG-T00-C02-02.json").write_text(
        json.dumps({"drillId": "DRL-PRG-T00-C02-02", "unitCode": "PRG-T00-C02", "problems": {"Q01": {"score": 1}}}),
        encoding="utf-8",
    )
    (tmp_path / "drills" / "workspace" / "DRL-PRG-T00-C02-02").mkdir(parents=True)
    (tmp_path / "drills" / "workspace" / "DRL-PRG-T00-C02-02" / "Q01_test.js").write_text(
        "// learner code\n", encoding="utf-8"
    )

    # Fake Notion store (pages_by_id uses hyphen-stripped IDs, matching fetch_notion_prg_state)
    pages = {
        "pidchap": _notion_page("pidchap", "PRG-T00-C02", "Old Chap", level="chapter"),
        "pidunit": _notion_page("pidunit", "PRG-T00-C02-U01", "Old Unit", level="unit"),
    }
    id_map = {
        "PRG-T00-C02": {"id": "pidchap", "title": "Old Chap"},
        "PRG-T00-C02-U01": {"id": "pidunit", "title": "Old Unit"},
    }

    def fake_req(method, endpoint, token, payload=None):
        if method == "GET" and endpoint.startswith("pages/"):
            pid = endpoint.split("/", 1)[1]
            return pages[pid]
        if method == "PATCH" and endpoint.startswith("pages/"):
            pid = endpoint.split("/", 1)[1]
            for k, v in (payload.get("properties") or {}).items():
                if "rich_text" in v:
                    pages[pid]["properties"][k] = {
                        "type": "rich_text",
                        "rich_text": [{"plain_text": v["rich_text"][0]["text"]["content"]}],
                    }
                elif "title" in v:
                    pages[pid]["properties"][k] = {
                        "type": "title",
                        "title": [{"plain_text": v["title"][0]["text"]["content"]}],
                    }
            return pages[pid]
        raise AssertionError(f"Unexpected request: {method} {endpoint}")

    monkeypatch.setattr(prg_migrate, "notion_request", fake_req)
    monkeypatch.setattr(prg_migrate, "get_all_blocks", lambda pid, tok: [])
    monkeypatch.setattr(
        prg_migrate, "rebuild_id_map", lambda tok, old: {"PRG-T00-C03": {"id": "pidchap", "title": "JS Baseline"}}
    )

    ops, refusals = prg_migrate.build_migration_plan(entries, id_map, pages, [], "tok", topic="PRG-T00")
    assert not refusals
    local_ops = prg_migrate.plan_local_operations(entries, tmp_path, topic="PRG-T00")
    _, log_path = prg_migrate.apply_plan(ops, local_ops, "tok", entries, id_map)

    assert (tmp_path / "code_engine" / "reasoning_vault" / "PRG-T00-C03.json").exists()
    assert (tmp_path / "drills" / "data" / "PRG-T00-C03" / "DRL-PRG-T00-C03-02.json").exists()
    prog_new = json.loads((tmp_path / "progress" / "DRL-PRG-T00-C03-02.json").read_text(encoding="utf-8"))
    assert prog_new["drillId"] == "DRL-PRG-T00-C03-02"
    assert (tmp_path / "drills" / "workspace" / "DRL-PRG-T00-C03-02" / "Q01_test.js").read_text(
        encoding="utf-8"
    ) == "// learner code\n"

    # Rollback restores both Notion and local files
    prg_migrate.rollback_from_log(log_path, "tok", dry_run=False)
    assert pages["pidchap"]["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "PRG-T00-C02"
    assert (tmp_path / "progress" / "DRL-PRG-T00-C02-02.json").exists()
    assert (tmp_path / "drills" / "workspace" / "DRL-PRG-T00-C02-02" / "Q01_test.js").exists()


def test_retire_clears_relations_prefixes_title_writes_property_pointer_no_blocks_and_rollback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    entries = [
        {
            "level": "topic",
            "order": 10,
            "newCode": None,
            "oldCodes": ["PRG-T08"],
            "action": "retire",
            "title": "Testing",
            "objective": "Old topic goal",
            "expectedOutput": None,
            "practiceType": None,
            "prereqs": [],
            "parent": None,
            "extended": False,
            "retireTarget": "PRG-T01-C04",
        },
        {
            "level": "unit",
            "order": 2,
            "newCode": "PRG-T00-C03-U02",
            "oldCodes": ["PRG-T00-C02-U02", "PRG-T00-C02-U03"],
            "action": "merge",
            "title": "Functions Check",
            "objective": "Clean target objective.",
            "expectedOutput": "Passing diagnostic drill",
            "practiceType": "drill: implement-with-tests",
            "prereqs": [],
            "parent": "PRG-T00-C03",
            "extended": False,
        },
    ]

    p_topic = _notion_page("pidt08", "PRG-T08", "Testing & Quality", level="topic")
    p_topic["properties"]["Goal"] = {"type": "rich_text", "rich_text": [{"plain_text": "Old topic goal."}]}

    p_retire_unit = _notion_page("pidu03", "PRG-T00-C02-U03", "Legacy Functions", level="unit", status="Not started")
    p_retire_unit["properties"]["Learning Objective"] = {
        "type": "rich_text",
        "rich_text": [{"plain_text": "Old unit objective."}],
    }
    p_retire_unit["properties"]["Learning Topics"] = {"type": "relation", "relation": [{"id": "pidt00"}]}
    p_retire_unit["properties"]["Learning Chapters"] = {"type": "relation", "relation": [{"id": "pidc02"}]}

    p_target_unit = _notion_page("pidu02", "PRG-T00-C02-U02", "Old Target", level="unit", status="Not started")

    pages = {"pidt08": p_topic, "pidu03": p_retire_unit, "pidu02": p_target_unit}
    id_map = {
        "PRG-T08": {"id": "pidt08", "title": "Testing & Quality"},
        "PRG-T00-C02-U03": {"id": "pidu03", "title": "Legacy Functions"},
        "PRG-T00-C02-U02": {"id": "pidu02", "title": "Old Target"},
        "PRG-T00-C03": {"id": "pidc03", "title": "Diagnostic"},
    }

    def fake_req(method, endpoint, token, payload=None):
        assert not endpoint.startswith("blocks/"), f"Unexpected block write on retired page: {method} {endpoint}"
        if method == "GET" and endpoint.startswith("pages/"):
            return pages[endpoint.split("/", 1)[1]]
        if method == "PATCH" and endpoint.startswith("pages/"):
            pid = endpoint.split("/", 1)[1]
            for k, v in (payload.get("properties") or {}).items():
                if "rich_text" in v:
                    pages[pid]["properties"][k] = {
                        "type": "rich_text",
                        "rich_text": [{"plain_text": v["rich_text"][0]["text"]["content"]}],
                    }
                elif "title" in v:
                    pages[pid]["properties"][k] = {
                        "type": "title",
                        "title": [{"plain_text": v["title"][0]["text"]["content"]}],
                    }
                elif "relation" in v:
                    pages[pid]["properties"][k] = {
                        "type": "relation",
                        "relation": [{"id": r["id"]} for r in v["relation"]],
                    }
                elif "number" in v:
                    pages[pid]["properties"][k] = {"type": "number", "number": v["number"]}
                elif "select" in v:
                    pages[pid]["properties"][k] = {"type": "select", "select": v["select"]}
            return pages[pid]
        raise AssertionError(f"Unexpected request: {method} {endpoint}")

    monkeypatch.setattr(prg_migrate, "notion_request", fake_req)
    monkeypatch.setattr(prg_migrate, "get_all_blocks", lambda pid, tok: [])
    monkeypatch.setattr(prg_migrate, "rebuild_id_map", lambda tok, old: id_map)

    ops, refusals = prg_migrate.build_migration_plan(entries, id_map, pages, [], "tok")
    assert not refusals
    _, log_path = prg_migrate.apply_plan(ops, [], "tok", entries, id_map)

    # Retired unit checks
    assert p_retire_unit["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "RETIRED-PRG-T00-C02-U03"
    assert p_retire_unit["properties"]["Unit"]["title"][0]["plain_text"] == "[Retired] Legacy Functions"
    assert p_retire_unit["properties"]["Status"]["status"]["name"] == "Not started"
    assert p_retire_unit["properties"]["Learning Topics"]["relation"] == []
    assert p_retire_unit["properties"]["Learning Chapters"]["relation"] == []
    retire_obj = p_retire_unit["properties"]["Learning Objective"]["rich_text"][0]["plain_text"]
    assert retire_obj.startswith("Retired 2026-11-16: merged into PRG-T00-C03-U02")
    assert retire_obj.endswith("Old unit objective.")

    # Retired topic checks
    assert p_topic["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "RETIRED-PRG-T08"
    assert p_topic["properties"]["Topic"]["title"][0]["plain_text"] == "[Retired] Testing & Quality"
    topic_goal = p_topic["properties"]["Goal"]["rich_text"][0]["plain_text"]
    assert topic_goal.startswith("Retired 2026-11-16: merged into PRG-T01-C04")
    assert topic_goal.endswith("Old topic goal.")

    # New-home page keeps clean Learning Objective (no "Merged from:")
    target_obj = p_target_unit["properties"]["Learning Objective"]["rich_text"][0]["plain_text"]
    assert target_obj == "Clean target objective."

    # Operations log records old_relations + merged_from
    log_records = json.loads(log_path.read_text(encoding="utf-8"))
    retire_unit_rec = next(r for r in log_records if r["kind"] == "retire" and r["old_full_id"] == "PRG-T00-C02-U03")
    assert retire_unit_rec["old_relations"] == {"Learning Topics": ["pidt00"], "Learning Chapters": ["pidc02"]}
    update_rec = next(r for r in log_records if r["kind"] == "update")
    assert update_rec["merged_from"] == ["PRG-T00-C02-U03"]

    # Rollback restores relations, title, code, and objective text
    monkeypatch.setattr(prg_migrate, "THROTTLE_SECONDS", 0.0)
    prg_migrate.rollback_from_log(log_path, "tok", dry_run=False)
    assert p_retire_unit["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "PRG-T00-C02-U03"
    assert p_retire_unit["properties"]["Unit"]["title"][0]["plain_text"] == "Legacy Functions"
    assert p_retire_unit["properties"]["Learning Objective"]["rich_text"][0]["plain_text"] == "Old unit objective."
    assert p_retire_unit["properties"]["Learning Topics"]["relation"] == [{"id": "pidt00"}]
    assert p_retire_unit["properties"]["Learning Chapters"]["relation"] == [{"id": "pidc02"}]
    assert p_topic["properties"]["Goal"]["rich_text"][0]["plain_text"] == "Old topic goal."


def test_cross_topic_cycle_checkpoint_resume_and_id_map_order(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(prg_migrate, "THROTTLE_SECONDS", 0.0)
    entries = [
        {
            "level": "topic",
            "order": 3,
            "newCode": "PRG-T03",
            "oldCodes": ["PRG-T04"],
            "action": "renumber",
            "title": "Backend",
            "objective": "Obj3",
            "expectedOutput": None,
            "practiceType": None,
            "prereqs": [],
            "parent": None,
            "extended": False,
        },
        {
            "level": "topic",
            "order": 4,
            "newCode": "PRG-T04",
            "oldCodes": ["PRG-T05"],
            "action": "renumber",
            "title": "Frontend",
            "objective": "Obj4",
            "expectedOutput": None,
            "practiceType": None,
            "prereqs": [],
            "parent": None,
            "extended": False,
        },
        {
            "level": "topic",
            "order": 5,
            "newCode": "PRG-T05",
            "oldCodes": ["PRG-T06"],
            "action": "renumber",
            "title": "Databases",
            "objective": "Obj5",
            "expectedOutput": None,
            "practiceType": None,
            "prereqs": [],
            "parent": None,
            "extended": False,
        },
        {
            "level": "topic",
            "order": 6,
            "newCode": "PRG-T06",
            "oldCodes": ["PRG-T03"],
            "action": "renumber",
            "title": "Async",
            "objective": "Obj6",
            "expectedOutput": None,
            "practiceType": None,
            "prereqs": [],
            "parent": None,
            "extended": False,
        },
    ]
    pages = {
        "pidt03": _notion_page("pidt03", "PRG-T03", "Old T03", level="topic"),
        "pidt04": _notion_page("pidt04", "PRG-T04", "Old T04", level="topic"),
        "pidt05": _notion_page("pidt05", "PRG-T05", "Old T05", level="topic"),
        "pidt06": _notion_page("pidt06", "PRG-T06", "Old T06", level="topic"),
    }
    id_map = {
        "PRG-T03": {"id": "pidt03", "title": "Old T03"},
        "PRG-T04": {"id": "pidt04", "title": "Old T04"},
        "PRG-T05": {"id": "pidt05", "title": "Old T05"},
        "PRG-T06": {"id": "pidt06", "title": "Old T06"},
    }
    (tmp_path / "id_map.json").write_text(json.dumps(id_map), encoding="utf-8")

    events: list[str] = []
    patch_count = 0
    fail_on_patch = 3

    def fake_req(method, endpoint, token, payload=None):
        nonlocal patch_count
        if method == "GET" and endpoint.startswith("pages/"):
            return pages[endpoint.split("/", 1)[1]]
        if method == "PATCH" and endpoint.startswith("pages/"):
            patch_count += 1
            if fail_on_patch and patch_count == fail_on_patch:
                raise RuntimeError("Simulated mid-run interruption")
            pid = endpoint.split("/", 1)[1]
            for k, v in (payload.get("properties") or {}).items():
                if "rich_text" in v:
                    pages[pid]["properties"][k] = {
                        "type": "rich_text",
                        "rich_text": [{"plain_text": v["rich_text"][0]["text"]["content"]}],
                    }
                elif "title" in v:
                    pages[pid]["properties"][k] = {
                        "type": "title",
                        "title": [{"plain_text": v["title"][0]["text"]["content"]}],
                    }
                elif "number" in v:
                    pages[pid]["properties"][k] = {"type": "number", "number": v["number"]}
            events.append(f"patch:{pid}:{pages[pid]['properties']['Full ID']['rich_text'][0]['plain_text']}")
            return pages[pid]
        raise AssertionError(f"Unexpected request: {method} {endpoint}")

    def fake_rebuild(tok, old):
        events.append("rebuild_id_map")
        return {
            "PRG-T03": {"id": "pidt04", "title": "Backend"},
            "PRG-T04": {"id": "pidt05", "title": "Frontend"},
            "PRG-T05": {"id": "pidt06", "title": "Databases"},
            "PRG-T06": {"id": "pidt03", "title": "Async"},
        }

    def fake_save_id_map(data, path=prg_migrate.ID_MAP_PATH):
        events.append("save_id_map")
        path.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(prg_migrate, "notion_request", fake_req)
    monkeypatch.setattr(prg_migrate, "get_all_blocks", lambda pid, tok: [])
    monkeypatch.setattr(prg_migrate, "rebuild_id_map", fake_rebuild)
    monkeypatch.setattr(prg_migrate, "save_id_map", fake_save_id_map)

    preflight = prg_migrate.run_preflight(entries, id_map, pages)
    assert not preflight.errors
    ops, refusals = prg_migrate.build_migration_plan(entries, id_map, pages, [], "tok", preflight=preflight)
    assert not refusals
    assert any(op.kind == "temp_rename" for op in ops)

    # First run: fails on 3rd PATCH; checkpoint log already has first 2 ops, and id_map was NOT written
    try:
        prg_migrate.apply_plan(ops, [], "tok", entries, id_map)
        raise AssertionError("Expected RuntimeError")
    except RuntimeError:
        pass

    assert "rebuild_id_map" not in events
    assert "save_id_map" not in events
    log_files = list((tmp_path / "migrations").glob("prg_v2_*.json"))
    assert len(log_files) == 1
    log_path = log_files[0]
    partial_records = json.loads(log_path.read_text(encoding="utf-8"))
    assert len(partial_records) == 2

    # Resume run: rebuilds plan from live Notion state and resumes from log_path
    fail_on_patch = 0
    preflight2 = prg_migrate.run_preflight(entries, id_map, pages)
    assert not preflight2.errors
    ops2, _ = prg_migrate.build_migration_plan(entries, id_map, pages, [], "tok", preflight=preflight2)
    records2, _ = prg_migrate.apply_plan(ops2, [], "tok", entries, id_map, resume_log=log_path)

    # All 4 topics reached their final codes
    assert pages["pidt04"]["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "PRG-T03"
    assert pages["pidt05"]["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "PRG-T04"
    assert pages["pidt06"]["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "PRG-T05"
    assert pages["pidt03"]["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "PRG-T06"

    # id_map written only once, strictly after the last Notion PATCH
    assert events.count("save_id_map") == 1
    last_patch_idx = max(i for i, ev in enumerate(events) if ev.startswith("patch:"))
    assert events.index("save_id_map") > last_patch_idx

    # Rollback from the resumed log restores all 4 topics to original codes
    prg_migrate.rollback_from_log(log_path, "tok", dry_run=False)
    assert pages["pidt03"]["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "PRG-T03"
    assert pages["pidt04"]["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "PRG-T04"
    assert pages["pidt05"]["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "PRG-T05"
    assert pages["pidt06"]["properties"]["Full ID"]["rich_text"][0]["plain_text"] == "PRG-T06"
    assert len(records2) >= 5


def test_preflight_duplicate_unmapped_and_stray_relations(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    entries = [
        {
            "level": "topic",
            "order": 4,
            "newCode": "PRG-T03",
            "oldCodes": ["PRG-T04"],
            "action": "renumber",
            "title": "Backend",
            "objective": "Obj",
            "expectedOutput": None,
            "practiceType": None,
            "prereqs": [],
            "parent": None,
            "extended": False,
        },
        {
            "level": "topic",
            "order": 5,
            "newCode": "PRG-T03",
            "oldCodes": ["PRG-T05"],
            "action": "renumber",
            "title": "Duplicate",
            "objective": "Obj2",
            "expectedOutput": None,
            "practiceType": None,
            "prereqs": [],
            "parent": None,
            "extended": False,
        },
    ]
    pages = {
        "pidt04": _notion_page("pidt04", "PRG-T04", "Backend", level="topic"),
        "pidt05": _notion_page("pidt05", "PRG-T05", "Other", level="topic"),
        "pidstray": _notion_page("pidstray", "PRG-T99", "Stray PRG", level="topic"),
    }
    id_map = {
        "PRG-T04": {"id": "pidt04", "title": "Backend"},
        "PRG-T05": {"id": "pidt05", "title": "Other"},
    }
    pf = prg_migrate.run_preflight(entries, id_map, pages)
    assert any("Duplicate final code 'PRG-T03'" in e for e in pf.errors)
    assert any("Unmapped Notion page pidstray holds PRG code 'PRG-T99'" in e for e in pf.errors)

    # main --all --apply aborts before any Notion write when preflight has errors
    (tmp_path / "docs" / "prg_migration_map.json").write_text(json.dumps(entries), encoding="utf-8")
    (tmp_path / "id_map.json").write_text(json.dumps(id_map), encoding="utf-8")
    monkeypatch.setattr(prg_migrate, "load_env", lambda: {"NOTION_TOKEN": "tok"})
    monkeypatch.setattr(prg_migrate, "fetch_notion_prg_state", lambda tok: (pages, []))
    with mock.patch.object(prg_migrate, "apply_plan") as m_apply:
        rc = prg_migrate.main(["--all", "--apply", "--i-have-reviewed-the-dry-run"])
        assert rc == 1
        m_apply.assert_not_called()

    # Stray relation not in id_map is reported & removed from PRG-T04.Chapters, while in-id_map relation stays
    entries_clean = [entries[0]]
    p_t04 = _notion_page("pidt04", "PRG-T04", "Backend", level="topic")
    p_t04["properties"]["Chapters"] = {
        "type": "relation",
        "relation": [{"id": "pidc01"}, {"id": "stray-chap-id"}],
    }
    pages_clean = {"pidt04": p_t04}
    id_map_clean = {
        "PRG-T04": {"id": "pidt04", "title": "Backend"},
        "PRG-T04-C01": {"id": "pidc01", "title": "Real Chap"},
    }
    pf2 = prg_migrate.run_preflight(entries_clean, id_map_clean, pages_clean)
    assert not pf2.errors
    assert any("stray-chap-id" in w for w in pf2.warnings)
    ops2, _ = prg_migrate.build_migration_plan(entries_clean, id_map_clean, pages_clean, [], "tok", preflight=pf2)
    assert len(ops2) == 1
    assert ops2[0].details["desired_props"]["Chapters"] == {"relation": [{"id": "pidc01"}]}
