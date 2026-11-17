"""Regression tests for equality of logarithmic expressions on shared real domains."""

from math_engine.answer_check import check_answer, is_equal, to_expr


def _same_on_shared_domain(left: str, right: str) -> bool:
    variables = ["x"]
    return is_equal(
        to_expr(left, variables=variables),
        to_expr(right, variables=variables),
        variables=variables,
    )


def test_log_power_identity_on_positive_shared_domain():
    assert _same_on_shared_domain("ln(x^2)", "2*ln(x)")


def test_log_absolute_value_identity_on_positive_shared_domain():
    assert _same_on_shared_domain("ln(x)", "ln(abs(x))")


def test_log_power_identity_on_negative_only_shared_domain():
    assert _same_on_shared_domain("ln(x^2)", "2*ln(-x)")


def test_log_forms_that_differ_on_the_shared_domain_remain_unequal():
    assert not _same_on_shared_domain("ln(x^2)", "ln(abs(x))")


def test_log_forms_without_a_shared_real_domain_are_not_equal():
    assert not _same_on_shared_domain("ln(x)", "ln(-x)")


def test_expression_answer_accepts_equivalent_log_form_on_its_real_domain():
    result = check_answer(
        {"type": "expression", "value": "ln(x^2)", "variables": ["x"]},
        "2*ln(x)",
    )
    assert result["verdict"] == "correct"
