"""Calculus Differentiation Templates (Task 5 Pilot & Task 4 Refinement).

Demonstrates scaling the math/code engine to higher-level mathematics:
- Power Rule (Level 1)
- Chain Rule (Level 2 Direct, Level 3 Diagnostic Flaw)

Features Dual Verification:
1. Analytical derivative via SymPy (sp.diff)
2. Numerical central difference at 5 random domain points
"""

from __future__ import annotations

import random
from typing import Any
import sympy as sp

from math_engine.templates.flaw_utils import build_flaw_choice_problem

UNIT = "MTH-CALC-DIFF"
TITLE = "Calculus: Differentiation Rules"
CHAPTER_CODE = "MTH-CALC-DIFF"
TOPIC_CODE = "MTH-CALC"

MISTAKE_TAGS = [
    {
        "id": "diff-forgot-decrement-power",
        "label": "Multiplied by exponent but forgot to decrease power by 1",
        "name": "Power Rule Forgot Exponent Decrement",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "diff-negative-power-increment",
        "label": "Incremented negative exponent instead of subtracting 1 (e.g. -2 to -1)",
        "name": "Negative Power Exponent Increment",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "diff-forgot-inner-derivative",
        "label": "Differentiated outer function but forgot to multiply by inside derivative",
        "name": "Chain Rule Omitted Inner Derivative",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "chain-rule-omission",
        "label": "Omitted inner derivative step in chain rule formulation",
        "name": "Chain Rule Formulation Omission",
        "autoFrom": [],
    },
    {
        "id": "diff-inner-derivative-error",
        "label": "Computed derivative of inner argument incorrectly",
        "name": "Inner Derivative Computation Error",
        "autoFrom": [],
    },
    {
        "id": "arithmetic-slip",
        "label": "Arithmetic / coefficient calculation slip",
        "name": "Arithmetic Slip",
        "autoFrom": ["rounding", "off_by_factor"],
    },
]


class VerificationError(Exception):
    pass


def _format_linear(a: int, b: int) -> tuple[str, str]:
    """Returns (latex, plain) for a*x + b formatted cleanly without '+ -'."""
    if b > 0:
        return f"{a}x + {b}", f"{a}*x + {b}"
    elif b < 0:
        return f"{a}x - {abs(b)}", f"{a}*x - {abs(b)}"
    else:
        return f"{a}x", f"{a}*x"


def _format_power(coeff: int, power: int) -> tuple[str, str]:
    """Returns (latex, plain) for coeff * x^power reduced (no ^1, ^0)."""
    if power == 0:
        return str(coeff), str(coeff)
    elif power == 1:
        return f"{coeff}x", f"{coeff}*x"
    else:
        return f"{coeff}x^{{{power}}}", f"{coeff}*x^{power}"


def _dual_verify(f_expr: sp.Expr, ans_expr: sp.Expr, x_sym: sp.Symbol, rng: random.Random) -> None:
    """Verifies derivative via both analytical SymPy diff and numerical central difference."""
    # 1. Analytical SymPy diff
    analytic = sp.diff(f_expr, x_sym)
    if sp.simplify(analytic - ans_expr) != 0:
        raise VerificationError(f"Symbolic diff mismatch: diff({f_expr}) = {analytic} != {ans_expr}")

    # 2. Numerical central difference at 5 random domain points in [1.5, 4.0]
    h = 1e-5
    for _ in range(5):
        pt = rng.uniform(1.5, 4.0)
        f_plus = float(f_expr.subs(x_sym, pt + h))
        f_minus = float(f_expr.subs(x_sym, pt - h))
        d_num = (f_plus - f_minus) / (2.0 * h)
        d_exact = float(ans_expr.subs(x_sym, pt))
        rel_diff = abs(d_num - d_exact) / max(1.0, abs(d_exact))
        if rel_diff > 1e-3:
            raise VerificationError(
                f"Numerical central difference mismatch at x={pt:.4f}: num={d_num:.6f}, exact={d_exact:.6f}, rel={rel_diff:.6f}"
            )


def _step(explain: str, latex: str, val: str | None = None) -> dict[str, Any]:
    st = {"explain": explain, "latex": latex}
    if val is not None:
        st["val"] = val
    return st


