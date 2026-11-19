# -*- coding: utf-8 -*-
"""
AI Code Drill Ingestion & Reasoning Vault Engine:
Bridges dynamic AI-generated programming problems into:
1. The Code Reasoning Vault (code_engine/reasoning_vault/<unit_code>.json)
2. Machine-Verified local Drill JSON files (drills/data/<unit_code>/DRL-....json)
3. 100% Local IDE Scaffolding (drills/workspace/<drill_id>/) with package.json, npm test, and folder deep links.
"""

import argparse
import copy
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from code_engine.answer_check import parse_tokens
from code_engine.examples_gate import (
    TOY_IDENTIFIER_PATTERN,
    check_examples_zero_leak,
    evaluate_drill_examples,
    validate_examples_and_constraints_schema,
)
from code_engine.fmt import LEVEL_LABELS, unit_hierarchy
from code_engine.generate import next_drill_id
from code_engine.lint_check import (
    TS_PRESETS,
    LintToolsMissingError,
    lint_drill_doc,
    typecheck_code_snippet,
    typecheck_drill_doc,
)
from code_engine.quality_checks import load_universal, validate_quality_checks, verify_known_bad_lint
from code_engine.submit import run_tests_junit
from code_engine.verify import run_node, verify_problem
from code_engine.workspace import (
    ENVIRONMENT_PRESETS,
    extract_exports,
    materialize_drill_workspace,
    resolve_test_imports,
)
from progress_store import strip_progress
from quality_rules import QUALITY_RULES, find_choice_prompt_option_duplicates

CODE_VAULT_DIR = os.path.join(os.path.dirname(__file__), "reasoning_vault")


class AiContractError(Exception):
    """Raised when an AI-generated programming problem violates Contract 04_CODE or 07 §4."""

    pass


# ---------------------------------------------------------------------------
# Zero Toy Code Pattern (shared via code_engine.examples_gate)
# ---------------------------------------------------------------------------


def scan_for_toy_identifiers(text: str, location_label: str, pid: str) -> None:
    """Scans text/code for meaningless toy variable or function names."""
    if not isinstance(text, str):
        return
    match = TOY_IDENTIFIER_PATTERN.search(text)
    if match:
        raise AiContractError(
            f"[{pid}] Zero Toy Code Guard violated: found toy identifier '{match.group()}' in {location_label}. "
            "Must model realistic production domains (04_CODE §5.3)."
        )


def check_zero_wall_of_text(pid: str, prompt: str) -> None:
    """Enforces the Zero Wall-of-Text Standard on programming prompts (04_CODE §4)."""
    if not isinstance(prompt, str):
        return
    if len(prompt) > 250:
        has_bullets = ("- " in prompt) or ("* " in prompt) or ("\n- " in prompt)
        has_sections = ("**" in prompt) or ("### " in prompt) or ("## " in prompt)
        has_backticks = "`" in prompt

        if not (has_bullets and has_sections and has_backticks):
            missing = []
            if not has_bullets:
                missing.append("bullet points ('- ')")
            if not has_sections:
                missing.append("markdown sections/bolding ('**' or '###')")
            if not has_backticks:
                missing.append("code backticks ('`')")
            raise AiContractError(
                f"[{pid}] Zero Wall-of-Text Guard violated: prompt length {len(prompt)} > 250 chars "
                f"lacks required structure: missing {', '.join(missing)} (04_CODE §4)."
            )

        paragraphs = [p.strip() for p in prompt.split("\n\n") if p.strip()]
        for p_idx, para in enumerate(paragraphs, 1):
            if len(para) > 350 and ("- " not in para) and ("\n" not in para):
                raise AiContractError(
                    f"[{pid}] Zero Wall-of-Text Guard violated: unbroken paragraph {p_idx} has {len(para)} chars (> 350). "
                    "Break down into structured bullet points (04_CODE §4)."
                )


def check_zero_leak_hint(pid: str, prob: Dict[str, Any]) -> None:
    """Ensures hints, placeholders, and visible test names do not spoil the answer, tokens, or bug locations (04_CODE §7, 00_CORE §6)."""
    hints = []
    for k in ("inputHint", "placeholder", "checkpointHint"):
        v = prob.get(k)
        if v and isinstance(v, str):
            hints.append((k, v))
    spec = prob.get("answerSpec") or {}
    for k in ("inputHint", "placeholder"):
        v = spec.get(k)
        if v and isinstance(v, str):
            hints.append((f"answerSpec.{k}", v))
    for idx, t in enumerate(prob.get("visibleTests") or [], 1):
        t_name = t.get("name")
        if t_name and isinstance(t_name, str):
            hints.append((f"visibleTests[{idx}].name", t_name))

    answer_plain = str(prob.get("answerPlain", "")).strip()

    for hint_name, hint_text in hints:
        # 1. Plain answer leak
        if answer_plain and len(answer_plain) > 1 and answer_plain.lower() in hint_text.lower():
            raise AiContractError(
                f"[{pid}] Zero-Leak Hint Guard violated: {hint_name} '{hint_text}' leaks answerPlain '{answer_plain}' (04_CODE §7)."
            )

        # 2. Accepted / tokens leak
        tokens = spec.get("tokens") or parse_tokens(answer_plain)
        if tokens and len(tokens) >= 2:
            token_seq = ", ".join(tokens)
            if token_seq in hint_text:
                raise AiContractError(
                    f"[{pid}] Zero-Leak Hint Guard violated: {hint_name} leaks token sequence '{token_seq}' (04_CODE §7)."
                )

        # 3. HTTP Status code leaks (3-digit status codes)
        if re.fullmatch(r"^[1-5]\d{2}$", answer_plain):
            if re.search(rf"\b{answer_plain}\b", hint_text):
                raise AiContractError(
                    f"[{pid}] Zero-Leak Hint Guard violated: {hint_name} leaks HTTP Status code '{answer_plain}' (04_CODE §7)."
                )

        # 4. HTTP Method leaks (GET, POST, PUT, DELETE, PATCH)
        if answer_plain.upper() in {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}:
            if re.search(rf"\b{answer_plain}\b", hint_text, re.IGNORECASE):
                raise AiContractError(
                    f"[{pid}] Zero-Leak Hint Guard violated: {hint_name} leaks HTTP Method '{answer_plain}' (04_CODE §7)."
                )

        # 5. Flawed line leak in debugging
        correct_line = spec.get("correctLine") or prob.get("correctLine")
        if correct_line is not None:
            cline_str = str(correct_line)
            if re.search(rf"\bline\s*{cline_str}\b", hint_text, re.IGNORECASE) or re.search(
                rf"\bL{cline_str}\b", hint_text
            ):
                raise AiContractError(
                    f"[{pid}] Zero-Leak Hint Guard violated: {hint_name} leaks defective line number {cline_str} (04_CODE §7)."
                )


def _allow_missing_lint(explicit: bool = False) -> bool:
    return bool(explicit) or os.environ.get("LEARNINGOS_ALLOW_MISSING_LINT", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _check_code_compiles(
    pid: str,
    label: str,
    code: str,
    environment: str = "node-vanilla",
    *,
    allow_missing_lint: bool = False,
) -> None:
    """Verify starter/mutant code parses/compiles cleanly in Node or tsc."""
    if not code or not code.strip():
        return
    if environment in TS_PRESETS:
        ext = ENVIRONMENT_PRESETS.get(environment, {}).get("defaultExt", "ts")
        try:
            diags = typecheck_code_snippet(code, ext=ext, filename=f"{pid}_{label}")
        except LintToolsMissingError as exc:
            if _allow_missing_lint(allow_missing_lint):
                return
            raise AiContractError(
                f"[{pid}] {label} TypeScript compile gate cannot run: {exc} "
                "(Run `cd tools/lint && npm ci`, or opt out with --allow-missing-lint / LEARNINGOS_ALLOW_MISSING_LINT=1.)"
            ) from exc
        if diags:
            msg = "; ".join(f"line {d['line']} {d['message']}" for d in diags[:3])
            raise AiContractError(f"[{pid}] {label} failed TypeScript compile check: {msg}")
        return

    if shutil.which("node") is None:
        return
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name
    try:
        proc = subprocess.run(["node", "--check", tmp_path], capture_output=True, text=True, timeout=5.0)
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "syntax error").strip().splitlines()[0]
            raise AiContractError(f"[{pid}] {label} failed syntax check: {err}")
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _is_coding_problem(prob: Dict[str, Any]) -> bool:
    archetype = prob.get("archetype") or prob.get("codeType", "problem-solving")
    if (
        archetype in ("code-tracing", "predict-output")
        and not prob.get("solutionCode")
        and not prob.get("visibleTests")
    ):
        return False
    return True


