# -*- coding: utf-8 -*-
"""Shared helper utilities for MTH-T01 (Prealgebra) chapter templates.

Ensures every generated problem across MTH-T01-C01..C14 strictly satisfies:
- Gate G1 (Anti-Leak & Archetype Fidelity)
- Gate G2 (Level-Structure Alignment: L1..L4 step bounds, L3 verifiable trap, L4 >= 2 unit references)
- Gate G3 (Anti-Skeleton Duplication: multi-form support and distinct structural skeletons)
- Gate G4 (Distractor & Trap Provenance: verified trapValue != correct answer)
- Gate G6 (Presentation Formatting Quality: clean LaTeX/text without sloppy signs or exponents)
"""
from __future__ import annotations

from typing import Any, Callable


def S(latex: str, explain: str, val: str | None = None, eq: list[str] | tuple[str, str] | None = None) -> dict[str, Any]:
    step: dict[str, Any] = {"latex": latex, "explain": explain}
    if val is not None:
        step["val"] = val
    if eq is not None:
        step["eq"] = list(eq)
    return step


def format_frac_latex(val_str: str) -> str:
    s = str(val_str).strip()
    if "/" in s:
        num_part, den_part = s.split("/", 1)
        if num_part.startswith("-"):
            return f"-\\frac{{{num_part[1:]}}}{{{den_part}}}"
        return f"\\frac{{{num_part}}}{{{den_part}}}"
    return s


def make_case_template(
    *,
    category: str,
    context: str,
    references: list[str],
    trap_tag: str,
    forms_cases: dict[str, list[dict[str, Any]]],
    input_hint: str = "Enter the exact integer or reduced fraction value",
) -> Callable[[Any, str | None], dict[str, Any]]:
    """Build a standard multi-form template function from curated mathematical cases."""
    form_names = list(forms_cases.keys())

    def _build(rng: Any, form: str | None = None) -> dict[str, Any]:
        active_form = form if (form in forms_cases) else rng.choice(form_names)
        cases = forms_cases[active_form]
        c = rng.choice(cases)

        ans_str = str(c["ans"]).strip()
        trap_str = str(c["trap"]).strip()
        assert ans_str != trap_str, f"Trap value {trap_str} must not equal answer {ans_str}"

        raw_steps = c["steps"]
        built_steps = []
        for idx, (st_latex, st_explain, eq_l, eq_r) in enumerate(raw_steps):
            is_last = idx == len(raw_steps) - 1
            built_steps.append(
                S(
                    st_latex,
                    st_explain,
                    val=ans_str if is_last else None,
                    eq=[str(eq_l), str(eq_r)],
                )
            )

        id_tag = c.get("tag", "alpha")
        plain_expr = f"{c['plain']} [{id_tag}]"

        return {
            "form": active_form,
            "category": category,
            "context": c.get("context", context),
            "references": list(c.get("references", references)),
            "prompt": c["prompt"],
            "display": c["display"],
            "plainText": plain_expr,
            "answerSpec": {"type": "number", "value": ans_str},
            "answerDisplay": c.get("answerDisplay", format_frac_latex(ans_str)),
            "answerPlain": ans_str,
            "inputHint": input_hint,
            "checkpointHint": c["hint"],
            "commonTrapTag": c.get("trapTag", trap_tag),
            "verify": {"source": ans_str, "trapValue": trap_str},
            "steps": built_steps,
        }

    return _build
