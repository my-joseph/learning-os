"""React DOM and PRG subprocess runner characterization tests for lab_ingest."""

from pathlib import Path

import pytest

from code_engine import lab_ingest
from code_engine.lab_ingest import _run_eslint_dir, _run_node_tests, _run_react_tests, _run_tsc
from code_engine.lint_check import LintToolsMissingError, get_lint_binaries


def _require_lint_tools() -> None:
    try:
        get_lint_binaries()
    except LintToolsMissingError as exc:
        pytest.skip(str(exc))


def _snapshot_tree(root: Path) -> dict[str, bytes | str]:
    """Capture every relative entry under `root` (file bytes or symlink target) for immutability checks."""
    snap: dict[str, bytes | str] = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            snap[rel] = f"SYMLINK:{p.readlink()}"
        elif p.is_file():
            snap[rel] = p.read_bytes()
        elif p.is_dir():
            snap[rel] = "DIR"
    return snap


def test_lab_ingest_runs_tsx_component_test_in_jsdom(tmp_path: Path):
    _require_lint_tools()
    lab = tmp_path / "lab"
    src = lab / "src"
    tests = lab / "tests"
    src.mkdir(parents=True)
    tests.mkdir()
    (src / "ClickCounter.tsx").write_text(
        """import React, { useState } from 'react';
export function ClickCounter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount((value) => value + 1)}>Count: {count}</button>;
}
""",
        encoding="utf-8",
    )
    test_file = tests / "M1.test.tsx"
    test_file.write_text(
        """import { test } from 'vitest';
import assert from 'node:assert';
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ClickCounter } from '../src/ClickCounter';

test('renders and increments after a user click', async () => {
  const user = userEvent.setup();
  render(<ClickCounter />);
  await user.click(screen.getByRole('button', { name: 'Count: 0' }));
  assert.equal(screen.getByRole('button').textContent, 'Count: 1');
});
""",
        encoding="utf-8",
    )

    before = _snapshot_tree(lab)
    cases = _run_node_tests([test_file], lab, src)

    assert len(cases) == 1
    assert cases[0]["passed"], cases
    assert {"name", "passed", "failure_msg", "is_hidden"} <= set(cases[0].keys())
    assert cases[0]["is_hidden"] is False
    assert not (lab / "node_modules").exists()
    assert _snapshot_tree(lab) == before


def test_lab_ingest_can_load_reference_component_outside_lab_root(tmp_path: Path):
    _require_lint_tools()
    lab = tmp_path / "lab"
    tests = lab / "tests"
    reference_src = tmp_path / "_reference" / "lab" / "src"
    tests.mkdir(parents=True)
    reference_src.mkdir(parents=True)
    (reference_src / "Notice.tsx").write_text(
        "import React from 'react';\nexport function Notice() { return <output>Saved</output>; }\n",
        encoding="utf-8",
    )
    test_file = tests / "M3.test.tsx"
    test_file.write_text(
        """import { test } from 'vitest';
import assert from 'node:assert';
import React from 'react';
import { render, screen } from '@testing-library/react';
const source = process.env.LAB_SRC_DIR;
const { Notice } = await import(`${source}/Notice.tsx`);
test('loads a component from the sibling reference workspace', () => {
  render(<Notice />);
  assert.equal(screen.getByText('Saved').textContent, 'Saved');
});
""",
        encoding="utf-8",
    )

    cases = _run_node_tests([test_file], lab, reference_src)

    assert len(cases) == 1
    assert cases[0]["passed"], cases


