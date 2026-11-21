# -*- coding: utf-8 -*-
"""Compare extracted source core cards against a unit's reasoning vault (read-only gap report)
and measure batch novelty for saturation stopping.

Supports both Math/PHY units (against ``math_engine/reasoning_vault/``) and PRG units
(against ``code_engine/reasoning_vault/`` — ``cognitiveTraps`` and ``qualityChecks``).

Reports:
1. Core cards matched to existing vault archetypes using structured scoring (trap tags and
   descriptions weighted highest, normalized skill/operation fields with stopwords removed and
   IDF weighting, and unitCode/level compatibility — assigning each matched card to its best
   archetype plus at most one runner-up above a high threshold) vs unmatched cards.
2. New trap tags found in cards that do not exist in any vault archetype.
3. For Math: reasoning moves, levels, exam formats, laterUnit, and bridge candidates.
   For PRG: new bug patterns/smells, new ``QC-*`` qualityCheck ideas, missing archetype kinds
   (across the 5 PRG archetypes in ``rules/04``), missing levels, languages/concepts, and laterUnit.

With ``--novelty <batch_cards.jsonl>``, reports how many cards in the batch represent new cores
versus fuzzy duplicates of existing cards so batched extraction can stop once two consecutive
batches add ``< 2`` new cores.

Usage:
    python -m scripts.source_gap MTH-T02-C01-U01
    python -m scripts.source_gap PRG-T01-C01-U02
    python -m scripts.source_gap PRG-T01-C01-U02 --json
    python -m scripts.source_gap PRG-T01-C01-U02 --novelty batch1.jsonl
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any, Iterable

from code_engine.ai_drill_ingest import load_scope_archetypes as load_code_scope_archetypes
from math_engine.ai_drill_ingest import load_scope_archetypes as load_math_scope_archetypes
from math_engine.bridge import MIN_BRIDGE_UNITS
from math_engine.source_cores import (
    PRG_ARCHETYPE_KINDS,
    REASONING_MOVES,
    CoreCardError,
    cores_path,
    is_prg_card,
    is_prg_unit,
    load_core_cards,
    validate_core_card,
)
from scripts.bridge_scope import eligible_units as load_eligible_units

SATURATION_MIN_NEW_CORES = 2
MATCH_THRESHOLD = 0.34
PRG_MATCH_THRESHOLD = 0.28
RUNNER_UP_THRESHOLD = 0.58
_TRAP_WEIGHT = 0.48
_SKILL_WEIGHT = 0.37
_COMPAT_WEIGHT = 0.15

# Consolidated PRG vault trap tags often unify several finer-grained ad-hoc card trap tags.
# Maps normalized (lowercase) card trap tag -> tuple of canonical vault trapTag names.
PRG_TRAP_TAG_ALIASES: dict[str, tuple[str, ...]] = {
    "category-confusion": ("coercion-context-confusion", "reference-identity-confusion"),
    "builtin-confusion": ("coercion-context-confusion",),
    "special-number-equality": ("coercion-context-confusion", "loose-equality-type-coercion"),
    "equality-semantics": ("loose-equality-type-coercion", "reference-identity-confusion"),
    "callback-timing": ("async-continuation-order", "collection-result-contract"),
    "sparse-length": ("collection-cardinality-order",),
    "preserve-input": ("in-place-array-mutation", "in-place-mutation"),
    "recovery-path": ("unhandled-rejection-fast-fail", "async-result-propagation"),
    "aggregate-policy": ("unhandled-rejection-fast-fail", "concurrent-result-alignment"),
    "chain-return": ("async-result-propagation",),
    "type-boundary": ("static-runtime-contract-drift", "type-model-too-broad"),
    "aggregation-state": ("accumulator-seed-update", "in-place-mutation"),
    "type-precision": ("type-model-too-broad",),
    "partial-coverage": ("checker-coverage-gap",),
    "overrestriction": ("checker-coverage-gap",),
    "predicate-inversion": ("collection-result-contract", "collection-cardinality-order"),
    "operation-contract": ("collection-result-contract", "mutation-observation-confusion"),
}

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
_PRG_TOKEN_ALIASES = {
    "asynchronous": "async",
    "async": "async",
    "awaiting": "await",
    "awaited": "await",
    "handlers": "continuation",
    "handler": "continuation",
    "reactions": "continuation",
    "reaction": "continuation",
    "callbacks": "continuation",
    "callback": "continuation",
    "returned": "return",
    "returns": "return",
    "returning": "return",
    "exposes": "return",
    "expose": "return",
    "forwards": "return",
    "forward": "return",
    "values": "result",
    "value": "result",
    "results": "result",
    "propagation": "propagate",
    "operations": "operation",
    "transformations": "transform",
    "transformation": "transform",
    "filtering": "filter",
    "mapping": "map",
    "aggregation": "aggregate",
    "accumulation": "accumulate",
    "collections": "collection",
    "entries": "entry",
    "elements": "element",
}

_MOVE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "reverse": ("reverse", "backward", "backwards", "target", "parameter", "unknown", "missing", "given the result"),
    "translate": ("translate", "convert", "plane", "graph", "table", "polar", "visual", "represent"),
    "diagnose": ("diagnose", "verify.flaw", "first wrong line", "wrong line", "flaw", "mistake"),
    "multi-relation": ("combine", "both", "system", "synthesis", "interleav", "plus", "two relation"),
    "case-check": ("discriminant", "condition", "bound", "positive", "rule out", "case", "domain", "constraint"),
    "generalise": ("general", "cycle", "period", "pattern", "identity", "for all", "mod"),
    "model": ("model", "circuit", "impedance", "oscillator", "physical", "real-world", "application"),
}

_PRG_ARCHETYPE_KIND_MAP: dict[str, str] = {
    "problem-solving": "implement",
    "implement": "implement",
    "implement-with-tests": "implement",
    "code-tracing": "predict-output",
    "predict-output": "predict-output",
    "trace-explain": "predict-output",
    "debugging": "find-the-bug",
    "find-the-bug": "find-the-bug",
    "find-bug": "find-the-bug",
    "fix-bug": "find-the-bug",
    "code-review": "find-the-bug",
    "review": "find-the-bug",
    "refactoring": "refactor",
    "refactor": "refactor",
    "project-based": "project-milestone",
    "project-milestone": "project-milestone",
    "project": "project-milestone",
    "lab-milestone": "project-milestone",
    "milestone": "project-milestone",
}


_MATCH_STOPWORDS: frozenset[str] = _STOPWORDS | frozenset(
    {
        "check",
        "checks",
        "result",
        "results",
        "apply",
        "use",
        "used",
        "make",
        "making",
        "without",
        "when",
        "where",
        "which",
        "while",
        "across",
        "before",
        "after",
        "between",
        "both",
        "each",
        "every",
        "only",
        "other",
        "another",
        "same",
        "different",
        "one",
        "two",
        "three",
        "four",
        "several",
        "multiple",
        "all",
        "any",
        "not",
        "are",
        "was",
        "were",
        "can",
        "may",
        "must",
        "should",
        "will",
        "does",
        "has",
        "have",
        "had",
        "its",
        "their",
        "they",
        "them",
        "then",
        "than",
        "also",
        "such",
        "how",
        "what",
        "whether",
        "instead",
        "rather",
        "keep",
        "kept",
        "give",
        "take",
        "get",
        "show",
        "treat",
        "avoid",
        "ensure",
        "remain",
        "remains",
        "cause",
        "causes",
        "allow",
        "allows",
        "require",
        "requires",
        "represent",
        "representing",
        "express",
        "expressing",
        "compare",
        "comparing",
        "based",
        "following",
        "followed",
        "way",
        "case",
        "cases",
        "step",
        "steps",
        "work",
        "working",
        "data",
        "behavior",
        "behaviour",
        "wrong",
        "error",
        "mistake",
        "trap",
        "bug",
        "small",
        "simple",
        "new",
        "build",
        "reason",
    }
)
_LATEX_NOISE_TOKENS: frozenset[str] = frozenset(
    {"frac", "sqrt", "left", "right", "quad", "qquad", "text", "implies", "land", "lor", "cdot", "times", "pm", "big"}
)
_TAG_MATCH_BOILERPLATE: frozenset[str] = frozenset(
    {
        "trap",
        "error",
        "mistake",
        "bug",
        "wrong",
        "cx",
        "qc",
        "confusion",
        "surprise",
        "drift",
        "mismatch",
        "state",
        "flow",
        "order",
        "check",
        "rule",
        "rules",
        "boundary",
        "contract",
        "update",
        "value",
        "values",
        "return",
        "returns",
        "missing",
        "omitted",
        "forgot",
        "dropped",
        "invalid",
        "bad",
        "fail",
        "failure",
        "type",
        "behavior",
        "behaviour",
    }
)
_MATCH_TOKEN_ALIASES: dict[str, str] = {
    "asynchronous": "async",
    "async": "async",
    "rationalise": "rational",
    "rationalize": "rational",
    "rationalising": "rational",
    "rationalizing": "rational",
    "rationalised": "rational",
    "rationalized": "rational",
    "mutating": "mutat",
    "mutate": "mutat",
    "mutates": "mutat",
    "mutation": "mutat",
    "mutations": "mutat",
    "immutable": "immut",
    "preserving": "preserv",
    "preserve": "preserv",
    "preserves": "preserv",
    "preservation": "preserv",
    "transforming": "transform",
    "transform": "transform",
    "transforms": "transform",
    "transformation": "transform",
    "transformations": "transform",
    "aggregating": "aggregat",
    "aggregate": "aggregat",
    "aggregates": "aggregat",
    "aggregation": "aggregat",
    "accumulating": "accumul",
    "accumulate": "accumul",
    "accumulates": "accumul",
    "accumulator": "accumul",
    "accumulation": "accumul",
    "reducing": "reduc",
    "reduce": "reduc",
    "reduces": "reduc",
    "reduction": "reduc",
    "reducer": "reduc",
    "filtering": "filter",
    "filter": "filter",
    "filters": "filter",
    "mapping": "map",
    "map": "map",
    "maps": "map",
    "deriving": "deriv",
    "derive": "deriv",
    "derives": "deriv",
    "derived": "deriv",
    "factoring": "factor",
    "factor": "factor",
    "factors": "factor",
    "factorize": "factor",
    "factorization": "factor",
    "conjugate": "conjug",
    "conjugates": "conjug",
    "conjugation": "conjug",
    "handlers": "handler",
    "handler": "handler",
    "callbacks": "callback",
    "callback": "callback",
    "collections": "collect",
    "collection": "collect",
    "arrays": "array",
    "array": "array",
    "promises": "promis",
    "promise": "promis",
    "settling": "settl",
    "settled": "settl",
    "settlement": "settl",
    "settle": "settl",
}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z]{3,}", (text or "").lower())
    return {w for w in words if w not in _STOPWORDS}


def _normalize_match_token(word: str) -> str:
    if word in _MATCH_TOKEN_ALIASES:
        return _MATCH_TOKEN_ALIASES[word]
    if len(word) >= 6 and word.endswith("ing"):
        word = word[:-3]
    elif len(word) >= 5 and word.endswith("ed"):
        word = word[:-2]
    elif len(word) >= 5 and word.endswith("ies"):
        word = word[:-3] + "y"
    elif len(word) >= 4 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        word = word[:-1]
    return _MATCH_TOKEN_ALIASES.get(word, word)


def _match_tokens(text: str) -> set[str]:
    """Extract normalized, stopword-free tokens for structured card-to-archetype matching."""
    cleaned = re.sub(r"\\[a-zA-Z]+", " ", text or "")
    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", cleaned)
    words = re.findall(r"[a-z]{3,}", cleaned.lower())
    out: set[str] = set()
    for w in words:
        if w in _MATCH_STOPWORDS or w in _LATEX_NOISE_TOKENS:
            continue
        norm = _normalize_match_token(w)
        if norm not in _MATCH_STOPWORDS and len(norm) >= 3:
            out.add(norm)
    return out


def _match_tag_tokens(tag: str) -> set[str]:
    """Extract normalized non-boilerplate tokens from a trap tag or QC identifier."""
    parts = [p for p in re.split(r"[-_\s]+", (tag or "").lower()) if p]
    out: set[str] = set()
    for p in parts:
        if len(p) < 2 or _UNIT_SLUG_TOKEN_RE.match(p) or p in _TAG_MATCH_BOILERPLATE:
            continue
        norm = _normalize_match_token(p)
        if norm not in _TAG_MATCH_BOILERPLATE:
            out.add(norm)
    return out


def _flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flatten_text(v) for v in value)
    if isinstance(value, dict):
        return " ".join(_flatten_text(v) for v in value.values())
    return ""


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


def _normalize_tag(tag: str) -> str:
    """Normalize ad-hoc trap tags so punctuation, separators, and suffixes do not dominate matching."""
    tokens = _trap_slug_tokens(tag)
    return " ".join(sorted(tokens))


def _prg_content_tokens(card: dict[str, Any]) -> set[str]:
    fields = (
        "skill",
        "concept",
        "bugPattern",
        "smell",
        "testsCatch",
        "difficultyDriver",
        "notes",
    )
    parts = [str(card.get(field) or "") for field in fields]
    parts.extend(str(trap.get("description") or "") for trap in card.get("traps") or [] if isinstance(trap, dict))
    parts.extend(str(qc.get("check") or "") for qc in card.get("qualityCheckIdeas") or [] if isinstance(qc, dict))
    return {_canonical_prg_token(token) for token in _tokens(" ".join(parts))}


def _prg_identity_tokens(card: dict[str, Any]) -> set[str]:
    return {_canonical_prg_token(token) for token in _tokens(f"{card.get('skill', '')} {card.get('concept', '')}")}


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _canonical_prg_token(token: str) -> str:
    return _PRG_TOKEN_ALIASES.get(token, _PRG_TOKEN_ALIASES.get(_light_stem(token), _light_stem(token)))


def _exact_prg_core(candidate: dict[str, Any], existing: dict[str, Any]) -> bool:
    """Exact core means normalized descriptions and trap/QC content match, independent of provenance."""
    fields = ("skill", "concept", "bugPattern", "smell", "testsCatch", "difficultyDriver", "notes")
    text_matches = all(
        _norm_skill_str(str(candidate.get(k) or "")) == _norm_skill_str(str(existing.get(k) or "")) for k in fields
    )
    if not text_matches:
        return False

    def trap_signature(card: dict[str, Any]) -> list[tuple[str, str]]:
        return sorted(
            (
                _normalize_tag(str(trap.get("tag") or "")),
                _norm_skill_str(str(trap.get("description") or "")),
            )
            for trap in card.get("traps") or []
            if isinstance(trap, dict)
        )

    def qc_signature(card: dict[str, Any]) -> list[tuple[str, str, str]]:
        return sorted(
            (
                str(qc.get("id") or "").strip().lower(),
                _norm_skill_str(str(qc.get("check") or "")),
                str(qc.get("severity") or "").strip().lower(),
            )
            for qc in card.get("qualityCheckIdeas") or []
            if isinstance(qc, dict)
        )

    return trap_signature(candidate) == trap_signature(existing) and qc_signature(candidate) == qc_signature(existing)


def _card_qc_ids(card: dict[str, Any]) -> set[str]:
    return {
        qc["id"].strip()
        for qc in card.get("qualityCheckIdeas") or []
        if isinstance(qc, dict) and isinstance(qc.get("id"), str) and qc["id"].strip()
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
    """Return ``(is_duplicate, details)`` comparing two core cards (Math or PRG)."""
    cand_prg = is_prg_card(candidate)
    ex_prg = is_prg_card(existing)
    if cand_prg != ex_prg:
        return (False, {"skillSimilarity": 0.0, "trapSimilarity": 0.0, "reason": "different card profile"})

    if cand_prg:
        kind_a = str(candidate.get("archetypeKind") or "").strip().lower()
        kind_b = str(existing.get("archetypeKind") or "").strip().lower()
        language_a = str(candidate.get("language") or "").strip().lower()
        language_b = str(existing.get("language") or "").strip().lower()
        if kind_a != kind_b or language_a != language_b:
            return (
                False,
                {"skillSimilarity": 0.0, "trapSimilarity": 0.0, "reason": "different archetypeKind or language"},
            )
        if _exact_prg_core(candidate, existing):
            return (
                True,
                {
                    "skillSimilarity": 1.0,
                    "trapSimilarity": round(
                        _trap_similarity(
                            {_normalize_tag(t) for t in _card_trap_tags(candidate)},
                            {_normalize_tag(t) for t in _card_trap_tags(existing)},
                        ),
                        3,
                    ),
                    "duplicateType": "exact",
                    "reason": "same normalized core description, archetypeKind, and language",
                },
            )
        identity_sim = _jaccard(_prg_identity_tokens(candidate), _prg_identity_tokens(existing))
        content_sim = _jaccard(_prg_content_tokens(candidate), _prg_content_tokens(existing))
        # Require overlap in the stated skill/concept as well as the broader card, so shared boilerplate alone
        # cannot mark two cards as repeats. Tags are normalized but are not required to match.
        if identity_sim >= 0.05 and content_sim >= 0.10:
            return (
                True,
                {
                    "skillSimilarity": round(identity_sim, 3),
                    "contentSimilarity": round(content_sim, 3),
                    "trapSimilarity": round(
                        _trap_similarity(
                            {_normalize_tag(t) for t in _card_trap_tags(candidate)},
                            {_normalize_tag(t) for t in _card_trap_tags(existing)},
                        ),
                        3,
                    ),
                    "duplicateType": "near",
                    "reason": "same archetypeKind and language with overlapping skill, concept, and card content",
                },
            )
        return (
            False,
            {
                "skillSimilarity": round(identity_sim, 3),
                "contentSimilarity": round(content_sim, 3),
                "trapSimilarity": 0.0,
                "reason": "distinct core",
            },
        )
    else:
        move_a = str(candidate.get("reasoningMove") or "").strip().lower()
        move_b = str(existing.get("reasoningMove") or "").strip().lower()
        if move_a != move_b:
            return (
                False,
                {"skillSimilarity": 0.0, "trapSimilarity": 0.0, "reason": "different reasoningMove"},
            )
        desc_a = str(candidate.get("skill") or "")
        desc_b = str(existing.get("skill") or "")

    tok_a = _fuzzy_skill_tokens(desc_a)
    tok_b = _fuzzy_skill_tokens(desc_b)
    union = tok_a | tok_b
    tok_jaccard = (len(tok_a & tok_b) / len(union)) if union else 0.0
    seq_ratio = difflib.SequenceMatcher(
        None,
        _norm_skill_str(desc_a),
        _norm_skill_str(desc_b),
    ).ratio()
    skill_sim = round(max(tok_jaccard, seq_ratio), 3)

    traps_a = _card_trap_tags(candidate)
    traps_b = _card_trap_tags(existing)
    if cand_prg:
        traps_a = traps_a | {q.lower() for q in _card_qc_ids(candidate)}
        traps_b = traps_b | {q.lower() for q in _card_qc_ids(existing)}
    shared_traps = sorted(traps_a & traps_b)
    trap_sim = round(_trap_similarity(traps_a, traps_b), 3)

    axis = "kind" if cand_prg else "move"
    if (shared_traps or (traps_a and traps_b and trap_sim >= 0.5)) and skill_sim >= 0.40:
        return (
            True,
            {
                "skillSimilarity": skill_sim,
                "trapSimilarity": trap_sim,
                "sharedTraps": shared_traps,
                "reason": f"same {axis} + overlapping skill and trap tags",
                "duplicateType": "near",
            },
        )
    if traps_a and traps_a == traps_b and skill_sim >= 0.30:
        return (
            True,
            {
                "skillSimilarity": skill_sim,
                "trapSimilarity": trap_sim,
                "sharedTraps": shared_traps,
                "reason": f"same {axis} + identical trap tags and related skill",
                "duplicateType": "near",
            },
        )
    if skill_sim >= 0.72 and (not traps_a or traps_a.issubset(traps_b) or trap_sim >= 0.30):
        return (
            True,
            {
                "skillSimilarity": skill_sim,
                "trapSimilarity": trap_sim,
                "sharedTraps": shared_traps,
                "reason": f"same {axis} + high skill similarity",
                "duplicateType": "near",
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
    registry_path: str | None = None,
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
            errs = validate_core_card(card, valid_unit_codes=valid_unit_codes, registry_path=registry_path)
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
    registry_path: str | None = None,
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
        registry_path=registry_path,
    )
    batch_cards = _load_jsonl_batch(
        batch_cards_path,
        valid_unit_codes=valid_unit_codes,
        registry_path=registry_path,
    )

    batch_identities = {_card_identity_key(c) for c in batch_cards}
    baseline = [c for c in existing if _card_identity_key(c) not in batch_identities]
    pool: list[dict[str, Any]] = list(baseline)

    new_cards: list[dict[str, Any]] = []
    duplicate_cards: list[dict[str, Any]] = []
    exact_duplicate_cards: list[dict[str, Any]] = []
    near_duplicate_cards: list[dict[str, Any]] = []

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
        axis_key = "archetypeKind" if is_prg_card(card) else "reasoningMove"
        axis_val = str(card.get(axis_key) or "")
        if best_match is not None:
            prior_card, details = best_match
            dup_entry: dict[str, Any] = {
                "id": card["id"],
                "skill": card["skill"],
                axis_key: axis_val,
                "level": card["level"],
                "matchedCardId": prior_card["id"],
                "skillSimilarity": details["skillSimilarity"],
                "trapSimilarity": details["trapSimilarity"],
                "contentSimilarity": details.get("contentSimilarity"),
                "duplicateType": details.get("duplicateType", "near"),
                "reason": details["reason"],
            }
            duplicate_cards.append(dup_entry)
            if dup_entry["duplicateType"] == "exact":
                exact_duplicate_cards.append(dup_entry)
            else:
                near_duplicate_cards.append(dup_entry)
        else:
            new_entry: dict[str, Any] = {
                "id": card["id"],
                "skill": card["skill"],
                axis_key: axis_val,
                "level": card["level"],
                "traps": sorted(_card_trap_tags(card)),
            }
            new_cards.append(new_entry)
            pool.append(card)

    new_count = len(new_cards)
    return {
        "unitCode": unit_code,
        "track": "prg" if is_prg_unit(unit_code) else "math",
        "batchPath": os.path.abspath(batch_cards_path),
        "existingCardsCount": len(baseline),
        "batchCardsCount": len(batch_cards),
        "newCoresCount": new_count,
        "duplicateCardsCount": len(duplicate_cards),
        "exactDuplicatesCount": len(exact_duplicate_cards),
        "nearDuplicatesCount": len(near_duplicate_cards),
        "saturationThreshold": SATURATION_MIN_NEW_CORES,
        "belowSaturationThreshold": new_count < SATURATION_MIN_NEW_CORES,
        "newCards": new_cards,
        "duplicateCards": duplicate_cards,
        "exactDuplicates": exact_duplicate_cards,
        "nearDuplicates": near_duplicate_cards,
    }


def format_novelty_report(report: dict[str, Any]) -> str:
    """Format ``compute_batch_novelty`` output for CLI display."""
    lines = [
        f"Novelty report for {report['unitCode']}",
        f"Batch file: {report['batchPath']}",
        f"Result: {report['newCoresCount']} new core(s), {report['duplicateCardsCount']} duplicate(s) "
        f"({report['exactDuplicatesCount']} exact, {report['nearDuplicatesCount']} near) "
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
        axis = item.get("archetypeKind") or item.get("reasoningMove") or "?"
        lines.append(f"  - [{item['id']}] L{item['level']} {axis} — {item['skill']}{traps}")

    lines.append("")
    lines.append(f"Exact duplicates ({report['exactDuplicatesCount']}):")
    if not report["exactDuplicates"]:
        lines.append("  (none)")
    for item in report["exactDuplicates"]:
        axis = item.get("archetypeKind") or item.get("reasoningMove") or "?"
        lines.append(f"  - [{item['id']}] {axis} — {item['skill']} = [{item['matchedCardId']}]")

    lines.append("")
    lines.append(f"Near-duplicates ({report['nearDuplicatesCount']}):")
    if not report["nearDuplicates"]:
        lines.append("  (none)")
    for item in report["nearDuplicates"]:
        axis = item.get("archetypeKind") or item.get("reasoningMove") or "?"
        lines.append(
            f"  - [{item['id']}] L{item['level']} {axis} — {item['skill']} "
            f"~= [{item['matchedCardId']}] (skill={item['skillSimilarity']:.2f}, "
            f"content={(item.get('contentSimilarity') or 0.0):.2f}, trap={item['trapSimilarity']:.2f}; "
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


def _archetype_quality_check_ids(arch: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for qc in arch.get("qualityChecks") or []:
        if isinstance(qc, dict) and isinstance(qc.get("id"), str) and qc["id"].strip():
            out.add(qc["id"].strip())
    return out


def _normalize_prg_archetype_kind(raw: str | None) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    key = raw.strip().lower().replace("_", "-")
    return _PRG_ARCHETYPE_KIND_MAP.get(key)


def _infer_vault_prg_kinds(archetypes: list[dict[str, Any]]) -> set[str]:
    kinds: set[str] = set()
    for arch in archetypes:
        for field in ("archetype", "archetypeKind", "codeType"):
            mapped = _normalize_prg_archetype_kind(arch.get(field))
            if mapped:
                kinds.add(mapped)
        for ct in arch.get("codeTypes") or []:
            mapped = _normalize_prg_archetype_kind(ct)
            if mapped:
                kinds.add(mapped)
    return kinds


def _infer_vault_moves(archetypes: list[dict[str, Any]]) -> set[str]:
    moves: set[str] = set()
    for arch in archetypes:
        lvl = arch.get("level")
        if isinstance(lvl, int) and lvl <= 2:
            moves.add("direct")
        blob = " ".join(
            _flatten_text(arch.get(k))
            for k in ("archetypeKey", "name", "coreConcept", "mentalModel", "levelNote", "governingRelation")
        ).lower()
        for move, keywords in _MOVE_KEYWORDS.items():
            if any(kw in blob for kw in keywords):
                moves.add(move)
        if isinstance(lvl, int) and lvl >= 4:
            moves.add("multi-relation")
    return moves


def _archetype_trap_entries(arch: dict[str, Any]) -> list[tuple[str, set[str]]]:
    """Return ``(trap_tag, description_tokens)`` pairs for an archetype's cognitiveTraps."""
    entries: list[tuple[str, set[str]]] = []
    for t in arch.get("cognitiveTraps") or []:
        if isinstance(t, dict):
            tag = str(t.get("trapTag") or "").strip()
            desc = f"{t.get('name') or ''} {t.get('description') or ''}"
            if tag or desc.strip():
                entries.append((tag, _match_tokens(desc)))
        elif isinstance(t, str) and t.strip():
            entries.append((t.strip(), set()))
    return entries


