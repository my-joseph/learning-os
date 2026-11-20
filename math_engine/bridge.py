# -*- coding: utf-8 -*-
"""Cross-unit bridge problem schema validation, unit extraction, and problem gates.

Bridge archetypes live in ``math_engine/reasoning_vault/MTH-BRIDGE.json`` and combine skills
from two or more passed math units in a single L3+ problem.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Sequence

from math_engine import figure_builder
from math_engine.figure_autofill import figure_decision_missing

BRIDGE_SCOPE = "MTH-BRIDGE"
BRIDGE_TITLE = "Cross-Unit Bridge Synthesis"
MIN_BRIDGE_UNITS = 2
MIN_BRIDGE_LEVEL = 3
MAX_BRIDGE_LEVEL = 5

UNIT_CODE_RE = re.compile(r"^[A-Z]+-T\d{2}-C\d{2}-U\d{2}$")


def is_unit_code(code: Any) -> bool:
    """Return True when ``code`` matches a concrete curriculum unit code (e.g. ``MTH-T02-C01-U01``)."""
    return isinstance(code, str) and bool(UNIT_CODE_RE.match(code.strip()))


def _dedupe_strs(values: Sequence[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for val in values:
        if isinstance(val, str):
            cleaned = val.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                out.append(cleaned)
    return out


def problem_unit_codes(
    prob: dict[str, Any],
    *,
    fallback_unit: str = "",
    arch_units: Sequence[str] = (),
) -> list[str]:
    """Return all concrete unit codes associated with ``prob`` (preserving order, deduplicated).

    Priority:
    1. Explicit ``prob["unitCodes"]`` (multi-unit bridge problems).
    2. Archetype ``unitCodes`` passed via ``arch_units``.
    3. Unit references in ``prob["references"]`` (entries containing ``-U``) when the drill is a
       bridge drill or the problem has no concrete single ``unitCode``.
    4. Single ``prob["unitCode"]`` or ``fallback_unit``.
    """
    explicit_multi = prob.get("unitCodes")
    if isinstance(explicit_multi, list):
        units = _dedupe_strs(explicit_multi)
        if units:
            return units

    arch_list = _dedupe_strs(arch_units)
    if arch_list:
        return arch_list

    single = prob.get("unitCode")
    single_clean = single.strip() if isinstance(single, str) else ""
    fallback_clean = fallback_unit.strip() if isinstance(fallback_unit, str) else ""

    is_bridge = fallback_clean == BRIDGE_SCOPE or single_clean == BRIDGE_SCOPE
    if is_bridge or not single_clean:
        refs = prob.get("references") or []
        if isinstance(refs, list):
            unit_refs = _dedupe_strs([r for r in refs if isinstance(r, str) and "-U" in r])
            if unit_refs:
                return unit_refs

    if single_clean and single_clean != BRIDGE_SCOPE:
        return [single_clean]
    if fallback_clean:
        return [fallback_clean]
    return []


def validate_bridge_archetype(
    archetype: Any,
    *,
    seen_keys: set[str] | None = None,
    prefix: str = "",
) -> list[str]:
    """Validate one bridge archetype entry from ``MTH-BRIDGE.json``, returning error strings."""
    if not isinstance(archetype, dict):
        return [f"{prefix or 'bridge archetype'} must be a JSON object."]

    errors: list[str] = []
    key = archetype.get("archetypeKey")
    label = prefix or (f"MTH-BRIDGE/{key}" if isinstance(key, str) and key.strip() else "MTH-BRIDGE/<unknown>")

    if not isinstance(key, str) or not key.strip():
        errors.append(f"{label}: 'archetypeKey' must be a non-empty string.")
    else:
        if seen_keys is not None:
            if key in seen_keys:
                errors.append(f"{label}: duplicate archetypeKey '{key}'.")
            seen_keys.add(key)

    # unitCodes: >= 2 distinct valid unit codes
    raw_units = archetype.get("unitCodes")
    valid_units: list[str] = []
    if not isinstance(raw_units, list) or len(raw_units) < MIN_BRIDGE_UNITS:
        errors.append(f"{label}: 'unitCodes' must be a list of at least {MIN_BRIDGE_UNITS} unit codes.")
    else:
        seen_u: set[str] = set()
        for idx, u in enumerate(raw_units):
            if not is_unit_code(u):
                errors.append(f"{label}.unitCodes[{idx}]: '{u}' is not a valid unit code (e.g. MTH-T02-C01-U01).")
                continue
            cleaned = u.strip()
            if cleaned in seen_u:
                errors.append(f"{label}.unitCodes[{idx}]: duplicate unit code '{cleaned}'.")
            else:
                seen_u.add(cleaned)
                valid_units.append(cleaned)
        if len(valid_units) < MIN_BRIDGE_UNITS:
            errors.append(f"{label}: 'unitCodes' must contain at least {MIN_BRIDGE_UNITS} distinct valid unit codes.")

    # junction: abstract description of how one skill's output feeds the next
    junction = archetype.get("junction")
    if not isinstance(junction, str) or not junction.strip():
        errors.append(f"{label}: 'junction' must be a non-empty string describing how the skills connect.")

    # skillsByUnit: {unit: skill} covering every unit in unitCodes
    skills_by_unit = archetype.get("skillsByUnit")
    if not isinstance(skills_by_unit, dict) or not skills_by_unit:
        errors.append(f"{label}: 'skillsByUnit' must be a non-empty object mapping each unitCode to its skill.")
    else:
        for u_key, skill_val in skills_by_unit.items():
            if not isinstance(u_key, str) or not u_key.strip():
                errors.append(f"{label}.skillsByUnit: keys must be non-empty unit code strings.")
            elif not isinstance(skill_val, str) or not skill_val.strip():
                errors.append(f"{label}.skillsByUnit['{u_key}']: skill must be a non-empty string.")
        if valid_units:
            expected_set = set(valid_units)
            actual_set = set(skills_by_unit.keys())
            missing_skills = sorted(expected_set - actual_set)
            extra_skills = sorted(actual_set - expected_set)
            if missing_skills:
                errors.append(f"{label}.skillsByUnit: missing skill entries for unitCodes {missing_skills}.")
            if extra_skills:
                errors.append(f"{label}.skillsByUnit: unexpected unit keys {extra_skills} not in unitCodes.")

    # cognitiveTraps: non-empty list of trap tags or {trapTag, description} objects
    traps = archetype.get("cognitiveTraps")
    if not isinstance(traps, list) or not traps:
        errors.append(f"{label}: 'cognitiveTraps' must be a non-empty list of junction traps.")
    else:
        for idx, t in enumerate(traps):
            if isinstance(t, str):
                if not t.strip():
                    errors.append(f"{label}.cognitiveTraps[{idx}]: trap tag must be a non-empty string.")
            elif isinstance(t, dict):
                tag = t.get("trapTag")
                if not isinstance(tag, str) or not tag.strip():
                    errors.append(f"{label}.cognitiveTraps[{idx}].trapTag: must be a non-empty string.")
                if "description" in t and (not isinstance(t["description"], str) or not t["description"].strip()):
                    errors.append(f"{label}.cognitiveTraps[{idx}].description: must be a non-empty string.")
            else:
                errors.append(f"{label}.cognitiveTraps[{idx}]: must be a trap string or {{trapTag, description}}.")

    # base level >= 3
    level = archetype.get("level")
    if isinstance(level, bool) or not isinstance(level, int) or not (MIN_BRIDGE_LEVEL <= level <= MAX_BRIDGE_LEVEL):
        errors.append(
            f"{label}: base 'level' must be an integer between {MIN_BRIDGE_LEVEL} and {MAX_BRIDGE_LEVEL}, got {level!r}."
        )

    # levelNote
    level_note = archetype.get("levelNote")
    if not isinstance(level_note, str) or not level_note.strip():
        errors.append(f"{label}: 'levelNote' must be a non-empty string.")

    # source
    source = archetype.get("source")
    if not isinstance(source, str) or not source.strip():
        errors.append(f"{label}: 'source' must be a non-empty string.")

    # figure decision: figureNone or figureBuilders (rules/03 §3.1)
    if figure_decision_missing(archetype):
        errors.append(f"{label}: must declare either 'figureBuilders' (non-empty list) or 'figureNone' (reason).")
    elif "figureBuilders" in archetype:
        builders = archetype["figureBuilders"]
        if not isinstance(builders, list) or not builders:
            errors.append(f"{label}: 'figureBuilders' must be a non-empty list when present.")
        else:
            for idx, spec in enumerate(builders):
                if not isinstance(spec, dict) or not isinstance(spec.get("fn"), str) or not spec["fn"].strip():
                    errors.append(f"{label}.figureBuilders[{idx}]: must be an object with a non-empty 'fn'.")
                elif getattr(figure_builder, spec["fn"], None) is None:
                    errors.append(f"{label}.figureBuilders[{idx}]: unknown builder function '{spec['fn']}'.")

    return errors


def validate_bridge_vault(vault_data: Any, *, label: str = "MTH-BRIDGE.json") -> list[str]:
    """Validate an entire ``MTH-BRIDGE.json`` vault document."""
    if not isinstance(vault_data, dict):
        return [f"{label}: vault file must contain a JSON object."]

    errors: list[str] = []
    if "unitCode" in vault_data and vault_data["unitCode"] != BRIDGE_SCOPE:
        errors.append(f"{label}: 'unitCode' must be '{BRIDGE_SCOPE}', got {vault_data['unitCode']!r}.")

    archetypes = vault_data.get("archetypes")
    if not isinstance(archetypes, list):
        errors.append(f"{label}: 'archetypes' must be a list.")
        return errors

    seen_keys: set[str] = set()
    for idx, arch in enumerate(archetypes):
        key = arch.get("archetypeKey") if isinstance(arch, dict) else None
        prefix = f"{label}[{idx}]/{key}" if isinstance(key, str) and key.strip() else f"{label}[{idx}]"
        errors.extend(validate_bridge_archetype(arch, seen_keys=seen_keys, prefix=prefix))
    return errors


def load_bridge_vault(vault_dir: Path | str | None = None) -> dict[str, Any]:
    """Load ``MTH-BRIDGE.json`` from ``vault_dir`` (default: ``math_engine/reasoning_vault``)."""
    base = (
        Path(vault_dir)
        if vault_dir is not None
        else Path(os.environ.get("REASONING_VAULT_DIR") or Path(__file__).resolve().parent / "reasoning_vault")
    )
    path = base / f"{BRIDGE_SCOPE}.json"
    if not path.exists():
        return {"unitCode": BRIDGE_SCOPE, "archetypes": []}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_bridge_problem(prob: dict[str, Any], arch: dict[str, Any] | None = None) -> list[str]:
    """Validate bridge-specific problem gates (07 §1):

    (a) Must reference >= 2 distinct units (and cover all of the archetype's ``unitCodes``).
    (b) Must have ``level`` >= 3 (L3+ blindSolve gate runs alongside this in ``validate_against_vault``).
    (c) Its ``steps`` must touch each referenced unit via a ``steps[].unit`` (or ``steps[].unitCode``) tag.
    """
    pid = prob.get("id", "?")
    errors: list[str] = []

    arch_units = _dedupe_strs((arch or {}).get("unitCodes") or [])
    if arch is not None and len(arch_units) < MIN_BRIDGE_UNITS:
        errors.append(
            f"[{pid}] Bridge archetype '{arch.get('archetypeKey', '?')}' must declare at least "
            f"{MIN_BRIDGE_UNITS} unitCodes (found {arch_units})."
        )

    # (a) Reference >= 2 units
    has_refs = "references" in prob and prob["references"] is not None
    has_unit_codes = "unitCodes" in prob and prob["unitCodes"] is not None

    ref_units: list[str] = []
    if has_refs:
        if not isinstance(prob["references"], list):
            errors.append(f"[{pid}] Bridge problem 'references' must be a list of at least {MIN_BRIDGE_UNITS} units.")
        else:
            ref_units = _dedupe_strs(
                [r for r in prob["references"] if isinstance(r, str) and not r.strip().startswith("CON-")]
            )
            if len(ref_units) < MIN_BRIDGE_UNITS:
                errors.append(
                    f"[{pid}] Bridge problem must reference at least {MIN_BRIDGE_UNITS} distinct units "
                    f"(found {ref_units})."
                )

    prob_units: list[str] = []
    if has_unit_codes:
        if not isinstance(prob["unitCodes"], list):
            errors.append(f"[{pid}] Bridge problem 'unitCodes' must be a list of at least {MIN_BRIDGE_UNITS} units.")
        else:
            prob_units = _dedupe_strs(prob["unitCodes"])
            if len(prob_units) < MIN_BRIDGE_UNITS:
                errors.append(
                    f"[{pid}] Bridge problem 'unitCodes' must list at least {MIN_BRIDGE_UNITS} distinct units "
                    f"(found {prob_units})."
                )

    if not has_refs and not has_unit_codes:
        errors.append(
            f"[{pid}] Bridge problem must reference at least {MIN_BRIDGE_UNITS} units via 'references' or 'unitCodes'."
        )

    if arch_units:
        if has_refs:
            missing_refs = [u for u in arch_units if u not in ref_units]
            if missing_refs:
                errors.append(f"[{pid}] Bridge problem 'references' is missing archetype unit(s) {missing_refs}.")
        if has_unit_codes:
            missing_ucs = [u for u in arch_units if u not in prob_units]
            if missing_ucs:
                errors.append(f"[{pid}] Bridge problem 'unitCodes' is missing archetype unit(s) {missing_ucs}.")

    required_units = arch_units or prob_units or ref_units

    # (b) Level >= 3 (blindSolve is enforced by validate_against_vault -> validate_blind_solve)
    level = prob.get("level")
    if isinstance(level, bool) or not isinstance(level, int) or level < MIN_BRIDGE_LEVEL:
        errors.append(
            f"[{pid}] Bridge problem must be L{MIN_BRIDGE_LEVEL}+ (found level={level!r}); "
            "L1-L2 problems cannot be bridge problems."
        )

    # (c) Steps must touch every unit via steps[].unit (or steps[].unitCode)
    steps = prob.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append(
            f"[{pid}] Bridge problem must include steps tagged with 'unit' covering all units {required_units}."
        )
    else:
        tagged_units: set[str] = set()
        for idx, st in enumerate(steps, 1):
            if not isinstance(st, dict):
                continue
            raw_tag = st.get("unit") if "unit" in st else st.get("unitCode")
            if raw_tag is None:
                continue
            if not isinstance(raw_tag, str) or not raw_tag.strip():
                errors.append(f"[{pid}] Step {idx} 'unit' tag must be a non-empty unit code string.")
            else:
                tagged_units.add(raw_tag.strip())
        missing_step_units = [u for u in required_units if u not in tagged_units]
        if missing_step_units:
            errors.append(
                f"[{pid}] Bridge problem steps must touch every unit's skill via steps[].unit; "
                f"missing step tag(s) for {missing_step_units}."
            )

    return errors
