"""Tests for PRG Layer 2 (ESLint + TypeScript lint toolkit, workspace config, and lint_check)."""

import json
import shutil

import pytest

from code_engine.ai_drill_ingest import AiContractError, validate_lint_overrides
from code_engine.lint_check import LintToolsMissingError, get_lint_binaries, lint_code_snippet
from code_engine.workspace import materialize_drill_workspace


def _sample_drill(environment: str = "node-vanilla", lint_overrides: list | None = None) -> dict:
    doc = {
        "drillId": "DRL-PRG-LINT-01",
        "subject": "PRG",
        "unitCode": "PRG-T00-C02-U01",
        "chapterCode": "PRG-T00-C02",
        "topicCode": "PRG-T00",
        "unitTitle": "Lint Layer Test",
        "environment": environment,
        "problems": [
            {
                "id": "Q01",
                "levelLabel": "L1",
                "category": "Problem Solving",
                "prompt": "**Requirements:**\n- Implement `addNums(a, b)`.",
                "entryPoint": "addNums",
                "codeType": "problem-solving",
                "starterCode": "function addNums(_a, _b) {\n  // TODO\n  return 0;\n}\nmodule.exports = { addNums };\n",
                "visibleTests": [{"name": "adds 1 + 2", "testCode": "assert.strictEqual(addNums(1, 2), 3);"}],
                "steps": [{"explain": "Return a + b."}],
            }
        ],
    }
    if lint_overrides is not None:
        doc["lintOverrides"] = lint_overrides
    return doc