def _card_trap_entries(card: dict[str, Any]) -> list[tuple[str, set[str]]]:
    """Return ``(trap_tag, description_tokens)`` pairs for a card's traps."""
    entries: list[tuple[str, set[str]]] = []
    for t in card.get("traps") or []:
        if isinstance(t, dict):
            tag = str(t.get("tag") or "").strip()
            desc = str(t.get("description") or "")
            if tag or desc.strip():
                entries.append((tag, _match_tokens(desc)))
    return entries


def _card_qc_entries(card: dict[str, Any]) -> list[tuple[str, set[str]]]:
    entries: list[tuple[str, set[str]]] = []
    for qc in card.get("qualityCheckIdeas") or []:
        if isinstance(qc, dict):
            qid = str(qc.get("id") or "").strip()
            chk = str(qc.get("check") or "")
            if qid or chk.strip():
                entries.append((qid, _match_tokens(chk)))
    return entries


def _archetype_qc_entries(arch: dict[str, Any]) -> list[tuple[str, set[str]]]:
    entries: list[tuple[str, set[str]]] = []
    for qc in arch.get("qualityChecks") or []:
        if isinstance(qc, dict):
            qid = str(qc.get("id") or "").strip()
            chk = str(qc.get("check") or "")
            if qid or chk.strip():
                entries.append((qid, _match_tokens(chk)))
    return entries