def check_starter_contract(
    pid: str,
    prob: Dict[str, Any],
    environment: str = "node-vanilla",
    *,
    check_identical: bool = True,
    allow_missing_lint: bool = False,
) -> None:
    """Verify starterCode compiles/parses and does not leak the reference solution."""
    if not _is_coding_problem(prob):
        return
    starter = prob.get("starterCode") or ""
    sol = prob.get("solutionCode") or ""
    if not starter.strip():
        raise AiContractError(f"[{pid}] starterCode is required and cannot be empty.")

    _check_code_compiles(pid, "starterCode", starter, environment=environment, allow_missing_lint=allow_missing_lint)

    if sol.strip():
        if check_identical:
            norm_starter = re.sub(r"\s+", "", starter)
            norm_sol = re.sub(r"\s+", "", sol)
            if norm_starter == norm_sol:
                raise AiContractError(f"[{pid}] No-Leak Guard violated: starterCode is identical to solutionCode.")
        # Check if starter comments/body leak a multi-line solution body verbatim
        sol_lines = [
            ln.strip()
            for ln in sol.splitlines()
            if len(ln.strip()) >= 20 and not ln.strip().startswith("module.exports")
        ]
        if len(sol_lines) >= 2:
            leaked = [ln for ln in sol_lines if ln in starter and ("//" in starter or "/*" in starter)]
            if len(leaked) >= 2:
                raise AiContractError(f"[{pid}] No-Leak Guard violated: starterCode leaks solution lines.")

    all_tests = list(prob.get("visibleTests") or []) + list(prob.get("hiddenTests") or [])
    if all_tests:
        all_test_code = "\n".join(t.get("testCode", "") for t in all_tests)
        required_exports = resolve_test_imports(prob, all_test_code)
        starter_exports = set(extract_exports(starter))
        missing_exports = [name for name in required_exports if name not in starter_exports]
        if missing_exports:
            raise AiContractError(f"[{pid}] starterCode is missing export(s) referenced by tests: {missing_exports}.")


def run_problem_in_workspace(
    prob: Dict[str, Any],
    code: str,
    *,
    environment: str = "node-vanilla",
    run_visible: bool = True,
    run_hidden: bool = True,
    timeout_sec: float = 4.0,
) -> Dict[str, Any]:
    """Materialise a temp workspace for `prob` with `code` and execute visible/hidden tests like the learner."""
    pid = str(prob.get("id") or "Q01")
    ws_prob = copy.deepcopy(prob)
    ws_prob["id"] = pid
    ws_prob["starterCode"] = code
    if not run_visible:
        ws_prob["visibleTests"] = []
    if not run_hidden:
        ws_prob["hiddenTests"] = []
    expected_visible = len(ws_prob.get("visibleTests") or [])
    expected_hidden = len(ws_prob.get("hiddenTests") or [])

    drill_doc = {
        "drillId": f"GATE-{pid}",
        "environment": environment,
        "problems": [ws_prob],
    }
    with tempfile.TemporaryDirectory(prefix="prg_ws_gate_") as tmp_dir:
        manifest = materialize_drill_workspace(drill_doc, root_dir=tmp_dir)
        ws_dir = Path(manifest["workspaceDir"])
        cases = run_tests_junit(ws_dir, drill_doc, problem_id=pid, timeout_sec=timeout_sec)

    vis_cases = [c for c in cases if not c.get("is_hidden")]
    hid_cases = [c for c in cases if c.get("is_hidden")]
    vis_ok = len(vis_cases) >= expected_visible and all(c.get("passed") for c in vis_cases)
    hid_ok = len(hid_cases) >= expected_hidden and all(c.get("passed") for c in hid_cases)
    all_passed = bool(cases) and vis_ok and hid_ok

    visible_results = [
        {
            "name": c.get("name", ""),
            "passed": bool(c.get("passed")),
            "error": c.get("failure_msg", ""),
        }
        for c in vis_cases
    ]
    if not all_passed and not visible_results:
        failed_hid = [c for c in hid_cases if not c.get("passed")]
        visible_results = [
            {
                "name": c.get("name", "Hidden test failure"),
                "passed": False,
                "error": c.get("failure_msg", "Failed"),
            }
            for c in failed_hid
        ] or [{"name": "Execution failure", "passed": False, "error": "0 tests executed"}]

    return {
        "allPassed": all_passed,
        "visibleResults": visible_results,
        "hiddenPassed": sum(1 for c in hid_cases if c.get("passed")),
        "hiddenTotal": max(expected_hidden, len(hid_cases)),
    }


def check_dual_pre_execution(pid: str, prob: Dict[str, Any], environment: str = "node-vanilla") -> None:
    """Enforces dual pre-execution verification: Canonical is 100% Green, Starter fails at least one visible test."""
    archetype = prob.get("archetype") or prob.get("codeType", "problem-solving")
    sol = prob.get("solutionCode") or prob.get("verify", {}).get("solutionCode")
    starter = prob.get("starterCode")
    visible = prob.get("visibleTests", [])
    hidden = prob.get("hiddenTests", [])

    # 1. Canonical solution verification (100% Green)
    if sol and (visible or hidden):
        report = run_problem_in_workspace(prob, sol, environment=environment)
        if not report.get("allPassed"):
            failed = [r["name"] for r in report.get("visibleResults", []) if not r.get("passed")]
            raise AiContractError(
                f"[{pid}] Dual Pre-Execution Verification: Canonical solution failed test suite: {failed}. "
                f"Details: {report.get('visibleResults')}"
            )

    # 2. Starter code must fail at least one visible test (stub / buggy before Green)
    if _is_coding_problem(prob) and starter and visible:
        starter_report = run_problem_in_workspace(prob, starter, environment=environment, run_hidden=False)
        if starter_report.get("allPassed"):
            if archetype in ("debugging", "find-bug"):
                raise AiContractError(
                    f"[{pid}] Dual Pre-Execution Verification: Debugging starterCode unexpectedly passed all visible tests. "
                    "Red-before-Green invariant violated: starterCode must fail at least one reproducer test (04_CODE §2.1)."
                )
            raise AiContractError(
                f"[{pid}] Dual Pre-Execution Verification: starterCode unexpectedly passed all visible tests. "
                "Starter must be a stub (or contain the bug/missing requirement) that fails at least one visible test."
            )

    # 3. Code Tracing / Predict Output
    if archetype in ("code-tracing", "predict-output"):
        snippet = prob.get("codeSnippet")
        if not snippet:
            raise AiContractError(f"[{pid}] Code-tracing problem must provide codeSnippet.")
        stdout, stderr, code = run_node(snippet, files=prob.get("files"))
        if code != 0:
            raise AiContractError(f"[{pid}] Code-tracing snippet failed to run in Node (exit code {code}): {stderr}")
        node_tokens = parse_tokens(stdout)
        spec = prob.get("answerSpec", {})
        expected_tokens = spec.get("tokens") or parse_tokens(spec.get("value", prob.get("answerPlain", "")))
        if node_tokens != expected_tokens:
            raise AiContractError(
                f"[{pid}] Code-tracing pre-execution mismatch: Node stdout {node_tokens} != expected answer {expected_tokens}."
            )


# ---------------------------------------------------------------------------
# Anti-Spoonfeeding & Mutation Testing Guards
# ---------------------------------------------------------------------------
SPOONFEEDING_PROMPT_PATTERN = re.compile(
    r"(?:\*\*|#{1,4}\s*|\b)(Defect Analysis|Root Cause Analysis|Bug Analysis|Root Cause|Defect Cause)(?:\*\*|:|\b)",
    re.IGNORECASE,
)

SPOONFEEDING_COMMENT_PATTERN = re.compile(
    r"(?://|/\*)\s*(?:BUG|DEFECT|FIX HERE|FIX ME|SOLUTION|ERROR)\b",
    re.IGNORECASE,
)

SPOONFEEDING_HINT_PATTERN = re.compile(
    r"\b(secondary\s+Map|use\s+closure|new\s+Map\(\)|state\s+machine)\b",
    re.IGNORECASE,
)

SET_TIMEOUT_PATTERN = re.compile(r"setTimeout\s*\([^,]+,\s*(\d+)\s*\)")


