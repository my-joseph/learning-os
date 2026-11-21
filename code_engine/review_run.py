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
import subprocess
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from code_engine.lint_check import TOOLS_LINT_DIR, LintToolsMissingError, get_lint_binaries  # noqa: E402
from code_engine.quality_checks import (  # noqa: E402
    _resolve_vault_dir,
    applicable_rubric,
    effective_severity,
    load_archetype,
    load_universal,
)
from code_engine.submit import _parse_junit_xml, _run_vitest_junit, run_tests_junit  # noqa: E402
from code_engine.workspace import ENVIRONMENT_PRESETS, get_entry_name  # noqa: E402
from progress_store import labs_root as default_labs_root  # noqa: E402
from progress_store import pilot_mode  # noqa: E402
from progress_store import workspace_root as default_workspace_root  # noqa: E402

TS_PRESETS = ("typescript-strict", "backend-sqlite", "react-dom")
_TSC_DIAG_RE = re.compile(r"^(.+?)\((\d+),(\d+)\):\s+(?:error|warning)\s+(TS\d+:\s*.*)$")
_HIDDEN_CASE_RE = re.compile(r"\[(?:[A-Z]\d+-)?HIDDEN(?:-[A-Z]?\d+)?\]|\bHIDDEN[-_](?:T?\d+|TRAP)\b", re.IGNORECASE)


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
    if data_root is not None:
        root = Path(data_root)
    elif os.environ.get("DRILLS_DATA_DIR"):
        root = Path(os.environ["DRILLS_DATA_DIR"])
    elif os.environ.get("LEARNINGOS_ROOT"):
        root = Path(os.environ["LEARNINGOS_ROOT"]) / "drills" / "data"
    else:
        root = Path("drills/data")
    matches = sorted(root.glob(f"*/{drill_id}.json"))
    if not matches:
        matches = sorted(root.glob(f"**/{drill_id}.json"))
    if not matches:
        raise FileNotFoundError(f"Drill '{drill_id}' not found under {root}")
    path = matches[0]
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not doc.get("drillId"):
        doc["drillId"] = path.stem
    return doc, path


def _active_tools_lint_dir() -> Path:
    """Resolve `tools/lint` under `LEARNINGOS_ROOT` when present, falling back to `TOOLS_LINT_DIR`."""
    env_root = os.environ.get("LEARNINGOS_ROOT")
    if env_root:
        candidate = Path(env_root).resolve() / "tools" / "lint"
        if candidate.exists() or candidate.is_symlink():
            return candidate
    return TOOLS_LINT_DIR


def _resolve_eslint_bin() -> Path | None:
    """Return the active ESLint binary path, or `None` when `tools/lint` dependencies are not installed."""
    lint_dir = _active_tools_lint_dir()
    try:
        same_as_default = lint_dir.resolve() == TOOLS_LINT_DIR.resolve()
    except OSError:
        same_as_default = False
    if not same_as_default:
        base_js = lint_dir / "base.js"
        eslint_bin = lint_dir / "node_modules" / ".bin" / "eslint"
        return eslint_bin if (base_js.exists() and eslint_bin.exists()) else None
    try:
        _, eslint_bin = get_lint_binaries()
        return eslint_bin
    except LintToolsMissingError:
        return None


def _resolve_tsc_bin() -> Path | None:
    """Return the active TypeScript compiler (`tsc`) binary path, or `None` when not installed."""
    tsc_bin = _active_tools_lint_dir() / "node_modules" / ".bin" / "tsc"
    return tsc_bin if tsc_bin.exists() else None


def find_problem(drill_doc: dict[str, Any], qid: str) -> dict[str, Any]:
    """Return the problem dict matching `qid` (case-insensitive)."""
    target = qid.upper()
    for prob in drill_doc.get("problems", []):
        if str(prob.get("id", "")).upper() == target:
            return prob
    available = [p.get("id", "?") for p in drill_doc.get("problems", [])]
    raise KeyError(f"Problem '{qid}' not found in {drill_doc.get('drillId')}. Available: {available}")


def find_problem_source(ws_dir: Path, prob: dict[str, Any], preset_ext: str) -> Path:
    """Locate the learner's source file for `prob` inside `ws_dir`."""
    pid = str(prob.get("id", "Q01"))
    entry = get_entry_name(prob)
    expected = ws_dir / f"{pid}_{entry}.{preset_ext}"
    if expected.exists():
        return expected

    for cand in sorted(ws_dir.glob(f"{pid}_*.*")):
        if ".test." not in cand.name and ".hidden." not in cand.name:
            return cand
    raise FileNotFoundError(f"Source file for {pid} not found in {ws_dir} (expected {expected.name})")


