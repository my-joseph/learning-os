# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C08: Exponents."""

from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C08"
TITLE = "Exponents"

MISTAKE_TAGS = [
    {
        "id": "c08-exponent-product-multiply-trap",
        "label": "Multiplied exponents instead of adding when multiplying same base",
        "name": "Product Rule Exponent Multiplication Trap",
        "autoFrom": [],
    },
    {
        "id": "c08-power-of-product-unscaled-coeff",
        "label": "Forgot to raise numerical coefficient to outer exponent in (a*b)^n",
        "name": "Power of Product Coefficient Trap",
        "autoFrom": ["off_by_factor"],
    },
    {
        "id": "c08-same-base-sum-exponent-trap",
        "label": "Added exponents across addition (2^a + 2^a != 2^(2a))",
        "name": "Same-Base Addition Exponent Trap",
        "autoFrom": [],
    },
    {
        "id": "c08-common-base-conversion-trap",
        "label": "Failed to convert composite bases to a common prime base before equating exponents",
        "name": "Common Prime Base Conversion Trap",
        "autoFrom": [],
    },
]


def t_c08_foundation(rng, form=None):
    if form not in ("direct", "quotient"):
        form = rng.choice(["direct", "quotient"])
    base = rng.choice([2, 3, 5])
    m = rng.randint(3, 5)
    n = rng.randint(2, 4)
    p = m + n - rng.choice([2, 3])
    net_exp = m + n - p
    ans = base**net_exp
    trap = base ** (m * n - p)
    if trap == ans:
        trap = ans * base
    if form == "quotient":
        prompt = f"Evaluate the exponential quotient $\\frac{{{base}^{m} \\cdot {base}^{n}}}{{{base}^{p}}}$."
        disp = f"\\frac{{{base}^{m} \\cdot {base}^{n}}}{{{base}^{p}}}"
    else:
        prompt = f"Simplify and evaluate the exact integer value of $({base}^{m} \\cdot {base}^{n}) \\div {base}^{p}$."
        disp = f"({base}^{m} \\cdot {base}^{n}) \\div {base}^{p}"
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Exponents: Product and Quotient Properties",
        "references": ["MTH-T01-C08-U02"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"({base}^{m} * {base}^{n}) / {base}^{p}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Add the exponents when multiplying powers with the same base, then subtract the denominator's exponent.",
        "commonTrapTag": "c08-exponent-product-multiply-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(
                f"{base}^{m} \\cdot {base}^{n} = {base}^{{{m} + {n}}} = {base}^{{{m + n}}}",
                "Apply the product property of exponents in the numerator.",
                eq=[f"({base}**{m}) * ({base}**{n})", f"{base}**({m + n})"],
            ),
            S(
                f"\\frac{{{base}^{{{m + n}}}}}{{{base}^{p}}} = {base}^{{{m + n} - {p}}} = {base}^{{{net_exp}}}",
                "Apply the quotient property by subtracting exponents.",
                eq=[f"({base}**({m + n})) / ({base}**{p})", str(ans)],
            ),
            S(
                f"{base}^{{{net_exp}}} = {ans}",
                "Evaluate the power to get the exact integer.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ],
    }


