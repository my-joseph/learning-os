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
    {"id": "sign-slip", "label": "Sign slip with $i^2 = -1$", "name": "Sign Slip (i^2 = -1)",
     "autoFrom": ["imag_sign_flip", "real_sign_flip", "whole_sign_flip"]},
    {"id": "distribute-negative-error", "label": "Did not distribute minus sign to imaginary component", "name": "Distribute Negative Error",
     "autoFrom": ["imag_sign_flip"]},
    {"id": "rotation-direction-inversion", "label": "Rotated in reverse direction (clockwise vs counterclockwise)", "name": "Rotation Direction Error",
     "autoFrom": ["swapped_parts"]},
    {"id": "principal-root", "label": "Combined $\\sqrt{-a}\\cdot\\sqrt{-b}$ into $\\sqrt{ab}$", "name": "Principal Root Trap", "autoFrom": []},
    {"id": "conjugate-denominator", "label": "Conjugate denominator: wrote $c^2 - d^2$ instead of $c^2 + d^2$", "name": "Conjugate Denominator Error",
     "autoFrom": ["complex_denominator"]},
    {"id": "power-cycle", "label": "Power cycle of $i$: wrong remainder of $n \\div 4$", "name": "Power of i Cycle Error", "autoFrom": []},
    {"id": "standard-form", "label": "Not in standard form $a + bi$", "name": "Unseparated Standard Form",
     "autoFrom": ["unseparated", "unexpanded_power", "uncombined_terms", "unreduced_fraction"]},
    {"id": "radical-simplify", "label": "Radical not simplified, e.g. $\\sqrt{48} = 4\\sqrt{3}$", "name": "Radical Simplification Error",
     "autoFrom": ["unsimplified_radical"]},
    {"id": "arithmetic", "label": "Arithmetic slip (FOIL or combining like terms)", "name": "Arithmetic Slip",
     "autoFrom": ["off_by_factor", "rounding", "swapped_parts", "constant_offset"]},
    {"id": "setup", "label": "Wrong setup or formula", "name": "Setup or Formula Error", "autoFrom": ["reciprocal", "wrong_component_count"]},
]

I_POW_VALUE = {0: ("1", "1"), 1: ("i", "I"), 2: ("-1", "-1"), 3: ("-i", "-I")}
I_POW_RULE = {0: "$i^0 = 1$", 1: "$i$", 2: "$i^2 = -1$", 3: "$i^3 = -i$"}


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
        "inputHint": "Standard form, e.g. 12 - 35i or -8/17 + 15/17 i",
    }


# ---------------------------------------------------------------------------
# Level 1 - Foundation
# ---------------------------------------------------------------------------
def t_radical(rng, form=None):
    m = rng.choice([2, 3, 5, 6, 7, 10])
    k = rng.randint(2, 7)
    a = k * k * m
    c = nonzero(rng, -9, 9)
    src = f"{c} + sqrt(-{a})"
    return {
        "form": "direct",
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
            S(f"{c} + \\sqrt{{-{a}}} = {c} + \\sqrt{{-1}}\\cdot\\sqrt{{{a}}}",
              "Split off the factor $-1$. This is valid here because only one radicand is negative.", f"{c} + sqrt(-1)*sqrt({a})"),
            S(f"= {c} + i\\sqrt{{{k * k}\\cdot {m}}}",
              f"Replace $\\sqrt{{-1}}$ with $i$ and factor out the largest perfect square ${k * k}$.", f"{c} + I*sqrt({k * k}*{m})"),
            S(f"= {c} + {k}\\sqrt{{{m}}}\\,i",
              f"Take $\\sqrt{{{k * k}}} = {k}$ outside the radical. Real part ${c}$, imaginary part ${k}\\sqrt{{{m}}}$.", f"{c} + {k}*sqrt({m})*I"),
        ],
        "verify": {"source": src, "trapValue": f"{c} + {a} i"},
    }


def t_add_sub(rng, form=None):
    a, b, c, d = (nonzero(rng, -9, 9) for _ in range(4))
    if form == "addition":
        s = 1
    elif form == "subtraction":
        s = -1
    else:
        s = rng.choice([1, -1])
    op = "+" if s == 1 else "-"
    form = "addition" if s == 1 else "subtraction"
    A, B = a + s * c, b + s * d
    if s == 1:
        trap_A, trap_B = a - c, b - d
        trap_tag = "sign-slip"
    else:
        trap_A, trap_B = a - c, b + d  # Mistake: forgot to distribute minus sign to imaginary part
        trap_tag = "distribute-negative-error"
    src = f"{cx_sym(a, b)} {op} {cx_sym(c, d)}"
    distribute = "Remove the parentheses." if s == 1 else "Distribute the minus sign to BOTH parts of the second number."
    return {
        "form": form,
        "category": "Core Skill",
        "prompt": "Simplify and write the result in standard form $a + bi$.",
        "display": f"({cx(a, b)}) {op} ({cx(c, d)})",
        "plainText": f"({cx_plain(a, b)}) {op} ({cx_plain(c, d)})",
        **complex_answer(A, B),
        "checkpointHint": f"The real parts combine to ${num(A)}$.",
        "commonTrapTag": trap_tag,
        "steps": [
            S(f"({cx(a, b)}) {op} ({cx(c, d)}) = {terms([(a, ''), (b, 'i'), (s * c, ''), (s * d, 'i')])}",
              distribute, f"{a} + {b}*I + ({s * c}) + ({s * d})*I"),
            S(f"= ({terms([(a, ''), (s * c, '')])}) + ({terms([(b, ''), (s * d, '')])})i",
              "Group the real parts together and the imaginary parts together.", f"({a} + ({s * c})) + ({b} + ({s * d}))*I"),
            S(f"= {cx(A, B)}", f"Real part ${num(A)}$, imaginary part ${num(B)}$.", cx_sym(A, B)),
        ],
        "verify": {"source": src, "trapValue": cx_plain(trap_A, trap_B)},
    }


