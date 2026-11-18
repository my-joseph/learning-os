"""Hermetic tests for PRG `examples` and `constraints` ingest gates (ai_drill_ingest & lab_ingest)."""

from __future__ import annotations

import json
import os
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from code_engine import lab_ingest
from code_engine.ai_drill_ingest import (
    check_code_drill,
    ingest_ai_code_drill,
    validate_ai_code_contract,
)
from code_engine.lint_check import LintToolsMissingError, get_lint_binaries

REPO_ROOT = Path(__file__).resolve().parent.parent


def _require_node_and_lint() -> None:
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
                "archetypeKey": "prg-t09-search-insert",
                "unitCode": "PRG-T09-C01-U01",
                "level": 1,
                "name": "Sorted Insertion Index",
                "cognitiveTraps": [{"trapTag": "off-by-one-bound", "description": "Stops before last index."}],
                "qualityChecks": [
                    {
                        "id": "QC-search-pure",
                        "check": "Does not mutate the input array.",
                        "why": "Callers reuse the sorted array.",
                        "severity": "must",
                        "knownBad": {
                            "code": "function searchInsert(nums, t) { nums.push(t); return 0; }",
                            "caughtBy": "review",
                        },
                    }
                ],
                "usedContexts": [],
            }
        ],
    }
    (vault_dir / "PRG-T09-C01.json").write_text(json.dumps(vault_data, indent=2), encoding="utf-8")


def _ts_drill_draft() -> dict[str, Any]:
    return {
        "unitCode": "PRG-T09-C01-U01",
        "unitTitle": "Sorted Search",
        "environment": "typescript-strict",
        "config": {"questionCount": 1, "difficulty": "ALL", "difficultyMode": "AI Synthesized Engineering Mode"},
        "problems": [
            {
                "id": "Q01",
                "level": 1,
                "category": "Core Skill",
                "archetype": "problem-solving",
                "codeType": "implement",
                "archetypeKey": "prg-t09-search-insert",
                "commonTrapTag": "off-by-one-bound",
                "context": "catalog_index_lookup",
                "entryPoint": "searchInsert",
                "prompt": (
                    "**Task**\n"
                    "Implement `searchInsert(nums, target)` returning the index where `target` is found or would be inserted.\n\n"
                    "**Requirements**\n"
                    "- Input `nums` is sorted in ascending order with distinct integers.\n"
                    "- Do not mutate `nums`."
                ),
                "inputHint": "Return a non-negative integer index.",
                "starterCode": (
                    "export function searchInsert(_nums: readonly number[], _target: number): number {\n"
                    "  return -1;\n"
                    "}\n"
                ),
                "solutionCode": (
                    "export function searchInsert(nums: readonly number[], target: number): number {\n"
                    "  let left = 0;\n"
                    "  let right = nums.length;\n"
                    "  while (left < right) {\n"
                    "    const mid = (left + right) >> 1;\n"
                    "    if (nums[mid]! < target) left = mid + 1;\n"
                    "    else right = mid;\n"
                    "  }\n"
                    "  return left;\n"
                    "}\n"
                ),
                "trapMutant": (
                    "export function searchInsert(nums: readonly number[], target: number): number {\n"
                    "  for (let i = 0; i < nums.length - 1; i++) {\n"
                    "    if (nums[i]! >= target) return i;\n"
                    "  }\n"
                    "  return 0;\n"
                    "}\n"
                ),
                "visibleTests": [
                    {
                        "name": "finds existing value",
                        "testCode": "assert.strictEqual(searchInsert([1, 3, 5, 6], 5), 2);",
                    },
                    {
                        "name": "returns zero for empty list",
                        "testCode": "assert.strictEqual(searchInsert([], 4), 0);",
                    },
                ],
                "hiddenTests": [
                    {
                        "name": "inserts past end of array",
                        "testCode": "assert.strictEqual(searchInsert([1, 3, 5, 6], 7), 4);",
                    }
                ],
                "examples": [
                    {
                        "input": "nums = [1, 3, 5, 6], target = 5",
                        "output": "2",
                        "explanation": "5 is present at index 2.",
                        "call": "searchInsert([1, 3, 5, 6], 5)",
                    },
                    {
                        "input": "nums = [1, 3, 5, 6], target = 2",
                        "output": "1",
                        "call": "searchInsert([1, 3, 5, 6], 2)",
                    },
                ],
                "constraints": ["0 <= nums.length <= 10^4", "nums contains distinct values sorted in ascending order"],
                "steps": [{"explain": "Binary search for the lower bound index where nums[i] >= target."}],
            }
        ],
        "blindSolve": [
            {
                "problemId": "Q01",
                "solutionCode": (
                    "export function searchInsert(nums: readonly number[], target: number): number {\n"
                    "  const idx = nums.findIndex((value) => value >= target);\n"
                    "  return idx === -1 ? nums.length : idx;\n"
                    "}\n"
                ),
                "ambiguous": False,
                "note": "Linear scan lower bound.",
            }
        ],
        "review": {"verdict": "pass", "note": "Clean contract, normal examples, hidden test catches trap."},
    }


