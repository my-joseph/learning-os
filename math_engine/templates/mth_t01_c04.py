# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C04: Fractions."""

import math
from fractions import Fraction

from math_engine.templates._prealg_helpers import S, format_frac_latex

UNIT = "MTH-T01-C04"
TITLE = "Fractions"

MISTAKE_TAGS = [
    {
        "id": "c04-reciprocal-omission",
        "label": "Multiplied directly by divisor fraction without inverting reciprocal",
        "name": "Fraction Division Reciprocal Omission",
        "autoFrom": ["reciprocal"],
    },
    {
        "id": "c04-unlike-denominator-direct-add",
        "label": "Added numerators and denominators directly without common denominator",
        "name": "Unlike Denominator Direct Addition Trap",
        "autoFrom": [],
    },
    {
        "id": "c04-complex-fraction-inversion-trap",
        "label": "Multiplied numerator by denominator in a complex fraction instead of dividing",
        "name": "Complex Fraction Inversion Trap",
        "autoFrom": ["reciprocal"],
    },
    {
        "id": "c04-remainder-fraction-base-trap",
        "label": "Subtracted sequential fractions from original whole instead of remaining fraction",
        "name": "Sequential Fractional Remainder Trap",
        "autoFrom": [],
    },
]


def _fstr(fr: Fraction) -> str:
    return f"{fr.numerator}/{fr.denominator}" if fr.denominator != 1 else str(fr.numerator)


def t_c04_foundation(rng, form=None):
    if form not in ("direct", "reciprocal"):
        form = rng.choice(["direct", "reciprocal"])
    pairs = [
        (Fraction(3, 4), Fraction(8, 9)),
        (Fraction(5, 6), Fraction(9, 10)),
        (Fraction(2, 5), Fraction(15, 16)),
        (Fraction(4, 7), Fraction(14, 15)),
        (Fraction(5, 8), Fraction(12, 25)),
        (Fraction(7, 9), Fraction(18, 35)),
    ]
    f1, f2 = rng.choice(pairs)
    if form == "reciprocal":
        ans_f = f1 / f2
        trap_f = f1 * f2
        ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
        prompt = f"Divide the fractions and express the result in lowest terms: $\\frac{{{f1.numerator}}}{{{f1.denominator}}} \\div \\frac{{{f2.numerator}}}{{{f2.denominator}}}$."
        disp = f"\\frac{{{f1.numerator}}}{{{f1.denominator}}} \\div \\frac{{{f2.numerator}}}{{{f2.denominator}}}"
        steps = [
            S(
                f"\\frac{{{f1.numerator}}}{{{f1.denominator}}} \\div \\frac{{{f2.numerator}}}{{{f2.denominator}}} = \\frac{{{f1.numerator}}}{{{f1.denominator}}} \\times \\frac{{{f2.denominator}}}{{{f2.numerator}}}",
                "Multiply by the reciprocal of the divisor fraction.",
                eq=[f"({f1}) / ({f2})", ans_s],
            ),
            S(
                f"= \\frac{{{f1.numerator * f2.denominator}}}{{{f1.denominator * f2.numerator}}}",
                "Multiply the numerators and multiply the denominators.",
                eq=[f"({f1.numerator * f2.denominator}) / ({f1.denominator * f2.numerator})", ans_s],
            ),
            S(
                f"= {format_frac_latex(ans_s)}",
                "Reduce by dividing numerator and denominator by their greatest common factor.",
                val=ans_s,
                eq=[ans_s, ans_s],
            ),
        ]
    else:
        ans_f = f1 * f2
        trap_f = f1 / f2
        ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
        prompt = f"Multiply the fractions and simplify to lowest terms: $\\frac{{{f1.numerator}}}{{{f1.denominator}}} \\times \\frac{{{f2.numerator}}}{{{f2.denominator}}}$."
        disp = f"\\frac{{{f1.numerator}}}{{{f1.denominator}}} \\times \\frac{{{f2.numerator}}}{{{f2.denominator}}}"
        steps = [
            S(
                f"\\frac{{{f1.numerator} \\times {f2.numerator}}}{{{f1.denominator} \\times {f2.denominator}}} = \\frac{{{f1.numerator * f2.numerator}}}{{{f1.denominator * f2.denominator}}}",
                "Multiply the numerators together and the denominators together.",
                eq=[f"({f1}) * ({f2})", ans_s],
            ),
            S(
                f"= {format_frac_latex(ans_s)}",
                "Cancel common factors between numerator and denominator.",
                eq=[ans_s, ans_s],
            ),
            S(
                f"\\text{{Simplified}} = {format_frac_latex(ans_s)}",
                "Confirm the fraction is in lowest terms.",
                val=ans_s,
                eq=[ans_s, ans_s],
            ),
        ]
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Fractions: Multiplication and Division",
        "references": ["MTH-T01-C04-U02"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"({f1}) op ({f2})",
        "answerSpec": {"type": "number", "value": ans_s},
        "answerDisplay": format_frac_latex(ans_s),
        "answerPlain": ans_s,
        "inputHint": "Enter the exact integer or reduced fraction p/q",
        "checkpointHint": "For fraction division, invert the second fraction and multiply, then cancel common factors.",
        "commonTrapTag": "c04-reciprocal-omission",
        "verify": {"source": ans_s, "trapValue": trap_s},
        "steps": steps,
    }


