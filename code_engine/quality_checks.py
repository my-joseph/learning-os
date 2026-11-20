# -*- coding: utf-8 -*-
"""
PRG Layer 3 review rubric loader, schema validator, and known-bad lint verifier.

Usage:
    python -m code_engine.quality_checks --check-vaults
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from code_engine.lint_check import LintToolsMissingError, get_lint_binaries, lint_code_snippet
from math_engine import figure_builder
from math_engine.bridge import BRIDGE_SCOPE, validate_bridge_vault
from math_engine.figure_autofill import figure_decision_missing

CODE_ENGINE_DIR = Path(__file__).resolve().parent
UNIVERSAL_CHECKS_PATH = CODE_ENGINE_DIR / "quality_checks.json"
VAULT_DIR = CODE_ENGINE_DIR / "reasoning_vault"
MATH_VAULT_DIR = CODE_ENGINE_DIR.parent / "math_engine" / "reasoning_vault"

QC_ID_PATTERN = re.compile(r"^QC-[a-z0-9]+(?:-[a-z0-9]+)*$")
UNIVERSAL_ID_PATTERN = re.compile(r"^U-[a-z0-9]+(?:-[a-z0-9]+)*$")
VALID_SEVERITIES = ("must", "should")


def load_universal(path: Path | None = None) -> list[dict[str, Any]]:
    """Load the universal quality checks list from `code_engine/quality_checks.json`."""
    if path is not None:
        target = Path(path)
    else:
        cwd_target = Path("code_engine/quality_checks.json")
        target = cwd_target if cwd_target.exists() else UNIVERSAL_CHECKS_PATH
    data = json.loads(target.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("checks"), list):
        return data["checks"]
    raise ValueError(f"Universal quality checks at {target} must be a JSON list.")


def _resolve_vault_dir(vault_dir: Path | None = None) -> Path:
    if vault_dir is not None:
        return Path(vault_dir)
    cwd_vault = Path("code_engine/reasoning_vault")
    return cwd_vault if cwd_vault.exists() else VAULT_DIR


def load_archetype(archetype_key: str, vault_dir: Path | None = None) -> dict[str, Any] | None:
    """Find and return the archetype dict for `archetype_key` from the PRG reasoning vaults."""
    if not archetype_key:
        return None
    target_dir = _resolve_vault_dir(vault_dir)
    if not target_dir.exists():
        return None
    for vf in sorted(target_dir.glob("*.json")):
        data = json.loads(vf.read_text(encoding="utf-8"))
        for arch in data.get("archetypes", []):
            if arch.get("archetypeKey") == archetype_key:
                return arch
    return None


def effective_severity(check: dict[str, Any], level: int | None) -> str:
    """Compute effective severity for a rubric check at a given problem level."""
    sev = check.get("severity", "should")
    mfl = check.get("mustFromLevel")
    if isinstance(level, int) and isinstance(mfl, int) and level >= mfl:
        return "must"
    return sev


def applicable_rubric(
    archetype_key: str | None,
    level: int | None,
    *,
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Return universal + archetype qualityChecks with effective severity for `level`."""
    universal = load_universal(universal_path)
    arch = load_archetype(archetype_key, vault_dir=vault_dir) if archetype_key else None
    arch_checks = (arch or {}).get("qualityChecks") or []

    out: list[dict[str, Any]] = []
    for c in [*universal, *arch_checks]:
        if not isinstance(c, dict) or not c.get("id"):
            continue
        item: dict[str, Any] = {
            "id": c["id"],
            "check": c.get("check", ""),
            "why": c.get("why", ""),
            "severity": effective_severity(c, level),
        }
        if "accepted" in c:
            item["accepted"] = c["accepted"]
        out.append(item)
    return out