def test_drill_examples_js_literals_and_ingest_hermetic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _require_node_and_lint()
    monkeypatch.chdir(tmp_path)
    tools_link = tmp_path / "tools"
    if not tools_link.exists():
        os.symlink(REPO_ROOT / "tools", tools_link)

    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)
    draft = _ts_drill_draft()

    assert check_code_drill(draft, vault_dir=str(vault_dir)) == []
    saved = ingest_ai_code_drill(
        deepcopy(draft),
        data_root=str(tmp_path / "drills" / "data"),
        workspace_root=str(tmp_path),
        vault_dir=str(vault_dir),
    )
    assert len(saved["problems"][0]["examples"]) == 2
    assert saved["problems"][0]["constraints"] == [
        "0 <= nums.length <= 10^4",
        "nums contains distinct values sorted in ascending order",
    ]


def test_drill_examples_support_js_object_and_map_literals(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _require_node_and_lint()
    monkeypatch.chdir(tmp_path)
    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)

    draft = {
        "unitCode": "PRG-T09-C01-U01",
        "environment": "node-vanilla",
        "problems": [
            {
                "id": "Q01",
                "level": 1,
                "category": "Core Skill",
                "archetype": "problem-solving",
                "codeType": "implement",
                "archetypeKey": "prg-t09-search-insert",
                "commonTrapTag": "off-by-one-bound",
                "context": "summary_record",
                "entryPoint": "summarizeRange",
                "prompt": "Implement `summarizeRange(values)` returning `{ count, first }` or `undefined` if empty.",
                "starterCode": "function summarizeRange(_values) { return null; }\nmodule.exports = { summarizeRange };\n",
                "solutionCode": (
                    "function summarizeRange(values) {\n"
                    "  if (values.length === 0) return undefined;\n"
                    "  return { count: values.length, first: values[0] };\n"
                    "}\n"
                    "module.exports = { summarizeRange };\n"
                ),
                "trapMutant": (
                    "function summarizeRange(values) {\n"
                    "  return { count: values.length, first: values[0] };\n"
                    "}\n"
                    "module.exports = { summarizeRange };\n"
                ),
                "visibleTests": [
                    {
                        "name": "summarizes array",
                        "testCode": "assert.deepStrictEqual(summarizeRange([4, 9]), { count: 2, first: 4 });",
                    },
                ],
                "hiddenTests": [
                    {
                        "name": "returns undefined for empty",
                        "testCode": "assert.strictEqual(summarizeRange([]), undefined);",
                    },
                ],
                "examples": [
                    {
                        "input": "values = [4, 9]",
                        "output": "{ count: 2, first: 4 }",
                        "call": "summarizeRange([4, 9])",
                    },
                    {
                        "input": "values = ['ok']",
                        "output": "{ count: 1, first: 'ok' }",
                        "call": "summarizeRange(['ok'])",
                    },
                ],
                "steps": [{"explain": "Check empty input before reading index 0."}],
            }
        ],
        "blindSolve": [
            {
                "problemId": "Q01",
                "solutionCode": (
                    "function summarizeRange(values) {\n"
                    "  return values.length ? { count: values.length, first: values[0] } : undefined;\n"
                    "}\n"
                    "module.exports = { summarizeRange };\n"
                ),
                "ambiguous": False,
                "note": "ok",
            }
        ],
        "review": {"verdict": "pass", "note": "ok"},
    }
    assert check_code_drill(draft, vault_dir=str(vault_dir)) == []