def t_c04_reverse(rng, form=None):
    if form not in ("direct", "missing-term"):
        form = rng.choice(["direct", "missing-term"])
    cases = [
        (Fraction(2, 3), Fraction(3, 4), 12),
        (Fraction(3, 5), Fraction(1, 2), 10),
        (Fraction(5, 6), Fraction(3, 8), 24),
        (Fraction(4, 9), Fraction(5, 6), 18),
        (Fraction(7, 10), Fraction(2, 15), 30),
        (Fraction(3, 7), Fraction(5, 14), 14),
    ]
    f1, f2, lcd = rng.choice(cases)
    total = f1 + f2
    if form == "missing-term":
        ans_f = f2
        trap_f = Fraction(abs(total.numerator - f1.numerator), max(1, abs(total.denominator - f1.denominator)))
        if trap_f == ans_f:
            trap_f = total + f1
        ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
        prompt = f"Solve for the fraction $x$ in lowest terms: $x + \\frac{{{f1.numerator}}}{{{f1.denominator}}} = \\frac{{{total.numerator}}}{{{total.denominator}}}$."
        disp = f"x + \\frac{{{f1.numerator}}}{{{f1.denominator}}} = \\frac{{{total.numerator}}}{{{total.denominator}}}"
        steps = [
            S(
                f"x = \\frac{{{total.numerator}}}{{{total.denominator}}} - \\frac{{{f1.numerator}}}{{{f1.denominator}}}",
                "Subtract the known fraction from both sides.",
                eq=[f"({total}) - ({f1})", ans_s],
            ),
            S(
                f"x = \\frac{{{total.numerator * (lcd // total.denominator)} - {f1.numerator * (lcd // f1.denominator)}}}{{{lcd}}}",
                f"Rewrite both fractions over the least common denominator ${lcd}$.",
                eq=[ans_s, ans_s],
            ),
            S(
                f"x = {format_frac_latex(ans_s)}",
                "Subtract the numerators and reduce to lowest terms.",
                val=ans_s,
                eq=[ans_s, ans_s],
            ),
        ]
    else:
        ans_f = total
        trap_f = Fraction(f1.numerator + f2.numerator, f1.denominator + f2.denominator)
        ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
        prompt = f"Add the fractions with unlike denominators and express in lowest terms: $\\frac{{{f1.numerator}}}{{{f1.denominator}}} + \\frac{{{f2.numerator}}}{{{f2.denominator}}}$."
        disp = f"\\frac{{{f1.numerator}}}{{{f1.denominator}}} + \\frac{{{f2.numerator}}}{{{f2.denominator}}}"
        steps = [
            S(
                f"\\text{{LCD}}({f1.denominator}, {f2.denominator}) = {lcd}",
                "Find the least common denominator of the two fractions.",
                eq=[str(lcd), str(lcd)],
            ),
            S(
                f"= \\frac{{{f1.numerator * (lcd // f1.denominator)}}}{{{lcd}}} + \\frac{{{f2.numerator * (lcd // f2.denominator)}}}{{{lcd}}}",
                "Convert each fraction to an equivalent fraction with the common denominator.",
                eq=[f"({f1}) + ({f2})", ans_s],
            ),
            S(f"= {format_frac_latex(ans_s)}", "Add the numerators and simplify.", val=ans_s, eq=[ans_s, ans_s]),
        ]
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Fractions: Unlike Denominators & Missing Addend",
        "references": ["MTH-T01-C04-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"({f1}) + ({f2}) lcd {lcd}",
        "answerSpec": {"type": "number", "value": ans_s},
        "answerDisplay": format_frac_latex(ans_s),
        "answerPlain": ans_s,
        "inputHint": "Enter the exact integer or reduced fraction p/q",
        "checkpointHint": "Convert both fractions to equivalent fractions sharing their least common denominator before adding or subtracting numerators.",
        "commonTrapTag": "c04-unlike-denominator-direct-add",
        "verify": {"source": ans_s, "trapValue": trap_s},
        "steps": steps,
    }


