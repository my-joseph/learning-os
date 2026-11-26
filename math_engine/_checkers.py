# -*- coding: utf-8 -*-
"""Per-type answer checkers for ``math_engine.answer_check``."""

import math
import re
from itertools import permutations

import sympy as sp

from math_engine._equivalence import (
    FORM_MESSAGES,
    EqualTimeoutError,
    _form_result,
    _intervals_equal,
    _run_with_timeout,
    form_issues,
    generic_value_diagnostics,
    is_equal,
)
from math_engine._parse import (
    VETTED_EXTRA_FUNCS,
    WHITELIST_FUNCS,
    SafeParseError,
    _parse_vector_unit_notation,
    _split_items,
    _tokenize_vector,
    parse_interval,
    parse_math,
    safe_parse,
    to_expr,
)


def check_number(spec, raw):
    raw_text = (raw or "").strip()
    variable = spec.get("variable") or next(iter(spec.get("variables") or []), None)
    assignment = re.match(r"^\s*([A-Za-z])\s*=\s*(.+)$", raw_text)
    function_assignment = re.match(r"^\s*[A-Za-z]\s*\([^)]*\)\s*=\s*(.+)$", raw_text)
    if assignment:
        if not variable or assignment.group(1) != variable:
            return {
                "verdict": "invalid input",
                "message": "Enter only the requested number, optionally as the answer variable followed by =.",
                "components": [],
                "diagnostics": [],
            }
        raw = assignment.group(2)
    elif function_assignment:
        raw = function_assignment.group(1)
    try:
        u = parse_math(raw)
    except SafeParseError as ex:
        u = None
        s_raw = (raw or "").strip()
        s_raw = s_raw.replace("\u27e8", "<").replace("\u27e9", ">").replace("\u3008", "<").replace("\u3009", ">")
        is_vec = (
            (s_raw.startswith("<") and s_raw.endswith(">"))
            or (s_raw.startswith("[") and s_raw.endswith("]"))
            or (s_raw.startswith("(") and s_raw.endswith(")") and "," in s_raw)
        )
        if is_vec:
            try:
                vars_list = spec.get("variables") or []
                toks = _tokenize_vector(s_raw)
                for t in toks:
                    safe_parse(t, variables=vars_list, allow_i=False)
                return {
                    "verdict": "incorrect",
                    "message": "Expected a scalar number, but received a vector. (If calculating a dot product, remember to sum the component products: $u_1 v_1 + u_2 v_2 + u_3 v_3$).",
                    "components": [{"label": "Value", "ok": False}],
                    "diagnostics": [
                        {"code": "vector_given_for_scalar", "message": "Expected a scalar, received a vector."}
                    ],
                }
            except Exception:
                pass
        if u is None:
            if "Syntax error" not in str(ex) and "invalid syntax" not in str(ex):
                raise
            return {
                "verdict": "invalid input",
                "message": "Enter a number or exact mathematical expression.",
                "components": [],
                "diagnostics": [],
            }
    tol = spec.get("tolerance")
    e = to_expr(spec["value"])
    comps = [{"label": "Value", "ok": False}]
    if is_equal(u, e, tolerance=tol):
        comps[0]["ok"] = True
        fr = _form_result(raw, u, spec)
        if fr:
            return {**fr, "components": comps}
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}
    diags = generic_value_diagnostics(u, e)
    return {
        "verdict": "incorrect",
        "message": "Not equal to the verified answer.",
        "components": comps,
        "diagnostics": diags,
    }


