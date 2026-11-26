# -*- coding: utf-8 -*-
"""Shared sandboxed PRG subprocess runners for Node JUnit, Vitest React/TSX, ESLint, and `tsc`."""

from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from code_engine.lint_check import (
    TOOLS_LINT_DIR,
    UNTRUSTED_TOOL_CONFIG_NAMES,
    LintToolsMissingError,
    build_trusted_eslint_config,
    build_trusted_tsconfig,
    get_lint_binaries,
)
from code_engine.sandbox import (
    DEFAULT_REACT_TIMEOUT_SEC,
    DEFAULT_TIMEOUT_SEC,
    DEFAULT_TOOL_TIMEOUT_SEC,
    SandboxResult,
    create_sandbox_dir,
    run_isolated,
    run_node_isolated,
    run_vitest_isolated,
    stage_lab_copy,
    stage_workspace_copy,
)

TS_PRESETS = ("typescript-strict", "backend-sqlite", "react-dom")
_TSC_DIAG_RE = re.compile(r"^(.+?)\((\d+),(\d+)\):\s+(?:error|warning)\s+(TS\d+:\s*.*)$")
_LAB_TS_INCLUDE = ("src/**/*.ts", "src/**/*.tsx", "tests/**/*.test-d.ts")
_LAB_ESLINT_TS_INCLUDE = ("src/**/*.ts", "src/**/*.tsx")


def active_tools_lint_dir(*, respect_env_root: bool = False) -> Path:
    """Resolve `tools/lint` under `LEARNINGOS_ROOT` when requested and present, else `TOOLS_LINT_DIR`."""
    if respect_env_root:
        env_root = os.environ.get("LEARNINGOS_ROOT")
        if env_root:
            candidate = Path(env_root).resolve() / "tools" / "lint"
            if candidate.exists() or candidate.is_symlink():
                return candidate
    return TOOLS_LINT_DIR


def _symlink_shared_modules(dst_dir: Path, lint_dir: Path) -> None:
    shared_modules = (lint_dir / "node_modules").resolve()
    target = dst_dir / "node_modules"
    if shared_modules.is_dir() and not target.exists() and not target.is_symlink():
        target.symlink_to(shared_modules, target_is_directory=True)


def resolve_eslint_tools(*, respect_env_root: bool = False, missing_ok: bool = False) -> tuple[Path, Path] | None:
    """Return `(base_js, eslint_bin)` for the active lint toolkit."""
    lint_dir = active_tools_lint_dir(respect_env_root=respect_env_root)
    try:
        same_as_default = lint_dir.resolve() == TOOLS_LINT_DIR.resolve()
    except OSError:
        same_as_default = False
    if not same_as_default:
        base_js = lint_dir / "base.js"
        eslint_bin = lint_dir / "node_modules" / ".bin" / "eslint"
        if base_js.exists() and eslint_bin.exists():
            return base_js, eslint_bin
        if missing_ok:
            return None
        raise LintToolsMissingError(
            f"Lint toolkit not installed. Expected {base_js} and {eslint_bin}. Run `npm ci` in tools/lint."
        )
    try:
        return get_lint_binaries()
    except LintToolsMissingError:
        if missing_ok:
            return None
        raise


def resolve_tsc_bin(*, respect_env_root: bool = False, missing_ok: bool = False) -> Path | None:
    """Return the active TypeScript compiler (`tsc`) binary path."""
    lint_dir = active_tools_lint_dir(respect_env_root=respect_env_root)
    tsc_bin = (lint_dir if respect_env_root else lint_dir.resolve()) / "node_modules" / ".bin" / "tsc"
    if tsc_bin.exists():
        return tsc_bin
    if missing_ok:
        return None
    raise FileNotFoundError(f"TypeScript compiler not installed at {tsc_bin}. Run `npm ci` in tools/lint.")


