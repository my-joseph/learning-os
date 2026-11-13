# -*- coding: utf-8 -*-
"""
AI Drill Ingestion & Reasoning Vault Engine:
Bridges dynamic AI-generated problems in chat into:
1. The Reasoning Vault (math_engine/reasoning_vault/<unit_code>.json)
2. Verified local Drill JSON files (drills/data/<unit_code>/DRL-....json)
"""

import argparse
import datetime
import json
import os
import re
from typing import Any, Dict, List, Optional

from math_engine.answer_check import CHECKERS, check_answer, is_equal, to_expr
from math_engine.figure_autofill import archetype_requires_figure, autofill_problem_figure
from math_engine.generate import next_drill_id
from math_engine.verify import verify_problem
from quality_rules import QUALITY_RULES

VAULT_DIR = os.path.join(os.path.dirname(__file__), "reasoning_vault")


class AiContractError(Exception):
    """Raised when an AI-generated problem violates Contract 07 §4 or 00_core §6."""

    pass


def normalize_prompt_numbers(prompt: str, keep_exponents: bool = False) -> List[float]:
    """Extracts numbers from prompt text, handling commas in numbers and removing unit exponents."""
    text = prompt
    while re.search(r"(\d+),(\d+)", text):
        text = re.sub(r"(\d+),(\d+)", r"\g<1>\g<2>", text)
    if not keep_exponents:
        text = re.sub(r"\^\{?[23]\}?", "", text)
    # Separate numeric coefficients from variables, units, and LaTeX macros (e.g. 3x -> 3 x, 4\theta -> 4 \theta, 15m -> 15 m)
    text = re.sub(r"(?<=\d)(?=[a-zA-Z\\])", " ", text)
    raw_nums = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    nums = []
    for r in raw_nums:
        try:
            nums.append(float(r))
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
_LATEX_OPS = (r"\times", r"\cdot", r"\div", r"\frac", r"\left", r"\right", r"\,", r"\;", r"\quad")


def _normalize_math(expr: str) -> str:
    s = expr
    for macro, repl in ((r"\times", "*"), (r"\cdot", "*"), (r"\div", "/")):
        s = s.replace(macro, repl)
    for macro in (r"\left", r"\right", r"\,", r"\;", r"\quad"):
        s = s.replace(macro, "")
    return re.sub(r"\s+", "", s)


def _is_numeric_computation(expr: str) -> bool:
    """True for things like `2(14) + 2(8)`, `\\frac{80}{16}`, `6 + 8`: digits plus an operator, no letters."""
    s = expr.replace("?", "")
    for macro in _LATEX_OPS:
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

    prompt = prob.get("prompt", "")
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

    # Forward: every number in prompt must be defined in givens (or be a declared constant)
    known_vals = list(givens_floats.values()) + list(constant_floats.values())
    for p_num in prompt_numbers:
        if not any(abs(p_num - g_val) < 1e-6 for g_val in known_vals):
            raise AiContractError(f"[{pid}] Number '{p_num}' in prompt is not defined in givens ({givens})")

    # Backward: every given must appear in prompt. Exponents count here ($2^3$ states the 3),
    # otherwise the AI is pushed to re-list them ("with first exponent 3 ...").
    prompt_numbers_all = normalize_prompt_numbers(prompt, keep_exponents=True)
    for g_key, g_val in givens_floats.items():
        if not any(abs(g_val - p_num) < 1e-6 for p_num in prompt_numbers_all):
            raise AiContractError(f"[{pid}] Given '{g_key}={g_val}' does not appear in prompt: '{prompt}'")

    # 4. Trap derivation integrity via Safe Parser (to_expr + is_equal)
    td = prob.get("trapDerivation")
    tv = prob.get("verify", {}).get("trapValue") or prob.get("trapValue")
    if not td or tv is None:
        raise AiContractError(f"[{pid}] Missing trapDerivation or trapValue.")

    if re.fullmatch(r"^\s*[-+]?\d*\.?\d+\s*$", str(td)):
        raise AiContractError(f"[{pid}] trapDerivation '{td}' cannot be a bare number.")

    vars_list = prob.get("answerSpec", {}).get("variables") or prob.get("variables") or ["x"]
    td_expr = to_expr(str(td), variables=vars_list, trusted=True)
    tv_expr = to_expr(str(tv), variables=vars_list, trusted=True)
    if not is_equal(td_expr, tv_expr, variables=vars_list):
        raise AiContractError(f"[{pid}] trapDerivation '{td}' evaluates to {td_expr} != trapValue '{tv}' ({tv_expr})")

    # Check that at least 2 distinct givens appear in trapDerivation
    td_tokens = re.findall(r"\b\d+(?:\.\d+)?\b", str(td))
    td_token_vals = [float(t) for t in td_tokens]

    matched_given_keys = set()
    # A trap may misuse a formula constant (e.g. 2 + r instead of 2r), so constants count too.
    for g_key, g_val in {**givens_floats, **constant_floats}.items():
        for t_val in td_token_vals:
            if abs(t_val - g_val) < 1e-6:
                matched_given_keys.add(g_key)
                break
            if abs(t_val - (g_val / 100.0)) < 1e-6:
                matched_given_keys.add(g_key)
                break

    if len(matched_given_keys) < 2:
        raise AiContractError(
            f"[{pid}] trapDerivation '{td}' must contain at least 2 distinct givens from {givens}, found {len(matched_given_keys)}: {matched_given_keys}"
        )

    # 5. Check answer simulation and trap matching across answer types
    spec = prob.get("answerSpec", {})
    if spec and "type" in spec:
        chk = check_answer(spec, str(tv))
        if chk.get("verdict") == "correct":
            raise AiContractError(f"[{pid}] trapValue '{tv}' evaluated as correct by check_answer!")

        spec_type = spec.get("type")
        trap_spec = dict(spec)
        if spec_type in ("number", "expression", "complex"):
            trap_spec["value"] = str(tv)
        elif spec_type == "vector":
            trap_spec["value"] = tv
            trap_spec.pop("components", None)
            trap_spec.pop("values", None)
        elif spec_type == "tuple":
            if isinstance(tv, (list, tuple)):
                trap_spec["values"] = list(tv)
            elif isinstance(tv, str):
                parts = [p.strip() for p in re.sub(r"^\s*[\(\[\{<]|[\)\]\}>]\s*$", "", tv).split(",") if p.strip()]
                trap_spec["values"] = parts
            else:
                trap_spec["values"] = [tv]

        fn = CHECKERS.get(spec_type)
        if fn:
            trap_chk = fn(trap_spec, str(tv))
            if trap_chk.get("verdict") != "correct":
                raise AiContractError(f"[{pid}] trapValue '{tv}' failed trap checker match.")

    # 6. Display LaTeX and plainText integrity for math problems (prevent undefined/unrendered equation bugs)
    display = prob.get("display")
    if not display or not isinstance(display, str) or not display.strip():
        raise AiContractError(f"[{pid}] Math problem must provide a non-empty LaTeX 'display' equation.")

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


