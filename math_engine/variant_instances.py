"""One bounded, exact family for parameter-only Similar variants."""

from __future__ import annotations

from math import gcd
from typing import Any

import sympy as sp

from math_engine.ai_drill_ingest import (
    L2_MIN_REAL_STEPS,
    AiContractError,
    count_real_steps,
    validate_blind_solve,
    validate_review,
)

PARAMETER_KEYS = ("a", "b", "d", "c")
FAMILY = "radical-equation-v1"
ARCHETYPE = "t02-c01-u03-radical-equations-extraneous"
TRAP = "t02-c01-u03-kept-extraneous-radical-root-trap"
# These fields come from ingestion or identify the parent. The actual problem
# (including the wording, hints, answer and complete derivation) must match.
PARENT_METADATA = {
    "id",
    "variantId",
    "sourceArchetype",
    "review",
    "blindSolve",
    "fingerprint",
    "qualityGates",
    "levelLabel",
    "verificationLevel",
    "references",
    "referenceBadges",
    "unitCode",
}


def _radical_problem(parameters: Any) -> tuple[dict[str, Any], tuple[bool, bool], tuple[int, ...]]:
    if not isinstance(parameters, dict) or set(parameters) != set(PARAMETER_KEYS):
        raise AiContractError("Expected integer parameters a, b, d, c.")
    if any(type(v) is not int for v in parameters.values()):
        raise AiContractError("Parameters must be integers.")
    a, b, d, c = (parameters[k] for k in PARAMETER_KEYS)
    if d == 0:
        raise AiContractError("The denominator is zero.")
    if d == 1:
        raise AiContractError("A unit denominator makes the clearing step trivial.")
    if not all(2 <= v <= 100 for v in (a, b, d, c)):
        raise AiContractError("The certified family uses parameters between 2 and 100.")

    x = sp.Symbol("x", real=True)
    radicand = (a * x + b) / d
    rhs = x + c
    squared = d * (rhs**2 - radicand)
    polynomial = sp.Poly(squared, x)
    linear, constant = 2 * d * c - a, d * c**2 - b
    if polynomial.all_coeffs() != [d, linear, constant]:
        raise AiContractError("The squared equation does not match the worked transformations.")
    discriminant = linear**2 - 4 * d * constant
    if discriminant == 0:
        raise AiContractError("The squared equation has a repeated candidate.")
    if not linear or not constant:
        raise AiContractError("A zero quadratic term collapses the solution steps.")
    if discriminant < 0 or not sp.sqrt(discriminant).is_Integer:
        raise AiContractError("The squared equation must have two distinct rational candidates.")

    lower = sp.Rational(-linear - sp.sqrt(discriminant), 2 * d)
    upper = sp.Rational(-linear + sp.sqrt(discriminant), 2 * d)
    if sp.solveset(polynomial.as_expr(), x, domain=sp.S.Reals) != sp.FiniteSet(lower, upper):
        raise AiContractError("The quadratic formula does not enumerate all candidates.")
    # The original equation implies the squared one. Check every candidate in
    # the original real domain to prove sufficiency and identify the rejected class.
    evaluations = [(radicand.subs(x, r), rhs.subs(x, r)) for r in (lower, upper)]
    if any(value < 0 for value, _ in evaluations):
        raise AiContractError("A candidate has an invalid radicand.")
    if [sp.sqrt(value) == right for value, right in evaluations] != [False, True] or not (
        evaluations[0][1] < 0 < evaluations[1][1]
    ):
        raise AiContractError("Candidate rejection changed: only the lower, negative-side candidate must fail.")
    if gcd(a, b, d) != 1 or discriminant == 1 or any(abs(r) <= 1 for r in (lower, upper)):
        raise AiContractError("A common factor, unit discriminant or small candidate makes a shortcut trivial.")

    equation = rf"\sqrt{{\frac{{{a}x+{b}}}{{{d}}}}}=x+{c}"
    lo, hi = sp.latex(lower), sp.latex(upper)
    numerator = f"{a}*x+{b}"
    expanded = f"x^2+{2 * c}*x+{c * c}"
    distributed = f"{d}*x^2+{2 * d * c}*x+{d * c * c}"
    root_formula = rf"\frac{{-({linear})\pm\sqrt{{({linear})^2-4\cdot {d}\cdot({constant})}}}}{{2\cdot {d}}}"
    steps = [
        {
            "latex": rf"\frac{{{a}x+{b}}}{{{d}}}=(x+{c})^2",
            "explain": "Square both sides to obtain candidate solutions.",
        },
        {
            "latex": rf"{a}x+{b}={d}(x+{c})^2",
            "explain": f"Multiply both sides by ${d}$.",
            "eq": [f"{d}*(({numerator})/{d})", numerator],
        },
        {
            "latex": rf"{a}x+{b}={d}(x^2+{2 * c}x+{c * c})",
            "explain": "Expand the squared binomial.",
            "eq": [f"(x+{c})^2", expanded],
        },
        {
            "latex": f"{a}x+{b}={d}x^2+{2 * d * c}x+{d * c * c}",
            "explain": f"Distribute ${d}$ across the trinomial.",
            "eq": [f"{d}*({expanded})", distributed],
        },
        {
            "latex": f"{d}x^2{linear:+}x{constant:+}=0",
            "explain": "Collect the terms on one side.",
            "eq": [f"{distributed}-({numerator})", f"{d}*x^2{linear:+}*x{constant:+}"],
        },
        {"latex": f"x={root_formula}", "explain": "Apply the quadratic formula to find both candidates."},
        {"latex": rf"x\in\{{{lo}, {hi}\}}", "explain": "Simplify the two values from the formula."},
    ]
    for root, (value, right), relation in zip((lo, hi), evaluations, (r"\ne", "="), strict=True):
        steps.append(
            {
                "latex": rf"\sqrt{{{sp.latex(value)}}}{relation}{sp.latex(right)}",
                "explain": f"Substitute ${root}$ into the original equation to check this candidate.",
            }
        )
    # Keep the original givens in the misconception derivation for the
    # provenance gates. This is the lower quadratic-formula root without filtering.
    b_formula, c_formula = f"2*{d}*{c}-{a}", f"{d}*{c}^2-{b}"
    trap = f"(-({b_formula})-sqrt(({b_formula})^2-4*{d}*({c_formula})))/(2*{d})"
    steps.append(
        {
            "latex": f"x={hi}",
            "explain": "Keep the candidate that satisfies the original equation.",
            "eq": [f"(-({linear})+sqrt(({linear})^2-4*{d}*({constant})))/(2*{d})", str(upper)],
        }
    )
    problem = {
        "archetypeKey": ARCHETYPE,
        "commonTrapTag": TRAP,
        "level": 3,
        "form": "direct",
        "prompt": f"Solve ${equation}$ over the reals. Enter the value of $x$.",
        "context": "",
        "display": equation,
        "plainText": f"sqrt(({a}*x+{b})/{d}) = x+{c}",
        "givens": parameters.copy(),
        "answerSpec": {"type": "number", "value": str(upper)},
        "answerPlain": str(upper),
        "answerDisplay": hi,
        "steps": steps,
        "trapDerivation": trap,
        "trapGivens": list(dict.fromkeys((a, b, d, c))),
        "verify": {"source": str(upper), "trapValue": str(lower)},
    }
    # Preserve each candidate's form and the signs of the displayed terms so
    # the derivation does not introduce a sign case or a different answer format.
    integer_candidates = (bool(lower.is_Integer), bool(upper.is_Integer))
    term_signs = tuple(int(sp.sign(v)) for v in (linear, constant, lower, upper))
    return problem, integer_candidates, term_signs