def check_anti_spoonfeeding(pid: str, prob: Dict[str, Any]) -> None:
    """Enforces Anti-Spoonfeeding Guard (04_CODE §4, §7):
    - No 'Defect Analysis' or 'Root Cause' in prompt.
    - No '// BUG:' or '// FIX HERE:' in starterCode.
    - No naming of internal data structures (e.g. 'secondary Map', 'use closure') in hints.
    """
    prompt = prob.get("prompt", "")
    m_prompt = SPOONFEEDING_PROMPT_PATTERN.search(prompt)
    if m_prompt:
        raise AiContractError(
            f"[{pid}] Anti-Spoonfeeding Guard violated: prompt contains explicit defect analysis header '{m_prompt.group()}'. "
            "Specify observable behavior and SLA contracts instead of spoon-feeding the bug."
        )

    starter = prob.get("starterCode", "")
    m_starter = SPOONFEEDING_COMMENT_PATTERN.search(starter)
    if m_starter:
        raise AiContractError(
            f"[{pid}] Anti-Spoonfeeding Guard violated: starterCode contains spoiler comment '{m_starter.group()}'. "
            "Do not point out bug locations with inline comments."
        )

    hints = []
    for k in ("inputHint", "placeholder", "checkpointHint"):
        v = prob.get(k)
        if isinstance(v, str):
            hints.append((k, v))
    spec = prob.get("answerSpec") or {}
    for k in ("inputHint", "placeholder"):
        v = spec.get(k)
        if isinstance(v, str):
            hints.append((f"answerSpec.{k}", v))

    for h_name, h_val in hints:
        m_hint = SPOONFEEDING_HINT_PATTERN.search(h_val)
        if m_hint:
            raise AiContractError(
                f"[{pid}] Anti-Spoonfeeding Guard violated: {h_name} contains explicit data structure spoon-feeding '{m_hint.group()}'. "
                "Use behavioral or contract hints instead of prescribing implementation details."
            )


def check_deterministic_clock(pid: str, prob: Dict[str, Any]) -> None:
    """Enforces Deterministic Clock Invariant:
    Time-based tests using setTimeout > 50ms must support/use an injectable clock (e.g. options.now).
    """
    tests = prob.get("visibleTests", []) + prob.get("hiddenTests", [])
    prompt = prob.get("prompt", "")
    sol = prob.get("solutionCode", "")

    for t in tests:
        code = t.get("testCode", "")
        for match in SET_TIMEOUT_PATTERN.finditer(code):
            delay = int(match.group(1))
            if delay > 50:
                # Strip Date.now to prevent false positives
                clean_text = re.sub(r"Date\.now", "", prompt + " " + code + " " + sol)
                has_clock = bool(re.search(r"\b(options\.now|now\s*[:=,]|fakeTime)\b", clean_text, re.IGNORECASE))
                if not has_clock:
                    raise AiContractError(
                        f"[{pid}] Deterministic Clock Invariant violated: test '{t.get('name')}' uses "
                        f"setTimeout with delay {delay}ms (> 50ms) without an injectable clock (options.now). "
                        "Inject a deterministic clock to prevent flaky test execution."
                    )


