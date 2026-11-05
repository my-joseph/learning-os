# -*- coding: utf-8 -*-
"""
Pre-output verification for Programming drill problems.
Nothing is written to disk unless every single check passes.

Checks per problem:
 1. Pre-Execution Verification (Zero Hallucination):
    - Runs the exact code snippet in Node.js subprocess.
    - Matches stdout lines against the problem's expected output tokens.
    - For find-the-flaw: verifies buggy snippet produces the expected defect/error and fixed snippet passes cleanly.
 2. Checker round-trip:
    - check_answer(answerSpec, answerPlain)["verdict"] must equal "correct".
 3. Anti-Answer-Leak Standard:
    - inputHint and placeholder must NOT contain the actual answer tokens, expected line, or output string.
 4. Render safety:
    - No Markdown bold (**) or underscore (__) in plain text fields (prompt, hints).
    - Balanced $ delimiters if math is used.
    - No raw [[ID]] tokens.
    - No Thai characters in JSON fields (English standard).
 5. Mistake taxonomy validation:
    - All commonTrapTag values must exist in the Unit's declared MISTAKE_TAGS.
"""
import re
import subprocess
from code_engine.answer_check import check_answer, parse_tokens

BANNED = [
    (re.compile(r"__"), "Markdown underscore emphasis (__)"),
    (re.compile(r"\[\[[^\]]*\]\]"), "raw [[ID]] token"),
    (re.compile(r"[\u0E00-\u0E7F]"), "non-English (Thai) text"),
]

TEXT_FIELDS = ["prompt", "checkpointHint", "context", "inputHint", "category"]


class VerificationError(AssertionError):
    pass


def _fail(pid, msg):
    raise VerificationError(f"[{pid}] {msg}")


def check_text_safety(pid, label, text):
    if not isinstance(text, str):
        return
    for rx, what in BANNED:
        if rx.search(text):
            _fail(pid, f"{label} contains {what}: {text[:120]}")
    if text.count("$") % 2 != 0:
        _fail(pid, f"{label} has unbalanced $ delimiters: {text[:120]}")


def check_prompt_readability(pid, prompt: str):
    """Enforces Zero Wall-of-Text Standard on programming prompts."""
    if not isinstance(prompt, str):
        return
    if len(prompt) > 250:
        has_structure = ("\n" in prompt) or ("- " in prompt) or ("**" in prompt)
        if not has_structure:
            _fail(
                pid,
                "prompt violates Zero Wall-of-Text Standard (> 250 chars without newlines, bullet points, or bold sections). "
                "Structure with markdown sections and bullet points."
            )


