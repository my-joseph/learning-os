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
from typing import Any, Dict, List, Optional

from math_engine.generate import next_drill_id
from math_engine.verify import verify_problem
from quality_rules import QUALITY_RULES

VAULT_DIR = os.path.join(os.path.dirname(__file__), "reasoning_vault")


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
            prob["verificationLevel"] = "machine-verified"
        # Run gate checks (G1-G6)
        verify_problem(prob, rules=active_rules)

    drill_id = drill_doc.get("drillId")
    if not drill_id:
        drill_id = next_drill_id(unit_code, data_root=data_root)
        drill_doc["drillId"] = drill_id

    drill_doc["schemaVersion"] = drill_doc.get("schemaVersion", "2.0-math")
    drill_doc["subject"] = drill_doc.get("subject", "MATH")
    drill_doc["createdAt"] = drill_doc.get(
        "createdAt", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
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
