# -*- coding: utf-8 -*-
"""
Flexible, type-driven answer checker for Math drills (SymPy).

Usage (CLI, used by the Studio API):
    echo '{"answerSpec": {...}, "input": "3 - 4i"}' | .venv/bin/python -m math_engine.answer_check

Supported answerSpec types (extensible - add a new checker function + register it in CHECKERS):
    number          {"type": "number", "value": "3/4", "forms": ["reduced_fraction", "exact"]}
    complex         {"type": "complex", "value": "-1 + 2*I", "forms": ["a+bi"]}
    expression      {"type": "expression", "value": "x**2 - 1", "variables": ["x"], "forms": ["factored"]}
    solution_set    {"type": "solution_set", "values": ["-2 + 3*I", "-2 - 3*I"], "variable": "x"}
    tuple           {"type": "tuple", "values": ["5", "3"], "labels": ["x", "y"], "acceptComplex": true}
    choice          {"type": "choice", "correct": "B"}
    text            {"type": "text", "accepted": ["server-only"]}

Result:
    {
      "verdict": "correct" | "equivalent_not_in_form" | "partial" | "incorrect" | "parse_error",
      "message": "...",                 # plain English, may contain $...$ inline math
      "components": [{"label": "...", "ok": true}],
      "diagnostics": [{"code": "...", "message": "..."}]
    }
Diagnostic codes are generic (whole_sign_flip, imag_sign_flip, real_sign_flip, swapped_parts, reciprocal,
off_by_factor, constant_offset, rounding, missing_solution, extra_solution, unseparated, complex_denominator,
unexpanded_power, uncombined_terms, unreduced_fraction, radical_denominator, decimal_not_exact, not_expanded,
not_factored). Each drill maps codes to its own mistake tags via mistakeTags[].autoFrom.
"""
import json
import random
import re
import sys

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_application,
    implicit_multiplication,
    parse_expr,
    standard_transformations,
)

TRANSFORMS = standard_transformations + (implicit_multiplication, implicit_application, convert_xor)