def lint_workspace_file(ws_dir: Path, src_file: Path) -> list[dict[str, Any]]:
    """Run ESLint with the workspace config on `src_file` and return [{rule, line, message}]."""
    eslint_bin = _resolve_eslint_bin()
    if eslint_bin is None:
        return []
    proc = subprocess.run(
        [str(eslint_bin), "--format", "json", src_file.name],
        cwd=str(ws_dir),
        capture_output=True,
        text=True,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"ESLint failed (exit {proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}")
    try:
        results = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse ESLint JSON output: {exc}\n{proc.stdout}") from exc

    findings: list[dict[str, Any]] = []
    for res in results:
        for msg in res.get("messages", []):
            findings.append(
                {
                    "file": src_file.name,
                    "rule": msg.get("ruleId") or "syntax",
                    "line": int(msg.get("line", 0) or 0),
                    "message": msg.get("message", ""),
                }
            )
    return findings


def typecheck_workspace_file(ws_dir: Path, src_file: Path, environment: str) -> list[dict[str, Any]]:
    """Run `tsc --noEmit` for TypeScript presets and return [{line, message}] for `src_file`."""
    if environment not in TS_PRESETS and src_file.suffix not in (".ts", ".tsx"):
        return []
    tsc_bin = _resolve_tsc_bin()
    if tsc_bin is None:
        return []

    proc = subprocess.run(
        [str(tsc_bin), "--noEmit", "--pretty", "false"],
        cwd=str(ws_dir),
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return []

    diagnostics: list[dict[str, Any]] = []
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    for line in combined.splitlines():
        m = _TSC_DIAG_RE.match(line.strip())
        if not m:
            continue
        file_part, line_no, _col, msg = m.groups()
        if Path(file_part).name == src_file.name:
            diagnostics.append({"line": int(line_no), "message": msg.strip()})

    if not diagnostics and proc.returncode != 0:
        # Surface non-file-specific tsconfig/compiler errors if any occurred.
        raw_errors = [
            ln.strip() for ln in combined.splitlines() if "error TS" in ln and not _TSC_DIAG_RE.match(ln.strip())
        ]
        for err in raw_errors:
            diagnostics.append({"line": 0, "message": err})
    return diagnostics


def _find_lab_config(lab_id: str, labs_root: Path | None = None) -> tuple[dict[str, Any], Path]:
    env_root = os.environ.get("LEARNINGOS_ROOT")
    lroot = Path(labs_root) if labs_root is not None else Path(default_labs_root(env_root))
    lab_dir = lroot / lab_id
    cfg_path = lab_dir / "lab.config.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Lab '{lab_id}' not found at {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8")), lab_dir


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


def _run_lab_tests(test_files: list[Path], cwd: Path, src_dir: Path, *, force_hidden: bool) -> list[dict[str, Any]]:
    if not test_files:
        return []
    if any(f.suffix == ".tsx" for f in test_files):
        shared_modules = TOOLS_LINT_DIR / "node_modules"
        linked: list[Path] = []
        for project_dir in dict.fromkeys((cwd.resolve(), src_dir.resolve().parent)):
            link = project_dir / "node_modules"
            if not link.exists() and not link.is_symlink():
                link.symlink_to(shared_modules, target_is_directory=True)
                linked.append(link)
        env = {**os.environ, "LAB_SRC_DIR": str(src_dir.resolve())}
        try:
            return _run_vitest_junit(test_files, cwd, force_hidden=force_hidden, env=env)
        finally:
            for link in linked:
                link.unlink(missing_ok=True)
    is_ts = any(f.suffix in (".ts", ".tsx") for f in test_files)
    cmd = ["node"]
    if is_ts:
        cmd.append("--experimental-strip-types")
    cmd.extend(["--test", "--test-reporter=junit", *[str(f.resolve()) for f in test_files]])
    env = dict(os.environ)
    env["LAB_SRC_DIR"] = str(src_dir.resolve())
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    return _parse_junit_xml(proc.stdout + "\n" + proc.stderr, force_hidden=force_hidden)


def _lint_lab_src(lab_dir: Path, src_dir: Path) -> list[dict[str, Any]]:
    eslint_bin = _resolve_eslint_bin()
    if eslint_bin is None:
        return []
    cfg_path = lab_dir / "eslint.config.js"
    cmd = [str(eslint_bin), "--format", "json"]
    if cfg_path.exists():
        cmd.extend(["--config", str(cfg_path.resolve())])
    cmd.append(src_dir.name)
    proc = subprocess.run(cmd, cwd=str(src_dir.parent), capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"ESLint failed (exit {proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}")
    results = json.loads(proc.stdout or "[]")
    findings: list[dict[str, Any]] = []
    for res in results:
        file_name = Path(res.get("filePath", "")).name
        for msg in res.get("messages", []):
            findings.append(
                {
                    "file": file_name,
                    "rule": msg.get("ruleId") or "syntax",
                    "line": int(msg.get("line", 0) or 0),
                    "message": msg.get("message", ""),
                }
            )
    return findings


