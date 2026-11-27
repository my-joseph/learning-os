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
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from code_engine import ai_drill_ingest as code_ingest
from ingest_core import archetype_owner, load_scope_archetypes
from math_engine import ai_drill_ingest as math_ingest
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
    return {"unit": scope, "rows": rows}


def format_report(rep: dict) -> str:
    lines = [f"{rep['unit']}: {len(rep['rows'])} archetypes (earned/failed counts by level)"]
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


def _current_usage_evidence(
    data_root: str,
    variants_dir: str | None = None,
) -> tuple[dict[str, Counter], dict[str, Counter]]:
    """Return ``(drill_levels_by_key, variant_levels_by_key)`` from current canonical drills and non-quarantined variants."""
    drill_levels: dict[str, Counter] = defaultdict(Counter)
    for prefix in ("MTH-*", "PRG-*"):
        for path in sorted(glob.glob(os.path.join(data_root, prefix, "*.json"))):
            try:
                with open(path, encoding="utf-8") as f:
                    drill = json.load(f)
            except (OSError, ValueError):
                continue
            for prob in drill.get("problems") or []:
                if not isinstance(prob, dict):
                    continue
                key = prob.get("archetypeKey")
                lvl = prob.get("level")
                if isinstance(key, str) and key.strip() and isinstance(lvl, int):
                    drill_levels[key.strip()][lvl] += 1

    variant_levels: dict[str, Counter] = defaultdict(Counter)
    vdir = variants_dir or os.environ.get("VARIANTS_DIR") or os.path.join("drills", "variants")
    if os.path.isdir(vdir):
        for path in sorted(glob.glob(os.path.join(vdir, "MTH-*.json"))):
            try:
                with open(path, encoding="utf-8") as f:
                    bank = json.load(f)
            except (OSError, ValueError):
                continue
            if not isinstance(bank, dict) or bank.get("status") == "quarantined":
                continue
            for var in bank.get("variants") or []:
                if not isinstance(var, dict) or var.get("status") == "quarantined":
                    continue
                key = var.get("archetypeKey") or var.get("sourceArchetype")
                lvl = var.get("level")
                if isinstance(key, str) and key.strip() and isinstance(lvl, int):
                    variant_levels[key.strip()][lvl] += 1
    return drill_levels, variant_levels


