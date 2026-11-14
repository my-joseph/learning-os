"""G4 trapGivens: decimal givens count by value (a ramp in metres, a price of 2.5)."""

import pytest

from math_engine.verify import _number_tokens, verify_problem
from quality_rules import QualityError


def problem(prompt, derivation, trap_value, trap_givens):
    return {
        "id": "Q01",
        "level": 1,
        "prompt": prompt,
        "plainText": "x",
        "answerPlain": "4",
        "answerDisplay": "4",
        "answerSpec": {"type": "number", "value": "4"},
        "verify": {"source": "4", "trapValue": trap_value},
        "commonTrapTag": "arithmetic-error",
        "steps": [{"latex": "4", "explain": "result", "val": "4"}],
        "checkpointHint": "Check the units",
        "references": ["MTH-T01-C12-U01"],
        "trapDerivation": derivation,
        "trapGivens": trap_givens,
    }


def test_number_tokens_keep_decimals_whole():
    assert _number_tokens("2.5*0.6 + 12.5 - .5 + r^2") == {2.5, 0.6, 12.5, 0.5, 2.0}


def test_decimal_givens_match_derivation():
    prob = problem("A ramp rises $0.6$ m over $7.2$ m.", "0.6 * 7.2", "4.32", [0.6, 7.2])
    assert verify_problem(prob)


def test_float_given_matches_integer_literal():
    prob = problem("Find the sum of $2$ and $3$.", "2 + 3", "5", [2.0, 3.0])
    assert verify_problem(prob)


def test_decimal_is_not_matched_by_its_digits():
    # 2.5 in the derivation must not count as the givens 2 and 5.
    prob = problem("Use $2$ and $5$.", "2.5 * 2", "5", [2, 5])
    with pytest.raises(QualityError, match="at least 2 distinct givens"):
        verify_problem(prob)


def test_missing_decimal_given_still_rejected():
    prob = problem("A ramp rises $0.6$ m.", "0.6 * 7.2", "4.32", [0.6, 7.2])
    with pytest.raises(QualityError, match="does not appear in prompt"):
        verify_problem(prob)
