# -*- coding: utf-8 -*-
"""
AI Drill Ingestion & Reasoning Vault Engine:
Bridges dynamic AI-generated problems in chat into:
1. The Reasoning Vault (math_engine/reasoning_vault/<unit_code>.json)
2. Verified local Drill JSON files (drills/data/<unit_code>/DRL-....json)
"""

import argparse
import copy
import json
import os
import re
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

import sympy as sp

import ingest_core
from ingest_core import archetype_owner as archetype_owner
from math_engine.answer_check import (
    CHECKERS,
    WHITELIST_CONSTANTS,
    WHITELIST_FUNCS,
    SafeParseError,
    _intervals_equal,
    _split_items,
    check_answer,
    is_equal,
    is_omission_trap,
    parse_interval,
    safe_parse,
    to_expr,
)
from math_engine.answer_spec_registry import validate_answer_spec
from math_engine.bridge import BRIDGE_SCOPE, BRIDGE_TITLE, validate_bridge_problem
from math_engine.bridge import MIN_BRIDGE_UNITS as MIN_BRIDGE_UNITS
from math_engine.drill_ids import next_drill_id
from math_engine.figure_autofill import (
    archetype_requires_figure,
    autofill_problem_figure,
    collect_figure_title_warnings,
    figure_decision_missing,
)
from math_engine.fmt import LEVEL_LABELS, unit_hierarchy
from math_engine.latex_guard import find_bare_words
from math_engine.source_cores import index_dir, resolve_sources_dir
from math_engine.source_cores.originality import check_document_originality, load_located_source_pages
from math_engine.verify import verify_problem
from progress_store import strip_progress as strip_progress
from quality_rules import (
    BLIND_SOLVE_TAGS,
    QUALITY_RULES,
    QualityError,
    check_gate_g3_set,
    demand_level,
    find_choice_prompt_option_duplicates,
)

VAULT_DIR = os.path.join(os.path.dirname(__file__), "reasoning_vault")
DEFAULT_DATA_ROOT = "drills/data"
L2_MIN_REAL_STEPS = 4
L2_STEP_FLOOR_BASELINE_PATH = Path("tests/data/l2_step_floor_baseline.json")

# Match the Studio's unescaped $ delimiters. FormattedText renders each line separately.
_STEP_INLINE_MATH_RE = re.compile(r"(?<!\\)\$(?:\\\$|[^$\r\n])+?(?<!\\)\$")
_STEP_PROSE_LABEL_RE = re.compile(r"\b(?:step|line|case|option|figure|part|example)\s+\d+\b(?![.,]\d)|\b[23]D\b", re.I)
_STEP_BARE_MATH_RE = re.compile(
    r"[\^=≠≤≥±√+<>×÷−≈°⁰¹²³⁴⁵⁶⁷⁸⁹]|\\[A-Za-z]+"
    r"|(?<!\w)-?(?:\d+(?:[.,]\d+)*|\.\d+)[A-Za-z]?(?!\w)"
    r"|\b[A-Za-z]_?\d+\b"
    # An article or pronoun can still be a variable in explicit algebraic context.
    r"|(?i:\b(?:variable|coefficient|parameter|constant)\s+)[aAI]\b"
    r"|(?i:\b(?:solve for|isolate|factor out)\s+)[aAI](?=$|[.,;:!?])"
    r"|\b[aAI]\s*[-*/]\s*[aAI]\b"
    # The other isolated letters are likely symbols. Skip suffixes such as the 't' in "don't".
    r"|\b(?<!\w['’])[B-HJ-Zb-z]\b"
)


class AiContractError(Exception):
    """Raised when an AI-generated problem violates Contract 07 §4 or 00_core §6."""

    pass


def normalize_prompt_numbers(prompt: str, keep_exponents: bool = False) -> List[float]:
    """Extract numbers from a prompt, preserving unary negatives and ignoring LaTeX commands."""
    text = prompt
    # Treat commas as thousands separators only outside coordinate/grouping
    # parentheses. A pair such as (2,3) contains two prompt numbers, not 23.
    grouped: list[str] = []
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char in "([{":
            depth += 1
            grouped.append(char)
            index += 1
            continue
        if char in ")]}":
            depth = max(0, depth - 1)
            grouped.append(char)
            index += 1
            continue
        if depth == 0 and char.isdigit():
            match = re.match(r"\d{1,3}(?:,\d{3})+(?!\d)", text[index:])
            if match:
                grouped.append(match.group(0).replace(",", ""))
                index += len(match.group(0))
                continue
        grouped.append(char)
        index += 1
    text = "".join(grouped)
    if not keep_exponents:
        text = re.sub(r"\^\{?[23]\}?", "", text)
    # Keep comparison operators as unary-sign context for values such as \le-4.
    relation_commands = {"le": "<=", "leq": "<=", "ge": ">=", "geq": ">=", "lt": "<", "gt": ">", "neq": "!="}
    text = re.sub(
        r"\\(leq?|geq?|lt|gt|neq)(?![A-Za-z])",
        lambda match: f" {relation_commands[match.group(1)]} ",
        text,
    )
    # A macro may be immediately followed by its numeric argument (for example, `\le4`).
    # Remove the command while leaving a boundary so the argument is still discovered.
    text = re.sub(r"\\[A-Za-z]+", " ", text)
    # Separate numeric coefficients from variables, units, and LaTeX macros (e.g. 3x -> 3 x, 4\theta -> 4 \theta, 15m -> 15 m)
    text = re.sub(r"(?<=\d)(?=[a-zA-Z\\])", " ", text)
    nums = []
    for match in re.finditer(r"(?<![\w.])(?:\d+\.\d+|\d+|\.\d+)(?!\w|\.\d)", text):
        raw = match.group(0)
        prefix = text[: match.start()]
        sign = re.search(r"[-−]\s*$", prefix)
        if sign:
            before_sign = prefix[: sign.start()].rstrip()
            unary = not before_sign or before_sign[-1] in "=([{,:;+*/^<>!$"
            if re.search(r"\b(?:is|was|were|equals?|equal\s+to|value|given|temperature|debt)\s*$", before_sign):
                # Natural-language context such as "the given is -2" is unary.
                # A variable (`x -2`) and numeric predecessor (`3 -2`) remain subtraction.
                unary = True
            if unary:
                raw = "-" + raw
        try:
            nums.append(float(raw))
        except ValueError:
            pass
    return nums


def heal_latex_string(s: str) -> str:
    """Repairs common escape artifact collisions in LaTeX strings caused by unescaped backslashes."""
    if not isinstance(s, str):
        return s
    # 1. Direct control-char prefix repair for LaTeX macros
    s = s.replace("\f" + "rac", r"\frac")
    s = s.replace("\r" + "ight", r"\right")
    s = s.replace("\b" + "egin", r"\begin")
    s = s.replace("\b" + "ar", r"\bar")
    s = s.replace("\t" + "ext", r"\text")
    s = s.replace("\t" + "imes", r"\times")
    s = s.replace("\t" + "heta", r"\theta")

    # 2. Stray control characters
    s = s.replace("\f", "")
    s = s.replace("\r", "")
    s = s.replace("\b", "")
    s = s.replace("\x0b", "")

    # 3. Textual unescaped macro repair (only if NOT already preceded by backslash)
    s = re.sub(r"(?<!\\)\brac\{", r"\\frac{", s)
    s = re.sub(r"(?<!\\)\bright([)\]}|.])", r"\\right\1", s)
    return s


# ---------------------------------------------------------------------------
# Solution-leak gate (07 §4). A learner sees `prompt` and `display` before
# answering, so neither may contain the computation they are supposed to set up.
# ---------------------------------------------------------------------------

# Re-lists numbers by their algebraic role: "..., with coefficient $5$, constant $15$".
_ROLE_RESTATEMENT_RE = re.compile(
    r"\b(?:with|using)\b[^.?!]*?\b(?:numerical\s+coefficient|coefficient|grouped\s+constant|constant|"
    r"factor|multiplier|target\s+value)s?\s*\$",
    re.IGNORECASE,
)
# Hands over the arithmetic: "using $6 + 8$", "by evaluating $(4 + 16) \div 2$".
_METHOD_PHRASE_RE = re.compile(
    r"\b(?:using|by\s+evaluating|by\s+calculating|by\s+computing|via)\s+\$([^$]+)\$",
    re.IGNORECASE,
)
_CALC_PHRASE_RE = re.compile(r"\b(?:calculate|compute|evaluate|evaluating)\s+\$([^$]+)\$", re.IGNORECASE)
_INLINE_MATH_RE = re.compile(r"\$([^$]+)\$")
_SINGLE_UNKNOWN_RE = re.compile(r"\\?[A-Za-z](?:_\{?[^}=]*\}?)?")


def _normalize_math(expr: str) -> str:
    s = expr
    for macro, repl in ((r"\times", "*"), (r"\cdot", "*"), (r"\div", "/")):
        s = s.replace(macro, repl)
    for macro in (r"\left", r"\right", r"\,", r"\;", r"\quad"):
        s = s.replace(macro, "")
    return re.sub(r"\s+", "", s)


def _is_numeric_computation(expr: str) -> bool:
    """True for things like `2(14) + 2(8)`, `\\frac{80}{16}`, `6 + 8`: digits plus an operator, no letters."""
    # Operators become ASCII operators (not spaces), so `14 \times 9` still reads as a computation.
    s = _normalize_math(expr.replace("?", ""))
    for macro in (r"\frac",):
        s = s.replace(macro, " ")
    if re.search(r"[A-Za-z\\]", s) or not re.search(r"\d", s):
        return False
    s = s.strip()
    # an operator between operands, or implicit multiplication like 2(14) / (a)(b)
    has_frac = r"\frac" in expr
    return (
        has_frac or bool(re.search(r"\d\s*[-+*/^]|[)}]\s*[-+*/^(]|\d\s*\(|[-+*/^]\s*[\d({]", s))
    ) and not re.fullmatch(r"[-+]?\s*\d+(?:\.\d+)?", s)


def _numeric_sides(expr: str) -> List[str]:
    parts = re.split(r"=|\\implies|\\Rightarrow|\\approx", expr)
    return [p.strip() for p in parts if _is_numeric_computation(p)]


def find_solution_leaks(prompt: str, display: str = "") -> List[str]:
    """Returns reasons the problem gives away how to solve it (empty list = clean)."""
    prompt = prompt or ""
    reasons = []
    m = _ROLE_RESTATEMENT_RE.search(prompt)
    if m:
        reasons.append(f"prompt re-lists numbers by their algebraic role ('{m.group(0).strip()}...')")

    maths = _INLINE_MATH_RE.findall(prompt)
    first_math = maths[0] if maths else None
    for expr in maths:
        # "$P = 2(14) + 2(8)$": an unknown set equal to a worked numeric computation.
        sides = [s.strip() for s in expr.split("=")]
        if len(sides) == 2:
            for unknown, other in ((sides[0], sides[1]), (sides[1], sides[0])):
                if _SINGLE_UNKNOWN_RE.fullmatch(unknown) and _is_numeric_computation(other):
                    reasons.append(f"prompt contains the substituted computation '${expr}$'")
                    break
    for expr in _METHOD_PHRASE_RE.findall(prompt):
        if _is_numeric_computation(expr):
            reasons.append(f"prompt hands over the arithmetic ('${expr}$')")
    for m2 in _CALC_PHRASE_RE.finditer(prompt):
        expr = m2.group(1)
        if _is_numeric_computation(expr) and expr != first_math:
            reasons.append(f"prompt spells out the computation to perform ('${expr}$')")

    if display:
        prompt_norm = _normalize_math(" ".join(maths))
        for side in _numeric_sides(display):
            if _normalize_math(side) not in prompt_norm:
                reasons.append(f"display shows the set-up computation '{side}' that the prompt does not give")
                break
    # de-duplicate, keep order
    return list(dict.fromkeys(reasons))


def check_prompt_does_not_leak_solution(pid: str, prompt: str, display: str = "") -> None:
    """Enforced on `prompt` at ingest. `display` is checked only when passed (audit use):
    whether a set-up computation in `display` is acceptable is still a per-level decision."""
    reasons = find_solution_leaks(prompt, display)
    if reasons:
        raise AiContractError(f"[{pid}] Problem gives away the solution: " + "; ".join(reasons))


MIN_FLAW_LINES = 4
_SHOWN_WORK_LINE_RE = re.compile(r"^\s*Line \d+:.*$", re.MULTILINE)


def is_find_the_flaw(prob: Dict[str, Any]) -> bool:
    """Diagnose form (06 §2.3): the prompt shows a worked solution as `Line N: $...$` lines and the
    answer is the first wrong line (`choice`), backed by `verify.flaw`."""
    spec = prob.get("answerSpec") or {}
    return spec.get("type") == "choice" and isinstance((prob.get("verify") or {}).get("flaw"), dict)


def story_text(prob: Dict[str, Any]) -> str:
    """The prompt without the shown-work lines of a find-the-flaw problem. Those lines are the
    stimulus to diagnose, not story data, so they are exempt from the givens and leak gates."""
    prompt = prob.get("prompt", "")
    return _SHOWN_WORK_LINE_RE.sub("", prompt) if is_find_the_flaw(prob) else prompt


def validate_flaw_trap(prob: Dict[str, Any], trap_value: Any) -> None:
    """For find-the-flaw: the shown work must end at the trap value, so the wrong line really is
    the tagged misconception; and the shown-work lines must match the options."""
    pid = prob.get("id", "?")
    spec = prob["answerSpec"]
    flaw = prob["verify"]["flaw"]
    values = flaw.get("values") or []
    shown = _SHOWN_WORK_LINE_RE.findall(prob.get("prompt", ""))
    if not shown or len(shown) != len(values):
        raise AiContractError(
            f"[{pid}] Find-the-flaw prompt must show one 'Line N: $...$' line per verify.flaw value "
            f"({len(shown)} lines, {len(values)} values)."
        )
    if len(shown) < MIN_FLAW_LINES:
        raise AiContractError(
            f"[{pid}] Find-the-flaw work shows {len(shown)} lines; show at least {MIN_FLAW_LINES} so the "
            f"wrong line cannot be guessed and is not the only step (06 §2.3)."
        )
    if {str(o.get("id")) for o in spec.get("options") or []} != {str(i) for i in range(1, len(shown) + 1)}:
        raise AiContractError(f"[{pid}] Find-the-flaw options must be exactly the line numbers 1..{len(shown)}.")
    last = values[-1]
    # Same variable list as verify.py, so shown work with symbols (e.g. FOIL in x) can be checked.
    vars_list = spec.get("variables") or prob.get("variables") or ["x"]
    last_expr = None if last is None else to_expr(str(last), variables=vars_list, trusted=True)
    trap_expr = to_expr(str(trap_value), variables=vars_list, trusted=True)
    if last_expr is None or not is_equal(last_expr, trap_expr, variables=vars_list):
        raise AiContractError(
            f"[{pid}] The shown work must end at the trap value '{trap_value}' (last line value '{last}')."
        )


