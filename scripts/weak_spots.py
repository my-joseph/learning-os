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
from urllib.parse import quote

from code_engine.quality_checks import load_universal
from progress_store import find_repo_root, item_score, progress_root
from progress_store import labs_root as default_labs_root

MIN_MATCHES = 2
CLOSE_AFTER = 2
WINDOW = 5
RECENT_WINDOW = 5
FIXED_STREAK = 3
FIXED_VISIBLE_DAYS = 1


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


def _is_prg(doc: dict) -> bool:
    return (
        doc.get("subject") == "PRG"
        or str(doc.get("unitCode", "")).startswith("PRG-")
        or str(doc.get("drillId", "")).startswith("DRL-PRG-")
    )


def _first_ts(state: dict, fallback: str) -> str:
    attempts = state.get("attempts") or []
    if attempts:
        return attempts[0].get("ts") or fallback
    reviews = state.get("reviews") or []
    if reviews:
        return reviews[0].get("at") or reviews[0].get("ts") or fallback
    return fallback


def _is_assisted_state(state: dict) -> bool:
    attempts = [a for a in (state.get("attempts") or []) if isinstance(a, dict) and a.get("kind") != "variant"]
    return bool(
        state.get("setupRevealedBeforeAnswer")
        or state.get("solutionRevealedBeforeAnswer")
        or state.get("exampleViewedAt")
        or (state.get("hintsRevealed") or 0) > 0
        or any(a.get("setupRevealed") or a.get("solutionRevealed") or a.get("exampleViewed") for a in attempts)
    )


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
    if state.get("skipped"):
        return 0.0
    assisted = _is_assisted_state(state)
    reviews = state.get("reviews") or []
    if reviews:
        if reviews[-1].get("verdict") == "pass":
            raw = 1.0 if reviews[0].get("verdict") == "pass" else 0.5
            return min(raw, 0.5) if assisted else raw
        return 0.0
    if state.get("lastTestReport") is not None or state.get("score") is not None:
        return 0.0
    if state.get("attempts"):
        sc, _ = _item_score(state)
        return sc
    return -1.0


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


def load_items(
    data_root: str | None = None,
    progress_dir: str | None = None,
    labs_root: str | None = None,
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
    cwd_mth_vault = os.path.join("math_engine", "reasoning_vault")
    mth_vault_dir = (
        cwd_mth_vault if os.path.isdir(cwd_mth_vault) else os.path.join(repo_root, "math_engine", "reasoning_vault")
    )
    for vpath in glob.glob(os.path.join(mth_vault_dir, "*.json")):
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
            if is_prg:
                score = _prg_item_score(state)
                if score < 0:
                    continue
                assisted = _is_assisted_state(state)
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
                        skipped=bool(state.get("skipped")),
                        assisted=assisted,
                        matched=[],
                        subject="PRG",
                        passed=bool(reviews and reviews[-1].get("verdict") == "pass") or (score == 1.0),
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
                        matched=_collect_matched_traps(state),
                        subject="MTH",
                        passed=(score == 1.0),
                        revisit_note=revisit_note,
                        state=dict(state),
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
    items = [i for i in load_items(data_root, progress_dir) if i.unit == unit]
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
_CHECK_PLUGIN_PREFIX = re.compile(r"^(?:@[^/]+/|[^/]+/)")
_CHECK_ID_PREFIX = re.compile(r"^(?:qc|u)-(?:prg-(?:t\d+-)?(?:c\d+-)?(?:u\d+-)?)?", re.IGNORECASE)


def trap_name(trap_id: str) -> str:
    """Plain-language name from a MTH trap tag: `t02-c01-u01-i-squared-positive-one-trap` -> `I squared positive one`."""
    words = _TRAP_PREFIX.sub("", trap_id.lower())
    words = re.sub(r"-trap$", "", words).replace("-", " ").strip()
    return words[:1].upper() + words[1:] if words else trap_id


def load_prg_check_names() -> dict[str, str]:
    """Load the canonical PRG check & ESLint plain-name map from `code_engine/check_names.json`."""
    for path in (
        os.path.join("code_engine", "check_names.json"),
        os.path.join(find_repo_root(), "code_engine", "check_names.json"),
    ):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items() if isinstance(k, str) and isinstance(v, str) and v.strip()}
    return {}


def humanize_check_id(check_id: str) -> str:
    """Fallback plain-language humanizer for an unmapped PRG check or ESLint rule id."""
    cleaned = check_id.strip()
    if not cleaned:
        return ""
    words = _CHECK_PLUGIN_PREFIX.sub("", cleaned)
    words = _CHECK_ID_PREFIX.sub("", words)
    words = re.sub(r"[-_]+", " ", words).strip().lower()
    return words[:1].upper() + words[1:] if words else cleaned


