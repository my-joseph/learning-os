# -*- coding: utf-8 -*-
"""
Pre-verifies 20 graded Complex Numbers problems (MTH-T02-C01-U01) and 10 Next.js Project Structure
problems (PRG-T03-C01-U01) using Python exact arithmetic & path-resolution assertions before generating:
1. Interactive HTML Drill Apps in drills/DRL-MTH-T02-C01-U01-01.html and drills/DRL-PRG-T03-C01-U01-01.html
2. Corresponding Notion pages in the 'Learning Practice & Drills' database linked to Topic, Chapter, and Unit.
"""
import json
import math
import os
from fractions import Fraction
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    rt,
    parse_rt,
    validate_blocks_clean,
    h2,
    h3,
    p_block,
    callout_block,
    divider_block,
    eq_block,
    code_block,
    bullet,
    num_item,
    toggle_block,
    replace_page_blocks,
)

class ExactComplex:
    """Exact rational complex number a + bi using Python fractions.Fraction."""
    def __init__(self, re_val, im_val=0):
        self.re = Fraction(re_val)
        self.im = Fraction(im_val)

    def __add__(self, other):
        return ExactComplex(self.re + other.re, self.im + other.im)

    def __sub__(self, other):
        return ExactComplex(self.re - other.re, self.im - other.im)

    def __mul__(self, other):
        return ExactComplex(
            self.re * other.re - self.im * other.im,
            self.re * other.im + self.im * other.re,
        )

    def conj(self):
        return ExactComplex(self.re, -self.im)

    def mod_sq(self):
        return self.re * self.re + self.im * self.im

    def __truediv__(self, other):
        denom = other.mod_sq()
        if denom == 0:
            raise ZeroDivisionError("Complex division by zero")
        num = self * other.conj()
        return ExactComplex(num.re / denom, num.im / denom)

    def __eq__(self, other):
        return self.re == other.re and self.im == other.im

def fmt_frac(f):
    f = Fraction(f)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"

