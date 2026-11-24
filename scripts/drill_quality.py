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

from progress_store import cycle_evidence, find_repo_root, is_timestamp_in_cycle, progress_root, score_problem
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


def _similar_slots_opened(state: dict[str, Any]) -> bool:
    """Read Similar slot tokens through their variant records, scoped to the active cycle."""
    slots = state.get("similarSlots")
    variants = state.get("variants")
    if not isinstance(slots, list):
        return False
    cycle_start = state.get("cycleStartedAt")
    cycle_start = cycle_start if isinstance(cycle_start, str) and cycle_start else None

    def current(timestamp: Any) -> bool:
        return isinstance(timestamp, str) and bool(timestamp) and is_timestamp_in_cycle(timestamp, cycle_start)

    for slot in slots:
        # Current schema stores opaque token strings with activity in state.variants[token].
        record = variants.get(slot) if isinstance(slot, str) and isinstance(variants, dict) else None
        # Keep reading pre-token records for existing historical progress files.
        if record is None and isinstance(slot, dict):
            record = slot
        if not isinstance(record, dict) or record.get("role", "try") != "try":
            continue
        if current(record.get("servedAt")):
            return True
        attempts = record.get("attempts")
        if isinstance(attempts, list):
            if cycle_start is None and attempts:
                return True
            if any(isinstance(attempt, dict) and current(attempt.get("ts")) for attempt in attempts):
                return True
    return False