def render_radical_problem(parameters: dict[str, int]) -> dict[str, Any]:
    """Render a full-path parent draft for independent blind solve and review."""
    problem, _, _ = _radical_problem(parameters)
    return problem


def certify_instance(parent: dict[str, Any], parameters: Any) -> dict[str, Any]:
    """Regenerate the instance and certify its invariants against a reviewed parent."""
    if parent.get("context"):
        raise AiContractError("A story needs the independent context check and review.")
    if parent.get("archetypeKey") != ARCHETYPE:
        raise AiContractError("This archetype has no certified parameter family.")
    expected_parent, parent_candidate_types, parent_signs = _radical_problem(parent.get("givens"))
    parent_content = {k: v for k, v in parent.items() if k not in PARENT_METADATA}
    # Omission of an empty context is equivalent to explicitly writing it.
    parent_content.setdefault("context", "")
    if parent_content != expected_parent:
        raise AiContractError("The parent does not match the family's exact wording, structure and solution path.")
    validate_review(parent)
    validate_blind_solve(parent)
    blind = parent["blindSolve"]
    if blind["check"] != "edge" or blind["strategy"] != "prescribed" or blind["setup"] != "given":
        raise AiContractError("The parent's independent solve must identify the direct candidate check as the demand.")
    problem, candidate_types, signs = _radical_problem(parameters)
    if parameters == parent.get("givens"):
        raise AiContractError("Change at least one parameter.")
    if candidate_types != parent_candidate_types:
        raise AiContractError("The candidate type or canonical answer form changed.")
    if signs != parent_signs:
        raise AiContractError("The signs in the solution path changed.")
    steps = count_real_steps(problem)
    if steps < L2_MIN_REAL_STEPS or abs(steps - count_real_steps(parent)) > 1:
        raise AiContractError("The real-step count fell below the L2 floor or left the parent's ±1 range.")
    return problem
