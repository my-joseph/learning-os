# -*- coding: utf-8 -*-
"""Tests for the `interval` answer type in answer_check, registry, and ai_drill_ingest."""

import json
from pathlib import Path

import pytest

from math_engine.ai_drill_ingest import _trap_matches_spec, validate_ai_problem_contract
from math_engine.answer_check import check_answer, is_omission_trap, match_trap
from math_engine.answer_spec_registry import get_registered_types, validate_answer_spec
from math_engine.verify import VerificationError, verify_problem


def test_interval_registered():
    assert "interval" in get_registered_types("math")
    assert validate_answer_spec({"type": "interval", "value": "[3, 21)"}) == (True, None)
    ok, err = validate_answer_spec({"type": "interval"})
    assert not ok and "value" in (err or "")


def test_interval_accepted_forms():
    spec = {"type": "interval", "value": "[3, 21)"}
    for raw in ["[3, 21)", " [ 3 , 21 ) ", "[6/2, 21)", "[sqrt(9), 21)"]:
        assert check_answer(spec, raw)["verdict"] == "correct", f"expected correct for {raw!r}"

    union_spec = {"type": "interval", "value": "(-oo, 2) U (2, oo)"}
    for raw in [
        "(-oo, 2) U (2, oo)",
        "(-inf, 2) U (2, inf)",
        "(-∞, 2) ∪ (2, ∞)",
        "(-infinity, 2) u (2, infinity)",
        r"(-\infty, 2) \cup (2, \infty)",
        "(2, inf) U (-inf, 2)",  # reversed union order
        " ( -inf , 2 )U( 2 , inf ) ",
    ]:
        assert check_answer(union_spec, raw)["verdict"] == "correct", f"expected correct for {raw!r}"

    # Adjacent / overlapping intervals merge
    assert check_answer({"type": "interval", "value": "[1, 3]"}, "[1, 2) U [2, 3]")["verdict"] == "correct"
    assert (
        check_answer({"type": "interval", "value": "(-oo, oo)"}, "(-inf, 2) U {2} U (2, inf)")["verdict"] == "correct"
    )

    # Exact SymPy endpoints & finite decimals
    assert check_answer({"type": "interval", "value": "[sqrt(2), 3]"}, "[sqrt(8)/2, 3]")["verdict"] == "correct"
    assert check_answer({"type": "interval", "value": "[1/2, 3]"}, "[0.5, 3]")["verdict"] == "correct"
    assert check_answer({"type": "interval", "value": "{3} U [5, oo)"}, "[3, 3] U [5, inf)")["verdict"] == "correct"


def test_interval_rejected_forms():
    spec = {"type": "interval", "value": "[3, 21)"}
    for raw in ["(3, 21)", "[3, 21]", "(3, 21]"]:
        res = check_answer(spec, raw)
        assert res["verdict"] == "incorrect", f"expected incorrect for {raw!r}"
        assert any(d["code"] == "wrong_bracket" for d in res["diagnostics"])

    union_spec = {"type": "interval", "value": "(-oo, 2) U (2, oo)"}
    res_missing = check_answer(union_spec, "(2, inf)")
    assert res_missing["verdict"] == "incorrect"
    assert any(d["code"] == "missing_interval" for d in res_missing["diagnostics"])

    res_extra = check_answer(union_spec, "(-inf, inf)")
    assert res_extra["verdict"] == "incorrect"
    assert any(d["code"] in ("wrong_bracket", "extra_interval") for d in res_extra["diagnostics"])

    res_superset = check_answer({"type": "interval", "value": "[1, 3]"}, "[0, 5]")
    assert res_superset["verdict"] == "incorrect"
    assert any(d["code"] == "extra_interval" for d in res_superset["diagnostics"])

    # Rounded decimal is not exact
    assert check_answer({"type": "interval", "value": "[sqrt(2), 3]"}, "[1.414, 3]")["verdict"] == "incorrect"