def _validate_known_bad(known_bad: Any, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(known_bad, dict):
        return [f"{prefix}.knownBad must be an object with 'code' and 'caughtBy'."]

    code = known_bad.get("code")
    if not isinstance(code, str) or not code.strip():
        errors.append(f"{prefix}.knownBad.code must be a non-empty string.")

    caught_by = known_bad.get("caughtBy")
    if not isinstance(caught_by, str) or not caught_by.strip():
        errors.append(f"{prefix}.knownBad.caughtBy must be 'review' or 'lint:<rule-id>'.")
    elif caught_by == "test":
        errors.append(
            f"{prefix}.knownBad.caughtBy='test' is not allowed; behaviour belongs in hiddenTests, not qualityChecks."
        )
    elif caught_by != "review":
        if not caught_by.startswith("lint:") or not caught_by[5:].strip():
            errors.append(f"{prefix}.knownBad.caughtBy '{caught_by}' must be 'review' or 'lint:<rule-id>'.")
    return errors


def _validate_check_entry(
    entry: Any,
    *,
    prefix: str,
    id_pattern: re.Pattern[str],
    id_desc: str,
    seen_ids: set[str],
    universal_ids: set[str] | None,
    allow_must_from_level: bool,
) -> list[str]:
    if not isinstance(entry, dict):
        return [f"{prefix} must be an object."]

    errors: list[str] = []
    cid = entry.get("id")
    if not isinstance(cid, str) or not cid.strip():
        errors.append(f"{prefix}.id must be a non-empty string.")
    else:
        if not id_pattern.match(cid):
            errors.append(f"{prefix}.id '{cid}' must match {id_desc}.")
        if cid in seen_ids:
            errors.append(f"{prefix}.id '{cid}' is duplicated.")
        if universal_ids is not None and cid in universal_ids:
            errors.append(f"{prefix}.id '{cid}' collides with a universal check id.")
        seen_ids.add(cid)

    for field in ("check", "why"):
        val = entry.get(field)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"{prefix}.{field} must be a non-empty string.")

    severity = entry.get("severity")
    if severity not in VALID_SEVERITIES:
        errors.append(f"{prefix}.severity must be one of {VALID_SEVERITIES}, got {severity!r}.")

    if "accepted" in entry:
        accepted = entry["accepted"]
        if (
            not isinstance(accepted, list)
            or not accepted
            or not all(isinstance(item, str) and item.strip() for item in accepted)
        ):
            errors.append(f"{prefix}.accepted must be a non-empty list of non-empty strings.")

    if "mustFromLevel" in entry:
        mfl = entry["mustFromLevel"]
        if not allow_must_from_level:
            errors.append(f"{prefix}.mustFromLevel is only supported on universal checks.")
        elif isinstance(mfl, bool) or not isinstance(mfl, int) or mfl < 1:
            errors.append(f"{prefix}.mustFromLevel must be a positive integer.")

    if "knownBad" not in entry:
        errors.append(f"{prefix} is missing 'knownBad'.")
    else:
        errors.extend(_validate_known_bad(entry["knownBad"], prefix))

    return errors


def validate_universal_checks(checks: Any) -> list[str]:
    """Validate the universal quality checks list, returning a list of error strings."""
    if not isinstance(checks, list) or not checks:
        return ["Universal quality checks must be a non-empty list."]

    errors: list[str] = []
    seen_ids: set[str] = set()
    for idx, entry in enumerate(checks):
        errors.extend(
            _validate_check_entry(
                entry,
                prefix=f"universal[{idx}]",
                id_pattern=UNIVERSAL_ID_PATTERN,
                id_desc="U-<kebab>",
                seen_ids=seen_ids,
                universal_ids=None,
                allow_must_from_level=True,
            )
        )
    return errors


def validate_quality_checks(
    archetype: dict[str, Any],
    *,
    seen_ids: set[str] | None = None,
    universal_ids: set[str] | None = None,
) -> list[str]:
    """Validate an archetype's `qualityChecks` list, returning a list of error strings."""
    key = archetype.get("archetypeKey", "<unknown>")
    checks = archetype.get("qualityChecks")
    if not isinstance(checks, list) or not checks:
        return [f"Archetype '{key}' must have a non-empty 'qualityChecks' list."]

    active_seen = seen_ids if seen_ids is not None else set()
    active_universal = universal_ids
    if active_universal is None and UNIVERSAL_CHECKS_PATH.exists():
        active_universal = {c["id"] for c in load_universal() if isinstance(c, dict) and "id" in c}

    errors: list[str] = []
    for idx, entry in enumerate(checks):
        errors.extend(
            _validate_check_entry(
                entry,
                prefix=f"{key}.qualityChecks[{idx}]",
                id_pattern=QC_ID_PATTERN,
                id_desc="QC-<kebab>",
                seen_ids=active_seen,
                universal_ids=active_universal,
                allow_must_from_level=False,
            )
        )
    return errors


