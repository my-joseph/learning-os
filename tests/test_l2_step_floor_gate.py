"""L2 step floor gate: new L2 math drills and variants need >= 4 real steps; existing items use a shrink-only baseline."""

from __future__ import annotations

import copy
import json
import os
import shutil
from pathlib import Path

import pytest

from math_engine import ai_drill_ingest, variant_bank

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / ".claude" / "skills" / "new-math-drill" / "template"
UNIT = "MTH-T99-C01"
EXISTING_DRILL = f"DRL-{UNIT}-01"
NEW_DRILL = f"DRL-{UNIT}-02"
EXISTING_VARIANT = f"VAR-{UNIT}-arch-01"
NEW_VARIANT = f"VAR-{UNIT}-arch-02"


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


def _write_bank(root: Path, unit: str, variants: list[dict]) -> None:
    vdir = root / "drills" / "variants"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / f"{unit}.json").write_text(json.dumps({"unitCode": unit, "variants": variants}), encoding="utf-8")


@pytest.fixture
def synthetic_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    baseline_path = tmp_path / ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH
    baseline_path.parent.mkdir(parents=True)
    baseline_path.write_text(
        json.dumps({"drills": {EXISTING_DRILL: ["Q02"]}, "variants": {UNIT: [EXISTING_VARIANT]}}),
        encoding="utf-8",
    )
    _write_drill(tmp_path, UNIT, EXISTING_DRILL, step_count=3)
    _write_bank(tmp_path, UNIT, [{"variantId": EXISTING_VARIANT, "level": 2, "steps": _make_steps(3)}])
    return tmp_path


def _template_draft() -> dict:
    return json.loads((TEMPLATE_DIR / "draft.json").read_text(encoding="utf-8"))


def test_repository_l2_step_floor_gate() -> None:
    passed, report = ai_drill_ingest.check_l2_step_floor_gate(ROOT)
    assert passed, report
    assert "drills 12/51 short" in report
    assert "variants 41/147 short" in report
    assert "Baseline: 10 drill(s), 12 problem(s); 10 bank(s), 41 variant(s)." in report
    # Zero-leak: report lists drill/variant IDs only, never prompt/step LaTeX.
    assert "DRL-MTH-T01-C04-01 Q04" in report
    assert "$" not in report


def test_new_draft_and_ingest_reject_short_l2_and_step_padding(tmp_path: Path) -> None:
    draft = _template_draft()
    assert ai_drill_ingest.check_ai_drill(copy.deepcopy(draft), vault_dir=str(TEMPLATE_DIR)) == []

    # 1. Truncating Q02 to 3 real steps fails check_ai_drill and ingest_ai_drill.
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

    # 2. Padding with repeated identical LaTeX (ignoring whitespace/\left/\right) is rejected.
    padded_dup = copy.deepcopy(short_draft)
    dup_step = copy.deepcopy(padded_dup["problems"][1]["steps"][1])
    dup_step["latex"] = r"\left 4x \right = 32 "
    padded_dup["problems"][1]["steps"].insert(2, dup_step)
    assert ai_drill_ingest.count_real_steps(padded_dup["problems"][1]) == 3
    errs_dup = ai_drill_ingest.check_ai_drill(padded_dup, vault_dir=str(TEMPLATE_DIR))
    assert any("L2 problem has 3 real step(s)" in e for e in errs_dup), errs_dup

    # 3. Padding with a pure restatement of the given display/prompt expression is rejected.
    padded_restate = copy.deepcopy(short_draft)
    padded_restate["problems"][1]["steps"].insert(
        0,
        {"latex": "4x + 7 = 39", "explain": "Start from the given equation."},
    )
    assert ai_drill_ingest.count_real_steps(padded_restate["problems"][1]) == 3
    errs_restate = ai_drill_ingest.check_ai_drill(padded_restate, vault_dir=str(TEMPLATE_DIR))
    assert any("L2 problem has 3 real step(s)" in e for e in errs_restate), errs_restate


def test_under_labelling_bypass_rejected_at_all_levels() -> None:
    draft = _template_draft()

    # 1. Short L2 reverse item labelled L1 with blindSolve (reverse=True -> demand_level 2 > 1) rejected.
    under_bs = copy.deepcopy(draft)
    p = under_bs["problems"][1]
    p["level"] = 1
    p["form"] = "direct"
    p["steps"] = p["steps"][:3]
    p["steps"][-1]["val"] = "8"
    p["blindSolve"] = {
        "answer": "8",
        "ambiguous": False,
        "setup": "given",
        "strategy": "prescribed",
        "check": "none",
        "task": "compute",
        "reverse": True,
        "steps": 3,
    }
    errs_bs = ai_drill_ingest.check_ai_drill(under_bs, vault_dir=str(TEMPLATE_DIR))
    assert any("under-labelled" in e and "give L2" in e for e in errs_bs), errs_bs

    # 2. Short L2 reverse item labelled L1 WITHOUT blindSolve (form="reverse") rejected.
    under_form = copy.deepcopy(draft)
    p2 = under_form["problems"][1]
    p2["level"] = 1
    p2["form"] = "reverse"
    p2["steps"] = p2["steps"][:3]
    p2["steps"][-1]["val"] = "8"
    errs_form = ai_drill_ingest.check_ai_drill(under_form, vault_dir=str(TEMPLATE_DIR))
    assert any("under-labelled" in e and "form='reverse'" in e for e in errs_form), errs_form

    # 3. L2 problem with blindSolve giving L3 rejected as under-labelled.
    under_l2 = copy.deepcopy(draft)
    p3 = under_l2["problems"][1]
    p3["blindSolve"] = {
        "answer": "8",
        "ambiguous": False,
        "setup": "given",
        "strategy": "choose",
        "check": "none",
        "task": "compute",
        "reverse": True,
        "steps": 4,
    }
    errs_l2 = ai_drill_ingest.check_ai_drill(under_l2, vault_dir=str(TEMPLATE_DIR))
    assert any("under-labelled" in e and "give L3" in e for e in errs_l2), errs_l2