def t_c04_trap(rng, form=None):
    if form not in ("direct", "difference"):
        form = rng.choice(["direct", "difference"])
    cases = [
        (Fraction(1, 2), Fraction(1, 3), Fraction(5, 12)),
        (Fraction(2, 3), Fraction(1, 4), Fraction(11, 24)),
        (Fraction(3, 4), Fraction(1, 6), Fraction(11, 18)),
        (Fraction(3, 5), Fraction(1, 2), Fraction(11, 20)),
        (Fraction(5, 6), Fraction(1, 3), Fraction(1, 4)),
    ]
    a, b, c = rng.choice(cases)
    if form == "difference":
        num_f = a - b
        ans_f = num_f / c
        trap_f = num_f * c
        ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
        prompt = f"Simplify the complex fraction to lowest terms: $\\dfrac{{\\frac{{{a.numerator}}}{{{a.denominator}}} - \\frac{{{b.numerator}}}{{{b.denominator}}}}}{{\\frac{{{c.numerator}}}{{{c.denominator}}}}}$."
        disp = f"\\frac{{\\frac{{{a.numerator}}}{{{a.denominator}}} - \\frac{{{b.numerator}}}{{{b.denominator}}}}}{{\\frac{{{c.numerator}}}{{{c.denominator}}}}}"
        steps = [
            S(
                f"\\text{{Numerator}} = \\frac{{{a.numerator}}}{{{a.denominator}}} - \\frac{{{b.numerator}}}{{{b.denominator}}} = {format_frac_latex(_fstr(num_f))}",
                "Combine the fractions in the numerator first.",
                eq=[f"({a}) - ({b})", _fstr(num_f)],
            ),
            S(
                f"{format_frac_latex(_fstr(num_f))} \\div \\frac{{{c.numerator}}}{{{c.denominator}}} = {format_frac_latex(_fstr(num_f))} \\times \\frac{{{c.denominator}}}{{{c.numerator}}}",
                "Rewrite the main fraction bar as division and multiply by the reciprocal of the denominator.",
                eq=[f"({_fstr(num_f)}) / ({c})", ans_s],
            ),
            S(f"= {format_frac_latex(ans_s)}", "Simplify the product to lowest terms.", val=ans_s, eq=[ans_s, ans_s]),
        ]
    else:
        num_f = a + b
        ans_f = num_f / c
        trap_f = num_f * c
        ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
        prompt = f"Simplify the complex fraction to lowest terms: $\\dfrac{{\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}}}}{{\\frac{{{c.numerator}}}{{{c.denominator}}}}}$."
        disp = f"\\frac{{\\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}}}}{{\\frac{{{c.numerator}}}{{{c.denominator}}}}}"
        steps = [
            S(
                f"\\text{{Numerator}} = \\frac{{{a.numerator}}}{{{a.denominator}}} + \\frac{{{b.numerator}}}{{{b.denominator}}} = {format_frac_latex(_fstr(num_f))}",
                "Add the fractions in the numerator over their common denominator.",
                eq=[f"({a}) + ({b})", _fstr(num_f)],
            ),
            S(
                f"{format_frac_latex(_fstr(num_f))} \\div \\frac{{{c.numerator}}}{{{c.denominator}}} = {format_frac_latex(_fstr(num_f))} \\times \\frac{{{c.denominator}}}{{{c.numerator}}}",
                "Invert the denominator fraction and multiply.",
                eq=[f"({_fstr(num_f)}) / ({c})", ans_s],
            ),
            S(
                f"= {format_frac_latex(ans_s)}",
                "Cancel common factors to obtain lowest terms.",
                val=ans_s,
                eq=[ans_s, ans_s],
            ),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Fractions: Complex Fraction Reciprocal Trap",
        "references": ["MTH-T01-C04-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"(({a}) and ({b})) / ({c})",
        "answerSpec": {"type": "number", "value": ans_s},
        "answerDisplay": format_frac_latex(ans_s),
        "answerPlain": ans_s,
        "inputHint": "Enter the exact integer or reduced fraction p/q",
        "checkpointHint": "Simplify the numerator into a single fraction first, then multiply by the reciprocal of the denominator fraction.",
        "commonTrapTag": "c04-complex-fraction-inversion-trap",
        "verify": {"source": ans_s, "trapValue": trap_s},
        "steps": steps,
    }


def t_c04_synthesis(rng, form=None):
    if form not in ("direct", "contextual"):
        form = rng.choice(["direct", "contextual"])
    cases = [
        (Fraction(1, 3), Fraction(1, 4), 120),
        (Fraction(1, 4), Fraction(1, 3), 180),
        (Fraction(2, 5), Fraction(1, 3), 150),
        (Fraction(1, 3), Fraction(2, 5), 240),
        (Fraction(1, 5), Fraction(1, 4), 200),
    ]
    f1, f2, total = rng.choice(cases)
    rem1 = Fraction(1, 1) - f1
    rem2 = rem1 * (Fraction(1, 1) - f2)
    final_left = int(total * rem2)
    naive_left_frac = Fraction(1, 1) - f1 - f2
    if form == "contextual":
        ans = total
        trap = (
            int(final_left / naive_left_frac)
            if naive_left_frac > 0 and (final_left / naive_left_frac).denominator == 1
            else total + 30
        )
        prompt = f"An engineering grant spends $\\frac{{{f1.numerator}}}{{{f1.denominator}}}$ of its total budget on hardware, and then spends $\\frac{{{f2.numerator}}}{{{f2.denominator}}}$ of the REMAINING budget on cloud compute. If ${final_left}$ thousand dollars remains unspent, what was the initial total budget (in thousands of dollars)?"
        disp = f"B \\cdot \\left(1 - \\frac{{{f1.numerator}}}{{{f1.denominator}}}\\right)\\left(1 - \\frac{{{f2.numerator}}}{{{f2.denominator}}}\\right) = {final_left}"
        steps = [
            S(
                f"\\text{{Remaining fraction after hardware}} = 1 - \\frac{{{f1.numerator}}}{{{f1.denominator}}} = {format_frac_latex(_fstr(rem1))}",
                "Find the fraction of the budget left after the first allocation.",
                eq=[f"1 - ({f1})", _fstr(rem1)],
            ),
            S(
                f"\\text{{Final remaining fraction}} = {format_frac_latex(_fstr(rem1))} \\times \\left(1 - \\frac{{{f2.numerator}}}{{{f2.denominator}}}\\right) = {format_frac_latex(_fstr(rem2))}",
                "Multiply by the fraction remaining after the second allocation.",
                eq=[f"({rem1}) * (1 - ({f2}))", _fstr(rem2)],
            ),
            S(
                f"B = {final_left} \\div {format_frac_latex(_fstr(rem2))} = {total}",
                "Divide the final dollar amount by the final remaining fraction.",
                val=str(ans),
                eq=[f"{final_left} / ({rem2})", str(ans)],
            ),
        ]
    else:
        ans = final_left
        trap = int(total * naive_left_frac)
        prompt = f"A reservoir holds ${total}$ megaliters of water. During Month 1, $\\frac{{{f1.numerator}}}{{{f1.denominator}}}$ of the water is released. During Month 2, $\\frac{{{f2.numerator}}}{{{f2.denominator}}}$ of the REMAINING water is released. How many megaliters of water remain in the reservoir at the end of Month 2?"
        disp = f"{total} \\times \\left(1 - \\frac{{{f1.numerator}}}{{{f1.denominator}}}\\right)\\left(1 - \\frac{{{f2.numerator}}}{{{f2.denominator}}}\\right)"
        steps = [
            S(
                f"R_1 = {total} \\times \\left(1 - \\frac{{{f1.numerator}}}{{{f1.denominator}}}\\right) = {int(total * rem1)}",
                "Compute the volume remaining after Month 1.",
                eq=[f"{total} * (1 - ({f1}))", str(int(total * rem1))],
            ),
            S(
                f"R_2 = {int(total * rem1)} \\times \\left(1 - \\frac{{{f2.numerator}}}{{{f2.denominator}}}\\right)",
                "Apply the second retention factor to the remaining volume.",
                eq=[f"{int(total * rem1)} * (1 - ({f2}))", str(ans)],
            ),
            S(
                f"R_2 = {ans}",
                "Evaluate the product to find the final remaining volume.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Fractions: Sequential Remainder Synthesis",
        "references": ["MTH-T01-C04-U02", "MTH-T01-C04-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{total} * (1 - {f1}) * (1 - {f2})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Notice that the second fraction applies to the remainder after the first stage, not to the original whole.",
        "commonTrapTag": "c04-remainder-fraction-base-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


TEMPLATES = [
    {
        "key": "c04-fraction-mult-div",
        "trapTag": "c04-reciprocal-omission",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C04-MULT-DIV"},
            "reciprocal": {"level": 1, "skill": "MTH-PREALG-C04-MULT-DIV"},
        },
        "build": t_c04_foundation,
    },
    {
        "key": "c04-unlike-denom-add-sub",
        "trapTag": "c04-unlike-denominator-direct-add",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C04-UNLIKE-ADD"},
            "missing-term": {"level": 2, "skill": "MTH-PREALG-C04-UNLIKE-ADD"},
        },
        "build": t_c04_reverse,
    },
    {
        "key": "c04-complex-fraction-trap",
        "trapTag": "c04-complex-fraction-inversion-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C04-COMPLEX-TRAP"},
            "difference": {"level": 3, "skill": "MTH-PREALG-C04-COMPLEX-TRAP"},
        },
        "build": t_c04_trap,
    },
    {
        "key": "c04-fractional-partition-synthesis",
        "trapTag": "c04-remainder-fraction-base-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C04-SYNTHESIS"},
            "contextual": {"level": 4, "skill": "MTH-PREALG-C04-SYNTHESIS"},
        },
        "build": t_c04_synthesis,
    },
]


