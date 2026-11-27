# -*- coding: utf-8 -*-
"""Read-only post-drill diagnostic report and deterministic next-step recommendations.

Usage:
    python -m scripts.drill_review <DRILL_ID> [--json]

Joins one drill's content with local progress (`PROGRESS_DIR` / `LEARNINGOS_PILOT`),
the unit review schedule (`_review_schedule.json`), vault trap descriptions,
`scripts.weak_spots`, `scripts.vault_report`, and `math_engine.variant_bank`.
Never modifies progress or Notion and never exposes answers, steps, or prompts.
"""

from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any

from math_engine.bridge import BRIDGE_SCOPE, problem_unit_codes
from math_engine.variant_bank import bank_path, is_quarantined_variant
from progress_store import (
    compare_iso_timestamps,
    cycle_evidence,
    find_repo_root,
    has_practice,
    is_timestamp_in_cycle,
    mistake_tags_in_cycle,
    progress_root,
    score_problem,
    score_variant,
)
from scripts import vault_report, weak_spots

REVIEW_DUE_WITHIN_DAYS = 2
_UNIT_CODE_RE = re.compile(r"^([A-Z]+-T\d+-C\d+)-U(\d+)$")

_UNIT_PAGE_SECTIONS = {
    "concepts": "1. Core Concepts & Intuition",
    "formulas": "2. Key Formulas & Decision Rules",
    "trapContrast": "3. Worked Examples (L3 — Trap Contrast)",
    "practiceGuide": "4. Unit Practice Guide",
    "mistakeLog": "6. My Implementation & Mistake Log",
}


def _resolve_today(today: datetime.date | str | None) -> datetime.date:
    if isinstance(today, datetime.date):
        return today
    if isinstance(today, str) and today.strip():
        return datetime.date.fromisoformat(today.strip()[:10])
    return datetime.date.today()


def _in_cycle(ts: Any, cycle_started_at: str | None) -> bool:
    return is_timestamp_in_cycle(ts, cycle_started_at)


def _find_drill_doc(drill_id: str, data_root: str) -> dict[str, Any]:
    direct_matches = sorted(glob.glob(os.path.join(data_root, "*", f"{drill_id}.json")))
    for path in direct_matches:
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
            if isinstance(doc, dict) and doc.get("drillId") == drill_id:
                return doc
        except (OSError, ValueError):
            continue

    for path in sorted(glob.glob(os.path.join(data_root, "*", "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and doc.get("drillId") == drill_id:
            return doc

    raise FileNotFoundError(f"Drill '{drill_id}' not found under {data_root}")


def _load_json_dict(path: str) -> dict[str, Any] | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _load_id_map(repo_root: str) -> dict[str, Any]:
    return _load_json_dict(os.path.join(repo_root, "id_map.json")) or {}


def _load_mth_vault_metadata(vault_dir: str) -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, str]]:
    """Return (archetypes_by_key, trap_descriptions, trap_archetype_owner)."""
    archetypes: dict[str, dict[str, Any]] = {}
    trap_descriptions: dict[str, str] = {}
    trap_owners: dict[str, str] = {}
    if not os.path.isdir(vault_dir):
        return archetypes, trap_descriptions, trap_owners
    for path in sorted(glob.glob(os.path.join(vault_dir, "*.json"))):
        doc = _load_json_dict(path)
        if not doc:
            continue
        file_unit = doc.get("unitCode")
        for arch in doc.get("archetypes") or []:
            if not isinstance(arch, dict):
                continue
            key = arch.get("archetypeKey")
            if not isinstance(key, str) or not key:
                continue
            entry = dict(arch)
            if not entry.get("unitCode") and isinstance(file_unit, str):
                entry["unitCode"] = file_unit
            archetypes[key] = entry
            for trap in arch.get("cognitiveTraps") or []:
                if isinstance(trap, dict):
                    tag = trap.get("trapTag")
                    desc = trap.get("description")
                    if isinstance(tag, str) and tag:
                        trap_owners.setdefault(tag, key)
                        if isinstance(desc, str) and desc.strip():
                            trap_descriptions.setdefault(tag, desc.strip())
                elif isinstance(trap, str) and trap:
                    trap_owners.setdefault(trap, key)
    return archetypes, trap_descriptions, trap_owners


def _outcome_bucket(score: float | None, outcome: str) -> str:
    if score is None:
        return "not_tried"
    if score >= 1.0:
        return "clean"
    if score > 0.0:
        return "assisted_or_retry"
    if outcome == "skipped":
        return "skipped"
    return "wrong"


def _setup_revealed_in_cycle(state: dict[str, Any], cycle_atts: list[dict[str, Any]], eff_cycle: str | None) -> bool:
    rev_setup = bool(state.get("reviewSetupRevealedAt") and _in_cycle(state.get("reviewSetupRevealedAt"), eff_cycle))
    if eff_cycle:
        return rev_setup or any(bool(a.get("setupRevealed")) for a in cycle_atts)
    return (
        bool(state.get("setupRevealedBeforeAnswer"))
        or rev_setup
        or any(bool(a.get("setupRevealed")) for a in cycle_atts)
    )


def _format_trap_entry(tag: str, count: int, trap_descriptions: dict[str, str]) -> dict[str, Any]:
    desc = trap_descriptions.get(tag)
    return {
        "tag": tag,
        "count": count,
        "name": weak_spots.trap_name(tag),
        "description": desc if desc else weak_spots.trap_name(tag),
        "hasVaultDescription": bool(desc),
    }


def _summarize_similar_usage(state: dict[str, Any], eff_cycle: str | None) -> dict[str, Any]:
    slots = state.get("similarSlots")
    slots_allocated = len(slots) if isinstance(slots, list) else 0
    variants = state.get("variants")
    opened = 0
    attempted = 0
    clean = 0
    assisted = 0
    wrong = 0
    examples_viewed = 0
    matched_traps: Counter[str] = Counter()

    if isinstance(variants, dict):
        for rec in variants.values():
            if not isinstance(rec, dict):
                continue
            role = rec.get("role") or "try"
            served_at = rec.get("servedAt")
            atts = rec.get("attempts") if isinstance(rec.get("attempts"), list) else []
            if role == "example":
                if _in_cycle(served_at, eff_cycle):
                    examples_viewed += 1
                continue
            if served_at or atts:
                opened += 1
            scored_v = score_variant(rec, eff_cycle)
            sc = scored_v["score"]
            if sc is not None:
                attempted += 1
                if sc >= 1.0:
                    clean += 1
                elif sc > 0.0:
                    assisted += 1
                else:
                    wrong += 1
            for att in atts:
                if isinstance(att, dict) and att.get("matchedTrap") and _in_cycle(att.get("ts"), eff_cycle):
                    matched_traps[str(att["matchedTrap"])] += 1

    return {
        "slotsAllocated": slots_allocated,
        "opened": opened,
        "attempted": attempted,
        "clean": clean,
        "assisted": assisted,
        "wrong": wrong,
        "examplesViewed": examples_viewed,
        "matchedTraps": dict(sorted(matched_traps.items())),
    }


def _build_item_report(
    prob: dict[str, Any],
    state: dict[str, Any],
    *,
    is_prg: bool,
    drill_unit: str,
    archetypes: dict[str, dict[str, Any]],
    trap_descriptions: dict[str, str],
) -> dict[str, Any]:
    qid = str(prob.get("id") or "")
    arch_key = str(prob.get("archetypeKey") or prob.get("templateKey") or "")
    arch_meta = archetypes.get(arch_key, {})
    arch_units = tuple(arch_meta.get("unitCodes") or ())
    prob_units = problem_unit_codes(
        prob,
        fallback_unit=arch_meta.get("unitCode") or drill_unit,
        arch_units=arch_units,
    )
    primary_unit = prob_units[0] if prob_units else drill_unit

    scored = score_problem(state, is_prg=is_prg)
    ev = cycle_evidence(state)
    raw_cycle = state.get("cycleStartedAt")
    eff_cycle = raw_cycle.strip() if isinstance(raw_cycle, str) and raw_cycle.strip() else None
    raw_atts = state.get("attempts") if isinstance(state.get("attempts"), list) else []
    cycle_atts = [
        a for a in raw_atts if isinstance(a, dict) and a.get("kind") != "variant" and _in_cycle(a.get("ts"), eff_cycle)
    ]

    trap_counts: Counter[str] = Counter()
    for att in cycle_atts:
        mt = att.get("matchedTrap")
        if isinstance(mt, str) and mt.strip():
            trap_counts[mt.strip()] += 1
    if not cycle_atts and not eff_cycle:
        last_check = state.get("lastCheck")
        if isinstance(last_check, dict) and last_check.get("trapMatched") and prob.get("commonTrapTag"):
            trap_counts[str(prob["commonTrapTag"])] += 1

    matched_traps = [_format_trap_entry(tag, cnt, trap_descriptions) for tag, cnt in trap_counts.items()]

    setup_revealed = _setup_revealed_in_cycle(state, cycle_atts, eff_cycle)
    reveals = {
        "hints": int(ev["hintUses"]),
        "setup": setup_revealed,
        "steps": bool(ev["stepsRevealed"]),
        "solution": bool(ev["solutionRevealed"]),
    }

    raw_dur = state.get("durationMs")
    duration_ms = (
        int(raw_dur) if isinstance(raw_dur, (int, float)) and not isinstance(raw_dur, bool) and raw_dur >= 0 else None
    )

    mistakes = [tag.strip() for tag in mistake_tags_in_cycle(state) if tag.strip()]
    mistake_note = state.get("mistakeNote").strip() if isinstance(state.get("mistakeNote"), str) else ""
    revisit_note = state.get("revisitNote").strip() if isinstance(state.get("revisitNote"), str) else ""

    return {
        "qid": qid,
        "archetypeKey": arch_key,
        "archetypeName": arch_meta.get("name"),
        "coreConcept": arch_meta.get("coreConcept"),
        "level": prob.get("level"),
        "form": prob.get("form") or "direct",
        "unitCode": primary_unit,
        "outcome": scored["outcome"],
        "outcomeBucket": _outcome_bucket(scored["score"], scored["outcome"]),
        "score": scored["score"],
        "firstTry": bool(scored["firstTry"]),
        "usedHelp": bool(scored["usedHelp"]),
        "attempts": len(ev["substantiveAttempts"]),
        "reveals": reveals,
        "matchedTraps": matched_traps,
        "durationMs": duration_ms,
        "mistakes": mistakes,
        "mistakeNote": mistake_note or None,
        "revisitNote": revisit_note or None,
        "similarUsage": _summarize_similar_usage(state, eff_cycle),
    }


def _find_untouched_drills(
    unit_code: str,
    current_drill_id: str,
    data_root: str,
    progress_dir: str,
) -> list[dict[str, Any]]:
    untouched: list[dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(data_root, "*", "*.json"))):
        doc = _load_json_dict(path)
        if not doc:
            continue
        did = doc.get("drillId")
        if not isinstance(did, str) or not did or did == current_drill_id:
            continue
        if doc.get("unitCode") != unit_code:
            continue
        prog = _load_json_dict(os.path.join(progress_dir, f"{did}.json"))
        if prog and has_practice(prog):
            continue
        probs = [p for p in (doc.get("problems") or []) if isinstance(p, dict)]
        level_mix = Counter(p.get("level") for p in probs if isinstance(p.get("level"), int))
        archetypes = sorted({str(p.get("archetypeKey")) for p in probs if p.get("archetypeKey")})
        untouched.append(
            {
                "drillId": did,
                "title": doc.get("title") or "",
                "problemCount": len(probs),
                "levelMix": {str(lv): cnt for lv, cnt in sorted(level_mix.items())},
                "archetypes": archetypes,
            }
        )
    return untouched


