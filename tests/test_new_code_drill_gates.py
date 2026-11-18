"""Hermetic tests for PRG `new-code-drill` ingest gates (`check_code_drill` & `ingest_ai_code_drill`)."""

from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from code_engine.ai_drill_ingest import (
    AiContractError,
    check_code_drill,
    ingest_ai_code_drill,
)
from code_engine.lint_check import LintToolsMissingError, get_lint_binaries


def _require_lint_tools() -> None:
    if shutil.which("node") is None:
        pytest.skip("node binary not installed on PATH")
    try:
        get_lint_binaries()
    except LintToolsMissingError as exc:
        pytest.skip(str(exc))


def _seed_vault(vault_dir: Path) -> None:
    vault_dir.mkdir(parents=True, exist_ok=True)
    vault_data = {
        "unitCode": "PRG-T09-C01",
        "archetypes": [
            {
                "archetypeKey": "prg-t09-nullish-guard",
                "unitCode": "PRG-T09-C01-U01",
                "level": 1,
                "name": "Nullish Guard",
                "cognitiveTraps": [{"trapTag": "falsy-zero-overwrite", "description": "Using || drops 0."}],
                "qualityChecks": [
                    {
                        "id": "QC-nullish-explicit",
                        "check": "Defaults distinguish null/undefined from 0.",
                        "why": "Using || overwrites legitimate 0 values.",
                        "severity": "must",
                        "knownBad": {
                            "code": "function getLimit(cfg) { return cfg.limit || 10; }",
                            "caughtBy": "review",
                        },
                    }
                ],
                "usedContexts": [],
            },
            {
                "archetypeKey": "prg-t09-immutable-cart",
                "unitCode": "PRG-T09-C01-U01",
                "level": 2,
                "name": "Immutable Cart Update",
                "cognitiveTraps": [{"trapTag": "input-mutation-leak", "description": "Mutates caller array."}],
                "qualityChecks": [
                    {
                        "id": "QC-cart-pure",
                        "check": "Cart update returns a new array without mutating input.",
                        "why": "Mutating input causes subtle state bugs.",
                        "severity": "must",
                        "knownBad": {
                            "code": "function addItem(items, x) { items.push(x); return items; }",
                            "caughtBy": "review",
                        },
                    }
                ],
                "usedContexts": [],
            },
            {
                "archetypeKey": "prg-t09-other-unit-arch",
                "unitCode": "PRG-T09-C01-U02",
                "level": 1,
                "name": "Other Unit Archetype",
                "cognitiveTraps": [{"trapTag": "other-trap", "description": "Other unit trap."}],
                "qualityChecks": [
                    {
                        "id": "QC-other-unit",
                        "check": "Other unit check.",
                        "why": "Isolation test.",
                        "severity": "must",
                        "knownBad": {"code": "const item = 1;", "caughtBy": "review"},
                    }
                ],
                "usedContexts": [],
            },
        ],
    }
    (vault_dir / "PRG-T09-C01.json").write_text(json.dumps(vault_data, indent=2), encoding="utf-8")


