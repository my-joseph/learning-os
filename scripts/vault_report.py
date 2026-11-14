"""Vault health from evidence: which archetypes have actually earned their level, and where a vault is thin.

Nothing here is stored by hand. Evidence is recomputed on every run from what passed the gates and what failed:
- earned: problems in `drills/data/<UNIT>/` built on the archetype. For an L3+ problem the level is the
  blind solve's mapped level (`demand_level`); an L1-L2 problem counts at its own level (it passed
  review and every gate on ingest).
- failed: issue-log records of kind `level` whose `where` names the archetype
  (`<UNIT>/<archetypeKey>`), resolved or not, i.e. times a problem built on it was dropped for missing its level.

Flags:
- THIN      a vault level with fewer than 2 archetypes (two problems at that level repeat one structure)
- FAILING   an L3+ archetype that has failed its level and never earned it
- UNPROVEN  an L3+ archetype that has never earned its level yet (not tried, or not yet passed)

    python -m scripts.vault_report MTH-T01-C04        # one unit
    python -m scripts.vault_report                    # every MTH vault
    python -m scripts.vault_report MTH-T01-C04 --log  # also log THIN and FAILING to the issue log
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import Counter, defaultdict

from quality_rules import BLIND_SOLVE_TAGS, demand_level
from scripts import issues

VAULT_DIR = os.path.join("math_engine", "reasoning_vault")


def _earned_level(prob: dict) -> int | None:
    level = prob.get("level")
    if not isinstance(level, int):
        return None
    if level < 3:
        return level
    bs = prob.get("blindSolve")
    if not isinstance(bs, dict) or any(bs.get(t) not in ok for t, ok in BLIND_SOLVE_TAGS.items()):
        return None
    if not isinstance(bs.get("reverse"), bool) or not isinstance(bs.get("steps"), int):
        return None
    return demand_level(bs)


def unit_report(unit: str, vault_dir: str = VAULT_DIR, data_root: str = "drills/data", log: str | None = None) -> dict:
    with open(os.path.join(vault_dir, f"{unit}.json"), encoding="utf-8") as f:
        archetypes = json.load(f).get("archetypes", [])

    earned: dict[str, Counter] = defaultdict(Counter)
    drills: dict[str, set] = defaultdict(set)
    for path in glob.glob(os.path.join(data_root, unit, "*.json")):
        with open(path, encoding="utf-8") as f:
            drill = json.load(f)
        for prob in drill.get("problems", []):
            key, lvl = prob.get("archetypeKey"), _earned_level(prob)
            if key and lvl:
                earned[key][lvl] += 1
                drills[key].add(drill.get("drillId") or os.path.basename(path))

    failed: Counter = Counter()
    for rec in issues.issues(log):
        if rec.get("kind") != "level":
            continue
        for a in archetypes:
            if a["archetypeKey"] in rec.get("where", ""):
                failed[a["archetypeKey"]] += 1

    rows = []
    for a in archetypes:
        key, level = a["archetypeKey"], a.get("level")
        ok = earned[key].get(level, 0) if isinstance(level, int) else 0
        flag = ""
        if isinstance(level, int) and level >= 3 and not ok:
            flag = "FAILING" if failed[key] else "UNPROVEN"
        rows.append(
            {
                "key": key,
                "level": level,
                "earned": ok,
                "earnedOther": {lv: n for lv, n in earned[key].items() if lv != level},
                "failed": failed[key],
                "drills": len(drills[key]),
                "levelNote": bool(a.get("levelNote")),
                "flag": flag,
            }
        )
    per_level = Counter(r["level"] for r in rows)
    thin = sorted(lv for lv, n in per_level.items() if isinstance(lv, int) and n < 2)
    return {"unit": unit, "rows": rows, "perLevel": dict(sorted(per_level.items())), "thin": thin}


def format_report(rep: dict) -> str:
    lines = [
        f"{rep['unit']}: archetypes per level {rep['perLevel']}" + (f"  THIN at L{rep['thin']}" if rep["thin"] else "")
    ]
    for r in sorted(rep["rows"], key=lambda r: (r["level"] or 0, r["key"])):
        other = f" (also earned {r['earnedOther']})" if r["earnedOther"] else ""
        note = " note" if r["levelNote"] else ""
        flag = f"  {r['flag']}" if r["flag"] else ""
        lines.append(f"  L{r['level']} {r['key']}: earned {r['earned']}, failed {r['failed']}{other}{note}{flag}")
    return "\n".join(lines)


def log_gaps(rep: dict, log: str | None = None) -> list[str]:
    """Log THIN levels and FAILING archetypes (identical pending records are not duplicated)."""
    ids = []
    for lv in rep["thin"]:
        iid, _ = issues.add_issue(
            "brief",
            "batch",
            "gate",
            f"{rep['unit']}/vault L{lv}",
            f"Vault has fewer than 2 archetypes at L{lv}, so problems at that level repeat one structure; add one",
            path=log,
        )
        ids.append(iid)
    for r in rep["rows"]:
        if r["flag"] == "FAILING":
            iid, _ = issues.add_issue(
                "level",
                "batch",
                "gate",
                f"{rep['unit']}/{r['key']}",
                f"Archetype labelled L{r['level']} has failed its level {r['failed']} time(s) and never earned it; "
                "redesign it (levelNote) or relabel it",
                path=log,
            )
            ids.append(iid)
    return ids


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m scripts.vault_report", description=__doc__.split("\n\n")[0])
    ap.add_argument("unit", nargs="?", help="unit code, e.g. MTH-T01-C04 (default: every MTH vault)")
    ap.add_argument("--log", action="store_true", help="log THIN levels and FAILING archetypes to the issue log")
    ap.add_argument("--vault-dir", default=VAULT_DIR)
    ap.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR", "drills/data"))
    args = ap.parse_args(argv)

    units = (
        [args.unit]
        if args.unit
        else sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(args.vault_dir, "MTH-*.json")))
    )
    for unit in units:
        rep = unit_report(unit, args.vault_dir, args.data_root)
        print(format_report(rep))
        if args.log:
            ids = log_gaps(rep)
            if ids:
                print(f"  logged: {', '.join(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