def _dice_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return (2.0 * len(left & right)) / (len(left) + len(right))


def _archetype_trap_aliases(arch: dict[str, Any]) -> dict[str, str]:
    """Return ``alias_lower -> canonical_trapTag`` for any vault-declared cognitiveTraps[].aliases."""
    alias_map: dict[str, str] = {}
    for t in arch.get("cognitiveTraps") or []:
        if not isinstance(t, dict):
            continue
        tag = str(t.get("trapTag") or "").strip()
        if not tag:
            continue
        for alias in t.get("aliases") or []:
            if isinstance(alias, str) and alias.strip():
                alias_map[alias.strip().lower()] = tag
    return alias_map


def _prg_trap_alias_hits(
    c_trap_map: dict[str, str],
    a_trap_map: dict[str, str],
    vault_aliases: dict[str, str] | None = None,
) -> list[tuple[str, str]]:
    """Find ``(card_tag, vault_tag)`` matches via PRG_TRAP_TAG_ALIASES or vault-declared aliases."""
    hits: list[tuple[str, str]] = []
    for c_low, c_orig in sorted(c_trap_map.items()):
        if vault_aliases and c_low in vault_aliases:
            hits.append((c_orig, vault_aliases[c_low]))
            continue
        for canonical in PRG_TRAP_TAG_ALIASES.get(c_low, ()):
            v_orig = a_trap_map.get(canonical.lower())
            if v_orig:
                hits.append((c_orig, v_orig))
                break
    return hits