# ---------------------------------------------------------------------------
# Template 1: diff-power-rule (Level 1)
# ---------------------------------------------------------------------------
def t_diff_power(rng: random.Random, form: str | None = None) -> dict[str, Any]:
    x = sp.Symbol("x")
    available_forms = ["direct-polynomial", "rewrite-negative-or-radical"]
    if form not in available_forms:
        form = rng.choice(available_forms)

    if form == "direct-polynomial":
        a = rng.randint(2, 6)
        n = rng.randint(2, 5)
        # f(x) = a*x^n
        f_expr = a * (x**n)
        ans_expr = (a * n) * (x ** (n - 1))
        _dual_verify(f_expr, ans_expr, x, rng)

        display_f = f"{a}x^{{{n}}}"
        ans_latex, ans_str = _format_power(a * n, n - 1)
        trap_latex, trap_str = _format_power(a * n, n)  # forgot to decrement power: a*n*x^n

        step2_val = f"{n}x" if n - 1 == 1 else f"{n}x^{{{n - 1}}}"
        steps = [
            _step("Apply the power rule $\\frac{d}{dx}[x^n] = n x^{n-1}$.", f"\\frac{{d}}{{dx}}[{display_f}] = {a} \\cdot \\frac{{d}}{{dx}}[x^{{{n}}}]", f"{a}*{n}*x**({n}-1)"),
            _step(f"Bring down the exponent ${n}$ and multiply by coefficient ${a}$.", f"= {a} \\cdot ({step2_val})", ans_str),
            _step("Simplify to obtain the final derivative.", f"= {ans_latex}", ans_str),
        ]

        return {
            "category": "Differentiation",
            "form": form,
            "skill": "CAL-DIFF-POWER",
            "level": 1,
            "verificationLevel": "machine-verified",
            "prompt": f"Find the derivative of $f(x) = {display_f}$ with respect to $x$.",
            "display": f"\\frac{{d}}{{dx}}\\left({display_f}\\right)",
            "plainText": f"d/dx ({a}*x^{n})",
            "answerSpec": {"type": "expression", "value": ans_str, "variables": ["x"]},
            "answerDisplay": ans_latex,
            "answerPlain": ans_str,
            "inputHint": "Enter derivative in terms of x (e.g. 7*x^6 or 42*x^5)",
            "checkpointHint": "Multiply coefficient by power, then decrease exponent by 1.",
            "commonTrapTag": "diff-forgot-decrement-power",
            "steps": steps,
            "verify": {
                "source": f"diff({a}*x**{n}, x)",
                "trapValue": trap_str,
            },
        }

    else:
        # rewrite-negative-or-radical: f(x) = a / x^n = a * x^(-n)
        a = rng.randint(2, 5)
        n = rng.randint(1, 3)
        f_expr = a * (x ** (-n))
        ans_expr = (-a * n) * (x ** (-n - 1))
        _dual_verify(f_expr, ans_expr, x, rng)

        display_f = f"\\frac{{{a}}}{{x^{{{n}}}}}" if n > 1 else f"\\frac{{{a}}}{{x}}"
        plain_f = f"{a}/x^{n}" if n > 1 else f"{a}/x"
        ans_latex = f"-\\frac{{{a * n}}}{{x^{{{n + 1}}}}}"
        ans_str = f"{-a * n}*x**{-n - 1}"
        
        # Increment negative exponent trap: e.g. -n + 1 instead of -n - 1
        # For n=1, -1 + 1 = 0 -> -a
        # For n > 1, -n + 1 -> -a*n * x**(-n + 1)
        if n == 1:
            trap_str = str(-a * n)
        else:
            trap_str = f"{-a * n}*x**{-n + 1}"

        inner_p = "-x" if -n == -1 else f"{-n}x"
        steps = [
            _step(f"Rewrite the reciprocal expression using negative exponents: ${display_f} = {a}x^{{-{n}}}$.", f"f(x) = {a}x^{{-{n}}}", None),
            _step(f"Apply power rule: multiply by ${-n}$ and subtract 1 from exponent: ${-n} - 1 = {-n - 1}$.", f"f'(x) = {a} \\cdot ({inner_p}^{{{-n - 1}}})", ans_str),
            _step("Express with positive exponents.", f"f'(x) = {ans_latex}", ans_str),
        ]

        return {
            "category": "Differentiation",
            "form": form,
            "skill": "CAL-DIFF-POWER",
            "level": 1,
            "verificationLevel": "machine-verified",
            "prompt": f"Find the derivative of $f(x) = {display_f}$ with respect to $x$.",
            "display": f"\\frac{{d}}{{dx}}\\left({display_f}\\right)",
            "plainText": f"d/dx ({plain_f})",
            "answerSpec": {"type": "expression", "value": ans_str, "variables": ["x"]},
            "answerDisplay": ans_latex,
            "answerPlain": ans_str,
            "inputHint": "Enter derivative in terms of x (e.g. -99*x^-8 or -99/x^8)",
            "checkpointHint": "Rewrite 1/x^n as x^(-n) before applying the power rule; remember -n - 1.",
            "commonTrapTag": "diff-negative-power-increment",
            "steps": steps,
            "verify": {
                "source": f"diff({a}*x**(-{n}), x)",
                "trapValue": trap_str,
            },
        }


