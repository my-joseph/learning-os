"""Tests for least-privilege PRG runner isolation across drills, review_run, submit, and labs."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from code_engine.lab_ingest import _run_node_tests
from code_engine.review_run import run_review
from code_engine.sandbox import (
    DEFAULT_MAX_OUTPUT_BYTES,
    build_sandbox_env,
    create_sandbox_dir,
    run_node_isolated,
    sandbox_capabilities,
)
from code_engine.submit import run_tests_junit
from code_engine.test_runner import run_tests
from code_engine.workspace import materialize_drill_workspace
from labs.common.submit_lab import run_tests_and_parse

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_sandbox_env_scrubs_secrets_and_confines_home_and_tmpdir(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "secret_notion_12345")
    monkeypatch.setenv("NOTION_DATABASE_ID", "db_secret_999")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws-secret")
    monkeypatch.setenv("NODE_OPTIONS", "--require /tmp/evil.js")

    sbx = tmp_path / "sbx"
    sbx.mkdir()
    env = build_sandbox_env(sbx, extra_env={"LAB_SRC_DIR": str(sbx / "src"), "CUSTOM_TOKEN": "must_drop"})

    assert "NOTION_TOKEN" not in env
    assert "NOTION_DATABASE_ID" not in env
    assert "ANTHROPIC_API_KEY" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "CUSTOM_TOKEN" not in env
    assert "NODE_OPTIONS" not in env
    assert env["LAB_SRC_DIR"] == str(sbx / "src")
    assert Path(env["HOME"]).resolve().is_relative_to(sbx.resolve())
    assert Path(env["TMPDIR"]).resolve().is_relative_to(sbx.resolve())
    assert env["PATH"]


def test_test_runner_contains_secret_read_outside_write_infinite_loop_and_huge_output(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "secret_notion_must_not_leak")
    monkeypatch.setenv("OPENAI_API_KEY", "secret_openai_must_not_leak")

    # 1. Secret env read & cwd/HOME/TMPDIR confinement (JS + TS)
    probe_js = """
function inspectEnv() {
  return {
    notion: process.env.NOTION_TOKEN || null,
    openai: process.env.OPENAI_API_KEY || null,
    cwd: process.cwd(),
    home: process.env.HOME || '',
    tmp: process.env.TMPDIR || '',
  };
}
module.exports = { inspectEnv };
"""
    probe_tests = [
        {
            "name": "env is scrubbed and cwd/HOME/TMPDIR are isolated",
            "testCode": (
                "const info = inspectEnv();\n"
                "assert.strictEqual(info.notion, null);\n"
                "assert.strictEqual(info.openai, null);\n"
                f"assert.ok(!info.cwd.startsWith({json.dumps(str(_REPO_ROOT.resolve()))}));\n"
                "assert.ok(info.home.length > 0 && info.tmp.length > 0);\n"
            ),
        }
    ]
    js_report = run_tests(probe_js, probe_tests, [], environment="node-vanilla", entry_point="inspectEnv")
    assert js_report["allPassed"] is True, js_report

    probe_ts = """
export function inspectTsEnv(): { notion: string | null; cwd: string } {
  return {
    notion: process.env.NOTION_TOKEN ?? null,
    cwd: process.cwd(),
  };
}
"""
    ts_tests = [
        {
            "name": "ts runner scrubs secrets and isolates cwd",
            "testCode": (
                "const info = inspectTsEnv();\n"
                "assert.strictEqual(info.notion, null);\n"
                f"assert.ok(!info.cwd.startsWith({json.dumps(str(_REPO_ROOT.resolve()))}));\n"
            ),
        }
    ]
    ts_report = run_tests(probe_ts, ts_tests, [], environment="typescript-strict", entry_point="inspectTsEnv")
    assert ts_report["allPassed"] is True, ts_report

    # 2. Write outside temp dir is blocked
    escape_target = tmp_path / "outside_escape.txt"
    escape_code = f"""
