# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C10: The Properties of Real Numbers."""

from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C10"
TITLE = "The Properties of Real Numbers"

MISTAKE_TAGS = [
    {
        "id": "c10-partial-distribution-slip",
        "label": "Multiplied only the first term inside parentheses when distributing",
        "name": "Partial Distributive Property Slip",
        "autoFrom": [],
    },
    {
        "id": "c10-inverse-property-sign-slip",
        "label": "Confused additive inverse (-a) with multiplicative reciprocal (1/a)",
        "name": "Additive vs Multiplicative Inverse Confusion",
        "autoFrom": ["reciprocal"],
    },
    {
        "id": "c10-negative-distribution-sign-trap",
        "label": "Failed to flip inner sign when distributing a negative factor: a - b(c - d)",
        "name": "Negative Distribution Sign Trap",
        "autoFrom": ["whole_sign_flip"],
    },
    {
        "id": "c10-dimensional-unit-conversion-trap",
        "label": "Divided instead of multiplied by unit conversion factor in multi-step conversion",
        "name": "Dimensional Analysis Conversion Trap",
        "autoFrom": ["off_by_factor"],
    },
]


def t_c10_foundation(rng, form=None):
    if form not in ("direct", "mental-split"):
        form = rng.choice(["direct", "mental-split"])
    a = rng.randint(6, 14)
    b = rng.choice([20, 30, 40, 50])
    c = rng.randint(3, 9)
    if form == "mental-split":
        ans = a * (b - c)
        trap = a * b - c
        prompt = (
            f"Use the distributive property to evaluate ${a} \\times {b - c}$ by rewriting ${b - c}$ as $({b} - {c})$."
        )
        disp = f"{a}({b} - {c}) = {a}({b}) - {a}({c})"
        steps = [
            S(
                f"{a}({b} - {c}) = {a} \\times {b} - {a} \\times {c}",
                "Distribute the outer factor across both terms in the difference.",
                eq=[f"{a} * ({b} - {c})", f"{a}*{b} - {a}*{c}"],
            ),
            S(f"= {a * b} - {a * c}", "Evaluate each product separately.", eq=[f"{a * b} - {a * c}", str(ans)]),
            S(f"= {ans}", "Subtract the second product from the first.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        ans = a * (b + c)
        trap = a * b + c
        prompt = f"Use the distributive property to evaluate ${a}({b} + {c})$."
        disp = f"{a}({b} + {c})"
        steps = [
            S(
                f"{a}({b} + {c}) = {a} \\times {b} + {a} \\times {c}",
                "Distribute the factor across both terms inside the parentheses.",
                eq=[f"{a} * ({b} + {c})", f"{a}*{b} + {a}*{c}"],
            ),
            S(f"= {a * b} + {a * c}", "Compute each individual product.", eq=[f"{a * b} + {a * c}", str(ans)]),
            S(f"= {ans}", "Add the two products.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Real Numbers: Distributive Property",
        "references": ["MTH-T01-C10-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{a}*({b} op {c})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Multiply the outside factor by every term inside the parentheses before combining.",
        "commonTrapTag": "c10-partial-distribution-slip",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c10_reverse(rng, form=None):
    if form not in ("direct", "unit-conversion"):
        form = rng.choice(["direct", "unit-conversion"])
    a = rng.randint(4, 9)
    b = rng.randint(5, 12)
    c = rng.randint(3, 8)
    x = rng.randint(4, 11)
    rhs = a * (x + b) + c * x
    ans = x
    trap = (rhs - b) // (a + c) if (rhs - b) != a * (x + b) + c * x - a * b else x + 3
    if trap == ans:
        trap = ans + 4
    if form == "unit-conversion":
        prompt = f"Using the distributive and associative properties, solve for $x$: ${a}(x + {b}) + {c}x = {rhs}$."
        disp = f"{a}(x + {b}) + {c}x = {rhs} \\implies x = ?"
    else:
        prompt = f"Find the real number $x$ that satisfies ${a}(x + {b}) + {c}x = {rhs}$."
        disp = f"{a}(x + {b}) + {c}x = {rhs}"
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Real Numbers: Distributive & Associative Equation",
        "references": ["MTH-T01-C10-U02"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{a}*(x + {b}) + {c}*x = {rhs}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Distribute the factor over the parentheses, combine like variable terms using the associative property, and isolate the variable.",
        "commonTrapTag": "c10-partial-distribution-slip",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": [
            S(
                f"{a}x + {a * b} + {c}x = {rhs}",
                "Apply the distributive property to expand the parenthesized term.",
                eq=[f"{a}*({ans} + {b}) + {c}*{ans}", str(rhs)],
            ),
            S(
                f"{a + c}x + {a * b} = {rhs} \\implies {a + c}x = {rhs - a * b}",
                "Combine like variable terms and subtract the constant term.",
                eq=[f"{rhs} - {a * b}", str((a + c) * ans)],
            ),
            S(
                f"x = \\frac{{{rhs - a * b}}}{{{a + c}}} = {ans}",
                "Multiply by the multiplicative inverse of the coefficient.",
                val=str(ans),
                eq=[f"({rhs - a * b}) / ({a + c})", str(ans)],
            ),
        ],
    }


def t_c10_trap(rng, form=None):
    if form not in ("direct", "nested-brackets"):
        form = rng.choice(["direct", "nested-brackets"])
    a = rng.randint(40, 85)
    b = rng.randint(3, 8)
    c = rng.randint(9, 18)
    d = rng.randint(4, 11)
    if form == "nested-brackets":
        e = rng.randint(5, 14)
        ans = a - b * (c - d) - e
        trap = a - b * c - b * d - e
        prompt = f"Evaluate the expression ${a} - {b}({c} - {d}) - {e}$ by applying the distributive property."
        disp = f"{a} - {b}({c} - {d}) - {e}"
        steps = [
            S(
                f"-{b}({c} - {d}) = -{b}({c}) + (-{b})(-{d}) = -{b * c} + {b * d}",
                "Distribute the negative factor across the inner difference, flipping the sign of the subtracted term.",
                eq=[f"-{b} * ({c} - {d})", f"-{b * c} + {b * d}"],
            ),
            S(
                f"{a} - {b * c} + {b * d} - {e}",
                "Substitute the distributed terms into the main expression.",
                eq=[f"{a} - {b * c} + {b * d} - {e}", str(ans)],
            ),
            S(f"= {ans}", "Combine the integer terms from left to right.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        ans = a - b * (c - d)
        trap = a - b * c - b * d
        prompt = f"Evaluate ${a} - {b}({c} - {d})$ carefully tracking the sign when distributing $-{b}$."
        disp = f"{a} - {b}({c} - {d})"
        steps = [
            S(
                f"-{b}({c} - {d}) = -{b * c} + {b * d}",
                "Multiplying $-b$ by $-d$ produces a positive product $+bd$.",
                eq=[f"-{b} * ({c} - {d})", f"-{b * c} + {b * d}"],
            ),
            S(
                f"{a} - {b * c} + {b * d}",
                "Combine the initial integer with the distributed terms.",
                eq=[f"{a} - {b * c} + {b * d}", str(ans)],
            ),
            S(f"= {ans}", "Simplify to obtain the exact result.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Real Numbers: Negative Distributive Sign Trap",
        "references": ["MTH-T01-C10-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"{a} - {b}*({c} - {d})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "When expanding parentheses preceded by a minus sign, remember that multiplying two negative numbers yields a positive product.",
        "commonTrapTag": "c10-negative-distribution-sign-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c10_synthesis(rng, form=None):
    if form not in ("direct", "unit-rate-conversion"):
        form = rng.choice(["direct", "unit-rate-conversion"])
    if form == "unit-rate-conversion":
        mps = rng.choice([5, 10, 15, 20, 25, 30])
        hours = rng.choice([2, 3, 4])
        km_per_hr = (mps * 3600) // 1000
        ans = km_per_hr * hours
        trap = (mps * 60 * hours) // 1000 if (mps * 60 * hours) // 1000 != ans else ans - 12
        prompt = f"An autonomous drone flies at a constant speed of ${mps}$ meters per second. Using unit conversion properties ($1\\text{{ km}} = 1000\\text{{ m}}$ and $1\\text{{ hour}} = 3600\\text{{ seconds}}$), how many kilometers does the drone travel in ${hours}$ hours?"
        disp = f"D = {mps}\\frac{{\\text{{m}}}}{{\\text{{s}}}} \\times \\frac{{3600\\text{{ s}}}}{{1\\text{{ hr}}}} \\times \\frac{{1\\text{{ km}}}}{{1000\\text{{ m}}}} \\times {hours}\\text{{ hr}}"
        steps = [
            S(
                f"v_{{\\text{{km/h}}}} = {mps} \\times \\frac{{3600}}{{1000}} = {km_per_hr}\\text{{ km/h}}",
                "Convert meters per second to kilometers per hour by multiplying by $3600/1000$.",
                eq=[f"({mps} * 3600) / 1000", str(km_per_hr)],
            ),
            S(
                f"D = {km_per_hr} \\times {hours}",
                "Multiply the speed in km/h by the duration in hours.",
                eq=[f"{km_per_hr} * {hours}", str(ans)],
            ),
            S(f"D = {ans}", "Obtain the total distance in kilometers.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        k = rng.randint(14, 38)
        p1 = rng.randint(35, 75)
        p2 = 100 - p1
        offset = rng.randint(15, 65)
        ans = k * 100 - offset
        trap = k * p1 + p2 - offset
        prompt = f"Use the distributive, commutative, and associative properties of real numbers to evaluate ${k} \\times {p1} - {offset} + {k} \\times {p2}$."
        disp = f"{k} \\times {p1} - {offset} + {k} \\times {p2}"
        steps = [
            S(
                f"= ({k} \\times {p1} + {k} \\times {p2}) - {offset}",
                "Use the commutative and associative properties to group the products sharing factor $k$.",
                eq=[f"{k}*{p1} + {k}*{p2} - {offset}", str(ans)],
            ),
            S(
                f"= {k}({p1} + {p2}) - {offset} = {k}(100) - {offset}",
                "Factor out the common multiplier using the distributive property.",
                eq=[f"{k} * ({p1} + {p2}) - {offset}", str(ans)],
            ),
            S(
                f"= {k * 100} - {offset} = {ans}",
                "Subtract the offset from the product.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Real Numbers: Algebraic Factoring & Unit Conversion Synthesis",
        "references": ["MTH-T01-C10-U03", "MTH-T01-C10-U05"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"real properties synthesis {ans}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Group terms sharing a common factor or align dimensional unit ratios so intermediate units cancel cleanly.",
        "commonTrapTag": "c10-dimensional-unit-conversion-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


TEMPLATES = [
    {
        "key": "c10-distributive-collect-terms",
        "trapTag": "c10-partial-distribution-slip",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C10-DISTRIBUTE"},
            "mental-split": {"level": 1, "skill": "MTH-PREALG-C10-DISTRIBUTE"},
        },
        "build": t_c10_foundation,
    },
    {
        "key": "c10-additive-multiplicative-inverse",
        "trapTag": "c10-partial-distribution-slip",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C10-ASSOC-INV"},
            "unit-conversion": {"level": 2, "skill": "MTH-PREALG-C10-ASSOC-INV"},
        },
        "build": t_c10_reverse,
    },
    {
        "key": "c10-negative-distribution-trap",
        "trapTag": "c10-negative-distribution-sign-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C10-NEG-DIST-TRAP"},
            "nested-brackets": {"level": 3, "skill": "MTH-PREALG-C10-NEG-DIST-TRAP"},
        },
        "build": t_c10_trap,
    },
    {
        "key": "c10-real-closure-measurement-synthesis",
        "trapTag": "c10-dimensional-unit-conversion-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C10-SYNTHESIS"},
            "unit-rate-conversion": {"level": 4, "skill": "MTH-PREALG-C10-SYNTHESIS"},
        },
        "build": t_c10_synthesis,
    },
]
