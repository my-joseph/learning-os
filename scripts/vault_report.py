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


def _build_problem_index(
    data_root: str,
) -> tuple[dict[tuple[str, str], tuple[str, int | None]], dict[tuple[str, str], list[tuple[str, int | None]]]]:
    """Index committed drills by ``(drillId, QID)`` and ``(scope, QID)`` -> ``(archetypeKey, level)``."""
    by_drill_qid: dict[tuple[str, str], tuple[str, int | None]] = {}
    by_scope_qid: dict[tuple[str, str], list[tuple[str, int | None]]] = defaultdict(list)
    for prefix in ("MTH-*", "PRG-*"):
        for path in sorted(glob.glob(os.path.join(data_root, prefix, "*.json"))):
            try:
                with open(path, encoding="utf-8") as f:
                    drill = json.load(f)
            except (OSError, ValueError):
                continue
            did = str(drill.get("drillId") or os.path.splitext(os.path.basename(path))[0])
            scope = str(drill.get("unitCode") or os.path.basename(os.path.dirname(path)))
            for idx, prob in enumerate(drill.get("problems", []), 1):
                if not isinstance(prob, dict):
                    continue
                qid = str(prob.get("id") or f"Q{idx:02d}").strip()
                m_q = re.fullmatch(r"Q(\d{1,2})", qid, re.IGNORECASE)
                norm_qid = f"Q{int(m_q.group(1)):02d}" if m_q else qid
                key = prob.get("archetypeKey")
                lvl = prob.get("level") if isinstance(prob.get("level"), int) else None
                if isinstance(key, str) and key.strip():
                    pair = (key.strip(), lvl)
                    by_drill_qid[(did, norm_qid)] = pair
                    if pair not in by_scope_qid[(scope, norm_qid)]:
                        by_scope_qid[(scope, norm_qid)].append(pair)
    return by_drill_qid, by_scope_qid


def _scope_matches(candidate: str, scope: str) -> bool:
    return candidate == scope or candidate.startswith(scope + "-U")


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
    arch_by_key = {a["archetypeKey"]: a for a in archetypes if a.get("archetypeKey")}
    if earned is None:
        earned = _evidence(data_root)
    by_drill_qid, by_scope_qid = _build_problem_index(data_root)

    failed: dict[str, Counter] = defaultdict(Counter)
    gate_failed: Counter[str] = Counter()
    scope_failures: list[dict[str, str | None]] = []

    for rec in issues.issues(log):
        kind = rec.get("kind")
        if kind not in ("level", "gate-gap"):
            continue
        raw_where = str(rec.get("where") or "")
        parsed = issues.parse_where_reference(raw_where)
        canon_where = str(parsed["canonical"])
        explicit_level = parsed["level"] if isinstance(parsed["level"], int) else None
        matched_any = False

        # 1. Direct archetype match (canonical `<SCOPE>/<key>[@Ln]` or path-normalised vault reference)
        for key, arch in arch_by_key.items():
            m = re.search(rf"(?:^|[\s/]){re.escape(key)}(?:@L(\d+))?(?:\s*\(vault\))?(?:$|[\s),;])", canon_where)
            if m:
                matched_any = True
                if kind == "level":
                    lv = int(m.group(1)) if m.group(1) else (explicit_level or arch.get("level"))
                    failed[key][lv] += 1
                else:
                    gate_failed[key] += 1

        # 2. Legacy or canonical `<DRILL_ID>/<QID>` (or path-normalised drill JSON) resolved via drills/data
        if not matched_any:
            seen_targets: set[tuple[str, int | None]] = set()
            for did, qid in parsed["drillQids"]:
                hit = by_drill_qid.get((did, qid))
                if hit and hit[0] in arch_by_key:
                    arch_key, prob_lv = hit
                    target_lv = explicit_level or prob_lv or arch_by_key[arch_key].get("level")
                    if (arch_key, target_lv) not in seen_targets:
                        seen_targets.add((arch_key, target_lv))
                        matched_any = True
                        if kind == "level":
                            failed[arch_key][target_lv] += 1
                        else:
                            gate_failed[arch_key] += 1

        # 3. Legacy `<SCOPE>/<QID>` resolved unambiguously via committed drills in that scope
        if not matched_any and parsed["qids"]:
            seen_targets = set()
            for sc in parsed["scopes"]:
                if not _scope_matches(sc, scope):
                    continue
                for qid in parsed["qids"]:
                    candidates = [h for h in by_scope_qid.get((sc, qid), []) if h[0] in arch_by_key]
                    if len(candidates) == 1:
                        arch_key, prob_lv = candidates[0]
                        target_lv = explicit_level or prob_lv or arch_by_key[arch_key].get("level")
                        if (arch_key, target_lv) not in seen_targets:
                            seen_targets.add((arch_key, target_lv))
                            matched_any = True
                            if kind == "level":
                                failed[arch_key][target_lv] += 1
                            else:
                                gate_failed[arch_key] += 1

        # 4. Unattributed scope-level failure (retired drill, draft path, or drill-level issue)
        if not matched_any and any(_scope_matches(sc, scope) for sc in parsed["scopes"]):
            scope_failures.append(
                {
                    "id": str(rec.get("id") or ""),
                    "kind": str(kind),
                    "where": canon_where,
                    "action": str(rec.get("action") or ""),
                    "resolved": rec.get("resolved"),
                }
            )

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
                "gateFailed": int(gate_failed[key]),
                "levelNote": bool(a.get("levelNote")),
                "flags": flags,
            }
        )
    return {"unit": scope, "rows": rows, "scopeFailures": scope_failures}


def format_report(rep: dict) -> str:
    lines = [f"{rep['unit']}: {len(rep['rows'])} archetypes (earned/failed counts by level)"]
    for r in sorted(rep["rows"], key=lambda r: (r["unit"], r["level"] or 0, r["key"])):
        earned = ", ".join(f"L{lv}x{n}" for lv, n in r["earned"].items()) or "none"
        failed = ", ".join(f"L{lv}x{n}" for lv, n in r["failed"].items())
        gate_n = int(r.get("gateFailed") or 0)
        tail = (
            (f"  failed {failed}" if failed else "")
            + (f"  gate-gap x{gate_n}" if gate_n else "")
            + (" note" if r["levelNote"] else "")
        )
        flags = f"  {' '.join(r['flags'])}" if r["flags"] else ""
        lines.append(f"  [{r['unit']}] base L{r['level']} {r['key']}: earned {earned}{tail}{flags}")
    scope_failures = rep.get("scopeFailures") or []
    if scope_failures:
        summary_bits = ", ".join(f"[{f['id']}] {f['kind']} {f['where']}" for f in scope_failures)
        lines.append(f"  Scope level/gate issues ({len(scope_failures)} unattributed): {summary_bits}")
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
