# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C07: Proportional & Ratio."""

from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C07"
TITLE = "Proportional & Ratio"

MISTAKE_TAGS = [
    {
        "id": "c07-cross-multiply-inversion",
        "label": "Multiplied numerator by numerator instead of cross-multiplying proportion",
        "name": "Proportion Cross-Multiplication Inversion",
        "autoFrom": [],
    },
    {
        "id": "c07-ratio-part-vs-whole-trap",
        "label": "Divided total by single ratio part instead of sum of ratio parts",
        "name": "Ratio Part vs Whole Partition Trap",
        "autoFrom": [],
    },
    {
        "id": "c07-area-linear-scale-trap",
        "label": "Scaled area by linear scale factor k instead of k^2",
        "name": "Area vs Linear Scale Factor Trap",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "c07-arithmetic-mean-speed-trap",
        "label": "Averaged round-trip speeds arithmetically instead of using harmonic mean",
        "name": "Round-Trip Harmonic Speed Trap",
        "autoFrom": [],
    },
]


def t_c07_foundation(rng, form=None):
    if form not in ("direct", "unit-rate"):
        form = rng.choice(["direct", "unit-rate"])
    a = rng.randint(3, 9)
    b = rng.randint(4, 11)
    if a == b:
        b += 1
    k = rng.randint(4, 12)
    c = a * k
    d = b * k
    ans = c
    trap = b * c
    if form == "unit-rate":
        prompt = f"A machine processes ${a}$ wafers every ${b}$ minutes. At this constant rate, how many wafers $x$ will it process in ${d}$ minutes?"
        disp = f"\\frac{{{a}}}{{{b}}} = \\frac{{x}}{{{d}}}"
    else:
        prompt = f"Solve the proportion for $x$: $\\frac{{{a}}}{{{b}}} = \\frac{{x}}{{{d}}}$."
        disp = f"\\frac{{{a}}}{{{b}}} = \\frac{{x}}{{{d}}} \\implies x = ?"
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Proportions: Cross-Multiplication & Scaling",
        "references": ["MTH-T01-C07-U02"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{a}/{b} = x/{d}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Cross-multiply the proportion and divide by the coefficient of the unknown variable.",
        "commonTrapTag": "c07-cross-multiply-inversion",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(f"{b}x = {a} \\times {d} = {a * d}", "Cross-multiply the proportion.", eq=[f"{a} * {d}", str(a * d)]),
            S(
                f"x = \\frac{{{a * d}}}{{{b}}}",
                "Divide both sides by the denominator coefficient.",
                eq=[f"({a * d}) / {b}", str(ans)],
            ),
            S(f"x = {ans}", "Simplify the quotient.", val=str(ans), eq=[str(ans), str(ans)]),
        ],
    }