def _v_c04_simplification_gcf(rng):
    base_pairs = [
        (2, 5),
        (3, 7),
        (4, 9),
        (5, 8),
        (5, 12),
        (7, 10),
        (7, 12),
        (5, 9),
        (3, 8),
        (2, 9),
        (4, 11),
        (7, 15),
        (8, 15),
        (5, 11),
        (3, 11),
    ]
    factors = [3, 4, 5, 6, 7, 8, 9, 11]
    p, q = rng.choice(base_pairs)
    g = rng.choice(factors)
    a, b = p * g, q * g
    ans_f = Fraction(a, b)
    trap_f = Fraction(b - a, b)
    ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
    return {
        "level": 1,
        "levelLabel": "Level 1 - Foundation",
        "category": "Fraction Simplification",
        "archetype": "problem-solving",
        "archetypeKey": "c04-fraction-simplification-gcf",
        "sourceArchetype": "c04-fraction-simplification-gcf",
        "unitCode": "MTH-T01-C04-U04",
        "form": "direct",
        "context": "",
        "verificationLevel": "partial",
        "prompt": f"Reduce $\\frac{{{a}}}{{{b}}}$ to lowest terms.",
        "display": f"\\frac{{{a}}}{{{b}}}",
        "plainText": f"{a}/{b}",
        "givens": {"a": a, "b": b},
        "constants": {},
        "trapGivens": [a, b],
        "answerSpec": {
            "type": "number",
            "value": ans_s,
            "tol": 0,
            "forms": ["reduced_fraction", "exact"],
        },
        "answerPlain": ans_s,
        "answerDisplay": format_frac_latex(ans_s),
        "inputHint": "Enter a reduced fraction",
        "commonTrapTag": "c04-partial-common-factor-reduction",
        "trapDerivation": f"({b} - {a}) / {b}",
        "trapValue": trap_s,
        "verify": {"source": f"{a} / {b}", "trapValue": trap_s},
        "checkpointHint": "Factor out the greatest common divisor shared by both the numerator and the denominator.",
        "references": ["MTH-T01-C04"],
        "steps": [
            S(
                f"\\frac{{{a}}}{{{b}}} = \\frac{{{p} \\cdot {g}}}{{{q} \\cdot {g}}}",
                "Factor the greatest common divisor out of both the numerator and the denominator.",
                eq=[f"{a} / {b}", f"({p} * {g}) / ({q} * {g})"],
            ),
            S(
                f"\\frac{{{p} \\cdot {g}}}{{{q} \\cdot {g}}} = {format_frac_latex(ans_s)}",
                "Cancel the common factor to obtain the fraction in lowest terms.",
                val=ans_s,
            ),
        ],
    }