FORM_MESSAGES = {
    "unseparated": "The value is correct, but it is not separated into standard form $a + bi$ (distribute or split the fraction).",
    "complex_denominator": "The value is correct, but $i$ still appears in a denominator. Multiply by the conjugate.",
    "unexpanded_power": "The value is correct, but a power of $i$ (such as $i^2$) or a product is left unsimplified.",
    "uncombined_terms": "The value is correct, but like terms are not combined.",
    "unreduced_fraction": "The value is correct, but a fraction is not reduced to lowest terms.",
    "radical_denominator": "The value is correct, but the denominator still contains a radical (rationalize it).",
    "decimal_not_exact": "The value matches numerically, but an exact answer (fraction / radical) is required, not a decimal.",
    "not_expanded": "The expression is equivalent, but it is not fully expanded.",
    "not_factored": "The expression is equivalent, but it is not fully factored.",
    "unsimplified_radical": "The value is correct, but a radical is not simplified (extract perfect-square factors, e.g. $\\sqrt{48} = 4\\sqrt{3}$).",
}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _normalize(raw: str) -> str:
    s = (raw or "").strip()
    repl = {
        "\u2212": "-", "\u2013": "-", "\u00d7": "*", "\u00b7": "*", "\u22c5": "*", "\u00f7": "/",
        "\u03c0": "pi", "\u221e": "oo", "**": "^",
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    s = s.replace("^", "**")
    s = re.sub(r"\u221a\s*\(", "sqrt(", s)              # √(…)
    s = re.sub(r"\u221a\s*([0-9.]+|[a-zA-Z])", r"sqrt(\1)", s)  # √12, √x
    s = re.sub(r"sqrt\s*([0-9]+)", r"sqrt(\1)", s)       # sqrt12
    s = s.replace("{", "(").replace("}", ")").replace("[", "(").replace("]", ")")
    return s


def _local_dict(variables, allow_i=True):
    d = {"e": sp.E, "pi": sp.pi, "sqrt": sp.sqrt, "oo": sp.oo}
    for v in variables or []:
        if v not in ("pi", "e", "oo"):
            d[v] = sp.Symbol(v)
    if allow_i and "i" not in (variables or []):
        d["i"] = sp.I
        d["I"] = sp.I
    return d


def parse_math(raw, variables=None, evaluate=True, allow_i=True):
    s = _normalize(raw)
    if not s:
        raise ValueError("Empty input")
    return parse_expr(s, local_dict=_local_dict(variables, allow_i), transformations=TRANSFORMS, evaluate=evaluate)


def to_expr(value, variables=None):
    if isinstance(value, (int, float)):
        return sp.nsimplify(value)
    return sp.sympify(value, locals=_local_dict(variables))


# ---------------------------------------------------------------------------
# Equality helpers
# ---------------------------------------------------------------------------
def is_equal(a, b, variables=None):
    try:
        diff = sp.simplify(sp.expand_complex(a - b)) if not variables else sp.simplify(a - b)
        if diff == 0:
            return True
    except Exception:
        pass
    syms = [sp.Symbol(v) for v in (variables or [])]
    try:
        for _ in range(6):
            subs = {s: sp.Rational(random.randint(-90, 90), random.randint(7, 19)) for s in syms}
            va = complex(sp.N(a.subs(subs)))
            vb = complex(sp.N(b.subs(subs)))
            if abs(va - vb) > 1e-9 * max(1.0, abs(vb)):
                return False
        return True
    except Exception:
        return False


def numeric_close(a, b, rel=1e-2):
    try:
        va, vb = complex(sp.N(a)), complex(sp.N(b))
        return abs(va - vb) <= rel * max(1.0, abs(vb)) and abs(va - vb) > 1e-12
    except Exception:
        return False


def generic_value_diagnostics(u, e, variables=None):
    """Diagnostics that apply to any scalar / expression comparison."""
    diags = []
    try:
        if e != 0 and is_equal(u, -e, variables):
            diags.append({"code": "whole_sign_flip", "message": "Your answer is the exact negative of the correct value. Check a sign (for example $i^2 = -1$ or a subtraction)."})
            return diags
        if e != 0 and u != 0 and is_equal(u, 1 / e, variables):
            diags.append({"code": "reciprocal", "message": "Your answer is the reciprocal of the correct value. Check which quantity is in the numerator."})
            return diags
        if e != 0 and u != 0:
            ratio = sp.simplify(u / e)
            if ratio.is_number and ratio.is_rational and ratio not in (1, -1):
                diags.append({"code": "off_by_factor", "message": f"Your answer differs from the correct value by a constant factor of ${sp.latex(ratio)}$."})
                return diags
        if variables:
            offset = sp.simplify(u - e)
            if offset.is_number and offset != 0:
                diags.append({"code": "constant_offset", "message": f"Your expression differs from the correct one by the constant ${sp.latex(offset)}$."})
                return diags
        if not variables and numeric_close(u, e):
            diags.append({"code": "rounding", "message": "Your answer is numerically close but not exact. Check rounding or keep exact fractions / radicals."})
    except Exception:
        pass
    return diags


# ---------------------------------------------------------------------------
# Form checks (performed on the UNEVALUATED parse tree)
# ---------------------------------------------------------------------------
def _is_rational_number(t):
    try:
        return bool(t.is_number) and bool(sp.nsimplify(t).is_rational) and not t.has(sp.I) and not any(
            isinstance(p, sp.Pow) and not p.exp.is_integer for p in sp.preorder_traversal(t)
        )
    except Exception:
        return False


def form_issues(tree, forms):
    issues = []
    forms = forms or []

    def walk(e):
        if "a+bi" in forms:
            if isinstance(e, sp.Pow) and e.base.has(sp.I):
                ex = e.exp
                if ex.is_number and ex.is_negative:
                    issues.append("complex_denominator")
                else:
                    issues.append("unexpanded_power")
            if isinstance(e, sp.Mul):
                if any(isinstance(a, sp.Add) and a.has(sp.I) for a in e.args):
                    issues.append("unseparated")
                if sum(1 for a in e.args if a == sp.I) > 1:
                    issues.append("unexpanded_power")
        if "reduced_fraction" in forms and isinstance(e, sp.Mul):
            ints = [a for a in e.args if isinstance(a, sp.Integer)]
            dens = [a.base for a in e.args if isinstance(a, sp.Pow) and isinstance(a.base, sp.Integer) and a.exp == -1]
            for p in ints:
                for q in dens:
                    if sp.gcd(int(p), int(q)) > 1:
                        issues.append("unreduced_fraction")
        if "rationalized" in forms and isinstance(e, sp.Pow) and e.exp.is_number and e.exp.is_negative:
            if any(isinstance(p, sp.Pow) and p.exp == sp.Rational(1, 2) for p in sp.preorder_traversal(e.base)) or (
                isinstance(e.base, sp.Pow) and e.base.exp == sp.Rational(1, 2)
            ):
                issues.append("radical_denominator")
        if "exact" in forms and isinstance(e, sp.Float):
            issues.append("decimal_not_exact")
        if "simplified_radical" in forms and isinstance(e, sp.Pow) and e.exp == sp.Rational(1, 2) and isinstance(e.base, sp.Integer):
            n = abs(int(e.base))
            if n > 1 and any(n % (k * k) == 0 for k in range(2, int(n ** 0.5) + 1)):
                issues.append("unsimplified_radical")
        for a in e.args:
            walk(a)

    walk(tree)

    if "a+bi" in forms and isinstance(tree, sp.Add):
        im_terms = [t for t in tree.args if t.has(sp.I)]
        re_terms = [t for t in tree.args if not t.has(sp.I)]
        if sum(1 for t in re_terms if _is_rational_number(t)) > 1:
            issues.append("uncombined_terms")
        if sum(1 for t in im_terms if _is_rational_number(t / sp.I)) > 1:
            issues.append("uncombined_terms")

    return list(dict.fromkeys(issues))


def _evaluated_form_issues(u, forms, variables):
    issues = []
    if "expanded" in forms and sp.expand(u) != u:
        issues.append("not_expanded")
    if "factored" in forms and sp.factor(u) != u:
        issues.append("not_factored")
    return issues


def _form_result(raw, u, spec, variables=None):
    forms = spec.get("forms", [])
    try:
        tree = parse_math(raw, variables, evaluate=False)
        issues = form_issues(tree, forms)
    except Exception:
        issues = []
    issues += _evaluated_form_issues(u, forms, variables)
    if issues:
        return {
            "verdict": "equivalent_not_in_form",
            "message": FORM_MESSAGES.get(issues[0], "Equivalent, but not in the required final form."),
            "diagnostics": [{"code": c, "message": FORM_MESSAGES.get(c, c)} for c in issues],
        }
    return None


# ---------------------------------------------------------------------------
# Type checkers
# ---------------------------------------------------------------------------
def check_number(spec, raw):
    e = to_expr(spec["value"])
    u = parse_math(raw)
    comps = [{"label": "Value", "ok": False}]
    if is_equal(u, e):
        comps[0]["ok"] = True
        fr = _form_result(raw, u, spec)
        if fr:
            return {**fr, "components": comps}
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}
    diags = generic_value_diagnostics(u, e)
    return {"verdict": "incorrect", "message": "Not equal to the verified answer.", "components": comps, "diagnostics": diags}