def _historical_deleted_drill_usage(repo_root: str | None = None) -> dict[str, Counter]:
    """Read-only git-history scan of deleted canonical drill files under ``drills/data/``."""
    cwd = repo_root or os.getcwd()
    try:
        proc = subprocess.run(
            ["git", "log", "--diff-filter=D", "--name-only", "--pretty=format:COMMIT:%H", "--", "drills/data/"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if proc.returncode != 0:
        return {}

    deleted_paths: list[tuple[str, str]] = []
    seen_paths: set[str] = set()
    cur_commit = ""
    for line in proc.stdout.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("COMMIT:"):
            cur_commit = s.split(":", 1)[1].strip()
            continue
        if cur_commit and s.endswith(".json") and s.startswith("drills/data/") and s not in seen_paths:
            seen_paths.add(s)
            deleted_paths.append((cur_commit, s))

    hist: dict[str, Counter] = defaultdict(Counter)
    for commit, rel_path in deleted_paths:
        try:
            show = subprocess.run(
                ["git", "show", f"{commit}^:{rel_path}"],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if show.returncode != 0:
            continue
        try:
            drill = json.loads(show.stdout)
        except ValueError:
            continue
        for prob in drill.get("problems") or []:
            if not isinstance(prob, dict):
                continue
            key = prob.get("archetypeKey")
            lvl = prob.get("level")
            if isinstance(key, str) and key.strip() and isinstance(lvl, int):
                hist[key.strip()][lvl] += 1
    return hist


def usage_report(
    scope: str,
    vault_dir: str | None = None,
    data_root: str = "drills/data",
    variants_dir: str | None = None,
    *,
    include_history: bool = True,
    repo_root: str | None = None,
    current_evidence: tuple[dict[str, Counter], dict[str, Counter]] | None = None,
    historical_evidence: dict[str, Counter] | None = None,
) -> dict:
    """Compute read-only archetype and level usage for ``scope`` (current drills/variants vs git history)."""
    is_prg = scope.startswith("PRG-")
    resolved_vault = vault_dir if vault_dir is not None else (CODE_VAULT_DIR if is_prg else MATH_VAULT_DIR)
    resolve_dir = code_ingest._code_vault_dir if is_prg else math_ingest._vault_dir
    archetypes = load_scope_archetypes(scope, resolve_dir(resolved_vault), math_scope=not is_prg)

    if current_evidence is None:
        drill_levels, variant_levels = _current_usage_evidence(data_root, variants_dir=variants_dir)
    else:
        drill_levels, variant_levels = current_evidence

    if historical_evidence is None:
        hist_levels = _historical_deleted_drill_usage(repo_root=repo_root) if include_history else {}
    else:
        hist_levels = historical_evidence

    rows = []
    active_count = 0
    hist_only_count = 0
    unused_count = 0
    unused_keys: list[str] = []
    missing_base_keys: list[str] = []

    for a in sorted(archetypes, key=lambda x: (archetype_owner(x), x.get("level") or 0, x.get("archetypeKey") or "")):
        key = a["archetypeKey"]
        base = a.get("level")
        cur_d = dict(sorted(drill_levels.get(key, Counter()).items()))
        cur_v = dict(sorted(variant_levels.get(key, Counter()).items())) if not is_prg else {}
        hist_d = dict(sorted(hist_levels.get(key, Counter()).items()))
        if cur_d:
            status = "active"
            active_count += 1
        elif hist_d:
            status = "historical-only"
            hist_only_count += 1
        else:
            status = "unused"
            unused_count += 1
            unused_keys.append(key)
        missing_base = isinstance(base, int) and not cur_d.get(base)
        if missing_base:
            missing_base_keys.append(key)
        rows.append(
            {
                "key": key,
                "unit": archetype_owner(a),
                "baseLevel": base,
                "status": status,
                "currentDrillLevels": cur_d,
                "currentVariantLevels": cur_v,
                "historicalDrillLevels": hist_d,
                "missingBaseLevel": missing_base,
            }
        )

    total = len(rows)
    ever_used = active_count + hist_only_count
    return {
        "unit": scope,
        "archetypeCount": total,
        "activeCount": active_count,
        "historicalOnlyCount": hist_only_count,
        "unusedCount": unused_count,
        "everUsedCount": ever_used,
        "activeShare": round(active_count / total, 4) if total else 0.0,
        "everUsedShare": round(ever_used / total, 4) if total else 0.0,
        "unusedKeys": unused_keys,
        "missingBaseLevelKeys": missing_base_keys,
        "rows": rows,
    }


def format_usage_report(rep: dict) -> str:
    """Format ``usage_report`` with unused and historical-only archetypes first so authors prefer them."""
    total = rep["archetypeCount"]
    act = rep["activeCount"]
    ever = rep["everUsedCount"]
    pct_act = f"{rep['activeShare'] * 100:.1f}%" if total else "0.0%"
    pct_ever = f"{rep['everUsedShare'] * 100:.1f}%" if total else "0.0%"
    lines = [
        f"{rep['unit']} usage: {act}/{total} active ({pct_act}), {ever}/{total} ever-used ({pct_ever}), "
        f"{rep['unusedCount']} unused, {rep['historicalOnlyCount']} historical-only"
    ]
    order = {"unused": 0, "historical-only": 1, "active": 2}
    for r in sorted(rep["rows"], key=lambda x: (order.get(x["status"], 9), x["unit"], x["baseLevel"] or 0, x["key"])):
        d_str = ", ".join(f"L{lv}x{n}" for lv, n in r["currentDrillLevels"].items()) or "none"
        v_str = ", ".join(f"L{lv}x{n}" for lv, n in r["currentVariantLevels"].items())
        h_str = ", ".join(f"L{lv}x{n}" for lv, n in r["historicalDrillLevels"].items())
        tag = {"unused": "UNUSED", "historical-only": "HIST-ONLY", "active": "ACTIVE"}[r["status"]]
        parts = [f"drills {d_str}"]
        if v_str:
            parts.append(f"variants {v_str}")
        if h_str:
            parts.append(f"history {h_str}")
        if r["missingBaseLevel"] and r["status"] == "active":
            parts.append(f"missing base L{r['baseLevel']}")
        lines.append(f"  {tag:9s} [{r['unit']}] base L{r['baseLevel']} {r['key']}: {'; '.join(parts)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m scripts.vault_report", description=__doc__.split("\n\n")[0])
    ap.add_argument("unit", nargs="?", help="unit or chapter code (default: every MTH and PRG vault file)")
    ap.add_argument("--log", action="store_true", help="log FAILING archetypes to the issue log")
    ap.add_argument(
        "--usage",
        action="store_true",
        help="read-only archetype and level usage report (current drills/variants vs git history)",
    )
    ap.add_argument("--no-history", action="store_true", help="with --usage: skip git-history scan of retired drills")
    ap.add_argument("--json", action="store_true", help="with --usage: emit structured JSON output")
    ap.add_argument("--vault-dir", default=None)
    ap.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR", "drills/data"))
    ap.add_argument("--variants-dir", default=os.environ.get("VARIANTS_DIR") or None)
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

    if args.usage:
        cur_ev = _current_usage_evidence(args.data_root, variants_dir=args.variants_dir)
        hist_ev = {} if args.no_history else _historical_deleted_drill_usage(str(Path.cwd()))
        reports = [
            usage_report(
                scope,
                args.vault_dir,
                args.data_root,
                args.variants_dir,
                include_history=not args.no_history,
                current_evidence=cur_ev,
                historical_evidence=hist_ev,
            )
            for scope in scopes
        ]
        if args.json:
            payload = reports[0] if args.unit else {"scopes": reports}
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for rep in reports:
                print(format_usage_report(rep))
        return 0

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
