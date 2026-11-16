# -*- coding: utf-8 -*-
"""
Lint checker for PRG drill reference solutions (Layer 2).

Writes each problem's `solutionCode` into a temporary directory alongside an
`eslint.config.mjs` using `tools/lint/base.js` and the drill's `lintOverrides`,
then runs ESLint and reports any rule violations as `file:line rule message`.

Usage:
    python -m code_engine.lint_check --all
    python -m code_engine.lint_check DRL-PRG-T00-C02-02
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

from code_engine.workspace import ENVIRONMENT_PRESETS, get_entry_name

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_LINT_DIR = REPO_ROOT / "tools" / "lint"


class LintToolsMissingError(RuntimeError):
    """Raised when tools/lint dependencies (node_modules/.bin/eslint) are not installed."""


def get_lint_binaries() -> tuple[Path, Path]:
    """Return paths to (base_js, eslint_bin), raising LintToolsMissingError if absent."""
    base_js = TOOLS_LINT_DIR / "base.js"
    eslint_bin = TOOLS_LINT_DIR / "node_modules" / ".bin" / "eslint"
    if not base_js.exists() or not eslint_bin.exists():
        raise LintToolsMissingError(
            f"Lint toolkit not installed. Expected {base_js} and {eslint_bin}. Run `npm ci` in tools/lint."
        )
    return base_js, eslint_bin


def lint_code_snippet(
    code: str,
    ext: str = "js",
    overrides: Optional[list[dict[str, str]]] = None,
    filename: str = "solution",
) -> list[dict[str, Any]]:
    """Lint a single code string in a temp directory and return structured findings."""
    base_js, eslint_bin = get_lint_binaries()
    active_overrides = overrides or []

    with tempfile.TemporaryDirectory(prefix="prg_lint_") as tmp:
        tmp_path = Path(tmp)
        cfg_path = tmp_path / "eslint.config.mjs"
        cfg_content = (
            f"import {{ prgConfig }} from {json.dumps(base_js.as_uri())};\n\n"
            f"export default prgConfig({{ overrides: {json.dumps(active_overrides)} }});\n"
        )
        cfg_path.write_text(cfg_content, encoding="utf-8")

        target_name = f"{filename}.{ext}"
        target_path = tmp_path / target_name
        target_path.write_text(code.rstrip() + "\n", encoding="utf-8")

        proc = subprocess.run(
            [str(eslint_bin), "--format", "json", target_name],
            cwd=str(tmp_path),
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
                        "file": target_name,
                        "line": msg.get("line", 0),
                        "rule": msg.get("ruleId") or "syntax",
                        "message": msg.get("message", ""),
                    }
                )
        return findings


def lint_drill_doc(drill_doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Lint all `solutionCode` entries in a drill document."""
    preset_key = drill_doc.get("environment", "node-vanilla")
    preset = ENVIRONMENT_PRESETS.get(preset_key, ENVIRONMENT_PRESETS["node-vanilla"])
    ext = preset.get("defaultExt", "js")
    overrides = drill_doc.get("lintOverrides") or []
    drill_id = drill_doc.get("drillId", "UNKNOWN")

    all_findings: list[dict[str, Any]] = []
    for prob in drill_doc.get("problems", []):
        sol = prob.get("solutionCode")
        if not sol:
            continue
        pid = prob.get("id", "Q01")
        entry = get_entry_name(prob)
        findings = lint_code_snippet(sol, ext=ext, overrides=overrides, filename=f"{pid}_{entry}")
        for f in findings:
            f["drillId"] = drill_id
            f["problemId"] = pid
            all_findings.append(f)
    return all_findings


def find_prg_drill_files(data_root: Path) -> list[Path]:
    """Return sorted list of all PRG drill JSON files under data_root."""
    return sorted(data_root.glob("PRG-*/*.json"))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Lint PRG drill reference solutions.")
    parser.add_argument("drill_id", nargs="?", help="Drill ID to check (e.g. DRL-PRG-T00-C02-02)")
    parser.add_argument("--all", action="store_true", help="Check all PRG drills under drills/data/PRG-*")
    parser.add_argument("--data-root", default="drills/data", help="Root directory for drill JSON files")
    args = parser.parse_args(argv)

    if not args.all and not args.drill_id:
        parser.error("Specify a DRILL_ID or --all")

    data_root = Path(args.data_root)
    files = find_prg_drill_files(data_root)
    if args.drill_id:
        files = [p for p in files if p.stem == args.drill_id]
        if not files:
            print(f"No PRG drill found matching '{args.drill_id}' under {data_root}", file=sys.stderr)
            return 1

    checked_drills = 0
    checked_problems = 0
    total_failures: list[dict[str, Any]] = []

    for path in files:
        drill_doc = json.loads(path.read_text(encoding="utf-8"))
        if not drill_doc.get("drillId"):
            drill_doc["drillId"] = path.stem
        checked_drills += 1
        checked_problems += sum(1 for p in drill_doc.get("problems", []) if p.get("solutionCode"))
        findings = lint_drill_doc(drill_doc)
        total_failures.extend(findings)

    for f in total_failures:
        print(f"[{f['drillId']} {f['problemId']}] {f['file']}:{f['line']} {f['rule']} {f['message']}")

    print(f"Checked {checked_drills} drill(s), {checked_problems} solution(s): {len(total_failures)} lint error(s).")
    return 1 if total_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
