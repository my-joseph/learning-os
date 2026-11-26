# -*- coding: utf-8 -*-
"""Formatting constants and curriculum hierarchy helpers for code_engine."""

LEVEL_LABELS = {
    1: "Foundation",
    2: "Standard Exam",
    3: "Trap & Diagnostic",
    4: "Applied Synthesis",
    5: "Non-Routine Synthesis",
}


def unit_hierarchy(unit_code: str) -> tuple[str, str]:
    """`PRG-T01-C01-U01` -> (`PRG-T01`, `PRG-T01-C01`): the topic and chapter a unit belongs to."""
    parts = unit_code.split("-")
    topic_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else unit_code
    chapter_code = f"{parts[0]}-{parts[1]}-{parts[2]}" if len(parts) >= 3 else unit_code
    return topic_code, chapter_code
