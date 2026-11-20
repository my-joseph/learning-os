# -*- coding: utf-8 -*-
"""Compare extracted source core cards against a unit's reasoning vault (read-only gap report)
and measure batch novelty for saturation stopping.

Reports:
1. Core cards matched to existing vault archetypes (by trap tag or skill keywords) vs unmatched cards.
2. New trap tags found in cards that do not exist in any vault archetype.
3. Reasoning moves and levels present in cards that the vault currently lacks.
4. Exam formats seen across cards (e.g. 5-option choice with distractor patterns).
5. ``laterUnit`` cards grouped by target future unit (kept for later, not drilled now).

With ``--novelty <batch_cards.jsonl>``, reports how many cards in the batch represent new cores
versus fuzzy duplicates of existing cards (same ``skill`` + ``reasoningMove`` + ``traps``) so
batched extraction can stop once two consecutive batches add ``< 2`` new cores.

Usage:
    python -m scripts.source_gap MTH-T02-C01-U01
    python -m scripts.source_gap MTH-T02-C01-U01 --json
    python -m scripts.source_gap MTH-T02-C01-U02 --novelty batch1.jsonl
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any, Iterable

from math_engine.ai_drill_ingest import load_scope_archetypes
from math_engine.bridge import MIN_BRIDGE_UNITS
from math_engine.source_cores import (
    REASONING_MOVES,
    CoreCardError,
    cores_path,
    load_core_cards,
    validate_core_card,
)
from scripts.bridge_scope import eligible_units as load_eligible_units

SATURATION_MIN_NEW_CORES = 2

_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "into",
        "that",
        "this",
        "using",
        "via",
        "given",
        "find",
        "determine",
        "compute",
        "calculate",
        "evaluate",
        "solve",
        "number",
        "numbers",
        "value",
        "values",
        "problem",
        "problems",
        "form",
        "standard",
    }
)

_TRAP_BOILERPLATE: frozenset[str] = frozenset({"trap", "error", "mistake", "bug", "sign", "wrong"})
_UNIT_SLUG_TOKEN_RE = re.compile(r"^(?:mth|phy|prg|t\d+|c\d+|u\d+)$")

_MOVE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "reverse": ("reverse", "backward", "backwards", "target", "parameter", "unknown", "missing", "given the result"),
    "translate": ("translate", "convert", "plane", "graph", "table", "polar", "visual", "represent"),
    "diagnose": ("diagnose", "verify.flaw", "first wrong line", "wrong line", "flaw", "mistake"),
    "multi-relation": ("combine", "both", "system", "synthesis", "interleav", "plus", "two relation"),
    "case-check": ("discriminant", "condition", "bound", "positive", "rule out", "case", "domain", "constraint"),
    "generalise": ("general", "cycle", "period", "pattern", "identity", "for all", "mod"),
    "model": ("model", "circuit", "impedance", "oscillator", "physical", "real-world", "application"),
}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z]{3,}", (text or "").lower())
    return {w for w in words if w not in _STOPWORDS}


def _light_stem(word: str) -> str:
    if len(word) >= 5 and word.endswith("ing"):
        return word[:-3]
    if len(word) >= 4 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def _fuzzy_skill_tokens(text: str) -> set[str]:
    return {_light_stem(w) for w in _tokens(text)}


def _norm_skill_str(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _card_trap_tags(card: dict[str, Any]) -> set[str]:
    return {
        t["tag"].strip().lower()
        for t in card.get("traps") or []
        if isinstance(t, dict) and isinstance(t.get("tag"), str) and t["tag"].strip()
    }


def _trap_slug_tokens(tag: str) -> set[str]:
    parts = [p for p in re.split(r"[-_\s]+", tag.lower()) if p]
    cleaned = {
        _light_stem(p) for p in parts if len(p) >= 2 and not _UNIT_SLUG_TOKEN_RE.match(p) and p not in _TRAP_BOILERPLATE
    }
    if cleaned:
        return cleaned
    return {p for p in parts if not _UNIT_SLUG_TOKEN_RE.match(p)}


def _trap_similarity(traps_a: set[str], traps_b: set[str]) -> float:
    if not traps_a and not traps_b:
        return 1.0
    if not traps_a or not traps_b:
        return 0.0
    exact = len(traps_a & traps_b) / len(traps_a | traps_b)

    toks_a = [_trap_slug_tokens(t) for t in traps_a]
    toks_b = [_trap_slug_tokens(t) for t in traps_b]

    def _avg_best(src: list[set[str]], dst: list[set[str]]) -> float:
        total = 0.0
        for sa in src:
            best = 0.0
            for sb in dst:
                union = sa | sb
                if union:
                    score = len(sa & sb) / len(union)
                    if score > best:
                        best = score
            total += best
        return total / len(src)

    fuzzy = 0.5 * (_avg_best(toks_a, toks_b) + _avg_best(toks_b, toks_a))
    return max(exact, fuzzy)


def cards_are_fuzzy_duplicate(
    candidate: dict[str, Any],
    existing: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    """Return ``(is_duplicate, details)`` comparing two core cards on ``skill + reasoningMove + traps``."""
    move_a = str(candidate.get("reasoningMove") or "").strip().lower()
    move_b = str(existing.get("reasoningMove") or "").strip().lower()
    if move_a != move_b:
        return (
            False,
            {"skillSimilarity": 0.0, "trapSimilarity": 0.0, "reason": "different reasoningMove"},
        )

    tok_a = _fuzzy_skill_tokens(str(candidate.get("skill") or ""))
    tok_b = _fuzzy_skill_tokens(str(existing.get("skill") or ""))
    union = tok_a | tok_b
    tok_jaccard = (len(tok_a & tok_b) / len(union)) if union else 0.0
    seq_ratio = difflib.SequenceMatcher(
        None,
        _norm_skill_str(str(candidate.get("skill") or "")),
        _norm_skill_str(str(existing.get("skill") or "")),
    ).ratio()
    skill_sim = round(max(tok_jaccard, seq_ratio), 3)

    traps_a = _card_trap_tags(candidate)
    traps_b = _card_trap_tags(existing)
    shared_traps = sorted(traps_a & traps_b)
    trap_sim = round(_trap_similarity(traps_a, traps_b), 3)

    if (shared_traps or (traps_a and traps_b and trap_sim >= 0.5)) and skill_sim >= 0.40:
        return (
            True,
            {
                "skillSimilarity": skill_sim,
                "trapSimilarity": trap_sim,
                "sharedTraps": shared_traps,
                "reason": "same move + overlapping skill and trap tags",
            },
        )
    if traps_a and traps_a == traps_b and skill_sim >= 0.30:
        return (
            True,
            {
                "skillSimilarity": skill_sim,
                "trapSimilarity": trap_sim,
                "sharedTraps": shared_traps,
                "reason": "same move + identical trap tags and related skill",
            },
        )
    if skill_sim >= 0.72 and (not traps_a or traps_a.issubset(traps_b) or trap_sim >= 0.30):
        return (
            True,
            {
                "skillSimilarity": skill_sim,
                "trapSimilarity": trap_sim,
                "sharedTraps": shared_traps,
                "reason": "same move + high skill similarity",
            },
        )
    return (
        False,
        {
            "skillSimilarity": skill_sim,
            "trapSimilarity": trap_sim,
            "sharedTraps": shared_traps,
            "reason": "distinct core",
        },
    )


def _load_jsonl_batch(
    batch_path: str,
    *,
    valid_unit_codes: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    if not os.path.isfile(batch_path):
        raise FileNotFoundError(f"Batch cards file not found: {batch_path}")
    cards: list[dict[str, Any]] = []
    with open(batch_path, "r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                card = json.loads(line)
            except ValueError as exc:
                raise CoreCardError(f"{batch_path}:{line_no}: invalid JSON: {exc}") from exc
            errs = validate_core_card(card, valid_unit_codes=valid_unit_codes)
            if errs:
                raise CoreCardError(f"{batch_path}:{line_no}: invalid core card: " + "; ".join(errs))
            cards.append(card)
    return cards


def _card_identity_key(card: dict[str, Any]) -> tuple[str, str]:
    cid = str(card.get("id") or "")
    ref = json.dumps(card.get("sourceRef") or {}, sort_keys=True, ensure_ascii=False)
    return (cid, ref)


def compute_batch_novelty(
    unit_code: str,
    batch_cards_path: str,
    *,
    sources_dir: str | None = None,
    valid_unit_codes: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Compare a batch of extracted core cards against existing cards for ``unit_code``.

    Works whether ``batch_cards_path`` is evaluated before or after appending to
    ``sources/_cores/<unit_code>.jsonl`` (exact self-copies with matching ``id`` and
    ``sourceRef`` are excluded from the baseline pool). Within-batch duplicates are also
    counted as duplicates so repeated items in one batch do not inflate novelty.
    """
    existing = load_core_cards(
        unit_code,
        sources_dir=sources_dir,
        validate=True,
        valid_unit_codes=valid_unit_codes,
    )
    batch_cards = _load_jsonl_batch(batch_cards_path, valid_unit_codes=valid_unit_codes)

    batch_identities = {_card_identity_key(c) for c in batch_cards}
    baseline = [c for c in existing if _card_identity_key(c) not in batch_identities]
    pool: list[dict[str, Any]] = list(baseline)

    new_cards: list[dict[str, Any]] = []
    duplicate_cards: list[dict[str, Any]] = []

    for card in batch_cards:
        best_match: tuple[dict[str, Any], dict[str, Any]] | None = None
        best_rank = (-1.0, -1.0)
        for prior in pool:
            is_dup, details = cards_are_fuzzy_duplicate(card, prior)
            if is_dup:
                rank_key = (float(details["skillSimilarity"]), float(details["trapSimilarity"]))
                if rank_key > best_rank:
                    best_rank = rank_key
                    best_match = (prior, details)
        if best_match is not None:
            prior_card, details = best_match
            duplicate_cards.append(
                {
                    "id": card["id"],
                    "skill": card["skill"],
                    "reasoningMove": card["reasoningMove"],
                    "level": card["level"],
                    "matchedCardId": prior_card["id"],
                    "skillSimilarity": details["skillSimilarity"],
                    "trapSimilarity": details["trapSimilarity"],
                    "reason": details["reason"],
                }
            )
        else:
            new_cards.append(
                {
                    "id": card["id"],
                    "skill": card["skill"],
                    "reasoningMove": card["reasoningMove"],
                    "level": card["level"],
                    "traps": sorted(_card_trap_tags(card)),
                }
            )
            pool.append(card)

    new_count = len(new_cards)
    return {
        "unitCode": unit_code,
        "batchPath": os.path.abspath(batch_cards_path),
        "existingCardsCount": len(baseline),
        "batchCardsCount": len(batch_cards),
        "newCoresCount": new_count,
        "duplicateCardsCount": len(duplicate_cards),
        "saturationThreshold": SATURATION_MIN_NEW_CORES,
        "belowSaturationThreshold": new_count < SATURATION_MIN_NEW_CORES,
        "newCards": new_cards,
        "duplicateCards": duplicate_cards,
    }


