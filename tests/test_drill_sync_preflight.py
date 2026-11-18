"""Drill -> Notion sync must never report success for a half-built page, and AI ingests must
carry the hierarchy/level fields the sync needs (gap found when syncing DRL-MTH-T02-C01-U01-03)."""

import json

import pytest

from code_engine import fmt as code_fmt
from math_engine import fmt as math_fmt
from notion_sync import drill_sync


def _doc(**overrides):
    doc = {
        "drillId": "DRL-MTH-T02-C01-U01-99",
        "unitCode": "MTH-T02-C01-U01",
        "chapterCode": "MTH-T02-C01",
        "topicCode": "MTH-T02",
        "problems": [
            {
                "id": "Q01",
                "levelLabel": "Level 1 - Foundation",
                "category": "Core Skill",
                "prompt": "Evaluate $3i^2 + 10$.",
                "steps": [{"latex": "i^2 = -1", "explain": "Use the definition of i."}],
            }
        ],
    }
    doc.update(overrides)
    return doc


@pytest.fixture
def no_disk(monkeypatch, tmp_path):
    monkeypatch.setenv("DRILLS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)


def test_unit_hierarchy_is_the_same_in_both_engines():
    for code in ("MTH-T02-C01-U01", "PRG-T00-C02", "MTH-SYNTHESIS", "PHY"):
        assert math_fmt.unit_hierarchy(code) == code_fmt.unit_hierarchy(code)
    assert math_fmt.unit_hierarchy("MTH-T02-C01-U01") == ("MTH-T02", "MTH-T02-C01")


def test_missing_fields_listed_before_any_notion_call(no_disk, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("must not reach Notion")

    monkeypatch.setattr(drill_sync, "_sync_drill_to_notion_inner", boom)
    doc = _doc()
    del doc["chapterCode"]
    del doc["problems"][0]["levelLabel"]
    res = drill_sync.sync_drill_to_notion(doc)
    assert res["ok"] is False
    assert "drill.chapterCode" in res["error"] and "Q01.levelLabel" in res["error"]


def test_complete_drill_passes_preflight():
    assert drill_sync.missing_sync_fields(_doc()) == []


def test_notion_outage_is_degraded_not_failed(no_disk, monkeypatch):
    def outage(*a, **k):
        raise RuntimeError("HTTP 503 on POST pages")

    monkeypatch.setattr(drill_sync, "_sync_drill_to_notion_inner", outage)
    res = drill_sync.sync_drill_to_notion(_doc())
    assert res["ok"] is True and res["degraded"] is True
    assert "Notion was not updated" in res["warning"]


def test_bug_during_sync_is_reported_as_failure(no_disk, monkeypatch):
    def bug(*a, **k):
        raise KeyError("levelLabel")

    monkeypatch.setattr(drill_sync, "_sync_drill_to_notion_inner", bug)
    res = drill_sync.sync_drill_to_notion(_doc())
    assert res["ok"] is False and "KeyError" in res["error"]


def test_cli_dry_run_by_path_and_drill_id(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    unit_dir = data_dir / "MTH-T02-C01-U01"
    unit_dir.mkdir(parents=True)
    drill_file = unit_dir / "DRL-MTH-T02-C01-U01-99.json"
    drill_file.write_text(json.dumps(_doc()), encoding="utf-8")

    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_dir))
    monkeypatch.setattr(drill_sync, "save_progress", lambda doc: None)

    def boom(*a, **k):
        raise AssertionError("dry-run must not call Notion")

    monkeypatch.setattr(drill_sync, "_sync_drill_to_notion_inner", boom)

    assert drill_sync.main([str(drill_file), "--dry-run"]) == 0
    out1 = json.loads(capsys.readouterr().out)
    assert out1["ok"] is True and out1["dryRun"] is True

    assert drill_sync.main(["DRL-MTH-T02-C01-U01-99", "--dry-run"]) == 0
    out2 = json.loads(capsys.readouterr().out)
    assert out2["ok"] is True and out2["dryRun"] is True


def test_cli_sync_uses_client_and_returns_nonzero_on_missing(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    unit_dir = data_dir / "MTH-T02-C01-U01"
    unit_dir.mkdir(parents=True)
    drill_file = unit_dir / "DRL-MTH-T02-C01-U01-99.json"
    drill_file.write_text(json.dumps(_doc()), encoding="utf-8")

    (tmp_path / "id_map.json").write_text(
        json.dumps({"DRILLS_DB": {"id": "db-1"}, "MTH-T02-C01-U01": {"id": "u-1"}}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_dir))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)
    monkeypatch.setattr(drill_sync, "save_progress", lambda doc: None)
    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "fake-token"})

    calls = []

    def fake_notion_request(method, path, token, payload=None):
        calls.append((method, path))
        if method == "POST" and path.endswith("/query"):
            return {"results": []}
        if method == "POST" and path == "pages":
            return {"id": "page-123"}
        return {}

    monkeypatch.setattr(drill_sync, "notion_request", fake_notion_request)
    monkeypatch.setattr(drill_sync, "replace_page_blocks", lambda *a, **k: None)

    assert drill_sync.main(["DRL-MTH-T02-C01-U01-99"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True and out["drillPageId"] == "page-123"
    assert ("POST", "pages") in calls

    assert drill_sync.main(["DRL-DOES-NOT-EXIST"]) == 1


def test_cli_sync_preserves_practised_progress_and_id_map_newline(tmp_path, monkeypatch, capsys):
    import progress_store

    data_dir = tmp_path / "data"
    unit_dir = data_dir / "MTH-T02-C01-U01"
    unit_dir.mkdir(parents=True)
    drill_file = unit_dir / "DRL-MTH-T02-C01-U01-99.json"
    drill_file.write_text(json.dumps(_doc()), encoding="utf-8")

    (tmp_path / "id_map.json").write_text(
        json.dumps({"DRILLS_DB": {"id": "db-1"}, "MTH-T02-C01-U01": {"id": "u-1"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_dir))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)

    practised = _doc()
    practised["problems"][0]["state"] = {
        "userInput": "7",
        "score": 1,
        "attempts": [{"input": "7", "verdict": "correct"}],
    }
    practised["sessionSummary"] = {"practiceStatus": "Graded", "score": 1, "maxScore": 1, "attemptDate": "2026-11-17"}
    progress_store.save_progress(practised)

    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "fake-token"})
    monkeypatch.setattr(
        drill_sync,
        "notion_request",
        lambda method, path, token, payload=None: (
            {"results": []} if method == "POST" and path.endswith("/query") else {"id": "page-123"}
        ),
    )
    monkeypatch.setattr(drill_sync, "replace_page_blocks", lambda *a, **k: None)
    monkeypatch.setattr(drill_sync, "update_unit_reviews", lambda *a, **k: {})
    monkeypatch.setattr(drill_sync, "get_all_blocks", lambda *a, **k: [])

    assert drill_sync.main(["DRL-MTH-T02-C01-U01-99"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True

    reloaded = progress_store.load_progress("DRL-MTH-T02-C01-U01-99")
    assert reloaded is not None
    assert reloaded["sessionSummary"]["attemptDate"] == "2026-11-17"
    assert reloaded["sessionSummary"]["score"] == 1
    assert reloaded["problems"]["Q01"]["userInput"] == "7"

    id_map_raw = (tmp_path / "id_map.json").read_text(encoding="utf-8")
    assert id_map_raw.endswith("\n") and not id_map_raw.endswith("\n\n")
    assert id_map_raw == json.dumps(json.loads(id_map_raw), ensure_ascii=False, indent=2) + "\n"


def test_cli_content_only_skips_progress_and_unit_writes(tmp_path, monkeypatch, capsys):
    import progress_store
    from notion_sync import unit_page

    data_dir = tmp_path / "data"
    unit_dir = data_dir / "MTH-T02-C01-U01"
    unit_dir.mkdir(parents=True)
    drill_file = unit_dir / "DRL-MTH-T02-C01-U01-99.json"
    drill_file.write_text(json.dumps(_doc()), encoding="utf-8")

    (tmp_path / "id_map.json").write_text(
        json.dumps({"DRILLS_DB": {"id": "db-1"}, "MTH-T02-C01-U01": {"id": "u-1"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_dir))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)

    practised = _doc()
    practised["problems"][0]["state"] = {"userInput": "7", "score": 1}
    practised["sessionSummary"] = {
        "practiceStatus": "Graded",
        "score": 1,
        "maxScore": 1,
        "accuracyPct": 100,
        "attemptDate": "2026-11-17",
    }
    prog_file_path = progress_store.save_progress(practised)
    prog_before = open(prog_file_path, encoding="utf-8").read()

    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "fake-token"})

    notion_calls = []

    def fake_notion_request(method, path, token, payload=None):
        notion_calls.append((method, path, payload))
        if method == "POST" and path.endswith("/query"):
            return {"results": [{"id": "page-existing"}]}
        return {"id": "page-existing"}

    replaced = []
    monkeypatch.setattr(drill_sync, "notion_request", fake_notion_request)
    monkeypatch.setattr(drill_sync, "replace_page_blocks", lambda pid, blocks, did, tok: replaced.append((pid, blocks)))

    def fail(*a, **k):
        raise AssertionError("must not be called in --content-only mode")

    monkeypatch.setattr(drill_sync, "save_progress", fail)
    monkeypatch.setattr(drill_sync, "update_unit_reviews", fail)
    monkeypatch.setattr(drill_sync, "merge_review_schedule", fail)
    monkeypatch.setattr(drill_sync, "get_all_blocks", fail)
    monkeypatch.setattr(unit_page, "insert_after", fail)

    assert drill_sync.main(["DRL-MTH-T02-C01-U01-99", "--content-only"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True and out["drillPageId"] == "page-existing"
    assert out["unitReviews"] == {}

    # Drill page updated with merged progress and question blocks
    patch_calls = [c for c in notion_calls if c[0] == "PATCH" and c[1] == "pages/page-existing"]
    assert len(patch_calls) == 1
    props = patch_calls[0][2]["properties"]
    assert props["Score"]["number"] == 1.0
    assert props["Practice Status"]["select"]["name"] == "Graded"
    assert len(replaced) == 1

    # Local progress and review cache untouched
    assert open(prog_file_path, encoding="utf-8").read() == prog_before
    assert not (tmp_path / "progress" / "_review_schedule.json").exists()
    id_map_raw = (tmp_path / "id_map.json").read_text(encoding="utf-8")
    assert id_map_raw.endswith("\n") and not id_map_raw.endswith("\n\n")


def test_cli_content_only_creates_no_progress_file_for_pristine_drill(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    unit_dir = data_dir / "MTH-T02-C01-U01"
    unit_dir.mkdir(parents=True)
    (unit_dir / "DRL-MTH-T02-C01-U01-99.json").write_text(json.dumps(_doc()), encoding="utf-8")
    (tmp_path / "id_map.json").write_text(
        json.dumps({"DRILLS_DB": {"id": "db-1"}, "MTH-T02-C01-U01": {"id": "u-1"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_dir))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)
    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "fake-token"})
    monkeypatch.setattr(
        drill_sync,
        "notion_request",
        lambda method, path, token, payload=None: (
            {"results": []} if method == "POST" and path.endswith("/query") else {"id": "page-123"}
        ),
    )
    monkeypatch.setattr(drill_sync, "replace_page_blocks", lambda *a, **k: None)

    assert drill_sync.main(["DRL-MTH-T02-C01-U01-99", "--content-only"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert not (tmp_path / "progress").exists()
