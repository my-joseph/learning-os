"""Shared reasoning-vault storage and metadata for drill ingest."""

from __future__ import annotations

import datetime
import glob
import json
import os
from collections.abc import Callable, Iterable
from typing import Any

from math_engine.bridge import BRIDGE_SCOPE, MIN_BRIDGE_UNITS
from math_engine.drill_ids import load_id_map as load_id_map
from progress_store import strip_progress


def resolve_vault_dir(vault_dir: str | None, env_name: str, default: str) -> str:
    return vault_dir or os.environ.get(env_name) or default


def get_vault_path(unit_code: str, vault_dir: str) -> str:
    os.makedirs(vault_dir, exist_ok=True)
    return os.path.join(vault_dir, f"{unit_code}.json")


def load_reasoning_vault(unit_code: str, vault_dir: str) -> dict[str, Any]:
    path = get_vault_path(unit_code, vault_dir)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"unitCode": unit_code, "archetypes": []}


def save_reasoning_vault(unit_code: str, vault_data: dict[str, Any], vault_dir: str) -> str:
    path = get_vault_path(unit_code, vault_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vault_data, f, indent=2, ensure_ascii=False)
    return path


def archetype_owner(archetype: dict[str, Any]) -> str:
    """The unit or chapter an archetype belongs to, falling back to its vault file."""
    return archetype.get("unitCode") or archetype.get("_vaultFile", "")


