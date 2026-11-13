# -*- coding: utf-8 -*-
"""
Formatting constants and level descriptors for code_engine.
"""

LEVEL_LABELS = {
    1: "Foundation",
    2: "Standard Exam",
    3: "Trap & Diagnostic",
    4: "Applied Synthesis",
    5: "Non-Routine Synthesis",
}


def unit_hierarchy(unit_code: str) -> tuple[str, str]:
    """`MTH-T02-C01-U01` -> (`MTH-T02`, `MTH-T02-C01`): the topic and chapter a unit belongs to."""
    parts = unit_code.split("-")
    topic_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else unit_code
    chapter_code = f"{parts[0]}-{parts[1]}-{parts[2]}" if len(parts) >= 3 else unit_code
    return topic_code, chapter_code


DIFFICULTY_MODES = {
    "ALL": "Mixed Exam Mode",
    "1": "Level 1 - Foundation",
    "2": "Level 2 - Standard Exam",
    "3": "Level 3 - Trap & Diagnostic",
    "4": "Level 4 - Applied Synthesis",
    "5": "Level 5 - Non-Routine Synthesis",
}