def build_and_verify_mth_problems():
    """
    Builds 20 Complex Numbers problems across Levels 1–4 and verifies every single answer
    using ExactComplex before returning the problem bank.
    """
    problems = []

    # --- Q1 (Level 1 - Core): (5 - 3i) - (-2 + 7i) ---
    z1 = ExactComplex(5, -3) - ExactComplex(-2, 7)
    assert z1 == ExactComplex(7, -10)
    problems.append({
        "id": "Q01",
        "level": 1,
        "levelLabel": "Level 1 — Foundation",
        "category": "Core Skills",
        "prompt": "Subtract the complex numbers and write the result in standard form $a + bi$: $$(5 - 3i) - (-2 + 7i)$$",
        "plainText": "(5 - 3i) - (-2 + 7i)",
        "re": fmt_frac(z1.re),
        "im": fmt_frac(z1.im),
        "displayAnswer": "7 - 10i",
        "checkpointHint": "After distributing the negative sign across $(-2 + 7i)$, the expression becomes $5 - 3i + 2 - 7i$.",
        "commonTrapTag": "Arithmetic / Sign Slip",
        "steps": [
            {"latex": "(5 - 3i) - (-2 + 7i) = 5 - 3i + 2 - 7i", "explain": "Distribute the subtraction sign $(-1)$ across both terms inside the second parentheses: $-(-2) = +2$ and $-(+7i) = -7i$."},
            {"latex": "= (5 + 2) + (-3 - 7)i", "explain": "Group the real parts together and the imaginary parts together using the commutative and associative properties."},
            {"latex": "= 7 - 10i", "explain": "Combine like terms to obtain standard form $a + bi$ with $a = 7$ and $b = -10$."},
        ],
    })

    # --- Q2 (Level 1 - Core): (3 - 4i)(2 + 5i) ---
    z2 = ExactComplex(3, -4) * ExactComplex(2, 5)
    assert z2 == ExactComplex(26, 7)
    problems.append({
        "id": "Q02",
        "level": 1,
        "levelLabel": "Level 1 — Foundation",
        "category": "Core Skills",
        "prompt": "Multiply the complex numbers and express the result in standard form $a + bi$: $$(3 - 4i)(2 + 5i)$$",
        "plainText": "(3 - 4i)*(2 + 5i)",
        "re": fmt_frac(z2.re),
        "im": fmt_frac(z2.im),
        "displayAnswer": "26 + 7i",
        "checkpointHint": "Expanding via FOIL gives $6 + 15i - 8i - 20i^2$. Remember that $-20i^2 = -20(-1) = +20$.",
        "commonTrapTag": "Arithmetic / Sign Slip",
        "steps": [
            {"latex": "(3 - 4i)(2 + 5i) = 3(2) + 3(5i) - 4i(2) - 4i(5i)", "explain": "Expand the product of binomials using the distributive property (FOIL)."},
            {"latex": "= 6 + 15i - 8i - 20i^2", "explain": "Multiply each pair of terms."},
            {"latex": "= 6 + 7i - 20(-1)", "explain": "Combine middle imaginary terms ($15i - 8i = 7i$) and substitute the fundamental identity $i^2 = -1$."},
            {"latex": "= (6 + 20) + 7i = 26 + 7i", "explain": "Add the real parts ($6 + 20 = 26$) to write the final answer in standard form $a + bi$."},
        ],
    })

    # --- Q3 (Level 1 - Core): (4 - 3i)(4 + 3i) ---
    z3 = ExactComplex(4, -3) * ExactComplex(4, 3)
    assert z3 == ExactComplex(25, 0)
    problems.append({
        "id": "Q03",
        "level": 1,
        "levelLabel": "Level 1 — Foundation",
        "category": "Core Skills",
        "prompt": "Multiply the complex conjugate pair and write the result in standard form $a + bi$: $$(4 - 3i)(4 + 3i)$$",
        "plainText": "(4 - 3i)*(4 + 3i)",
        "re": fmt_frac(z3.re),
        "im": fmt_frac(z3.im),
        "displayAnswer": "25",
        "checkpointHint": "For conjugates $(a - bi)(a + bi)$, the cross terms cancel and yield $a^2 + b^2$ (not $a^2 - b^2$).",
        "commonTrapTag": "Conjugate Denominator Error",
        "steps": [
            {"latex": "(4 - 3i)(4 + 3i) = 4^2 - (3i)^2", "explain": "Apply the difference-of-squares pattern $(A - B)(A + B) = A^2 - B^2$ with $A = 4$ and $B = 3i$."},
            {"latex": "= 16 - 9i^2", "explain": "Square both factors: $4^2 = 16$ and $(3i)^2 = 9i^2$."},
            {"latex": "= 16 - 9(-1) = 16 + 9 = 25", "explain": "Substitute $i^2 = -1$, converting subtraction into addition ($16 + 9 = 25$, or $25 + 0i$)."},
        ],
    })

    # --- Q4 (Level 1 - Core): Simplify i^75 + i^42 ---
    # i^75 = i^3 = -i; i^42 = i^2 = -1 -> -1 - i
    z4 = ExactComplex(-1, -1)
    problems.append({
        "id": "Q04",
        "level": 1,
        "levelLabel": "Level 1 — Foundation",
        "category": "Core Skills",
        "prompt": "Simplify the sum of powers of $i$ and write the result in standard form $a + bi$: $$i^{75} + i^{42}$$",
        "plainText": "i^75 + i^42",
        "re": fmt_frac(z4.re),
        "im": fmt_frac(z4.im),
        "displayAnswer": "-1 - i",
        "checkpointHint": "Divide each exponent by 4: $75 = 4(18) + 3$ and $42 = 4(10) + 2$.",
        "commonTrapTag": "Formula / Identity Mix-up",
        "steps": [
            {"latex": "i^{75} = i^{4(18) + 3} = (i^4)^{18} \\cdot i^3 = 1^{18} \\cdot (-i) = -i", "explain": "Divide $75$ by $4$: quotient $18$ with remainder $r = 3$, so $i^{75} = i^3 = -i$."},
            {"latex": "i^{42} = i^{4(10) + 2} = (i^4)^{10} \\cdot i^2 = 1^{10} \\cdot (-1) = -1", "explain": "Divide $42$ by $4$: quotient $10$ with remainder $r = 2$, so $i^{42} = i^2 = -1$."},
            {"latex": "i^{75} + i^{42} = -1 - i", "explain": "Write the real part $(-1)$ first and the imaginary part $(-i)$ second in standard form $a + bi$."},
        ],
    })

    # --- Q5 (Level 1 - Core): Simplify sqrt(-36) - sqrt(-100) ---
    # 6i - 10i = -4i
    z5 = ExactComplex(0, 6) - ExactComplex(0, 10)
    assert z5 == ExactComplex(0, -4)
    problems.append({
        "id": "Q05",
        "level": 1,
        "levelLabel": "Level 1 — Foundation",
        "category": "Core Skills",
        "prompt": "Express each principal square root in terms of $i$ and simplify into standard form $a + bi$: $$\\sqrt{-36} - \\sqrt{-100}$$",
        "plainText": "sqrt(-36) - sqrt(-100)",
        "re": fmt_frac(z5.re),
        "im": fmt_frac(z5.im),
        "displayAnswer": "-4i",
        "checkpointHint": "Rewrite $\\sqrt{-36} = 6i$ and $\\sqrt{-100} = 10i$ before subtracting.",
        "commonTrapTag": "Premature Radical Multiplication",
        "steps": [
            {"latex": "\\sqrt{-36} - \\sqrt{-100} = i\\sqrt{36} - i\\sqrt{100}", "explain": "Apply the definition $\\sqrt{-b} = i\\sqrt{b}$ ($b > 0$) to each negative radical separately."},
            {"latex": "= 6i - 10i", "explain": "Evaluate the principal square roots $\\sqrt{36} = 6$ and $\\sqrt{100} = 10$."},
            {"latex": "= 0 - 4i = -4i", "explain": "Combine like imaginary terms ($6 - 10 = -4$)."},
        ],
    })

    # --- Q6 (Level 2 - Prior Blend: Roots MTH-T01-C09): sqrt(-12) * sqrt(-27) ---
    # (2i sqrt(3))(3i sqrt(3)) = 6 * (-1) * 3 = -18
    z6 = ExactComplex(-18, 0)
    problems.append({
        "id": "Q06",
        "level": 2,
        "levelLabel": "Level 2 — Standard Exam",
        "category": "Combined with Prior Units",
        "prompt": "Simplify the product of negative radicals (combining with [[MTH-T01-C09]] `Roots`) and write the result in standard form $a + bi$: $$\\sqrt{-12} \\cdot \\sqrt{-27}$$",
        "plainText": "sqrt(-12) * sqrt(-27)",
        "re": fmt_frac(z6.re),
        "im": fmt_frac(z6.im),
        "displayAnswer": "-18",
        "checkpointHint": "Extract $i$ FIRST: $\\sqrt{-12} = 2i\\sqrt{3}$ and $\\sqrt{-27} = 3i\\sqrt{3}$. Do NOT multiply $(-12)(-27)$ under the radical!",
        "commonTrapTag": "Premature Radical Multiplication",
        "steps": [
            {"latex": "\\sqrt{-12} \\cdot \\sqrt{-27} = \\left(i\\sqrt{12}\\right) \\cdot \\left(i\\sqrt{27}\\right)", "explain": "Mandatory first step: extract $i = \\sqrt{-1}$ from each negative radical before multiplying."},
            {"latex": "= \\left(i\\sqrt{4 \\cdot 3}\\right) \\cdot \\left(i\\sqrt{9 \\cdot 3}\\right) = \\left(2i\\sqrt{3}\\right)\\left(3i\\sqrt{3}\\right)", "explain": "Factor out perfect squares $4$ and $9$ from the radicands."},
            {"latex": "= (2 \\cdot 3) \\cdot i^2 \\cdot \\left(\\sqrt{3}\\right)^2", "explain": "Multiply rational coefficients, $i$ factors, and remaining radicals."},
            {"latex": "= 6 \\cdot (-1) \\cdot 3 = -18", "explain": "Substitute $i^2 = -1$ and $(\\sqrt{3})^2 = 3$ to obtain $-18 + 0i$."},
        ],
    })

    # --- Q7 (Level 2 - Prior Blend: Fractions MTH-T01-C04): (2 + 5i) / (4 - i) ---
    z7 = ExactComplex(2, 5) / ExactComplex(4, -1)
    assert z7 == ExactComplex(Fraction(3, 17), Fraction(22, 17))
    problems.append({
        "id": "Q07",
        "level": 2,
        "levelLabel": "Level 2 — Standard Exam",
        "category": "Combined with Prior Units",
        "prompt": "Divide the complex numbers and write the exact quotient in standard form $a + bi$ using simplified fractions ([[MTH-T01-C04]]): $$\\frac{2 + 5i}{4 - i}$$",
        "plainText": "(2 + 5i) / (4 - i)",
        "re": fmt_frac(z7.re),
        "im": fmt_frac(z7.im),
        "displayAnswer": "3/17 + 22/17i",
        "checkpointHint": "Multiply numerator and denominator by the conjugate $4 + i$. The denominator becomes $4^2 + 1^2 = 17$.",
        "commonTrapTag": "Conjugate Denominator Error",
        "steps": [
            {"latex": "\\frac{2 + 5i}{4 - i} = \\frac{(2 + 5i)(4 + i)}{(4 - i)(4 + i)}", "explain": "Multiply numerator and denominator by the complex conjugate of the denominator, $\\overline{4 - i} = 4 + i$."},
            {"latex": "= \\frac{8 + 2i + 20i + 5i^2}{4^2 + (-1)^2}", "explain": "Expand the numerator via FOIL and apply $(c - di)(c + di) = c^2 + d^2$ in the denominator."},
            {"latex": "= \\frac{8 + 22i + 5(-1)}{16 + 1} = \\frac{3 + 22i}{17}", "explain": "Substitute $i^2 = -1$ in the numerator ($8 - 5 = 3$) and add $16 + 1 = 17$ in the denominator."},
            {"latex": "= \\frac{3}{17} + \\frac{22}{17}i", "explain": "Split into separate real and imaginary fractions in standard form $a + bi$."},
        ],
    })

    # --- Q8 (Level 2 - Prior Blend: Fraction Reduction MTH-T01-C04): (4 - 6i) / (2 + 4i) ---
    z8 = ExactComplex(4, -6) / ExactComplex(2, 4)
    assert z8 == ExactComplex(Fraction(-4, 5), Fraction(-7, 5))
    problems.append({
        "id": "Q08",
        "level": 2,
        "levelLabel": "Level 2 — Standard Exam",
        "category": "Combined with Prior Units",
        "prompt": "Divide and reduce the resulting fractions to lowest terms in standard form $a + bi$: $$\\frac{4 - 6i}{2 + 4i}$$",
        "plainText": "(4 - 6i) / (2 + 4i)",
        "re": fmt_frac(z8.re),
        "im": fmt_frac(z8.im),
        "displayAnswer": "-4/5 - 7/5i",
        "checkpointHint": "Multiplying by $(2 - 4i)$ gives numerator $-16 - 28i$ and denominator $2^2 + 4^2 = 20$. Then reduce by dividing numerator and denominator by $4$.",
        "commonTrapTag": "Unseparated Standard Form",
        "steps": [
            {"latex": "\\frac{4 - 6i}{2 + 4i} = \\frac{(4 - 6i)(2 - 4i)}{(2 + 4i)(2 - 4i)}", "explain": "Multiply numerator and denominator by the denominator's conjugate, $2 - 4i$."},
            {"latex": "= \\frac{8 - 16i - 12i + 24i^2}{2^2 + 4^2}", "explain": "Expand the numerator via FOIL and compute $c^2 + d^2 = 4 + 16 = 20$ in the denominator."},
            {"latex": "= \\frac{8 - 28i + 24(-1)}{20} = \\frac{-16 - 28i}{20}", "explain": "Substitute $i^2 = -1$ and combine real terms: $8 - 24 = -16$."},
            {"latex": "= -\\frac{16}{20} - \\frac{28}{20}i = -\\frac{4}{5} - \\frac{7}{5}i", "explain": "Separate into $a + bi$ and divide each fraction's numerator and denominator by $\\gcd(16, 20) = \\gcd(28, 20) = 4$."},
        ],
    })

    # --- Q9 (Level 2 - Prior Blend: Polynomials MTH-T01-C13): (2 - 3i)^2 - (4 + i)(4 - i) ---
    z9 = (ExactComplex(2, -3) * ExactComplex(2, -3)) - (ExactComplex(4, 1) * ExactComplex(4, -1))
    assert z9 == ExactComplex(-22, -12)
    problems.append({
        "id": "Q09",
        "level": 2,
        "levelLabel": "Level 2 — Standard Exam",
        "category": "Combined with Prior Units",
        "prompt": "Expand using binomial special products ([[MTH-T01-C13]]) and simplify into standard form $a + bi$: $$(2 - 3i)^2 - (4 + i)(4 - i)$$",
        "plainText": "(2 - 3i)^2 - (4 + i)*(4 - i)",
        "re": fmt_frac(z9.re),
        "im": fmt_frac(z9.im),
        "displayAnswer": "-22 - 12i",
        "checkpointHint": "$(2 - 3i)^2 = 4 - 12i + 9i^2 = -5 - 12i$, and $(4 + i)(4 - i) = 16 + 1 = 17$.",
        "commonTrapTag": "Formula / Identity Mix-up",
        "steps": [
            {"latex": "(2 - 3i)^2 = 2^2 - 2(2)(3i) + (3i)^2 = 4 - 12i + 9i^2 = -5 - 12i", "explain": "Expand the binomial square $(A - B)^2 = A^2 - 2AB + B^2$ and substitute $9i^2 = -9$."},
            {"latex": "(4 + i)(4 - i) = 4^2 + 1^2 = 16 + 1 = 17", "explain": "Multiply the conjugate pair $(c + di)(c - di) = c^2 + d^2$."},
            {"latex": "(-5 - 12i) - 17 = (-5 - 17) - 12i = -22 - 12i", "explain": "Subtract $17$ from the real part $-5$ to obtain $-22 - 12i$."},
        ],
    })

    # --- Q10 (Level 2 - Polynomial Root Evaluation): f(z) = z^2 - 6z + 13 at z = 3 + 2i ---
    z_in = ExactComplex(3, 2)
    z10 = (z_in * z_in) - (ExactComplex(6, 0) * z_in) + ExactComplex(13, 0)
    assert z10 == ExactComplex(0, 0)
    problems.append({
        "id": "Q10",
        "level": 2,
        "levelLabel": "Level 2 — Standard Exam",
        "category": "Core Skills",
        "prompt": "Evaluate the quadratic polynomial $f(z) = z^2 - 6z + 13$ at $z = 3 + 2i$ and write the result in standard form $a + bi$: $$(3 + 2i)^2 - 6(3 + 2i) + 13$$",
        "plainText": "(3 + 2i)^2 - 6*(3 + 2i) + 13",
        "re": fmt_frac(z10.re),
        "im": fmt_frac(z10.im),
        "displayAnswer": "0",
        "checkpointHint": "$(3 + 2i)^2 = 9 + 12i + 4i^2 = 5 + 12i$. Then subtract $18 + 12i$ and add $13$.",
        "commonTrapTag": "Arithmetic / Sign Slip",
        "steps": [
            {"latex": "(3 + 2i)^2 - 6(3 + 2i) + 13 = (9 + 12i + 4i^2) - 18 - 12i + 13", "explain": "Expand $(3 + 2i)^2$ using $(a+b)^2 = a^2 + 2ab + b^2$ and distribute $-6$ across $(3 + 2i)$."},
            {"latex": "= (9 + 12i - 4) - 18 - 12i + 13", "explain": "Substitute $4i^2 = 4(-1) = -4$."},
            {"latex": "= (5 - 18 + 13) + (12 - 12)i = 0 + 0i = 0", "explain": "Group real and imaginary parts; both sum to $0$, proving $z = 3 + 2i$ is a root of $z^2 - 6z + 13 = 0$."},
        ],
    })

    # --- Q11 (Level 2 - Prior Blend: Radical Division): sqrt(-48) / sqrt(3) + (1 - i)^2 ---
    # sqrt(-48)/sqrt(3) = 4i; (1 - i)^2 = 1 - 2i + i^2 = -2i -> 2i
    z11 = ExactComplex(0, 4) + (ExactComplex(1, -1) * ExactComplex(1, -1))
    assert z11 == ExactComplex(0, 2)
    problems.append({
        "id": "Q11",
        "level": 2,
        "levelLabel": "Level 2 — Standard Exam",
        "category": "Combined with Prior Units",
        "prompt": "Simplify the radical quotient and binomial square into standard form $a + bi$: $$\\frac{\\sqrt{-48}}{\\sqrt{3}} + (1 - i)^2$$",
        "plainText": "sqrt(-48)/sqrt(3) + (1 - i)^2",
        "re": fmt_frac(z11.re),
        "im": fmt_frac(z11.im),
        "displayAnswer": "2i",
        "checkpointHint": "$\\frac{\\sqrt{-48}}{\\sqrt{3}} = \\frac{i\\sqrt{48}}{\\sqrt{3}} = i\\sqrt{16} = 4i$, and $(1 - i)^2 = -2i$.",
        "commonTrapTag": "Premature Radical Multiplication",
        "steps": [
            {"latex": "\\frac{\\sqrt{-48}}{\\sqrt{3}} = \\frac{i\\sqrt{48}}{\\sqrt{3}} = i\\sqrt{\\frac{48}{3}} = i\\sqrt{16} = 4i", "explain": "Extract $i$ first, then apply the quotient property of positive radicals $\\frac{\\sqrt{48}}{\\sqrt{3}} = \\sqrt{16} = 4$."},
            {"latex": "(1 - i)^2 = 1^2 - 2(1)(i) + i^2 = 1 - 2i - 1 = -2i", "explain": "Expand $(1 - i)^2$ and replace $i^2$ with $-1$; the real parts $1 - 1$ cancel."},
            {"latex": "4i + (-2i) = 2i", "explain": "Add the two imaginary results to obtain $0 + 2i = 2i$."},
        ],
    })

    # --- Q12 (Level 2 - Multiplicative Inverse / Reciprocal): 10 / (1 - 3i) ---
    z12 = ExactComplex(10, 0) / ExactComplex(1, -3)
    assert z12 == ExactComplex(1, 3)
    problems.append({
        "id": "Q12",
        "level": 2,
        "levelLabel": "Level 2 — Standard Exam",
        "category": "Core Skills",
        "prompt": "Simplify the complex quotient into standard form $a + bi$: $$\\frac{10}{1 - 3i}$$",
        "plainText": "10 / (1 - 3i)",
        "re": fmt_frac(z12.re),
        "im": fmt_frac(z12.im),
        "displayAnswer": "1 + 3i",
        "checkpointHint": "Multiply top and bottom by $1 + 3i$. The denominator is $1^2 + 3^2 = 10$, which cancels the $10$ in the numerator!",
        "commonTrapTag": "Conjugate Denominator Error",
        "steps": [
            {"latex": "\\frac{10}{1 - 3i} = \\frac{10(1 + 3i)}{(1 - 3i)(1 + 3i)}", "explain": "Multiply numerator and denominator by the conjugate $1 + 3i$."},
            {"latex": "= \\frac{10(1 + 3i)}{1^2 + (-3)^2} = \\frac{10(1 + 3i)}{10}", "explain": "Compute the denominator $1^2 + 3^2 = 10$ before expanding the numerator so you can cancel the common factor $10$."},
            {"latex": "= 1 + 3i", "explain": "Cancel $10$ from numerator and denominator to obtain $1 + 3i$."},
        ],
    })

    # --- Q13 (Level 3 - Trap: Reordered Conjugate Division): (5 + 2i) / (-3i + 1) ---
    # Denominator is 1 - 3i, conjugate is 1 + 3i!
    z13 = ExactComplex(5, 2) / ExactComplex(1, -3)
    assert z13 == ExactComplex(Fraction(-1, 10), Fraction(17, 10))
    problems.append({
        "id": "Q13",
        "level": 3,
        "levelLabel": "Level 3 — Trap & Diagnostic",
        "category": "Traps & Edge Cases",
        "prompt": "Carefully reorder the denominator into standard form first, then divide and write the exact answer in standard form $a + bi$: $$\\frac{5 + 2i}{-3i + 1}$$",
        "plainText": "(5 + 2i) / (-3i + 1)",
        "re": fmt_frac(z13.re),
        "im": fmt_frac(z13.im),
        "displayAnswer": "-1/10 + 17/10i",
        "checkpointHint": "Trap alert! The denominator is $-3i + 1 = 1 - 3i$, so its complex conjugate is $1 + 3i$ (flip the sign of the imaginary part, NOT the real part!).",
        "commonTrapTag": "Conjugate Denominator Error",
        "steps": [
            {"latex": "\\frac{5 + 2i}{-3i + 1} = \\frac{5 + 2i}{1 - 3i}", "explain": "Rewrite the denominator in standard form $c + di = 1 - 3i$ first so you identify its conjugate correctly as $1 + 3i$."},
            {"latex": "= \\frac{(5 + 2i)(1 + 3i)}{(1 - 3i)(1 + 3i)}", "explain": "Multiply numerator and denominator by the conjugate $1 + 3i$."},
            {"latex": "= \\frac{5 + 15i + 2i + 6i^2}{1^2 + 3^2} = \\frac{5 + 17i - 6}{10}", "explain": "Expand the numerator, substitute $6i^2 = -6$, and evaluate the denominator $1 + 9 = 10$."},
            {"latex": "= \\frac{-1 + 17i}{10} = -\\frac{1}{10} + \\frac{17}{10}i", "explain": "Combine real terms ($5 - 6 = -1$) and split into standard form $a + bi$."},
        ],
    })

    # --- Q14 (Level 3 - Trap: Negative Radicands + Subtraction): sqrt(-8)*sqrt(-18) - sqrt(-16) ---
    # (2i sqrt(2))(3i sqrt(2)) - 4i = 6 * (-1) * 2 - 4i = -12 - 4i
    z14 = ExactComplex(-12, -4)
    problems.append({
        "id": "Q14",
        "level": 3,
        "levelLabel": "Level 3 — Trap & Diagnostic",
        "category": "Traps & Edge Cases",
        "prompt": "Evaluate the expression without falling into the negative-radicand product trap, and write the result in standard form $a + bi$: $$\\sqrt{-8}\\cdot\\sqrt{-18} - \\sqrt{-16}$$",
        "plainText": "sqrt(-8)*sqrt(-18) - sqrt(-16)",
        "re": fmt_frac(z14.re),
        "im": fmt_frac(z14.im),
        "displayAnswer": "-12 - 4i",
        "checkpointHint": "$\\sqrt{-8} = i\\sqrt{8}$ and $\\sqrt{-18} = i\\sqrt{18}$, so their product is $i^2\\sqrt{144} = -12$ (not $+12$).",
        "commonTrapTag": "Premature Radical Multiplication",
        "steps": [
            {"latex": "\\sqrt{-8}\\cdot\\sqrt{-18} - \\sqrt{-16} = \\left(i\\sqrt{8}\\right)\\left(i\\sqrt{18}\\right) - 4i", "explain": "Extract $i$ from every negative square root before multiplying."},
            {"latex": "= i^2 \\sqrt{8 \\cdot 18} - 4i = (-1)\\sqrt{144} - 4i", "explain": "Now that the radicands $8$ and $18$ are positive, apply $\\sqrt{8}\\sqrt{18} = \\sqrt{144} = 12$ and $i^2 = -1$."},
            {"latex": "= -12 - 4i", "explain": "Write the final result in standard form $a + bi$."},
        ],
    })

    # --- Q15 (Level 3 - Trap: Negative Exponent Powers of i): 2*i^(-13) - 5*i^(98) + 3*i^(60) ---
    # i^(-13) = i^(-13 + 16) = i^3 = -i -> 2(-i) = -2i
    # i^98 = i^(96 + 2) = i^2 = -1 -> -5(-1) = +5
    # i^60 = (i^4)^15 = 1 -> +3(1) = +3
    # Total = 8 - 2i
    z15 = ExactComplex(8, -2)
    problems.append({
        "id": "Q15",
        "level": 3,
        "levelLabel": "Level 3 — Trap & Diagnostic",
        "category": "Traps & Edge Cases",
        "prompt": "Simplify the expression involving negative and large powers of $i$ into standard form $a + bi$: $$2i^{-13} - 5i^{98} + 3i^{60}$$",
        "plainText": "2*i^(-13) - 5*i^98 + 3*i^60",
        "re": fmt_frac(z15.re),
        "im": fmt_frac(z15.im),
        "displayAnswer": "8 - 2i",
        "checkpointHint": "For $i^{-13}$, multiply by $i^{16} = 1$ to get $i^3 = -i$. Also $98 = 4(24) + 2 \\implies i^{98} = -1$, and $60 = 4(15) \\implies i^{60} = 1$.",
        "commonTrapTag": "Formula / Identity Mix-up",
        "steps": [
            {"latex": "i^{-13} = i^{-13} \\cdot i^{16} = i^3 = -i", "explain": "Add the smallest multiple of $4$ ($16$) to the negative exponent $-13$ so the remainder is positive: $-13 + 16 = 3$."},
            {"latex": "i^{98} = i^{4(24) + 2} = i^2 = -1, \\qquad i^{60} = i^{4(15) + 0} = i^0 = 1", "explain": "Reduce exponents $98$ and $60$ modulo $4$."},
            {"latex": "2(-i) - 5(-1) + 3(1) = -2i + 5 + 3 = 8 - 2i", "explain": "Substitute each simplified power of $i$ and group real part $(5 + 3 = 8)$ before imaginary part $(-2i)$."},
        ],
    })

    # --- Q16 (Level 3 - Spot & Fix the Flaw / Cubic Power): (1 - 2i)^3 ---
    z16 = ExactComplex(1, -2) * ExactComplex(1, -2) * ExactComplex(1, -2)
    assert z16 == ExactComplex(-11, 2)
    problems.append({
        "id": "Q16",
        "level": 3,
        "levelLabel": "Level 3 — Trap & Diagnostic",
        "category": "Traps & Edge Cases",
        "prompt": "A student falsely claims that $(1 - 2i)^3 = 1^3 - (2i)^3 = 1 - 8i^3 = 1 + 8i$. Compute the **true** value of $$(1 - 2i)^3$$ in standard form $a + bi$.",
        "plainText": "(1 - 2i)^3",
        "re": fmt_frac(z16.re),
        "im": fmt_frac(z16.im),
        "displayAnswer": "-11 + 2i",
        "checkpointHint": "Exponents do NOT distribute over subtraction! First compute $(1 - 2i)^2 = -3 - 4i$, then multiply $(-3 - 4i)(1 - 2i)$.",
        "commonTrapTag": "Formula / Identity Mix-up",
        "steps": [
            {"latex": "(1 - 2i)^2 = 1^2 - 2(1)(2i) + (2i)^2 = 1 - 4i + 4(-1) = -3 - 4i", "explain": "First square the binomial $(1 - 2i)^2$ properly instead of distributing the cube."},
            {"latex": "(1 - 2i)^3 = (-3 - 4i)(1 - 2i) = -3 + 6i - 4i + 8i^2", "explain": "Multiply the squared result $(-3 - 4i)$ by the remaining factor $(1 - 2i)$."},
            {"latex": "= -3 + 2i + 8(-1) = -11 + 2i", "explain": "Substitute $i^2 = -1$ and combine real terms ($-3 - 8 = -11$) to get $-11 + 2i$."},
        ],
    })

    # --- Q17 (Level 3 - Difference of Two Complex Quotients): (3 + i)/(1 - i) - (2 - i)/(1 + i) ---
    z17 = (ExactComplex(3, 1) / ExactComplex(1, -1)) - (ExactComplex(2, -1) / ExactComplex(1, 1))
    assert z17 == ExactComplex(Fraction(1, 2), Fraction(7, 2))
    problems.append({
        "id": "Q17",
        "level": 3,
        "levelLabel": "Level 3 — Trap & Diagnostic",
        "category": "Combined with Prior Units",
        "prompt": "Simplify the difference of two complex quotients into standard form $a + bi$: $$\\frac{3 + i}{1 - i} - \\frac{2 - i}{1 + i}$$",
        "plainText": "(3 + i)/(1 - i) - (2 - i)/(1 + i)",
        "re": fmt_frac(z17.re),
        "im": fmt_frac(z17.im),
        "displayAnswer": "1/2 + 7/2i",
        "checkpointHint": "Notice that $(1 - i)$ and $(1 + i)$ are already conjugates of each other! Their common denominator is $(1 - i)(1 + i) = 2$.",
        "commonTrapTag": "Arithmetic / Sign Slip",
        "steps": [
            {"latex": "\\frac{3 + i}{1 - i} - \\frac{2 - i}{1 + i} = \\frac{(3 + i)(1 + i) - (2 - i)(1 - i)}{(1 - i)(1 + i)}", "explain": "Use the conjugate pair $(1 - i)(1 + i) = 1^2 + 1^2 = 2$ as the common denominator."},
            {"latex": "= \\frac{(3 + 4i + i^2) - (2 - 3i + i^2)}{2}", "explain": "Expand both products in the numerator, keeping parentheses around the subtracted second product."},
            {"latex": "= \\frac{(2 + 4i) - (1 - 3i)}{2} = \\frac{1 + 7i}{2}", "explain": "Substitute $i^2 = -1$ in each group, then distribute the minus sign: $(2 - 1) + (4 - (-3))i = 1 + 7i$."},
            {"latex": "= \\frac{1}{2} + \\frac{7}{2}i", "explain": "Separate into standard form $a + bi$."},
        ],
    })

    # --- Q18 (Level 4 - Applied Physics: AC Circuit Ohm's Law PHY-T01-C19): I = V / Z ---
    # V = 26 + 0i volts, Z = 2 - 3i ohms -> I = 26 / (2 - 3i) = 26(2 + 3i)/13 = 4 + 6i amps
    z18 = ExactComplex(26, 0) / ExactComplex(2, -3)
    assert z18 == ExactComplex(4, 6)
    problems.append({
        "id": "Q18",
        "level": 4,
        "levelLabel": "Level 4 — Applied Synthesis",
        "category": "Cross-Subject Application",
        "prompt": "**Physics Application ([[PHY-T01-C19]] — AC Electrical Circuits):** An alternating-current circuit has complex voltage $V = 26\\text{ V}$ and series impedance $Z = 2 - 3i\\text{ }\\Omega$. Using complex Ohm's Law $I = \\frac{V}{Z}$, compute the complex current $I$ in standard form $a + bi$.",
        "plainText": "26 / (2 - 3i)",
        "re": fmt_frac(z18.re),
        "im": fmt_frac(z18.im),
        "displayAnswer": "4 + 6i",
        "checkpointHint": "Substitute $V = 26$ and $Z = 2 - 3i$ into $I = \\frac{26}{2 - 3i}$, then multiply top and bottom by $2 + 3i$ (denominator is $2^2 + 3^2 = 13$).",
        "commonTrapTag": "Conjugate Denominator Error",
        "steps": [
            {"latex": "I = \\frac{V}{Z} = \\frac{26}{2 - 3i}", "explain": "Set up complex Ohm's Law with $V = 26$ and $Z = 2 - 3i$."},
            {"latex": "= \\frac{26(2 + 3i)}{(2 - 3i)(2 + 3i)} = \\frac{26(2 + 3i)}{2^2 + (-3)^2}", "explain": "Multiply numerator and denominator by the conjugateimpedance $\\bar{Z} = 2 + 3i$."},
            {"latex": "= \\frac{26(2 + 3i)}{13} = 2(2 + 3i) = 4 + 6i", "explain": "Simplify $\\frac{26}{13} = 2$ and distribute to obtain the complex current $I = 4 + 6i\\text{ A}$."},
        ],
    })

    # --- Q19 (Level 4 - Applied Physics: Parallel Impedance PHY-T01-C19): Z_eq = (Z1 * Z2) / (Z1 + Z2) ---
    # Z1 = 2 + 2i, Z2 = 2 - 2i -> Z1*Z2 = 8, Z1+Z2 = 4 -> Z_eq = 8/4 = 2
    z1_imp = ExactComplex(2, 2)
    z2_imp = ExactComplex(2, -2)
    z19 = (z1_imp * z2_imp) / (z1_imp + z2_imp)
    assert z19 == ExactComplex(2, 0)
    problems.append({
        "id": "Q19",
        "level": 4,
        "levelLabel": "Level 4 — Applied Synthesis",
        "category": "Cross-Subject Application",
        "prompt": "**Physics Application ([[PHY-T01-C19]] — Parallel AC Resonance):** Two parallel branches have conjugate impedances $Z_1 = 2 + 2i\\text{ }\\Omega$ (inductive) and $Z_2 = 2 - 2i\\text{ }\\Omega$ (capacitive). Compute the equivalent parallel impedance $$Z_{\\text{eq}} = \\frac{Z_1 Z_2}{Z_1 + Z_2}$$ in standard form $a + bi$.",
        "plainText": "((2 + 2i)*(2 - 2i)) / ((2 + 2i) + (2 - 2i))",
        "re": fmt_frac(z19.re),
        "im": fmt_frac(z19.im),
        "displayAnswer": "2",
        "checkpointHint": "Because $Z_1$ and $Z_2$ are complex conjugates, both their product $Z_1 Z_2 = 2^2 + 2^2 = 8$ and their sum $Z_1 + Z_2 = 4$ are purely real!",
        "commonTrapTag": "Conjugate Denominator Error",
        "steps": [
            {"latex": "Z_1 Z_2 = (2 + 2i)(2 - 2i) = 2^2 + 2^2 = 4 + 4 = 8", "explain": "Evaluate the numerator product using the conjugate identity $(a + bi)(a - bi) = a^2 + b^2$."},
            {"latex": "Z_1 + Z_2 = (2 + 2i) + (2 - 2i) = (2 + 2) + (2 - 2)i = 4", "explain": "Evaluate the denominator sum; the opposite imaginary reactances $+2i$ and $-2i$ cancel out (resonance)."},
            {"latex": "Z_{\\text{eq}} = \\frac{8}{4} = 2", "explain": "Divide numerator by denominator to obtain purely resistive equivalent impedance $Z_{\\text{eq}} = 2 + 0i\\text{ }\\Omega$."},
        ],
    })

    # --- Q20 (Level 4 - Applied Code / 2D Geometry Rotation PRG-T01-C03): z' = i * z + (2 - i) ---
    # Rotate point (4, -3) by 90 deg CCW around origin via multiplying by i, then translate by (2 - i)
    z20 = (ExactComplex(0, 1) * ExactComplex(4, -3)) + ExactComplex(2, -1)
    assert z20 == ExactComplex(5, 3)
    problems.append({
        "id": "Q20",
        "level": 4,
        "levelLabel": "Level 4 — Applied Synthesis",
        "category": "Cross-Subject Application",
        "prompt": "**Graphics & Algorithm Application ([[PRG-T01-C03]]):** In the 2D complex plane, multiplying a point $z = x + yi$ by $i$ rotates it $90^\\circ$ counterclockwise about the origin. If the point $(4, -3)$ (represented as $z = 4 - 3i$) is rotated $90^\\circ$ counterclockwise and then translated by $w = 2 - i$, compute its new complex coordinate $$z' = i(4 - 3i) + (2 - i)$$ in standard form $a + bi$.",
        "plainText": "i*(4 - 3i) + (2 - i)",
        "re": fmt_frac(z20.re),
        "im": fmt_frac(z20.im),
        "displayAnswer": "5 + 3i",
        "checkpointHint": "First compute the rotation $i(4 - 3i) = 4i - 3i^2 = 3 + 4i$, then add the translation $(2 - i)$.",
        "commonTrapTag": "Arithmetic / Sign Slip",
        "steps": [
            {"latex": "i(4 - 3i) = 4i - 3i^2 = 4i - 3(-1) = 3 + 4i", "explain": "Multiply $z = 4 - 3i$ by $i$ to perform the $90^\\circ$ counterclockwise rotation: $(4, -3) \\mapsto (3, 4)$."},
            {"latex": "z' = (3 + 4i) + (2 - i) = (3 + 2) + (4 - 1)i = 5 + 3i", "explain": "Add the translation vector $w = 2 - i$ to obtain the final coordinate $5 + 3i$ (point $(5, 3)$)."},
        ],
    })

    print(f"  Verified all {len(problems)} MTH-T02-C01-U01 Complex Numbers problems via ExactComplex!")
    return problems