def _read_vault_archetypes(path: str) -> list[dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("archetypes", [])
    except (OSError, ValueError):
        return []


def _load_bridge_archetypes(vault_dir: str, eligible_units: Iterable[str] | None) -> list[dict[str, Any]]:
    if eligible_units is None:
        from scripts.bridge_scope import eligible_units as load_eligible_units

        eligible_set = load_eligible_units()
    else:
        eligible_set = {u.strip() for u in eligible_units if isinstance(u, str) and u.strip()}
    if len(eligible_set) < MIN_BRIDGE_UNITS:
        return []

    found = []
    for archetype in _read_vault_archetypes(os.path.join(vault_dir, f"{BRIDGE_SCOPE}.json")):
        if not isinstance(archetype, dict):
            continue
        units = {u.strip() for u in (archetype.get("unitCodes") or []) if isinstance(u, str) and u.strip()}
        if len(units) >= MIN_BRIDGE_UNITS and units.issubset(eligible_set):
            found.append({**archetype, "_vaultFile": BRIDGE_SCOPE})
    return found


def load_scope_archetypes(
    code: str,
    vault_dir: str,
    *,
    math_scope: bool = False,
    eligible_units: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Read sorted vaults, attaching each matching archetype's file stem for context rotation."""
    if math_scope and code == BRIDGE_SCOPE:
        return _load_bridge_archetypes(vault_dir, eligible_units)

    found = []
    for path in sorted(glob.glob(os.path.join(vault_dir, "*.json"))):
        stem = os.path.basename(path)[:-5]
        if math_scope and stem == BRIDGE_SCOPE:
            continue
        for archetype in _read_vault_archetypes(path):
            entry = {**archetype, "_vaultFile": stem}
            owner = archetype_owner(entry)
            if owner == code or owner.startswith(code + "-U"):
                found.append(entry)
    return found


def register_archetype(unit_code: str, archetype: dict[str, Any], vault_dir: str) -> dict[str, Any]:
    """Add or replace an archetype, preserving its context history."""
    vault = load_reasoning_vault(unit_code, vault_dir)
    archetypes = vault.get("archetypes", [])
    key = archetype.get("archetypeKey")
    if not key:
        raise ValueError("Archetype must have an 'archetypeKey'.")

    for index, existing in enumerate(archetypes):
        if existing.get("archetypeKey") == key:
            used = existing.get("usedContexts", [])
            archetype["usedContexts"] = list(dict.fromkeys(used + archetype.get("usedContexts", [])))
            archetypes[index] = archetype
            break
    else:
        archetype.setdefault("usedContexts", [])
        archetypes.append(archetype)

    vault["archetypes"] = archetypes
    save_reasoning_vault(unit_code, vault, vault_dir)
    return archetype


def mark_context_used(
    unit_code: str,
    archetype_key: str,
    context_tag: str,
    vault_dir: str,
    scope_archetypes: Iterable[dict[str, Any]],
) -> None:
    """Record a context in the file holding the archetype, including chapter vaults."""
    holder = next((a["_vaultFile"] for a in scope_archetypes if a.get("archetypeKey") == archetype_key), unit_code)
    vault = load_reasoning_vault(holder, vault_dir)
    for archetype in vault.get("archetypes", []):
        if archetype.get("archetypeKey") == archetype_key:
            used = archetype.get("usedContexts", [])
            if context_tag not in used:
                used.append(context_tag)
                archetype["usedContexts"] = used
            break
    save_reasoning_vault(holder, vault, vault_dir)


def rotate_problem_contexts(problems: list[dict[str, Any]], mark_used: Callable[[str, str], None]) -> None:
    for prob in problems:
        key, context = prob.get("archetypeKey"), prob.get("context")
        if key and context:
            mark_used(key, context)


def archetype_trap_tags(archetype: dict[str, Any], *, normalize_legacy: bool = False) -> list[Any]:
    traps = archetype.get("cognitiveTraps") or []
    if normalize_legacy:
        traps = (t if isinstance(t, dict) else str(t) for t in traps if t)
    return [t.get("trapTag") if isinstance(t, dict) else t for t in traps]


def has_review_record(review: Any, verdicts: tuple[str, ...] = ("pass",)) -> bool:
    return (
        isinstance(review, dict) and review.get("verdict") in verdicts and bool(str(review.get("note") or "").strip())
    )


def load_unit_title(unit_code: str, id_map_path: str) -> Any:
    entry = load_id_map(id_map_path).get(unit_code)
    return entry.get("title") if isinstance(entry, dict) else None


def ensure_drill_id(
    drill_doc: dict[str, Any],
    unit_code: str,
    data_root: str,
    next_drill_id: Callable[..., str],
) -> str:
    drill_id = drill_doc.get("drillId")
    if not drill_id:
        drill_id = next_drill_id(unit_code, data_root=data_root)
        drill_doc["drillId"] = drill_id
    return drill_id


def set_problem_defaults(prob: dict[str, Any], index: int) -> None:
    prob.setdefault("id", f"Q{index:02d}")
    prob.setdefault("verificationLevel", "partial")


def populate_hierarchy(drill_doc: dict[str, Any], hierarchy: tuple[str, str]) -> None:
    for field, code in zip(("topicCode", "chapterCode"), hierarchy, strict=True):
        if not drill_doc.get(field):
            drill_doc[field] = code


def populate_level_label(prob: dict[str, Any], level_labels: dict[int, str]) -> None:
    if not prob.get("levelLabel") and prob.get("level") in level_labels:
        prob["levelLabel"] = level_labels[prob["level"]]


def populate_archetype_unit(prob: dict[str, Any], archetype: dict[str, Any] | None) -> None:
    if archetype and "-U" in (owner := archetype_owner(archetype)):
        prob.setdefault("unitCode", owner)


def finalize_drill_metadata(
    drill_doc: dict[str, Any], question_count: int, difficulty_mode: str, *, defaults: dict[str, str]
) -> None:
    """Apply engine-specific defaults and remove learner progress from drill content."""
    for field, value in defaults.items():
        drill_doc[field] = drill_doc.get(field, value)
    drill_doc["createdAt"] = drill_doc.get("createdAt", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    drill_doc["config"] = drill_doc.get(
        "config",
        {"questionCount": question_count, "difficulty": "ALL", "difficultyMode": difficulty_mode},
    )
    strip_progress(drill_doc)