_is_omission_trap = is_omission_trap  # kept for callers/tests that use the old name


def _trap_matches_spec(spec: Dict[str, Any], tv: Any) -> bool:
    """True when `tv`, put in place of the expected answer, is a well-formed answer of the spec's type
    (so the trap is something a learner could actually enter). Types without a checker pass."""
    spec_type = spec.get("type")
    if spec_type == "choice" and not spec.get("verify", {}).get("flaw"):
        return True
    trap_spec = dict(spec)
    if spec_type in ("number", "expression", "complex", "interval"):
        trap_spec["value"] = str(tv)
    elif spec_type == "vector":
        trap_spec["value"] = tv
        trap_spec.pop("components", None)
        trap_spec.pop("values", None)
    elif spec_type == "solution_set":
        # A realistic trap may contain all true values plus one extra candidate.
        trap_spec["values"] = _split_items(str(tv), spec.get("variable", "x"))
    elif spec_type == "tuple":
        if isinstance(tv, (list, tuple)):
            trap_spec["values"] = list(tv)
        elif isinstance(tv, str):
            parts = [p.strip() for p in re.sub(r"^\s*[\(\[\{<]|[\)\]\}>]\s*$", "", tv).split(",") if p.strip()]
            trap_spec["values"] = parts
        else:
            trap_spec["values"] = [tv]
    fn = CHECKERS.get(spec_type)
    if not fn:
        return True
    try:
        if spec_type == "solution_set":
            # Running the answer against its own parsed set proves it is a valid learner response;
            # the separate contract check ensures it differs from the verified set.
            return fn(trap_spec, str(tv)).get("verdict") == "correct"
        return fn(trap_spec, str(tv)).get("verdict") == "correct"
    except Exception:
        return False


def validate_ai_problem_contract(prob: Dict[str, Any], enforce_leak_gate: bool = True) -> bool:
    """
    Enforces strict rules for AI-written problems (Contract 07 §4, 00_core §6):
    1. Zero-Number rule in checkpointHint
    2. Two-way check: prompt numbers must match givens, and all givens must appear in prompt
    3. trapDerivation must evaluate to trapValue via safe parser (to_expr/is_equal) and reference >= 2 givens
    4. verificationLevel must be 'partial' until blind-solve
    5. Full simulation of check_answer and trap matching across answer types
    """
    pid = prob.get("id", "?")

    # 1. Verification level must be partial (or human-verified)
    level = prob.get("verificationLevel", "partial")
    if level not in ("partial", "human-verified"):
        raise AiContractError(
            f"[{pid}] AI-written problem must have verificationLevel='partial' until blind-solve (found '{level}')."
        )
    prob["verificationLevel"] = level

    # 2. Checkpoint Hint must not contain numbers (00_core §6)
    hint = prob.get("checkpointHint", "")
    if hint:
        nums = re.findall(r"\b\d+\b", hint)
        if nums:
            raise AiContractError(
                f"[{pid}] checkpointHint violates 00_core §6: must contain no numbers, found {nums}: {hint}"
            )

    # 3. Givens two-way completeness check
    givens = prob.get("givens")
    if not givens or not isinstance(givens, dict):
        raise AiContractError(f"[{pid}] Problem must specify a 'givens' dictionary.")

    prompt = story_text(prob)
    prompt_numbers = normalize_prompt_numbers(prompt)

    givens_floats = {}
    for k, v in givens.items():
        try:
            givens_floats[k] = float(v)
        except Exception:
            pass

    # Formula constants (e.g. the 2 in P = 2L + 2W, the 1/2 in A = bh/2) are part of the
    # method, not the story. They live in `constants`, never have to appear in the prompt,
    # and do not count as givens for the trap check. Forcing them into the prompt is what
    # produced self-solving prompts like "using P = 2(14) + 2(8) ... and factor 2".
    constants = prob.get("constants") or {}
    if not isinstance(constants, dict):
        raise AiContractError(f"[{pid}] 'constants' must be a dictionary when present.")
    overlap = set(constants) & set(givens)
    if overlap:
        raise AiContractError(f"[{pid}] Keys {sorted(overlap)} appear in both 'givens' and 'constants'.")
    constant_floats = {}
    for k, v in constants.items():
        try:
            constant_floats[k] = float(v)
        except Exception:
            pass

    if enforce_leak_gate:
        check_prompt_does_not_leak_solution(pid, prompt)

    choice_dups = find_choice_prompt_option_duplicates(prob)
    if choice_dups:
        raise AiContractError(
            f"[{pid}] Choice prompt must not list or duplicate its options ({'; '.join(choice_dups)}). "
            "Keep options only in answerSpec.options (Studio and Notion render them)."
        )

    # Forward: every number in prompt must be defined in givens (or be a declared constant)
    known_vals = list(givens_floats.values()) + list(constant_floats.values())
    for p_num in prompt_numbers:
        if p_num == 0:
            continue  # the 0 in "= 0" or "X > 0" is notation, not story data
        # A sign in the prompt may belong to the notation (x = -4 with given 4), so magnitudes also match.
        if not any(abs(p_num - g_val) < 1e-6 or abs(abs(p_num) - abs(g_val)) < 1e-6 for g_val in known_vals):
            raise AiContractError(f"[{pid}] Number '{p_num}' in prompt is not defined in givens ({givens})")

    # Backward: every given must appear in prompt. Exponents count here ($2^3$ states the 3),
    # otherwise the AI is pushed to re-list them ("with first exponent 3 ...").
    prompt_numbers_all = normalize_prompt_numbers(prompt, keep_exponents=True)
    for g_key, g_val in givens_floats.items():
        if not any(abs(g_val - p_num) < 1e-6 or abs(abs(g_val) - abs(p_num)) < 1e-6 for p_num in prompt_numbers_all):
            raise AiContractError(f"[{pid}] Given '{g_key}={g_val}' does not appear in prompt: '{prompt}'")

    # 4. Trap derivation integrity via Safe Parser (to_expr + is_equal)
    td = prob.get("trapDerivation")
    tv = prob.get("verify", {}).get("trapValue") or prob.get("trapValue")
    if not td or tv is None:
        raise AiContractError(f"[{pid}] Missing trapDerivation or trapValue.")

    if re.fullmatch(r"^\s*[-+]?\d*\.?\d+\s*$", str(td)):
        raise AiContractError(f"[{pid}] trapDerivation '{td}' cannot be a bare number.")

    spec = prob.get("answerSpec") or {}
    if spec and "type" in spec:
        ok_spec, spec_err = validate_answer_spec(spec)
        if not ok_spec:
            raise AiContractError(f"[{pid}] Invalid answerSpec: {spec_err}")
    vars_list = spec.get("variables") or prob.get("variables") or ["x"]
    if spec.get("type") == "interval":
        try:
            td_set = parse_interval(str(td), variables=spec.get("variables"))
            tv_set = parse_interval(str(tv), variables=spec.get("variables"))
        except Exception as ex:
            raise AiContractError(f"[{pid}] Invalid interval in trapDerivation/trapValue: {ex}") from ex
        if not _intervals_equal(td_set, tv_set):
            raise AiContractError(f"[{pid}] trapDerivation '{td}' evaluates to {td_set} != trapValue '{tv}' ({tv_set})")
    elif spec.get("type") == "solution_set":
        variable = spec.get("variable", "x")
        try:
            td_values = [to_expr(v, variables=vars_list, trusted=True) for v in _split_items(str(td), variable)]
            tv_values = [to_expr(v, variables=vars_list, trusted=True) for v in _split_items(str(tv), variable)]
        except Exception as ex:
            raise AiContractError(f"[{pid}] Invalid solution_set trapDerivation/trapValue: {ex}") from ex
        same_set = len(td_values) == len(tv_values) and all(
            any(is_equal(v, candidate, variables=vars_list) for candidate in tv_values) for v in td_values
        )
        if not same_set:
            raise AiContractError(f"[{pid}] trapDerivation '{td}' does not evaluate to solution set '{tv}'.")
    else:
        env_map, _, _, all_vars = _build_givens_env(prob)
        td_norm = _normalize_sympy_candidate(str(td))
        td_expr = _safe_to_expr(td_norm, variables=all_vars, trusted=True)
        if td_expr is not None:
            td_expr = _substitute_env_symbols(td_expr, env_map, vars_list)
        else:
            td_expr = to_expr(str(td), variables=vars_list, trusted=True)
        tv_expr = _safe_to_expr(_normalize_sympy_candidate(str(tv)), variables=vars_list, trusted=True)
        if tv_expr is None:
            tv_expr = to_expr(str(tv), variables=vars_list, trusted=True)
        if not is_equal(td_expr, tv_expr, variables=vars_list):
            raise AiContractError(
                f"[{pid}] trapDerivation '{td}' evaluates to {td_expr} != trapValue '{tv}' ({tv_expr})"
            )

    # Check that at least 2 distinct givens appear in trapDerivation (by numeric value or symbolic key)
    matched_given_keys = _matched_env_keys_in_expr(str(td), prob)

    # An omission trap ("found only the principal angle", "kept only the positive root", "missing union part") is a
    # strict subset of the answer set; it has no arithmetic of its own, so the 2-givens rule does not apply.
    # For single-given interval problems (e.g. sqrt(x - a)), 1 given in trapDerivation is the maximum available.
    min_givens = 1 if (spec.get("type") == "interval" and len(givens_floats) + len(constant_floats) < 2) else 2
    if len(matched_given_keys) < min_givens and not _is_omission_trap(prob.get("answerSpec") or {}, tv):
        raise AiContractError(
            f"[{pid}] trapDerivation '{td}' must contain at least {min_givens} distinct givens from {givens}, found {len(matched_given_keys)}: {matched_given_keys}"
        )

    if enforce_leak_gate:
        validate_distractor_provenance(prob)

    # 5. Check answer simulation and trap matching across answer types
    spec = prob.get("answerSpec", {})
    if spec and "type" in spec:
        chk = check_answer(spec, str(tv))
        if chk.get("verdict") == "correct":
            raise AiContractError(f"[{pid}] trapValue '{tv}' evaluated as correct by check_answer!")

        if is_find_the_flaw(prob):
            validate_flaw_trap(prob, tv)  # the trap is the shown work's result, not an option id
        elif not _trap_matches_spec(spec, tv):
            raise AiContractError(f"[{pid}] trapValue '{tv}' failed trap checker match.")

    # 6. Display LaTeX and plainText integrity for math problems (prevent undefined/unrendered equation bugs)
    display = prob.get("display")
    if not display or not isinstance(display, str) or not display.strip():
        raise AiContractError(f"[{pid}] Math problem must provide a non-empty LaTeX 'display' equation.")

    # plainText is the CAS copy line for typed answers. Choice problems (incl. find-the-flaw)
    # have no expression to paste into a CAS, so the field is dropped instead of restating
    # the prompt (learner decision 2026-11-19).
    if (prob.get("answerSpec") or {}).get("type") == "choice":
        prob.pop("plainText", None)
    else:
        plain_text = prob.get("plainText")
        if not plain_text or not isinstance(plain_text, str) or not plain_text.strip():
            raise AiContractError(f"[{pid}] Math problem must provide a non-empty CAS 'plainText' string.")

    # 7. Prompt must contain LaTeX math delimiters ($...$) for formulas/numbers
    prompt = prob.get("prompt", "")
    if not re.search(r"\$[^$]+\$", prompt):
        raise AiContractError(f"[{pid}] Prompt must contain LaTeX formatting with '$...$' around numbers or variables.")

    # 8. Zero-Corrupted-LaTeX Guard: Validate and heal any control-character escape artifacts (\f -> rac, \r -> ight)
    for field in ("display", "answerDisplay", "prompt"):
        if field in prob and isinstance(prob[field], str):
            prob[field] = heal_latex_string(prob[field])
            if re.search(r"[\x0c\r\x08\x0b]", prob[field]):
                raise AiContractError(
                    f"[{pid}] LaTeX field '{field}' contains invalid control characters: {repr(prob[field])}"
                )
            if re.search(r"(?:^|(?<=[\s({\[]))rac\{", prob[field]) or re.search(
                r"(?:^|(?<=[\s({\[]))ight[)\]}]", prob[field]
            ):
                raise AiContractError(
                    f"[{pid}] LaTeX field '{field}' contains corrupted LaTeX macros: {repr(prob[field])}"
                )

    for s_idx, st in enumerate(prob.get("steps", [])):
        if "latex" in st and isinstance(st["latex"], str):
            st["latex"] = heal_latex_string(st["latex"])
            if re.search(r"[\x0c\r\x08\x0b]", st["latex"]):
                raise AiContractError(
                    f"[{pid}] Step {s_idx + 1} 'latex' contains invalid control characters: {repr(st['latex'])}"
                )
            if re.search(r"(?:^|(?<=[\s({\[]))rac\{", st["latex"]) or re.search(
                r"(?:^|(?<=[\s({\[]))ight[)\]}]", st["latex"]
            ):
                raise AiContractError(
                    f"[{pid}] Step {s_idx + 1} 'latex' contains corrupted LaTeX macros: {repr(st['latex'])}"
                )

    # 9. Granular Step-by-Step Derivation Standard (00_core §7, 03_stem §1, 06 §2.1)
    steps = prob.get("steps", [])
    if not steps or not isinstance(steps, list):
        raise AiContractError(f"[{pid}] Math problem must provide a non-empty 'steps' array.")

    for s_idx, st in enumerate(steps):
        if not isinstance(st, dict):
            raise AiContractError(f"[{pid}] Step {s_idx + 1} must be an object with 'latex' and 'explain'.")
        latex_str = st.get("latex", "")
        explain_str = st.get("explain", "")
        if not latex_str or not latex_str.strip():
            raise AiContractError(f"[{pid}] Step {s_idx + 1} must have a non-empty 'latex' equation.")
        if not explain_str or not explain_str.strip():
            raise AiContractError(f"[{pid}] Step {s_idx + 1} must have an action-oriented 'explain' string.")
        # Anti-Clumping check: 1 discrete transformation per step across all levels L1-L5 (rules/00_core.md §7, 03_stem.md §1)
        if "\\begin" not in latex_str and latex_str.count("=") > 1:
            raise AiContractError(
                f"[{pid}] Step {s_idx + 1} violates 00_core §7 / 03_stem §1: horizontal equality chaining is forbidden ('{latex_str}'). Each step must isolate a single discrete algebraic transformation."
            )
        bare_step = find_bare_words(latex_str)
        if bare_step:
            raise AiContractError(
                f"[{pid}] Step {s_idx + 1} 'latex' contains bare English words {bare_step}; wrap prose in \\text{{...}}: {repr(latex_str)}"
            )

    for field in ("display", "answerDisplay"):
        val = prob.get(field)
        if isinstance(val, str) and val.strip():
            bare = find_bare_words(val)
            if bare:
                raise AiContractError(
                    f"[{pid}] LaTeX field '{field}' contains bare English words {bare}; wrap prose in \\text{{...}}: {repr(val)}"
                )

    spec_obj = prob.get("answerSpec") or {}
    if isinstance(spec_obj, dict):
        if isinstance(spec_obj.get("display"), str) and spec_obj["display"].strip():
            bare = find_bare_words(spec_obj["display"])
            if bare:
                raise AiContractError(
                    f"[{pid}] LaTeX field 'answerSpec.display' contains bare English words {bare}; wrap prose in \\text{{...}}: {repr(spec_obj['display'])}"
                )
        for o_idx, opt in enumerate(spec_obj.get("options") or [], 1):
            if not isinstance(opt, dict):
                continue
            for key in ("latex", "display"):
                oval = opt.get(key)
                if isinstance(oval, str) and oval.strip():
                    bare = find_bare_words(oval)
                    if bare:
                        raise AiContractError(
                            f"[{pid}] Option {o_idx} '{key}' contains bare English words {bare}; wrap prose in \\text{{...}}: {repr(oval)}"
                        )

    # 10. Spatial / Parametric Visual & Figure Spec Guard (rules/03_stem.md Part 2)
    if "figure" in prob:
        fig = prob["figure"]
        if not isinstance(fig, dict):
            raise AiContractError(f"[{pid}] 'figure' must be a dictionary specification.")
        if "kind" not in fig:
            raise AiContractError(f"[{pid}] 'figure' specification must contain 'kind'.")
        if fig["kind"] == "geometry_2d":
            if "points" not in fig or not isinstance(fig["points"], dict):
                raise AiContractError(f"[{pid}] 'geometry_2d' figure must contain a 'points' dict.")
            if "shapes" not in fig or not isinstance(fig["shapes"], list) or len(fig["shapes"]) == 0:
                raise AiContractError(f"[{pid}] 'geometry_2d' figure must contain a non-empty 'shapes' list.")
        elif fig["kind"] == "cartesian_graph":
            if "xRange" not in fig or "yRange" not in fig:
                raise AiContractError(f"[{pid}] 'cartesian_graph' figure must contain 'xRange' and 'yRange'.")
            if "plots" not in fig or not isinstance(fig["plots"], list) or len(fig["plots"]) == 0:
                raise AiContractError(f"[{pid}] 'cartesian_graph' figure must contain a non-empty 'plots' list.")

    if "visual" in prob:
        vis = prob["visual"]
        if not isinstance(vis, dict):
            raise AiContractError(f"[{pid}] 'visual' must be a dictionary specification.")
        if "type" not in vis or "viewBox" not in vis or "elements" not in vis:
            raise AiContractError(f"[{pid}] 'visual' specification must contain 'type', 'viewBox', and 'elements'.")
        if not isinstance(vis.get("elements"), list) or len(vis["elements"]) == 0:
            raise AiContractError(f"[{pid}] 'visual.elements' must be a non-empty list of visual elements.")

    return True