def t_power_i(rng, form=None):
    if form and str(form).startswith("rem-"):
        r = int(str(form).split("-")[1]) % 4
        q = rng.randint(6, 49)
        n = 4 * q + r
    else:
        n = rng.randint(23, 199)
        q, r = divmod(n, 4)
    latex_v, sym_v = I_POW_VALUE[r]
    trap_latex, _ = I_POW_VALUE[(r + 1) % 4]
    i_split = f"i^{{{r}}}" if r in (2, 3) else ("i" if r == 1 else "1")
    return {
        "form": f"rem-{r}",
        "category": "Core Skill",
        "prompt": "Simplify the power of $i$.",
        "display": f"i^{{{n}}}",
        "plainText": f"i^{n}",
        **complex_answer(sp.re(sp.sympify(sym_v)), sp.im(sp.sympify(sym_v))),
        "inputHint": "One of 1, i, -1, -i",
        "checkpointHint": f"Divide the exponent by $4$ and keep only the remainder.",
        "commonTrapTag": "power-cycle",
        "steps": [
            S(f"i^{{{n}}} = i^{{4\\cdot {q} + {r}}} = (i^4)^{{{q}}}\\cdot {i_split}",
              f"Divide the exponent by $4$: ${n} = 4 \\cdot {q} + {r}$, then split the power.", f"(I**4)**{q} * I**{r}"),
            S(f"= 1^{{{q}}}\\cdot {i_split}", "Use $i^4 = 1$, so any power of $i^4$ equals $1$.", f"1 * I**{r}"),
            S(f"= {latex_v}", f"Use the cycle: {I_POW_RULE[r]}.", sym_v),
        ],
        "verify": {"source": f"I**{n}", "trapValue": trap_latex},
    }


# ---------------------------------------------------------------------------
# Level 2 - Standard Exam
# ---------------------------------------------------------------------------
def t_multiply(rng, form=None):
    if form == "missing-factor":
        form = "missing-coefficient"
    available_forms = ["direct", "missing-coefficient", "pure-imaginary"]
    if form not in available_forms:
        form = rng.choice(available_forms)

    if form == "direct":
        a, b, c, d = (nonzero(rng, -7, 7) for _ in range(4))
        ac, ad, bc, bd = a * c, a * d, b * c, b * d
        A, B = ac - bd, ad + bc
        trap_A = ac + bd  # Mistake: treating i^2 = +1
        src = f"{cx_sym(a, b)} * {cx_sym(c, d)}"
        return {
            "form": "direct",
            "category": "Core Skill",
            "skill": "MTH-COMPLEX-MULTIPLICATION",
            "level": 2,
            "verificationLevel": "machine-verified",
            "prompt": "Multiply and write the product in standard form $a + bi$.",
            "display": f"({cx(a, b)})({cx(c, d)})",
            "plainText": f"({cx_plain(a, b)})*({cx_plain(c, d)})",
            **complex_answer(A, B),
            "checkpointHint": f"After FOIL, the $i^2$ term is ${terms([(bd, 'i^2')])}$, which equals ${num(-bd)}$.",
            "commonTrapTag": "sign-slip",
            "steps": [
                S(f"({cx(a, b)})({cx(c, d)}) = {terms([(ac, ''), (ad, 'i'), (bc, 'i'), (bd, 'i^2')])}",
                  "Distribute every term (FOIL: First, Outer, Inner, Last).", f"{ac} + ({ad})*I + ({bc})*I + ({bd})*I**2"),
                S(f"= {terms([(ac, ''), (ad + bc, 'i')], keep_zero=True)} {'-' if bd < 0 else '+'} {abs(bd)}(-1)",
                  "Combine the two imaginary terms and substitute $i^2 = -1$.", f"{ac} + ({ad + bc})*I + ({bd})*(-1)"),
                S(f"= {cx(A, B)}", f"The last term becomes ${num(-bd)}$; add it to the real part: ${num(ac)} {'+' if -bd >= 0 else '-'} {abs(bd)} = {num(A)}$.", cx_sym(A, B)),
            ],
            "verify": {"source": src, "trapValue": cx_plain(trap_A, B)},
        }

    elif form in ("missing-coefficient", "missing-factor"):
        # Solve for missing real coefficient k in (a + ki)(c + di) = A + Bi without complex division
        # Real part: ac + (k*d)*i^2 = ac - k*d = A => k*d = ac - A => k = (ac - A) / d
        # Trap: treating i^2 = +1 => ac + k*d = A => k_trap = (A - ac) / d = -k
        a = nonzero(rng, -5, 5)
        c = nonzero(rng, -5, 5)
        d = nonzero(rng, -5, 5)
        k = 0
        while k == 0:
            k = nonzero(rng, -5, 5)
        assert k != 0, "k must be non-zero for trap=-k provenance"
        ac = a * c
        kd = k * d
        A = ac - kd
        B = a * d + k * c
        k_trap = -k

        d_sign = "-" if d > 0 else "+"
        d_abs = abs(d)
        dk_str = f"{d_abs}k" if d_abs != 1 else "k"

        c_sign = "+" if c > 0 else "-"
        c_abs = abs(c)
        ck_str = f"{c_abs}ki" if c_abs != 1 else "ki"

        last_sign = "+" if d > 0 else "-"
        last_str = f"{d_abs}ki^2" if d_abs != 1 else "ki^2"

        t_first = terms([(ac, ""), (a * d, "i")])
        step1_latex = f"({num(a)} + ki)({cx(c, d)}) = {t_first} {c_sign} {ck_str} {last_sign} {last_str} = {cx(A, B)}"
        step2_latex = f"\\text{{Equate real parts: }} {num(ac)} + ({num(d)}k)i^2 = {num(A)} \\implies {num(ac)} {d_sign} {dk_str} = {num(A)}"
        step3_latex = f"{d_sign} {dk_str} = {num(A - ac)} \\implies k = {k}"

        steps = [
            S(step1_latex,
              "Expand the left-hand side with FOIL (First, Outer, Inner, Last).",
              eq=(f"({a} + ({k})*I)*({c} + ({d})*I)", f"{ac} + ({a * d})*I + ({c * k})*I + ({d * k})*I**2")),
            S(step2_latex,
              "The real part comes from First and Last terms: $(a)(c) + (ki)(di) = ac + dk \\cdot i^2$. Substitute $i^2 = -1$.",
              eq=(f"{ac} - ({d})*({k})", f"{A}")),
            S(step3_latex,
              f"Solve for $k$: {num(ac)} {d_sign} {dk_str} = {num(A)} yields $k = {k}$ (watch the sign slip: $i^2 = -1$, not $+1$).",
              val=str(k)),
        ]
        return {
            "form": "missing-coefficient",
            "category": "Reverse Reasoning",
            "skill": "MTH-COMPLEX-MULTIPLICATION",
            "level": 2,
            "verificationLevel": "machine-verified",
            "prompt": "Find the missing real coefficient $k$ that satisfies the equation.",
            "display": f"({num(a)} + ki)({cx(c, d)}) = {cx(A, B)}",
            "plainText": f"({a} + k*i)*({cx_plain(c, d)}) = {cx_plain(A, B)}",
            "answerSpec": {"type": "number", "value": k},
            "answerDisplay": str(k),
            "answerPlain": str(k),
            "inputHint": "Enter integer value for k",
            "checkpointHint": f"In FOIL, the product of the imaginary terms is $(ki)({num(d)}i) = {num(d)}k \\cdot i^2 = {num(-d)}k$.",
            "trapValue": str(k_trap),
            "commonTrapTag": "sign-slip",
            "steps": steps,
            "verify": {"source": str(k), "trapValue": str(k_trap)},
        }

    else:
        # pure-imaginary: (k*i)(a + bi) = -k*b + k*a*i
        k = nonzero(rng, -6, 6)
        a, b = (nonzero(rng, -6, 6) for _ in range(2))
        ans_re = -k * b
        ans_im = k * a
        trap_re = k * b  # forgetting that i^2 = -1
        src = f"({k}*I)*({cx_sym(a, b)})"
        first_expanded = terms([(ans_im, 'i'), (k * b, 'i^2')])
        im_part = terms([(ans_im, 'i')])
        sign_quad = '-' if k * b < 0 else '+'
        val_quad = abs(k * b)
        step2_latex = f"= {first_expanded} = {im_part} {sign_quad} {val_quad}(-1)"
        steps = [
            S(f"({num(k)}i)({cx(a, b)}) = ({num(k)}i)({num(a)}) + ({num(k)}i)({num(b)}i)",
              "Distribute the monomial across both terms.", src),
            S(step2_latex,
              "Substitute $i^2 = -1$ into the quadratic term.", src),
            S(f"= {cx(ans_re, ans_im)}",
              f"Rewrite in standard form $a + bi$ with real part ${num(ans_re)}$ first.", cx_sym(ans_re, ans_im)),
        ]
        return {
            "form": "pure-imaginary",
            "category": "Monomial Distribution",
            "skill": "MTH-COMPLEX-MULTIPLICATION",
            "level": 2,
            "verificationLevel": "machine-verified",
            "prompt": "Multiply and write the product in standard form $a + bi$.",
            "display": f"({num(k)}i)({cx(a, b)})",
            "plainText": f"({num(k)}i)*({cx_plain(a, b)})",
            **complex_answer(ans_re, ans_im),
            "inputHint": "Enter complex number in standard form a + bi",
            "checkpointHint": f"Remember that $i \\cdot i = i^2 = -1$, so $({num(k)}i)({num(b)}i) = {num(ans_re)}$.",
            "commonTrapTag": "sign-slip",
            "steps": steps,
            "verify": {"source": src, "trapValue": cx_plain(trap_re, ans_im)},
        }