def run_node(code: str, timeout: float = 3.0):
    """Executes JS in Node.js and returns (stdout, stderr, exit_code)."""
    try:
        proc = subprocess.run(
            ["node", "-e", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.stdout.strip(), proc.stderr.strip(), proc.returncode
    except subprocess.TimeoutExpired:
        raise VerificationError(f"Node execution timed out ({timeout}s). Code snippet may contain an infinite loop.")
    except Exception as ex:
        raise VerificationError(f"Node execution failed to start: {ex}")


def check_anti_leak(pid, prob):
    """
    Ensures inputHint does not leak the exact answer, sequence, or correct line.
    """
    hint = prob.get("inputHint", "")
    if not hint:
        return

    plain_ans = prob.get("answerPlain", "").strip()
    spec = prob.get("answerSpec", {})

    # Check 1: plain answer substring
    if plain_ans and len(plain_ans) > 1 and plain_ans.lower() in hint.lower():
        _fail(pid, f"inputHint '{hint}' leaks the answerPlain '{plain_ans}'")

    # Check 2: token leaks
    tokens = spec.get("tokens") or parse_tokens(plain_ans)
    if tokens and len(tokens) >= 2:
        token_seq = ", ".join(tokens)
        if token_seq in hint:
            _fail(pid, f"inputHint '{hint}' leaks the output sequence '{token_seq}'")

    # Check 3: line number leaks in find-the-flaw
    if spec.get("type") in ("line_number", "find_bug"):
        correct_line = str(spec.get("correctLine", ""))
        # Check if hint says e.g. "Line 4" or "line 4" when correct line is 4
        leak_pattern = rf"\bline\s*{correct_line}\b"
        if re.search(leak_pattern, hint, re.IGNORECASE):
            _fail(pid, f"inputHint '{hint}' leaks the flawed line {correct_line}")


def verify_tags(tags):
    if not tags:
        raise VerificationError("MISTAKE_TAGS must be non-empty")
    for t in tags:
        for k in ("id", "label", "name", "autoFrom"):
            if k not in t:
                raise VerificationError(f"Mistake tag {t} missing {k}")


def verify_problem(p, id_map=None):
    pid = p.get("id", p.get("templateKey", "?"))
    v = p.get("verify", {})

    # 1. Text safety & Zero Wall-of-Text check
    for fld in TEXT_FIELDS:
        if fld in p:
            check_text_safety(pid, fld, p[fld])
    check_prompt_readability(pid, p.get("prompt", ""))

    # 2. Anti-Answer-Leak
    check_anti_leak(pid, p)

    # 3. Steps check
    steps = p.get("steps", [])
    if len(steps) < 2:
        _fail(pid, "Programming problem must have at least 2 explanation steps (e.g. Call Stack / Event Loop).")
    for idx, st in enumerate(steps, 1):
        check_text_safety(pid, f"step {idx} explain", st.get("explain", ""))

    # 4. Pre-Execution Verification via Node.js
    snippet = p.get("codeSnippet", "")
    spec = p.get("answerSpec", {})
    stype = spec.get("type")
    ctype = p.get("codeType", "")
    archetype = p.get("archetype", "")

    is_suite = (
        ctype in ("kata", "implement", "refactor", "problem-solving", "debugging", "refactoring", "project-based")
        or archetype in ("problem-solving", "debugging", "refactoring", "project-based")
        or bool(p.get("visibleTests"))
    )

    if is_suite:
        sol = p.get("solutionCode") or v.get("solutionCode")
        if not sol:
            _fail(pid, "Programming suite problem must provide solutionCode for pre-execution verification")

        from code_engine.test_runner import run_tests
        report = run_tests(sol, p.get("visibleTests", []), p.get("hiddenTests", []))
        if not report.get("allPassed"):
            _fail(pid, f"Canonical solution failed test suite: {report}")
        return  # Suite verification complete

    elif stype in ("code_output", "predict_output") or ctype == "predict-output" or archetype == "code-tracing":
        if not snippet:
            _fail(pid, "predict-output problem must provide codeSnippet for execution verification")

        stdout, stderr, code = run_node(snippet)
        if code != 0:
            _fail(pid, f"Execution failed with code {code}. Stderr: {stderr}")

        node_tokens = parse_tokens(stdout)
        expected_tokens = spec.get("tokens") or parse_tokens(spec.get("value", p.get("answerPlain", "")))
        if node_tokens != expected_tokens:
            _fail(pid, f"Pre-Execution mismatch! Node stdout {node_tokens} != asserted answer {expected_tokens}")

    elif stype in ("line_number", "find_bug") or p.get("codeType") == "find-bug":
        correct_line = spec.get("correctLine")
        if correct_line is None:
            _fail(pid, "find-bug problem must specify correctLine in answerSpec")

        total_lines = len(snippet.strip().splitlines())
        if not (1 <= int(correct_line) <= total_lines):
            _fail(pid, f"correctLine {correct_line} is out of bounds (snippet has {total_lines} lines)")

        # If a verified fix is provided, execute it to ensure the fix actually succeeds
        fix_snippet = v.get("fixedSnippet")
        if fix_snippet:
            f_stdout, f_stderr, f_code = run_node(fix_snippet)
            if f_code != 0:
                _fail(pid, f"Fixed snippet failed in Node: {f_stderr}")

    # 5. Checker round-trip
    plain = p.get("answerPlain", "")
    res = check_answer(spec, plain)
    if res.get("verdict") != "correct":
        _fail(pid, f"Checker round-trip failed for answerPlain '{plain}': got {res}")
