"""Tests for PRG workspace safety, hidden test temp execution, and drill_sync preflight."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from code_engine.ai_drill_ingest import AiContractError, check_starter_contract, run_problem_in_workspace
from code_engine.submit import run_tests_junit
from code_engine.workspace import materialize_drill_workspace
from notion_sync.drill_sync import missing_sync_fields


def _sample_prg_drill() -> dict:
    return {
        "drillId": "DRL-PRG-SAFE-01",
        "subject": "PRG",
        "unitCode": "PRG-T00-C02-U01",
        "chapterCode": "PRG-T00-C02",
        "topicCode": "PRG-T00",
        "unitTitle": "Safety Test Unit",
        "environment": "node-vanilla",
        "problems": [
            {
                "id": "Q01",
                "levelLabel": "L1",
                "category": "Problem Solving",
                "prompt": "Implement `addNums(a, b)`.",
                "entryPoint": "addNums",
                "codeType": "problem-solving",
                "starterCode": "function addNums(a, b) {\n  // TODO\n}\nmodule.exports = { addNums };\n",
                "solutionCode": "function addNums(a, b) {\n  return a + b; // SECRET_CANONICAL_MARKER\n}\nmodule.exports = { addNums };\n",
                "visibleTests": [{"name": "adds 1 + 2", "testCode": "assert.strictEqual(addNums(1, 2), 3);"}],
                "hiddenTests": [{"name": "adds negatives", "testCode": "assert.strictEqual(addNums(-4, 1), -3);"}],
                "steps": [{"explain": "Return the sum of a and b."}],
            }
        ],
    }


def test_materialize_writes_no_canonical_removes_stale_and_preserves_learner_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    drill_doc = _sample_prg_drill()

    ws_dir = tmp_path / "drills" / "workspace" / "DRL-PRG-SAFE-01"
    stale_canonical = ws_dir / ".canonical"
    stale_canonical.mkdir(parents=True)
    (stale_canonical / "Q01_addNums.js").write_text("stale secret", encoding="utf-8")

    learner_file = ws_dir / "Q01_addNums.js"
    learner_marker = "// LEARNER_EDITED_CODE\nfunction addNums(a, b) { return a + b; }\nmodule.exports = { addNums };\n"
    learner_file.write_text(learner_marker, encoding="utf-8")

    materialize_drill_workspace(drill_doc, root_dir=str(tmp_path))

    assert not stale_canonical.exists(), ".canonical directory must be removed on regeneration"
    assert learner_file.read_text(encoding="utf-8") == learner_marker, "learner file must survive regeneration"

    for p in ws_dir.rglob("*"):
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            assert "SECRET_CANONICAL_MARKER" not in text, f"solution text leaked into {p}"


def test_hidden_tests_run_from_temp_dir_and_cleanup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    drill_doc = _sample_prg_drill()
    materialize_drill_workspace(drill_doc, root_dir=str(tmp_path))

    ws_dir = tmp_path / "drills" / "workspace" / "DRL-PRG-SAFE-01"
    observed_cwds: list[Path] = []
    observed_hidden_files: list[Path] = []

    sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="suite" tests="1" failures="0">
    <testcase name="[Q01-HIDDEN-T01] adds negatives" time="0.001" />
  </testsuite>
</testsuites>"""

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        observed_cwds.append(Path(cwd))
        for arg in cmd:
            if isinstance(arg, str) and ".hidden.test." in arg:
                observed_hidden_files.append(Path(arg))
                assert Path(arg).exists(), "hidden test file must exist during execution"
        return subprocess.CompletedProcess(cmd, 0, stdout=sample_xml, stderr="")

    with patch("code_engine.submit.subprocess.run", side_effect=fake_run):
        cases = run_tests_junit(ws_dir, drill_doc)

    assert any(c.get("is_hidden") for c in cases), "hidden test cases must be reported as is_hidden=True"
    assert observed_hidden_files, "hidden test file must have been written to a temp dir"
    for hf in observed_hidden_files:
        assert not str(hf).startswith(str(ws_dir)), "hidden test must be outside workspace"
        assert not hf.exists(), "hidden test temp file must be deleted after execution"
        assert not hf.parent.exists(), "hidden test temp dir must be deleted after execution"


def test_drill_sync_preflight_allows_prg_steps_without_latex():
    drill_doc = _sample_prg_drill()
    missing = missing_sync_fields(drill_doc)
    assert missing == [], f"PRG drill with explain-only steps should pass preflight, got: {missing}"


