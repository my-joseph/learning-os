"""Read-only aggregate feedback brief for drill authoring (new-math-drill / new-code-drill).

Joins aggregate signals from:
- `scripts.weak_spots` (open traps, level advice, mastery cap, skipped archetypes)
- `scripts.drill_quality` (difficulty & ladder flags, per-level first-try clean rates)
- recent mistakes (ranked recurring mistake/trap tags across recent practice items)
- unit issues (`issues/log.jsonl` filtered to scope across all kinds)

Strictly aggregate-only and zero-leak: never outputs prompts, answers, worked steps,
learner inputs, personal notes, or drill, question, and issue locators. Practice breakdowns require at least three
distinct items, and recency is bucketed. Supports
`--no-progress` for offline/audit runs.

Usage:
    python -m scripts.authoring_signals <UNIT|CHAPTER> [--json] [--no-progress]
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

from ingest_core import archetype_trap_tags
from progress_store import find_repo_root
from scripts import drill_quality, issues, weak_spots

_SCOPE_CODE = re.compile(r"(?:MTH|PRG|PHY)-(?:T\d+-C\d+(?:-U\d+)?|BRIDGE)")
_SIGNAL_KEY = re.compile(r"(?!(?:DRL|LAB|VAR)-|Q\d+$)[A-Za-z0-9][A-Za-z0-9_-]*", re.IGNORECASE)


def _signal_key(value: Any) -> bool:
    return isinstance(value, str) and _SIGNAL_KEY.fullmatch(value) is not None


_MIN_ITEMS = 3
_RECENCY = ("last 7 days", "last 30 days", "older")


def _recency_bucket(value: str, today: date) -> str:
    try:
        age = (today - date.fromisoformat(value[:10])).days
    except ValueError:
        return ""
    if 0 <= age < 7:
        return _RECENCY[0]
    if 7 <= age < 30:
        return _RECENCY[1]
    return _RECENCY[2] if age >= 30 else ""


def _published_recency(items: list[weak_spots.Item], today: date) -> str:
    buckets = Counter(_recency_bucket(item.ts, today) for item in items)
    return next((bucket for bucket in _RECENCY if buckets[bucket] >= _MIN_ITEMS), "")


def _registered_labels(unit: str, root: str, vault: dict[str, Any]) -> set[str]:
    labels: set[str] = set()
    for arch in vault.values():
        labels.update(tag for tag in archetype_trap_tags(arch) if isinstance(tag, str))
        if unit.startswith("PRG-"):
            labels.update(
                check["id"]
                for check in arch.get("qualityChecks") or []
                if isinstance(check, dict) and isinstance(check.get("id"), str)
            )
    if unit.startswith("PRG-"):
        path = Path(root) / "code_engine" / "check_names.json"
        if path.is_file():
            labels.update(json.loads(path.read_text(encoding="utf-8")))
    return labels


def _item_tags(item: weak_spots.Item) -> list[str]:
    return item.signals if item.subject == "PRG" else item.matched


def _practice_signals(scope: str, items: list[weak_spots.Item], root: str) -> tuple[dict, list[dict]]:
    """Build each unit's breakdowns from distinct practiced items in groups of three or more."""
    today = date.today()
    units: dict[str, list[weak_spots.Item]] = defaultdict(list)
    for item in items:
        if item.unit == scope and scope.endswith("-BRIDGE"):
            units[scope].append(item)
        else:
            for unit in set(weak_spots._item_units(item)):
                if _SCOPE_CODE.fullmatch(unit) and weak_spots._unit_matches_scope(unit, scope):
                    units[unit].append(item)

    open_traps = []
    level_advice = {}
    mastery_caps = []
    skip_items: dict[str, set[tuple[str, str]]] = defaultdict(set)
    tag_items: dict[str, dict[tuple[str, str], weak_spots.Item]] = defaultdict(dict)
    tag_archetypes: dict[str, dict[str, set[tuple[str, str]]]] = defaultdict(lambda: defaultdict(set))
    unit_count = 0
    for unit, unit_items in sorted(units.items()):
        unique = {(item.drill, item.pid): item for item in unit_items}
        group_sizes = Counter((item.archetype, item.level) for item in unique.values())
        eligible = [item for item in unique.values() if group_sizes[item.archetype, item.level] >= _MIN_ITEMS]
        if not eligible:
            continue
        unit_count += 1
        vault = drill_quality._load_vault(unit, root)
        labels = _registered_labels(unit, root, vault)
        hits = defaultdict(list)
        for item in eligible:
            key = (item.drill, item.pid)
            if item.skipped and item.archetype in vault and _signal_key(item.archetype):
                skip_items[item.archetype].add(key)
            raw_tags = _item_tags(item)
            tags = {tag for tag in raw_tags if isinstance(tag, str) and tag in labels}
            for tag in tags:
                hits[tag].append(item)
                if item.archetype in vault and _signal_key(item.archetype):
                    tag_archetypes[tag][item.archetype].add(key)
            if any(not isinstance(tag, str) or tag not in labels for tag in raw_tags):
                tags.add("unrecognized")
            for tag in tags:
                tag_items[tag][key] = item

        # Evaluate open status with the same weak-spots logic, using registered
        # labels and eligible evidence only.
        recognized = [
            replace(
                item,
                matched=[tag for tag in item.matched if isinstance(tag, str) and tag in labels],
                signals=[tag for tag in item.signals if isinstance(tag, str) and tag in labels],
            )
            for item in eligible
        ]
        unit_open = [
            {
                "unit": unit,
                "tag": tag,
                "matches": len(hits[tag]),
                "last": _published_recency(hits[tag], today),
            }
            for tag, status in sorted(weak_spots.trap_status(recognized).items())
            if status["open"] and len(hits[tag]) >= _MIN_ITEMS
        ]
        open_traps.extend(unit_open)
        for level, advice in weak_spots.level_advice(eligible).items():
            if 1 <= level <= 5 and advice["n"] >= _MIN_ITEMS:
                key = f"L{level}" if unit == scope else f"{unit}@L{level}"
                level_advice[key] = advice["move"]
        if weak_spots.mastery_cap(eligible, bool(unit_open)).get("capped"):
            mastery_caps.append({"unit": unit, "cappedAt": 2})

    recent = [
        {
            "tag": tag,
            "count": len(matched),
            "last": _published_recency(list(matched.values()), today),
            "archetypes": sorted(key for key, evidence in tag_archetypes[tag].items() if len(evidence) >= _MIN_ITEMS),
        }
        for tag, matched in tag_items.items()
        if len(matched) >= _MIN_ITEMS
    ]
    bucket_order = {bucket: rank for rank, bucket in enumerate((*_RECENCY, ""))}
    recent.sort(key=lambda row: (-row["count"], bucket_order[row["last"]], row["tag"]))
    return {
        "unitCount": unit_count,
        "openTrapCount": len(open_traps),
        "openTraps": open_traps,
        "levelAdvice": level_advice,
        "skippedArchetypes": sorted(key for key, skipped in skip_items.items() if len(skipped) >= _MIN_ITEMS),
        "masteryCaps": mastery_caps,
    }, recent[:8]