def _lint_tools_available() -> tuple[bool, str | None]:
    if shutil.which("node") is None:
        return False, "node binary not found on PATH"
    try:
        get_lint_binaries()
    except LintToolsMissingError as exc:
        return False, str(exc)
    return True, None


def verify_known_bad_lint(check: dict[str, Any], *, label: str = "") -> tuple[bool, str | None]:
    """
    If `check.knownBad.caughtBy` is `lint:<rule>`, lint `knownBad.code` with `tools/lint/base.js`
    and verify that `<rule>` fires.

    Returns (ok, message). If lint tools are missing, returns (True, skip_message).
    """
    known_bad = check.get("knownBad") or {}
    caught_by = known_bad.get("caughtBy", "")
    if not isinstance(caught_by, str) or not caught_by.startswith("lint:"):
        return True, None

    rule_id = caught_by[5:].strip()
    available, reason = _lint_tools_available()
    cid = check.get("id", "<unknown>")
    prefix = f"{label} " if label else ""
    if not available:
        return True, f"SKIP {prefix}{cid} ({caught_by}): {reason}"

    code = known_bad.get("code", "")
    ext = known_bad.get("ext") or ("ts" if "@typescript-eslint/" in rule_id else "js")
    findings = lint_code_snippet(code, ext=ext, filename="known_bad")
    fired_rules = {f["rule"] for f in findings}
    if rule_id not in fired_rules:
        return (
            False,
            f"{prefix}{cid}: knownBad snippet with caughtBy='{caught_by}' did not trigger '{rule_id}' "
            f"(fired: {sorted(fired_rules) or 'none'}).",
        )
    return True, None


def validate_math_archetype(
    archetype: Any,
    *,
    seen_keys: set[str] | None = None,
    prefix: str = "",
) -> tuple[list[str], list[str]]:
    """Validate one unit/chapter math vault archetype entry.

    Required (errors): `archetypeKey`, `level` (1..5), `name`, `coreConcept`,
    `governingRelation`, `cognitiveTraps`, figure decision (`figureBuilders` or `figureNone`).
    Recommended (warnings): `unitCode`, `mentalModel`, `source`, object-form `cognitiveTraps`.

    Returns ``(errors, warnings)``.
    """
    if not isinstance(archetype, dict):
        return [f"{prefix or 'math archetype'} must be a JSON object."], []

    errors: list[str] = []
    warnings_list: list[str] = []
    key = archetype.get("archetypeKey")
    label = prefix or (str(key).strip() if isinstance(key, str) and key.strip() else "<unknown>")

    if not isinstance(key, str) or not key.strip():
        errors.append(f"{label}: 'archetypeKey' must be a non-empty string.")
    elif seen_keys is not None:
        if key in seen_keys:
            errors.append(f"{label}: duplicate archetypeKey '{key}'.")
        seen_keys.add(key)

    level = archetype.get("level")
    if isinstance(level, bool) or not isinstance(level, int) or not (1 <= level <= 5):
        errors.append(f"{label}: 'level' must be an integer 1..5, got {level!r}.")

    for req in ("name", "coreConcept", "governingRelation"):
        val = archetype.get(req)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"{label}: '{req}' must be a non-empty string.")

    traps = archetype.get("cognitiveTraps")
    if not isinstance(traps, list) or not traps:
        errors.append(f"{label}: 'cognitiveTraps' must be a non-empty list.")
    else:
        has_legacy_str_trap = False
        for idx, t in enumerate(traps):
            if isinstance(t, str):
                if not t.strip():
                    errors.append(f"{label}.cognitiveTraps[{idx}]: trap tag must be a non-empty string.")
                has_legacy_str_trap = True
            elif isinstance(t, dict):
                tag = t.get("trapTag")
                if not isinstance(tag, str) or not tag.strip():
                    errors.append(f"{label}.cognitiveTraps[{idx}].trapTag: must be a non-empty string.")
                if "description" in t and (not isinstance(t["description"], str) or not t["description"].strip()):
                    errors.append(f"{label}.cognitiveTraps[{idx}].description: must be a non-empty string.")
            else:
                errors.append(f"{label}.cognitiveTraps[{idx}]: must be a trap string or {{trapTag, description}}.")
        if has_legacy_str_trap:
            warnings_list.append(
                f"{label}: 'cognitiveTraps' uses legacy string entries (prefer {{trapTag, description}} objects)."
            )

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

    for rec in ("unitCode", "source"):
        val = archetype.get(rec)
        if not isinstance(val, str) or not val.strip():
            warnings_list.append(f"{label}: missing recommended field '{rec}'.")

    mm = archetype.get("mentalModel")
    valid_mm = (isinstance(mm, str) and bool(mm.strip())) or (
        isinstance(mm, list) and bool(mm) and all(isinstance(x, str) and bool(x.strip()) for x in mm)
    )
    if not valid_mm:
        warnings_list.append(f"{label}: missing recommended field 'mentalModel'.")

    return errors, warnings_list