def _similar_variants_for_missed(
    items: list[dict[str, Any]],
    drill_states: dict[str, Any],
    unit_code: str,
    variants_dir: str,
) -> list[dict[str, Any]]:
    bank = _load_json_dict(bank_path(unit_code, variants_dir=variants_dir))
    variants = bank.get("variants") if isinstance(bank, dict) and isinstance(bank.get("variants"), list) else []
    by_pair: dict[tuple[str, int], list[str]] = defaultdict(list)
    by_arch: Counter[str] = Counter()
    for var in variants:
        if not isinstance(var, dict) or is_quarantined_variant(var, bank):
            continue
        arch = var.get("sourceArchetype") or var.get("archetypeKey")
        lvl = var.get("level")
        vid = var.get("variantId")
        if isinstance(arch, str) and arch:
            by_arch[arch] += 1
            if isinstance(lvl, int) and isinstance(vid, str) and vid:
                by_pair[(arch, lvl)].append(vid)

    missed_rows: list[dict[str, Any]] = []
    for item in items:
        if item["outcome"] not in ("wrong", "assisted", "skipped"):
            continue
        qid = item["qid"]
        arch = item["archetypeKey"]
        lvl = item["level"]
        pair_vids = by_pair.get((arch, lvl), []) if isinstance(lvl, int) else []

        st = drill_states.get(qid) if isinstance(drill_states.get(qid), dict) else {}
        attempted_vids = set(st.get("variantsAttempted") or [])
        raw_vars = st.get("variants")
        if isinstance(raw_vars, dict):
            for rec in raw_vars.values():
                if not isinstance(rec, dict):
                    continue
                vid = rec.get("variantId")
                if isinstance(vid, str) and vid and score_variant(rec, st.get("cycleStartedAt"))["score"] is not None:
                    attempted_vids.add(vid)

        unattempted = [vid for vid in pair_vids if vid not in attempted_vids]
        missed_rows.append(
            {
                "qid": qid,
                "archetypeKey": arch,
                "level": lvl,
                "outcome": item["outcome"],
                "availableAtLevel": len(pair_vids),
                "unattemptedAtLevel": len(unattempted),
                "totalForArchetype": int(by_arch.get(arch, 0)),
            }
        )
    return missed_rows


def _next_unit_info(
    unit_code: str,
    id_map: dict[str, Any],
    data_root: str,
    progress_dir: str,
    vault_dir: str,
) -> dict[str, Any] | None:
    m = _UNIT_CODE_RE.match(unit_code)
    if not m:
        return None
    chapter_prefix, cur_num = m.group(1), int(m.group(2))
    candidates: list[tuple[int, str, str]] = []
    for code, meta in id_map.items():
        if not isinstance(code, str) or not isinstance(meta, dict):
            continue
        cm = _UNIT_CODE_RE.match(code)
        if cm and cm.group(1) == chapter_prefix:
            num = int(cm.group(2))
            if num > cur_num:
                candidates.append((num, code, str(meta.get("title") or "")))
    if not candidates:
        return None
    candidates.sort()
    _, next_code, next_title = candidates[0]
    next_untouched = _find_untouched_drills(next_code, "", data_root, progress_dir)
    next_vault = _load_json_dict(os.path.join(vault_dir, f"{next_code}.json")) or {}
    next_archetypes = [
        a.get("archetypeKey")
        for a in (next_vault.get("archetypes") or [])
        if isinstance(a, dict) and a.get("archetypeKey")
    ]
    return {
        "unitCode": next_code,
        "title": next_title,
        "untouchedDrills": next_untouched,
        "archetypes": next_archetypes[:4],
    }