def _unit_issues_summary(scope: str, *, issue_log: str | None = None) -> dict[str, Any]:
    """Count issues in scope. Read locators only to assign each record to its scope."""
    by_kind: Counter[str] = Counter()
    open_by_kind: Counter[str] = Counter()
    for record in issues.issues(issue_log):
        ref = issues.parse_where_reference(str(record.get("where") or ""))
        if not any(
            _SCOPE_CODE.fullmatch(unit) and weak_spots._unit_matches_scope(unit, scope) for unit in ref["scopes"]
        ):
            continue
        raw_kind = record.get("kind")
        kind = raw_kind if raw_kind in issues.KINDS else "other"
        by_kind[kind] += 1
        if not record.get("resolved"):
            open_by_kind[kind] += 1
    return {
        "total": sum(by_kind.values()),
        "openCount": sum(open_by_kind.values()),
        "byKind": dict(sorted((kind, count) for kind, count in by_kind.items() if count >= _MIN_ITEMS)),
        "openByKind": dict(sorted((kind, count) for kind, count in open_by_kind.items() if count >= _MIN_ITEMS)),
    }


def _build_signals_used_line(summary: dict[str, Any]) -> str:
    """Format a concise one-line `Signals used:` summary for a drill PR body."""
    parts: list[str] = []
    if not summary["progressRead"]:
        parts.append("progress skipped (--no-progress)")
    else:
        ws = summary["weakSpots"]
        if ws["unitCount"] > 0:
            parts.append(f"weak_spots ({ws['openTrapCount']} open trap(s), {len(ws['levelAdvice'])} level signal(s))")
        else:
            parts.append("weak_spots (no practice data)")
        dq = summary["drillQuality"]
        if dq["attempts"] > 0 or dq["flags"]:
            parts.append(f"drill_quality ({len(dq['flags'])} flag(s), {dq['attempts']} attempt(s))")
        else:
            parts.append("drill_quality (no practice data)")
        rm = summary["recentMistakes"]
        parts.append(f"recent_mistakes ({len(rm)} recurring tag(s))")
    iss = summary["issues"]
    parts.append(f"issues ({iss['openCount']} open / {iss['total']} total)")
    return "Signals used: " + "; ".join(parts)