const fs = require('fs');
function tryEscape() {{
  fs.writeFileSync({json.dumps(str(escape_target))}, 'pwned');
  return true;
}}
module.exports = {{ tryEscape }};
"""
    escape_report = run_tests(
        escape_code,
        [{"name": "cannot write outside temp dir", "testCode": "assert.strictEqual(tryEscape(), true);"}],
        [],
        environment="node-vanilla",
        entry_point="tryEscape",
    )
    assert escape_report["allPassed"] is False
    assert not escape_target.exists(), "Learner code must not be able to write outside its temp sandbox"

    # 3. Infinite loop is terminated promptly on timeout
    loop_code = "function spin() { while (true) {} }\nmodule.exports = { spin };\n"
    t0 = time.monotonic()
    loop_report = run_tests(
        loop_code,
        [{"name": "infinite loop", "testCode": "spin();"}],
        [],
        timeout_sec=1.0,
        environment="node-vanilla",
        entry_point="spin",
    )
    elapsed = time.monotonic() - t0
    assert loop_report["allPassed"] is False
    assert elapsed < 5.0, f"Infinite loop took too long to kill: {elapsed:.2f}s"
    assert any("Timeout" in r.get("name", "") for r in loop_report["visibleResults"]), loop_report

    # 4. Huge output is bounded and contained
    spam_code = """
function flood() {
  const chunk = 'X'.repeat(4096);
  for (let i = 0; i < 2000; i++) {
    console.log(chunk);
  }
  return true;
}
module.exports = { flood };
"""
    spam_report = run_tests(
        spam_code,
        [{"name": "huge stdout", "testCode": "assert.strictEqual(flood(), true);"}],
        [],
        timeout_sec=5.0,
        environment="node-vanilla",
        entry_point="flood",
    )
    assert spam_report["allPassed"] is False
    assert len(json.dumps(spam_report)) < DEFAULT_MAX_OUTPUT_BYTES
    assert any("Output limit" in r.get("name", "") for r in spam_report["visibleResults"]), spam_report


def test_submit_and_review_run_confine_writes_to_temp_copy_and_scrub_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "secret_submit_token")
    monkeypatch.chdir(tmp_path)

    outside_file = tmp_path / "repo_sentinel.txt"
    solution = f"""
