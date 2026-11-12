# -*- coding: utf-8 -*-
"""
Figure Auto-Fill: attaches a parametric `figure` to a problem from its Reasoning Vault
archetype (`figureBuilders`) and the problem's `givens` (rules/03_stem.md §3).

Vault spec (per archetype):
  "figureBuilders": [
    {"fn": "build_circle_figure",
     "args": {"radius": "diameter/2"},          # arithmetic over given keys
     "labels": {"label_radius": "d = {diameter:g}"}}   # optional format strings over givens
  ]
The first builder whose referenced given keys all exist is used.
"""
import re
from typing import Any, Dict, List, Optional

from math_engine import figure_builder

_SAFE = re.compile(r"^[0-9a-zA-Z_+\-*/(). ]+$")


def _eval(expr: str, givens: Dict[str, Any]) -> Optional[float]:
    if not _SAFE.match(expr):
        return None
    names = re.findall(r"[A-Za-z_]\w*", expr)
    if any(n not in givens for n in names):
        return None
    local = {n: float(givens[n]) for n in names}
    try:
        return float(eval(expr, {"__builtins__": {}}, local))
    except Exception:
        return None


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
            for param, fmt in spec.get("labels", {}).items():
                kwargs[param] = fmt.format(**{k: float(v) for k, v in givens.items()
                                              if isinstance(v, (int, float))})
            if spec.get("title"):
                kwargs["title"] = spec["title"]
            return fn(**kwargs)
        except Exception:
            continue
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
