# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C09: Roots."""
from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C09"
TITLE = "Roots"

MISTAKE_TAGS = [
    {"id": "c09-root-halving-trap", "label": "Divided radicand by 2 instead of taking principal square root", "name": "Radicand Halving Error", "autoFrom": []},
    {"id": "c09-radical-equation-unsquared-trap", "label": "Failed to square both sides when isolating variable inside a radical", "name": "Radical Equation Unsquared Trap", "autoFrom": []},
    {"id": "c09-root-sum-distribution-trap", "label": "Distributed square root across addition: sqrt(a^2 + b^2) != a + b", "name": "Square Root Sum Distribution Trap", "autoFrom": []},
    {"id": "c09-nested-radical-evaluation-trap", "label": "Evaluated outer radical before simplifying inner nested radical", "name": "Nested Radical Inside-Out Trap", "autoFrom": []},
]



def t_c09_foundation(rng, form=None):
    if form not in ("direct", "combined"):
        form = rng.choice(["direct", "combined"])
    a = rng.choice([6, 7, 8, 9, 11, 12, 13])
    b = rng.choice([2, 3, 4, 5])
    k = rng.randint(2, 5)
    if form == "combined":
        ans = k * a + b
        trap = k * (a * a // 2) + b
        prompt = f"Evaluate the radical expression ${k}\\sqrt{{{a*a}}} + \\sqrt[3]{{{b**3}}}$."
        disp = f"{k}\\sqrt{{{a*a}}} + \\sqrt[3]{{{b**3}}}"
        steps = [
            S(f"\\sqrt{{{a*a}}} = {a}, \\quad \\sqrt[3]{{{b**3}}} = {b}", "Evaluate the principal square root and the cube root.", eq=[f"sqrt({a*a})", str(a)]),
            S(f"{k}\\sqrt{{{a*a}}} = {k}({a}) = {k * a}", "Multiply the square root by its outer coefficient.", eq=[f"{k} * {a}", str(k * a)]),
            S(f"{k * a} + {b} = {ans}", "Add the two results.", val=str(ans), eq=[f"{k * a} + {b}", str(ans)]),
        ]
    else:
        c = rng.choice([4, 5, 9, 10])
        ans = a * a_mul if (a_mul := k) else 0
        ans = k * a - c
        trap = (a * a // 2) - c
        prompt = f"Evaluate the radical expression ${k}\\sqrt{{{a*a}}} - \\sqrt{{{c*c}}}$."
        disp = f"{k}\\sqrt{{{a*a}}} - \\sqrt{{{c*c}}}"
        steps = [
            S(f"\\sqrt{{{a*a}}} = {a}, \\quad \\sqrt{{{c*c}}} = {c}", "Take the principal square root of each perfect square.", eq=[f"sqrt({a*a})", str(a)]),
            S(f"{k}\\sqrt{{{a*a}}} = {k}({a}) = {k * a}", "Multiply the first root by its coefficient.", eq=[f"{k} * {a}", str(k * a)]),
            S(f"{k * a} - {c} = {ans}", "Subtract the second root.", val=str(ans), eq=[f"{k * a} - {c}", str(ans)]),
        ]
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Roots: Principal Square and Cube Roots",
        "references": ["MTH-T01-C09-U01"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{k}*sqrt({a*a}) op root({b})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Evaluate each principal root first, then perform the multiplication and addition or subtraction.",
        "commonTrapTag": "c09-root-halving-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c09_reverse(rng, form=None):
    if form not in ("direct", "radical-equation"):
        form = rng.choice(["direct", "radical-equation"])
    a = rng.choice([2, 3, 4, 5])
    x = rng.randint(6, 18)
    r = rng.randint(5, 11)
    b = r * r - a * x
    ans = x
    trap = (2 * r - b) // a if (2 * r - b) != r * r - b else x + 4
    if trap == ans:
        trap = ans + 5
    b_sign = "+" if b >= 0 else "-"
    b_abs = abs(b)
    if form == "radical-equation":
        prompt = f"Solve the radical equation for $x$: $\\sqrt{{{a}x {b_sign} {b_abs}}} = {r}$."
        disp = f"\\sqrt{{{a}x {b_sign} {b_abs}}} = {r} \\implies x = ?"
    else:
        prompt = f"Find the real number $x$ such that the principal square root of ${a}x {b_sign} {b_abs}$ equals ${r}$."
        disp = f"\\sqrt{{{a}x {b_sign} {b_abs}}} = {r}"
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Roots: Solving Radical Equations",
        "references": ["MTH-T01-C09-U06"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"sqrt({a}*x {b_sign} {b_abs}) = {r}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Square both sides of the equation to eliminate the radical, then solve the resulting linear equation.",
        "commonTrapTag": "c09-radical-equation-unsquared-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(f"{a}x {b_sign} {b_abs} = {r}^2 = {r * r}", "Square both sides of the equation.", eq=[f"{r}**2", str(r * r)]),
            S(f"{a}x = {r * r - b}", "Isolate the variable term on the left-hand side.", eq=[f"{r * r} - ({b})", str(a * x)]),
            S(f"x = \\frac{{{a * x}}}{{{a}}} = {ans}", "Divide by the coefficient to find $x$.", val=str(ans), eq=[f"({a * x}) / {a}", str(ans)]),
        ],
    }


def t_c09_trap(rng, form=None):
    if form not in ("direct", "quotient-radical"):
        form = rng.choice(["direct", "quotient-radical"])
    triples = [(6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15), (12, 16, 20), (7, 24, 25)]
    a, b, c = rng.choice(triples)
    if form == "quotient-radical":
        k = rng.choice([2, 3, 5])
        ans = k * c
        trap = k * (a + b)
        prompt = f"Evaluate the exact value of $\\sqrt{{{k*k*a*a} + {k*k*b*b}}}$."
        disp = f"\\sqrt{{{k*k*a*a} + {k*k*b*b}}}"
        steps = [
            S(f"{k*k*a*a} + {k*k*b*b} = {(k*c)**2}", "Add the two numbers inside the radicand first before taking the square root.", eq=[f"{k*k*a*a} + {k*k*b*b}", str((k * c) ** 2)]),
            S(f"\\sqrt{{{(k*c)**2}}} = {k * c}", "Take the principal square root of the combined sum.", eq=[f"sqrt({(k*c)**2})", str(ans)]),
            S(f"= {ans}", "Note that the square root of a sum is strictly less than the sum of the individual square roots.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        ans = (a + b) - c
        trap = 0
        prompt = f"Compute the exact difference $(\\sqrt{{{a*a}}} + \\sqrt{{{b*b}}}) - \\sqrt{{{a*a} + {b*b}}}$."
        disp = f"(\\sqrt{{{a*a}}} + \\sqrt{{{b*b}}}) - \\sqrt{{{a*a} + {b*b}}}"
        steps = [
            S(f"\\sqrt{{{a*a}}} + \\sqrt{{{b*b}}} = {a} + {b} = {a + b}", "Evaluate the sum of the separate square roots.", eq=[f"sqrt({a*a}) + sqrt({b*b})", str(a + b)]),
            S(f"\\sqrt{{{a*a} + {b*b}}} = \\sqrt{{{c*c}}} = {c}", "Add the terms under the second radical before taking the square root.", eq=[f"sqrt({a*a} + {b*b})", str(c)]),
            S(f"{a + b} - {c} = {ans}", "Subtract the two values to see the non-zero discrepancy.", val=str(ans), eq=[f"{a + b} - {c}", str(ans)]),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Roots: Non-Distributivity of Radicals Over Addition",
        "references": ["MTH-T01-C09-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"sqrt({a*a} + {b*b}) vs {a} + {b}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Always evaluate the sum underneath the radical symbol first before taking the principal square root.",
        "commonTrapTag": "c09-root-sum-distribution-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c09_synthesis(rng, form=None):
    if form not in ("direct", "radical-conjugate"):
        form = rng.choice(["direct", "radical-conjugate"])
    if form == "radical-conjugate":
        a = rng.randint(5, 11)
        b = rng.choice([2, 3, 5, 6, 7])
        k = rng.randint(2, 4)
        diff_sq = a * a - k * k * b
        mult = rng.randint(2, 5)
        num_val = mult * abs(diff_sq)
        ans = mult if diff_sq > 0 else -mult
        trap = a + k * b
        prompt = f"Evaluate the product $({a} - {k}\\sqrt{{{b}}})({a} + {k}\\sqrt{{{b}}})$ and multiply the result by ${mult}$."
        disp = f"{mult}({a} - {k}\\sqrt{{{b}}})({a} + {k}\\sqrt{{{b}}})"
        ans = mult * diff_sq
        steps = [
            S(f"({a} - {k}\\sqrt{{{b}}})({a} + {k}\\sqrt{{{b}}}) = {a}^2 - ({k}\\sqrt{{{b}}})^2", "Apply the difference of squares identity $(u - v)(u + v) = u^2 - v^2$.", eq=[f"{a}**2 - ({k}**2)*{b}", str(diff_sq)]),
            S(f"= {a * a} - {k * k * b} = {diff_sq}", "Evaluate both squared terms so the radical cancels cleanly.", eq=[f"{a * a} - {k * k * b}", str(diff_sq)]),
            S(f"{mult} \\times ({diff_sq}) = {ans}", "Multiply by the outer integer factor.", val=str(ans), eq=[f"{mult} * ({diff_sq})", str(ans)]),
        ]
    else:
        cases = [
            (21, 12, 16, 4, 16, 4, 25, 5, 5, 8),
            (32, 13, 9, 3, 16, 4, 36, 6, 6, 9),
            (45, 11, 25, 5, 16, 4, 49, 7, 7, 11),
            (60, 12, 16, 4, 16, 4, 64, 8, 8, 12),
            (77, 10, 36, 6, 16, 4, 81, 9, 9, 13),
        ]
        c_out, c_mid, c_in, r_in, s_mid, r_mid, s_out, ans, _, trap = rng.choice(cases)
        prompt = f"Evaluate the nested radical expression $\\sqrt{{{c_out} + \\sqrt{{{c_mid} + \\sqrt{{{c_in}}}}}}}$."
        disp = f"\\sqrt{{{c_out} + \\sqrt{{{c_mid} + \\sqrt{{{c_in}}}}}}}"
        steps = [
            S(f"\\sqrt{{{c_in}}} = {r_in} \\implies {c_mid} + {r_in} = {s_mid}", "Evaluate the innermost square root first and add it to the middle radicand.", eq=[f"{c_mid} + sqrt({c_in})", str(s_mid)]),
            S(f"\\sqrt{{{s_mid}}} = {r_mid} \\implies {c_out} + {r_mid} = {s_out}", "Evaluate the middle square root and add it to the outer radicand.", eq=[f"{c_out} + sqrt({s_mid})", str(s_out)]),
            S(f"\\sqrt{{{s_out}}} = {ans}", "Take the final outer square root.", val=str(ans), eq=[f"sqrt({s_out})", str(ans)]),
        ]
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Roots: Nested Radicals & Conjugate Synthesis",
        "references": ["MTH-T01-C09-U04", "MTH-T01-C09-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"nested radical synthesis {ans}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "For nested radicals, simplify from the innermost radical outward; for conjugate products, apply the difference of squares.",
        "commonTrapTag": "c09-nested-radical-evaluation-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


TEMPLATES = [
    {
        "key": "c09-perfect-square-cube-roots",
        "trapTag": "c09-root-halving-trap",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C09-ROOT-EVAL"},
            "combined": {"level": 1, "skill": "MTH-PREALG-C09-ROOT-EVAL"},
        },
        "build": t_c09_foundation,
    },
    {
        "key": "c09-simplify-like-radicals",
        "trapTag": "c09-radical-equation-unsquared-trap",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C09-RADICAL-EQ"},
            "radical-equation": {"level": 2, "skill": "MTH-PREALG-C09-RADICAL-EQ"},
        },
        "build": t_c09_reverse,
    },
    {
        "key": "c09-non-distributive-root-trap",
        "trapTag": "c09-root-sum-distribution-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C09-SUM-TRAP"},
            "quotient-radical": {"level": 3, "skill": "MTH-PREALG-C09-SUM-TRAP"},
        },
        "build": t_c09_trap,
    },
    {
        "key": "c09-nested-radical-geometric-synthesis",
        "trapTag": "c09-nested-radical-evaluation-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C09-SYNTHESIS"},
            "radical-conjugate": {"level": 4, "skill": "MTH-PREALG-C09-SYNTHESIS"},
        },
        "build": t_c09_synthesis,
    },
]
