# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C11: Solving Linear Equations."""
from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C11"
TITLE = "Solving Linear Equations"

MISTAKE_TAGS = [
    {"id": "c11-constant-transposition-sign", "label": "Added instead of subtracted constant when transposing across equals sign", "name": "Constant Transposition Sign Slip", "autoFrom": ["whole_sign_flip"]},
    {"id": "c11-variable-grouping-sign-slip", "label": "Combined variable terms across equals sign with wrong sign", "name": "Variable Transposition Sign Slip", "autoFrom": ["whole_sign_flip"]},
    {"id": "c11-fraction-numerator-sign-trap", "label": "Failed to distribute subtraction sign across entire second numerator when clearing fractions", "name": "Fractional Numerator Subtraction Trap", "autoFrom": ["whole_sign_flip"]},
    {"id": "c11-consecutive-parity-step-trap", "label": "Used x+1, x+2 instead of x+2, x+4 for consecutive even/odd integers", "name": "Consecutive Parity Step Trap", "autoFrom": []},
]



def t_c11_foundation(rng, form=None):
    if form not in ("direct", "negative-coeff"):
        form = rng.choice(["direct", "negative-coeff"])
    a = rng.randint(4, 11)
    x = rng.randint(5, 16)
    b = rng.randint(7, 29)
    if form == "negative-coeff":
        rhs = b - a * x
        ans = x
        trap = -x
        prompt = f"Solve the linear equation for $x$: ${b} - {a}x = {rhs}$."
        disp = f"{b} - {a}x = {rhs}"
        steps = [
            S(f"-{a}x = {rhs} - {b} = {rhs - b}", "Subtract the constant term from both sides.", eq=[f"{rhs} - {b}", str(-a * x)]),
            S(f"x = \\frac{{{rhs - b}}}{{-{a}}}", "Divide both sides by the negative coefficient.", eq=[f"({rhs - b}) / (-{a})", str(ans)]),
            S(f"x = {ans}", "Simplify the quotient of two negative integers.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        rhs = a * x + b
        ans = x
        trap = (rhs + b) // a if (rhs + b) // a != x else x + 3
        prompt = f"Solve the two-step linear equation for $x$: ${a}x + {b} = {rhs}$."
        disp = f"{a}x + {b} = {rhs}"
        steps = [
            S(f"{a}x = {rhs} - {b} = {rhs - b}", "Subtract the constant from both sides.", eq=[f"{rhs} - {b}", str(a * x)]),
            S(f"x = \\frac{{{rhs - b}}}{{{a}}}", "Divide both sides by the coefficient of $x$.", eq=[f"({rhs - b}) / {a}", str(ans)]),
            S(f"x = {ans}", "State the exact integer solution.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Linear Equations: Two-Step Equations",
        "references": ["MTH-T01-C11-U02"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{a}*x and {b} = {rhs}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Isolate the variable term by undoing addition or subtraction first, then divide by the coefficient.",
        "commonTrapTag": "c11-constant-transposition-sign",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c11_reverse(rng, form=None):
    if form not in ("direct", "grouped"):
        form = rng.choice(["direct", "grouped"])
    x = rng.randint(4, 14)
    a = rng.randint(6, 12)
    c = rng.randint(2, a - 2)
    b = rng.randint(3, 15)
    if form == "grouped":
        k = rng.randint(2, 5)
        d = (a * (x + k)) - c * x
        ans = x
        trap = (d - k) // (a - c) if (d - k) // (a - c) != x else x + 2
        prompt = f"Solve for $x$: ${a}(x + {k}) = {c}x + {d}$."
        disp = f"{a}(x + {k}) = {c}x + {d}"
        steps = [
            S(f"{a}x + {a * k} = {c}x + {d}", "Expand the left-hand side using the distributive property.", eq=[f"{a}*({ans} + {k})", f"{c}*{ans} + {d}"]),
            S(f"{a - c}x = {d} - {a * k} = {d - a * k}", "Collect variable terms on the left and constant terms on the right.", eq=[f"{d} - {a * k}", str((a - c) * ans)]),
            S(f"x = \\frac{{{d - a * k}}}{{{a - c}}} = {ans}", "Divide by the net coefficient of $x$.", val=str(ans), eq=[f"({d - a * k}) / ({a - c})", str(ans)]),
        ]
    else:
        d = (a - c) * x + b
        ans = x
        trap = (d - b) // (a + c) if (d - b) // (a + c) != x else x + 3
        prompt = f"Solve the equation with variables on both sides: ${a}x + {b} = {c}x + {d}$."
        disp = f"{a}x + {b} = {c}x + {d}"
        steps = [
            S(f"{a}x - {c}x + {b} = {d} \\implies {a - c}x + {b} = {d}", "Subtract the right-hand variable term from both sides.", eq=[f"{a} - {c}", str(a - c)]),
            S(f"{a - c}x = {d} - {b} = {d - b}", "Subtract the left-hand constant from both sides.", eq=[f"{d} - {b}", str((a - c) * ans)]),
            S(f"x = \\frac{{{d - b}}}{{{a - c}}} = {ans}", "Divide by the combined coefficient.", val=str(ans), eq=[f"({d - b}) / ({a - c})", str(ans)]),
        ]
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Linear Equations: Variables on Both Sides",
        "references": ["MTH-T01-C11-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{a}*x + {b} = {c}*x + {d}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Expand any parentheses first, gather all variable terms on one side and constants on the other, and divide.",
        "commonTrapTag": "c11-variable-grouping-sign-slip",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c11_trap(rng, form=None):
    if form not in ("direct", "unscaled-constant-trap"):
        form = rng.choice(["direct", "unscaled-constant-trap"])
    cases = [
        (3, 5, 1, 2, 11, -9),
        (5, 3, 2, 3, 14, -4),
        (2, 6, 3, 4, 15, -9),
        (7, 4, 1, 3, 9, -7),
        (4, 9, 2, 5, 17, -19),
    ]
    a, c, k, m_mult, ans, trap = rng.choice(cases)
    ans = 6 * k - 3 * a - 2 * c
    trap = 6 * k - 3 * a + 2 * c
    if form == "unscaled-constant-trap":
        prompt = f"Solve the fractional linear equation by clearing denominators: $\\frac{{x + {a}}}{{2}} - \\frac{{x - {c}}}{{3}} = {k}$."
        disp = f"\\frac{{x + {a}}}{{2}} - \\frac{{x - {c}}}{{3}} = {k}"
    else:
        prompt = f"Find the exact solution $x$ to $\\frac{{x + {a}}}{{2}} - \\frac{{x - {c}}}{{3}} = {k}$."
        disp = f"\\frac{{x + {a}}}{{2}} - \\frac{{x - {c}}}{{3}} = {k} \\implies x = ?"
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Linear Equations: Fractional Numerator Sign Distribution Trap",
        "references": ["MTH-T01-C11-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"(x + {a})/2 - (x - {c})/3 = {k}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Multiply every term on both sides by the least common denominator, enclosing each numerator in parentheses before expanding.",
        "commonTrapTag": "c11-fraction-numerator-sign-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(f"6\\left(\\frac{{x + {a}}}{{2}}\\right) - 6\\left(\\frac{{x - {c}}}{{3}}\\right) = 6({k}) \\implies 3(x + {a}) - 2(x - {c}) = {6 * k}", "Multiply both sides by the least common denominator 6.", eq=[f"3*({ans} + {a}) - 2*({ans} - {c})", str(6 * k)]),
            S(f"3x + {3 * a} - 2x + {2 * c} = {6 * k}", "Distribute both factors carefully, noting that $-2(-c) = +2c$.", eq=[f"{ans} + {3 * a} + {2 * c}", str(6 * k)]),
            S(f"x = {6 * k} - {3 * a + 2 * c} = {ans}", "Combine like terms and isolate $x$.", val=str(ans), eq=[f"{6 * k} - ({3 * a + 2 * c})", str(ans)]),
        ],
    }


def t_c11_synthesis(rng, form=None):
    if form not in ("direct", "parametric-root"):
        form = rng.choice(["direct", "parametric-root"])
    if form == "parametric-root":
        x_root = rng.randint(3, 8)
        a = rng.randint(4, 9)
        b = rng.randint(5, 14)
        rhs = (a + 2) * x_root * x_root + b
        ans = a * x_root + b
        trap = a * x_root - b
        prompt = f"Suppose $x = {x_root}$ is the solution to the linear equation $k x - {b} = {a * x_root}$. Find the value of the parameter $k$."
        disp = f"k({x_root}) - {b} = {a * x_root} \\implies k = ?"
        ans = a + b
        x_root = 3
        rhs_val = a * 3
        tot_rhs = rhs_val + b * 3
        ans = a + b
        trap = a - b
        prompt = f"If $x = {x_root}$ is the solution to the parametric linear equation $k x - {b * x_root} = {rhs_val}$, find the exact value of the parameter $k$."
        disp = f"k({x_root}) - {b * x_root} = {rhs_val} \\implies k = ?"
        steps = [
            S(f"{x_root}k - {b * x_root} = {rhs_val}", f"Substitute the known solution $x = {x_root}$ into the equation.", eq=[f"{x_root}*{ans} - {b * x_root}", str(rhs_val)]),
            S(f"{x_root}k = {rhs_val} + {b * x_root} = {tot_rhs}", "Add the constant term to both sides.", eq=[f"{rhs_val} + {b * x_root}", str(tot_rhs)]),
            S(f"k = \\frac{{{tot_rhs}}}{{{x_root}}} = {ans}", "Divide by the coefficient of $k$.", val=str(ans), eq=[f"{tot_rhs} / {x_root}", str(ans)]),
        ]
    else:
        first_even = 2 * rng.randint(8, 22)
        second_even = first_even + 2
        third_even = first_even + 4
        w1, w2, w3 = 2, 3, 1
        rhs = w1 * first_even + w2 * second_even + w3 * third_even
        const_sum = w2 * 2 + w3 * 4
        w_sum = w1 + w2 + w3
        ans = third_even
        trap = first_even
        prompt = f"Three consecutive even integers $n,\\ n+2,\\ n+4$ satisfy the weighted linear equation ${w1}n + {w2}(n + 2) + (n + 4) = {rhs}$. Find the LARGEST of the three consecutive even integers."
        disp = f"{w1}n + {w2}(n + 2) + (n + 4) = {rhs} \\implies n + 4 = ?"
        steps = [
            S(f"{w1}n + {w2}n + {2 * w2} + n + 4 = {rhs} \\implies {w_sum}n + {const_sum} = {rhs}", "Expand and combine the variable terms and constants.", eq=[f"{w_sum}*{first_even} + {const_sum}", str(rhs)]),
            S(f"{w_sum}n = {rhs - const_sum} \\implies n = {first_even}", "Solve for the smallest even integer $n$.", eq=[f"({rhs} - {const_sum}) / {w_sum}", str(first_even)]),
            S(f"n + 4 = {first_even} + 4 = {ans}", "Add 4 to obtain the largest of the three consecutive even integers.", val=str(ans), eq=[f"{first_even} + 4", str(ans)]),
        ]
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Linear Equations: Multi-Condition & Parametric Synthesis",
        "references": ["MTH-T01-C11-U03", "MTH-T01-C11-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"linear synthesis {ans}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Set up the linear equation in terms of the unknown, solve for the base variable, and evaluate the requested target quantity.",
        "commonTrapTag": "c11-consecutive-parity-step-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


TEMPLATES = [
    {
        "key": "c11-two-step-linear-equation",
        "trapTag": "c11-constant-transposition-sign",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C11-TWO-STEP"},
            "negative-coeff": {"level": 1, "skill": "MTH-PREALG-C11-TWO-STEP"},
        },
        "build": t_c11_foundation,
    },
    {
        "key": "c11-variables-both-sides",
        "trapTag": "c11-variable-grouping-sign-slip",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C11-BOTH-SIDES"},
            "grouped": {"level": 2, "skill": "MTH-PREALG-C11-BOTH-SIDES"},
        },
        "build": t_c11_reverse,
    },
    {
        "key": "c11-fractional-equation-clearing-trap",
        "trapTag": "c11-fraction-numerator-sign-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C11-FRAC-CLEAR"},
            "unscaled-constant-trap": {"level": 3, "skill": "MTH-PREALG-C11-FRAC-CLEAR"},
        },
        "build": t_c11_trap,
    },
    {
        "key": "c11-parametric-consecutive-linear-synthesis",
        "trapTag": "c11-consecutive-parity-step-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C11-SYNTHESIS"},
            "parametric-root": {"level": 4, "skill": "MTH-PREALG-C11-SYNTHESIS"},
        },
        "build": t_c11_synthesis,
    },
]
