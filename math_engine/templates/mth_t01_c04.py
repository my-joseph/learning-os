# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C04: Fractions."""

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