def require_figure_decision(prob: Dict[str, Any], archetypes: List[Dict[str, Any]]) -> None:
    """03_stem §3.1: every archetype a problem uses has decided about figures, `figureBuilders` or a
    `figureNone` reason. Older archetypes get the field the first time a drill uses them."""
    arch = next((a for a in archetypes if a.get("archetypeKey") == prob.get("archetypeKey")), None)
    if arch and figure_decision_missing(arch):
        raise AiContractError(
            f"[{prob.get('id', '?')}] archetype '{arch['archetypeKey']}' has no figure decision. In its vault file "
            f"add 'figureBuilders' (geometry, graphs, number lines, the complex plane, anything a learner would sketch) "
            f"or 'figureNone': '<why a picture adds nothing>' (03_stem §3.1)."
        )


def require_figure_if_declared(prob: Dict[str, Any], archetypes: List[Dict[str, Any]]) -> None:
    """Rule 11 guard (03_stem §3.1): archetypes with `figureBuilders` demand a figure or a `figureWaiver`."""
    if "figure" in prob or prob.get("figureWaiver"):
        return
    if archetype_requires_figure(prob, archetypes):
        raise AiContractError(
            f"[{prob.get('id', '?')}] Rule 11 violated: archetype '{prob.get('archetypeKey')}' declares figureBuilders "
            f"but no figure could be built from givens {list(prob.get('givens', {}))}. "
            f"Use matching given keys or set 'figureWaiver' with a reason."
        )


BLIND_SOLVE_FIELDS = ("answer", "ambiguous", *BLIND_SOLVE_TAGS, "reverse", "steps")
# "If it fits, report X; otherwise report 0": a sentinel answer bolted on to earn check=edge.
SENTINEL_ANSWER_RE = re.compile(
    r"\b(?:otherwise|if\s+not|else)\b[^.?!]{0,40}?\b(?:report|answer|write|enter|give|respond\s+with)\b\s*\$?\s*0(?!\.?\d)",
    re.IGNORECASE,
)


def validate_blind_solve(prob: Dict[str, Any]) -> None:
    """L3+ floor gate (06 §2.3, 07 §4 V2): a separate solver that saw only the prompt must agree
    on the answer, find no ambiguity, and report demand tags whose level reaches `level`.
    A prompt with a sentinel fallback answer is rejected outright."""
    pid = prob.get("id", "?")
    level = prob["level"]
    bs = prob.get("blindSolve")
    missing = [f for f in BLIND_SOLVE_FIELDS if not isinstance(bs, dict) or f not in bs]
    if missing:
        raise AiContractError(
            f"[{pid}] L{level} problem needs a 'blindSolve' record with {list(BLIND_SOLVE_FIELDS)} "
            f"from a separate solver that saw only the prompt (07 §4 V2); missing {missing}."
        )
    for tag, allowed in BLIND_SOLVE_TAGS.items():
        if bs[tag] not in allowed:
            raise AiContractError(f"[{pid}] blindSolve.{tag} '{bs[tag]}' must be one of {list(allowed)}.")
    if not isinstance(bs["reverse"], bool) or not isinstance(bs["steps"], int) or isinstance(bs["steps"], bool):
        raise AiContractError(f"[{pid}] blindSolve.reverse must be true/false and blindSolve.steps an integer.")
    if bs["ambiguous"]:
        raise AiContractError(f"[{pid}] Blind solver found the prompt ambiguous.")
    if bs["check"] == "edge" and not str(bs.get("edgeRejected") or "").strip():
        raise AiContractError(
            f"[{pid}] blindSolve.check is 'edge' but 'edgeRejected' is empty. Record the candidate, branch or case "
            f"the check ruled out (06 §2.3). If every candidate passed, the check decided nothing: the tag is 'none'."
        )
    spec = prob.get("answerSpec") or {}
    if check_answer(spec, str(bs["answer"])).get("verdict") != "correct":
        raise AiContractError(
            f"[{pid}] Blind-solve answer '{bs['answer']}' does not match answerSpec '{spec.get('value')}'."
        )
    if SENTINEL_ANSWER_RE.search(prob.get("prompt") or ""):
        raise AiContractError(
            f"[{pid}] Prompt asks for a fallback answer ('otherwise report 0'). A fits/doesn't-fit clause added "
            f"to earn check=edge is not real demand (06 §2.3); make the constraint part of what is asked "
            f"(e.g. the largest value that satisfies it) or drop it."
        )
    got = demand_level(bs)
    if got < level:  # every L3+ label must be earned exactly (06 §2.3)
        shape = ", ".join(f"{t}={bs[t]}" for t in (*BLIND_SOLVE_TAGS, "reverse", "steps"))
        floor = " It is a direct computation (mental-math level)." if got == 1 else ""
        raise AiContractError(
            f"[{pid}] Labelled L{level} but the blind solver's tags ({shape}) give L{got}.{floor} "
            f"Redesign it once to add real demand; else drop the problem and log it with scripts.issues (06 §2.3)."
        )
    if got > level:
        shape = ", ".join(f"{t}={bs[t]}" for t in (*BLIND_SOLVE_TAGS, "reverse", "steps"))
        raise AiContractError(
            f"[{pid}] Labelled L{level} but the blind solver's tags ({shape}) give L{got} (under-labelled). "
            f"Label it L{got} (and satisfy L{got} gates) or simplify it to match L{level} (06 §2.3)."
        )


def _extract_braced_arg(s: str, start_idx: int) -> Optional[Tuple[str, int]]:
    """Extract content inside `{...}` starting at `start_idx` (where `s[start_idx] == '{'`)."""
    if start_idx >= len(s) or s[start_idx] != "{":
        return None
    depth = 0
    for idx in range(start_idx, len(s)):
        if s[idx] == "{":
            depth += 1
        elif s[idx] == "}":
            depth -= 1
            if depth == 0:
                return s[start_idx + 1 : idx], idx + 1
    return None


def _normalize_sympy_candidate(raw: str) -> str:
    """Normalize LaTeX/math notation in a candidate expression or option value for SymPy parsing."""
    s = str(raw or "").strip()
    if s.startswith("$") and s.endswith("$") and s.count("$") == 2:
        s = s[1:-1].strip()
    s = s.replace("\u2212", "-")
    for macro, repl in ((r"\times", "*"), (r"\cdot", "*"), (r"\div", "/")):
        s = s.replace(macro, repl)
    for macro in (r"\left", r"\right", r"\,", r"\;", r"\quad"):
        s = s.replace(macro, " ")
    # Convert \frac{a}{b} and \dfrac{a}{b}
    for cmd in (r"\dfrac", r"\frac"):
        while cmd in s:
            pos = s.find(cmd)
            rest = pos + len(cmd)
            while rest < len(s) and s[rest].isspace():
                rest += 1
            arg1 = _extract_braced_arg(s, rest)
            if not arg1:
                break
            num_str, next_idx = arg1
            while next_idx < len(s) and s[next_idx].isspace():
                next_idx += 1
            arg2 = _extract_braced_arg(s, next_idx)
            if not arg2:
                break
            den_str, end_idx = arg2
            s = s[:pos] + f"(({num_str})/({den_str}))" + s[end_idx:]
    # Convert \sqrt{a}
    while r"\sqrt" in s:
        pos = s.find(r"\sqrt")
        rest = pos + len(r"\sqrt")
        while rest < len(s) and s[rest].isspace():
            rest += 1
        arg1 = _extract_braced_arg(s, rest)
        if not arg1:
            break
        rad_str, end_idx = arg1
        s = s[:pos] + f"sqrt({rad_str})" + s[end_idx:]
    # Convert ^{a}
    while "^{" in s:
        pos = s.find("^{")
        arg1 = _extract_braced_arg(s, pos + 1)
        if not arg1:
            break
        exp_str, end_idx = arg1
        s = s[:pos] + f"**({exp_str})" + s[end_idx:]
    return s.strip()


_ALLOWED_MATH_WORDS = {
    "or",
    "and",
    "mod",
    "sqrt",
    "sin",
    "cos",
    "tan",
    "ln",
    "log",
    "exp",
    "abs",
    "Abs",
    "re",
    "im",
    "conjugate",
    "floor",
    "round",
    "diff",
    "inf",
    "oo",
    "pi",
}


def _looks_like_prose(raw: Any) -> bool:
    """True when `raw` is an English prose explanation rather than a mathematical expression."""
    if not isinstance(raw, str) or not raw.strip():
        return True
    s = raw.strip()
    if any(tok in s for tok in (r"\text{", r"\implies", r"\mapsto", "->", "<-", "↦")):
        return True
    if s.endswith("."):
        return True
    # Strip math delimiters to inspect words
    plain = s.replace("$", " ")
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", plain)
    # Two consecutive multi-letter words (neither a math function/connector) indicate English prose.
    prev_prose_word = False
    for m in re.finditer(r"[A-Za-z_]{2,}|\S", plain):
        tok = m.group(0)
        if re.fullmatch(r"[A-Za-z_]{2,}", tok) and tok not in _ALLOWED_MATH_WORDS:
            if prev_prose_word:
                return True
            prev_prose_word = True
        else:
            prev_prose_word = False
    # Also reject if there are >= 3 multi-letter non-math words in total without operators
    prose_words = [w for w in words if len(w) >= 3 and w not in _ALLOWED_MATH_WORDS]
    if len(prose_words) >= 3 and not re.search(r"[-+*/^=]", plain):
        return True
    return False