def _score_trap_overlap(
    c_traps: list[tuple[str, set[str]]],
    c_qcs: list[tuple[str, set[str]]],
    a_traps: list[tuple[str, set[str]]],
    a_qcs: list[tuple[str, set[str]]],
    *,
    is_prg: bool,
    vault_aliases: dict[str, str] | None = None,
) -> tuple[float, list[str], list[str], list[str]]:
    """Score trap-tag/description (and PRG QC) overlap between a card and an archetype."""
    c_trap_map = {tag.lower(): tag for tag, _ in c_traps if tag}
    a_trap_map = {tag.lower(): tag for tag, _ in a_traps if tag}
    a_trap_set = set(a_trap_map)
    shared_exact_traps = sorted(c_trap_map[k] for k in (set(c_trap_map) & a_trap_set))

    c_qc_map = {qid.lower(): qid for qid, _ in c_qcs if qid} if is_prg else {}
    a_qc_set = {qid.lower() for qid, _ in a_qcs if qid} if is_prg else set()
    shared_exact_qcs = sorted(c_qc_map[k] for k in (set(c_qc_map) & a_qc_set))

    if shared_exact_traps or shared_exact_qcs:
        trap_ratio = len(shared_exact_traps) / max(len(c_trap_map), 1)
        qc_ratio = len(shared_exact_qcs) / max(len(c_qc_map), 1) if is_prg else 0.0
        base = 0.85 if shared_exact_traps else 0.80
        return (base + 0.15 * max(trap_ratio, qc_ratio), shared_exact_traps, shared_exact_qcs, [])

    if is_prg:
        alias_hits = _prg_trap_alias_hits(c_trap_map, a_trap_map, vault_aliases=vault_aliases)
        if alias_hits:
            alias_ratio = len(alias_hits) / max(len(c_trap_map), 1)
            matched_vault_tags = sorted({v_tag for _, v_tag in alias_hits})
            alias_labels = [f"{c_tag}->{v_tag}" for c_tag, v_tag in alias_hits]
            return (0.78 + 0.12 * alias_ratio, matched_vault_tags, [], alias_labels)

    best_fuzzy = 0.0
    fuzzy_labels: list[str] = []

    def _consider(
        src_tag: str,
        src_toks: set[str],
        src_desc: set[str],
        dst_tag: str,
        dst_toks: set[str],
        dst_desc: set[str],
        scale: float,
    ) -> None:
        nonlocal best_fuzzy
        tag_sim = _dice_similarity(src_toks, dst_toks)
        if tag_sim >= 0.45 or len(src_toks & dst_toks) >= 2:
            cand = scale * tag_sim
            if cand > best_fuzzy:
                best_fuzzy = cand
                fuzzy_labels[:] = [f"{src_tag}~{dst_tag}" if src_tag and dst_tag else (src_tag or dst_tag)]
        desc_shared = len(src_desc & dst_desc)
        desc_sim = _dice_similarity(src_desc, dst_desc) if desc_shared >= 2 else 0.0
        if desc_sim >= 0.30:
            cand = scale * 0.85 * desc_sim
            if cand > best_fuzzy:
                best_fuzzy = cand
                fuzzy_labels[:] = [f"{src_tag}~{dst_tag}" if src_tag and dst_tag else (src_tag or dst_tag)]

    c_trap_toks = [(tag, _match_tag_tokens(tag), desc) for tag, desc in c_traps]
    a_trap_toks = [(tag, _match_tag_tokens(tag), desc) for tag, desc in a_traps]
    for c_tag, c_tt, c_desc in c_trap_toks:
        for a_tag, a_tt, a_desc in a_trap_toks:
            _consider(c_tag, c_tt, c_desc, a_tag, a_tt, a_desc, 1.0)

    if is_prg:
        c_qc_toks = [(qid, _match_tag_tokens(qid), desc) for qid, desc in c_qcs]
        a_qc_toks = [(qid, _match_tag_tokens(qid), desc) for qid, desc in a_qcs]
        for c_tag, c_tt, c_desc in c_trap_toks:
            for a_qid, a_qt, a_desc in a_qc_toks:
                _consider(c_tag, c_tt, c_desc, a_qid, a_qt, a_desc, 0.85)
        for c_qid, c_qt, c_desc in c_qc_toks:
            for a_tag, a_tt, a_desc in a_trap_toks:
                _consider(c_qid, c_qt, c_desc, a_tag, a_tt, a_desc, 0.85)

    return (min(0.75, best_fuzzy), [], [], fuzzy_labels)