def _v_c04_multiplication_product(rng):
    cases = [
        (3, 5, 10, 9),
        (4, 9, 15, 8),
        (5, 6, 9, 25),
        (7, 12, 8, 21),
        (3, 10, 5, 12),
        (8, 15, 5, 12),
        (9, 14, 7, 15),
        (4, 15, 9, 16),
        (5, 14, 7, 20),
        (6, 11, 22, 15),
        (7, 10, 15, 14),
        (9, 16, 4, 27),
    ]
    a, b, c, d = rng.choice(cases)
    ans_f = Fraction(a, b) * Fraction(c, d)
    trap_f = Fraction(a * d, b * c)
    ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
    raw_num, raw_den = a * c, b * d
    return {
        "level": 1,
        "levelLabel": "Level 1 - Foundation",
        "category": "Fraction Multiplication",
        "archetype": "problem-solving",
        "archetypeKey": "c04-fraction-multiplication-product",
        "sourceArchetype": "c04-fraction-multiplication-product",
        "unitCode": "MTH-T01-C04-U04",
        "form": "direct",
        "context": "",
        "verificationLevel": "partial",
        "prompt": f"Multiply $\\frac{{{a}}}{{{b}}} \\times \\frac{{{c}}}{{{d}}}$ and express the result in lowest terms.",
        "display": f"\\frac{{{a}}}{{{b}}} \\times \\frac{{{c}}}{{{d}}}",
        "plainText": f"({a}/{b}) * ({c}/{d})",
        "givens": {"a": a, "b": b, "c": c, "d": d},
        "constants": {},
        "trapGivens": [a, b, c, d],
        "answerSpec": {
            "type": "number",
            "value": ans_s,
            "tol": 0,
            "forms": ["reduced_fraction", "exact"],
        },
        "answerPlain": ans_s,
        "answerDisplay": format_frac_latex(ans_s),
        "inputHint": "Enter a reduced fraction",
        "commonTrapTag": "c04-cross-multiplication-confusion",
        "trapDerivation": f"({a} * {d}) / ({b} * {c})",
        "trapValue": trap_s,
        "verify": {"source": f"({a} / {b}) * ({c} / {d})", "trapValue": trap_s},
        "checkpointHint": "Multiply numerator by numerator and denominator by denominator, then cancel common factors.",
        "references": ["MTH-T01-C04"],
        "steps": [
            S(
                f"\\frac{{{a}}}{{{b}}} \\times \\frac{{{c}}}{{{d}}} = \\frac{{{a} \\cdot {c}}}{{{b} \\cdot {d}}}",
                "Multiply the numerators together and multiply the denominators together.",
                eq=[f"({a} / {b}) * ({c} / {d})", f"({a} * {c}) / ({b} * {d})"],
            ),
            S(
                f"\\frac{{{a} \\cdot {c}}}{{{b} \\cdot {d}}} = \\frac{{{raw_num}}}{{{raw_den}}}",
                "Evaluate the products in the numerator and the denominator.",
                eq=[f"({a} * {c}) / ({b} * {d})", f"{raw_num} / {raw_den}"],
            ),
            S(
                f"\\frac{{{raw_num}}}{{{raw_den}}} = {format_frac_latex(ans_s)}",
                "Divide both numerator and denominator by their greatest common factor.",
                val=ans_s,
            ),
        ],
    }