def _build_totals(
    drill_doc: dict[str, Any], items: list[dict[str, Any]], progress: dict[str, Any] | None
) -> dict[str, Any]:
    summary = (progress or {}).get("sessionSummary") or {}
    attempted = [it for it in items if it["score"] is not None]
    clean = [it for it in items if it["outcomeBucket"] == "clean"]
    assisted = [it for it in items if it["outcomeBucket"] == "assisted_or_retry"]
    wrong = [it for it in items if it["outcomeBucket"] == "wrong"]
    skipped = [it for it in items if it["outcomeBucket"] == "skipped"]
    not_tried = [it for it in items if it["outcomeBucket"] == "not_tried"]

    total_score = round(sum(float(it["score"] or 0.0) for it in items), 2)
    max_score = float(len(items))
    accuracy_pct = round((total_score / max_score) * 100.0, 1) if max_score > 0 else 0.0
    durations = [it["durationMs"] for it in items if isinstance(it["durationMs"], int)]

    by_level: dict[str, dict[str, int]] = {}
    for it in items:
        lv = it["level"]
        if not isinstance(lv, int):
            continue
        key = str(lv)
        bucket = by_level.setdefault(
            key,
            {"total": 0, "clean": 0, "assistedOrRetry": 0, "wrong": 0, "skipped": 0, "notTried": 0},
        )
        bucket["total"] += 1
        if it["outcomeBucket"] == "clean":
            bucket["clean"] += 1
        elif it["outcomeBucket"] == "assisted_or_retry":
            bucket["assistedOrRetry"] += 1
        elif it["outcomeBucket"] == "wrong":
            bucket["wrong"] += 1
        elif it["outcomeBucket"] == "skipped":
            bucket["skipped"] += 1
        else:
            bucket["notTried"] += 1

    trap_agg: dict[str, dict[str, Any]] = {}
    mistakes_counter: Counter[str] = Counter()
    notes_items: list[dict[str, Any]] = []
    for it in items:
        for m in it["mistakes"]:
            mistakes_counter[m] += 1
        for tr in it["matchedTraps"]:
            tag = tr["tag"]
            entry = trap_agg.setdefault(
                tag,
                {
                    "tag": tag,
                    "name": tr["name"],
                    "description": tr["description"],
                    "hasVaultDescription": tr["hasVaultDescription"],
                    "count": 0,
                    "qids": [],
                },
            )
            entry["count"] += tr["count"]
            if it["qid"] not in entry["qids"]:
                entry["qids"].append(it["qid"])
        if it["mistakeNote"] or it["revisitNote"]:
            notes_items.append(
                {
                    "qid": it["qid"],
                    "archetypeKey": it["archetypeKey"],
                    "level": it["level"],
                    "outcome": it["outcome"],
                    "mistakeNote": it["mistakeNote"],
                    "revisitNote": it["revisitNote"],
                }
            )

    if not attempted:
        status = "Not started"
    elif not_tried:
        status = "In progress"
    elif isinstance(summary.get("practiceStatus"), str) and summary["practiceStatus"].strip():
        status = summary["practiceStatus"].strip()
    elif max_score > 0 and total_score / max_score >= 0.8:
        status = "Graded"
    else:
        status = "Needs Retry"

    return {
        "drillId": drill_doc.get("drillId"),
        "title": drill_doc.get("title") or "",
        "unitCode": drill_doc.get("unitCode") or "",
        "unitTitle": drill_doc.get("unitTitle") or "",
        "chapterCode": drill_doc.get("chapterCode") or "",
        "topicCode": drill_doc.get("topicCode") or "",
        "subject": drill_doc.get("subject") or "MATH",
        "attemptDate": summary.get("attemptDate"),
        "practiceStatus": status,
        "problemCount": len(items),
        "attemptedCount": len(attempted),
        "notTriedCount": len(not_tried),
        "cleanCount": len(clean),
        "assistedOrRetryCount": len(assisted),
        "wrongCount": len(wrong),
        "skippedCount": len(skipped),
        "totalScore": total_score,
        "maxScore": max_score,
        "accuracyPct": accuracy_pct,
        "totalDurationMs": sum(durations) if durations else None,
        "byLevel": dict(sorted(by_level.items(), key=lambda kv: int(kv[0]))),
        "trapsMatched": sorted(trap_agg.values(), key=lambda e: (-e["count"], e["tag"])),
        "mistakesCategories": dict(sorted(mistakes_counter.items())),
        "notesCount": len(notes_items),
        "notes": notes_items,
    }


def _build_unit_context(
    drill_doc: dict[str, Any],
    items: list[dict[str, Any]],
    drill_states: dict[str, Any],
    *,
    repo_root: str,
    data_root: str,
    progress_dir: str,
    variants_dir: str,
    vault_dir: str,
    issue_log: str | None,
    today: datetime.date,
    id_map: dict[str, Any],
    archetypes: dict[str, dict[str, Any]],
    trap_descriptions: dict[str, str],
) -> dict[str, Any]:
    unit_code = str(drill_doc.get("unitCode") or "")
    drill_id = str(drill_doc.get("drillId") or "")
    unit_title = str(drill_doc.get("unitTitle") or (id_map.get(unit_code) or {}).get("title") or "")

    schedule_all = _load_json_dict(os.path.join(progress_dir, "_review_schedule.json")) or {}
    sched_entry = schedule_all.get(unit_code) if isinstance(schedule_all.get(unit_code), dict) else None
    next_review = sched_entry.get("nextReview") if isinstance(sched_entry, dict) else None
    last_reviewed = sched_entry.get("lastReviewed") if isinstance(sched_entry, dict) else None
    days_until: int | None = None
    if isinstance(next_review, str) and len(next_review) >= 10:
        try:
            days_until = (datetime.date.fromisoformat(next_review[:10]) - today).days
        except ValueError:
            days_until = None

    all_items = weak_spots.load_items(data_root=data_root, progress_dir=progress_dir)
    unit_items = [it for it in all_items if unit_code in weak_spots._item_units(it)]
    traps = weak_spots.trap_status(unit_items)

    trap_drills_all: dict[str, list[str]] = defaultdict(list)
    trap_matches_all: Counter[str] = Counter()
    trap_last_all: dict[str, str] = {}
    for it in unit_items:
        for tag in it.matched:
            trap_matches_all[tag] += 1
            if it.drill not in trap_drills_all[tag]:
                trap_drills_all[tag].append(it.drill)
            if it.ts:
                prev_last = trap_last_all.get(tag)
                cmp_ts = compare_iso_timestamps(it.ts, prev_last) if prev_last else None
                if prev_last is None or (cmp_ts > 0 if cmp_ts is not None else it.ts > prev_last):
                    trap_last_all[tag] = it.ts

    open_weak_spots: list[dict[str, Any]] = []
    closed_weak_spots: list[dict[str, Any]] = []
    for tag, st in traps.items():
        if unit_code != BRIDGE_SCOPE and unit_code not in st["units"]:
            continue
        row = {
            **_format_trap_entry(tag, st["matches"], trap_descriptions),
            "matches": st["matches"],
            "drillsCount": st["drills"],
            "drills": trap_drills_all.get(tag, []),
            "last": st["last"],
            "open": bool(st["open"]),
        }
        if st["open"]:
            open_weak_spots.append(row)
        else:
            closed_weak_spots.append(row)
    open_weak_spots.sort(key=lambda r: (-r["matches"], r["tag"]))
    closed_weak_spots.sort(key=lambda r: r["tag"])

    drill_matched_tags = {tr["tag"] for it in items for tr in it["matchedTraps"]}
    repeated_traps: list[dict[str, Any]] = []
    for tag, drill_list in sorted(trap_drills_all.items()):
        if len(drill_list) >= 2 and (tag in drill_matched_tags or any(w["tag"] == tag for w in open_weak_spots)):
            is_open = traps[tag]["open"] if tag in traps else True
            repeated_traps.append(
                {
                    **_format_trap_entry(tag, trap_matches_all[tag], trap_descriptions),
                    "matches": trap_matches_all[tag],
                    "drills": drill_list,
                    "drillsCount": len(drill_list),
                    "open": bool(is_open),
                    "inCurrentDrill": tag in drill_matched_tags,
                    "last": trap_last_all.get(tag, "")[:10],
                }
            )

    ev_mastery, ev_cap = weak_spots.evaluate_mastery(unit_items, bool(open_weak_spots))

    sched_mastery = sched_entry.get("mastery") if isinstance(sched_entry, dict) else None
    sched_cap = (
        sched_entry.get("masteryCap")
        if isinstance(sched_entry, dict) and isinstance(sched_entry.get("masteryCap"), dict)
        else None
    )

    if unit_items and ev_mastery is not None:
        if sched_mastery == 4 and ev_mastery == 3:
            effective_mastery = 4
            effective_cap = {"capped": False, "reason": ""}
        else:
            effective_mastery = ev_mastery
            sched_reason = (
                str(sched_cap.get("reason") or "") if isinstance(sched_cap, dict) and sched_cap.get("capped") else ""
            )
            if sched_reason == weak_spots.OPEN_WEAK_SPOT_CAP_REASON and open_weak_spots:
                effective_cap = sched_cap
            elif sched_reason == weak_spots.ASSISTED_CAP_REASON and any(
                isinstance(it.get("level"), int) and it["level"] >= 3 and it.get("usedHelp") for it in items
            ):
                effective_cap = sched_cap
            else:
                effective_cap = ev_cap
    else:
        effective_mastery = sched_mastery if isinstance(sched_mastery, int) else ev_mastery
        effective_cap = sched_cap if sched_cap is not None else ev_cap

    earned_all = vault_report._evidence(data_root)
    v_rep = vault_report.unit_report(
        unit_code,
        vault_dir=vault_dir,
        data_root=data_root,
        log=issue_log,
        earned=earned_all,
    )

    practised_by_arch: dict[str, list[weak_spots.Item]] = defaultdict(list)
    for it in unit_items:
        if it.archetype:
            practised_by_arch[it.archetype].append(it)

    levels_per_archetype: list[dict[str, Any]] = []
    unpractised_archetypes: list[dict[str, Any]] = []
    seen_arch_keys: set[str] = set()
    for row in v_rep.get("rows", []):
        key = row["key"]
        seen_arch_keys.add(key)
        p_items = practised_by_arch.get(key, [])
        clean_levels = sorted({it.level for it in p_items if isinstance(it.level, int) and it.score >= 1.0})
        attempted_levels = sorted({it.level for it in p_items if isinstance(it.level, int)})
        arch_info = {
            "archetypeKey": key,
            "name": archetypes.get(key, {}).get("name") or key,
            "baseLevel": row.get("level"),
            "vaultEarnedLevels": {str(lv): cnt for lv, cnt in (row.get("earned") or {}).items()},
            "vaultFlags": row.get("flags") or [],
            "practisedItems": len(p_items),
            "practisedLevels": attempted_levels,
            "practisedCleanLevels": clean_levels,
        }
        levels_per_archetype.append(arch_info)
        if not p_items:
            unpractised_archetypes.append(
                {
                    "archetypeKey": key,
                    "name": arch_info["name"],
                    "baseLevel": row.get("level"),
                    "vaultEarnedLevels": arch_info["vaultEarnedLevels"],
                    "vaultFlags": arch_info["vaultFlags"],
                    "coreConcept": archetypes.get(key, {}).get("coreConcept"),
                }
            )

    untouched_drills = _find_untouched_drills(unit_code, drill_id, data_root, progress_dir)
    similar_missed = _similar_variants_for_missed(items, drill_states, unit_code, variants_dir)
    lvl_advice = {str(lv): adv for lv, adv in weak_spots.level_advice(unit_items).items()}

    unit_entry = id_map.get(unit_code) if isinstance(id_map.get(unit_code), dict) else None
    next_unit = _next_unit_info(unit_code, id_map, data_root, progress_dir, vault_dir)

    return {
        "unitCode": unit_code,
        "unitTitle": unit_title,
        "mastery": effective_mastery,
        "masteryCap": effective_cap,
        "reviewSchedule": {
            "mastery": sched_mastery,
            "masteryCap": sched_cap,
            "lastReviewed": last_reviewed,
            "nextReview": next_review,
            "daysUntilReview": days_until,
        },
        "evidenceMastery": {
            "mastery": ev_mastery,
            "masteryCap": ev_cap,
            "recentItems": min(len(unit_items), weak_spots.MASTERY_WINDOW),
            "hasL4Challenge": bool(weak_spots._has_l4_challenge(unit_items)),
        },
        "levelsEarnedPerArchetype": levels_per_archetype,
        "unpractisedArchetypes": unpractised_archetypes,
        "availableUntouchedDrills": untouched_drills,
        "similarVariantsForMissed": similar_missed,
        "weakSpots": {
            "open": open_weak_spots,
            "closed": closed_weak_spots,
            "repeatedAcrossDrills": repeated_traps,
            "levelAdvice": lvl_advice,
        },
        "nextUnit": next_unit,
        "unitPage": {
            "code": unit_code,
            "title": unit_title,
            "inIdMap": bool(unit_entry),
            "sections": _UNIT_PAGE_SECTIONS,
        },
    }


