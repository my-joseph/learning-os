# -*- coding: utf-8 -*-
"""
AI-generated Project Lab validation & finalisation gates.

Validates a lab directory (`labs/LAB-<CHAPTER>-NN/` + `labs/_reference/<LAB>/`)
against schema, id_map/Notion unit status, rubric qualityChecks, reference
execution (visible + hidden + lint + tsc), stub negative verification + lint/tsc,
per-milestone trapMutant killing, zero-leak checks, blind-solve verification, and
reviewer sign-off.

Usage:
    python -m code_engine.lab_ingest --check <lab_dir> [--offline]
    python -m code_engine.lab_ingest <lab_dir> [--offline]
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from code_engine.examples_gate import (
    check_examples_zero_leak,
    evaluate_lab_milestone_examples,
    validate_examples_and_constraints_schema,
)
from code_engine.lint_check import TOOLS_LINT_DIR, LintToolsMissingError, get_lint_binaries
from code_engine.quality_checks import load_universal
from code_engine.submit import _parse_junit_xml
from math_engine.source_cores import resolve_sources_dir
from math_engine.source_cores.code_originality import check_lab_originality
from notion_sync.client import load_env, notion_request

LAB_ID_RE = re.compile(r"^LAB-[A-Z0-9-]+$")
TOY_ID_RE = re.compile(r"\b(foo|bar|baz|test1|funcA)\b", re.IGNORECASE)
LEAK_MARKER_RE = re.compile(
    r"(//\s*(?:BUG|DEFECT|FIX HERE|SOLUTION|ANSWER)\s*:|\btrapMutant\b|\bsolutionCode\b)",
    re.IGNORECASE,
)
VALID_KINDS = ("chapter-lab", "extra-project")
REQUIRED_PACKAGE_SCRIPTS = ("test", "check", "test:reference", "check:reference", "check:hidden")


def _normalize_whitespace(code: str) -> str:
    return " ".join(code.split())


def _resolve_ref_dir(lab_dir: Path, ref_dir: Path | None = None) -> Path:
    if ref_dir is not None:
        return ref_dir
    return lab_dir.parent / "_reference" / lab_dir.name


def _run_node_tests(test_files: list[Path], cwd: Path, src_dir: Path) -> list[dict[str, Any]]:
    if not test_files:
        return []
    if any(f.suffix == ".tsx" for f in test_files):
        return _run_react_tests(test_files, cwd, src_dir)
    is_ts = any(f.suffix in (".ts", ".tsx") for f in test_files)
    cmd = ["node"]
    if is_ts:
        cmd.append("--experimental-strip-types")
    cmd.extend(["--test", "--test-reporter=junit", *[str(f.resolve()) for f in test_files]])
    env = dict(os.environ)
    env["LAB_SRC_DIR"] = str(src_dir.resolve())
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    return _parse_junit_xml(proc.stdout + "\n" + proc.stderr, force_hidden=False)


def _run_react_tests(test_files: list[Path], cwd: Path, src_dir: Path) -> list[dict[str, Any]]:
    """Run lab TSX acceptance tests against React DOM with the shared test installation."""
    vitest = TOOLS_LINT_DIR / "node_modules" / ".bin" / "vitest"
    if not vitest.is_file():
        return [
            {
                "name": "React test runner unavailable",
                "passed": False,
                "failure_msg": f"Vitest is missing at {vitest}; run npm ci in tools/lint.",
            }
        ]
    cwd = cwd.resolve()
    src_dir = src_dir.resolve()
    shared_modules = TOOLS_LINT_DIR / "node_modules"
    linked: list[Path] = []
    for project_dir in dict.fromkeys((cwd, src_dir.parent)):
        link = project_dir / "node_modules"
        if link.is_symlink() and link.resolve() == shared_modules.resolve():
            continue
        if link.exists() or link.is_symlink():
            continue
        link.symlink_to(shared_modules, target_is_directory=True)
        linked.append(link)
    test_root = Path(os.path.commonpath([str(f.resolve().parent) for f in test_files]))
    allowed_dirs = list(
        dict.fromkeys(
            (
                str(cwd),
                str(src_dir),
                str(test_root),
                str(Path(__file__).resolve().parents[1]),
            )
        )
    )
    try:
        with tempfile.TemporaryDirectory(prefix="lab_vitest_", dir=TOOLS_LINT_DIR) as tmp:
            tmp_dir = Path(tmp)
            config = tmp_dir / "vitest.config.ts"
            report = tmp_dir / "junit.xml"
            allow_js = ", ".join(json.dumps(d) for d in allowed_dirs)
            config.write_text(
                "import { defineConfig } from 'vitest/config';\n"
                f"export default defineConfig({{ root: {json.dumps(str(test_root))}, esbuild: {{ jsx: 'automatic' }}, test: {{ environment: 'jsdom' }}, server: {{ fs: {{ allow: [{allow_js}] }} }} }});\n",
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["LAB_SRC_DIR"] = str(src_dir)
            cmd = [
                str(vitest),
                "run",
                *[str(f.resolve()) for f in test_files],
                "--config",
                str(config),
                "--environment",
                "jsdom",
                "--reporter=junit",
                f"--outputFile={report}",
            ]
            proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
            if report.is_file():
                cases = _parse_junit_xml(report.read_text(encoding="utf-8"), force_hidden=False)
                if cases:
                    return cases
            output = (proc.stderr or proc.stdout or f"Vitest exited with code {proc.returncode}").strip()
            return [{"name": "React test execution failure", "passed": False, "failure_msg": output}]
    finally:
        for link in linked:
            link.unlink(missing_ok=True)


def _run_eslint_dir(src_dir: Path, config_path: Path) -> list[dict[str, Any]]:
    _, eslint_bin = get_lint_binaries()
    proc = subprocess.run(
        [str(eslint_bin), "--config", str(config_path.resolve()), "--format", "json", src_dir.name],
        cwd=str(src_dir.parent),
        capture_output=True,
        text=True,
    )
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
                    "line": int(msg.get("line", 0) or 0),
                    "rule": msg.get("ruleId") or "syntax",
                    "message": msg.get("message", ""),
                }
            )
    return findings


def _run_tsc(tsconfig_path: Path) -> list[str]:
    tsc_bin = TOOLS_LINT_DIR / "node_modules" / ".bin" / "tsc"
    if not tsc_bin.exists():
        raise FileNotFoundError(f"TypeScript compiler not installed at {tsc_bin}. Run `npm ci` in tools/lint.")
    project_modules = tsconfig_path.parent / "node_modules"
    created_link = False
    if not project_modules.exists() and not project_modules.is_symlink():
        project_modules.symlink_to(TOOLS_LINT_DIR / "node_modules", target_is_directory=True)
        created_link = True
    try:
        proc = subprocess.run(
            [str(tsc_bin), "--noEmit", "--pretty", "false", "-p", str(tsconfig_path.resolve())],
            cwd=str(tsconfig_path.parent),
            capture_output=True,
            text=True,
        )
    finally:
        if created_link:
            project_modules.unlink(missing_ok=True)
    if proc.returncode == 0:
        return []
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    lines = [ln.strip() for ln in combined.splitlines() if ln.strip()]
    return lines or [f"tsc failed with exit code {proc.returncode}"]


def _milestone_hidden_tests(hidden_dir: Path, milestone_id: str) -> list[Path]:
    all_hidden = sorted(
        list(hidden_dir.glob("*.test.tsx")) + list(hidden_dir.glob("*.test.ts")) + list(hidden_dir.glob("*.test.js"))
    )
    prefix = f"{milestone_id.lower()}_"
    matched = [f for f in all_hidden if f.name.lower().startswith(prefix)]
    return matched if matched else all_hidden


def _milestone_visible_tests(lab_dir: Path, ms: dict[str, Any]) -> list[Path]:
    pattern = ms.get("visibleTests")
    if isinstance(pattern, str) and pattern.strip():
        return sorted(lab_dir.glob(pattern))
    tp = ms.get("testPattern")
    if isinstance(tp, str) and tp.strip():
        return sorted(lab_dir.glob(f"tests/*{tp}*.test.*"))
    return []


def _load_vault_checks_by_unit(vault_dir: Path | None = None) -> dict[str, set[str]]:
    vdir = vault_dir or Path("code_engine/reasoning_vault")
    by_unit: dict[str, set[str]] = {}
    if not vdir.exists():
        return by_unit
    for vf in sorted(vdir.glob("*.json")):
        data = json.loads(vf.read_text(encoding="utf-8"))
        for arch in data.get("archetypes", []):
            uc = arch.get("unitCode")
            if not uc:
                continue
            bucket = by_unit.setdefault(uc, set())
            for c in arch.get("qualityChecks") or []:
                if isinstance(c, dict) and c.get("id"):
                    bucket.add(c["id"])
    return by_unit


def _extract_notion_status(page: dict[str, Any]) -> str:
    props = page.get("properties") or {}
    st = props.get("Status") or {}
    if isinstance(st.get("status"), dict):
        return str(st["status"].get("name") or "")
    if isinstance(st.get("select"), dict):
        return str(st["select"].get("name") or "")
    return ""


def _validate_config_and_layout(lab_dir: Path, ref_dir: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    cfg_path = lab_dir / "lab.config.json"
    if not cfg_path.exists():
        return None, [f"Missing {cfg_path}"]
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON in {cfg_path}: {exc}"]
    if not isinstance(cfg, dict):
        return None, ["lab.config.json must be a JSON object."]

    lab_id = cfg.get("labId")
    if not isinstance(lab_id, str) or not LAB_ID_RE.match(lab_id):
        errors.append(f"Invalid or missing 'labId': {lab_id!r}")

    if not isinstance(cfg.get("chapterCode"), str) or not cfg["chapterCode"].strip():
        errors.append("Missing non-empty 'chapterCode'.")

    units_used = cfg.get("unitsUsed")
    if (
        not isinstance(units_used, list)
        or not units_used
        or not all(isinstance(u, str) and u.strip() for u in units_used)
    ):
        errors.append("'unitsUsed' must be a non-empty list of unit code strings.")

    kind = cfg.get("kind")
    if kind not in VALID_KINDS:
        errors.append(f"'kind' must be one of {VALID_KINDS}, got {kind!r}.")

    level = cfg.get("level")
    if isinstance(level, bool) or not isinstance(level, int) or not (1 <= level <= 5):
        errors.append(f"'level' must be an integer 1..5, got {level!r}.")

    if not isinstance(cfg.get("domain"), str) or not cfg["domain"].strip():
        errors.append("Missing non-empty 'domain'.")

    if not isinstance(cfg.get("targetsWeakSpots"), list) or not all(
        isinstance(w, str) for w in cfg["targetsWeakSpots"]
    ):
        errors.append("'targetsWeakSpots' must be a list of strings.")

    milestones = cfg.get("milestones")
    if not isinstance(milestones, list) or not milestones:
        errors.append("'milestones' must be a non-empty list.")
    else:
        for idx, ms in enumerate(milestones, 1):
            if not isinstance(ms, dict):
                errors.append(f"milestones[{idx}] must be an object.")
                continue
            mid = ms.get("id") or f"#{idx}"
            for field in ("id", "title", "goal", "visibleTests"):
                if not isinstance(ms.get(field), str) or not ms[field].strip():
                    errors.append(f"[{mid}] Missing non-empty '{field}'.")
            if not isinstance(ms.get("units"), list) or not ms["units"]:
                errors.append(f"[{mid}] 'units' must be a non-empty list.")
            if not isinstance(ms.get("qualityChecks"), list) or not ms["qualityChecks"]:
                errors.append(f"[{mid}] 'qualityChecks' must be a non-empty list.")
            vis = _milestone_visible_tests(lab_dir, ms)
            if not vis:
                errors.append(f"[{mid}] visibleTests pattern {ms.get('visibleTests')!r} matched no files.")

    for req_file in ("README.md", "eslint.config.js", "tsconfig.json", "package.json"):
        if not (lab_dir / req_file).exists():
            errors.append(f"Missing required file: {lab_dir / req_file}")
    for req_dir in ("src", "tests"):
        if not (lab_dir / req_dir).is_dir():
            errors.append(f"Missing required directory: {lab_dir / req_dir}")

    pkg_path = lab_dir / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            scripts = pkg.get("scripts") or {}
            missing_scripts = [s for s in REQUIRED_PACKAGE_SCRIPTS if s not in scripts]
            if missing_scripts:
                errors.append(f"package.json missing required scripts: {missing_scripts}")
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid package.json: {exc}")

    if not (ref_dir / "src").is_dir():
        errors.append(f"Missing reference src directory: {ref_dir / 'src'}")
    if not (ref_dir / "hidden").is_dir():
        errors.append(f"Missing reference hidden tests directory: {ref_dir / 'hidden'}")
    else:
        hidden_files = list((ref_dir / "hidden").glob("*.test.*"))
        if not hidden_files:
            errors.append(f"No hidden test files (*.test.*) in {ref_dir / 'hidden'}")
    if not (ref_dir / "tsconfig.json").exists():
        errors.append(f"Missing reference tsconfig.json: {ref_dir / 'tsconfig.json'}")

    return cfg, errors


def _check_units_and_notion(
    cfg: dict[str, Any],
    *,
    id_map_path: Path,
    offline: bool,
) -> list[str]:
    errors: list[str] = []
    if not id_map_path.exists():
        return [f"id_map.json not found at {id_map_path}"]
    id_map = json.loads(id_map_path.read_text(encoding="utf-8"))

    units_used = cfg.get("unitsUsed") or []
    all_units = list(dict.fromkeys(units_used))
    for ms in cfg.get("milestones") or []:
        for u in ms.get("units") or []:
            if u not in all_units:
                all_units.append(u)

    for u in all_units:
        if u not in id_map:
            errors.append(f"Unit '{u}' not found in id_map.json.")
        elif u not in units_used:
            errors.append(f"Milestone unit '{u}' must also be listed in top-level 'unitsUsed'.")

    if cfg.get("kind") == "extra-project":
        if offline:
            print("Skipping Notion Status check (--offline).")
        else:
            env = load_env()
            token = env.get("NOTION_TOKEN") or os.environ.get("NOTION_TOKEN")
            if not token:
                errors.append("NOTION_TOKEN is required for extra-project Status check (or pass --offline).")
                return errors
            for u in units_used:
                entry = id_map.get(u)
                if not entry:
                    continue
                page_id = entry["id"] if isinstance(entry, dict) else entry
                page = notion_request("GET", f"pages/{page_id}", token)
                status = _extract_notion_status(page)
                if status not in ("Done", "In progress"):
                    errors.append(
                        f"extra-project unit '{u}' has Notion Status {status!r}; must be 'Done' or 'In progress'."
                    )
    return errors


def _check_rubric(
    cfg: dict[str, Any],
    *,
    vault_dir: Path | None,
    universal_path: Path | None,
) -> list[str]:
    errors: list[str] = []
    universal = load_universal(universal_path)
    universal_ids = {c["id"] for c in universal if isinstance(c, dict) and c.get("id")}
    by_unit = _load_vault_checks_by_unit(vault_dir)

    for ms in cfg.get("milestones") or []:
        mid = ms.get("id", "?")
        allowed = set(universal_ids)
        for u in ms.get("units") or []:
            allowed |= by_unit.get(u, set())
        for cid in ms.get("qualityChecks") or []:
            if cid not in allowed:
                errors.append(f"[{mid}] qualityCheck '{cid}' does not exist in U-* or {ms.get('units')} archetypes.")
    return errors


def _allow_missing_lint(explicit: bool = False) -> bool:
    return bool(explicit) or os.environ.get("LEARNINGOS_ALLOW_MISSING_LINT", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _check_reference(
    lab_dir: Path,
    ref_dir: Path,
    cfg: dict[str, Any],
    *,
    allow_missing_lint: bool = False,
) -> list[str]:
    errors: list[str] = []
    ref_src = ref_dir / "src"
    hidden_dir = ref_dir / "hidden"
    eslint_cfg = lab_dir / "eslint.config.js"
    for ms in cfg.get("milestones") or []:
        mid = ms.get("id", "?")
        vis_files = _milestone_visible_tests(lab_dir, ms)
        if vis_files:
            cases = _run_node_tests(vis_files, lab_dir, ref_src)
            failed = [c["name"] for c in cases if not c["passed"]]
            if not cases or failed:
                errors.append(f"[{mid}] Reference failed visible tests: {failed or '0 tests ran'}")

        hid_files = _milestone_hidden_tests(hidden_dir, mid)
        if hid_files:
            cases = _run_node_tests(hid_files, hidden_dir, ref_src)
            failed = [c["name"] for c in cases if not c["passed"]]
            if not cases or failed:
                errors.append(f"[{mid}] Reference failed hidden tests: {failed or '0 tests ran'}")

    try:
        lint_findings = _run_eslint_dir(ref_src, eslint_cfg)
    except (LintToolsMissingError, FileNotFoundError) as exc:
        if _allow_missing_lint(allow_missing_lint):
            print(f"  [SKIP] Reference ESLint gate: {exc}")
            lint_findings = []
        else:
            errors.append(
                f"Reference ESLint gate cannot run: {exc} "
                "(Run `cd tools/lint && npm ci`, or opt out with --allow-missing-lint / LEARNINGOS_ALLOW_MISSING_LINT=1.)"
            )
            lint_findings = []
    if lint_findings:
        errors.append(f"Reference ESLint errors ({len(lint_findings)}): {lint_findings[:3]}")

    try:
        tsc_errors = _run_tsc(ref_dir / "tsconfig.json")
    except (LintToolsMissingError, FileNotFoundError) as exc:
        if _allow_missing_lint(allow_missing_lint):
            print(f"  [SKIP] Reference tsc gate: {exc}")
            tsc_errors = []
        else:
            errors.append(
                f"Reference tsc gate cannot run: {exc} "
                "(Run `cd tools/lint && npm ci`, or opt out with --allow-missing-lint / LEARNINGOS_ALLOW_MISSING_LINT=1.)"
            )
            tsc_errors = []
    if tsc_errors:
        errors.append(f"Reference tsc errors: {tsc_errors[:3]}")
    return errors


def _check_stubs(
    lab_dir: Path,
    cfg: dict[str, Any],
    *,
    allow_missing_lint: bool = False,
) -> list[str]:
    errors: list[str] = []
    stub_src = lab_dir / "src"
    eslint_cfg = lab_dir / "eslint.config.js"

    try:
        lint_findings = _run_eslint_dir(stub_src, eslint_cfg)
    except (LintToolsMissingError, FileNotFoundError) as exc:
        if _allow_missing_lint(allow_missing_lint):
            print(f"  [SKIP] Stub ESLint gate: {exc}")
            lint_findings = []
        else:
            errors.append(
                f"Stub ESLint gate cannot run: {exc} "
                "(Run `cd tools/lint && npm ci`, or opt out with --allow-missing-lint / LEARNINGOS_ALLOW_MISSING_LINT=1.)"
            )
            lint_findings = []
    if lint_findings:
        errors.append(f"Stub ESLint errors ({len(lint_findings)}): {lint_findings[:3]}")

    try:
        tsc_errors = _run_tsc(lab_dir / "tsconfig.json")
    except (LintToolsMissingError, FileNotFoundError) as exc:
        if _allow_missing_lint(allow_missing_lint):
            print(f"  [SKIP] Stub tsc gate: {exc}")
            tsc_errors = []
        else:
            errors.append(
                f"Stub tsc gate cannot run: {exc} "
                "(Run `cd tools/lint && npm ci`, or opt out with --allow-missing-lint / LEARNINGOS_ALLOW_MISSING_LINT=1.)"
            )
            tsc_errors = []
    if tsc_errors:
        errors.append(f"Stub tsc errors: {tsc_errors[:3]}")

    for ms in cfg.get("milestones") or []:
        mid = ms.get("id", "?")
        vis_files = _milestone_visible_tests(lab_dir, ms)
        if not vis_files:
            continue
        cases = _run_node_tests(vis_files, lab_dir, stub_src)
        failed = [c["name"] for c in cases if not c["passed"]]
        if not cases:
            errors.append(f"[{mid}] Stub visible tests ran 0 cases.")
        elif not failed:
            errors.append(f"[{mid}] Stub unexpectedly passed all visible tests (must fail before solving).")
    return errors


def _mutant_files_map(mutant: dict[str, Any]) -> dict[str, str]:
    if isinstance(mutant.get("files"), dict):
        return {str(k): str(v) for k, v in mutant["files"].items()}
    if isinstance(mutant.get("file"), str) and isinstance(mutant.get("code"), str):
        return {mutant["file"]: mutant["code"]}
    return {}


def _apply_files(base_dir: Path, files_map: dict[str, str]) -> None:
    for rel, code in files_map.items():
        rel_clean = rel.lstrip("/")
        if rel_clean.startswith("src/"):
            target = base_dir / rel_clean
        else:
            target = base_dir / "src" / rel_clean
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(code, encoding="utf-8")


def _check_trap_mutants(ref_dir: Path, cfg: dict[str, Any], *, ingested: bool = False) -> list[str]:
    errors: list[str] = []
    ref_src = ref_dir / "src"
    hidden_dir = ref_dir / "hidden"

    for ms in cfg.get("milestones") or []:
        mid = ms.get("id", "?")
        mutant = ms.get("trapMutant")
        if mutant is None and ingested:
            continue
        if not isinstance(mutant, dict):
            errors.append(f"[{mid}] Missing 'trapMutant' on milestone.")
            continue
        fmap = _mutant_files_map(mutant)
        if not fmap:
            errors.append(f"[{mid}] trapMutant must specify 'files' (or 'file' + 'code').")
            continue

        hid_files = _milestone_hidden_tests(hidden_dir, mid)
        if not hid_files:
            errors.append(f"[{mid}] No hidden tests found to verify trapMutant.")
            continue

        with tempfile.TemporaryDirectory(prefix=f"lab_mutant_{mid}_") as tmp:
            tmp_root = Path(tmp)
            tmp_src = tmp_root / "src"
            shutil.copytree(ref_src, tmp_src)
            _apply_files(tmp_root, fmap)
            cases = _run_node_tests(hid_files, hidden_dir, tmp_src)
            failed = [c["name"] for c in cases if not c["passed"]]
            if not cases:
                errors.append(f"[{mid}] trapMutant hidden test run produced 0 test cases.")
            elif not failed:
                errors.append(f"[{mid}] trapMutant was NOT caught by hidden tests (all {len(cases)} passed).")
    return errors


def _check_no_leaks(lab_dir: Path) -> list[str]:
    errors: list[str] = []
    files_to_scan: list[Path] = []
    readme = lab_dir / "README.md"
    if readme.exists():
        files_to_scan.append(readme)
    for folder in ("src", "tests"):
        fdir = lab_dir / folder
        if fdir.is_dir():
            files_to_scan.extend(
                sorted(p for p in fdir.rglob("*") if p.is_file() and p.suffix in (".ts", ".js", ".md"))
            )

    for path in files_to_scan:
        text = path.read_text(encoding="utf-8")
        m_toy = TOY_ID_RE.search(text)
        if m_toy:
            errors.append(f"Leak/toy identifier {m_toy.group(1)!r} found in {path.relative_to(lab_dir)}")
        m_leak = LEAK_MARKER_RE.search(text)
        if m_leak:
            errors.append(f"Leak marker {m_leak.group(1)!r} found in {path.relative_to(lab_dir)}")
    return errors


def _check_blind_solve(
    lab_dir: Path,
    ref_dir: Path,
    cfg: dict[str, Any],
    *,
    ingested: bool = False,
) -> list[str]:
    errors: list[str] = []
    bs = cfg.get("blindSolve")
    if not isinstance(bs, list) or not bs:
        return ["Missing 'blindSolve' list [{milestone, files: {path: code}}] from independent subagent."]

    by_ms: dict[str, dict[str, Any]] = {}
    for entry in bs:
        if isinstance(entry, dict) and entry.get("milestone"):
            by_ms[str(entry["milestone"]).upper()] = entry

    ref_src = ref_dir / "src"
    hidden_dir = ref_dir / "hidden"

    with tempfile.TemporaryDirectory(prefix="lab_blind_") as tmp:
        tmp_lab = Path(tmp) / lab_dir.name
        copied = False

        for ms in cfg.get("milestones") or []:
            mid = str(ms.get("id", "?"))
            rec = by_ms.get(mid.upper())
            if rec is None:
                errors.append(f"[{mid}] Missing blindSolve entry for '{mid}'.")
                continue
            if rec.get("ambiguous") is True:
                errors.append(f"[{mid}] blindSolve flagged '{mid}' as ambiguous.")
                continue
            fmap = rec.get("files")
            if not isinstance(fmap, dict) or not fmap:
                if ingested and rec.get("passed") is True:
                    continue
                errors.append(f"[{mid}] blindSolve entry for '{mid}' is missing 'files'.")
                continue

            if not copied:
                shutil.copytree(lab_dir, tmp_lab)
                copied = True

            identical = False
            for rel, code in fmap.items():
                if not isinstance(code, str) or not code.strip():
                    errors.append(f"[{mid}] blindSolve file '{rel}' has empty code.")
                    identical = True
                    break
                rel_name = rel.lstrip("/")
                if rel_name.startswith("src/"):
                    rel_name = rel_name[4:]
                ref_file = ref_src / rel_name
                if ref_file.exists() and _normalize_whitespace(code) == _normalize_whitespace(
                    ref_file.read_text(encoding="utf-8")
                ):
                    errors.append(
                        f"[{mid}] blindSolve file '{rel}' is identical to reference (blind solver must not see reference)."
                    )
                    identical = True
                    break
            if identical:
                continue

            _apply_files(tmp_lab, fmap)
            tmp_src = tmp_lab / "src"

            vis_files = _milestone_visible_tests(tmp_lab, ms)
            if vis_files:
                vis_cases = _run_node_tests(vis_files, tmp_lab, tmp_src)
                vis_failed = [c["name"] for c in vis_cases if not c["passed"]]
                if not vis_cases or vis_failed:
                    errors.append(f"[{mid}] blindSolve failed visible tests: {vis_failed or '0 tests ran'}")

            hid_files = _milestone_hidden_tests(hidden_dir, mid)
            if hid_files:
                hid_cases = _run_node_tests(hid_files, hidden_dir, tmp_src)
                hid_failed = [c["name"] for c in hid_cases if not c["passed"]]
                if not hid_cases or hid_failed:
                    errors.append(f"[{mid}] blindSolve failed hidden tests: {hid_failed or '0 tests ran'}")
    return errors


def _check_examples(lab_dir: Path, ref_dir: Path, cfg: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    hidden_dir = ref_dir / "hidden"
    for ms in cfg.get("milestones") or []:
        if not isinstance(ms, dict):
            continue
        mid = str(ms.get("id") or "?")
        schema_errs = validate_examples_and_constraints_schema(mid, ms, require_examples=True)
        if schema_errs:
            errors.extend(schema_errs)
            continue

        examples = ms.get("examples") or []
        hid_files = _milestone_hidden_tests(hidden_dir, mid)
        hidden_sources = [(f.name, f.read_text(encoding="utf-8")) for f in hid_files if f.is_file()]
        leak_errs = check_examples_zero_leak(mid, examples, hidden_sources)
        if leak_errs:
            errors.extend(leak_errs)
            continue

        errors.extend(
            evaluate_lab_milestone_examples(
                mid,
                ms,
                lab_dir,
                ref_dir,
                _run_node_tests,
                tools_lint_dir=TOOLS_LINT_DIR,
            )
        )
    return errors


def _check_review(cfg: dict[str, Any]) -> list[str]:
    rv = cfg.get("review")
    if not isinstance(rv, dict):
        return ["Missing 'review' {verdict: 'pass', note} from reviewer subagent."]
    if rv.get("verdict") != "pass" or not str(rv.get("note") or "").strip():
        return [f"Lab 'review' must have verdict='pass' and a non-empty 'note' (got {rv!r})."]
    return []


def check_lab(
    lab_dir: Path,
    *,
    ref_dir: Path | None = None,
    id_map_path: Path | None = None,
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
    offline: bool = False,
    ingested: bool = False,
    allow_missing_lint: bool = False,
    check_originality: bool = False,
    sources_dir: str | None = None,
) -> list[str]:
    """Run all lab ingest gates without modifying files. Returns list of error strings."""
    resolved_ref = _resolve_ref_dir(lab_dir, ref_dir)
    cfg, errors = _validate_config_and_layout(lab_dir, resolved_ref)
    if cfg is None or errors:
        return errors

    errors.extend(
        _check_units_and_notion(
            cfg,
            id_map_path=id_map_path or Path("id_map.json"),
            offline=offline,
        )
    )
    errors.extend(_check_rubric(cfg, vault_dir=vault_dir, universal_path=universal_path))
    errors.extend(_check_no_leaks(lab_dir))
    errors.extend(_check_reference(lab_dir, resolved_ref, cfg, allow_missing_lint=allow_missing_lint))
    errors.extend(_check_examples(lab_dir, resolved_ref, cfg))
    errors.extend(_check_stubs(lab_dir, cfg, allow_missing_lint=allow_missing_lint))
    errors.extend(_check_trap_mutants(resolved_ref, cfg, ingested=ingested))
    errors.extend(_check_blind_solve(lab_dir, resolved_ref, cfg, ingested=ingested))
    errors.extend(_check_review(cfg))
    if check_originality:
        orig_errors, _ = check_lab_originality(
            lab_dir,
            ref_dir=resolved_ref,
            sources_dir=sources_dir,
        )
        errors.extend(orig_errors)
    return errors


def finalise_lab(
    lab_dir: Path,
    *,
    ref_dir: Path | None = None,
    id_map_path: Path | None = None,
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
    offline: bool = False,
    allow_missing_lint: bool = False,
) -> dict[str, Any]:
    """Run all gates, then strip blindSolve code and trapMutants from lab.config.json."""
    errors = check_lab(
        lab_dir,
        ref_dir=ref_dir,
        id_map_path=id_map_path,
        vault_dir=vault_dir,
        universal_path=universal_path,
        offline=offline,
        allow_missing_lint=allow_missing_lint,
    )
    if errors:
        raise ValueError("\n".join(errors))

    cfg_path = lab_dir / "lab.config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    final_cfg = copy.deepcopy(cfg)

    if isinstance(final_cfg.get("blindSolve"), list):
        final_cfg["blindSolve"] = [
            {"milestone": entry.get("milestone"), "passed": True}
            for entry in final_cfg["blindSolve"]
            if isinstance(entry, dict)
        ]

    for ms in final_cfg.get("milestones") or []:
        if isinstance(ms, dict):
            ms.pop("trapMutant", None)

    cfg_path.write_text(json.dumps(final_cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return final_cfg


def _resolve_ingested_lab_dir(target: str) -> Path:
    candidate = Path(target)
    if candidate.is_dir():
        return candidate
    labs_root = Path(os.environ.get("LABS_DIR", "labs"))
    return labs_root / target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m code_engine.lab_ingest",
        description="Validate and finalise a PRG project lab.",
    )
    parser.add_argument("lab_dir", nargs="?", default=None, help="Path to lab directory, e.g. labs/LAB-PRG-T01-C01-01")
    parser.add_argument("--check", action="store_true", help="Run gates only without modifying lab.config.json")
    parser.add_argument(
        "--ingested",
        nargs="?",
        const=True,
        default=False,
        help="Re-run gates on an already-finalised lab (accepts stripped blindSolve/trapMutant provenance). Pass a LAB_ID/path or combine with --check <lab_dir>.",
    )
    parser.add_argument(
        "--allow-missing-lint",
        action="store_true",
        help="Allow skipping ESLint/tsc gates if tools/lint/node_modules is missing (or set LEARNINGOS_ALLOW_MISSING_LINT=1).",
    )
    parser.add_argument("--offline", action="store_true", help="Skip Notion Status GET check for extra-project")
    parser.add_argument("--id-map", default="id_map.json", help="Path to id_map.json")
    parser.add_argument("--vault-dir", default=None, help="Override reasoning_vault directory")
    parser.add_argument(
        "--originality",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="With --check: run the source code/prompt originality gate (default: ON when sources dir exists, skipped with a notice when absent).",
    )
    parser.add_argument(
        "--sources-dir",
        default=None,
        help="Override sources directory for --originality (default: LEARNINGOS_SOURCES_DIR or <main>/sources).",
    )
    args = parser.parse_args(argv)

    ingested_mode = bool(args.ingested)
    raw_target = args.lab_dir
    if raw_target is None and isinstance(args.ingested, str):
        raw_target = args.ingested
    if not raw_target:
        parser.error("lab_dir is required (or pass --ingested <LAB_ID>)")

    lab_dir = _resolve_ingested_lab_dir(raw_target) if ingested_mode else Path(raw_target)
    id_map_path = Path(args.id_map)
    vault_dir = Path(args.vault_dir) if args.vault_dir else None

    if args.check or ingested_mode:
        errors = check_lab(
            lab_dir,
            id_map_path=id_map_path,
            vault_dir=vault_dir,
            offline=args.offline,
            ingested=ingested_mode,
            allow_missing_lint=args.allow_missing_lint,
        )
        resolved_sources = resolve_sources_dir(sources_dir=args.sources_dir)
        if args.originality is False:
            pass
        elif not os.path.isdir(resolved_sources):
            print(f"NOTE: Originality gate skipped (sources directory not found: {resolved_sources}).")
        else:
            orig_errors, orig_notice = check_lab_originality(
                lab_dir,
                sources_dir=resolved_sources,
            )
            if orig_notice:
                print(f"NOTE: {orig_notice}")
            errors.extend(orig_errors)
        if errors:
            for err in errors:
                print(f"FAIL: {err}", file=sys.stderr)
            return 1
        print(f"OK: {lab_dir.name} passed all lab_ingest gates.")
        return 0

    try:
        cfg = finalise_lab(
            lab_dir,
            id_map_path=id_map_path,
            vault_dir=vault_dir,
            offline=args.offline,
            allow_missing_lint=args.allow_missing_lint,
        )
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"Finalised {cfg.get('labId', lab_dir.name)} ({len(cfg.get('milestones', []))} milestones).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