def _v_c04_division_reciprocal(rng):
    cases = [
        (3, 5, 9, 10),
        (5, 8, 15, 16),
        (4, 7, 8, 21),
        (7, 9, 14, 15),
        (5, 12, 10, 9),
        (9, 10, 3, 4),
        (7, 8, 21, 16),
        (4, 9, 16, 15),
        (5, 6, 15, 8),
        (3, 8, 9, 16),
        (8, 9, 4, 15),
        (11, 12, 22, 9),
    ]
    a, b, c, d = rng.choice(cases)
    ans_f = Fraction(a, b) / Fraction(c, d)
    trap_f = Fraction(a, b) * Fraction(c, d)
    ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
    raw_num, raw_den = a * d, b * c
    return {
        "level": 2,
        "levelLabel": "Level 2 - Standard Exam",
        "category": "Fraction Division",
        "archetype": "problem-solving",
        "archetypeKey": "c04-fraction-division-reciprocal-inversion",
        "sourceArchetype": "c04-fraction-division-reciprocal-inversion",
        "unitCode": "MTH-T01-C04-U04",
        "form": "direct",
        "context": "",
        "verificationLevel": "partial",
        "prompt": f"Divide $\\frac{{{a}}}{{{b}}} \\div \\frac{{{c}}}{{{d}}}$ and write the answer in lowest terms.",
        "display": f"\\frac{{{a}}}{{{b}}} \\div \\frac{{{c}}}{{{d}}}",
        "plainText": f"({a}/{b}) / ({c}/{d})",
        "givens": {"a": a, "b": b, "c": c, "d": d},
        "constants": {},
        "trapGivens": [a, b, c, d],
        "answerSpec": {
            "type": "number",
            "value": ans_s,
            "tol": 0,
            "forms": ["reduced_fraction", "exact"],
        },
        "answerPlain": ans_s,
        "answerDisplay": format_frac_latex(ans_s),
        "inputHint": "Enter a reduced fraction",
        "commonTrapTag": "c04-first-fraction-reciprocal-flip",
        "trapDerivation": f"({a} * {c}) / ({b} * {d})",
        "trapValue": trap_s,
        "verify": {"source": f"({a} / {b}) / ({c} / {d})", "trapValue": trap_s},
        "checkpointHint": "Keep the dividend unchanged and multiply by the reciprocal of the divisor fraction.",
        "references": ["MTH-T01-C04"],
        "steps": [
            S(
                f"\\frac{{{a}}}{{{b}}} \\div \\frac{{{c}}}{{{d}}} = \\frac{{{a}}}{{{b}}} \\times \\frac{{{d}}}{{{c}}}",
                "Rewrite division as multiplication by the reciprocal of the divisor fraction.",
                eq=[f"({a} / {b}) / ({c} / {d})", f"({a} / {b}) * ({d} / {c})"],
            ),
            S(
                f"\\frac{{{a}}}{{{b}}} \\times \\frac{{{d}}}{{{c}}} = \\frac{{{raw_num}}}{{{raw_den}}}",
                "Multiply the numerators together and multiply the denominators together.",
                eq=[f"({a} / {b}) * ({d} / {c})", f"{raw_num} / {raw_den}"],
            ),
            S(
                f"\\frac{{{raw_num}}}{{{raw_den}}} = {format_frac_latex(ans_s)}",
                "Reduce the resulting fraction to lowest terms.",
                val=ans_s,
            ),
        ],
    }