def collect_authoring_signals(
    scope: str,
    *,
    no_progress: bool = False,
    data_root: str | None = None,
    progress_dir: str | None = None,
    repo_root: str | None = None,
    issue_log: str | None = None,
) -> dict[str, Any]:
    """Collect read-only, zero-leak aggregate feedback signals for ``scope``."""
    if not _SCOPE_CODE.fullmatch(scope):
        raise ValueError("Expected a unit or chapter code.")
    resolved_data = data_root or os.environ.get("DRILLS_DATA_DIR", "drills/data")
    unit_issues = _unit_issues_summary(scope, issue_log=issue_log)

    if no_progress:
        summary: dict[str, Any] = {
            "scope": scope,
            "progressRead": False,
            "weakSpots": {
                "unitCount": 0,
                "openTrapCount": 0,
                "openTraps": [],
                "levelAdvice": {},
                "skippedArchetypes": [],
                "masteryCaps": [],
            },
            "drillQuality": {
                "drills": 0,
                "attempts": 0,
                "levelCleanRates": {},
                "flags": [],
            },
            "recentMistakes": [],
            "issues": unit_issues,
        }
        summary["signalsUsedLine"] = _build_signals_used_line(summary)
        return summary

    root = repo_root or find_repo_root()
    items = weak_spots.load_items(resolved_data, progress_dir)
    weak_summary, recent_mistakes = _practice_signals(scope, items, root)

    # 2. drill_quality aggregates (respect explicit progress_dir / data_root via env override cleanly)
    prev_prog = os.environ.get("PROGRESS_DIR")
    prev_data = os.environ.get("DRILLS_DATA_DIR")
    try:
        if progress_dir is not None:
            os.environ["PROGRESS_DIR"] = progress_dir
        if data_root is not None:
            os.environ["DRILLS_DATA_DIR"] = data_root
        dq_raw = drill_quality.build_report(scope, repo_root=root)
    finally:
        if progress_dir is not None:
            if prev_prog is None:
                os.environ.pop("PROGRESS_DIR", None)
            else:
                os.environ["PROGRESS_DIR"] = prev_prog
        if data_root is not None:
            if prev_data is None:
                os.environ.pop("DRILLS_DATA_DIR", None)
            else:
                os.environ["DRILLS_DATA_DIR"] = prev_data

    level_clean_rates = {}
    for lv, stats in sorted(dq_raw["levels"].items()):
        if not re.fullmatch(r"L[1-5]", lv) or stats["items"] < _MIN_ITEMS:
            continue
        rate = stats["firstTryCleanRate"]
        level_clean_rates[lv] = {
            "items": stats["items"],
            "attempts": stats["attempts"] if stats["attempts"] >= _MIN_ITEMS else None,
            "firstTryCleanRate": round(rate, 3)
            if rate is not None and sum(stats["scores"].values()) >= _MIN_ITEMS
            else None,
            "skips": stats["skips"] if stats["skips"] >= _MIN_ITEMS else None,
        }

    vault = drill_quality._load_vault(scope, root)
    dq_flags = []
    for flag in dq_raw["flags"]:
        kind = flag.get("type")
        if kind not in drill_quality._FLAG_ORDER:
            continue
        archetype = flag.get("archetype")
        if archetype is not None and (not _signal_key(archetype) or archetype not in vault):
            continue
        level = flag.get("level")
        if level is not None and (type(level) is not int or not 1 <= level <= 5):
            continue
        level_key = f"L{level}"
        stats = dq_raw["archetypes"].get(archetype, {})
        if level is not None:
            levels = stats.get("levels", {}) if archetype is not None else dq_raw["levels"]
            stats = levels.get(level_key, {})
        support = flag.get("items") if kind == "untouched" else stats.get("items", 0)
        if type(support) is not int or support < _MIN_ITEMS:
            continue
        if kind in {"trap_never_triggered", "similar_never_opened"} and sum(stats["scores"].values()) < _MIN_ITEMS:
            continue
        slim = {"type": kind}
        if archetype is not None:
            slim["archetype"] = archetype
        if level is not None:
            slim["level"] = level
        if kind == "untouched":
            slim["items"] = support
        if kind == "level_ladder_gap":
            slim["missing"] = [lv for lv in flag["missing"] if isinstance(lv, str) and re.fullmatch(r"L[1-5]", lv)]
        dq_flags.append(slim)

    summary = {
        "scope": scope,
        "progressRead": True,
        "weakSpots": weak_summary,
        "drillQuality": {
            "drills": int(dq_raw.get("drills") or 0),
            "attempts": sum(row["attempts"] or 0 for row in level_clean_rates.values()),
            "levelCleanRates": level_clean_rates,
            "flags": dq_flags,
        },
        "recentMistakes": recent_mistakes,
        "issues": unit_issues,
    }
    summary["signalsUsedLine"] = _build_signals_used_line(summary)
    return summary