def check_complex(spec, raw):
    tol = spec.get("tolerance")
    e = sp.expand_complex(to_expr(spec["value"]))
    u = sp.expand_complex(parse_math(raw))
    ere, eim = sp.re(e), sp.im(e)
    ure, uim = sp.re(u), sp.im(u)
    re_ok, im_ok = is_equal(ure, ere, tolerance=tol), is_equal(uim, eim, tolerance=tol)
    comps = [{"label": "Real part", "ok": re_ok}, {"label": "Imaginary part", "ok": im_ok}]
    if re_ok and im_ok:
        fr = _form_result(raw, u, spec)
        if fr:
            return {**fr, "components": comps}
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}

    diags = []
    if re_ok and eim != 0 and is_equal(uim, -eim, tolerance=tol):
        diags.append(
            {
                "code": "imag_sign_flip",
                "message": "Real part is correct, but the imaginary part has the opposite sign. Check $i^2 = -1$ or the conjugate sign.",
            }
        )
    elif im_ok and ere != 0 and is_equal(ure, -ere, tolerance=tol):
        diags.append(
            {
                "code": "real_sign_flip",
                "message": "Imaginary part is correct, but the real part has the opposite sign. Check $i^2 = -1$ when combining real terms.",
            }
        )
    elif is_equal(ure, eim, tolerance=tol) and is_equal(uim, ere, tolerance=tol) and ere != eim:
        diags.append({"code": "swapped_parts", "message": "Your real and imaginary parts are swapped."})
    else:
        diags = generic_value_diagnostics(u, e)

    verdict = "partial" if (spec.get("allowPartial") and (re_ok or im_ok)) else "incorrect"
    msg = "One component matches; inspect the other." if (re_ok or im_ok) else "Not equal to the verified answer."
    return {"verdict": verdict, "message": msg, "components": comps, "diagnostics": diags}


def check_expression(spec, raw):
    tol = spec.get("tolerance")
    variables = spec.get("variables", ["x"])
    allowed_funcs = dict(WHITELIST_FUNCS)
    if "allowFuncs" in spec:
        for fn_name in spec["allowFuncs"]:
            if fn_name not in VETTED_EXTRA_FUNCS:
                raise SafeParseError(f"Unvetted function in allowFuncs: {fn_name}")
            allowed_funcs[fn_name] = VETTED_EXTRA_FUNCS[fn_name]
    e = to_expr(spec["value"], variables, trusted=True)
    u = safe_parse(raw, variables, allow_i=spec.get("allowI", False), allowed_funcs=allowed_funcs)
    comps = [{"label": "Equivalence", "ok": False}]
    if is_equal(u, e, variables=variables, tolerance=tol):
        comps[0]["ok"] = True
        fr = _form_result(raw, u, spec, variables)
        if fr:
            return {**fr, "components": comps}
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}
    return {
        "verdict": "incorrect",
        "message": "Not equivalent to the verified answer.",
        "components": comps,
        "diagnostics": generic_value_diagnostics(u, e, variables),
    }


def check_solution_set(spec, raw):
    variable = spec.get("variable", "x")
    expected = [sp.expand_complex(to_expr(v)) for v in spec["values"]]
    symmetric_roots = spec.get("symmetricRoots", False) or any(
        i != j and is_equal(value, -other) for i, value in enumerate(expected) for j, other in enumerate(expected)
    )
    try:
        users = [sp.expand_complex(parse_math(it)) for it in _split_items(raw, variable)]
    except Exception as ex:
        raise ValueError(f"Could not parse the solution list: {ex}")
    matched_u = set()
    matched_e = set()
    comps, diags = [], []
    for j, uv in enumerate(users):
        hit = next((i for i, ev in enumerate(expected) if i not in matched_e and is_equal(uv, ev)), None)
        ok = hit is not None
        if ok:
            matched_u.add(j)
            matched_e.add(hit)
        comps.append({"label": f"Your value ${sp.latex(uv)}$", "ok": ok})
    extras = [users[j] for j in range(len(users)) if j not in matched_u]
    for x in extras:
        if any(is_equal(x, -ev) for ev in expected):
            diags.append(
                {
                    "code": "whole_sign_flip",
                    "message": f"${sp.latex(x)}$ is the negative of a true solution. Check the sign of this value.",
                }
            )
        elif any(is_equal(sp.conjugate(x), ev) or is_equal(sp.re(x), sp.re(ev)) for ev in expected):
            diags.append(
                {
                    "code": "imag_sign_flip",
                    "message": f"${sp.latex(x)}$ has the right real part but the wrong imaginary part.",
                }
            )
        else:
            is_decimal_approx = any(
                not ev.is_Rational and x.is_number and abs(float(x.evalf()) - float(ev.evalf())) <= 0.0005
                for ev in expected
            )
            if is_decimal_approx:
                diags.append(
                    {"code": "decimal_not_exact", "message": "Give the exact form rather than a rounded decimal."}
                )
            else:
                diags.append(
                    {
                        "code": "extra_solution",
                        "message": "This value does not satisfy the equation (extraneous value).",
                    }
                )
    missing = len(expected) - len(matched_e)
    if missing:
        missing_guidance = (
            "Remember both signs of $\\pm$." if symmetric_roots else "Check whether another solution is missing."
        )
        diags.append({"code": "missing_solution", "message": f"{missing} solution(s) missing. {missing_guidance}"})
    if missing == 0 and not extras:
        forms = spec.get("forms", [])
        issues = []
        for it in _split_items(raw, variable):
            try:
                issues += form_issues(parse_math(it, evaluate=False), forms)
            except Exception:
                pass
        if issues:
            return {
                "verdict": "equivalent_not_in_form",
                "message": FORM_MESSAGES.get(issues[0], "Not in required form."),
                "components": comps,
                "diagnostics": [{"code": c, "message": FORM_MESSAGES.get(c, c)} for c in dict.fromkeys(issues)],
            }
        return {
            "verdict": "correct",
            "message": "Correct. All solutions found.",
            "components": comps,
            "diagnostics": [],
        }
    verdict = "partial" if matched_e else "incorrect"
    matched_count = len(matched_e)
    msg = f"{matched_count} of {len(expected)} expected values match; {missing} missing, {len(extras)} extra."
    return {
        "verdict": verdict,
        "message": msg,
        "components": comps,
        "diagnostics": diags,
    }


