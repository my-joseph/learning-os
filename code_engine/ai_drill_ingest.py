# -*- coding: utf-8 -*-
"""
AI Code Drill Ingestion & Reasoning Vault Engine:
Bridges dynamic AI-generated programming problems into:
1. The Code Reasoning Vault (code_engine/reasoning_vault/<unit_code>.json)
2. Machine-Verified local Drill JSON files (drills/data/<unit_code>/DRL-....json)
3. 100% Local IDE Scaffolding (drills/workspace/<drill_id>/) with package.json, npm test, and folder deep links.
"""

import argparse
import datetime
import json
import os
import re
from typing import Any, Dict, List, Optional

from code_engine.answer_check import parse_tokens
from code_engine.fmt import LEVEL_LABELS, unit_hierarchy
from code_engine.generate import next_drill_id
from code_engine.test_runner import run_tests
from code_engine.verify import run_node, verify_problem
from code_engine.workspace import materialize_drill_workspace
from quality_rules import QUALITY_RULES

CODE_VAULT_DIR = os.path.join(os.path.dirname(__file__), "reasoning_vault")


class AiContractError(Exception):
    """Raised when an AI-generated programming problem violates Contract 04_CODE or 07 §4."""

    pass


# ---------------------------------------------------------------------------
# Zero Toy Code Pattern
# ---------------------------------------------------------------------------
TOY_IDENTIFIER_PATTERN = re.compile(
    r"\b(foo|baz|qux|foobar|test1|test2|test3|funcA|funcB|func1|func2|"
    r"myFunc|myVar|someVar|someFunc|doSomething|temp1|temp2|dummy|dummyFunc|dummyVar)\b|"
    r"(?<!progress[-_ ])(?<!status[-_ ])(?<!scroll[-_ ])(?<!app[-_ ])(?<!nav[-_ ])(?<!tool[-_ ])\bbar\b",
    re.IGNORECASE,
)


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
    """Ensures inputHint and placeholder do not spoil the answer, tokens, or bug locations (04_CODE §7)."""
    hints = []
    for k in ("inputHint", "placeholder"):
        v = prob.get(k)
        if v and isinstance(v, str):
            hints.append((k, v))
    spec = prob.get("answerSpec") or {}
    for k in ("inputHint", "placeholder"):
        v = spec.get(k)
        if v and isinstance(v, str):
            hints.append((f"answerSpec.{k}", v))

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


def check_dual_pre_execution(pid: str, prob: Dict[str, Any]) -> None:
    """Enforces dual pre-execution verification: Canonical is 100% Green, Starter fails reproducer (Red before Green)."""
    archetype = prob.get("archetype") or prob.get("codeType", "problem-solving")
    sol = prob.get("solutionCode") or prob.get("verify", {}).get("solutionCode")
    starter = prob.get("starterCode")
    visible = prob.get("visibleTests", [])
    hidden = prob.get("hiddenTests", [])

    # 1. Canonical solution verification (100% Green)
    if sol and (visible or hidden):
        report = run_tests(sol, visible, hidden)
        if not report.get("allPassed"):
            failed = [r["name"] for r in report.get("visibleResults", []) if not r.get("passed")]
            raise AiContractError(
                f"[{pid}] Dual Pre-Execution Verification: Canonical solution failed test suite: {failed}. "
                f"Details: {report.get('visibleResults')}"
            )

    # 2. Starter code verification for Debugging (Red before Green)
    if archetype in ("debugging", "find-bug"):
        if starter and visible:
            starter_report = run_tests(starter, visible, [])
            if starter_report.get("allPassed"):
                raise AiContractError(
                    f"[{pid}] Dual Pre-Execution Verification: Debugging starterCode unexpectedly passed all visible tests. "
                    "Red-before-Green invariant violated: starterCode must fail at least one reproducer test (04_CODE §2.1)."
                )

    # 3. Code Tracing / Predict Output
    if archetype in ("code-tracing", "predict-output"):
        snippet = prob.get("codeSnippet")
        if not snippet:
            raise AiContractError(f"[{pid}] Code-tracing problem must provide codeSnippet.")
        stdout, stderr, code = run_node(snippet)
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


def check_mutation_testing(pid: str, prob: Dict[str, Any]) -> None:
    """Enforces Mutation Testing Guard (Anti-Green-Illusion Guard):
    Runs mutated / cheating implementations against the problem's test suites.
    The test suite MUST fail on every mutant. If any mutant passes, tests are too weak.
    """
    sol = prob.get("solutionCode")
    visible = prob.get("visibleTests", [])
    hidden = prob.get("hiddenTests", [])

    if not sol or not (visible or hidden):
        return

    mutants = generate_mutants_for_problem(prob)
    custom_mutants = prob.get("verify", {}).get("mutants") or prob.get("mutants") or []
    mutants.extend(custom_mutants)

    for m in mutants:
        m_name = m.get("name", "unnamed_mutant")
        m_code = m.get("code", "")
        if not m_code:
            continue

        report = run_tests(m_code, visible, hidden, timeout_sec=2.0)
        if report.get("allPassed"):
            raise AiContractError(
                f"[{pid}] Anti-Green-Illusion Guard: Test suite failed Mutation Testing for mutant '{m_name}'. "
                "Mutant code passed all tests! Add stricter assertions or edge-case tests to kill this mutant."
            )