def _division_steps(a, b, c, d, lead=None):
    """Steps for (a+bi)/(c+di). Returns (steps, A/D, B/D)."""
    D = c * c + d * d
    A, B = a * c + b * d, b * c - a * d
    num_l, den_l = cx(a, b), cx(c, d)
    first = lead if lead else f"\\frac{{{num_l}}}{{{den_l}}}"
    steps = [
        S(f"{first} = \\frac{{({num_l})({cx(c, -d)})}}{{({den_l})({cx(c, -d)})}}",
          f"Multiply the numerator and denominator by the conjugate ${cx(c, -d)}$ of the denominator.",
          f"({cx_sym(a, b)}*{cx_sym(c, -d)})/({cx_sym(c, d)}*{cx_sym(c, -d)})"),
        S(f"= \\frac{{{terms([(a * c, ''), (-a * d, 'i'), (b * c, 'i'), (-b * d, 'i^2')])}}}{{{sq(c)} + {sq(d)}}}",
          "Expand the numerator with FOIL. The denominator is $(c + di)(c - di) = c^2 + d^2$ (always a plus sign).",
          f"({a * c} + ({-a * d})*I + ({b * c})*I + ({-b * d})*I**2)/(({c})**2 + ({d})**2)"),
        S(f"= \\frac{{{cx(A, B)}}}{{{D}}}", "Substitute $i^2 = -1$ and combine like terms.", f"{cx_sym(A, B)}/{D}"),
    ]
    rA, rB = R(A) / D, R(B) / D
    explain = f"Split into real and imaginary parts and reduce each fraction." if (rA.q != 1 or rB.q != 1) else f"Divide each part by ${D}$."
    if D != 1:
        steps.append(S(f"= {cx(rA, rB)}", explain, cx_sym(rA, rB)))
    return steps, rA, rB