def _dedup_preserve(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _make_rec(
    *,
    rule_id: str,
    kind: str,
    action: str,
    why: str,
    unit: str,
    archetypes: list[str],
    levels: list[int],
    count: int,
    focus_tags: list[str] | None = None,
    qids: list[str] | None = None,
    drill_id: str | None = None,
    unit_page_section: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "unit": unit,
        "archetypes": _dedup_preserve(archetypes),
        "levels": sorted({lv for lv in levels if isinstance(lv, int)}),
        "count": max(1, int(count)),
    }
    if focus_tags:
        params["focusTags"] = _dedup_preserve(focus_tags)[:2]
    if qids:
        params["qids"] = _dedup_preserve(qids)
    if drill_id:
        params["drillId"] = drill_id
    if unit_page_section:
        params["unitPageSection"] = unit_page_section
    if extra:
        params.update(extra)
    return {
        "ruleId": rule_id,
        "kind": kind,
        "action": action,
        "why": why,
        "params": params,
    }


def _compute_recommendations(
    drill_doc: dict[str, Any],
    items: list[dict[str, Any]],
    totals: dict[str, Any],
    unit_ctx: dict[str, Any],
    archetypes_meta: dict[str, dict[str, Any]],
    trap_owners: dict[str, str],
) -> dict[str, Any]:
    unit_code = str(totals["unitCode"])
    drill_id = str(totals["drillId"])
    candidates: list[dict[str, Any]] = []

    sched = unit_ctx["reviewSchedule"]
    days_until = sched.get("daysUntilReview")
    next_review = sched.get("nextReview")
    mastery = unit_ctx.get("mastery")
    cap = unit_ctx.get("masteryCap") or {}
    cap_reason = str(cap.get("reason") or "") if cap.get("capped") else ""

    not_tried_items = [it for it in items if it["outcomeBucket"] == "not_tried"]
    skipped_items = [it for it in items if it["outcomeBucket"] == "skipped"]
    wrong_items = [it for it in items if it["outcomeBucket"] == "wrong"]
    assisted_items = [it for it in items if it["outcomeBucket"] == "assisted_or_retry"]
    attempted_items = [it for it in items if it["score"] is not None]

    repeated_traps = unit_ctx["weakSpots"]["repeatedAcrossDrills"]
    open_weak = unit_ctx["weakSpots"]["open"]
    unpractised = unit_ctx["unpractisedArchetypes"]
    untouched_drills = unit_ctx["availableUntouchedDrills"]
    similar_missed = unit_ctx["similarVariantsForMissed"]

    note_qids = [n["qid"] for n in totals["notes"]]

    # 1. Review due within N days -> prioritise completing due review before starting new work
    if isinstance(days_until, int) and days_until <= REVIEW_DUE_WITHIN_DAYS and attempted_items:
        rem_archs = [it["archetypeKey"] for it in not_tried_items] or [it["archetypeKey"] for it in items]
        rem_levels = [it["level"] for it in not_tried_items if isinstance(it["level"], int)] or [
            it["level"] for it in items if isinstance(it["level"], int)
        ]
        due_phrase = (
            "overdue" if days_until < 0 else ("due today" if days_until == 0 else f"due in {days_until} day(s)")
        )
        if not_tried_items:
            action = (
                f"Finish the remaining {len(not_tried_items)} item(s) in {drill_id} and complete the {unit_code} "
                f"spaced review before {next_review}."
            )
            why = (
                f"Unit review is {due_phrase} ({next_review}), and {drill_id} is half done "
                f"({totals['attemptedCount']}/{totals['problemCount']} attempted)."
            )
            count = len(not_tried_items)
        else:
            action = f"Complete the {unit_code} spaced review (Daily Review) before {next_review} prior to starting a new drill."
            why = f"Unit review is {due_phrase} ({next_review}; current mastery {mastery})."
            count = max(4, len(rem_archs))
        candidates.append(
            _make_rec(
                rule_id="review_due_soon",
                kind="daily_review",
                action=action,
                why=why,
                unit=unit_code,
                archetypes=rem_archs,
                levels=rem_levels,
                count=count,
                qids=[it["qid"] for it in not_tried_items] or None,
                drill_id=drill_id if not_tried_items else None,
                extra={"dueDate": next_review, "daysUntilReview": days_until},
            )
        )

    # 2. Skipped items -> concept explanation pointer + stepped-down foundation drill
    if skipped_items:
        sk_archs = _dedup_preserve([it["archetypeKey"] for it in skipped_items if it.get("archetypeKey")])
        lowest_levels: list[int] = []
        foundation_archs: list[str] = []
        for ak in sk_archs:
            base_lv = archetypes_meta.get(ak, {}).get("baseLevel") or archetypes_meta.get(ak, {}).get("level")
            skipped_lv = min(
                (it["level"] for it in skipped_items if it["archetypeKey"] == ak and isinstance(it["level"], int)),
                default=2,
            )
            step_down_lv = max(1, skipped_lv - 1)
            if isinstance(base_lv, int) and base_lv <= step_down_lv:
                lowest_levels.append(base_lv)
                foundation_archs.append(ak)
            else:
                lowest_levels.append(step_down_lv)
                prereq_archs = [
                    r["archetypeKey"]
                    for r in unit_ctx["levelsEarnedPerArchetype"]
                    if isinstance(r.get("baseLevel"), int) and r["baseLevel"] <= step_down_lv
                ]
                foundation_archs.extend(prereq_archs[-2:] or [ak])
        foundation_archs = _dedup_preserve(foundation_archs or sk_archs)
        target_lvs = sorted(set(lowest_levels)) or [1]
        lv_label = ", ".join(f"L{lv}" for lv in target_lvs)
        sk_qids = [it["qid"] for it in skipped_items]
        sk_levels = sorted({it["level"] for it in skipped_items if isinstance(it["level"], int)})
        candidates.append(
            _make_rec(
                rule_id="skipped_items",
                kind="new_math_drill",
                action=(
                    f"Review '{_UNIT_PAGE_SECTIONS['concepts']}' and '{_UNIT_PAGE_SECTIONS['trapContrast']}' on the {unit_code} "
                    f"unit page for the skipped concept(s), then generate a foundation drill at {lv_label} "
                    f"on {', '.join(foundation_archs)}."
                ),
                why=(
                    f"Skipped {len(skipped_items)} item(s) ({', '.join(sk_qids)} at L{', L'.join(str(x) for x in sk_levels)}) "
                    f"with concept-gap; stepping down to {lv_label} rebuilds the missing prerequisite before retrying L{max(sk_levels, default=3)}."
                ),
                unit=unit_code,
                archetypes=foundation_archs,
                levels=target_lvs,
                count=max(4, min(6, len(foundation_archs) * 2)),
                qids=sk_qids,
                unit_page_section=_UNIT_PAGE_SECTIONS["concepts"],
            )
        )
        sim_sk = [s for s in similar_missed if s["outcome"] == "skipped" and s["unattemptedAtLevel"] > 0]
        if sim_sk:
            sim_sk_qids = [s["qid"] for s in sim_sk]
            candidates.append(
                _make_rec(
                    rule_id="retry_similar_for_skipped",
                    kind="practice_similar",
                    action=(
                        f"After reviewing the {unit_code} unit page, practice Similar variants on "
                        f"{', '.join(sim_sk_qids)} in Studio."
                    ),
                    why=(
                        f"{sum(s['unattemptedAtLevel'] for s in sim_sk)} unattempted Similar variant(s) are ready "
                        f"for skipped item(s) ({', '.join(sim_sk_qids)})."
                    ),
                    unit=unit_code,
                    archetypes=sk_archs,
                    levels=sk_levels or target_lvs,
                    count=len(sim_sk_qids),
                    qids=sim_sk_qids,
                )
            )

    # 3. Repeated trap across drills -> concept recap pointer + trap-focused drill
    if repeated_traps:
        top_traps = repeated_traps[:2]
        rep_tags = [t["tag"] for t in top_traps]
        rep_archs = _dedup_preserve(
            [it["archetypeKey"] for it in items if any(tr["tag"] in rep_tags for tr in it["matchedTraps"])]
            + [trap_owners[tag] for tag in rep_tags if tag in trap_owners]
        )
        rep_levels = [
            it["level"]
            for it in items
            if isinstance(it["level"], int) and any(tr["tag"] in rep_tags for tr in it["matchedTraps"])
        ]
        if not rep_levels:
            rep_levels = [
                int(archetypes_meta[ak]["level"])
                for ak in rep_archs
                if ak in archetypes_meta and isinstance(archetypes_meta[ak].get("level"), int)
            ] or [2]
        evidence_bits = [
            f"{t['name']} ({t['tag']}: {t['matches']}x across {', '.join(t['drills'])})" for t in top_traps
        ]
        candidates.append(
            _make_rec(
                rule_id="repeated_trap_across_drills",
                kind="review_drill",
                action=(
                    f"Read '{_UNIT_PAGE_SECTIONS['trapContrast']}' and '{_UNIT_PAGE_SECTIONS['formulas']}' on the {unit_code} "
                    f"unit page, then run a trap-focused drill targeting {', '.join(t['name'] for t in top_traps)}."
                ),
                why="Repeated trap across drills: " + "; ".join(evidence_bits) + ".",
                unit=unit_code,
                archetypes=rep_archs,
                levels=rep_levels,
                count=max(4, min(6, len(rep_archs) * 2)),
                focus_tags=rep_tags,
                unit_page_section=_UNIT_PAGE_SECTIONS["trapContrast"],
            )
        )

    # 4. Any wrong or assisted item -> retry Similar first, then targeted review drill (or unassisted fluency)
    if wrong_items:
        target_items = wrong_items + assisted_items
        w_qids = [it["qid"] for it in target_items]
        w_archs = _dedup_preserve([it["archetypeKey"] for it in target_items])
        w_levels = [it["level"] for it in target_items if isinstance(it["level"], int)]
        w_traps = _dedup_preserve([tr["tag"] for it in target_items for tr in it["matchedTraps"]])
        sim_avail = [s for s in similar_missed if s["unattemptedAtLevel"] > 0]
        note_clause = (
            f" Learner notes recorded on {', '.join(note_qids)} highlight specific confusion points."
            if note_qids
            else ""
        )
        if sim_avail:
            sim_qids = [s["qid"] for s in sim_avail]
            candidates.append(
                _make_rec(
                    rule_id="retry_similar_then_targeted",
                    kind="practice_similar",
                    action=(
                        f"Retry Similar variants on {', '.join(sim_qids)} unassisted first, then generate a targeted "
                        f"review drill on {', '.join(w_archs)} at L{', L'.join(str(x) for x in sorted(set(w_levels)))}."
                    ),
                    why=(
                        f"{len(wrong_items)} wrong and {len(assisted_items)} assisted item(s) in {drill_id}; "
                        f"{sum(s['unattemptedAtLevel'] for s in sim_avail)} unattempted Similar variant(s) are ready.{note_clause}"
                    ),
                    unit=unit_code,
                    archetypes=w_archs,
                    levels=w_levels,
                    count=max(4, min(6, len(w_archs) * 2)),
                    focus_tags=w_traps[:2] or None,
                    qids=sim_qids,
                )
            )
        candidates.append(
            _make_rec(
                rule_id="targeted_review_drill",
                kind="review_drill",
                action=(
                    f"Generate a targeted review drill for {unit_code} on {', '.join(w_archs)} "
                    f"at L{', L'.join(str(x) for x in sorted(set(w_levels)))}"
                    + (f" focused on {', '.join(w_traps[:2])}" if w_traps else "")
                    + "."
                ),
                why=(
                    f"Direct targeted practice for {len(wrong_items)} wrong and {len(assisted_items)} assisted item(s) "
                    f"({', '.join(w_qids)}).{note_clause}"
                ),
                unit=unit_code,
                archetypes=w_archs,
                levels=w_levels,
                count=max(4, min(6, len(w_archs) * 2)),
                focus_tags=w_traps[:2] or None,
                qids=w_qids,
            )
        )
    elif assisted_items:
        a_qids = [it["qid"] for it in assisted_items]
        a_archs = _dedup_preserve([it["archetypeKey"] for it in assisted_items])
        a_levels = [it["level"] for it in assisted_items if isinstance(it["level"], int)]
        help_count = sum(1 for it in assisted_items if it["usedHelp"])
        sim_avail = [s for s in similar_missed if s["unattemptedAtLevel"] > 0]
        note_clause = f" Notes on {', '.join(note_qids)} also point to steps to reinforce." if note_qids else ""
        if sim_avail:
            action = (
                f"Redo Similar variants on {', '.join(s['qid'] for s in sim_avail)} without opening hints, set-up, steps, or solution, "
                f"then run an unassisted fluency drill on {', '.join(a_archs)} at L{', L'.join(str(x) for x in sorted(set(a_levels)))}."
            )
            kind = "practice_similar"
        else:
            action = (
                f"Generate an unassisted fluency drill on {', '.join(a_archs)} at "
                f"L{', L'.join(str(x) for x in sorted(set(a_levels)))} without hints, steps, or solution."
            )
            kind = "new_math_drill"
        cap_clause = f" Mastery is capped ({cap_reason})." if cap_reason else ""
        unattempted_archs = {it["archetypeKey"] for it in not_tried_items if it.get("archetypeKey")}
        fresh_a_archs = [ak for ak in a_archs if ak not in unattempted_archs]
        if sim_avail or fresh_a_archs:
            candidates.append(
                _make_rec(
                    rule_id="consolidate_unassisted_fluency",
                    kind=kind,
                    action=action,
                    why=(
                        f"{len(assisted_items)}/{totals['attemptedCount']} attempted item(s) scored 0.5 "
                        f"({help_count} used hints/set-up/steps/solution before answering).{cap_clause}{note_clause}"
                    ),
                    unit=unit_code,
                    archetypes=a_archs,
                    levels=a_levels,
                    count=max(4, min(6, len(a_archs) * 2)),
                    qids=a_qids,
                )
            )
        if fresh_a_archs:
            candidates.append(
                _make_rec(
                    rule_id="unassisted_new_drill",
                    kind="new_math_drill",
                    action=(
                        f"Build a fresh {unit_code} drill on {', '.join(fresh_a_archs)} at "
                        f"L{', L'.join(str(x) for x in sorted(set(a_levels)))} and complete it without opening help."
                    ),
                    why=f"Fresh unassisted problems verify independent recall after heavy help on {', '.join(a_qids)}.",
                    unit=unit_code,
                    archetypes=fresh_a_archs,
                    levels=a_levels,
                    count=max(4, min(6, len(fresh_a_archs) * 2)),
                    qids=a_qids,
                )
            )

    # 5. All attempted items clean (no wrong/skipped/assisted)
    max_attempted_level = max((it["level"] for it in attempted_items if isinstance(it["level"], int)), default=0)
    all_done_clean = (
        totals["problemCount"] > 0 and totals["notTriedCount"] == 0 and totals["cleanCount"] == totals["problemCount"]
    )

    if all_done_clean and max_attempted_level <= 2:
        focus_archs = [
            a["archetypeKey"]
            for a in sorted(
                unpractised,
                key=lambda x: (
                    "UNPROVEN" in (x.get("vaultFlags") or []),
                    -(x.get("baseLevel") or 0),
                    x["archetypeKey"],
                ),
            )
        ]
        if not focus_archs:
            focus_archs = [
                r["archetypeKey"]
                for r in sorted(
                    unit_ctx["levelsEarnedPerArchetype"],
                    key=lambda x: (
                        "UNPROVEN" in (x.get("vaultFlags") or []),
                        -(x.get("baseLevel") or 0),
                        x["archetypeKey"],
                    ),
                )
            ]
        if not focus_archs:
            focus_archs = _dedup_preserve([it["archetypeKey"] for it in items if it.get("archetypeKey")])
        focus_archs = focus_archs[:4]
        cap_clause = f" ({cap_reason})" if cap_reason else ""
        candidates.append(
            _make_rec(
                rule_id="lift_mastery_cap_l3_l4",
                kind="new_math_drill",
                action=(
                    f"Generate an L3–L4 drill for {unit_code} focused on "
                    f"{'unpractised/higher-level ' if unpractised else ''}archetypes ({', '.join(focus_archs)}) "
                    f"to lift the Mastery cap{cap_clause}."
                ),
                why=(
                    f"All {totals['cleanCount']}/{totals['problemCount']} items in {drill_id} are clean, "
                    f"but max level reached is L{max_attempted_level} (Mastery {mastery}{cap_clause}); "
                    f"{len(unpractised)} vault archetype(s) remain unpractised."
                ),
                unit=unit_code,
                archetypes=focus_archs,
                levels=[3, 4],
                count=4,
            )
        )

    # 6. Cap reason present -> ensure an explicit action satisfies the cap reason
    if cap_reason:
        if (
            cap_reason == weak_spots.L4_CHALLENGE_CAP_REASON
            and totals["practiceStatus"] != "Needs Retry"
            and not wrong_items
            and not skipped_items
            and not not_tried_items
            and not unit_ctx["evidenceMastery"].get("hasL4Challenge")
        ):
            high_archs = [
                r["archetypeKey"]
                for r in sorted(
                    unit_ctx["levelsEarnedPerArchetype"],
                    key=lambda x: (
                        "UNPROVEN" in (x.get("vaultFlags") or []),
                        -(x.get("baseLevel") or 0),
                        x["practisedItems"],
                        x["archetypeKey"],
                    ),
                )
            ][:3]
            if high_archs:
                candidates.append(
                    _make_rec(
                        rule_id="mastery_cap_l4_challenge",
                        kind="new_math_drill",
                        action=(
                            f"Attempt an unassisted L4 challenge drill in {unit_code} on {', '.join(high_archs)} "
                            f"without hints, set-up, or steps."
                        ),
                        why=f"Mastery is capped at {mastery}: {cap_reason}.",
                        unit=unit_code,
                        archetypes=high_archs,
                        levels=[4],
                        count=4,
                    )
                )
        elif cap_reason == weak_spots.OPEN_WEAK_SPOT_CAP_REASON and open_weak:
            ow_tags = [w["tag"] for w in open_weak[:2]]
            ow_archs = _dedup_preserve(
                [it["archetypeKey"] for it in items if any(tr["tag"] in ow_tags for tr in it["matchedTraps"])]
                + [trap_owners[t] for t in ow_tags if t in trap_owners]
            ) or [it["archetypeKey"] for it in items[:2]]
            candidates.append(
                _make_rec(
                    rule_id="mastery_cap_close_weak_spot",
                    kind="review_drill",
                    action=(
                        f"Complete 2 consecutive clean weak-spot drills in {unit_code} targeting {', '.join(ow_tags)} "
                        f"to close the open weak spot and lift the Mastery cap."
                    ),
                    why=f"Mastery is capped at {mastery}: {cap_reason} ({', '.join(ow_tags)}).",
                    unit=unit_code,
                    archetypes=ow_archs,
                    levels=[2, 3],
                    count=4,
                    focus_tags=ow_tags,
                )
            )
        elif cap_reason == weak_spots.ASSISTED_CAP_REASON:
            l3_archs = _dedup_preserve(
                [it["archetypeKey"] for it in items if isinstance(it["level"], int) and it["level"] >= 3]
            ) or _dedup_preserve([it["archetypeKey"] for it in items])
            candidates.append(
                _make_rec(
                    rule_id="mastery_cap_unassisted_l3",
                    kind="new_math_drill",
                    action=f"Solve L3–L4 problems in {unit_code} on {', '.join(l3_archs)} without hints, steps, or solution.",
                    why=f"Mastery is capped at {mastery}: {cap_reason}.",
                    unit=unit_code,
                    archetypes=l3_archs,
                    levels=[3, 4],
                    count=4,
                )
            )

    # 7. Incomplete drill (when review is not already due soon)
    if not_tried_items and not any(c["ruleId"] == "review_due_soon" for c in candidates):
        rem_archs = [it["archetypeKey"] for it in not_tried_items]
        rem_levels = [it["level"] for it in not_tried_items if isinstance(it["level"], int)]
        due_note = ""
        if not attempted_items and isinstance(days_until, int) and days_until <= REVIEW_DUE_WITHIN_DAYS:
            due_phrase = (
                "overdue" if days_until < 0 else ("due today" if days_until == 0 else f"due in {days_until} day(s)")
            )
            due_note = f" Unit spaced review is {due_phrase} ({next_review})."
        candidates.append(
            _make_rec(
                rule_id="finish_current_drill" if attempted_items else "start_current_drill",
                kind="untouched_drill",
                action=f"Complete the remaining {len(not_tried_items)} item(s) in {drill_id} ({', '.join(it['qid'] for it in not_tried_items)}).",
                why=f"{totals['attemptedCount']}/{totals['problemCount']} items attempted so far in {drill_id}.{due_note}",
                unit=unit_code,
                archetypes=rem_archs,
                levels=rem_levels,
                count=len(not_tried_items),
                qids=[it["qid"] for it in not_tried_items],
                drill_id=drill_id,
            )
        )

    # 8. All clean including L4+ with no cap and no open weak spots -> ready for next unit
    if all_done_clean and max_attempted_level >= 4 and not cap_reason and not open_weak:
        next_u = unit_ctx.get("nextUnit")
        if isinstance(next_u, dict) and next_u.get("unitCode"):
            nu_code = next_u["unitCode"]
            nu_title = next_u.get("title") or nu_code
            nu_drills = next_u.get("untouchedDrills") or []
            if nu_drills:
                first_d = nu_drills[0]
                action = f"Advance to {nu_code} ({nu_title}): start {first_d['drillId']} (or generate a starter L1–L2 drill)."
                existing_id = first_d["drillId"]
                nu_archs = first_d.get("archetypes") or next_u.get("archetypes") or []
            else:
                action = f"Advance to {nu_code} ({nu_title}) and generate a starter L1–L2 drill."
                existing_id = None
                nu_archs = next_u.get("archetypes") or []
            candidates.append(
                _make_rec(
                    rule_id="ready_for_next_unit",
                    kind="advance_unit",
                    action=action,
                    why=(
                        f"All {totals['problemCount']}/{totals['problemCount']} items in {drill_id} (up to L{max_attempted_level}) "
                        f"passed clean with Mastery {mastery} (uncapped) and 0 open weak spots."
                    ),
                    unit=nu_code,
                    archetypes=nu_archs,
                    levels=[1, 2],
                    count=5,
                    drill_id=existing_id,
                    extra={"nextUnit": nu_code, "nextUnitTitle": nu_title},
                )
            )
        else:
            candidates.append(
                _make_rec(
                    rule_id="ready_for_next_unit",
                    kind="advance_unit",
                    action=f"Unit {unit_code} is mastered (clean through L{max_attempted_level}); advance to the next unit or chapter mixed drill.",
                    why=(
                        f"All {totals['problemCount']}/{totals['problemCount']} items in {drill_id} passed clean "
                        f"with Mastery {mastery} (uncapped) and 0 open weak spots."
                    ),
                    unit=unit_code,
                    archetypes=_dedup_preserve([it["archetypeKey"] for it in items]),
                    levels=[3, 4],
                    count=4,
                )
            )

    # 9. Learner wrote notes -> concept recap + targeted reinforcement alternative
    if note_qids:
        n_archs = _dedup_preserve([n["archetypeKey"] for n in totals["notes"] if n.get("archetypeKey")])
        n_levels = [n["level"] for n in totals["notes"] if isinstance(n.get("level"), int)] or [2]
        candidates.append(
            _make_rec(
                rule_id="note_guided_recap",
                kind="concept_recap",
                action=(
                    f"Revisit '{_UNIT_PAGE_SECTIONS['concepts']}' and '{_UNIT_PAGE_SECTIONS['formulas']}' on {unit_code} "
                    f"for {', '.join(note_qids)} to reinforce the points recorded in your Mistake Log notes."
                ),
                why=f"Learner recorded Mistake Log / revisit notes on {', '.join(note_qids)}.",
                unit=unit_code,
                archetypes=n_archs,
                levels=n_levels,
                count=max(4, len(n_archs) * 2),
                qids=note_qids,
                unit_page_section=_UNIT_PAGE_SECTIONS["concepts"],
            )
        )

    # 9b. Unpractised archetypes in a mastered or skipped-only unit
    if (
        (all_done_clean and any(c["ruleId"] == "ready_for_next_unit" for c in candidates))
        or (skipped_items and not wrong_items and not assisted_items)
    ) and unpractised:
        up_archs = [a["archetypeKey"] for a in unpractised[:3]]
        up_levels = sorted({int(a["baseLevel"]) for a in unpractised[:3] if isinstance(a.get("baseLevel"), int)}) or [2]
        candidates.append(
            _make_rec(
                rule_id="cover_unpractised_archetypes",
                kind="new_math_drill",
                action=f"Optional completeness drill in {unit_code} on unpractised archetype(s): {', '.join(up_archs)}.",
                why=f"{len(unpractised)} archetype(s) in {unit_code} have 0 practised items ({', '.join(up_archs)}).",
                unit=unit_code,
                archetypes=up_archs,
                levels=up_levels,
                count=4,
            )
        )

    # 10. Untouched drills in the unit as a ready-to-run alternative (only after starting current drill)
    if untouched_drills and attempted_items:
        higher = sorted(
            untouched_drills,
            key=lambda d: (-max((int(k) for k in d["levelMix"]), default=0), d["drillId"]),
        )[0]
        mix_str = ", ".join(f"L{lv}x{cnt}" for lv, cnt in higher["levelMix"].items())
        candidates.append(
            _make_rec(
                rule_id="untouched_drill",
                kind="untouched_drill",
                action=f"Practice existing untouched drill {higher['drillId']} ({higher['problemCount']} Qs: {mix_str}).",
                why=f"{len(untouched_drills)} untouched drill(s) already exist for {unit_code}.",
                unit=unit_code,
                archetypes=higher["archetypes"],
                levels=[int(lv) for lv in higher["levelMix"]],
                count=higher["problemCount"],
                drill_id=higher["drillId"],
            )
        )

    # Deduplicate by ruleId and identical drill-parameter signature while preserving priority order
    deduped: list[dict[str, Any]] = []
    seen_rules: set[str] = set()
    seen_param_sigs: set[tuple[Any, ...]] = set()
    for rec in candidates:
        p = rec["params"]
        param_sig = (
            p.get("unit") or "",
            p.get("drillId") or "",
            tuple(sorted(p.get("archetypes") or [])),
            tuple(p.get("levels") or []),
            tuple(sorted(p.get("focusTags") or [])),
            p.get("unitPageSection") or "",
        )
        if rec["ruleId"] not in seen_rules and param_sig not in seen_param_sigs:
            seen_rules.add(rec["ruleId"])
            seen_param_sigs.add(param_sig)
            deduped.append(rec)

    if not deduped:
        deduped.append(
            _make_rec(
                rule_id="general_unit_practice",
                kind="new_math_drill",
                action=f"Generate a mixed {unit_code} practice drill.",
                why="Continue building fluency across unit archetypes.",
                unit=unit_code,
                archetypes=_dedup_preserve([it["archetypeKey"] for it in items]),
                levels=[1, 2, 3],
                count=5,
            )
        )

    return {
        "primary": deduped[0],
        "alternatives": deduped[1:3],
    }


def build_drill_review(
    drill_id: str,
    *,
    repo_root: str | None = None,
    data_root: str | None = None,
    progress_dir: str | None = None,
    variants_dir: str | None = None,
    vault_dir: str | None = None,
    issue_log: str | None = None,
    today: datetime.date | str | None = None,
) -> dict[str, Any]:
    """Build a zero-leak read-only diagnostic report and recommendation for ``drill_id``."""
    resolved_root = repo_root or find_repo_root()
    resolved_data = data_root or os.environ.get("DRILLS_DATA_DIR", os.path.join(resolved_root, "drills", "data"))
    resolved_progress = progress_dir or progress_root(resolved_root)
    resolved_variants = variants_dir or os.environ.get(
        "VARIANTS_DIR", os.path.join(resolved_root, "drills", "variants")
    )
    resolved_vault = vault_dir or os.path.join(resolved_root, "math_engine", "reasoning_vault")
    resolved_today = _resolve_today(today)

    if drill_id.startswith("LAB-") or drill_id.startswith("DRL-PRG-"):
        raise ValueError(
            f"Drill '{drill_id}' is a PRG programming drill/lab; scripts.drill_review supports MATH drills only. "
            f"Use 'python -m code_engine.review_run {drill_id} <QID>' (review-code skill) instead."
        )

    drill_doc = _find_drill_doc(drill_id, resolved_data)
    is_prg = drill_doc.get("subject") == "PRG" or str(drill_doc.get("unitCode", "")).startswith("PRG-")
    if is_prg:
        raise ValueError(
            f"Drill '{drill_id}' is a PRG programming drill/lab; scripts.drill_review supports MATH drills only. "
            f"Use 'python -m code_engine.review_run {drill_id} <QID>' (review-code skill) instead."
        )

    raw_probs = [p for p in (drill_doc.get("problems") or []) if isinstance(p, dict)]
    if not raw_probs or not any((p.get("archetypeKey") or p.get("templateKey")) for p in raw_probs):
        raise ValueError(
            f"Drill '{drill_id}' has no problem archetypes (archetypeKey/templateKey); cannot build a drill review."
        )

    progress = _load_json_dict(os.path.join(resolved_progress, f"{drill_id}.json"))
    drill_states = (progress or {}).get("problems") if isinstance((progress or {}).get("problems"), dict) else {}

    id_map = _load_id_map(resolved_root)
    archetypes, trap_descriptions, trap_owners = _load_mth_vault_metadata(resolved_vault)
    drill_unit = str(drill_doc.get("unitCode") or "")

    items = [
        _build_item_report(
            prob,
            drill_states.get(prob.get("id")) if isinstance(drill_states.get(prob.get("id")), dict) else {},
            is_prg=is_prg,
            drill_unit=drill_unit,
            archetypes=archetypes,
            trap_descriptions=trap_descriptions,
        )
        for prob in (drill_doc.get("problems") or [])
        if isinstance(prob, dict)
    ]

    totals = _build_totals(drill_doc, items, progress)
    unit_ctx = _build_unit_context(
        drill_doc,
        items,
        drill_states,
        repo_root=resolved_root,
        data_root=resolved_data,
        progress_dir=resolved_progress,
        variants_dir=resolved_variants,
        vault_dir=resolved_vault,
        issue_log=issue_log,
        today=resolved_today,
        id_map=id_map,
        archetypes=archetypes,
        trap_descriptions=trap_descriptions,
    )
    recommendation = _compute_recommendations(
        drill_doc,
        items,
        totals,
        unit_ctx,
        archetypes,
        trap_owners,
    )

    return {
        "drillId": drill_id,
        "generatedForDate": resolved_today.isoformat(),
        "progressDir": resolved_progress,
        "totals": totals,
        "items": items,
        "unitContext": unit_ctx,
        "recommendation": recommendation,
    }


def _fmt_duration(ms: int | None) -> str:
    if ms is None:
        return "-"
    secs = round(ms / 1000.0)
    if secs < 60:
        return f"{secs}s"
    return f"{secs // 60}m{secs % 60:02d}s"


def format_drill_review(report: dict[str, Any]) -> str:
    """Format a ``build_drill_review`` report as readable plain text (zero-leak)."""
    t = report["totals"]
    u = report["unitContext"]
    rec = report["recommendation"]
    lines: list[str] = [
        f"DRILL REVIEW: {t['drillId']} ({t['unitCode']} · {t['unitTitle']})",
        f"Status: {t['practiceStatus']} | Score: {t['totalScore']}/{t['maxScore']} ({t['accuracyPct']}%) | "
        f"Attempt date: {t['attemptDate'] or '-'} | Time: {_fmt_duration(t['totalDurationMs'])}",
        f"Counts: clean={t['cleanCount']}, assisted/retry={t['assistedOrRetryCount']}, "
        f"wrong={t['wrongCount']}, skipped={t['skippedCount']}, notTried={t['notTriedCount']}",
        "",
        "ITEMS:",
    ]
    for it in report["items"]:
        rev = it["reveals"]
        rev_bits = []
        if rev["hints"]:
            rev_bits.append(f"hint×{rev['hints']}")
        if rev["setup"]:
            rev_bits.append("setup")
        if rev["steps"]:
            rev_bits.append("steps")
        if rev["solution"]:
            rev_bits.append("sol")
        rev_str = ",".join(rev_bits) if rev_bits else "none"
        traps_str = ", ".join(f"{tr['tag']} ({tr['description']})" for tr in it["matchedTraps"]) or "-"
        sim = it["similarUsage"]
        sim_str = f"opened={sim['opened']} att={sim['attempted']} clean={sim['clean']}" if sim["opened"] else "0"
        sc_str = "null" if it["score"] is None else f"{it['score']}"
        lines.append(
            f"  {it['qid']} | L{it['level']} | {it['archetypeKey']} | {it['outcome']} ({sc_str}) | "
            f"att={it['attempts']} | help={rev_str} | time={_fmt_duration(it['durationMs'])} | "
            f"similar=[{sim_str}] | traps={traps_str}"
        )
        if it["mistakes"]:
            lines.append(f"       mistakes={it['mistakes']}")
        if it["mistakeNote"]:
            lines.append(f"       mistakeNote: {it['mistakeNote']}")
        if it["revisitNote"]:
            lines.append(f"       revisitNote: {it['revisitNote']}")

    cap = u.get("masteryCap") or {}
    cap_str = f" (capped: {cap.get('reason')})" if cap.get("capped") else ""
    sched = u["reviewSchedule"]
    due_str = (
        f"{sched['nextReview']} ({sched['daysUntilReview']}d)"
        if sched.get("nextReview") is not None and sched.get("daysUntilReview") is not None
        else str(sched.get("nextReview") or "-")
    )
    lines.extend(
        [
            "",
            "UNIT CONTEXT:",
            f"  Mastery: {u['mastery']}{cap_str} | Last reviewed: {sched.get('lastReviewed') or '-'} | Next review: {due_str}",
            f"  Unpractised archetypes ({len(u['unpractisedArchetypes'])}): "
            + (", ".join(f"{a['archetypeKey']} (L{a['baseLevel']})" for a in u["unpractisedArchetypes"]) or "none"),
            f"  Untouched drills ({len(u['availableUntouchedDrills'])}): "
            + (
                ", ".join(
                    f"{d['drillId']} ({', '.join(f'L{lv}x{c}' for lv, c in d['levelMix'].items())})"
                    for d in u["availableUntouchedDrills"]
                )
                or "none"
            ),
        ]
    )
    if u["weakSpots"]["open"]:
        lines.append(
            "  Open weak spots: "
            + "; ".join(f"{w['tag']} ({w['matches']}x in {w['drillsCount']} drills)" for w in u["weakSpots"]["open"])
        )
    if u["weakSpots"]["repeatedAcrossDrills"]:
        lines.append(
            "  Repeated traps across drills: "
            + "; ".join(
                f"{r['tag']} ({r['matches']}x in {', '.join(r['drills'])})"
                for r in u["weakSpots"]["repeatedAcrossDrills"]
            )
        )
    if u["similarVariantsForMissed"]:
        lines.append(
            "  Similar variants for missed: "
            + "; ".join(
                f"{s['qid']} ({s['archetypeKey']}@L{s['level']}): {s['unattemptedAtLevel']}/{s['availableAtLevel']} ready"
                for s in u["similarVariantsForMissed"]
            )
        )

    lines.extend(["", "RECOMMENDATION:"])
    p = rec["primary"]
    lines.append(f"  [PRIMARY: {p['ruleId']}] {p['action']}")
    lines.append(f"    Why: {p['why']}")
    lines.append(f"    Params: {json.dumps(p['params'], ensure_ascii=False)}")
    for idx, alt in enumerate(rec.get("alternatives") or [], start=1):
        lines.append(f"  [ALT {idx}: {alt['ruleId']}] {alt['action']}")
        lines.append(f"    Why: {alt['why']}")
        lines.append(f"    Params: {json.dumps(alt['params'], ensure_ascii=False)}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `python -m scripts.drill_review`."""
    ap = argparse.ArgumentParser(
        prog="python -m scripts.drill_review",
        description="Read-only post-drill review and deterministic next-step recommendations.",
    )
    ap.add_argument("drill_id", help="Drill ID (e.g. DRL-MTH-T02-C01-U01-03)")
    ap.add_argument("--json", action="store_true", dest="as_json", help="Output structured JSON report")
    ap.add_argument("--data-root", default=None, help="Override drills/data directory")
    ap.add_argument("--progress-dir", default=None, help="Override progress directory")
    ap.add_argument("--today", default=None, help="Override current date (YYYY-MM-DD) for due-date checks")
    args = ap.parse_args(argv)

    try:
        report = build_drill_review(
            args.drill_id,
            data_root=args.data_root,
            progress_dir=args.progress_dir,
            today=args.today,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_drill_review(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