def validate_ai_code_contract(prob: Dict[str, Any]) -> bool:
    """
    Enforces strict rules for AI-written programming problems (04_CODE, 07_PROBLEM_GEN §4):
    1. verificationLevel must be 'partial' until blind solve
    2. Zero Toy Code Guard: No foo/bar/baz/test1 in prompt, code, or tests
    3. Zero Wall-of-Text Guard: Prompt > 250 chars requires bullets, sections, and backticks
    4. Zero-Leak Hint Guard: Hints do not spoil answers, methods, or bug lines
    5. Anti-Spoonfeeding Guard: No defect analysis headers, // BUG: comments, or explicit data structure hints
    6. Deterministic Clock Invariant: Time-based tests > 50ms must support injectable clock
    7. Dual Pre-Execution Verification: Canonical is 100% Green; Debugging starterCode is Red
    8. Mutation Testing Guard (Anti-Green-Illusion): Test suite must kill all synthetic mutants
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
    scan_for_toy_identifiers(prob.get("starterCode", ""), "starterCode", pid)
    scan_for_toy_identifiers(prob.get("solutionCode", ""), "solutionCode", pid)
    scan_for_toy_identifiers(prob.get("codeSnippet", ""), "codeSnippet", pid)

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

    # 6. Deterministic Clock Invariant
    check_deterministic_clock(pid, prob)

    # 7. Dual Pre-Execution Verification
    check_dual_pre_execution(pid, prob)

    # 8. Mutation Testing Guard (Anti-Green-Illusion)
    check_mutation_testing(pid, prob)

    return True


# ---------------------------------------------------------------------------
# Code Reasoning Vault Management
# ---------------------------------------------------------------------------
def get_code_vault_path(unit_code: str, vault_dir: Optional[str] = None) -> str:
    dir_path = vault_dir or os.environ.get("CODE_REASONING_VAULT_DIR") or CODE_VAULT_DIR
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
    """Marks a domain context as used so future AI generations rotate to fresh domains."""
    vault = load_code_reasoning_vault(unit_code, vault_dir=vault_dir)
    for a in vault.get("archetypes", []):
        if a.get("archetypeKey") == archetype_key:
            used = a.get("usedContexts", [])
            if context_tag not in used:
                used.append(context_tag)
                a["usedContexts"] = used
            break
    save_code_reasoning_vault(unit_code, vault, vault_dir=vault_dir)


# ---------------------------------------------------------------------------
# Ingest Pipeline
# ---------------------------------------------------------------------------
def ingest_ai_code_drill(
    drill_doc: Dict[str, Any],
    data_root: Optional[str] = None,
    workspace_root: Optional[str] = None,
    rules: Optional[Dict[str, Any]] = None,
    vault_dir: Optional[str] = None,
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

    # 1. Verification of all problems
    for idx, prob in enumerate(problems, 1):
        if "id" not in prob:
            prob["id"] = f"Q{idx:02d}"
        if "verificationLevel" not in prob:
            prob["verificationLevel"] = "partial"

        # Contract Guard validation
        validate_ai_code_contract(prob)

        # Quality Gates (G1, G2, G4, G6) + Node execution verification
        verify_problem(prob, rules=active_rules)

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
    for prob in problems:
        if not prob.get("levelLabel") and prob.get("level") in LEVEL_LABELS:
            prob["levelLabel"] = LEVEL_LABELS[prob["level"]]

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

    if "sessionSummary" not in drill_doc:
        drill_doc["sessionSummary"] = {
            "practiceStatus": "Ready",
            "score": 0,
            "maxScore": len(problems),
            "accuracyPct": 0,
            "mistakeCategories": [],
            "divergedStepsSummary": "",
            "attemptDate": None,
            "syncedToNotionAt": None,
            "notionPageId": None,
        }

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
    return drill_doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest AI-generated code drill or inspect Reasoning Vault.")
    parser.add_argument("--unit", default="PRG-T01-C03", help="Unit code (e.g. PRG-T01-C03)")
    parser.add_argument("--list-vault", action="store_true", help="List registered engineering archetypes")
    parser.add_argument("--ingest-file", help="Path to JSON file containing AI-generated code drill document")
    args = parser.parse_args()

    if args.list_vault:
        v = load_code_reasoning_vault(args.unit)
        print(f"\nCode Reasoning Vault for {args.unit}: {len(v.get('archetypes', []))} archetypes")
        for a in v.get("archetypes", []):
            print(f"  [{a.get('level', 1)}] {a.get('archetypeKey')}: {a.get('name')}")
            print(f"      Invariant: {a.get('governingInvariant')}")
            print(f"      Used Contexts: {a.get('usedContexts', [])}")

    if args.ingest_file:
        with open(args.ingest_file, "r", encoding="utf-8") as f:
            drill_data = json.load(f)
        saved = ingest_ai_code_drill(drill_data)
        print(f"Successfully verified and ingested code drill: {saved.get('drillId')}")
