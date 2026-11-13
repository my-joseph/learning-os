# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C05: Decimals."""

from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C05"
TITLE = "Decimals"

MISTAKE_TAGS = [
    {
        "id": "c05-decimal-point-alignment",
        "label": "Misaligned decimal places when adding or multiplying decimals",
        "name": "Decimal Place Alignment Slip",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "c05-missing-score-mean-trap",
        "label": "Divided by N-1 instead of N when solving for a missing score from target mean",
        "name": "Target Mean Count Error",
        "autoFrom": [],
    },
    {
        "id": "c05-decimal-divisor-shift-trap",
        "label": "Shifted decimal point in wrong direction when dividing by a small decimal",
        "name": "Decimal Divisor Shift Trap",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "c05-weighted-average-unweighted-trap",
        "label": "Averaged group means directly without weighting by group sizes",
        "name": "Unweighted Group Mean Fallacy",
        "autoFrom": [],
    },
]


def t_c05_foundation(rng, form=None):
    if form not in ("direct", "rate"):
        form = rng.choice(["direct", "rate"])
    cases = [
        ("2.5", 6, "3.2", 5, 15, 16, 31, 19),
        ("1.5", 8, "2.5", 4, 12, 10, 22, 14),
        ("3.5", 4, "1.25", 8, 14, 10, 24, 18),
        ("2.25", 4, "1.5", 6, 9, 9, 18, 12),
        ("4.5", 2, "0.75", 8, 9, 6, 15, 11),
    ]
    d1, n1, d2, n2, p1, p2, ans, trap = rng.choice(cases)
    if form == "rate":
        prompt = f"A courier drives for ${n1}$ hours at ${d1}$ meters per millisecond equivalent scale and ${n2}$ hours at ${d2}$ units per hour. Compute the exact total ${n1}({d1}) + {n2}({d2})$."
        disp = f"{n1}({d1}) + {n2}({d2})"
    else:
        prompt = f"Evaluate the exact decimal expression ${n1} \\times {d1} + {n2} \\times {d2}$."
        disp = f"{n1} \\times {d1} + {n2} \\times {d2}"
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Decimals: Exact Decimal Operations",
        "references": ["MTH-T01-C05-U02"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{n1}*{d1} + {n2}*{d2}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Multiply each decimal by its whole-number factor carefully tracking decimal places, then sum the two products.",
        "commonTrapTag": "c05-decimal-point-alignment",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(f"P_1 = {n1} \\times {d1} = {p1}", "Compute the first decimal product.", eq=[f"{n1} * {d1}", str(p1)]),
            S(f"P_2 = {n2} \\times {d2} = {p2}", "Compute the second decimal product.", eq=[f"{n2} * {d2}", str(p2)]),
            S(
                f"P_1 + P_2 = {p1} + {p2} = {ans}",
                "Add the two exact products.",
                val=str(ans),
                eq=[f"{p1} + {p2}", str(ans)],
            ),
        ],
    }


