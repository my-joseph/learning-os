"""Tests for bare English word detection in LaTeX (math_engine.latex_guard) and ingest/repo gates."""

from __future__ import annotations

import copy
import glob
import json

import pytest

from math_engine.ai_drill_ingest import AiContractError, check_ai_drill, validate_ai_problem_contract
from math_engine.latex_guard import find_bare_words, wrap_bare_words_in_latex
from math_engine.templates._prealg_helpers import S
from math_engine.verify import VerificationError, check_text_safety, verify_problem
from notion_sync.blocks import eq_block, eq_inline


@pytest.mark.parametrize(
    "tex",
    [
        "2x+3",
        r"\frac{a}{b}",
        r"\sin x",
        "mx + b",
        r"\text{if } x>0",
        "abc",
        "V = abc",
        "a^2 + b^2 + c^2 = 3abc",
        r"\triangle ABC",
        r"\text{Trapezoid } ABCD",
        r"\begin{aligned}x&=1\\y&=2\end{aligned}",
        r"x_{max}=8",
        r"(f o g)(x)=1/sqrt(sqrt(2x-2))",
        "3+sqrt(x)",
        r"\operatorname{Dom}(f^{-1})=\operatorname{Range}(f)",
        r"\mathrm{sgn}(x)",
        r"\textbf{Note: } x > 0",
        r"\text{set } \{1, 2\} \text{ has } x",
        r"2(L + W) = P,\quad LW = A_{\text{inner}}",
        "ac - bd",
        "mx, ny",
    ],
)
def test_false_positives_are_not_flagged(tex: str) -> None:
    assert find_bare_words(tex) == []
    assert wrap_bare_words_in_latex(tex) == tex


@pytest.mark.parametrize(
    ("tex", "expected_snippets"),
    [
        (
            "y = mx + b; exchange the variables and isolate the new output",
            ["exchange the variables and isolate the new output"],
        ),
        (
            "y=3x-8; solve for x, then exchange x and y",
            ["solve for", "then exchange", "and"],
        ),
        ("Domain(f)=[0,4]; Range(f)=[1,9)", ["Domain", "Range"]),
        ("f(k)=0 iff x-k is a factor", ["iff", "is a factor"]),
        (
            "For a real square root, the radicand must be nonnegative.",
            ["For a real square root, the radicand must be nonnegative"],
        ),
        ("is it", ["is it"]),
        ("to be", ["to be"]),
        ("degree(h)=7", ["degree"]),
        (r"p=\\frac{3}{2}", ["frac"]),
        (r"f(x)\\to-\\infty", ["infty"]),
    ],
)
def test_true_positives_are_flagged_and_wrapped_idempotently(tex: str, expected_snippets: list[str]) -> None:
    found = find_bare_words(tex)
    assert found == expected_snippets
    wrapped = wrap_bare_words_in_latex(tex)
    assert r"\text{" in wrapped
    assert find_bare_words(wrapped) == []
    assert wrap_bare_words_in_latex(wrapped) == wrapped


def test_wrap_preserves_spaces_around_wrapped_runs() -> None:
    assert (
        wrap_bare_words_in_latex("y=3x-8; solve for x, then exchange x and y")
        == r"y=3x-8;\text{ solve for }x,\text{ then exchange }x\text{ and }y"
    )
    assert wrap_bare_words_in_latex("f(k)=0 iff x-k is a factor") == r"f(k)=0\text{ iff }x-k\text{ is a factor}"


def _sample_valid_problem() -> dict:
    return {
        "id": "Q01",
        "verificationLevel": "partial",
        "review": {"verdict": "pass", "note": "Verified."},
        "templateKey": "c06-rate-base-part-triad",
        "archetypeKey": "c06-rate-base-part-triad",
        "level": 1,
        "givens": {"rate": 20, "base": 50},
        "prompt": r"Find $20\%$ of $50$.",
        "display": r"20\% \times 50 = ?",
        "plainText": "0.20 * 50 = ?",
        "answerSpec": {"type": "number", "value": "10"},
        "answerDisplay": "10",
        "answerPlain": "10",
        "inputHint": "Enter an integer.",
        "checkpointHint": "Convert the percentage to a decimal first.",
        "commonTrapTag": "c06-percent-decimal-conversion",
        "trapDerivation": "50 * 20",
        "verify": {"source": "10", "trapValue": "1000"},
        "steps": [S(r"50 \times 0.20 = 10", "Multiply base by rate.", val="10", eq=["50 * 0.20", "10"])],
    }


def test_gates_reject_bare_words_in_display_and_steps() -> None:
    with pytest.raises(VerificationError, match=r"\\text\{\.\.\.\}"):
        check_text_safety("Q01", "display", "solve for x", is_latex=True)

    prob_bad_display = _sample_valid_problem()
    prob_bad_display["display"] = "multiply rate by base"
    with pytest.raises(AiContractError, match=r"\\text\{\.\.\.\}"):
        validate_ai_problem_contract(copy.deepcopy(prob_bad_display))
    with pytest.raises(VerificationError, match=r"\\text\{\.\.\.\}"):
        verify_problem(copy.deepcopy(prob_bad_display))

    prob_bad_step = _sample_valid_problem()
    prob_bad_step["steps"][0]["latex"] = "answer is 10"
    with pytest.raises(AiContractError, match=r"\\text\{\.\.\.\}"):
        validate_ai_problem_contract(copy.deepcopy(prob_bad_step))
    with pytest.raises(VerificationError, match=r"\\text\{\.\.\.\}"):
        verify_problem(copy.deepcopy(prob_bad_step))

    errors = check_ai_drill({"unitCode": "MTH-T01-C06", "problems": [prob_bad_display]})
    assert any(r"\text{...}" in err for err in errors), errors


def test_notion_equation_blocks_wrap_bare_words() -> None:
    blk = eq_block("y = mx + b; exchange the variables")
    assert blk["equation"]["expression"] == r"y = mx + b;\text{ exchange the variables}"
    inl = eq_inline("Domain(f)")
    assert inl["equation"]["expression"] == r"\text{Domain}(f)"


DRILL_PATHS = sorted(glob.glob("drills/data/MTH-*/*.json") + glob.glob("drills/data/PHY-*/*.json"))


@pytest.mark.parametrize("path", DRILL_PATHS)
def test_all_math_and_physics_drills_have_no_bare_words_in_latex(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    offenders: list[str] = []
    for prob in doc.get("problems", []):
        pid = prob.get("id", "?")
        for field in ("display", "answerDisplay"):
            val = prob.get(field)
            if isinstance(val, str):
                bare = find_bare_words(val)
                if bare:
                    offenders.append(f"{pid}.{field}: {bare}")
        spec = prob.get("answerSpec") or {}
        if isinstance(spec.get("display"), str):
            bare = find_bare_words(spec["display"])
            if bare:
                offenders.append(f"{pid}.answerSpec.display: {bare}")
        for idx, st in enumerate(prob.get("steps") or [], 1):
            latex = st.get("latex")
            if isinstance(latex, str):
                bare = find_bare_words(latex)
                if bare:
                    offenders.append(f"{pid}.steps[{idx}].latex: {bare}")
        for idx, opt in enumerate(spec.get("options") or [], 1):
            for key in ("latex", "display"):
                val = opt.get(key)
                if isinstance(val, str):
                    bare = find_bare_words(val)
                    if bare:
                        offenders.append(f"{pid}.options[{idx}].{key}: {bare}")
    assert not offenders, f"{path} has bare English words in LaTeX: {offenders}"