def check_interval(spec, raw):
    variables = spec.get("variables")
    expected_set = parse_interval(str(spec["value"]), variables=variables)
    user_set = parse_interval(raw, variables=variables)

    def _cmp():
        return _intervals_equal(user_set, expected_set)

    if _run_with_timeout(_cmp):
        return {
            "verdict": "correct",
            "message": "Correct.",
            "components": [],
            "diagnostics": [],
        }

    diags = []
    try:
        if _intervals_equal(user_set.closure, expected_set.closure):
            diags.append(
                {
                    "code": "wrong_bracket",
                    "message": "Check whether the endpoints are included ([ or ]) or excluded (( or )).",
                }
            )
        elif user_set.is_subset(expected_set):
            diags.append(
                {
                    "code": "missing_interval",
                    "message": "Your interval is missing part of the set.",
                }
            )
        elif expected_set.is_subset(user_set):
            diags.append(
                {
                    "code": "extra_interval",
                    "message": "Your interval includes values that should be excluded.",
                }
            )
    except Exception:
        pass

    return {
        "verdict": "incorrect",
        "message": "Not equal to the verified interval.",
        "components": [],
        "diagnostics": diags,
    }


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
    comps = [
        {"label": labels[i], "ok": i < len(users) and is_equal(users[i], expected[i])} for i in range(len(expected))
    ]
    if len(users) == len(expected) and all(c["ok"] for c in comps):
        return {"verdict": "correct", "message": "Correct.", "components": comps, "diagnostics": []}
    diags = []
    if len(users) != len(expected):
        diags.append(
            {"code": "wrong_component_count", "message": f"Expected {len(expected)} components, received {len(users)}."}
        )
    else:
        for i, (uv, ev) in enumerate(zip(users, expected)):
            if not comps[i]["ok"] and ev != 0 and is_equal(uv, -ev):
                diags.append({"code": "whole_sign_flip", "message": f"{labels[i]} has the opposite sign."})
        if len(expected) == 2 and is_equal(users[0], expected[1]) and is_equal(users[1], expected[0]):
            diags.append({"code": "swapped_parts", "message": "The components are swapped."})
    verdict = "partial" if any(c["ok"] for c in comps) else "incorrect"
    return {
        "verdict": verdict,
        "message": "Some components match." if verdict == "partial" else "No component matches.",
        "components": comps,
        "diagnostics": diags,
    }


def check_choice(spec, raw):
    from math_engine.answer_spec_registry import check_choice_spec

    return check_choice_spec(spec, raw)


def check_text(spec, raw):
    from math_engine.answer_spec_registry import check_text_spec

    return check_text_spec(spec, raw)


