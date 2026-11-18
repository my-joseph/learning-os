"""Hermetic tests for new-project lab tooling: lab_ingest, lab review_run, review_record, weak_spots, lab_sync."""

from __future__ import annotations

import copy
import json
import os
import shutil
from pathlib import Path
from typing import Any

import pytest

from code_engine import lab_ingest, review_run
from code_engine.lint_check import LintToolsMissingError, get_lint_binaries
from notion_sync import lab_sync
from scripts import review_record, weak_spots

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_c04_lab_has_generated_milestone_commands_and_scenario_readme(monkeypatch, capsys):
    lab_dir = REPO_ROOT / "labs" / "LAB-PRG-T01-C04-02"
    config = json.loads((lab_dir / "lab.config.json").read_text(encoding="utf-8"))
    package = json.loads((lab_dir / "package.json").read_text(encoding="utf-8"))
    readme = (lab_dir / "README.md").read_text(encoding="utf-8")
    assert config["scenario"] in readme
    for milestone in config["milestones"]:
        key = milestone["id"].lower()
        assert f"test:{key}" in package["scripts"]
        assert f"check:{key}" in package["scripts"]
        assert milestone["title"] in readme

    from labs.common import review

    monkeypatch.chdir(lab_dir)
    monkeypatch.setattr("sys.argv", ["review", "m3"])
    assert review.main() == 0
    assert "ตรวจโค้ด LAB-PRG-T01-C04-02 M3" in capsys.readouterr().out


def _require_node_and_lint() -> None:
    if shutil.which("node") is None:
        pytest.skip("node binary not installed on PATH")
    try:
        get_lint_binaries()
    except LintToolsMissingError as exc:
        pytest.skip(str(exc))


def _make_fixture_lab(tmp_path: Path, *, kind: str = "chapter-lab") -> tuple[Path, Path, Path]:
    """Create a minimal valid TS fixture lab + _reference + id_map in tmp_path."""
    labs_dir = tmp_path / "labs"
    lab_id = "LAB-PRG-T01-C01-99"
    lab_dir = labs_dir / lab_id
    ref_dir = labs_dir / "_reference" / lab_id

    # Symlink tools/ so eslint.config.js (`../../tools/lint/base.js`) resolves identically.
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
    pkg = {
        "name": "lab-prg-t01-c01-99",
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "test": "node --experimental-strip-types --test tests/*.test.ts",
            "test:reference": "LAB_SRC_DIR=../../_reference/LAB-PRG-T01-C01-99/src node --experimental-strip-types --test tests/*.test.ts",
            "lint": "../../tools/lint/node_modules/.bin/eslint --format ../../tools/lint/format.js src",
            "typecheck": "../../tools/lint/node_modules/.bin/tsc --noEmit",
            "check": "npm test && npm run lint && npm run typecheck",
            "check:reference": "npm run test:reference",
            "check:hidden": "LAB_SRC_DIR=../../_reference/LAB-PRG-T01-C01-99/src node --experimental-strip-types --test ../../_reference/LAB-PRG-T01-C01-99/hidden/*.test.ts",
        },
    }
    (lab_dir / "package.json").write_text(json.dumps(pkg, indent=2), encoding="utf-8")
    (lab_dir / "README.md").write_text(
        "# Retry Budget\n\n## M1: Budget Counter\nImplement `consumeRetry(budget, cost)` returning remaining budget or `null`.\n",
        encoding="utf-8",
    )

    stub_code = (
        "export function consumeRetry(_budget: number, _cost: number): number | null {\n"
        '  throw new Error("TODO [M1]: implement consumeRetry");\n'
        "}\n"
    )
    ref_code = (
        "export function consumeRetry(budget: number, cost: number): number | null {\n"
        "  if (cost < 0 || budget < cost) {\n"
        "    return null;\n"
        "  }\n"
        "  return budget - cost;\n"
        "}\n"
    )
    blind_code = (
        "export function consumeRetry(remaining: number, spend: number): number | null {\n"
        "  if (spend < 0) return null;\n"
        "  const next = remaining - spend;\n"
        "  return next < 0 ? null : next;\n"
        "}\n"
    )
    trap_mutant_code = (
        "export function consumeRetry(budget: number, cost: number): number | null {\n"
        "  if (cost < 0) {\n"
        "    return null;\n"
        "  }\n"
        "  // Trap: forgets budget < cost boundary when budget === 0 and cost === 1\n"
        "  return budget >= 0 ? budget - cost : null;\n"
        "}\n"
    )

    (lab_dir / "src" / "budget.ts").write_text(stub_code, encoding="utf-8")
    (ref_dir / "src" / "budget.ts").write_text(ref_code, encoding="utf-8")

    vis_test = (
        'import test from "node:test";\n'
        'import assert from "node:assert";\n'
        'const srcDir = process.env.LAB_SRC_DIR || "../src";\n'
        "const { consumeRetry } = await import(`${srcDir}/budget.ts`);\n\n"
        'test("M1: deducts valid retry cost", () => {\n'
        "  assert.strictEqual(consumeRetry(3, 1), 2);\n"
        "});\n"
    )
    hid_test = (
        'import test from "node:test";\n'
        'import assert from "node:assert";\n'
        'const srcDir = process.env.LAB_SRC_DIR || "../src";\n'
        "const { consumeRetry } = await import(`${srcDir}/budget.ts`);\n\n"
        'test("[M1-HIDDEN-01] rejects overspend when budget is zero", () => {\n'
        "  assert.strictEqual(consumeRetry(0, 1), null);\n"
        "});\n"
        'test("[M1-HIDDEN-02] allows exact zero remaining", () => {\n'
        "  assert.strictEqual(consumeRetry(2, 2), 0);\n"
        "});\n"
    )
    (lab_dir / "tests" / "m1_budget.test.ts").write_text(vis_test, encoding="utf-8")
    (ref_dir / "hidden" / "m1_budget.test.ts").write_text(hid_test, encoding="utf-8")

    cfg: dict[str, Any] = {
        "labId": lab_id,
        "title": "Retry Budget Engine",
        "chapterCode": "PRG-T01-C01",
        "unitsUsed": ["PRG-T01-C01-U02"],
        "kind": kind,
        "level": 2,
        "domain": "retry-budget-engine",
        "targetsWeakSpots": ["U-names"],
        "milestones": [
            {
                "id": "M1",
                "title": "Budget Counter",
                "goal": "Track and deduct retry budget safely.",
                "units": ["PRG-T01-C01-U02"],
                "qualityChecks": ["U-names", "U-errors"],
                "visibleTests": "tests/m1_*.test.ts",
                "examples": [
                    {
                        "input": "budget = 3, cost = 1",
                        "output": "2",
                        "explanation": "Deducts cost 1 from budget 3.",
                        "call": "consumeRetry(3, 1)",
                    },
                    {
                        "input": "budget = 5, cost = 2",
                        "output": "3",
                        "call": "consumeRetry(5, 2)",
                    },
                ],
                "constraints": ["budget >= 0", "cost is an integer"],
                "trapMutant": {"files": {"src/budget.ts": trap_mutant_code}, "note": "Allows negative balance"},
            }
        ],
        "blindSolve": [{"milestone": "M1", "files": {"src/budget.ts": blind_code}, "ambiguous": False, "note": "ok"}],
        "review": {"verdict": "pass", "note": "Clean contracts, no leaks, zero must findings."},
    }
    (lab_dir / "lab.config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    id_map = {
        "DRILLS_DB": {"id": "db-drills-1"},
        "PRG-T01": {"id": "page-t01", "title": "T01"},
        "PRG-T01-C01": {"id": "page-c01", "title": "C01"},
        "PRG-T01-C01-U02": {"id": "page-u02", "title": "Closures"},
    }
    id_map_path = tmp_path / "id_map.json"
    id_map_path.write_text(json.dumps(id_map, indent=2), encoding="utf-8")
    return lab_dir, ref_dir, id_map_path