def test_drill_gate_rejects_missing_wrong_count_wrong_output_and_hidden_leak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _require_node_and_lint()
    monkeypatch.chdir(tmp_path)
    tools_link = tmp_path / "tools"
    if not tools_link.exists():
        os.symlink(REPO_ROOT / "tools", tools_link)

    vault_dir = tmp_path / "vault"
    _seed_vault(vault_dir)

    # 1. Missing examples
    d_missing = _ts_drill_draft()
    del d_missing["problems"][0]["examples"]
    errs_missing = check_code_drill(d_missing, vault_dir=str(vault_dir))
    assert any("examples" in e and "2-3" in e for e in errs_missing)

    # 2. Only 1 example
    d_one = _ts_drill_draft()
    d_one["problems"][0]["examples"] = d_one["problems"][0]["examples"][:1]
    errs_one = check_code_drill(d_one, vault_dir=str(vault_dir))
    assert any("2-3 examples" in e for e in errs_one)

    # 3. 4 examples
    d_four = _ts_drill_draft()
    d_four["problems"][0]["examples"] = d_four["problems"][0]["examples"] * 2
    errs_four = check_code_drill(d_four, vault_dir=str(vault_dir))
    assert any("2-3 examples" in e for e in errs_four)

    # 4. Wrong output
    d_wrong = _ts_drill_draft()
    d_wrong["problems"][0]["examples"][1]["output"] = "99"
    errs_wrong = check_code_drill(d_wrong, vault_dir=str(vault_dir))
    assert any("Example 2 failed verification" in e for e in errs_wrong)

    # 5. Zero-leak: example call matches hidden test (even with different whitespace)
    d_leak = _ts_drill_draft()
    d_leak["problems"][0]["examples"][1] = {
        "input": "nums = [1,3,5,6], target = 7",
        "output": "4",
        "call": "searchInsert([1,3,5,6],7)",
    }
    errs_leak = check_code_drill(d_leak, vault_dir=str(vault_dir))
    assert any("Zero-Leak Guard violated" in e and "Example 2" in e for e in errs_leak)

    # 6. Bad constraints
    d_bad_con = _ts_drill_draft()
    d_bad_con["problems"][0]["constraints"] = [""]
    errs_con = check_code_drill(d_bad_con, vault_dir=str(vault_dir))
    assert any("constraints[1]" in e for e in errs_con)


def test_existing_problem_without_examples_still_passes_validate_ai_code_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _require_node_and_lint()
    monkeypatch.chdir(tmp_path)
    prob = _ts_drill_draft()["problems"][0]
    del prob["examples"]
    del prob["constraints"]
    assert validate_ai_code_contract(prob, environment="typescript-strict", require_trap_mutant=True) is True


