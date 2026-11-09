# -*- coding: utf-8 -*-
"""LaTeX / plain-text / SymPy formatting helpers shared by all Math templates."""
import sympy as sp

LEVEL_LABELS = {
    1: "Level 1 - Foundation",
    2: "Level 2 - Standard Exam",
    3: "Level 3 - Trap & Diagnostic",
    4: "Level 4 - Applied Synthesis",
    5: "Level 5 - Non-Routine Synthesis",
}


def R(x):
    return sp.Rational(x)


def num(r):
    """LaTeX for a rational number: 3, -3, \\frac{3}{5}, -\\frac{3}{5}."""
    r = R(r)
    if r.q == 1:
        return str(r.p)
    sign = "-" if r < 0 else ""
    return f"{sign}\\frac{{{abs(r.p)}}}{{{r.q}}}"


def num_plain(r):
    r = R(r)
    return str(r.p) if r.q == 1 else f"({r.p}/{r.q})"


def sym(r):
    return f"({R(r)})"


def _coef_suffix(c, suffix):
    c = abs(R(c))
    if suffix and c == 1 and not suffix.startswith("("):
        return suffix
    return f"{num(c)}{suffix}"


def terms(items, keep_zero=False):
    """items: list of (coef, suffix) -> '3 - 4i + 2i^2' with correct signs."""
    out = ""
    for coef, suffix in items:
        coef = R(coef)
        if coef == 0 and not keep_zero:
            continue
        body = _coef_suffix(coef, suffix)
        if not out:
            out = ("-" if coef < 0 else "") + body
        else:
            out += (" - " if coef < 0 else " + ") + body
    return out or "0"


def cx(a, b):
    """LaTeX for a + bi in standard form."""
    return terms([(a, ""), (b, "i")])


def cx_paren(a, b):
    return f"({cx(a, b)})" if (R(a) != 0 and R(b) != 0) or R(a) < 0 or R(b) < 0 else cx(a, b)


def cx_plain(a, b):
    a, b = R(a), R(b)
    if b == 0:
        return num_plain(a).strip("()") if a.q == 1 else num_plain(a)
    im = ("" if abs(b) == 1 else num_plain(abs(b))) + "i"
    if a == 0:
        return ("-" if b < 0 else "") + im
    return f"{num_plain(a)} {'-' if b < 0 else '+'} {im}"


def cx_sym(a, b):
    return f"({sym(a)} + {sym(b)}*I)"


def sq(n):
    """LaTeX for n^2 with parentheses on negatives."""
    n = R(n)
    return f"({num(n)})^2" if n < 0 else f"{num(n)}^2"


def nonzero(rng, lo, hi, exclude=()):
    while True:
        v = rng.randint(lo, hi)
        if v != 0 and v not in exclude:
            return v