def parse_junit_xml(raw: str, force_hidden: bool = False, *, require_complete: bool = False) -> list[dict[str, Any]]:
    """Parse Node or Vitest JUnit XML into normalized testcase dicts."""
    xml_start = raw.find("<?xml")
    if xml_start == -1:
        xml_start = raw.find("<testsuites")
    if xml_start == -1:
        return []

    xml_text = raw[xml_start:].strip()
    end_tag = "</testsuites>"
    end_idx = xml_text.rfind(end_tag)
    if end_idx != -1:
        xml_text = xml_text[: end_idx + len(end_tag)]

    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return []

    if require_complete:
        if root.tag not in {"testsuites", "testsuite"} or root.find(".//skipped") is not None:
            return []
        for suite in (root, *root.iterfind(".//testsuite")):
            declared = suite.get("tests")
            # Node counts immediate child suites as tests; Vitest reports the total number of cases.
            if declared is not None and declared not in {
                str(len(suite.findall("testcase")) + len(suite.findall("testsuite"))),
                str(len(suite.findall(".//testcase"))),
            }:
                return []

    cases: list[dict[str, Any]] = []
    for tc in root.findall(".//testcase"):
        name = tc.attrib.get("name", "")
        f_elem = tc.find("failure")
        if f_elem is None:
            f_elem = tc.find("error")
        fail_msg = f_elem.attrib.get("message", f_elem.text or "Assertion failed") if f_elem is not None else ""
        cases.append(
            {
                "name": name,
                "file": tc.attrib.get("file", ""),
                "classname": tc.attrib.get("classname", ""),
                "passed": f_elem is None,
                "failure_msg": fail_msg,
                "is_hidden": force_hidden or "HIDDEN" in name.upper(),
            }
        )
    return cases


def parse_completed_junit_run(raw: str, returncode: int, *, force_hidden: bool) -> list[dict[str, Any]]:
    """Reject incomplete reports and runner failures that are absent from the test cases."""
    cases = parse_junit_xml(raw, force_hidden=force_hidden, require_complete=True)
    return [] if (returncode != 0 and all(case["passed"] for case in cases)) else cases


def _error_case(name: str, msg: str, *, force_hidden: bool = False, file_hint: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "file": file_hint,
        "classname": "",
        "passed": False,
        "failure_msg": msg,
        "is_hidden": force_hidden,
    }


def _check_proc_bounds(
    proc: SandboxResult,
    *,
    timeout_sec: float,
    timeout_name: str,
    truncated_name: str,
    force_hidden: bool = False,
    file_hint: str = "",
) -> list[dict[str, Any]] | None:
    if proc.timed_out:
        return [
            _error_case(
                timeout_name, f"Execution exceeded {timeout_sec}s limit", force_hidden=force_hidden, file_hint=file_hint
            )
        ]
    if proc.output_truncated:
        return [
            _error_case(
                truncated_name, "Execution exceeded output size limit", force_hidden=force_hidden, file_hint=file_hint
            )
        ]
    return None


def run_node_junit_cmd(
    node_args: Sequence[str],
    *,
    cwd: Path,
    sandbox_root: Path,
    force_hidden: bool = False,
    timeout_sec: float | None = None,
    file_hint: str = "",
    qid_hint: str = "Q01",
    run_node_fn: Callable[..., SandboxResult] = run_node_isolated,
) -> list[dict[str, Any]]:
    """Run one Node `--test --test-reporter=junit` command inside the sandbox and parse results."""
    eff_timeout = timeout_sec if timeout_sec is not None else DEFAULT_TIMEOUT_SEC
    proc = run_node_fn(list(node_args), cwd=cwd, sandbox_root=sandbox_root, timeout_sec=eff_timeout)
    bounded = _check_proc_bounds(
        proc,
        timeout_sec=eff_timeout,
        timeout_name=f"[{qid_hint}] Timeout",
        truncated_name=f"[{qid_hint}] Output limit exceeded",
        force_hidden=force_hidden,
        file_hint=file_hint,
    )
    if bounded is not None:
        return bounded
    parsed = parse_junit_xml(proc.stdout + "\n" + proc.stderr, force_hidden=force_hidden)
    if not parsed and proc.returncode != 0:
        err_msg = (proc.stderr or proc.stdout or f"Exited with code {proc.returncode}").strip()
        return [_error_case(f"[{qid_hint}] Execution failure", err_msg, force_hidden=force_hidden, file_hint=file_hint)]
    return parsed


