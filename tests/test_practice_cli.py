"""Tests for the local math practice CLI."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRILL_ID = "DRL-MTH-T01-C04-03"
DRILL_PATH = ROOT / "drills" / "data" / "MTH-T01-C04" / f"{DRILL_ID}.json"


def run_cli(*args: str, progress_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "scripts.practice", *args],
        cwd=ROOT,
        env={**os.environ, "PROGRESS_DIR": str(progress_dir)},
        capture_output=True,
        text=True,
    )


def test_show_exposes_only_prompt_hint_and_svg_path(tmp_path):
    before = DRILL_PATH.read_bytes()
    doc = json.loads(before)
    problem = doc["problems"][0]
    result = run_cli("show", DRILL_ID, problem["id"], progress_dir=tmp_path / "progress")
    assert result.returncode == 0, result.stderr
    assert problem["prompt"] in result.stdout
    assert problem["inputHint"] in result.stdout
    assert problem["answerPlain"] not in result.stdout
    assert problem["answerDisplay"] not in result.stdout
    assert "steps" not in result.stdout
    assert DRILL_PATH.read_bytes() == before


def test_answer_persists_studio_attempt_shape_only_to_progress(tmp_path):
    doc = json.loads(DRILL_PATH.read_text(encoding="utf-8"))
    problem = doc["problems"][0]
    progress_dir = tmp_path / "progress"
    result = run_cli("answer", DRILL_ID, problem["id"], "15/8", progress_dir=progress_dir)
    assert result.returncode == 0, result.stderr
    progress = json.loads((progress_dir / f"{DRILL_ID}.json").read_text(encoding="utf-8"))
    state = progress["problems"][problem["id"]]
    assert state["attempts"][0]["input"] == "15/8"
    assert state["attempts"][0]["verdict"] == "incorrect"
    assert state["attempts"][0]["matchedTrap"] == problem["commonTrapTag"]
    assert state["score"] == 0
    assert "state" not in json.loads(DRILL_PATH.read_text(encoding="utf-8"))["problems"][0]
