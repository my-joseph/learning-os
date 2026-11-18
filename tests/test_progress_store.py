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
    peek_sol = _doc()
    peek_sol["problems"][0]["state"] = {"userInput": "", "solutionRevealedBeforeAnswer": True}
    assert ps.has_practice(peek_sol), "opening the solution steps is learner activity too"


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


def test_item_score_matches_studio_rules():
    assert ps.item_score({"attempts": [{"verdict": "correct", "ts": "2026-11-16"}], "score": 1}) == (1.0, False)
    # Wrong -> open solution -> correct => 0.5, assisted
    assert ps.item_score(
        {
            "attempts": [
                {"verdict": "incorrect", "ts": "2026-11-16"},
                {"verdict": "correct", "ts": "2026-11-16", "solutionRevealed": True},
            ],
            "solutionRevealedBeforeAnswer": True,
            "score": 0.5,
        }
    ) == (0.5, True)
    # Wrong -> retry correct (unassisted) => 0.5, unassisted
    assert ps.item_score(
        {
            "attempts": [
                {"verdict": "incorrect", "ts": "2026-11-16"},
                {"verdict": "correct", "ts": "2026-11-16"},
            ],
            "score": 1,
        }
    ) == (0.5, False)
    # Format typo before first-try correct does not penalize
    assert ps.item_score(
        {
            "attempts": [
                {"verdict": "invalid input", "ts": "2026-11-16"},
                {"verdict": "correct", "ts": "2026-11-16"},
            ],
            "score": 1,
        }
    ) == (1.0, False)


def test_save_progress_refuses_to_blank_practised_progress():
    practised = _doc()
    practised["problems"][0]["state"] = {"userInput": "42", "score": 1, "attempts": [{"input": "42"}]}
    practised["sessionSummary"] = {"score": 1, "attemptDate": "2026-11-17", "practiceStatus": "Graded"}
    ps.save_progress(practised)

    saved = ps.load_progress("DRL-MTH-X-01")
    assert saved is not None and ps.has_practice(saved)

    # Attempting to overwrite with an empty or pristine-defaults doc must raise and preserve disk state
    with pytest.raises(ValueError, match="allow_reset=True"):
        ps.save_progress(_doc())

    pristine_defaults = _doc()
    pristine_defaults["problems"][0]["state"] = {"userInput": "", "score": None, "mistakes": []}
    pristine_defaults["sessionSummary"] = {"practiceStatus": "Ready", "score": 0, "attemptDate": None}
    with pytest.raises(ValueError, match="allow_reset=True"):
        ps.save_progress(pristine_defaults)

    still_there = ps.load_progress("DRL-MTH-X-01")
    assert still_there["problems"]["Q01"]["userInput"] == "42"
    assert still_there["sessionSummary"]["attemptDate"] == "2026-11-17"

    # Explicit reset is allowed
    ps.save_progress(_doc(), allow_reset=True)
    reset_prog = ps.load_progress("DRL-MTH-X-01")
    assert reset_prog is not None and not ps.has_practice(reset_prog)

    # Overwriting a pristine (non-practised) progress file does not require allow_reset
    ps.save_progress(_doc())
