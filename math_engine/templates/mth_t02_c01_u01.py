# -*- coding: utf-8 -*-
"""
Parameterized, randomized problem templates for MTH-T02-C01-U01 (Complex Numbers).

Scope (cumulative, strictly within the Unit): imaginary unit, square roots of negatives, standard form a + bi,
add / subtract / multiply / divide (conjugates), powers of i, plus Level 4 applications (AC impedance, 2D rotation).
Quadratic-equation solving belongs to MTH-T02-C01-U02 and is intentionally excluded.

Every template returns a problem dict. Each step carries `val` (SymPy value of the row, must equal `verify.source`)
or `eq` ([lhs, rhs] that must be equal). math_engine.verify enforces all of these before any JSON is written.
Text fields: plain English + inline `$...$` only. No Markdown, no [[ID]] tokens, no \\displaystyle.
"""

import sympy as sp

from math_engine.fmt import R, cx, cx_plain, cx_sym, nonzero, num, sq, terms

UNIT = "MTH-T02-C01-U01"
TITLE = "Complex Numbers"

MISTAKE_TAGS = [
    {
        "id": "sign-slip",
        "label": "Sign slip with $i^2 = -1$",
        "name": "Sign Slip (i^2 = -1)",
        "autoFrom": ["imag_sign_flip", "real_sign_flip", "whole_sign_flip"],
    },
    {
        "id": "principal-root",
        "label": "Combined $\\sqrt{-a}\\cdot\\sqrt{-b}$ into $\\sqrt{ab}$",
        "name": "Principal Root Trap",
        "autoFrom": [],
    },
    {
        "id": "conjugate-denominator",
        "label": "Conjugate denominator: wrote $c^2 - d^2$ instead of $c^2 + d^2$",
        "name": "Conjugate Denominator Error",
        "autoFrom": ["complex_denominator"],
    },
    {
        "id": "power-cycle",
        "label": "Power cycle of $i$: wrong remainder of $n \\div 4$",
        "name": "Power of i Cycle Error",
        "autoFrom": [],
    },
    {
        "id": "standard-form",
        "label": "Not in standard form $a + bi$",
        "name": "Unseparated Standard Form",
        "autoFrom": ["unseparated", "unexpanded_power", "uncombined_terms", "unreduced_fraction"],
    },
    {
        "id": "radical-simplify",
        "label": "Radical not simplified, e.g. $\\sqrt{48} = 4\\sqrt{3}$",
        "name": "Radical Simplification Error",
        "autoFrom": ["unsimplified_radical"],
    },
    {
        "id": "arithmetic",
        "label": "Arithmetic slip (FOIL or combining like terms)",
        "name": "Arithmetic Slip",
        "autoFrom": ["off_by_factor", "rounding", "swapped_parts", "constant_offset"],
    },
    {
        "id": "setup",
        "label": "Wrong setup or formula",
        "name": "Setup or Formula Error",
        "autoFrom": ["reciprocal", "wrong_component_count"],
    },
]

I_POW_VALUE = {0: ("1", "1"), 1: ("i", "I"), 2: ("-1", "-1"), 3: ("-i", "-I")}
I_POW_RULE = {0: "$i^0 = 1$", 1: "$i^1 = i$", 2: "$i^2 = -1$", 3: "$i^3 = -i$"}


def S(latex, explain, val=None, eq=None):
    step = {"latex": latex, "explain": explain}
    if val is not None:
        step["val"] = val
    if eq is not None:
        step["eq"] = eq
    return step


def complex_answer(a, b, forms=("a+bi", "reduced_fraction")):
    a, b = R(a), R(b)
    return {
        "answerSpec": {"type": "complex", "value": f"{a} + ({b})*I", "forms": list(forms)},
        "answerDisplay": cx(a, b),
        "answerPlain": cx_plain(a, b),
        "inputHint": "Standard form, e.g. 3 - 4i or -8/17 + 15/17 i",
    }