def run_vitest_junit(
    test_files: Sequence[Path],
    cwd: Path,
    *,
    timeout_sec: float | None = None,
    force_hidden: bool = False,
    env: Mapping[str, str] | None = None,
    require_complete: bool = False,
    sandbox_root: Path | None = None,
    tools_lint_dir: Path | None = None,
    extra_allowed_dirs: Sequence[Path] = (),
    unavailable_name: str = "React runner unavailable",
    run_vitest_fn: Callable[..., SandboxResult] = run_vitest_isolated,
) -> list[dict[str, Any]]:
    """Run React/TSX tests with shared Vitest inside the sandbox (never mutating `cwd`) and return JUnit cases."""
    tools_dir = (tools_lint_dir or TOOLS_LINT_DIR).resolve()
    shared_modules = (tools_dir / "node_modules").resolve()
    vitest = shared_modules / ".bin" / "vitest"
    if not vitest.is_file():
        return [
            _error_case(
                unavailable_name,
                f"Vitest is missing at {vitest}; run npm ci in tools/lint.",
                force_hidden=force_hidden,
            )
        ]

    eff_timeout = timeout_sec if timeout_sec is not None else DEFAULT_REACT_TIMEOUT_SEC
    cwd_real = Path(os.path.realpath(cwd))
    test_files_real = [Path(os.path.realpath(f)) for f in test_files]
    test_root = Path(os.path.commonpath([str(f.parent) for f in test_files_real])) if test_files_real else cwd_real

    own_sbx = create_sandbox_dir(prefix="prg_vitest_") if sandbox_root is None else None
    try:
        sbx_root = Path(os.path.realpath(own_sbx.name if own_sbx is not None else sandbox_root))
        _symlink_shared_modules(sbx_root, tools_dir)
        extra_real = tuple(Path(os.path.realpath(d)) for d in extra_allowed_dirs)
        allowed_dirs = list(
            dict.fromkeys(str(d) for d in (sbx_root, cwd_real, *extra_real, test_root, shared_modules, tools_dir))
        )
        config_path = sbx_root / f"vitest.config.{os.getpid()}.{id(test_files)}.ts"
        report_path = sbx_root / f"vitest-junit-{os.getpid()}-{id(test_files)}.xml"
        allow_js = ", ".join(json.dumps(d) for d in allowed_dirs)
        config_path.write_text(
            "import { defineConfig } from 'vitest/config';\n"
            f"export default defineConfig({{ root: {json.dumps(str(test_root))}, esbuild: {{ jsx: 'automatic' }}, test: {{ environment: 'jsdom' }}, server: {{ fs: {{ allow: [{allow_js}] }} }} }});\n",
            encoding="utf-8",
        )
        env_extra = {k: v for k, v in (env or {}).items() if k in ("LAB_SRC_DIR",)}
        proc = run_vitest_fn(
            test_files_real,
            cwd=cwd_real,
            sandbox_root=sbx_root,
            config_path=config_path,
            report_path=report_path,
            reporter="junit",
            timeout_sec=eff_timeout,
            env_extra=env_extra,
            tools_lint_dir=tools_dir,
        )
        bounded = _check_proc_bounds(
            proc,
            timeout_sec=eff_timeout,
            timeout_name="React test timeout",
            truncated_name="React test output limit exceeded",
            force_hidden=force_hidden,
        )
        if bounded is not None:
            return bounded
        raw = report_path.read_text(encoding="utf-8") if report_path.is_file() else ""
        if require_complete:
            return parse_completed_junit_run(raw, proc.returncode, force_hidden=force_hidden)
        cases = parse_junit_xml(raw, force_hidden=force_hidden)
        if cases:
            return cases
        message = (proc.stderr or proc.stdout or f"Vitest exited with code {proc.returncode}").strip()
        return [_error_case("React test execution failure", message, force_hidden=force_hidden)]
    finally:
        if own_sbx is not None:
            own_sbx.cleanup()


