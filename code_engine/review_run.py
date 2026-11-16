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

from code_engine.lint_check import TOOLS_LINT_DIR, get_lint_binaries
from code_engine.quality_checks import applicable_rubric, load_archetype
from code_engine.submit import run_tests_junit
from code_engine.workspace import ENVIRONMENT_PRESETS, get_entry_name

TS_PRESETS = ("typescript-strict", "backend-sqlite", "react-dom")
_TSC_DIAG_RE = re.compile(r"^(.+?)\((\d+),(\d+)\):\s+(?:error|warning)\s+(TS\d+:\s*.*)$")


def find_drill_doc(drill_id: str, data_root: Path | None = None) -> tuple[dict[str, Any], Path]:
    """Locate and load the drill JSON document for `drill_id`."""
    root = Path(data_root) if data_root is not None else Path(os.environ.get("DRILLS_DATA_DIR", "drills/data"))
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
    _, eslint_bin = get_lint_binaries()
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
    tsc_bin = TOOLS_LINT_DIR / "node_modules" / ".bin" / "tsc"
    if not tsc_bin.exists():
        raise FileNotFoundError(f"TypeScript compiler not installed at {tsc_bin}. Run `npm ci` in tools/lint.")

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


def run_review_with_source(
    drill_id: str,
    qid: str,
    *,
    data_root: Path | None = None,
    workspace_root: Path | None = None,
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """Run Layer 1 + Layer 2 checks for one problem and return (result_dict, source_text, drill_doc)."""
    drill_doc, _ = find_drill_doc(drill_id, data_root)
    prob = find_problem(drill_doc, qid)
    pid = str(prob["id"])

    ws_root = Path(workspace_root) if workspace_root is not None else Path("drills/workspace")
    ws_dir = ws_root / drill_id
    if not ws_dir.is_dir():
        raise FileNotFoundError(f"Workspace directory not found: {ws_dir}")

    env_key = drill_doc.get("environment", "node-vanilla")
    preset = ENVIRONMENT_PRESETS.get(env_key, ENVIRONMENT_PRESETS["node-vanilla"])
    src_file = find_problem_source(ws_dir, prob, preset.get("defaultExt", "js"))
    src_text = src_file.read_text(encoding="utf-8")
    code_hash = f"sha256:{hashlib.sha256(src_text.encode('utf-8')).hexdigest()}"

    cases = run_tests_junit(ws_dir, drill_doc, problem_id=pid)
    passed = sum(1 for c in cases if c.get("passed"))
    total = len(cases)
    failed = [c["name"] for c in cases if not c.get("passed")]

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
        "tests": {"passed": passed, "total": total, "failed": failed},
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
) -> dict[str, Any]:
    """Run Layer 1 + Layer 2 checks for one problem (read-only) and return the structured report."""
    result, _, _ = run_review_with_source(
        drill_id,
        qid,
        data_root=data_root,
        workspace_root=workspace_root,
        vault_dir=vault_dir,
        universal_path=universal_path,
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
        lines.append(f"  L{item['line']} [{item['rule']}] {item['message']}")

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