def _build_givens_env(prob: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, float], Dict[str, float], List[str]]:
    givens = prob.get("givens") if isinstance(prob.get("givens"), dict) else {}
    constants = prob.get("constants") if isinstance(prob.get("constants"), dict) else {}
    env = {**constants, **givens}
    givens_floats: Dict[str, float] = {}
    for k, v in givens.items():
        try:
            givens_floats[k] = float(v)
        except Exception:
            pass
    constant_floats: Dict[str, float] = {}
    for k, v in constants.items():
        try:
            constant_floats[k] = float(v)
        except Exception:
            pass
    spec = prob.get("answerSpec") or {}
    base_vars = list(spec.get("variables") or prob.get("variables") or ["x"])
    env_vars = [k for k in env if isinstance(k, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k)]
    all_vars = list(dict.fromkeys([*base_vars, *env_vars]))
    return env, givens_floats, constant_floats, all_vars


def _safe_to_expr(s: str, variables: Optional[List[str]] = None, trusted: bool = True) -> Optional[Any]:
    """Call `to_expr` safely, returning None on SafeParseError/Exception and supporting underscore given keys."""
    if not isinstance(s, str) or not s.strip():
        return None
    vars_in = list(variables or ["x"])
    alias_to_orig: Dict[str, str] = {}
    clean_vars: List[str] = []
    expr_str = s
    for idx, v in enumerate(vars_in):
        if "_" in v:
            alias = f"uvar{idx}x"
            alias_to_orig[alias] = v
            clean_vars.append(alias)
            expr_str = re.sub(rf"\b{re.escape(v)}\b", alias, expr_str)
        else:
            clean_vars.append(v)
    try:
        expr = to_expr(expr_str, variables=clean_vars, trusted=trusted)
    except Exception:
        return None
    if expr is not None and alias_to_orig and hasattr(expr, "free_symbols"):
        import sympy as sp

        subs = {sp.Symbol(alias): sp.Symbol(orig) for alias, orig in alias_to_orig.items()}
        expr = expr.subs(subs)
    return expr


def _substitute_env_symbols(expr: Any, env: Dict[str, Any], base_vars: List[str]) -> Any:
    if expr is None or not hasattr(expr, "free_symbols"):
        return expr
    subs_map = {}
    for sym in list(expr.free_symbols):
        name = str(sym)
        if name in env:
            val_expr = _safe_to_expr(str(env[name]), variables=base_vars, trusted=True)
            if val_expr is not None:
                subs_map[sym] = val_expr
    return expr.subs(subs_map) if subs_map else expr


def _matched_env_keys_in_expr(raw_expr: str, prob: Dict[str, Any]) -> Set[str]:
    """Return all keys in `givens` or `constants` referenced by `raw_expr` (symbolically or by number)."""
    env, givens_floats, constant_floats, _ = _build_givens_env(prob)
    matched: Set[str] = set()
    ident_tokens = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", str(raw_expr)))
    for k in env:
        if k in ident_tokens:
            matched.add(k)
    num_tokens = [float(t) for t in re.findall(r"\b\d+(?:\.\d+)?\b", str(raw_expr))]
    for g_key, g_val in {**givens_floats, **constant_floats}.items():
        for t_val in num_tokens:
            if abs(t_val - g_val) < 1e-6 or abs(t_val - abs(g_val)) < 1e-6 or abs(t_val - (g_val / 100.0)) < 1e-6:
                matched.add(g_key)
                break
    return matched


def _parse_single_math_piece(
    piece: str,
    env: Dict[str, Any],
    base_vars: List[str],
    all_vars: List[str],
) -> Optional[Any]:
    norm = _normalize_sympy_candidate(piece)
    if not norm or _looks_like_prose(norm):
        return None
    # Support single-variable assignment like "k = -3" or "x = 2"
    if "=" in norm and norm.count("=") == 1:
        lhs, rhs = [p.strip() for p in norm.split("=", 1)]
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", lhs):
            rhs_expr = _safe_to_expr(rhs, variables=all_vars, trusted=True)
            if rhs_expr is not None:
                return _substitute_env_symbols(rhs_expr, env, base_vars)
        return None
    expr = _safe_to_expr(norm, variables=all_vars, trusted=True)
    if expr is None:
        return None
    return _substitute_env_symbols(expr, env, base_vars)


def _eval_math_from_givens(
    raw_expr: str,
    prob: Dict[str, Any],
    substitute_env: bool = True,
) -> Tuple[Optional[Tuple[str, Any]], Set[str], Optional[str]]:
    """Evaluate `raw_expr` with SymPy from `prob['givens']` and `prob['constants']`."""
    if not isinstance(raw_expr, str) or not raw_expr.strip():
        return None, set(), "empty expression"
    s = raw_expr.strip()
    env, _, _, all_vars = _build_givens_env(prob)
    spec = prob.get("answerSpec") or {}
    base_vars = list(spec.get("variables") or prob.get("variables") or ["x"])
    active_env = env if substitute_env else {}
    active_vars = all_vars if substitute_env else base_vars
    matched = _matched_env_keys_in_expr(s, prob)

    # 1. Interval form
    norm_s = _normalize_sympy_candidate(s)
    if spec.get("type") == "interval" or (norm_s and norm_s[0] in "[(" and norm_s[-1] in "])" and "," in norm_s):
        try:
            iv = parse_interval(norm_s, variables=spec.get("variables"))
            return ("interval", iv), matched, None
        except Exception:
            if spec.get("type") == "interval":
                return None, matched, f"invalid interval '{s}'"

    # 2. Multi-value set form (e.g. "$k = -3$ or $k = 2$", "{-3, 2}", "-3, 2")
    unwrapped = norm_s
    if unwrapped.startswith(r"\{") and unwrapped.endswith(r"\}"):
        unwrapped = unwrapped[2:-2].strip()
    elif unwrapped.startswith("{") and unwrapped.endswith("}"):
        unwrapped = unwrapped[1:-1].strip()
    if re.search(r"\bor\b", s) or ("," in unwrapped and not re.search(r"[A-Za-z_]+\s*\([^)]*,", unwrapped)):
        parts = re.split(r"\s+\bor\b\s+|,", unwrapped if "," in unwrapped and not re.search(r"\bor\b", s) else s)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= 2:
            parsed_items = []
            for p_item in parts:
                expr_item = _parse_single_math_piece(p_item, active_env, base_vars, active_vars)
                if expr_item is None:
                    parsed_items = []
                    break
                parsed_items.append(expr_item)
            if parsed_items:
                return ("set", parsed_items), matched, None

    # 3. Single expression or variable assignment
    if _looks_like_prose(s):
        return None, matched, "prose string"
    single = _parse_single_math_piece(s, active_env, base_vars, active_vars)
    if single is not None:
        return ("expr", single), matched, None
    return None, matched, f"SymPy could not parse '{s}'"


def _parse_option_math_value(opt: Dict[str, Any], prob: Dict[str, Any]) -> Optional[Tuple[str, Any]]:
    """Parse a choice option's mathematical value (from `value`, `latex`, `display`, or `label`)."""
    if not isinstance(opt, dict):
        return None
    raw = opt.get("value")
    if raw is None:
        raw = opt.get("latex") or opt.get("display") or opt.get("label")
    if not isinstance(raw, str) or not raw.strip():
        return None
    s = raw.strip()
    if re.fullmatch(r"Line\s+\d+", s, re.IGNORECASE):
        return None
    # Do not substitute givens into the option's displayed value unless `opt["value"]` is used:
    # e.g., an option label "$x - 2$" is a polynomial in x, not a given lookup.
    val, _, _ = _eval_math_from_givens(s, prob, substitute_env=False)
    return val


def _math_values_equal(val_a: Tuple[str, Any], val_b: Tuple[str, Any], vars_list: List[str]) -> bool:
    kind_a, a = val_a
    kind_b, b = val_b
    if kind_a == "interval" and kind_b == "interval":
        return _intervals_equal(a, b)
    if kind_a == "expr" and kind_b == "expr":
        return is_equal(a, b, variables=vars_list)
    if kind_a == "set" and kind_b == "set":
        return (
            len(a) == len(b)
            and all(any(is_equal(x, y, variables=vars_list) for y in b) for x in a)
            and all(any(is_equal(y, x, variables=vars_list) for x in a) for y in b)
        )
    if kind_a == "set" and kind_b == "expr":
        return len(a) == 1 and is_equal(a[0], b, variables=vars_list)
    if kind_a == "expr" and kind_b == "set":
        return len(b) == 1 and is_equal(a, b[0], variables=vars_list)
    return False