def t_c08_reverse(rng, form=None):
    if form not in ("direct", "solve-exponent"):
        form = rng.choice(["direct", "solve-exponent"])
    base = rng.choice([2, 3, 5])
    a = rng.randint(2, 4)
    b = rng.randint(2, 3)
    c = rng.randint(2, 4)
    total_exp = a * b + c
    if form == "solve-exponent":
        ans = total_exp
        trap = a + b + c
        prompt = f"Find the integer exponent $k$ that satisfies $\\left({base}^{a}\\right)^{b} \\cdot {base}^{c} = {base}^k$."
        disp = f"\\left({base}^{a}\\right)^{b} \\cdot {base}^{c} = {base}^k \\implies k = ?"
        steps = [
            S(
                f"\\left({base}^{a}\\right)^{b} = {base}^{{{a} \\times {b}}} = {base}^{{{a * b}}}",
                "Use the power-of-a-power rule to multiply the exponents.",
                eq=[f"{a} * {b}", str(a * b)],
            ),
            S(
                f"{base}^{{{a * b}}} \\cdot {base}^{c} = {base}^{{{a * b} + {c}}} = {base}^{{{total_exp}}}",
                "Add the exponents of the common base.",
                eq=[f"{a * b} + {c}", str(ans)],
            ),
            S(f"k = {ans}", "Equate the exponents of the identical base.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        coeff = rng.choice([2, 3, 4])
        n_pow = rng.choice([2, 3])
        x_val = rng.choice([2, 3])
        ans = (coeff**n_pow) * (x_val ** (2 * n_pow))
        trap = coeff * (x_val ** (2 * n_pow))
        prompt = f"Evaluate the expression $({coeff}x^2)^{n_pow}$ when $x = {x_val}$."
        disp = f"({coeff}x^2)^{n_pow} \\quad \\text{{at }} x = {x_val}"
        steps = [
            S(
                f"({coeff}x^2)^{n_pow} = {coeff}^{n_pow} \\cdot x^{{2 \\times {n_pow}}} = {coeff**n_pow} x^{{{2 * n_pow}}}",
                "Apply the outer exponent to both the numerical coefficient and the variable factor.",
                eq=[f"{coeff}**{n_pow}", str(coeff**n_pow)],
            ),
            S(
                f"x^{{{2 * n_pow}}} = {x_val}^{{{2 * n_pow}}} = {x_val ** (2 * n_pow)}",
                "Substitute the given value of $x$ and evaluate its power.",
                eq=[f"{x_val}**({2 * n_pow})", str(x_val ** (2 * n_pow))],
            ),
            S(
                f"{coeff**n_pow} \\times {x_val ** (2 * n_pow)} = {ans}",
                "Multiply the powered coefficient by the variable power.",
                val=str(ans),
                eq=[f"({coeff**n_pow}) * ({x_val ** (2 * n_pow)})", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Exponents: Power of a Product & Unknown Exponents",
        "references": ["MTH-T01-C08-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"power rule {base}^{a}^{b}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Raise every factor inside the parentheses to the outer power and multiply exponents when raising a power to a power.",
        "commonTrapTag": "c08-power-of-product-unscaled-coeff",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c08_trap(rng, form=None):
    if form not in ("direct", "same-base-sum"):
        form = rng.choice(["direct", "same-base-sum"])
    if form == "same-base-sum":
        base = rng.choice([2, 3, 4])
        k = rng.randint(3, 5)
        ans = k + 1
        trap = base * k
        prompt = f"The sum of ${base}$ identical exponential terms $\\underbrace{{{base}^{k} + {base}^{k} + \\dots + {base}^{k}}}_{{{base}\\text{{ terms}}}}$ can be written as a single power ${base}^n$. Find the exponent $n$."
        disp = f"{base} \\cdot {base}^{k} = {base}^n \\implies n = ?"
        steps = [
            S(
                f"\\underbrace{{{base}^{k} + \\dots + {base}^{k}}}_{{{base}\\text{{ terms}}}} = {base} \\cdot {base}^{k}",
                "Factor out the common exponential term to rewrite repeated addition as multiplication.",
                eq=[f"{base} * ({base}**{k})", f"{base}**({k + 1})"],
            ),
            S(
                f"{base} \\cdot {base}^{k} = {base}^{{{k} + 1}} = {base}^{{{ans}}}",
                "Add the implicit exponent of 1 to the exponent $k$.",
                eq=[f"{k} + 1", str(ans)],
            ),
            S(f"n = {ans}", "Identify the resulting exponent.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        m = rng.randint(3, 6)
        ans = 2 ** (m + 1)
        trap = 4**m
        if trap == ans:
            trap = 2 ** (2 * m) + 4
        prompt = f"Evaluate the exact value of $2^{m} + 2^{m}$."
        disp = f"2^{m} + 2^{m}"
        steps = [
            S(
                f"2^{m} + 2^{m} = 2 \\cdot 2^{m}",
                "Combine the two identical terms by factoring out 2.",
                eq=[f"2**{m} + 2**{m}", f"2 * (2**{m})"],
            ),
            S(
                f"2 \\cdot 2^{m} = 2^{{{m} + 1}} = 2^{{{m + 1}}}",
                "Apply the product property of exponents.",
                eq=[f"2 * (2**{m})", str(ans)],
            ),
            S(f"2^{{{m + 1}}} = {ans}", "Evaluate the power of 2.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Exponents: Same-Base Addition Trap",
        "references": ["MTH-T01-C08-U01"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"sum of identical powers {ans}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Factor out the common power rather than adding exponents or bases directly across an addition sign.",
        "commonTrapTag": "c08-same-base-sum-exponent-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c08_synthesis(rng, form=None):
    if form not in ("direct", "exponential-doubling"):
        form = rng.choice(["direct", "exponential-doubling"])
    cases = [
        (2, 4, 8, 3, 2, 14, 5),
        (2, 4, 16, 4, 3, 20, 7),
        (3, 9, 27, 2, 3, 13, 5),
        (2, 8, 16, 3, 2, 17, 5),
        (3, 9, 81, 3, 2, 14, 5),
    ]
    p, b1, b2, e1, e2, ans, trap = rng.choice(cases)
    k1 = 2 if b1 in (4, 9) else 3
    k2 = 3 if b2 in (8, 27) else 4
    ans = k1 * e1 + k2 * e2
    if form == "exponential-doubling":
        prompt = f"A computing cluster scales its throughput by a factor of ${b1}^{e1}$ in Phase 1 and by a factor of ${b2}^{e2}$ in Phase 2. If the combined scaling factor equals ${p}^x$, find the exact integer $x$."
        disp = f"{b1}^{e1} \\cdot {b2}^{e2} = {p}^x \\implies x = ?"
    else:
        prompt = f"Solve for the integer exponent $x$ by converting to a common prime base: ${b1}^{e1} \\cdot {b2}^{e2} = {p}^x$."
        disp = f"{b1}^{e1} \\cdot {b2}^{e2} = {p}^x"
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Exponents: Common Prime Base Exponential Equation",
        "references": ["MTH-T01-C08-U01", "MTH-T01-C08-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{b1}^{e1} * {b2}^{e2} = {p}^x",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Rewrite each composite base as a power of the prime base, apply the power property, and sum the resulting exponents.",
        "commonTrapTag": "c08-common-base-conversion-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(
                f"{b1}^{e1} = ({p}^{k1})^{e1} = {p}^{{{k1 * e1}}}",
                f"Rewrite ${b1}$ as ${p}^{k1}$ and multiply the exponents.",
                eq=[f"{k1} * {e1}", str(k1 * e1)],
            ),
            S(
                f"{b2}^{e2} = ({p}^{k2})^{e2} = {p}^{{{k2 * e2}}}",
                f"Rewrite ${b2}$ as ${p}^{k2}$ and multiply the exponents.",
                eq=[f"{k2} * {e2}", str(k2 * e2)],
            ),
            S(
                f"x = {k1 * e1} + {k2 * e2} = {ans}",
                "Add the exponents of the common prime base.",
                val=str(ans),
                eq=[f"{k1 * e1} + {k2 * e2}", str(ans)],
            ),
        ],
    }


TEMPLATES = [
    {
        "key": "c08-product-quotient-powers",
        "trapTag": "c08-exponent-product-multiply-trap",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C08-PROD-QUOT"},
            "quotient": {"level": 1, "skill": "MTH-PREALG-C08-PROD-QUOT"},
        },
        "build": t_c08_foundation,
    },
    {
        "key": "c08-power-of-product-neg-exp",
        "trapTag": "c08-power-of-product-unscaled-coeff",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C08-POWER-PRODUCT"},
            "solve-exponent": {"level": 2, "skill": "MTH-PREALG-C08-POWER-PRODUCT"},
        },
        "build": t_c08_reverse,
    },
    {
        "key": "c08-power-tower-addition-trap",
        "trapTag": "c08-same-base-sum-exponent-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C08-ADD-TRAP"},
            "same-base-sum": {"level": 3, "skill": "MTH-PREALG-C08-ADD-TRAP"},
        },
        "build": t_c08_trap,
    },
    {
        "key": "c08-scientific-notation-growth-synthesis",
        "trapTag": "c08-common-base-conversion-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C08-SYNTHESIS"},
            "exponential-doubling": {"level": 4, "skill": "MTH-PREALG-C08-SYNTHESIS"},
        },
        "build": t_c08_synthesis,
    },
]
