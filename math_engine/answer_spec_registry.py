# -*- coding: utf-8 -*-
"""Centralized AnswerSpec Registry defining schemas, engines, and validators for all problem types."""

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
    "code_output": {
        "engine": "code",
        "description": "Standard output string comparison from code execution",
        "required_fields": ["expected"],
        "optional_fields": ["trim_whitespace", "ignore_trailing_newline"],
        "examples": [{"type": "code_output", "expected": "hello\nworld"}],
    },
    "predict_output": {
        "engine": "code",
        "description": "Predicted execution logs or output array",
        "required_fields": ["expected"],
        "optional_fields": [],
        "examples": [{"type": "predict_output", "expected": ["1", "3", "2"]}],
    },
    "line_number": {
        "engine": "code",
        "description": "Specific 1-indexed source line containing bug",
        "required_fields": ["correct_line"],
        "optional_fields": ["acceptable_range"],
        "examples": [{"type": "line_number", "correct_line": 14}],
    },
    "find_bug": {
        "engine": "code",
        "description": "Bug identification and categorization in source code",
        "required_fields": ["bug_type"],
        "optional_fields": ["line"],
        "examples": [{"type": "find_bug", "bug_type": "this_binding", "line": 8}],
    },
}


def validate_answer_spec(spec: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate that an answerSpec dictionary conforms to registered schema."""
    if not isinstance(spec, dict):
        return False, "answerSpec must be a dictionary"
    stype = spec.get("type")
    if not stype:
        return False, "answerSpec must have a 'type' field"
    info = ANSWER_SPEC_TYPES.get(stype)
    if not info:
        return False, f"Unknown answerSpec type: '{stype}'"
    for rf in info["required_fields"]:
        if rf not in spec:
            return False, f"Missing required field '{rf}' for answerSpec type '{stype}'"
    return True, None


def get_registered_types(engine: Optional[str] = None) -> list[str]:
    """Return all registered answerSpec type names, optionally filtered by engine ('math', 'code', 'shared')."""
    if not engine:
        return sorted(ANSWER_SPEC_TYPES.keys())
    return sorted(k for k, v in ANSWER_SPEC_TYPES.items() if v["engine"] in (engine, "shared"))
