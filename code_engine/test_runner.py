# -*- coding: utf-8 -*-
"""
Test runner for Coding Katas and Implementation Problems.
Executes student code against Visible Tests and Hidden Tests in a sandboxed Node.js subprocess.
Produces structured JSON reports with test statuses, durations, errors, and score calculation.
"""

import hmac
import json
import math
import os
import re
import secrets
import sys
from pathlib import Path
from urllib.parse import quote

from code_engine.sandbox import (
    create_sandbox_dir,
    run_node_isolated,
    run_vitest_isolated,
)

_HIDDEN_TAG_RE = re.compile(r"\[(?:[A-Z]\d+-)?HIDDEN(?:-[A-Z]?\d+)?\]|\bHIDDEN[-_](?:T?\d+|TRAP)\b", re.IGNORECASE)
_HIDDEN_FILE_LINE_RE = re.compile(r"^.*hidden\.test\.[jt]sx?.*$", re.IGNORECASE | re.MULTILINE)
_MAX_VISIBLE_NAME_LEN = 500
_MAX_VISIBLE_ERROR_LEN = 2000
_MAX_RAW_OUTPUT_LEN = 8000


def _is_hidden_case_text(text: str | None, hidden_tests: list | None = None) -> bool:
    if not text or not isinstance(text, str):
        return False
    if _HIDDEN_TAG_RE.search(text):
        return True
    for case in hidden_tests or []:
        if not isinstance(case, dict):
            continue
        name = str(case.get("name") or "").strip()
        if len(name) >= 3 and name in text:
            return True
    return False


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


def _bounded_nonneg_int(val: object, default: int = 0) -> int:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return default
    if not math.isfinite(val) or val < 0:
        return default
    return int(val)


def _bounded_nonneg_ms(val: object, default: float = 0) -> float | int:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return default
    if not math.isfinite(val) or val < 0:
        return default
    return round(val, 2) if isinstance(val, float) else val


def project_test_report(
    raw_report: dict | None,
    *,
    visible_tests: list,
    hidden_tests: list,
    returncode: int = 0,
    raw_output: str = "",
    require_complete: bool = True,
) -> dict:
    """Project a raw runner report onto the strict allowlisted TestRunReport schema."""
    hidden_total = len(hidden_tests)
    expected_visible = len(visible_tests)
    safe_raw_output = _sanitize_runner_output(raw_output, hidden_tests)[:_MAX_RAW_OUTPUT_LEN]

    if not isinstance(raw_report, dict):
        return _failure_report(
            "Execution failure",
            "Test runner did not produce a valid report",
            visible_tests,
            hidden_tests,
            raw_output=safe_raw_output,
        )

    raw_visible = raw_report.get("visibleResults")
    if not isinstance(raw_visible, list):
        return _failure_report(
            "Execution failure",
            "Test runner produced an invalid visibleResults payload",
            visible_tests,
            hidden_tests,
            raw_output=safe_raw_output,
        )

    visible_results: list[dict] = []
    for entry in raw_visible:
        if not isinstance(entry, dict):
            continue
        raw_name = str(entry.get("name") or "Test case")
        raw_err = entry.get("error")
        err_str = str(raw_err) if raw_err is not None else ""
        if _is_hidden_case_text(raw_name, hidden_tests):
            # Hidden cases must never appear in visibleResults.
            continue
        passed = bool(entry.get("passed") is True)
        clean_name = _sanitize_runner_output(raw_name, hidden_tests)[:_MAX_VISIBLE_NAME_LEN] or "Test case"
        item: dict = {
            "name": clean_name,
            "passed": passed,
        }
        duration_ms = entry.get("durationMs")
        if (
            not isinstance(duration_ms, bool)
            and isinstance(duration_ms, (int, float))
            and math.isfinite(duration_ms)
            and duration_ms >= 0
        ):
            item["durationMs"] = round(duration_ms, 2)
        if not passed and err_str.strip():
            item["error"] = _sanitize_runner_output(err_str, hidden_tests)[:_MAX_VISIBLE_ERROR_LEN]
        visible_results.append(item)

    if require_complete and len(visible_results) != expected_visible:
        return _failure_report(
            "Execution failure",
            "Test runner returned an incomplete visible test report",
            visible_tests,
            hidden_tests,
            raw_output=safe_raw_output,
        )

    if require_complete and "hiddenTotal" in raw_report:
        reported_hidden_total = _bounded_nonneg_int(raw_report.get("hiddenTotal"), -1)
        if reported_hidden_total != hidden_total:
            return _failure_report(
                "Execution failure",
                "Test runner returned an incomplete hidden test report",
                visible_tests,
                hidden_tests,
                raw_output=safe_raw_output,
            )

    hidden_passed = min(_bounded_nonneg_int(raw_report.get("hiddenPassed"), 0), hidden_total)
    visible_passed = sum(1 for r in visible_results if r["passed"])
    total_count = len(visible_results) + hidden_total
    passed_count = visible_passed + hidden_passed
    all_passed = returncode == 0 and total_count > 0 and passed_count == total_count
    score = round(passed_count / total_count, 2) if total_count > 0 else 0

    return {
        "allPassed": all_passed,
        "score": score,
        "passedCount": passed_count,
        "totalCount": total_count,
        "visibleResults": visible_results,
        "hiddenPassed": hidden_passed,
        "hiddenTotal": hidden_total,
        "executionTimeMs": _bounded_nonneg_ms(raw_report.get("executionTimeMs"), 0),
        "rawOutput": safe_raw_output,
    }


