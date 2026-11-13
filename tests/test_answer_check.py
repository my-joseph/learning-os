"""Characterization tests: lock in current checker behavior (no network, no Notion)."""
import pytest

from code_engine.answer_check import check_answer as code_check
from math_engine.answer_check import check_answer as math_check


@pytest.mark.parametrize("check", [math_check, code_check])
def test_choice_correct_and_incorrect(check):
    spec = {"type": "choice", "correct": "C", "options": []}
    assert check(spec, "C")["verdict"] == "correct"
    assert check(spec, "A")["verdict"] == "incorrect"


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
