"""validate_against_vault: trap tags must come from the vault; L3+ must pass the blind-solve floor gate (06 §2.3, 07 §4)."""

import pytest

from math_engine.ai_drill_ingest import AiContractError, demand_level, validate_against_vault

ARCHETYPES = [
    {"archetypeKey": "string-traps", "cognitiveTraps": ["listed-trap"]},
    {"archetypeKey": "dict-traps", "cognitiveTraps": [{"trapTag": "dict-trap", "description": "..."}]},
]
# Ramp-style problem: build a model from two relations and check it against a limit -> L4.
MODEL = {"setup": "model", "strategy": "prescribed", "check": "edge", "task": "compute", "reverse": False, "steps": 6}
# "35% of 240": given, prescribed, no check -> L1 (mental-math level).
DIRECT = {"setup": "given", "strategy": "prescribed", "check": "none", "task": "compute", "reverse": False, "steps": 2}
GOOD_BLIND = {"answer": "20", "ambiguous": False, **MODEL}


def problem(**overrides):
    prob = {
        "id": "Q01",
        "level": 2,
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


def test_l1_l2_need_no_blind_solve_record():
    check(problem(level=1))
    check(problem(level=2))


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        (DIRECT, 1),
        ({**DIRECT, "reverse": True}, 2),
        ({**DIRECT, "setup": "translate"}, 2),
        ({**DIRECT, "steps": 4}, 2),
        ({**DIRECT, "task": "diagnose"}, 3),
        ({**DIRECT, "check": "edge"}, 3),
        ({**DIRECT, "strategy": "choose"}, 3),
        ({**DIRECT, "setup": "model"}, 3),
        (MODEL, 4),
        ({**DIRECT, "setup": "model", "check": "justify"}, 4),
        ({**DIRECT, "strategy": "invent"}, 5),
    ],
)
def test_demand_level_mapping(tags, expected):
    assert demand_level(tags) == expected


@pytest.mark.parametrize("level", [3, 4])
def test_tags_at_or_above_label_pass(level):
    check(problem(level=level, blindSolve=GOOD_BLIND))  # tags give L4


def test_l3_must_reach_label_too():
    with pytest.raises(AiContractError, match="give L2"):
        check(problem(level=3, blindSolve={"answer": "20", "ambiguous": False, **DIRECT, "reverse": True}))


@pytest.mark.parametrize(("level", "shallow"), [(4, {**MODEL, "check": "none"}), (5, MODEL)])
def test_l4_l5_must_reach_label_exactly(level, shallow):
    with pytest.raises(AiContractError, match=f"give L{level - 1}"):
        check(problem(level=level, blindSolve={"answer": "20", "ambiguous": False, **shallow}))


@pytest.mark.parametrize(
    "tail",
    [
        "If it fits, report the diameter in cm; otherwise report $0$.",
        "If the run fits within the bay, report the ramp length. Otherwise, answer 0.",
        "Report the height if it fits the fairing; if not, write $0$.",
    ],
)
def test_sentinel_fallback_answer_rejected(tail):
    prob = problem(level=4, blindSolve=GOOD_BLIND, prompt=f"A tank holds $20$ L. {tail}")
    with pytest.raises(AiContractError, match="fallback answer"):
        check(prob)


def test_real_limit_is_not_a_sentinel():
    prompt = "The budget is capped at $2198$ dollars. What is the largest lane width that stays within budget?"
    check(problem(level=4, blindSolve=GOOD_BLIND, prompt=prompt))


@pytest.mark.parametrize(
    ("level", "blind", "match"),
    [
        (3, None, "needs a 'blindSolve' record"),
        (4, {"answer": "20", "level": 4, "ambiguous": False}, "missing"),
        (4, {**GOOD_BLIND, "ambiguous": True}, "ambiguous"),
        (4, {**GOOD_BLIND, "answer": "36"}, "does not match answerSpec"),
        (4, {**GOOD_BLIND, "setup": "hard"}, "blindSolve.setup"),
        (4, {**GOOD_BLIND, "steps": "6"}, "steps an integer"),
        (3, {"answer": "20", "ambiguous": False, **DIRECT}, "direct computation"),
        (4, {"answer": "20", "ambiguous": False, **DIRECT, "reverse": True}, "give L2"),
        (5, {"answer": "20", "ambiguous": False, **DIRECT, "check": "edge"}, "give L3"),
        (4, {"answer": "20", "ambiguous": False, **DIRECT, "check": "edge"}, "give L3"),
    ],
)
def test_blind_solve_failures_rejected(level, blind, match):
    prob = problem(level=level)
    if blind is not None:
        prob["blindSolve"] = blind
    with pytest.raises(AiContractError, match=match):
        check(prob)


def test_interleaved_category_does_not_bypass_blind_solve():
    shallow = {"answer": "20", "ambiguous": False, **DIRECT}
    with pytest.raises(AiContractError, match="direct computation"):
        check(problem(level=4, category="Interleaved Synthesis", blindSolve=shallow))