def _typecheck_lab(lab_dir: Path, src_files: list[Path]) -> list[dict[str, Any]]:
    if not (lab_dir / "tsconfig.json").exists() and not any(f.suffix in (".ts", ".tsx") for f in src_files):
        return []
    tsc_bin = _resolve_tsc_bin()
    if tsc_bin is None:
        return []
    modules_link = lab_dir / "node_modules"
    created_link = False
    shared_modules = _active_tools_lint_dir() / "node_modules"
    if shared_modules.is_dir() and not modules_link.exists() and not modules_link.is_symlink():
        modules_link.symlink_to(shared_modules, target_is_directory=True)
        created_link = True
    try:
        proc = subprocess.run(
            [str(tsc_bin), "--noEmit", "--pretty", "false"], cwd=str(lab_dir), capture_output=True, text=True
        )
    finally:
        if created_link:
            modules_link.unlink(missing_ok=True)
    if proc.returncode == 0:
        return []
    diagnostics: list[dict[str, Any]] = []
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    for line in combined.splitlines():
        m = _TSC_DIAG_RE.match(line.strip())
        if m:
            file_part, line_no, _col, msg = m.groups()
            diagnostics.append({"file": Path(file_part).name, "line": int(line_no), "message": msg.strip()})
        elif "error TS" in line:
            diagnostics.append({"line": 0, "message": line.strip()})
    return diagnostics


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
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Lab src directory not found: {src_dir}")
    src_files = sorted(list(src_dir.rglob("*.tsx")) + list(src_dir.rglob("*.ts")) + list(src_dir.rglob("*.js")))
    if not src_files:
        raise FileNotFoundError(f"No source files found in {src_dir}")

    src_text = "\n".join(f"// === {f.relative_to(lab_dir)} ===\n{f.read_text(encoding='utf-8')}" for f in src_files)
    code_hash = f"sha256:{hashlib.sha256(src_text.encode('utf-8')).hexdigest()}"

    vis_pattern = ms.get("visibleTests")
    if isinstance(vis_pattern, str) and vis_pattern.strip():
        vis_files = sorted(lab_dir.glob(vis_pattern))
    elif isinstance(ms.get("testPattern"), str) and ms["testPattern"].strip():
        vis_files = sorted(lab_dir.glob(f"tests/*{ms['testPattern']}*.test.*"))
    else:
        vis_files = []

    cases = _run_lab_tests(vis_files, lab_dir, src_dir, force_hidden=False)
    ref_hidden = lab_dir.parent / "_reference" / lab_id / "hidden"
    if not ref_hidden.is_dir() and pilot_mode():
        ref_hidden = Path(os.environ.get("LABS_DIR", "labs")) / "_reference" / lab_id / "hidden"
    if ref_hidden.is_dir():
        all_hidden = sorted(
            list(ref_hidden.glob("*.test.tsx"))
            + list(ref_hidden.glob("*.test.ts"))
            + list(ref_hidden.glob("*.test.js"))
        )
        prefix = f"{mid.lower()}_"
        hid_files = [f for f in all_hidden if f.name.lower().startswith(prefix)] or all_hidden
        cases.extend(_run_lab_tests(hid_files, ref_hidden, src_dir, force_hidden=True))

    tests_summary = _summarize_test_cases(cases)
    lint = _lint_lab_src(lab_dir, src_dir)
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

    env_root = os.environ.get("LEARNINGOS_ROOT")
    ws_root = Path(workspace_root) if workspace_root is not None else Path(default_workspace_root(env_root))
    ws_dir = ws_root / drill_id
    if not ws_dir.is_dir():
        raise FileNotFoundError(f"Workspace directory not found: {ws_dir}")

    env_key = drill_doc.get("environment", "node-vanilla")
    preset = ENVIRONMENT_PRESETS.get(env_key, ENVIRONMENT_PRESETS["node-vanilla"])
    src_file = find_problem_source(ws_dir, prob, preset.get("defaultExt", "js"))
    src_text = src_file.read_text(encoding="utf-8")
    code_hash = f"sha256:{hashlib.sha256(src_text.encode('utf-8')).hexdigest()}"

    cases = run_tests_junit(ws_dir, drill_doc, problem_id=pid)
    tests_summary = _summarize_test_cases(cases)

    lint = lint_workspace_file(ws_dir, src_file)
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