# ---------------------------------------------------------------------------
# Level 1 - Foundation
# ---------------------------------------------------------------------------
def t_radical(rng):
    m = rng.choice([2, 3, 5, 6, 7, 10])
    k = rng.randint(2, 7)
    a = k * k * m
    c = nonzero(rng, -9, 9)
    src = f"{c} + sqrt(-{a})"
    return {
        "category": "Core Skill",
        "prompt": "Write the number in standard form $a + bi$ with the radical fully simplified.",
        "display": f"{c} + \\sqrt{{-{a}}}",
        "plainText": f"{c} + sqrt(-{a})",
        "answerSpec": {"type": "complex", "value": f"{c} + {k}*sqrt({m})*I", "forms": ["a+bi", "simplified_radical"]},
        "answerDisplay": f"{c} + {k}\\sqrt{{{m}}}\\,i",
        "answerPlain": f"{c} + {k}sqrt({m}) i",
        "inputHint": "e.g. 5 + 3sqrt(2) i or 2 - 4sqrt(3) i",
        "checkpointHint": f"Factor the radicand as ${a} = {k * k} \\cdot {m}$ and use $\\sqrt{{-1}} = i$.",
        "commonTrapTag": "radical-simplify",
        "steps": [
            S(
                f"{c} + \\sqrt{{-{a}}} = {c} + \\sqrt{{-1}}\\cdot\\sqrt{{{a}}}",
                "Split off the factor $-1$. This is valid here because only one radicand is negative.",
                f"{c} + sqrt(-1)*sqrt({a})",
            ),
            S(
                f"= {c} + i\\sqrt{{{k * k}\\cdot {m}}}",
                f"Replace $\\sqrt{{-1}}$ with $i$ and factor out the largest perfect square ${k * k}$.",
                f"{c} + I*sqrt({k * k}*{m})",
            ),
            S(
                f"= {c} + {k}\\sqrt{{{m}}}\\,i",
                f"Take $\\sqrt{{{k * k}}} = {k}$ outside the radical. Real part ${c}$, imaginary part ${k}\\sqrt{{{m}}}$.",
                f"{c} + {k}*sqrt({m})*I",
            ),
        ],
        "verify": {"source": src},
    }


def t_add_sub(rng):
    a, b, c, d = (nonzero(rng, -9, 9) for _ in range(4))
    s = rng.choice([1, -1])
    op = "+" if s == 1 else "-"
    A, B = a + s * c, b + s * d
    src = f"{cx_sym(a, b)} {op} {cx_sym(c, d)}"
    distribute = (
        "Remove the parentheses." if s == 1 else "Distribute the minus sign to BOTH parts of the second number."
    )
    return {
        "category": "Core Skill",
        "prompt": "Simplify and write the result in standard form $a + bi$.",
        "display": f"({cx(a, b)}) {op} ({cx(c, d)})",
        "plainText": f"({cx_plain(a, b)}) {op} ({cx_plain(c, d)})",
        **complex_answer(A, B),
        "checkpointHint": f"The real parts combine to ${num(A)}$.",
        "commonTrapTag": "sign-slip",
        "steps": [
            S(
                f"({cx(a, b)}) {op} ({cx(c, d)}) = {terms([(a, ''), (b, 'i'), (s * c, ''), (s * d, 'i')])}",
                distribute,
                f"{a} + {b}*I + ({s * c}) + ({s * d})*I",
            ),
            S(
                f"= ({terms([(a, ''), (s * c, '')])}) + ({terms([(b, ''), (s * d, '')])})i",
                "Group the real parts together and the imaginary parts together.",
                f"({a} + ({s * c})) + ({b} + ({s * d}))*I",
            ),
            S(f"= {cx(A, B)}", f"Real part ${num(A)}$, imaginary part ${num(B)}$.", cx_sym(A, B)),
        ],
        "verify": {"source": src},
    }


def t_power_i(rng):
    n = rng.randint(23, 199)
    q, r = divmod(n, 4)
    latex_v, sym_v = I_POW_VALUE[r]
    return {
        "category": "Core Skill",
        "prompt": "Simplify the power of $i$.",
        "display": f"i^{{{n}}}",
        "plainText": f"i^{n}",
        **complex_answer(sp.re(sp.sympify(sym_v)), sp.im(sp.sympify(sym_v))),
        "inputHint": "One of 1, i, -1, -i",
        "checkpointHint": "Divide the exponent by $4$ and keep only the remainder.",
        "commonTrapTag": "power-cycle",
        "steps": [
            S(
                f"i^{{{n}}} = i^{{4\\cdot {q} + {r}}} = (i^4)^{{{q}}}\\cdot i^{{{r}}}",
                f"Divide the exponent by $4$: ${n} = 4 \\cdot {q} + {r}$, then split the power.",
                f"(I**4)**{q} * I**{r}",
            ),
            S(f"= 1^{{{q}}}\\cdot i^{{{r}}}", "Use $i^4 = 1$, so any power of $i^4$ equals $1$.", f"1 * I**{r}"),
            S(f"= {latex_v}", f"Use the cycle value {I_POW_RULE[r]}.", sym_v),
        ],
        "verify": {"source": f"I**{n}"},
    }