def t_divide(rng, form=None):
    available_forms = ["direct", "reciprocal", "pure-imaginary-denom"]
    if form not in available_forms:
        form = rng.choice(available_forms)

    if form == "direct":
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
        trap_rA, trap_rB = R(a * c - b * d) / (c * c + d * d), R(b * c + a * d) / (c * c + d * d)
        return {
            "form": "direct",
            "category": "Core Skill",
            "skill": "MTH-COMPLEX-DIVISION-CONJUGATE",
            "level": 2,
            "verificationLevel": "machine-verified",
            "prompt": "Divide and write the quotient in standard form $a + bi$.",
            "display": f"\\frac{{{cx(a, b)}}}{{{cx(c, d)}}}",
            "plainText": f"({cx_plain(a, b)})/({cx_plain(c, d)})",
            **complex_answer(rA, rB),
            "checkpointHint": f"The new denominator is ${sq(c)} + {sq(d)} = {c * c + d * d}$.",
            "commonTrapTag": "conjugate-denominator",
            "steps": steps,
            "verify": {"source": f"{cx_sym(a, b)}/{cx_sym(c, d)}", "trapValue": cx_plain(trap_rA, trap_rB)},
        }

    elif form == "reciprocal":
        # Reciprocal of c + di: 1 / (c + di) = (c - di) / (c^2 + d^2)
        c = nonzero(rng, -4, 4)
        d = nonzero(rng, -4, 4)
        D = c * c + d * d
        rA = R(c) / D
        rB = R(-d) / D
        # Trap: forgot to conjugate denominator (c + di) / (c^2 + d^2)
        trap_rA = R(c) / D
        trap_rB = R(d) / D
        src = f"1/({cx_sym(c, d)})"
        steps = [
            S(f"\\frac{{1}}{{{cx(c, d)}}} = \\frac{{1 \\cdot ({cx(c, -d)})}}{{({cx(c, d)})({cx(c, -d)})}}",
              f"Multiply numerator and denominator by the complex conjugate ${cx(c, -d)}$.", src),
            S(f"= \\frac{{{cx(c, -d)}}}{{{sq(c)} + {sq(d)}}} = \\frac{{{cx(c, -d)}}}{{{D}}}",
              f"The denominator expands to $c^2 + d^2 = {sq(c)} + {sq(d)} = {D}$.", src),
            S(f"= {cx(rA, rB)}", "Split into real and imaginary components in standard form $a + bi$.", cx_sym(rA, rB)),
        ]
        return {
            "form": "reciprocal",
            "category": "Multiplicative Inverse",
            "skill": "MTH-COMPLEX-DIVISION-CONJUGATE",
            "level": 2,
            "verificationLevel": "machine-verified",
            "prompt": f"Find the reciprocal (multiplicative inverse) of $z = {cx(c, d)}$ in standard form $a + bi$.",
            "display": f"\\frac{{1}}{{{cx(c, d)}}}",
            "plainText": f"1/({cx_plain(c, d)})",
            **complex_answer(rA, rB),
            "inputHint": "Enter complex number in standard form a + bi (fractions allowed)",
            "checkpointHint": f"The conjugate of ${cx(c, d)}$ is ${cx(c, -d)}$; denominator is ${D}$.",
            "commonTrapTag": "conjugate-denominator",
            "steps": steps,
            "verify": {"source": src, "trapValue": cx_plain(trap_rA, trap_rB)},
        }

    else:
        # pure-imaginary-denom: (a + bi) / (d*i) = (b/d) - (a/d)*i
        d = nonzero(rng, -5, 5)
        while True:
            a = nonzero(rng, -6, 6)
            b = nonzero(rng, -6, 6)
            if a != b and a != -b:
                break
        rA = R(b) / d
        rB = R(-a) / d
        # Trap: student forgot that 1/i = -i, wrote (a/d) + (b/d)*i
        trap_rA = R(a) / d
        trap_rB = R(b) / d
        src = f"({cx_sym(a, b)})/({d}*I)"
        num_expanded = terms([(-a * d, 'i'), (-b * d, 'i^2')])
        num_sub = terms([(b * d, ''), (-a * d, 'i')])
        conj_denom = f"-{d}i" if d > 0 else f"{abs(d)}i"
        denom_sq = d * d
        steps = [
            S(f"\\frac{{{cx(a, b)}}}{{{num(d)}i}} = \\frac{{({cx(a, b)})({conj_denom})}}{{({num(d)}i)({conj_denom})}}",
              f"Multiply numerator and denominator by the conjugate ${conj_denom}$.", src),
            S(f"= \\frac{{{num_expanded}}}{{{denom_sq}}} = \\frac{{{num_sub}}}{{{denom_sq}}}",
              "Substitute $i^2 = -1$ in numerator and denominator.", src),
            S(f"= {cx(rA, rB)}", "Reduce each fraction and write in standard form $a + bi$.", cx_sym(rA, rB)),
        ]
        return {
            "form": "pure-imaginary-denom",
            "category": "Monomial Denominator",
            "skill": "MTH-COMPLEX-DIVISION-CONJUGATE",
            "level": 2,
            "verificationLevel": "machine-verified",
            "prompt": "Divide and write the quotient in standard form $a + bi$.",
            "display": f"\\frac{{{cx(a, b)}}}{{{num(d)}i}}",
            "plainText": f"({cx_plain(a, b)})/({num(d)}i)",
            **complex_answer(rA, rB),
            "inputHint": "Enter complex number in standard form a + bi (fractions allowed)",
            "checkpointHint": "Multiplying by $-i$ swaps real and imaginary parts: $1/i = -i$.",
            "commonTrapTag": "conjugate-denominator",
            "steps": steps,
            "verify": {"source": src, "trapValue": cx_plain(trap_rA, trap_rB)},
        }


def t_square(rng, form=None):
    a, b = nonzero(rng, -8, 8), nonzero(rng, -8, 8)
    A, B = a * a - b * b, 2 * a * b
    trap_A = a * a + b * b  # Mistake: (bi)^2 = +b^2 instead of -b^2
    return {
        "form": "direct",
        "category": "Core Skill",
        "prompt": "Expand and write the result in standard form $a + bi$.",
        "display": f"({cx(a, b)})^2",
        "plainText": f"({cx_plain(a, b)})^2",
        **complex_answer(A, B),
        "checkpointHint": f"Use $(a + bi)^2 = a^2 + 2abi + b^2 i^2$. Here $b^2 i^2 = {num(-b * b)}$.",
        "commonTrapTag": "sign-slip",
        "steps": [
            S(f"({cx(a, b)})^2 = {sq(a)} + 2({num(a)})({cx(0, b)}) + ({cx(0, b)})^2",
              "Apply the square of a binomial: $(x + y)^2 = x^2 + 2xy + y^2$.", f"({a})**2 + 2*({a})*({b}*I) + ({b}*I)**2"),
            S(f"= {terms([(a * a, ''), (2 * a * b, 'i'), (b * b, 'i^2')])}",
              "Evaluate each square and product; note $(bi)^2 = b^2 i^2$.", f"{a * a} + ({2 * a * b})*I + {b * b}*I**2"),
            S(f"= {cx(A, B)}", f"Use $i^2 = -1$, so ${b * b}i^2 = {num(-b * b)}$, then combine the real parts.", cx_sym(A, B)),
        ],
        "verify": {"source": f"{cx_sym(a, b)}**2", "trapValue": cx_plain(trap_A, B)},
    }