def format_novelty_report(report: dict[str, Any]) -> str:
    """Format ``compute_batch_novelty`` output for CLI display."""
    lines = [
        f"Novelty report for {report['unitCode']}",
        f"Batch file: {report['batchPath']}",
        f"Result: {report['newCoresCount']} new core(s), {report['duplicateCardsCount']} duplicate(s) "
        f"out of {report['batchCardsCount']} batch card(s) (baseline: {report['existingCardsCount']} existing)",
    ]
    if report["belowSaturationThreshold"]:
        lines.append(
            f"SATURATION SIGNAL: < {report['saturationThreshold']} new cores in this batch "
            "(stop extraction when two consecutive batches add < 2 new cores)."
        )

    lines.append("")
    lines.append(f"New cores ({report['newCoresCount']}):")
    if not report["newCards"]:
        lines.append("  (none)")
    for item in report["newCards"]:
        traps = f" [traps: {', '.join(item['traps'])}]" if item["traps"] else ""
        lines.append(f"  - [{item['id']}] L{item['level']} {item['reasoningMove']} — {item['skill']}{traps}")

    lines.append("")
    lines.append(f"Duplicates ({report['duplicateCardsCount']}):")
    if not report["duplicateCards"]:
        lines.append("  (none)")
    for item in report["duplicateCards"]:
        lines.append(
            f"  - [{item['id']}] L{item['level']} {item['reasoningMove']} — {item['skill']} "
            f"~= [{item['matchedCardId']}] (skill={item['skillSimilarity']:.2f}, trap={item['trapSimilarity']:.2f}; "
            f"{item['reason']})"
        )

    return "\n".join(lines)