def generate_mutants_for_problem(prob: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generates synthetic mutants (cheating, constant returns, bypassed logic) for a problem."""
    entry_point = prob.get("entryPoint")
    if not entry_point:
        return []

    mutants = []

    # Mutant 1: Always returns constant true / empty object / CLOSED
    m1 = f"""
function {entry_point}() {{
  return {{
    consume: () => true,
    get: async () => ({{}}),
    execute: async () => 'MUTANT_OK',
    getState: () => 'CLOSED'
  }};
}}
module.exports = {{ {entry_point} }};
"""
    mutants.append({"name": "always_true_or_closed", "code": m1})

    # Mutant 2: Always returns false / throws / OPEN
    m2 = f"""
function {entry_point}() {{
  return {{
    consume: () => false,
    get: async () => {{ throw new Error('MUTANT_FAIL'); }},
    execute: async () => {{ throw new Error('CIRCUIT_BREAKER_OPEN'); }},
    getState: () => 'OPEN'
  }};
}}
module.exports = {{ {entry_point} }};
"""
    mutants.append({"name": "always_false_or_open", "code": m2})

    # Mutant 3: Rate Limiter bypass (always refills to capacity on call)
    if "limiter" in entry_point.lower() or "ratelimit" in entry_point.lower():
        m3 = f"""
function {entry_point}({{ capacity = 10, refillRate = 1, initialTokens, now = Date.now }} = {{}}) {{
  return {{
    consume(cost = 1) {{
      // Mutant cheater: sets tokens = capacity every call
      return cost <= capacity;
    }}
  }};
}}
module.exports = {{ {entry_point} }};
"""
        mutants.append({"name": "bypass_capacity_clamp", "code": m3})

    # Mutant 4: Circuit Breaker that never resets failure count on success
    if "circuit" in entry_point.lower() or "breaker" in entry_point.lower():
        m4 = f"""
function {entry_point}(asyncOperation, options = {{}}) {{
  const failureThreshold = options.failureThreshold !== undefined ? options.failureThreshold : 3;
  const resetTimeoutMs = options.resetTimeoutMs !== undefined ? options.resetTimeoutMs : 50;
  const now = options.now || Date.now;

  let state = 'CLOSED';
  let failureCount = 0;
  let openedAt = 0;

  return {{
    async execute(...args) {{
      const currentTime = now();
      if (state === 'OPEN') {{
        if (currentTime - openedAt >= resetTimeoutMs) {{
          state = 'HALF_OPEN';
        }} else {{
          throw new Error('CIRCUIT_BREAKER_OPEN');
        }}
      }}
      try {{
        const res = await asyncOperation(...args);
        // BUG MUTANT: Omit failureCount = 0 on success in CLOSED!
        if (state === 'HALF_OPEN') {{
          state = 'CLOSED';
        }}
        return res;
      }} catch (err) {{
        failureCount++;
        if (state === 'HALF_OPEN' || failureCount >= failureThreshold) {{
          state = 'OPEN';
          openedAt = now();
        }}
        throw err;
      }}
    }},
    getState() {{
      if (state === 'OPEN' && now() - openedAt >= resetTimeoutMs) return 'HALF_OPEN';
      return state;
    }}
  }};
}}
module.exports = {{ {entry_point} }};
"""
        mutants.append({"name": "no_failure_count_reset_on_success", "code": m4})

    # Mutant 5: Async Cache that ignores inFlight coalescing (the starterCode bug)
    if "cache" in entry_point.lower():
        m5 = f"""
function {entry_point}(fetchFn) {{
  const cache = new Map();
  return {{
    async get(key) {{
      if (cache.has(key)) return cache.get(key);
      // BUG MUTANT: no in-flight promise sharing
      const data = await fetchFn(key);
      cache.set(key, data);
      return data;
    }}
  }};
}}
module.exports = {{ {entry_point} }};
"""
        mutants.append({"name": "no_in_flight_coalescing", "code": m5})

    return mutants


def _extract_trap_mutant(prob: Dict[str, Any]) -> tuple[str, str]:
    """Extract (name, code) from problem.trapMutant (str or {name, code})."""
    raw = prob.get("trapMutant")
    if isinstance(raw, str):
        return (prob.get("commonTrapTag") or "trap_mutant", raw)
    if isinstance(raw, dict):
        return (str(raw.get("name") or prob.get("commonTrapTag") or "trap_mutant"), str(raw.get("code") or ""))
    return ("", "")


def check_mutation_testing(
    pid: str,
    prob: Dict[str, Any],
    *,
    environment: str = "node-vanilla",
    require_trap_mutant: bool = False,
    allow_missing_lint: bool = False,
) -> None:
    """Enforces Mutation Testing Guard (Anti-Green-Illusion Guard):
    Runs mutated / cheating implementations against the problem's test suites.
    - Generic/custom mutants must fail `visibleTests + hiddenTests`.
    - When `require_trap_mutant` is True (coding problems), `hiddenTests` must be non-empty and
      `trapMutant` (a plausible wrong solution embodying `commonTrapTag`) must compile and FAIL `hiddenTests`.
    """
    sol = prob.get("solutionCode")
    visible = prob.get("visibleTests", [])
    hidden = prob.get("hiddenTests", [])

    if not sol or not (visible or hidden):
        return

    if require_trap_mutant and _is_coding_problem(prob):
        if not hidden:
            raise AiContractError(
                f"[{pid}] hiddenTests must be non-empty so trapMutant can be verified against hidden tests."
            )
        tm_name, tm_code = _extract_trap_mutant(prob)
        if not tm_code.strip():
            raise AiContractError(
                f"[{pid}] Missing 'trapMutant': supply a plausible wrong solution embodying "
                f"commonTrapTag '{prob.get('commonTrapTag', '?')}' that fails hiddenTests."
            )
        _check_code_compiles(pid, "trapMutant", tm_code, environment=environment, allow_missing_lint=allow_missing_lint)
        tm_report = run_problem_in_workspace(
            prob, tm_code, environment=environment, run_visible=False, run_hidden=True, timeout_sec=2.0
        )
        if tm_report.get("allPassed"):
            raise AiContractError(
                f"[{pid}] Trap mutant '{tm_name}' passed all hidden tests! Add hiddenTests that catch this trap."
            )

    mutants = generate_mutants_for_problem(prob)
    custom_mutants = prob.get("verify", {}).get("mutants") or prob.get("mutants") or []
    mutants.extend(custom_mutants)

    for m in mutants:
        m_name = m.get("name", "unnamed_mutant")
        m_code = m.get("code", "")
        if not m_code:
            continue

        report = run_problem_in_workspace(prob, m_code, environment=environment, timeout_sec=2.0)
        if report.get("allPassed"):
            raise AiContractError(
                f"[{pid}] Anti-Green-Illusion Guard: Test suite failed Mutation Testing for mutant '{m_name}'. "
                "Mutant code passed all tests! Add stricter assertions or edge-case tests to kill this mutant."
            )


def _validate_rule_override_list(entries: Any, label: str) -> None:
    """Validate a list of {rule, reason} objects with non-empty rule and reason strings."""
    if entries is None:
        return
    if not isinstance(entries, list):
        raise AiContractError(f"{label} must be a list of {{rule, reason}} objects.")
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise AiContractError(f"{label}[{idx}] must be an object with 'rule' and 'reason'.")
        rule = entry.get("rule")
        reason = entry.get("reason")
        if not isinstance(rule, str) or not rule.strip():
            raise AiContractError(f"{label}[{idx}] is missing a non-empty 'rule'.")
        if not isinstance(reason, str) or not reason.strip():
            raise AiContractError(f"{label}[{idx}] for rule '{rule}' must have a non-empty 'reason'.")


def validate_lint_overrides(lint_overrides: Any) -> None:
    """Validates optional drill-level lintOverrides: list of {rule, reason} with non-empty reason."""
    _validate_rule_override_list(lint_overrides, "Drill 'lintOverrides'")


STARTER_LINT_EXPECTED_ALLOWED_TYPES = {"fix-bug", "debugging", "find-bug", "refactor", "refactoring"}
REFACTOR_PROMPT_PATTERN = re.compile(
    r"\b(refactor(?:ing|ed)?|simplify|simplifying|split|complexity|restructure|decompose)\b",
    re.IGNORECASE,
)


def validate_starter_lint_expected(prob: Dict[str, Any]) -> set[str]:
    """Validate per-problem `starterLintExpected: [{rule, reason}]` and return allowed rule names.

    Only fix-bug/refactor problems may declare `starterLintExpected`, and their prompt must
    explicitly state that the code structure must be improved too.
    """
    pid = prob.get("id", "?")
    expected = prob.get("starterLintExpected")
    if expected is None:
        return set()
    _validate_rule_override_list(expected, f"[{pid}] 'starterLintExpected'")
    if not expected:
        return set()

    is_fix_or_refactor = (
        prob.get("codeType") in STARTER_LINT_EXPECTED_ALLOWED_TYPES
        or prob.get("archetype") in STARTER_LINT_EXPECTED_ALLOWED_TYPES
    )
    if not is_fix_or_refactor:
        raise AiContractError(
            f"[{pid}] 'starterLintExpected' is only allowed on fix-bug or refactor problems "
            "(stubs must be lint-clean and must not import unused modules)."
        )

    prompt = prob.get("prompt", "")
    if not isinstance(prompt, str) or not REFACTOR_PROMPT_PATTERN.search(prompt):
        raise AiContractError(
            f"[{pid}] 'starterLintExpected' requires the prompt to state that the structure must be "
            "improved too (mention 'refactor', 'simplify', 'split', or 'complexity')."
        )

    return {entry["rule"].strip() for entry in expected}


def check_problem_examples(
    pid: str,
    prob: Dict[str, Any],
    *,
    environment: str = "node-vanilla",
    require_examples: bool = False,
) -> List[str]:
    """Validate optional/required `examples` & `constraints`, zero-leak against hiddenTests, and reference execution."""
    is_tracing_with_snippet = (
        prob.get("archetype") == "code-tracing" or prob.get("codeType") in ("predict-output", "trace-explain")
    ) and bool(prob.get("codeSnippet"))
    should_require = require_examples and _is_coding_problem(prob) and not is_tracing_with_snippet

    errors = validate_examples_and_constraints_schema(pid, prob, require_examples=should_require)
    if errors:
        return errors

    examples = prob.get("examples")
    if not isinstance(examples, list) or not examples:
        return []

    hidden_sources = [
        (f"hiddenTests[{idx}]", str(ht.get("testCode") or ""))
        for idx, ht in enumerate(prob.get("hiddenTests") or [], 1)
    ]
    leak_errors = check_examples_zero_leak(pid, examples, hidden_sources)
    if leak_errors:
        return leak_errors

    return evaluate_drill_examples(pid, prob, environment=environment)


def validate_ai_code_contract(
    prob: Dict[str, Any],
    *,
    environment: str = "node-vanilla",
    require_trap_mutant: bool = False,
    require_examples: bool = False,
    allow_missing_lint: bool = False,
) -> bool:
    """
    Enforces strict rules for AI-written programming problems (04_CODE, 07_PROBLEM_GEN §4):
    1. verificationLevel must be 'partial' until blind solve
    2. Zero Toy Code Guard: No foo/bar/baz/test1 in prompt, code, or tests
    3. Zero Wall-of-Text Guard: Prompt > 250 chars requires bullets, sections, and backticks
    4. Zero-Leak Hint Guard: Hints and visible test names do not spoil answers, methods, or bug lines
    5. Anti-Spoonfeeding Guard: No defect analysis headers, // BUG: comments, or explicit data structure hints
    6. Starter Contract: starterCode compiles/parses and does not leak solutionCode
    7. Deterministic Clock Invariant: Time-based tests > 50ms must support injectable clock
    8. Dual Pre-Execution Verification: Canonical is 100% Green; Starter fails at least one visible test
    9. Mutation Testing Guard (Anti-Green-Illusion): Test suite must kill trapMutant and synthetic mutants
    """
    pid = prob.get("id", "?")

    # 1. Verification level must be partial (or human-verified)
    level = prob.get("verificationLevel", "partial")
    if level not in ("partial", "human-verified"):
        raise AiContractError(
            f"[{pid}] AI-written problem must have verificationLevel='partial' until blind-solve (found '{level}')."
        )
    prob["verificationLevel"] = level

    # 2. Zero Toy Code Guard
    scan_for_toy_identifiers(prob.get("prompt", ""), "prompt", pid)
    scan_for_toy_identifiers(prob.get("context", ""), "context", pid)
    scan_for_toy_identifiers(prob.get("starterCode", ""), "starterCode", pid)
    scan_for_toy_identifiers(prob.get("solutionCode", ""), "solutionCode", pid)
    scan_for_toy_identifiers(prob.get("codeSnippet", ""), "codeSnippet", pid)
    _, tm_code = _extract_trap_mutant(prob)
    if tm_code:
        scan_for_toy_identifiers(tm_code, "trapMutant", pid)

    for idx, t in enumerate(prob.get("visibleTests", []), 1):
        scan_for_toy_identifiers(t.get("name", ""), f"visibleTests[{idx}].name", pid)
        scan_for_toy_identifiers(t.get("testCode", ""), f"visibleTests[{idx}].testCode", pid)

    for idx, t in enumerate(prob.get("hiddenTests", []), 1):
        scan_for_toy_identifiers(t.get("name", ""), f"hiddenTests[{idx}].name", pid)
        scan_for_toy_identifiers(t.get("testCode", ""), f"hiddenTests[{idx}].testCode", pid)

    # 3. Zero Wall-of-Text Guard
    check_zero_wall_of_text(pid, prob.get("prompt", ""))

    # 4. Zero-Leak Hint Guard
    check_zero_leak_hint(pid, prob)

    # 5. Anti-Spoonfeeding Guard
    check_anti_spoonfeeding(pid, prob)

    # 5b. Choice Prompt Option-Duplication Guard (07 §4)
    choice_dups = find_choice_prompt_option_duplicates(prob)
    if choice_dups:
        raise AiContractError(
            f"[{pid}] Choice prompt must not list or duplicate its options ({'; '.join(choice_dups)}). "
            "Keep options only in answerSpec.options (Studio and Notion render them)."
        )

    # 6. Starter syntax/compile check
    check_starter_contract(
        pid, prob, environment=environment, check_identical=False, allow_missing_lint=allow_missing_lint
    )

    # 7. Deterministic Clock Invariant
    check_deterministic_clock(pid, prob)

    # 8. Dual Pre-Execution Verification (canonical Green; starter fails >= 1 visible test)
    check_dual_pre_execution(pid, prob, environment=environment)

    # 9. Starter no-leak check (cannot be identical to solutionCode)
    check_starter_contract(
        pid, prob, environment=environment, check_identical=True, allow_missing_lint=allow_missing_lint
    )

    # 9. Mutation Testing Guard (Anti-Green-Illusion)
    check_mutation_testing(
        pid,
        prob,
        environment=environment,
        require_trap_mutant=require_trap_mutant,
        allow_missing_lint=allow_missing_lint,
    )

    # 10. Examples & Constraints Gate
    example_errors = check_problem_examples(pid, prob, environment=environment, require_examples=require_examples)
    if example_errors:
        raise AiContractError("; ".join(example_errors))

    return True


# ---------------------------------------------------------------------------
# Code Reasoning Vault Management
# ---------------------------------------------------------------------------
def _code_vault_dir(vault_dir: Optional[str] = None) -> str:
    return vault_dir or os.environ.get("CODE_REASONING_VAULT_DIR") or CODE_VAULT_DIR


def archetype_owner(archetype: Dict[str, Any]) -> str:
    """The unit (or chapter) an archetype belongs to: its `unitCode`, else the vault file it lives in."""
    return archetype.get("unitCode") or archetype.get("_vaultFile", "")


def load_scope_archetypes(code: str, vault_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Archetypes in scope for a drill on `code`, read across every PRG vault file.

    - A unit code (`PRG-T01-C01-U01`) gets only that unit's archetypes, so a unit drill never mixes in another unit.
    - A chapter code (`PRG-T01-C01`) gets the archetypes of every unit in the chapter (chapter mixed drill).
    An archetype belongs to its `unitCode`, or, without one, to the vault file it is stored in. Each returned
    dict carries `_vaultFile` (not saved anywhere) so callers can tell where it lives.
    """
    found: List[Dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(_code_vault_dir(vault_dir), "*.json"))):
        stem = os.path.basename(path)[:-5]
        try:
            with open(path, "r", encoding="utf-8") as f:
                archetypes = json.load(f).get("archetypes", [])
        except (OSError, ValueError):
            continue
        for a in archetypes:
            a = {**a, "_vaultFile": stem}
            owner = archetype_owner(a)
            if owner == code or owner.startswith(code + "-U"):
                found.append(a)
    return found