def check_distractor_provenance(
    prob: Dict[str, Any],
    archetypes: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[str], List[str]]:
    """Deterministic distractor & trap provenance gate (06 §3, §4 G4, 07 §4).

    Returns ``(errors, warnings)``:
    - Evaluates every declared option ``provenance`` / ``trapFormula`` / ``derivation`` (and problem
      ``trapDerivation`` / ``trapFormula`` / ``trapValue``) with SymPy from ``givens`` and ``constants``,
      requiring it to equal the option's value (or ``trapValue``) and differ from the correct answer.
    - Requires every distractor option in a choice problem to name a vault ``trapTag`` of the problem's
      archetype and declare a non-empty provenance (for find-the-flaw, ``provenance`` or ``trapTag``).
    - Cross-checks ``trapDerivation`` against ``trapGivens`` and against the vault's ``trapFormula``
      when the vault defines a SymPy-evaluable formula over the problem's ``givens``.
    - Reports ``"unverifiable"`` warnings when an option's provenance or label is English prose because
      the current ``RawChoiceOption`` schema lacks dedicated symbolic ``trapFormula`` / ``value`` fields.
    """
    errors: List[str] = []
    warnings: List[str] = []
    pid = prob.get("id", "?")
    spec = prob.get("answerSpec") or {}
    givens = prob.get("givens") if isinstance(prob.get("givens"), dict) else {}
    env, _, _, all_vars = _build_givens_env(prob)
    base_vars = list(spec.get("variables") or prob.get("variables") or ["x"])

    arch_key = prob.get("archetypeKey")
    arch = next((a for a in (archetypes or []) if a.get("archetypeKey") == arch_key), None)
    arch_traps: List[str] = []
    arch_trap_formulas: Dict[str, str] = {}
    if arch is not None:
        for t in arch.get("cognitiveTraps") or []:
            if isinstance(t, dict):
                t_tag = t.get("trapTag")
                if t_tag:
                    arch_traps.append(t_tag)
                    if isinstance(t.get("trapFormula"), str) and t["trapFormula"].strip():
                        arch_trap_formulas[t_tag] = t["trapFormula"].strip()
            elif isinstance(t, str):
                arch_traps.append(t)

    common_tag = prob.get("commonTrapTag")
    td = prob.get("trapDerivation")
    verify_obj = prob.get("verify") if isinstance(prob.get("verify"), dict) else {}
    tv = verify_obj.get("trapValue") if verify_obj.get("trapValue") is not None else prob.get("trapValue")
    prob_tf = prob.get("trapFormula") or verify_obj.get("trapFormula")
    verify_src = verify_obj.get("source")
    verify_src_val, _, _ = (
        _eval_math_from_givens(str(verify_src), prob) if verify_src is not None else (None, set(), None)
    )
    tv_val, _, _ = _eval_math_from_givens(str(tv), prob) if tv is not None else (None, set(), None)
    td_val, td_matched_keys, _ = _eval_math_from_givens(str(td), prob) if td is not None else (None, set(), None)

    # 1. Problem-level trapDerivation / trapFormula / trapGivens checks
    if td is not None and tv is not None:
        if td_val is None or tv_val is None or not _math_values_equal(td_val, tv_val, base_vars):
            errors.append(
                f"[{pid}] trapDerivation '{td}' evaluates to '{td_val[1] if td_val else None}' from givens, "
                f"which does not equal trapValue '{tv}'."
            )

        trap_givens = prob.get("trapGivens")
        if isinstance(trap_givens, list) and trap_givens and not _is_omission_trap(spec, tv):
            td_num_tokens = [float(t) for t in re.findall(r"\b\d+(?:\.\d+)?\b", str(td))]
            matched_tg = set()
            for idx_tg, raw_tg in enumerate(trap_givens):
                try:
                    tg_f = float(raw_tg)
                except Exception:
                    continue
                if any(
                    abs(tg_f - t) < 1e-6 or abs(abs(tg_f) - t) < 1e-6 or abs(tg_f / 100.0 - t) < 1e-6
                    for t in td_num_tokens
                ) or any(
                    k in td_matched_keys and isinstance(env.get(k), (int, float)) and abs(float(env[k]) - tg_f) < 1e-6
                    for k in env
                ):
                    matched_tg.add((idx_tg, tg_f))
            req_tg_count = min(2, len(trap_givens))
            if len(matched_tg) < req_tg_count:
                errors.append(
                    f"[{pid}] trapDerivation '{td}' is unrelated to trap '{common_tag}': must use at least "
                    f"{req_tg_count} values from trapGivens {trap_givens} (found {len(matched_tg)})."
                )

        if isinstance(prob_tf, str) and prob_tf.strip():
            ptf_val, ptf_keys, ptf_err = _eval_math_from_givens(prob_tf, prob)
            if ptf_val is None or not ptf_keys:
                errors.append(
                    f"[{pid}] trapFormula '{prob_tf}' could not be evaluated from givens {givens}: "
                    f"{ptf_err or 'no givens referenced'}."
                )
            elif tv_val is not None and not _math_values_equal(ptf_val, tv_val, base_vars):
                errors.append(
                    f"[{pid}] trapFormula '{prob_tf}' evaluates to '{ptf_val[1]}' from givens, "
                    f"which does not equal trapValue '{tv}'."
                )

        vault_tf = arch_trap_formulas.get(common_tag) if common_tag else None
        if vault_tf and not _looks_like_prose(vault_tf):
            vtf_norm = _normalize_sympy_candidate(vault_tf)
            vtf_expr = _safe_to_expr(vtf_norm, variables=all_vars, trusted=True)
            if vtf_expr is not None and hasattr(vtf_expr, "free_symbols"):
                free_names = {str(s) for s in vtf_expr.free_symbols}
                if free_names and free_names <= set(env.keys()):
                    req_given_keys = free_names & set(givens.keys())
                    used_req_keys = req_given_keys & td_matched_keys
                    if req_given_keys and len(used_req_keys) < min(2, len(req_given_keys)):
                        errors.append(
                            f"[{pid}] trapDerivation '{td}' is unrelated to trap '{common_tag}': vault trapFormula "
                            f"'{vault_tf}' operates on givens {sorted(req_given_keys)}, but trapDerivation only uses "
                            f"{sorted(used_req_keys)}."
                        )
                    elif free_names >= set(givens.keys()) and tv_val is not None:
                        vtf_sub = _substitute_env_symbols(vtf_expr, env, base_vars)
                        if not _math_values_equal(("expr", vtf_sub), tv_val, base_vars):
                            errors.append(
                                f"[{pid}] trapDerivation '{td}' (trapValue '{tv}') is unrelated to trap '{common_tag}': "
                                f"vault trapFormula '{vault_tf}' evaluates to '{vtf_sub}' at givens {givens}."
                            )

    # 2. Choice option provenance & trapTag checks
    if spec.get("type") != "choice":
        return errors, warnings

    options = [o for o in (spec.get("options") or []) if isinstance(o, dict)]
    correct_id = str(spec.get("correct") or prob.get("answerPlain") or "").strip()

    if is_find_the_flaw(prob):
        distractor_tags_found = 0
        for opt in options:
            opt_id = str(opt.get("id", "?")).strip()
            opt_tag = str(opt.get("trapTag") or opt.get("tag") or "").strip()
            has_prov = any(
                isinstance(opt.get(k), str) and opt.get(k).strip() for k in ("provenance", "trapFormula", "derivation")
            )
            if opt_tag:
                if opt_id != correct_id:
                    distractor_tags_found += 1
                if arch is not None and opt_tag not in arch_traps:
                    errors.append(
                        f"[{pid}] Option '{opt_id}' trapTag '{opt_tag}' is not one of archetype '{arch_key}' "
                        f"cognitiveTraps {arch_traps}."
                    )
            if opt_id != correct_id and not opt_tag and not has_prov:
                errors.append(f"[{pid}] Option '{opt_id}' is a distractor with no provenance or trapTag (06 §2.3).")
        return errors, warnings

    # Non-flaw choice problem
    correct_opt = next((o for o in options if str(o.get("id", "")).strip() == correct_id), None)
    correct_opt_val = _parse_option_math_value(correct_opt, prob) if correct_opt else None

    if tv_val is not None and verify_src_val is not None and _math_values_equal(tv_val, verify_src_val, base_vars):
        errors.append(
            f"[{pid}] trapValue '{tv}' (from trapDerivation '{td}') equals the correct answer "
            f"from verify.source '{verify_src}'."
        )
    if tv_val is not None and correct_opt_val is not None and _math_values_equal(tv_val, correct_opt_val, base_vars):
        errors.append(
            f"[{pid}] trapValue '{tv}' (from trapDerivation '{td}') equals correct Option '{correct_id}' "
            f"value '{correct_opt.get('label') if correct_opt else ''}'."
        )

    common_trap_options: List[Tuple[Dict[str, Any], Optional[Tuple[str, Any]]]] = []
    for opt in options:
        opt_id = str(opt.get("id", "?")).strip()
        opt_tag = str(opt.get("trapTag") or opt.get("tag") or "").strip()
        raw_tf = opt.get("trapFormula")
        raw_deriv = opt.get("derivation")
        raw_prov = opt.get("provenance")
        opt_val = _parse_option_math_value(opt, prob)
        opt_label_str = str(opt.get("value") if opt.get("value") is not None else opt.get("label", ""))

        if opt_id == correct_id:
            if opt_tag:
                errors.append(
                    f"[{pid}] Option '{opt_id}' is the correct answer ('{correct_id}') but carries distractor "
                    f"trapTag '{opt_tag}'."
                )
        else:
            if not opt_tag:
                errors.append(
                    f"[{pid}] Option '{opt_id}' is a distractor without a trapTag (every distractor must name a "
                    f"single-misconception vault trapTag of archetype '{arch_key}')."
                )
            elif arch is not None and opt_tag not in arch_traps:
                errors.append(
                    f"[{pid}] Option '{opt_id}' trapTag '{opt_tag}' is not one of archetype '{arch_key}' "
                    f"cognitiveTraps {arch_traps}."
                )
            if common_tag and opt_tag == common_tag:
                common_trap_options.append((opt, opt_val))

            has_prov = any(isinstance(x, str) and x.strip() for x in (raw_prov, raw_tf, raw_deriv))
            if not has_prov:
                errors.append(
                    f"[{pid}] Option '{opt_id}' is a distractor with no provenance (must declare provenance, "
                    f"trapFormula, or derivation)."
                )

            if (
                opt_val is not None
                and correct_opt_val is not None
                and _math_values_equal(opt_val, correct_opt_val, base_vars)
            ):
                errors.append(
                    f"[{pid}] Option '{opt_id}' value '{opt_label_str}' equals correct Option '{correct_id}' value."
                )

        # Evaluate declared option formula (trapFormula / derivation / non-prose provenance)
        explicit_formula = None
        if isinstance(raw_tf, str) and raw_tf.strip():
            explicit_formula = raw_tf.strip()
        elif isinstance(raw_deriv, str) and raw_deriv.strip():
            explicit_formula = raw_deriv.strip()
        elif isinstance(raw_prov, str) and raw_prov.strip() and not _looks_like_prose(raw_prov):
            explicit_formula = raw_prov.strip()

        if explicit_formula is not None:
            norm_f = _normalize_sympy_candidate(explicit_formula)
            if re.fullmatch(r"^\s*[-+]?\d*\.?\d+\s*$", norm_f):
                errors.append(
                    f"[{pid}] Option '{opt_id}' provenance/derivation '{explicit_formula}' cannot be a bare number; "
                    f"it must be derived from givens {givens}."
                )
                continue
            eval_val, matched_keys, eval_err = _eval_math_from_givens(explicit_formula, prob)
            if eval_val is None:
                errors.append(
                    f"[{pid}] Option '{opt_id}' provenance/derivation '{explicit_formula}' could not be evaluated "
                    f"with SymPy from givens {givens}: {eval_err or 'invalid expression'}."
                )
                continue
            if not matched_keys:
                errors.append(
                    f"[{pid}] Option '{opt_id}' provenance/derivation '{explicit_formula}' does not reference any "
                    f"problem givens {givens}."
                )
                continue
            if opt_val is None:
                warnings.append(
                    f"[{pid}] Option '{opt_id}' value is unverifiable with SymPy: option label '{opt_label_str}' "
                    f"has no parseable symbolic/numeric value in current RawChoiceOption schema."
                )
            else:
                if not _math_values_equal(eval_val, opt_val, base_vars):
                    errors.append(
                        f"[{pid}] Option '{opt_id}' provenance/derivation '{explicit_formula}' evaluates to "
                        f"'{eval_val[1]}' from givens, which does not equal option value '{opt_label_str}'."
                    )
                if opt_id != correct_id:
                    if (correct_opt_val is not None and _math_values_equal(eval_val, correct_opt_val, base_vars)) or (
                        correct_opt_val is not None
                        and verify_src_val is not None
                        and _math_values_equal(eval_val, verify_src_val, base_vars)
                    ):
                        errors.append(
                            f"[{pid}] Option '{opt_id}' provenance/derivation '{explicit_formula}' evaluates to "
                            f"'{eval_val[1]}', which equals the correct answer."
                        )
        elif opt_id != correct_id and isinstance(raw_prov, str) and raw_prov.strip():
            # Prose provenance in current RawChoiceOption schema
            verified_by_common_or_vault = False
            if common_tag and opt_tag == common_tag and tv_val is not None and opt_val is not None:
                verified_by_common_or_vault = True
                if not _math_values_equal(tv_val, opt_val, base_vars):
                    errors.append(
                        f"[{pid}] Option '{opt_id}' carries commonTrapTag '{common_tag}' with value '{opt_label_str}', "
                        f"which does not equal trapValue '{tv}' (from trapDerivation '{td}')."
                    )
            opt_vault_tf = arch_trap_formulas.get(opt_tag) if opt_tag else None
            if opt_vault_tf and not _looks_like_prose(opt_vault_tf):
                ov_expr = _safe_to_expr(_normalize_sympy_candidate(opt_vault_tf), variables=all_vars, trusted=True)
                if ov_expr is not None and hasattr(ov_expr, "free_symbols"):
                    ov_free = {str(s) for s in ov_expr.free_symbols}
                    if ov_free and ov_free <= set(env.keys()) and ov_free >= set(givens.keys()) and opt_val is not None:
                        verified_by_common_or_vault = True
                        ov_sub = _substitute_env_symbols(ov_expr, env, base_vars)
                        if not _math_values_equal(("expr", ov_sub), opt_val, base_vars):
                            errors.append(
                                f"[{pid}] Option '{opt_id}' (trapTag '{opt_tag}') value '{opt_label_str}' does not "
                                f"equal vault trapFormula '{opt_vault_tf}' evaluated at givens ('{ov_sub}')."
                            )
            if not verified_by_common_or_vault:
                warnings.append(
                    f"[{pid}] Option '{opt_id}' provenance is unverifiable with SymPy: current RawChoiceOption "
                    f"schema lacks a dedicated symbolic trapFormula/value field and provenance is prose."
                )

    if common_tag:
        distractor_ids = [str(o.get("id", "?")).strip() for o in options if str(o.get("id", "")).strip() != correct_id]
        if not common_trap_options:
            errors.append(
                f"[{pid}] No distractor option (options {distractor_ids}) carries commonTrapTag '{common_tag}'."
            )
        else:
            for c_opt, c_val in common_trap_options:
                c_id = str(c_opt.get("id", "?")).strip()
                c_lbl = str(c_opt.get("value") if c_opt.get("value") is not None else c_opt.get("label", ""))
                if c_val is not None and tv_val is not None and not _math_values_equal(tv_val, c_val, base_vars):
                    err_msg = (
                        f"[{pid}] Option '{c_id}' carries commonTrapTag '{common_tag}' with value '{c_lbl}', "
                        f"which does not equal trapValue '{tv}' (from trapDerivation '{td}')."
                    )
                    if err_msg not in errors:
                        errors.append(err_msg)

    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