# ---------------------------------------------------------------------------
# Level 2 - Standard Exam
# ---------------------------------------------------------------------------
def t_multiply(rng):
    a, b, c, d = (nonzero(rng, -7, 7) for _ in range(4))
    ac, ad, bc, bd = a * c, a * d, b * c, b * d
    A, B = ac - bd, ad + bc
    src = f"{cx_sym(a, b)} * {cx_sym(c, d)}"
    return {
        "category": "Core Skill",
        "prompt": "Multiply and write the product in standard form $a + bi$.",
        "display": f"({cx(a, b)})({cx(c, d)})",
        "plainText": f"({cx_plain(a, b)})*({cx_plain(c, d)})",
        **complex_answer(A, B),
        "checkpointHint": f"After FOIL, the $i^2$ term is ${terms([(bd, 'i^2')])}$, which equals ${num(-bd)}$.",
        "commonTrapTag": "sign-slip",
        "steps": [
            S(
                f"({cx(a, b)})({cx(c, d)}) = {terms([(ac, ''), (ad, 'i'), (bc, 'i'), (bd, 'i^2')])}",
                "Distribute every term (FOIL: First, Outer, Inner, Last).",
                f"{ac} + ({ad})*I + ({bc})*I + ({bd})*I**2",
            ),
            S(
                f"= {terms([(ac, ''), (ad + bc, 'i')], keep_zero=True)} {'-' if bd < 0 else '+'} {abs(bd)}(-1)",
                "Combine the two imaginary terms and substitute $i^2 = -1$.",
                f"{ac} + ({ad + bc})*I + ({bd})*(-1)",
            ),
            S(
                f"= {cx(A, B)}",
                f"The last term becomes ${num(-bd)}$; add it to the real part: ${num(ac)} {'+' if -bd >= 0 else '-'} {abs(bd)} = {num(A)}$.",
                cx_sym(A, B),
            ),
        ],
        "verify": {"source": src},
    }


def _division_steps(a, b, c, d, lead=None):
    """Steps for (a+bi)/(c+di). Returns (steps, A/D, B/D)."""
    D = c * c + d * d
    A, B = a * c + b * d, b * c - a * d
    num_l, den_l = cx(a, b), cx(c, d)
    first = lead if lead else f"\\frac{{{num_l}}}{{{den_l}}}"
    steps = [
        S(
            f"{first} = \\frac{{({num_l})({cx(c, -d)})}}{{({den_l})({cx(c, -d)})}}",
            f"Multiply the numerator and denominator by the conjugate ${cx(c, -d)}$ of the denominator.",
            f"({cx_sym(a, b)}*{cx_sym(c, -d)})/({cx_sym(c, d)}*{cx_sym(c, -d)})",
        ),
        S(
            f"= \\frac{{{terms([(a * c, ''), (-a * d, 'i'), (b * c, 'i'), (-b * d, 'i^2')])}}}{{{sq(c)} + {sq(d)}}}",
            "Expand the numerator with FOIL. The denominator is $(c + di)(c - di) = c^2 + d^2$ (always a plus sign).",
            f"({a * c} + ({-a * d})*I + ({b * c})*I + ({-b * d})*I**2)/(({c})**2 + ({d})**2)",
        ),
        S(f"= \\frac{{{cx(A, B)}}}{{{D}}}", "Substitute $i^2 = -1$ and combine like terms.", f"{cx_sym(A, B)}/{D}"),
    ]
    rA, rB = R(A) / D, R(B) / D
    explain = (
        "Split into real and imaginary parts and reduce each fraction."
        if (rA.q != 1 or rB.q != 1)
        else f"Divide each part by ${D}$."
    )
    if D != 1:
        steps.append(S(f"= {cx(rA, rB)}", explain, cx_sym(rA, rB)))
    return steps, rA, rB


def t_divide(rng):
    c, d = nonzero(rng, -5, 5), nonzero(rng, -5, 5)
    while True:
        if rng.random() < 0.5:
            p, q = nonzero(rng, -6, 6), nonzero(rng, -6, 6)
            a, b = p * c - q * d, p * d + q * c
        else:
            a, b = nonzero(rng, -9, 9), nonzero(rng, -9, 9)
        if a != 0 and b != 0:
            break
    steps, rA, rB = _division_steps(a, b, c, d)
    return {
        "category": "Core Skill",
        "prompt": "Divide and write the quotient in standard form $a + bi$.",
        "display": f"\\frac{{{cx(a, b)}}}{{{cx(c, d)}}}",
        "plainText": f"({cx_plain(a, b)})/({cx_plain(c, d)})",
        **complex_answer(rA, rB),
        "checkpointHint": f"The new denominator is ${sq(c)} + {sq(d)} = {c * c + d * d}$.",
        "commonTrapTag": "conjugate-denominator",
        "steps": steps,
        "verify": {"source": f"{cx_sym(a, b)}/{cx_sym(c, d)}"},
    }