def test_generated_workspace_has_eslint_config_and_check_script(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    overrides = [{"rule": "no-param-reassign", "reason": "Debugging drill starter mutates input"}]
    drill_doc = _sample_drill(environment="node-vanilla", lint_overrides=overrides)
    materialize_drill_workspace(drill_doc, root_dir=str(tmp_path))

    ws_dir = tmp_path / "drills" / "workspace" / "DRL-PRG-LINT-01"
    eslint_cfg = ws_dir / "eslint.config.mjs"
    assert eslint_cfg.exists()
    cfg_text = eslint_cfg.read_text(encoding="utf-8")
    assert "../../../tools/lint/base.js" in cfg_text
    assert "no-param-reassign" in cfg_text

    pkg = json.loads((ws_dir / "package.json").read_text(encoding="utf-8"))
    assert "check" in pkg["scripts"]
    assert "lint" in pkg["scripts"]
    assert "tools/lint/node_modules/.bin/eslint" in pkg["scripts"]["lint"]
    assert "test_status=$?" in pkg["scripts"]["check"]
    assert "lint_status=$?" in pkg["scripts"]["check"]
    assert "check:q01" in pkg["scripts"]
    assert ".venv/bin/python" in pkg["scripts"]["review"]
    assert ".venv/bin/python" in pkg["scripts"]["submit"]
    assert "PYTHONPATH" not in pkg["scripts"]["submit"]
    assert (ws_dir / "code_engine").is_symlink()
    readme = (ws_dir / "README.md").read_text(encoding="utf-8")
    assert "npm run check:q01" in readme
    assert "npm run review -- q01" in readme
    assert "python -m code_engine.review_run" not in readme
    starter = (ws_dir / "Q01_addNums.js").read_text(encoding="utf-8")
    assert " * **Requirements:**" in starter
    assert " * -" in starter


def test_regeneration_removes_stale_eslint_config_js(tmp_path, monkeypatch):
    """Drill code may be CommonJS, so the workspace config is .mjs; an older .js config would shadow it."""
    monkeypatch.chdir(tmp_path)
    ws_dir = tmp_path / "drills" / "workspace" / "DRL-PRG-LINT-01"
    ws_dir.mkdir(parents=True)
    (ws_dir / "eslint.config.js").write_text("export default [];\n", encoding="utf-8")
    materialize_drill_workspace(_sample_drill(environment="node-vanilla"), root_dir=str(tmp_path))
    assert not (ws_dir / "eslint.config.js").exists()
    assert (ws_dir / "eslint.config.mjs").exists()


def test_generated_ts_workspace_has_typecheck_and_tsconfig(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    drill_doc = _sample_drill(environment="typescript-strict")
    materialize_drill_workspace(drill_doc, root_dir=str(tmp_path))

    ws_dir = tmp_path / "drills" / "workspace" / "DRL-PRG-LINT-01"
    assert (ws_dir / "eslint.config.mjs").exists()
    assert (ws_dir / "tsconfig.json").exists()

    pkg = json.loads((ws_dir / "package.json").read_text(encoding="utf-8"))
    assert "typecheck" in pkg["scripts"]
    assert "tools/lint/node_modules/.bin/tsc" in pkg["scripts"]["typecheck"]
    assert "npm run typecheck" in pkg["scripts"]["check"]


def test_review_run_summary_has_verdict_and_file_line_format():
    from code_engine.review_run import format_summary

    result = {
        "drillId": "DRL-PRG-TEST-01",
        "problemId": "Q01",
        "archetypeKey": "example",
        "level": 1,
        "codeHash": "sha256:test",
        "tests": {"passed": 1, "total": 1, "failed": []},
        "lint": [{"file": "Q01_example.js", "line": 3, "rule": "no-var", "message": "Use let or const."}],
        "typecheck": [],
        "checks": [],
        "passed": False,
    }
    summary = format_summary(result)
    assert "Q01_example.js:3 no-var Use let or const." in summary
    assert summary.endswith("Verdict: REVISE — fix the reported failures, then run review again.")


@pytest.mark.parametrize(
    "bad_overrides",
    [
        [{"rule": "eqeqeq", "reason": ""}],
        [{"rule": "eqeqeq", "reason": "   "}],
        [{"rule": "eqeqeq"}],
        [{"reason": "missing rule"}],
        "not-a-list",
    ],
)
def test_lint_overrides_without_reason_rejected(bad_overrides):
    with pytest.raises(AiContractError):
        validate_lint_overrides(bad_overrides)


def test_lint_overrides_valid_accepted():
    validate_lint_overrides(None)
    validate_lint_overrides([])
    validate_lint_overrides([{"rule": "no-param-reassign", "reason": "Starter mutates input on purpose"}])


def _require_lint_tools():
    if shutil.which("node") is None:
        pytest.skip("node binary not installed on PATH")
    try:
        get_lint_binaries()
    except LintToolsMissingError as exc:
        pytest.skip(str(exc))


def test_lint_check_flags_known_bad_and_passes_clean():
    _require_lint_tools()

    bad_code = "function f(a) {\n  a.x = 1;\n  return a == 1;\n}\nmodule.exports = { f };\n"
    findings = lint_code_snippet(bad_code, ext="js")
    rules = {f["rule"] for f in findings}
    assert "no-param-reassign" in rules
    assert "eqeqeq" in rules

    # Override suppresses no-param-reassign while keeping eqeqeq active
    partial_findings = lint_code_snippet(
        bad_code,
        ext="js",
        overrides=[{"rule": "no-param-reassign", "reason": "Intentional mutation in test"}],
    )
    partial_rules = {f["rule"] for f in partial_findings}
    assert "no-param-reassign" not in partial_rules
    assert "eqeqeq" in partial_rules

    clean_code = "function add(a, b) {\n  return a + b;\n}\nmodule.exports = { add };\n"
    assert lint_code_snippet(clean_code, ext="js") == []


def test_lint_check_flags_ts_explicit_any():
    _require_lint_tools()

    bad_ts = "export function echo(x: any): unknown {\n  return x;\n}\n"
    findings = lint_code_snippet(bad_ts, ext="ts")
    rules = {f["rule"] for f in findings}
    assert "@typescript-eslint/no-explicit-any" in rules

    clean_ts = "export function echo(x: unknown): unknown {\n  return x;\n}\n"
    assert lint_code_snippet(clean_ts, ext="ts") == []