def t_c05_reverse(rng, form=None):
    if form not in ("direct", "missing-score"):
        form = rng.choice(["direct", "missing-score"])
    s1 = rng.randint(72, 88)
    s2 = rng.randint(74, 90)
    s3 = rng.randint(76, 92)
    target_mean = rng.randint(82, 91)
    total_needed = 4 * target_mean
    current_sum = s1 + s2 + s3
    ans = total_needed - current_sum
    trap = 3 * target_mean - current_sum
    if ans == trap:
        trap = ans - 5
    if form == "missing-score":
        prompt = f"A student has scored ${s1}$, ${s2}$, and ${s3}$ on the first three exams. What score $x$ on the fourth exam is required to achieve an exact mean score of ${target_mean}$ across all four exams?"
        disp = f"\\frac{{{s1} + {s2} + {s3} + x}}{{4}} = {target_mean}"
    else:
        prompt = (
            f"Solve for $x$ so that the arithmetic mean of $\\{{{s1},\\ {s2},\\ {s3},\\ x\\}}$ equals ${target_mean}$."
        )
        disp = f"\\frac{{{s1} + {s2} + {s3} + x}}{{4}} = {target_mean} \\implies x = ?"
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Decimals & Averages: Missing Score for Target Mean",
        "references": ["MTH-T01-C05-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"({s1} + {s2} + {s3} + x) / 4 = {target_mean}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Multiply the target mean by the total number of exams (including the new exam), then subtract the sum of the existing scores.",
        "commonTrapTag": "c05-missing-score-mean-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(
                f"S_{{\\text{{required}}}} = 4 \\times {target_mean} = {total_needed}",
                "Multiply the target average by 4 to find the required sum of all four scores.",
                eq=[f"4 * {target_mean}", str(total_needed)],
            ),
            S(
                f"S_{{\\text{{current}}}} = {s1} + {s2} + {s3} = {current_sum}",
                "Sum the three known scores.",
                eq=[f"{s1} + {s2} + {s3}", str(current_sum)],
            ),
            S(
                f"x = {total_needed} - {current_sum} = {ans}",
                "Subtract the known sum from the required total.",
                val=str(ans),
                eq=[f"{total_needed} - {current_sum}", str(ans)],
            ),
        ],
    }


