"""Tests for math unit-vault schema validation in `code_engine.quality_checks --check-vaults`."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from code_engine import quality_checks as qc


def _valid_math_archetype(**overrides) -> dict:
    arch = {
        "unitCode": "MTH-T02-C01-U02",
        "archetypeKey": "t02-c01-u02-sample-quad",
        "level": 2,
        "name": "Sample Quadratic Archetype",
        "source": "OpenStax Algebra and Trigonometry 2e §2.5",
        "coreConcept": "Apply the quadratic formula after rearranging to standard form.",
        "mentalModel": "Discriminant separates real and complex conjugate roots.",
        "governingRelation": "x = (-b +/- sqrt(b^2 - 4ac)) / (2a)",
        "cognitiveTraps": [
            {
                "trapTag": "t02-c01-u02-sign-error-trap",
                "description": "Drops leading minus sign on b.",
            }
        ],
        "figureNone": "Purely symbolic equation solving.",
    }
    arch.update(overrides)
    return arch


def test_clean_math_archetype_has_zero_errors_and_zero_warnings() -> None:
    errors, warnings_list = qc.validate_math_archetype(_valid_math_archetype())
    assert errors == []
    assert warnings_list == []


@pytest.mark.parametrize(
    "missing_field",
    ("archetypeKey", "level", "name", "coreConcept", "governingRelation", "cognitiveTraps", "figureNone"),
)
def test_missing_required_field_produces_error(missing_field: str) -> None:
    arch = _valid_math_archetype()
    del arch[missing_field]
    errors, _warnings = qc.validate_math_archetype(arch)
    assert errors, f"Expected error when missing required field '{missing_field}'"


def test_invalid_level_duplicate_key_and_unknown_figure_builder_produce_errors() -> None:
    errs_lvl, _ = qc.validate_math_archetype(_valid_math_archetype(level=6))
    assert any("level" in e for e in errs_lvl)
    errs_bool, _ = qc.validate_math_archetype(_valid_math_archetype(level=True))
    assert any("level" in e for e in errs_bool)

    seen: set[str] = set()
    e1, _ = qc.validate_math_archetype(_valid_math_archetype(), seen_keys=seen)
    e2, _ = qc.validate_math_archetype(_valid_math_archetype(), seen_keys=seen)
    assert e1 == []
    assert any("duplicate" in e for e in e2)

    bad_fig = _valid_math_archetype(figureBuilders=[{"fn": "nonexistent_builder_fn"}])
    del bad_fig["figureNone"]
    errs_fig, _ = qc.validate_math_archetype(bad_fig)
    assert any("unknown builder" in e for e in errs_fig)


def test_legacy_math_archetype_passes_with_warnings_only() -> None:
    legacy = deepcopy(_valid_math_archetype())
    del legacy["unitCode"]
    del legacy["mentalModel"]
    del legacy["source"]
    legacy["cognitiveTraps"] = ["legacy-string-trap"]

    errors, warnings_list = qc.validate_math_archetype(legacy)
    assert errors == []
    assert any("unitCode" in w for w in warnings_list)
    assert any("mentalModel" in w for w in warnings_list)
    assert any("source" in w for w in warnings_list)
    assert any("legacy string" in w for w in warnings_list)


def test_real_math_vaults_all_pass_with_warnings_only(tmp_path: Path) -> None:
    errors, warnings_list, vault_count, archetype_count = qc.check_math_vaults()
    assert errors == []
    assert vault_count >= 35
    assert archetype_count >= 150
    assert len(warnings_list) > 0, "Expected legacy math vaults to emit non-blocking warnings"

    # CLI --check-vaults exits 0 on a temp vault containing only a legacy archetype
    prg_dir = tmp_path / "prg_vaults"
    prg_dir.mkdir()
    math_dir = tmp_path / "math_vaults"
    math_dir.mkdir()
    legacy_vault = {
        "unitCode": "MTH-T99-C01",
        "archetypes": [
            {
                "archetypeKey": "legacy-k",
                "level": 1,
                "name": "Legacy",
                "coreConcept": "Concept",
                "governingRelation": "a = b",
                "cognitiveTraps": ["legacy-trap"],
                "figureNone": "Symbolic.",
            }
        ],
    }
    (math_dir / "MTH-T99-C01.json").write_text(json.dumps(legacy_vault), encoding="utf-8")

    rc = qc.main(["--check-vaults", "--vault-dir", str(prg_dir), "--math-vault-dir", str(math_dir)])
    assert rc == 0

    # Missing required field fails CLI with exit code 1
    bad_vault = deepcopy(legacy_vault)
    del bad_vault["archetypes"][0]["governingRelation"]
    (math_dir / "MTH-T99-C01.json").write_text(json.dumps(bad_vault), encoding="utf-8")
    rc_bad = qc.main(["--check-vaults", "--vault-dir", str(prg_dir), "--math-vault-dir", str(math_dir)])
    assert rc_bad == 1