def t_square(rng):
    a, b = nonzero(rng, -8, 8), nonzero(rng, -8, 8)
    A, B = a * a - b * b, 2 * a * b
    return {
        "category": "Core Skill",
        "prompt": "Expand and write the result in standard form $a + bi$.",
        "display": f"({cx(a, b)})^2",
        "plainText": f"({cx_plain(a, b)})^2",
        **complex_answer(A, B),
        "checkpointHint": f"Use $(a + bi)^2 = a^2 + 2abi + b^2 i^2$. Here $b^2 i^2 = {num(-b * b)}$.",
        "commonTrapTag": "sign-slip",
        "steps": [
            S(
                f"({cx(a, b)})^2 = {sq(a)} + 2({num(a)})({cx(0, b)}) + ({cx(0, b)})^2",
                "Apply the square of a binomial: $(x + y)^2 = x^2 + 2xy + y^2$.",
                f"({a})**2 + 2*({a})*({b}*I) + ({b}*I)**2",
            ),
            S(
                f"= {terms([(a * a, ''), (2 * a * b, 'i'), (b * b, 'i^2')])}",
                "Evaluate each square and product; note $(bi)^2 = b^2 i^2$.",
                f"{a * a} + ({2 * a * b})*I + {b * b}*I**2",
            ),
            S(
                f"= {cx(A, B)}",
                f"Use $i^2 = -1$, so ${b * b}i^2 = {num(-b * b)}$, then combine the real parts.",
                cx_sym(A, B),
            ),
        ],
        "verify": {"source": f"{cx_sym(a, b)}**2"},
    }


def t_eval_poly(rng):
    a, b = nonzero(rng, -4, 4), nonzero(rng, -4, 4)
    if rng.random() < 0.4:
        p, q = -2 * a, a * a + b * b
    else:
        p, q = nonzero(rng, -6, 6), rng.randint(-9, 9)
    x2r, x2i = a * a - b * b, 2 * a * b
    A, B = x2r + p * a + q, x2i + p * b
    poly = terms([(1, "x^2"), (p, "x"), (q, "")])
    z = cx(a, b)
    q_part = f" {'+' if q >= 0 else '-'} {abs(q)}" if q != 0 else ""
    src = f"{cx_sym(a, b)}**2 + ({p})*{cx_sym(a, b)} + ({q})"
    return {
        "category": "Combined with Prior Units",
        "prompt": f"Let $f(x) = {poly}$. Evaluate $f({z})$ and write the result in standard form $a + bi$.",
        "display": f"f({z}) = ({z})^2 {'+' if p > 0 else '-'} {abs(p)}({z}){q_part}",
        "plainText": f"({cx_plain(a, b)})^2 + ({p})*({cx_plain(a, b)}) + ({q})",
        **complex_answer(A, B),
        "checkpointHint": f"First compute $({z})^2 = {cx(x2r, x2i)}$.",
        "commonTrapTag": "sign-slip",
        "steps": [
            S(
                f"f({z}) = ({z})^2 {'+' if p > 0 else '-'} {abs(p)}({z}){q_part}",
                "Substitute the complex number for every $x$, keeping it in parentheses.",
                src,
            ),
            S(
                f"= ({cx(x2r, x2i)}) + ({cx(p * a, p * b)}){q_part}",
                f"Square first: $({z})^2 = {sq(a)} + 2({num(a)})({cx(0, b)}) + ({cx(0, b)})^2 = {cx(x2r, x2i)}$. Then distribute ${p}$.",
                f"{cx_sym(x2r, x2i)} + {cx_sym(p * a, p * b)} + ({q})",
            ),
            S(
                f"= {cx(A, B)}",
                "Add the real parts and the imaginary parts separately."
                + (" A result of $0$ means the number is a root of $f$." if A == 0 and B == 0 else ""),
                cx_sym(A, B),
            ),
        ],
        "verify": {"source": src},
    }


# ---------------------------------------------------------------------------
# Level 3 - Trap & Diagnostic
# ---------------------------------------------------------------------------
def _i_radical(k, m):
    return f"{k}i" if m == 1 else f"{k}\\sqrt{{{m}}}\\,i"