def validate_math_vault(vault_data: Any, *, label: str = "math vault") -> tuple[list[str], list[str]]:
    """Validate one unit/chapter math vault document. Returns ``(errors, warnings)``."""
    if not isinstance(vault_data, dict):
        return [f"{label}: vault file must contain a JSON object."], []

    archetypes = vault_data.get("archetypes")
    if not isinstance(archetypes, list):
        return [f"{label}: 'archetypes' must be a list."], []

    errors: list[str] = []
    warnings_list: list[str] = []
    seen_keys: set[str] = set()
    for idx, arch in enumerate(archetypes):
        key = arch.get("archetypeKey") if isinstance(arch, dict) else None
        prefix = f"{label}[{idx}]/{key}" if isinstance(key, str) and key.strip() else f"{label}[{idx}]"
        arch_errors, arch_warnings = validate_math_archetype(arch, seen_keys=seen_keys, prefix=prefix)
        errors.extend(arch_errors)
        warnings_list.extend(arch_warnings)
    return errors, warnings_list


def check_math_vaults(math_vault_dir: Path | None = None) -> tuple[list[str], list[str], int, int]:
    """Validate all unit/chapter math vault files under ``math_engine/reasoning_vault/``.

    Skips ``MTH-BRIDGE.json`` (validated by ``check_bridge_vault``) and ``MTH-TEMPLATE.json``.
    Returns ``(errors, warnings, vault_count, archetype_count)``.
    """
    target_dir = Path(math_vault_dir) if math_vault_dir is not None else MATH_VAULT_DIR
    if not target_dir.exists():
        return [], [], 0, 0

    errors: list[str] = []
    warnings_list: list[str] = []
    vault_count = 0
    archetype_count = 0

    for vf in sorted(target_dir.glob("*.json")):
        if vf.stem in (BRIDGE_SCOPE, "MTH-TEMPLATE"):
            continue
        vault_count += 1
        try:
            data = json.loads(vf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"{vf.name}: invalid JSON: {exc}")
            continue
        v_errors, v_warnings = validate_math_vault(data, label=vf.name)
        errors.extend(v_errors)
        warnings_list.extend(v_warnings)
        archetypes = data.get("archetypes") if isinstance(data, dict) else []
        if isinstance(archetypes, list):
            archetype_count += len(archetypes)

    return errors, warnings_list, vault_count, archetype_count


