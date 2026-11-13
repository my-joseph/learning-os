# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C02: The Language of Algebra."""

import math

from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C02"
TITLE = "The Language of Algebra"

MISTAKE_TAGS = [
    {
        "id": "c02-substitution-precedence",
        "label": "Added before multiplying when evaluating algebraic expression",
        "name": "Algebraic Evaluation Precedence Slip",
        "autoFrom": [],
    },
    {
        "id": "c02-translation-subtraction-order",
        "label": "Reversed order of 'a less than b' during equation translation",
        "name": "Subtraction Translation Order Reversal",
        "autoFrom": [],
    },
    {
        "id": "c02-lcm-gcd-exponent-trap",
        "label": "Took minimum prime exponents (GCD) instead of maximum prime exponents (LCM)",
        "name": "LCM vs GCD Prime Exponent Trap",
        "autoFrom": [],
    },
    {
        "id": "c02-synodic-offset-trap",
        "label": "Forgot initial offset when computing next simultaneous cycle occurrence",
        "name": "Simultaneous Cycle Offset Omission",
        "autoFrom": [],
    },
]


def t_c02_foundation(rng, form=None):
    if form not in ("direct", "nested"):
        form = rng.choice(["direct", "nested"])
    a = rng.randint(3, 8)
    x = rng.randint(4, 11)
    b = rng.randint(2, 7)
    y = rng.randint(3, 9)
    if form == "nested":
        c = rng.randint(4, 15)
        ans = a * (x + y) - c
        trap = a * x + y - c
        prompt = f"Evaluate the algebraic expression ${a}(x + y) - {c}$ when $x = {x}$ and $y = {y}$."
        disp = f"{a}({x} + {y}) - {c}"
        steps = [
            S(
                f"x + y = {x} + {y} = {x + y}",
                "Substitute the given values and evaluate the parentheses first.",
                eq=[f"{x} + {y}", str(x + y)],
            ),
            S(
                f"{a}({x + y}) = {a * (x + y)}",
                "Multiply the sum by the outer coefficient.",
                eq=[f"{a} * ({x + y})", str(a * (x + y))],
            ),
            S(
                f"{a * (x + y)} - {c} = {ans}",
                "Subtract the constant term.",
                val=str(ans),
                eq=[f"{a * (x + y)} - {c}", str(ans)],
            ),
        ]
    else:
        ans = a * x + b * y
        trap = (a + b) * (x + y)
        prompt = f"Evaluate the algebraic expression ${a}x + {b}y$ when $x = {x}$ and $y = {y}$."
        disp = f"{a}({x}) + {b}({y})"
        steps = [
            S(f"{a}x = {a}({x}) = {a * x}", "Evaluate the first product term.", eq=[f"{a} * {x}", str(a * x)]),
            S(f"{b}y = {b}({y}) = {b * y}", "Evaluate the second product term.", eq=[f"{b} * {y}", str(b * y)]),
            S(
                f"{a * x} + {b * y} = {ans}",
                "Add the two products together.",
                val=str(ans),
                eq=[f"{a * x} + {b * y}", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Language of Algebra: Expression Evaluation",
        "references": ["MTH-T01-C02-U02"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{a}*x + {b}*y at ({x},{y})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Substitute each variable with its assigned value and follow the order of operations.",
        "commonTrapTag": "c02-substitution-precedence",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c02_reverse(rng, form=None):
    if form not in ("direct", "reverse"):
        form = rng.choice(["direct", "reverse"])
    while True:
        k = rng.randint(3, 9)
        m = rng.randint(11, 35)
        target = k * rng.randint(8, 22) - m
        while target <= m:
            target = k * rng.randint(12, 28) - m
        ans = (target + m) // k
        trap = target - m
        if trap != ans:
            break
    if form == "reverse":
        prompt = (
            f"When ${m}$ is subtracted from ${k}$ times a number $n$, the result is ${target}$. Find the number $n$."
        )
        disp = f"{k}n - {m} = {target} \\implies n = ?"
    else:
        prompt = f"Translate and solve for $n$: '${m}$ less than the product of ${k}$ and $n$ equals ${target}$'."
        disp = f"{k}n - {m} = {target}"
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Language of Algebra: Verbal Translation & Solution",
        "references": ["MTH-T01-C02-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{k}*n - {m} = {target}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Translate 'a less than b' as b - a, add the constant to both sides, and divide by the coefficient.",
        "commonTrapTag": "c02-translation-subtraction-order",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(
                f"{k}n - {m} = {target}",
                "Write the algebraic equation from the verbal statement.",
                eq=[f"{k}*{ans} - {m}", str(target)],
            ),
            S(
                f"{k}n = {target} + {m} = {target + m}",
                "Add the subtracted constant to both sides of the equation.",
                eq=[f"{target} + {m}", str(target + m)],
            ),
            S(
                f"n = \\frac{{{target + m}}}{{{k}}} = {ans}",
                "Divide by the coefficient to isolate the unknown.",
                val=str(ans),
                eq=[f"({target + m}) / {k}", str(ans)],
            ),
        ],
    }


def t_c02_trap(rng, form=None):
    if form not in ("direct", "synodic-cycle"):
        form = rng.choice(["direct", "synodic-cycle"])
    pairs = [
        (12, 18, "2^2 \\cdot 3", "2 \\cdot 3^2"),
        (24, 36, "2^3 \\cdot 3", "2^2 \\cdot 3^2"),
        (18, 30, "2 \\cdot 3^2", "2 \\cdot 3 \\cdot 5"),
        (20, 28, "2^2 \\cdot 5", "2^2 \\cdot 7"),
        (16, 24, "2^4", "2^3 \\cdot 3"),
        (15, 25, "3 \\cdot 5", "5^2"),
    ]
    a, b, pf_a, pf_b = rng.choice(pairs)
    g = math.gcd(a, b)
    lcm_val = (a * b) // g
    if form == "synodic-cycle":
        offset = rng.randint(2, 9)
        ans = lcm_val + offset
        trap = g + offset
        prompt = f"Two automated beacons flash every ${a}$ minutes and ${b}$ minutes, respectively. Both beacons flashed together at $t = {offset}$ minutes past the hour. At what time $t$ (in minutes past the hour) will they next flash simultaneously?"
        disp = f"t = {offset} + \\text{{LCM}}({a}, {b})"
        steps = [
            S(
                f"{a} = {pf_a}, \\quad {b} = {pf_b}",
                "Find the prime factorization of each period.",
                eq=[f"({a} * {b}) / {g}", str(lcm_val)],
            ),
            S(
                f"\\text{{LCM}}({a}, {b}) = {lcm_val}",
                "Take the highest power of each prime factor to obtain the least common multiple.",
                eq=[str(lcm_val), str(lcm_val)],
            ),
            S(
                f"t = {offset} + {lcm_val} = {ans}",
                "Add the period LCM to the initial synchronization time.",
                val=str(ans),
                eq=[f"{offset} + {lcm_val}", str(ans)],
            ),
        ]
    else:
        ans = lcm_val
        trap = g
        prompt = f"Using prime factorization, find the Least Common Multiple (LCM) of ${a}$ and ${b}$."
        disp = f"\\text{{LCM}}({a}, {b}) = ?"
        steps = [
            S(
                f"{a} = {pf_a}, \\quad {b} = {pf_b}",
                "Express both integers in prime-factored form.",
                eq=[f"{a} * {b}", str(a * b)],
            ),
            S(
                f"\\text{{GCD}}({a}, {b}) = {g}",
                "Identify the greatest common divisor from shared prime factors.",
                eq=[str(g), str(g)],
            ),
            S(
                f"\\text{{LCM}}({a}, {b}) = \\frac{{{a} \\times {b}}}{{{g}}} = {ans}",
                "Take the highest exponent of each prime factor to compute the LCM.",
                val=str(ans),
                eq=[f"({a} * {b}) / {g}", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Language of Algebra: Prime Factorization & LCM Trap",
        "references": ["MTH-T01-C02-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"LCM({a}, {b})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "For the least common multiple, select the highest power of each prime factor present in either number rather than the lowest power.",
        "commonTrapTag": "c02-lcm-gcd-exponent-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c02_synthesis(rng, form=None):
    if form not in ("direct", "multi-constraint"):
        form = rng.choice(["direct", "multi-constraint"])
    pairs = [(8, 12), (10, 15), (12, 18), (14, 21), (16, 24)]
    a, b = rng.choice(pairs)
    g = math.gcd(a, b)
    L = (a * b) // g
    k = rng.randint(2, 5)
    c = rng.randint(3, 9)
    if form == "multi-constraint":
        ans = k * L - c * g
        trap = k * g + c * L
        prompt = f"Let $L = \\text{{LCM}}({a}, {b})$ and $G = \\text{{GCD}}({a}, {b})$. Evaluate the algebraic expression ${k}L - {c}G$."
        disp = f"{k}\\,\\text{{LCM}}({a}, {b}) - {c}\\,\\text{{GCD}}({a}, {b})"
        steps = [
            S(
                f"L = \\text{{LCM}}({a}, {b}) = {L}, \\quad G = \\text{{GCD}}({a}, {b}) = {g}",
                "Compute both the least common multiple and greatest common divisor.",
                eq=[f"({a}*{b})/{g}", str(L)],
            ),
            S(
                f"{k}L = {k * L}, \\quad {c}G = {c * g}",
                "Substitute $L$ and $G$ into their respective terms.",
                eq=[f"{k}*{L} - {c}*{g}", str(ans)],
            ),
            S(
                f"{k * L} - {c * g} = {ans}",
                "Subtract to obtain the final value.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ]
    else:
        ans = k * L + c * g
        trap = k * (a + b) + c * g
        prompt = f"Let $L = \\text{{LCM}}({a}, {b})$ and $G = \\text{{GCD}}({a}, {b})$. Evaluate the algebraic expression ${k}L + {c}G$."
        disp = f"{k}\\,\\text{{LCM}}({a}, {b}) + {c}\\,\\text{{GCD}}({a}, {b})"
        steps = [
            S(
                f"L = \\text{{LCM}}({a}, {b}) = {L}, \\quad G = \\text{{GCD}}({a}, {b}) = {g}",
                "Find the LCM and GCD of the two integers.",
                eq=[f"({a}*{b})/{g}", str(L)],
            ),
            S(
                f"{k}L = {k * L}, \\quad {c}G = {c * g}",
                "Multiply each quantity by its algebraic coefficient.",
                eq=[f"{k}*{L} + {c}*{g}", str(ans)],
            ),
            S(f"{k * L} + {c * g} = {ans}", "Add the two products together.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Language of Algebra: LCM/GCD Algebraic Synthesis",
        "references": ["MTH-T01-C02-U02", "MTH-T01-C02-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{k}*LCM({a},{b}) + {c}*GCD({a},{b})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Determine the LCM and GCD of the pair first, then substitute those values into the linear expression.",
        "commonTrapTag": "c02-lcm-gcd-exponent-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


TEMPLATES = [
    {
        "key": "c02-evaluate-expression",
        "trapTag": "c02-substitution-precedence",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C02-EVAL"},
            "nested": {"level": 1, "skill": "MTH-PREALG-C02-EVAL"},
        },
        "build": t_c02_foundation,
    },
    {
        "key": "c02-translate-and-solve-one-step",
        "trapTag": "c02-translation-subtraction-order",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C02-TRANSLATE"},
            "reverse": {"level": 2, "skill": "MTH-PREALG-C02-TRANSLATE"},
        },
        "build": t_c02_reverse,
    },
    {
        "key": "c02-lcm-gcd-prime-trap",
        "trapTag": "c02-lcm-gcd-exponent-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C02-LCM-TRAP"},
            "synodic-cycle": {"level": 3, "skill": "MTH-PREALG-C02-LCM-TRAP"},
        },
        "build": t_c02_trap,
    },
    {
        "key": "c02-algebraic-divisibility-synthesis",
        "trapTag": "c02-lcm-gcd-exponent-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C02-SYNTHESIS"},
            "multi-constraint": {"level": 4, "skill": "MTH-PREALG-C02-SYNTHESIS"},
        },
        "build": t_c02_synthesis,
    },
]