def t_principal_root(rng):
    m = rng.choice([1, 2, 3, 5, 7])
    k1, k2 = rng.randint(2, 6), rng.randint(2, 6)
    a, b = k1 * k1 * m, k2 * k2 * m
    P = k1 * k2 * m
    return {
        "category": "Trap & Edge Case",
        "prompt": "Simplify the product. Be careful with the rule $\\sqrt{x}\\cdot\\sqrt{y} = \\sqrt{xy}$.",
        "display": f"\\sqrt{{-{a}}}\\cdot\\sqrt{{-{b}}}",
        "plainText": f"sqrt(-{a})*sqrt(-{b})",
        **complex_answer(-P, 0),
        "inputHint": "e.g. -15 or -24",
        "checkpointHint": f"Rewrite each factor with $i$ first: $\\sqrt{{-{a}}} = {_i_radical(k1, m)}$.",
        "commonTrapTag": "principal-root",
        "steps": [
            S(
                f"\\sqrt{{-{a}}}\\cdot\\sqrt{{-{b}}} = ({_i_radical(k1, m)})({_i_radical(k2, m)})",
                "Convert each radical to $i$-form FIRST. Combining into $\\sqrt{(-a)(-b)}$ is invalid because $\\sqrt{x}\\sqrt{y} = \\sqrt{xy}$ only holds for $x, y \\ge 0$.",
                f"({k1}*sqrt({m})*I)*({k2}*sqrt({m})*I)",
            ),
            S(
                f"= {k1 * k2}" + ("" if m == 1 else f"(\\sqrt{{{m}}})^2") + "\\, i^2",
                "Multiply the coefficients, the radicals, and the $i$ factors separately.",
                f"{k1 * k2}*sqrt({m})**2*I**2",
            ),
            S(f"= {P}(-1) = {num(-P)}", f"Use $i^2 = -1$. The tempting answer ${P}$ is wrong by a sign.", f"{-P}"),
        ],
        "verify": {"source": f"sqrt(-{a})*sqrt(-{b})"},
    }


def t_power_sum(rng):
    exps = rng.sample(range(10, 130), 3)
    coefs = [nonzero(rng, -5, 5) for _ in range(3)]
    rems = [e % 4 for e in exps]
    total = sum(c * sp.I**r for c, r in zip(coefs, rems))
    A, B = sp.re(total), sp.im(total)
    display = terms([(c, f"i^{{{e}}}") for c, e in zip(coefs, exps)])
    reduced = terms([(c, f"i^{{{r}}}") for c, r in zip(coefs, rems)], keep_zero=True)
    sub_parts = []
    for c, r in zip(coefs, rems):
        v = {0: "(1)", 1: "(i)", 2: "(-1)", 3: "(-i)"}[r]
        sub_parts.append((c, v))
    substituted = terms(sub_parts)
    mods = ", ".join(f"{e} = 4\\cdot {e // 4} + {e % 4}" for e in exps)
    src = " + ".join(f"({c})*I**{e}" for c, e in zip(coefs, exps))
    return {
        "category": "Trap & Edge Case",
        "prompt": "Simplify and write the result in standard form $a + bi$.",
        "display": display,
        "plainText": " + ".join(f"({c})*i^{e}" for c, e in zip(coefs, exps)),
        **complex_answer(A, B),
        "checkpointHint": f"The remainders of the exponents divided by $4$ are ${rems[0]}, {rems[1]}, {rems[2]}$.",
        "commonTrapTag": "power-cycle",
        "steps": [
            S(
                f"{display} = {reduced}",
                f"Reduce each exponent modulo $4$: ${mods}$.",
                " + ".join(f"({c})*I**{r}" for c, r in zip(coefs, rems)),
            ),
            S(
                f"= {substituted}",
                "Replace each power using the cycle $i^0 = 1$, $i^1 = i$, $i^2 = -1$, $i^3 = -i$.",
                " + ".join(f"({c})*({ {0: '1', 1: 'I', 2: '-1', 3: '-I'}[r] })" for c, r in zip(coefs, rems)),
            ),
            S(
                f"= {cx(A, B)}",
                "Combine the real terms and the imaginary terms; watch the sign of each coefficient.",
                cx_sym(A, B),
            ),
        ],
        "verify": {"source": src},
    }


