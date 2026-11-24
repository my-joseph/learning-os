# -*- coding: utf-8 -*-
"""
Lint checker for PRG drill reference solutions (Layer 2).

Writes each problem's `solutionCode` into an isolated per-run sandbox alongside a
trusted `eslint.config.mjs` using `tools/lint/base.js` and the drill's `lintOverrides`,
then runs ESLint / `tsc` through `code_engine.sandbox.run_isolated` and reports any
rule violations as `file:line rule message`.

Usage:
    python -m code_engine.lint_check --all
    python -m code_engine.lint_check DRL-PRG-T00-C03-02
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Optional

from code_engine.sandbox import DEFAULT_TOOL_TIMEOUT_SEC, create_sandbox_dir, run_isolated
from code_engine.workspace import ENVIRONMENT_PRESETS, get_entry_name

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_LINT_DIR = REPO_ROOT / "tools" / "lint"
TS_PRESETS = ("typescript-strict", "backend-sqlite", "react-dom")
_TSC_DIAG_RE = re.compile(r"^(.+?)\((\d+),(\d+)\):\s+(?:error|warning)\s+(TS\d+:\s*.*)$")

UNTRUSTED_TOOL_CONFIG_NAMES = frozenset(
    {
        "eslint.config.js",
        "eslint.config.mjs",
        "eslint.config.cjs",
        ".eslintrc",
        ".eslintrc.js",
        ".eslintrc.cjs",
        ".eslintrc.json",
        ".eslintrc.yml",
        ".eslintrc.yaml",
        "tsconfig.json",
        "vitest.config.ts",
        "vitest.config.mjs",
        "vitest.config.js",
    }
)


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


def build_trusted_eslint_config(
    base_js: Path,
    overrides: Sequence[dict[str, Any]] | None = None,
) -> str:
    """Generate a canonical ESLint 9 flat config referencing trusted `tools/lint/base.js`."""
    active_overrides = list(overrides or [])
    return (
        f"import {{ prgConfig }} from {json.dumps(base_js.resolve().as_uri())};\n\n"
        f"export default prgConfig({{ overrides: {json.dumps(active_overrides)} }});\n"
    )


def build_trusted_tsconfig(
    *,
    include: Sequence[str],
    jsx: bool = False,
) -> dict[str, Any]:
    """Generate a canonical strict TypeScript configuration for sandboxed Layer 2 checks."""
    compiler_options: dict[str, Any] = {
        "target": "ES2024",
        "module": "NodeNext",
        "moduleResolution": "NodeNext",
        "strict": True,
        "noEmit": True,
        "allowImportingTsExtensions": True,
        "skipLibCheck": True,
    }
    if jsx:
        compiler_options["jsx"] = "react-jsx"
    return {
        "compilerOptions": compiler_options,
        "include": list(include),
    }


def lint_code_snippet(
    code: str,
    ext: str = "js",
    overrides: Optional[list[dict[str, str]]] = None,
    filename: str = "solution",
) -> list[dict[str, Any]]:
    """Lint a single code string inside an isolated sandbox and return structured findings."""
    base_js, eslint_bin = get_lint_binaries()
    shared_modules = (TOOLS_LINT_DIR / "node_modules").resolve()

    with create_sandbox_dir(prefix="prg_lint_") as sbx_str:
        sbx_root = Path(os.path.realpath(sbx_str))
        work_dir = sbx_root / "work"
        work_dir.mkdir(parents=True, exist_ok=True)

        cfg_path = work_dir / "eslint.config.mjs"
        cfg_path.write_text(build_trusted_eslint_config(base_js, overrides), encoding="utf-8")

        target_name = f"{filename}.{ext}"
        (work_dir / target_name).write_text(code.rstrip() + "\n", encoding="utf-8")
        if ext in ("ts", "tsx"):
            tsconfig_data = build_trusted_tsconfig(include=("*.ts", "*.tsx"), jsx=(ext == "tsx"))
            (work_dir / "tsconfig.json").write_text(json.dumps(tsconfig_data), encoding="utf-8")
            if ext == "tsx" and shared_modules.is_dir():
                (work_dir / "node_modules").symlink_to(shared_modules, target_is_directory=True)

        proc = run_isolated(
            [str(eslint_bin), "--config", str(cfg_path), "--no-config-lookup", "--format", "json", target_name],
            cwd=work_dir,
            sandbox_root=sbx_root,
            timeout_sec=DEFAULT_TOOL_TIMEOUT_SEC,
            use_node_permission=False,
        )

        if proc.timed_out:
            raise RuntimeError(f"ESLint timed out after {DEFAULT_TOOL_TIMEOUT_SEC}s")
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


def lint_drill_doc(drill_doc: dict[str, Any], *, field: str = "solutionCode") -> list[dict[str, Any]]:
    """Lint all `field` (default `solutionCode`) entries in a drill document."""
    preset_key = drill_doc.get("environment", "node-vanilla")
    preset = ENVIRONMENT_PRESETS.get(preset_key, ENVIRONMENT_PRESETS["node-vanilla"])
    ext = preset.get("defaultExt", "js")
    overrides = drill_doc.get("lintOverrides") or []
    drill_id = drill_doc.get("drillId", "UNKNOWN")

    all_findings: list[dict[str, Any]] = []
    for prob in drill_doc.get("problems", []):
        code = prob.get(field)
        if not code:
            continue
        pid = prob.get("id", "Q01")
        entry = get_entry_name(prob)
        findings = lint_code_snippet(code, ext=ext, overrides=overrides, filename=f"{pid}_{entry}")
        for f in findings:
            f["drillId"] = drill_id
            f["problemId"] = pid
            all_findings.append(f)
    return all_findings


def typecheck_code_snippet(
    code: str,
    ext: str = "ts",
    filename: str = "solution",
) -> list[dict[str, Any]]:
    """Run `tsc --noEmit` on a single TypeScript snippet inside an isolated sandbox."""
    shared_modules = (TOOLS_LINT_DIR / "node_modules").resolve()
    tsc_bin = shared_modules / ".bin" / "tsc"
    if not tsc_bin.exists():
        raise LintToolsMissingError(
            f"TypeScript compiler not installed. Expected {tsc_bin}. Run `npm ci` in tools/lint."
        )

    with create_sandbox_dir(prefix="prg_tsc_") as sbx_str:
        sbx_root = Path(os.path.realpath(sbx_str))
        work_dir = sbx_root / "work"
        work_dir.mkdir(parents=True, exist_ok=True)

        tsconfig_data = build_trusted_tsconfig(include=("*.ts", "*.tsx"), jsx=(ext == "tsx"))
        if shared_modules.is_dir():
            (work_dir / "node_modules").symlink_to(shared_modules, target_is_directory=True)
        tsconfig_path = work_dir / "tsconfig.json"
        tsconfig_path.write_text(json.dumps(tsconfig_data, indent=2) + "\n", encoding="utf-8")

        target_name = f"{filename}.{ext}"
        (work_dir / target_name).write_text(code.rstrip() + "\n", encoding="utf-8")

        proc = run_isolated(
            [str(tsc_bin), "--noEmit", "--pretty", "false", "-p", str(tsconfig_path)],
            cwd=work_dir,
            sandbox_root=sbx_root,
            timeout_sec=DEFAULT_TOOL_TIMEOUT_SEC,
            use_node_permission=False,
        )
        if proc.timed_out:
            return [{"file": target_name, "line": 0, "message": f"tsc timed out after {DEFAULT_TOOL_TIMEOUT_SEC}s"}]
        if proc.returncode == 0:
            return []

        diagnostics: list[dict[str, Any]] = []
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        for line in combined.splitlines():
            m = _TSC_DIAG_RE.match(line.strip())
            if m:
                file_part, line_no, _col, msg = m.groups()
                diagnostics.append({"file": Path(file_part).name, "line": int(line_no), "message": msg.strip()})
        if not diagnostics:
            for line in combined.splitlines():
                if "error TS" in line:
                    diagnostics.append({"file": target_name, "line": 0, "message": line.strip()})
        return diagnostics


def typecheck_drill_doc(drill_doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run `tsc --noEmit` on all `solutionCode` entries in a TypeScript drill document."""
    preset_key = drill_doc.get("environment", "node-vanilla")
    if preset_key not in TS_PRESETS:
        return []
    preset = ENVIRONMENT_PRESETS.get(preset_key, ENVIRONMENT_PRESETS["typescript-strict"])
    ext = preset.get("defaultExt", "ts")
    drill_id = drill_doc.get("drillId", "UNKNOWN")

    all_diags: list[dict[str, Any]] = []
    for prob in drill_doc.get("problems", []):
        sol = prob.get("solutionCode")
        if not sol:
            continue
        pid = prob.get("id", "Q01")
        entry = get_entry_name(prob)
        for d in typecheck_code_snippet(sol, ext=ext, filename=f"{pid}_{entry}"):
            d["drillId"] = drill_id
            d["problemId"] = pid
            all_diags.append(d)
    return all_diags


def find_prg_drill_files(data_root: Path) -> list[Path]:
    """Return sorted list of all PRG drill JSON files under data_root."""
    return sorted(data_root.glob("PRG-*/*.json"))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Lint PRG drill reference solutions.")
    parser.add_argument("drill_id", nargs="?", help="Drill ID to check (e.g. DRL-PRG-T00-C03-02)")
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
