"""G2 for single-unit L4/L5: a passing blind-solve demand replaces category/constraints padding (06 §2.3),
and a solution_set answer can carry a trap value (07 §4)."""

import pytest

from math_engine.ai_drill_ingest import _trap_matches_spec
from quality_rules import QualityError, check_gate_g2

MODEL = {"setup": "model", "strategy": "choose", "check": "edge", "task": "compute", "reverse": False, "steps": 6}


def l4_problem(**overrides):
    prob = {
        "id": "Q01",
        "level": 4,
        "category": "Applied Synthesis",
        "references": ["MTH-TEST"],
        "commonTrapTag": "some-trap",
        "trapValue": "16",
        "steps": [{"latex": f"s_{i}", "explain": "step"} for i in range(6)],
    }
    prob.update(overrides)
    return prob


def test_single_unit_l4_without_blind_solve_still_needs_concepts():
    with pytest.raises(QualityError, match="concept"):
        check_gate_g2(l4_problem())


def test_blind_solve_at_label_satisfies_g2():
    assert check_gate_g2(l4_problem(blindSolve={"answer": "20", "ambiguous": False, **MODEL}))["passed"]


def test_g2_leaves_a_shallow_blind_solve_to_the_vault_gate():
    # G2 must not tell the author to pad `constraints`; validate_blind_solve rejects the level instead.
    shallow = {**MODEL, "setup": "translate"}  # L3
    assert check_gate_g2(l4_problem(blindSolve={"answer": "20", "ambiguous": False, **shallow}))["passed"]


def test_numeric_tolerance_is_absolute():
    from math_engine.answer_check import check_answer

    spec = {"type": "number", "value": "18.06", "tolerance": 0.005}
    assert check_answer(spec, "18")["verdict"] != "correct"
    assert check_answer(spec, "18.064")["verdict"] == "correct"
    rel = {"type": "number", "value": "18.06", "tolerance": {"rel": 0.005}}
    assert check_answer(rel, "18")["verdict"] == "correct"


SET_SPEC = {"type": "solution_set", "values": ["16", "4"], "variable": "X_L"}


def test_solution_set_trap_matches_partial_set():
    assert _trap_matches_spec(SET_SPEC, "16")


def test_solution_set_trap_must_be_parseable_set():
    assert not _trap_matches_spec(SET_SPEC, "not a value")


TRIG_SPEC = {"type": "solution_set", "values": ["pi/6", "5*pi/6"], "variable": "x"}


def test_principal_angle_only_is_an_omission_trap():
    from math_engine.ai_drill_ingest import _is_omission_trap

    assert _is_omission_trap(TRIG_SPEC, "pi/6")
    assert not _is_omission_trap(TRIG_SPEC, "pi/6, 5*pi/6")  # the full answer is not a trap
    assert not _is_omission_trap(TRIG_SPEC, "13*pi/6")  # not a subset: needs its own derivation
    assert not _is_omission_trap({"type": "number", "value": "3"}, "3")