def t_find_flaw(rng):
    while True:
        a, b, c, d = (nonzero(rng, -6, 6) for _ in range(4))
        ac, ad, bc, bd = a * c, a * d, b * c, b * d
        if ad + bc != 0 and ad - bc != 0:
            break
    A, B = ac - bd, ad + bc
    head = f"({cx(a, b)})({cx(c, d)})"
    correct = [
        (
            f"{head} = {terms([(ac, ''), (ad, 'i'), (bc, 'i'), (bd, 'i^2')])}",
            f"{ac} + ({ad})*I + ({bc})*I + ({bd})*I**2",
        ),
        (
            f"= {terms([(ac, ''), (ad + bc, 'i')], keep_zero=True)} {'-' if bd < 0 else '+'} {abs(bd)}(-1)",
            f"{ac} + ({ad + bc})*I + ({bd})*(-1)",
        ),
        (f"= {cx(A, B)}", cx_sym(A, B)),
    ]
    kind = rng.choice([1, 2, 3])
    if kind == 1:  # sign error in the Inner FOIL term
        wbc = -bc
        shown = [
            f"{head} = {terms([(ac, ''), (ad, 'i'), (wbc, 'i'), (bd, 'i^2')])}",
            f"= {terms([(ac, ''), (ad + wbc, 'i')], keep_zero=True)} {'-' if bd < 0 else '+'} {abs(bd)}(-1)",
            f"= {cx(ac - bd, ad + wbc)}",
        ]
        vals = [f"{ac} + ({ad})*I + ({wbc})*I + ({bd})*I**2", None, None]
        why = f"Line 1 is wrong: the Inner product is $({cx(0, b)})({num(c)}) = {terms([(bc, 'i')])}$, not ${terms([(wbc, 'i')])}$."
    elif kind == 2:  # i^2 treated as +1
        shown = [
            correct[0][0],
            f"= {terms([(ac, ''), (ad + bc, 'i')], keep_zero=True)} {'-' if bd < 0 else '+'} {abs(bd)}(1)",
            f"= {cx(ac + bd, ad + bc)}",
        ]
        vals = [correct[0][1], f"{ac} + ({ad + bc})*I + ({bd})*(1)", None]
        why = "Line 2 is wrong: it replaced $i^2$ with $+1$ instead of $-1$."
    else:  # combining error in the final line
        shown = [correct[0][0], correct[1][0], f"= {cx(ac + bd, ad + bc)}"]
        vals = [correct[0][1], correct[1][1], cx_sym(ac + bd, ad + bc)]
        why = f"Line 3 is wrong: ${num(bd)}(-1) = {num(-bd)}$, so the real part is ${num(ac)} {'+' if -bd >= 0 else '-'} {abs(bd)} = {num(A)}$."
    flaw_line = kind
    aligned = (
        "\\begin{aligned}"
        + " \\\\ ".join(f"&\\text{{Line {i + 1}: }}\\; {ln}" for i, ln in enumerate(shown))
        + "\\end{aligned}"
    )
    steps = [
        S(
            correct[0][0],
            ("Correct Line 1. " if kind != 1 else why + " Correct version shown.") + " FOIL every pair of terms.",
            correct[0][1],
        ),
        S(
            correct[1][0],
            (
                why + " Correct version shown."
                if kind == 2
                else "Correct Line 2: combine imaginary terms and use $i^2 = -1$."
            ),
            correct[1][1],
        ),
        S(
            correct[2][0],
            (why if kind == 3 else "Correct Line 3: combine the real parts.") + f" The true product is ${cx(A, B)}$.",
            correct[2][1],
        ),
    ]
    return {
        "category": "Trap & Edge Case",
        "prompt": "A student multiplied two complex numbers as shown. Which line contains the FIRST error?",
        "display": aligned,
        "plainText": f"({cx_plain(a, b)})*({cx_plain(c, d)})",
        "answerSpec": {
            "type": "choice",
            "options": [{"id": str(i), "label": f"Line {i}"} for i in (1, 2, 3)],
            "correct": str(flaw_line),
        },
        "answerDisplay": f"\\text{{Line {flaw_line}}}",
        "answerPlain": str(flaw_line),
        "inputHint": "Choose a line",
        "checkpointHint": f"Compute the product yourself first; the correct result is not ${cx(*_last_vals(kind, ac, ad, bc, bd))}$.",
        "commonTrapTag": "sign-slip",
        "steps": steps,
        "verify": {"source": f"{cx_sym(a, b)}*{cx_sym(c, d)}", "flaw": {"values": vals, "firstWrong": flaw_line}},
    }


def _last_vals(kind, ac, ad, bc, bd):
    if kind == 1:
        return (ac - bd, ad - bc)
    return (ac + bd, ad + bc)


# ---------------------------------------------------------------------------
# Level 4 - Applied Synthesis
# ---------------------------------------------------------------------------
IMPEDANCES = [(3, 4), (4, -3), (1, 2), (2, -1), (6, 8), (5, -12), (2, 3), (3, -2), (8, -6), (1, -3)]