def t_eval_poly(rng, form=None):
    a, b = nonzero(rng, -4, 4), nonzero(rng, -4, 4)
    if rng.random() < 0.4:
        p, q = -2 * a, a * a + b * b
    else:
        p, q = nonzero(rng, -6, 6), rng.randint(-9, 9)
    x2r, x2i = a * a - b * b, 2 * a * b
    A, B = x2r + p * a + q, x2i + p * b
    trap_A = (a * a + b * b) + p * a + q
    poly = terms([(1, "x^2"), (p, "x"), (q, "")])
    z = cx(a, b)
    q_part = f" {'+' if q >= 0 else '-'} {abs(q)}" if q != 0 else ""
    src = f"{cx_sym(a, b)}**2 + ({p})*{cx_sym(a, b)} + ({q})"
    return {
        "form": "direct",
        "category": "Combined with Prior Units",
        "prompt": f"Let $f(x) = {poly}$. Evaluate $f({z})$ and write the result in standard form $a + bi$.",
        "display": f"f({z}) = ({z})^2 {'+' if p > 0 else '-'} {abs(p)}({z}){q_part}",
        "plainText": f"({cx_plain(a, b)})^2 + ({p})*({cx_plain(a, b)}) + ({q})",
        **complex_answer(A, B),
        "checkpointHint": f"First compute $({z})^2 = {cx(x2r, x2i)}$.",
        "commonTrapTag": "sign-slip",
        "steps": [
            S(f"f({z}) = ({z})^2 {'+' if p > 0 else '-'} {abs(p)}({z}){q_part}",
              "Substitute the complex number for every $x$, keeping it in parentheses.", src),
            S(f"= ({cx(x2r, x2i)}) + ({cx(p * a, p * b)}){q_part}",
              f"Square first: $({z})^2 = {sq(a)} + 2({num(a)})({cx(0, b)}) + ({cx(0, b)})^2 = {cx(x2r, x2i)}$. Then distribute ${p}$.",
              f"{cx_sym(x2r, x2i)} + {cx_sym(p * a, p * b)} + ({q})"),
            S(f"= {cx(A, B)}", "Add the real parts and the imaginary parts separately." + (" A result of $0$ means the number is a root of $f$." if A == 0 and B == 0 else ""), cx_sym(A, B)),
        ],
        "verify": {"source": src, "trapValue": cx_plain(trap_A, B)},
    }


# ---------------------------------------------------------------------------
# Level 3 - Trap & Diagnostic
# ---------------------------------------------------------------------------
def _i_radical(k, m):
    return f"{k}i" if m == 1 else f"{k}\\sqrt{{{m}}}\\,i"


def t_principal_root(rng, form=None):
    m = rng.choice([1, 2, 3, 5, 7])
    k1, k2 = rng.randint(2, 6), rng.randint(2, 6)
    a, b = k1 * k1 * m, k2 * k2 * m
    P = k1 * k2 * m
    return {
        "form": "direct",
        "category": "Trap & Edge Case",
        "prompt": "Simplify the product. Be careful with the rule $\\sqrt{x}\\cdot\\sqrt{y} = \\sqrt{xy}$.",
        "display": f"\\sqrt{{-{a}}}\\cdot\\sqrt{{-{b}}}",
        "plainText": f"sqrt(-{a})*sqrt(-{b})",
        **complex_answer(-P, 0),
        "inputHint": "e.g. -15 or -24",
        "checkpointHint": f"Rewrite each factor with $i$ first: $\\sqrt{{-{a}}} = {_i_radical(k1, m)}$.",
        "commonTrapTag": "principal-root",
        "steps": [
            S(f"\\sqrt{{-{a}}}\\cdot\\sqrt{{-{b}}} = ({_i_radical(k1, m)})({_i_radical(k2, m)})",
              "Convert each radical to $i$-form FIRST. Combining into $\\sqrt{(-a)(-b)}$ is invalid because $\\sqrt{x}\\sqrt{y} = \\sqrt{xy}$ only holds for $x, y \\ge 0$.",
              f"({k1}*sqrt({m})*I)*({k2}*sqrt({m})*I)"),
            S(f"= {k1 * k2}" + ("" if m == 1 else f"(\\sqrt{{{m}}})^2") + "\\, i^2",
              "Multiply the coefficients, the radicals, and the $i$ factors separately.", f"{k1 * k2}*sqrt({m})**2*I**2"),
            S(f"= {P}(-1) = {num(-P)}", f"Use $i^2 = -1$. The tempting answer ${P}$ is wrong by a sign.", f"{-P}"),
        ],
        "verify": {"source": f"sqrt(-{a})*sqrt(-{b})", "trapValue": str(P)},
    }


def t_power_sum(rng, form=None):
    exps = rng.sample(range(10, 130), 3)
    coefs = [nonzero(rng, -5, 5) for _ in range(3)]
    rems = [e % 4 for e in exps]
    total = sum(c * sp.I ** r for c, r in zip(coefs, rems))
    A, B = sp.re(total), sp.im(total)
    trap_A = A + coefs[0]  # Mistake: wrong remainder on first term
    def _pow_part(r):
        return "(1)" if r == 0 else ("(i)" if r == 1 else f"i^{{{r}}}")

    display = terms([(c, f"i^{{{e}}}") for c, e in zip(coefs, exps)])
    reduced = terms([(c, _pow_part(r)) for c, r in zip(coefs, rems)], keep_zero=True)
    sub_parts = []
    for c, r in zip(coefs, rems):
        v = {0: "(1)", 1: "(i)", 2: "(-1)", 3: "(-i)"}[r]
        sub_parts.append((c, v))
    substituted = terms(sub_parts)
    mods = ", ".join(f"{e} = 4\\cdot {e // 4} + {e % 4}" for e in exps)
    src = " + ".join(f"({c})*I**{e}" for c, e in zip(coefs, exps))
    return {
        "form": "direct",
        "category": "Trap & Edge Case",
        "prompt": "Simplify and write the result in standard form $a + bi$.",
        "display": display,
        "plainText": " + ".join(f"({c})*i^{e}" for c, e in zip(coefs, exps)),
        **complex_answer(A, B),
        "checkpointHint": f"The remainders of the exponents divided by $4$ are ${rems[0]}, {rems[1]}, {rems[2]}$.",
        "commonTrapTag": "power-cycle",
        "steps": [
            S(f"{display} = {reduced}", f"Reduce each exponent modulo $4$: ${mods}$.",
              " + ".join(f"({c})*I**{r}" for c, r in zip(coefs, rems))),
            S(f"= {substituted}", "Replace each power using the cycle: remainder 0 is 1, remainder 1 is i, remainder 2 is -1, remainder 3 is -i.",
              " + ".join(f"({c})*({ {0: '1', 1: 'I', 2: '-1', 3: '-I'}[r] })" for c, r in zip(coefs, rems))),
            S(f"= {cx(A, B)}", "Combine the real terms and the imaginary terms; watch the sign of each coefficient.", cx_sym(A, B)),
        ],
        "verify": {"source": src, "trapValue": cx_plain(trap_A, B)},
    }