def get_vault_path(unit_code: str, vault_dir: Optional[str] = None) -> str:
    dir_path = vault_dir or os.environ.get("REASONING_VAULT_DIR") or VAULT_DIR
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{unit_code}.json")


def load_reasoning_vault(unit_code: str, vault_dir: Optional[str] = None) -> Dict[str, Any]:
    path = get_vault_path(unit_code, vault_dir=vault_dir)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"unitCode": unit_code, "archetypes": []}


def save_reasoning_vault(unit_code: str, vault_data: Dict[str, Any], vault_dir: Optional[str] = None) -> str:
    path = get_vault_path(unit_code, vault_dir=vault_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vault_data, f, indent=2, ensure_ascii=False)
    return path


def register_archetype(unit_code: str, archetype: Dict[str, Any], vault_dir: Optional[str] = None) -> Dict[str, Any]:
    """Adds or updates a reasoning archetype in the unit's Reasoning Vault."""
    vault = load_reasoning_vault(unit_code, vault_dir=vault_dir)
    archetypes = vault.get("archetypes", [])
    key = archetype.get("archetypeKey")
    if not key:
        raise ValueError("Archetype must have an 'archetypeKey'.")

    idx = next((i for i, a in enumerate(archetypes) if a.get("archetypeKey") == key), -1)
    if idx >= 0:
        # Merge existing, preserving usedContexts
        existing = archetypes[idx]
        used = existing.get("usedContexts", [])
        archetype["usedContexts"] = list(dict.fromkeys(used + archetype.get("usedContexts", [])))
        archetypes[idx] = archetype
    else:
        if "usedContexts" not in archetype:
            archetype["usedContexts"] = []
        archetypes.append(archetype)

    vault["archetypes"] = archetypes
    save_reasoning_vault(unit_code, vault, vault_dir=vault_dir)
    return archetype


def mark_context_used(unit_code: str, archetype_key: str, context_tag: str, vault_dir: Optional[str] = None) -> None:
    """Marks a context domain as used so future AI generations rotate to fresh domains."""
    vault = load_reasoning_vault(unit_code, vault_dir=vault_dir)
    for a in vault.get("archetypes", []):
        if a.get("archetypeKey") == archetype_key:
            used = a.get("usedContexts", [])
            if context_tag not in used:
                used.append(context_tag)
                a["usedContexts"] = used
            break
    save_reasoning_vault(unit_code, vault, vault_dir=vault_dir)


