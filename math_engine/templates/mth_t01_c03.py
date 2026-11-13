# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C03: Integers."""

from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C03"
TITLE = "Integers"

MISTAKE_TAGS = [
    {
        "id": "c03-double-negative-slip",
        "label": "Failed to convert subtracting a negative into addition",
        "name": "Double Negative Subtraction Slip",
        "autoFrom": ["whole_sign_flip"],
    },
    {
        "id": "c03-signed-division-sign-error",
        "label": "Lost negative sign when dividing integers of opposite signs",
        "name": "Signed Division Sign Error",
        "autoFrom": ["whole_sign_flip"],
    },
    {
        "id": "c03-negated-square-precedence-trap",
        "label": "Evaluated -a^2 as (-a)^2 instead of -(a^2)",
        "name": "Negated Power Precedence Trap",
        "autoFrom": ["whole_sign_flip"],
    },
    {
        "id": "c03-net-integer-change-trap",
        "label": "Reversed directional signs in multi-stage integer change",
        "name": "Directional Integer Sign Trap",
        "autoFrom": [],
    },
]


def t_c03_foundation(rng, form=None):
    if form not in ("direct", "elevation"):
        form = rng.choice(["direct", "elevation"])
    a = rng.randint(15, 45)
    b = rng.randint(12, 38)
    c = rng.randint(8, 25)
    ans = -a + b + c
    trap = -a + b - c
    if form == "elevation":
        prompt = f"A submersible is at an elevation of $-{a}$ meters relative to sea level. It ascends ${b}$ meters and then ascends another ${c}$ meters. What is its new elevation in meters?"
        disp = f"-{a} + {b} + {c}"
    else:
        prompt = f"Evaluate the signed integer expression $-{a} + {b} - (-{c})$."
        disp = f"-{a} + {b} - (-{c})"
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Integers: Signed Addition and Subtraction",
        "references": ["MTH-T01-C03-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"(0 - {a}) + {b} + {c}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact signed integer value",
        "checkpointHint": "Rewrite subtracting a negative as adding a positive, then combine the signed integers from left to right.",
        "commonTrapTag": "c03-double-negative-slip",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(f"-{a} + {b} = {-a + b}", "Combine the first two signed integers.", eq=[f"-{a} + {b}", str(-a + b)]),
            S(
                f"{-a + b} + {c}",
                "Add the positive increment to the intermediate result.",
                eq=[f"{-a + b} + {c}", str(ans)],
            ),
            S(f"= {ans}", "Simplify to obtain the final signed integer.", val=str(ans), eq=[str(ans), str(ans)]),
        ],
    }


