# -*- coding: utf-8 -*-
"""Parameterized problem templates for MTH-T01-C13: Polynomials."""

from math_engine.templates._prealg_helpers import S

UNIT = "MTH-T01-C13"
TITLE = "Polynomials"

MISTAKE_TAGS = [
    {
        "id": "c13-polynomial-subtraction-sign-slip",
        "label": "Failed to distribute minus sign to all terms of subtracted polynomial",
        "name": "Polynomial Subtraction Sign Slip",
        "autoFrom": ["whole_sign_flip"],
    },
    {
        "id": "c13-foil-middle-term-omission",
        "label": "Omitted or miscalculated outer/inner cross terms in FOIL binomial multiplication",
        "name": "FOIL Cross-Term Error",
        "autoFrom": [],
    },
    {
        "id": "c13-freshman-dream-square-trap",
        "label": "Squared binomial as (ax - b)^2 = a^2 x^2 + b^2, omitting -2abx cross term",
        "name": "Freshman's Dream Binomial Square Trap",
        "autoFrom": [],
    },
    {
        "id": "c13-difference-of-squares-frame-trap",
        "label": "Subtracted inner dimension linearly instead of subtracting inner polynomial area",
        "name": "Polynomial Frame Area Trap",
        "autoFrom": [],
    },
]