# ---------------------------------------------------------------------------
# Template 2: diff-chain-rule (Level 2 Direct, Level 3 Diagnostic Flaw)
# ---------------------------------------------------------------------------
def t_diff_chain(rng: random.Random, form: str | None = None) -> dict[str, Any]:
    x = sp.Symbol("x")
    available_forms = ["direct-power", "composite-transcendental", "flaw-line-1", "flaw-line-2", "flaw-line-3"]
    if form not in available_forms:
        form = rng.choice(available_forms)

    if form == "direct-power":
        a = rng.randint(2, 4)
        b = rng.choice([-3, -2, -1, 1, 2, 3])
        n = rng.randint(3, 5)
        # f(x) = (a*x + b)^n
        inner = a * x + b
        f_expr = inner**n
        ans_expr = (n * a) * (inner ** (n - 1))
        _dual_verify(f_expr, ans_expr, x, rng)

        inner_tex, inner_plain = _format_linear(a, b)
        display_f = f"({inner_tex})^{{{n}}}"
        
        pow_p = n - 1
        if pow_p == 1:
            ans_latex = f"{n * a}({inner_tex})"
            ans_str = f"{n * a}*({inner_plain})"
            trap_str = f"{n}*({inner_plain})"  # forgot inner derivative a
            outer_step_tex = f"{n}({inner_tex})"
        else:
            ans_latex = f"{n * a}({inner_tex})^{{{pow_p}}}"
            ans_str = f"{n * a}*({inner_plain})**{pow_p}"
            trap_str = f"{n}*({inner_plain})**{pow_p}"  # forgot inner derivative a
            outer_step_tex = f"{n}({inner_tex})^{{{pow_p}}}"

        steps = [
            _step(f"Identify inner function $u = {inner_tex}$ and outer function $f(u) = u^{{{n}}}$.", f"u = {inner_tex},\\quad f(u) = u^{{{n}}}", None),
            _step(f"Compute derivative of outer function with respect to $u$: $\\frac{{df}}{{du}} = n u^{{n-1}}$.", f"\\frac{{df}}{{du}} = {outer_step_tex}", None),
            _step(f"Compute derivative of inner function: $\\frac{{du}}{{dx}} = \\frac{{d}}{{dx}}[{inner_tex}] = {a}$.", f"\\frac{{du}}{{dx}} = {a}", None),
            _step("Apply chain rule: $\\frac{df}{dx} = \\frac{df}{du} \\cdot \\frac{du}{dx}$.", f"\\frac{{df}}{{dx}} = {outer_step_tex} \\cdot {a}", ans_str),
            _step("Multiply constants to obtain final derivative.", f"f'(x) = {ans_latex}", ans_str),
        ]

        return {
            "category": "Differentiation",
            "form": form,
            "skill": "CAL-DIFF-CHAIN",
            "level": 2,
            "verificationLevel": "machine-verified",
            "prompt": f"Find the derivative of $f(x) = {display_f}$ with respect to $x$ using the chain rule.",
            "display": f"\\frac{{d}}{{dx}}\\left({display_f}\\right)",
            "plainText": f"d/dx (({inner_plain})^{n})",
            "answerSpec": {"type": "expression", "value": ans_str, "variables": ["x"]},
            "answerDisplay": ans_latex,
            "answerPlain": ans_str,
            "inputHint": "Enter expression in terms of x (e.g. 42*(6*x - 5)^7)",
            "checkpointHint": "Don't forget to multiply by the derivative of the inside function.",
            "commonTrapTag": "diff-forgot-inner-derivative",
            "steps": steps,
            "verify": {
                "source": f"diff(({inner_plain})**{n}, x)",
                "trapValue": trap_str,
            },
        }

    elif form == "composite-transcendental":
        a = rng.randint(2, 5)
        b = rng.choice([-3, -2, -1, 1, 2, 3])
        is_sin = rng.choice([True, False])

        inner_tex, inner_plain = _format_linear(a, b)
        if is_sin:
            f_expr = sp.sin(a * x + b)
            ans_expr = a * sp.cos(a * x + b)
            _dual_verify(f_expr, ans_expr, x, rng)
            display_f = f"\\sin({inner_tex})"
            ans_latex = f"{a}\\cos({inner_tex})"
            ans_str = f"{a}*cos({inner_plain})"
            trap_str = f"cos({inner_plain})"  # forgot inner derivative factor of a

            steps = [
                _step(f"Identify outer function $\\sin(u)$ with inner function $u = {inner_tex}$.", f"u = {inner_tex}", None),
                _step(f"Differentiate outer function: $\\frac{{d}}{{du}}[\\sin(u)] = \\cos(u)$.", f"\\frac{{df}}{{du}} = \\cos({inner_tex})", None),
                _step(f"Differentiate inner function: $\\frac{{du}}{{dx}} = \\frac{{d}}{{dx}}[{inner_tex}] = {a}$.", f"\\frac{{du}}{{dx}} = {a}", None),
                _step("Multiply by chain rule: $\\frac{df}{dx} = \\frac{df}{du} \\cdot \\frac{du}{dx}$.", f"f'(x) = \\cos({inner_tex}) \\cdot {a} = {ans_latex}", ans_str),
            ]
        else:
            f_expr = sp.exp(a * x + b)
            ans_expr = a * sp.exp(a * x + b)
            _dual_verify(f_expr, ans_expr, x, rng)
            display_f = f"e^{{{inner_tex}}}"
            ans_latex = f"{a}e^{{{inner_tex}}}"
            ans_str = f"{a}*exp({inner_plain})"
            trap_str = f"exp({inner_plain})"  # forgot inner derivative factor of a

            steps = [
                _step(f"Identify outer function $e^u$ with inner function $u = {inner_tex}$.", f"u = {inner_tex}", None),
                _step(f"Differentiate outer function: $\\frac{{d}}{{du}}[e^u] = e^u$.", f"\\frac{{df}}{{du}} = e^{{{inner_tex}}}", None),
                _step(f"Differentiate inner function: $\\frac{{du}}{{dx}} = \\frac{{d}}{{dx}}[{inner_tex}] = {a}$.", f"\\frac{{du}}{{dx}} = {a}", None),
                _step("Multiply by chain rule: $\\frac{df}{dx} = \\frac{df}{du} \\cdot \\frac{du}{dx}$.", f"f'(x) = e^{{{inner_tex}}} \\cdot {a} = {ans_latex}", ans_str),
            ]

        return {
            "category": "Differentiation",
            "form": form,
            "skill": "CAL-DIFF-CHAIN",
            "level": 2,
            "verificationLevel": "machine-verified",
            "prompt": f"Find the derivative of $f(x) = {display_f}$ with respect to $x$ using the chain rule.",
            "display": f"\\frac{{d}}{{dx}}\\left({display_f}\\right)",
            "plainText": f"d/dx ({display_f})",
            "answerSpec": {"type": "expression", "value": ans_str, "variables": ["x"]},
            "answerDisplay": ans_latex,
            "answerPlain": ans_str,
            "inputHint": "Enter expression in terms of x (e.g. 7*cos(7*x + 5) or 9*exp(9*x - 4))",
            "checkpointHint": "Remember to multiply by the derivative of the inner argument.",
            "commonTrapTag": "diff-forgot-inner-derivative",
            "steps": steps,
            "verify": {
                "source": f"diff({f_expr}, x)",
                "trapValue": trap_str,
            },
        }

    else:
        # find-the-flaw: Diagnostic L3 problem
        a = rng.randint(2, 4)
        n = rng.randint(3, 4)
        inner_tex = f"{a}x + 1"
        correct_l1 = f"f'(x) = \\frac{{d}}{{du}}[u^{{{n}}}] \\cdot \\frac{{d}}{{dx}}[{inner_tex}]"
        correct_l2 = f"= {n}({inner_tex})^{{{n - 1}}} \\cdot {a}"
        correct_l3 = f"= {n * a}({inner_tex})^{{{n - 1}}}"

        if form == "flaw-line-1":
            flaw_line = 1
        elif form == "flaw-line-2":
            flaw_line = 2
        elif form == "flaw-line-3":
            flaw_line = 3
        else:
            flaw_line = rng.choice([1, 2, 3])

        if flaw_line == 1:
            shown_l1 = f"f'(x) = \\frac{{d}}{{du}}[u^{{{n}}}]"  # omitted inner derivative in formulation
            shown_lines = [shown_l1, f"= {n}({inner_tex})^{{{n - 1}}}", f"= {n}({inner_tex})^{{{n - 1}}}"]
            vals = [f"{n}*({a}*x + 1)**{n - 1}", None, None]
            why = f"Line 1 is wrong: The student wrote ${shown_lines[0]}$, omitting the inner derivative factor $\\frac{{d}}{{dx}}[{inner_tex}]$. True formulation: ${correct_l1}$."
        elif flaw_line == 2:
            shown_lines = [correct_l1, f"= {n}({inner_tex})^{{{n - 1}}} \\cdot 1", f"= {n}({inner_tex})^{{{n - 1}}}"]
            vals = [None, f"{n}*({a}*x + 1)**{n-1} * 1", None]
            why = f"Line 2 is wrong: The student wrote ${shown_lines[1]}$, but $\\frac{{d}}{{dx}}[{inner_tex}] = {a}$ (differentiated as $1$). True evaluation: ${correct_l2}$."
        else:
            wrong_mult = n + a
            shown_lines = [correct_l1, correct_l2, f"= {wrong_mult}({inner_tex})^{{{n - 1}}}"]
            vals = [None, f"{n}*({a}*x + 1)**{n - 1} * {a}", f"{wrong_mult}*({a}*x + 1)**{n - 1}"]
            why = f"Line 3 is wrong: The student wrote ${shown_lines[2]}$, but ${n} \\cdot {a} = {n * a}$ (added instead of multiplied). True derivative: ${correct_l3}$."

        steps = [
            _step(why if flaw_line == 1 else f"Step 1 (True formulation): ${correct_l1}$.", correct_l1),
            _step(why if flaw_line == 2 else f"Step 2 (True evaluation): ${correct_l2}$.", correct_l2, f"{n}*({a}*x + 1)**{n - 1} * {a}"),
            _step(why if flaw_line == 3 else f"Step 3 (True derivative): ${correct_l3}$.", correct_l3, f"{n * a}*({a}*x + 1)**{n - 1}"),
        ]

        line_trap_map = {1: "chain-rule-omission", 2: "diff-inner-derivative-error", 3: "arithmetic-slip"}

        prob = build_flaw_choice_problem(
            prompt="A student differentiated $f(x) = (" + inner_tex + ")^" + str(n) + "$ as shown below. Which line contains the FIRST error?",
            shown_lines=shown_lines,
            steps=steps,
            flaw_line=flaw_line,
            line_trap_map=line_trap_map,
            verify_source=f"diff(({a}*x + 1)**{n}, x)",
            vals=vals,
            form_prefix="flaw-line",
            category="Diagnostic & Trap",
            checkpoint_hint="Differentiate the composite function step-by-step on scratch paper, then compare your derivation line by line with the student's solution to pinpoint the first incorrect step.",
            common_trap_tag="diff-forgot-inner-derivative",
            flaw_tag=line_trap_map[flaw_line],
            variables=["x"],
        )
        prob["skill"] = "CAL-DIFF-CHAIN"
        prob["level"] = 3
        prob["verificationLevel"] = "machine-verified"
        return prob