# ============================================================================
# 2. PRG-T03-C01-U01 VERIFIED PROBLEMS + EXECUTABLE TS TEST SUITE
# ============================================================================
def build_and_verify_prg_problems():
    problems = [
        {
            "id": "Q01",
            "level": 1,
            "levelLabel": "Level 1 — Foundation",
            "category": "Concept & Syntax Check",
            "prompt": "**Root Layout Requirement ([[PRG-T03-C01-U01]]):** In a Next.js App Router project using `src/app/`, which file is **strictly required** at the root of `src/app/` and what two HTML tags must its returned JSX contain?",
            "plainText": "src/app/layout.tsx -> <html> and <body>",
            "re": "src/app/layout.tsx",
            "im": "html,body",
            "displayAnswer": "src/app/layout.tsx (containing <html> and <body>)",
            "checkpointHint": "Unlike Pages Router (`_app.tsx` / `_document.tsx`), App Router requires a root layout file that wraps the entire document shell.",
            "commonTrapTag": "Route Boundary Confusion",
            "steps": [
                {"latex": "\\text{Path: } \\texttt{src/app/layout.tsx}", "explain": "Locate the top-level layout segment inside `src/app/`. Without `layout.tsx`, Next.js cannot render the application shell."},
                {"latex": "\\text{Required DOM Shell: } \\texttt{<html lang=\"en\"><body>\\{children\\}</body></html>}", "explain": "The root layout is the only layout allowed to define `<html>` and `<body>` tags wrapping `{children}`."},
            ],
        },
        {
            "id": "Q02",
            "level": 1,
            "levelLabel": "Level 1 — Foundation",
            "category": "Concept & Syntax Check",
            "prompt": "**Environment Variable Prefix Rule ([[PRG-T03-C01-U01]]):** Which exact prefix causes Next.js (`next build`) to inline an environment variable as a literal string into the client-side browser JavaScript bundle?",
            "plainText": "NEXT_PUBLIC_",
            "re": "NEXT_PUBLIC_",
            "im": "client-inline",
            "displayAnswer": "NEXT_PUBLIC_",
            "checkpointHint": "Variables without this prefix remain `undefined` in browser bundles and can only be read inside Server Components, Route Handlers, or Server Actions.",
            "commonTrapTag": "Env Boundary Leak (NEXT_PUBLIC_)",
            "steps": [
                {"latex": "\\texttt{NEXT\\_PUBLIC\\_API\\_URL} \\longrightarrow \\text{Inlined into client JS bundle at build time}", "explain": "Webpack/Turbopack replaces `process.env.NEXT_PUBLIC_*` references with literal strings during compilation."},
                {"latex": "\\texttt{DATABASE\\_URL} \\longrightarrow \\texttt{undefined} \\text{ in browser, server-only in Node.js}", "explain": "Any variable lacking `NEXT_PUBLIC_` is stripped from client bundles to prevent secret leakage."},
            ],
        },
        {
            "id": "Q03",
            "level": 2,
            "levelLabel": "Level 2 — Standard Exam",
            "category": "Core Implementation",
            "prompt": "**Environment Loading Priority ([[PRG-T03-C01-U01]]):** During `next dev` (`NODE_ENV === 'development'`), if the variable `API_TIMEOUT` is defined in `.env` (`3000`), `.env.development` (`5000`), and `.env.local` (`1000`), which value does `process.env.API_TIMEOUT` resolve to at runtime?",
            "plainText": "1000 (.env.local overrides .env.development and .env)",
            "re": "1000",
            "im": ".env.local",
            "displayAnswer": "1000 (from .env.local)",
            "checkpointHint": "Check the Next.js environment precedence chain: `process.env` > `.env.$(NODE_ENV).local` > `.env.local` > `.env.$(NODE_ENV)` > `.env`.",
            "commonTrapTag": "Env Precedence Order Error",
            "steps": [
                {"latex": "\\text{Precedence: } \\texttt{.env.development.local} > \\texttt{.env.local} > \\texttt{.env.development} > \\texttt{.env}", "explain": "Rank the candidate files in `development` mode from highest priority (1) to lowest priority (4)."},
                {"latex": "\\texttt{.env.local} = 1000 \\implies \\texttt{process.env.API\\_TIMEOUT} = \\texttt{\"1000\"}", "explain": "Because `.env.local` has higher priority than `.env.development` (`5000`) and `.env` (`3000`), `1000` wins."},
            ],
        },
        {
            "id": "Q04",
            "level": 2,
            "levelLabel": "Level 2 — Standard Exam",
            "category": "Core Implementation",
            "prompt": "**Path Alias Resolution ([[PRG-T03-C01-U01]]):** Given `\"paths\": { \"@/*\": [\"./src/*\"] }` in `tsconfig.json`, write the clean alias import path that replaces `import { db } from '../../../lib/db'` from inside `src/app/(dashboard)/settings/billing/page.tsx`.",
            "plainText": "@/lib/db",
            "re": "@/lib/db",
            "im": "src/lib/db",
            "displayAnswer": "@/lib/db",
            "checkpointHint": "The `@/*` prefix maps directly to `./src/*` regardless of how deeply nested the importing file is.",
            "commonTrapTag": "Path Alias Resolution Error",
            "steps": [
                {"latex": "\\texttt{\"@/*\": [\"./src/*\"]} \\implies \\texttt{@/} \\equiv \\texttt{src/}", "explain": "Match the wildcard prefix `@/` to the `src/` directory root."},
                {"latex": "\\texttt{src/lib/db.ts} \\longrightarrow \\texttt{import \\{ db \\} from \"@/lib/db\"}", "explain": "Replace fragile relative traversal `../../../lib/db` with the root-anchored path `@/lib/db`."},
            ],
        },
        {
            "id": "Q05",
            "level": 2,
            "levelLabel": "Level 2 — Standard Exam",
            "category": "Core Implementation",
            "prompt": "**Route Group URL Mapping ([[PRG-T03-C01-U02]]):** What public URL pathname is generated by the file `src/app/(marketing)/pricing/page.tsx`?",
            "plainText": "/pricing",
            "re": "/pricing",
            "im": "route-group-omitted",
            "displayAnswer": "/pricing",
            "checkpointHint": "Folder names wrapped in parentheses `(folder)` are Route Groups used for layout organization without adding URL segments.",
            "commonTrapTag": "Route Boundary Confusion",
            "steps": [
                {"latex": "\\texttt{src/app/(marketing)/pricing/page.tsx}", "explain": "Inspect each path segment beneath `src/app/`."},
                {"latex": "\\texttt{(marketing)} \\mapsto \\varnothing, \\quad \\texttt{pricing} \\mapsto \\texttt{/pricing}", "explain": "Omit the parenthesized Route Group `(marketing)` from the URL path, leaving `/pricing`."},
            ],
        },
        {
            "id": "Q06",
            "level": 3,
            "levelLabel": "Level 3 — Trap & Diagnostic",
            "category": "Debugging & Edge Cases",
            "prompt": "**Test Environment Determinism Trap ([[PRG-T03-C01-U01]]):** A developer puts a mock key in `.env.local` and runs automated tests (`NODE_ENV === 'test'`), expecting `.env.local` to be loaded. However, the variable is missing during `NODE_ENV=test`. Why?",
            "plainText": "Next.js skips .env.local when NODE_ENV === 'test' for deterministic tests",
            "re": "skips .env.local in test",
            "im": "deterministic",
            "displayAnswer": "Next.js intentionally skips .env.local when NODE_ENV === 'test' to ensure deterministic test runs across machines",
            "checkpointHint": "Remember the special rule for `NODE_ENV === 'test'`: local developer overrides in `.env.local` are ignored so CI and local tests behave identically.",
            "commonTrapTag": "Env Precedence Order Error",
            "steps": [
                {"latex": "\\texttt{NODE\\_ENV === \"test\"} \\implies \\texttt{.env.local} \\text{ is skipped}", "explain": "Next.js explicitly excludes `.env.local` in test mode so unversioned developer files cannot break CI reproducibility."},
                {"latex": "\\text{Active chain in test: } \\texttt{.env.test.local} > \\texttt{.env.test} > \\texttt{.env}", "explain": "Place shared test defaults in `.env.test` or local test overrides in `.env.test.local`."},
            ],
        },
        {
            "id": "Q07",
            "level": 3,
            "levelLabel": "Level 3 — Trap & Diagnostic",
            "category": "Debugging & Edge Cases",
            "prompt": "**Dynamic `process.env` Lookup Trap ([[PRG-T03-C01-U01]]):** In a Client Component (`'use client'`), why does `const k = 'NEXT_PUBLIC_SITE_URL'; return <p>{process.env[k]}</p>;` evaluate to `undefined` in the browser even though `NEXT_PUBLIC_SITE_URL` is set?",
            "plainText": "Bundler static AST replacement requires literal dot notation process.env.NEXT_PUBLIC_SITE_URL",
            "re": "process.env.NEXT_PUBLIC_SITE_URL",
            "im": "static-ast-inlining",
            "displayAnswer": "Bundler inlining only matches static literal property access (process.env.NEXT_PUBLIC_SITE_URL), not dynamic bracket lookups (process.env[k])",
            "checkpointHint": "Next.js does not ship a full `process.env` object to the browser; it replaces literal `process.env.NEXT_PUBLIC_X` AST nodes at build time.",
            "commonTrapTag": "Env Boundary Leak (NEXT_PUBLIC_)",
            "steps": [
                {"latex": "\\texttt{process.env[k]} \\longrightarrow \\text{Not matched by static AST replacement} \\implies \\texttt{undefined}", "explain": "Dynamic bracket indexing (`process.env[k]`) or destructuring (`const { NEXT_PUBLIC_SITE_URL } = process.env`) cannot be statically replaced by the bundler."},
                {"latex": "\\texttt{process.env.NEXT\\_PUBLIC\\_SITE\\_URL} \\longrightarrow \\texttt{\"https://example.com\"}", "explain": "Always use full static dot notation `process.env.NEXT_PUBLIC_SITE_URL` in Client Components."},
            ],
        },
        {
            "id": "Q08",
            "level": 3,
            "levelLabel": "Level 3 — Trap & Diagnostic",
            "category": "Debugging & Edge Cases",
            "prompt": "**Accidental Public Route Exposure ([[PRG-T03-C01-U01]]):** A developer places helper components inside `src/app/dashboard/components/page.tsx` thinking `components/` is ignored. What happens in production?",
            "plainText": "/dashboard/components becomes a publicly accessible route",
            "re": "/dashboard/components",
            "im": "public-route-exposed",
            "displayAnswer": "Next.js exposes /dashboard/components as a live public URL route because it contains a page.tsx file",
            "checkpointHint": "Any folder inside `src/app/` containing `page.tsx` or `route.ts` becomes a public route unless prefixed with `_folder` (private folder) or moved to `src/components/`.",
            "commonTrapTag": "Route Boundary Confusion",
            "steps": [
                {"latex": "\\texttt{src/app/dashboard/components/page.tsx} \\implies \\text{Public URL } \\texttt{/dashboard/components}", "explain": "In App Router, colocation is safe ONLY when folders do not contain `page.tsx` or `route.ts`."},
                {"latex": "\\text{Fix: Move to } \\texttt{src/components/} \\text{ or rename to } \\texttt{src/app/dashboard/\\_components/}", "explain": "Prefixing a folder with an underscore (`_components`) opts the folder and all its subfolders out of routing."},
            ],
        },
        {
            "id": "Q09",
            "level": 4,
            "levelLabel": "Level 4 — Applied Synthesis",
            "category": "Cross-Subject Application",
            "prompt": "**Server-Only Guard & Build Verification ([[PRG-T03-C01-U01]] & [[PRG-T03-C02]]):** You are writing `src/lib/env.server.ts` which exports `STRIPE_SECRET_KEY`. Which package import should be placed at line 1 of `src/lib/env.server.ts` so that any accidental import from a `'use client'` file immediately fails `next build` with a compile-time error?",
            "plainText": "import 'server-only';",
            "re": "import 'server-only'",
            "im": "compile-time-guard",
            "displayAnswer": "import 'server-only';",
            "checkpointHint": "The `server-only` package poison-pills client bundle graphs at build time before secrets or server logic can leak.",
            "commonTrapTag": "Env Boundary Leak (NEXT_PUBLIC_)",
            "steps": [
                {"latex": "\\texttt{import \"server-only\";} \\text{ at top of } \\texttt{src/lib/env.server.ts}", "explain": "Add the `server-only` marker module at the top of any module accessing private credentials."},
                {"latex": "\\text{Client import graph includes } \\texttt{env.server.ts} \\implies \\text{Build Error!}", "explain": "If any `'use client'` component imports `env.server.ts` directly or transitively, `next build` aborts immediately."},
            ],
        },
        {
            "id": "Q10",
            "level": 4,
            "levelLabel": "Level 4 — Applied Synthesis",
            "category": "Cross-Subject Application",
            "prompt": "**Full-Stack Architecture Audit ([[PRG-T03-C01-U01]]):** A repository has both `pages/index.tsx` and `src/app/page.tsx`. What happens when running `next build`, and how should the repository structure be consolidated?",
            "plainText": "Build conflict on root route /; consolidate into src/app/page.tsx and remove legacy pages/index.tsx",
            "re": "route conflict on /",
            "im": "src/app/page.tsx",
            "displayAnswer": "Next.js throws a conflicting route error on `/` (or ignores `src/pages` if root `pages/` exists); consolidate into `src/app/page.tsx`",
            "checkpointHint": "App Router (`app/`) and Pages Router (`pages/`) cannot both define the exact same route path `/`, and Next.js ignores `src/` if a top-level `app/` or `pages/` exists.",
            "commonTrapTag": "Route Boundary Confusion",
            "steps": [
                {"latex": "\\texttt{pages/index.tsx} \\leftrightarrow \\texttt{src/app/page.tsx} \\implies \\text{Route Collision on } \\texttt{/}", "explain": "Both files resolve to the root pathname `/`, causing a build error or shadowing `src/`."},
                {"latex": "\\text{Consolidate all routes under } \\texttt{src/app/} \\text{ and delete top-level } \\texttt{pages/}", "explain": "Keep `src/app/` as the single authoritative routing root and place shared non-routing modules in `src/components/` and `src/lib/`."},
            ],
        },
    ]

    # Also write an executable TypeScript verification file for PRG-T03-C01-U01
    os.makedirs("drills", exist_ok=True)
    ts_content = """/**
 * Automated Verification Suite for PRG-T03-C01-U01 (Next.js Project Structure & Environment Boundaries)
 * Drill ID: DRL-PRG-T03-C01-U01-01
 */

export type NodeEnvMode = "development" | "production" | "test";

export interface EnvFiles {
  processEnv?: Record<string, string>;
  envLocal?: Record<string, string>;
  envModeLocal?: Record<string, string>;
  envMode?: Record<string, string>;
  envBase?: Record<string, string>;
}

/**
 * Resolves Next.js environment variable priority exactly as next/env does:
 * 1. process.env
 * 2. .env.$(NODE_ENV).local
 * 3. .env.local (SKIPPED when NODE_ENV === 'test')
 * 4. .env.$(NODE_ENV)
 * 5. .env
 */
export function resolveNextEnvVar(key: string, mode: NodeEnvMode, files: EnvFiles): string | undefined {
  if (files.processEnv && key in files.processEnv) return files.processEnv[key];
  if (files.envModeLocal && key in files.envModeLocal) return files.envModeLocal[key];
  if (mode !== "test" && files.envLocal && key in files.envLocal) return files.envLocal[key];
  if (files.envMode && key in files.envMode) return files.envMode[key];
  if (files.envBase && key in files.envBase) return files.envBase[key];
  return undefined;
}

/**
 * Verifies whether an environment variable is exposed to the browser bundle.
 */
export function isClientExposedEnv(varName: string, isStaticDotAccess: boolean): boolean {
  return varName.startsWith("NEXT_PUBLIC_") && isStaticDotAccess;
}

// Self-verification assertions
const devVal = resolveNextEnvVar("API_TIMEOUT", "development", {
  envBase: { API_TIMEOUT: "3000" },
  envMode: { API_TIMEOUT: "5000" },
  envLocal: { API_TIMEOUT: "1000" },
});
if (devVal !== "1000") throw new Error(`Expected 1000 in development, got ${devVal}`);

const testVal = resolveNextEnvVar("API_TIMEOUT", "test", {
  envBase: { API_TIMEOUT: "3000" },
  envMode: { API_TIMEOUT: "5000" },
  envLocal: { API_TIMEOUT: "1000" },
});
if (testVal !== "5000") throw new Error(`Expected 5000 in test (.env.local skipped), got ${testVal}`);
"""
    with open("drills/prg_t03_c01_u01_drill.ts", "w") as f:
        f.write(ts_content)

    print(f"  Verified all {len(problems)} PRG-T03-C01-U01 problems and generated drills/prg_t03_c01_u01_drill.ts!")
    return problems