def t_ac_current(rng):
    Rr, X = rng.choice(IMPEDANCES)
    V = rng.choice([10, 20, 25, 26, 30, 39, 50, 52, 60, 65, 100])
    D = Rr * Rr + X * X
    A, B = R(V * Rr) / D, R(-V * X) / D
    return {
        "category": "Cross-Subject Application",
        "context": "Physics Application: AC Circuits",
        "references": ["PHY-T01-C19"],
        "prompt": f"In an AC circuit the voltage phasor is $V = {V}$ volts and the impedance is $Z = {cx(Rr, X)}$ ohms. "
        f"Using Ohm's law $I = \\dfrac{{V}}{{Z}}$, find the current phasor $I$ in standard form $a + bi$ (amperes).",
        "display": f"I = \\frac{{{V}}}{{{cx(Rr, X)}}}",
        "plainText": f"{V}/({cx_plain(Rr, X)})",
        **complex_answer(A, B),
        "checkpointHint": f"Multiply by the conjugate ${cx(Rr, -X)}$; the denominator becomes ${D}$.",
        "commonTrapTag": "conjugate-denominator",
        "steps": [
            S(
                f"I = \\frac{{V}}{{Z}} = \\frac{{{V}}}{{{cx(Rr, X)}}}",
                "Substitute the given voltage and impedance into Ohm's law.",
                f"{V}/{cx_sym(Rr, X)}",
            ),
            S(
                f"= \\frac{{{V}({cx(Rr, -X)})}}{{({cx(Rr, X)})({cx(Rr, -X)})}}",
                f"Multiply the numerator and denominator by the conjugate ${cx(Rr, -X)}$.",
                f"({V}*{cx_sym(Rr, -X)})/({cx_sym(Rr, X)}*{cx_sym(Rr, -X)})",
            ),
            S(
                f"= \\frac{{{cx(V * Rr, -V * X)}}}{{{sq(Rr)} + {sq(X)}}}",
                "Distribute in the numerator; the denominator is $R^2 + X^2$.",
                f"{cx_sym(V * Rr, -V * X)}/({Rr}**2 + ({X})**2)",
            ),
            S(
                f"= {cx(A, B)}",
                f"Divide both parts by ${D}$ and reduce. The real part is the in-phase current; the imaginary part is the reactive (quadrature) current.",
                cx_sym(A, B),
            ),
        ],
        "verify": {"source": f"{V}/{cx_sym(Rr, X)}"},
    }


def t_rotation(rng):
    x, y = nonzero(rng, -9, 9), nonzero(rng, -9, 9)
    p, q = nonzero(rng, -6, 6), nonzero(rng, -6, 6)
    rot = rng.choice(
        [
            ("i", "I", "90^\\circ counterclockwise", (0, 1)),
            ("-1", "-1", "180^\\circ", (-1, 0)),
            ("-i", "-I", "90^\\circ clockwise", (0, -1)),
        ]
    )
    rl, rs, rname, (ra, rb) = rot
    zr = sp.expand(sp.sympify(rs) * (x + y * sp.I))
    rx, ry = sp.re(zr), sp.im(zr)
    X, Y = rx + p, ry + q
    if rl == "i":
        mult_row = f"i({cx(x, y)}) = {terms([(x, 'i'), (y, 'i^2')])} = {cx(rx, ry)}"
        mult_expl = "Multiply by $i$ and use $i^2 = -1$: the point $(x, y)$ maps to $(-y, x)$."
    elif rl == "-i":
        mult_row = f"-i({cx(x, y)}) = {terms([(-x, 'i'), (-y, 'i^2')])} = {cx(rx, ry)}"
        mult_expl = "Multiply by $-i$ and use $i^2 = -1$: the point $(x, y)$ maps to $(y, -x)$."
    else:
        mult_row = f"-1\\cdot({cx(x, y)}) = {cx(rx, ry)}"
        mult_expl = "Multiplying by $-1$ negates both coordinates (a half turn)."
    zs = cx_sym(x, y)
    return {
        "category": "Cross-Subject Application",
        "context": "Graphics and Algorithms Application",
        "references": ["PRG-T01-C03"],
        "prompt": f"In a 2D game engine, points are stored as complex numbers $z = x + yi$. Multiplying by ${rl}$ rotates a point ${rname}$ about the origin. "
        f"The point $({x}, {y})$ is rotated ${rname}$ and then translated by $w = {cx(p, q)}$. Find the new point $(x', y')$.",
        "display": f"z' = {rl if rl != '-1' else '-1 \\cdot '}({cx(x, y)}) + ({cx(p, q)})",
        "plainText": f"({rs.replace('I', 'i')})*({cx_plain(x, y)}) + ({cx_plain(p, q)})",
        "answerSpec": {"type": "tuple", "values": [str(X), str(Y)], "labels": ["x'", "y'"], "acceptComplex": True},
        "answerDisplay": f"({num(X)}, {num(Y)})",
        "answerPlain": f"({X}, {Y})",
        "inputHint": "e.g. (4, -2) or 4 - 2i",
        "checkpointHint": f"After the rotation only, the point is $({num(rx)}, {num(ry)})$.",
        "commonTrapTag": "sign-slip",
        "steps": [
            S(f"z = {cx(x, y)}", f"Represent the point $({x}, {y})$ as a complex number.", eq=[zs, f"{x} + ({y})*I"]),
            S(mult_row, mult_expl, eq=[f"({rs})*{zs}", cx_sym(rx, ry)]),
            S(
                f"z' = ({cx(rx, ry)}) + ({cx(p, q)}) = {cx(X, Y)}",
                f"Add the translation $w$ component-wise. The new point is $({num(X)}, {num(Y)})$.",
                eq=[f"({rs})*{zs} + {cx_sym(p, q)}", cx_sym(X, Y)],
            ),
        ],
        "verify": {"tuple": [f"re(({rs})*{zs} + {cx_sym(p, q)})", f"im(({rs})*{zs} + {cx_sym(p, q)})"]},
    }