TEMPLATES = [
    {
        "key": "diff-power-rule",
        "level": 1,
        "skill": "CAL-DIFF-POWER",
        "verificationLevel": "machine-verified",
        "forms": {
            "direct-polynomial": {"level": 1, "skill": "CAL-DIFF-POWER", "trapTag": "diff-forgot-decrement-power"},
            "rewrite-negative-or-radical": {"level": 1, "skill": "CAL-DIFF-POWER", "trapTag": "diff-negative-power-increment"},
        },
        "build": t_diff_power,
    },
    {
        "key": "diff-chain-rule",
        "level": 2,
        "skill": "CAL-DIFF-CHAIN",
        "verificationLevel": "machine-verified",
        "forms": {
            "direct-power": {"level": 2, "skill": "CAL-DIFF-CHAIN", "trapTag": "diff-forgot-inner-derivative"},
            "composite-transcendental": {"level": 2, "skill": "CAL-DIFF-CHAIN", "trapTag": "diff-forgot-inner-derivative"},
            "flaw-line-1": {"level": 3, "skill": "CAL-DIFF-CHAIN", "trapTag": "diff-forgot-inner-derivative"},
            "flaw-line-2": {"level": 3, "skill": "CAL-DIFF-CHAIN", "trapTag": "diff-forgot-inner-derivative"},
            "flaw-line-3": {"level": 3, "skill": "CAL-DIFF-CHAIN", "trapTag": "diff-forgot-inner-derivative"},
        },
        "build": t_diff_chain,
    },
]
