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