def _score_skill_overlap(
    card_tokens: set[str],
    arch_tokens: set[str],
    idf: dict[str, float],
    default_idf: float,
) -> tuple[float, list[str]]:
    """Compute IDF-weighted skill/operation similarity and return top shared tokens."""
    shared = card_tokens & arch_tokens
    if not shared or not card_tokens or not arch_tokens:
        return (0.0, [])
    num = sum(idf.get(tok, default_idf) ** 2 for tok in shared)
    sq_card = sum(idf.get(tok, default_idf) ** 2 for tok in card_tokens)
    sq_arch = sum(idf.get(tok, default_idf) ** 2 for tok in arch_tokens)
    cosine = num / math.sqrt(sq_card * sq_arch) if (sq_card and sq_arch) else 0.0
    overlap = num / min(sq_card, sq_arch) if min(sq_card, sq_arch) else 0.0
    score = 0.6 * cosine + 0.4 * overlap
    ranked_terms = sorted(shared, key=lambda tok: (-idf.get(tok, default_idf), tok))
    return (score, ranked_terms)


def _card_effective_unit(card: dict[str, Any], report_unit_code: str) -> str:
    later = str(card.get("laterUnit") or "").strip()
    if later == report_unit_code:
        return report_unit_code
    units = card.get("units")
    if isinstance(units, list) and any(isinstance(u, str) and u.strip() == report_unit_code for u in units):
        return report_unit_code
    return str(card.get("unitCode") or report_unit_code).strip()


def _compatibility_score(
    card: dict[str, Any],
    arch: dict[str, Any],
    report_unit_code: str,
    *,
    is_prg: bool,
) -> tuple[float, str]:
    """Score unitCode, level (and PRG archetypeKind) compatibility in ``[0.0, 1.0]``."""
    card_unit = _card_effective_unit(card, report_unit_code)
    arch_unit = str(arch.get("unitCode") or arch.get("_vaultFile") or report_unit_code).strip()
    if card_unit == arch_unit:
        unit_compat = 1.0
        unit_note = "unit match"
    elif arch_unit.startswith(card_unit + "-") or card_unit.startswith(arch_unit + "-"):
        unit_compat = 0.9
        unit_note = "chapter-unit match"
    else:
        unit_compat = 0.0
        unit_note = "unit mismatch"

    c_lvl = card.get("level")
    a_lvl = arch.get("level")
    if isinstance(c_lvl, int) and isinstance(a_lvl, int):
        diff = abs(c_lvl - a_lvl)
        level_compat = 1.0 if diff == 0 else (0.75 if diff == 1 else (0.45 if diff == 2 else 0.2))
        level_note = f"L{c_lvl}~L{a_lvl}"
    else:
        level_compat = 0.5
        level_note = "level n/a"

    if is_prg:
        c_kind = _normalize_prg_archetype_kind(card.get("archetypeKind"))
        a_kind = _normalize_prg_archetype_kind(arch.get("archetype") or arch.get("archetypeKind"))
        if c_kind and a_kind and c_kind == a_kind:
            kind_compat = 1.0
            kind_note = f"{c_kind} kind"
        else:
            kind_compat = 0.5
            kind_note = "cross-kind"
        score = 0.45 * unit_compat + 0.35 * level_compat + 0.20 * kind_compat
        return (score, f"{unit_note}, {level_note}, {kind_note}")

    score = 0.55 * unit_compat + 0.45 * level_compat
    return (score, f"{unit_note}, {level_note}")