def t_c07_reverse(rng, form=None):
    if form not in ("direct", "reverse-scale"):
        form = rng.choice(["direct", "reverse-scale"])
    ratios = [(2, 3), (3, 5), (4, 5), (3, 7), (5, 7), (4, 9)]
    r1, r2 = rng.choice(ratios)
    mult = rng.randint(8, 25)
    part2 = r2 * mult
    total = (r1 + r2) * mult
    if form == "reverse-scale":
        ans = total
        trap = part2 + r1
        prompt = f"Two alloy components are mixed in the ratio ${r1} : {r2}$. If the heavier component weighs ${part2}$ grams, what is the total weight of the mixture in grams?"
        disp = f"\\frac{{\\text{{Total}}}}{{{r1} + {r2}}} = \\frac{{{part2}}}{{{r2}}}"
        steps = [
            S(
                f"k = \\frac{{{part2}}}{{{r2}}} = {mult}",
                "Find the weight corresponding to one ratio unit.",
                eq=[f"{part2} / {r2}", str(mult)],
            ),
            S(
                f"\\text{{Total parts}} = {r1} + {r2} = {r1 + r2}",
                "Add the ratio parts to get total parts.",
                eq=[f"{r1} + {r2}", str(r1 + r2)],
            ),
            S(
                f"\\text{{Total}} = {r1 + r2} \\times {mult} = {ans}",
                "Multiply total parts by the unit multiplier.",
                val=str(ans),
                eq=[f"({r1 + r2}) * {mult}", str(ans)],
            ),
        ]
    else:
        ans = part2
        trap = total // r2
        prompt = f"A sum of ${total}$ dollars is partitioned between two research teams in the ratio ${r1} : {r2}$. How many dollars does the team with the larger share receive?"
        disp = f"\\text{{Share}}_2 = {total} \\times \\frac{{{r2}}}{{{r1} + {r2}}}"
        steps = [
            S(
                f"\\text{{Total parts}} = {r1} + {r2} = {r1 + r2}",
                "Sum the parts of the ratio.",
                eq=[f"{r1} + {r2}", str(r1 + r2)],
            ),
            S(
                f"\\text{{One part}} = \\frac{{{total}}}{{{r1 + r2}}} = {mult}",
                "Divide the total amount by the sum of the ratio parts.",
                eq=[f"{total} / ({r1 + r2})", str(mult)],
            ),
            S(
                f"\\text{{Larger share}} = {r2} \\times {mult} = {ans}",
                "Multiply the larger ratio number by one part.",
                val=str(ans),
                eq=[f"{r2} * {mult}", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Proportions: Ratio Partitioning",
        "references": ["MTH-T01-C07-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"ratio {r1}:{r2} with mult {mult}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Sum the individual ratio parts to relate each part to the whole quantity.",
        "commonTrapTag": "c07-ratio-part-vs-whole-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c07_trap(rng, form=None):
    if form not in ("direct", "volume-scale"):
        form = rng.choice(["direct", "volume-scale"])
    k = rng.choice([2, 3, 4, 5])
    base_area = rng.randint(12, 35)
    if form == "volume-scale":
        ans = base_area * (k**3)
        trap = base_area * k
        prompt = f"A scale model of a storage tank has a volume of ${base_area}$ cubic centimeters. If every linear dimension of the full-size tank is ${k}$ times the corresponding dimension of the model, what is the volume of the full-size tank in cubic centimeters?"
        disp = f"V_{{\\text{{new}}}} = k^3 V_0 = ({k})^3 ({base_area})"
        steps = [
            S(
                f"\\text{{Linear scale factor }} k = {k} \\implies \\text{{Volume scale factor}} = k^3 = {k}^3 = {k**3}",
                "Volume scales by the cube of the linear similarity factor.",
                eq=[f"{k}**3", str(k**3)],
            ),
            S(
                f"V_{{\\text{{new}}}} = {base_area} \\times {k**3}",
                "Multiply the original volume by the cubic scale factor.",
                eq=[f"{base_area} * ({k**3})", str(ans)],
            ),
            S(f"V_{{\\text{{new}}}} = {ans}", "Evaluate the product.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        ans = base_area * (k**2)
        trap = base_area * k
        prompt = f"Triangle $T_1$ has an area of ${base_area}$ square meters. Triangle $T_2$ is similar to $T_1$ with every side length multiplied by a scale factor of $k = {k}$. Find the area of triangle $T_2$ in square meters."
        disp = f"A_2 = k^2 A_1 = ({k})^2 ({base_area})"
        steps = [
            S(
                f"\\text{{Linear scale factor }} k = {k} \\implies \\text{{Area scale factor}} = k^2 = {k}^2 = {k**2}",
                "For similar figures, area scales as the square of the linear scale factor.",
                eq=[f"{k}**2", str(k**2)],
            ),
            S(
                f"A_2 = {base_area} \\times {k**2}",
                "Multiply the original area by the squared scale factor.",
                eq=[f"{base_area} * ({k**2})", str(ans)],
            ),
            S(f"A_2 = {ans}", "Compute the exact area.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Proportions: Similar Figures Area & Volume Scaling Trap",
        "references": ["MTH-T01-C07-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{base_area} * {k}^d",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Remember that scaling all linear dimensions by k multiplies area by k^2 and volume by k^3.",
        "commonTrapTag": "c07-area-linear-scale-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c07_synthesis(rng, form=None):
    if form not in ("direct", "combined-work"):
        form = rng.choice(["direct", "combined-work"])
    cases = [
        (30, 60, 40, 45, 20),
        (40, 60, 48, 50, 24),
        (20, 30, 24, 25, 12),
        (60, 120, 80, 90, 40),
        (36, 72, 48, 54, 24),
    ]
    v1, v2, h_mean, a_mean, work_t = rng.choice(cases)
    if form == "combined-work":
        ans = work_t
        trap = a_mean
        prompt = f"Pump A can empty a basin alone in ${v1}$ minutes, and Pump B can empty the same basin alone in ${v2}$ minutes. Working together simultaneously at their constant rates, how many minutes will it take them to empty the basin?"
        disp = f"\\frac{{1}}{{{v1}}} + \\frac{{1}}{{{v2}}} = \\frac{{1}}{{t}} \\implies t = ?"
        steps = [
            S(
                f"R_{{\\text{{combined}}}} = \\frac{{1}}{{{v1}}} + \\frac{{1}}{{{v2}}} = \\frac{{{v1 + v2}}}{{{v1 * v2}}}",
                "Add the individual unit work rates.",
                eq=[f"1/{v1} + 1/{v2}", f"({v1 + v2})/({v1 * v2})"],
            ),
            S(
                f"t = \\frac{{{v1} \\times {v2}}}{{{v1} + {v2}}} = \\frac{{{v1 * v2}}}{{{v1 + v2}}}",
                "Take the reciprocal of the combined rate to find total time.",
                eq=[f"({v1} * {v2}) / ({v1} + {v2})", str(ans)],
            ),
            S(f"t = {ans}", "Simplify the quotient.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        ans = h_mean
        trap = a_mean
        prompt = f"A train travels from Station A to Station B at a constant speed of ${v1}\\text{{ km/h}}$ and immediately returns along the exact same route from Station B to Station A at ${v2}\\text{{ km/h}}$. What is the train's average speed for the entire round trip in km/h?"
        disp = f"v_{{\\text{{avg}}}} = \\frac{{2 v_1 v_2}}{{v_1 + v_2}} = \\frac{{2({v1})({v2})}}{{{v1} + {v2}}}"
        steps = [
            S(
                f"t_{{\\text{{total}}}} = \\frac{{d}}{{{v1}}} + \\frac{{d}}{{{v2}}} = d\\left(\\frac{{{v1 + v2}}}{{{v1 * v2}}}\\right)",
                "Express total round-trip time in terms of one-way distance $d$.",
                eq=[f"1/{v1} + 1/{v2}", f"({v1 + v2})/({v1 * v2})"],
            ),
            S(
                f"v_{{\\text{{avg}}}} = \\frac{{2d}}{{t_{{\\text{{total}}}}}} = \\frac{{2({v1})({v2})}}{{{v1} + {v2}}}",
                "Divide total distance $2d$ by total time to get the harmonic mean.",
                eq=[f"(2 * {v1} * {v2}) / ({v1} + {v2})", str(ans)],
            ),
            S(f"v_{{\\text{{avg}}}} = {ans}", "Evaluate the harmonic mean.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Proportions & Rates: Harmonic Speed & Combined Work Synthesis",
        "references": ["MTH-T01-C07-U01", "MTH-T01-C07-U06"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"(2*{v1}*{v2})/({v1}+{v2})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Combine rates (reciprocals of time) rather than averaging times or speeds directly.",
        "commonTrapTag": "c07-arithmetic-mean-speed-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


TEMPLATES = [
    {
        "key": "c07-unit-rate-proportion",
        "trapTag": "c07-cross-multiply-inversion",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C07-PROPORTION"},
            "unit-rate": {"level": 1, "skill": "MTH-PREALG-C07-PROPORTION"},
        },
        "build": t_c07_foundation,
    },
    {
        "key": "c07-similar-figures-scale",
        "trapTag": "c07-ratio-part-vs-whole-trap",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C07-RATIO-SHARE"},
            "reverse-scale": {"level": 2, "skill": "MTH-PREALG-C07-RATIO-SHARE"},
        },
        "build": t_c07_reverse,
    },
    {
        "key": "c07-area-scale-factor-trap",
        "trapTag": "c07-area-linear-scale-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C07-SCALE-TRAP"},
            "volume-scale": {"level": 3, "skill": "MTH-PREALG-C07-SCALE-TRAP"},
        },
        "build": t_c07_trap,
    },
    {
        "key": "c07-harmonic-speed-work-synthesis",
        "trapTag": "c07-arithmetic-mean-speed-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C07-SYNTHESIS"},
            "combined-work": {"level": 4, "skill": "MTH-PREALG-C07-SYNTHESIS"},
        },
        "build": t_c07_synthesis,
    },
]