def test_add_variants_enforces_l2_step_floor_for_new_variants(tmp_path: Path) -> None:
    draft = _template_draft()
    short_l2 = copy.deepcopy(draft["problems"][1])
    short_l2["steps"] = short_l2["steps"][:3]
    short_l2["steps"][-1]["val"] = "8"
    short_l2["review"] = {"verdict": "pass", "note": "Fixture short L2 variant."}

    variants_dir = tmp_path / "variants"
    variants_dir.mkdir()
    with pytest.raises(variant_bank.VariantBankError, match="L2 problem has 3 real step"):
        variant_bank.add_variants(
            {"unitCode": "MTH-TEMPLATE", "variants": [short_l2]},
            variants_dir=str(variants_dir),
            data_root=str(tmp_path / "empty_data"),
            vault_dir=str(TEMPLATE_DIR),
        )
    assert not (variants_dir / "MTH-TEMPLATE.json").exists()

    # Expanding to 4 real steps passes add_variants cleanly.
    good_l2 = copy.deepcopy(draft["problems"][1])
    saved = variant_bank.add_variants(
        {"unitCode": "MTH-TEMPLATE", "variants": [good_l2]},
        variants_dir=str(variants_dir),
        data_root=str(tmp_path / "empty_data"),
        vault_dir=str(TEMPLATE_DIR),
    )
    assert len(saved["variants"]) == 1


def test_l2_step_floor_gate_accepts_baseline_and_skips_prg(
    synthetic_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_drill(synthetic_repo, "PRG-T99-C01", "DRL-PRG-T99-C01-01", step_count=1)
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 0
    report = capsys.readouterr().out
    assert f"Baseline short L2 problem: {EXISTING_DRILL} Q02 (3 real steps, need >= 4)." in report
    assert f"Baseline short L2 variant: {UNIT} {EXISTING_VARIANT} (3 real steps, need >= 4)." in report
    assert "PRG-T99-C01" not in report


def test_l2_step_floor_gate_rejects_new_short_l2_drill_and_variant(
    synthetic_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_drill(synthetic_repo, UNIT, NEW_DRILL, step_count=2, qid="Q05")
    _write_bank(
        synthetic_repo,
        UNIT,
        [
            {"variantId": EXISTING_VARIANT, "level": 2, "steps": _make_steps(3)},
            {"variantId": NEW_VARIANT, "level": 2, "steps": _make_steps(2)},
        ],
    )
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 1
    report = capsys.readouterr().out
    assert f"FAIL New short L2 problem: {NEW_DRILL} Q05 (2 real steps, need >= 4)." in report
    assert f"FAIL New short L2 variant: {UNIT} {NEW_VARIANT} (2 real steps, need >= 4)." in report
    assert "Adding baseline entries is forbidden." in report


def test_l2_step_floor_gate_requires_pruning_stale_baseline(
    synthetic_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_drill(synthetic_repo, UNIT, EXISTING_DRILL, step_count=4)
    _write_bank(synthetic_repo, UNIT, [{"variantId": EXISTING_VARIANT, "level": 2, "steps": _make_steps(4)}])
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 1
    report = capsys.readouterr().out
    assert f"FAIL Stale drill baseline entry: {EXISTING_DRILL} Q02" in report
    assert f"FAIL Stale variant baseline entry: {UNIT} {EXISTING_VARIANT}" in report

    (synthetic_repo / ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH).write_text(
        json.dumps({"drills": {}, "variants": {}}), encoding="utf-8"
    )
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 0


def test_check_ai_drill_grandfathers_saved_baseline_only_when_allowed() -> None:
    draft = _template_draft()
    draft["drillId"] = "DRL-MTH-T01-C04-01"
    draft["problems"][1]["id"] = "Q04"
    draft["problems"][1]["steps"] = draft["problems"][1]["steps"][:3]
    draft["problems"][1]["steps"][-1]["val"] = "8"

    errs_draft = ai_drill_ingest.check_ai_drill(copy.deepcopy(draft), vault_dir=str(TEMPLATE_DIR))
    assert any("L2 problem has 3 real step(s)" in e for e in errs_draft), errs_draft

    errs_saved = ai_drill_ingest.check_ai_drill(
        copy.deepcopy(draft), vault_dir=str(TEMPLATE_DIR), allow_l2_baseline=True
    )
    assert errs_saved == []
    assert os.path.isfile(ROOT / ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH)