def _card_skill_tokens(card: dict[str, Any]) -> set[str]:
    primary = _match_tokens(" ".join(_flatten_text(card.get(k)) for k in ("core", "skill", "relation", "concept")))
    if primary:
        return primary
    return _match_tokens(_flatten_text(card.get("difficultyDriver")))


def _archetype_skill_tokens(arch: dict[str, Any]) -> set[str]:
    return _match_tokens(
        " ".join(
            _flatten_text(arch.get(k))
            for k in ("name", "coreConcept", "governingRelation", "governingInvariant", "competencies")
        )
    )


def _format_match_reason(
    *,
    shared_exact_traps: list[str],
    shared_exact_qcs: list[str],
    fuzzy_traps: list[str],
    matched_terms: list[str],
    skill_score: float,
    compat_note: str,
) -> str:
    parts: list[str] = []
    if fuzzy_traps and any("->" in item for item in fuzzy_traps):
        parts.append(f"alias-trap:{','.join(fuzzy_traps[:2])}")
    elif shared_exact_traps:
        parts.append(f"trap:{','.join(shared_exact_traps)}")
    elif fuzzy_traps:
        parts.append(f"fuzzy-trap:{','.join(fuzzy_traps[:2])}")
    if shared_exact_qcs:
        parts.append(f"qc:{','.join(shared_exact_qcs)}")
    if matched_terms and skill_score > 0:
        parts.append(f"skill:{','.join(matched_terms[:4])}")
    parts.append(compat_note)
    return "; ".join(parts)


def _score_card_with_features(
    card: dict[str, Any],
    arch: dict[str, Any],
    *,
    c_traps: list[tuple[str, set[str]]],
    c_qcs: list[tuple[str, set[str]]],
    c_skill: set[str],
    a_traps: list[tuple[str, set[str]]],
    a_qcs: list[tuple[str, set[str]]],
    a_skill: set[str],
    unit_code: str,
    is_prg: bool,
    idf: dict[str, float],
    default_idf: float,
    a_aliases: dict[str, str] | None = None,
) -> dict[str, Any]:
    trap_score, shared_traps, shared_qcs, fuzzy_traps = _score_trap_overlap(
        c_traps,
        c_qcs,
        a_traps,
        a_qcs,
        is_prg=is_prg,
        vault_aliases=a_aliases,
    )
    skill_score, matched_terms = _score_skill_overlap(c_skill, a_skill, idf, default_idf)
    compat_score, compat_note = _compatibility_score(card, arch, unit_code, is_prg=is_prg)

    evidence = max(trap_score, skill_score)
    compat_gate = min(1.0, evidence / 0.25) if evidence > 0 else 0.0
    total_score = _TRAP_WEIGHT * trap_score + _SKILL_WEIGHT * skill_score + _COMPAT_WEIGHT * compat_score * compat_gate

    reason = _format_match_reason(
        shared_exact_traps=shared_traps,
        shared_exact_qcs=shared_qcs,
        fuzzy_traps=fuzzy_traps,
        matched_terms=matched_terms,
        skill_score=skill_score,
        compat_note=compat_note,
    )
    match: dict[str, Any] = {
        "archetypeKey": str(arch.get("archetypeKey") or ""),
        "score": round(total_score, 3),
        "reason": reason,
        "scoreBreakdown": {
            "trap": round(trap_score, 3),
            "skill": round(skill_score, 3),
            "compatibility": round(compat_score, 3),
        },
        "matchedTraps": shared_traps,
        "matchedTerms": matched_terms[:6],
    }
    if is_prg:
        match["matchedQualityChecks"] = shared_qcs
    return match


def score_card_against_archetype(
    card: dict[str, Any],
    arch: dict[str, Any],
    *,
    unit_code: str,
    is_prg: bool,
    idf: dict[str, float] | None = None,
    default_idf: float = 1.0,
) -> dict[str, Any]:
    """Score one core card against one vault archetype across traps, skill fields, and compatibility."""
    return _score_card_with_features(
        card,
        arch,
        c_traps=_card_trap_entries(card),
        c_qcs=_card_qc_entries(card) if is_prg else [],
        c_skill=_card_skill_tokens(card),
        a_traps=_archetype_trap_entries(arch),
        a_qcs=_archetype_qc_entries(arch) if is_prg else [],
        a_skill=_archetype_skill_tokens(arch),
        unit_code=unit_code,
        is_prg=is_prg,
        idf=idf or {},
        default_idf=default_idf,
        a_aliases=_archetype_trap_aliases(arch) if is_prg else None,
    )


