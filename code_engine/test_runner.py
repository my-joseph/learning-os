# -*- coding: utf-8 -*-
"""
Test runner for Coding Katas and Implementation Problems.
Executes student code against Visible Tests and Hidden Tests in a sandboxed Node.js subprocess.
Produces structured JSON reports with test statuses, durations, errors, and score calculation.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_HIDDEN_TAG_RE = re.compile(r"\[(?:[A-Z]\d+-)?HIDDEN(?:-[A-Z]?\d+)?\]", re.IGNORECASE)
_HIDDEN_FILE_LINE_RE = re.compile(r"^.*hidden\.test\.[jt]sx?.*$", re.IGNORECASE | re.MULTILINE)


def _sanitize_runner_output(text: str, hidden_tests: list | None = None) -> str:
    """Strip hidden test names, hidden test bodies, and hidden file frames from runner output."""
    if not text:
        return ""
    cleaned = str(text)
    if "// 2. Run Hidden Tests" in cleaned:
        cleaned = cleaned.split("// 2. Run Hidden Tests", 1)[0]
    cleaned = _HIDDEN_FILE_LINE_RE.sub("", cleaned)
    cleaned = _HIDDEN_TAG_RE.sub("[hidden check]", cleaned)
    for case in hidden_tests or []:
        if not isinstance(case, dict):
            continue
        name = str(case.get("name") or "").strip()
        if len(name) >= 3:
            cleaned = cleaned.replace(name, "[hidden check]")
        body = str(case.get("testCode") or "").strip()
        if len(body) >= 6:
            cleaned = cleaned.replace(body, "[hidden test body]")
        for line in body.splitlines():
            stripped = line.strip()
            if len(stripped) >= 6:
                cleaned = cleaned.replace(stripped, "[hidden test body]")
    return cleaned.strip()


def assemble_harness(
    user_code: str,
    visible_tests: list,
    hidden_tests: list,
    *,
    ts_import_line: str = "",
) -> str:
    """
    Creates an executable Node.js script bundling user code, an asynchronous test harness,
    and assertions for both visible and hidden test suites.
    """
    if ts_import_line:
        preamble = (
            f"import {{ performance }} from 'node:perf_hooks';\nimport assert from 'node:assert';\n{ts_import_line}\n"
        )
        user_section = ""
    else:
        preamble = "const { performance } = require('perf_hooks');\nconst assert = require('assert');\n"
        user_section = f"\n// --- User Implementation ---\n{user_code}\n"

    harness = """
{PREAMBLE}
{USER_SECTION}
// --- Test Runner Harness ---
async function __executeTest(name, fn) {
  const start = performance.now();
  try {
    await fn();
    return { name, passed: true, durationMs: Math.round((performance.now() - start) * 100) / 100 };
  } catch (err) {
    return {
      name,
      passed: false,
      durationMs: Math.round((performance.now() - start) * 100) / 100,
      error: err && (err.message || String(err))
    };
  }
}

async function __runHarness() {
  const overallStart = performance.now();
  const visibleResults = [];
  let hiddenPassed = 0;
  const hiddenTotal = {HIDDEN_TOTAL};

  // 1. Run Visible Tests
{VISIBLE_BLOCKS}

  // 2. Run Hidden Tests
{HIDDEN_BLOCKS}

  const overallTime = Math.round((performance.now() - overallStart) * 100) / 100;
  const visiblePassedCount = visibleResults.filter(r => r.passed).length;
  const totalTests = visibleResults.length + hiddenTotal;
  const totalPassed = visiblePassedCount + hiddenPassed;
  const allPassed = totalPassed === totalTests;
  const score = totalTests > 0 ? Math.round((totalPassed / totalTests) * 100) / 100 : 0;

  const report = {
    allPassed,
    score,
    passedCount: totalPassed,
    totalCount: totalTests,
    visibleResults,
    hiddenPassed,
    hiddenTotal,
    executionTimeMs: overallTime
  };

  console.log('__TEST_REPORT_JSON_START__');
  console.log(JSON.stringify(report));
  console.log('__TEST_REPORT_JSON_END__');
}

