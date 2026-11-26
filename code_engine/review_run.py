# -*- coding: utf-8 -*-
"""
Read-only Layer 1 (tests) + Layer 2 (ESLint + tsc) + Layer 3 rubric runner for one PRG problem.

Usage:
    python -m code_engine.review_run <DRILL_ID> <QID> [--json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Sequence
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from code_engine import submit as _submit  # noqa: E402
from code_engine.quality_checks import (  # noqa: E402
    _resolve_vault_dir,
    applicable_rubric,
    effective_severity,
    load_archetype,
    load_universal,
)
from code_engine.runners import (  # noqa: E402
    _TSC_DIAG_RE,  # noqa: F401 - re-exported for callers/tests
    TS_PRESETS,
    active_tools_lint_dir,
    parse_tsc_diagnostics,
    resolve_eslint_tools,
    resolve_tsc_bin,
    run_eslint_sandbox,
    run_lab_tests,
    run_tsc_sandbox,
)
from code_engine.sandbox import (  # noqa: E402
    JSON_SUFFIXES,
    SOURCE_SUFFIXES,
    assert_safe_contained_path,
    run_node_isolated,
)
from code_engine.submit import run_tests_junit  # noqa: E402
from code_engine.workspace import ENVIRONMENT_PRESETS, find_drill_json, resolve_workspace_source  # noqa: E402
from progress_store import labs_root as default_labs_root  # noqa: E402
from progress_store import pilot_mode  # noqa: E402
from progress_store import workspace_root as default_workspace_root  # noqa: E402

_HIDDEN_CASE_RE = re.compile(r"\[(?:[A-Z]\d+-)?HIDDEN(?:-[A-Z]?\d+)?\]|\bHIDDEN[-_](?:T?\d+|TRAP)\b", re.IGNORECASE)
_MILESTONE_TEST_PREFIX_RE = re.compile(r"^m\d+_", re.IGNORECASE)


def is_hidden_test_name(name: str) -> bool:
    """Return True if a test name carries an internal hidden-test marker."""
    return isinstance(name, str) and bool(_HIDDEN_CASE_RE.search(name))


def mask_hidden_test_failures(failed: list[str]) -> list[str]:
    """Mask any hidden-labelled failure names into a single count summary."""
    visible_failed: list[str] = []
    hidden_count = 0
    for name in failed:
        if is_hidden_test_name(name):
            hidden_count += 1
        elif isinstance(name, str) and name.strip():
            visible_failed.append(name)
    if hidden_count > 0:
        label = "hidden check failed" if hidden_count == 1 else "hidden checks failed"
        visible_failed.append(f"{hidden_count} {label}")
    return visible_failed


def _summarize_test_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize test cases while filtering and masking failing hidden test details."""
    passed = sum(1 for c in cases if c.get("passed"))
    total = len(cases)
    visible_failed: list[str] = []
    hidden_failed_count = 0
    for c in cases:
        if c.get("passed"):
            continue
        name = str(c.get("name") or "Test failed")
        if c.get("is_hidden") or is_hidden_test_name(name):
            hidden_failed_count += 1
        else:
            visible_failed.append(name)
    if hidden_failed_count > 0:
        label = "hidden check failed" if hidden_failed_count == 1 else "hidden checks failed"
        visible_failed.append(f"{hidden_failed_count} {label}")
    return {"passed": passed, "total": total, "failed": visible_failed}


