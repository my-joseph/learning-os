"""Generators must raise instead of silently falling back (06 §2.2)."""

import pytest

from math_engine.generate import generate_drill_set

UNIT = "MTH-T02-C01-U01"


def test_difficulty_5_without_l5_templates_raises(tmp_path):
    with pytest.raises(ValueError, match="L5"):
        generate_drill_set(UNIT, count=3, difficulty="5", seed=1, data_root=str(tmp_path))


def test_unknown_template_filter_raises(tmp_path):
    with pytest.raises(ValueError, match="template filter"):
        generate_drill_set(UNIT, count=3, seed=1, templates="no-such-template", data_root=str(tmp_path))
