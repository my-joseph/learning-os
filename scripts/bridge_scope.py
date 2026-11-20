# -*- coding: utf-8 -*-
"""Cross-unit bridge problem eligibility report from local learner progress (read-only).

Lists math units the learner has passed (mastery >= 2 by default, using the same
``scripts.weak_spots.evaluate_mastery`` logic on local ``progress/`` files — never calls Notion)
and which bridge archetypes in ``math_engine/reasoning_vault/MTH-BRIDGE.json`` have all of their
``unitCodes`` passed.

Dormant until the learner has passed at least 2 units.

Usage:
    python -m scripts.bridge_scope
    python -m scripts.bridge_scope --json
    python -m scripts.bridge_scope --min-mastery 3
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from math_engine.bridge import BRIDGE_SCOPE, MIN_BRIDGE_UNITS, is_unit_code, load_bridge_vault
from progress_store import find_repo_root, pilot_mode, progress_root
from scripts import weak_spots

DEFAULT_MIN_MASTERY = 2


def _find_checkout_root(cwd: str | None = None) -> str:
    """Locate the enclosing git checkout root (worktree or main), falling back to ``find_repo_root``."""
    current = Path(cwd or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return str(candidate)
    return find_repo_root(cwd)


def main_checkout_progress_dir(cwd: str | None = None) -> str | None:
    """In a git worktree `.git` is a file (`gitdir: <main>/.git/worktrees/<name>`).

    Return `<main>/progress` (or `<main>/pilot/progress` in pilot mode) if it exists,
    matching how ``notion_sync.client.load_env`` falls back to the main checkout's `.env`.
    """
    checkout_root = _find_checkout_root(cwd)
    git_path = os.path.join(checkout_root, ".git")
    if not os.path.isfile(git_path):
        return None
    try:
        with open(git_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
    except OSError:
        return None
    if not text.startswith("gitdir:"):
        return None
    gitdir = os.path.abspath(os.path.join(checkout_root, text.split(":", 1)[1].strip()))
    worktrees_dir = os.path.dirname(gitdir)
    if os.path.basename(worktrees_dir) != "worktrees":
        return None
    main_root = os.path.dirname(os.path.dirname(worktrees_dir))
    sub = os.path.join("pilot", "progress") if pilot_mode() else "progress"
    candidate = os.path.join(main_root, sub)
    return candidate if os.path.isdir(candidate) else None


def resolve_progress_dir(progress_dir: str | None = None, cwd: str | None = None) -> str:
    """Resolve the progress directory to read for bridge eligibility.

    Precedence: explicit ``progress_dir`` > ``PROGRESS_DIR`` env > local checkout's
    ``progress/`` if present > main checkout's ``progress/`` when run from a git worktree >
    local checkout default path.
    """
    if progress_dir:
        return progress_dir
    if os.environ.get("PROGRESS_DIR"):
        return os.environ["PROGRESS_DIR"]
    checkout_root = _find_checkout_root(cwd)
    local = progress_root(checkout_root)
    if os.path.isdir(local):
        return local
    return main_checkout_progress_dir(checkout_root) or local


def _item_units_of(item: weak_spots.Item) -> tuple[str, ...]:
    units = getattr(item, "units", ())
    if units:
        return tuple(units)
    return (item.unit,) if item.unit else ()


def _is_eligible_math_unit(unit_code: str) -> bool:
    return unit_code.startswith("MTH-") and is_unit_code(unit_code)


def evaluate_bridge_scope(
    data_root: str | None = None,
    progress_dir: str | None = None,
    vault_dir: str | None = None,
    *,
    min_mastery: int = DEFAULT_MIN_MASTERY,
) -> dict[str, Any]:
    """Compute passed math units and eligible bridge archetypes from local evidence only."""
    resolved_progress_dir = resolve_progress_dir(progress_dir)
    items = weak_spots.load_items(data_root=data_root, progress_dir=resolved_progress_dir)
    traps = weak_spots.trap_status(items)
    titles = weak_spots._load_titles()

    by_unit: dict[str, list[weak_spots.Item]] = {}
    for item in items:
        for unit in _item_units_of(item):
            if _is_eligible_math_unit(unit):
                by_unit.setdefault(unit, []).append(item)

    passed_units: list[dict[str, Any]] = []
    pending_units: list[dict[str, Any]] = []

    for unit in sorted(by_unit):
        unit_items = by_unit[unit]
        open_weak = any(s["open"] and unit in s["units"] for s in traps.values())
        mastery, cap = weak_spots.evaluate_mastery(unit_items, open_weak)
        if mastery is None:
            continue
        entry = {
            "unitCode": unit,
            "unitTitle": titles.get(unit, ""),
            "mastery": mastery,
            "itemCount": len(unit_items),
            "drillCount": len({i.drill for i in unit_items}),
            "openWeakSpot": open_weak,
            "masteryCap": cap,
        }
        if mastery >= min_mastery:
            passed_units.append(entry)
        else:
            pending_units.append(entry)

    passed_set = {u["unitCode"] for u in passed_units}
    dormant = len(passed_set) < MIN_BRIDGE_UNITS

    vault = load_bridge_vault(vault_dir=vault_dir)
    archetypes = vault.get("archetypes") if isinstance(vault, dict) else []
    if not isinstance(archetypes, list):
        archetypes = []

    eligible_archetypes: list[dict[str, Any]] = []
    blocked_archetypes: list[dict[str, Any]] = []

    for arch in archetypes:
        if not isinstance(arch, dict):
            continue
        req_units = [u for u in (arch.get("unitCodes") or []) if isinstance(u, str) and u.strip()]
        missing = [u for u in req_units if u not in passed_set]
        summary = {
            "archetypeKey": arch.get("archetypeKey", ""),
            "name": arch.get("name", ""),
            "level": arch.get("level"),
            "unitCodes": req_units,
            "junction": arch.get("junction", ""),
        }
        if not dormant and len(req_units) >= MIN_BRIDGE_UNITS and not missing:
            eligible_archetypes.append(summary)
        else:
            blocked_archetypes.append({**summary, "missingUnits": missing})

    return {
        "scope": BRIDGE_SCOPE,
        "status": "dormant" if dormant else "active",
        "dormant": dormant,
        "minMastery": min_mastery,
        "minEligibleUnits": MIN_BRIDGE_UNITS,
        "eligibleUnitCount": len(passed_units),
        "eligibleUnits": passed_units,
        "pendingUnits": pending_units,
        "eligibleArchetypes": eligible_archetypes,
        "blockedArchetypes": blocked_archetypes,
    }


def eligible_units(
    data_root: str | None = None,
    progress_dir: str | None = None,
    *,
    min_mastery: int = DEFAULT_MIN_MASTERY,
) -> set[str]:
    """Return the set of math unit codes that currently qualify for bridge problems."""
    report = evaluate_bridge_scope(
        data_root=data_root,
        progress_dir=progress_dir,
        min_mastery=min_mastery,
    )
    return {u["unitCode"] for u in report["eligibleUnits"]}


def format_bridge_scope(report: dict[str, Any]) -> str:
    """Format ``evaluate_bridge_scope`` output as a concise human-readable status report."""
    n = report["eligibleUnitCount"]
    min_m = report["minMastery"]
    req_n = report["minEligibleUnits"]
    lines: list[str] = []

    if report["dormant"]:
        lines.append(f"MTH-BRIDGE — dormant: {n} eligible unit(s), need ≥{req_n} (mastery >= {min_m})")
    else:
        lines.append(
            f"MTH-BRIDGE — active: {n} eligible unit(s) (mastery >= {min_m}); "
            f"{len(report['eligibleArchetypes'])} eligible bridge archetype(s)"
        )

    lines.append("")
    lines.append(f"Passed units ({n}):")
    if not report["eligibleUnits"]:
        lines.append("  (none)")
    for u in report["eligibleUnits"]:
        title = f" · {u['unitTitle']}" if u.get("unitTitle") else ""
        lines.append(
            f"  - {u['unitCode']}{title}  (mastery {u['mastery']}, {u['itemCount']} items in {u['drillCount']} drills)"
        )

    if report["pendingUnits"]:
        lines.append("")
        lines.append(f"Attempted, not yet passed (< mastery {min_m}) ({len(report['pendingUnits'])}):")
        for u in report["pendingUnits"]:
            title = f" · {u['unitTitle']}" if u.get("unitTitle") else ""
            lines.append(
                f"  - {u['unitCode']}{title}  "
                f"(mastery {u['mastery']}, {u['itemCount']} items in {u['drillCount']} drills)"
            )

    lines.append("")
    lines.append(f"Eligible bridge archetypes ({len(report['eligibleArchetypes'])}):")
    if not report["eligibleArchetypes"]:
        lines.append("  (none)")
    for a in report["eligibleArchetypes"]:
        units_str = " + ".join(a["unitCodes"])
        lines.append(f"  - [L{a['level']}] {a['archetypeKey']} ({units_str})")

    if report["blockedArchetypes"]:
        lines.append("")
        lines.append(f"Blocked bridge archetypes ({len(report['blockedArchetypes'])}):")
        for a in report["blockedArchetypes"]:
            units_str = " + ".join(a["unitCodes"])
            missing_str = ", ".join(a["missingUnits"]) if a["missingUnits"] else "dormant"
            lines.append(f"  - [L{a['level']}] {a['archetypeKey']} ({units_str}) — needs {missing_str}")

    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.bridge_scope",
        description="List passed math units and eligible cross-unit bridge archetypes from local progress (read-only).",
    )
    parser.add_argument(
        "--min-mastery",
        type=int,
        default=DEFAULT_MIN_MASTERY,
        help=f"Minimum evidence-based mastery level required for a unit to qualify (default: {DEFAULT_MIN_MASTERY}).",
    )
    parser.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR") or None)
    parser.add_argument("--progress-dir", default=None)
    parser.add_argument("--vault-dir", default=None)
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output structured JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.min_mastery < 1 or args.min_mastery > 4:
        parser.error("--min-mastery must be between 1 and 4.")
    report = evaluate_bridge_scope(
        data_root=args.data_root,
        progress_dir=args.progress_dir,
        vault_dir=args.vault_dir,
        min_mastery=args.min_mastery,
    )
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_bridge_scope(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