def sanitize_tests_summary(tests: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of a `tests` summary dict with any hidden test names masked."""
    failed_raw = [str(x) for x in (tests.get("failed") or [])]
    return {
        "passed": int(tests.get("passed", 0) or 0),
        "total": int(tests.get("total", 0) or 0),
        "failed": mask_hidden_test_failures(failed_raw),
    }


def find_drill_doc(drill_id: str, data_root: Path | None = None) -> tuple[dict[str, Any], Path]:
    """Locate and load the drill JSON document for `drill_id`."""
    repo = Path(os.environ.get("LEARNINGOS_ROOT") or Path.cwd()).absolute()
    configured = data_root or os.environ.get("DRILLS_DATA_DIR")
    root = Path(configured) if configured else repo / "drills" / "data"
    boundary = repo if root.absolute().is_relative_to(repo) else root
    root = assert_safe_contained_path(root, boundary, expect_file=False)
    path = find_drill_json(drill_id, root)
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("drillId") not in (None, "", drill_id):
        raise ValueError("Drill ID does not match its filename")
    doc["drillId"] = drill_id
    return doc, path


def _active_tools_lint_dir() -> Path:
    """Resolve `tools/lint` under `LEARNINGOS_ROOT` when present, falling back to `TOOLS_LINT_DIR`."""
    return active_tools_lint_dir(respect_env_root=True)


def _resolve_eslint_tools() -> tuple[Path, Path] | None:
    """Return `(base_js, eslint_bin)` for the active lint toolkit, or `None` when not installed."""
    return resolve_eslint_tools(respect_env_root=True, missing_ok=True)


def _resolve_eslint_bin() -> Path | None:
    """Return the active ESLint binary path, or `None` when `tools/lint` dependencies are not installed."""
    tools = _resolve_eslint_tools()
    return tools[1] if tools is not None else None


def _resolve_tsc_bin() -> Path | None:
    """Return the active TypeScript compiler (`tsc`) binary path, or `None` when not installed."""
    return resolve_tsc_bin(respect_env_root=True, missing_ok=True)


def find_problem(drill_doc: dict[str, Any], qid: str) -> dict[str, Any]:
    """Return the problem dict matching `qid` (case-insensitive)."""
    target = qid.upper()
    for prob in drill_doc.get("problems", []):
        if str(prob.get("id", "")).upper() == target:
            return prob
    available = [p.get("id", "?") for p in drill_doc.get("problems", [])]
    raise KeyError(f"Problem '{qid}' not found in {drill_doc.get('drillId')}. Available: {available}")


def lint_workspace_file(
    ws_dir: Path,
    src_file: Path,
    *,
    lint_overrides: Sequence[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Run ESLint on a staged copy of `ws_dir` using a freshly generated trusted config."""
    assert_safe_contained_path(src_file, ws_dir, expect_file=True, label="source file")
    is_ts = src_file.suffix in (".ts", ".tsx")
    return run_eslint_sandbox(
        ws_dir,
        target_arg=src_file.name,
        stage_subdir=None,
        tsconfig_include=("*.ts", "*.tsx") if is_ts else None,
        jsx=(src_file.suffix == ".tsx"),
        symlink_node_modules=(src_file.suffix == ".tsx"),
        file_label_override=src_file.name,
        lint_overrides=lint_overrides,
        respect_env_root=True,
        missing_ok=True,
        sandbox_prefix="prg_eslint_",
    )


def typecheck_workspace_file(ws_dir: Path, src_file: Path, environment: str) -> list[dict[str, Any]]:
    """Run `tsc --noEmit` on a staged copy of `ws_dir` with a trusted `tsconfig.json`."""
    assert_safe_contained_path(src_file, ws_dir, expect_file=True, label="source file")
    if environment not in TS_PRESETS and src_file.suffix not in (".ts", ".tsx"):
        return []
    proc = run_tsc_sandbox(
        ws_dir,
        include=("*.ts", "*.tsx"),
        jsx=(environment == "react-dom" or src_file.suffix == ".tsx"),
        respect_env_root=True,
        missing_ok=True,
        sandbox_prefix="prg_tsc_",
    )
    if proc is None:
        return []
    return parse_tsc_diagnostics(proc, filter_filename=src_file.name, include_file=False)


def _find_lab_config(lab_id: str, labs_root: Path | None = None) -> tuple[dict[str, Any], Path]:
    if not re.fullmatch(r"LAB-[A-Za-z0-9_-]{1,124}", lab_id):
        raise ValueError("Invalid lab ID")
    repo = Path(os.environ.get("LEARNINGOS_ROOT") or Path.cwd())
    if labs_root is not None or os.environ.get("LABS_DIR"):
        lroot = Path(labs_root) if labs_root is not None else Path(os.environ["LABS_DIR"])
    else:
        lroot = assert_safe_contained_path(default_labs_root(str(repo)), repo, expect_file=False)
    lab_dir = assert_safe_contained_path(lab_id, lroot, expect_file=False, relative=True, label="lab directory")
    cfg_path = assert_safe_contained_path("lab.config.json", lab_dir, relative=True, suffixes=JSON_SUFFIXES)
    config = json.loads(cfg_path.read_text(encoding="utf-8"))
    if config.get("labId") not in (None, "", lab_id):
        raise ValueError("Lab ID does not match its directory")
    return config, lab_dir


def _load_qc_by_id(vault_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    vdir = _resolve_vault_dir(vault_dir)
    out: dict[str, dict[str, Any]] = {}
    if not vdir.exists():
        return out
    for vf in sorted(vdir.glob("*.json")):
        data = json.loads(vf.read_text(encoding="utf-8"))
        for arch in data.get("archetypes", []):
            for c in arch.get("qualityChecks") or []:
                if isinstance(c, dict) and c.get("id"):
                    out[c["id"]] = c
    return out


def _lab_rubric(
    ms: dict[str, Any],
    level: int | None,
    *,
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
) -> list[dict[str, Any]]:
    universal = load_universal(universal_path)
    qc_by_id = _load_qc_by_id(vault_dir)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for c in universal:
        if isinstance(c, dict) and c.get("id") and c["id"] not in seen:
            seen.add(c["id"])
            item: dict[str, Any] = {
                "id": c["id"],
                "check": c.get("check", ""),
                "why": c.get("why", ""),
                "severity": effective_severity(c, level),
            }
            if "accepted" in c:
                item["accepted"] = c["accepted"]
            out.append(item)
    for cid in ms.get("qualityChecks") or []:
        if cid in seen or cid not in qc_by_id:
            continue
        c = qc_by_id[cid]
        seen.add(cid)
        item = {
            "id": c["id"],
            "check": c.get("check", ""),
            "why": c.get("why", ""),
            "severity": effective_severity(c, level),
        }
        if "accepted" in c:
            item["accepted"] = c["accepted"]
        out.append(item)
    return out


def _collect_safe_lab_sources(src_dir: Path) -> list[Path]:
    """Collect `.tsx`/`.ts`/`.js` files under `src_dir`, failing closed on any symlink."""
    if src_dir.is_symlink():
        raise ValueError(f"Refusing symlinked lab src directory: {src_dir}")
    src_real = src_dir.resolve(strict=True)
    collected: list[Path] = []
    for root, dirs, files in os.walk(src_real, followlinks=False):
        root_path = Path(root)
        for dname in list(dirs):
            cand_dir = root_path / dname
            if cand_dir.is_symlink():
                raise ValueError(f"Refusing symlinked directory inside lab src: {cand_dir}")
        for fname in files:
            cand_file = root_path / fname
            if cand_file.is_symlink():
                raise ValueError(f"Refusing symlinked file inside lab src: {cand_file}")
            if cand_file.suffix in (".tsx", ".ts", ".js"):
                collected.append(
                    assert_safe_contained_path(cand_file, src_real, label="lab source file", suffixes=SOURCE_SUFFIXES)
                )
    return sorted(collected)


def _run_lab_tests(
    test_files: list[Path],
    cwd: Path,
    src_dir: Path,
    *,
    force_hidden: bool,
    allowed_test_roots: Sequence[Path] | None = None,
) -> list[dict[str, Any]]:
    return run_lab_tests(
        test_files,
        cwd,
        src_dir,
        force_hidden=force_hidden,
        require_complete=True,
        allowed_test_roots=allowed_test_roots,
        sandbox_prefix="prg_lab_review_",
        tools_lint_dir=_active_tools_lint_dir(),
        run_node_fn=run_node_isolated,
        run_vitest_fn=_submit.run_vitest_isolated,
    )


def _lint_lab_src(
    lab_dir: Path,
    src_dir: Path,
    *,
    lint_overrides: Sequence[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Run ESLint on a staged copy of `src_dir` with a freshly generated trusted config."""
    del lab_dir
    return run_eslint_sandbox(
        src_dir,
        lint_overrides=lint_overrides,
        respect_env_root=True,
        missing_ok=True,
        sandbox_prefix="prg_lab_eslint_",
    )


def _typecheck_lab(lab_dir: Path, src_files: list[Path]) -> list[dict[str, Any]]:
    if not (lab_dir / "tsconfig.json").exists() and not any(f.suffix in (".ts", ".tsx") for f in src_files):
        return []
    proc = run_tsc_sandbox(lab_dir, respect_env_root=True, missing_ok=True, sandbox_prefix="prg_lab_tsc_")
    return parse_tsc_diagnostics(proc) if proc is not None else []


def _run_lab_review_with_source(
    lab_id: str,
    milestone: str,
    *,
    labs_root: Path | None = None,
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    lab_cfg, lab_dir = _find_lab_config(lab_id, labs_root=labs_root)
    target = milestone.upper()
    ms = next((m for m in lab_cfg.get("milestones", []) if str(m.get("id", "")).upper() == target), None)
    if ms is None:
        avail = [m.get("id", "?") for m in lab_cfg.get("milestones", [])]
        raise KeyError(f"Milestone '{milestone}' not found in {lab_id}. Available: {avail}")
    mid = str(ms["id"])

    src_dir = lab_dir / "src"
    if not src_dir.is_dir() and not src_dir.is_symlink():
        raise FileNotFoundError(f"Lab src directory not found: {src_dir}")
    assert_safe_contained_path(src_dir, lab_dir, expect_file=False, label="lab src directory")
    src_files = _collect_safe_lab_sources(src_dir)
    if not src_files:
        raise FileNotFoundError(f"No source files found in {src_dir}")

    lab_real = lab_dir.resolve()
    src_text = "\n".join(f"// === {f.relative_to(lab_real)} ===\n{f.read_text(encoding='utf-8')}" for f in src_files)
    code_hash = f"sha256:{hashlib.sha256(src_text.encode('utf-8')).hexdigest()}"

    lab_tests_dir = assert_safe_contained_path(
        "tests", lab_dir, expect_file=False, relative=True, allow_missing=True, label="lab tests directory"
    )
    vis_pattern = ms.get("visibleTests")
    test_pattern = ms.get("testPattern")
    if isinstance(vis_pattern, str) and vis_pattern.strip():
        if not vis_pattern.startswith("tests/"):
            raise ValueError("Visible tests must be selected from tests/")
        pattern = vis_pattern.removeprefix("tests/")
    elif isinstance(test_pattern, str) and test_pattern.strip():
        pattern = f"*{test_pattern}*.test.*"
    else:
        pattern = ""
    if not re.fullmatch(r"[A-Za-z0-9_.*?\[\]-]*", pattern) or ".." in pattern:
        raise ValueError("Invalid visible test pattern")
    vis_files = []
    if pattern and lab_tests_dir.is_dir():
        for candidate in sorted(lab_tests_dir.iterdir()):
            if (
                ".test." in candidate.name
                and "hidden" not in candidate.name.lower()
                and fnmatchcase(candidate.name, pattern)
            ):
                vis_files.append(
                    assert_safe_contained_path(
                        candidate, lab_tests_dir, label="visible test file", suffixes=SOURCE_SUFFIXES
                    )
                )

    ref_root = lab_dir.parent
    hidden_rel = f"_reference/{lab_id}/hidden"
    ref_hidden = assert_safe_contained_path(
        hidden_rel, ref_root, expect_file=False, relative=True, allow_missing=True, label="hidden tests directory"
    )
    if not ref_hidden.is_dir() and pilot_mode():
        configured_labs = os.environ.get("LABS_DIR")
        repo = Path(os.environ.get("LEARNINGOS_ROOT") or Path.cwd())
        ref_hidden = assert_safe_contained_path(
            hidden_rel if configured_labs else f"labs/{hidden_rel}",
            Path(configured_labs) if configured_labs else repo,
            expect_file=False,
            relative=True,
            allow_missing=True,
            label="hidden tests directory",
        )
    all_hidden = sorted(
        list(ref_hidden.glob("*.test.tsx")) + list(ref_hidden.glob("*.test.ts")) + list(ref_hidden.glob("*.test.js"))
    )
    prefix = f"{mid.lower()}_"
    hid_files = [f for f in all_hidden if f.name.lower().startswith(prefix)]
    if not hid_files and not any(_MILESTONE_TEST_PREFIX_RE.match(f.name) for f in all_hidden):
        hid_files = all_hidden  # Older labs can use one shared hidden suite.
    hid_files = [
        assert_safe_contained_path(hf, ref_hidden, label="hidden test file", suffixes=SOURCE_SUFFIXES)
        for hf in hid_files
    ]

    cases = []
    for files, cwd, hidden, allowed_roots in (
        (vis_files, lab_dir, False, (lab_tests_dir,)),
        (hid_files, ref_hidden, True, (ref_hidden,)),
    ):
        try:
            suite_cases = _run_lab_tests(
                files,
                cwd,
                src_dir,
                force_hidden=hidden,
                allowed_test_roots=allowed_roots,
            )
        except (OSError, UnicodeError):
            suite_cases = []
        cases.extend(
            suite_cases
            or [{"name": "Test suite did not produce a complete report", "passed": False, "is_hidden": hidden}]
        )

    tests_summary = _summarize_test_cases(cases)
    lab_lint_overrides = lab_cfg.get("lintOverrides")
    lint = (
        _lint_lab_src(lab_dir, src_dir, lint_overrides=lab_lint_overrides)
        if lab_lint_overrides
        else _lint_lab_src(lab_dir, src_dir)
    )
    typecheck = _typecheck_lab(lab_dir, src_files)

    level = lab_cfg.get("level") if isinstance(lab_cfg.get("level"), int) else None
    checks = _lab_rubric(ms, level, vault_dir=vault_dir, universal_path=universal_path)

    synthetic_doc = {
        "drillId": lab_id,
        "labId": lab_id,
        "unitCode": lab_cfg.get("chapterCode") or (lab_cfg.get("unitsUsed") or [""])[0],
        "chapterCode": lab_cfg.get("chapterCode", ""),
        "problems": [{"id": m["id"]} for m in lab_cfg.get("milestones", []) if isinstance(m, dict) and m.get("id")],
    }
    result = {
        "labId": lab_id,
        "drillId": lab_id,
        "problemId": mid,
        "milestone": mid,
        "archetypeKey": None,
        "level": level,
        "codeHash": code_hash,
        "tests": tests_summary,
        "lint": lint,
        "typecheck": typecheck,
        "checks": checks,
    }
    return result, src_text, synthetic_doc


def run_review_with_source(
    drill_id: str,
    qid: str,
    *,
    data_root: Path | None = None,
    workspace_root: Path | None = None,
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
    labs_root: Path | None = None,
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """Run Layer 1 + Layer 2 checks for one problem or lab milestone and return (result_dict, source_text, doc)."""
    if drill_id.startswith("LAB-"):
        return _run_lab_review_with_source(
            drill_id,
            qid,
            labs_root=labs_root,
            vault_dir=vault_dir,
            universal_path=universal_path,
        )
    drill_doc, _ = find_drill_doc(drill_id, data_root)
    prob = find_problem(drill_doc, qid)
    pid = str(prob["id"])

    repo = Path(os.environ.get("LEARNINGOS_ROOT") or Path.cwd())
    ws_root = (
        Path(workspace_root)
        if workspace_root is not None
        else assert_safe_contained_path(default_workspace_root(str(repo)), repo, expect_file=False)
    )
    ws_dir = assert_safe_contained_path(
        drill_id, ws_root, expect_file=False, relative=True, label="workspace directory"
    )

    env_key = drill_doc.get("environment", "node-vanilla")
    preset = ENVIRONMENT_PRESETS.get(env_key, ENVIRONMENT_PRESETS["node-vanilla"])
    src_file = resolve_workspace_source(ws_dir, drill_id, prob, preset.get("defaultExt", "js"))
    src_text = src_file.read_text(encoding="utf-8")
    code_hash = f"sha256:{hashlib.sha256(src_text.encode('utf-8')).hexdigest()}"

    cases = run_tests_junit(ws_dir, drill_doc, problem_id=pid)
    tests_summary = _summarize_test_cases(cases)

    drill_lint_overrides = drill_doc.get("lintOverrides")
    lint = (
        lint_workspace_file(ws_dir, src_file, lint_overrides=drill_lint_overrides)
        if drill_lint_overrides
        else lint_workspace_file(ws_dir, src_file)
    )
    typecheck = typecheck_workspace_file(ws_dir, src_file, env_key)

    archetype_key = prob.get("archetypeKey")
    level = prob.get("level")
    if level is None and archetype_key:
        arch = load_archetype(archetype_key, vault_dir=vault_dir)
        if arch:
            level = arch.get("level")

    checks = applicable_rubric(archetype_key, level, vault_dir=vault_dir, universal_path=universal_path)

    result = {
        "drillId": drill_id,
        "problemId": pid,
        "archetypeKey": archetype_key,
        "level": level,
        "codeHash": code_hash,
        "tests": tests_summary,
        "lint": lint,
        "typecheck": typecheck,
        "checks": checks,
    }
    return result, src_text, drill_doc


def run_review(
    drill_id: str,
    qid: str,
    *,
    data_root: Path | None = None,
    workspace_root: Path | None = None,
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
    labs_root: Path | None = None,
) -> dict[str, Any]:
    """Run Layer 1 + Layer 2 checks for one problem or lab milestone (read-only) and return the structured report."""
    result, _, _ = run_review_with_source(
        drill_id,
        qid,
        data_root=data_root,
        workspace_root=workspace_root,
        vault_dir=vault_dir,
        universal_path=universal_path,
        labs_root=labs_root,
    )
    return result


def format_summary(res: dict[str, Any]) -> str:
    """Format a human-readable summary of a `run_review` result."""
    tests = res["tests"]
    lines = [
        f"Review Check: {res['drillId']} {res['problemId']} "
        f"(archetype={res.get('archetypeKey') or '-'}, level=L{res.get('level') or '?'})",
        f"Code Hash: {res['codeHash']}",
        f"Layer 1 Tests: {tests['passed']}/{tests['total']} passed",
    ]
    for name in tests["failed"]:
        lines.append(f"  FAIL  {name}")

    lint = res["lint"]
    lines.append(f"Layer 2 Lint: {len(lint)} error(s)")
    for item in lint:
        lines.append(f"  {item.get('file', '')}:{item['line']} {item['rule']} {item['message']}")

    tc = res["typecheck"]
    if tc:
        lines.append(f"Layer 2 Typecheck: {len(tc)} error(s)")
        for item in tc:
            lines.append(f"  L{item['line']} {item['message']}")
    else:
        lines.append("Layer 2 Typecheck: 0 error(s)")

    lines.append(f"Layer 3 Rubric ({len(res['checks'])} checks):")
    for c in res["checks"]:
        lines.append(f"  [{c['severity']}] {c['id']}: {c['check']}")
    passed = tests["total"] > 0 and tests["passed"] == tests["total"] and not lint and not tc
    lines.append(
        "Verdict: PASS — continue with the recorded explain step."
        if passed
        else "Verdict: REVISE — fix the reported failures, then run review again."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m code_engine.review_run",
        description="Run Layer 1 (tests) and Layer 2 (lint/tsc) for one PRG problem (read-only).",
    )
    parser.add_argument("drill_id", help="Drill ID, e.g. DRL-PRG-T00-C03-02")
    parser.add_argument("qid", help="Problem ID, e.g. Q01")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print JSON output")
    args = parser.parse_args(argv)
    target_root = Path(os.environ["LEARNINGOS_ROOT"]).resolve() if os.environ.get("LEARNINGOS_ROOT") else _REPO_ROOT
    os.chdir(target_root)

    try:
        res = run_review(args.drill_id, args.qid)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(format_summary(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
