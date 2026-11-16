"""Weak spots from the learner's own practice: which traps they keep falling into, and what to drill next.

Read-only. Joins learner progress (`progress/<DRILL_ID>.json`, gitignored) with drill content
(`drills/data/<SCOPE>/<DRILL_ID>.json`) and applies `rules/07` §2-3:
- a trap is a **weak spot** when the learner's wrong answers matched it (`matchedTrap`) at least twice;
- it **closes** after the last 2 drills that contained it were answered right every time it came up
  (unassisted), and reopens on any new match;
- per unit and level, the last 5 items decide **up** (>= 80% and at least one reverse-form item),
  **down** (< 50%) or **stay**. An item scores 1 when the first answer was right with no set-up box or hint,
  0.5 when it was right later or with help, 0 when wrong or skipped.

    python -m scripts.weak_spots                      # every unit with practice data
    python -m scripts.weak_spots MTH-T01-C04          # one chapter (all its units) or one unit
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from code_engine.quality_checks import load_universal
from scripts.issues import main_checkout_root

MIN_MATCHES = 2
CLOSE_AFTER = 2
WINDOW = 5


@dataclass
class Item:
    drill: str
    unit: str
    pid: str
    level: int | None
    form: str
    trap: str | None
    archetype: str | None
    ts: str
    score: float
    skipped: bool
    assisted: bool
    matched: list[str] = field(default_factory=list)
    subject: str = "MTH"
    passed: bool = False
    signals: list[str] = field(default_factory=list)
    applicable_checks: set[str] = field(default_factory=set)
    lint_overrides: set[str] = field(default_factory=set)


def _is_prg(doc: dict) -> bool:
    return (
        doc.get("subject") == "PRG"
        or str(doc.get("unitCode", "")).startswith("PRG-")
        or str(doc.get("drillId", "")).startswith("DRL-PRG-")
    )


def _first_ts(state: dict, fallback: str) -> str:
    attempts = state.get("attempts") or []
    if attempts:
        return attempts[0].get("ts", fallback)
    reviews = state.get("reviews") or []
    if reviews:
        return reviews[0].get("at", fallback)
    return fallback


def _prg_item_score(state: dict) -> float:
    if state.get("skipped"):
        return 0.0
    reviews = state.get("reviews") or []
    if reviews:
        if reviews[-1].get("verdict") == "pass":
            return 1.0 if reviews[0].get("verdict") == "pass" else 0.5
        return 0.0
    if state.get("lastTestReport") is not None or state.get("score") is not None:
        return 0.0
    return -1.0


def _item_score(state: dict) -> tuple[float, bool]:
    attempts = state.get("attempts") or []
    assisted = bool(state.get("setupRevealedBeforeAnswer") or (state.get("hintsRevealed") or 0) > 0)
    assisted = assisted or any(a.get("setupRevealed") for a in attempts)
    if state.get("skipped"):
        return 0.0, assisted
    if attempts:
        first = attempts[0].get("verdict")
        if first == "correct" and not assisted:
            return 1.0, assisted
        if any(a.get("verdict") in ("correct", "equivalent_not_in_form", "partial") for a in attempts):
            return 0.5, assisted
        return 0.0, assisted
    score = state.get("score")
    if score is None:
        return -1.0, assisted  # not attempted
    return (min(float(score), 0.5) if assisted else float(score)), assisted


def _load_prg_vault_meta() -> tuple[dict[str, str], dict[str, int], dict[str, set[str]], dict[str, str]]:
    """Return (unit_of, level_of, arch_check_ids, check_sentences) from PRG vaults & universal checks."""
    unit_of: dict[str, str] = {}
    level_of: dict[str, int] = {}
    arch_checks: dict[str, set[str]] = {}
    sentences: dict[str, str] = {}

    for c in load_universal():
        if isinstance(c, dict) and c.get("id") and c.get("check"):
            sentences[c["id"]] = c["check"]

    cwd_vault = os.path.join("code_engine", "reasoning_vault")
    vault_dir = (
        cwd_vault if os.path.isdir(cwd_vault) else os.path.join(main_checkout_root(), "code_engine", "reasoning_vault")
    )
    for vpath in sorted(glob.glob(os.path.join(vault_dir, "*.json"))):
        with open(vpath, encoding="utf-8") as f:
            for a in json.load(f).get("archetypes", []):
                key = a.get("archetypeKey")
                if not key:
                    continue
                if a.get("unitCode"):
                    unit_of[key] = a["unitCode"]
                if isinstance(a.get("level"), int):
                    level_of[key] = a["level"]
                cids: set[str] = set()
                for c in a.get("qualityChecks") or []:
                    if isinstance(c, dict) and c.get("id"):
                        cids.add(c["id"])
                        if c.get("check"):
                            sentences[c["id"]] = c["check"]
                arch_checks[key] = cids
    return unit_of, level_of, arch_checks, sentences


def load_items(data_root: str | None = None, progress_dir: str | None = None) -> list[Item]:
    data_root = data_root or os.environ.get("DRILLS_DATA_DIR", "drills/data")
    progress_dir = progress_dir or os.environ.get("PROGRESS_DIR") or os.path.join(main_checkout_root(), "progress")
    drills = {}
    for pattern in ("MTH-*", "PRG-*"):
        for path in glob.glob(os.path.join(data_root, pattern, "*.json")):
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
            if doc.get("drillId"):
                drills[doc["drillId"]] = doc
    # Problems ingested before archetypes carried `unitCode` get their unit from the archetype.
    unit_of = {}
    for vpath in glob.glob(os.path.join("math_engine", "reasoning_vault", "*.json")):
        with open(vpath, encoding="utf-8") as f:
            for a in json.load(f).get("archetypes", []):
                if a.get("unitCode"):
                    unit_of[a.get("archetypeKey")] = a["unitCode"]
    prg_unit_of, prg_level_of, prg_arch_checks, _ = _load_prg_vault_meta()
    unit_of.update({k: v for k, v in prg_unit_of.items() if k not in unit_of})
    universal_ids = {c["id"] for c in load_universal() if isinstance(c, dict) and c.get("id")}

    items: list[Item] = []
    for path in sorted(glob.glob(os.path.join(progress_dir, "*.json"))):
        with open(path, encoding="utf-8") as f:
            prog = json.load(f)
        doc = drills.get(prog.get("drillId"))
        if not doc:
            continue
        is_prg = _is_prg(doc)
        lint_overrides = {o.get("rule") for o in (doc.get("lintOverrides") or []) if o.get("rule")}
        fallback = prog.get("updatedAt", "")
        for prob in doc.get("problems", []):
            state = (prog.get("problems") or {}).get(prob.get("id")) or {}
            arch_key = prob.get("archetypeKey")
            if is_prg:
                score = _prg_item_score(state)
                if score < 0:
                    continue
                reviews = state.get("reviews") or []
                sigs: list[str] = []
                for r in reviews:
                    for finding in r.get("findings") or []:
                        if not finding.get("disputed") and finding.get("check") and finding["check"] not in sigs:
                            sigs.append(finding["check"])
                    for lint_err in r.get("lint") or []:
                        rule = lint_err.get("rule")
                        if rule and rule not in sigs:
                            sigs.append(rule)
                level = prob.get("level")
                if level is None and arch_key:
                    level = prg_level_of.get(arch_key)
                items.append(
                    Item(
                        drill=doc["drillId"],
                        unit=prob.get("unitCode") or unit_of.get(arch_key) or doc.get("unitCode", ""),
                        pid=prob.get("id", ""),
                        level=level,
                        form=prob.get("archetype") or prob.get("codeType") or prob.get("form", ""),
                        trap=prob.get("commonTrapTag"),
                        archetype=arch_key,
                        ts=_first_ts(state, fallback),
                        score=score,
                        skipped=bool(state.get("skipped")),
                        assisted=False,
                        matched=[],
                        subject="PRG",
                        passed=bool(reviews and reviews[-1].get("verdict") == "pass"),
                        signals=sigs,
                        applicable_checks=universal_ids | prg_arch_checks.get(arch_key or "", set()),
                        lint_overrides=lint_overrides,
                    )
                )
            else:
                score, assisted = _item_score(state)
                if score < 0:
                    continue
                items.append(
                    Item(
                        drill=doc["drillId"],
                        unit=prob.get("unitCode") or unit_of.get(arch_key) or doc.get("unitCode", ""),
                        pid=prob.get("id", ""),
                        level=prob.get("level"),
                        form=prob.get("form", ""),
                        trap=prob.get("commonTrapTag"),
                        archetype=arch_key,
                        ts=_first_ts(state, fallback),
                        score=score,
                        skipped=bool(state.get("skipped")),
                        assisted=assisted,
                        matched=[a["matchedTrap"] for a in state.get("attempts") or [] if a.get("matchedTrap")],
                        subject="MTH",
                        passed=(score == 1.0),
                    )
                )
    return sorted(items, key=lambda i: i.ts)


def _is_prg_signal_applicable(sig: str, item: Item) -> bool:
    if sig.startswith(("U-", "QC-")):
        return sig in item.applicable_checks
    return sig not in item.lint_overrides


def trap_status(items: list[Item]) -> dict[str, dict]:
    """Per trap (MTH) or check/lint rule (PRG): matches, drills, last match, and open status."""
    out: dict[str, dict] = {}
    mth_items = [i for i in items if i.subject != "PRG"]
    traps = {t for i in mth_items for t in i.matched} | {i.trap for i in mth_items if i.trap}
    for trap in traps:
        hits = [i for i in mth_items if trap in i.matched]
        n = sum(i.matched.count(trap) for i in hits)
        if n < MIN_MATCHES:
            continue
        last_hit = max(i.ts for i in hits)
        # drills that contained the trap, after the last match, in order
        later: dict[str, list[Item]] = defaultdict(list)
        for i in mth_items:
            if (i.trap == trap or trap in i.matched) and i.ts > last_hit and trap not in i.matched:
                later[i.drill].append(i)
        clean = [d for d, its in later.items() if all(x.score == 1.0 for x in its)]
        out[trap] = {
            "matches": n,
            "drills": len({i.drill for i in hits}),
            "last": last_hit[:10],
            "units": sorted({i.unit for i in hits}),
            "open": len(clean) < CLOSE_AFTER,
            "subject": "MTH",
        }

    prg_items = [i for i in items if i.subject == "PRG"]
    prg_signals = {s for i in prg_items for s in i.signals}
    for sig in prg_signals:
        hits = [(idx, i) for idx, i in enumerate(prg_items) if sig in i.signals]
        if len(hits) < MIN_MATCHES:
            continue
        last_idx, last_hit = hits[-1]
        later_clean = [
            i
            for i in prg_items[last_idx + 1 :]
            if i.passed and _is_prg_signal_applicable(sig, i) and sig not in i.signals
        ]
        out[sig] = {
            "matches": len(hits),
            "drills": len({i.drill for _, i in hits}),
            "last": last_hit.ts[:10],
            "units": sorted({i.unit for _, i in hits}),
            "open": len(later_clean) < CLOSE_AFTER,
            "subject": "PRG",
        }
    return out


def level_advice(items: list[Item]) -> dict[int, dict]:
    by_level: dict[int, list[Item]] = defaultdict(list)
    for i in items:
        if isinstance(i.level, int):
            by_level[i.level].append(i)
    advice = {}
    for lv, its in sorted(by_level.items()):
        last = its[-WINDOW:]
        pct = round(100 * sum(x.score for x in last) / len(last))
        is_prg = any(x.subject == "PRG" for x in last)
        has_variety = (
            any(x.form in ("debugging", "refactoring") for x in last)
            if is_prg
            else any(x.form == "reverse" for x in last)
        )
        if len(last) >= WINDOW and pct >= 80 and has_variety:
            move = "up"
        elif pct < 50:
            move = "down"
        else:
            move = "stay"
        advice[lv] = {"pct": pct, "n": len(last), "move": move}
    return advice


MASTERY_WINDOW = 10
REVIEW_DAYS = {1: 2, 2: 5, 3: 17, 4: 45}  # rules/01 §8 intervals (mid-points)


def suggest_mastery(unit_items: list[Item], open_weak_spot: bool) -> int | None:
    """Evidence-based Mastery (0-4) for one unit from its last items (rules/01 §7).

    1 under 50%; 3 when at least 3 recent L3+ items average >= 70% and no weak spot is open; otherwise 2.
    Drills cannot show 4 (Feynman explanation, cross-subject synthesis), so the learner sets 4 by hand.
    """
    recent = unit_items[-MASTERY_WINDOW:]
    if not recent:
        return None
    pct = sum(i.score for i in recent) / len(recent)
    if pct < 0.5:
        return 1
    hard = [i for i in recent if isinstance(i.level, int) and i.level >= 3]
    if len(hard) >= 3 and sum(i.score for i in hard) / len(hard) >= 0.7 and not open_weak_spot:
        return 3
    return 2


def review_update(
    unit: str, current_mastery: int | None, attempt_date: str, data_root: str | None = None, progress_dir=None
) -> dict | None:
    """Mastery, Last Reviewed and Next Review for a unit page after practice, or None without evidence.
    A learner-set 4 is kept while the evidence still says 3 (drills cannot confirm or refute 4)."""
    items = [i for i in load_items(data_root, progress_dir) if i.unit == unit]
    open_weak = any(s["open"] and unit in s["units"] for s in trap_status(items).values())
    mastery = suggest_mastery(items, open_weak)
    if mastery is None:
        return None
    if current_mastery == 4 and mastery == 3:
        mastery = 4
    nxt = date.fromisoformat(attempt_date[:10]) + timedelta(days=REVIEW_DAYS[mastery])
    return {"mastery": mastery, "lastReviewed": attempt_date[:10], "nextReview": nxt.isoformat()}


def report(scope: str | None = None, data_root: str = "drills/data", progress_dir: str | None = None) -> str:
    items = load_items(data_root, progress_dir)
    if scope:
        items = [i for i in items if i.unit == scope or i.unit.startswith(scope + "-U")]
    if not items:
        return "No practice data yet" + (f" for {scope}" if scope else "") + ". Practise a drill in the Studio first."
    titles = {}
    if os.path.exists("id_map.json"):
        with open("id_map.json", encoding="utf-8") as f:
            titles = {k: v.get("title", "") for k, v in json.load(f).items() if isinstance(v, dict)}
    traps = trap_status(items)
    _, _, _, check_sentences = _load_prg_vault_meta()
    lines = []
    for unit in sorted({i.unit for i in items}):
        its = [i for i in items if i.unit == unit]
        lines.append(f"{unit} · {titles.get(unit, '')}  ({len(its)} items in {len({i.drill for i in its})} drills)")
        open_traps = [t for t, s in traps.items() if s["open"] and unit in s["units"]]
        closed = [t for t, s in traps.items() if not s["open"] and unit in s["units"]]
        for t in sorted(open_traps, key=lambda t: traps[t]["last"], reverse=True):
            s = traps[t]
            label = f"{t} ({check_sentences[t]})" if t in check_sentences else t
            lines.append(f"  WEAK     {label}: matched {s['matches']}x in {s['drills']} drill(s), last {s['last']}")
        for t in closed:
            s = traps[t]
            label = f"{t} ({check_sentences[t]})" if t in check_sentences else t
            if s.get("subject") == "PRG":
                lines.append(f"  closed   {label}: clean in the last {CLOSE_AFTER} problems that tested it")
            else:
                lines.append(f"  closed   {label}: clean in the last {CLOSE_AFTER} drills that tested it")
        adv = level_advice(its)
        if adv:
            lines.append(
                "  levels   " + " · ".join(f"L{lv} {a['pct']}% ({a['n']}) {a['move']}" for lv, a in adv.items())
            )
        assisted = sum(i.assisted for i in its)
        if assisted:
            lines.append(f"  assisted {assisted} item(s) answered after opening the set-up box or a hint")
        skipped = sorted({i.archetype or i.pid for i in its if i.skipped})
        if skipped:
            lines.append(f"  skipped  {', '.join(skipped)}")
        if open_traps:
            lines.append(f"  NEXT     new drill for {unit} focused on {', '.join(open_traps[:2])}")
        lines.append("")
    return "\n".join(lines).rstrip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m scripts.weak_spots", description=__doc__.split("\n\n")[0])
    ap.add_argument("scope", nargs="?", help="unit or chapter code (default: all units with practice data)")
    ap.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR", "drills/data"))
    ap.add_argument("--progress-dir", default=None)
    args = ap.parse_args(argv)
    print(report(args.scope, args.data_root, args.progress_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