def _v_c04_addition_like_denom(rng):
    cases = [
        (3, 5, 12),
        (5, 7, 16),
        (4, 5, 15),
        (5, 9, 18),
        (7, 11, 24),
        (3, 7, 15),
        (5, 11, 20),
        (7, 9, 20),
        (5, 7, 18),
        (4, 11, 21),
        (5, 13, 24),
        (7, 8, 25),
    ]
    a, b, d = rng.choice(cases)
    total_num = a + b
    ans_f = Fraction(total_num, d)
    trap_f = Fraction(total_num, d + d)
    ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
    return {
        "level": 2,
        "levelLabel": "Level 2 - Standard Exam",
        "category": "Fraction Addition",
        "archetype": "problem-solving",
        "archetypeKey": "c04-fraction-addition-like-denominators",
        "sourceArchetype": "c04-fraction-addition-like-denominators",
        "unitCode": "MTH-T01-C04-U02",
        "form": "direct",
        "context": "",
        "verificationLevel": "partial",
        "prompt": f"Add $\\frac{{{a}}}{{{d}}} + \\frac{{{b}}}{{{d}}}$ and simplify your answer to lowest terms.",
        "display": f"\\frac{{{a}}}{{{d}}} + \\frac{{{b}}}{{{d}}}",
        "plainText": f"{a}/{d} + {b}/{d}",
        "givens": {"a": a, "b": b, "d": d},
        "constants": {},
        "trapGivens": [a, b, d],
        "answerSpec": {
            "type": "number",
            "value": ans_s,
            "tol": 0,
            "forms": ["reduced_fraction", "exact"],
        },
        "answerPlain": ans_s,
        "answerDisplay": format_frac_latex(ans_s),
        "inputHint": "Enter a reduced fraction",
        "commonTrapTag": "c04-denominator-addition-fallacy",
        "trapDerivation": f"({a} + {b}) / ({d} + {d})",
        "trapValue": trap_s,
        "verify": {"source": f"{a} / {d} + {b} / {d}", "trapValue": trap_s},
        "checkpointHint": "Keep the shared denominator unchanged while adding only the numerators, then reduce.",
        "references": ["MTH-T01-C04"],
        "steps": [
            S(
                f"\\frac{{{a}}}{{{d}}} + \\frac{{{b}}}{{{d}}} = \\frac{{{a} + {b}}}{{{d}}}",
                "Combine the numerators over the shared denominator.",
                eq=[f"{a} / {d} + {b} / {d}", f"({a} + {b}) / {d}"],
            ),
            S(
                f"\\frac{{{a} + {b}}}{{{d}}} = \\frac{{{total_num}}}{{{d}}}",
                "Add the numerators.",
                eq=[f"({a} + {b}) / {d}", f"{total_num} / {d}"],
            ),
            S(
                f"\\frac{{{total_num}}}{{{d}}} = {format_frac_latex(ans_s)}",
                "Divide numerator and denominator by their greatest common factor.",
                val=ans_s,
            ),
        ],
    }