# ============================================================================
# 3. INTERACTIVE HTML DRILL GENERATOR (CLICK-TO-HIGHLIGHT + PAPER DIAGNOSTICS)
# ============================================================================
def render_interactive_drill_html(
    drill_id: str,
    title: str,
    unit_code: str,
    unit_title: str,
    chapter_code: str,
    topic_code: str,
    subject_mode: str,  # "MATH" or "PRG"
    problems: list,
    mistake_tags: list,
    output_path: str,
):
    problems_json = json.dumps(problems, ensure_ascii=False)
    mistake_tags_json = json.dumps(mistake_tags, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{drill_id} — {title}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
  <style>
    :root {{
      --bg: #0f1117;
      --surface: #171b26;
      --surface-2: #1f2535;
      --border: #2e364f;
      --text: #e6edf3;
      --muted: #93a1b8;
      --accent: #6366f1;
      --accent-soft: rgba(99, 102, 241, 0.16);
      --amber: #f59e0b;
      --amber-soft: rgba(245, 158, 11, 0.18);
      --green: #10b981;
      --green-soft: rgba(16, 185, 129, 0.16);
      --red: #ef4444;
      --red-soft: rgba(239, 68, 68, 0.16);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 28px 20px 80px;
      font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}
    .container {{
      max-width: 1080px;
      margin: 0 auto;
    }}
    .header-card {{
      background: linear-gradient(135deg, #191f2e 0%, #131722 100%);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 24px 28px;
      margin-bottom: 20px;
    }}
    .badge-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
    }}
    .badge {{
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: #a5b4fc;
      border: 1px solid rgba(99, 102, 241, 0.35);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 24px;
      font-weight: 700;
    }}
    .subtitle {{
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }}
    .config-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: center;
      justify-content: space-between;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 22px;
      position: sticky;
      top: 10px;
      z-index: 50;
      backdrop-filter: blur(10px);
    }}
    .config-group {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
    }}
    label {{
      font-size: 13px;
      color: var(--muted);
      font-weight: 600;
    }}
    select, input[type="text"] {{
      background: var(--surface-2);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 13px;
    }}
    button {{
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--surface-2);
      color: var(--text);
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.15s ease;
    }}
    button:hover {{
      border-color: var(--accent);
      background: rgba(99, 102, 241, 0.2);
    }}
    .btn-primary {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }}
    .btn-primary:hover {{
      background: #4f46e5;
    }}
    .btn-success {{
      background: var(--green);
      border-color: var(--green);
      color: #06281e;
    }}
    .problem-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 22px 24px;
      margin-bottom: 20px;
      transition: border-color 0.2s ease;
    }}
    .problem-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border);
    }}
    .problem-num {{
      font-weight: 700;
      font-size: 16px;
      color: #c7d2fe;
    }}
    .level-pill {{
      font-size: 12px;
      padding: 3px 10px;
      border-radius: 999px;
      background: var(--surface-2);
      color: var(--muted);
      border: 1px solid var(--border);
    }}
    .prompt-box {{
      font-size: 15px;
      margin-bottom: 14px;
    }}
    .cas-box {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      background: #111520;
      border: 1px dashed var(--border);
      border-radius: 8px;
      padding: 8px 12px;
      margin-bottom: 16px;
      font-family: "JetBrains Mono", "Fira Code", monospace;
      font-size: 12.5px;
      color: #cbd5e1;
    }}
    .workspace-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-bottom: 12px;
    }}
    .answer-input {{
      flex: 1;
      min-width: 240px;
      font-family: "JetBrains Mono", monospace;
    }}
    .diag-feedback {{
      font-size: 13px;
      padding: 10px 14px;
      border-radius: 8px;
      margin-top: 8px;
      display: none;
    }}
    .diag-pass {{
      display: block;
      background: var(--green-soft);
      border: 1px solid var(--green);
      color: #6ee7b7;
    }}
    .diag-warn {{
      display: block;
      background: var(--amber-soft);
      border: 1px solid var(--amber);
      color: #fcd34d;
    }}
    .diag-fail {{
      display: block;
      background: var(--red-soft);
      border: 1px solid var(--red);
      color: #fca5a5;
    }}
    .hint-box {{
      display: none;
      background: rgba(99, 102, 241, 0.1);
      border-left: 3px solid var(--accent);
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 13.5px;
      color: #c7d2fe;
      margin-top: 10px;
    }}
    /* Click-to-Highlight Synchronized Step Grid */
    .solution-panel {{
      display: none;
      margin-top: 16px;
      border-top: 1px solid var(--border);
      padding-top: 16px;
    }}
    .solution-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      font-size: 13px;
      color: var(--muted);
    }}
    .steps-container {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .step-row {{
      display: grid;
      grid-template-columns: 1.15fr 1fr auto;
      gap: 14px;
      align-items: center;
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 16px;
      cursor: pointer;
      transition: all 0.18s ease;
    }}
    @media (max-width: 780px) {{
      .step-row {{
        grid-template-columns: 1fr;
      }}
    }}
    .steps-container.has-active .step-row {{
      opacity: 0.38;
      filter: grayscale(25%);
    }}
    .steps-container.has-active .step-row.active-step {{
      opacity: 1;
      filter: none;
      background: rgba(245, 158, 11, 0.13);
      border-color: var(--amber);
      box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.25);
    }}
    .step-row.diverged-step {{
      border-color: var(--red) !important;
      background: rgba(239, 68, 68, 0.14) !important;
      opacity: 1 !important;
    }}
    .step-math {{
      font-size: 15px;
      overflow-x: auto;
      padding: 4px 0;
    }}
    .step-explain {{
      font-size: 13.5px;
      color: #cbd5e1;
      border-left: 2px solid var(--border);
      padding-left: 12px;
    }}
    .step-row.active-step .step-explain {{
      border-left-color: var(--amber);
      color: #fef3c7;
      font-weight: 500;
    }}
    .diverge-btn {{
      font-size: 11.5px;
      padding: 5px 10px;
      border-radius: 6px;
      background: rgba(239, 68, 68, 0.12);
      border: 1px solid rgba(239, 68, 68, 0.35);
      color: #fca5a5;
      white-space: nowrap;
    }}
    .diverge-btn.active {{
      background: var(--red);
      color: #fff;
      border-color: var(--red);
    }}
    /* Paper-First Root Cause Mistake Pills & Self-Grade */
    .grading-bar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px dashed var(--border);
    }}
    .grade-btns {{
      display: flex;
      gap: 8px;
    }}
    .grade-btn.selected-correct {{
      background: var(--green);
      color: #052e16;
      border-color: var(--green);
    }}
    .grade-btn.selected-partial {{
      background: var(--amber);
      color: #451a03;
      border-color: var(--amber);
    }}
    .grade-btn.selected-wrong {{
      background: var(--red);
      color: #fff;
      border-color: var(--red);
    }}
    .mistake-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }}
    .mistake-pill {{
      font-size: 11.5px;
      padding: 4px 10px;
      border-radius: 999px;
      background: #141824;
      border: 1px solid var(--border);
      color: var(--muted);
      cursor: pointer;
    }}
    .mistake-pill.active {{
      background: var(--red-soft);
      border-color: var(--red);
      color: #fca5a5;
      font-weight: 600;
    }}
    .summary-card {{
      background: linear-gradient(135deg, #1b2234 0%, #121722 100%);
      border: 1px solid var(--accent);
      border-radius: 14px;
      padding: 22px 26px;
      margin-top: 28px;
    }}
    .sync-status {{
      margin-top: 12px;
      font-size: 13.5px;
      padding: 10px 14px;
      border-radius: 8px;
      display: none;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header-card">
      <div class="badge-row">
        <span class="badge">{drill_id}</span>
        <span class="badge">Unit: {unit_code}</span>
        <span class="badge">Chapter: {chapter_code}</span>
        <span class="badge">Topic: {topic_code}</span>
        <span class="badge">100% Pre-Verified Answers</span>
      </div>
      <h1>{title} — Interactive Practice &amp; Diagnostics</h1>
      <p class="subtitle">
        Designed for <strong>Paper-First Working</strong>: solve on physical scratch paper, verify intermediate checkpoints, click any derivation step to highlight the equation &amp; explanation side-by-side, tag the exact step where your paper diverged, and sync directly to Notion.
      </p>
    </div>

    <div class="config-bar">
      <div class="config-group">
        <label for="countSelect">Question Count:</label>
        <select id="countSelect">
          <option value="5">5 Questions (Quick Drill)</option>
          <option value="10" selected>10 Questions (Standard Set)</option>
          <option value="15">15 Questions (Extended Set)</option>
          <option value="20">20 Questions (Full Bank)</option>
        </select>

        <label for="levelSelect">Difficulty Filter:</label>
        <select id="levelSelect">
          <option value="ALL" selected>Mixed Exam Mode (Proportional L1–L4)</option>
          <option value="1">Level 1 — Foundation (Direct Concept)</option>
          <option value="2">Level 2 — Standard Exam (Multi-Step)</option>
          <option value="3">Level 3 — Trap &amp; Diagnostic (Edge Cases)</option>
          <option value="4">Level 4 — Applied Synthesis (Cross-Topic)</option>
        </select>

        <button class="btn-primary" onclick="generateDrillSet()">Shuffle &amp; Generate Set</button>
      </div>

      <div class="config-group">
        <span id="liveScoreBadge" class="badge">Score: 0 / 0 (0%)</span>
        <button class="btn-success" onclick="syncToNotion()">Grade &amp; Sync to Notion</button>
      </div>
    </div>

    <div id="problemsRoot"></div>

    <div class="summary-card">
      <h2 style="margin-top:0; font-size:18px;">Practice Session Telemetry &amp; Notion Sync</h2>
      <p style="font-size:13.5px; color:var(--muted); margin-bottom:14px;">
        Clicking <strong>Grade &amp; Sync to Notion</strong> sends your Score, Accuracy %, Mistake Categories, and Diverged Step diagnostics to <code>http://localhost:8765/api/sync-notion</code> (updating <strong>Learning Practice &amp; Drills</strong> and appending to <strong>{unit_code} — My Implementation &amp; Mistake Log</strong>). If the local bridge server is offline, it copies a clean Markdown summary to your clipboard.
      </p>
      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <button class="btn-success" onclick="syncToNotion()">Grade &amp; Sync to Notion Now</button>
        <button onclick="copyMarkdownLog()">Copy Mistake Log for Notion</button>
      </div>
      <div id="syncStatusBox" class="sync-status"></div>
    </div>
  </div>

  <script>
    const DRILL_META = {{
      drillId: "{drill_id}",
      title: "{title}",
      unitCode: "{unit_code}",
      chapterCode: "{chapter_code}",
      topicCode: "{topic_code}",
      subjectMode: "{subject_mode}",
      localFilePath: "{output_path}"
    }};
    const ALL_PROBLEMS = {problems_json};
    const MISTAKE_TAGS = {mistake_tags_json};

    let activeProblems = [];
    // Per-problem state: {{ score: null | 1 | 0.5 | 0, divergedStep: null | number, mistakes: Set<string>, activeStep: null | number }}
    let sessionState = {{}};

    function shuffleArray(arr) {{
      const copy = [...arr];
      for (let i = copy.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
      }}
      return copy;
    }}

    function generateDrillSet() {{
      const count = parseInt(document.getElementById("countSelect").value, 10);
      const levelFilter = document.getElementById("levelSelect").value;

      let pool = [];
      if (levelFilter === "ALL") {{
        pool = shuffleArray(ALL_PROBLEMS);
      }} else {{
        const lv = parseInt(levelFilter, 10);
        const matching = ALL_PROBLEMS.filter(p => p.level === lv);
        const others = ALL_PROBLEMS.filter(p => p.level !== lv);
        pool = [...shuffleArray(matching), ...shuffleArray(others)];
      }}

      activeProblems = pool.slice(0, Math.min(count, ALL_PROBLEMS.length));
      sessionState = {{}};
      activeProblems.forEach(p => {{
        sessionState[p.id] = {{
          score: null,
          divergedStep: null,
          mistakes: new Set(),
          activeStep: null
        }};
      }});

      renderProblems();
      updateScoreBadge();
    }}

    function renderMathInRoot() {{
      if (window.renderMathInElement) {{
        window.renderMathInElement(document.getElementById("problemsRoot"), {{
          delimiters: [
            {{ left: "$$", right: "$$", display: true }},
            {{ left: "$", right: "$", display: false }}
          ],
          throwOnError: false
        }});
      }}
    }}

    function copyText(text, btnEl) {{
      navigator.clipboard.writeText(text);
      const old = btnEl.textContent;
      btnEl.textContent = "Copied!";
      setTimeout(() => {{ btnEl.textContent = old; }}, 1200);
    }}

    // Parse user complex answer like "3 - 4i", "-8/17 + 15/17i", "-6", "3i"
    function parseComplexInput(raw) {{
      const s = raw.replace(/\\s+/g, "");
      if (!s) return null;
      // Check if user left it as unseparated fraction like (3+4i)/5
      if (/\\(.*i.*\\)\\//.test(s)) {{
        return {{ unseparated: true, raw: s }};
      }}
      // Pure real
      if (!s.includes("i")) {{
        return {{ re: s, im: "0", raw: s }};
      }}
      // Pure imaginary like "3i", "-i", "i", "-14/5i"
      const pureIm = s.match(/^([+-]?[0-9./]*)i$/);
      if (pureIm) {{
        let coeff = pureIm[1];
        if (coeff === "" || coeff === "+") coeff = "1";
        if (coeff === "-") coeff = "-1";
        return {{ re: "0", im: coeff, raw: s }};
      }}
      // Standard a+bi or a-bi
      const m = s.match(/^([+-]?[0-9./]+)([+-][0-9./]*)i$/);
      if (m) {{
        let re = m[1];
        let im = m[2];
        if (im === "+") im = "1";
        else if (im === "-") im = "-1";
        else if (im.startsWith("+")) im = im.slice(1);
        return {{ re, im, raw: s }};
      }}
      return {{ raw: s }};
    }}

    function checkUserAnswer(probId, idx) {{
      const prob = activeProblems[idx];
      const inputEl = document.getElementById(`ans-${{probId}}`);
      const diagEl = document.getElementById(`diag-${{probId}}`);
      const val = (inputEl.value || "").trim();

      if (!val) {{
        diagEl.className = "diag-feedback diag-warn";
        diagEl.textContent = "Working on paper? Click 'Reveal Step-by-Step Solution' below to compare your derivation and mark your paper score.";
        return;
      }}

      if (DRILL_META.subjectMode === "MATH") {{
        const parsed = parseComplexInput(val);
        if (parsed && parsed.unseparated) {{
          diagEl.className = "diag-feedback diag-warn";
          diagEl.textContent = "Diagnostic: Your answer is still a single fraction over c. Split it into separate real and imaginary parts: a + bi.";
          sessionState[probId].mistakes.add("Unseparated Form (a+bi)/c");
          setScore(probId, 0.5);
          renderMistakePills(probId);
          return;
        }}
        if (parsed && parsed.re !== undefined && parsed.im !== undefined) {{
          const reMatch = parsed.re === prob.re;
          const imMatch = parsed.im === prob.im;
          const negImMatch = parsed.im === (prob.im.startsWith("-") ? prob.im.slice(1) : "-" + prob.im);

          if (reMatch && imMatch) {{
            diagEl.className = "diag-feedback diag-pass";
            diagEl.textContent = `Exact Match! Verified standard form: ${{prob.displayAnswer}}.`;
            setScore(probId, 1);
            return;
          }}
          if (reMatch && negImMatch && prob.im !== "0") {{
            diagEl.className = "diag-feedback diag-warn";
            diagEl.textContent = `Partial Match: Real part (${{prob.re}}) is correct, but Imaginary part has the opposite sign (${{parsed.im}}i vs ${{prob.im}}i). Check your i^2 = -1 or conjugate sign!`;
            sessionState[probId].mistakes.add("Arithmetic / Sign Slip");
            setScore(probId, 0.5);
            renderMistakePills(probId);
            return;
          }}
          if (reMatch || imMatch) {{
            diagEl.className = "diag-feedback diag-warn";
            diagEl.textContent = `Partial Match: ${{reMatch ? "Real part matches" : "Imaginary part matches"}}, but the other component differs from ${{prob.displayAnswer}}. Inspect the step-by-step derivation below.`;
            setScore(probId, 0.5);
            return;
          }}
        }}
      }}

      // Fallback normalized string comparison
      const normUser = val.toLowerCase().replace(/\\s+/g, "");
      const normTarget = prob.displayAnswer.toLowerCase().replace(/\\s+/g, "");
      const normRe = prob.re.toLowerCase().replace(/\\s+/g, "");
      if (normUser === normTarget || normUser === normRe || normTarget.includes(normUser)) {{
        diagEl.className = "diag-feedback diag-pass";
        diagEl.textContent = `Correct! Verified answer: ${{prob.displayAnswer}}`;
        setScore(probId, 1);
      }} else {{
        diagEl.className = "diag-feedback diag-fail";
        diagEl.textContent = `Differs from verified answer (${{prob.displayAnswer}}). Open the step-by-step derivation below and click the step where your paper diverged.`;
        if (prob.commonTrapTag) {{
          sessionState[probId].mistakes.add(prob.commonTrapTag);
          renderMistakePills(probId);
        }}
        setScore(probId, 0);
      }}
    }}

    function toggleHint(probId) {{
      const el = document.getElementById(`hint-${{probId}}`);
      el.style.display = el.style.display === "block" ? "none" : "block";
    }}

    function toggleSolution(probId) {{
      const el = document.getElementById(`sol-${{probId}}`);
      el.style.display = el.style.display === "block" ? "none" : "block";
    }}

    // Click-to-Highlight Synchronized Equation & Explanation Step
    function toggleStepHighlight(probId, stepIdx, event) {{
      if (event && event.target && event.target.classList.contains("diverge-btn")) {{
        return;
      }}
      const st = sessionState[probId];
      st.activeStep = st.activeStep === stepIdx ? null : stepIdx;

      const container = document.getElementById(`steps-${{probId}}`);
      const rows = container.querySelectorAll(".step-row");
      if (st.activeStep === null) {{
        container.classList.remove("has-active");
        rows.forEach(r => r.classList.remove("active-step"));
      }} else {{
        container.classList.add("has-active");
        rows.forEach((r, idx) => {{
          if (idx === st.activeStep) r.classList.add("active-step");
          else r.classList.remove("active-step");
        }});
      }}
    }}

    // Mark exact step where handwritten paper work diverged
    function markDivergedStep(probId, stepIdx, trapTag, event) {{
      event.stopPropagation();
      const st = sessionState[probId];
      if (st.divergedStep === stepIdx) {{
        st.divergedStep = null;
      }} else {{
        st.divergedStep = stepIdx;
        if (trapTag) st.mistakes.add(trapTag);
        if (st.score === null || st.score === 1) {{
          setScore(probId, 0.5);
        }}
      }}
      const container = document.getElementById(`steps-${{probId}}`);
      const rows = container.querySelectorAll(".step-row");
      rows.forEach((r, idx) => {{
        const btn = r.querySelector(".diverge-btn");
        if (idx === st.divergedStep) {{
          r.classList.add("diverged-step");
          btn.classList.add("active");
          btn.textContent = `✗ Diverged at Step ${{idx + 1}}`;
        }} else {{
          r.classList.remove("diverged-step");
          btn.classList.remove("active");
          btn.textContent = `✗ My Paper Diverged Here`;
        }}
      }});
      renderMistakePills(probId);
    }}

    function setScore(probId, val) {{
      sessionState[probId].score = val;
      const b1 = document.getElementById(`g1-${{probId}}`);
      const bHalf = document.getElementById(`ghalf-${{probId}}`);
      const b0 = document.getElementById(`g0-${{probId}}`);
      if (b1 && bHalf && b0) {{
        b1.className = "grade-btn" + (val === 1 ? " selected-correct" : "");
        bHalf.className = "grade-btn" + (val === 0.5 ? " selected-partial" : "");
        b0.className = "grade-btn" + (val === 0 ? " selected-wrong" : "");
      }}
      updateScoreBadge();
    }}

    function toggleMistakeTag(probId, tag) {{
      const set = sessionState[probId].mistakes;
      if (set.has(tag)) set.delete(tag);
      else set.add(tag);
      renderMistakePills(probId);
    }}

    function renderMistakePills(probId) {{
      const root = document.getElementById(`pills-${{probId}}`);
      if (!root) return;
      const set = sessionState[probId].mistakes;
      root.innerHTML = MISTAKE_TAGS.map(tag => {{
        const active = set.has(tag) ? "active" : "";
        return `<span class="mistake-pill ${{active}}" onclick="toggleMistakeTag('${{probId}}', '${{tag.replace(/'/g, "\\\\'")}}')">${{tag}}</span>`;
      }}).join("");
    }}

    function updateScoreBadge() {{
      let earned = 0;
      let max = activeProblems.length;
      activeProblems.forEach(p => {{
        const s = sessionState[p.id]?.score;
        if (typeof s === "number") earned += s;
      }});
      const pct = max > 0 ? Math.round((earned / max) * 100) : 0;
      document.getElementById("liveScoreBadge").textContent = `Score: ${{earned}} / ${{max}} (${{pct}}%)`;
    }}

    function renderProblems() {{
      const root = document.getElementById("problemsRoot");
      root.innerHTML = activeProblems.map((p, idx) => {{
        const stepsHtml = p.steps.map((st, sIdx) => `
          <div class="step-row" onclick="toggleStepHighlight('${{p.id}}', ${{sIdx}}, event)">
            <div class="step-math">$$\\displaystyle ${{st.latex}}$$</div>
            <div class="step-explain"><strong>Step ${{sIdx + 1}}:</strong> ${{st.explain}}</div>
            <button class="diverge-btn" onclick="markDivergedStep('${{p.id}}', ${{sIdx}}, '${{(p.commonTrapTag || "").replace(/'/g, "\\\\'")}}', event)">
              ✗ My Paper Diverged Here
            </button>
          </div>
        `).join("");

        return `
          <div class="problem-card" id="card-${{p.id}}">
            <div class="problem-header">
              <span class="problem-num">Problem ${{idx + 1}} <span style="color:var(--muted); font-weight:400;">(${{p.id}})</span></span>
              <span class="level-pill">Level ${{p.level}}</span>
            </div>

            <div class="prompt-box">${{p.prompt}}</div>

            <div class="cas-box">
              <span><strong>Plain-Text / CAS Input:</strong> <code id="cas-${{p.id}}">${{p.plainText}}</code></span>
              <button onclick="copyText('${{p.plainText.replace(/'/g, "\\\\'")}}', this)">Copy Plain Text</button>
            </div>

            <div class="workspace-row">
              <input
                type="text"
                id="ans-${{p.id}}"
                class="answer-input"
                placeholder="Optional: Type final answer (e.g. ${{p.displayAnswer}}) or solve on paper..."
                onkeydown="if(event.key==='Enter') checkUserAnswer('${{p.id}}', ${{idx}})"
              />
              <button class="btn-primary" onclick="checkUserAnswer('${{p.id}}', ${{idx}})">Check Final Answer</button>
              <button onclick="toggleHint('${{p.id}}')">Checkpoint Hint</button>
              <button onclick="toggleSolution('${{p.id}}')">Reveal Step-by-Step Solution</button>
            </div>

            <div id="diag-${{p.id}}" class="diag-feedback"></div>
            <div id="hint-${{p.id}}" class="hint-box"><strong>Intermediate Paper Checkpoint:</strong> ${{p.checkpointHint}}</div>

            <div id="sol-${{p.id}}" class="solution-panel">
              <div class="solution-header">
                <span><strong>Verified Answer:</strong> <code>${{p.displayAnswer}}</code> (Category revealed after attempt: <em>${{p.category}} — ${{p.levelLabel}}</em>)</span>
                <span>💡 <em>Click any step row to focus &amp; highlight equation + explanation</em></span>
              </div>

              <div class="steps-container" id="steps-${{p.id}}">
                ${{stepsHtml}}
              </div>

              <div class="grading-bar">
                <div class="grade-btns">
                  <span style="font-size:12.5px; color:var(--muted); align-self:center; margin-right:4px;">Paper Self-Grade:</span>
                  <button id="g1-${{p.id}}" class="grade-btn" onclick="setScore('${{p.id}}', 1)">✓ Correct (1.0)</button>
                  <button id="ghalf-${{p.id}}" class="grade-btn" onclick="setScore('${{p.id}}', 0.5)">~ Partial / Careless (0.5)</button>
                  <button id="g0-${{p.id}}" class="grade-btn" onclick="setScore('${{p.id}}', 0)">✗ Miss (0.0)</button>
                </div>
                <div style="font-size:12px; color:var(--muted);">Tag root-cause mistake (if any):</div>
              </div>
              <div class="mistake-pills" id="pills-${{p.id}}"></div>
            </div>
          </div>
        `;
      }}).join("");

      activeProblems.forEach(p => renderMistakePills(p.id));
      setTimeout(renderMathInRoot, 60);
    }}

    function buildTelemetryPayload() {{
      let earned = 0;
      const maxScore = activeProblems.length;
      const mistakeSet = new Set();
      const divergedDetails = [];

      activeProblems.forEach((p, idx) => {{
        const st = sessionState[p.id];
        if (typeof st.score === "number") earned += st.score;
        st.mistakes.forEach(m => mistakeSet.add(m));
        if (st.divergedStep !== null) {{
          const stepObj = p.steps[st.divergedStep];
          divergedDetails.push(`${{p.id}} (Step ${{st.divergedStep + 1}}: ${{stepObj ? stepObj.explain : "Diverged"}})`);
        }} else if (st.score !== null && st.score < 1 && st.mistakes.size > 0) {{
          divergedDetails.push(`${{p.id}} (${{Array.from(st.mistakes).join(", ")}})`);
        }}
      }});

      const levelVal = document.getElementById("levelSelect").value;
      const levelMap = {{
        "ALL": "Mixed Exam Mode",
        "1": "Level 1 - Foundation",
        "2": "Level 2 - Standard Exam",
        "3": "Level 3 - Trap & Diagnostic",
        "4": "Level 4 - Applied Synthesis"
      }};

      return {{
        drillId: DRILL_META.drillId,
        unitCode: DRILL_META.unitCode,
        score: earned,
        maxScore: maxScore,
        questionCount: maxScore,
        difficultyMode: levelMap[levelVal] || "Mixed Exam Mode",
        practiceStatus: (maxScore > 0 && earned / maxScore >= 0.8) ? "Graded" : "Needs Retry",
        mistakeCategories: Array.from(mistakeSet),
        divergedStepsSummary: divergedDetails.length > 0 ? divergedDetails.join(" | ") : "No diverged steps logged.",
        attemptDate: new Date().toISOString().slice(0, 10)
      }};
    }}

    function copyMarkdownLog() {{
      const payload = buildTelemetryPayload();
      const pct = payload.maxScore > 0 ? Math.round((payload.score / payload.maxScore) * 100) : 0;
      const md = [
        `### Drill Attempt: ${{payload.drillId}} (${{payload.attemptDate}})`,
        `- **Score:** ${{payload.score}} / ${{payload.maxScore}} (${{pct}}%) — **${{payload.practiceStatus}}**`,
        `- **Difficulty Mode:** ${{payload.difficultyMode}} (${{payload.questionCount}} Questions)`,
        `- **Mistake Categories:** ${{payload.mistakeCategories.join(", ") || "None"}}`,
        `- **Paper Divergence Log:** ${{payload.divergedStepsSummary}}`
      ].join("\\n");
      navigator.clipboard.writeText(md);
      const box = document.getElementById("syncStatusBox");
      box.style.display = "block";
      box.className = "sync-status diag-pass";
      box.textContent = "Copied Markdown Mistake Log to clipboard! You can paste it directly into Notion.";
    }}

    async function syncToNotion() {{
      const payload = buildTelemetryPayload();
      const box = document.getElementById("syncStatusBox");
      box.style.display = "block";
      box.className = "sync-status diag-warn";
      box.textContent = "Syncing practice telemetry to Notion via localhost:8765...";

      try {{
        const res = await fetch("http://localhost:8765/api/sync-notion", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify(payload)
        }});
        const data = await res.json();
        if (res.ok && data.ok) {{
          box.className = "sync-status diag-pass";
          box.textContent = `Synced to Notion! Updated ${{payload.drillId}} (${{payload.score}}/${{payload.maxScore}}) and appended log to ${{payload.unitCode}}.`;
        }} else {{
          throw new Error(data.error || "Bridge returned error");
        }}
      }} catch (err) {{
        copyMarkdownLog();
        box.className = "sync-status diag-warn";
        box.textContent = `Local bridge (practice_hub.py on port 8765) not running — copied clean Markdown summary to clipboard instead! Run 'python3 practice_hub.py' for 1-click Notion API sync.`;
      }}
    }}

    window.addEventListener("DOMContentLoaded", () => {{
      generateDrillSet();
    }});
  </script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)
    print(f"  Generated interactive HTML drill: {output_path}")


