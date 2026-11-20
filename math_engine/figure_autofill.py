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

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from math_engine import figure_builder
from math_engine.safe_expr import try_evaluate

# Figure titles must describe the neutral visual object ("Graph", "Rectangle", "Number Line"),
# never the test, method, theorem, or property the learner is supposed to recognize or choose.
METHOD_NAMING_TITLE_PATTERNS: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\b(?:horizontal|vertical)\s+line\s+test\b"
            r"|\b(?:line|ratio|root|derivative|comparison|integral|divergence|alternating\s+series)\s+test\b",
            re.IGNORECASE,
        ),
        "names a test",
    ),
    (
        re.compile(
            r"\b(?:quadratic|distance|midpoint|slope|heron'?s|euler'?s)\s+formula\b"
            r"|\b(?:pythagorean|remainder|factor|rational\s+root|rational\s+zero|intermediate\s+value"
            r"|mean\s+value|binomial|fundamental)\s+theorem\b"
            r"|\b(?:chain|product|quotient|power|cramer'?s|l'?h[oô]pital'?s|descartes'?)\s+rule\b",
            re.IGNORECASE,
        ),
        "names a formula, theorem, or rule",
    ),
    (
        re.compile(
            r"\b(?:completing\s+the\s+square|synthetic\s+division|long\s+division|u-substitution"
            r"|integration\s+by\s+parts|implicit\s+differentiation|soh[\s-]*cah[\s-]*toa|foil)\b",
            re.IGNORECASE,
        ),
        "names a solution method",
    ),
    (
        re.compile(
            r"\b(?:non-)?one-to-one\b"
            r"|\b(?:complementary|supplementary)\s+angles?\b"
            r"|\btoolkit\s+function\b"
            r"|\b(?:transformation|transformed|horizontally\s+stretched|vertically\s+stretched"
            r"|horizontally\s+compressed|vertically\s+compressed)\b"
            r"|\b(?:slope\s+triangle|axis\s+of\s+symmetry|end\s+behavior|multiplicity|regression\s+line"
            r"|extrapolation|interpolation|exchanged\s+coordinates|constant\s+slope|constant\s+rate"
            r"|downward\s+trend|upward\s+trend|asymptotes?\s+separate)\b",
            re.IGNORECASE,
        ),
        "hints the mathematical property or classification",
    ),
)


def figure_title_warning_reason(title: Optional[str]) -> Optional[str]:
    """Return a short reason if ``title`` names a method, test, or concept to choose, else None."""
    if not isinstance(title, str) or not title.strip():
        return None
    for pattern, reason in METHOD_NAMING_TITLE_PATTERNS:
        if pattern.search(title):
            return reason
    return None


def collect_figure_title_warnings(problems: Iterable[Dict[str, Any]]) -> List[str]:
    """Return non-blocking warning messages for problems with method-naming figure titles."""
    warnings: List[str] = []
    for idx, prob in enumerate(problems, 1):
        if not isinstance(prob, dict):
            continue
        fig = prob.get("figure")
        if not isinstance(fig, dict):
            continue
        title = fig.get("title")
        reason = figure_title_warning_reason(title)
        if reason:
            pid = prob.get("id") or prob.get("variantId") or f"Q{idx:02d}"
            warnings.append(f"[{pid}] Figure title '{title}' {reason}; keep figure titles neutral (e.g. 'Graph').")
    return warnings


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