def format_authoring_signals(summary: dict[str, Any]) -> str:
    """Format ``collect_authoring_signals`` as a concise worker-spec summary (zero-leak)."""
    lines = [f"Authoring feedback signals for {summary['scope']} (aggregates only; no answers)"]
    if not summary["progressRead"]:
        lines.append("  Practice signals: skipped (--no-progress)")
    else:
        ws = summary["weakSpots"]
        if ws["openTraps"]:
            traps_txt = ", ".join(f"{t['tag']} ({t['matches']}x)" for t in ws["openTraps"])
            lines.append(f"  Weak spots (open): {traps_txt}")
        else:
            lines.append("  Weak spots (open): none")
        if ws["levelAdvice"]:
            lvl_txt = ", ".join(f"{k}={v}" for k, v in sorted(ws["levelAdvice"].items()))
            lines.append(f"  Level advice: {lvl_txt}")
        if ws["masteryCaps"]:
            cap_txt = ", ".join(f"{c['unit']} capped at {c['cappedAt']}" for c in ws["masteryCaps"])
            lines.append(f"  Mastery cap: {cap_txt}")
        if ws["skippedArchetypes"]:
            lines.append(f"  Skipped archetypes: {', '.join(ws['skippedArchetypes'])}")

        dq = summary["drillQuality"]
        if dq["levelCleanRates"]:
            rate_bits = []
            for lv, st in dq["levelCleanRates"].items():
                pct = f"{st['firstTryCleanRate'] * 100:.0f}%" if st["firstTryCleanRate"] is not None else "n/a"
                attempts = f" ({st['attempts']} att)" if st["attempts"] is not None else ""
                rate_bits.append(f"{lv}={pct}{attempts}")
            lines.append(f"  Drill quality clean rates: {', '.join(rate_bits)}")
        if dq["flags"]:
            flag_bits = [
                f"{f['type']}({f.get('archetype') or 'L' + str(f['level'])})"
                if "archetype" in f or "level" in f
                else f["type"]
                for f in dq["flags"][:8]
            ]
            lines.append(f"  Drill quality flags ({len(dq['flags'])}): {', '.join(flag_bits)}")
        else:
            lines.append("  Drill quality flags: none")

        rm = summary["recentMistakes"]
        if rm:
            rm_bits = [f"{row['tag']} x{row['count']}" + (f" ({row['last']})" if row["last"] else "") for row in rm[:6]]
            lines.append(f"  Recent mistakes: {', '.join(rm_bits)}")
        else:
            lines.append("  Recent mistakes: none")

    iss = summary["issues"]
    if iss["total"]:
        kind_bits = ", ".join(f"{k}:{n}" for k, n in iss["byKind"].items())
        kinds = f" ({kind_bits})" if kind_bits else ""
        lines.append(f"  Unit issues: {iss['openCount']} open / {iss['total']} total{kinds}")
    else:
        lines.append("  Unit issues: none")
    lines.append(f"  {summary['signalsUsedLine']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.authoring_signals",
        description="Print read-only aggregate authoring feedback signals (weak_spots, drill_quality, recent mistakes, unit issues).",
    )
    parser.add_argument("scope", help="Unit or chapter code (e.g. MTH-T02-C01-U01 or PRG-T01-C01-U01).")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    parser.add_argument("--no-progress", action="store_true", help="Skip reading progress/ (offline/audit mode).")
    parser.add_argument("--data-root", default=None, help="Override drills data directory.")
    parser.add_argument("--progress-dir", default=None, help="Override progress directory.")
    parser.add_argument("--issue-log", default=None, help="Override issue log path.")
    args = parser.parse_args(argv)
    if not _SCOPE_CODE.fullmatch(args.scope):
        parser.error("expected a unit or chapter code")

    summary = collect_authoring_signals(
        args.scope,
        no_progress=args.no_progress,
        data_root=args.data_root,
        progress_dir=args.progress_dir,
        issue_log=args.issue_log,
    )
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(format_authoring_signals(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
