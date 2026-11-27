"""Vault health from evidence: which levels each archetype has actually reached, and where it keeps failing.

An archetype is a skill; its `level` is only the base level where the skill is used directly. A problem may
build on it at any level from the base upward, and the gates (blind solve for L3+) decide whether that level
was earned. Nothing here is stored by hand; every run recomputes:
- earned: ingested problems built on the archetype, in any drill folder, counted by level (L3+: the blind
  solve's `demand_level`; L1-L2: the problem's level, since it passed review and every gate on ingest);
- failed: issue-log records of kind `level` whose `where` is `<SCOPE>/<archetypeKey>@L<n>` (a problem at Ln
  was dropped for missing its level). Without `@L<n>` the archetype's base level is assumed.

Flags:
- FAILING@Ln  failed at Ln and never earned Ln
- UNPROVEN    an L3+ base level that no drill has earned yet

    python -m scripts.vault_report MTH-T01-C04-U04    # one unit
    python -m scripts.vault_report MTH-T01-C04        # a chapter (all its units)
    python -m scripts.vault_report                    # every MTH chapter or unit vault file
    python -m scripts.vault_report MTH-T01-C04 --log  # also log FAILING archetypes to the issue log
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
from collections import Counter, defaultdict

from code_engine import ai_drill_ingest as code_ingest
from ingest_core import archetype_owner, load_scope_archetypes
from math_engine import ai_drill_ingest as math_ingest
from math_engine.variant_bank import count_quarantined_variants
from quality_rules import BLIND_SOLVE_TAGS, demand_level
from scripts import issues

MATH_VAULT_DIR = os.path.join("math_engine", "reasoning_vault")
CODE_VAULT_DIR = os.path.join("code_engine", "reasoning_vault")
VAULT_DIR = MATH_VAULT_DIR

# Keep the existing report imports available to callers.
mth_archetype_owner = prg_archetype_owner = archetype_owner
mth_load_scope_archetypes = math_ingest.load_scope_archetypes
prg_load_scope_archetypes = code_ingest.load_scope_archetypes


def _earned_level(prob: dict, is_prg: bool = False) -> int | None:
    level = prob.get("level")
    if not isinstance(level, int):
        return None
    if is_prg or level < 3:
        return level
    bs = prob.get("blindSolve")
    if not isinstance(bs, dict) or any(bs.get(t) not in ok for t, ok in BLIND_SOLVE_TAGS.items()):
        return None
    if not isinstance(bs.get("reverse"), bool) or not isinstance(bs.get("steps"), int):
        return None
    return demand_level(bs)


def _evidence(data_root: str) -> dict[str, Counter]:
    earned: dict[str, Counter] = defaultdict(Counter)
    for prefix, is_prg in (("MTH-*", False), ("PRG-*", True)):
        for path in glob.glob(os.path.join(data_root, prefix, "*.json")):
            with open(path, encoding="utf-8") as f:
                drill = json.load(f)
            for prob in drill.get("problems", []):
                key, lvl = prob.get("archetypeKey"), _earned_level(prob, is_prg=is_prg)
                if key and lvl:
                    earned[key][lvl] += 1
    return earned


def unit_report(
    scope: str,
    vault_dir: str | None = None,
    data_root: str = "drills/data",
    log: str | None = None,
    earned: dict[str, Counter] | None = None,
) -> dict:
    is_prg = scope.startswith("PRG-")
    resolved_vault = vault_dir if vault_dir is not None else (CODE_VAULT_DIR if is_prg else MATH_VAULT_DIR)
    resolve_dir = code_ingest._code_vault_dir if is_prg else math_ingest._vault_dir
    archetypes = load_scope_archetypes(scope, resolve_dir(resolved_vault), math_scope=not is_prg)
    if earned is None:
        earned = _evidence(data_root)
    failed: dict[str, Counter] = defaultdict(Counter)
    for rec in issues.issues(log):
        if rec.get("kind") != "level":
            continue
        where = rec.get("where", "")
        for a in archetypes:
            key = a["archetypeKey"]
            m = re.search(rf"/{re.escape(key)}(?:@L(\d))?(?:\s*\(vault\))?$", where)
            if m:
                failed[key][int(m.group(1)) if m.group(1) else a.get("level")] += 1

    rows = []
    for a in archetypes:
        key, base = a["archetypeKey"], a.get("level")
        flags = [f"FAILING@L{lv}" for lv in sorted(failed[key]) if not earned[key].get(lv)]
        if isinstance(base, int) and base >= 3 and not earned[key].get(base) and not flags:
            flags.append("UNPROVEN")
        rows.append(
            {
                "key": key,
                "unit": archetype_owner(a),
                "level": base,
                "earned": dict(sorted(earned[key].items())),
                "failed": dict(sorted(failed[key].items())),
                "levelNote": bool(a.get("levelNote")),
                "flags": flags,
            }
        )
    quarantined_count = 0 if is_prg else count_quarantined_variants(scope)
    return {"unit": scope, "rows": rows, "quarantinedVariants": quarantined_count}


def format_report(rep: dict) -> str:
    lines = [f"{rep['unit']}: {len(rep['rows'])} archetypes (earned/failed counts by level)"]
    q_count = int(rep.get("quarantinedVariants") or 0)
    if q_count > 0:
        lines.append(
            f"  Quarantined variants: {q_count} (skipped by Studio & coverage gate; "
            f"run python -m math_engine.variant_bank --reverify {rep['unit']})"
        )
    for r in sorted(rep["rows"], key=lambda r: (r["unit"], r["level"] or 0, r["key"])):
        earned = ", ".join(f"L{lv}x{n}" for lv, n in r["earned"].items()) or "none"
        failed = ", ".join(f"L{lv}x{n}" for lv, n in r["failed"].items())
        tail = (f"  failed {failed}" if failed else "") + (" note" if r["levelNote"] else "")
        flags = f"  {' '.join(r['flags'])}" if r["flags"] else ""
        lines.append(f"  [{r['unit']}] base L{r['level']} {r['key']}: earned {earned}{tail}{flags}")
    return "\n".join(lines)


def log_gaps(rep: dict, log: str | None = None) -> list[str]:
    """Log FAILING archetypes (identical pending records are not duplicated)."""
    ids = []
    for r in rep["rows"]:
        for flag in r["flags"]:
            if not flag.startswith("FAILING"):
                continue
            lv = flag.split("@L")[1]
            iid, _ = issues.add_issue(
                "level",
                "batch",
                "gate",
                f"{r['unit']}/{r['key']} (vault)",
                f"Archetype keeps failing at L{lv} and has never earned it; add a levelNote on how to earn L{lv} "
                "or stop using it at that level",
                path=log,
            )
            ids.append(iid)
    return ids


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m scripts.vault_report", description=__doc__.split("\n\n")[0])
    ap.add_argument("unit", nargs="?", help="unit or chapter code (default: every MTH and PRG vault file)")
    ap.add_argument("--log", action="store_true", help="log FAILING archetypes to the issue log")
    ap.add_argument("--vault-dir", default=None)
    ap.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR", "drills/data"))
    args = ap.parse_args(argv)

    if args.unit:
        scopes = [args.unit]
    elif args.vault_dir:
        scopes = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(args.vault_dir, "*.json")))
    else:
        scopes = sorted(
            [os.path.basename(p)[:-5] for p in glob.glob(os.path.join(MATH_VAULT_DIR, "MTH-*.json"))]
            + [os.path.basename(p)[:-5] for p in glob.glob(os.path.join(CODE_VAULT_DIR, "PRG-*.json"))]
        )
    earned = _evidence(args.data_root)
    for scope in scopes:
        rep = unit_report(scope, args.vault_dir, args.data_root, earned=earned)
        print(format_report(rep))
        if args.log:
            ids = log_gaps(rep)
            if ids:
                print(f"  logged: {', '.join(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