def t_c05_trap(rng, form=None):
    if form not in ("direct", "combined"):
        form = rng.choice(["direct", "combined"])
    cases = [
        ("3.6", "0.04", 360, 4, 90, 9),
        ("4.8", "0.06", 480, 6, 80, 8),
        ("7.2", "0.08", 720, 8, 90, 9),
        ("6.3", "0.07", 630, 7, 90, 9),
        ("5.4", "0.09", 540, 9, 60, 6),
        ("8.4", "0.07", 840, 7, 120, 12),
    ]
    num_d, den_d, num_s, den_s, q_val, trap_q = rng.choice(cases)
    if form == "combined":
        offset = rng.randint(15, 45)
        ans = q_val - offset
        trap = trap_q + offset
        prompt = f"Evaluate the decimal expression $\\frac{{{num_d}}}{{{den_d}}} - {offset}$."
        disp = f"\\frac{{{num_d}}}{{{den_d}}} - {offset}"
        steps = [
            S(
                f"\\frac{{{num_d}}}{{{den_d}}} = \\frac{{{num_d} \\times 100}}{{{den_d} \\times 100}} = \\frac{{{num_s}}}{{{den_s}}}",
                "Multiply numerator and denominator by 100 to clear two decimal places in the divisor.",
                eq=[f"{num_d} / {den_d}", str(q_val)],
            ),
            S(
                f"\\frac{{{num_s}}}{{{den_s}}} = {q_val}",
                "Divide the whole numbers.",
                eq=[f"{num_s} / {den_s}", str(q_val)],
            ),
            S(
                f"{q_val} - {offset} = {ans}",
                "Subtract the integer offset.",
                val=str(ans),
                eq=[f"{q_val} - {offset}", str(ans)],
            ),
        ]
    else:
        ans = q_val
        trap = trap_q
        prompt = f"Divide the decimals by shifting place values: $\\frac{{{num_d}}}{{{den_d}}}$."
        disp = f"\\frac{{{num_d}}}{{{den_d}}}"
        steps = [
            S(
                f"\\frac{{{num_d}}}{{{den_d}}} = \\frac{{{num_d} \\times 100}}{{{den_d} \\times 100}}",
                "Shift the decimal point two places to the right in both numerator and denominator.",
                eq=[f"{num_d} / {den_d}", str(ans)],
            ),
            S(
                f"= \\frac{{{num_s}}}{{{den_s}}}",
                "Rewrite as a quotient of whole numbers.",
                eq=[f"{num_s} / {den_s}", str(ans)],
            ),
            S(f"= {ans}", "Perform the integer division.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Decimals: Small Divisor Place-Value Shift Trap",
        "references": ["MTH-T01-C05-U02"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"({num_d}) / ({den_d})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Multiply both numerator and denominator by 100 so the divisor becomes a whole number before dividing.",
        "commonTrapTag": "c05-decimal-divisor-shift-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c05_synthesis(rng, form=None):
    if form not in ("direct", "contextual"):
        form = rng.choice(["direct", "contextual"])
    cases = [
        (10, 78, 15, 88, 84, 83),
        (12, 75, 18, 85, 81, 80),
        (8, 70, 12, 90, 82, 80),
        (15, 80, 10, 95, 86, 87),
        (6, 72, 14, 92, 86, 82),
    ]
    n1, m1, n2, m2, ans, trap = rng.choice(cases)
    tot1 = n1 * m1
    tot2 = n2 * m2
    tot_n = n1 + n2
    if form == "contextual":
        prompt = f"In a physics tournament, Section A has ${n1}$ students with a mean score of ${m1}$, and Section B has ${n2}$ students with a mean score of ${m2}$. What is the combined mean score of all ${tot_n}$ students?"
        disp = f"\\bar{{x}} = \\frac{{{n1}({m1}) + {n2}({m2})}}{{{n1} + {n2}}}"
    else:
        prompt = f"Compute the weighted average of two groups: ${n1}$ observations with mean ${m1}$ and ${n2}$ observations with mean ${m2}$."
        disp = f"\\frac{{{n1} \\times {m1} + {n2} \\times {m2}}}{{{n1} + {n2}}}"
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Decimals & Averages: Weighted Group Mean Synthesis",
        "references": ["MTH-T01-C05-U05", "MTH-T01-C05-U06"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"({n1}*{m1} + {n2}*{m2}) / ({n1} + {n2})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Find the total sum of scores across both groups by multiplying each group size by its mean, then divide by the combined number of students.",
        "commonTrapTag": "c05-weighted-average-unweighted-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(
                f"S_1 = {n1} \\times {m1} = {tot1}, \\quad S_2 = {n2} \\times {m2} = {tot2}",
                "Compute the total score for each group separately.",
                eq=[f"{n1}*{m1} + {n2}*{m2}", str(tot1 + tot2)],
            ),
            S(
                f"S_{{\\text{{total}}}} = {tot1} + {tot2} = {tot1 + tot2}, \\quad N_{{\\text{{total}}}} = {n1} + {n2} = {tot_n}",
                "Sum the group totals and the group sizes.",
                eq=[f"{n1} + {n2}", str(tot_n)],
            ),
            S(
                f"\\bar{{x}} = \\frac{{{tot1 + tot2}}}{{{tot_n}}} = {ans}",
                "Divide the combined score sum by the total number of observations.",
                val=str(ans),
                eq=[f"({tot1 + tot2}) / {tot_n}", str(ans)],
            ),
        ],
    }


TEMPLATES = [
    {
        "key": "c05-decimal-linear-eval",
        "trapTag": "c05-decimal-point-alignment",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C05-DEC-OPS"},
            "rate": {"level": 1, "skill": "MTH-PREALG-C05-DEC-OPS"},
        },
        "build": t_c05_foundation,
    },
    {
        "key": "c05-decimal-equation-mean",
        "trapTag": "c05-missing-score-mean-trap",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C05-MEAN"},
            "missing-score": {"level": 2, "skill": "MTH-PREALG-C05-MEAN"},
        },
        "build": t_c05_reverse,
    },
    {
        "key": "c05-decimal-division-shift-trap",
        "trapTag": "c05-decimal-divisor-shift-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C05-DIV-SHIFT"},
            "combined": {"level": 3, "skill": "MTH-PREALG-C05-DIV-SHIFT"},
        },
        "build": t_c05_trap,
    },
    {
        "key": "c05-weighted-average-probability-synthesis",
        "trapTag": "c05-weighted-average-unweighted-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C05-SYNTHESIS"},
            "contextual": {"level": 4, "skill": "MTH-PREALG-C05-SYNTHESIS"},
        },
        "build": t_c05_synthesis,
    },
]