def check_bridge_vault(math_vault_dir: Path | None = None) -> tuple[list[str], int]:
    """Validate ``math_engine/reasoning_vault/MTH-BRIDGE.json`` if present.

    Returns ``(errors, bridge_archetype_count)``.
    """
    target_dir = Path(math_vault_dir) if math_vault_dir is not None else MATH_VAULT_DIR
    bridge_path = target_dir / f"{BRIDGE_SCOPE}.json"
    if not bridge_path.exists():
        return [], 0
    try:
        data = json.loads(bridge_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{bridge_path.name}: invalid JSON: {exc}"], 0
    errors = validate_bridge_vault(data, label=bridge_path.name)
    archetypes = data.get("archetypes") if isinstance(data, dict) else []
    count = len(archetypes) if isinstance(archetypes, list) else 0
    return errors, count


def check_all_vaults(
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
    math_vault_dir: Path | None = None,
    *,
    warnings_out: list[str] | None = None,
) -> tuple[list[str], list[str], dict[str, int]]:
    """Validate universal checks + all PRG vault files + math unit vaults + MTH-BRIDGE vault schema."""
    errors: list[str] = []
    skips: list[str] = []

    universal = load_universal(universal_path)
    errors.extend(validate_universal_checks(universal))
    universal_ids = {c["id"] for c in universal if isinstance(c, dict) and isinstance(c.get("id"), str)}

    for check in universal:
        if isinstance(check, dict):
            ok, msg = verify_known_bad_lint(check, label="universal")
            if not ok and msg:
                errors.append(msg)
            elif ok and msg:
                skips.append(msg)

    target_vault_dir = Path(vault_dir) if vault_dir is not None else VAULT_DIR
    vault_files = sorted(target_vault_dir.glob("*.json"))
    seen_ids: set[str] = set()
    archetype_count = 0
    check_count = 0

    for vf in vault_files:
        data = json.loads(vf.read_text(encoding="utf-8"))
        for arch in data.get("archetypes", []):
            archetype_count += 1
            errors.extend(validate_quality_checks(arch, seen_ids=seen_ids, universal_ids=universal_ids))
            for check in arch.get("qualityChecks") or []:
                if not isinstance(check, dict):
                    continue
                check_count += 1
                ok, msg = verify_known_bad_lint(check, label=f"{vf.name}/{arch.get('archetypeKey', '?')}")
                if not ok and msg:
                    errors.append(msg)
                elif ok and msg:
                    skips.append(msg)

    bridge_archetypes = 0
    math_vaults = 0
    math_archetypes = 0
    math_warnings: list[str] = []
    if math_vault_dir is not None or vault_dir is None:
        bridge_errors, bridge_archetypes = check_bridge_vault(math_vault_dir=math_vault_dir)
        errors.extend(bridge_errors)
        math_errors, math_warnings, math_vaults, math_archetypes = check_math_vaults(math_vault_dir=math_vault_dir)
        errors.extend(math_errors)
        if warnings_out is not None:
            warnings_out.extend(math_warnings)

    stats = {
        "universal": len(universal),
        "vaults": len(vault_files),
        "archetypes": archetype_count,
        "checks": check_count,
        "mathVaults": math_vaults,
        "mathArchetypes": math_archetypes,
        "mathWarnings": len(math_warnings),
        "bridgeArchetypes": bridge_archetypes,
    }
    return errors, skips, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate PRG qualityChecks, math unit vaults, and MTH-BRIDGE reasoning vault schema."
    )
    parser.add_argument("--check-vaults", action="store_true", help="Validate all vaults and run knownBad lint checks")
    parser.add_argument("--vault-dir", default=None, help="Override code_engine/reasoning_vault directory")
    parser.add_argument("--math-vault-dir", default=None, help="Override math_engine/reasoning_vault directory")
    args = parser.parse_args(argv)

    if not args.check_vaults:
        parser.error("Specify --check-vaults")

    vault_dir = Path(args.vault_dir) if args.vault_dir else None
    math_vault_dir = Path(args.math_vault_dir) if args.math_vault_dir else None
    warnings_list: list[str] = []
    errors, skips, stats = check_all_vaults(
        vault_dir=vault_dir,
        math_vault_dir=math_vault_dir,
        warnings_out=warnings_list,
    )

    for s in skips:
        print(s)
    for w in warnings_list:
        print(f"WARN: {w}")
    for err in errors:
        print(f"ERROR: {err}", file=sys.stderr)

    print(
        f"Checked {stats['universal']} universal check(s), {stats['vaults']} PRG vault(s), "
        f"{stats['archetypes']} PRG archetype(s), {stats['checks']} archetype check(s), "
        f"{stats['mathVaults']} math vault(s), {stats['mathArchetypes']} math archetype(s), "
        f"{stats['bridgeArchetypes']} bridge archetype(s): "
        f"{len(errors)} error(s), {stats['mathWarnings']} warning(s), {len(skips)} skipped."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
