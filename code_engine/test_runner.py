# -*- coding: utf-8 -*-
"""
Test runner for Coding Katas and Implementation Problems.
Executes student code against Visible Tests and Hidden Tests in a sandboxed Node.js subprocess.
Produces structured JSON reports with test statuses, durations, errors, and score calculation.
"""

import json
import os
import subprocess
import sys
import tempfile


def assemble_harness(user_code: str, visible_tests: list, hidden_tests: list) -> str:
    """
    Creates an executable Node.js script bundling user code, an asynchronous test harness,
    and assertions for both visible and hidden test suites.
    """
    harness = """
const { performance } = require('perf_hooks');
const assert = require('assert');

// --- User Implementation ---
{USER_CODE}

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

    script = harness.replace("{USER_CODE}", user_code)
    script = script.replace("{HIDDEN_TOTAL}", str(len(hidden_tests)))
    script = script.replace("{VISIBLE_BLOCKS}", "\n".join(visible_blocks))
    script = script.replace("{HIDDEN_BLOCKS}", "\n".join(hidden_blocks))
    return script


def run_tests(user_code: str, visible_tests: list, hidden_tests: list, timeout_sec: float = 4.0) -> dict:
    """
    Runs the assembled test suite in Node.js subprocess and returns the parsed report dict.
    """
    script = assemble_harness(user_code, visible_tests, hidden_tests)

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(script)
        temp_path = f.name

    try:
        proc = subprocess.run(
            ["node", temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        stdout = proc.stdout
        stderr = proc.stderr

        if "__TEST_REPORT_JSON_START__" in stdout:
            parts = stdout.split("__TEST_REPORT_JSON_START__")[1].split("__TEST_REPORT_JSON_END__")
            report = json.loads(parts[0].strip())
            report["rawOutput"] = stdout
            return report
        else:
            return {
                "allPassed": false,
                "score": 0,
                "passedCount": 0,
                "totalCount": len(visible_tests) + len(hidden_tests),
                "visibleResults": [
                    {
                        "name": "Execution failure",
                        "passed": False,
                        "error": stderr or stdout or "Script exited unexpectedly",
                    }
                ],
                "hiddenPassed": 0,
                "hiddenTotal": len(hidden_tests),
                "executionTimeMs": 0,
                "rawOutput": stdout + "\n" + stderr,
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
        try:
            os.remove(temp_path)
        except OSError:
            pass


if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    user_code = payload.get("userCode", "")
    vis = payload.get("visibleTests", [])
    hid = payload.get("hiddenTests", [])
    res = run_tests(user_code, vis, hid)
    print(json.dumps(res))
