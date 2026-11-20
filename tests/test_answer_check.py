"""Characterization tests: lock in current checker behavior (no network, no Notion)."""

import pytest

from code_engine.answer_check import check_answer as code_check
from math_engine.answer_check import check_answer as math_check


@pytest.mark.parametrize("check", [math_check, code_check])
def test_choice_correct_and_incorrect(check):
    spec = {"type": "choice", "correct": "C", "options": []}
    assert check(spec, "C")["verdict"] == "correct"
    assert check(spec, "A")["verdict"] == "incorrect"


@pytest.mark.parametrize("check", [math_check, code_check])
def test_choice_unknown_option_id_returns_invalid_input(check):
    """C-06: Undeclared option IDs must return non-substantive 'invalid input', not 'incorrect'."""
    spec = {
        "type": "choice",
        "correct": "B",
        "options": [
            {"id": "A", "label": "Option A"},
            {"id": "B", "label": "Option B"},
            {"id": "C", "label": "Option C"},
        ],
    }
    assert check(spec, "b")["verdict"] == "correct"
    assert check(spec, "A")["verdict"] == "incorrect"
    res = check(spec, "INVALID_CHOICE_Z")
    assert res["verdict"] == "invalid input"
    assert res["components"] == []
    assert res["diagnostics"] == []


def test_math_choice_is_case_insensitive():
    spec = {"type": "choice", "correct": "C", "options": []}
    assert math_check(spec, "c")["verdict"] == "correct"


def test_math_complex_accepts_equivalent_zero():
    spec = {"type": "complex", "value": "0 + (0)*I", "forms": ["a+bi"]}
    res = math_check(spec, "0")
    assert res["verdict"] == "correct"
    assert all(c["ok"] for c in res["components"])


def test_code_wrong_choice_reports_diagnostic():
    res = code_check({"type": "choice", "correct": "C"}, "B")
    assert res["verdict"] == "incorrect"
    assert res["diagnostics"][0]["code"] == "wrong_choice"


def test_number_answer_accepts_its_variable_assignment_and_superscripts():
    assert math_check({"type": "number", "value": "6", "variable": "x"}, "x = 6")["verdict"] == "correct"
    assert math_check({"type": "number", "value": "4", "variable": "x"}, "2²")["verdict"] == "correct"


def test_number_answer_assignment_errors_are_friendly():
    result = math_check({"type": "number", "value": "6", "variable": "x"}, "y = 6")
    assert result["verdict"] == "invalid input"
    assert "SyntaxError" not in result["message"] and "invalid syntax" not in result["message"]


def test_solution_set_decimal_approximation_requests_exact_form():
    result = math_check({"type": "solution_set", "values": ["sqrt(2)"]}, "1.4142")
    assert result["verdict"] == "incorrect"
    assert any(d["code"] == "decimal_not_exact" for d in result["diagnostics"])


def test_legacy_prg_answer_spec_types_deprecated_consistently():
    from code_engine.answer_check import CHECKERS, DEPRECATED_CHECKERS
    from math_engine.answer_spec_registry import (
        DEPRECATED_ANSWER_SPEC_TYPES,
        get_registered_types,
        validate_answer_spec,
    )

    legacy_types = ("code_output", "line_number", "find_bug")
    active_code_types = set(get_registered_types("code"))
    assert active_code_types == {"choice", "predict_output", "text"}
    assert set(CHECKERS.keys()) == active_code_types
    assert set(DEPRECATED_CHECKERS.keys()) == set(DEPRECATED_ANSWER_SPEC_TYPES.keys()) == set(legacy_types)

    # predict_output validates against tokens or value (matching code_engine/answer_check.py)
    assert validate_answer_spec({"type": "predict_output", "tokens": ["1", "3", "2"]}) == (True, None)
    assert validate_answer_spec({"type": "predict_output", "value": "1, 3, 2"}) == (True, None)
    ok_missing, err_missing = validate_answer_spec({"type": "predict_output"})
    assert ok_missing is False and err_missing is not None
    assert code_check({"type": "predict_output", "tokens": ["1", "3", "2"]}, "1, 3, 2")["verdict"] == "correct"

    # Deprecated types are rejected by validate_answer_spec and warn in code_engine.answer_check
    for legacy_type in legacy_types:
        ok, err = validate_answer_spec({"type": legacy_type})
        assert ok is False and err is not None and "Deprecated" in err

    with pytest.warns(DeprecationWarning, match="code_output"):
        assert code_check({"type": "code_output", "tokens": ["1", "2"]}, "1, 2")["verdict"] == "correct"
    with pytest.warns(DeprecationWarning, match="line_number"):
        assert code_check({"type": "line_number", "correctLine": 4}, "Line 4")["verdict"] == "correct"
    with pytest.warns(DeprecationWarning, match="find_bug"):
        assert code_check({"type": "find_bug", "correctLine": 8}, "8")["verdict"] == "correct"
