"""Find-the-flaw L3 form (06 §2.3): shown-work lines are exempt from the givens/leak gates,
and the shown work must end at the trap value."""

import copy

import pytest

from math_engine.ai_drill_ingest import AiContractError, story_text, validate_ai_problem_contract


def flaw_problem():
    return {
        "id": "Q01",
        "level": 3,
        "verificationLevel": "partial",
        "prompt": (
            "A student multiplied $(2 + 3i)(4 - 2i)$ and wrote:\n"
            "Line 1: $(2 + 3i)(4 - 2i) = 8 - 4i + 12i - 6i^2$\n"
            "Line 2: $= 8 + 8i - 6i^2$\n"
            "Line 3: $= 8 + 8i - 6$\n"
            "Line 4: $= 2 + 8i$\n"
            "Which line is the first one that is wrong?"
        ),
        "display": "(a + bi)(c + di) = (ac - bd) + (ad + bc)i",
        "plainText": "(a + b*i)*(c + d*i)",
        "givens": {"a": 2, "b": 3, "c": 4, "d": 2},
        "answerSpec": {
            "type": "choice",
            "options": [
                {"id": "1", "label": "Line 1", "provenance": "flags a correct step"},
                {"id": "2", "label": "Line 2", "provenance": "flags a correct step"},
                {"id": "3", "label": "Line 3"},
                {"id": "4", "label": "Line 4", "trapTag": "positive-last-term"},
            ],
            "correct": "3",
        },
        "answerPlain": "3",
        "commonTrapTag": "positive-last-term",
        "trapDerivation": "(2*4 - 3*2) + (3*4 - 2*2)*I",
        "trapValue": "2 + 8*I",
        "verify": {
            "source": "14 + 8*I",
            "trapValue": "2 + 8*I",
            "flaw": {
                "values": ["8 - 4*I + 12*I - 6*I^2", "8 + 8*I - 6*I^2", "8 + 8*I - 6", "2 + 8*I"],
                "firstWrong": 3,
            },
        },
        "checkpointHint": "Check what each term becomes once the square of the imaginary unit is replaced",
        "steps": [{"latex": "14 + 8i", "explain": "The correct product.", "val": "14 + 8*I"}],
    }


def test_flaw_problem_passes_contract():
    assert validate_ai_problem_contract(flaw_problem())


def test_shown_work_lines_are_not_story_text():
    text = story_text(flaw_problem())
    assert "Line" not in text and "12i" not in text and "(2 + 3i)(4 - 2i)" in text


def test_non_flaw_prompt_keeps_line_text():
    prob = flaw_problem()
    prob["answerSpec"] = {"type": "complex", "value": "14 + 8*I"}
    assert story_text(prob) == prob["prompt"]


def test_shown_work_must_end_at_trap_value():
    prob = flaw_problem()
    prob["verify"]["flaw"]["values"][-1] = "14 + 8*I"
    with pytest.raises(AiContractError, match="end at the trap value"):
        validate_ai_problem_contract(prob)


def test_line_count_must_match_flaw_values():
    prob = flaw_problem()
    prob["verify"]["flaw"]["values"].append("2 + 8*I")
    with pytest.raises(AiContractError, match="one 'Line N"):
        validate_ai_problem_contract(prob)


def test_options_must_be_line_numbers():
    prob = flaw_problem()
    prob["answerSpec"]["options"][0]["id"] = "A"
    with pytest.raises(AiContractError, match="line numbers"):
        validate_ai_problem_contract(prob)


def test_story_numbers_still_need_givens():
    prob = copy.deepcopy(flaw_problem())
    prob["prompt"] = prob["prompt"].replace("A student", "At $7$ pm a student")
    with pytest.raises(AiContractError, match="not defined in givens"):
        validate_ai_problem_contract(prob)


def test_flaw_needs_at_least_four_lines():
    prob = flaw_problem()
    prob["prompt"] = (
        prob["prompt"]
        .replace("Line 2: $= 8 + 8i - 6i^2$\n", "")
        .replace("Line 3:", "Line 2:")
        .replace("Line 4:", "Line 3:")
    )
    prob["verify"]["flaw"] = {"values": ["8 - 4*I + 12*I - 6*I^2", "8 + 8*I - 6", "2 + 8*I"], "firstWrong": 2}
    prob["answerSpec"]["options"] = prob["answerSpec"]["options"][:3]
    with pytest.raises(AiContractError, match="at least 4"):
        validate_ai_problem_contract(prob)