def t_c13_foundation(rng, form=None):
    if form not in ("direct", "evaluate"):
        form = rng.choice(["direct", "evaluate"])
    a1 = rng.randint(2, 6)
    b1 = rng.randint(3, 9)
    c1 = rng.randint(2, 8)
    a2 = rng.randint(2, 5)
    b2 = rng.randint(2, 7)
    c2 = rng.randint(3, 9)
    while b2 == c2:
        c2 = rng.randint(3, 9)
    x_val = rng.choice([2, 3])
    if form == "evaluate":
        A = a1 + a2
        B = b1 - b2
        C = c1 + c2
        ans = A * (x_val**2) + B * x_val + C
        trap = A * (x_val**2) + (b1 + b2) * x_val + C
        prompt = f"Let $P(x) = ({a1}x^2 + {b1}x + {c1}) + ({a2}x^2 - {b2}x + {c2})$. Simplify $P(x)$ and evaluate $P({x_val})$."
        disp = f"P(x) = ({a1}x^2 + {b1}x + {c1}) + ({a2}x^2 - {b2}x + {c2}) \\quad \\text{{at }} x = {x_val}"
        steps = [
            S(
                f"P(x) = ({a1} + {a2})x^2 + ({b1} - {b2})x + ({c1} + {c2})",
                "Group like terms by degree.",
                eq=[f"({a1} + {a2})*({x_val}**2) + ({b1} - {b2})*{x_val} + ({c1} + {c2})", str(ans)],
            ),
            S(
                f"P({x_val}) = {A}({x_val}^2) + ({B})({x_val}) + {C}",
                f"Substitute $x = {x_val}$ into the combined polynomial.",
                eq=[f"{A}*({x_val}**2) + ({B})*{x_val} + {C}", str(ans)],
            ),
            S(
                f"P({x_val}) = {A * x_val * x_val} + ({B * x_val}) + {C} = {ans}",
                "Evaluate and sum the terms.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ]
    else:
        ans = (a1 + a2) + (b1 + b2) + (c1 - c2)
        trap = (a1 + a2) + (b1 - b2) + (c1 + c2)
        prompt = f"Simplify the polynomial difference $({a1}x^2 + {b1}x + {c1}) - (-{a2}x^2 - {b2}x + {c2})$ and find the sum of its resulting coefficients ($A + B + C$ in $Ax^2 + Bx + C$)."
        disp = f"({a1}x^2 + {b1}x + {c1}) - (-{a2}x^2 - {b2}x + {c2}) = Ax^2 + Bx + C"
        steps = [
            S(
                f"= {a1}x^2 + {b1}x + {c1} + {a2}x^2 + {b2}x - {c2}",
                "Distribute the subtraction sign across every term in the second polynomial.",
                eq=[f"({a1} + {a2}) + ({b1} + {b2}) + ({c1} - {c2})", str(ans)],
            ),
            S(
                f"= {a1 + a2}x^2 + {b1 + b2}x + ({c1 - c2})",
                "Combine like terms of degree 2, degree 1, and degree 0.",
                eq=[f"{a1 + a2} + {b1 + b2} + ({c1 - c2})", str(ans)],
            ),
            S(
                f"A + B + C = {a1 + a2} + {b1 + b2} + ({c1 - c2}) = {ans}",
                "Sum the three resulting coefficients.",
                val=str(ans),
                eq=[str(ans), str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Core Skill",
        "context": "Polynomials: Addition, Subtraction, and Evaluation",
        "references": ["MTH-T01-C13-U01"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"poly add sub {a1}*x^2 + {b1}*x + {c1}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Distribute any minus sign across all terms of the subtracted polynomial, then group like powers of x.",
        "commonTrapTag": "c13-polynomial-subtraction-sign-slip",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c13_reverse(rng, form=None):
    if form not in ("direct", "missing-middle-coeff"):
        form = rng.choice(["direct", "missing-middle-coeff"])
    a = rng.randint(2, 5)
    b = rng.randint(3, 8)
    c = rng.randint(2, 6)
    d = rng.randint(2, 7)
    if form == "missing-middle-coeff":
        B = a * d - b * c
        while abs(B) <= 1:
            d += 1
            B = a * d - b * c
        ans = B
        trap = a * d + b * c
        prompt = f"When the binomial product $({a}x - {b})({c}x + {d})$ is expanded into standard form $Ax^2 + Bx + C$, what is the linear coefficient $B$?"
        disp = f"({a}x - {b})({c}x + {d}) = Ax^2 + Bx + C \\implies B = ?"
        steps = [
            S(
                f"\\text{{Outer}} = ({a}x)({d}) = {a * d}x, \\quad \\text{{Inner}} = (-{b})({c}x) = -{b * c}x",
                "Compute the Outer and Inner products using FOIL.",
                eq=[f"{a} * {d} - {b} * {c}", str(ans)],
            ),
            S(
                f"Bx = ({a * d} - {b * c})x = {B}x",
                "Combine the Outer and Inner linear terms.",
                eq=[str(ans), str(ans)],
            ),
            S(f"B = {ans}", "Extract the linear coefficient $B$.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        k = rng.randint(3, 9)
        mid_coeff = a * k + b * c
        ans = k
        trap = mid_coeff - b * c
        if trap == ans:
            trap = ans + 3
        prompt = f"Find the positive integer $k$ such that the expansion of $({a}x + {b})({c}x + k)$ has a linear ($x$) coefficient equal to ${mid_coeff}$."
        disp = f"({a}x + {b})({c}x + k) = {a * c}x^2 + {mid_coeff}x + {b}k \\implies k = ?"
        steps = [
            S(
                f"\\text{{Linear term}} = ({a}k + {b * c})x = {mid_coeff}x",
                "Express the coefficient of $x$ from the Outer and Inner products.",
                eq=[f"{a}*{ans} + {b * c}", str(mid_coeff)],
            ),
            S(
                f"{a}k = {mid_coeff} - {b * c} = {a * k}",
                "Subtract the Inner product contribution from both sides.",
                eq=[f"{mid_coeff} - {b * c}", str(a * k)],
            ),
            S(
                f"k = \\frac{{{a * k}}}{{{a}}} = {ans}",
                "Divide by the leading coefficient $a$.",
                val=str(ans),
                eq=[f"({a * k}) / {a}", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Reverse Reasoning",
        "context": "Polynomials: FOIL Binomial Expansion & Coefficient Recovery",
        "references": ["MTH-T01-C13-U03"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"({a}*x op {b})*({c}*x + {d})",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact signed integer value",
        "checkpointHint": "Use FOIL (First, Outer, Inner, Last) and combine the Outer and Inner products to form the linear x-term.",
        "commonTrapTag": "c13-foil-middle-term-omission",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c13_trap(rng, form=None):
    if form not in ("direct", "subtracted-polynomial-sign-trap"):
        form = rng.choice(["direct", "subtracted-polynomial-sign-trap"])
    a = rng.randint(2, 5)
    b = rng.randint(3, 7)
    x_val = rng.choice([2, 3, 4])
    if form == "subtracted-polynomial-sign-trap":
        ans = -2 * a * b
        trap = 0
        prompt = f"Expand $({a}x - {b})^2 - ({a * a}x^2 + {b * b})$ and find the coefficient of $x$ in the simplified result."
        disp = f"({a}x - {b})^2 - ({a * a}x^2 + {b * b}) = Bx \\implies B = ?"
        steps = [
            S(
                f"({a}x - {b})^2 = {a * a}x^2 - 2({a})({b})x + {b * b} = {a * a}x^2 - {2 * a * b}x + {b * b}",
                "Use the binomial square identity $(u - v)^2 = u^2 - 2uv + v^2$.",
                eq=[f"-2 * {a} * {b}", str(ans)],
            ),
            S(
                f"({a * a}x^2 - {2 * a * b}x + {b * b}) - ({a * a}x^2 + {b * b}) = -{2 * a * b}x",
                "Subtract the quadratic and constant terms, leaving the cross term.",
                eq=[str(ans), str(ans)],
            ),
            S(f"B = {ans}", "State the coefficient of $x$.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        ans = (a * x_val + b) ** 2
        trap = (a * x_val) ** 2 + b**2
        prompt = f"Expand the binomial square $({a}x + {b})^2$ and evaluate it at $x = {x_val}$."
        disp = f"({a}x + {b})^2 \\quad \\text{{at }} x = {x_val}"
        steps = [
            S(
                f"({a}x + {b})^2 = {a * a}x^2 + {2 * a * b}x + {b * b}",
                "Expand using $(u + v)^2 = u^2 + 2uv + v^2$, including the middle cross term $2uv$.",
                eq=[f"({a}*{x_val} + {b})**2", str(ans)],
            ),
            S(
                f"= {a * a}({x_val}^2) + {2 * a * b}({x_val}) + {b * b} = {a * a * x_val * x_val} + {2 * a * b * x_val} + {b * b}",
                f"Substitute $x = {x_val}$ into each term.",
                eq=[f"{a * a * x_val * x_val} + {2 * a * b * x_val} + {b * b}", str(ans)],
            ),
            S(f"= {ans}", "Sum all three terms.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    return {
        "form": form,
        "category": "Trap & Edge Case",
        "context": "Polynomials: Binomial Square Cross-Term Trap",
        "references": ["MTH-T01-C13-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"({a}*x - {b})^2 cross term",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact signed integer value",
        "checkpointHint": "Remember that squaring a binomial always produces a middle cross term equal to twice the product of the two terms.",
        "commonTrapTag": "c13-freshman-dream-square-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


def t_c13_synthesis(rng, form=None):
    if form not in ("direct", "quotient-identity"):
        form = rng.choice(["direct", "quotient-identity"])
    a = rng.randint(3, 7)
    b = rng.randint(2, 6)
    x_val = rng.randint(4, 9)
    if form == "quotient-identity":
        _c = rng.randint(2, 5)
        ans = 4 * a * b * x_val
        trap = 2 * a * b * x_val
        prompt = f"Simplify the polynomial identity $({a}x + {b})^2 - ({a}x - {b})^2$ and evaluate the resulting expression at $x = {x_val}$."
        disp = f"({a}x + {b})^2 - ({a}x - {b})^2 \\quad \\text{{at }} x = {x_val}"
        steps = [
            S(
                f"({a}x + {b})^2 = {a * a}x^2 + {2 * a * b}x + {b * b}, \\quad ({a}x - {b})^2 = {a * a}x^2 - {2 * a * b}x + {b * b}",
                "Expand both binomial squares.",
                eq=[f"({a}*{x_val} + {b})**2 - ({a}*{x_val} - {b})**2", str(ans)],
            ),
            S(
                f"({a}x + {b})^2 - ({a}x - {b})^2 = {4 * a * b}x",
                "Subtracting cancels the squared terms and doubles the middle term to $4abx$.",
                eq=[f"4 * {a} * {b} * {x_val}", str(ans)],
            ),
            S(f"{4 * a * b}({x_val}) = {ans}", f"Evaluate at $x = {x_val}$.", val=str(ans), eq=[str(ans), str(ans)]),
        ]
    else:
        ans = (a * x_val) ** 2 - b**2 - ((a * x_val) ** 2 - (b + 2) ** 2)
        ans = (b + 2) ** 2 - b**2
        trap = (b + 2) - b
        prompt = f"An outer rectangular solar panel has length $({a}x + {b})$ and width $({a}x - {b})$. An inner cutout has length $({a}x + {b + 2})$ and width $({a}x - {b + 2})$. Find the constant difference $(\\text{{Area}}_{{\\text{{outer}}}} - \\text{{Area}}_{{\\text{{inner}}}})$, which is independent of $x$."
        disp = f"({a}x + {b})({a}x - {b}) - ({a}x + {b + 2})({a}x - {b + 2})"
        steps = [
            S(
                f"\\text{{Area}}_{{\\text{{outer}}}} = ({a}x + {b})({a}x - {b}) = {a * a}x^2 - {b * b}",
                "Expand the outer product using the difference of squares.",
                eq=[f"({b + 2})**2 - {b}**2", str(ans)],
            ),
            S(
                f"\\text{{Area}}_{{\\text{{inner}}}} = ({a}x + {b + 2})({a}x - {b + 2}) = {a * a}x^2 - {(b + 2) ** 2}",
                "Expand the inner product using the difference of squares.",
                eq=[f"({b + 2})**2 - {b}**2", str(ans)],
            ),
            S(
                f"({a * a}x^2 - {b * b}) - ({a * a}x^2 - {(b + 2) ** 2}) = {(b + 2) ** 2} - {b * b} = {ans}",
                "Subtract the two polynomials so the quadratic terms cancel.",
                val=str(ans),
                eq=[f"{(b + 2) ** 2} - {b * b}", str(ans)],
            ),
        ]
    return {
        "form": form,
        "category": "Interleaved Synthesis",
        "context": "Polynomials: Special Products & Invariant Area Synthesis",
        "references": ["MTH-T01-C13-U03", "MTH-T01-C13-U04"],
        "prompt": prompt,
        "display": disp,
        "plainText": f"poly identity synthesis {a}*x and {b}",
        "answerSpec": {"type": "number", "value": str(ans)},
        "answerDisplay": str(ans),
        "answerPlain": str(ans),
        "inputHint": "Enter the exact integer value",
        "checkpointHint": "Expand each product using the difference of squares or square of a binomial identity, then cancel opposing terms.",
        "commonTrapTag": "c13-difference-of-squares-frame-trap",
        "verify": {"source": str(ans), "trapValue": str(trap)},
        "steps": steps,
    }


TEMPLATES = [
    {
        "key": "c13-add-subtract-polynomials",
        "trapTag": "c13-polynomial-subtraction-sign-slip",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 1, "skill": "MTH-PREALG-C13-ADD-SUB"},
            "evaluate": {"level": 1, "skill": "MTH-PREALG-C13-ADD-SUB"},
        },
        "build": t_c13_foundation,
    },
    {
        "key": "c13-multiply-binomials-foil",
        "trapTag": "c13-foil-middle-term-omission",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-PREALG-C13-FOIL"},
            "missing-middle-coeff": {"level": 2, "skill": "MTH-PREALG-C13-FOIL"},
        },
        "build": t_c13_reverse,
    },
    {
        "key": "c13-binomial-square-freshman-trap",
        "trapTag": "c13-freshman-dream-square-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 3, "skill": "MTH-PREALG-C13-SPECIAL-PROD"},
            "subtracted-polynomial-sign-trap": {"level": 3, "skill": "MTH-PREALG-C13-SPECIAL-PROD"},
        },
        "build": t_c13_trap,
    },
    {
        "key": "c13-polynomial-identity-area-synthesis",
        "trapTag": "c13-difference-of-squares-frame-trap",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 4, "skill": "MTH-PREALG-C13-SYNTHESIS"},
            "quotient-identity": {"level": 4, "skill": "MTH-PREALG-C13-SYNTHESIS"},
        },
        "build": t_c13_synthesis,
    },
]
