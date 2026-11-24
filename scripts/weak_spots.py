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
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from code_engine.quality_checks import load_universal
from math_engine.bridge import BRIDGE_SCOPE, problem_unit_codes
from progress_store import find_repo_root, item_score, progress_root, score_problem
from progress_store import labs_root as default_labs_root

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
    revisit_note: str | None = None
    state: dict = field(default_factory=dict)
    units: tuple[str, ...] = ()


def _item_units(item: Item) -> tuple[str, ...]:
    """Return all concrete units an Item attributes evidence to (multi-unit for bridge problems)."""
    if item.units:
        return item.units
    return (item.unit,) if item.unit else ()


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


def _is_assisted_state(state: dict) -> bool:
    return bool(score_problem(state)["usedHelp"])


def _collect_matched_traps(state: dict) -> list[str]:
    """Collect matchedTrap tags from original attempts and server-stored variant attempts."""
    matched = [a["matchedTrap"] for a in (state.get("attempts") or []) if isinstance(a, dict) and a.get("matchedTrap")]
    variants = state.get("variants")
    if isinstance(variants, dict):
        for token in sorted(variants.keys()):
            rec = variants.get(token)
            if not isinstance(rec, dict):
                continue
            for a in rec.get("attempts") or []:
                if isinstance(a, dict) and a.get("matchedTrap"):
                    matched.append(a["matchedTrap"])
    return matched


def _prg_item_score(state: dict) -> float:
    sc, _ = item_score(state, is_prg=True)
    return sc


_item_score = item_score


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
        cwd_vault if os.path.isdir(cwd_vault) else os.path.join(find_repo_root(), "code_engine", "reasoning_vault")
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


def prior_review_evidence(state: dict, cycle: str) -> dict:
    """Keep historical attempts and reviews without current-cycle summary fields."""
    return {
        field: [
            record
            for record in (state.get(field) or [])
            if isinstance(record, dict)
            and (not isinstance(recorded_at := record.get(timestamp) or record.get("ts"), str) or recorded_at < cycle)
        ]
        for field, timestamp in (("attempts", "ts"), ("reviews", "at"))
    }


