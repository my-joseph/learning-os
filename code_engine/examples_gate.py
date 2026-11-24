# -*- coding: utf-8 -*-
"""Shared schema, zero-leak, and reference-execution gates for PRG `examples` and `constraints`."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable

from code_engine.test_runner import run_tests
from code_engine.workspace import _strip_js_comments, extract_exports, resolve_test_imports

TOY_IDENTIFIER_PATTERN = re.compile(
    r"\b(foo|baz|qux|foobar|test1|test2|test3|funcA|funcB|func1|func2|"
    r"myFunc|myVar|someVar|someFunc|doSomething|temp1|temp2|dummy|dummyFunc|dummyVar)\b|"
    r"(?<!progress[-_ ])(?<!status[-_ ])(?<!scroll[-_ ])(?<!app[-_ ])(?<!nav[-_ ])(?<!tool[-_ ])\bbar\b",
    re.IGNORECASE,
)

_THAI_RE = re.compile(r"[\u0E00-\u0E7F]")
_RAW_ID_TOKEN_RE = re.compile(r"\[\[[^\]]*\]\]")
_LEAK_MARKER_RE = re.compile(
    r"(//\s*(?:BUG|DEFECT|FIX HERE|FIX ME|SOLUTION|ANSWER)\s*:|\btrapMutant\b|\bsolutionCode\b)",
    re.IGNORECASE,
)
_LEADING_AWAIT_RE = re.compile(r"^\s*await\b\s*")


def normalize_js_expr(expr: str) -> str:
    """Normalize a JS/TS expression for whitespace-insensitive comparison while preserving string literals."""
    if not isinstance(expr, str):
        return ""
    stripped = _strip_js_comments(expr).strip()
    stripped = _LEADING_AWAIT_RE.sub("", stripped)
    out: list[str] = []
    i = 0
    n = len(stripped)
    while i < n:
        ch = stripped[i]
        if ch in ('"', "'", "`"):
            quote = ch
            j = i + 1
            while j < n:
                if stripped[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if stripped[j] == quote:
                    j += 1
                    break
                j += 1
            out.append(stripped[i:j])
            i = j
            continue
        if ch.isspace():
            while i < n and stripped[i].isspace():
                i += 1
            prev_ch = out[-1][-1] if out and out[-1] else ""
            next_ch = stripped[i] if i < n else ""
            if (
                prev_ch
                and next_ch
                and (prev_ch.isalnum() or prev_ch in "_$")
                and (next_ch.isalnum() or next_ch in "_$")
            ):
                out.append(" ")
            continue
        out.append(ch)
        i += 1
    return "".join(out).strip()


def _check_text_fragments(pid: str, label: str, text: str, *, check_toy: bool = True) -> list[str]:
    errors: list[str] = []
    if check_toy:
        m_toy = TOY_IDENTIFIER_PATTERN.search(text)
        if m_toy:
            errors.append(f"[{pid}] Zero Toy Code Guard violated: found toy identifier '{m_toy.group()}' in {label}.")
    if _THAI_RE.search(text):
        errors.append(f"[{pid}] {label} contains non-English (Thai) text.")
    if _RAW_ID_TOKEN_RE.search(text):
        errors.append(f"[{pid}] {label} contains raw [[ID]] token.")
    m_leak = _LEAK_MARKER_RE.search(text)
    if m_leak:
        errors.append(f"[{pid}] Leak marker '{m_leak.group(1)}' found in {label}.")
    return errors


def validate_examples_and_constraints_schema(
    pid: str,
    item: dict[str, Any],
    *,
    require_examples: bool = False,
) -> list[str]:
    """Validate optional `constraints` and `examples` fields on a PRG problem or lab milestone."""
    errors: list[str] = []

    if "constraints" in item and item["constraints"] is not None:
        constraints = item["constraints"]
        if not isinstance(constraints, list):
            errors.append(f"[{pid}] 'constraints' must be a list of strings.")
        else:
            for idx, c in enumerate(constraints, 1):
                if not isinstance(c, str) or not c.strip():
                    errors.append(f"[{pid}] constraints[{idx}] must be a non-empty string.")
                else:
                    errors.extend(_check_text_fragments(pid, f"constraints[{idx}]", c))

    raw_examples = item.get("examples")
    if raw_examples is None:
        if require_examples:
            errors.append(f"[{pid}] Missing 'examples': new problems/milestones require 2-3 examples.")
        return errors

    if not isinstance(raw_examples, list):
        errors.append(f"[{pid}] 'examples' must be a list of 2-3 example objects.")
        return errors

    if not (2 <= len(raw_examples) <= 3):
        errors.append(f"[{pid}] 'examples' must contain 2-3 examples (got {len(raw_examples)}).")
        return errors

    for idx, ex in enumerate(raw_examples, 1):
        if not isinstance(ex, dict):
            errors.append(f"[{pid}] examples[{idx}] must be an object.")
            continue
        for req_key in ("input", "output", "call"):
            val = ex.get(req_key)
            if not isinstance(val, str) or not val.strip():
                errors.append(f"[{pid}] examples[{idx}] is missing a non-empty '{req_key}' string.")
            else:
                errors.extend(_check_text_fragments(pid, f"examples[{idx}].{req_key}", val))
        expl = ex.get("explanation")
        if expl is not None:
            if not isinstance(expl, str):
                errors.append(f"[{pid}] examples[{idx}].explanation must be a string.")
            elif expl.strip():
                errors.extend(_check_text_fragments(pid, f"examples[{idx}].explanation", expl))

    return errors


def check_examples_zero_leak(
    pid: str,
    examples: list[dict[str, Any]],
    hidden_sources: list[tuple[str, str]],
) -> list[str]:
    """Reject any example whose normalized `call` matches a hidden test case."""
    if not examples or not hidden_sources:
        return []
    normalized_hidden = [(label, normalize_js_expr(code)) for label, code in hidden_sources if code and code.strip()]
    errors: list[str] = []
    for idx, ex in enumerate(examples, 1):
        call = ex.get("call")
        if not isinstance(call, str) or not call.strip():
            continue
        norm_call = normalize_js_expr(call)
        if not norm_call:
            continue
        pat = re.compile(rf"(?<![A-Za-z0-9_$]){re.escape(norm_call)}(?![A-Za-z0-9_$])")
        for label, norm_hid in normalized_hidden:
            if pat.search(norm_hid):
                errors.append(
                    f"[{pid}] Zero-Leak Guard violated: Example {idx} call {call!r} matches hidden test ({label})."
                )
                break
    return errors


def build_example_assertion_body(call_expr: str, output_expr: str) -> str:
    """Build JS/TS assertion code comparing `await call_expr` against parsed `output_expr` via deepStrictEqual."""
    expected_js = f"({output_expr})"
    if output_expr.strip() != "-0":
        try:
            parsed = json.loads(output_expr)
        except (ValueError, TypeError):
            parsed = None
        else:
            expected_js = f"JSON.parse({json.dumps(json.dumps(parsed))})"

    return (
        f"const __actual = await (async () => (\n{call_expr}\n))();\n"
        f"const __expected = {expected_js};\n"
        "assert.deepStrictEqual(__actual, __expected);"
    )


def _format_example_failure(pid: str, idx: int, ex: dict[str, Any], detail: str) -> str:
    cleaned = (detail or "Verification failed").strip()
    return (
        f"[{pid}] Example {idx} failed verification (call={ex.get('call')!r}, output={ex.get('output')!r}): {cleaned}"
    )


def evaluate_drill_examples(
    pid: str,
    prob: dict[str, Any],
    *,
    environment: str = "node-vanilla",
) -> list[str]:
    """Evaluate every example `call` against `prob['solutionCode']` using `code_engine.test_runner`."""
    examples = prob.get("examples")
    if not isinstance(examples, list) or not examples:
        return []
    sol = prob.get("solutionCode") or (prob.get("verify") or {}).get("solutionCode") or ""
    if not sol.strip():
        return [f"[{pid}] Cannot verify examples without 'solutionCode'."]
    if shutil.which("node") is None:
        return [f"[{pid}] Cannot verify examples: Node.js is not installed (examples must run against the reference)."]

    def _run_batch(batch: list[tuple[int, dict[str, Any]]]) -> list[dict[str, Any]]:
        all_calls = "\n".join(ex["call"] for _, ex in batch)
        import_names = resolve_test_imports(prob, all_calls)
        tests = [
            {
                "name": f"example {idx}",
                "testCode": build_example_assertion_body(ex["call"], ex["output"]),
            }
            for idx, ex in batch
        ]
        report = run_tests(
            sol,
            tests,
            [],
            environment=environment,
            entry_point=", ".join(import_names),
        )
        return report.get("visibleResults") or []

    indexed = list(enumerate(examples, 1))
    results = _run_batch(indexed)
    if len(results) == len(indexed):
        errors: list[str] = []
        for (idx, ex), res in zip(indexed, results):
            if not res.get("passed"):
                errors.append(_format_example_failure(pid, idx, ex, str(res.get("error") or "")))
        return errors

    # If the bundled script failed to parse/compile (e.g. a bad literal in one example), isolate per example.
    errors = []
    for idx, ex in indexed:
        single = _run_batch([(idx, ex)])
        if not single or not single[0].get("passed"):
            err_msg = str(single[0].get("error") or "") if single else "0 tests ran"
            errors.append(_format_example_failure(pid, idx, ex, err_msg))
    return errors


def _collect_lab_exports(ref_src: Path, main_file: str | None = None) -> dict[str, Path]:
    """Map exported runtime symbol names in `ref_src` to their defining source Path."""
    files = sorted(list(ref_src.rglob("*.tsx")) + list(ref_src.rglob("*.ts")) + list(ref_src.rglob("*.js")))
    if main_file:
        rel_main = main_file.lstrip("/")
        if rel_main.startswith("src/"):
            rel_main = rel_main[4:]
        main_path = (ref_src / rel_main).resolve()
        files.sort(key=lambda p: (0 if p.resolve() == main_path else 1, str(p)))

    symbol_to_file: dict[str, Path] = {}
    for f in files:
        if ".test." in f.name:
            continue
        text = f.read_text(encoding="utf-8")
        for sym in extract_exports(text):
            symbol_to_file.setdefault(sym, f)
    return symbol_to_file


def _build_lab_example_test_source(
    batch: list[tuple[int, dict[str, Any]]],
    symbol_to_file: dict[str, Path],
    *,
    is_tsx: bool,
    ref_src: Path | None = None,
) -> str:
    all_calls = "\n".join(ex["call"] for _, ex in batch)
    by_file: dict[Path, list[str]] = {}
    for sym, path in symbol_to_file.items():
        if re.search(rf"\b{re.escape(sym)}\b", all_calls):
            by_file.setdefault(path, []).append(sym)

    lines = [
        "import { test } from 'vitest';" if is_tsx else "import test from 'node:test';",
        "import assert from 'node:assert';",
    ]
    ref_src_resolved = ref_src.resolve() if ref_src is not None else None
    for src_path, syms in by_file.items():
        src_resolved = src_path.resolve()
        if ref_src_resolved is not None:
            try:
                rel_posix = src_resolved.relative_to(ref_src_resolved).as_posix()
                specifier = f"../src/{rel_posix}"
            except ValueError:
                specifier = src_resolved.as_posix() if is_tsx else src_resolved.as_uri()
        else:
            specifier = src_resolved.as_posix() if is_tsx else src_resolved.as_uri()
        lines.append(f"import {{ {', '.join(syms)} }} from {json.dumps(specifier)};")
    lines.append("")

    for idx, ex in batch:
        body = build_example_assertion_body(ex["call"], ex["output"])
        lines.append(f"test({json.dumps(f'example {idx}')}, async () => {{\n{body}\n}});")
    return "\n".join(lines) + "\n"


def evaluate_lab_milestone_examples(
    mid: str,
    ms: dict[str, Any],
    lab_dir: Path,
    ref_dir: Path,
    run_node_tests_fn: Callable[[list[Path], Path, Path], list[dict[str, Any]]],
    *,
    tools_lint_dir: Path | None = None,
) -> list[str]:
    """Evaluate every example `call` on a lab milestone against `ref_dir / 'src'`."""
    examples = ms.get("examples")
    if not isinstance(examples, list) or not examples:
        return []
    if shutil.which("node") is None:
        return [
            f"[{ms.get('id', '?')}] Cannot verify examples: Node.js is not installed (examples must run against the reference)."
        ]

    ref_src = ref_dir / "src"
    if not ref_src.is_dir():
        return [f"[{mid}] Cannot verify examples without reference src directory {ref_src}."]

    symbol_to_file = _collect_lab_exports(
        ref_src, main_file=ms.get("mainFile") if isinstance(ms.get("mainFile"), str) else None
    )
    vis_pattern = str(ms.get("visibleTests") or "")
    all_calls = "\n".join(str(ex.get("call") or "") for ex in examples if isinstance(ex, dict))
    used_files = [path for sym, path in symbol_to_file.items() if re.search(rf"\b{re.escape(sym)}\b", all_calls)]
    is_tsx = ".tsx" in vis_pattern or any(p.suffix == ".tsx" for p in used_files)
    is_ts = is_tsx or ".ts" in vis_pattern or any(p.suffix == ".ts" for p in symbol_to_file.values())
    ext = "test.tsx" if is_tsx else ("test.ts" if is_ts else "test.js")

    def _run_batch(batch: list[tuple[int, dict[str, Any]]]) -> list[dict[str, Any]]:
        content = _build_lab_example_test_source(batch, symbol_to_file, is_tsx=is_tsx, ref_src=ref_src)
        with tempfile.TemporaryDirectory(prefix=f"lab_ex_{mid}_") as tmp:
            tmp_root = Path(tmp)
            tmp_tests = tmp_root / "tests"
            tmp_tests.mkdir(parents=True, exist_ok=True)
            pkg_src = lab_dir / "package.json"
            if pkg_src.is_file() and not pkg_src.is_symlink():
                shutil.copy2(pkg_src, tmp_root / "package.json")
            test_path = tmp_tests / f"{mid.lower()}_examples.{ext}"
            test_path.write_text(content, encoding="utf-8")
            return run_node_tests_fn([test_path], tmp_root, ref_src)

    indexed = list(enumerate(examples, 1))
    cases = _run_batch(indexed)
    if len(cases) == len(indexed):
        errors: list[str] = []
        for (idx, ex), c in zip(indexed, cases):
            if not c.get("passed"):
                errors.append(_format_example_failure(mid, idx, ex, str(c.get("failure_msg") or "")))
        return errors

    errors = []
    for idx, ex in indexed:
        single = _run_batch([(idx, ex)])
        if not single or not single[0].get("passed"):
            err_msg = str(single[0].get("failure_msg") or "") if single else "0 tests ran"
            errors.append(_format_example_failure(mid, idx, ex, err_msg))
    return errors
