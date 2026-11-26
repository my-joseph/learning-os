# -*- coding: utf-8 -*-
"""Timeout-bounded SymPy equivalence, generic value diagnostics, and form checking."""

import random
import signal
import threading

import sympy as sp

from math_engine._parse import parse_math


class EqualTimeoutError(BaseException):
    """Raised when expression equality evaluation exceeds time budget."""

    pass


def _run_with_timeout(func, args=(), kwargs=None, timeout_sec=1.5):
    kwargs = kwargs or {}
    timer_active = False
    if hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread():
        rem, _ = signal.getitimer(signal.ITIMER_REAL)
        timer_active = rem > 0

    if hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread() and not timer_active:

        def _handler(signum, frame):
            raise EqualTimeoutError("is_equal computation timed out")

        old_handler = signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, timeout_sec)
        try:
            return func(*args, **kwargs)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        res = [None]
        err = [None]
        done = threading.Event()

        def _worker():
            try:
                res[0] = func(*args, **kwargs)
            except BaseException as e:
                err[0] = e
            finally:
                done.set()

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        finished = done.wait(timeout=timeout_sec)
        if not finished:
            raise EqualTimeoutError("is_equal computation timed out")
        if err[0] is not None:
            raise err[0]
        return res[0]


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


def is_equal(a, b, variables=None, tolerance=None, timeout=1.5, raise_on_timeout=False):
    if a == b:
        return True

    def _eval():
        if isinstance(a, sp.Matrix) and isinstance(b, sp.Matrix):
            if a.shape != b.shape:
                return False
            return all(
                is_equal(
                    a[i],
                    b[i],
                    variables=variables,
                    tolerance=tolerance,
                    timeout=timeout,
                    raise_on_timeout=raise_on_timeout,
                )
                for i in range(len(a))
            )
        if isinstance(a, sp.Matrix) != isinstance(b, sp.Matrix):
            return False

        # If tolerance is specified, check numerical difference
        if tolerance is not None:
            try:
                if not variables:
                    diff = abs(sp.N(a - b, 30))
                    val_b = abs(sp.N(b, 30))
                    if isinstance(tolerance, (int, float)):
                        # A plain number is an absolute tolerance; use {"rel": ...} for a relative one.
                        if diff <= tolerance:
                            return True
                    elif isinstance(tolerance, dict):
                        abs_tol = tolerance.get("abs", 0.0)
                        rel_tol = tolerance.get("rel", 0.0)
                        if (abs_tol and diff <= abs_tol) or (rel_tol and diff <= rel_tol * max(1.0, float(val_b))):
                            return True
                else:
                    syms = [sp.Symbol(v) for v in variables]
                    tol_val = tolerance if isinstance(tolerance, (int, float)) else tolerance.get("abs", 1e-3)
                    all_close = True
                    for _ in range(5):
                        subs = {s: sp.Rational(random.randint(1, 10), 1) for s in syms}
                        diff_sub = abs(sp.N((a - b).subs(subs), 30))
                        val_b = abs(sp.N(b.subs(subs), 30))
                        if not (diff_sub <= tol_val or diff_sub <= tol_val * max(1.0, float(val_b))):
                            all_close = False
                            break
                    if all_close:
                        return True
            except Exception:
                pass

        # Quick pre-filter for expressions with variables
        if variables:
            syms = [sp.Symbol(v) for v in variables]
            try:
                for _ in range(2):
                    subs = {s: sp.Rational(random.randint(2, 6), 1) for s in syms}
                    a_sub = sp.N(a.subs(subs), 30)
                    b_sub = sp.N(b.subs(subs), 30)
                    if a_sub.is_real is not True or b_sub.is_real is not True:
                        continue
                    if a_sub.is_finite is not True or b_sub.is_finite is not True:
                        continue
                    if abs(a_sub - b_sub) > 1e-9:
                        return False
            except Exception:
                pass

        try:
            diff = sp.simplify(sp.expand_complex(a - b)) if not variables else sp.simplify(a - b)
            if diff == 0:
                return True
            if not variables:
                val = abs(sp.N(diff, 30))
                return bool(val < 1e-12)
            if diff.is_number and diff != 0:
                return False
        except Exception:
            pass

        syms = [sp.Symbol(v) for v in (variables or [])]
        if not syms:
            return False

        valid_samples = 0
        try:
            # Sample only where both expressions define real, finite values. This
            # compares equivalent forms on their shared real domain instead of
            # treating an undefined logarithm or radical sample as inequality.
            for _ in range(64):
                subs = {s: sp.Rational(random.randint(-90, 90), random.randint(7, 19)) for s in syms}
                a_sub = sp.N(a.subs(subs), 30)
                b_sub = sp.N(b.subs(subs), 30)
                if a_sub.is_real is not True or b_sub.is_real is not True:
                    continue
                if a_sub.is_finite is not True or b_sub.is_finite is not True:
                    continue
                valid_samples += 1
                if abs(a_sub - b_sub) > 1e-9:
                    return False
            return valid_samples >= 6
        except Exception:
            return False

    try:
        return _run_with_timeout(_eval, timeout_sec=timeout)
    except EqualTimeoutError:
        if raise_on_timeout:
            raise
        return False


def _intervals_equal(u_set: sp.Set, e_set: sp.Set) -> bool:
    if u_set == e_set:
        return True
    try:
        return u_set.symmetric_difference(e_set) == sp.EmptySet
    except Exception:
        return False


