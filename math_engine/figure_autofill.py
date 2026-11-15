# -*- coding: utf-8 -*-
"""
Figure Auto-Fill: attaches a parametric `figure` to a problem from its Reasoning Vault
archetype (`figureBuilders`) and the problem's `givens` (rules/03_stem.md §3).

Vault spec (per archetype):
  "figureBuilders": [
    {"fn": "build_circle_figure",
     "args": {"radius": "sqrt(area/pi)"},       # numeric args: math over given keys (math_engine.safe_expr)
     "labels": {"label_radius": "r = ?"},        # string args: format strings over givens ("{area:g}")
     "note": "Not to scale"}                     # optional; added automatically when a label contains "?"
  ]
The first builder whose referenced given keys all exist is used. Draw the asked-for quantity to scale but
label it `?` (rules/03_stem.md §3.1), so reverse and multi-step problems keep their figure.

An archetype with no figure says why: `"figureNone": "<reason>"` (gate: `require_figure_decision`).
"""

from typing import Any, Dict, List, Optional

from math_engine import figure_builder
from math_engine.safe_expr import try_evaluate


def _numeric(givens: Dict[str, Any]) -> Dict[str, float]:
    return {k: float(v) for k, v in givens.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}


def _eval(expr: str, givens: Dict[str, Any]) -> Optional[float]:
    return try_evaluate(str(expr), _numeric(givens))


def build_figure(archetype: Dict[str, Any], givens: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for spec in archetype.get("figureBuilders", []) or []:
        fn = getattr(figure_builder, spec.get("fn", ""), None)
        if fn is None:
            continue
        kwargs: Dict[str, Any] = {}
        ok = True
        for param, expr in spec.get("args", {}).items():
            val = _eval(str(expr), givens)
            if val is None:
                ok = False
                break
            kwargs[param] = val
        if not ok:
            continue
        try:
            labels = {param: fmt.format(**_numeric(givens)) for param, fmt in spec.get("labels", {}).items()}
            kwargs.update(labels)
            if spec.get("title"):
                kwargs["title"] = spec["title"]
            fig = fn(**kwargs)
        except Exception:
            continue
        note = spec.get("note") or ("Not to scale" if any("?" in v for v in labels.values()) else None)
        if note:
            fig["note"] = note
        return fig
    return None


def autofill_problem_figure(prob: Dict[str, Any], archetypes: List[Dict[str, Any]]) -> bool:
    """Fill prob['figure'] if absent. Returns True if a figure was attached."""
    if "figure" in prob or prob.get("figureWaiver"):
        return False
    arch = next((a for a in archetypes if a.get("archetypeKey") == prob.get("archetypeKey")), None)
    if not arch or not arch.get("figureBuilders"):
        return False
    fig = build_figure(arch, prob.get("givens", {}))
    if fig:
        prob["figure"] = fig
        return True
    return False


def archetype_requires_figure(prob: Dict[str, Any], archetypes: List[Dict[str, Any]]) -> bool:
    arch = next((x for x in archetypes if x.get("archetypeKey") == prob.get("archetypeKey")), None)
    return bool(arch and arch.get("figureBuilders"))


def figure_decision_missing(archetype: Dict[str, Any]) -> bool:
    """True when an archetype has neither `figureBuilders` nor a `figureNone` reason."""
    return not archetype.get("figureBuilders") and not str(archetype.get("figureNone") or "").strip()