def _add_state(stats: dict[str, Any], problem: dict[str, Any], state: dict[str, Any], is_prg: bool) -> None:
    stats["items"] += 1
    evidence = cycle_evidence(state)
    attempts = evidence["substantiveAttempts"]
    reviews = evidence["reviews"]
    stats["attempts"] += len(attempts) + (len(reviews) if is_prg else 0)
    scored = score_problem(state, is_prg=is_prg)
    score = scored["score"]
    if score is not None:
        label = "1" if score == 1 else "0.5" if score == 0.5 else "0"
        stats["scores"][label] += 1
        if scored["firstTry"] and score == 1:
            stats["firstTryClean"] += 1
    stats["hintUses"] += evidence["hintUses"]
    stats["stepsRevealed"] += int(evidence["stepsRevealed"])
    stats["solutionRevealed"] += int(evidence["solutionRevealed"])
    stats["skips"] += int(scored["outcome"] == "skipped")
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
    untouched_by_arch_level: Counter[tuple[str, int]] = Counter()
    untouched_drills: list[str] = []
    matched_progress_files = 0

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
        drill_has_activity = False
        if drill_id in progress:
            matched_progress_files += 1
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
            has_evidence = scored["score"] is not None or any(
                state.get(field)
                for field in (
                    "attempts",
                    "userInput",
                    "hintsRevealed",
                    "stepsRevealed",
                    "solutionRevealedBeforeAnswer",
                    "solutionRevealed",
                    "revealed",
                    "reviews",
                    "reviewHintRevealedAt",
                    "reviewSetupRevealedAt",
                    "reviewStepsRevealedAt",
                    "exampleViewedAt",
                    "selfScoreAt",
                )
            )
            if not has_evidence:
                untouched.append(f"{drill_id}/{pid}")
                if isinstance(level, int):
                    untouched_by_arch_level[(key, level)] += 1
            else:
                drill_has_activity = True
            if isinstance(level, int):
                _add_state(by_level[f"L{level}"], problem, state, is_prg)
            _add_state(by_arch[key], problem, state, is_prg)
            item_meta[key] = {
                "unit": problem.get("unitCode") or drill.get("unitCode"),
                "subject": "PRG" if is_prg else "MTH",
            }
            opened = _similar_slots_opened(state)
            if key in similar_keys and opened:
                similar_opened.add(key)
            if isinstance(level, int):
                _add_state(arch_levels[key][level], problem, state, is_prg)
        if not drill_has_activity:
            untouched_drills.append(drill_id)

    archetypes = {}
    flags = []
    for key in sorted(set(vault) | set(by_arch) | set(declared)):
        stats = by_arch[key]
        score_total = sum(stats["scores"].values())
        clean_rate = stats["firstTryClean"] / score_total if score_total else None
        levels = sorted(declared.get(key, set()))
        archetypes[key] = {
            **item_meta.get(key, {}),
            "baseLevel": vault.get(key, {}).get("level"),
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
        if stats["attempts"] >= 2:
            untriggered = sorted(trap for trap in stats["trapTags"] if stats["matchedTraps"].get(trap, 0) == 0)
            if untriggered:
                flags.append(
                    {
                        "type": "trap_never_triggered",
                        "archetype": key,
                        "trapCount": len(untriggered),
                        "traps": untriggered,
                    }
                )
        if not stats["items"]:
            flags.append({"type": "archetype_never_drilled", "archetype": key})
        if (
            key in similar_keys
            and not archetypes[key]["similarOpened"]
            and item_meta.get(key, {}).get("subject") != "PRG"
        ):
            flags.append({"type": "similar_never_opened", "archetype": key})
        base_level = vault.get(key, {}).get("level")
        ladder_start = base_level if isinstance(base_level, int) else 1
        ladder = {f"L{lv}" for lv in set(range(max(1, ladder_start), 5)) - set(levels)}
        if levels and ladder:
            flags.append({"type": "level_ladder_gap", "archetype": key, "missing": sorted(ladder)})

    for level, stats in sorted(by_level.items()):
        total = sum(stats["scores"].values())
        rate = stats["firstTryClean"] / total if total else None
        if total >= 3 and rate is not None and rate >= 0.9:
            flags.append({"type": "level_too_easy", "level": level, "recommendation": "step up"})
        elif total >= 3 and rate is not None and rate <= 0.3:
            flags.append({"type": "level_too_hard", "level": level, "recommendation": "add scaffolding or lower level"})

    for (key, level), count in sorted(untouched_by_arch_level.items()):
        flags.append({"type": "untouched", "archetype": key, "level": level, "items": count})

    return {
        "scope": scope,
        "progressDir": progress_root(root),
        "drills": len(drills),
        "matchedProgressFiles": matched_progress_files,
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
        "untouchedDrills": sorted(untouched_drills),
        "untouchedItems": untouched,
        "qcReviewTotals": {
            "pass": sum(s.get("qcPasses", 0) for s in by_arch.values()),
            "fail": sum(s.get("qcFails", 0) for s in by_arch.values()),
        },
    }


_FLAG_ORDER = {
    "too_hard": 0,
    "level_too_hard": 0,
    "too_easy": 1,
    "level_too_easy": 1,
    "trap_never_triggered": 2,
    "level_ladder_gap": 3,
    "archetype_never_drilled": 4,
    "similar_never_opened": 5,
    "untouched": 6,
}


def _flag_level(flag: dict[str, Any], report: dict[str, Any]) -> str:
    level = flag.get("level")
    if isinstance(level, int):
        return f"L{level}"
    key = flag.get("archetype")
    arch = report["archetypes"].get(key, {})
    levels = arch.get("declaredLevels", [])
    return f"L{levels[0]}" if levels else f"L{arch['baseLevel']}" if arch.get("baseLevel") else "L?"


def _format_flag(flag: dict[str, Any], report: dict[str, Any]) -> str:
    kind = flag["type"]
    key = flag.get("archetype", "all archetypes")
    subject = f"{key}@{_flag_level(flag, report)}"
    reasons = {
        "too_hard": "low first-try clean rate; add scaffolding or lower level",
        "level_too_hard": "low first-try clean rate; add scaffolding",
        "too_easy": "high first-try clean rate; step up a level",
        "level_too_easy": "high first-try clean rate; step up",
        "archetype_never_drilled": "no practice items yet",
        "similar_never_opened": "Similar variants have not been opened",
    }
    if kind == "level_ladder_gap":
        missing = ", ".join(flag.get("missing", []))
        return f"{key}@{_flag_level(flag, report)} missing {missing}"
    if kind == "trap_never_triggered":
        reasons[kind] = f"{flag['trapCount']} expected trap(s) never triggered"
    if kind == "untouched":
        reasons[kind] = f"{flag['items']} item(s) have no practice activity"
    return f"{subject} — {reasons.get(kind, 'review practice evidence')}"


def format_report(report: dict[str, Any], *, show_all: bool = False) -> str:
    """Render a concise human-readable report without learner answer content."""
    lines = [
        f"{report['scope']}: {report['drills']} drills, {report['items']} items, {report['attempts']} recorded attempts"
    ]
    if report["drills"] and not report.get("matchedProgressFiles"):
        lines.append(f"no practice data found in {report['progressDir']}")
    for level, row in report["levels"].items():
        rate = "n/a" if row["firstTryCleanRate"] is None else f"{row['firstTryCleanRate']:.0%}"
        lines.append(
            f"  {level}: items={row['items']} attempts={row['attempts']} first-try-clean={rate} hints={row['hintUses']} steps={row['stepsRevealed']} skips={row['skips']} scores={row['scores']}"
        )
    lines.append("Archetypes: key | levels seen | attempts | clean | reveals")
    for key, row in sorted(report["archetypes"].items()):
        levels = ",".join(f"L{lv}" for lv in row["declaredLevels"]) or "—"
        rate = "n/a" if row["firstTryCleanRate"] is None else f"{row['firstTryCleanRate']:.0%}"
        reveals = row["stepsRevealed"] + row["solutionRevealed"]
        lines.append(f"  {key} | {levels} | {row['attempts']} | {rate} | {reveals}")
    text_flags = [flag for flag in report["flags"] if flag["type"] not in {"level_too_easy", "level_too_hard"}]
    lines.append(
        f"Flags: {len(text_flags)}; untouched drills: {len(report['untouchedDrills'])}; QC pass/fail: {report['qcReviewTotals']['pass']}/{report['qcReviewTotals']['fail']}"
    )
    flags = sorted(
        text_flags,
        key=lambda flag: (
            _FLAG_ORDER.get(flag["type"], 99),
            str(flag.get("archetype", "")),
            _flag_level(flag, report),
        ),
    )
    if flags:
        lines.append("Flags by kind (most actionable first):")
        kinds = sorted({flag["type"] for flag in flags}, key=lambda kind: _FLAG_ORDER.get(kind, 99))
        shown = 0
        for kind in kinds:
            lines.append(f"  {kind}:")
            for flag in (item for item in flags if item["type"] == kind):
                if not show_all and len(lines) >= 29:
                    lines.append(f"  … {len(flags) - shown} more; use --all to show all flags")
                    return "\n".join(lines)
                lines.append(f"    {_format_flag(flag, report)}")
                shown += 1
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", help="unit or chapter code, e.g. MTH-T02-C01-U01")
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    parser.add_argument("--all", action="store_true", help="show all flags in text output")
    args = parser.parse_args(argv)
    report = build_report(args.scope)
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_report(report, show_all=args.all))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