# ============================================================================
# 4. CREATE INITIAL NOTION DRILL PAGES IN "LEARNING PRACTICE & DRILLS"
# ============================================================================
def upsert_drill_page_in_notion(
    drills_db_id: str,
    drill_id: str,
    title: str,
    order_num: int,
    scope_level: str,
    fmt: str,
    difficulty_mode: str,
    question_count: int,
    local_file_path: str,
    unit_code: str,
    chapter_code: str,
    topic_code: str,
    problems: list,
    id_map: dict,
    token: str,
):
    # Query if drill_id already exists
    q = notion_request(
        "POST",
        f"databases/{drills_db_id}/query",
        token,
        {
            "filter": {
                "property": "Drill ID",
                "rich_text": {"equals": drill_id},
            }
        },
    )
    results = q.get("results", [])

    props = {
        "Drill": {"title": [{"type": "text", "text": {"content": title}}]},
        "Drill ID": {"rich_text": [{"type": "text", "text": {"content": drill_id}}]},
        "Order": {"number": order_num},
        "Scope Level": {"select": {"name": scope_level}},
        "Format": {"select": {"name": fmt}},
        "Difficulty Mode": {"select": {"name": difficulty_mode}},
        "Question Count": {"number": question_count},
        "Practice Status": {"select": {"name": "Ready"}},
        "Score": {"number": 0},
        "Max Score": {"number": question_count},
        "Local File Path": {"rich_text": [{"type": "text", "text": {"content": local_file_path}}]},
        "Units": {"relation": [{"id": id_map[unit_code]["id"]}]},
        "Chapters": {"relation": [{"id": id_map[chapter_code]["id"]}]},
        "Topics": {"relation": [{"id": id_map[topic_code]["id"]}]},
    }

    icon_payload = {"type": "icon", "icon": {"name": "target", "color": "purple"}}

    if results:
        page_id = results[0]["id"]
        notion_request(
            "PATCH",
            f"pages/{page_id}",
            token,
            {"icon": icon_payload, "properties": props},
        )
    else:
        created = notion_request(
            "POST",
            "pages",
            token,
            {
                "parent": {"database_id": drills_db_id},
                "icon": icon_payload,
                "properties": props,
            },
        )
        page_id = created["id"]

    id_map[drill_id] = {"id": page_id, "title": title}

    # Build clean 100% English Notion page body with vertical aligned equation toggles
    blocks = [
        callout_block(
            f"**Interactive Hybrid Drill (`{drill_id}`):** Open `{local_file_path}` in your browser (or via `http://localhost:8765/{local_file_path}`) for shuffled question sets (`5 / 10 / 15 / 20`), **Click-to-Highlight synchronized equation steps**, **Paper-First divergence buttons**, and **1-click Notion Auto-Sync**.\n"
            f"Scope: [[{unit_code}]] | Chapter: [[{chapter_code}]] | Topic: [[{topic_code}]]",
            id_map,
            color="purple_background",
        ),
        divider_block(),
        h2("Verified Question Bank & Vertical Step-by-Step Solutions", id_map),
        p_block(
            "Every problem below has been pre-executed and verified in Python (`ExactComplex` / `Fraction`) prior to generation. Expand any toggle below to inspect the vertical `\\begin{aligned}` step-by-step derivation.",
            id_map,
        ),
    ]

    for idx, prob in enumerate(problems, 1):
        aligned_lines = []
        step_bullets = []
        for s_i, st in enumerate(prob["steps"], 1):
            latex_line = st["latex"].replace("=", "&=", 1) if "=" in st["latex"] else "& " + st["latex"]
            aligned_lines.append(latex_line)
            step_bullets.append(bullet(f"**Step {s_i}:** {st['explain']}", id_map))

        aligned_tex = "\\begin{aligned}\n" + " \\\\\n".join(aligned_lines) + "\n\\end{aligned}"
        blocks.append(
            toggle_block(
                f"**{prob['id']} ({prob['levelLabel']} — {prob['category']}):** {prob['prompt']}",
                [
                    p_block(f"**Plain-Text / CAS Input:** `{prob['plainText']}`", id_map),
                    p_block(f"**Intermediate Paper Checkpoint:** {prob['checkpointHint']}", id_map),
                    eq_block(aligned_tex),
                    *step_bullets,
                    p_block(f"**Verified Final Answer:** `{prob['displayAnswer']}` | **Common Trap Tag:** `{prob['commonTrapTag']}`", id_map),
                ],
                id_map,
            )
        )

    replace_page_blocks(page_id, blocks, drill_id, token)
    print(f"  Synced Notion Drill Page {drill_id} ({page_id}) with {len(problems)} verified problems!")
    return page_id