def _v_c04_addition_unlike_denom(rng):
    cases = [
        (2, 3, 1, 4),
        (3, 5, 1, 2),
        (5, 6, 3, 8),
        (4, 9, 5, 6),
        (7, 10, 2, 15),
        (3, 7, 5, 14),
        (5, 8, 1, 6),
        (2, 9, 5, 12),
        (3, 4, 2, 5),
        (5, 12, 3, 10),
        (4, 15, 7, 20),
        (1, 6, 4, 9),
    ]
    a, b, c, d = rng.choice(cases)
    lcd = math.lcm(b, d)
    m1, m2 = lcd // b, lcd // d
    n1, n2 = a * m1, c * m2
    sum_n = n1 + n2
    ans_f = Fraction(a, b) + Fraction(c, d)
    trap_f = Fraction(a + c, b + d)
    ans_s, trap_s = _fstr(ans_f), _fstr(trap_f)
    steps = [
        S(
            f"\\text{{LCD}}({b}, {d}) = {lcd}",
            "Find the least common denominator of the two fractions.",
            eq=[str(lcd), str(lcd)],
        ),
        S(
            f"\\frac{{{a}}}{{{b}}} + \\frac{{{c}}}{{{d}}} = \\frac{{{n1}}}{{{lcd}}} + \\frac{{{n2}}}{{{lcd}}}",
            "Convert each fraction to an equivalent fraction with the common denominator.",
            eq=[f"{a} / {b} + {c} / {d}", f"{n1} / {lcd} + {n2} / {lcd}"],
        ),
    ]
    if math.gcd(sum_n, lcd) > 1:
        steps.append(
            S(
                f"\\frac{{{n1}}}{{{lcd}}} + \\frac{{{n2}}}{{{lcd}}} = \\frac{{{sum_n}}}{{{lcd}}}",
                "Add the numerators over the common denominator.",
                eq=[f"{n1} / {lcd} + {n2} / {lcd}", f"{sum_n} / {lcd}"],
            )
        )
        steps.append(
            S(
                f"\\frac{{{sum_n}}}{{{lcd}}} = {format_frac_latex(ans_s)}",
                "Reduce the sum to lowest terms.",
                val=ans_s,
            )
        )
    else:
        steps.append(
            S(
                f"\\frac{{{n1}}}{{{lcd}}} + \\frac{{{n2}}}{{{lcd}}} = {format_frac_latex(ans_s)}",
                "Add the numerators over the common denominator; the result is already in lowest terms.",
                val=ans_s,
            )
        )
    return {
        "level": 2,
        "levelLabel": "Level 2 - Standard Exam",
        "category": "Fraction Addition",
        "archetype": "problem-solving",
        "archetypeKey": "c04-fraction-addition-unlike-denominators-lcd",
        "sourceArchetype": "c04-fraction-addition-unlike-denominators-lcd",
        "unitCode": "MTH-T01-C04-U03",
        "form": "direct",
        "context": "",
        "verificationLevel": "partial",
        "prompt": f"Add $\\frac{{{a}}}{{{b}}} + \\frac{{{c}}}{{{d}}}$ and write the result as a reduced fraction.",
        "display": f"\\frac{{{a}}}{{{b}}} + \\frac{{{c}}}{{{d}}}",
        "plainText": f"{a}/{b} + {c}/{d}",
        "givens": {"a": a, "b": b, "c": c, "d": d},
        "constants": {},
        "trapGivens": [a, b, c, d],
        "answerSpec": {
            "type": "number",
            "value": ans_s,
            "tol": 0,
            "forms": ["reduced_fraction", "exact"],
        },
        "answerPlain": ans_s,
        "answerDisplay": format_frac_latex(ans_s),
        "inputHint": "Enter a reduced fraction",
        "commonTrapTag": "c04-naive-numerator-denominator-sum",
        "trapDerivation": f"({a} + {c}) / ({b} + {d})",
        "trapValue": trap_s,
        "verify": {"source": f"{a} / {b} + {c} / {d}", "trapValue": trap_s},
        "checkpointHint": "Rewrite both fractions over their least common denominator before adding the numerators.",
        "references": ["MTH-T01-C04"],
        "steps": steps,
    }


VARIANT_TEMPLATES = {
    "c04-fraction-simplification-gcf": _v_c04_simplification_gcf,
    "c04-fraction-multiplication-product": _v_c04_multiplication_product,
    "c04-fraction-division-reciprocal-inversion": _v_c04_division_reciprocal,
    "c04-fraction-addition-like-denominators": _v_c04_addition_like_denom,
    "c04-fraction-addition-unlike-denominators-lcd": _v_c04_addition_unlike_denom,
}
