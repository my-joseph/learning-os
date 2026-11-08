"""Helper utilities for Find-the-Flaw diagnostic problem templates.

Eliminates structural boilerplate across domains (complex numbers, calculus, etc.).
"""

from __future__ import annotations

from typing import Any


def build_flaw_choice_problem(
    *,
    prompt: str,
    shown_lines: list[str],
    steps: list[dict[str, Any]],
    flaw_line: int,
    line_trap_map: dict[int, str],
    verify_source: str,
    vals: list[Any],
    form_prefix: str = "flaw-line",
    category: str = "Trap & Edge Case",
    checkpoint_hint: str = "Compute the derivation yourself first to check each step.",
    common_trap_tag: str = "flaw-selection",
    variables: list[str] | None = None,
) -> dict[str, Any]:
    """Constructs a standard machine-verified find-the-flaw problem."""
    aligned = "\\begin{aligned}" + " \\\\ ".join(
        f"&\\text{{Line {i + 1}: }}\\; {ln}" for i, ln in enumerate(shown_lines)
    ) + "\\end{aligned}"

    num_lines = len(shown_lines)
    options = [
        {"id": str(i), "label": f"Line {i}", "trapTag": line_trap_map.get(i, "flaw-line")}
        for i in range(1, num_lines + 1)
    ]
    trap_choice = str((flaw_line % num_lines) + 1)

    prob = {
        "form": f"{form_prefix}-{flaw_line}",
        "category": category,
        "prompt": prompt,
        "display": aligned,
        "plainText": f"Find flaw in: {shown_lines[0]}",
        "answerSpec": {"type": "choice", "options": options, "correct": str(flaw_line)},
        "answerDisplay": f"\\text{{Line {flaw_line}}}",
        "answerPlain": str(flaw_line),
        "inputHint": "Choose a line",
        "checkpointHint": checkpoint_hint,
        "commonTrapTag": common_trap_tag,
        "steps": steps,
        "verify": {
            "source": verify_source,
            "flaw": {"values": vals, "firstWrong": flaw_line},
            "trapValue": trap_choice,
        },
    }
    if variables:
        prob["variables"] = variables
    return prob
