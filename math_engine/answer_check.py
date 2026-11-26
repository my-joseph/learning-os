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
    interval        {"type": "interval", "value": "[3, 21)"}
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
import re
import sys

import sympy as sp

from math_engine._checkers import (  # noqa: F401
    _check_parallel_numeric,
    _format_scalar_multiple_ratio,
    check_choice,
    check_complex,
    check_expression,
    check_interval,
    check_number,
    check_solution_set,
    check_text,
    check_tuple,
    check_vector,
)
from math_engine._equivalence import (  # noqa: F401
    FORM_MESSAGES,
    EqualTimeoutError,
    _evaluated_form_issues,
    _form_result,
    _has_large_exponent,
    _intervals_equal,
    _is_allowed_diagnostic_factor,
    _is_rational_number,
    _run_with_timeout,
    form_issues,
    generic_value_diagnostics,
    is_equal,
    numeric_close,
)
from math_engine._parse import (  # noqa: F401
    _INTERVAL_FORMAT_MSG,
    MAX_INPUT_LEN,
    TRUSTED_INTERNAL_FUNCS,
    VETTED_EXTRA_FUNCS,
    WHITELIST_CONSTANTS,
    WHITELIST_FUNCS,
    ASTTransformer,
    SafeParseError,
    SecurityVisitor,
    _insert_implicit_mul,
    _normalize,
    _parse_interval_endpoint,
    _parse_interval_piece,
    _parse_vector_unit_notation,
    _split_interval_pieces,
    _split_items,
    _split_top_level_commas,
    _tokenize_vector,
    _uneval_add,
    _uneval_div,
    _uneval_mul,
    _uneval_pow,
    _uneval_sub,
    _uneval_usub,
    parse_interval,
    parse_math,
    safe_parse,
    to_expr,
)

__all__ = [
    "ASTTransformer",
    "CHECKERS",
    "EqualTimeoutError",
    "FORM_MESSAGES",
    "MAX_INPUT_LEN",
    "SafeParseError",
    "SecurityVisitor",
    "TRAP_VERDICTS",
    "TRUSTED_INTERNAL_FUNCS",
    "VETTED_EXTRA_FUNCS",
    "WHITELIST_CONSTANTS",
    "WHITELIST_FUNCS",
    "check_answer",
    "check_choice",
    "check_complex",
    "check_expression",
    "check_interval",
    "check_number",
    "check_solution_set",
    "check_text",
    "check_tuple",
    "check_variant_answer",
    "check_vector",
    "form_issues",
    "generic_value_diagnostics",
    "is_equal",
    "is_omission_trap",
    "match_trap",
    "numeric_close",
    "parse_interval",
    "parse_math",
    "safe_parse",
    "to_expr",
]

CHECKERS = {
    "number": check_number,
    "complex": check_complex,
    "expression": check_expression,
    "solution_set": check_solution_set,
    "interval": check_interval,
    "tuple": check_tuple,
    "choice": check_choice,
    "text": check_text,
    "vector": check_vector,
}


def check_answer(spec, raw):
    if not (raw or "").strip():
        return {
            "verdict": "invalid input",
            "message": "Type your final answer first.",
            "components": [],
            "diagnostics": [],
        }
    fn = CHECKERS.get(spec.get("type"))
    if not fn:
        return {
            "verdict": "invalid input",
            "message": f"Unsupported answer type: {spec.get('type')}",
            "components": [],
            "diagnostics": [],
        }
    try:
        return fn(spec, raw)
    except SafeParseError as ex:
        return {"verdict": "invalid input", "message": f"Invalid input: {ex}", "components": [], "diagnostics": []}
    except EqualTimeoutError:
        return {
            "verdict": "invalid input",
            "message": "Evaluation timed out. Input is too complex.",
            "components": [],
            "diagnostics": [],
        }
    except ValueError as ex:
        return {"verdict": "invalid input", "message": f"Invalid input: {ex}", "components": [], "diagnostics": []}
    except Exception:
        return {
            "verdict": "invalid input",
            "message": "Could not read that input. Use forms like 3 - 4i, 3/4, sqrt(2)/2, x^2 + 1, or x = 2, x = -3.",
            "components": [],
            "diagnostics": [],
        }