def prg_check_name(check_id: str, names_map: dict[str, str] | None = None) -> str:
    """Short plain-language name for a PRG rubric check (`QC-*`, `U-*`) or ESLint rule."""
    mapping = names_map if names_map is not None else load_prg_check_names()
    if check_id in mapping:
        return mapping[check_id]
    return humanize_check_id(check_id)


def plain_mistake_name(entry_id: str, subject: str, names_map: dict[str, str] | None = None) -> str:
    """Plain-language name for a MTH trap tag or PRG check/lint rule id."""
    if str(subject).upper() == "PRG":
        return prg_check_name(entry_id, names_map)
    return trap_name(entry_id)


def _unit_matches_current(unit_code: str, current_unit: str | None) -> bool:
    if not unit_code or not current_unit:
        return False
    return unit_code == current_unit or unit_code.startswith(current_unit + "-U")


def _fallback_drill_href(drill_id: str | None, qid: str | None, subject: str) -> str | None:
    if not drill_id:
        return None
    if drill_id.startswith("LAB-"):
        return f"/code/lab/{drill_id}?m={quote(qid, safe='')}" if qid else f"/code/lab/{drill_id}"
    prefix = "/code" if (subject == "PRG" or drill_id.startswith("DRL-PRG-")) else "/math"
    return f"{prefix}/{drill_id}?q={quote(qid, safe='')}" if qid else f"{prefix}/{drill_id}"


def _parse_iso_date(raw: str | None) -> date | None:
    if not raw:
        return None
    cand = raw.strip()[:10]
    try:
        return date.fromisoformat(cand)
    except ValueError:
        return None


