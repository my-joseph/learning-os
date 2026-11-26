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


@pytest.mark.parametrize(
    ("spec", "answer"),
    [
        ({"type": "number", "value": "5"}, "-5"),
        ({"type": "expression", "value": "2*x"}, "-2*x"),
        ({"type": "tuple", "values": ["5", "3"]}, "-5,-3"),
        ({"type": "vector", "components": ["5", "3"]}, "-5,-3"),
    ],
)
def test_real_whole_sign_flip_diagnostic_avoids_complex_identity(spec, answer):
    result = math_check(spec, answer)
    assert result["diagnostics"]
    assert all("i^2 = -1" not in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_complex_whole_sign_flip_keeps_complex_identity_reminder():
    result = math_check({"type": "complex", "value": "3 + 4*I"}, "-3 - 4*I")
    diagnostic = next(d for d in result["diagnostics"] if d["code"] == "whole_sign_flip")
    assert "i^2 = -1" in diagnostic["message"]


def test_solution_set_sign_flip_diagnostic_is_domain_neutral():
    result = math_check({"type": "solution_set", "values": ["2", "5"]}, "-2, 5")
    diagnostic = next(d for d in result["diagnostics"] if d["code"] == "whole_sign_flip")
    assert "quadratic formula" not in diagnostic["message"]
    assert "sign" in diagnostic["message"].lower()


def test_solution_set_missing_root_mentions_pm_only_for_symmetric_roots():
    ordinary = math_check({"type": "solution_set", "values": ["2", "5"]}, "2")
    ordinary_diagnostic = next(d for d in ordinary["diagnostics"] if d["code"] == "missing_solution")
    assert "±" not in ordinary_diagnostic["message"]

    symmetric = math_check({"type": "solution_set", "values": ["-3", "3"]}, "3")
    symmetric_diagnostic = next(d for d in symmetric["diagnostics"] if d["code"] == "missing_solution")
    assert "\\pm" in symmetric_diagnostic["message"]

    declared_symmetric = math_check({"type": "solution_set", "values": ["2", "5"], "symmetricRoots": True}, "2")
    declared_diagnostic = next(d for d in declared_symmetric["diagnostics"] if d["code"] == "missing_solution")
    assert "\\pm" in declared_diagnostic["message"]


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


@pytest.mark.parametrize("check", [math_check, code_check])
def test_text_respects_case_sensitive_and_normalizes_whitespace(check):
    spec_default = {"type": "text", "accepted": ["Server-Only"]}
    assert check(spec_default, "server-only")["verdict"] == "correct"
    assert check(spec_default, "  SERVER-ONLY  ")["verdict"] == "correct"
    assert check(spec_default, "client-only")["verdict"] == "incorrect"

    spec_insensitive = {"type": "text", "accepted": ["Server-Only"], "case_sensitive": False}
    assert check(spec_insensitive, "server-only")["verdict"] == "correct"
    assert check(spec_insensitive, "SERVER-ONLY")["verdict"] == "correct"

    spec_sensitive = {"type": "text", "accepted": ["Server-Only"], "case_sensitive": True}
    assert check(spec_sensitive, "Server-Only")["verdict"] == "correct"
    assert check(spec_sensitive, "  Server-Only  ")["verdict"] == "correct"
    assert check(spec_sensitive, "server-only")["verdict"] == "incorrect"
    assert check(spec_sensitive, "SERVER-ONLY")["verdict"] == "incorrect"

    spec_multi_ws = {"type": "text", "accepted": ["read  committed"], "case_sensitive": True}
    assert check(spec_multi_ws, "read committed")["verdict"] == "correct"
    assert check(spec_multi_ws, "Read Committed")["verdict"] == "incorrect"


def test_math_answer_check_public_api_contract():
    """Lock every symbol imported across math_engine/, quality_rules.py, scripts/, and tests/."""
    import math_engine.answer_check as ac

    expected_symbols = [
        "MAX_INPUT_LEN",
        "WHITELIST_FUNCS",
        "TRUSTED_INTERNAL_FUNCS",
        "VETTED_EXTRA_FUNCS",
        "WHITELIST_CONSTANTS",
        "FORM_MESSAGES",
        "TRAP_VERDICTS",
        "SafeParseError",
        "EqualTimeoutError",
        "SecurityVisitor",
        "ASTTransformer",
        "safe_parse",
        "parse_math",
        "to_expr",
        "is_equal",
        "numeric_close",
        "generic_value_diagnostics",
        "form_issues",
        "parse_interval",
        "_intervals_equal",
        "_split_items",
        "check_number",
        "check_complex",
        "check_expression",
        "check_solution_set",
        "check_interval",
        "check_tuple",
        "check_choice",
        "check_text",
        "check_vector",
        "CHECKERS",
        "check_answer",
        "match_trap",
        "check_variant_answer",
        "is_omission_trap",
    ]
    for name in expected_symbols:
        assert hasattr(ac, name), f"Missing exported symbol on math_engine.answer_check: {name}"

    assert set(ac.CHECKERS.keys()) == {
        "number",
        "complex",
        "expression",
        "solution_set",
        "interval",
        "tuple",
        "choice",
        "text",
        "vector",
    }
    assert issubclass(ac.SafeParseError, ValueError)
    assert issubclass(ac.EqualTimeoutError, BaseException)


def test_math_answer_check_parsing_and_equivalence_characterization():
    import sympy as sp

    from math_engine.answer_check import (
        SafeParseError,
        _intervals_equal,
        _split_items,
        form_issues,
        generic_value_diagnostics,
        is_equal,
        is_omission_trap,
        match_trap,
        numeric_close,
        parse_interval,
        parse_math,
        safe_parse,
        to_expr,
    )

    assert safe_parse("2x + 1", variables=["x"]) == 2 * sp.Symbol("x") + 1
    assert parse_math("3 - 4i") == 3 - 4 * sp.I
    assert to_expr("<3, 4>") == sp.Matrix([3, 4])
    assert is_equal(parse_math("(x+1)**2", variables=["x"]), parse_math("x**2 + 2*x + 1", variables=["x"]), ["x"])
    assert numeric_close(sp.Rational(2, 3), sp.Float("0.667"))
    assert not numeric_close(sp.Rational(2, 3), sp.Rational(2, 3))

    with pytest.raises(SafeParseError):
        safe_parse("x**101", variables=["x"])

    assert _split_items("{x_1 = 2, x_2 = 1 +- 3}", "x") == ["2", "(1)+( 3)", "(1)-( 3)"]
    iv = parse_interval("[1, 3) U (4, inf)")
    assert _intervals_equal(iv, parse_interval("(4, oo) U [1, 3)"))

    tree = parse_math("2/4", evaluate=False)
    assert "unreduced_fraction" in form_issues(tree, ["reduced_fraction"])

    diags = generic_value_diagnostics(to_expr("1/5"), to_expr("5"))
    assert diags[0]["code"] == "reciprocal"

    spec_set = {"type": "solution_set", "values": ["-2", "2"], "variable": "x"}
    assert is_omission_trap(spec_set, "2") is True
    assert is_omission_trap(spec_set, "-2, 2") is False
    assert match_trap(spec_set, "2", "2") is True


def test_math_answer_check_cli_round_trips():
    import json
    import subprocess
    import sys

    def run_cli(payload: dict) -> dict:
        proc = subprocess.run(
            [sys.executable, "-m", "math_engine.answer_check"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(proc.stdout)

    ok = run_cli({"answerSpec": {"type": "complex", "value": "3 - 4*I", "forms": ["a+bi"]}, "input": "3 - 4i"})
    assert ok == {
        "verdict": "correct",
        "message": "Correct.",
        "components": [{"label": "Real part", "ok": True}, {"label": "Imaginary part", "ok": True}],
        "diagnostics": [],
    }

    bad_form = run_cli(
        {"answerSpec": {"type": "number", "value": "1/2", "forms": ["reduced_fraction"]}, "input": "2/4"}
    )
    assert bad_form["verdict"] == "equivalent_not_in_form"
    assert bad_form["diagnostics"][0]["code"] == "unreduced_fraction"

    trap = run_cli({"answerSpec": {"type": "number", "value": "10"}, "trapValue": "-10", "input": "-10"})
    assert trap["verdict"] == "incorrect"
    assert trap["trapMatched"] is True

    empty = run_cli({"answerSpec": {"type": "number", "value": "1"}, "input": "   "})
    assert empty["verdict"] == "invalid input"

    iv_res = run_cli({"answerSpec": {"type": "interval", "value": "[1, 5)"}, "input": "[1, 5]"})
    assert iv_res["verdict"] == "incorrect"
    assert iv_res["diagnostics"][0]["code"] == "wrong_bracket"

    vec_res = run_cli(
        {
            "answerSpec": {"type": "vector", "components": ["3", "4"], "allowPartial": True},
            "input": "<3, 5>",
        }
    )
    assert vec_res["verdict"] == "partial"
    assert vec_res["components"] == [{"label": "Component 1", "ok": True}, {"label": "Component 2", "ok": False}]
