"""Tests for PRG Layer 3 review rubric (`qualityChecks`), validator, and ingest gates."""

from __future__ import annotations

import json
import shutil
from copy import deepcopy

import pytest

from code_engine.ai_drill_ingest import (
    AiContractError,
    ingest_ai_code_drill,
    register_code_archetype,
)
from code_engine.lint_check import LintToolsMissingError, get_lint_binaries
from code_engine.quality_checks import (
    VAULT_DIR,
    check_all_vaults,
    load_universal,
    validate_quality_checks,
    validate_universal_checks,
    verify_known_bad_lint,
)


def _require_lint_tools() -> None:
    if shutil.which("node") is None:
        pytest.skip("node binary not installed on PATH")
    try:
        get_lint_binaries()
    except LintToolsMissingError as exc:
        pytest.skip(str(exc))


def _valid_check(cid: str = "QC-sample-check", severity: str = "must") -> dict:
    return {
        "id": cid,
        "check": "No reference to internal mutable state escapes the factory.",
        "why": "Returning a live reference lets callers mutate private state outside the API.",
        "severity": severity,
        "knownBad": {
            "code": "function makeBox() { const items = []; return { getAll: () => items }; }",
            "caughtBy": "review",
        },
    }


def _valid_problem(archetype_key: str = "prg-test-arch", solution_code: str | None = None) -> dict:
    sol = solution_code or ("function addNums(a, b) {\n  return a + b;\n}\nmodule.exports = { addNums };\n")
    return {
        "id": "Q01",
        "verificationLevel": "partial",
        "archetype": "problem-solving",
        "archetypeKey": archetype_key,
        "context": "billing_calc",
        "level": 1,
        "entryPoint": "addNums",
        "prompt": "Implement `addNums(a, b)`.",
        "starterCode": "function addNums(_a, _b) {\n  return 0;\n}\nmodule.exports = { addNums };\n",
        "solutionCode": sol,
        "visibleTests": [
            {"name": "adds positive numbers", "testCode": "assert.strictEqual(addNums(2, 3), 5);"},
        ],
        "hiddenTests": [
            {"name": "adds negative numbers", "testCode": "assert.strictEqual(addNums(-2, 5), 3);"},
        ],
        "steps": [{"explain": "Return the sum of a and b."}],
    }


def test_universal_checks_load_and_validate():
    universal = load_universal()
    assert validate_universal_checks(universal) == []
    ids = {c["id"] for c in universal}
    assert ids == {
        "U-names",
        "U-one-job",
        "U-no-input-mutation",
        "U-errors",
        "U-no-magic",
        "U-no-dead-code",
        "U-simplest",
    }
    one_job = next(c for c in universal if c["id"] == "U-one-job")
    assert one_job["severity"] == "should"
    assert one_job["mustFromLevel"] == 3


def test_validator_rejects_missing_or_empty_quality_checks():
    assert validate_quality_checks({"archetypeKey": "prg-x"})
    assert validate_quality_checks({"archetypeKey": "prg-x", "qualityChecks": []})


def test_validator_rejects_missing_fields_and_bad_severity():
    base = {"archetypeKey": "prg-x", "qualityChecks": [_valid_check()]}

    for missing_key in ("id", "check", "why", "severity", "knownBad"):
        arch = deepcopy(base)
        del arch["qualityChecks"][0][missing_key]
        assert validate_quality_checks(arch), f"Expected error when missing {missing_key}"

    bad_sev = deepcopy(base)
    bad_sev["qualityChecks"][0]["severity"] = "blocker"
    assert validate_quality_checks(bad_sev)

    bad_caught = deepcopy(base)
    bad_caught["qualityChecks"][0]["knownBad"]["caughtBy"] = "magic"
    assert validate_quality_checks(bad_caught)

    bad_id = deepcopy(base)
    bad_id["qualityChecks"][0]["id"] = "bad-id"
    assert validate_quality_checks(bad_id)


def test_validator_rejects_caught_by_test_and_invalid_accepted():
    arch = {"archetypeKey": "prg-x", "qualityChecks": [_valid_check()]}
    arch["qualityChecks"][0]["knownBad"]["caughtBy"] = "test"
    errors = validate_quality_checks(arch)
    assert any("hiddenTests" in e for e in errors)

    good_accepted = {"archetypeKey": "prg-x", "qualityChecks": [_valid_check()]}
    good_accepted["qualityChecks"][0]["accepted"] = ["[...arr].sort()", "arr.toSorted()"]
    assert validate_quality_checks(good_accepted) == []

    bad_accepted = {"archetypeKey": "prg-x", "qualityChecks": [_valid_check()]}
    bad_accepted["qualityChecks"][0]["accepted"] = []
    assert validate_quality_checks(bad_accepted)