def get_code_vault_path(unit_code: str, vault_dir: Optional[str] = None) -> str:
    dir_path = _code_vault_dir(vault_dir)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{unit_code}.json")


def load_code_reasoning_vault(unit_code: str, vault_dir: Optional[str] = None) -> Dict[str, Any]:
    path = get_code_vault_path(unit_code, vault_dir=vault_dir)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"unitCode": unit_code, "archetypes": []}


def save_code_reasoning_vault(unit_code: str, vault_data: Dict[str, Any], vault_dir: Optional[str] = None) -> str:
    path = get_code_vault_path(unit_code, vault_dir=vault_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vault_data, f, indent=2, ensure_ascii=False)
    return path


def register_code_archetype(
    unit_code: str, archetype: Dict[str, Any], vault_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Adds or updates an engineering archetype in the unit's Code Reasoning Vault."""
    vault = load_code_reasoning_vault(unit_code, vault_dir=vault_dir)
    archetypes = vault.get("archetypes", [])
    key = archetype.get("archetypeKey")
    if not key:
        raise ValueError("Archetype must have an 'archetypeKey'.")

    idx = next((i for i, a in enumerate(archetypes) if a.get("archetypeKey") == key), -1)
    if idx >= 0:
        existing = archetypes[idx]
        used = existing.get("usedContexts", [])
        archetype["usedContexts"] = list(dict.fromkeys(used + archetype.get("usedContexts", [])))
        archetypes[idx] = archetype
    else:
        if "usedContexts" not in archetype:
            archetype["usedContexts"] = []
        archetypes.append(archetype)

    vault["archetypes"] = archetypes
    save_code_reasoning_vault(unit_code, vault, vault_dir=vault_dir)
    return archetype


def mark_code_context_used(
    unit_code: str, archetype_key: str, context_tag: str, vault_dir: Optional[str] = None
) -> None:
    """Marks a domain context as used so future AI generations rotate to fresh domains.
    Writes to the vault file that holds the archetype (a unit drill may use a chapter vault's archetype)."""
    holder = next(
        (
            a["_vaultFile"]
            for a in load_scope_archetypes(unit_code, vault_dir=vault_dir)
            if a.get("archetypeKey") == archetype_key
        ),
        unit_code,
    )
    vault = load_code_reasoning_vault(holder, vault_dir=vault_dir)
    for a in vault.get("archetypes", []):
        if a.get("archetypeKey") == archetype_key:
            used = a.get("usedContexts", [])
            if context_tag not in used:
                used.append(context_tag)
                a["usedContexts"] = used
            break
    save_code_reasoning_vault(holder, vault, vault_dir=vault_dir)


# ---------------------------------------------------------------------------
# Ingest Pipeline
# ---------------------------------------------------------------------------
def _find_archetype_in_vaults(
    unit_code: str, archetype_key: str, vault_dir: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Look up an archetype by key within the unit or chapter scope."""
    for arch in load_scope_archetypes(unit_code, vault_dir=vault_dir):
        if arch.get("archetypeKey") == archetype_key:
            return arch
    return None


def _archetype_trap_tags(arch: Dict[str, Any]) -> List[str]:
    """Extract cognitive trap tag strings from an archetype."""
    traps = arch.get("cognitiveTraps") or []
    return [t.get("trapTag") if isinstance(t, dict) else str(t) for t in traps if t]


def validate_code_against_vault(
    prob: Dict[str, Any],
    archetypes: List[Dict[str, Any]],
    unit_code: str,
) -> Dict[str, Any]:
    """Scope & trap gate: archetypeKey must be in scope, and commonTrapTag in its cognitiveTraps."""
    pid = prob.get("id", "?")
    key = prob.get("archetypeKey")
    if not key:
        raise AiContractError(f"[{pid}] Problem is missing 'archetypeKey'.")
    arch = next((a for a in archetypes if a.get("archetypeKey") == key), None)
    if arch is None:
        raise AiContractError(f"[{pid}] archetypeKey '{key}' is out of scope for '{unit_code}' reasoning vault.")

    tag = prob.get("commonTrapTag")
    traps = _archetype_trap_tags(arch)
    if not tag or tag not in traps:
        raise AiContractError(
            f"[{pid}] commonTrapTag '{tag}' is not one of archetype '{key}' cognitiveTraps {traps}. "
            "Use a listed tag, or propose adding the trap to the vault first."
        )
    return arch


def validate_problem_quality_checks(
    pid: str,
    arch: Dict[str, Any],
    *,
    universal_ids: set[str],
) -> None:
    """Validate that an archetype has valid `qualityChecks` (R2) and `knownBad` lint snippets fire."""
    arch_key = arch.get("archetypeKey", "?")
    errors = validate_quality_checks(arch, universal_ids=universal_ids)
    if errors:
        raise AiContractError(f"[{pid}] Archetype '{arch_key}' has invalid qualityChecks: {'; '.join(errors)}")

    for check in arch.get("qualityChecks", []):
        ok, msg = verify_known_bad_lint(check, label=arch_key)
        if not ok:
            raise AiContractError(f"[{pid}] {msg}")
        if msg:
            print(f"  [{pid}] {msg}")


def validate_drill_quality_checks(
    unit_code: str, problems: List[Dict[str, Any]], vault_dir: Optional[str] = None
) -> None:
    """
    Ensure every archetype used by the draft has valid `qualityChecks` in the vault,
    and every `lint:<rule>` knownBad snippet triggers its declared ESLint rule.
    """
    universal = load_universal()
    universal_ids = {c["id"] for c in universal if isinstance(c, dict) and isinstance(c.get("id"), str)}
    checked_archetypes: set[str] = set()

    for idx, prob in enumerate(problems, 1):
        pid = prob.get("id", f"Q{idx:02d}")
        arch_key = prob.get("archetypeKey")
        if not arch_key:
            raise AiContractError(f"[{pid}] Problem is missing 'archetypeKey' (required for qualityChecks gate).")
        if arch_key in checked_archetypes:
            continue

        arch = _find_archetype_in_vaults(unit_code, arch_key, vault_dir=vault_dir)
        if arch is None:
            raise AiContractError(
                f"[{pid}] Archetype '{arch_key}' not found in vault for '{unit_code}' (required for qualityChecks gate)."
            )

        validate_problem_quality_checks(pid, arch, universal_ids=universal_ids)
        checked_archetypes.add(arch_key)


def validate_drill_solution_lint(drill_doc: Dict[str, Any], *, allow_missing_lint: bool = False) -> None:
    """Run Layer 2 ESLint (and tsc for TS presets) checks on every problem's solutionCode."""
    if shutil.which("node") is None:
        if _allow_missing_lint(allow_missing_lint):
            print("  [SKIP] solutionCode lint gate: node binary not found on PATH.")
            return
        raise AiContractError(
            "solutionCode lint/tsc gate cannot run: node binary not found on PATH. "
            "Install Node.js and run `cd tools/lint && npm ci`, or opt out with "
            "--allow-missing-lint / LEARNINGOS_ALLOW_MISSING_LINT=1."
        )
    try:
        findings = lint_drill_doc(drill_doc)
        ts_diags = typecheck_drill_doc(drill_doc)
    except LintToolsMissingError as exc:
        if _allow_missing_lint(allow_missing_lint):
            print(f"  [SKIP] solutionCode lint gate: {exc}")
            return
        raise AiContractError(
            f"solutionCode lint/tsc gate cannot run: {exc} "
            "(Run `cd tools/lint && npm ci`, or opt out with --allow-missing-lint / LEARNINGOS_ALLOW_MISSING_LINT=1.)"
        ) from exc

    if findings:
        details = "; ".join(f"[{f['problemId']}] line {f['line']} {f['rule']} {f['message']}" for f in findings)
        raise AiContractError(f"solutionCode failed Layer 2 lint: {details}")
    if ts_diags:
        details = "; ".join(f"[{d['problemId']}] line {d['line']} {d['message']}" for d in ts_diags)
        raise AiContractError(f"solutionCode failed TypeScript typecheck: {details}")


def validate_drill_starter_lint(drill_doc: Dict[str, Any], *, allow_missing_lint: bool = False) -> None:
    """Run Layer 2 ESLint on every problem's starterCode with the drill's config.

    Errors are allowed only when covered by drill-level `lintOverrides` (disabled in ESLint)
    or declared in per-problem `starterLintExpected` on fix-bug/refactor problems whose prompt
    asks for structural improvement.
    """
    expected_by_pid: Dict[str, set[str]] = {}
    for idx, prob in enumerate(drill_doc.get("problems", []), 1):
        pid = prob.get("id", f"Q{idx:02d}")
        expected_by_pid[pid] = validate_starter_lint_expected(prob)

    if shutil.which("node") is None:
        if _allow_missing_lint(allow_missing_lint):
            print("  [SKIP] starterCode lint gate: node binary not found on PATH.")
            return
        raise AiContractError(
            "starterCode lint gate cannot run: node binary not found on PATH. "
            "Install Node.js and run `cd tools/lint && npm ci`, or opt out with "
            "--allow-missing-lint / LEARNINGOS_ALLOW_MISSING_LINT=1."
        )
    try:
        findings = lint_drill_doc(drill_doc, field="starterCode")
    except LintToolsMissingError as exc:
        if _allow_missing_lint(allow_missing_lint):
            print(f"  [SKIP] starterCode lint gate: {exc}")
            return
        raise AiContractError(
            f"starterCode lint gate cannot run: {exc} "
            "(Run `cd tools/lint && npm ci`, or opt out with --allow-missing-lint / LEARNINGOS_ALLOW_MISSING_LINT=1.)"
        ) from exc

    unexpected = [f for f in findings if f["rule"] not in expected_by_pid.get(f["problemId"], set())]
    if unexpected:
        details = "; ".join(f"[{f['problemId']}] line {f['line']} {f['rule']} {f['message']}" for f in unexpected)
        raise AiContractError(f"starterCode failed Layer 2 lint: {details}")


NON_IMPLEMENT_TYPES = {
    "fix-bug",
    "debugging",
    "refactor",
    "refactoring",
    "predict-output",
    "code-tracing",
    "trace-explain",
}


def validate_drill_mix(drill_doc: Dict[str, Any], problems: List[Dict[str, Any]]) -> List[str]:
    """Enforce rules/07 mix invariants:
    - Each problem has a realistic non-empty `context` domain.
    - No two problems share the same (archetypeKey, context).
    - For drills with >= 4 problems:
      - Level spread (at least 2 distinct levels when difficulty is ALL/unset, or matching pinned difficulty).
      - At least one non-implement item (fix-bug / refactor / predict-output / trace-explain).
    """
    errors: List[str] = []
    seen_pairs: Dict[tuple[str, str], str] = {}

    for idx, prob in enumerate(problems, 1):
        pid = prob.get("id", f"Q{idx:02d}")
        arch_key = str(prob.get("archetypeKey") or "")
        ctx = str(prob.get("context") or "").strip()
        if not ctx:
            errors.append(f"[{pid}] Missing 'context': prompts must name a realistic scenario domain.")
            continue
        pair = (arch_key, ctx.lower())
        if pair in seen_pairs:
            errors.append(
                f"[{pid}] Duplicate (archetypeKey='{arch_key}', context='{ctx}') already used in {seen_pairs[pair]}."
            )
        else:
            seen_pairs[pair] = pid

    if len(problems) >= 4:
        cfg = drill_doc.get("config") or {}
        diff = str(cfg.get("difficulty") or "ALL").upper()
        levels = [p.get("level") for p in problems if p.get("level") is not None]
        if diff in ("1", "2", "3", "4", "5"):
            expected_lvl = int(diff)
            for p in problems:
                if p.get("level") != expected_lvl:
                    errors.append(
                        f"[{p.get('id', '?')}] Level {p.get('level')} does not match pinned difficulty L{expected_lvl}."
                    )
        elif len(set(levels)) < 2:
            errors.append(
                f"Drill of {len(problems)} problems needs level spread (found only level(s) {sorted(set(levels))})."
            )

        has_non_implement = any(
            (p.get("codeType") in NON_IMPLEMENT_TYPES) or (p.get("archetype") in NON_IMPLEMENT_TYPES) for p in problems
        )
        if not has_non_implement:
            errors.append(
                f"Drill of {len(problems)} problems needs at least one non-implement item "
                "(fix-bug / refactor / predict-output / trace-explain)."
            )

    return errors


def visible_edge_case_warnings(drill_doc: Dict[str, Any]) -> List[str]:
    """Warn when public tests lack a visibly recognizable boundary input."""
    warnings = []
    edge_pattern = re.compile(
        r"(?:\bnull\b|\bundefined\b|\bempty\b|\bzero\b|\bnegative\b|(?:^|[^\w])0(?:[^\w]|$)|(?:^|[^\w])-\d)",
        re.I,
    )
    for problem in drill_doc.get("problems") or []:
        tests = problem.get("visibleTests") or []
        text = " ".join(f"{test.get('name', '')} {test.get('testCode', '')}" for test in tests)
        if not edge_pattern.search(text):
            warnings.append(
                f"[{problem.get('id', '?')}] Visible tests have no recognizable edge-case input; "
                "add an appropriate empty/zero/null/negative/boundary case."
            )
    return warnings


def validate_drill_review(drill_doc: Dict[str, Any], problems: List[Dict[str, Any]]) -> List[str]:
    """Require reviewer record: `review: {verdict: 'pass', note}` on draft (or on every problem)."""
    rv = drill_doc.get("review")
    if isinstance(rv, dict):
        verdict = rv.get("verdict")
        note = str(rv.get("note") or "").strip()
        if verdict != "pass" or not note:
            return [f"Drill 'review' must have verdict='pass' and a non-empty 'note' (got {rv!r})."]
        return []

    # Fallback: per-problem review
    if all(isinstance(p.get("review"), dict) for p in problems):
        errors: List[str] = []
        for p in problems:
            prv = p["review"]
            if prv.get("verdict") != "pass" or not str(prv.get("note") or "").strip():
                errors.append(f"[{p.get('id', '?')}] Problem 'review' must have verdict='pass' and a non-empty 'note'.")
        return errors

    return ["Missing 'review' {verdict: 'pass', note} from the reviewer subagent."]


def _normalize_whitespace(code: str) -> str:
    return " ".join(code.split())


def validate_drill_blind_solve(
    drill_doc: Dict[str, Any],
    problems: List[Dict[str, Any]],
    *,
    ingested: bool = False,
) -> List[str]:
    """Verify blindSolve: [{problemId, solutionCode, ambiguous, note}] for every problem.

    Runs each blind solver's solutionCode against visibleTests AND hiddenTests using
    code_engine.test_runner, and rejects missing entries, ambiguous flags, test failures,
    or blind solutions that are byte-identical (after whitespace normalisation) to the
    reference solutionCode. When `ingested=True`, accepts `{problemId, passed: True}`
    provenance records produced by `ingest_ai_code_drill`.
    """
    bs = drill_doc.get("blindSolve")
    if not isinstance(bs, list) or not bs:
        return ["Missing 'blindSolve' list [{problemId, solutionCode, ambiguous, note}] from the blind-solve subagent."]

    by_id: Dict[str, Dict[str, Any]] = {}
    for entry in bs:
        if isinstance(entry, dict) and entry.get("problemId"):
            by_id[str(entry["problemId"])] = entry

    env_key = drill_doc.get("environment", "node-vanilla")
    errors: List[str] = []
    for idx, p in enumerate(problems, 1):
        pid = p.get("id", f"Q{idx:02d}")
        rec = by_id.get(pid)
        if rec is None:
            errors.append(f"[{pid}] Missing blindSolve entry for '{pid}'.")
            continue
        if rec.get("ambiguous") is True:
            errors.append(f"[{pid}] blindSolve flagged '{pid}' as ambiguous.")
            continue

        blind_code = rec.get("solutionCode")
        if not isinstance(blind_code, str) or not blind_code.strip():
            if ingested and rec.get("passed") is True:
                continue
            errors.append(f"[{pid}] blindSolve entry for '{pid}' is missing 'solutionCode'.")
            continue

        ref_sol = p.get("solutionCode") or p.get("verify", {}).get("solutionCode") or ""
        if ref_sol and _normalize_whitespace(blind_code) == _normalize_whitespace(ref_sol):
            errors.append(
                f"[{pid}] blindSolve solutionCode for '{pid}' is identical to reference solutionCode "
                "(blind solver must not see the answer)."
            )
            continue

        visible = p.get("visibleTests", [])
        hidden = p.get("hiddenTests", [])
        if _is_coding_problem(p) and (visible or hidden):
            prob_env = p.get("environment", env_key)
            report = run_problem_in_workspace(p, blind_code, environment=prob_env)
            if not report.get("allPassed"):
                failed_vis = [r.get("name", "?") for r in report.get("visibleResults", []) if not r.get("passed")]
                hid_passed = report.get("hiddenPassed", 0)
                hid_total = report.get("hiddenTotal", len(hidden))
                errors.append(
                    f"[{pid}] blindSolve solutionCode failed tests "
                    f"(visible failed: {failed_vis}, hidden: {hid_passed}/{hid_total})."
                )
    return errors


def check_code_drill(
    drill_doc: Dict[str, Any],
    rules: Optional[Dict[str, Any]] = None,
    vault_dir: Optional[str] = None,
    *,
    ingested: bool = False,
    allow_missing_lint: bool = False,
) -> List[str]:
    """Run every PRG ingest gate on a draft WITHOUT writing anything or touching the vault.

    Returns a list of failure strings across all problems (empty list = ready to ingest).
    """
    unit_code = drill_doc.get("unitCode")
    if not unit_code:
        return ["Drill document must specify 'unitCode'."]
    problems = drill_doc.get("problems") or []
    if not problems:
        return ["Drill document has no 'problems'."]

    errors: List[str] = []
    try:
        validate_lint_overrides(drill_doc.get("lintOverrides"))
    except AiContractError as exc:
        errors.append(str(exc))

    scope_archs = load_scope_archetypes(unit_code, vault_dir=vault_dir)
    if not scope_archs:
        errors.append(f"No archetypes found in reasoning vault for scope '{unit_code}'.")

    active_rules = rules or QUALITY_RULES
    env_key = drill_doc.get("environment", "node-vanilla")
    universal = load_universal()
    universal_ids = {c["id"] for c in universal if isinstance(c, dict) and isinstance(c.get("id"), str)}
    checked_rubrics: set[str] = set()

    working_problems: List[Dict[str, Any]] = []
    for idx, original in enumerate(problems, 1):
        prob = copy.deepcopy(original)
        prob.setdefault("id", f"Q{idx:02d}")
        prob.setdefault("verificationLevel", "partial")
        working_problems.append(prob)
        pid = prob["id"]

        # 1. Scope & trap tag + Rubric (qualityChecks)
        if scope_archs:
            try:
                arch = validate_code_against_vault(prob, scope_archs, unit_code)
                arch_key = arch.get("archetypeKey", "")
                if arch_key not in checked_rubrics:
                    validate_problem_quality_checks(pid, arch, universal_ids=universal_ids)
                    checked_rubrics.add(arch_key)
            except AiContractError as exc:
                errors.append(str(exc))

        # 2. Contract, no-leak, starter compile, dual pre-exec, trapMutant + generic mutants, quality gates
        try:
            validate_ai_code_contract(
                prob,
                environment=env_key,
                require_trap_mutant=True,
                require_examples=False,
                allow_missing_lint=allow_missing_lint,
            )
            verify_problem(prob, rules=active_rules, environment=env_key)
        except Exception as exc:  # noqa: BLE001 - collect all per-problem gate errors
            msg = str(exc)
            errors.append(msg if f"[{pid}]" in msg else f"[{pid}] {msg}")

        # 2b. Examples & Constraints Gate (2-3 verified normal examples required for new drills)
        errors.extend(check_problem_examples(pid, prob, environment=env_key, require_examples=True))

    # 3. Layer 2 lint + tsc on solutionCode, and Layer 2 lint on starterCode
    try:
        validate_drill_solution_lint(drill_doc, allow_missing_lint=allow_missing_lint)
    except AiContractError as exc:
        errors.append(str(exc))
    try:
        validate_drill_starter_lint(drill_doc, allow_missing_lint=allow_missing_lint)
    except AiContractError as exc:
        errors.append(str(exc))

    # 4. Mix invariants
    errors.extend(validate_drill_mix(drill_doc, working_problems))

    # 5. Blind solve & Reviewer record
    errors.extend(validate_drill_blind_solve(drill_doc, working_problems, ingested=ingested))
    errors.extend(validate_drill_review(drill_doc, working_problems))

    return errors


def _resolve_unit_title(unit_code: str) -> Optional[str]:
    id_map_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "id_map.json")
    if os.path.exists(id_map_path):
        try:
            with open(id_map_path, "r", encoding="utf-8") as f:
                id_map = json.load(f)
            entry = id_map.get(unit_code)
            if isinstance(entry, dict) and entry.get("title"):
                return str(entry["title"])
        except (OSError, ValueError):
            pass
    return None


def ingest_ai_code_drill(
    drill_doc: Dict[str, Any],
    data_root: Optional[str] = None,
    workspace_root: Optional[str] = None,
    rules: Optional[Dict[str, Any]] = None,
    vault_dir: Optional[str] = None,
    *,
    allow_missing_lint: bool = False,
) -> Dict[str, Any]:
    """
    Validates an AI-written programming drill document against Contract 04_CODE & 07 §4,
    verifies quality gates and test suites, assigns an official Drill ID,
    scaffolds the local IDE workspace directory, and writes verified Drill JSON.
    """
    if data_root is None:
        data_root = os.environ.get("DRILLS_DATA_DIR", "drills/data")

    unit_code = drill_doc.get("unitCode")
    if not unit_code:
        raise ValueError("Drill document must specify 'unitCode'.")

    problems = drill_doc.get("problems", [])
    if not problems:
        raise ValueError("Drill document has no 'problems'.")

    active_rules = rules or QUALITY_RULES

    # 1. Run all ingest gates
    gate_errors = check_code_drill(
        drill_doc, rules=active_rules, vault_dir=vault_dir, allow_missing_lint=allow_missing_lint
    )
    if gate_errors:
        raise AiContractError("\n".join(gate_errors))

    for idx, prob in enumerate(problems, 1):
        if "id" not in prob:
            prob["id"] = f"Q{idx:02d}"
        if "verificationLevel" not in prob:
            prob["verificationLevel"] = "partial"
        verify_problem(prob, rules=active_rules, environment=drill_doc.get("environment", "node-vanilla"))

    # 2. Allocate or preserve official Drill ID
    drill_id = drill_doc.get("drillId")
    if not drill_id:
        drill_id = next_drill_id(unit_code, data_root=data_root)
        drill_doc["drillId"] = drill_id

    # 3. Populate metadata
    # Hierarchy + level labels that notion_sync.drill_sync needs (the template path sets them too).
    topic_code, chapter_code = unit_hierarchy(unit_code)
    if not drill_doc.get("topicCode"):
        drill_doc["topicCode"] = topic_code
    if not drill_doc.get("chapterCode"):
        drill_doc["chapterCode"] = chapter_code
    if not drill_doc.get("unitTitle"):
        drill_doc["unitTitle"] = _resolve_unit_title(unit_code) or drill_doc.get("topicTitle") or unit_code

    scope_archs = {a["archetypeKey"]: a for a in load_scope_archetypes(unit_code, vault_dir=vault_dir)}
    for prob in problems:
        if not prob.get("levelLabel") and prob.get("level") in LEVEL_LABELS:
            prob["levelLabel"] = LEVEL_LABELS[prob["level"]]
        arch = scope_archs.get(prob.get("archetypeKey", ""))
        if arch and "-U" in archetype_owner(arch):
            prob.setdefault("unitCode", archetype_owner(arch))

    drill_doc["schemaVersion"] = drill_doc.get("schemaVersion", "2.0-code")
    drill_doc["subject"] = drill_doc.get("subject", "PRG")
    drill_doc["environment"] = drill_doc.get("environment", "node-vanilla")
    drill_doc["createdAt"] = drill_doc.get("createdAt", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if "sourceAttribution" in drill_doc:
        drill_doc["sourceAttribution"] = drill_doc["sourceAttribution"]

    drill_doc["config"] = drill_doc.get(
        "config",
        {
            "questionCount": len(problems),
            "difficulty": "ALL",
            "difficultyMode": "AI Synthesized Engineering Mode",
        },
    )

    # Learner progress (state / sessionSummary) lives in progress/, not in the drill file.
    strip_progress(drill_doc)

    # Do not store blind solutions in the ingested drill file; keep only provenance.
    drill_doc["blindSolve"] = [
        {"problemId": p.get("id", f"Q{idx:02d}"), "passed": True} for idx, p in enumerate(problems, 1)
    ]

    # 4. Scaffold Local Workspace Directory (drills/workspace/<drillId>)
    ws_root = workspace_root or "."
    materialize_drill_workspace(drill_doc, root_dir=ws_root)

    # 5. Save Drill JSON to drills/data/<unit_code>/<drill_id>.json
    unit_dir = os.path.join(data_root, unit_code)
    os.makedirs(unit_dir, exist_ok=True)
    file_path = os.path.join(unit_dir, f"{drill_id}.json")
    drill_doc["localFilePath"] = file_path

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(drill_doc, f, ensure_ascii=False, indent=2)

    # 6. Rotate and update usedContexts in Code Reasoning Vault
    for prob in problems:
        arch_key = prob.get("archetypeKey")
        ctx = prob.get("context")
        if arch_key and ctx:
            mark_code_context_used(unit_code, arch_key, ctx, vault_dir=vault_dir)

    print(f"  [AI Code Verified & Materialized] {file_path} ({len(problems)} problems)")
    print("  Next steps:")
    print(f"    1. Sync pristine record to Notion (rules/00 §8): python -m notion_sync.drill_sync {file_path}")
    print(
        f"    2. Commit only {file_path}, its unit/chapter vault, and id_map.json on a branch "
        f"(drill/{drill_id}), open PR, and self-merge after CI (CLAUDE.md)."
    )
    return drill_doc


def _resolve_ingested_drill_path(target: str, data_root: Optional[str] = None) -> str:
    """Resolve a drill JSON path or DRILL_ID (e.g. DRL-PRG-T00-C02-U01-01) under data_root."""
    if os.path.isfile(target):
        return target
    root = Path(data_root or os.environ.get("DRILLS_DATA_DIR", "drills/data"))
    drill_id = target[:-5] if target.endswith(".json") else target
    matches = sorted(root.glob(f"*/{drill_id}.json"))
    if not matches:
        matches = sorted(root.glob(f"**/{drill_id}.json"))
    if not matches:
        raise FileNotFoundError(f"Ingested drill '{target}' not found under {root}")
    return str(matches[0])


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest AI-generated code drill or inspect Reasoning Vault.")
    parser.add_argument("--unit", default="PRG-T01-C04", help="Unit code (e.g. PRG-T01-C04)")
    parser.add_argument("--list-vault", action="store_true", help="List registered engineering archetypes")
    parser.add_argument("--ingest-file", help="Path to JSON file containing AI-generated code drill document")
    parser.add_argument(
        "--check",
        nargs="?",
        const="__USE_INGEST_FILE__",
        default=None,
        help="Run all gates without writing or touching the vault. Pass a draft path or combine with --ingest-file / --ingested.",
    )
    parser.add_argument(
        "--ingested",
        nargs="?",
        const=True,
        default=False,
        help="Re-run gates on an already-ingested drill (accepts stripped blindSolve provenance). Pass a DRILL_ID/path or combine with --check <path>.",
    )
    parser.add_argument(
        "--allow-missing-lint",
        action="store_true",
        help="Allow skipping ESLint/tsc gates if tools/lint/node_modules or node is missing (or set LEARNINGOS_ALLOW_MISSING_LINT=1).",
    )
    args = parser.parse_args(argv)

    if args.list_vault:
        archs = load_scope_archetypes(args.unit)
        print(f"\nCode Reasoning Vault for {args.unit}: {len(archs)} archetypes")
        for a in archs:
            print(f"  [{a.get('level', 1)}] {a.get('archetypeKey')} ({archetype_owner(a)}): {a.get('name')}")
            print(f"      Invariant: {a.get('governingInvariant')}")
            print(f"      Used Contexts: {a.get('usedContexts', [])}")
            checks = a.get("qualityChecks") or []
            checks_str = ", ".join(f"{c.get('id')} ({c.get('severity')})" for c in checks) if checks else "none"
            print(f"      Quality Checks: {checks_str}")

    ingested_mode = bool(args.ingested)
    check_target: Optional[str] = None
    if args.check is not None:
        if args.check != "__USE_INGEST_FILE__":
            check_target = args.check
        elif isinstance(args.ingested, str):
            check_target = args.ingested
        else:
            check_target = args.ingest_file
        if not check_target:
            parser.error("--check requires a draft JSON path, --ingest-file <path>, or --ingested <DRILL_ID>")
    elif ingested_mode:
        check_target = args.ingested if isinstance(args.ingested, str) else args.ingest_file
        if not check_target:
            parser.error("--ingested requires a DRILL_ID/path (or combine with --check <path>)")

    if check_target:
        try:
            resolved_target = _resolve_ingested_drill_path(check_target) if ingested_mode else check_target
        except FileNotFoundError as exc:
            print(f"  FAIL {exc}", file=sys.stderr)
            return 1
        with open(resolved_target, "r", encoding="utf-8") as f:
            drill_data = json.load(f)
        failures = check_code_drill(
            drill_data,
            ingested=ingested_mode,
            allow_missing_lint=args.allow_missing_lint,
        )
        for warning in visible_edge_case_warnings(drill_data):
            print(f"  WARN {warning}")
        for line in failures:
            print(f"  FAIL {line}")
        n = len(drill_data.get("problems") or [])
        print(
            f"\n{len(failures)} error(s) across {n} problem(s)."
            if failures
            else f"OK: all {n} problems pass every gate (nothing saved)."
        )
        return 1 if failures else 0

    if args.ingest_file:
        with open(args.ingest_file, "r", encoding="utf-8") as f:
            drill_data = json.load(f)
        saved = ingest_ai_code_drill(drill_data, allow_missing_lint=args.allow_missing_lint)
        print(f"Successfully verified and ingested code drill: {saved.get('drillId')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
