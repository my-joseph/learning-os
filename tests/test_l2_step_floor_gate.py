"""L2 step floor gate: new L2 math problems need >= 4 real steps; existing drills use a shrink-only baseline."""

from __future__ import annotations

import copy
import json
import os
import shutil
from pathlib import Path

import pytest

from math_engine import ai_drill_ingest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / ".claude" / "skills" / "new-math-drill" / "template"
UNIT = "MTH-T99-C01"
EXISTING_DRILL = f"DRL-{UNIT}-01"
NEW_DRILL = f"DRL-{UNIT}-02"


def _make_steps(count: int) -> list[dict[str, str]]:
    return [{"latex": f"x = {i}", "explain": f"Step {i} transformation."} for i in range(1, count + 1)]


def _write_drill(root: Path, scope: str, drill_id: str, step_count: int, qid: str = "Q02", level: int = 2) -> None:
    scope_dir = root / "drills" / "data" / scope
    scope_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "drillId": drill_id,
        "unitCode": scope,
        "problems": [{"id": qid, "level": level, "steps": _make_steps(step_count)}],
    }
    (scope_dir / f"{drill_id}.json").write_text(json.dumps(doc), encoding="utf-8")


@pytest.fixture
def synthetic_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    baseline_path = tmp_path / ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH
    baseline_path.parent.mkdir(parents=True)
    baseline_path.write_text(json.dumps({EXISTING_DRILL: ["Q02"]}), encoding="utf-8")
    _write_drill(tmp_path, UNIT, EXISTING_DRILL, step_count=3)
    return tmp_path


def _template_draft() -> dict:
    return json.loads((TEMPLATE_DIR / "draft.json").read_text(encoding="utf-8"))


def test_repository_l2_step_floor_gate() -> None:
    passed, report = ai_drill_ingest.check_l2_step_floor_gate(ROOT)
    assert passed, report
    assert "12/51 short" in report
    assert "Baseline: 10 drill(s), 12 problem(s)." in report
    # Zero-leak: report lists drill IDs and QIDs only, never prompt/step LaTeX.
    assert "DRL-MTH-T01-C04-01 Q04" in report
    assert "$" not in report


def test_new_draft_and_ingest_reject_short_l2_and_empty_steps(tmp_path: Path) -> None:
    draft = _template_draft()
    # Baseline template Q02 has 4 real steps -> passes.
    assert ai_drill_ingest.check_ai_drill(copy.deepcopy(draft), vault_dir=str(TEMPLATE_DIR)) == []

    # Truncating Q02 to 3 real steps fails check_ai_drill and ingest_ai_drill.
    short_draft = copy.deepcopy(draft)
    short_draft["problems"][1]["steps"] = short_draft["problems"][1]["steps"][:3]
    short_draft["problems"][1]["steps"][-1]["val"] = "8"
    errs = ai_drill_ingest.check_ai_drill(copy.deepcopy(short_draft), vault_dir=str(TEMPLATE_DIR))
    assert any("L2 problem has 3 real step(s)" in e for e in errs), errs

    vault = tmp_path / "vault"
    shutil.copytree(TEMPLATE_DIR, vault)
    with pytest.raises(ai_drill_ingest.AiContractError, match="L2 problem has 3 real step"):
        ai_drill_ingest.ingest_ai_drill(short_draft, data_root=str(tmp_path / "data"), vault_dir=str(vault))
    assert not (tmp_path / "data").exists()

    # Padding with an empty/whitespace step does not count as a real step.
    padded = copy.deepcopy(short_draft["problems"][1])
    padded["steps"].append({"latex": "   ", "explain": "Placeholder"})
    assert ai_drill_ingest.count_real_steps(padded) == 3
    with pytest.raises(ai_drill_ingest.AiContractError, match="3 real step"):
        ai_drill_ingest.validate_l2_step_floor(padded)


def test_l2_step_floor_gate_accepts_baseline_and_skips_prg(
    synthetic_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_drill(synthetic_repo, "PRG-T99-C01", "DRL-PRG-T99-C01-01", step_count=1)
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 0
    report = capsys.readouterr().out
    assert f"Baseline short L2 problem: {EXISTING_DRILL} Q02 (3 real steps, need >= 4)." in report
    assert "PRG-T99-C01" not in report


def test_l2_step_floor_gate_rejects_new_short_l2(synthetic_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_drill(synthetic_repo, UNIT, NEW_DRILL, step_count=2, qid="Q05")
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 1
    report = capsys.readouterr().out
    assert f"FAIL New short L2 problem: {NEW_DRILL} Q05 (2 real steps, need >= 4)." in report
    assert "Adding baseline entries is forbidden." in report


def test_l2_step_floor_gate_requires_pruning_stale_baseline(
    synthetic_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_drill(synthetic_repo, UNIT, EXISTING_DRILL, step_count=4)
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 1
    report = capsys.readouterr().out
    assert f"FAIL Stale baseline entry: {EXISTING_DRILL} Q02" in report
    assert f'Delete "Q02" under {EXISTING_DRILL} in {ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH}.' in report

    (synthetic_repo / ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH).write_text("{}", encoding="utf-8")
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 0


def test_check_ai_drill_grandfathers_saved_baseline_only_when_allowed() -> None:
    draft = _template_draft()
    draft["drillId"] = "DRL-MTH-T01-C04-01"
    draft["problems"][1]["id"] = "Q04"
    draft["problems"][1]["steps"] = draft["problems"][1]["steps"][:3]
    draft["problems"][1]["steps"][-1]["val"] = "8"

    # Draft mode (default) rejects even if drillId/QID match the baseline.
    errs_draft = ai_drill_ingest.check_ai_drill(copy.deepcopy(draft), vault_dir=str(TEMPLATE_DIR))
    assert any("L2 problem has 3 real step(s)" in e for e in errs_draft), errs_draft

    # Saved-drill recheck mode honors the baseline entry.
    errs_saved = ai_drill_ingest.check_ai_drill(
        copy.deepcopy(draft), vault_dir=str(TEMPLATE_DIR), allow_l2_baseline=True
    )
    assert errs_saved == []
    assert os.path.isfile(ROOT / ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH)
