"""Read-only analysis of learner practice quality by archetype and level.

Usage: python -m scripts.drill_quality <UNIT|CHAPTER> [--json]

The report joins drill content to local progress without modifying either. Progress
location follows ``PROGRESS_DIR`` and ``LEARNINGOS_PILOT`` via progress_store.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import Counter, defaultdict
from typing import Any

from progress_store import find_repo_root, progress_root, score_problem
from scripts.weak_spots import _collect_matched_traps, _is_prg


def _scope_match(value: str, scope: str) -> bool:
    return value == scope or (len(scope.split("-")) == 3 and value.startswith(scope + "-"))


def _load_vault(scope: str, repo_root: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for pattern in ("math_engine/reasoning_vault/*.json", "code_engine/reasoning_vault/*.json"):
        for path in glob.glob(os.path.join(repo_root, pattern)):
            try:
                doc = json.load(open(path, encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for arch in doc.get("archetypes", []):
                owner = arch.get("unitCode") or doc.get("unitCode", "")
                units = arch.get("unitCodes") or [owner]
                if any(isinstance(unit, str) and _scope_match(unit, scope) for unit in units):
                    key = arch.get("archetypeKey")
                    if key:
                        result[key] = arch
    return result


def _load_data(scope: str, repo_root: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    data_root = os.environ.get("DRILLS_DATA_DIR", os.path.join(repo_root, "drills", "data"))
    drills: list[dict[str, Any]] = []
    for path in glob.glob(os.path.join(data_root, "*", "*.json")):
        try:
            doc = json.load(open(path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not _scope_match(str(doc.get("unitCode", "")), scope):
            continue
        drills.append(doc)
    progress: dict[str, dict[str, Any]] = {}
    for path in glob.glob(os.path.join(progress_root(repo_root), "*.json")):
        try:
            record = json.load(open(path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(record, dict) and record.get("drillId"):
            progress[record["drillId"]] = record
    return drills, progress


def _empty_stats() -> dict[str, Any]:
    return {
        "items": 0,
        "attempts": 0,
        "firstTryClean": 0,
        "hintUses": 0,
        "stepsRevealed": 0,
        "solutionRevealed": 0,
        "skips": 0,
        "durationMs": [],
        "scores": Counter(),
        "trapTags": Counter(),
        "matchedTraps": Counter(),
        "qcPasses": 0,
        "qcFails": 0,
    }


def _add_state(stats: dict[str, Any], problem: dict[str, Any], state: dict[str, Any], is_prg: bool) -> None:
    stats["items"] += 1
    attempts = [a for a in state.get("attempts", []) if isinstance(a, dict)]
    reviews = [r for r in state.get("reviews", []) if isinstance(r, dict)]
    stats["attempts"] += len(attempts) + (len(reviews) if is_prg else 0)
    scored = score_problem(state, is_prg=is_prg)
    score = scored["score"]
    if score is not None:
        label = "1" if score == 1 else "0.5" if score == 0.5 else "0"
        stats["scores"][label] += 1
        if scored["firstTry"] and score == 1:
            stats["firstTryClean"] += 1
    stats["hintUses"] += int(state.get("hintsRevealed") or 0)
    stats["stepsRevealed"] += int(bool(state.get("stepsRevealed") or state.get("solutionRevealedBeforeAnswer")))
    stats["solutionRevealed"] += int(bool(state.get("solutionRevealedBeforeAnswer")))
    stats["skips"] += int(bool(state.get("skipped")))
    duration = state.get("durationMs")
    if isinstance(duration, (int, float)) and duration >= 0:
        stats["durationMs"].append(float(duration))
    trap = problem.get("commonTrapTag")
    if trap:
        stats["trapTags"][str(trap)] += 1
    for tag in _collect_matched_traps(state):
        stats["matchedTraps"][tag] += 1
    # PRG review records are the authoritative pass/fail QC evidence.
    for review in reviews:
        stats["qcPasses"] += int(review.get("verdict") == "pass")
        stats["qcFails"] += int(review.get("verdict") != "pass")


def build_report(scope: str, *, repo_root: str | None = None) -> dict[str, Any]:
    """Build a JSON-safe practice quality report for a unit or chapter."""
    root = repo_root or find_repo_root()
    drills, progress = _load_data(scope, root)
    vault = _load_vault(scope, root)
    by_arch: dict[str, dict[str, Any]] = defaultdict(_empty_stats)
    by_level: dict[str, dict[str, Any]] = defaultdict(_empty_stats)
    declared: dict[str, set[int]] = defaultdict(set)
    item_meta: dict[str, dict[str, Any]] = {}
    similar_opened: set[str] = set()
    similar_keys: set[str] = set()
    untouched: list[str] = []

    variants_root = os.environ.get("VARIANTS_DIR", os.path.join(root, "drills", "variants"))
    if os.path.isdir(variants_root):
        for path in glob.glob(os.path.join(variants_root, "*.json")):
            try:
                bank = json.load(open(path, encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            unit = bank.get("unitCode", "")
            if not _scope_match(unit, scope):
                continue
            for variant in bank.get("variants", []):
                if variant.get("sourceArchetype"):
                    similar_keys.add(str(variant["sourceArchetype"]))

    arch_levels: dict[str, dict[int, dict[str, Any]]] = defaultdict(lambda: defaultdict(_empty_stats))
    for drill in drills:
        drill_id = str(drill.get("drillId", ""))
        prog = progress.get(drill_id, {})
        states = prog.get("problems", {}) if isinstance(prog.get("problems"), dict) else {}
        is_prg = _is_prg(drill)
        for problem in drill.get("problems", []):
            if not isinstance(problem, dict):
                continue
            pid = str(problem.get("id", ""))
            key = str(problem.get("archetypeKey") or problem.get("templateKey") or "(unclassified)")
            level = problem.get("level")
            if isinstance(level, int):
                declared[key].add(level)
            state = states.get(pid, {}) if isinstance(states, dict) else {}
            if not isinstance(state, dict):
                state = {}
            scored = score_problem(state, is_prg=is_prg)
            has_evidence = scored["score"] is not None or bool(state.get("attempts") or state.get("reviews"))
            if not has_evidence:
                untouched.append(f"{drill_id}/{pid}")
            if isinstance(level, int):
                _add_state(by_level[f"L{level}"], problem, state, is_prg)
            _add_state(by_arch[key], problem, state, is_prg)
            item_meta[key] = {
                "unit": problem.get("unitCode") or drill.get("unitCode"),
                "subject": "PRG" if is_prg else "MTH",
            }
            seen = state.get("similarSlots") or []
            if key in similar_keys and isinstance(seen, list) and seen:
                similar_opened.add(key)
            if isinstance(level, int):
                _add_state(arch_levels[key][level], problem, state, is_prg)

    archetypes = {}
    flags = []
    for key in sorted(set(vault) | set(by_arch) | set(declared)):
        stats = by_arch[key]
        score_total = sum(stats["scores"].values())
        clean_rate = stats["firstTryClean"] / score_total if score_total else None
        levels = sorted(declared.get(key, set()))
        archetypes[key] = {
            **item_meta.get(key, {}),
            "attempts": stats["attempts"],
            "items": stats["items"],
            "firstTryClean": stats["firstTryClean"],
            "firstTryCleanRate": clean_rate,
            "hintUses": stats["hintUses"],
            "stepsRevealed": stats["stepsRevealed"],
            "solutionRevealed": stats["solutionRevealed"],
            "skips": stats["skips"],
            "timeMsMean": sum(stats["durationMs"]) / len(stats["durationMs"]) if stats["durationMs"] else None,
            "scores": dict(stats["scores"]),
            "levels": {
                f"L{lv}": {
                    "items": arch_levels[key][lv]["items"],
                    "attempts": arch_levels[key][lv]["attempts"],
                    "firstTryClean": arch_levels[key][lv]["firstTryClean"],
                    "firstTryCleanRate": (
                        arch_levels[key][lv]["firstTryClean"] / sum(arch_levels[key][lv]["scores"].values())
                        if arch_levels[key][lv]["scores"]
                        else None
                    ),
                    "hintUses": arch_levels[key][lv]["hintUses"],
                    "stepsRevealed": arch_levels[key][lv]["stepsRevealed"],
                    "skips": arch_levels[key][lv]["skips"],
                    "scores": dict(arch_levels[key][lv]["scores"]),
                }
                for lv in levels
            },
            "trapTags": dict(stats["trapTags"]),
            "matchedTraps": dict(stats["matchedTraps"]),
            "similarOpened": key in similar_opened,
            "declaredLevels": levels,
        }
        for lv in levels:
            lev = arch_levels[key][lv]
            count = sum(lev["scores"].values())
            rate = lev["firstTryClean"] / count if count else None
            if count >= 3 and rate is not None and rate >= 0.9:
                flags.append({"type": "too_easy", "archetype": key, "level": lv, "recommendation": "step up a level"})
            if count >= 3 and rate is not None and rate <= 0.3:
                flags.append(
                    {
                        "type": "too_hard",
                        "archetype": key,
                        "level": lv,
                        "recommendation": "add scaffolding or lower the level",
                    }
                )
        for trap in stats["trapTags"]:
            if stats["matchedTraps"].get(trap, 0) == 0:
                flags.append({"type": "trap_never_triggered", "archetype": key, "trap": trap})
        if not stats["items"]:
            flags.append({"type": "archetype_never_drilled", "archetype": key})
        if (
            key in similar_keys
            and not archetypes[key]["similarOpened"]
            and item_meta.get(key, {}).get("subject") != "PRG"
        ):
            flags.append({"type": "similar_never_opened", "archetype": key})
        ladder = {f"L{lv}" for lv in range(1, 5)} - set(levels)
        if levels and ladder:
            flags.append({"type": "level_ladder_gap", "archetype": key, "missing": sorted(ladder)})

    for level, stats in sorted(by_level.items()):
        total = sum(stats["scores"].values())
        rate = stats["firstTryClean"] / total if total else None
        if total >= 3 and rate is not None and rate >= 0.9:
            flags.append({"type": "level_too_easy", "level": level, "recommendation": "step up"})
        elif total >= 3 and rate is not None and rate <= 0.3:
            flags.append({"type": "level_too_hard", "level": level, "recommendation": "add scaffolding or lower level"})

    untouched_drills = sorted({item.split("/", 1)[0] for item in untouched})
    return {
        "scope": scope,
        "progressDir": progress_root(root),
        "drills": len(drills),
        "items": sum(s["items"] for s in by_arch.values()),
        "attempts": sum(s["attempts"] for s in by_arch.values()),
        "archetypes": archetypes,
        "levels": {
            level: {
                "items": stats["items"],
                "attempts": stats["attempts"],
                "firstTryClean": stats["firstTryClean"],
                "firstTryCleanRate": stats["firstTryClean"] / sum(stats["scores"].values())
                if stats["scores"]
                else None,
                "hintUses": stats["hintUses"],
                "stepsRevealed": stats["stepsRevealed"],
                "solutionRevealed": stats["solutionRevealed"],
                "skips": stats["skips"],
                "scores": dict(stats["scores"]),
            }
            for level, stats in sorted(by_level.items())
        },
        "flags": flags,
        "similarNeverOpened": [key for key in sorted(similar_keys) if not archetypes.get(key, {}).get("similarOpened")],
        "untouchedDrills": untouched_drills,
        "untouchedItems": untouched,
        "qcReviewTotals": {
            "pass": sum(s.get("qcPasses", 0) for s in by_arch.values()),
            "fail": sum(s.get("qcFails", 0) for s in by_arch.values()),
        },
    }


def format_report(report: dict[str, Any]) -> str:
    """Render a concise human-readable report without learner answer content."""
    lines = [
        f"{report['scope']}: {report['drills']} drills, {report['items']} items, {report['attempts']} recorded attempts"
    ]
    for level, row in report["levels"].items():
        rate = "n/a" if row["firstTryCleanRate"] is None else f"{row['firstTryCleanRate']:.0%}"
        lines.append(
            f"  {level}: items={row['items']} attempts={row['attempts']} first-try-clean={rate} hints={row['hintUses']} steps={row['stepsRevealed']} skips={row['skips']} scores={row['scores']}"
        )
    lines.append(
        f"Flags: {len(report['flags'])}; untouched drills: {len(report['untouchedDrills'])}; QC pass/fail: {report['qcReviewTotals']['pass']}/{report['qcReviewTotals']['fail']}"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", help="unit or chapter code, e.g. MTH-T02-C01-U01")
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = parser.parse_args(argv)
    report = build_report(args.scope)
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
