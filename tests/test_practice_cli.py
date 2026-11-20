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


def test_submit_saves_and_prints_session_summary(tmp_path):
    doc = json.loads(DRILL_PATH.read_text(encoding="utf-8"))
    problem = doc["problems"][0]
    progress_dir = tmp_path / "progress"
    run_cli("answer", DRILL_ID, problem["id"], "15/8", progress_dir=progress_dir)

    result = run_cli("submit", DRILL_ID, progress_dir=progress_dir)
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    progress = json.loads((progress_dir / f"{DRILL_ID}.json").read_text(encoding="utf-8"))
    assert summary["practiceStatus"] == "In Progress"
    assert progress["sessionSummary"] == summary
    assert "sessionSummary" not in json.loads(DRILL_PATH.read_text(encoding="utf-8"))
    assert "pilot-only" in result.stderr.lower()


def test_pilot_only_docstring_and_banner(tmp_path):
    import scripts.practice as practice

    assert "pilot-only" in (practice.__doc__ or "").lower()
    result = run_cli("summary", DRILL_ID, progress_dir=tmp_path / "progress")
    assert result.returncode == 0
    assert "pilot-only" in result.stderr.lower()
    assert json.loads(result.stdout)["practiceStatus"] == "Ready"


def test_reveal_flags_respect_cycle_started_at_and_variant_attempts(tmp_path):
    doc = json.loads(DRILL_PATH.read_text(encoding="utf-8"))
    qid = doc["problems"][0]["id"]
    progress_dir = tmp_path / "progress"
    progress_dir.mkdir(parents=True)

    # Prior-cycle correct attempt + variant correct attempt in current cycle should NOT
    # suppress setupRevealedBeforeAnswer or solutionRevealedBeforeAnswer in the new cycle.
    progress_file = progress_dir / f"{DRILL_ID}.json"
    progress_file.write_text(
        json.dumps(
            {
                "drillId": DRILL_ID,
                "unitCode": doc["unitCode"],
                "sessionSummary": {},
                "problems": {
                    qid: {
                        "userInput": "27/10",
                        "score": 1,
                        "divergedStep": None,
                        "mistakes": [],
                        "lastCheck": {"verdict": "correct"},
                        "cycleStartedAt": "2026-11-20T12:00:00Z",
                        "attempts": [
                            {"input": "27/10", "ts": "2026-11-19T10:00:00Z", "verdict": "correct"},
                            {
                                "input": "99",
                                "ts": "2026-11-20T12:05:00Z",
                                "verdict": "correct",
                                "kind": "variant",
                            },
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    res_setup = run_cli("setup", DRILL_ID, qid, progress_dir=progress_dir)
    assert res_setup.returncode == 0
    st = json.loads(progress_file.read_text(encoding="utf-8"))["problems"][qid]
    assert st.get("setupRevealedBeforeAnswer") is True

    res_sol = run_cli("solution", DRILL_ID, qid, progress_dir=progress_dir)
    assert res_sol.returncode == 0
    st = json.loads(progress_file.read_text(encoding="utf-8"))["problems"][qid]
    assert st.get("solutionRevealedBeforeAnswer") is True

    # Once an original correct attempt exists in the current cycle, neither flag is set.
    progress_file.write_text(
        json.dumps(
            {
                "drillId": DRILL_ID,
                "unitCode": doc["unitCode"],
                "sessionSummary": {},
                "problems": {
                    qid: {
                        "userInput": "27/10",
                        "score": 1,
                        "divergedStep": None,
                        "mistakes": [],
                        "lastCheck": {"verdict": "correct"},
                        "cycleStartedAt": "2026-11-20T12:00:00Z",
                        "attempts": [
                            {"input": "27/10", "ts": "2026-11-20T12:10:00Z", "verdict": "correct"},
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    assert run_cli("setup", DRILL_ID, qid, progress_dir=progress_dir).returncode == 0
    assert run_cli("solution", DRILL_ID, qid, progress_dir=progress_dir).returncode == 0
    st_after = json.loads(progress_file.read_text(encoding="utf-8"))["problems"][qid]
    assert not st_after.get("setupRevealedBeforeAnswer")
    assert not st_after.get("solutionRevealedBeforeAnswer")