def _make_lab_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    labs_dir = tmp_path / "labs"
    lab_id = "LAB-PRG-T01-C01-98"
    lab_dir = labs_dir / lab_id
    ref_dir = labs_dir / "_reference" / lab_id
    tools_link = tmp_path / "tools"
    if not tools_link.exists():
        os.symlink(REPO_ROOT / "tools", tools_link)

    for d in (lab_dir / "src", lab_dir / "tests", ref_dir / "src", ref_dir / "hidden"):
        d.mkdir(parents=True, exist_ok=True)

    tsconfig = {
        "compilerOptions": {
            "target": "ES2024",
            "module": "NodeNext",
            "moduleResolution": "NodeNext",
            "strict": True,
            "noEmit": True,
            "allowImportingTsExtensions": True,
            "skipLibCheck": True,
        },
        "include": ["src/**/*.ts"],
    }
    (lab_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2), encoding="utf-8")
    (ref_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2), encoding="utf-8")
    (lab_dir / "eslint.config.js").write_text(
        'import { prgConfig } from "../../tools/lint/base.js";\nexport default prgConfig();\n',
        encoding="utf-8",
    )
    (lab_dir / "package.json").write_text(
        json.dumps(
            {
                "name": "lab-ex-test",
                "version": "1.0.0",
                "type": "module",
                "scripts": {
                    "test": "node --experimental-strip-types --test tests/*.test.ts",
                    "test:reference": "true",
                    "lint": "true",
                    "typecheck": "true",
                    "check": "true",
                    "check:reference": "true",
                    "check:hidden": "true",
                },
            }
        ),
        encoding="utf-8",
    )
    (lab_dir / "README.md").write_text("# Retry\n\n### M1 — Counter\nImplement `consumeRetry`.\n", encoding="utf-8")
    (lab_dir / "src" / "budget.ts").write_text(
        'export function consumeRetry(_budget: number, _cost: number): number | null {\n  throw new Error("TODO [M1]");\n}\n',
        encoding="utf-8",
    )
    (ref_dir / "src" / "budget.ts").write_text(
        "export function consumeRetry(budget: number, cost: number): number | null {\n"
        "  if (cost < 0 || budget < cost) return null;\n"
        "  return budget - cost;\n"
        "}\n",
        encoding="utf-8",
    )
    (lab_dir / "tests" / "m1_budget.test.ts").write_text(
        'import test from "node:test";\nimport assert from "node:assert";\n'
        'const srcDir = process.env.LAB_SRC_DIR || "../src";\n'
        "const { consumeRetry } = await import(`${srcDir}/budget.ts`);\n"
        'test("deducts cost", () => { assert.strictEqual(consumeRetry(4, 1), 3); });\n',
        encoding="utf-8",
    )
    (ref_dir / "hidden" / "m1_budget.test.ts").write_text(
        'import test from "node:test";\nimport assert from "node:assert";\n'
        'const srcDir = process.env.LAB_SRC_DIR || "../src";\n'
        "const { consumeRetry } = await import(`${srcDir}/budget.ts`);\n"
        'test("[M1-HIDDEN-01] rejects overspend", () => { assert.strictEqual(consumeRetry(0, 1), null); });\n',
        encoding="utf-8",
    )
    cfg: dict[str, Any] = {
        "labId": lab_id,
        "title": "Retry Engine",
        "chapterCode": "PRG-T01-C01",
        "unitsUsed": ["PRG-T01-C01-U02"],
        "kind": "chapter-lab",
        "level": 2,
        "domain": "retry-engine",
        "targetsWeakSpots": ["U-names"],
        "milestones": [
            {
                "id": "M1",
                "title": "Counter",
                "goal": "Deduct retry cost.",
                "units": ["PRG-T01-C01-U02"],
                "qualityChecks": ["U-names"],
                "visibleTests": "tests/m1_*.test.ts",
                "examples": [
                    {"input": "budget = 4, cost = 1", "output": "3", "call": "consumeRetry(4, 1)"},
                    {"input": "budget = 6, cost = 2", "output": "4", "call": "consumeRetry(6, 2)"},
                ],
                "constraints": ["budget >= 0"],
                "trapMutant": {
                    "files": {
                        "src/budget.ts": (
                            "export function consumeRetry(budget: number, cost: number): number | null {\n"
                            "  return budget - cost;\n"
                            "}\n"
                        )
                    }
                },
            }
        ],
        "blindSolve": [
            {
                "milestone": "M1",
                "files": {
                    "src/budget.ts": (
                        "export function consumeRetry(remaining: number, spend: number): number | null {\n"
                        "  return spend >= 0 && remaining >= spend ? remaining - spend : null;\n"
                        "}\n"
                    )
                },
                "ambiguous": False,
                "note": "ok",
            }
        ],
        "review": {"verdict": "pass", "note": "Clean."},
    }
    (lab_dir / "lab.config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    id_map_path = tmp_path / "id_map.json"
    id_map_path.write_text(json.dumps({"PRG-T01-C01-U02": {"id": "p1", "title": "Closures"}}), encoding="utf-8")
    return lab_dir, ref_dir, id_map_path


def test_lab_examples_gate_validates_and_rejects_bad_and_leaky(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _require_node_and_lint()
    monkeypatch.chdir(tmp_path)
    lab_dir, ref_dir, id_map_path = _make_lab_fixture(tmp_path)
    cfg_path = lab_dir / "lab.config.json"
    base_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    # 1. Missing examples -> rejected by check_lab & finalise_lab
    no_ex = deepcopy(base_cfg)
    del no_ex["milestones"][0]["examples"]
    cfg_path.write_text(json.dumps(no_ex, indent=2), encoding="utf-8")
    errs = lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert any("Missing 'examples'" in e for e in errs)
    with pytest.raises(ValueError, match="Missing 'examples'"):
        lab_ingest.finalise_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)

    # 2. Wrong example output -> rejected
    bad_out = deepcopy(base_cfg)
    bad_out["milestones"][0]["examples"][0]["output"] = "999"
    cfg_path.write_text(json.dumps(bad_out, indent=2), encoding="utf-8")
    errs_out = lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert any("Example 1 failed verification" in e for e in errs_out)

    # 3. Zero-leak: example call matching hidden test -> rejected
    leak_cfg = deepcopy(base_cfg)
    leak_cfg["milestones"][0]["examples"][1] = {
        "input": "budget = 0, cost = 1",
        "output": "null",
        "call": "consumeRetry(0,1)",
    }
    cfg_path.write_text(json.dumps(leak_cfg, indent=2), encoding="utf-8")
    errs_leak = lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert any("Zero-Leak Guard violated" in e and "Example 2" in e for e in errs_leak)

    # 4. Valid config passes check_lab and finalise_lab preserves examples & constraints
    cfg_path.write_text(json.dumps(base_cfg, indent=2), encoding="utf-8")
    assert lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True) == []
    final_cfg = lab_ingest.finalise_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert len(final_cfg["milestones"][0]["examples"]) == 2
    assert final_cfg["milestones"][0]["constraints"] == ["budget >= 0"]
