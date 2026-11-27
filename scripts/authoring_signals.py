"""Read-only aggregate feedback brief for drill authoring (new-math-drill / new-code-drill).

Joins aggregate signals from:
- `scripts.weak_spots` (open traps, level advice, mastery cap, skipped archetypes)
- `scripts.drill_quality` (difficulty & ladder flags, per-level first-try clean rates)
- recent mistakes (ranked recurring mistake/trap tags across recent practice items)
- unit issues (`issues/log.jsonl` filtered to scope across all kinds)

Strictly aggregate-only and zero-leak: never outputs prompts, answers, worked steps,
learner inputs, personal notes, or drill, question, and issue locators. Supports
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
from datetime import date
from typing import Any

from scripts import drill_quality, issues, weak_spots

_SCOPE_CODE = re.compile(r"(?:MTH|PRG|PHY)-(?:T\d+-C\d+(?:-U\d+)?|BRIDGE)")
_SIGNAL_KEY = re.compile(r"(?!(?:DRL|LAB|VAR)-|Q\d+$)[A-Za-z0-9][A-Za-z0-9_-]*", re.IGNORECASE)


def _signal_key(value: Any) -> bool:
    return isinstance(value, str) and _SIGNAL_KEY.fullmatch(value) is not None


def _signal_date(value: Any) -> str:
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError:
        return ""


def _recent_mistakes_summary(
    scoped: list[weak_spots.Item],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Rank recurring mistake/trap tags in ``scope`` (aggregate counts + archetypes only; no inputs/notes)."""
    counts: Counter[str] = Counter()
    last_ts: dict[str, str] = {}
    archetypes: dict[str, set[str]] = defaultdict(set)

    for it in scoped:
        tags = list(it.matched)
        if it.skipped and "concept-gap" not in tags:
            tags.append("concept-gap")
        for tag in dict.fromkeys(t for t in tags if _signal_key(t)):
            counts[tag] += 1
            if it.ts and it.ts > last_ts.get(tag, ""):
                last_ts[tag] = it.ts
            if it.archetype and _signal_key(it.archetype):
                archetypes[tag].add(it.archetype)

    # Secondary sort: most recent timestamp first when counts tie.
    ranked = sorted(
        counts.items(), key=lambda kv: (-kv[1], -(int(re.sub(r"\D", "", last_ts.get(kv[0], ""))[:14] or 0)))
    )
    return [
        {
            "tag": tag,
            "count": int(cnt),
            "last": _signal_date(last_ts.get(tag)),
            "archetypes": sorted(archetypes.get(tag) or ()),
        }
        for tag, cnt in ranked[:limit]
    ]


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
        "byKind": dict(sorted(by_kind.items())),
        "openByKind": dict(sorted(open_by_kind.items())),
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

    # 1. weak_spots aggregates
    ws_raw = weak_spots.report_json(scope, data_root=resolved_data, progress_dir=progress_dir)
    ws_units = [u for u in ws_raw.get("units") or [] if _SCOPE_CODE.fullmatch(str(u.get("unitCode") or ""))]
    open_traps: list[dict[str, Any]] = []
    level_advice_map: dict[str, str] = {}
    mastery_caps: list[dict[str, Any]] = []
    for u in ws_units:
        uc = str(u.get("unitCode") or "")
        for t in u.get("open") or []:
            if not _signal_key(t.get("id")):
                continue
            open_traps.append(
                {
                    "unit": uc,
                    "tag": t["id"],
                    "matches": int(t.get("matches") or 0),
                    "drills": int(t.get("drills") or 0),
                    "last": _signal_date(t.get("last")),
                }
            )
        for lv_str, adv in (u.get("levels") or {}).items():
            if (
                re.fullmatch(r"[1-5]", str(lv_str))
                and isinstance(adv, dict)
                and adv.get("move") in ("up", "down", "stay")
            ):
                key = f"{uc}@L{lv_str}" if len(ws_units) > 1 else f"L{lv_str}"
                level_advice_map[key] = str(adv["move"])
        cap = u.get("masteryCap")
        if isinstance(cap, dict) and cap.get("capped"):
            mastery_caps.append(
                {
                    "unit": uc,
                    "cappedAt": 2,
                }
            )

    # 2. drill_quality aggregates (respect explicit progress_dir / data_root via env override cleanly)
    prev_prog = os.environ.get("PROGRESS_DIR")
    prev_data = os.environ.get("DRILLS_DATA_DIR")
    try:
        if progress_dir is not None:
            os.environ["PROGRESS_DIR"] = progress_dir
        if data_root is not None:
            os.environ["DRILLS_DATA_DIR"] = data_root
        dq_raw = drill_quality.build_report(scope, repo_root=repo_root)
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

    level_clean_rates: dict[str, dict[str, Any]] = {}
    for lv, stats in sorted((dq_raw.get("levels") or {}).items()):
        if not re.fullmatch(r"L[1-5]", lv):
            continue
        rate = stats.get("firstTryCleanRate")
        level_clean_rates[lv] = {
            "items": int(stats.get("items") or 0),
            "attempts": int(stats.get("attempts") or 0),
            "firstTryCleanRate": round(float(rate), 3) if rate is not None else None,
            "skips": int(stats.get("skips") or 0),
        }

    # Keep only structured aggregate flag fields (never raw prose or answers).
    dq_flags: list[dict[str, Any]] = []
    for f in dq_raw.get("flags") or []:
        if not isinstance(f, dict) or f.get("type") not in drill_quality._FLAG_ORDER:
            continue
        slim = {"type": f["type"]}
        if _signal_key(f.get("archetype")):
            slim["archetype"] = f["archetype"]
        if type(f.get("level")) is int and 1 <= f["level"] <= 5:
            slim["level"] = f["level"]
        if isinstance(f.get("missing"), list):
            slim["missing"] = [lv for lv in f["missing"] if isinstance(lv, str) and re.fullmatch(r"L[1-5]", lv)]
        if type(f.get("items")) is int:
            slim["items"] = f["items"]
        dq_flags.append(slim)

    # 3. recent mistakes aggregates
    scoped_items = [
        item
        for item in weak_spots.load_items(resolved_data, progress_dir)
        if item.unit == scope or any(weak_spots._unit_matches_scope(u, scope) for u in weak_spots._item_units(item))
    ]
    recent_mistakes = _recent_mistakes_summary(scoped_items)
    skipped_archs = {item.archetype for item in scoped_items if item.skipped and _signal_key(item.archetype)}

    summary = {
        "scope": scope,
        "progressRead": True,
        "weakSpots": {
            "unitCount": len(ws_units),
            "openTrapCount": len(open_traps),
            "openTraps": open_traps,
            "levelAdvice": level_advice_map,
            "skippedArchetypes": sorted(skipped_archs),
            "masteryCaps": mastery_caps,
        },
        "drillQuality": {
            "drills": int(dq_raw.get("drills") or 0),
            "attempts": int(dq_raw.get("attempts") or 0),
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
            traps_txt = ", ".join(f"{t['tag']} ({t['matches']}x/{t['drills']}d)" for t in ws["openTraps"])
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
                rate_bits.append(f"{lv}={pct} ({st['attempts']} att)")
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
            rm_bits = [f"{m['tag']} x{m['count']}" for m in rm[:6]]
            lines.append(f"  Recent mistakes: {', '.join(rm_bits)}")
        else:
            lines.append("  Recent mistakes: none")

    iss = summary["issues"]
    if iss["total"]:
        kind_bits = ", ".join(f"{k}:{n}" for k, n in iss["byKind"].items())
        lines.append(f"  Unit issues: {iss['openCount']} open / {iss['total']} total ({kind_bits})")
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