const fs = require('fs');
function checkIsolation() {{
  fs.writeFileSync('ephemeral_local_write.txt', 'temp-only');
  let blockedOutside = false;
  try {{
    fs.writeFileSync({json.dumps(str(outside_file))}, 'escaped');
  }} catch (_err) {{
    blockedOutside = true;
  }}
  return {{
    hasToken: Boolean(process.env.NOTION_TOKEN),
    blockedOutside,
  }};
}}
module.exports = {{ checkIsolation }};
"""
    drill_doc = {
        "drillId": "DRL-PRG-ISO-01",
        "subject": "PRG",
        "unitCode": "PRG-T00-C02-U01",
        "chapterCode": "PRG-T00-C02",
        "topicCode": "PRG-T00",
        "unitTitle": "Isolation Drill",
        "environment": "node-vanilla",
        "problems": [
            {
                "id": "Q01",
                "level": 1,
                "levelLabel": "L1",
                "category": "Core",
                "entryPoint": "checkIsolation",
                "codeType": "implement",
                "prompt": "Implement `checkIsolation()`.",
                "starterCode": solution,
                "solutionCode": solution,
                "visibleTests": [
                    {
                        "name": "runs in isolated temp copy without secrets",
                        "testCode": (
                            "const res = checkIsolation();\n"
                            "assert.strictEqual(res.hasToken, false);\n"
                            "assert.strictEqual(res.blockedOutside, true);\n"
                        ),
                    }
                ],
                "hiddenTests": [
                    {
                        "name": "hidden suite also sees no secret and blocks outside writes",
                        "testCode": (
                            "const res = checkIsolation();\n"
                            "assert.strictEqual(res.hasToken, false);\n"
                            "assert.strictEqual(res.blockedOutside, true);\n"
                        ),
                    }
                ],
                "steps": [{"explain": "Verify isolation."}],
            }
        ],
    }

    data_dir = tmp_path / "drills" / "data" / "PRG-T00-C02-U01"
    data_dir.mkdir(parents=True)
    (data_dir / "DRL-PRG-ISO-01.json").write_text(json.dumps(drill_doc), encoding="utf-8")

    manifest = materialize_drill_workspace(drill_doc, root_dir=str(tmp_path))
    ws_dir = Path(manifest["workspaceDir"])

    # 1. submit.run_tests_junit
    cases = run_tests_junit(ws_dir, drill_doc, problem_id="Q01")
    assert len(cases) == 2
    assert all(c["passed"] for c in cases), cases
    assert not outside_file.exists(), "Outside file must never be created"
    assert not (ws_dir / "ephemeral_local_write.txt").exists(), (
        "Relative writes must stay inside the per-run temp copy, not the real workspace"
    )

    # 2. review_run.run_review
    review = run_review(
        "DRL-PRG-ISO-01",
        "Q01",
        data_root=tmp_path / "drills" / "data",
        workspace_root=tmp_path / "drills" / "workspace",
    )
    assert review["tests"] == {"passed": 2, "total": 2, "failed": []}
    assert not outside_file.exists()
    assert not (ws_dir / "ephemeral_local_write.txt").exists()


def test_lab_runners_isolate_env_and_writes(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "secret_lab_token")

    outside_file = tmp_path / "lab_escape.txt"
    lab_dir = tmp_path / "labs" / "LAB-PRG-ISO-01"
    src_dir = lab_dir / "src"
    tests_dir = lab_dir / "tests"
    hidden_dir = tmp_path / "labs" / "_reference" / "LAB-PRG-ISO-01" / "hidden"
    src_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)
    hidden_dir.mkdir(parents=True)

    (lab_dir / "package.json").write_text('{"name": "lab-iso", "type": "module"}\n', encoding="utf-8")
    base_js_uri = (_REPO_ROOT / "tools" / "lint" / "base.js").resolve().as_uri()
    (lab_dir / "eslint.config.js").write_text(
        f"import {{ prgConfig }} from {json.dumps(base_js_uri)};\nexport default prgConfig();\n",
        encoding="utf-8",
    )
    (lab_dir / "lab.config.json").write_text(
        json.dumps(
            {
                "labId": "LAB-PRG-ISO-01",
                "title": "Isolation Lab",
                "chapterCode": "PRG-T01-C01",
                "unitsUsed": ["PRG-T01-C01-U02"],
                "level": 2,
                "testCommand": "node --experimental-strip-types --test --test-reporter=junit tests/*.test.ts",
                "milestones": [
                    {
                        "id": "M1",
                        "title": "Isolation check",
                        "visibleTests": "tests/m1_*.test.ts",
                        "qualityChecks": ["U-names"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (src_dir / "probe.ts").write_text(
        f"""import fs from "node:fs";
export function runProbe(): {{ hasToken: boolean; blockedOutside: boolean }} {{
  fs.writeFileSync("ephemeral_lab_write.txt", "temp-only");
  let blockedOutside = false;
  try {{
    fs.writeFileSync({json.dumps(str(outside_file))}, "escaped");
  }} catch {{
    blockedOutside = true;
  }}
  return {{
    hasToken: Boolean(process.env.NOTION_TOKEN),
    blockedOutside,
  }};
}}
""",
        encoding="utf-8",
    )
    test_body = """import assert from "node:assert/strict";