def numeric_close(a, b, rel=1e-2):
    try:
        va, vb = complex(sp.N(a)), complex(sp.N(b))
        return abs(va - vb) <= rel * max(1.0, abs(vb)) and abs(va - vb) > 1e-12
    except Exception:
        return False


def _has_large_exponent(expr, threshold=20):
    try:
        for p in sp.preorder_traversal(expr):
            if isinstance(p, sp.Pow) and isinstance(p.exp, sp.Number) and abs(p.exp) > threshold:
                return True
    except Exception:
        pass
    return False


def _is_allowed_diagnostic_factor(ratio):
    """
    Check if ratio is one of the allowed diagnostic factors:
    -1, 2, 1/2, 10^k, 1/10^k, pi, 1/pi, integers 3..12, or 1/3..1/12.
    """
    try:
        if ratio == 1:
            return False
        if ratio == -1:
            return True
        # Check pi and 1/pi
        if sp.simplify(ratio - sp.pi) == 0 or sp.simplify(ratio - 1 / sp.pi) == 0:
            return True
        if not ratio.is_number:
            return False
        # Integer 2..12 or 10^k
        if ratio.is_integer:
            val = int(ratio)
            if 2 <= val <= 12:
                return True
            if val > 12:
                s = str(val)
                return s.startswith("1") and all(c == "0" for c in s[1:])
        # Rational 1/2..1/12 or 1/10^k
        if ratio.is_rational and ratio > 0:
            p, q = ratio.p, ratio.q
            if p == 1:
                if 2 <= q <= 12:
                    return True
                s = str(q)
                return s.startswith("1") and all(c == "0" for c in s[1:])
    except Exception:
        pass
    return False


def generic_value_diagnostics(u, e, variables=None):
    """Diagnostics that apply to any scalar / expression comparison."""
    if _has_large_exponent(u, threshold=20) or _has_large_exponent(e, threshold=20):
        return []
    diags = []
    try:
        if e != 0 and is_equal(u, -e, variables):
            complex_context = u.has(sp.I) or e.has(sp.I)
            sign_guidance = (
                "Check a sign (for example $i^2 = -1$ or a subtraction)."
                if complex_context
                else "Check the sign of your answer."
            )
            diags.append(
                {
                    "code": "whole_sign_flip",
                    "message": f"Your answer is the exact negative of the correct value. {sign_guidance}",
                }
            )
            return diags
        if e != 0 and u != 0 and is_equal(u, 1 / e, variables):
            diags.append(
                {
                    "code": "reciprocal",
                    "message": "Your answer is the reciprocal of the correct value. Check which quantity is in the numerator.",
                }
            )
            return diags
        if not variables and numeric_close(u, e):
            diags.append(
                {
                    "code": "rounding",
                    "message": "Your answer is numerically close but not exact. Check rounding or keep exact fractions / radicals.",
                }
            )
            return diags
        if e != 0 and u != 0:
            # Fast check: only simplify if ratio could be constant
            can_be_const = True
            if variables:
                syms = [sp.Symbol(v) for v in variables]
                try:
                    p1 = {s: sp.Rational(2, 1) for s in syms}
                    p2 = {s: sp.Rational(3, 1) for s in syms}
                    r1 = complex(sp.N((u / e).subs(p1)))
                    r2 = complex(sp.N((u / e).subs(p2)))
                    if abs(r1 - r2) > 1e-6 * max(1.0, abs(r1)):
                        can_be_const = False
                except Exception:
                    pass
            if can_be_const:
                ratio = sp.simplify(u / e)
                if _is_allowed_diagnostic_factor(ratio):
                    diags.append(
                        {
                            "code": "off_by_factor",
                            "message": f"Your answer differs from the correct value by a constant factor of ${sp.latex(ratio)}$.",
                        }
                    )
                    return diags
        if variables:
            # Fast check: only simplify if offset could be constant
            can_be_const_offset = True
            syms = [sp.Symbol(v) for v in variables]
            try:
                p1 = {s: sp.Rational(2, 1) for s in syms}
                p2 = {s: sp.Rational(3, 1) for s in syms}
                o1 = complex(sp.N((u - e).subs(p1)))
                o2 = complex(sp.N((u - e).subs(p2)))
                if abs(o1 - o2) > 1e-6 * max(1.0, abs(o1)):
                    can_be_const_offset = False
            except Exception:
                pass
            if can_be_const_offset:
                offset = sp.simplify(u - e)
                if offset.is_number and offset != 0:
                    diags.append(
                        {
                            "code": "constant_offset",
                            "message": f"Your expression differs from the correct one by the constant ${sp.latex(offset)}$.",
                        }
                    )
                    return diags
    except Exception:
        pass
    return diags


# ---------------------------------------------------------------------------
# Form checks (performed on the UNEVALUATED parse tree)
# ---------------------------------------------------------------------------
def _is_rational_number(t):
    try:
        return (
            bool(t.is_number)
            and bool(sp.nsimplify(t).is_rational)
            and not t.has(sp.I)
            and not any(isinstance(p, sp.Pow) and not p.exp.is_integer for p in sp.preorder_traversal(t))
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
        if (
            "simplified_radical" in forms
            and isinstance(e, sp.Pow)
            and e.exp == sp.Rational(1, 2)
            and isinstance(e.base, sp.Integer)
        ):
            n = abs(int(e.base))
            if n > 1 and any(n % (k * k) == 0 for k in range(2, int(n**0.5) + 1)):
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
