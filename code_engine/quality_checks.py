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

CODE_ENGINE_DIR = Path(__file__).resolve().parent
UNIVERSAL_CHECKS_PATH = CODE_ENGINE_DIR / "quality_checks.json"
VAULT_DIR = CODE_ENGINE_DIR / "reasoning_vault"

QC_ID_PATTERN = re.compile(r"^QC-[a-z0-9]+(?:-[a-z0-9]+)*$")
UNIVERSAL_ID_PATTERN = re.compile(r"^U-[a-z0-9]+(?:-[a-z0-9]+)*$")
VALID_SEVERITIES = ("must", "should")


def load_universal(path: Path | None = None) -> list[dict[str, Any]]:
    """Load the universal quality checks list from `code_engine/quality_checks.json`."""
    target = Path(path) if path is not None else UNIVERSAL_CHECKS_PATH
    data = json.loads(target.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("checks"), list):
        return data["checks"]
    raise ValueError(f"Universal quality checks at {target} must be a JSON list.")


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


def check_all_vaults(
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
) -> tuple[list[str], list[str], dict[str, int]]:
    """Validate universal checks + all vault files and verify every `lint:<rule>` knownBad snippet."""
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

    stats = {
        "universal": len(universal),
        "vaults": len(vault_files),
        "archetypes": archetype_count,
        "checks": check_count,
    }
    return errors, skips, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PRG qualityChecks in universal list and reasoning vaults.")
    parser.add_argument("--check-vaults", action="store_true", help="Validate all vaults and run knownBad lint checks")
    parser.add_argument("--vault-dir", default=None, help="Override code_engine/reasoning_vault directory")
    args = parser.parse_args(argv)

    if not args.check_vaults:
        parser.error("Specify --check-vaults")

    vault_dir = Path(args.vault_dir) if args.vault_dir else None
    errors, skips, stats = check_all_vaults(vault_dir=vault_dir)

    for s in skips:
        print(s)
    for err in errors:
        print(f"ERROR: {err}", file=sys.stderr)

    print(
        f"Checked {stats['universal']} universal check(s), {stats['vaults']} vault(s), "
        f"{stats['archetypes']} archetype(s), {stats['checks']} archetype check(s): "
        f"{len(errors)} error(s), {len(skips)} skipped."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
