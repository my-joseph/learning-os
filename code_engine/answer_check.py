# -*- coding: utf-8 -*-
"""
Answer checker for Programming Practice Drills.
Handles:
- predict-output / code_output (token-aware, accepts newline, comma, space, bracketed inputs)
- line_number / find-bug (extracts line numbers like "Line 4", "4", "line 4")
- choice (exact option id match)
- text (normalized accepted string match)
Provides smart diagnostic feedback when known anti-patterns or misorderings are detected.
"""
import json
import re
import sys


def parse_tokens(raw: str) -> list[str]:
    """
    Parses user input string into a list of normalized tokens.
    Handles:
      "1, 4, 3, 2" -> ["1", "4", "3", "2"]
      "1\n4\n3\n2" -> ["1", "4", "3", "2"]
      "[1, 4, 3, 2]" -> ["1", "4", "3", "2"]
      " 'hello', \"world\" " -> ["hello", "world"]
    """
    if not raw:
        return []
    s = raw.strip()
    # Strip enclosing brackets if user wrapped the output like an array
    if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
        s = s[1:-1].strip()

    # Split by newlines, commas, or semicolons
    raw_parts = re.split(r"[\n,;]+", s)
    tokens = []
    for part in raw_parts:
        # Also split by whitespace if part contains multiple space-separated words
        # but keep single quotes/double quotes intact
        subparts = part.strip().split()
        for sub in subparts:
            # Strip outer quotes if any
            cleaned = sub.strip()
            if (cleaned.startswith("'") and cleaned.endswith("'")) or (
                cleaned.startswith('"') and cleaned.endswith('"')
            ):
                cleaned = cleaned[1:-1]
            if cleaned:
                tokens.append(cleaned)
    return tokens


def check_code_output(spec: dict, raw: str) -> dict:
    expected = spec.get("tokens")
    if expected is None:
        raw_val = spec.get("value", "")
        expected = parse_tokens(str(raw_val))
    else:
        expected = [str(t) for t in expected]

    user_tokens = parse_tokens(raw)
    if not user_tokens:
        return {
            "verdict": "parse_error",
            "message": "Type your predicted output (e.g. comma-separated or one per line).",
            "components": [],
            "diagnostics": [],
        }

    comps = []
    for idx, exp in enumerate(expected):
        u = user_tokens[idx] if idx < len(user_tokens) else None
        ok = u == exp
        comps.append({"label": f"Output #{idx + 1}", "ok": ok})

    diags = []
    if user_tokens == expected:
        return {
            "verdict": "correct",
            "message": "Correct output sequence!",
            "components": comps,
            "diagnostics": [],
        }

    # Diagnostics for common mistakes
    trap_tag = spec.get("commonTrapTag")
    if trap_tag == "microtask-order":
        diags.append({
            "code": "microtask-order",
            "message": (
                "Remember: The Call Stack runs first to completion. "
                "Microtasks (Promises, queueMicrotask) run immediately after each stack frame empties, "
                "BEFORE any Macrotask (setTimeout, setInterval) from the Task Queue."
            ),
        })
    elif trap_tag == "var-vs-let-scope":
        diags.append({
            "code": "var-vs-let-scope",
            "message": (
                "Notice the loop variable declaration: 'var' is function-scoped (or global), "
                "so closures share the exact same variable reference after the loop terminates. "
                "'let' creates a new binding for each loop iteration."
            ),
        })
    elif trap_tag == "stale-closure":
        diags.append({
            "code": "stale-closure",
            "message": (
                "Check which scope was captured when the function was created. "
                "A closure retains the variable reference from its outer lexical environment at creation."
            ),
        })

    if len(user_tokens) != len(expected):
        diags.append({
            "code": "token_count_mismatch",
            "message": f"Expected {len(expected)} output values, but received {len(user_tokens)}.",
        })

    is_partial = any(c["ok"] for c in comps)
    verdict = "partial" if is_partial else "incorrect"
    return {
        "verdict": verdict,
        "message": (
            "Some outputs matched, but the sequence or values diverged."
            if is_partial
            else "Output sequence does not match."
        ),
        "components": comps,
        "diagnostics": diags,
    }


def check_line_number(spec: dict, raw: str) -> dict:
    if not (raw or "").strip():
        return {
            "verdict": "parse_error",
            "message": "Enter the line number where the flaw occurs.",
            "components": [],
            "diagnostics": [],
        }

    m = re.search(r"\b(\d+)\b", raw.strip())
    if not m:
        return {
            "verdict": "parse_error",
            "message": "Could not identify a line number in your input. Enter an integer (e.g. 4 or Line 4).",
            "components": [],
            "diagnostics": [],
        }

    user_line = int(m.group(1))
    expected_line = int(spec["correctLine"])
    ok = user_line == expected_line

    diags = []
    if not ok:
        trap = spec.get("commonTrapTag")
        if trap:
            diags.append({"code": trap, "message": spec.get("flawExplanation", f"The bug is located at line {expected_line}.")})

    return {
        "verdict": "correct" if ok else "incorrect",
        "message": f"Line {user_line} is correct!" if ok else f"Line {user_line} is not where the primary defect occurs.",
        "components": [{"label": "Flawed Line", "ok": ok}],
        "diagnostics": diags,
    }


def check_choice(spec: dict, raw: str) -> dict:
    u = raw.strip().upper()
    c = str(spec.get("correct", "")).strip().upper()
    ok = u == c
    return {
        "verdict": "correct" if ok else "incorrect",
        "message": "Correct option selected." if ok else "Incorrect option selected.",
        "components": [{"label": "Choice", "ok": ok}],
        "diagnostics": [] if ok else [{"code": "wrong_choice", "message": "Selected option is not the intended resolution."}],
    }


def check_text(spec: dict, raw: str) -> dict:
    norm = lambda t: re.sub(r"\s+", " ", t.strip().lower())
    accepted = [norm(a) for a in spec.get("accepted", [spec.get("value", "")])]
    ok = norm(raw) in accepted
    return {
        "verdict": "correct" if ok else "incorrect",
        "message": "Correct!" if ok else "Does not match the expected answer.",
        "components": [{"label": "Answer", "ok": ok}],
        "diagnostics": [],
    }


CHECKERS = {
    "code_output": check_code_output,
    "predict_output": check_code_output,
    "line_number": check_line_number,
    "find_bug": check_line_number,
    "choice": check_choice,
    "text": check_text,
}


def check_answer(spec: dict, raw: str) -> dict:
    if not (raw or "").strip():
        return {
            "verdict": "parse_error",
            "message": "Type your answer first.",
            "components": [],
            "diagnostics": [],
        }

    stype = spec.get("type", "code_output")
    fn = CHECKERS.get(stype)
    if not fn:
        # Fallback to check_code_output if tokens or value exist
        if "tokens" in spec or stype in ("text", "string"):
            fn = check_code_output
        else:
            return {
                "verdict": "parse_error",
                "message": f"Unsupported programming answer type: {stype}",
                "components": [],
                "diagnostics": [],
            }

    try:
        return fn(spec, raw)
    except Exception as ex:
        return {
            "verdict": "parse_error",
            "message": f"Error evaluating input: {type(ex).__name__}: {ex}",
            "components": [],
            "diagnostics": [],
        }


if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    res = check_answer(payload.get("answerSpec", {}), payload.get("input", ""))
    print(json.dumps(res))