def run_lab_tests(
    test_files: Sequence[Path],
    cwd: Path,
    src_dir: Path,
    *,
    force_hidden: bool = False,
    require_complete: bool = False,
    allowed_test_roots: Sequence[Path] | None = None,
    sandbox_prefix: str = "prg_lab_ingest_",
    tools_lint_dir: Path | None = None,
    unavailable_name: str = "React test runner unavailable",
    force_vitest: bool = False,
    run_node_fn: Callable[..., SandboxResult] = run_node_isolated,
    run_vitest_fn: Callable[..., SandboxResult] = run_vitest_isolated,
) -> list[dict[str, Any]]:
    """Run lab Node/TS or React TSX acceptance tests inside a per-run isolated sandbox."""
    if not test_files:
        return []
    tools_dir = (tools_lint_dir or TOOLS_LINT_DIR).resolve()
    with create_sandbox_dir(prefix=sandbox_prefix) as sbx_str:
        sbx_root = Path(os.path.realpath(sbx_str))
        work_dir, staged_src, staged_tests = stage_lab_copy(
            cwd, src_dir, test_files, sbx_root / "work", allowed_test_roots=allowed_test_roots
        )
        env_extra = {"LAB_SRC_DIR": str(staged_src.resolve())}
        if force_vitest or any(f.suffix == ".tsx" for f in staged_tests):
            _symlink_shared_modules(work_dir, tools_dir)
            return run_vitest_junit(
                staged_tests,
                work_dir,
                force_hidden=force_hidden,
                env=env_extra,
                require_complete=require_complete,
                sandbox_root=sbx_root,
                tools_lint_dir=tools_dir,
                extra_allowed_dirs=(staged_src,),
                unavailable_name=unavailable_name,
                run_vitest_fn=run_vitest_fn,
            )
        all_cases: list[dict[str, Any]] = []
        for tf in staged_tests:
            node_args = ["--experimental-strip-types"] if tf.suffix in (".ts", ".tsx") else []
            node_args.extend(["--test", "--test-reporter=junit", str(tf.relative_to(work_dir))])
            proc = run_node_fn(
                node_args, cwd=work_dir, sandbox_root=sbx_root, timeout_sec=DEFAULT_TIMEOUT_SEC, env_extra=env_extra
            )
            bounded = _check_proc_bounds(
                proc,
                timeout_sec=DEFAULT_TIMEOUT_SEC,
                timeout_name="Lab test timeout",
                truncated_name="Lab test output limit exceeded",
                force_hidden=force_hidden,
            )
            if bounded is not None:
                return bounded
            combined = proc.stdout + "\n" + proc.stderr
            if require_complete:
                file_cases = parse_completed_junit_run(combined, proc.returncode, force_hidden=force_hidden)
                if not file_cases:
                    return []
            else:
                file_cases = parse_junit_xml(combined, force_hidden=force_hidden)
            all_cases.extend(file_cases)
        return all_cases