def t_find_flaw(rng, form=None):
    while True:
        a, b, c, d = (nonzero(rng, -6, 6) for _ in range(4))
        ac, ad, bc, bd = a * c, a * d, b * c, b * d
        if ad + bc != 0 and ad - bc != 0:
            break
    A, B = ac - bd, ad + bc
    head = f"({cx(a, b)})({cx(c, d)})"
    correct = [
        (f"{head} = {terms([(ac, ''), (ad, 'i'), (bc, 'i'), (bd, 'i^2')])}", f"{ac} + ({ad})*I + ({bc})*I + ({bd})*I**2"),
        (f"= {terms([(ac, ''), (ad + bc, 'i')], keep_zero=True)} {'-' if bd < 0 else '+'} {abs(bd)}(-1)", f"{ac} + ({ad + bc})*I + ({bd})*(-1)"),
        (f"= {cx(A, B)}", cx_sym(A, B)),
    ]
    if form == "flaw-line-1":
        kind = 1
    elif form == "flaw-line-2":
        kind = 2
    elif form == "flaw-line-3":
        kind = 3
    else:
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
        shown = [correct[0][0],
                 f"= {terms([(ac, ''), (ad + bc, 'i')], keep_zero=True)} {'-' if bd < 0 else '+'} {abs(bd)}(1)",
                 f"= {cx(ac + bd, ad + bc)}"]
        vals = [correct[0][1], f"{ac} + ({ad + bc})*I + ({bd})*(1)", None]
        why = "Line 2 is wrong: it replaced $i^2$ with $+1$ instead of $-1$."
    else:  # combining error in the final line
        shown = [correct[0][0], correct[1][0], f"= {cx(ac + bd, ad + bc)}"]
        vals = [correct[0][1], correct[1][1], cx_sym(ac + bd, ad + bc)]
        why = f"Line 3 is wrong: ${num(bd)}(-1) = {num(-bd)}$, so the real part is ${num(ac)} {'+' if -bd >= 0 else '-'} {abs(bd)} = {num(A)}$."
    flaw_line = kind
    aligned = "\\begin{aligned}" + " \\\\ ".join(
        f"&\\text{{Line {i + 1}: }}\\; {ln}" for i, ln in enumerate(shown)) + "\\end{aligned}"
    steps = [S(correct[0][0], ("Correct Line 1. " if kind != 1 else why + " Correct version shown.") + " FOIL every pair of terms.", correct[0][1]),
             S(correct[1][0], (why + " Correct version shown." if kind == 2 else "Correct Line 2: combine imaginary terms and use $i^2 = -1$."), correct[1][1]),
             S(correct[2][0], (why if kind == 3 else "Correct Line 3: combine the real parts.") + f" The true product is ${cx(A, B)}$.", correct[2][1])]
    line_trap_map = {1: "arithmetic", 2: "sign-slip", 3: "standard-form"}
    options = [
        {"id": str(i), "label": f"Line {i}", "trapTag": line_trap_map[i]}
        for i in (1, 2, 3)
    ]
    trap_choice = str((flaw_line % 3) + 1)
    return {
        "form": f"flaw-line-{flaw_line}",
        "category": "Trap & Edge Case",
        "prompt": "A student multiplied two complex numbers as shown. Which line contains the FIRST error?",
        "display": aligned,
        "plainText": f"({cx_plain(a, b)})*({cx_plain(c, d)})",
        "answerSpec": {"type": "choice", "options": options, "correct": str(flaw_line)},
        "answerDisplay": f"\\text{{Line {flaw_line}}}",
        "answerPlain": str(flaw_line),
        "inputHint": "Choose a line",
        "checkpointHint": f"Compute the product yourself first; the correct result is not ${cx(*_last_vals(kind, ac, ad, bc, bd))}$.",
        "commonTrapTag": "sign-slip",
        "steps": steps,
        "verify": {
            "source": f"{cx_sym(a, b)}*{cx_sym(c, d)}",
            "flaw": {"values": vals, "firstWrong": flaw_line},
            "trapValue": trap_choice,
        },
    }


def _last_vals(kind, ac, ad, bc, bd):
    if kind == 1:
        return (ac - bd, ad - bc)
    return (ac + bd, ad + bc)


# ---------------------------------------------------------------------------
# Level 4 - Applied Synthesis
# ---------------------------------------------------------------------------
IMPEDANCES = [(3, 4), (4, -3), (1, 2), (2, -1), (6, 8), (5, -12), (2, 3), (3, -2), (8, -6), (1, -3)]