__runHarness().catch(err => {
  console.error('Harness runtime fatal error:', err);
  process.exit(1);
});
"""

    visible_blocks = []
    for t in visible_tests:
        name = json.dumps(t.get("name", "Test case"))
        test_code = t.get("testCode", "").strip()
        visible_blocks.append(f"""
  visibleResults.push(await __executeTest({name}, async () => {{
    {test_code}
  }}));""")

    hidden_blocks = []
    for t in hidden_tests:
        name = json.dumps(t.get("name", "Hidden test case"))
        test_code = t.get("testCode", "").strip()
        hidden_blocks.append(f"""
  {{
    const res = await __executeTest({name}, async () => {{
      {test_code}
    }});
    if (res.passed) hiddenPassed++;
  }}""")

    script = harness.replace("{PREAMBLE}", preamble)
    script = script.replace("{USER_SECTION}", user_section)
    script = script.replace("{HIDDEN_TOTAL}", str(len(hidden_tests)))
    script = script.replace("{VISIBLE_BLOCKS}", "\n".join(visible_blocks))
    script = script.replace("{HIDDEN_BLOCKS}", "\n".join(hidden_blocks))
    return script


def run_tests(
    user_code: str,
    visible_tests: list,
    hidden_tests: list,
    timeout_sec: float = 4.0,
    *,
    environment: str = "node-vanilla",
    entry_point: str = "",
) -> dict:
    """
    Runs the assembled test suite in Node.js subprocess and returns the parsed report dict.
    """
    if environment == "react-dom":
        return _run_react_tests(user_code, visible_tests, hidden_tests, timeout_sec, entry_point=entry_point)

    is_ts = environment in ("typescript-strict", "backend-sqlite")
    tmp_dir_obj = None
    temp_path = ""

    if is_ts:
        from code_engine.workspace import extract_exports

        tmp_dir_obj = tempfile.TemporaryDirectory(prefix="prg_ts_run_")
        src_path = os.path.join(tmp_dir_obj.name, "solution.ts")
        with open(src_path, "w", encoding="utf-8") as sf:
            sf.write(user_code)
        all_test_code = "\n".join(str(case.get("testCode", "")) for case in (*visible_tests, *hidden_tests))
        import_names = [
            name for name in extract_exports(user_code) if re.search(rf"\b{re.escape(name)}\b", all_test_code)
        ]
        if entry_point and entry_point not in import_names:
            import_names.insert(0, entry_point)
        ts_import = (
            f"import {{ {', '.join(import_names)} }} from './solution.ts';"
            if import_names
            else "import './solution.ts';"
        )
        script = assemble_harness(user_code, visible_tests, hidden_tests, ts_import_line=ts_import)
        temp_path = os.path.join(tmp_dir_obj.name, "harness.ts")
        with open(temp_path, "w", encoding="utf-8") as hf:
            hf.write(script)
        cmd = ["node", "--experimental-strip-types", temp_path]
    else:
        script = assemble_harness(user_code, visible_tests, hidden_tests)
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(script)
            temp_path = f.name
        cmd = ["node", temp_path]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        stdout = proc.stdout
        stderr = proc.stderr

        if "__TEST_REPORT_JSON_START__" in stdout:
            parts = stdout.split("__TEST_REPORT_JSON_START__")[1].split("__TEST_REPORT_JSON_END__")
            report = json.loads(parts[0].strip())
            pre_marker = stdout.split("__TEST_REPORT_JSON_START__", 1)[0]
            report["rawOutput"] = _sanitize_runner_output(pre_marker, hidden_tests)
            return report
        else:
            raw_err = stderr or stdout or "Script exited unexpectedly"
            return {
                "allPassed": False,
                "score": 0,
                "passedCount": 0,
                "totalCount": len(visible_tests) + len(hidden_tests),
                "visibleResults": [
                    {
                        "name": "Execution failure",
                        "passed": False,
                        "error": _sanitize_runner_output(raw_err, hidden_tests),
                    }
                ],
                "hiddenPassed": 0,
                "hiddenTotal": len(hidden_tests),
                "executionTimeMs": 0,
                "rawOutput": _sanitize_runner_output(stdout + "\n" + stderr, hidden_tests),
            }
    except subprocess.TimeoutExpired:
        return {
            "allPassed": False,
            "score": 0,
            "passedCount": 0,
            "totalCount": len(visible_tests) + len(hidden_tests),
            "visibleResults": [
                {
                    "name": "Timeout",
                    "passed": False,
                    "error": f"Execution exceeded {timeout_sec}s limit (possible infinite loop)",
                }
            ],
            "hiddenPassed": 0,
            "hiddenTotal": len(hidden_tests),
            "executionTimeMs": int(timeout_sec * 1000),
            "rawOutput": "Timeout error",
        }
    except Exception as ex:
        return {
            "allPassed": False,
            "score": 0,
            "passedCount": 0,
            "totalCount": len(visible_tests) + len(hidden_tests),
            "visibleResults": [{"name": "System error", "passed": False, "error": str(ex)}],
            "hiddenPassed": 0,
            "hiddenTotal": len(hidden_tests),
            "executionTimeMs": 0,
            "rawOutput": str(ex),
        }
    finally:
        if tmp_dir_obj is not None:
            tmp_dir_obj.cleanup()
        elif temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _run_react_tests(
    user_code: str,
    visible_tests: list,
    hidden_tests: list,
    timeout_sec: float,
    *,
    entry_point: str,
) -> dict:
    """Run a React/TSX drill in jsdom using the shared tools/lint installation."""
    tools_dir = Path(__file__).resolve().parents[1] / "tools" / "lint"
    vitest = tools_dir / "node_modules" / ".bin" / "vitest"
    if not vitest.is_file():
        return _react_failure(
            f"React drill runner is not installed at {vitest}; run `npm ci` in tools/lint.", visible_tests, hidden_tests
        )

    # Put the temporary project under tools/lint so Vite resolves the shared modules without a per-workspace install.
    try:
        with tempfile.TemporaryDirectory(prefix=".react_drill_", dir=tools_dir) as tmp:
            tmp_dir = Path(tmp)
            (tmp_dir / "solution.tsx").write_text(user_code.rstrip() + "\n", encoding="utf-8")
            visible_test_file = tmp_dir / "visible.test.tsx"
            hidden_test_file = tmp_dir / "hidden.test.tsx"
            config_file = tmp_dir / "vitest.config.ts"
            report_file = tmp_dir / "vitest-report.json"

            from code_engine.workspace import build_react_test_header, extract_exports

            all_test_code = [str(case.get("testCode", "")) for case in (*visible_tests, *hidden_tests)]
            import_names = [
                name
                for name in extract_exports(user_code)
                if any(re.search(rf"\b{re.escape(name)}\b", test_code) for test_code in all_test_code)
            ]
            if not import_names and entry_point:
                import_names = [entry_point]
            visible_blocks = []
            for case in visible_tests:
                name = str(case.get("name") or "Test")
                body = str(case.get("testCode", "")).strip()
                visible_blocks.append(f"test({json.dumps(name)}, async () => {{\n{body}\n}});\n")
            visible_code = "\n".join(str(case.get("testCode", "")) for case in visible_tests)
            visible_header = build_react_test_header(", ".join(import_names), visible_code, "./solution.tsx")
            visible_test_file.write_text(visible_header + "\n".join(visible_blocks), encoding="utf-8")

            test_files = [str(visible_test_file)]
            if hidden_tests:
                hidden_blocks = []
                for index, case in enumerate(hidden_tests, 1):
                    name = f"[HIDDEN-{index:02d}] {case.get('name') or 'Hidden test'}"
                    body = str(case.get("testCode", "")).strip()
                    hidden_blocks.append(f"test({json.dumps(name)}, async () => {{\n{body}\n}});\n")
                hidden_code = "\n".join(str(case.get("testCode", "")) for case in hidden_tests)
                hidden_header = build_react_test_header(", ".join(import_names), hidden_code, "./solution.tsx")
                hidden_test_file.write_text(hidden_header + "\n".join(hidden_blocks), encoding="utf-8")
                test_files.append(str(hidden_test_file))

            config_file.write_text(
                "import { defineConfig } from 'vitest/config';\n"
                "export default defineConfig({ esbuild: { jsx: 'automatic' }, test: { environment: 'jsdom' } });\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    str(vitest),
                    "run",
                    *test_files,
                    "--config",
                    str(config_file),
                    "--reporter=json",
                    f"--outputFile={report_file}",
                ],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            if not report_file.is_file():
                return _react_failure(
                    _sanitize_runner_output(
                        proc.stderr or proc.stdout or f"Vitest exited with code {proc.returncode}",
                        hidden_tests,
                    ),
                    visible_tests,
                    hidden_tests,
                )

            report = json.loads(report_file.read_text(encoding="utf-8"))
            visible_results = []
            hidden_passed = hidden_total = 0
            for suite in report.get("testResults", []):
                suite_file = str(suite.get("name") or "")
                is_hidden_suite = suite_file.endswith("hidden.test.tsx")
                for result in suite.get("assertionResults", []):
                    name = result.get("fullName") or result.get("title") or "React test"
                    passed = result.get("status") == "passed"
                    if is_hidden_suite or "[HIDDEN-" in name:
                        hidden_total += 1
                        hidden_passed += int(passed)
                    else:
                        visible_results.append(
                            {
                                "name": name,
                                "passed": passed,
                                "error": "\n".join(result.get("failureMessages") or []) if not passed else None,
                            }
                        )
            total = len(visible_results) + hidden_total
            passed_count = sum(bool(result["passed"]) for result in visible_results) + hidden_passed
            start, end = report.get("startTime"), report.get("endTime")
            return {
                "allPassed": proc.returncode == 0 and total > 0 and passed_count == total,
                "score": round(passed_count / total, 2) if total else 0,
                "passedCount": passed_count,
                "totalCount": total,
                "visibleResults": visible_results,
                "hiddenPassed": hidden_passed,
                "hiddenTotal": hidden_total,
                "executionTimeMs": int(end - start)
                if isinstance(start, (int, float)) and isinstance(end, (int, float))
                else 0,
                "rawOutput": ""
                if proc.returncode == 0
                else _sanitize_runner_output(proc.stdout + proc.stderr, hidden_tests),
            }
    except subprocess.TimeoutExpired:
        return _react_failure(f"Execution exceeded {timeout_sec}s limit", visible_tests, hidden_tests)
    except Exception as exc:
        return _react_failure(
            _sanitize_runner_output(f"React runner error: {exc}", hidden_tests), visible_tests, hidden_tests
        )


def _react_failure(message: str, visible_tests: list, hidden_tests: list) -> dict:
    safe_msg = _sanitize_runner_output(message, hidden_tests)
    return {
        "allPassed": False,
        "score": 0,
        "passedCount": 0,
        "totalCount": len(visible_tests) + len(hidden_tests),
        "visibleResults": [{"name": "React runner failure", "passed": False, "error": safe_msg}],
        "hiddenPassed": 0,
        "hiddenTotal": len(hidden_tests),
        "executionTimeMs": 0,
        "rawOutput": safe_msg,
    }


if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    user_code = payload.get("userCode", "")
    vis = payload.get("visibleTests", [])
    hid = payload.get("hiddenTests", [])
    environment = payload.get("environment") or "node-vanilla"
    entry_point = payload.get("entryPoint") or ""
    res = run_tests(user_code, vis, hid, environment=environment, entry_point=entry_point)
    print(json.dumps(res))