def _check_parallel_numeric(user_comps, expected_comps, vars_list=None):
    if not vars_list:
        try:
            pivot_idx = None
            for i, e in enumerate(expected_comps):
                try:
                    if abs(float(e)) > 1e-12:
                        pivot_idx = i
                        break
                except Exception:
                    continue
            if pivot_idx is None:
                return None

            val_e_pivot = float(expected_comps[pivot_idx])
            val_u_pivot = float(user_comps[pivot_idx])
            if abs(val_e_pivot) < 1e-12 or abs(val_u_pivot) < 1e-12:
                return None
            k = val_u_pivot / val_e_pivot
            for u, e in zip(user_comps, expected_comps):
                if abs(float(u) - k * float(e)) > 1e-5 * max(1.0, abs(float(u))):
                    return None
            return k
        except Exception:
            return None
    else:
        syms = [sp.Symbol(v) for v in vars_list]
        try:
            fixed_points = [{s: sp.Rational(base + i * 2, 1) for i, s in enumerate(syms)} for base in (2, 3, 5)]
            sample_ks = []
            for pt in fixed_points:
                pivot_idx = None
                for i, e in enumerate(expected_comps):
                    try:
                        v_e = float(e.subs(pt))
                        if abs(v_e) > 1e-6:
                            pivot_idx = i
                            break
                    except Exception:
                        continue
                if pivot_idx is None:
                    continue

                val_e = float(expected_comps[pivot_idx].subs(pt))
                val_u = float(user_comps[pivot_idx].subs(pt))
                if abs(val_e) < 1e-6 or abs(val_u) < 1e-9:
                    continue
                k = val_u / val_e
                all_match = True
                for u, e in zip(user_comps, expected_comps):
                    u_val = float(u.subs(pt))
                    e_val = float(e.subs(pt))
                    if abs(u_val - k * e_val) > 1e-5 * max(1.0, abs(u_val)):
                        all_match = False
                        break
                if not all_match:
                    return None
                sample_ks.append(k)

            if len(sample_ks) >= 2 and all(abs(k - sample_ks[0]) < 1e-5 for k in sample_ks):
                return sample_ks[0]
            return None
        except Exception:
            return None


def _format_scalar_multiple_ratio(k_val):
    """Formats scalar multiple ratio cleanly to integer, simple fraction, or simple radical (sqrt(2), sqrt(3))."""
    # 1. Exact or simple rational fraction (e.g. 5, 3/2, -2/3)
    try:
        q = sp.nsimplify(k_val, rational=True)
        if abs(k_val - float(q)) < 1e-5 and getattr(q, "q", 1) <= 20:
            return sp.latex(q)
    except Exception:
        pass

    # 2. Simple rational multiple of sqrt(2) or sqrt(3) (e.g. \sqrt{2}, 2\sqrt{2}, \frac{\sqrt{2}}{2}, \sqrt{3})
    for rad_sym, rad_val in [(sp.sqrt(2), math.sqrt(2)), (sp.sqrt(3), math.sqrt(3))]:
        try:
            ratio = k_val / rad_val
            q = sp.nsimplify(ratio, rational=True)
            if abs(ratio - float(q)) < 1e-4 and getattr(q, "q", 1) <= 10:
                return sp.latex(q * rad_sym)
        except Exception:
            pass

    # 3. Clean decimal fallback
    if abs(k_val - round(k_val)) < 1e-5:
        return str(int(round(k_val)))
    return f"{k_val:.3f}"


