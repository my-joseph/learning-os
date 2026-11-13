"""Drill -> Notion sync must never report success for a half-built page, and AI ingests must
carry the hierarchy/level fields the sync needs (gap found when syncing DRL-MTH-T02-C01-U01-03)."""

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