def _good_four_problem_draft() -> dict:
    return {
        "unitCode": "PRG-T09-C01-U01",
        "unitTitle": "Nullish & Immutability",
        "environment": "node-vanilla",
        "config": {"questionCount": 4, "difficulty": "ALL", "difficultyMode": "AI Synthesized Engineering Mode"},
        "problems": [
            {
                "id": "Q01",
                "level": 1,
                "category": "Core Skill",
                "archetype": "problem-solving",
                "codeType": "implement",
                "archetypeKey": "prg-t09-nullish-guard",
                "commonTrapTag": "falsy-zero-overwrite",
                "context": "webhook_retry_config",
                "entryPoint": "resolveRetryDelay",
                "prompt": "Implement `resolveRetryDelay(options)` to return `options.delayMs` or default `250` when nullish.",
                "inputHint": "Preserve numeric zero",
                "starterCode": (
                    "function resolveRetryDelay(_options) {\n"
                    "  return null;\n"
                    "}\n"
                    "module.exports = { resolveRetryDelay };\n"
                ),
                "solutionCode": (
                    "function resolveRetryDelay(options) {\n"
                    "  return options?.delayMs ?? 250;\n"
                    "}\n"
                    "module.exports = { resolveRetryDelay };\n"
                ),
                "trapMutant": (
                    "function resolveRetryDelay(options) {\n"
                    "  return (options && options.delayMs) || 250;\n"
                    "}\n"
                    "module.exports = { resolveRetryDelay };\n"
                ),
                "visibleTests": [
                    {
                        "name": "uses configured delay",
                        "testCode": "assert.strictEqual(resolveRetryDelay({ delayMs: 500 }), 500);",
                    },
                    {"name": "defaults when missing", "testCode": "assert.strictEqual(resolveRetryDelay({}), 250);"},
                ],
                "hiddenTests": [
                    {
                        "name": "preserves zero delay",
                        "testCode": "assert.strictEqual(resolveRetryDelay({ delayMs: 0 }), 0);",
                    },
                ],
                "examples": [
                    {
                        "input": "options = { delayMs: 500 }",
                        "output": "500",
                        "explanation": "Returns the configured positive delay directly.",
                        "call": "resolveRetryDelay({ delayMs: 500 })",
                    },
                    {
                        "input": "options = { delayMs: 120 }",
                        "output": "120",
                        "call": "resolveRetryDelay({ delayMs: 120 })",
                    },
                ],
                "constraints": ["delayMs >= 0 when provided"],
                "steps": [{"explain": "Use optional chaining and nullish coalescing."}],
            },
            {
                "id": "Q02",
                "level": 2,
                "category": "Core Skill",
                "archetype": "problem-solving",
                "codeType": "implement",
                "archetypeKey": "prg-t09-nullish-guard",
                "commonTrapTag": "falsy-zero-overwrite",
                "context": "quota_threshold_policy",
                "entryPoint": "resolveQuotaCap",
                "prompt": "Implement `resolveQuotaCap(policy)` returning `policy.maxItems` or `100` when nullish.",
                "inputHint": "Distinguish 0 from nullish",
                "starterCode": (
                    "function resolveQuotaCap(_policy) {\n  return null;\n}\nmodule.exports = { resolveQuotaCap };\n"
                ),
                "solutionCode": (
                    "function resolveQuotaCap(policy) {\n"
                    "  return policy?.maxItems ?? 100;\n"
                    "}\n"
                    "module.exports = { resolveQuotaCap };\n"
                ),
                "trapMutant": (
                    "function resolveQuotaCap(policy) {\n"
                    "  return (policy && policy.maxItems) || 100;\n"
                    "}\n"
                    "module.exports = { resolveQuotaCap };\n"
                ),
                "visibleTests": [
                    {
                        "name": "returns provided cap",
                        "testCode": "assert.strictEqual(resolveQuotaCap({ maxItems: 25 }), 25);",
                    },
                ],
                "hiddenTests": [
                    {"name": "keeps zero cap", "testCode": "assert.strictEqual(resolveQuotaCap({ maxItems: 0 }), 0);"},
                ],
                "examples": [
                    {
                        "input": "policy = { maxItems: 25 }",
                        "output": "25",
                        "call": "resolveQuotaCap({ maxItems: 25 })",
                    },
                    {
                        "input": "policy = {}",
                        "output": "100",
                        "explanation": "Falls back to 100 when maxItems is omitted.",
                        "call": "resolveQuotaCap({})",
                    },
                ],
                "steps": [
                    {"explain": "Read policy?.maxItems safely without throwing on missing policy."},
                    {"explain": "Apply nullish coalescing (??) so 0 is preserved."},
                ],
            },
            {
                "id": "Q03",
                "level": 2,
                "category": "Trap & Edge Case",
                "archetype": "debugging",
                "codeType": "fix-bug",
                "archetypeKey": "prg-t09-immutable-cart",
                "commonTrapTag": "input-mutation-leak",
                "context": "checkout_basket",
                "entryPoint": "appendLineItem",
                "prompt": "Fix `appendLineItem(items, nextItem)` so it returns a new array without mutating `items`.",
                "inputHint": "Avoid in-place array mutation",
                "starterCode": (
                    "function appendLineItem(items, nextItem) {\n"
                    "  items.push(nextItem);\n"
                    "  return items;\n"
                    "}\n"
                    "module.exports = { appendLineItem };\n"
                ),
                "solutionCode": (
                    "function appendLineItem(items, nextItem) {\n"
                    "  return [...items, nextItem];\n"
                    "}\n"
                    "module.exports = { appendLineItem };\n"
                ),
                "trapMutant": (
                    "function appendLineItem(items, nextItem) {\n"
                    "  items.push(nextItem);\n"
                    "  return items;\n"
                    "}\n"
                    "module.exports = { appendLineItem };\n"
                ),
                "visibleTests": [
                    {
                        "name": "does not mutate input array",
                        "testCode": (
                            "const orig = ['sku-1'];\n"
                            "const next = appendLineItem(orig, 'sku-2');\n"
                            "assert.deepStrictEqual(orig, ['sku-1']);\n"
                            "assert.deepStrictEqual(next, ['sku-1', 'sku-2']);\n"
                        ),
                    }
                ],
                "hiddenTests": [
                    {
                        "name": "handles empty basket without mutation",
                        "testCode": (
                            "const empty = [];\n"
                            "const next = appendLineItem(empty, 'sku-9');\n"
                            "assert.strictEqual(empty.length, 0);\n"
                            "assert.deepStrictEqual(next, ['sku-9']);\n"
                        ),
                    }
                ],
                "examples": [
                    {
                        "input": "items = ['sku-1'], nextItem = 'sku-2'",
                        "output": "['sku-1', 'sku-2']",
                        "call": "appendLineItem(['sku-1'], 'sku-2')",
                    },
                    {
                        "input": "items = ['a', 'b'], nextItem = 'c'",
                        "output": "['a', 'b', 'c']",
                        "call": "appendLineItem(['a', 'b'], 'c')",
                    },
                ],
                "steps": [
                    {"explain": "Avoid Array.prototype.push on the input array."},
                    {"explain": "Return a shallow copy with the new item appended."},
                ],
            },
            {
                "id": "Q04",
                "level": 3,
                "category": "Trap & Edge Case",
                "archetype": "problem-solving",
                "codeType": "implement",
                "archetypeKey": "prg-t09-immutable-cart",
                "commonTrapTag": "input-mutation-leak",
                "context": "playlist_queue",
                "entryPoint": "enqueueTrack",
                "prompt": "Implement `enqueueTrack(queue, track)` returning a new queue with `track` at the end.",
                "inputHint": "Return a fresh array",
                "starterCode": (
                    "function enqueueTrack(_queue, _track) {\n  return [];\n}\nmodule.exports = { enqueueTrack };\n"
                ),
                "solutionCode": (
                    "function enqueueTrack(queue, track) {\n"
                    "  return [...queue, track];\n"
                    "}\n"
                    "module.exports = { enqueueTrack };\n"
                ),
                "trapMutant": (
                    "function enqueueTrack(queue, track) {\n"
                    "  queue.push(track);\n"
                    "  return queue;\n"
                    "}\n"
                    "module.exports = { enqueueTrack };\n"
                ),
                "visibleTests": [
                    {
                        "name": "appends track",
                        "testCode": "assert.deepStrictEqual(enqueueTrack(['a'], 'b'), ['a', 'b']);",
                    },
                ],
                "hiddenTests": [
                    {
                        "name": "preserves original queue",
                        "testCode": (
                            "const q = ['intro'];\n"
                            "const res = enqueueTrack(q, 'chorus');\n"
                            "assert.deepStrictEqual(q, ['intro']);\n"
                            "assert.deepStrictEqual(res, ['intro', 'chorus']);\n"
                        ),
                    }
                ],
                "examples": [
                    {
                        "input": "queue = ['a'], track = 'b'",
                        "output": "['a', 'b']",
                        "call": "enqueueTrack(['a'], 'b')",
                    },
                    {
                        "input": "queue = ['intro', 'verse'], track = 'outro'",
                        "output": "['intro', 'verse', 'outro']",
                        "call": "enqueueTrack(['intro', 'verse'], 'outro')",
                    },
                ],
                "steps": [
                    {"explain": "Avoid mutating the caller's queue in place."},
                    {"explain": "Spread the original queue into a new array with track appended."},
                ],
            },
        ],
        "blindSolve": [
            {
                "problemId": "Q01",
                "solutionCode": (
                    "function resolveRetryDelay(options) {\n"
                    "  if (!options || options.delayMs === null || options.delayMs === undefined) {\n"
                    "    return 250;\n"
                    "  }\n"
                    "  return options.delayMs;\n"
                    "}\n"
                    "module.exports = { resolveRetryDelay };\n"
                ),
                "ambiguous": False,
                "note": "Solved from prompt and visible tests.",
            },
            {
                "problemId": "Q02",
                "solutionCode": (
                    "function resolveQuotaCap(policy) {\n"
                    "  if (!policy || policy.maxItems == null) {\n"
                    "    return 100;\n"
                    "  }\n"
                    "  return policy.maxItems;\n"
                    "}\n"
                    "module.exports = { resolveQuotaCap };\n"
                ),
                "ambiguous": False,
                "note": "Solved from prompt and visible tests.",
            },
            {
                "problemId": "Q03",
                "solutionCode": (
                    "function appendLineItem(items, nextItem) {\n"
                    "  return items.concat([nextItem]);\n"
                    "}\n"
                    "module.exports = { appendLineItem };\n"
                ),
                "ambiguous": False,
                "note": "Solved from prompt and visible tests.",
            },
            {
                "problemId": "Q04",
                "solutionCode": (
                    "function enqueueTrack(queue, track) {\n"
                    "  return queue.concat([track]);\n"
                    "}\n"
                    "module.exports = { enqueueTrack };\n"
                ),
                "ambiguous": False,
                "note": "Solved from prompt and visible tests.",
            },
        ],
        "review": {"verdict": "pass", "note": "All 4 problems pass scope, mix, rubric, and zero-leak checks."},
    }