def check_vector(spec, raw):
    vars_list = spec.get("variables") or []

    def _eval_vector():
        raw_str = (raw or "").strip()
        if not raw_str:
            return {
                "verdict": "invalid input",
                "message": "Type your final answer first.",
                "components": [],
                "diagnostics": [],
            }

        expected_raw = spec.get("components") or spec.get("values") or spec.get("value")
        if expected_raw is None:
            raise ValueError("Vector answerSpec missing 'components' or 'values'")

        if isinstance(expected_raw, (list, tuple)):
            expected_comps = [to_expr(c, variables=vars_list) for c in expected_raw]
        elif isinstance(expected_raw, str):
            toks = _tokenize_vector(expected_raw)
            expected_comps = [safe_parse(t, variables=vars_list, allow_i=False) for t in toks]
        else:
            expected_comps = [to_expr(expected_raw, variables=vars_list)]

        dim = len(expected_comps)
        vector_notation = spec.get("vectorNotation", False)
        user_comps = None

        if vector_notation and not (raw_str.startswith(("<", "[", "(")) or "," in raw_str):
            user_comps = _parse_vector_unit_notation(raw_str, dim)

        if user_comps is None:
            toks = _tokenize_vector(raw_str)
            user_comps = [safe_parse(t, variables=vars_list, allow_i=False) for t in toks]

        # 1. Dimension mismatch check
        if len(user_comps) != len(expected_comps):
            comps = [{"label": f"Component {i + 1}", "ok": False} for i in range(len(expected_comps))]
            diags = [
                {
                    "code": "dimension_mismatch",
                    "message": f"Dimension mismatch: expected {len(expected_comps)} components, received {len(user_comps)}.",
                }
            ]
            return {
                "verdict": "incorrect",
                "message": f"Expected a {len(expected_comps)}-dimensional vector.",
                "components": comps,
                "diagnostics": diags,
            }

        tol = spec.get("tolerance")
        comp_matches = [is_equal(u, e, variables=vars_list, tolerance=tol) for u, e in zip(user_comps, expected_comps)]
        comps = [{"label": f"Component {i + 1}", "ok": comp_matches[i]} for i in range(len(expected_comps))]

        if all(comp_matches):
            return {
                "verdict": "correct",
                "message": "Correct.",
                "components": comps,
                "diagnostics": [],
            }

        # Determine verdict strictly from component comparison first
        verdict = "partial" if (spec.get("allowPartial") and any(comp_matches)) else "incorrect"
        message = "Some components match." if verdict == "partial" else "Not equal to the verified vector."

        # Diagnostics (parallel/swapped/sign): isolated so timeouts or errors discard diagnostics and keep determined verdict
        diags = []
        try:

            def _gather_diagnostics():
                d_list = []
                # 2. Parallel / scalar multiple check (numeric substitution, no sp.simplify)
                k_ratio = _check_parallel_numeric(user_comps, expected_comps, vars_list)
                is_opposite_dir = False
                if k_ratio is not None and abs(k_ratio) > 1e-6:
                    if abs(k_ratio - (-1.0)) < 1e-5:
                        is_opposite_dir = True
                        d_list.append(
                            {
                                "code": "scalar_multiple",
                                "message": "Your vector points in the opposite direction (factor of -1). Check negative signs.",
                            }
                        )
                    else:
                        k_disp = _format_scalar_multiple_ratio(k_ratio)
                        d_list.append(
                            {
                                "code": "scalar_multiple",
                                "message": f"Your vector is parallel to the correct answer but differs by a scalar factor of ${k_disp}$.",
                            }
                        )

                # 3. Swapped order / permutation check
                if not d_list:
                    is_swapped = False
                    for p in permutations(range(len(expected_comps))):
                        if list(p) == list(range(len(expected_comps))):
                            continue
                        if all(
                            is_equal(
                                user_comps[p[i]], expected_comps[i], variables=vars_list, tolerance=tol, timeout=0.08
                            )
                            for i in range(len(expected_comps))
                        ):
                            is_swapped = True
                            break
                    if is_swapped:
                        d_list.append(
                            {
                                "code": "swapped_order",
                                "message": "The vector components are swapped or entered in the wrong order.",
                            }
                        )

                # 4. Component sign error check (skipped if parallel(-1) already reported)
                if not is_opposite_dir:
                    inverted_indices = []
                    for i, (u, e) in enumerate(zip(user_comps, expected_comps)):
                        if (
                            not comp_matches[i]
                            and e != 0
                            and is_equal(u, -e, variables=vars_list, tolerance=tol, timeout=0.08)
                        ):
                            inverted_indices.append(i + 1)
                    if inverted_indices:
                        if len(inverted_indices) == 1:
                            sign_msg = f"Component {inverted_indices[0]} has the opposite sign."
                        else:
                            comps_str = (
                                ", ".join(str(x) for x in inverted_indices[:-1]) + f" and {inverted_indices[-1]}"
                            )
                            sign_msg = f"Components {comps_str} have the opposite sign."
                        d_list.append(
                            {
                                "code": "component_sign_error",
                                "message": sign_msg,
                            }
                        )

                return d_list

            diags = _run_with_timeout(_gather_diagnostics, timeout_sec=0.15)
        except (Exception, EqualTimeoutError):
            diags = []

        # Deduplicate diagnostics by code
        seen_codes = set()
        unique_diags = []
        for d in diags:
            c = d.get("code")
            if c not in seen_codes:
                seen_codes.add(c)
                unique_diags.append(d)

        return {
            "verdict": verdict,
            "message": message,
            "components": comps,
            "diagnostics": unique_diags,
        }

    try:
        return _run_with_timeout(_eval_vector, timeout_sec=1.5)
    except EqualTimeoutError:
        return {
            "verdict": "invalid input",
            "message": "Evaluation timed out. Input is too complex.",
            "components": [],
            "diagnostics": [],
        }