def test_validator_rejects_duplicate_and_universal_colliding_ids():
    arch = {
        "archetypeKey": "prg-dup",
        "qualityChecks": [_valid_check("QC-dup-one"), _valid_check("QC-dup-one")],
    }
    errors = validate_quality_checks(arch)
    assert any("duplicated" in e for e in errors)

    seen: set[str] = set()
    arch1 = {"archetypeKey": "prg-a", "qualityChecks": [_valid_check("QC-shared-id")]}
    arch2 = {"archetypeKey": "prg-b", "qualityChecks": [_valid_check("QC-shared-id")]}
    assert validate_quality_checks(arch1, seen_ids=seen) == []
    errors2 = validate_quality_checks(arch2, seen_ids=seen)
    assert any("duplicated" in e for e in errors2)

    arch_u = {"archetypeKey": "prg-u", "qualityChecks": [_valid_check("U-names")]}
    errors_u = validate_quality_checks(arch_u, universal_ids={"U-names"})
    assert any("universal" in e for e in errors_u)


def test_known_bad_lint_eqeqeq_passes_and_fails():
    _require_lint_tools()

    bad_with_eqeq = {
        "id": "QC-strict-eq",
        "knownBad": {"code": "function eq(a, b) { return a == b; }", "caughtBy": "lint:eqeqeq"},
    }
    ok, msg = verify_known_bad_lint(bad_with_eqeq)
    assert ok is True
    assert msg is None

    bad_without_eqeq = {
        "id": "QC-strict-eq",
        "knownBad": {"code": "function eq(a, b) { return a === b; }", "caughtBy": "lint:eqeqeq"},
    }
    ok2, msg2 = verify_known_bad_lint(bad_without_eqeq)
    assert ok2 is False
    assert msg2 is not None and "eqeqeq" in msg2


def test_ingest_refuses_archetype_without_quality_checks(tmp_path):
    vault_dir = tmp_path / "vault"
    data_dir = tmp_path / "data"
    ws_dir = tmp_path / "ws"

    register_code_archetype(
        "PRG-T00-C02",
        {"archetypeKey": "prg-no-qc", "name": "Missing QC", "level": 1},
        vault_dir=str(vault_dir),
    )

    drill_doc = {
        "unitCode": "PRG-T00-C02",
        "drillId": "DRL-PRG-T00-C02-TEST99",
        "environment": "node-vanilla",
        "problems": [_valid_problem(archetype_key="prg-no-qc")],
    }

    with pytest.raises(AiContractError) as exc_info:
        ingest_ai_code_drill(
            drill_doc,
            data_root=str(data_dir),
            workspace_root=str(ws_dir),
            vault_dir=str(vault_dir),
        )
    assert "prg-no-qc" in str(exc_info.value)


def test_ingest_refuses_solution_failing_lint(tmp_path):
    _require_lint_tools()

    vault_dir = tmp_path / "vault"
    data_dir = tmp_path / "data"
    ws_dir = tmp_path / "ws"

    register_code_archetype(
        "PRG-T00-C02",
        {
            "archetypeKey": "prg-clean-qc",
            "name": "Clean QC",
            "level": 1,
            "qualityChecks": [_valid_check("QC-clean-one")],
        },
        vault_dir=str(vault_dir),
    )

    bad_sol = "function addNums(a, b) {\n  var total = a + b;\n  return total;\n}\nmodule.exports = { addNums };\n"
    drill_doc = {
        "unitCode": "PRG-T00-C02",
        "drillId": "DRL-PRG-T00-C02-TEST98",
        "environment": "node-vanilla",
        "problems": [_valid_problem(archetype_key="prg-clean-qc", solution_code=bad_sol)],
    }

    with pytest.raises(AiContractError) as exc_info:
        ingest_ai_code_drill(
            drill_doc,
            data_root=str(data_dir),
            workspace_root=str(ws_dir),
            vault_dir=str(vault_dir),
        )
    assert "no-var" in str(exc_info.value)


def test_all_three_prg_vaults_validate():
    errors, _skips, stats = check_all_vaults()
    assert errors == []
    assert stats["vaults"] == 3
    assert stats["archetypes"] == 19
    assert stats["universal"] == 7

    for vf in sorted(VAULT_DIR.glob("*.json")):
        data = json.loads(vf.read_text(encoding="utf-8"))
        for arch in data.get("archetypes", []):
            checks = arch.get("qualityChecks", [])
            assert 2 <= len(checks) <= 3, f"{arch['archetypeKey']} has {len(checks)} checks (expected 2-3)"
            assert any(c.get("severity") == "must" for c in checks), f"{arch['archetypeKey']} has no 'must' check"
            for c in checks:
                assert c["knownBad"]["caughtBy"] != "test"