def check_complex(spec, raw):
    e = sp.expand_complex(to_expr(spec["value"]))
    u = sp.expand_complex(parse_math(raw))
    ere, eim = sp.re(e), sp.im(e)
    ure, uim = sp.re(u), sp.im(u)
    re_ok, im_ok = is_equal(ure, ere), is_equal(uim, eim)
    comps = [{"label": "Real part", "ok": re_ok}, {"label": "Imaginary part", "ok": im_ok}]
    if re_ok and im_ok:
        fr = _form_result(raw, u, spec)
        if fr:
            return {**fr, "components": comps}
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}

    diags = []
    if re_ok and eim != 0 and is_equal(uim, -eim):
        diags.append({"code": "imag_sign_flip", "message": "Real part is correct, but the imaginary part has the opposite sign. Check $i^2 = -1$ or the conjugate sign."})
    elif im_ok and ere != 0 and is_equal(ure, -ere):
        diags.append({"code": "real_sign_flip", "message": "Imaginary part is correct, but the real part has the opposite sign. Check $i^2 = -1$ when combining real terms."})
    elif is_equal(ure, eim) and is_equal(uim, ere) and ere != eim:
        diags.append({"code": "swapped_parts", "message": "Your real and imaginary parts are swapped."})
    else:
        diags = generic_value_diagnostics(u, e)

    verdict = "partial" if (re_ok or im_ok) else "incorrect"
    msg = "One component matches; inspect the other." if verdict == "partial" else "Not equal to the verified answer."
    return {"verdict": verdict, "message": msg, "components": comps, "diagnostics": diags}


