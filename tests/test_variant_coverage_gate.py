"""The Similar coverage ratchet blocks new gaps and requires pruning stale entries."""

import json
from pathlib import Path

import pytest

from math_engine import variant_bank

ROOT = Path(__file__).resolve().parents[1]
UNIT = "MTH-T99-C01"
EXISTING_DRILL = f"DRL-{UNIT}-01"
NEW_DRILL = f"DRL-{UNIT}-02"
ARCHETYPE = "synthetic-archetype"


def _write_drill(root: Path, scope: str, drill_id: str) -> None:
    scope_dir = root / "drills/data" / scope
    scope_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "drillId": drill_id,
        "unitCode": scope,
        "problems": [{"archetypeKey": ARCHETYPE, "level": 2}],
    }
    (scope_dir / f"{drill_id}.json").write_text(json.dumps(doc), encoding="utf-8")


@pytest.fixture
def synthetic_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    baseline_path = tmp_path / variant_bank.COVERAGE_BASELINE_PATH
    baseline_path.parent.mkdir(parents=True)
    baseline_path.write_text(json.dumps({EXISTING_DRILL: [[ARCHETYPE, 2]]}), encoding="utf-8")
    _write_drill(tmp_path, UNIT, EXISTING_DRILL)
    return tmp_path


def test_repository_variant_coverage_gate() -> None:
    passed, report = variant_bank.check_coverage_gate(ROOT)
    assert passed, report


def test_gate_accepts_baseline_and_skips_prg(synthetic_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_drill(synthetic_repo, "PRG-T99-C01", "DRL-PRG-T99-C01-01")

    assert variant_bank.main(["--coverage-gate"]) == 0
    report = capsys.readouterr().out
    assert "trial minimum: 1 eligible variant per (archetypeKey, level) pair" in report
    assert f"Baseline uncovered pair: {EXISTING_DRILL} {ARCHETYPE} @ L2 (have 0, need 1 more)." in report
    assert "PRG-T99-C01" not in report


def test_gate_rejects_new_drill_with_grandfathered_pair(
    synthetic_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_drill(synthetic_repo, UNIT, NEW_DRILL)

    assert variant_bank.main(["--coverage-gate"]) == 1
    report = capsys.readouterr().out
    assert f"FAIL New uncovered pair: {NEW_DRILL} {ARCHETYPE} @ L2 (have 0, need 1 more)." in report
    assert "Adding baseline entries is forbidden." in report


def test_gate_requires_pruning_a_covered_baseline_pair(
    synthetic_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    variants_dir = synthetic_repo / "drills/variants"
    variants_dir.mkdir(parents=True)
    variants = [
        {
            "variantId": f"VAR-{UNIT}-{ARCHETYPE}-01",
            "archetypeKey": ARCHETYPE,
            "level": 2,
            "review": {"verdict": "pass", "note": "Verified fixture variant."},
        }
    ]
    (variants_dir / f"{UNIT}.json").write_text(json.dumps({"variants": variants}), encoding="utf-8")

    assert variant_bank.main(["--coverage-gate"]) == 1
    report = capsys.readouterr().out
    assert f"FAIL Stale baseline entry: {EXISTING_DRILL} {ARCHETYPE} @ L2" in report
    assert f'Delete ["{ARCHETYPE}", 2] under {EXISTING_DRILL} in {variant_bank.COVERAGE_BASELINE_PATH}.' in report

    (synthetic_repo / variant_bank.COVERAGE_BASELINE_PATH).write_text("{}", encoding="utf-8")
    assert variant_bank.main(["--coverage-gate"]) == 0


def test_coverage_counts_existing_stock_once_and_at_the_exact_pair(synthetic_repo: Path) -> None:
    variants_dir = synthetic_repo / "drills/variants"
    variants_dir.mkdir(parents=True)
    reviewed = {
        "variantId": f"VAR-{UNIT}-{ARCHETYPE}-01",
        "archetypeKey": ARCHETYPE,
        "level": 2,
        "review": {"verdict": "pass", "note": "Verified fixture variant."},
    }
    wrong_level = dict(reviewed, variantId="other-level", level=3)
    quarantined = dict(reviewed, variantId="old-variant", status="quarantined")
    rejected = dict(reviewed, variantId="rejected-variant", review={"verdict": "fix", "note": "Needs revision."})
    (variants_dir / f"{UNIT}.json").write_text(
        json.dumps({"variants": [reviewed, wrong_level, quarantined, rejected]}), encoding="utf-8"
    )
    (variants_dir / f"{UNIT}-U01.json").write_text(json.dumps({"variants": [reviewed]}), encoding="utf-8")
    drill_doc = {
        "unitCode": UNIT,
        "problems": [{"archetypeKey": ARCHETYPE, "level": level} for level in (1, 2, 2, 3)],
    }
    coverage = variant_bank.compute_drill_coverage(drill_doc, variants_dir=str(variants_dir))
    assert [(p["level"], p["drillProblems"], p["variantCount"], p["covered"]) for p in coverage["pairs"]] == [
        (1, 1, 0, False),
        (2, 2, 1, True),
        (3, 1, 1, True),
    ]