def _match_cards_to_archetypes(
    unit_code: str,
    cards: list[dict[str, Any]],
    archetypes: list[dict[str, Any]],
    *,
    is_prg: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Assign each card to its best archetype (plus at most one high-confidence runner-up) or unmatched."""
    num_archs = len(archetypes)
    doc_freq: Counter[str] = Counter()
    arch_skill_cache: list[set[str]] = []
    arch_trap_cache: list[list[tuple[str, set[str]]]] = []
    arch_qc_cache: list[list[tuple[str, set[str]]]] = []
    arch_alias_cache: list[dict[str, str]] = []

    for arch in archetypes:
        sk = _archetype_skill_tokens(arch)
        arch_skill_cache.append(sk)
        for tok in sk:
            doc_freq[tok] += 1
        arch_trap_cache.append(_archetype_trap_entries(arch))
        arch_qc_cache.append(_archetype_qc_entries(arch) if is_prg else [])
        arch_alias_cache.append(_archetype_trap_aliases(arch) if is_prg else {})

    default_idf = math.log(num_archs + 1.0) if num_archs >= 3 else 1.0
    idf = {
        tok: (math.log((num_archs + 1.0) / (count + 0.5)) if num_archs >= 3 else 1.0) for tok, count in doc_freq.items()
    }

    match_threshold = PRG_MATCH_THRESHOLD if is_prg else MATCH_THRESHOLD
    matched_cards: list[dict[str, Any]] = []
    unmatched_cards: list[dict[str, Any]] = []

    for card in cards:
        c_traps = _card_trap_entries(card)
        c_qcs = _card_qc_entries(card) if is_prg else []
        c_skill = _card_skill_tokens(card)

        candidates = [
            _score_card_with_features(
                card,
                arch,
                c_traps=c_traps,
                c_qcs=c_qcs,
                c_skill=c_skill,
                a_traps=arch_trap_cache[idx],
                a_qcs=arch_qc_cache[idx],
                a_skill=arch_skill_cache[idx],
                unit_code=unit_code,
                is_prg=is_prg,
                idf=idf,
                default_idf=default_idf,
                a_aliases=arch_alias_cache[idx],
            )
            for idx, arch in enumerate(archetypes)
        ]

        candidates.sort(
            key=lambda m: (
                -m["score"],
                -m["scoreBreakdown"]["trap"],
                -m["scoreBreakdown"]["skill"],
                m["archetypeKey"],
            )
        )

        hits: list[dict[str, Any]] = []
        if candidates and candidates[0]["score"] >= match_threshold:
            hits.append(candidates[0])
            if len(candidates) > 1 and candidates[1]["score"] >= RUNNER_UP_THRESHOLD:
                hits.append(candidates[1])

        if is_prg:
            summary: dict[str, Any] = {
                "id": card["id"],
                "skill": card["skill"],
                "concept": card.get("concept", ""),
                "language": card.get("language", ""),
                "level": card["level"],
                "archetypeKind": card.get("archetypeKind", ""),
                "bugPattern": card.get("bugPattern", ""),
            }
        else:
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

    return matched_cards, unmatched_cards


def _build_prg_gap_report(
    unit_code: str,
    cpath: str,
    cards: list[dict[str, Any]],
    archetypes: list[dict[str, Any]],
) -> dict[str, Any]:
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

    all_vault_traps: set[str] = set()
    all_vault_traps_lower: set[str] = set()
    all_vault_aliases_lower: set[str] = set()
    all_vault_qcs: set[str] = set()
    all_vault_trap_tokens: list[set[str]] = []
    vault_levels: set[int] = set()

    for arch in archetypes:
        traps = _archetype_traps(arch)
        qcs = _archetype_quality_check_ids(arch)
        all_vault_traps.update(traps)
        all_vault_traps_lower.update(t.lower() for t in traps)
        all_vault_aliases_lower.update(_archetype_trap_aliases(arch).keys())
        all_vault_qcs.update(qcs)
        for t in arch.get("cognitiveTraps") or []:
            t_blob = _flatten_text(t)
            if t_blob:
                all_vault_trap_tokens.append(_fuzzy_skill_tokens(t_blob))
        if isinstance(arch.get("level"), int):
            vault_levels.add(arch["level"])

    def _trap_covered_by_vault(tag: str) -> bool:
        low = tag.lower()
        if tag in all_vault_traps or low in all_vault_traps_lower or low in all_vault_aliases_lower:
            return True
        return any(canon.lower() in all_vault_traps_lower for canon in PRG_TRAP_TAG_ALIASES.get(low, ()))

    matched_cards, unmatched_cards = _match_cards_to_archetypes(
        unit_code,
        current_cards,
        archetypes,
        is_prg=True,
    )

    # New trap tags not in any vault archetype's cognitiveTraps (including consolidated aliases)
    new_traps_map: dict[str, dict[str, Any]] = {}
    for card in current_cards:
        for t in card.get("traps") or []:
            tag = t["tag"]
            if _trap_covered_by_vault(tag):
                continue
            entry = new_traps_map.setdefault(tag, {"tag": tag, "descriptions": [], "cardIds": []})
            desc = t.get("description", "")
            if desc and desc not in entry["descriptions"]:
                entry["descriptions"].append(desc)
            if card["id"] not in entry["cardIds"]:
                entry["cardIds"].append(card["id"])

    # New bug patterns / smells not clearly covered by existing vault cognitiveTraps
    new_bug_patterns_map: dict[str, dict[str, Any]] = {}
    for card in current_cards:
        bp = str(card.get("bugPattern") or "").strip()
        if not bp:
            continue
        bp_toks = _fuzzy_skill_tokens(bp)
        covered_by_trap = False
        if bp_toks:
            for vt in all_vault_trap_tokens:
                union = bp_toks | vt
                if union and (len(bp_toks & vt) / len(union)) >= 0.45:
                    covered_by_trap = True
                    break
        card_has_new_trap = any(
            isinstance(t, dict) and t.get("tag") and not _trap_covered_by_vault(t["tag"])
            for t in card.get("traps") or []
        )
        if not covered_by_trap or card_has_new_trap:
            norm_key = _norm_skill_str(bp)
            grp = new_bug_patterns_map.setdefault(
                norm_key,
                {
                    "bugPattern": bp,
                    "smells": [],
                    "concept": card.get("concept", ""),
                    "archetypeKind": card.get("archetypeKind", ""),
                    "cardIds": [],
                },
            )
            smell = str(card.get("smell") or "").strip()
            if smell and smell not in grp["smells"]:
                grp["smells"].append(smell)
            if card["id"] not in grp["cardIds"]:
                grp["cardIds"].append(card["id"])

    # New QC-* qualityCheck ideas not yet in the vault
    new_qcs_map: dict[str, dict[str, Any]] = {}
    for card in current_cards:
        for qc in card.get("qualityCheckIdeas") or []:
            if not isinstance(qc, dict) or not qc.get("id"):
                continue
            qid = str(qc["id"]).strip()
            if qid in all_vault_qcs:
                continue
            entry = new_qcs_map.setdefault(
                qid,
                {
                    "id": qid,
                    "check": str(qc.get("check") or "").strip(),
                    "severity": str(qc.get("severity") or "should"),
                    "cardIds": [],
                },
            )
            if card["id"] not in entry["cardIds"]:
                entry["cardIds"].append(card["id"])

    # Archetype kinds & levels gap
    card_levels = Counter(int(c["level"]) for c in current_cards)
    card_kinds = Counter(str(c.get("archetypeKind") or "") for c in current_cards if c.get("archetypeKind"))
    vault_kinds = _infer_vault_prg_kinds(archetypes)
    missing_levels_in_vault = sorted(lvl for lvl in card_levels if lvl not in vault_levels)
    missing_kinds_in_vault = sorted(k for k in card_kinds if k not in vault_kinds)
    all_missing_kinds = [k for k in PRG_ARCHETYPE_KINDS if k not in vault_kinds]

    languages = Counter(str(c.get("language") or "") for c in current_cards if c.get("language"))
    concepts = Counter(str(c.get("concept") or "") for c in current_cards if c.get("concept"))

    later_groups = {
        target: [
            {
                "id": c["id"],
                "level": c["level"],
                "archetypeKind": c.get("archetypeKind", ""),
                "skill": c["skill"],
                "sourceRef": c["sourceRef"],
            }
            for c in items
        ]
        for target, items in sorted(later_by_unit.items())
    }

    return {
        "unitCode": unit_code,
        "track": "prg",
        "cardsPath": cpath,
        "cardsFileExists": os.path.isfile(cpath),
        "totalCards": len(cards),
        "currentCardsCount": len(current_cards),
        "carriedCardsCount": carried_count,
        "laterCardsCount": sum(len(v) for v in later_groups.values()),
        "vaultArchetypeCount": len(archetypes),
        "vaultQualityCheckIds": sorted(all_vault_qcs),
        "matchedCards": matched_cards,
        "unmatchedCards": unmatched_cards,
        "newTraps": sorted(new_traps_map.values(), key=lambda x: x["tag"]),
        "newBugPatterns": sorted(new_bug_patterns_map.values(), key=lambda x: x["bugPattern"].lower()),
        "newQualityChecks": sorted(new_qcs_map.values(), key=lambda x: x["id"]),
        "levels": {
            "vaultBaseLevels": sorted(vault_levels),
            "cardLevelCounts": {str(k): v for k, v in sorted(card_levels.items())},
            "cardLevelsMissingInVault": missing_levels_in_vault,
        },
        "archetypeKinds": {
            "vaultKinds": sorted(vault_kinds),
            "cardKindCounts": dict(sorted(card_kinds.items())),
            "cardKindsMissingInVault": missing_kinds_in_vault,
            "allVaultMissingKinds": all_missing_kinds,
        },
        "languages": dict(sorted(languages.items())),
        "concepts": dict(sorted(concepts.items())),
        "laterUnitCards": later_groups,
    }


def build_gap_report(
    unit_code: str,
    *,
    sources_dir: str | None = None,
    vault_dir: str | None = None,
    eligible_units: Iterable[str] | None = None,
    data_root: str | None = None,
    progress_dir: str | None = None,
    valid_unit_codes: Iterable[str] | None = None,
    registry_path: str | None = None,
) -> dict[str, Any]:
    """Compute a read-only gap report comparing ``unit_code``'s core cards and reasoning vault."""
    cpath = cores_path(unit_code, sources_dir=sources_dir)
    cards = load_core_cards(
        unit_code,
        sources_dir=sources_dir,
        validate=True,
        valid_unit_codes=valid_unit_codes,
        registry_path=registry_path,
    )

    if is_prg_unit(unit_code):
        archetypes = load_code_scope_archetypes(unit_code, vault_dir=vault_dir)
        return _build_prg_gap_report(unit_code, cpath, cards, archetypes)

    archetypes = load_math_scope_archetypes(unit_code, vault_dir=vault_dir)

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

    all_vault_traps: set[str] = set()
    vault_levels: set[int] = set()

    for arch in archetypes:
        all_vault_traps.update(_archetype_traps(arch))
        if isinstance(arch.get("level"), int):
            vault_levels.add(arch["level"])

    matched_cards, unmatched_cards = _match_cards_to_archetypes(
        unit_code,
        current_cards,
        archetypes,
        is_prg=False,
    )

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
        "track": "math",
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


def _format_match_target(match: dict[str, Any]) -> str:
    score = match.get("score")
    score_prefix = f"{score:.2f}; " if isinstance(score, (int, float)) else ""
    reason = match.get("reason")
    if reason:
        return f"{match['archetypeKey']} ({score_prefix}{reason})"
    reasons = []
    if match.get("matchedTraps"):
        reasons.append(f"trap:{','.join(match['matchedTraps'])}")
    if match.get("matchedQualityChecks"):
        reasons.append(f"qc:{','.join(match['matchedQualityChecks'])}")
    if not reasons and match.get("matchedTerms"):
        reasons.append(f"skill:{','.join(match['matchedTerms'])}")
    return f"{match['archetypeKey']} ({score_prefix}{'; '.join(reasons)})"


def _format_prg_gap_report(report: dict[str, Any], header: list[str]) -> str:
    lines = list(header)
    lines.append(f"Vault qualityChecks in scope: {len(report.get('vaultQualityCheckIds') or [])}")

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
        parts = [_format_match_target(m) for m in item["matches"]]
        carried_tag = f" [carried from {item['carriedFrom']}]" if item.get("carriedFrom") else ""
        lines.append(
            f"  - [{item['id']}] L{item['level']} {item['archetypeKind']} [{item['language']}] — "
            f"{item['skill']} ({item['concept']}){carried_tag} -> {', '.join(parts)}"
        )

    lines.append("")
    lines.append(f"Unmatched cards — candidate new archetypes ({len(unmatched)}):")
    if not unmatched:
        lines.append("  (none)")
    for item in unmatched:
        carried_tag = f" [carried from {item['carriedFrom']}]" if item.get("carriedFrom") else ""
        lines.append(
            f"  - [{item['id']}] L{item['level']} {item['archetypeKind']} [{item['language']}] — "
            f"{item['skill']} ({item['concept']}){carried_tag}"
        )

    lines.append("")
    new_traps = report["newTraps"]
    lines.append(f"New trap tags not in any archetype ({len(new_traps)}):")
    if not new_traps:
        lines.append("  (none)")
    for t in new_traps:
        desc = t["descriptions"][0] if t["descriptions"] else ""
        lines.append(f"  - {t['tag']}: {desc} (cards: {', '.join(t['cardIds'])})")

    lines.append("")
    new_bps = report.get("newBugPatterns") or []
    lines.append(f"New bug patterns / smells ({len(new_bps)}):")
    if not new_bps:
        lines.append("  (none)")
    for bp in new_bps:
        smell_note = f" [smell: {', '.join(bp['smells'])}]" if bp.get("smells") else ""
        lines.append(
            f"  - [{bp['archetypeKind']}] {bp['bugPattern']}{smell_note} "
            f"(concept: {bp['concept']}; cards: {', '.join(bp['cardIds'])})"
        )

    lines.append("")
    new_qcs = report.get("newQualityChecks") or []
    lines.append(f"New qualityCheck ideas (QC-*) not in vault ({len(new_qcs)}):")
    if not new_qcs:
        lines.append("  (none)")
    for qc in new_qcs:
        lines.append(f"  - {qc['id']} ({qc['severity']}): {qc['check']} (cards: {', '.join(qc['cardIds'])})")

    lines.append("")
    lv = report["levels"]
    ak = report["archetypeKinds"]
    lines.append("Levels & PRG archetype kinds:")
    lines.append(f"  Vault base levels: {lv['vaultBaseLevels'] or ['none']}")
    lines.append("  Card levels: " + (", ".join(f"L{k}x{v}" for k, v in lv["cardLevelCounts"].items()) or "none"))
    lines.append(
        "  Card levels missing from vault: " + (", ".join(f"L{x}" for x in lv["cardLevelsMissingInVault"]) or "none")
    )
    lines.append("  Vault archetype kinds: " + (", ".join(ak["vaultKinds"]) or "none"))
    lines.append(
        "  Card archetype kinds: " + (", ".join(f"{k}x{v}" for k, v in ak["cardKindCounts"].items()) or "none")
    )
    lines.append("  Card archetype kinds missing from vault: " + (", ".join(ak["cardKindsMissingInVault"]) or "none"))
    lines.append("  All PRG archetype kinds missing from vault: " + (", ".join(ak["allVaultMissingKinds"]) or "none"))

    if report.get("languages") or report.get("concepts"):
        lines.append("")
        langs = ", ".join(f"{k}x{v}" for k, v in (report.get("languages") or {}).items())
        concepts = ", ".join(f"{k}x{v}" for k, v in (report.get("concepts") or {}).items())
        lines.append(f"Languages: {langs or 'none'}")
        lines.append(f"Concepts: {concepts or 'none'}")

    lines.append("")
    later = report["laterUnitCards"]
    lines.append(f"Deferred laterUnit cards ({report['laterCardsCount']}):")
    if not later:
        lines.append("  (none)")
    for target_unit, items in later.items():
        lines.append(f"  {target_unit} ({len(items)} card(s)):")
        for c in items:
            lines.append(f"    - [{c['id']}] L{c['level']} {c['archetypeKind']} — {c['skill']}")

    return "\n".join(lines)


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

    if report.get("track") == "prg":
        return _format_prg_gap_report(report, lines)

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
        targets = ", ".join(_format_match_target(m) for m in item["matches"])
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
        description="Read-only gap report comparing a unit's source core cards against its reasoning vault (Math or PRG).",
    )
    parser.add_argument("unit", help="Target unit code (e.g. MTH-T02-C01-U01 or PRG-T01-C01-U02).")
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
        help="Override reasoning vault directory (default: math_engine/reasoning_vault or code_engine/reasoning_vault).",
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