def ingest_ai_drill(
    drill_doc: Dict[str, Any],
    data_root: Optional[str] = None,
    rules: Optional[Dict[str, Any]] = None,
    vault_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verifies every problem in an AI-generated drill document using Machine Quality Gates G1–G6,
    assigns an official drill ID, and saves to drills/data/<unit_code>/<drill_id>.json.
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

    # Machine Verification of all problems
    id_map = {}
    id_map_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "id_map.json")
    if os.path.exists(id_map_path):
        try:
            with open(id_map_path, "r", encoding="utf-8") as f:
                id_map = json.load(f)
        except Exception:
            pass

    for idx, prob in enumerate(problems, 1):
        if "id" not in prob:
            prob["id"] = f"Q{idx:02d}"
        if "verificationLevel" not in prob:
            prob["verificationLevel"] = "partial"
        # Auto-resolve referenceBadges if references are provided
        refs = prob.get("references")
        if refs and not prob.get("referenceBadges") and id_map:
            badges = []
            for ref in refs:
                entry = id_map.get(ref, {})
                title = entry.get("title", ref) if isinstance(entry, dict) else ref
                raw_id = (entry.get("id", "") if isinstance(entry, dict) else str(entry)).replace("-", "")
                notion_url = f"https://www.notion.so/{raw_id}" if raw_id else None
                badges.append(
                    {
                        "code": ref,
                        "title": title,
                        "notionUrl": notion_url,
                    }
                )
            prob["referenceBadges"] = badges

        # Rule 11: auto-attach parametric figure from vault archetype `figureBuilders` (03_stem §3)
        vault_archs = load_reasoning_vault(unit_code, vault_dir=vault_dir).get("archetypes", [])
        autofill_problem_figure(prob, vault_archs)
        require_figure_if_declared(prob, vault_archs)
        validate_ai_problem_contract(prob)
        # Run gate checks (G1-G6)
        verify_problem(prob, rules=active_rules)

    drill_id = drill_doc.get("drillId")
    if not drill_id:
        drill_id = next_drill_id(unit_code, data_root=data_root)
        drill_doc["drillId"] = drill_id

    # Auto-resolve unitTitle from id_map.json if missing
    if not drill_doc.get("unitTitle"):
        id_map_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "id_map.json")
        if os.path.exists(id_map_path):
            try:
                with open(id_map_path, "r", encoding="utf-8") as f:
                    id_map = json.load(f)
                if unit_code in id_map and isinstance(id_map[unit_code], dict):
                    drill_doc["unitTitle"] = id_map[unit_code].get("title")
            except Exception:
                pass

    if not drill_doc.get("unitTitle"):
        drill_doc["unitTitle"] = drill_doc.get("topicTitle") or unit_code

    if not drill_doc.get("title"):
        drill_doc["title"] = f"{drill_doc['unitTitle']} — Verified Math Drill ({len(problems)} Qs)"

    drill_doc["schemaVersion"] = drill_doc.get("schemaVersion", "2.0-math")
    drill_doc["subject"] = drill_doc.get("subject", "MATH")
    drill_doc["createdAt"] = drill_doc.get("createdAt", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if "sourceAttribution" in drill_doc:
        drill_doc["sourceAttribution"] = drill_doc["sourceAttribution"]
    drill_doc["config"] = drill_doc.get(
        "config",
        {
            "questionCount": len(problems),
            "difficulty": "ALL",
            "difficultyMode": "AI Synthesized Reasoning Mode",
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

    unit_dir = os.path.join(data_root, unit_code)
    os.makedirs(unit_dir, exist_ok=True)
    file_path = os.path.join(unit_dir, f"{drill_id}.json")
    drill_doc["localFilePath"] = file_path

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(drill_doc, f, ensure_ascii=False, indent=2)

    # Rotate and update usedContexts in Reasoning Vault
    for prob in problems:
        arch_key = prob.get("archetypeKey")
        ctx = prob.get("context")
        if arch_key and ctx:
            mark_context_used(unit_code, arch_key, ctx, vault_dir=vault_dir)

    print(f"  [AI Verified & Saved] {file_path} ({len(problems)} problems)")
    return drill_doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest AI-generated drill or inspect Reasoning Vault.")
    parser.add_argument("--unit", default="MTH-T01-C06", help="Unit code (e.g. MTH-T01-C06)")
    parser.add_argument("--list-vault", action="store_true", help="List registered reasoning archetypes")
    parser.add_argument("--ingest-file", help="Path to JSON file containing AI-generated drill document")
    args = parser.parse_args()

    if args.list_vault:
        v = load_reasoning_vault(args.unit)
        print(f"\nReasoning Vault for {args.unit}: {len(v.get('archetypes', []))} archetypes")
        for a in v.get("archetypes", []):
            print(f"  [{a.get('level', 1)}] {a.get('archetypeKey')}: {a.get('name')}")
            print(f"      Governing: {a.get('governingRelation')}")
            print(f"      Used Contexts: {a.get('usedContexts', [])}")

    if args.ingest_file:
        with open(args.ingest_file, "r", encoding="utf-8") as f:
            drill_data = json.load(f)
        saved = ingest_ai_drill(drill_data)
        print(f"Successfully verified and ingested drill: {saved.get('drillId')}")
