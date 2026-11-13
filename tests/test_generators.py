"""Seeded generation must be deterministic and produce well-formed drill docs (hermetic: tmp dir)."""

import shutil

import pytest

from code_engine.generate import generate_drill_set as code_generate
from math_engine.generate import generate_drill_set as math_generate

REQUIRED_KEYS = {"drillId", "unitCode", "problems", "config", "subject"}


def _signature(doc):
    return [(p["prompt"], p["answerDisplay"]) for p in doc["problems"]]


def test_math_generation_is_deterministic(tmp_path):
    a = math_generate("MTH-T02-C01-U01", 5, "ALL", seed=42, data_root=str(tmp_path), drill_id="A")
    b = math_generate("MTH-T02-C01-U01", 5, "ALL", seed=42, data_root=str(tmp_path), drill_id="B")
    assert REQUIRED_KEYS <= a.keys()
    assert len(a["problems"]) == 5
    assert _signature(a) == _signature(b)


@pytest.mark.skipif(shutil.which("node") is None, reason="code_engine verification needs node")
def test_code_generation_is_deterministic(tmp_path, monkeypatch):
    # code_engine writes CWD-relative side effects (drills/workspace/),
    # so run it inside an empty temp dir to keep the repo clean.
    monkeypatch.chdir(tmp_path)
    a = code_generate("PRG-T01-C01", 3, "ALL", seed=7, drill_id="A")
    b = code_generate("PRG-T01-C01", 3, "ALL", seed=7, drill_id="B")
    assert REQUIRED_KEYS <= a.keys()
    assert len(a["problems"]) == 3
    assert _signature(a) == _signature(b)


@pytest.mark.skipif(shutil.which("node") is None, reason="code_engine verification needs node")
def test_code_generation_does_not_mirror_into_practice_studio(tmp_path, monkeypatch):
    # Single source of truth: drills live only under <root>/drills/data (P3).
    monkeypatch.chdir(tmp_path)
    (tmp_path / "practice-studio").mkdir()
    code_generate("PRG-T01-C01", 1, "ALL", seed=1, drill_id="M")
    assert not (tmp_path / "practice-studio" / "drills").exists()