def test_lab_ingest_accepts_good_fixture_and_finalises(tmp_path: Path) -> None:
    _require_node_and_lint()
    lab_dir, ref_dir, id_map_path = _make_fixture_lab(tmp_path)

    errors = lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert errors == []

    final_cfg = lab_ingest.finalise_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert final_cfg["blindSolve"] == [{"milestone": "M1", "passed": True}]
    assert "trapMutant" not in final_cfg["milestones"][0]


def test_lab_ingest_refuses_stub_passing_tests(tmp_path: Path) -> None:
    _require_node_and_lint()
    lab_dir, ref_dir, id_map_path = _make_fixture_lab(tmp_path)
    (lab_dir / "src" / "budget.ts").write_text(
        "export function consumeRetry(_budget: number, _cost: number): number | null { return 2; }\n",
        encoding="utf-8",
    )
    errors = lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert any("unexpectedly passed all visible tests" in e for e in errors)


def test_lab_ingest_refuses_dirty_lint_stub(tmp_path: Path) -> None:
    _require_node_and_lint()
    lab_dir, ref_dir, id_map_path = _make_fixture_lab(tmp_path)
    (lab_dir / "src" / "budget.ts").write_text(
        "export function consumeRetry(budget: number, cost: number): number | null {\n"
        "  var unused = budget + cost;\n"
        '  throw new Error("TODO [M1]");\n'
        "}\n",
        encoding="utf-8",
    )
    errors = lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert any("Stub ESLint errors" in e for e in errors)