def t_c03_reverse(rng, form=None):
    if form not in ("direct", "reverse"):
        form = rng.choice(["direct", "reverse"])
    a = rng.randint(4, 11)
    x = -rng.randint(5, 16)
    b = rng.randint(7, 24)
    rhs = -a * x + b
    ans = x
    trap = -x
    if form == "reverse":
        prompt = f"Find the integer $x$ that satisfies the equation $-{a}x + {b} = {rhs}$."
        disp = f"-{a}x + {b} = {rhs} \\implies x = ?"
    else:
        prompt = f"Solve the integer equation $-{a}x + {b} = {rhs}$ for $x$."
        disp = f"-{a}x + {b} = {rhs}"
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Integers: Signed Multiplication & Division Equations",
        "references": ["MTH-T01-C03-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"(0 - {a})*x + {b} = {rhs}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact signed integer value",
        "checkpointHint": "Subtract the constant from both sides first, then divide by the negative coefficient, paying close attention to the sign of the quotient.",
        "commonTrapTag": "c03-signed-division-sign-error",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(
                f"-{a}x = {rhs} - {b} = {rhs - b}",
                "Subtract the constant term from both sides.",
                eq=[f"{rhs} - {b}", str(rhs - b)],
            ),
            S(
                f"x = \\frac{{{rhs - b}}}{{-{a}}}",
                "Divide both sides by the negative coefficient.",
                eq=[f"({rhs - b}) / (-{a})", str(ans)],
            ),
            S(
                f"x = {ans}",
                "A positive integer divided by a negative integer yields a negative quotient.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ],
    }


def t_c03_trap(rng, form=None):
    if form not in ("direct", "nested-abs"):
        form = rng.choice(["direct", "nested-abs"])
    a = rng.randint(3, 8)
    b = rng.randint(2, 6)
    c = rng.randint(4, 12)
    if form == "nested-abs":
        ans = -(a * a) + abs(-b * c)
        trap = (a * a) + abs(-b * c)
        prompt = f"Evaluate the integer expression $-{a}^2 + |(-{b})({c})|$."
        disp = f"-{a}^2 + |(-{b})({c})|"
        steps = [
            S(
                f"-{a}^2 = -({a}^2) = -{a * a}",
                "Exponentiation binds tighter than unary negation, so square first and then negate.",
                eq=[f"-({a}**2)", str(-(a * a))],
            ),
            S(
                f"|(-{b})({c})| = |-{b * c}| = {b * c}",
                "Evaluate the product inside the absolute value bars and take its non-negative magnitude.",
                eq=[f"abs((-{b})*{c})", str(b * c)],
            ),
            S(
                f"-{a * a} + {b * c} = {ans}",
                "Add the two results to find the exact value.",
                val=str(ans),
                eq=[f"-({a * a}) + {b * c}", str(ans)],
            ),
        ]
    else:
        ans = -(a * a) - (-b) * (-b)
        trap = (a * a) - (-b) * (-b)
        prompt = f"Evaluate the integer expression $-{a}^2 - (-{b})^2$."
        disp = f"-{a}^2 - (-{b})^2"
        steps = [
            S(
                f"-{a}^2 = -({a * a}) = -{a * a}",
                "Without parentheses around the negative sign, the exponent applies only to the base integer.",
                eq=[f"-({a}**2)", str(-(a * a))],
            ),
            S(
                f"(-{b})^2 = (-{b})(-{b}) = {b * b}",
                "With parentheses, the negative base is squared to produce a positive integer.",
                eq=[f"(-{b})**2", str(b * b)],
            ),
            S(
                f"-{a * a} - {b * b} = {ans}",
                "Subtract the second square from the negated first square.",
                val=str(ans),
                eq=[f"-({a * a}) - ({b * b})", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Integers: Negated Power Precedence Trap",
        "references": ["MTH-T01-C03-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"(0 - {a}^2) and ({b}^2)",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact signed integer value",
        "checkpointHint": "Distinguish carefully between an unparenthesized negated power and a parenthesized negative base squared.",
        "commonTrapTag": "c03-negated-square-precedence-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c03_synthesis(rng, form=None):
    if form not in ("direct", "contextual"):
        form = rng.choice(["direct", "contextual"])
    t0 = rng.randint(10, 28)
    drop_rate = rng.randint(4, 9)
    hrs_drop = rng.randint(5, 9)
    rise_rate = rng.randint(3, 7)
    hrs_rise = rng.randint(2, 5)
    ans = t0 - drop_rate * hrs_drop + rise_rate * hrs_rise
    trap = t0 + drop_rate * hrs_drop - rise_rate * hrs_rise
    if form == "contextual":
        prompt = f"A high-altitude weather probe starts at ${t0}^\\circ\\text{{C}}$. Its temperature changes by $-{drop_rate}^\\circ\\text{{C}}$ per hour for ${hrs_drop}$ hours during ascent, and then changes by $+{rise_rate}^\\circ\\text{{C}}$ per hour for ${hrs_rise}$ hours. What is the final temperature in degrees Celsius?"
        disp = f"T = {t0} + ({hrs_drop})(-{drop_rate}) + ({hrs_rise})({rise_rate})"
    else:
        prompt = f"A deep-sea drilling rig starts at an elevation of ${t0}$ meters above a reference datum, descends at ${drop_rate}$ meters per minute for ${hrs_drop}$ minutes, and then ascends at ${rise_rate}$ meters per minute for ${hrs_rise}$ minutes. Find its final elevation relative to the datum."
        disp = f"E = {t0} - {drop_rate}({hrs_drop}) + {rise_rate}({hrs_rise})"
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Integers: Multi-Stage Signed Rate Synthesis",
        "references": ["MTH-T01-C03-U03", "MTH-T01-C03-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{t0} - {drop_rate}*{hrs_drop} + {rise_rate}*{hrs_rise}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact signed integer value",
        "checkpointHint": "Multiply each signed rate of change by its duration, then add the net changes to the initial value.",
        "commonTrapTag": "c03-net-integer-change-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(
                f"\\Delta_1 = ({hrs_drop})(-{drop_rate}) = -{drop_rate * hrs_drop}",
                "Compute the signed change during the first phase.",
                eq=[f"({hrs_drop}) * (-{drop_rate})", str(-(drop_rate * hrs_drop))],
            ),
            S(
                f"\\Delta_2 = ({hrs_rise})({rise_rate}) = {rise_rate * hrs_rise}",
                "Compute the signed change during the second phase.",
                eq=[f"({hrs_rise}) * ({rise_rate})", str(rise_rate * hrs_rise)],
            ),
            S(
                f"\\text{{Final}} = {t0} - {drop_rate * hrs_drop} + {rise_rate * hrs_rise} = {ans}",
                "Combine the initial value with both net changes.",
                val=str(ans),
                eq=[f"{t0} - {drop_rate * hrs_drop} + {rise_rate * hrs_rise}", str(ans)],
            ),
        ],
    }


TEMPLATES = [
    {
        "key": "c03-abs-value-integer-add",
        "trapTag": "c03-double-negative-slip",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C03-ADD-SUB"},
            "elevation": {"level": 1, "skill": "MTH-PREALG-C03-ADD-SUB"},
        },
        "build": t_c03_foundation,
    },
    {
        "key": "c03-signed-mult-div-equations",
        "trapTag": "c03-signed-division-sign-error",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C03-MULT-DIV"},
            "reverse": {"level": 2, "skill": "MTH-PREALG-C03-MULT-DIV"},
        },
        "build": t_c03_reverse,
    },
    {
        "key": "c03-negated-power-order-trap",
        "trapTag": "c03-negated-square-precedence-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C03-POWER-TRAP"},
            "nested-abs": {"level": 3, "skill": "MTH-PREALG-C03-POWER-TRAP"},
        },
        "build": t_c03_trap,
    },
    {
        "key": "c03-thermal-depth-integer-synthesis",
        "trapTag": "c03-net-integer-change-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C03-SYNTHESIS"},
            "contextual": {"level": 4, "skill": "MTH-PREALG-C03-SYNTHESIS"},
        },
        "build": t_c03_synthesis,
    },
]