def load_items(
    data_root: str | None = None,
    progress_dir: str | None = None,
    labs_root: str | None = None,
    *,
    for_review_schedule: bool = False,
) -> list[Item]:
    repo_root = find_repo_root()
    data_root = data_root or os.environ.get("DRILLS_DATA_DIR", os.path.join(repo_root, "drills", "data"))
    progress_dir = progress_dir or progress_root(repo_root)
    labs_root = labs_root or default_labs_root(repo_root)
    drills = {}
    for pattern in ("MTH-*", "PRG-*"):
        for path in glob.glob(os.path.join(data_root, pattern, "*.json")):
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
            if doc.get("drillId"):
                drills[doc["drillId"]] = doc
    for path in glob.glob(os.path.join(labs_root, "LAB-*", "lab.config.json")):
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        lab_id = cfg.get("labId")
        if not lab_id:
            continue
        drills[lab_id] = {
            "drillId": lab_id,
            "subject": "PRG",
            "unitCode": cfg.get("chapterCode") or (cfg.get("unitsUsed") or [""])[0],
            "problems": [
                {
                    "id": ms["id"],
                    "level": cfg.get("level"),
                    "unitCode": (ms.get("units") or [cfg.get("chapterCode", "")])[0],
                    "archetype": "project-based",
                    "qualityChecks": ms.get("qualityChecks") or [],
                }
                for ms in cfg.get("milestones") or []
                if isinstance(ms, dict) and ms.get("id")
            ],
        }
    # Problems ingested before archetypes carried `unitCode` get their unit from the archetype.
    unit_of = {}
    units_of: dict[str, tuple[str, ...]] = {}
    cwd_mth_vault = os.path.join("math_engine", "reasoning_vault")
    mth_vault_dir = (
        cwd_mth_vault if os.path.isdir(cwd_mth_vault) else os.path.join(repo_root, "math_engine", "reasoning_vault")
    )
    for vpath in glob.glob(os.path.join(mth_vault_dir, "*.json")):
        with open(vpath, encoding="utf-8") as f:
            for a in json.load(f).get("archetypes", []):
                key = a.get("archetypeKey")
                if not key:
                    continue
                if a.get("unitCode"):
                    unit_of[key] = a["unitCode"]
                if isinstance(a.get("unitCodes"), list) and a["unitCodes"]:
                    units_of[key] = tuple(u.strip() for u in a["unitCodes"] if isinstance(u, str) and u.strip())
    prg_unit_of, prg_level_of, prg_arch_checks, _ = _load_prg_vault_meta()
    unit_of.update({k: v for k, v in prg_unit_of.items() if k not in unit_of})
    universal_ids = {c["id"] for c in load_universal() if isinstance(c, dict) and c.get("id")}

    items: list[Item] = []
    for path in sorted(glob.glob(os.path.join(progress_dir, "*.json"))):
        with open(path, encoding="utf-8") as f:
            prog = json.load(f)
        if not isinstance(prog, dict):
            continue
        doc = drills.get(prog.get("drillId"))
        if not doc:
            continue
        is_prg = _is_prg(doc)
        lint_overrides = {o.get("rule") for o in (doc.get("lintOverrides") or []) if o.get("rule")}
        fallback = prog.get("updatedAt", "") or (prog.get("sessionSummary") or {}).get("attemptDate") or ""
        for prob in doc.get("problems", []):
            state = (prog.get("problems") or {}).get(prob.get("id")) or {}
            arch_key = prob.get("archetypeKey") or prob.get("templateKey")
            raw_note = state.get("revisitNote")
            revisit_note = raw_note.strip() if isinstance(raw_note, str) and raw_note.strip() else None
            scored = score_problem(state, is_prg=is_prg)
            cycle = state.get("cycleStartedAt")
            if scored["score"] is None and for_review_schedule and isinstance(cycle, str) and cycle:
                scored = score_problem(prior_review_evidence(state, cycle), is_prg=is_prg)
            if scored["score"] is None:
                continue
            score = float(scored["score"])
            assisted = bool(scored["usedHelp"])
            if is_prg:
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
                        trap=prob.get("commonTrapTag") or (sigs[0] if sigs else None),
                        archetype=arch_key,
                        ts=_first_ts(state, fallback),
                        score=score,
                        skipped=scored["outcome"] == "skipped",
                        assisted=assisted,
                        matched=[],
                        subject="PRG",
                        passed=scored["outcome"] in ("correct", "assisted"),
                        signals=sigs,
                        applicable_checks=(
                            universal_ids | set(prob.get("qualityChecks") or [])
                            if prob.get("qualityChecks")
                            else universal_ids | prg_arch_checks.get(arch_key or "", set())
                        ),
                        lint_overrides=lint_overrides,
                        revisit_note=revisit_note,
                        state=dict(state),
                    )
                )
            else:
                fallback_unit = unit_of.get(arch_key) or doc.get("unitCode", "")
                prob_units = problem_unit_codes(
                    prob,
                    fallback_unit=fallback_unit,
                    arch_units=units_of.get(arch_key or "", ()),
                )
                primary_unit = (
                    BRIDGE_SCOPE
                    if doc.get("unitCode") == BRIDGE_SCOPE and len(prob_units) >= 2
                    else (prob_units[0] if prob_units else fallback_unit)
                )
                items.append(
                    Item(
                        drill=doc["drillId"],
                        unit=primary_unit,
                        pid=prob.get("id", ""),
                        level=prob.get("level"),
                        form=prob.get("form", ""),
                        trap=prob.get("commonTrapTag"),
                        archetype=arch_key,
                        ts=_first_ts(state, fallback),
                        score=score,
                        skipped=scored["outcome"] == "skipped",
                        assisted=assisted,
                        matched=_collect_matched_traps(state),
                        subject="MTH",
                        passed=(score == 1.0),
                        revisit_note=revisit_note,
                        state=dict(state),
                        units=tuple(prob_units) if prob_units else ((primary_unit,) if primary_unit else ()),
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
            "units": sorted({u for i in hits for u in _item_units(i)}),
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
            "units": sorted({u for _, i in hits for u in _item_units(i)}),
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
L4_CHALLENGE_CAP_REASON = "needs one L4 challenge without hints"
OPEN_WEAK_SPOT_CAP_REASON = "open weak spot"
ASSISTED_CAP_REASON = "assisted L3+ answers weighted below fluent"


def _effective_mastery_score(item: Item) -> float:
    """Weight assisted items (hints, set-up or steps revealed before answering) below fluent ones."""
    if item.skipped or item.score <= 0:
        return 0.0
    if item.assisted:
        return min(float(item.score), 0.5)
    return float(item.score)


def _has_l4_challenge(unit_items: list[Item]) -> bool:
    """True when the unit has at least one correct L4+ item answered with no hints/assistance."""
    return any(
        isinstance(i.level, int)
        and i.level >= 4
        and not i.assisted
        and not i.skipped
        and _effective_mastery_score(i) >= 1.0
        for i in unit_items
    )


def evaluate_mastery(unit_items: list[Item], open_weak_spot: bool = False) -> tuple[int | None, dict[str, object]]:
    """Return (mastery, masteryCap) for one unit from its practice items (rules/01 §7 & §9)."""
    no_cap: dict[str, object] = {"capped": False, "reason": ""}
    recent = unit_items[-MASTERY_WINDOW:]
    if not recent:
        return None, no_cap
    pct = sum(_effective_mastery_score(i) for i in recent) / len(recent)
    if pct < 0.5:
        return 1, no_cap
    hard = [i for i in recent if isinstance(i.level, int) and i.level >= 3]
    hard_avg = (sum(_effective_mastery_score(i) for i in hard) / len(hard)) if hard else 0.0
    has_challenge = _has_l4_challenge(unit_items)
    if len(hard) >= 3 and hard_avg >= 0.7 and not open_weak_spot and has_challenge:
        return 3, no_cap
    if not has_challenge:
        return 2, {"capped": True, "reason": L4_CHALLENGE_CAP_REASON}
    if open_weak_spot:
        return 2, {"capped": True, "reason": OPEN_WEAK_SPOT_CAP_REASON}
    if len(hard) >= 3 and hard_avg < 0.7 and any(i.assisted and i.score > 0 for i in hard):
        unassisted_potential = sum(
            1.0 if (i.assisted and i.score > 0) else _effective_mastery_score(i) for i in hard
        ) / len(hard)
        if unassisted_potential >= 0.7:
            return 2, {"capped": True, "reason": ASSISTED_CAP_REASON}
    return 2, no_cap


def mastery_cap(unit_items: list[Item], open_weak_spot: bool = False) -> dict[str, object]:
    """Return `{capped: bool, reason: str}` explaining whether and why a unit's Mastery is capped at 2."""
    _, cap = evaluate_mastery(unit_items, open_weak_spot)
    return cap


def suggest_mastery(
    unit_items: list[Item],
    open_weak_spot: bool = False,
    *,
    return_cap: bool = False,
) -> int | None | tuple[int | None, dict[str, object]]:
    """Evidence-based Mastery (0-4) for one unit from its last items (rules/01 §7 & §9).

    1 under 50%; 3 when at least 3 recent L3+ items average >= 70%, no weak spot is open,
    and the unit has at least one correct L4+ item with no hint ("challenge"); otherwise 2.
    Assisted items (hints, set-up or steps revealed before answering) are weighted below fluent ones.
    Drills cannot show 4 (Feynman explanation, cross-subject synthesis), so the learner sets 4 by hand.
    """
    mastery, cap = evaluate_mastery(unit_items, open_weak_spot)
    if return_cap:
        return mastery, cap
    return mastery


def review_update(
    unit: str, current_mastery: int | None, attempt_date: str, data_root: str | None = None, progress_dir=None
) -> dict | None:
    """Mastery, Last Reviewed, Next Review and masteryCap for a unit page after practice, or None without evidence.
    A learner-set 4 is kept while the evidence still says 3 (drills cannot confirm or refute 4)."""
    items = [i for i in load_items(data_root, progress_dir) if unit in _item_units(i)]
    open_weak = any(s["open"] and unit in s["units"] for s in trap_status(items).values())
    mastery, cap = evaluate_mastery(items, open_weak)
    if mastery is None:
        return None
    if current_mastery == 4 and mastery == 3:
        mastery = 4
        cap = {"capped": False, "reason": ""}
    nxt = date.fromisoformat(attempt_date[:10]) + timedelta(days=REVIEW_DAYS[mastery])
    return {
        "mastery": mastery,
        "lastReviewed": attempt_date[:10],
        "nextReview": nxt.isoformat(),
        "masteryCap": cap,
    }


def _load_titles() -> dict[str, str]:
    for path in ("id_map.json", os.path.join(find_repo_root(), "id_map.json")):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return {k: v.get("title", "") for k, v in json.load(f).items() if isinstance(v, dict)}
    return {}


_TRAP_PREFIX = re.compile(r"^(?:t\d+-)?(?:c\d+-)?(?:u\d+-)?")


def trap_name(trap_id: str) -> str:
    """Plain-language name from a MTH trap tag: `t02-c01-u01-i-squared-positive-one-trap` -> `I squared positive one`."""
    words = _TRAP_PREFIX.sub("", trap_id.lower())
    words = re.sub(r"-trap$", "", words).replace("-", " ").strip()
    return words[:1].upper() + words[1:] if words else trap_id


def _load_mth_trap_descriptions() -> dict[str, str]:
    """trapTag -> description from the MTH reasoning vaults."""
    cwd_vault = os.path.join("math_engine", "reasoning_vault")
    vault_dir = (
        cwd_vault if os.path.isdir(cwd_vault) else os.path.join(find_repo_root(), "math_engine", "reasoning_vault")
    )
    out: dict[str, str] = {}
    for vpath in sorted(glob.glob(os.path.join(vault_dir, "*.json"))):
        with open(vpath, encoding="utf-8") as f:
            for a in json.load(f).get("archetypes", []):
                for t in a.get("cognitiveTraps") or []:
                    if isinstance(t, dict) and t.get("trapTag") and t.get("description"):
                        out.setdefault(t["trapTag"], t["description"])
    return out


def _unit_matches_scope(unit: str, scope: str | None) -> bool:
    if not scope:
        return True
    return unit == scope or unit.startswith(scope + "-U")


def _build_unit_reports(
    scope: str | None = None,
    data_root: str = "drills/data",
    progress_dir: str | None = None,
) -> list[dict]:
    items = load_items(data_root, progress_dir)
    if scope:
        items = [i for i in items if i.unit == scope or any(_unit_matches_scope(u, scope) for u in _item_units(i))]
    if not items:
        return []
    titles = _load_titles()
    traps = trap_status(items)
    _, _, _, check_sentences = _load_prg_vault_meta()
    trap_descriptions = _load_mth_trap_descriptions()
    reports: list[dict] = []
    if scope == BRIDGE_SCOPE:
        target_units = [BRIDGE_SCOPE] if any(i.unit == BRIDGE_SCOPE for i in items) else []
    else:
        target_units = sorted({u for i in items for u in _item_units(i) if _unit_matches_scope(u, scope)})
    for unit in target_units:
        its = [i for i in items if (i.unit == BRIDGE_SCOPE if unit == BRIDGE_SCOPE else unit in _item_units(i))]
        open_traps = sorted(
            (t for t, s in traps.items() if s["open"] and (unit == BRIDGE_SCOPE or unit in s["units"])),
            key=lambda t: traps[t]["last"],
            reverse=True,
        )
        closed_traps = [t for t, s in traps.items() if not s["open"] and (unit == BRIDGE_SCOPE or unit in s["units"])]
        subject = "PRG" if unit.startswith("PRG-") or any(i.subject == "PRG" for i in its) else "MTH"

        def _entry(trap_id: str) -> dict:
            s = traps[trap_id]
            row = {
                "id": trap_id,
                "matches": s["matches"],
                "drills": s["drills"],
                "last": s["last"],
                "subject": s["subject"],
            }
            if trap_id in check_sentences:
                row["detail"] = check_sentences[trap_id]
            elif s["subject"] == "MTH":
                row["name"] = trap_name(trap_id)
                if trap_id in trap_descriptions:
                    row["detail"] = trap_descriptions[trap_id]
            return row

        reports.append(
            {
                "unitCode": unit,
                "unitTitle": titles.get(unit, ""),
                "subject": subject,
                "itemCount": len(its),
                "drillCount": len({i.drill for i in its}),
                "open": [_entry(t) for t in open_traps],
                "closed": [_entry(t) for t in closed_traps],
                "levels": level_advice(its),
                "assistedCount": sum(i.assisted for i in its),
                "skipped": sorted({i.archetype or i.pid for i in its if i.skipped}),
                "masteryCap": mastery_cap(its, bool(open_traps)),
            }
        )
    return reports


def report_json(scope: str | None = None, data_root: str = "drills/data", progress_dir: str | None = None) -> dict:
    """Return structured weak-spots data for JSON consumers."""
    units = _build_unit_reports(scope, data_root, progress_dir)
    return {
        "scope": scope,
        "units": [{**u, "levels": {str(lv): a for lv, a in u["levels"].items()}} for u in units],
    }


def report(scope: str | None = None, data_root: str = "drills/data", progress_dir: str | None = None) -> str:
    units = _build_unit_reports(scope, data_root, progress_dir)
    if not units:
        return "No practice data yet" + (f" for {scope}" if scope else "") + ". Practise a drill in the Studio first."
    lines = []
    for u in units:
        unit = u["unitCode"]
        lines.append(f"{unit} · {u['unitTitle']}  ({u['itemCount']} items in {u['drillCount']} drills)")
        for s in u["open"]:
            label = f"{s['id']} ({s['detail']})" if "detail" in s else s["id"]
            lines.append(f"  WEAK     {label}: matched {s['matches']}x in {s['drills']} drill(s), last {s['last']}")
        for s in u["closed"]:
            label = f"{s['id']} ({s['detail']})" if "detail" in s else s["id"]
            if s.get("subject") == "PRG":
                lines.append(f"  closed   {label}: clean in the last {CLOSE_AFTER} problems that tested it")
            else:
                lines.append(f"  closed   {label}: clean in the last {CLOSE_AFTER} drills that tested it")
        adv = u["levels"]
        if adv:
            lines.append(
                "  levels   " + " · ".join(f"L{lv} {a['pct']}% ({a['n']}) {a['move']}" for lv, a in adv.items())
            )
        if u["assistedCount"]:
            lines.append(
                f"  assisted {u['assistedCount']} item(s) answered after opening the set-up box, solution steps, or a hint"
            )
        if u["skipped"]:
            lines.append(f"  skipped  {', '.join(u['skipped'])}")
        if u["open"]:
            lines.append(f"  NEXT     new drill for {unit} focused on {', '.join(s['id'] for s in u['open'][:2])}")
        lines.append("")
    return "\n".join(lines).rstrip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m scripts.weak_spots", description=__doc__.split("\n\n")[0])
    ap.add_argument("scope", nargs="?", help="unit or chapter code (default: all units with practice data)")
    ap.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR", "drills/data"))
    ap.add_argument("--progress-dir", default=None)
    ap.add_argument("--json", action="store_true", dest="as_json", help="output JSON instead of text report")
    args = ap.parse_args(argv)
    if args.as_json:
        print(json.dumps(report_json(args.scope, args.data_root, args.progress_dir), ensure_ascii=False))
    else:
        print(report(args.scope, args.data_root, args.progress_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
