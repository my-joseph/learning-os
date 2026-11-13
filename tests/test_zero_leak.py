"""Zero-leak invariant (rules/00_core.md section 6): hints must never contain the answer."""
import copy

from drill_sync import validate_and_sanitize_drill_doc


def _doc(hint, accepted, subject="PRG", **extra):
    prob = {"answerSpec": {"accepted": accepted}, "answerPlain": accepted[0], "inputHint": hint, **extra}
    return {"subject": subject, "problems": [prob]}


def test_hint_leaking_answer_is_replaced():
    doc = _doc("Type the 3-digit status code (e.g. 401).", ["401"], codeType="predict-output")
    validate_and_sanitize_drill_doc(doc)
    assert "401" not in doc["problems"][0]["inputHint"]


def test_hint_with_only_leaking_example_keeps_contract_text():
    doc = _doc("Enter 3-digit HTTP status code (e.g. 401)", ["401"])
    validate_and_sanitize_drill_doc(doc)
    assert doc["problems"][0]["inputHint"] == "Enter 3-digit HTTP status code"


def test_disjoint_hint_is_unchanged():
    doc = _doc("Enter 3-digit HTTP status code (e.g. 200, 500)", ["401"])
    before = copy.deepcopy(doc)
    validate_and_sanitize_drill_doc(doc)
    assert doc == before


def test_all_committed_drills_have_no_leaking_hints():
    import glob, json
    for path in glob.glob("drills/data/*/DRL-*.json"):
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        before = copy.deepcopy(doc)
        validate_and_sanitize_drill_doc(doc)
        assert doc == before, f"leaking inputHint in {path}"


def test_save_drill_doc_sanitizes_and_writes(tmp_path, monkeypatch):
    import json

    from drill_sync import save_drill_doc

    monkeypatch.chdir(tmp_path)
    doc = _doc("Type the 3-digit status code (e.g. 401).", ["401"], codeType="predict-output")
    doc.update({"drillId": "DRL-X-01", "unitCode": "PRG-X"})
    path = save_drill_doc(doc)
    saved = json.loads((tmp_path / path).read_text(encoding="utf-8"))
    assert path.endswith("PRG-X/DRL-X-01.json")
    assert "401" not in saved["problems"][0]["inputHint"]