def run_eslint_sandbox(
    target_dir: Path,
    *,
    target_arg: str = "src",
    stage_subdir: str | None = "src",
    tsconfig_include: Sequence[str] | None = _LAB_ESLINT_TS_INCLUDE,
    jsx: bool | None = None,
    symlink_node_modules: bool = True,
    file_label_override: str | None = None,
    lint_overrides: Sequence[dict[str, Any]] | None = None,
    respect_env_root: bool = False,
    missing_ok: bool = False,
    sandbox_prefix: str = "prg_eslint_",
) -> list[dict[str, Any]]:
    """Run ESLint on a staged copy of `target_dir` with a freshly generated trusted config."""
    tools = resolve_eslint_tools(respect_env_root=respect_env_root, missing_ok=missing_ok)
    if tools is None:
        return []
    base_js, eslint_bin = tools
    lint_dir = active_tools_lint_dir(respect_env_root=respect_env_root)

    with create_sandbox_dir(prefix=sandbox_prefix) as sbx_str:
        sbx_root = Path(os.path.realpath(sbx_str))
        work_dir = sbx_root / "work"
        dst = (work_dir / stage_subdir) if stage_subdir else work_dir
        staged_target = stage_workspace_copy(target_dir, dst, ignore_names=UNTRUSTED_TOOL_CONFIG_NAMES)
        cfg_path = work_dir / "eslint.config.mjs"
        cfg_path.write_text(build_trusted_eslint_config(base_js, lint_overrides), encoding="utf-8")
        if tsconfig_include is not None:
            has_tsx = jsx if jsx is not None else any(staged_target.rglob("*.tsx"))
            (work_dir / "tsconfig.json").write_text(
                json.dumps(build_trusted_tsconfig(include=tsconfig_include, jsx=has_tsx), indent=2) + "\n",
                encoding="utf-8",
            )
        if symlink_node_modules:
            _symlink_shared_modules(work_dir, lint_dir)
        proc = run_isolated(
            [str(eslint_bin), "--config", str(cfg_path), "--no-config-lookup", "--format", "json", target_arg],
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
        file_name = file_label_override if file_label_override is not None else Path(res.get("filePath", "")).name
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


def run_tsc_sandbox(
    root_dir: Path,
    *,
    include: Sequence[str] = _LAB_TS_INCLUDE,
    jsx: bool | None = None,
    respect_env_root: bool = False,
    missing_ok: bool = False,
    sandbox_prefix: str = "prg_tsc_",
) -> SandboxResult | None:
    """Run `tsc --noEmit` on a staged copy of `root_dir` with a trusted `tsconfig.json`."""
    tsc_bin = resolve_tsc_bin(respect_env_root=respect_env_root, missing_ok=missing_ok)
    if tsc_bin is None:
        return None
    lint_dir = active_tools_lint_dir(respect_env_root=respect_env_root)

    with create_sandbox_dir(prefix=sandbox_prefix) as sbx_str:
        sbx_root = Path(os.path.realpath(sbx_str))
        work_dir = stage_workspace_copy(root_dir, sbx_root / "work", ignore_names=UNTRUSTED_TOOL_CONFIG_NAMES)
        is_jsx = (
            jsx
            if jsx is not None
            else (any((work_dir / "src").rglob("*.tsx")) if (work_dir / "src").is_dir() else False)
        )
        staged_tsconfig = work_dir / "tsconfig.json"
        staged_tsconfig.write_text(
            json.dumps(build_trusted_tsconfig(include=include, jsx=is_jsx), indent=2) + "\n", encoding="utf-8"
        )
        _symlink_shared_modules(work_dir, lint_dir)
        return run_isolated(
            [str(tsc_bin), "--noEmit", "--pretty", "false", "-p", str(staged_tsconfig)],
            cwd=work_dir,
            sandbox_root=sbx_root,
            timeout_sec=DEFAULT_TOOL_TIMEOUT_SEC,
            use_node_permission=False,
        )


def parse_tsc_diagnostics(
    proc: SandboxResult,
    *,
    filter_filename: str | None = None,
    include_file: bool = True,
) -> list[dict[str, Any]]:
    """Parse `tsc --noEmit --pretty false` output into structured diagnostic dicts."""
    if proc.timed_out:
        return [{"line": 0, "message": f"Typecheck timed out after {DEFAULT_TOOL_TIMEOUT_SEC}s"}]
    if proc.returncode == 0:
        return []
    diagnostics: list[dict[str, Any]] = []
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    for line in combined.splitlines():
        stripped = line.strip()
        m = _TSC_DIAG_RE.match(stripped)
        if m:
            file_part, line_no, _col, msg = m.groups()
            fname = Path(file_part).name
            if filter_filename is not None and fname != filter_filename:
                continue
            item: dict[str, Any] = {"line": int(line_no), "message": msg.strip()}
            if include_file:
                item["file"] = fname
            diagnostics.append(item)
        elif filter_filename is None and "error TS" in line:
            diagnostics.append({"line": 0, "message": stripped})
    if filter_filename is not None and not diagnostics:
        # Surface non-file-specific tsconfig/compiler errors if any occurred.
        for ln in combined.splitlines():
            stripped = ln.strip()
            if "error TS" in ln and not _TSC_DIAG_RE.match(stripped):
                diagnostics.append({"line": 0, "message": stripped})
    return diagnostics


def format_tsc_raw_lines(proc: SandboxResult) -> list[str]:
    """Format `tsc --noEmit` failure output as raw non-empty diagnostic lines."""
    if proc.timed_out:
        return [f"tsc timed out after {DEFAULT_TOOL_TIMEOUT_SEC}s"]
    if proc.returncode == 0:
        return []
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    lines = [ln.strip() for ln in combined.splitlines() if ln.strip()]
    return lines or [f"tsc failed with exit code {proc.returncode}"]