def check_expression(spec, raw):
    variables = spec.get("variables", ["x"])
    e = to_expr(spec["value"], variables)
    u = parse_math(raw, variables, allow_i=spec.get("allowI", False))
    comps = [{"label": "Equivalence", "ok": False}]
    if is_equal(u, e, variables):
        comps[0]["ok"] = True
        fr = _form_result(raw, u, spec, variables)
        if fr:
            return {**fr, "components": comps}
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}
    return {"verdict": "incorrect", "message": "Not equivalent to the verified answer.", "components": comps, "diagnostics": generic_value_diagnostics(u, e, variables)}


def _split_items(raw, variable):
    s = raw.strip()
    s = re.sub(r"^[\(\{\[]\s*|\s*[\)\}\]]$", "", s) if re.match(r"^[\{\[]", s) else s
    parts = re.split(r",|;|\bor\b|\band\b", s)
    items = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if variable:
            p = re.sub(rf"^\s*{re.escape(variable)}\s*(_?\d+)?\s*=\s*", "", p)
        if "\u00b1" in p or "+-" in p:
            a, b = re.split(r"\u00b1|\+-", p, maxsplit=1)
            a = a.strip() or "0"
            items += [f"({a})+({b})", f"({a})-({b})"]
        else:
            items.append(p)
    return items


def check_solution_set(spec, raw):
    variable = spec.get("variable", "x")
    expected = [sp.expand_complex(to_expr(v)) for v in spec["values"]]
    try:
        users = [sp.expand_complex(parse_math(it)) for it in _split_items(raw, variable)]
    except Exception as ex:
        raise ValueError(f"Could not parse the solution list: {ex}")
    matched_u = set()
    comps, diags = [], []
    for i, ev in enumerate(expected):
        hit = next((j for j, uv in enumerate(users) if j not in matched_u and is_equal(uv, ev)), None)
        ok = hit is not None
        if ok:
            matched_u.add(hit)
        comps.append({"label": f"Solution {i + 1}: ${sp.latex(ev)}$", "ok": ok})
    extras = [users[j] for j in range(len(users)) if j not in matched_u]
    for x in extras:
        if any(is_equal(x, -ev) for ev in expected):
            diags.append({"code": "whole_sign_flip", "message": f"${sp.latex(x)}$ is the negative of a true solution. Check the sign in front of $b$ in the quadratic formula."})
        elif any(is_equal(sp.conjugate(x), ev) or is_equal(sp.re(x), sp.re(ev)) for ev in expected):
            diags.append({"code": "imag_sign_flip", "message": f"${sp.latex(x)}$ has the right real part but the wrong imaginary part."})
        else:
            diags.append({"code": "extra_solution", "message": f"${sp.latex(x)}$ does not satisfy the equation (extraneous value)."})
    missing = sum(1 for c in comps if not c["ok"])
    if missing:
        diags.append({"code": "missing_solution", "message": f"{missing} solution(s) missing. Remember both signs of $\\pm$."})
    if missing == 0 and not extras:
        forms = spec.get("forms", [])
        issues = []
        for it in _split_items(raw, variable):
            try:
                issues += form_issues(parse_math(it, evaluate=False), forms)
            except Exception:
                pass
        if issues:
            return {"verdict": "equivalent_not_in_form", "message": FORM_MESSAGES.get(issues[0], "Not in required form."), "components": comps,
                    "diagnostics": [{"code": c, "message": FORM_MESSAGES.get(c, c)} for c in dict.fromkeys(issues)]}
        return {"verdict": "correct", "message": "Correct. All solutions found.", "components": comps, "diagnostics": []}
    verdict = "partial" if missing < len(expected) else "incorrect"
    return {"verdict": verdict, "message": "Some solutions match." if verdict == "partial" else "No solution matches.", "components": comps, "diagnostics": diags}