TRAP_VERDICTS = ("incorrect", "partial")


def match_trap(spec: dict, user_input: str, trap_val: object) -> bool:
    """True when `user_input` equals the problem's trap answer (`trapValue`), checked with the same checker as
    the real answer. Applies to wrong (`incorrect`) and incomplete (`partial`) answers, so an omission trap on a
    solution set (a strict subset of the roots) is matched too."""
    spec_type = spec.get("type")
    try:
        trap_spec = dict(spec)
        if spec_type in ("number", "expression", "complex", "interval"):
            trap_spec["value"] = str(trap_val)
        elif spec_type == "vector":
            trap_spec["value"] = trap_val
            trap_spec.pop("components", None)
            trap_spec.pop("values", None)
        elif spec_type == "tuple":
            if isinstance(trap_val, (list, tuple)):
                trap_spec["values"] = list(trap_val)
            elif isinstance(trap_val, str):
                parts = [
                    p.strip() for p in re.sub(r"^\s*[\(\[\{<]|[\)\]\}>]\s*$", "", trap_val).split(",") if p.strip()
                ]
                trap_spec["values"] = parts
            else:
                trap_spec["values"] = [trap_val]
        elif spec_type == "solution_set":
            if isinstance(trap_val, (list, tuple)):
                trap_spec["values"] = [str(v) for v in trap_val]
            else:
                trap_spec["values"] = _split_items(str(trap_val), spec.get("variable", "x"))
        else:
            return False
        fn = CHECKERS.get(spec_type)
        return bool(fn) and fn(trap_spec, user_input).get("verdict") == "correct"
    except Exception:
        return False


def check_variant_answer(variant_id: str, raw: str, variants_dir: str | None = None) -> dict:
    """Check ``raw`` against a variant in ``drills/variants/`` identified by ``variant_id``."""
    from math_engine.variant_bank import find_variant

    found = find_variant(variant_id, variants_dir=variants_dir)
    if not found:
        return {
            "verdict": "invalid input",
            "message": f"Variant '{variant_id}' not found.",
            "components": [],
            "diagnostics": [],
        }
    _, variant = found
    spec = variant.get("answerSpec") or {}
    res = check_answer(spec, raw)
    trap_val = variant.get("trapValue")
    if trap_val is None:
        trap_val = (variant.get("verify") or {}).get("trapValue")
    if res.get("verdict") in TRAP_VERDICTS and trap_val is not None and match_trap(spec, raw, trap_val):
        res["trapMatched"] = True
    return res


def is_omission_trap(spec: dict, tv: object) -> bool:
    """True when a solution_set or interval trap is a strict, non-empty subset of the correct set."""
    spec_type = spec.get("type")
    if spec_type == "interval":
        try:
            expected_set = parse_interval(str(spec.get("value", "")), variables=spec.get("variables"))
            trap_set = parse_interval(str(tv), variables=spec.get("variables"))
            return trap_set != sp.EmptySet and trap_set.is_proper_subset(expected_set)
        except Exception:
            return False
    if spec_type != "solution_set":
        return False
    variable = spec.get("variable", "x")
    try:
        expected = [to_expr(str(v), variables=[variable], trusted=True) for v in spec.get("values") or []]
        items = [to_expr(it, variables=[variable], trusted=True) for it in _split_items(str(tv), variable)]
    except Exception:
        return False
    return 0 < len(items) < len(expected) and all(any(is_equal(i, e) for e in expected) for i in items)


if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    user_input = payload.get("input", "")
    variant_id = payload.get("variantId")
    if isinstance(variant_id, str) and variant_id.strip():
        res = check_variant_answer(variant_id.strip(), user_input)
    else:
        spec = payload.get("answerSpec", {})
        res = check_answer(spec, user_input)
        trap_val = payload.get("trapValue")
        if res.get("verdict") in TRAP_VERDICTS and trap_val is not None and match_trap(spec, user_input, trap_val):
            res["trapMatched"] = True

    print(json.dumps(res))
