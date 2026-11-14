"""Real-world context gate (rules/07 §4.8): a story needs a separate reviewer's contextCheck."""

import pytest

from math_engine.ai_drill_ingest import AiContractError, validate_context_check


def _prob(**extra):
    return {"id": "Q01", "level": 1, **extra}


@pytest.mark.parametrize("ctx", [None, "", "   "])
def test_plain_problem_needs_no_check(ctx):
    validate_context_check(_prob(context=ctx))


def test_context_without_check_is_rejected():
    with pytest.raises(AiContractError, match="contextCheck"):
        validate_context_check(_prob(context="ac_series_impedance"))


@pytest.mark.parametrize(
    "cc",
    [{"verdict": "ok"}, {"verdict": "maybe", "note": "x"}, {"verdict": "ok", "note": "  "}, "ok"],
)
def test_malformed_check_is_rejected(cc):
    with pytest.raises(AiContractError, match="contextCheck"):
        validate_context_check(_prob(context="ac_series_impedance", contextCheck=cc))


def test_failed_check_is_rejected_with_note():
    cc = {"verdict": "fail", "note": "A quantum phase factor has modulus 1, but 4i^2 - 9 = -13."}
    with pytest.raises(AiContractError, match="modulus 1"):
        validate_context_check(_prob(context="quantum_phase_factor", contextCheck=cc))


def test_passed_check_is_accepted():
    cc = {"verdict": "ok", "note": "Series impedances add: Z = Z1 + Z2 in ohms."}
    validate_context_check(_prob(context="ac_series_impedance", contextCheck=cc))