def _secondary_export_problem() -> dict:
    return {
        "id": "Q01",
        "levelLabel": "L2",
        "category": "Trap & Edge Case",
        "prompt": "Fix `createServiceClient(name)` while preserving `baseClientProto`.",
        "entryPoint": "createServiceClient",
        "codeType": "fix-bug",
        "starterCode": (
            "const baseClientProto = { kind: 'client' };\n"
            "function createServiceClient(_name) {\n"
            "  return {};\n"
            "}\n"
            "module.exports = { baseClientProto, createServiceClient };\n"
        ),
        "solutionCode": (
            "const baseClientProto = { kind: 'client' };\n"
            "function createServiceClient(name) {\n"
            "  const c = Object.create(baseClientProto);\n"
            "  c.name = name;\n"
            "  return c;\n"
            "}\n"
            "module.exports = { baseClientProto, createServiceClient };\n"
        ),
        "visibleTests": [
            {
                "name": "preserves prototype delegation to baseClientProto",
                "testCode": (
                    "const client = createServiceClient('orders');\n"
                    "assert.strictEqual(Object.getPrototypeOf(client), baseClientProto);"
                ),
            }
        ],
        "hiddenTests": [
            {
                "name": "keeps baseClientProto.kind intact",
                "testCode": (
                    "const client = createServiceClient('billing');\n"
                    "assert.strictEqual(client.kind, baseClientProto.kind);"
                ),
            }
        ],
        "steps": [{"explain": "Use Object.create(baseClientProto)."}],
    }


def test_secondary_export_passes_in_materialized_workspace_and_hidden_tests(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prob = _secondary_export_problem()
    drill_doc = {
        "drillId": "DRL-PRG-SEC-01",
        "subject": "PRG",
        "unitCode": "PRG-T01-C01-U04",
        "chapterCode": "PRG-T01-C01",
        "topicCode": "PRG-T01",
        "unitTitle": "Secondary Export Test",
        "environment": "node-vanilla",
        "problems": [prob],
    }

    manifest = materialize_drill_workspace(drill_doc, root_dir=str(tmp_path))
    ws_dir = Path(manifest["workspaceDir"])
    (ws_dir / "Q01_createServiceClient.js").write_text(prob["solutionCode"], encoding="utf-8")

    cases = run_tests_junit(ws_dir, drill_doc, problem_id="Q01")
    assert len(cases) == 2
    assert all(c["passed"] for c in cases), f"Expected all visible+hidden tests to pass, got: {cases}"

    gate_report = run_problem_in_workspace(prob, prob["solutionCode"], environment="node-vanilla")
    assert gate_report["allPassed"] is True
    assert gate_report["hiddenPassed"] == 1


def test_typescript_secondary_export_passes_in_materialized_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prob = {
        "id": "Q01",
        "entryPoint": "createClient",
        "codeType": "implement",
        "prompt": "Implement `createClient` using `BASE_PROTO`.",
        "starterCode": (
            "export const BASE_PROTO = { kind: 'ts-client' };\n"
            "export function createClient(_name: string): { kind: string; name?: string } {\n"
            "  return { kind: 'wrong' };\n"
            "}\n"
        ),
        "solutionCode": (
            "export const BASE_PROTO = { kind: 'ts-client' };\n"
            "export function createClient(name: string): { kind: string; name: string } {\n"
            "  const c = Object.create(BASE_PROTO) as { kind: string; name: string };\n"
            "  c.name = name;\n"
            "  return c;\n"
            "}\n"
        ),
        "visibleTests": [
            {
                "name": "uses BASE_PROTO",
                "testCode": "const c = createClient('api');\nassert.strictEqual(Object.getPrototypeOf(c), BASE_PROTO);",
            }
        ],
        "hiddenTests": [
            {
                "name": "inherits kind from BASE_PROTO",
                "testCode": "const c = createClient('auth');\nassert.strictEqual(c.kind, BASE_PROTO.kind);",
            }
        ],
    }
    drill_doc = {
        "drillId": "DRL-PRG-TS-SEC-01",
        "subject": "PRG",
        "unitCode": "PRG-T01-C01-U04",
        "environment": "typescript-strict",
        "problems": [prob],
    }
    manifest = materialize_drill_workspace(drill_doc, root_dir=str(tmp_path))
    ws_dir = Path(manifest["workspaceDir"])
    (ws_dir / "Q01_createClient.ts").write_text(prob["solutionCode"], encoding="utf-8")

    cases = run_tests_junit(ws_dir, drill_doc, problem_id="Q01")
    assert len(cases) == 2
    assert all(c["passed"] for c in cases), f"Expected TS secondary export tests to pass, got: {cases}"


def test_missing_export_from_starter_fails_gate_with_clear_message():
    prob = _secondary_export_problem()
    prob["starterCode"] = (
        "const baseClientProto = { kind: 'client' };\n"
        "function createServiceClient(_name) {\n"
        "  return {};\n"
        "}\n"
        "module.exports = { createServiceClient };\n"
    )
    with pytest.raises(AiContractError) as exc_info:
        check_starter_contract("Q01", prob, environment="node-vanilla")
    msg = str(exc_info.value)
    assert "starterCode is missing export(s) referenced by tests" in msg
    assert "baseClientProto" in msg


def test_materialized_gate_rejects_unexported_symbol_used_in_tests():
    prob = _secondary_export_problem()
    prob["solutionCode"] = (
        "const baseClientProto = { kind: 'client' };\n"
        "function createServiceClient(name) {\n"
        "  const c = Object.create(baseClientProto);\n"
        "  c.name = name;\n"
        "  return c;\n"
        "}\n"
        "module.exports = { createServiceClient };\n"
    )
    prob["starterCode"] = "function createServiceClient() { return {}; }\nmodule.exports = { createServiceClient };\n"
    report = run_problem_in_workspace(prob, prob["solutionCode"], environment="node-vanilla")
    assert report["allPassed"] is False