def check_tuple(spec, raw):
    expected = [to_expr(v) for v in spec["values"]]
    labels = spec.get("labels") or [f"Component {i + 1}" for i in range(len(expected))]
    s = raw.strip()
    if spec.get("acceptComplex") and "," not in s and len(expected) == 2:
        z = sp.expand_complex(parse_math(s))
        users = [sp.re(z), sp.im(z)]
    else:
        s = re.sub(r"^\s*[\(\[\{<]|[\)\]\}>]\s*$", "", s)
        users = [parse_math(p) for p in s.split(",") if p.strip()]
    comps = [{"label": labels[i], "ok": i < len(users) and is_equal(users[i], expected[i])} for i in range(len(expected))]
    if len(users) == len(expected) and all(c["ok"] for c in comps):
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}
    diags = []
    if len(users) != len(expected):
        diags.append({"code": "wrong_component_count", "message": f"Expected {len(expected)} components, received {len(users)}."})
    else:
        for i, (uv, ev) in enumerate(zip(users, expected)):
            if not comps[i]["ok"] and ev != 0 and is_equal(uv, -ev):
                diags.append({"code": "whole_sign_flip", "message": f"{labels[i]} has the opposite sign."})
        if len(expected) == 2 and is_equal(users[0], expected[1]) and is_equal(users[1], expected[0]):
            diags.append({"code": "swapped_parts", "message": "The components are swapped."})
    verdict = "partial" if any(c["ok"] for c in comps) else "incorrect"
    return {"verdict": verdict, "message": "Some components match." if verdict == "partial" else "No component matches.", "components": comps, "diagnostics": diags}


def check_choice(spec, raw):
    ok = raw.strip().upper() == str(spec["correct"]).strip().upper()
    return {"verdict": "correct" if ok else "incorrect", "message": "Correct." if ok else "Incorrect choice.", "components": [{"label": "Choice", "ok": ok}], "diagnostics": []}


def check_text(spec, raw):
    norm = lambda t: re.sub(r"\s+", " ", t.strip().lower())
    ok = norm(raw) in [norm(a) for a in spec["accepted"]]
    return {"verdict": "correct" if ok else "incorrect", "message": "Correct." if ok else "Does not match the accepted answers.", "components": [{"label": "Answer", "ok": ok}], "diagnostics": []}


CHECKERS = {
    "number": check_number,
    "complex": check_complex,
    "expression": check_expression,
    "solution_set": check_solution_set,
    "tuple": check_tuple,
    "choice": check_choice,
    "text": check_text,
}


def check_answer(spec, raw):
    if not (raw or "").strip():
        return {"verdict": "parse_error", "message": "Type your final answer first.", "components": [], "diagnostics": []}
    fn = CHECKERS.get(spec.get("type"))
    if not fn:
        return {"verdict": "parse_error", "message": f"Unsupported answer type: {spec.get('type')}", "components": [], "diagnostics": []}
    try:
        return fn(spec, raw)
    except Exception as ex:
        return {"verdict": "parse_error", "message": f"Could not read that input. Use forms like 3 - 4i, 3/4, sqrt(2)/2, x^2 + 1, or x = 2, x = -3. ({type(ex).__name__})", "components": [], "diagnostics": []}


if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(check_answer(payload.get("answerSpec", {}), payload.get("input", ""))))
