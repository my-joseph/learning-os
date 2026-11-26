# -*- coding: utf-8 -*-
"""Centralized AnswerSpec Registry defining schemas, engines, and validators for all problem types."""

import re
from typing import Any, Dict, Optional

ANSWER_SPEC_TYPES: Dict[str, Dict[str, Any]] = {
    "number": {
        "engine": "math",
        "description": "Scalar numerical answers (exact integers, reduced fractions, radicals, or decimal tolerances)",
        "required_fields": ["value"],
        "optional_fields": ["forms", "tolerance", "unit"],
        "examples": [{"type": "number", "value": "3/4"}, {"type": "number", "value": 11}],
    },
    "complex": {
        "engine": "math",
        "description": "Complex numbers in standard form a + bi or rectangular coordinates",
        "required_fields": ["value"],
        "optional_fields": ["forms", "allow_i"],
        "examples": [{"type": "complex", "value": "3 - 4*I"}],
    },
    "expression": {
        "engine": "math",
        "description": "Symbolic algebraic expressions with specified variables",
        "required_fields": ["value"],
        "optional_fields": ["variables", "forms", "allowFuncs"],
        "examples": [{"type": "expression", "value": "x**2 - 1", "variables": ["x"]}],
    },
    "solution_set": {
        "engine": "math",
        "description": "Unordered set of roots or algebraic equation solutions",
        "required_fields": ["values"],
        "optional_fields": ["variable", "tolerance"],
        "examples": [{"type": "solution_set", "values": ["-2 + 3*I", "-2 - 3*I"], "variable": "x"}],
    },
    "interval": {
        "engine": "math",
        "description": "Real-number intervals and unions using (, [, ), ], inf/oo/∞, and U/∪",
        "required_fields": ["value"],
        "optional_fields": ["variables"],
        "examples": [
            {"type": "interval", "value": "[3, 21)"},
            {"type": "interval", "value": "(-oo, 2) U (2, oo)"},
        ],
    },
    "tuple": {
        "engine": "math",
        "description": "Ordered coordinate tuples or multi-variable points",
        "required_fields": ["values"],
        "optional_fields": ["labels", "acceptComplex"],
        "examples": [{"type": "tuple", "values": ["5", "3"], "labels": ["x", "y"]}],
    },
    "vector": {
        "engine": "math",
        "description": "Euclidean vectors in R^2, R^3, R^4 with angle bracket or unit vector notation",
        "required_fields": ["components"],
        "optional_fields": ["dimension", "vectorNotation", "allowPartial"],
        "examples": [{"type": "vector", "dimension": 3, "components": [1, -2, 3]}],
    },
    "choice": {
        "engine": "shared",
        "description": "Multiple-choice discrete options (A, B, C, D)",
        "required_fields": ["correct"],
        "optional_fields": ["options"],
        "examples": [{"type": "choice", "correct": "B"}],
    },
    "text": {
        "engine": "shared",
        "description": "Exact text or keyword validation (case-insensitive option)",
        "required_fields": ["accepted"],
        "optional_fields": ["case_sensitive"],
        "examples": [{"type": "text", "accepted": ["server-only"]}],
    },
    "predict_output": {
        "engine": "code",
        "description": "Predicted execution output token sequence",
        "required_fields": [],
        "required_any_of": ["tokens", "value"],
        "optional_fields": ["tokens", "value", "commonTrapTag", "allowPartial"],
        "examples": [
            {"type": "predict_output", "tokens": ["1", "3", "2"]},
            {"type": "predict_output", "value": "1, 3, 2"},
        ],
    },
}

# Deprecated PRG answerSpec types from retired templates (no drill/lab/variant uses them; kept here for clear rejection messages).
DEPRECATED_ANSWER_SPEC_TYPES: Dict[str, Dict[str, Any]] = {
    "code_output": {
        "engine": "code",
        "deprecated": True,
        "replacement": "predict_output",
        "description": "Deprecated alias for 'predict_output' (retired templates).",
        "required_fields": [],
        "required_any_of": ["tokens", "value"],
        "optional_fields": ["tokens", "value", "commonTrapTag", "allowPartial"],
    },
    "line_number": {
        "engine": "code",
        "deprecated": True,
        "replacement": "choice",
        "description": "Deprecated 1-indexed defective line number (use 'choice' for find-the-flaw drills).",
        "required_fields": ["correctLine"],
        "optional_fields": ["commonTrapTag", "flawExplanation"],
    },
    "find_bug": {
        "engine": "code",
        "deprecated": True,
        "replacement": "choice",
        "description": "Deprecated alias for 'line_number' (use 'choice' for find-the-flaw drills).",
        "required_fields": ["correctLine"],
        "optional_fields": ["commonTrapTag", "flawExplanation"],
    },
}