def _failure_report(
    name: str,
    message: str,
    visible_tests: list,
    hidden_tests: list,
    *,
    execution_time_ms: int | float = 0,
    raw_output: str | None = None,
) -> dict:
    safe_msg = _sanitize_runner_output(message, hidden_tests)[:_MAX_VISIBLE_ERROR_LEN]
    safe_raw = _sanitize_runner_output(raw_output if raw_output is not None else safe_msg, hidden_tests)[
        :_MAX_RAW_OUTPUT_LEN
    ]
    return {
        "allPassed": False,
        "score": 0,
        "passedCount": 0,
        "totalCount": len(visible_tests) + len(hidden_tests),
        "visibleResults": [{"name": name, "passed": False, "error": safe_msg}],
        "hiddenPassed": 0,
        "hiddenTotal": len(hidden_tests),
        "executionTimeMs": execution_time_ms,
        "rawOutput": safe_raw,
    }


def assemble_harness(
    user_code: str,
    visible_tests: list,
    hidden_tests: list,
    *,
    ts_import_line: str = "",
    solution_url: str = "",
    ts_import_names: list[str] | None = None,
    solution_path: str = "",
    entry_point: str = "",
) -> str:
    """
    Create an executable Node.js script that executes `user_code` separately from trusted
    report serialization and writes the structured report to `LEARNINGOS_REPORT_FILE`.
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

    if ts_import_line or solution_url:
        if solution_url:
            names = [n for n in (ts_import_names or []) if re.match(r"^[A-Za-z_$][\w$]*$", n)]
            binding_line = f"const {{ {', '.join(names)} }} = __sol;" if names else ""
            load_ts_line = f"const __sol = await import({json.dumps(solution_url)});\n  {binding_line}"
        else:
            load_ts_line = ""
        preamble = (
            "import __fs from 'node:fs';\n"
            "import { performance as __perf } from 'node:perf_hooks';\n"
            "import assert from 'node:assert';\n"
            f"{ts_import_line}\n"
        )
        return (
            f"{preamble}\n"
            "const __writeFileSync = __fs.writeFileSync.bind(__fs);\n"
            "const __stringify = JSON.stringify;\n"
            "const __now = __perf.now.bind(__perf);\n"
            "const __reportPath = process.env.LEARNINGOS_REPORT_FILE || '';\n"
            "const __reportNonce = process.env.LEARNINGOS_REPORT_NONCE || '';\n"
            "delete process.env.LEARNINGOS_REPORT_FILE;\n"
            "delete process.env.LEARNINGOS_REPORT_NONCE;\n"
            "\n"
            "async function __executeTest(name, fn) {\n"
            "  const start = __now();\n"
            "  try {\n"
            "    await fn();\n"
            "    return { name, passed: true, durationMs: Math.round((__now() - start) * 100) / 100 };\n"
            "  } catch (err) {\n"
            "    return {\n"
            "      name,\n"
            "      passed: false,\n"
            "      durationMs: Math.round((__now() - start) * 100) / 100,\n"
            "      error: err && (err.message || String(err))\n"
            "    };\n"
            "  }\n"
            "}\n"
            "\n"
            "async function __runHarness() {\n"
            f"  {load_ts_line}\n"
            "  const overallStart = __now();\n"
            "  const visibleResults = [];\n"
            "  let hiddenPassed = 0;\n"
            f"  const hiddenTotal = {len(hidden_tests)};\n"
            "\n"
            "  // 1. Run Visible Tests\n"
            + "\n".join(visible_blocks)
            + "\n\n  // 2. Run Hidden Tests\n"
            + "\n".join(hidden_blocks)
            + "\n\n"
            "  const overallTime = Math.round((__now() - overallStart) * 100) / 100;\n"
            "  const report = {\n"
            "    nonce: __reportNonce,\n"
            "    visibleResults,\n"
            "    hiddenPassed,\n"
            "    hiddenTotal,\n"
            "    executionTimeMs: overallTime\n"
            "  };\n"
            "  if (!__reportPath) throw new Error('Missing trusted report destination');\n"
            "  __writeFileSync(__reportPath, __stringify(report), 'utf8');\n"
            "}\n"
            "\n"
            "__runHarness().catch(err => {\n"
            "  console.error('Harness runtime fatal error:', err);\n"
            "  process.exit(1);\n"
            "});\n"
        )

    # CommonJS / node-vanilla path: wrap harness in an IIFE so learner code cannot access
    # __reportPath, __reportNonce, __writeFileSync, or __stringify.
    sol_load_block = ""
    if solution_path:
        sol_load_block = f"""
  const __solPath = {json.dumps(solution_path)};
  const __entryPoint = {json.dumps(entry_point)};
  const __solCode = __readFileSync(__solPath, 'utf8');
  const __req = __createRequire(__solPath);
  if (/\\b(?:module\\.exports|exports\\s*(?:\\.|\\[|=))/.test(__solCode)) {{
    const __loaded = __req(__solPath);
    if (typeof __loaded === 'function' && __entryPoint) {{
      globalThis[__entryPoint] = __loaded;
    }} else if (__loaded && typeof __loaded === 'object') {{
      for (const [__k, __v] of __entries(__loaded)) {{
        if (__k !== 'assert' && __k !== 'performance' && __k !== 'globalThis' && __k !== 'require') {{
          globalThis[__k] = __v;
        }}
      }}
    }}
  }} else {{
    const __prevReq = globalThis.require;
    globalThis.require = __req;
    try {{
      __vm.runInThisContext(__solCode, {{ filename: __solPath }});
    }} finally {{
      if (__prevReq === undefined) delete globalThis.require;
      else globalThis.require = __prevReq;
    }}
  }}"""
    else:
        sol_load_block = f"\n  // --- User Implementation ---\n{user_code}\n"

    return (
        "(async () => {\n"
        "  const __fs = require('node:fs');\n"
        "  const { performance: __perf } = require('node:perf_hooks');\n"
        "  const assert = require('node:assert');\n"
        "  const { createRequire: __createRequire } = require('node:module');\n"
        "  const __vm = require('node:vm');\n"
        "  const __writeFileSync = __fs.writeFileSync.bind(__fs);\n"
        "  const __readFileSync = __fs.readFileSync.bind(__fs);\n"
        "  const __stringify = JSON.stringify;\n"
        "  const __entries = Object.entries;\n"
        "  const __now = __perf.now.bind(__perf);\n"
        "  const __reportPath = process.env.LEARNINGOS_REPORT_FILE || '';\n"
        "  const __reportNonce = process.env.LEARNINGOS_REPORT_NONCE || '';\n"
        "  delete process.env.LEARNINGOS_REPORT_FILE;\n"
        "  delete process.env.LEARNINGOS_REPORT_NONCE;\n"
        "\n"
        "  async function __executeTest(name, fn) {\n"
        "    const start = __now();\n"
        "    try {\n"
        "      await fn();\n"
        "      return { name, passed: true, durationMs: Math.round((__now() - start) * 100) / 100 };\n"
        "    } catch (err) {\n"
        "      return {\n"
        "        name,\n"
        "        passed: false,\n"
        "        durationMs: Math.round((__now() - start) * 100) / 100,\n"
        "        error: err && (err.message || String(err))\n"
        "      };\n"
        "    }\n"
        "  }\n"
        f"{sol_load_block}\n"
        "  const overallStart = __now();\n"
        "  const visibleResults = [];\n"
        "  let hiddenPassed = 0;\n"
        f"  const hiddenTotal = {len(hidden_tests)};\n"
        "\n"
        "  // 1. Run Visible Tests\n"
        + "\n".join(visible_blocks)
        + "\n\n  // 2. Run Hidden Tests\n"
        + "\n".join(hidden_blocks)
        + "\n\n"
        "  const overallTime = Math.round((__now() - overallStart) * 100) / 100;\n"
        "  const report = {\n"
        "    nonce: __reportNonce,\n"
        "    visibleResults,\n"
        "    hiddenPassed,\n"
        "    hiddenTotal,\n"
        "    executionTimeMs: overallTime\n"
        "  };\n"
        "  if (!__reportPath) throw new Error('Missing trusted report destination');\n"
        "  __writeFileSync(__reportPath, __stringify(report), 'utf8');\n"
        "})().catch(err => {\n"
        "  console.error('Harness runtime fatal error:', err);\n"
        "  process.exit(1);\n"
        "});\n"
    )


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
    Runs the assembled test suite in an isolated Node.js subprocess and returns a projected report dict.
    """
    if environment == "react-dom":
        return _run_react_tests(user_code, visible_tests, hidden_tests, timeout_sec, entry_point=entry_point)

    is_ts = environment in ("typescript-strict", "backend-sqlite")

    try:
        with create_sandbox_dir(prefix="prg_ts_run_" if is_ts else "prg_js_run_") as sbx_str:
            sbx_root = Path(os.path.realpath(sbx_str))
            work_dir = sbx_root / "work"
            runner_dir = sbx_root / f"runner-{secrets.token_hex(8)}"
            report_dir = sbx_root / f"report-{secrets.token_hex(8)}"
            work_dir.mkdir(parents=True, exist_ok=True)
            runner_dir.mkdir(parents=True, exist_ok=True)
            report_dir.mkdir(parents=True, exist_ok=True)

            report_file = report_dir / f"result-{secrets.token_hex(12)}.json"
            report_nonce = secrets.token_hex(16)

            if is_ts:
                from code_engine.workspace import extract_exports

                sol_file = work_dir / "solution.ts"
                sol_file.write_text(user_code, encoding="utf-8")
                all_test_code = "\n".join(str(case.get("testCode", "")) for case in (*visible_tests, *hidden_tests))
                import_names = [
                    name for name in extract_exports(user_code) if re.search(rf"\b{re.escape(name)}\b", all_test_code)
                ]
                if entry_point and entry_point not in import_names:
                    import_names.insert(0, entry_point)
                sol_url = "file://" + quote(str(sol_file))
                script = assemble_harness(
                    user_code,
                    visible_tests,
                    hidden_tests,
                    solution_url=sol_url,
                    ts_import_names=import_names,
                )
                harness_file = runner_dir / "harness.ts"
                harness_file.write_text(script, encoding="utf-8")
                node_args = ["--experimental-strip-types", str(harness_file)]
            else:
                sol_file = work_dir / "solution.js"
                sol_file.write_text(user_code, encoding="utf-8")
                script = assemble_harness(
                    user_code,
                    visible_tests,
                    hidden_tests,
                    solution_path=str(sol_file),
                    entry_point=entry_point,
                )
                harness_file = runner_dir / "harness.js"
                harness_file.write_text(script, encoding="utf-8")
                node_args = [str(harness_file)]

            proc = run_node_isolated(
                node_args,
                cwd=work_dir,
                sandbox_root=sbx_root,
                timeout_sec=timeout_sec,
                env_extra={
                    "LEARNINGOS_REPORT_FILE": str(report_file),
                    "LEARNINGOS_REPORT_NONCE": report_nonce,
                },
            )

            if proc.timed_out:
                return _failure_report(
                    "Timeout",
                    f"Execution exceeded {timeout_sec}s limit (possible infinite loop)",
                    visible_tests,
                    hidden_tests,
                    execution_time_ms=int(timeout_sec * 1000),
                    raw_output="Timeout error",
                )

            if proc.output_truncated:
                return _failure_report(
                    "Output limit exceeded",
                    "Execution exceeded output size limit",
                    visible_tests,
                    hidden_tests,
                    raw_output=proc.stdout[:2000],
                )

            stdout = proc.stdout
            stderr = proc.stderr

            if proc.returncode == 0 and report_file.is_file() and not report_file.is_symlink():
                try:
                    raw_report = json.loads(report_file.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    raw_report = None
                if isinstance(raw_report, dict) and hmac.compare_digest(
                    str(raw_report.get("nonce") or ""), report_nonce
                ):
                    return project_test_report(
                        raw_report,
                        visible_tests=visible_tests,
                        hidden_tests=hidden_tests,
                        returncode=proc.returncode,
                        raw_output=stdout,
                        require_complete=True,
                    )

            raw_err = stderr or stdout or "Script exited unexpectedly"
            return _failure_report(
                "Execution failure",
                raw_err,
                visible_tests,
                hidden_tests,
                raw_output=stdout + "\n" + stderr,
            )
    except Exception as ex:
        return _failure_report(
            "System error",
            str(ex),
            visible_tests,
            hidden_tests,
            raw_output=str(ex),
        )


def _run_react_tests(
    user_code: str,
    visible_tests: list,
    hidden_tests: list,
    timeout_sec: float,
    *,
    entry_point: str,
) -> dict:
    """Run a React/TSX drill in jsdom using the shared tools/lint installation inside an isolated temp sandbox."""
    tools_dir = (Path(__file__).resolve().parents[1] / "tools" / "lint").resolve()
    shared_modules = (tools_dir / "node_modules").resolve()
    vitest = shared_modules / ".bin" / "vitest"
    if not vitest.is_file():
        return _react_failure(
            f"React drill runner is not installed at {vitest}; run `npm ci` in tools/lint.", visible_tests, hidden_tests
        )

    try:
        with create_sandbox_dir(prefix="prg_react_drill_") as sbx_str:
            sbx_root = Path(os.path.realpath(sbx_str))
            (sbx_root / "node_modules").symlink_to(shared_modules, target_is_directory=True)
            work_dir = sbx_root / "work"
            work_dir.mkdir(parents=True, exist_ok=True)

            (work_dir / "solution.tsx").write_text(user_code.rstrip() + "\n", encoding="utf-8")
            visible_test_file = work_dir / "visible.test.tsx"
            hidden_test_file = work_dir / "hidden.test.tsx"
            config_file = sbx_root / "vitest.config.ts"
            report_file = sbx_root / "vitest-report.json"

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

            allow_js = ", ".join(json.dumps(str(d)) for d in dict.fromkeys((sbx_root, shared_modules, tools_dir)))
            config_file.write_text(
                "import { defineConfig } from 'vitest/config';\n"
                f"export default defineConfig({{ root: {json.dumps(str(work_dir))}, esbuild: {{ jsx: 'automatic' }}, test: {{ environment: 'jsdom' }}, server: {{ fs: {{ allow: [{allow_js}] }} }} }});\n",
                encoding="utf-8",
            )
            proc = run_vitest_isolated(
                test_files,
                cwd=work_dir,
                sandbox_root=sbx_root,
                config_path=config_file,
                report_path=report_file,
                reporter="json",
                timeout_sec=timeout_sec,
                tools_lint_dir=tools_dir,
            )
            if proc.timed_out:
                return _react_failure(f"Execution exceeded {timeout_sec}s limit", visible_tests, hidden_tests)
            if proc.output_truncated:
                return _react_failure("Execution exceeded output size limit", visible_tests, hidden_tests)
            if not report_file.is_file() or report_file.is_symlink():
                return _react_failure(
                    proc.stderr or proc.stdout or f"Vitest exited with code {proc.returncode}",
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
                    if is_hidden_suite or _is_hidden_case_text(name, hidden_tests):
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
            start, end = report.get("startTime"), report.get("endTime")
            exec_ms = int(end - start) if isinstance(start, (int, float)) and isinstance(end, (int, float)) else 0
            return project_test_report(
                {
                    "visibleResults": visible_results,
                    "hiddenPassed": hidden_passed,
                    "hiddenTotal": hidden_total,
                    "executionTimeMs": exec_ms,
                },
                visible_tests=visible_tests,
                hidden_tests=hidden_tests,
                returncode=proc.returncode,
                raw_output="" if proc.returncode == 0 else (proc.stdout + proc.stderr),
                require_complete=True,
            )
    except Exception as exc:
        return _react_failure(f"React runner error: {exc}", visible_tests, hidden_tests)


def _react_failure(message: str, visible_tests: list, hidden_tests: list) -> dict:
    return _failure_report("React runner failure", message, visible_tests, hidden_tests)


if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    user_code = payload.get("userCode", "")
    vis = payload.get("visibleTests", [])
    hid = payload.get("hiddenTests", [])
    environment = payload.get("environment") or "node-vanilla"
    entry_point = payload.get("entryPoint") or ""
    res = run_tests(user_code, vis, hid, environment=environment, entry_point=entry_point)
    print(json.dumps(res))
