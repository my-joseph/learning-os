"""Regression tests ensuring per-component checker feedback never leaks missing expected values."""

import json

from math_engine.answer_check import check_solution_set, check_tuple, check_vector


def _blob(res: dict) -> str:
    return json.dumps({"message": res["message"], "components": res["components"], "diagnostics": res["diagnostics"]})


def test_solution_set_partial_never_leaks_missing_expected_solution():
    spec = {"type": "solution_set", "values": ["-sqrt(7)", "sqrt(7)"], "variable": "x"}
    res = check_solution_set(spec, "sqrt(7)")
    assert res["verdict"] == "partial"
    assert "1 missing" in res["message"]
    assert res["components"] == [{"label": "Your value $\\sqrt{7}$", "ok": True}]
    assert "sqrt(7)" not in _blob(res).replace("\\sqrt{7}", "") or "-\\sqrt{7}" not in _blob(res)
    assert "-\\sqrt{7}" not in _blob(res)


def test_solution_set_wrong_and_extra_never_leaks_expected_solutions():
    spec = {"type": "solution_set", "values": ["3", "11"], "variable": "x"}
    res = check_solution_set(spec, "3, 99")
    assert res["verdict"] == "partial"
    assert "1 of 2 expected values match; 1 missing, 1 extra" in res["message"]
    assert res["components"] == [
        {"label": "Your value $3$", "ok": True},
        {"label": "Your value $99$", "ok": False},
    ]
    assert "11" not in _blob(res)

    res_wrong = check_solution_set(spec, "99")
    assert res_wrong["verdict"] == "incorrect"
    assert "0 of 2 expected values match; 2 missing, 1 extra" in res_wrong["message"]
    assert res_wrong["components"] == [{"label": "Your value $99$", "ok": False}]
    assert "3" not in _blob(res_wrong)
    assert "11" not in _blob(res_wrong)


def test_tuple_and_vector_feedback_never_leak_expected_components():
    t_res = check_tuple({"type": "tuple", "values": ["17", "-29"], "labels": ["x", "y"]}, "17, 5")
    assert t_res["verdict"] == "partial"
    assert t_res["components"] == [{"label": "x", "ok": True}, {"label": "y", "ok": False}]
    assert "-29" not in _blob(t_res) and "29" not in _blob(t_res)

    v_res = check_vector({"type": "vector", "components": ["13", "-41"], "allowPartial": True}, "<13, 5>")
    assert v_res["verdict"] == "partial"
    assert v_res["components"] == [{"label": "Component 1", "ok": True}, {"label": "Component 2", "ok": False}]
    assert "-41" not in _blob(v_res) and "41" not in _blob(v_res)


def test_solution_set_partial_feedback_flags_extra_without_answer_leak():
    res = check_solution_set({"type": "solution_set", "values": ["3", "11"], "variable": "x"}, "3, 11, 99")
    assert res["verdict"] == "partial"
    assert "2 of 2 expected values match; 0 missing, 1 extra" in res["message"]