def test_interval_format_errors_do_not_leak():
    spec = {"type": "interval", "value": "[17, 43)"}
    bad_inputs = [
        "x >= 17",
        "17 <= x < 43",
        "17",
        "[17, 43",
        "(17, 43))",
        "[17, inf]",
        "[-oo, 43)",
        "[43, 17]",
        "[17]",
        "[1, 2, 3]",
        "(1, 2), (3, 4)",
        "(1, 2) and (3, 4)",
        "[1 + I, 5]",
    ]
    for raw in bad_inputs:
        res = check_answer(spec, raw)
        assert res["verdict"] == "invalid input", f"expected invalid input for {raw!r}, got {res}"
        assert "17" not in res["message"] and "43" not in res["message"]


def test_interval_match_trap_and_omission():
    spec = {"type": "interval", "value": "[3, 21)"}
    assert match_trap(spec, "( 3 , 21 )", "(3, 21)") is True
    assert match_trap(spec, "[3, 21]", "(3, 21)") is False

    union_spec = {"type": "interval", "value": "(-oo, 2) U (2, oo)"}
    assert match_trap(union_spec, "(2, inf)", "(2, oo)") is True
    assert is_omission_trap(union_spec, "(2, inf)") is True
    assert is_omission_trap(spec, "[3, 21]") is False


def test_interval_ingest_contract():
    prob = {
        "id": "Q01",
        "prompt": "Find the domain of $f(x) = \\sqrt{x - 3}$.",
        "givens": {"a": 3},
        "display": "f(x) = \\sqrt{x - 3}",
        "plainText": "sqrt(x - 3)",
        "answerSpec": {"type": "interval", "value": "[3, oo)"},
        "answerPlain": "[3, oo)",
        "answerDisplay": "[3, \\infty)",
        "checkpointHint": "Set the radicand to be non-negative.",
        "commonTrapTag": "t02-c02-u02-radical-negative-or-zero-endpoint-trap",
        "trapDerivation": "(3, oo)",
        "trapValue": "(3, oo)",
        "steps": [{"latex": "x - 3 \\ge 0", "explain": "Radicand must be non-negative."}],
        "verificationLevel": "partial",
    }
    assert validate_ai_problem_contract(prob) is True
    assert _trap_matches_spec(prob["answerSpec"], prob["trapValue"]) is True


def test_interval_verify_source_and_step_values_are_machine_checked():
    path = Path(__file__).resolve().parents[1] / "drills/data/MTH-T02-C02-U07/DRL-MTH-T02-C02-U07-01.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    problem = next(p for p in doc["problems"] if p["id"] == "Q03")
    problem["verify"] = {**problem.get("verify", {}), "source": "[1,9)"}
    problem["steps"][0]["val"] = "[1,9)"
    assert verify_problem(problem) is True

    problem["steps"][0]["val"] = "[0,9)"
    with pytest.raises(VerificationError, match="step 1 interval"):
        verify_problem(problem)


def test_selection_trap_metadata_alone_does_not_require_scalar_step_check():
    path = Path(__file__).resolve().parents[1] / "drills/data/MTH-T02-C02-U07/DRL-MTH-T02-C02-U07-01.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    problem = next(p for p in doc["problems"] if p["id"] == "Q03")
    assert "source" not in problem.get("verify", {})
    assert verify_problem(problem) is True


def test_solution_set_superset_trap_passes_ingest_contract():
    prob = {
        "id": "Q01",
        "prompt": "Solve $x^2 - 8x + 15 = 0$.",
        "givens": {"a": 8, "b": 15},
        "display": "x^2 - 8x + 15 = 0",
        "plainText": "x^2 - 8x + 15 = 0",
        "answerSpec": {"type": "solution_set", "values": ["3", "5"], "variable": "x"},
        "answerPlain": "3, 5",
        "answerDisplay": "3, 5",
        "checkpointHint": "Factor the quadratic and test every candidate.",
        "commonTrapTag": "extra-candidate-trap",
        "trapDerivation": "3, 5, 8, 15",
        "trapValue": "3, 5, 8, 15",
        "steps": [{"latex": "(x - 3)(x - 5) = 0", "explain": "Factor the quadratic."}],
        "verificationLevel": "partial",
    }
    assert validate_ai_problem_contract(prob) is True