def _archetype_traps(arch: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for t in arch.get("cognitiveTraps") or []:
        if isinstance(t, dict) and isinstance(t.get("trapTag"), str):
            out.add(t["trapTag"])
        elif isinstance(t, str):
            out.add(t)
    return out


def _infer_vault_moves(archetypes: list[dict[str, Any]]) -> set[str]:
    moves: set[str] = set()
    for arch in archetypes:
        lvl = arch.get("level")
        if isinstance(lvl, int) and lvl <= 2:
            moves.add("direct")
        blob = " ".join(
            str(arch.get(k) or "")
            for k in ("archetypeKey", "name", "coreConcept", "mentalModel", "levelNote", "governingRelation")
        ).lower()
        for move, keywords in _MOVE_KEYWORDS.items():
            if any(kw in blob for kw in keywords):
                moves.add(move)
        if isinstance(lvl, int) and lvl >= 4:
            moves.add("multi-relation")
    return moves


def build_gap_report(
    unit_code: str,
    *,
    sources_dir: str | None = None,
    vault_dir: str | None = None,
    eligible_units: Iterable[str] | None = None,
    data_root: str | None = None,
    progress_dir: str | None = None,
    valid_unit_codes: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Compute a read-only gap report comparing ``unit_code``'s core cards and reasoning vault."""
    cpath = cores_path(unit_code, sources_dir=sources_dir)
    cards = load_core_cards(
        unit_code,
        sources_dir=sources_dir,
        validate=True,
        valid_unit_codes=valid_unit_codes,
    )
    archetypes = load_scope_archetypes(unit_code, vault_dir=vault_dir)

    current_cards: list[dict[str, Any]] = []
    later_by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    carried_count = 0
    for card in cards:
        carried = bool(card.get("carriedFrom"))
        if carried:
            carried_count += 1
        later = card.get("laterUnit")
        raw_units = card.get("units")
        in_units = isinstance(raw_units, list) and any(isinstance(u, str) and u.strip() == unit_code for u in raw_units)
        if isinstance(later, str) and later.strip() and later.strip() != unit_code and not (carried and in_units):
            later_by_unit[later.strip()].append(card)
        else:
            current_cards.append(card)

    arch_traps: dict[str, set[str]] = {}
    arch_tokens: dict[str, set[str]] = {}
    all_vault_traps: set[str] = set()
    vault_levels: set[int] = set()

    for arch in archetypes:
        key = str(arch.get("archetypeKey") or "")
        traps = _archetype_traps(arch)
        arch_traps[key] = traps
        all_vault_traps.update(traps)
        arch_tokens[key] = _tokens(
            " ".join(str(arch.get(k) or "") for k in ("archetypeKey", "name", "coreConcept", "mentalModel"))
        )
        if isinstance(arch.get("level"), int):
            vault_levels.add(arch["level"])

    matched_cards: list[dict[str, Any]] = []
    unmatched_cards: list[dict[str, Any]] = []

    for card in current_cards:
        c_traps = {t["tag"] for t in card.get("traps") or [] if isinstance(t, dict) and t.get("tag")}
        c_tokens = _tokens(f"{card.get('skill', '')} {card.get('difficultyDriver', '')}")
        hits: list[dict[str, Any]] = []
        for arch in archetypes:
            key = str(arch.get("archetypeKey") or "")
            shared_traps = sorted(c_traps & arch_traps[key])
            shared_tokens = sorted(c_tokens & arch_tokens[key])
            min_tok_hit = 1 if len(c_tokens) <= 2 else 2
            skill_hit = len(shared_tokens) >= min_tok_hit
            if shared_traps or skill_hit:
                hits.append(
                    {
                        "archetypeKey": key,
                        "matchedTraps": shared_traps,
                        "matchedTerms": shared_tokens[:6],
                    }
                )
        summary = {
            "id": card["id"],
            "skill": card["skill"],
            "level": card["level"],
            "reasoningMove": card["reasoningMove"],
        }
        if card.get("carriedFrom"):
            summary["carriedFrom"] = card["carriedFrom"]
        if hits:
            matched_cards.append({**summary, "matches": hits})
        else:
            unmatched_cards.append(summary)

    # New trap tags not in any existing vault archetype
    new_traps_map: dict[str, dict[str, Any]] = {}
    for card in current_cards:
        for t in card.get("traps") or []:
            tag = t["tag"]
            if tag in all_vault_traps:
                continue
            entry = new_traps_map.setdefault(tag, {"tag": tag, "descriptions": [], "cardIds": []})
            desc = t.get("description", "")
            if desc and desc not in entry["descriptions"]:
                entry["descriptions"].append(desc)
            if card["id"] not in entry["cardIds"]:
                entry["cardIds"].append(card["id"])

    # Reasoning moves & levels gap
    card_levels = Counter(int(c["level"]) for c in current_cards)
    card_moves = Counter(str(c["reasoningMove"]) for c in current_cards)
    vault_moves = _infer_vault_moves(archetypes)
    missing_levels_in_vault = sorted(lvl for lvl in card_levels if lvl not in vault_levels)
    missing_moves_in_vault = sorted(mv for mv in card_moves if mv not in vault_moves)
    unseen_moves_in_vault = [mv for mv in REASONING_MOVES if mv not in vault_moves]

    # Exam formats seen
    format_groups: dict[tuple[str, int | None], dict[str, Any]] = {}
    representations: Counter[str] = Counter()
    for card in current_cards:
        fmt = card.get("format") or {}
        kind = str(fmt.get("kind") or "unknown")
        opt_count = fmt.get("optionCount")
        fkey = (kind, opt_count)
        grp = format_groups.setdefault(
            fkey,
            {
                "kind": kind,
                "optionCount": opt_count,
                "count": 0,
                "distractorPatterns": [],
                "cardIds": [],
            },
        )
        grp["count"] += 1
        grp["cardIds"].append(card["id"])
        for pat in fmt.get("distractorPatterns") or []:
            if pat not in grp["distractorPatterns"]:
                grp["distractorPatterns"].append(pat)
        if card.get("representation"):
            representations[str(card["representation"])] += 1

    exam_formats = sorted(
        format_groups.values(),
        key=lambda g: (-g["count"], g["kind"], g["optionCount"] or 0),
    )

    later_groups = {
        target: [
            {
                "id": c["id"],
                "level": c["level"],
                "reasoningMove": c["reasoningMove"],
                "skill": c["skill"],
                "sourceRef": c["sourceRef"],
            }
            for c in items
        ]
        for target, items in sorted(later_by_unit.items())
    }

    # Bridge candidates: multi-unit cards (`units` list with >= 2 unit codes) grouped by unit pair/set
    bridge_by_pair: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        raw_units = card.get("units")
        if isinstance(raw_units, list):
            pair = tuple(sorted({u.strip() for u in raw_units if isinstance(u, str) and u.strip()}))
            if len(pair) >= MIN_BRIDGE_UNITS:
                bridge_by_pair[pair].append(card)

    if eligible_units is not None:
        eligible_set = {u.strip() for u in eligible_units if isinstance(u, str) and u.strip()}
    elif bridge_by_pair:
        eligible_set = load_eligible_units(data_root=data_root, progress_dir=progress_dir)
    else:
        eligible_set = set()

    bridge_candidates: list[dict[str, Any]] = []
    for pair, items in sorted(bridge_by_pair.items()):
        missing_units = [u for u in pair if u not in eligible_set]
        is_eligible = len(eligible_set) >= MIN_BRIDGE_UNITS and not missing_units
        bridge_candidates.append(
            {
                "units": list(pair),
                "eligible": is_eligible,
                "missingUnits": missing_units,
                "cards": [
                    {
                        "id": c["id"],
                        "level": c["level"],
                        "reasoningMove": c["reasoningMove"],
                        "skill": c["skill"],
                        "sourceRef": c["sourceRef"],
                    }
                    for c in items
                ],
            }
        )

    return {
        "unitCode": unit_code,
        "cardsPath": cpath,
        "cardsFileExists": os.path.isfile(cpath),
        "totalCards": len(cards),
        "currentCardsCount": len(current_cards),
        "carriedCardsCount": carried_count,
        "laterCardsCount": sum(len(v) for v in later_groups.values()),
        "vaultArchetypeCount": len(archetypes),
        "matchedCards": matched_cards,
        "unmatchedCards": unmatched_cards,
        "newTraps": sorted(new_traps_map.values(), key=lambda x: x["tag"]),
        "levels": {
            "vaultBaseLevels": sorted(vault_levels),
            "cardLevelCounts": {str(k): v for k, v in sorted(card_levels.items())},
            "cardLevelsMissingInVault": missing_levels_in_vault,
        },
        "reasoningMoves": {
            "vaultEvidencedMoves": sorted(vault_moves),
            "cardMoveCounts": dict(sorted(card_moves.items())),
            "cardMovesMissingInVault": missing_moves_in_vault,
            "allVaultMissingMoves": unseen_moves_in_vault,
        },
        "examFormats": exam_formats,
        "representations": dict(sorted(representations.items())),
        "laterUnitCards": later_groups,
        "bridgeCandidates": bridge_candidates,
    }


def format_gap_report(report: dict[str, Any]) -> str:
    """Format ``build_gap_report`` output as a concise human-readable report."""
    carried = int(report.get("carriedCardsCount") or 0)
    carried_note = f" ({carried} carried-forward)" if carried else ""
    file_note = (
        f"file: {report['cardsPath']}"
        if report["cardsFileExists"]
        else f"no local file at {report['cardsPath']}; carried-forward only"
        if carried
        else f"file: {report['cardsPath']}"
    )
    lines = [
        f"Source Gap Report for {report['unitCode']}",
        f"Cards: {report['currentCardsCount']} current-unit{carried_note}, {report['laterCardsCount']} laterUnit "
        f"({file_note})",
        f"Vault archetypes in scope: {report['vaultArchetypeCount']}",
    ]

    if not report["cardsFileExists"] and report["totalCards"] == 0:
        lines.append("")
        lines.append("No core cards file found yet. Run scripts.source_find and extract core cards first.")
        return "\n".join(lines)

    lines.append("")
    matched = report["matchedCards"]
    unmatched = report["unmatchedCards"]
    lines.append(f"Matched cards ({len(matched)}/{report['currentCardsCount']}):")
    if not matched:
        lines.append("  (none)")
    for item in matched:
        targets = ", ".join(
            f"{m['archetypeKey']} ("
            + (f"trap:{','.join(m['matchedTraps'])}" if m["matchedTraps"] else f"skill:{','.join(m['matchedTerms'])}")
            + ")"
            for m in item["matches"]
        )
        carried_tag = f" [carried from {item['carriedFrom']}]" if item.get("carriedFrom") else ""
        lines.append(
            f"  - [{item['id']}] L{item['level']} {item['reasoningMove']} — {item['skill']}{carried_tag} -> {targets}"
        )

    lines.append("")
    lines.append(f"Unmatched cards — candidate new archetypes ({len(unmatched)}):")
    if not unmatched:
        lines.append("  (none)")
    for item in unmatched:
        carried_tag = f" [carried from {item['carriedFrom']}]" if item.get("carriedFrom") else ""
        lines.append(f"  - [{item['id']}] L{item['level']} {item['reasoningMove']} — {item['skill']}{carried_tag}")

    lines.append("")
    new_traps = report["newTraps"]
    lines.append(f"New trap tags not in any archetype ({len(new_traps)}):")
    if not new_traps:
        lines.append("  (none)")
    for t in new_traps:
        desc = t["descriptions"][0] if t["descriptions"] else ""
        lines.append(f"  - {t['tag']}: {desc} (cards: {', '.join(t['cardIds'])})")

    lines.append("")
    lv = report["levels"]
    mv = report["reasoningMoves"]
    lines.append("Levels & reasoning moves:")
    lines.append(f"  Vault base levels: {lv['vaultBaseLevels'] or ['none']}")
    lines.append("  Card levels: " + (", ".join(f"L{k}x{v}" for k, v in lv["cardLevelCounts"].items()) or "none"))
    lines.append(
        "  Card levels missing from vault: " + (", ".join(f"L{x}" for x in lv["cardLevelsMissingInVault"]) or "none")
    )
    lines.append("  Card moves: " + (", ".join(f"{k}x{v}" for k, v in mv["cardMoveCounts"].items()) or "none"))
    lines.append("  Card moves missing from vault: " + (", ".join(mv["cardMovesMissingInVault"]) or "none"))

    lines.append("")
    formats = report["examFormats"]
    lines.append(f"Exam formats seen ({len(formats)}):")
    if not formats:
        lines.append("  (none)")
    for fmt in formats:
        opt = f" ({fmt['optionCount']} options)" if fmt.get("optionCount") else ""
        pats = f" — distractors: {', '.join(fmt['distractorPatterns'])}" if fmt["distractorPatterns"] else ""
        lines.append(f"  - {fmt['kind']}{opt}: {fmt['count']} card(s){pats}")
    if report["representations"]:
        reps = ", ".join(f"{k}x{v}" for k, v in report["representations"].items())
        lines.append(f"  Representations: {reps}")

    lines.append("")
    later = report["laterUnitCards"]
    lines.append(f"Deferred laterUnit cards ({report['laterCardsCount']}):")
    if not later:
        lines.append("  (none)")
    for target_unit, items in later.items():
        lines.append(f"  {target_unit} ({len(items)} card(s)):")
        for c in items:
            lines.append(f"    - [{c['id']}] L{c['level']} {c['reasoningMove']} — {c['skill']}")

    lines.append("")
    bridges = report.get("bridgeCandidates") or []
    total_bridge_cards = sum(len(g["cards"]) for g in bridges)
    lines.append(f"Bridge candidates ({len(bridges)} pair(s), {total_bridge_cards} card(s)):")
    if not bridges:
        lines.append("  (none)")
    for grp in bridges:
        pair_label = " + ".join(grp["units"])
        status = "ELIGIBLE" if grp["eligible"] else f"not eligible — needs {', '.join(grp['missingUnits'])}"
        lines.append(f"  {pair_label} [{status}] ({len(grp['cards'])} card(s)):")
        for c in grp["cards"]:
            lines.append(f"    - [{c['id']}] L{c['level']} {c['reasoningMove']} — {c['skill']}")

    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.source_gap",
        description="Read-only gap report comparing a unit's source core cards against its reasoning vault.",
    )
    parser.add_argument("unit", help="Target unit code (e.g. MTH-T02-C01-U01).")
    parser.add_argument(
        "--novelty",
        metavar="BATCH_JSONL",
        default=None,
        help="Compare a batch JSONL file against existing unit cards and report new cores vs fuzzy duplicates.",
    )
    parser.add_argument(
        "--sources-dir",
        default=None,
        help="Override sources directory (default: LEARNINGOS_SOURCES_DIR or <main>/sources).",
    )
    parser.add_argument(
        "--vault-dir",
        default=None,
        help="Override reasoning vault directory (default: math_engine/reasoning_vault).",
    )
    parser.add_argument("--data-root", default=None, help="Override drills/data directory for bridge eligibility.")
    parser.add_argument("--progress-dir", default=None, help="Override progress directory for bridge eligibility.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.novelty:
            novelty = compute_batch_novelty(
                args.unit,
                args.novelty,
                sources_dir=args.sources_dir,
            )
            if args.json:
                print(json.dumps(novelty, ensure_ascii=False, indent=2))
            else:
                print(format_novelty_report(novelty))
            return 0
        report = build_gap_report(
            args.unit,
            sources_dir=args.sources_dir,
            vault_dir=args.vault_dir,
            data_root=args.data_root,
            progress_dir=args.progress_dir,
        )
    except (CoreCardError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_gap_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
