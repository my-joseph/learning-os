"""Choice problems carry no CAS plainText (learner decision 2026-11-19)."""

import copy
import glob
import json

import pytest

from math_engine import ai_drill_ingest


def test_no_mth_choice_problem_has_plaintext() -> None:
    offenders = []
    for path in glob.glob("drills/data/**/DRL-MTH-*.json", recursive=True):
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        for prob in doc.get("problems", []):
            if (prob.get("answerSpec") or {}).get("type") == "choice" and "plainText" in prob:
                offenders.append(f"{doc['drillId']}/{prob.get('id')}")
    assert offenders == []


def test_template_draft_choice_problems_omit_plaintext() -> None:
    with open(".claude/skills/new-math-drill/template/draft.json", encoding="utf-8") as fh:
        draft = json.load(fh)
    for prob in draft["problems"]:
        if (prob.get("answerSpec") or {}).get("type") == "choice":
            assert "plainText" not in prob


def _choice_and_typed_problems() -> tuple[dict, dict]:
    with open("drills/data/MTH-T01-C04/DRL-MTH-T01-C04-01.json", encoding="utf-8") as fh:
        doc = json.load(fh)
    choice = next(p for p in doc["problems"] if p["answerSpec"]["type"] == "choice")
    typed = next(p for p in doc["problems"] if p["answerSpec"]["type"] != "choice")
    return copy.deepcopy(choice), copy.deepcopy(typed)


def test_contract_drops_plaintext_on_choice_and_still_requires_it_on_typed() -> None:
    choice, typed = _choice_and_typed_problems()
    choice["plainText"] = "A student simplified ... Which line is the first one that is wrong?"
    ai_drill_ingest.validate_ai_problem_contract(choice, enforce_leak_gate=False)
    assert "plainText" not in choice

    typed.pop("plainText", None)
    with pytest.raises(ai_drill_ingest.AiContractError, match="plainText"):
        ai_drill_ingest.validate_ai_problem_contract(typed, enforce_leak_gate=False)