import test from "node:test";
const srcDir = process.env.LAB_SRC_DIR || "../src";
const { runProbe } = await import(`${srcDir}/probe.ts`);
test("m1 probe stays isolated", () => {
  const res = runProbe();
  assert.equal(res.hasToken, false);
  assert.equal(res.blockedOutside, true);
});
"""
    vis_test = tests_dir / "m1_probe.test.ts"
    vis_test.write_text(test_body, encoding="utf-8")
    (hidden_dir / "m1_hidden.test.ts").write_text(test_body, encoding="utf-8")

    # 1. lab_ingest._run_node_tests
    ingest_cases = _run_node_tests([vis_test], lab_dir, src_dir)
    assert len(ingest_cases) == 1 and ingest_cases[0]["passed"], ingest_cases

    # 2. labs/common/submit_lab.run_tests_and_parse
    lab_cfg = json.loads((lab_dir / "lab.config.json").read_text(encoding="utf-8"))
    submit_res = run_tests_and_parse(lab_dir, lab_cfg)
    assert submit_res["success"] is True, submit_res
    assert len(submit_res["testcases"]) == 1 and submit_res["testcases"][0]["passed"]

    # 3. code_engine.review_run (lab path with visible + hidden suites)
    lab_review = run_review("LAB-PRG-ISO-01", "M1", labs_root=tmp_path / "labs")
    assert lab_review["tests"] == {"passed": 2, "total": 2, "failed": []}, lab_review

    assert not outside_file.exists()
    assert not (lab_dir / "ephemeral_lab_write.txt").exists()
    assert not (hidden_dir / "ephemeral_lab_write.txt").exists()


def test_react_dom_runner_scrubs_secrets_and_does_not_write_under_tools_lint(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "secret_react_token")
    tools_lint = _REPO_ROOT / "tools" / "lint"
    before_entries = {p.name for p in tools_lint.iterdir()}

    outside_file = tmp_path / "react_escape.txt"
    component = """import React from 'react';
export function SecretProbe() {
  const token = process.env.NOTION_TOKEN || 'none';
  return <output data-testid="probe">{token}</output>;
}
"""
    visible = [
        {
            "name": "react runner scrubs NOTION_TOKEN",
            "testCode": "render(<SecretProbe />); assert.equal(screen.getByTestId('probe').textContent, 'none');",
        }
    ]
    report = run_tests(component, visible, [], timeout_sec=15.0, environment="react-dom", entry_point="SecretProbe")
    assert report["allPassed"] is True, report

    after_entries = {p.name for p in tools_lint.iterdir()}
    assert after_entries == before_entries, "React runner must not create temp directories inside tools/lint"

    # On macOS (Seatbelt active), React/Vitest writes outside the temp sandbox are also OS-blocked.
    if sandbox_capabilities()["macos_seatbelt"]:
        escape_component = f"""import React from 'react';
import fs from 'node:fs';
export function BadWriter() {{
  fs.writeFileSync({json.dumps(str(outside_file))}, 'escaped');
  return <span />;
}}
"""
        bad_report = run_tests(
            escape_component,
            [{"name": "blocked write", "testCode": "render(<BadWriter />);"}],
            [],
            timeout_sec=15.0,
            environment="react-dom",
            entry_point="BadWriter",
        )
        assert bad_report["allPassed"] is False
        assert not outside_file.exists()


def test_network_blocked_when_os_network_sandbox_available():
    caps = sandbox_capabilities()
    if not (caps["macos_seatbelt"] or caps["linux_unshare_net"]):
        return
    with create_sandbox_dir(prefix="prg_net_probe_") as sbx_str:
        sbx = Path(sbx_str)
        work = sbx / "work"
        work.mkdir()
        (work / "net.js").write_text(
            "const net = require('node:net');\n"
            "const s = net.connect({ host: '1.1.1.1', port: 80 });\n"
            "s.on('error', (err) => { console.log('NET_BLOCKED:' + err.code); process.exit(0); });\n"
            "s.on('connect', () => { console.log('NET_ALLOWED'); s.destroy(); process.exit(1); });\n",
            encoding="utf-8",
        )
        res = run_node_isolated(["net.js"], cwd=work, sandbox_root=sbx, timeout_sec=5.0)
        assert res.returncode == 0, f"Expected network error exit 0, got {res}"
        assert "NET_BLOCKED:" in res.stdout, res
        assert "NET_ALLOWED" not in res.stdout
        if sys.platform == "darwin":
            assert "EPERM" in res.stdout
