"""validate_against_vault: trap tags must come from the vault; L4/L5 need a passing blind solve (07 §4)."""

import pytest

from math_engine.ai_drill_ingest import AiContractError, validate_against_vault

ARCHETYPES = [
    {"archetypeKey": "string-traps", "cognitiveTraps": ["listed-trap"]},
    {"archetypeKey": "dict-traps", "cognitiveTraps": [{"trapTag": "dict-trap", "description": "..."}]},
]
GOOD_BLIND = {"answer": "20", "level": 4, "ambiguous": False}


def problem(**overrides):
    prob = {
        "id": "Q01",
        "level": 3,
        "archetypeKey": "string-traps",
        "commonTrapTag": "listed-trap",
        "answerSpec": {"type": "number", "value": "20", "tolerance": 0.001},
    }
    prob.update(overrides)
    return prob


def check(prob):
    validate_against_vault(prob, ARCHETYPES, "MTH-TEST")


def test_listed_string_and_dict_traps_pass():
    check(problem())
    check(problem(archetypeKey="dict-traps", commonTrapTag="dict-trap"))


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"archetypeKey": "missing"}, "not in the MTH-TEST reasoning vault"),
        ({"commonTrapTag": "invented-trap"}, "not one of archetype"),
        ({"commonTrapTag": None}, "not one of archetype"),
        ({"commonTrapTag": "dict-trap"}, "not one of archetype"),  # tag from another archetype
    ],
)
def test_vault_mismatch_rejected(overrides, match):
    with pytest.raises(AiContractError, match=match):
        check(problem(**overrides))


def test_l3_needs_no_blind_solve_record():
    check(problem(level=3))


@pytest.mark.parametrize("level", [4, 5])
def test_l4_l5_pass_with_matching_blind_solve(level):
    check(problem(level=level, blindSolve={**GOOD_BLIND, "level": level}))


@pytest.mark.parametrize(
    ("blind", "match"),
    [
        (None, "needs a 'blindSolve' record"),
        ({"answer": "20", "level": 4}, "needs a 'blindSolve' record"),
        ({**GOOD_BLIND, "ambiguous": True}, "ambiguous"),
        ({**GOOD_BLIND, "answer": "36"}, "does not match answerSpec"),
        ({**GOOD_BLIND, "level": 3}, "rated it L3"),
    ],
)
def test_l4_blind_solve_failures_rejected(blind, match):
    prob = problem(level=4)
    if blind is not None:
        prob["blindSolve"] = blind
    with pytest.raises(AiContractError, match=match):
        check(prob)


def test_interleaved_category_does_not_bypass_blind_solve():
    with pytest.raises(AiContractError, match="rated it L2"):
        check(problem(level=4, category="Interleaved Synthesis", blindSolve={**GOOD_BLIND, "level": 2}))