def t_ac_current(rng, form=None):
    Rr, X = rng.choice(IMPEDANCES)
    V = rng.choice([10, 20, 25, 26, 30, 39, 50, 52, 60, 65, 100])
    D = Rr * Rr + X * X
    A, B = R(V * Rr) / D, R(-V * X) / D
    trap_B = R(V * X) / D  # Mistake: forgot to negate imaginary part of conjugate
    return {
        "form": "direct",
        "category": "Cross-Subject Application",
        "context": "Physics Application: AC Circuits",
        "references": ["MTH-T02-C01-U01", "PHY-T01-C19"],
        "prompt": f"In an AC circuit the voltage phasor is $V = {V}$ volts and the impedance is $Z = {cx(Rr, X)}$ ohms. "
                  f"Using Ohm's law $I = \\dfrac{{V}}{{Z}}$, find the current phasor $I$ in standard form $a + bi$ (amperes).",
        "display": f"I = \\frac{{{V}}}{{{cx(Rr, X)}}}",
        "plainText": f"{V}/({cx_plain(Rr, X)})",
        **complex_answer(A, B),
        "checkpointHint": f"Multiply by the conjugate ${cx(Rr, -X)}$; the denominator becomes ${D}$.",
        "commonTrapTag": "conjugate-denominator",
        "steps": [
            S(f"I = \\frac{{V}}{{Z}} = \\frac{{{V}}}{{{cx(Rr, X)}}}", "Substitute the given voltage and impedance into Ohm's law.", f"{V}/{cx_sym(Rr, X)}"),
            S(f"= \\frac{{{V}({cx(Rr, -X)})}}{{({cx(Rr, X)})({cx(Rr, -X)})}}", f"Multiply the numerator and denominator by the conjugate ${cx(Rr, -X)}$.",
              f"({V}*{cx_sym(Rr, -X)})/({cx_sym(Rr, X)}*{cx_sym(Rr, -X)})"),
            S(f"= \\frac{{{cx(V * Rr, -V * X)}}}{{{sq(Rr)} + {sq(X)}}}", "Distribute in the numerator; the denominator is $R^2 + X^2$.",
              f"{cx_sym(V * Rr, -V * X)}/({Rr}**2 + ({X})**2)"),
            S(f"= {cx(A, B)}", f"Divide both parts by ${D}$ and reduce. The real part is the in-phase current; the imaginary part is the reactive (quadrature) current.", cx_sym(A, B)),
        ],
        "verify": {"source": f"{V}/{cx_sym(Rr, X)}", "trapValue": cx_plain(A, trap_B)},
    }


def t_rotation(rng, form=None):
    x, y = nonzero(rng, -9, 9), nonzero(rng, -9, 9)
    p, q = nonzero(rng, -6, 6), nonzero(rng, -6, 6)
    rot_options = [("i", "I", "90^\\circ counterclockwise", (0, 1)),
                   ("-1", "-1", "180^\\circ", (-1, 0)),
                   ("-i", "-I", "90^\\circ clockwise", (0, -1))]
    if form == "rot-i":
        rot = rot_options[0]
    elif form == "rot--1":
        rot = rot_options[1]
    elif form == "rot--i":
        rot = rot_options[2]
    else:
        rot = rng.choice(rot_options)
    rl, rs, rname, (ra, rb) = rot
    zr = sp.expand(sp.sympify(rs) * (x + y * sp.I))
    rx, ry = sp.re(zr), sp.im(zr)
    X, Y = rx + p, ry + q
    if rl == "i":
        mult_row = f"i({cx(x, y)}) = {terms([(x, 'i'), (y, 'i^2')])} = {cx(rx, ry)}"
        mult_expl = "Multiply by $i$ and use $i^2 = -1$: the point $(x, y)$ maps to $(-y, x)$."
        trap_tuple = f"({y + p}, {-x + q})"  # Mistake: rotated clockwise instead of counterclockwise
        trap_tag = "rotation-direction-inversion"
    elif rl == "-i":
        mult_row = f"-i({cx(x, y)}) = {terms([(-x, 'i'), (-y, 'i^2')])} = {cx(rx, ry)}"
        mult_expl = "Multiply by $-i$ and use $i^2 = -1$: the point $(x, y)$ maps to $(y, -x)$."
        trap_tuple = f"({-y + p}, {x + q})"  # Mistake: rotated counterclockwise instead of clockwise
        trap_tag = "rotation-direction-inversion"
    else:
        mult_row = f"-1\\cdot({cx(x, y)}) = {cx(rx, ry)}"
        mult_expl = "Multiplying by $-1$ negates both coordinates (a half turn)."
        trap_tuple = f"({x + p}, {-y + q})"  # Mistake: only negated y coordinate
        trap_tag = "sign-slip"
    zs = cx_sym(x, y)
    return {
        "form": f"rot-{rl}",
        "category": "Cross-Subject Application",
        "context": "Graphics and Algorithms Application",
        "references": ["MTH-T02-C01-U01", "PRG-T01-C03"],
        "prompt": f"In a 2D game engine, points are stored as complex numbers $z = x + yi$. Multiplying by ${rl}$ rotates a point ${rname}$ about the origin. "
                  f"The point $({x}, {y})$ is rotated ${rname}$ and then translated by $w = {cx(p, q)}$. Find the new point $(x', y')$.",
        "display": f"z' = {rl if rl != '-1' else '-1 \\cdot '}({cx(x, y)}) + ({cx(p, q)})",
        "plainText": f"({rs.replace('I', 'i')})*({cx_plain(x, y)}) + ({cx_plain(p, q)})",
        "answerSpec": {"type": "tuple", "values": [str(X), str(Y)], "labels": ["x'", "y'"], "acceptComplex": True},
        "answerDisplay": f"({num(X)}, {num(Y)})",
        "answerPlain": f"({X}, {Y})",
        "inputHint": "e.g. (4, -2) or 4 - 2i",
        "checkpointHint": f"After the rotation only, the point is $({num(rx)}, {num(ry)})$.",
        "commonTrapTag": trap_tag,
        "steps": [
            S(f"z = {cx(x, y)}", f"Represent the point $({x}, {y})$ as a complex number.", eq=[zs, f"{x} + ({y})*I"]),
            S(mult_row, mult_expl, eq=[f"({rs})*{zs}", cx_sym(rx, ry)]),
            S(f"z' = ({cx(rx, ry)}) + ({cx(p, q)}) = {cx(X, Y)}", f"Add the translation $w$ component-wise. The new point is $({num(X)}, {num(Y)})$.",
              eq=[f"({rs})*{zs} + {cx_sym(p, q)}", cx_sym(X, Y)]),
        ],
        "verify": {"tuple": [f"re(({rs})*{zs} + {cx_sym(p, q)})", f"im(({rs})*{zs} + {cx_sym(p, q)})"], "trapValue": trap_tuple},
    }


