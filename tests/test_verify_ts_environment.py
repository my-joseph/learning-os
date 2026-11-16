"""verify_problem must run a TypeScript solution as TypeScript (pilot issue c28868)."""

import shutil

import pytest

from code_engine.verify import verify_problem

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _ts_problem() -> dict:
    return {
        "id": "Q01",
        "archetype": "problem-solving",
        "prompt": "Clamp a percentage into the range 0 to 100.",
        "steps": [{"explain": "Bound the value from both sides."}],
        "entryPoint": "clampPercent",
        "solutionCode": (
            "export function clampPercent(value: number): number {\n"
            "  return Math.min(100, Math.max(0, value));\n"
            "}\n"
        ),
        "visibleTests": [{"name": "clamps high", "testCode": "assert.strictEqual(clampPercent(150), 100);"}],
        "hiddenTests": [{"name": "clamps low", "testCode": "assert.strictEqual(clampPercent(-5), 0);"}],
    }


def test_run_tests_gets_typescript_environment(monkeypatch):
    seen = {}
    import code_engine.verify as verify_mod

    def fake_run_tests(sol, visible, hidden, **kwargs):
        seen.update(kwargs)
        return {"allPassed": True, "passed": 2, "total": 2, "results": []}

    import code_engine.test_runner as runner_mod

    monkeypatch.setattr(runner_mod, "run_tests", fake_run_tests)
    monkeypatch.setattr(verify_mod, "verify_quality_gates", lambda *a, **k: None)
    try:
        verify_problem(_ts_problem(), environment="typescript-strict")
    except Exception:
        pass  # other gates may reject the minimal fixture; only the runner call matters here
    assert seen.get("environment") == "typescript-strict"
    assert seen.get("entry_point") == "clampPercent"