def validate_distractor_provenance(
    prob: Dict[str, Any],
    archetypes: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Run ``check_distractor_provenance`` and raise ``AiContractError`` on any errors; returns warnings."""
    errors, warnings = check_distractor_provenance(prob, archetypes=archetypes)
    if errors:
        raise AiContractError("; ".join(errors))
    return warnings


def validate_against_vault(prob: Dict[str, Any], archetypes: List[Dict[str, Any]], unit_code: str) -> None:
    """Gates that need the vault or a blind solve (07 §4), shared by --check and ingest.

    - archetypeKey must be a vault archetype, and commonTrapTag one of its cognitiveTraps,
      so trapMatched telemetry only ever reports misconceptions the vault defines.
    - L3+ problems must pass the blind-solve floor gate (`validate_blind_solve`).
      G2 counts structure (steps, concepts, constraints, category) and cannot judge demand.
    """
    pid = prob.get("id", "?")
    key = prob.get("archetypeKey")
    arch = next((a for a in archetypes if a.get("archetypeKey") == key), None)
    if arch is None:
        hint = " (or its units are not yet eligible)" if unit_code == BRIDGE_SCOPE else ""
        raise AiContractError(f"[{pid}] archetypeKey '{key}' is not in the {unit_code} reasoning vault{hint}.")

    tag = prob.get("commonTrapTag")
    traps = ingest_core.archetype_trap_tags(arch)
    if tag not in traps:
        raise AiContractError(
            f"[{pid}] commonTrapTag '{tag}' is not one of archetype '{key}' cognitiveTraps {traps}. "
            f"Use a listed tag, or propose adding the trap to the vault first."
        )

    validate_distractor_provenance(prob, archetypes)

    if unit_code == BRIDGE_SCOPE:
        bridge_errors = validate_bridge_problem(prob, arch)
        if bridge_errors:
            raise AiContractError("; ".join(bridge_errors))

    validate_context_check(prob)  # before the blind-solve gate, so a bad story is reported even if the level fails too
    level = prob.get("level")
    if isinstance(level, int) and not isinstance(level, bool):
        if level >= 3 or prob.get("blindSolve") is not None:
            validate_blind_solve(prob)
        form = str(prob.get("form") or "").strip().lower()
        if level == 1 and form == "reverse":
            raise AiContractError(
                f"[{pid}] Labelled L1 but form='reverse' demands at least L2 (under-labelled; 06 §2.3). "
                f"Label it L2 (with >= {L2_MIN_REAL_STEPS} real steps) or make it a direct L1 problem."
            )
        if level < 3 and form == "diagnose":
            raise AiContractError(
                f"[{pid}] Labelled L{level} but form='diagnose' demands at least L3 (under-labelled; 06 §2.3). "
                f"Label it L3 with a passing blindSolve or rewrite it for L{level}."
            )
        verify_obj = prob.get("verify")
        if level < 3 and isinstance(verify_obj, dict) and verify_obj.get("flaw") is not None:
            raise AiContractError(
                f"[{pid}] Labelled L{level} but verify.flaw (find-the-flaw / diagnose form) demands at least L3 "
                f"(under-labelled; 06 §2.3). Label it L3 with a passing blindSolve or remove verify.flaw."
            )
        arch_level = arch.get("level")
        if level < 3 and isinstance(arch_level, int) and not isinstance(arch_level, bool) and level < arch_level:
            raise AiContractError(
                f"[{pid}] Labelled L{level} is below archetype '{key}' base level L{arch_level} "
                f"(under-labelled; 06 §2.3). Raise level to at least L{arch_level} or use a lower-level archetype."
            )


CONTEXT_CHECK_VERDICTS = ("ok", "fail")


def validate_context_check(prob: Dict[str, Any]) -> None:
    """Real-world context gate (07 §4.8): a problem with a non-empty `context` needs a
    `contextCheck` {verdict, note} from a separate reviewer who judged the story against the
    three criteria (real domain law, units and bounds, removal test). Plain problems leave
    `context` empty and skip this gate."""
    ctx = prob.get("context")
    if not (isinstance(ctx, str) and ctx.strip()):
        return
    pid = prob.get("id", "?")
    cc = prob.get("contextCheck")
    if (
        not isinstance(cc, dict)
        or cc.get("verdict") not in CONTEXT_CHECK_VERDICTS
        or not str(cc.get("note") or "").strip()
    ):
        raise AiContractError(
            f"[{pid}] Problem has context '{ctx}' but no 'contextCheck' {{verdict: ok|fail, note}} from a separate "
            f"reviewer (07 §4.8). Get the check, or drop the story and leave 'context' empty."
        )
    if cc["verdict"] == "fail":
        raise AiContractError(
            f"[{pid}] Context reviewer rejected the story: {cc['note']} (07 §4.8). "
            f"Fix the story so the math is the real domain law, or make the problem plain."
        )


REVIEW_VERDICTS = ("pass", "fix")


def validate_review(prob: Dict[str, Any]) -> None:
    """Automated review gate (07 §4 V3): before ingest, a separate reviewer subagent that sees the whole
    problem (prompt, answer, steps, hints) and the brief records `review: {verdict, note}`. Only `pass`
    is ingested; `fix` means the author must fix or drop the problem. `--check` runs before the review,
    so it only checks a review that is already present; ingest requires one."""
    pid = prob.get("id", "?")
    rv = prob.get("review")
    if not ingest_core.has_review_record(rv, REVIEW_VERDICTS):
        raise AiContractError(
            f"[{pid}] Needs 'review' {{verdict: pass|fix, note}} from the reviewer subagent (07 §4 V3) before ingest."
        )
    if rv["verdict"] != "pass":
        raise AiContractError(f"[{pid}] Reviewer asked for a fix: {rv['note']} (07 §4 V3). Fix or drop the problem.")


def get_vault_path(unit_code: str, vault_dir: Optional[str] = None) -> str:
    return ingest_core.get_vault_path(unit_code, _vault_dir(vault_dir))


def _vault_dir(vault_dir: Optional[str] = None) -> str:
    return ingest_core.resolve_vault_dir(vault_dir, "REASONING_VAULT_DIR", VAULT_DIR)


def load_scope_archetypes(
    code: str,
    vault_dir: Optional[str] = None,
    eligible_units: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    """Load unit, chapter, or eligible bridge archetypes with their vault file annotations."""
    return ingest_core.load_scope_archetypes(
        code, _vault_dir(vault_dir), math_scope=True, eligible_units=eligible_units
    )


def load_reasoning_vault(unit_code: str, vault_dir: Optional[str] = None) -> Dict[str, Any]:
    return ingest_core.load_reasoning_vault(unit_code, _vault_dir(vault_dir))


def save_reasoning_vault(unit_code: str, vault_data: Dict[str, Any], vault_dir: Optional[str] = None) -> str:
    return ingest_core.save_reasoning_vault(unit_code, vault_data, _vault_dir(vault_dir))


def register_archetype(unit_code: str, archetype: Dict[str, Any], vault_dir: Optional[str] = None) -> Dict[str, Any]:
    return ingest_core.register_archetype(unit_code, archetype, _vault_dir(vault_dir))


def mark_context_used(
    unit_code: str,
    archetype_key: str,
    context_tag: str,
    vault_dir: Optional[str] = None,
    eligible_units: Optional[Iterable[str]] = None,
) -> None:
    scope_archetypes = load_scope_archetypes(unit_code, vault_dir, eligible_units=eligible_units)
    ingest_core.mark_context_used(unit_code, archetype_key, context_tag, _vault_dir(vault_dir), scope_archetypes)


def _step_math_errors(prob: Dict[str, Any]) -> Iterable[str]:
    for index, step in enumerate(prob.get("steps") or [], 1):
        explain = step.get("explain") if isinstance(step, dict) else None
        if not isinstance(explain, str):
            continue
        for prose in _STEP_INLINE_MATH_RE.split(explain):
            match = _STEP_BARE_MATH_RE.search(_STEP_PROSE_LABEL_RE.sub(" ", prose))
            if match:
                yield f"[{prob['id']}] Step {index} explanation contains {match[0]!r} outside $...$. Use inline math."
                break


_STEP_LATEX_FUNC_RE = re.compile(r"\\(sin|cos|tan|ln|log|exp|pi)\b")
_STEP_LEADING_EQ_RE = re.compile(r"^\s*=+\s*")
_STEP_SINGLE_EQ_RE = re.compile(r"(?<![<>!=\\])=(?!=)")
# Preserve function calls as written so evaluating a radical or a trig function still counts as a step.
_STEP_UNEVALUATED_FUNCS = {name: sp.Function(name) for name in WHITELIST_FUNCS}
_STEP_KNOWN_SYMBOLS = _STEP_UNEVALUATED_FUNCS.keys() | WHITELIST_CONSTANTS.keys()


def _canonical_sympy_expr(expr: Any) -> str:
    """Canonicalize an unevaluated SymPy expression up to Add/Mul commutativity and associativity.

    Arithmetic stays unevaluated so genuine simplification steps (e.g. ``39 - 7`` -> ``32`` or
    ``32 / 4`` -> ``8``) remain distinct, while commutative reorderings (``4x + 7`` vs ``7 + 4x``,
    ``4 * x`` vs ``x * 4``, ``a - b`` vs ``-b + a``) map to the same canonical key.
    """
    if isinstance(expr, (sp.Add, sp.Mul)):
        kind = type(expr)
        flat: List[str] = []
        stack = list(expr.args)
        while stack:
            item = stack.pop()
            if isinstance(item, kind):
                stack.extend(item.args)
            else:
                flat.append(_canonical_sympy_expr(item))
        return f"{kind.__name__}({','.join(sorted(flat))})"
    if getattr(expr, "args", ()):
        return f"{type(expr).__name__}(" + ",".join(_canonical_sympy_expr(a) for a in expr.args) + ")"
    return sp.srepr(expr)


def _parse_step_side_canonical(raw_side: str) -> Optional[str]:
    """Parse one side of a step via ``answer_check.safe_parse(..., evaluate=False)`` into a canonical key."""
    s = raw_side.strip()
    if not s or "\\" in s:
        return None
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", s)
    if any("_" in t for t in tokens):
        return None
    variables = sorted({t for t in tokens if t not in _STEP_KNOWN_SYMBOLS})
    try:
        expr = safe_parse(s, variables=variables, evaluate=False, allowed_funcs=_STEP_UNEVALUATED_FUNCS)
    except SafeParseError:
        return None
    return _canonical_sympy_expr(expr)


def _normalize_step_latex(latex: Any) -> str:
    """Return a canonical anti-padding key for a step's LaTeX.

    Strips leading ``=``, formatting macros, extra braces, and whitespace. When the expression (or
    both sides of a single ``=`` equation) parses via ``answer_check.safe_parse(..., evaluate=False)``,
    returns a canonical math form that treats commutative reordering and LHS/RHS equation flips as
    identical while keeping real simplification steps distinct. Falls back to string normalisation
    when parsing fails.
    """
    if not isinstance(latex, str):
        return ""
    s = latex.strip().replace("$", "").replace("\u2212", "-")
    for macro in (
        r"\left",
        r"\right",
        r"\,",
        r"\;",
        r"\:",
        r"\!",
        r"\quad",
        r"\qquad",
        r"\displaystyle",
        r"\textstyle",
    ):
        s = s.replace(macro, "")
    cand = _normalize_sympy_candidate(s)
    cand = _STEP_LATEX_FUNC_RE.sub(r"\1", cand)
    cand = _STEP_LEADING_EQ_RE.sub("", cand).strip()
    while cand.startswith("{"):
        group = _extract_braced_arg(cand, 0)
        if group is None or group[1] != len(cand):
            break
        cand = _STEP_LEADING_EQ_RE.sub("", group[0]).strip()
    if not cand:
        return ""

    eq_parts = _STEP_SINGLE_EQ_RE.split(cand)
    if len(eq_parts) == 2:
        lhs = _parse_step_side_canonical(eq_parts[0])
        rhs = _parse_step_side_canonical(eq_parts[1])
        if lhs is not None and rhs is not None:
            left_k, right_k = sorted((lhs, rhs))
            return f"eq:{left_k}={right_k}"
    elif len(eq_parts) == 1:
        parsed = _parse_step_side_canonical(eq_parts[0])
        if parsed is not None:
            return f"expr:{parsed}"

    # String fallback when SymPy parsing fails: drop braces and whitespace (and sort sides of a single '=').
    fallback = re.sub(r"\s+", "", cand.replace("{", "").replace("}", ""))
    if not fallback:
        return ""
    fb_parts = _STEP_SINGLE_EQ_RE.split(fallback)
    if len(fb_parts) == 2 and all(fb_parts):
        fallback = "=".join(sorted(fb_parts))
    return f"str:{fallback}"


def count_real_steps(prob: Dict[str, Any]) -> int:
    """Count distinct real derivation steps in ``prob['steps']``.

    A step counts only when:
    - both ``latex`` and ``explain`` are non-empty strings; and
    - its canonical ``latex`` key has not already been seen in the given ``display``/prompt
      expressions or any earlier counted step (rejects adjacent and non-adjacent repeats,
      leading ``=``, extra braces, commutative reorderings, and LHS/RHS equation flips).
    """
    steps = prob.get("steps")
    if not isinstance(steps, list):
        return 0
    seen: Set[str] = set()
    given_norm = _normalize_step_latex(prob.get("display") or "")
    if given_norm:
        seen.add(given_norm)
    for match in _INLINE_MATH_RE.findall(str(prob.get("prompt") or "")):
        norm_match = _normalize_step_latex(match)
        if norm_match:
            seen.add(norm_match)

    count = 0
    for st in steps:
        if not isinstance(st, dict):
            continue
        lx, ex = st.get("latex"), st.get("explain")
        if not (isinstance(lx, str) and lx.strip() and isinstance(ex, str) and ex.strip()):
            continue
        norm = _normalize_step_latex(lx)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        count += 1
    return count


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _unique_baseline_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AiContractError(f"Duplicate baseline key: {key!r}.")
        result[key] = value
    return result


def load_l2_step_floor_baseline(repo_root: Optional[Path] = None) -> Dict[str, Dict[str, List[str]]]:
    """Load the shrink-only baseline and reject malformed entries or duplicate IDs."""
    path = (repo_root or _repo_root()) / L2_STEP_FLOOR_BASELINE_PATH
    if not path.is_file():
        return {"drills": {}, "variants": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_baseline_object)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AiContractError(f"Malformed baseline JSON in {L2_STEP_FLOOR_BASELINE_PATH}: {exc}") from exc

    if not isinstance(raw, dict):
        raise AiContractError("Malformed baseline: top-level value must be an object.")

    allowed_sections = ("drills", "variants")
    unknown_keys = sorted(raw.keys() - set(allowed_sections))
    if unknown_keys:
        raise AiContractError(f"Malformed baseline: unknown top-level key(s) {unknown_keys}.")

    baseline: Dict[str, Dict[str, List[str]]] = {}
    for section in allowed_sections:
        entries = raw.get(section, {})
        if not isinstance(entries, dict):
            raise AiContractError(f"Malformed baseline entry: '{section}' must be an object mapping IDs to lists.")
        for container_id, id_list in entries.items():
            if not container_id or container_id != container_id.strip():
                raise AiContractError(f"Malformed baseline key under '{section}'.")
            if not isinstance(id_list, list) or not id_list:
                raise AiContractError(
                    f"Malformed baseline entry: {section}.{container_id} must be a non-empty list of IDs."
                )
            if any(not isinstance(item, str) or not item or item != item.strip() for item in id_list):
                raise AiContractError(f"Malformed baseline ID under {section}.{container_id}.")
            if len(set(id_list)) != len(id_list):
                raise AiContractError(f"Duplicate baseline ID: {section}.{container_id}.")
        baseline[section] = entries
    return baseline


def validate_l2_step_floor(
    prob: Dict[str, Any],
    *,
    drill_id: Optional[str] = None,
    bank_unit: Optional[str] = None,
    baseline: Optional[Dict[str, Dict[str, List[str]]]] = None,
) -> None:
    """Enforce the L2 step floor (``>= 4`` real steps, matching ``demand_level``).

    Existing canonical drills and variant banks recorded in ``tests/data/l2_step_floor_baseline.json``
    may be grandfathered only when both ``baseline`` and ``drill_id``/``bank_unit`` are supplied.
    New drafts, drill ingests, and newly added variants pass neither.
    """
    if prob.get("level") != 2:
        return
    pid = str(prob.get("variantId") or prob.get("id") or "?")
    n_steps = count_real_steps(prob)
    if n_steps >= L2_MIN_REAL_STEPS:
        return
    if baseline:
        if drill_id and pid in baseline.get("drills", {}).get(drill_id, ()):
            return
        if bank_unit and pid in baseline.get("variants", {}).get(bank_unit, ()):
            return
    raise AiContractError(
        f"[{pid}] L2 problem has {n_steps} real step(s); new L2 problems need at least "
        f"{L2_MIN_REAL_STEPS} real steps (matching demand_level, rules/07 §4; repeated or restated steps do not count). "
        f"Expand the derivation into discrete transformations or relabel to L1."
    )


def collect_short_l2_problems(repo_root: Path) -> Tuple[Dict[str, List[Tuple[str, int]]], int]:
    """Return ``({drillId: [(qid, real_step_count), ...]}, total_l2_count)`` for canonical math drills."""
    from code_engine.sandbox import assert_safe_contained_path

    data_root = repo_root / "drills" / "data"
    short: Dict[str, List[Tuple[str, int]]] = {}
    total_l2 = 0
    if not data_root.is_dir():
        return short, total_l2
    for scope in sorted(data_root.iterdir()):
        if not scope.is_dir() or not scope.name.startswith("MTH-"):
            continue
        for path in sorted(scope.glob("*.json")):
            drill_file = assert_safe_contained_path(path, data_root, suffixes=(".json",))
            drill = json.loads(drill_file.read_text(encoding="utf-8"))
            did = str(drill.get("drillId") or path.stem)
            items: List[Tuple[str, int]] = []
            for idx, prob in enumerate(drill.get("problems") or [], 1):
                if not isinstance(prob, dict) or prob.get("level") != 2:
                    continue
                total_l2 += 1
                n_steps = count_real_steps(prob)
                if n_steps < L2_MIN_REAL_STEPS:
                    qid = str(prob.get("id") or f"Q{idx:02d}")
                    items.append((qid, n_steps))
            if items:
                short[did] = sorted(items)
    return short, total_l2


def collect_short_l2_variants(repo_root: Path) -> Tuple[Dict[str, List[Tuple[str, int]]], int]:
    """Return ``({unitCode: [(variantId, real_step_count), ...]}, total_l2_variants)`` for math variant banks."""
    from code_engine.sandbox import assert_safe_contained_path

    variants_root = repo_root / "drills" / "variants"
    short: Dict[str, List[Tuple[str, int]]] = {}
    total_l2 = 0
    if not variants_root.is_dir():
        return short, total_l2
    for path in sorted(variants_root.glob("MTH-*.json")):
        bank_file = assert_safe_contained_path(path, variants_root, suffixes=(".json",))
        bank = json.loads(bank_file.read_text(encoding="utf-8"))
        uc = str(bank.get("unitCode") or path.stem)
        items: List[Tuple[str, int]] = []
        for idx, var in enumerate(bank.get("variants") or [], 1):
            if not isinstance(var, dict) or var.get("level") != 2:
                continue
            total_l2 += 1
            n_steps = count_real_steps(var)
            if n_steps < L2_MIN_REAL_STEPS:
                vid = str(var.get("variantId") or var.get("id") or f"V{idx:02d}")
                items.append((vid, n_steps))
        if items:
            short[uc] = sorted(items)
    return short, total_l2


def check_l2_step_floor_gate(repo_root: Optional[Path] = None) -> Tuple[bool, str]:
    """Check canonical math drills and variant banks against the shrink-only L2 step-floor baseline (zero-leak)."""
    root = repo_root or _repo_root()
    try:
        baseline = load_l2_step_floor_baseline(root)
    except AiContractError as exc:
        return False, f"FAIL L2 step floor gate: invalid {L2_STEP_FLOOR_BASELINE_PATH}. {exc}"
    drills_base = baseline["drills"]
    variants_base = baseline["variants"]

    expected_drills = {(drill, qid) for drill, qids in drills_base.items() for qid in qids}
    short_by_drill, total_l2_drills = collect_short_l2_problems(root)
    actual_drills = {(drill, qid): n_steps for drill, entries in short_by_drill.items() for qid, n_steps in entries}
    new_drills = actual_drills.keys() - expected_drills
    stale_drills = expected_drills - actual_drills.keys()

    expected_vars = {(bank, vid) for bank, vids in variants_base.items() for vid in vids}
    short_by_bank, total_l2_vars = collect_short_l2_variants(root)
    actual_vars = {(bank, vid): n_steps for bank, entries in short_by_bank.items() for vid, n_steps in entries}
    new_vars = actual_vars.keys() - expected_vars
    stale_vars = expected_vars - actual_vars.keys()

    passed = not (new_drills or stale_drills or new_vars or stale_vars)
    lines = [
        f"{'PASS' if passed else 'FAIL'} L2 step floor gate "
        f"(minimum {L2_MIN_REAL_STEPS} real steps per L2 item; "
        f"drills {len(actual_drills)}/{total_l2_drills} short, variants {len(actual_vars)}/{total_l2_vars} short)."
    ]
    for drill, qid in sorted(actual_drills.keys()):
        n_steps = actual_drills[(drill, qid)]
        status = "FAIL New short L2 problem" if (drill, qid) in new_drills else "Baseline short L2 problem"
        lines.append(f"{status}: {drill} {qid} ({n_steps} real steps, need >= {L2_MIN_REAL_STEPS}).")
    for bank, vid in sorted(actual_vars.keys()):
        n_steps = actual_vars[(bank, vid)]
        status = "FAIL New short L2 variant" if (bank, vid) in new_vars else "Baseline short L2 variant"
        lines.append(f"{status}: {bank} {vid} ({n_steps} real steps, need >= {L2_MIN_REAL_STEPS}).")
    if new_drills or new_vars:
        lines.append("Expand new L2 items to >= 4 real steps or relabel to L1. Adding baseline entries is forbidden.")
    for drill, qid in sorted(stale_drills):
        lines.append(
            f"FAIL Stale drill baseline entry: {drill} {qid} now meets the L2 step floor or no longer exists. "
            f'Delete "{qid}" under drills.{drill} in {L2_STEP_FLOOR_BASELINE_PATH}.'
        )
    for bank, vid in sorted(stale_vars):
        lines.append(
            f"FAIL Stale variant baseline entry: {bank} {vid} now meets the L2 step floor or no longer exists. "
            f'Delete "{vid}" under variants.{bank} in {L2_STEP_FLOOR_BASELINE_PATH}.'
        )
    if stale_drills or stale_vars:
        lines.append("Remove any drill or bank key left with an empty list.")
    lines.append(
        f"Baseline: {len(drills_base)} drill(s), {len(expected_drills)} problem(s); "
        f"{len(variants_base)} bank(s), {len(expected_vars)} variant(s)."
    )
    return passed, "\n".join(lines)


def _run_problem_gates(
    prob: Dict[str, Any],
    archetypes: List[Dict[str, Any]],
    unit_code: str,
    rules: Dict[str, Any],
    *,
    errors: Optional[List[str]] = None,
    prepare_for_ingest: Optional[Callable[[Dict[str, Any]], None]] = None,
    enforce_l2_step_floor: bool = True,
    drill_id: Optional[str] = None,
    bank_unit: Optional[str] = None,
    l2_baseline: Optional[Dict[str, Dict[str, List[str]]]] = None,
) -> None:
    """Run vault/review and figure/verification gates in order.

    Checks collect one failure from each group and allow an absent review. Ingest
    stops at the first failure and fills references after the vault gate passes.
    """
    try:
        validate_against_vault(prob, archetypes, unit_code)
        if prepare_for_ingest is not None:
            prepare_for_ingest(prob)
        if errors is None or "review" in prob:
            validate_review(prob)
    except AiContractError as exc:
        if errors is None:
            raise
        errors.append(str(exc))

    try:
        require_figure_decision(prob, archetypes)
        autofill_problem_figure(prob, archetypes)
        require_figure_if_declared(prob, archetypes)
        validate_ai_problem_contract(prob)
        if enforce_l2_step_floor:
            validate_l2_step_floor(prob, drill_id=drill_id, bank_unit=bank_unit, baseline=l2_baseline)
        verify_problem(prob, rules=rules)
    except Exception as exc:  # noqa: BLE001 - checks report each gate failure
        if errors is None:
            raise
        pid, msg = prob["id"], str(exc)
        errors.append(msg if pid in msg else f"[{pid}] {msg}")


def check_ai_drill(
    drill_doc: Dict[str, Any],
    rules: Optional[Dict[str, Any]] = None,
    vault_dir: Optional[str] = None,
    check_originality: bool = False,
    sources_dir: Optional[str] = None,
    eligible_units: Optional[Iterable[str]] = None,
    *,
    check_step_math: bool = True,
    allow_l2_baseline: bool = False,
) -> List[str]:
    """Run every ingest gate on a draft WITHOUT saving it or touching the vault.

    Returns all problems' errors at once (empty list = ready to ingest), so a draft
    can be fixed in one pass instead of one error per run. The CLI disables
    ``check_step_math`` and enables ``allow_l2_baseline`` when rechecking a saved drill.
    """
    unit_code = drill_doc.get("unitCode")
    if not unit_code:
        return ["Drill document must specify 'unitCode'."]
    problems = drill_doc.get("problems") or []
    if not problems:
        return ["Drill document has no 'problems'."]

    vault_archs = load_scope_archetypes(unit_code, vault_dir=vault_dir, eligible_units=eligible_units)
    drill_id = str(drill_doc.get("drillId") or "").strip() or None
    l2_baseline = load_l2_step_floor_baseline() if (allow_l2_baseline and drill_id) else None
    errors: List[str] = []
    checked: List[Dict[str, Any]] = []
    for idx, original in enumerate(problems, 1):
        prob = copy.deepcopy(original)
        checked.append(prob)
        ingest_core.set_problem_defaults(prob, idx)
        if check_step_math:
            errors.extend(_step_math_errors(prob))
        _run_problem_gates(
            prob,
            vault_archs,
            unit_code,
            rules or QUALITY_RULES,
            errors=errors,
            enforce_l2_step_floor=True,
            drill_id=drill_id if allow_l2_baseline else None,
            l2_baseline=l2_baseline,
        )
    try:
        check_gate_g3_set(checked, rules=rules or QUALITY_RULES)
    except QualityError as exc:
        errors.append(str(exc))
    if check_originality:
        orig_errors, _ = check_document_originality(drill_doc, unit_code=unit_code, sources_dir=sources_dir)
        errors.extend(orig_errors)
    return list(dict.fromkeys(errors))


def _originality_skip_reason(
    doc: Dict[str, Any],
    *,
    unit_code: str,
    sources_dir: str,
) -> Optional[str]:
    """Return a skip reason when originality cannot run for ``doc`` under ``sources_dir``, else None."""
    if not os.path.isdir(sources_dir):
        return f"sources directory not found ({sources_dir})"
    pages = load_located_source_pages(unit_code, sources_dir=sources_dir)
    if unit_code == BRIDGE_SCOPE or not pages:
        raw_items = doc.get("problems") or doc.get("variants") or []
        seen_u: Set[str] = set()
        for prob in raw_items:
            if not isinstance(prob, dict):
                continue
            for candidate in [*(prob.get("unitCodes") or []), *(prob.get("references") or [])]:
                if (
                    isinstance(candidate, str)
                    and "-U" in candidate
                    and candidate not in seen_u
                    and candidate != unit_code
                ):
                    seen_u.add(candidate)
                    if load_located_source_pages(candidate, sources_dir=sources_dir):
                        return None
    if not pages:
        return f"no cached located source pages for {unit_code} under {index_dir(sources_dir)}"
    return None


def _generic_skip_reason(reason: str) -> str:
    if reason.startswith("no cached located source pages"):
        return "no cached located source pages under sources/_index"
    if reason.startswith("sources directory not found"):
        return "sources directory not found"
    return reason


def summarize_originality_skips(
    repo_root: Optional[Path] = None,
    *,
    sources_dir: Optional[str] = None,
    data_root: Optional[str] = None,
    variants_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Read-only summary of how many canonical math drills and variant banks skip originality and why."""
    from code_engine.sandbox import assert_safe_contained_path

    root = repo_root or Path(__file__).resolve().parents[1]
    sdir = resolve_sources_dir(sources_dir=sources_dir)
    droot = Path(data_root) if data_root else (root / DEFAULT_DATA_ROOT)
    vroot = Path(variants_dir) if variants_dir else (root / "drills" / "variants")

    drills_total = 0
    drills_skipped = 0
    drill_reasons: Dict[str, int] = {}
    skipped_drills: List[Dict[str, str]] = []
    if droot.is_dir():
        for scope in sorted(droot.iterdir()):
            if not scope.is_dir() or not scope.name.startswith("MTH-"):
                continue
            for path in sorted(scope.glob("*.json")):
                drill_file = assert_safe_contained_path(path, droot, suffixes=(".json",))
                doc = json.loads(drill_file.read_text(encoding="utf-8"))
                did = str(doc.get("drillId") or path.stem)
                uc = str(doc.get("unitCode") or scope.name)
                drills_total += 1
                reason = _originality_skip_reason(doc, unit_code=uc, sources_dir=sdir)
                if reason:
                    drills_skipped += 1
                    bucket = _generic_skip_reason(reason)
                    drill_reasons[bucket] = drill_reasons.get(bucket, 0) + 1
                    skipped_drills.append({"drillId": did, "unitCode": uc, "reason": reason})

    banks_total = 0
    banks_skipped = 0
    variants_total = 0
    variants_skipped = 0
    bank_reasons: Dict[str, int] = {}
    skipped_banks: List[Dict[str, Any]] = []
    if vroot.is_dir():
        for path in sorted(vroot.glob("MTH-*.json")):
            bank_file = assert_safe_contained_path(path, vroot, suffixes=(".json",))
            doc = json.loads(bank_file.read_text(encoding="utf-8"))
            uc = str(doc.get("unitCode") or path.stem)
            n_vars = len([v for v in (doc.get("variants") or []) if isinstance(v, dict)])
            banks_total += 1
            variants_total += n_vars
            reason = _originality_skip_reason(doc, unit_code=uc, sources_dir=sdir)
            if reason:
                banks_skipped += 1
                variants_skipped += n_vars
                bucket = _generic_skip_reason(reason)
                bank_reasons[bucket] = bank_reasons.get(bucket, 0) + 1
                skipped_banks.append({"unitCode": uc, "variantCount": n_vars, "reason": reason})

    return {
        "sourcesDir": sdir,
        "sourcesDirExists": os.path.isdir(sdir),
        "drills": {
            "total": drills_total,
            "checked": drills_total - drills_skipped,
            "skipped": drills_skipped,
            "skipReasons": drill_reasons,
            "skippedIds": [d["drillId"] for d in skipped_drills],
        },
        "variantBanks": {
            "total": banks_total,
            "checked": banks_total - banks_skipped,
            "skipped": banks_skipped,
            "variantsTotal": variants_total,
            "variantsChecked": variants_total - variants_skipped,
            "variantsSkipped": variants_skipped,
            "skipReasons": bank_reasons,
            "skippedBanks": skipped_banks,
        },
    }


def format_originality_summary(summary: Dict[str, Any]) -> str:
    """Format ``summarize_originality_skips`` output as a concise read-only gate summary."""
    d = summary["drills"]
    b = summary["variantBanks"]
    lines = [
        f"Originality gate summary (sources: {summary['sourcesDir']})",
        f"  Drills: {d['checked']}/{d['total']} checked, {d['skipped']}/{d['total']} skipped",
    ]
    for reason, count in sorted(d["skipReasons"].items()):
        lines.append(f"    - skipped ({count}): {reason}")
    lines.append(
        f"  Variant banks: {b['checked']}/{b['total']} checked, {b['skipped']}/{b['total']} skipped "
        f"({b['variantsSkipped']}/{b['variantsTotal']} variants skipped)"
    )
    for reason, count in sorted(b["skipReasons"].items()):
        lines.append(f"    - skipped ({count}): {reason}")
    return "\n".join(lines)


def check_ai_drill_report(
    drill_doc: Dict[str, Any],
    rules: Optional[Dict[str, Any]] = None,
    vault_dir: Optional[str] = None,
    check_originality: bool = True,
    sources_dir: Optional[str] = None,
    eligible_units: Optional[Iterable[str]] = None,
    *,
    check_step_math: bool = True,
) -> Dict[str, Any]:
    """Run all gates and return structured errors, warnings, and originality skip status."""
    errors = check_ai_drill(
        drill_doc,
        rules=rules,
        vault_dir=vault_dir,
        check_originality=False,
        eligible_units=eligible_units,
        check_step_math=check_step_math,
    )
    warnings = check_ai_drill_warnings(drill_doc, vault_dir=vault_dir, eligible_units=eligible_units)
    n_probs = len(drill_doc.get("problems") or [])
    unit_code = drill_doc.get("unitCode") or ""
    if not check_originality:
        orig = {
            "status": "skipped",
            "checkedDrills": 0,
            "skippedDrills": 1,
            "reason": "disabled by --no-originality",
            "errors": [],
        }
    else:
        resolved_sources = resolve_sources_dir(sources_dir=sources_dir)
        if not os.path.isdir(resolved_sources):
            orig = {
                "status": "skipped",
                "checkedDrills": 0,
                "skippedDrills": 1,
                "reason": f"sources directory not found ({resolved_sources})",
                "errors": [],
            }
        else:
            orig_errors, orig_notice = check_document_originality(
                drill_doc,
                unit_code=unit_code,
                sources_dir=resolved_sources,
            )
            if orig_notice:
                orig = {
                    "status": "skipped",
                    "checkedDrills": 0,
                    "skippedDrills": 1,
                    "reason": orig_notice,
                    "errors": orig_errors,
                }
            else:
                orig = {
                    "status": "checked",
                    "checkedDrills": 1,
                    "skippedDrills": 0,
                    "reason": None,
                    "errors": orig_errors,
                }
            errors = list(dict.fromkeys([*errors, *orig_errors]))
    return {
        "problemCount": n_probs,
        "errors": errors,
        "warnings": warnings,
        "originality": orig,
    }


def check_ai_drill_warnings(
    drill_doc: Dict[str, Any],
    vault_dir: Optional[str] = None,
    eligible_units: Optional[Iterable[str]] = None,
) -> List[str]:
    """Return non-blocking ingest warnings (such as method-naming figure titles or unverifiable option provenance) without mutating ``drill_doc``."""
    unit_code = drill_doc.get("unitCode")
    problems = drill_doc.get("problems") or []
    if not unit_code or not problems:
        return []
    vault_archs = load_scope_archetypes(unit_code, vault_dir=vault_dir, eligible_units=eligible_units)
    checked: List[Dict[str, Any]] = []
    prov_warnings: List[str] = []
    for idx, original in enumerate(problems, 1):
        prob = copy.deepcopy(original)
        prob.setdefault("id", f"Q{idx:02d}")
        autofill_problem_figure(prob, vault_archs)
        checked.append(prob)
        _, p_warns = check_distractor_provenance(prob, vault_archs)
        prov_warnings.extend(p_warns)
    return list(dict.fromkeys([*collect_figure_title_warnings(checked), *prov_warnings]))


def _populate_problem_references(
    prob: Dict[str, Any], *, unit_code: str, archetypes: List[Dict[str, Any]], id_map: Dict[str, Any]
) -> None:
    arch = next((a for a in archetypes if a.get("archetypeKey") == prob.get("archetypeKey")), None)
    if unit_code == BRIDGE_SCOPE and arch:
        arch_units = list(
            dict.fromkeys(u.strip() for u in (arch.get("unitCodes") or []) if isinstance(u, str) and u.strip())
        )
        prob["unitCodes"] = arch_units
        existing_refs = [r.strip() for r in (prob.get("references") or []) if isinstance(r, str) and r.strip()]
        prob["references"] = list(dict.fromkeys([*arch_units, *existing_refs]))
    else:
        ingest_core.populate_archetype_unit(prob, arch)

    refs = prob.get("references")
    if refs and not prob.get("referenceBadges") and id_map:
        badges = []
        for ref in refs:
            entry = id_map.get(ref, {})
            title = entry.get("title", ref) if isinstance(entry, dict) else ref
            raw_id = (entry.get("id", "") if isinstance(entry, dict) else str(entry)).replace("-", "")
            notion_url = f"https://www.notion.so/{raw_id}" if raw_id else None
            badges.append({"code": ref, "title": title, "notionUrl": notion_url})
        prob["referenceBadges"] = badges


def ingest_ai_drill(
    drill_doc: Dict[str, Any],
    data_root: Optional[str] = None,
    rules: Optional[Dict[str, Any]] = None,
    vault_dir: Optional[str] = None,
    eligible_units: Optional[Iterable[str]] = None,
    variants_dir: Optional[str] = None,
    warn_coverage: bool = True,
) -> Dict[str, Any]:
    """
    Verifies every problem in an AI-generated drill document using Machine Quality Gates G1–G6,
    assigns an official drill ID, and saves to drills/data/<unit_code>/<drill_id>.json.
    """
    if data_root is None:
        data_root = os.environ.get("DRILLS_DATA_DIR", DEFAULT_DATA_ROOT)

    unit_code = drill_doc.get("unitCode")
    if not unit_code:
        raise ValueError("Drill document must specify 'unitCode'.")

    problems = drill_doc.get("problems", [])
    if not problems:
        raise ValueError("Drill document has no 'problems'.")

    active_rules = rules or QUALITY_RULES

    id_map = {}
    id_map_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "id_map.json")
    try:
        id_map = ingest_core.load_id_map(id_map_path)
    except Exception:
        pass

    vault_archs = load_scope_archetypes(unit_code, vault_dir=vault_dir, eligible_units=eligible_units)
    prepare = partial(_populate_problem_references, unit_code=unit_code, archetypes=vault_archs, id_map=id_map)

    for idx, prob in enumerate(problems, 1):
        ingest_core.set_problem_defaults(prob, idx)
        if step_errors := list(_step_math_errors(prob)):
            raise AiContractError("\n".join(step_errors))
        _run_problem_gates(prob, vault_archs, unit_code, active_rules, prepare_for_ingest=prepare)

    # G3: no two problems in the drill share a structural fingerprint.
    check_gate_g3_set(problems, rules=active_rules)

    drill_id = ingest_core.ensure_drill_id(drill_doc, unit_code, data_root, next_drill_id)

    if not drill_doc.get("unitTitle"):
        try:
            drill_doc["unitTitle"] = ingest_core.load_unit_title(unit_code, id_map_path)
        except Exception:
            pass

    if not drill_doc.get("unitTitle"):
        drill_doc["unitTitle"] = (
            BRIDGE_TITLE if unit_code == BRIDGE_SCOPE else (drill_doc.get("topicTitle") or unit_code)
        )

    if not drill_doc.get("title"):
        drill_doc["title"] = f"{drill_doc['unitTitle']} — Verified Math Drill ({len(problems)} Qs)"

    ingest_core.populate_hierarchy(drill_doc, unit_hierarchy(unit_code))
    for prob in problems:
        ingest_core.populate_level_label(prob, LEVEL_LABELS)

    ingest_core.finalize_drill_metadata(
        drill_doc,
        len(problems),
        "AI Synthesized Reasoning Mode",
        defaults={"schemaVersion": "2.0-math", "subject": "MATH"},
    )

    unit_dir = os.path.join(data_root, unit_code)
    os.makedirs(unit_dir, exist_ok=True)
    file_path = os.path.join(unit_dir, f"{drill_id}.json")
    drill_doc["localFilePath"] = file_path

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(drill_doc, f, ensure_ascii=False, indent=2)

    ingest_core.rotate_problem_contexts(
        problems, partial(mark_context_used, unit_code, vault_dir=vault_dir, eligible_units=eligible_units)
    )

    print(f"  [AI Verified & Saved] {file_path} ({len(problems)} problems)")
    prov_warnings: List[str] = []
    for prob in problems:
        _, p_warns = check_distractor_provenance(prob, vault_archs)
        prov_warnings.extend(p_warns)
    for warn in list(dict.fromkeys([*collect_figure_title_warnings(problems), *prov_warnings])):
        print(f"WARNING: {warn}")
    if warn_coverage:
        from math_engine.variant_bank import format_coverage_warning

        cov_warning = format_coverage_warning(drill_doc, variants_dir=variants_dir, drill_path=file_path)
        if cov_warning:
            print(cov_warning)
    return drill_doc


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest AI-generated drill or inspect Reasoning Vault.")
    parser.add_argument("--unit", default="MTH-T01-C06", help="Unit code (e.g. MTH-T01-C06)")
    parser.add_argument("--list-vault", action="store_true", help="List registered reasoning archetypes")
    parser.add_argument("--ingest-file", help="Path to JSON file containing AI-generated drill document")
    parser.add_argument(
        "--check",
        action="store_true",
        help="With --ingest-file: run all gates and list every error; save nothing, do not touch the vault.",
    )
    parser.add_argument(
        "--originality",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="With --check: run the source originality gate (default: ON when sources dir exists, skipped with a notice when absent).",
    )
    parser.add_argument(
        "--sources-dir",
        default=None,
        help="Override sources directory for --originality (default: LEARNINGOS_SOURCES_DIR or <main>/sources).",
    )
    parser.add_argument(
        "--l2-step-gate",
        action="store_true",
        help="Check canonical math drills and variant banks against the shrink-only L2 step-floor baseline (>= 4 real steps).",
    )
    parser.add_argument(
        "--originality-summary",
        action="store_true",
        help="Read-only summary of how many math drills and variant banks skip the originality gate and why.",
    )
    parser.add_argument("--json", action="store_true", help="With --originality-summary: print structured JSON output.")
    args = parser.parse_args(argv)

    if args.l2_step_gate:
        root = Path.cwd() if (Path.cwd() / L2_STEP_FLOOR_BASELINE_PATH).is_file() else _repo_root()
        passed, report = check_l2_step_floor_gate(root)
        print(report)
        return 0 if passed else 1

    if args.originality_summary:
        summary = summarize_originality_skips(sources_dir=args.sources_dir)
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print(format_originality_summary(summary))
        return 0

    if args.list_vault:
        archs = load_scope_archetypes(args.unit)
        print(f"\nReasoning Vault for {args.unit}: {len(archs)} archetypes")
        if args.unit == BRIDGE_SCOPE and not archs:
            print("  (none eligible — run `python -m scripts.bridge_scope` to check passed units)")
        for a in archs:
            if args.unit == BRIDGE_SCOPE:
                units_label = " + ".join(a.get("unitCodes") or [])
                print(f"  [{a.get('level', 3)}] {a.get('archetypeKey')} ({units_label}): {a.get('name', '')}")
                print(f"      Junction: {a.get('junction')}")
            else:
                print(f"  [{a.get('level', 1)}] {a.get('archetypeKey')} ({archetype_owner(a)}): {a.get('name')}")
                print(f"      Governing: {a.get('governingRelation')}")
            print(f"      Used Contexts: {a.get('usedContexts', [])}")
            figs = list(dict.fromkeys(b.get("fn") for b in a.get("figureBuilders") or []))
            decision = ", ".join(figs) if figs else (f"none ({a['figureNone']})" if a.get("figureNone") else None)
            print(f"      Figure: {decision or 'UNDECIDED - add figureBuilders or figureNone (rules/03 §3.1)'}")

    if args.ingest_file:
        with open(args.ingest_file, "r", encoding="utf-8") as f:
            drill_data = json.load(f)
        if args.check:
            input_path = Path(args.ingest_file).resolve()
            data_roots = (
                Path(__file__).resolve().parents[1] / DEFAULT_DATA_ROOT,
                Path(os.environ.get("DRILLS_DATA_DIR", DEFAULT_DATA_ROOT)).resolve(),
            )
            is_saved = any(input_path.is_relative_to(root) for root in data_roots)
            problems_found = check_ai_drill(drill_data, check_step_math=not is_saved, allow_l2_baseline=is_saved)
            fig_warnings = check_ai_drill_warnings(drill_data)
            resolved_sources = resolve_sources_dir(sources_dir=args.sources_dir)
            orig_skip_reason: Optional[str] = None
            if args.originality is False:
                orig_skip_reason = "disabled by --no-originality"
            elif not os.path.isdir(resolved_sources):
                orig_skip_reason = f"sources directory not found ({resolved_sources})"
                print(f"NOTE: Originality gate skipped (sources directory not found: {resolved_sources}).")
            else:
                orig_errors, orig_notice = check_document_originality(
                    drill_data,
                    unit_code=drill_data.get("unitCode") or args.unit,
                    sources_dir=resolved_sources,
                )
                if orig_notice:
                    orig_skip_reason = orig_notice
                    print(f"NOTE: {orig_notice}")
                problems_found.extend(orig_errors)
            for warn in fig_warnings:
                print(f"WARNING: {warn}")
            for line in problems_found:
                print(f"  FAIL {line}")
            n = len(drill_data.get("problems") or [])
            orig_tail = (
                f"originality skipped (1/1 drill skipped: {orig_skip_reason})"
                if orig_skip_reason
                else "originality checked (0/1 drill skipped)"
            )
            print(
                f"\n{len(problems_found)} error(s) across {n} problem(s); {orig_tail}."
                if problems_found
                else (
                    f"OK: all {n} problems pass {'checked gates' if orig_skip_reason else 'every gate'} "
                    f"(nothing saved); {orig_tail}."
                )
            )
            return 1 if problems_found else 0
        saved = ingest_ai_drill(drill_data, warn_coverage=False)
        print(f"Successfully verified and ingested drill: {saved.get('drillId')}")
        from math_engine.variant_bank import format_coverage_warning

        cov_warning = format_coverage_warning(saved, drill_path=saved.get("localFilePath"))
        if cov_warning:
            print(cov_warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