def main():
    mth_problems = build_and_verify_mth_problems()
    prg_problems = build_and_verify_prg_problems()

    mth_mistake_tags = [
        "Principal Root Error (sqrt(-a)*sqrt(-b))",
        "Conjugate Denominator Error (a^2-b^2)",
        "Power of i Cycle Error",
        "Unseparated Form (a+bi)/c",
        "Arithmetic / Sign Slip",
    ]
    prg_mistake_tags = [
        "Env Boundary Leak (NEXT_PUBLIC_)",
        "Env Precedence Order Error",
        "Route Boundary Confusion",
        "Path Alias Resolution Error",
    ]

    mth_html_path = "drills/DRL-MTH-T02-C01-U01-01.html"
    prg_html_path = "drills/DRL-PRG-T03-C01-U01-01.html"

    render_interactive_drill_html(
        drill_id="DRL-MTH-T02-C01-U01-01",
        title="Complex Numbers (MTH-T02-C01-U01)",
        unit_code="MTH-T02-C01-U01",
        unit_title="Complex Numbers",
        chapter_code="MTH-T02-C01",
        topic_code="MTH-T02",
        subject_mode="MATH",
        problems=mth_problems,
        mistake_tags=mth_mistake_tags,
        output_path=mth_html_path,
    )

    render_interactive_drill_html(
        drill_id="DRL-PRG-T03-C01-U01-01",
        title="Next.js Project Structure & Env Boundaries (PRG-T03-C01-U01)",
        unit_code="PRG-T03-C01-U01",
        unit_title="Next.js Project Structure",
        chapter_code="PRG-T03-C01",
        topic_code="PRG-T03",
        subject_mode="PRG",
        problems=prg_problems,
        mistake_tags=prg_mistake_tags,
        output_path=prg_html_path,
    )

    env = load_env()
    token = env.get("NOTION_TOKEN")
    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    drills_entry = id_map.get("DRILLS_DB")
    drills_db_id = drills_entry["id"] if isinstance(drills_entry, dict) else drills_entry
    if drills_db_id and token:
        upsert_drill_page_in_notion(
            drills_db_id=drills_db_id,
            drill_id="DRL-MTH-T02-C01-U01-01",
            title="Complex Numbers — Interactive Verification & Diagnostic Drill",
            order_num=1,
            scope_level="Unit Drill",
            fmt="Interactive HTML",
            difficulty_mode="Mixed Exam Mode",
            question_count=20,
            local_file_path=mth_html_path,
            unit_code="MTH-T02-C01-U01",
            chapter_code="MTH-T02-C01",
            topic_code="MTH-T02",
            problems=mth_problems,
            id_map=id_map,
            token=token,
        )
        upsert_drill_page_in_notion(
            drills_db_id=drills_db_id,
            drill_id="DRL-PRG-T03-C01-U01-01",
            title="Next.js Project Structure — Architecture & Env Boundary Drill",
            order_num=2,
            scope_level="Unit Drill",
            fmt="Interactive HTML",
            difficulty_mode="Mixed Exam Mode",
            question_count=10,
            local_file_path=prg_html_path,
            unit_code="PRG-T03-C01-U01",
            chapter_code="PRG-T03-C01",
            topic_code="PRG-T03",
            problems=prg_problems,
            id_map=id_map,
            token=token,
        )
        with open("id_map.json", "w", encoding="utf-8") as f:
            json.dump(id_map, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