def t_parallel(rng):
    while True:
        a, b = rng.randint(1, 6), nonzero(rng, -6, 6)
        c, d = rng.randint(1, 6), nonzero(rng, -6, 6)
        Sr, Si = a + c, b + d
        if Sr != 0:
            break
    Pr, Pi = a * c - b * d, a * d + b * c
    val = sp.expand_complex((a + b * sp.I) * (c + d * sp.I) / ((a + c) + (b + d) * sp.I))
    A, B = sp.re(val), sp.im(val)
    steps = [
        S(
            f"Z_1 Z_2 = ({cx(a, b)})({cx(c, d)}) = {cx(Pr, Pi)}",
            "Multiply the impedances (FOIL, then $i^2 = -1$).",
            eq=[f"{cx_sym(a, b)}*{cx_sym(c, d)}", cx_sym(Pr, Pi)],
        ),
        S(
            f"Z_1 + Z_2 = {cx(Sr, Si)}",
            "Add the real parts and the imaginary parts.",
            eq=[f"{cx_sym(a, b)}+{cx_sym(c, d)}", cx_sym(Sr, Si)],
        ),
    ]
    src = f"({cx_sym(a, b)}*{cx_sym(c, d)})/({cx_sym(a, b)}+{cx_sym(c, d)})"
    if Si == 0:
        steps.append(
            S(
                f"Z_{{eq}} = \\frac{{{cx(Pr, Pi)}}}{{{Sr}}} = {cx(A, B)}",
                "The sum is real, so divide each part directly.",
                eq=[src, cx_sym(A, B)],
            )
        )
    else:
        div_steps, rA, rB = _division_steps(Pr, Pi, Sr, Si, lead=f"Z_{{eq}} = \\frac{{{cx(Pr, Pi)}}}{{{cx(Sr, Si)}}}")
        for st in div_steps:
            st["eq"] = [src, st.pop("val")]
        steps += div_steps
    return {
        "category": "Cross-Subject Application",
        "context": "Physics Application: Parallel Impedance",
        "references": ["PHY-T01-C19"],
        "prompt": f"Two branches with impedances $Z_1 = {cx(a, b)}$ ohms and $Z_2 = {cx(c, d)}$ ohms are connected in parallel. "
        f"Find the equivalent impedance $Z_{{eq}} = \\dfrac{{Z_1 Z_2}}{{Z_1 + Z_2}}$ in standard form $a + bi$.",
        "display": f"Z_{{eq}} = \\frac{{({cx(a, b)})({cx(c, d)})}}{{({cx(a, b)}) + ({cx(c, d)})}}",
        "plainText": f"(({cx_plain(a, b)})*({cx_plain(c, d)}))/(({cx_plain(a, b)}) + ({cx_plain(c, d)}))",
        **complex_answer(A, B),
        "checkpointHint": f"Compute the product first: $Z_1 Z_2 = {cx(Pr, Pi)}$.",
        "commonTrapTag": "conjugate-denominator",
        "steps": steps,
        "verify": {"source": src},
    }


TEMPLATES = [
    {"key": "radical-standard-form", "level": 1, "build": t_radical},
    {"key": "add-subtract", "level": 1, "build": t_add_sub},
    {"key": "power-of-i", "level": 1, "build": t_power_i},
    {"key": "multiply", "level": 2, "build": t_multiply},
    {"key": "divide-conjugate", "level": 2, "build": t_divide},
    {"key": "square-binomial", "level": 2, "build": t_square},
    {"key": "evaluate-polynomial", "level": 2, "build": t_eval_poly},
    {"key": "principal-root-trap", "level": 3, "build": t_principal_root},
    {"key": "power-sum", "level": 3, "build": t_power_sum},
    {"key": "find-the-flaw", "level": 3, "build": t_find_flaw},
    {"key": "ac-current", "level": 4, "build": t_ac_current},
    {"key": "rotation-2d", "level": 4, "build": t_rotation},
    {"key": "parallel-impedance", "level": 4, "build": t_parallel},
]