def test_lab_ingest_node_js_and_ts_test_runner_shapes(tmp_path: Path):
    assert _run_node_tests([], tmp_path, tmp_path) == []

    # 1. Plain JS lab test (pass + fail)
    js_lab = tmp_path / "js_lab"
    js_src = js_lab / "src"
    js_tests = js_lab / "tests"
    js_src.mkdir(parents=True)
    js_tests.mkdir()
    (js_src / "calc.js").write_text("module.exports = { add: (a, b) => a + b };\n", encoding="utf-8")
    js_test = js_tests / "m1.test.js"
    js_test.write_text(
        "const test = require('node:test');\n"
        "const assert = require('node:assert');\n"
        "const { add } = require('../src/calc.js');\n"
        "test('adds positive numbers', () => { assert.strictEqual(add(2, 3), 5); });\n"
        "test('intentional failure case', () => { assert.strictEqual(add(2, 3), 99); });\n",
        encoding="utf-8",
    )
    js_before = _snapshot_tree(js_lab)
    js_cases = _run_node_tests([js_test], js_lab, js_src)
    assert len(js_cases) == 2
    passed_case = next(c for c in js_cases if c["name"] == "adds positive numbers")
    failed_case = next(c for c in js_cases if c["name"] == "intentional failure case")
    assert passed_case["passed"] is True
    assert passed_case["failure_msg"] == ""
    assert passed_case["is_hidden"] is False
    assert failed_case["passed"] is False
    assert failed_case["failure_msg"]
    assert _snapshot_tree(js_lab) == js_before

    # 2. TypeScript lab test using LAB_SRC_DIR
    ts_lab = tmp_path / "ts_lab"
    ts_src = ts_lab / "src"
    ts_tests = ts_lab / "tests"
    ts_src.mkdir(parents=True)
    ts_tests.mkdir()
    (ts_lab / "package.json").write_text('{"type": "module"}\n', encoding="utf-8")
    (ts_src / "math.ts").write_text(
        "export function double(value: number): number { return value * 2; }\n", encoding="utf-8"
    )
    ts_test = ts_tests / "m1.test.ts"
    ts_test.write_text(
        "import test from 'node:test';\n"
        "import assert from 'node:assert';\n"
        "const { double } = await import(`${process.env.LAB_SRC_DIR}/math.ts`);\n"
        "test('doubles number', () => { assert.strictEqual(double(4), 8); });\n",
        encoding="utf-8",
    )
    ts_before = _snapshot_tree(ts_lab)
    ts_cases = _run_node_tests([ts_test], ts_lab, ts_src)
    assert len(ts_cases) == 1
    assert ts_cases[0]["passed"] is True
    assert ts_cases[0]["name"] == "doubles number"
    assert _snapshot_tree(ts_lab) == ts_before


def test_lab_ingest_eslint_and_tsc_runner_shapes_and_immutability(tmp_path: Path):
    _require_lint_tools()
    lab = tmp_path / "lint_tsc_lab"
    src = lab / "src"
    src.mkdir(parents=True)
    (lab / "tsconfig.json").write_text("{}\n", encoding="utf-8")
    (src / "clean.ts").write_text(
        "export function clamp(value: number, max: number): number {\n  return value > max ? max : value;\n}\n",
        encoding="utf-8",
    )

    before_clean = _snapshot_tree(lab)
    assert _run_eslint_dir(src) == []
    assert _run_tsc(lab / "tsconfig.json") == []
    assert _snapshot_tree(lab) == before_clean

    # Introduce ESLint + TypeScript errors
    (src / "broken.ts").write_text(
        "export function bad(input: any): number {\n  input = 1;\n  const wrong: number = 'oops';\n  return wrong;\n}\n",
        encoding="utf-8",
    )
    before_broken = _snapshot_tree(lab)

    lint_findings = _run_eslint_dir(src)
    assert lint_findings
    for finding in lint_findings:
        assert set(finding.keys()) == {"file", "line", "rule", "message"}
        assert isinstance(finding["file"], str)
        assert isinstance(finding["line"], int)
        assert isinstance(finding["rule"], str)
        assert isinstance(finding["message"], str)
    assert any(f["file"] == "broken.ts" and f["rule"] == "no-param-reassign" for f in lint_findings)

    tsc_errors = _run_tsc(lab / "tsconfig.json")
    assert tsc_errors
    assert all(isinstance(line, str) and line for line in tsc_errors)
    assert any("TS2322" in line for line in tsc_errors)
    assert _snapshot_tree(lab) == before_broken


def test_lab_ingest_reexports_runner_helpers():
    assert callable(lab_ingest._run_node_tests)
    assert callable(lab_ingest._run_react_tests)
    assert callable(lab_ingest._run_eslint_dir)
    assert callable(lab_ingest._run_tsc)
    assert callable(lab_ingest._parse_junit_xml)
    assert _run_react_tests is lab_ingest._run_react_tests
