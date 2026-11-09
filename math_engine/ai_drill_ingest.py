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

from math_engine.generate import next_drill_id
from math_engine.verify import verify_problem
from math_engine.answer_check import check_answer, CHECKERS, to_expr, is_equal
from quality_rules import QUALITY_RULES

VAULT_DIR = os.path.join(os.path.dirname(__file__), "reasoning_vault")


class AiContractError(Exception):
    """Raised when an AI-generated problem violates Contract 07 §4 or 00_core §6."""
    pass


def normalize_prompt_numbers(prompt: str) -> List[float]:
    """Extracts numbers from prompt text, handling commas in numbers and removing unit exponents."""
    text = prompt
    while re.search(r"(\d+),(\d+)", text):
        text = re.sub(r"(\d+),(\d+)", r"\g<1>\g<2>", text)
    text = re.sub(r"\^\{?[23]\}?", "", text)
    raw_nums = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    nums = []
    for r in raw_nums:
        try:
            nums.append(float(r))
        except ValueError:
            pass
    return nums


def validate_ai_problem_contract(prob: Dict[str, Any]) -> bool:
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

    # Forward: every number in prompt must be defined in givens
    for p_num in prompt_numbers:
        if not any(abs(p_num - g_val) < 1e-6 for g_val in givens_floats.values()):
            raise AiContractError(
                f"[{pid}] Number '{p_num}' in prompt is not defined in givens ({givens})"
            )

    # Backward: every given must appear in prompt
    for g_key, g_val in givens_floats.items():
        if not any(abs(g_val - p_num) < 1e-6 for p_num in prompt_numbers):
            raise AiContractError(
                f"[{pid}] Given '{g_key}={g_val}' does not appear in prompt: '{prompt}'"
            )

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
        raise AiContractError(
            f"[{pid}] trapDerivation '{td}' evaluates to {td_expr} != trapValue '{tv}' ({tv_expr})"
        )

    # Check that at least 2 distinct givens appear in trapDerivation
    td_tokens = re.findall(r"\b\d+(?:\.\d+)?\b", str(td))
    td_token_vals = [float(t) for t in td_tokens]

    matched_given_keys = set()
    for g_key, g_val in givens_floats.items():
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
                parts = [
                    p.strip()
                    for p in re.sub(r"^\s*[\(\[\{<]|[\)\]\}>]\s*$", "", tv).split(",")
                    if p.strip()
                ]
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

    return True


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


def save_reasoning_vault(
    unit_code: str, vault_data: Dict[str, Any], vault_dir: Optional[str] = None
) -> str:
    path = get_vault_path(unit_code, vault_dir=vault_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vault_data, f, indent=2, ensure_ascii=False)
    return path


def register_archetype(
    unit_code: str, archetype: Dict[str, Any], vault_dir: Optional[str] = None
) -> Dict[str, Any]:
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


def mark_context_used(
    unit_code: str, archetype_key: str, context_tag: str, vault_dir: Optional[str] = None
) -> None:
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
    for idx, prob in enumerate(problems, 1):
        if "id" not in prob:
            prob["id"] = f"Q{idx:02d}"
        if "verificationLevel" not in prob:
            prob["verificationLevel"] = "partial"
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
    drill_doc["createdAt"] = drill_doc.get(
        "createdAt", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
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