def recent_mistakes(
    items: list[Item],
    *,
    subject: str | None = None,
    current_unit: str | None = None,
    today: str | None = None,
    due_counts: dict[str, int] | None = None,
    titles: dict[str, str] | None = None,
    check_sentences: dict[str, str] | None = None,
    trap_descriptions: dict[str, str] | None = None,
    check_names: dict[str, str] | None = None,
) -> list[dict]:
    """Build the workspace-scoped 'What I get wrong' list ranked by recent miss rate.

    - Includes MTH traps and PRG rubric/lint signals the learner actually missed.
    - Computes recent miss rate over the last `RECENT_WINDOW` (5) tries.
    - Marks an entry 'fixed' when there is no miss in the last `FIXED_STREAK` (3) tries;
      fixed entries remain visible for `FIXED_VISIBLE_DAYS` (1) day after the 3rd clean try,
      then drop out.
    - Ranks active entries before fixed entries, pinning `current_unit` entries first,
      then by recent miss rate descending, recent misses descending, total matches descending,
      most recent miss date descending, and id ascending.
    """
    norm_subject = subject.strip().upper() if isinstance(subject, str) and subject.strip() else None
    today_date = _parse_iso_date(today) or date.today()
    resolved_titles = titles if titles is not None else _load_titles()
    if check_sentences is None:
        _, _, _, check_sentences = _load_prg_vault_meta()
    resolved_trap_desc = trap_descriptions if trap_descriptions is not None else _load_mth_trap_descriptions()
    resolved_check_names = check_names if check_names is not None else load_prg_check_names()
    resolved_due = due_counts or {}

    entries: list[dict] = []

    def _build_entry(
        entry_id: str,
        entry_subject: str,
        tries: list[tuple[Item, bool]],
        total_matches: int,
    ) -> dict | None:
        missed_items = [it for it, missed in tries if missed]
        if not missed_items:
            return None

        is_fixed = len(tries) >= FIXED_STREAK and all(not m for _, m in tries[-FIXED_STREAK:])
        fixed_at: str | None = None
        if is_fixed:
            last_miss_idx = max(idx for idx, (_, m) in enumerate(tries) if m)
            fixed_item = tries[last_miss_idx + FIXED_STREAK][0]
            fixed_at = fixed_item.ts[:10] if fixed_item.ts else None
            fixed_date = _parse_iso_date(fixed_at)
            if fixed_date is not None and (today_date - fixed_date).days > FIXED_VISIBLE_DAYS:
                return None

        recent = tries[-RECENT_WINDOW:]
        recent_tries = len(recent)
        recent_misses = sum(1 for _, m in recent if m)
        recent_miss_rate = round(recent_misses / recent_tries, 4) if recent_tries else 0.0

        units_missed = sorted({it.unit for it in missed_items if it.unit})
        in_current_unit = bool(
            current_unit and any(_unit_matches_current(u, current_unit) for u in units_missed)
        )
        latest_hit = missed_items[-1]
        last_date = max((it.ts for it in missed_items), default="")[:10]
        due_count = int(resolved_due.get(entry_id, 0))

        if is_fixed:
            practise_href = None
        elif due_count > 0:
            practise_href = f"/review?trap={quote(entry_id, safe='')}"
        else:
            practise_href = _fallback_drill_href(latest_hit.drill, latest_hit.pid, entry_subject)

        primary_unit = (
            next((u for u in units_missed if _unit_matches_current(u, current_unit)), None)
            or (latest_hit.unit if latest_hit.unit else (units_missed[0] if units_missed else ""))
        )
        detail = (
            check_sentences.get(entry_id, "")
            if entry_subject == "PRG"
            else resolved_trap_desc.get(entry_id, "")
        )
        row: dict = {
            "id": entry_id,
            "name": plain_mistake_name(entry_id, entry_subject, resolved_check_names),
            "subject": entry_subject,
            "status": "fixed" if is_fixed else "active",
            "recentMisses": recent_misses,
            "recentTries": recent_tries,
            "recentMissRate": recent_miss_rate,
            "matches": total_matches,
            "drills": len({it.drill for it in missed_items if it.drill}),
            "last": last_date,
            "fixedAt": fixed_at,
            "units": units_missed,
            "unitCode": primary_unit,
            "unitTitle": resolved_titles.get(primary_unit, ""),
            "inCurrentUnit": in_current_unit,
            "dueCount": due_count,
            "latestDrillId": latest_hit.drill or None,
            "latestQid": latest_hit.pid or None,
            "practiseHref": practise_href,
        }
        if detail:
            row["detail"] = detail
        return row

    if norm_subject in (None, "MTH"):
        mth_items = [i for i in items if i.subject != "PRG"]
        missed_mth_traps = sorted({t for i in mth_items for t in i.matched if t})
        for trap in missed_mth_traps:
            tries: list[tuple[Item, bool]] = []
            total_matches = 0
            for it in mth_items:
                if trap in it.matched:
                    tries.append((it, True))
                    total_matches += it.matched.count(trap)
                elif it.trap == trap and not it.skipped and it.score == 1.0:
                    tries.append((it, False))
            entry = _build_entry(trap, "MTH", tries, total_matches)
            if entry is not None:
                entries.append(entry)

    if norm_subject in (None, "PRG"):
        prg_items = [i for i in items if i.subject == "PRG"]
        missed_prg_sigs = sorted({s for i in prg_items for s in i.signals if s})
        for sig in missed_prg_sigs:
            tries = []
            total_matches = 0
            for it in prg_items:
                if sig in it.signals:
                    tries.append((it, True))
                    total_matches += 1
                elif it.passed and not it.assisted and not it.skipped and _is_prg_signal_applicable(sig, it):
                    tries.append((it, False))
            entry = _build_entry(sig, "PRG", tries, total_matches)
            if entry is not None:
                entries.append(entry)

    # Deterministic multi-pass stable sort:
    # active before fixed, current unit pinned first, recentMissRate desc, recentMisses desc,
    # total matches desc, last date desc, id asc.
    entries.sort(key=lambda e: e["id"])
    entries.sort(key=lambda e: e["last"], reverse=True)
    entries.sort(
        key=lambda e: (
            1 if e["status"] == "fixed" else 0,
            0 if e["inCurrentUnit"] else 1,
            -e["recentMissRate"],
            -e["recentMisses"],
            -e["matches"],
        )
    )
    return entries


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


def _build_unit_reports(
    scope: str | None = None,
    data_root: str = "drills/data",
    progress_dir: str | None = None,
) -> list[dict]:
    items = load_items(data_root, progress_dir)
    if scope:
        items = [i for i in items if i.unit == scope or i.unit.startswith(scope + "-U")]
    if not items:
        return []
    titles = _load_titles()
    traps = trap_status(items)
    _, _, _, check_sentences = _load_prg_vault_meta()
    trap_descriptions = _load_mth_trap_descriptions()
    reports: list[dict] = []
    for unit in sorted({i.unit for i in items}):
        its = [i for i in items if i.unit == unit]
        open_traps = sorted(
            (t for t, s in traps.items() if s["open"] and unit in s["units"]),
            key=lambda t: traps[t]["last"],
            reverse=True,
        )
        closed_traps = [t for t, s in traps.items() if not s["open"] and unit in s["units"]]
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
