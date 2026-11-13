"""Learner progress lives in progress/<DRILL_ID>.json, never in drill content files."""

import glob
import json

import pytest

import progress_store as ps


def _doc():
    return {
        "drillId": "DRL-MTH-X-01",
        "unitCode": "MTH-X",
        "problems": [{"id": "Q01", "prompt": "p1"}, {"id": "Q02", "prompt": "p2"}],
    }


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    return tmp_path


def test_round_trip_overlays_state_and_summary():
    doc = _doc()
    doc["problems"][0]["state"] = {"userInput": "42", "score": 1, "attempts": [{"input": "41"}]}
    doc["sessionSummary"] = {"score": 1, "attemptDate": "2026-11-13"}
    ps.save_progress(doc)

    fresh = ps.apply_progress(_doc(), ps.load_progress("DRL-MTH-X-01"))
    assert fresh["problems"][0]["state"]["attempts"] == [{"input": "41"}]
    assert "state" not in fresh["problems"][1]
    assert fresh["sessionSummary"]["attemptDate"] == "2026-11-13"


def test_strip_removes_only_learner_fields():
    doc = _doc()
    doc["problems"][0]["state"] = {"score": 0}
    doc["sessionSummary"] = {}
    ps.strip_progress(doc)
    assert doc == _doc()


def test_pristine_defaults_are_not_practice():
    doc = _doc()
    doc["problems"][0]["state"] = {"userInput": "", "score": None, "mistakes": [], "lastCheck": None}
    doc["sessionSummary"] = {"practiceStatus": "Ready", "score": 0, "attemptDate": None}
    assert not ps.has_practice(doc)
    doc["problems"][1]["state"] = {"skipped": True}
    assert ps.has_practice(doc)
    peek = _doc()
    peek["problems"][0]["state"] = {"userInput": "", "setupRevealedBeforeAnswer": True}
    assert ps.has_practice(peek), "opening the set-up is learner activity too"


def test_migration_moves_practice_and_strips_content(tmp_path):
    from scripts.migrate_progress import migrate

    unit = tmp_path / "data" / "MTH-X"
    unit.mkdir(parents=True)
    practised = _doc()
    practised["problems"][0]["state"] = {"userInput": "7", "score": 1}
    (unit / "DRL-MTH-X-01.json").write_text(json.dumps(practised, indent=2), encoding="utf-8")
    pristine = dict(_doc(), drillId="DRL-MTH-X-02")
    pristine["sessionSummary"] = {"practiceStatus": "Ready", "score": 0}
    (unit / "DRL-MTH-X-02.json").write_text(json.dumps(pristine, indent=2) + "\n", encoding="utf-8")

    rep = migrate(str(tmp_path / "data"))
    assert rep["saved"] == ["DRL-MTH-X-01"] and len(rep["stripped"]) == 2
    assert ps.load_progress("DRL-MTH-X-01")["problems"]["Q01"]["userInput"] == "7"
    assert ps.load_progress("DRL-MTH-X-02") is None
    for f in unit.iterdir():
        content = f.read_text(encoding="utf-8")
        assert '"state"' not in content and "sessionSummary" not in content
    assert (unit / "DRL-MTH-X-02.json").read_text(encoding="utf-8").endswith("\n"), "trailing newline kept"


def test_committed_drills_hold_content_only():
    offenders = []
    for path in glob.glob("drills/data/*/DRL-*.json"):
        doc = json.load(open(path, encoding="utf-8"))
        if "sessionSummary" in doc or any("state" in p for p in doc.get("problems", [])):
            offenders.append(path)
    assert offenders == [], "practice state belongs in progress/, run scripts/migrate_progress.py"
