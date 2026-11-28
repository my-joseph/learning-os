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


def test_b01_symlinks_rejected_in_workspace_lab_and_review_run(tmp_path):
    import pytest

    from code_engine.sandbox import stage_lab_copy, stage_workspace_copy

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_secret = outside_dir / "secret.txt"
    outside_secret.write_text("TOP_SECRET_B01_VALUE", encoding="utf-8")

    # 1. stage_workspace_copy must reject a symlinked src_dir itself
    ws_link = tmp_path / "ws_link"
    ws_link.symlink_to(outside_dir)
    with pytest.raises(ValueError, match="symlink"):
        stage_workspace_copy(ws_link, tmp_path / "dst_ws")

    # 2. stage_lab_copy must reject symlinked test_files or test_files outside tests/
    lab_dir = tmp_path / "labs" / "LAB-PRG-B01-01"
    (lab_dir / "src").mkdir(parents=True)
    (lab_dir / "tests").mkdir(parents=True)
    (lab_dir / "src" / "mod.ts").write_text("export const x = 1;\n", encoding="utf-8")
    symlink_test = lab_dir / "tests" / "m1_leak.test.ts"
    symlink_test.symlink_to(outside_secret)
    with pytest.raises(ValueError, match="symlink"):
        stage_lab_copy(lab_dir, lab_dir / "src", [symlink_test], tmp_path / "dst_lab")

    # 3. review_run must reject visibleTests path traversal outside lab_dir/tests
    symlink_test.unlink()
    (lab_dir / "lab.config.json").write_text(
        json.dumps(
            {
                "labId": "LAB-PRG-B01-01",
                "title": "B01 Lab",
                "chapterCode": "PRG-T01-C01",
                "unitsUsed": ["PRG-T01-C01-U01"],
                "level": 1,
                "milestones": [
                    {
                        "id": "M1",
                        "title": "M1",
                        "visibleTests": "../../outside/secret.txt",
                        "qualityChecks": ["U-names"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    hidden_dir = tmp_path / "labs" / "_reference" / "LAB-PRG-B01-01" / "hidden"
    hidden_dir.mkdir(parents=True)
    (hidden_dir / "m1_h.test.ts").write_text('import test from "node:test"; test("ok", () => {});\n', encoding="utf-8")
    with pytest.raises(ValueError):
        run_review("LAB-PRG-B01-01", "M1", labs_root=tmp_path / "labs")

    # 4. review_run must reject symlinked lab src file before reading src_text
    (lab_dir / "src" / "leak.ts").symlink_to(outside_secret)
    with pytest.raises(ValueError, match="symlink"):
        run_review("LAB-PRG-B01-01", "M1", labs_root=tmp_path / "labs")
    (lab_dir / "src" / "leak.ts").unlink()

    # 5. review_run must reject symlinked drill source file before reading src_text
    drill_doc = {
        "drillId": "DRL-PRG-B01-01",
        "subject": "PRG",
        "unitCode": "PRG-T00-C02-U01",
        "chapterCode": "PRG-T00-C02",
        "topicCode": "PRG-T00",
        "unitTitle": "B01 Drill",
        "environment": "node-vanilla",
        "problems": [
            {
                "id": "Q01",
                "level": 1,
                "entryPoint": "solve",
                "prompt": "Solve.",
                "starterCode": "function solve() { return 1; }\nmodule.exports = { solve };\n",
                "solutionCode": "function solve() { return 1; }\nmodule.exports = { solve };\n",
                "visibleTests": [{"name": "ok", "testCode": "assert.strictEqual(solve(), 1);"}],
                "hiddenTests": [],
                "steps": [{"explain": "ok"}],
            }
        ],
    }
    data_dir = tmp_path / "drills" / "data" / "PRG-T00-C02-U01"
    data_dir.mkdir(parents=True)
    (data_dir / "DRL-PRG-B01-01.json").write_text(json.dumps(drill_doc), encoding="utf-8")
    ws_dir = tmp_path / "drills" / "workspace" / "DRL-PRG-B01-01"
    ws_dir.mkdir(parents=True)
    (ws_dir / "Q01_solve.js").symlink_to(outside_secret)
    with pytest.raises(ValueError, match="symlink"):
        run_review(
            "DRL-PRG-B01-01",
            "Q01",
            data_root=tmp_path / "drills" / "data",
            workspace_root=tmp_path / "drills" / "workspace",
        )


def test_b02_seatbelt_denies_worktree_main_checkout_home_and_repo_secrets(tmp_path, monkeypatch):
    from code_engine.sandbox import _build_seatbelt_profile, _default_deny_read_paths

    # Simulate a git worktree whose main checkout holds .env, .env.local, progress, drills/data, labs/_reference
    main_repo = tmp_path / "main_repo"
    wt_repo = tmp_path / "wt_repo"
    git_wt_dir = main_repo / ".git" / "worktrees" / "wt_repo"
    git_wt_dir.mkdir(parents=True)
    wt_repo.mkdir(parents=True)
    (wt_repo / ".git").write_text(f"gitdir: {git_wt_dir}\n", encoding="utf-8")
    (main_repo / ".env").write_text("NOTION_TOKEN=secret_from_main_env\n", encoding="utf-8")
    (main_repo / ".env.local").write_text("EXTRA_SECRET=secret_from_env_local\n", encoding="utf-8")
    (main_repo / "drills" / "data" / "PRG-T01").mkdir(parents=True)
    secret_drill = main_repo / "drills" / "data" / "PRG-T01" / "DRL-SECRET.json"
    secret_drill.write_text('{"solutionCode": "SECRET_SOLUTION"}', encoding="utf-8")
    (main_repo / "labs" / "_reference" / "LAB-SECRET" / "src").mkdir(parents=True)
    secret_ref = main_repo / "labs" / "_reference" / "LAB-SECRET" / "src" / "ref.ts"
    secret_ref.write_text("export const secret = 'SECRET_REF';\n", encoding="utf-8")

    monkeypatch.setenv("LEARNINGOS_ROOT", str(wt_repo))
    denied = _default_deny_read_paths()
    denied_strs = {str(p) for p in denied}
    main_real = main_repo.resolve()
    for rel in (
        ".env",
        ".env.local",
        "progress",
        "pilot/progress",
        "sources",
        "issues",
        "drills/data",
        "labs/_reference",
    ):
        assert str(main_real / rel) in denied_strs, f"Missing main-checkout deny path: {rel} in {denied_strs}"
    real_home = Path.home().resolve()
    for home_rel in (".ssh", ".aws", ".gnupg", ".npmrc"):
        assert str(real_home / home_rel) in denied_strs, f"Missing home deny path: {home_rel}"

    # Seatbelt profile must use file-read* (blocking both read and stat metadata probes)
    profile = _build_seatbelt_profile(tmp_path / "sbx", deny_read_paths=denied)
    assert "(deny file-read*" in profile
    assert "(deny file-read-data" not in profile

    # On macOS, verify Vitest (use_node_permission=False) cannot read or stat main-checkout secrets or ~/.ssh
    if sandbox_capabilities()["macos_seatbelt"]:
        probes = [
            str(main_real / ".env"),
            str(main_real / ".env.local"),
            str(secret_drill.resolve()),
            str(secret_ref.resolve()),
            str(real_home / ".ssh"),
        ]
        component = f"""import React from 'react';
import fs from 'node:fs';
export function SecretReader() {{
  const targets = {json.dumps(probes)};
  const results: string[] = [];
  for (const t of targets) {{
    try {{
      fs.statSync(t);
      results.push('STAT_OK:' + t);
    }} catch (e: any) {{
      results.push('STAT_BLOCKED:' + (e?.code || 'ERR'));
    }}
    try {{
      fs.readFileSync(t, 'utf8');
      results.push('READ_OK:' + t);
    }} catch (e: any) {{
      results.push('READ_BLOCKED:' + (e?.code || 'ERR'));
    }}
  }}
  return <output data-testid="res">{{results.join('|')}}</output>;
}}
"""
        visible = [
            {
                "name": "cannot read or stat sensitive paths under vitest",
                "testCode": (
                    "render(<SecretReader />);\n"
                    "const text = screen.getByTestId('res').textContent || '';\n"
                    "assert.ok(!text.includes('STAT_OK:'), 'statSync must be blocked: ' + text);\n"
                    "assert.ok(!text.includes('READ_OK:'), 'readFileSync must be blocked: ' + text);\n"
                ),
            }
        ]
        report = run_tests(
            component, visible, [], timeout_sec=20.0, environment="react-dom", entry_point="SecretReader"
        )
        assert report["allPassed"] is True, report


def test_b03_layer2_ignores_learner_eslint_config_and_isolates_lint_check_ingest_submit_lab(tmp_path, monkeypatch):
    import code_engine.ai_drill_ingest as ingest_mod
    import code_engine.lint_check as lint_mod

    monkeypatch.setenv("NOTION_TOKEN", "secret_b03_token")

    # 1. Drill review_run must never execute learner-modified eslint.config.mjs
    sentinel_drill = tmp_path / "pwned_drill_eslint.txt"
    drill_doc = {
        "drillId": "DRL-PRG-B03-01",
        "subject": "PRG",
        "unitCode": "PRG-T00-C02-U01",
        "chapterCode": "PRG-T00-C02",
        "topicCode": "PRG-T00",
        "unitTitle": "B03 Drill",
        "environment": "node-vanilla",
        "problems": [
            {
                "id": "Q01",
                "level": 1,
                "entryPoint": "doubleVal",
                "prompt": "Double value.",
                "starterCode": "function doubleVal(n) { return n * 2; }\nmodule.exports = { doubleVal };\n",
                "solutionCode": "function doubleVal(n) { return n * 2; }\nmodule.exports = { doubleVal };\n",
                "visibleTests": [{"name": "doubles", "testCode": "assert.strictEqual(doubleVal(3), 6);"}],
                "hiddenTests": [],
                "steps": [{"explain": "Multiply by 2."}],
            }
        ],
    }
    data_dir = tmp_path / "drills" / "data" / "PRG-T00-C02-U01"
    data_dir.mkdir(parents=True)
    (data_dir / "DRL-PRG-B03-01.json").write_text(json.dumps(drill_doc), encoding="utf-8")
    manifest = materialize_drill_workspace(drill_doc, root_dir=str(tmp_path))
    ws_dir = Path(manifest["workspaceDir"])
    # Tamper with workspace eslint.config.mjs to write sentinel & throw custom error
    (ws_dir / "eslint.config.mjs").write_text(
        f"import fs from 'node:fs';\n"
        f"try {{ fs.writeFileSync({json.dumps(str(sentinel_drill))}, 'pwned'); }} catch {{}}\n"
        f"throw new Error('LEARNER_ESLINT_CONFIG_EXECUTED');\n",
        encoding="utf-8",
    )
    rev = run_review(
        "DRL-PRG-B03-01",
        "Q01",
        data_root=tmp_path / "drills" / "data",
        workspace_root=tmp_path / "drills" / "workspace",
    )
    assert not sentinel_drill.exists(), "Learner eslint.config.mjs must never be executed"
    assert rev["tests"] == {"passed": 1, "total": 1, "failed": []}
    assert rev["lint"] == []

    # 2. Lab review_run must never execute learner-modified labs/<ID>/eslint.config.js
    sentinel_lab = tmp_path / "pwned_lab_eslint.txt"
    lab_dir = tmp_path / "labs" / "LAB-PRG-B03-01"
    (lab_dir / "src").mkdir(parents=True)
    (lab_dir / "tests").mkdir(parents=True)
    hidden_dir = tmp_path / "labs" / "_reference" / "LAB-PRG-B03-01" / "hidden"
    hidden_dir.mkdir(parents=True)
    (lab_dir / "package.json").write_text('{"name":"b03","type":"module"}\n', encoding="utf-8")
    (lab_dir / "eslint.config.js").write_text(
        f"import fs from 'node:fs';\n"
        f"try {{ fs.writeFileSync({json.dumps(str(sentinel_lab))}, 'pwned'); }} catch {{}}\n"
        f"throw new Error('LEARNER_LAB_ESLINT_EXECUTED');\n",
        encoding="utf-8",
    )
    (lab_dir / "src" / "calc.ts").write_text(
        "export function addOne(n: number): number {\n  return n + 1;\n}\n", encoding="utf-8"
    )
    test_src = (
        'import assert from "node:assert/strict";\n'
        'import test from "node:test";\n'
        'const srcDir = process.env.LAB_SRC_DIR || "../src";\n'
        "const { addOne } = await import(`${srcDir}/calc.ts`);\n"
        'test("m1 addOne", () => { assert.equal(addOne(2), 3); });\n'
    )
    (lab_dir / "tests" / "m1_calc.test.ts").write_text(test_src, encoding="utf-8")
    (hidden_dir / "m1_hidden.test.ts").write_text(test_src, encoding="utf-8")
    # Also include a malicious testCommand in lab.config.json to verify submit_lab ignores it
    sentinel_cmd = tmp_path / "pwned_submit_lab_cmd.txt"
    lab_cfg = {
        "labId": "LAB-PRG-B03-01",
        "title": "B03 Lab",
        "chapterCode": "PRG-T01-C01",
        "unitsUsed": ["PRG-T01-C01-U01"],
        "level": 1,
        "testCommand": f"touch {sentinel_cmd} && echo pwned",
        "milestones": [{"id": "M1", "title": "M1", "visibleTests": "tests/m1_*.test.ts", "qualityChecks": ["U-names"]}],
    }
    (lab_dir / "lab.config.json").write_text(json.dumps(lab_cfg), encoding="utf-8")

    lab_rev = run_review("LAB-PRG-B03-01", "M1", labs_root=tmp_path / "labs")
    assert not sentinel_lab.exists(), "Learner lab eslint.config.js must never be executed"
    assert lab_rev["tests"] == {"passed": 2, "total": 2, "failed": []}
    assert lab_rev["lint"] == []

    # 3. submit_lab.run_tests_and_parse must ignore learner testCommand shell fallback
    submit_res = run_tests_and_parse(lab_dir, lab_cfg)
    assert not sentinel_cmd.exists(), "submit_lab must never execute learner testCommand via /bin/sh -c"
    assert submit_res["success"] is True, submit_res
    assert len(submit_res["testcases"]) == 1 and submit_res["testcases"][0]["passed"]

    # 4. lint_check and ai_drill_ingest._check_code_compiles must route through sandbox (never raw subprocess.run)
    isolated_calls: list[str] = []
    orig_run_isolated = lint_mod.run_isolated if hasattr(lint_mod, "run_isolated") else None
    assert orig_run_isolated is not None, "lint_check must use code_engine.sandbox.run_isolated"

    def spy_run_isolated(*args, **kwargs):
        isolated_calls.append("lint_check")
        return orig_run_isolated(*args, **kwargs)

    monkeypatch.setattr(lint_mod, "run_isolated", spy_run_isolated)
    assert lint_mod.lint_code_snippet("export const val = 1;\n", ext="ts") == []
    assert lint_mod.typecheck_code_snippet("export const val: number = 1;\n", ext="ts") == []
    assert len(isolated_calls) == 2

    orig_run_node = ingest_mod.run_node_isolated if hasattr(ingest_mod, "run_node_isolated") else None
    assert orig_run_node is not None, "ai_drill_ingest must use code_engine.sandbox.run_node_isolated"
    node_calls: list[str] = []

    def spy_run_node(*args, **kwargs):
        node_calls.append("ingest_syntax")
        return orig_run_node(*args, **kwargs)

    monkeypatch.setattr(ingest_mod, "run_node_isolated", spy_run_node)
    ingest_mod._check_code_compiles("Q01", "starterCode", "const x = 1;\n", environment="node-vanilla")
    assert node_calls == ["ingest_syntax"]


def test_b04_process_group_kills_sigterm_ignoring_grandchild_and_cleans_up_on_sigterm(tmp_path):
    import os
    import shutil
    import signal
    import subprocess

    from code_engine.sandbox import run_isolated
    from tests.test_sandbox_sigterm_race import wait_for_pid_absent

    # 1. Grandchild ignoring SIGTERM survives leader exit unless process group is swept with SIGKILL
    with create_sandbox_dir(prefix="prg_b04_gc_") as sbx_str:
        sbx = Path(sbx_str)
        work = sbx / "work"
        work.mkdir()
        pid_file = work / "grandchild.pid"
        # Shell spawns a background Python/sh child trapping SIGTERM, writes its PID, then leader exits immediately
        script = f"sh -c 'trap \"\" TERM; sleep 60' & echo $! > {json.dumps(str(pid_file))}; exit 0"
        res = run_isolated(
            ["/bin/sh", "-c", script],
            cwd=work,
            sandbox_root=sbx,
            timeout_sec=5.0,
            use_node_permission=False,
        )
        assert res.returncode == 0
        gc_pid = int(pid_file.read_text(encoding="utf-8").strip())
        gc_state, gc_detail = wait_for_pid_absent(gc_pid, timeout_sec=2.0)
        try:
            assert gc_state != "live", (
                f"Grandchild PID {gc_pid} survived as a LIVE ORPHAN after run_isolated returned "
                f"(state={gc_state}/{gc_detail})"
            )
            assert gc_state != "zombie", (
                f"Grandchild PID {gc_pid} remained an unreaped ZOMBIE after run_isolated returned "
                f"(state={gc_state}/{gc_detail})"
            )
            assert gc_state == "absent", f"Grandchild PID {gc_pid} unexpected state {(gc_state, gc_detail)}"
        finally:
            if gc_state == "live":
                try:
                    os.kill(gc_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    # 2. SIGTERM sent to parent Python process must kill start_new_session child group AND clean temp sandbox dir
    marker_file = tmp_path / "b04_child_info.json"
    driver = f"""
import json, sys, time
from pathlib import Path
from code_engine.sandbox import create_sandbox_dir, run_isolated
with create_sandbox_dir(prefix="prg_b04_sigterm_") as sbx_str:
    sbx = Path(sbx_str)
    work = sbx / "work"
    work.mkdir()
    child_pid_file = work / "child.pid"
    tmp_pid_file = work / "child.pid.tmp"
    Path({json.dumps(str(marker_file))}).write_text(json.dumps({{"sbx": str(sbx), "pid_file": str(child_pid_file)}}))
    run_isolated(
        [
            "/bin/sh",
            "-c",
            f"trap '' TERM; echo $$ > {{str(tmp_pid_file)!r}} && mv {{str(tmp_pid_file)!r}} {{str(child_pid_file)!r}}; exec sleep 60",
        ],
        cwd=work,
        sandbox_root=sbx,
        timeout_sec=30.0,
        use_node_permission=False,
    )
"""
    parent = subprocess.Popen(
        [sys.executable, "-c", driver],
        cwd=str(_REPO_ROOT),
        start_new_session=True,
    )
    info = None
    child_pid = None
    try:
        wait_until = time.monotonic() + 5.0
        while time.monotonic() < wait_until:
            if marker_file.is_file():
                info = json.loads(marker_file.read_text(encoding="utf-8"))
                pf = Path(info["pid_file"])
                if pf.is_file() and pf.read_text(encoding="utf-8").strip():
                    child_pid = int(pf.read_text(encoding="utf-8").strip())
                    break
            time.sleep(0.05)
        assert info is not None and child_pid is not None, "Child process did not start in time"

        # Simulate Studio killProcessTree sending SIGTERM to parent Python process group
        os.killpg(parent.pid, signal.SIGTERM)
        driver_rc = parent.wait(timeout=5.0)

        child_state, child_detail = wait_for_pid_absent(child_pid, timeout_sec=2.0)
        sbx_exists = Path(info["sbx"]).exists()
        assert child_state != "live", (
            f"start_new_session child PID {child_pid} survived as a LIVE ORPHAN when parent got SIGTERM "
            f"(state={child_state}/{child_detail}, driver_rc={driver_rc}, sbx_exists={sbx_exists})"
        )
        assert child_state != "zombie", (
            f"start_new_session child PID {child_pid} remained an unreaped ZOMBIE when parent got SIGTERM "
            f"(state={child_state}/{child_detail}, driver_rc={driver_rc}, sbx_exists={sbx_exists})"
        )
        assert child_state == "absent", (
            f"start_new_session child PID {child_pid} had unexpected state {(child_state, child_detail)} "
            f"(driver_rc={driver_rc}, sbx_exists={sbx_exists})"
        )
        assert driver_rc == 128 + signal.SIGTERM, (
            f"Expected driver exit {128 + signal.SIGTERM} from SIGTERM handler, "
            f"got {driver_rc} (sbx_exists={sbx_exists})"
        )
        assert not sbx_exists, (
            f"Sandbox temp dir {info['sbx']} leaked when parent got SIGTERM "
            f"(driver_rc={driver_rc}, child_state={child_state}/{child_detail})"
        )
    finally:
        if parent.poll() is None:
            try:
                os.killpg(parent.pid, signal.SIGKILL)
            except OSError:
                pass
            try:
                parent.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                pass
        if child_pid is not None:
            try:
                os.killpg(child_pid, signal.SIGKILL)
            except OSError:
                try:
                    os.kill(child_pid, signal.SIGKILL)
                except OSError:
                    pass
        if info is not None and Path(info["sbx"]).exists():
            shutil.rmtree(info["sbx"], ignore_errors=True)


def test_b05_fail_closed_when_sandbox_unavailable_and_react_lab_submit(tmp_path, monkeypatch, capsys):
    import shutil

    import pytest

    import code_engine.sandbox as sbx_mod
    from code_engine.sandbox import SandboxUnavailableError, run_isolated
    from labs.common.submit_lab import evaluate_milestones

    # 1. Fail closed when use_node_permission=True and _supports_node_permission() is False
    with create_sandbox_dir(prefix="prg_b05_node_") as sbx_str:
        sbx = Path(sbx_str)
        monkeypatch.setattr(sbx_mod, "_supports_node_permission", lambda: False)
        with pytest.raises(SandboxUnavailableError):
            run_node_isolated(["-e", "process.exit(0)"], cwd=sbx, sandbox_root=sbx)

    # 2. On macOS, fail closed when Seatbelt is unavailable
    if sys.platform == "darwin":
        with create_sandbox_dir(prefix="prg_b05_sb_") as sbx_str:
            sbx = Path(sbx_str)
            monkeypatch.setattr(sbx_mod, "_supports_node_permission", lambda: True)
            monkeypatch.setattr(sbx_mod, "_supports_macos_seatbelt", lambda: False)
            with pytest.raises(SandboxUnavailableError):
                run_isolated(["/usr/bin/true"], cwd=sbx, sandbox_root=sbx, use_node_permission=False)

    # 3. On Linux without unshare/Seatbelt, log explicit degradation warning and populate degraded_reasons
    with create_sandbox_dir(prefix="prg_b05_linux_") as sbx_str:
        sbx = Path(sbx_str)
        monkeypatch.setattr(sbx_mod.sys, "platform", "linux")
        monkeypatch.setattr(sbx_mod, "_supports_macos_seatbelt", lambda: False)
        monkeypatch.setattr(sbx_mod, "_supports_linux_unshare_net", lambda: False)
        monkeypatch.setattr(sbx_mod, "_WARNED_DEGRADATIONS", set())
        res = run_isolated(["/bin/echo", "ok"], cwd=sbx, sandbox_root=sbx, use_node_permission=False)
        assert res.returncode == 0
        assert res.degraded_reasons, "Linux degradation must be recorded on SandboxResult"
        err = capsys.readouterr().err
        assert "WARNING" in err or "degraded" in err.lower(), f"Expected explicit stderr warning, got: {err!r}"

    # Reset mocks before running real React lab submission test
    monkeypatch.undo()

    # 4. Mixed .test.ts + .test.tsx React lab (LAB-PRG-T02-C01-01) submits cleanly across M1-M4
    src_lab = _REPO_ROOT / "labs" / "LAB-PRG-T02-C01-01"
    ref_src = _REPO_ROOT / "labs" / "_reference" / "LAB-PRG-T02-C01-01" / "src"
    lab_copy = tmp_path / "LAB-PRG-T02-C01-01"
    shutil.copytree(src_lab, lab_copy)
    shutil.rmtree(lab_copy / "src")
    shutil.copytree(ref_src, lab_copy / "src")

    cfg = json.loads((lab_copy / "lab.config.json").read_text(encoding="utf-8"))
    run_res = run_tests_and_parse(lab_copy, cfg)
    assert run_res["success"] is True, run_res
    eval_res = evaluate_milestones(cfg["milestones"], run_res["testcases"])
    assert eval_res["all_passed"] is True, eval_res
    assert [m["id"] for m in eval_res["milestones"] if m["passed"]] == ["M1", "M2", "M3", "M4"]


def test_batch_test_files_do_not_share_process_state(tmp_path):
    lab_dir = tmp_path / "labs" / "LAB-PRG-BATCH-01"
    (lab_dir / "src").mkdir(parents=True)
    (lab_dir / "tests").mkdir(parents=True)
    (lab_dir / "package.json").write_text('{"name":"batch","type":"module"}\n', encoding="utf-8")
    (lab_dir / "src" / "noop.ts").write_text("export const ok = true;\n", encoding="utf-8")
    t1 = lab_dir / "tests" / "m1_a.test.ts"
    t2 = lab_dir / "tests" / "m1_b.test.ts"
    t1.write_text(
        'import test from "node:test";\n'
        'test("m1_a sets global", () => { (globalThis as Record<string, unknown>).__LEAKED_STATE = "polluted"; });\n',
        encoding="utf-8",
    )
    t2.write_text(
        'import assert from "node:assert/strict";\n'
        'import test from "node:test";\n'
        'test("m1_b sees clean global", () => { assert.equal((globalThis as Record<string, unknown>).__LEAKED_STATE, undefined); });\n',
        encoding="utf-8",
    )
    cases = _run_node_tests([t1, t2], lab_dir, lab_dir / "src")
    assert len(cases) == 2 and all(c["passed"] for c in cases), cases