def validate_answer_spec(spec: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate that an answerSpec dictionary conforms to the active registered schema."""
    if not isinstance(spec, dict):
        return False, "answerSpec must be a dictionary"
    stype = spec.get("type")
    if not stype:
        return False, "answerSpec must have a 'type' field"
    deprecated = DEPRECATED_ANSWER_SPEC_TYPES.get(stype)
    if deprecated:
        return False, f"Deprecated answerSpec type: '{stype}' (use '{deprecated['replacement']}' instead)"
    info = ANSWER_SPEC_TYPES.get(stype)
    if not info:
        return False, f"Unknown answerSpec type: '{stype}'"
    for rf in info["required_fields"]:
        if rf not in spec:
            return False, f"Missing required field '{rf}' for answerSpec type '{stype}'"
    any_of = info.get("required_any_of")
    if any_of and not any(rf in spec for rf in any_of):
        return False, f"Missing required field (one of {any_of}) for answerSpec type '{stype}'"
    return True, None


def get_registered_types(engine: Optional[str] = None) -> list[str]:
    """Return active registered answerSpec type names, optionally filtered by engine ('math', 'code', 'shared')."""
    if not engine:
        return sorted(ANSWER_SPEC_TYPES.keys())
    return sorted(k for k, v in ANSWER_SPEC_TYPES.items() if v["engine"] in (engine, "shared"))


def check_choice_spec(
    spec: dict[str, Any],
    raw: str,
    *,
    correct_message: str = "Correct.",
    incorrect_message: str = "Incorrect choice.",
    wrong_diagnostics: Optional[list[dict[str, str]]] = None,
) -> dict[str, Any]:
    """Shared validator for 'choice' answerSpecs across math_engine and code_engine."""
    raw_text = "" if raw is None else str(raw).strip()
    u = raw_text.upper()
    options = spec.get("options")
    if isinstance(options, list) and options:
        valid_ids = {
            str(opt["id"]).strip().upper() for opt in options if isinstance(opt, dict) and opt.get("id") is not None
        }
        if valid_ids and u not in valid_ids:
            return {
                "verdict": "invalid input",
                "message": f"Option '{raw_text}' is not one of the available choices.",
                "components": [],
                "diagnostics": [],
            }
    correct_id = str(spec.get("correct", "")).strip().upper()
    ok = bool(correct_id) and u == correct_id
    return {
        "verdict": "correct" if ok else "incorrect",
        "message": correct_message if ok else incorrect_message,
        "components": [{"label": "Choice", "ok": ok}],
        "diagnostics": [] if ok else list(wrong_diagnostics or []),
    }


def check_text_spec(
    spec: dict[str, Any],
    raw: str,
    *,
    correct_message: str = "Correct.",
    incorrect_message: str = "Does not match the accepted answers.",
) -> dict[str, Any]:
    """Shared validator for 'text' answerSpecs across math_engine and code_engine."""
    case_sensitive = bool(spec.get("case_sensitive", False))

    def norm(value: Any) -> str:
        text = re.sub(r"\s+", " ", ("" if value is None else str(value)).strip())
        return text if case_sensitive else text.lower()

    raw_accepted = spec.get("accepted")
    if raw_accepted is None:
        fallback = spec.get("value")
        raw_accepted = [fallback] if fallback is not None else []
    accepted = [norm(item) for item in raw_accepted if item is not None]
    ok = norm(raw) in accepted
    return {
        "verdict": "correct" if ok else "incorrect",
        "message": correct_message if ok else incorrect_message,
        "components": [{"label": "Answer", "ok": ok}],
        "diagnostics": [],
    }