def test_good_draft_passes_all_gates(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert errors == []


def test_ingest_writes_expected_files_in_tmp_dirs(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    data_dir = tmp_path / "data"
    ws_dir = tmp_path / "ws"
    _seed_vault(vault_dir)

    draft = _good_four_problem_draft()
    saved = ingest_ai_code_drill(
        deepcopy(draft),
        data_root=str(data_dir),
        workspace_root=str(ws_dir),
        vault_dir=str(vault_dir),
    )

    assert saved["drillId"] == "DRL-PRG-T09-C01-U01-01"
    assert saved["topicCode"] == "PRG-T09"
    assert saved["chapterCode"] == "PRG-T09-C01"

    drill_file = data_dir / "PRG-T09-C01-U01" / "DRL-PRG-T09-C01-U01-01.json"
    assert drill_file.exists()

    ingested = json.loads(drill_file.read_text(encoding="utf-8"))
    assert ingested["blindSolve"] == [
        {"problemId": "Q01", "passed": True},
        {"problemId": "Q02", "passed": True},
        {"problemId": "Q03", "passed": True},
        {"problemId": "Q04", "passed": True},
    ]
    assert all("solutionCode" not in entry for entry in ingested["blindSolve"])

    ws_path = ws_dir / "drills" / "workspace" / "DRL-PRG-T09-C01-U01-01"
    assert (ws_path / "package.json").exists()
    assert (ws_path / "README.md").exists()
    assert (ws_path / "eslint.config.mjs").exists()
    assert (ws_path / "Q01_resolveRetryDelay.js").exists()

    vault_after = json.loads((vault_dir / "PRG-T09-C01.json").read_text(encoding="utf-8"))
    arch0 = vault_after["archetypes"][0]
    assert set(arch0["usedContexts"]) == {"webhook_retry_config", "quota_threshold_policy"}


def test_gate_refuses_leaky_starter(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    draft["problems"][0]["starterCode"] = (
        "function resolveRetryDelay(options) {\n"
        "  // BUG: fix this return\n"
        "  return null;\n"
        "}\n"
        "module.exports = { resolveRetryDelay };\n"
    )

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("Anti-Spoonfeeding" in e or "spoiler comment" in e for e in errors)


def test_gate_refuses_starter_passing_all_visible_tests(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    # Starter already passes all visible tests (missing only hidden zero check)
    draft["problems"][0]["starterCode"] = (
        "function resolveRetryDelay(options) {\n"
        "  return (options && options.delayMs) || 250;\n"
        "}\n"
        "module.exports = { resolveRetryDelay };\n"
    )

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("unexpectedly passed all visible tests" in e for e in errors)


def test_gate_refuses_trap_mutant_not_caught_by_hidden_tests(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    # Trap mutant is identical to solutionCode so hidden tests fail to catch it
    draft["problems"][0]["trapMutant"] = draft["problems"][0]["solutionCode"]

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("Trap mutant" in e and "passed all hidden tests" in e for e in errors)


def test_gate_refuses_missing_review(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    del draft["review"]

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("review" in e.lower() for e in errors)


def test_gate_refuses_missing_blind_solve(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    del draft["blindSolve"]

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("blindSolve" in e for e in errors)


def test_gate_refuses_blind_solve_failing_hidden_test(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    # Passes visible tests, fails hidden zero-delay test
    draft["blindSolve"][0]["solutionCode"] = (
        "function resolveRetryDelay(options) {\n"
        "  return (options && options.delayMs) || 250;\n"
        "}\n"
        "module.exports = { resolveRetryDelay };\n"
    )

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("[Q01]" in e and "failed tests" in e for e in errors)


def test_gate_refuses_blind_solve_identical_to_reference(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    # Identical to reference solutionCode after whitespace normalisation
    draft["blindSolve"][0]["solutionCode"] = (
        "function   resolveRetryDelay(options) {   return options?.delayMs ?? 250; }\n"
        "module.exports = { resolveRetryDelay };"
    )

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("[Q01]" in e and "identical to reference solutionCode" in e for e in errors)


def test_gate_refuses_self_reported_blind_solve_without_code(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    draft["blindSolve"] = [{"problemId": p["id"], "passed": True} for p in draft["problems"]]

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("missing 'solutionCode'" in e for e in errors)


def test_gate_refuses_out_of_scope_archetype(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    # prg-t09-other-unit-arch belongs to U02, not U01
    draft["problems"][0]["archetypeKey"] = "prg-t09-other-unit-arch"
    draft["problems"][0]["commonTrapTag"] = "other-trap"

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("out of scope" in e for e in errors)


def test_gate_refuses_lint_failure(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    draft["problems"][0]["solutionCode"] = (
        "function resolveRetryDelay(options) {\n"
        "  var delay = options?.delayMs ?? 250;\n"
        "  return delay;\n"
        "}\n"
        "module.exports = { resolveRetryDelay };\n"
    )

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("no-var" in e for e in errors)


def test_gate_refuses_bad_mix_and_duplicate_context(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    # Make all 4 problems 'implement' (no non-implement item) and duplicate (archetypeKey, context)
    draft["problems"][2]["archetype"] = "problem-solving"
    draft["problems"][2]["codeType"] = "implement"
    draft["problems"][1]["context"] = draft["problems"][0]["context"]

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("non-implement" in e for e in errors)
    assert any("Duplicate" in e for e in errors)

    with pytest.raises(AiContractError):
        ingest_ai_code_drill(
            draft,
            data_root=str(tmp_path / "data"),
            workspace_root=str(tmp_path / "ws"),
            vault_dir=str(vault_dir),
        )


def test_gate_refuses_unused_import_in_stub_starter(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    draft["problems"][0]["starterCode"] = (
        "const path = require('path');\n"
        "function resolveRetryDelay(_options) {\n"
        "  return null;\n"
        "}\n"
        "module.exports = { resolveRetryDelay };\n"
    )

    errors = check_code_drill(draft, vault_dir=str(vault_dir))
    assert any("starterCode failed Layer 2 lint" in e and "no-unused-vars" in e for e in errors)


def test_gate_allows_starter_lint_via_drill_override(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _good_four_problem_draft()
    draft["lintOverrides"] = [{"rule": "no-var", "reason": "Legacy starter intentionally uses var"}]
    draft["problems"][2]["starterCode"] = (
        "function appendLineItem(items, nextItem) {\n"
        "  var copy = items;\n"
        "  copy.push(nextItem);\n"
        "  return copy;\n"
        "}\n"
        "module.exports = { appendLineItem };\n"
    )

    assert check_code_drill(draft, vault_dir=str(vault_dir)) == []


def test_gate_starter_lint_expected_requires_fix_or_refactor_and_prompt_mention(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)

    # 1. Rejected on implement stub
    draft_stub = _good_four_problem_draft()
    draft_stub["problems"][0]["starterLintExpected"] = [{"rule": "no-unused-vars", "reason": "Stub import"}]
    errors_stub = check_code_drill(draft_stub, vault_dir=str(vault_dir))
    assert any("only allowed on fix-bug or refactor" in e for e in errors_stub)

    # 2. Rejected on fix-bug when prompt does not mention structural improvement
    draft_no_prompt = _good_four_problem_draft()
    draft_no_prompt["problems"][2]["starterCode"] = (
        "function appendLineItem(items, nextItem) {\n"
        "  var copy = items;\n"
        "  copy.push(nextItem);\n"
        "  return copy;\n"
        "}\n"
        "module.exports = { appendLineItem };\n"
    )
    draft_no_prompt["problems"][2]["starterLintExpected"] = [
        {"rule": "no-var", "reason": "Legacy starter uses var before refactor"}
    ]
    errors_no_prompt = check_code_drill(draft_no_prompt, vault_dir=str(vault_dir))
    assert any("structure must be improved too" in e for e in errors_no_prompt)

    # 3. Accepted when prompt mentions refactor/simplify/split/complexity
    draft_ok = deepcopy(draft_no_prompt)
    draft_ok["problems"][2]["prompt"] = (
        "Fix and refactor `appendLineItem(items, nextItem)` so it returns a new array without mutating `items`."
    )
    assert check_code_drill(draft_ok, vault_dir=str(vault_dir)) == []


def test_underscore_emphasis_check_ignores_backticks_and_code_blocks(tmp_path):
    _require_lint_tools()
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)

    # 1. __ inside inline backticks and fenced code block is allowed
    draft = _good_four_problem_draft()
    draft["problems"][0]["prompt"] = (
        "Implement `resolveRetryDelay(options)` using `__dirname` fallback or:\n"
        "```js\n"
        "const root = __dirname;\n"
        "```\n"
        "- Return `options.delayMs` or `250` when nullish."
    )
    assert check_code_drill(draft, vault_dir=str(vault_dir)) == []

    # 2. __ outside backticks (Markdown emphasis) is still rejected
    draft_bad = _good_four_problem_draft()
    draft_bad["problems"][0]["prompt"] = "Implement `resolveRetryDelay(options)` with __strict__ fallback to `250`."
    errors = check_code_drill(draft_bad, vault_dir=str(vault_dir))
    assert any("Markdown underscore emphasis (__)" in e for e in errors)
