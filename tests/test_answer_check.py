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