def t_parallel(rng, form=None):
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
        S(f"Z_1 Z_2 = ({cx(a, b)})({cx(c, d)}) = {cx(Pr, Pi)}", "Multiply the impedances (FOIL, then $i^2 = -1$).", eq=[f"{cx_sym(a, b)}*{cx_sym(c, d)}", cx_sym(Pr, Pi)]),
        S(f"Z_1 + Z_2 = {cx(Sr, Si)}", "Add the real parts and the imaginary parts.", eq=[f"{cx_sym(a, b)}+{cx_sym(c, d)}", cx_sym(Sr, Si)]),
    ]
    src = f"({cx_sym(a, b)}*{cx_sym(c, d)})/({cx_sym(a, b)}+{cx_sym(c, d)})"
    if Si == 0:
        steps.append(S(f"Z_{{eq}} = \\frac{{{cx(Pr, Pi)}}}{{{Sr}}} = {cx(A, B)}", "The sum is real, so divide each part directly.", eq=[src, cx_sym(A, B)]))
    else:
        div_steps, rA, rB = _division_steps(Pr, Pi, Sr, Si, lead=f"Z_{{eq}} = \\frac{{{cx(Pr, Pi)}}}{{{cx(Sr, Si)}}}")
        for st in div_steps:
            st["eq"] = [src, st.pop("val")]
        steps += div_steps
    return {
        "form": "direct",
        "category": "Cross-Subject Application",
        "context": "Physics Application: Parallel Impedance",
        "references": ["MTH-T02-C01-U01", "PHY-T01-C19"],
        "prompt": f"Two branches with impedances $Z_1 = {cx(a, b)}$ ohms and $Z_2 = {cx(c, d)}$ ohms are connected in parallel. "
                  f"Find the equivalent impedance $Z_{{eq}} = \\dfrac{{Z_1 Z_2}}{{Z_1 + Z_2}}$ in standard form $a + bi$.",
        "display": f"Z_{{eq}} = \\frac{{({cx(a, b)})({cx(c, d)})}}{{({cx(a, b)}) + ({cx(c, d)})}}",
        "plainText": f"(({cx_plain(a, b)})*({cx_plain(c, d)}))/(({cx_plain(a, b)}) + ({cx_plain(c, d)}))",
        **complex_answer(A, B),
        "checkpointHint": f"Compute the product first: $Z_1 Z_2 = {cx(Pr, Pi)}$.",
        "commonTrapTag": "conjugate-denominator",
        "steps": steps,
        "verify": {"source": src, "trapValue": cx_plain(Sr, Si)},
    }


TEMPLATES = [
    {
        "key": "radical-standard-form",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {"direct": {"level": 1, "skill": "MTH-COMPLEX-RADICAL-SIMPLIFY"}},
        "build": t_radical,
    },
    {
        "key": "add-subtract",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "addition": {"level": 1, "skill": "MTH-COMPLEX-ADDITION"},
            "subtraction": {"level": 1, "skill": "MTH-COMPLEX-SUBTRACTION"},
        },
        "build": t_add_sub,
    },
    {
        "key": "power-of-i",
        "level": 1,
        "verificationLevel": "machine-verified",
        "forms": {
            "rem-0": {"level": 1, "skill": "MTH-COMPLEX-POWER-I-MOD4"},
            "rem-1": {"level": 1, "skill": "MTH-COMPLEX-POWER-I-MOD4"},
            "rem-2": {"level": 1, "skill": "MTH-COMPLEX-POWER-I-MOD4"},
            "rem-3": {"level": 1, "skill": "MTH-COMPLEX-POWER-I-MOD4"},
        },
        "build": t_power_i,
    },
    {
        "key": "multiply",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-COMPLEX-MULTIPLICATION", "trapTag": "sign-slip"},
            "missing-coefficient": {"level": 2, "skill": "MTH-COMPLEX-MULTIPLICATION", "trapTag": "sign-slip"},
            "pure-imaginary": {"level": 2, "skill": "MTH-COMPLEX-MULTIPLICATION", "trapTag": "sign-slip"},
        },
        "form_aliases": {"missing-factor": "missing-coefficient"},
        "build": t_multiply,
    },
    {
        "key": "divide-conjugate",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {
            "direct": {"level": 2, "skill": "MTH-COMPLEX-DIVISION-CONJUGATE", "trapTag": "conjugate-denominator"},
            "reciprocal": {"level": 2, "skill": "MTH-COMPLEX-DIVISION-CONJUGATE", "trapTag": "conjugate-denominator"},
            "pure-imaginary-denom": {"level": 2, "skill": "MTH-COMPLEX-DIVISION-CONJUGATE", "trapTag": "conjugate-denominator"},
        },
        "build": t_divide,
    },
    {
        "key": "square-binomial",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {"direct": {"level": 2, "skill": "MTH-COMPLEX-SQUARE-BINOMIAL"}},
        "build": t_square,
    },
    {
        "key": "evaluate-polynomial",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {"direct": {"level": 2, "skill": "MTH-COMPLEX-EVALUATE-POLYNOMIAL"}},
        "build": t_eval_poly,
    },
    {
        "key": "principal-root-trap",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {"direct": {"level": 3, "skill": "MTH-COMPLEX-PRINCIPAL-ROOT-TRAP"}},
        "build": t_principal_root,
    },
    {
        "key": "power-sum",
        "level": 2,
        "verificationLevel": "machine-verified",
        "forms": {"direct": {"level": 2, "skill": "MTH-COMPLEX-POWER-SUM"}},
        "build": t_power_sum,
    },
    {
        "key": "find-the-flaw",
        "level": 3,
        "verificationLevel": "machine-verified",
        "forms": {
            "flaw-line-1": {"level": 3, "skill": "MTH-COMPLEX-DIAGNOSTIC-FLAW"},
            "flaw-line-2": {"level": 3, "skill": "MTH-COMPLEX-DIAGNOSTIC-FLAW"},
            "flaw-line-3": {"level": 3, "skill": "MTH-COMPLEX-DIAGNOSTIC-FLAW"},
        },
        "build": t_find_flaw,
    },
    {
        "key": "ac-current",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {"direct": {"level": 4, "skill": "MTH-COMPLEX-AC-OHMS-LAW"}},
        "build": t_ac_current,
    },
    {
        "key": "rotation-2d",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {
            "rot-i": {"level": 4, "skill": "MTH-COMPLEX-GEOMETRIC-ROTATION"},
            "rot--1": {"level": 4, "skill": "MTH-COMPLEX-GEOMETRIC-ROTATION"},
            "rot--i": {"level": 4, "skill": "MTH-COMPLEX-GEOMETRIC-ROTATION"},
        },
        "build": t_rotation,
    },
    {
        "key": "parallel-impedance",
        "level": 4,
        "verificationLevel": "machine-verified",
        "forms": {"direct": {"level": 4, "skill": "MTH-COMPLEX-PARALLEL-IMPEDANCE"}},
        "build": t_parallel,
    },
]
