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
    checkpoint_hint: str = "Work through the derivation step-by-step on scratch paper, then compare your solution line by line with the student's work to identify where they diverge.",
    common_trap_tag: str = "flaw-selection",
    flaw_tag: str | None = None,
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

    # Invariant: Step explaining the flaw must reference the student's erroneous LaTeX line
    flaw_idx = flaw_line - 1
    if 0 <= flaw_idx < len(steps):
        erroneous_line = shown_lines[flaw_idx]
        exp = steps[flaw_idx].get("explain", "")
        if erroneous_line not in exp:
            steps[flaw_idx]["explain"] = f"Line {flaw_line} is wrong: The student wrote ${erroneous_line}$, but this is incorrect. {exp}"

    actual_flaw_tag = flaw_tag or line_trap_map.get(flaw_line) or common_trap_tag

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
        "trapKind": "selection",
        "trapDerivation": None,
        "flawTag": actual_flaw_tag,
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