def test_lab_ingest_refuses_uncaught_trap_mutant(tmp_path: Path) -> None:
    _require_node_and_lint()
    lab_dir, ref_dir, id_map_path = _make_fixture_lab(tmp_path)
    cfg = json.loads((lab_dir / "lab.config.json").read_text(encoding="utf-8"))
    cfg["milestones"][0]["trapMutant"]["files"]["src/budget.ts"] = (ref_dir / "src" / "budget.ts").read_text(
        encoding="utf-8"
    )
    (lab_dir / "lab.config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    errors = lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert any("trapMutant was NOT caught" in e for e in errors)


def test_lab_ingest_refuses_missing_review(tmp_path: Path) -> None:
    _require_node_and_lint()
    lab_dir, ref_dir, id_map_path = _make_fixture_lab(tmp_path)
    cfg = json.loads((lab_dir / "lab.config.json").read_text(encoding="utf-8"))
    del cfg["review"]
    (lab_dir / "lab.config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    errors = lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert any("Missing 'review'" in e for e in errors)


def test_lab_ingest_refuses_blind_solve_failing_hidden_tests(tmp_path: Path) -> None:
    _require_node_and_lint()
    lab_dir, ref_dir, id_map_path = _make_fixture_lab(tmp_path)
    cfg = json.loads((lab_dir / "lab.config.json").read_text(encoding="utf-8"))
    cfg["blindSolve"][0]["files"]["src/budget.ts"] = (
        "export function consumeRetry(remaining: number, spend: number): number | null {\n"
        "  return remaining - spend;\n"
        "}\n"
    )
    (lab_dir / "lab.config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    errors = lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=True)
    assert any("blindSolve failed hidden tests" in e for e in errors)


def test_lab_ingest_refuses_extra_project_unstudied_unit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _require_node_and_lint()
    lab_dir, ref_dir, id_map_path = _make_fixture_lab(tmp_path, kind="extra-project")
    monkeypatch.setenv("NOTION_TOKEN", "test-token")

    def fake_notion_request(method: str, endpoint: str, token: str, payload: Any = None) -> dict[str, Any]:
        assert method == "GET"
        return {"properties": {"Status": {"status": {"name": "Not started"}}}}

    monkeypatch.setattr(lab_ingest, "notion_request", fake_notion_request)
    errors = lab_ingest.check_lab(lab_dir, ref_dir=ref_dir, id_map_path=id_map_path, offline=False)
    assert any("must be 'Done' or 'In progress'" in e for e in errors)


def test_lab_review_run_record_and_weak_spots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _require_node_and_lint()
    lab_dir, ref_dir, _ = _make_fixture_lab(tmp_path)
    labs_root = lab_dir.parent
    progress_dir = tmp_path / "progress"
    monkeypatch.setenv("PROGRESS_DIR", str(progress_dir))
    monkeypatch.setenv("LABS_DIR", str(labs_root))

    # Learner writes a clean solution in lab_dir/src
    (lab_dir / "src" / "budget.ts").write_text((ref_dir / "src" / "budget.ts").read_text(encoding="utf-8"))

    res = review_run.run_review("LAB-PRG-T01-C01-99", "M1", labs_root=labs_root)
    assert res["tests"]["passed"] == 3
    assert res["tests"]["total"] == 3
    assert res["lint"] == []
    assert res["typecheck"] == []
    assert any(c["id"] == "U-names" for c in res["checks"])
    assert any(c["id"] == "U-resource-lifecycle" for c in res["checks"])

    # Record a revise attempt with a must finding, then a pass attempt
    rec1 = review_record.add_record(
        "LAB-PRG-T01-C01-99",
        "M1",
        [{"check": "U-names", "line": 1, "note": "Vague parameter name.", "hint": "Rename parameter."}],
        labs_root=labs_root,
    )
    assert rec1["verdict"] == "revise"

    rec2 = review_record.add_record("LAB-PRG-T01-C01-99", "M1", [], labs_root=labs_root)
    assert rec2["verdict"] == "pass"

    prog_file = progress_dir / "LAB-PRG-T01-C01-99.json"
    assert prog_file.exists()
    hist = review_record.format_history("LAB-PRG-T01-C01-99", "M1")
    assert "PASS" in hist

    # weak_spots loads lab items from progress/ + labs/
    items = weak_spots.load_items(
        data_root=str(tmp_path / "drills" / "data"),
        progress_dir=str(progress_dir),
        labs_root=str(labs_root),
    )
    assert len(items) == 1
    assert items[0].drill == "LAB-PRG-T01-C01-99"
    assert "U-names" in items[0].signals


def test_lab_sync_pristine_mocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lab_dir, _, id_map_path = _make_fixture_lab(tmp_path)
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    calls: list[tuple[str, str]] = []

    def fake_request(method: str, endpoint: str, token: str, payload: Any = None) -> dict[str, Any]:
        calls.append((method, endpoint))
        if method == "POST" and endpoint.endswith("/query"):
            return {"results": []}
        if method == "POST" and endpoint == "pages":
            return {"id": "new-lab-page-123"}
        return {}

    monkeypatch.setattr(lab_sync, "notion_request", fake_request)
    monkeypatch.setattr(lab_sync, "replace_page_content", lambda page_id, blocks, token: None)

    res = lab_sync.sync_lab_to_notion(lab_dir, id_map_path=id_map_path)
    assert res["synced"] is True
    assert res["pageId"] == "new-lab-page-123"
    updated_map = json.loads(id_map_path.read_text(encoding="utf-8"))
    assert copy.deepcopy(updated_map["LAB-PRG-T01-C01-99"])["id"] == "new-lab-page-123"
