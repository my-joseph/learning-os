# -*- coding: utf-8 -*-
"""Originality gate: ensure generated math prompts and choice options do not copy source material.

Compares every generated prompt (and its choice options) against the cached source text of a
unit's located pages under ``sources/_index/``:
1. 8-word shingle overlap -> reject.
2. Prompt number multiset equals any source item's number multiset (with >= 2 numbers) -> reject.
3. Normalised ``difflib.SequenceMatcher`` similarity >= 0.6 against any source sentence window -> reject.

CLI:
    python -m math_engine.source_cores.originality <draft.json|variants.json> --unit <UNIT>
"""

from __future__ import annotations

import argparse
import difflib
import glob
import json
import os
import re
import sys
from collections import Counter
from typing import Any

from math_engine.source_cores import (
    extract_digit_runs,
    get_unit_terms,
    index_dir,
    load_core_cards,
    resolve_sources_dir,
)

DEFAULT_SHINGLE_SIZE = 8
DEFAULT_SIMILARITY_THRESHOLD = 0.6
MIN_WINDOW_CHARS = 15
# Two small numbers (e.g. {1, 11}) collide with unrelated pages everywhere; a set of
# three or more numbers is distinctive enough to flag a reused item.
MIN_MULTISET_NUMBERS = 3
# Short task phrasings ("Simplify X.") are inherently similar to textbook wording;
# copying of short prompts is still caught by the shingle and number-set checks.
MIN_SIMILARITY_CHARS = 40


def _family_relevant(rel_path: str, unit_code: str) -> bool:
    """Compare MTH units only with math-relevant families (skip CS/physics books that merely mention a term)."""
    rel = rel_path.replace("\\", "/")
    if unit_code.startswith("MTH") and rel.startswith("openstax/cs-physics/"):
        return False
    return True


_LATEX_STRIP_COMMANDS_RE = re.compile(
    r"\\(?:left|right|displaystyle|textstyle|quad|qquad|text|mathrm|mathbf|mathit|operatorname)\b"
)
_ITEM_PREFIX_RE = re.compile(
    r"^\s*(?:(?:Q|Question|Problem|Example|Ex)\s*\.?\s*)?\d+\s*[\.\):]\s+|^\s*ข้อ\s*\d+\s*[\.\):]?\s*",
    re.IGNORECASE,
)
_SENTENCE_SPLIT_RE = re.compile(r"(?:[.?!;]+(?:\s+|$)|\n+)")
_ITEM_BOUNDARY_RE = re.compile(
    r"(?m)(?=^\s*(?:(?:Q|Question|Problem|Example|Ex)\s*\.?\s*)?\d+\s*[\.\):]\s+|^\s*ข้อ\s*\d+\s*[\.\):]?\s*)",
    re.IGNORECASE,
)
_WORD_TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?|[\u0e00-\u0e7f]+")


def normalize_text(text: str) -> str:
    """Normalize English/Thai/LaTeX math text for shingle and similarity comparison."""
    s = str(text or "")
    s = _LATEX_STRIP_COMMANDS_RE.sub(" ", s)
    for macro, repl in (
        (r"\times", " * "),
        (r"\cdot", " * "),
        (r"\div", " / "),
        (r"\frac", " "),
        (r"\sqrt", " sqrt "),
        (r"\pm", " pm "),
    ):
        s = s.replace(macro, repl)
    s = re.sub(r"\\[A-Za-z]+", " ", s)
    s = s.replace("$", " ").replace("{", " ").replace("}", " ").replace("\\", " ")
    s = s.lower()
    # Keep ASCII alphanumerics, Thai characters, decimal dots inside numbers, and spaces.
    s = re.sub(r"(?<!\d)\.(?!\d)", " ", s)
    s = re.sub(r"[^a-z0-9.\u0e00-\u0e7f\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def word_tokens(text: str) -> list[str]:
    """Tokenize normalized text into word/number tokens."""
    return _WORD_TOKEN_RE.findall(normalize_text(text))


def word_shingles(text: str, size: int = DEFAULT_SHINGLE_SIZE) -> set[tuple[str, ...]]:
    """Return all contiguous ``size``-word shingles from ``text``."""
    toks = word_tokens(text)
    if len(toks) < size:
        return set()
    return {tuple(toks[i : i + size]) for i in range(len(toks) - size + 1)}


def number_multiset(text: str) -> Counter[str]:
    """Return the normalized multiset of numeric literals in ``text``."""
    cleaned = _ITEM_PREFIX_RE.sub("", str(text or ""))
    return Counter(extract_digit_runs(cleaned))


def _extract_source_items(page_text: str) -> list[str]:
    """Split a source page into candidate item chunks (blocks, lines, and sentences)."""
    items: list[str] = []
    seen: set[str] = set()

    def _add(chunk: str) -> None:
        cleaned = _ITEM_PREFIX_RE.sub("", chunk.strip()).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            items.append(cleaned)

    for block in re.split(r"\n\s*\n+", page_text or ""):
        for sub in _ITEM_BOUNDARY_RE.split(block):
            _add(sub)
            for line in sub.splitlines():
                _add(line)
            for sent in _SENTENCE_SPLIT_RE.split(sub):
                _add(sent)
    return items


def _sentence_windows(page_text: str, max_sentences: int = 3) -> list[str]:
    """Build normalized sliding windows of 1..``max_sentences`` consecutive sentences."""
    raw_sents = [_ITEM_PREFIX_RE.sub("", s.strip()).strip() for s in _SENTENCE_SPLIT_RE.split(page_text or "")]
    sents = [normalize_text(s) for s in raw_sents if s]
    sents = [s for s in sents if s]
    windows: list[str] = []
    seen: set[str] = set()
    for i in range(len(sents)):
        for span in range(1, max_sentences + 1):
            if i + span > len(sents):
                break
            win = " ".join(sents[i : i + span])
            if len(win) >= MIN_WINDOW_CHARS and win not in seen:
                seen.add(win)
                windows.append(win)
    return windows


def _load_pdf_cache_by_relpath(idx_dir: str) -> dict[str, dict[str, Any]]:
    by_rel: dict[str, dict[str, Any]] = {}
    if not os.path.isdir(idx_dir):
        return by_rel
    for path in sorted(glob.glob(os.path.join(idx_dir, "pdf_*.json"))):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        rel = doc.get("relPath")
        if isinstance(rel, str) and rel:
            by_rel[rel] = doc
    return by_rel


def load_located_source_pages(
    unit_code: str,
    sources_dir: str | None = None,
) -> list[dict[str, Any]]:
    """Load cached source text for ``unit_code``'s located pages under ``sources/_index/``.

    Resolution order:
    1. Pages listed in ``sources/_index/located_<unit_code>.json`` (written by ``source_find``).
    2. Any additional pages referenced by ``sources/_cores/<unit_code>.jsonl`` present in cache.
    3. Fallback if neither exists: cached pages in ``sources/_index/pdf_*.json`` matching the
       unit's seeded terms from ``unit_terms.json``.
    """
    idx_dir = index_dir(sources_dir=sources_dir)
    if not os.path.isdir(idx_dir):
        return []

    by_rel = _load_pdf_cache_by_relpath(idx_dir)
    pages_out: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, int]] = set()

    def _add_page(rel: str, page_num: int, text: str) -> None:
        key = (rel, page_num)
        if key in seen_keys or not text.strip():
            return
        seen_keys.add(key)
        pages_out.append({"relPath": rel, "page": page_num, "text": text})

    def _lookup_page_text(cache_doc: dict[str, Any], page_num: int) -> str:
        for p in cache_doc.get("pages") or []:
            if p.get("page") == page_num:
                return str(p.get("text") or "")
        return ""

    # 1. Located manifest from source_find
    located_path = os.path.join(idx_dir, f"located_{unit_code}.json")
    if os.path.isfile(located_path):
        try:
            with open(located_path, "r", encoding="utf-8") as fh:
                located = json.load(fh)
        except (OSError, ValueError):
            located = {}
        for match in located.get("matches") or []:
            rel = str(match.get("relPath") or "")
            if not _family_relevant(rel, unit_code):
                continue
            cache_doc = None
            cache_file = match.get("cacheFile")
            if isinstance(cache_file, str):
                cpath = os.path.join(idx_dir, cache_file)
                if os.path.isfile(cpath):
                    try:
                        with open(cpath, "r", encoding="utf-8") as fh:
                            cache_doc = json.load(fh)
                    except (OSError, ValueError):
                        cache_doc = None
            if cache_doc is None:
                cache_doc = by_rel.get(rel)
            if not cache_doc:
                continue
            for p_info in match.get("pages") or []:
                pnum = p_info.get("page") if isinstance(p_info, dict) else p_info
                if isinstance(pnum, int):
                    _add_page(rel, pnum, _lookup_page_text(cache_doc, pnum))

    # 2. Core-card referenced pages (if cached)
    try:
        cards = load_core_cards(unit_code, sources_dir=sources_dir, validate=False)
    except Exception:  # noqa: BLE001
        cards = []
    for card in cards:
        ref = card.get("sourceRef") or {}
        ref_file = str(ref.get("file") or "")
        ref_page = ref.get("page")
        if not ref_file or not isinstance(ref_page, int):
            continue
        for rel, cache_doc in by_rel.items():
            if rel == ref_file or rel.endswith("/" + ref_file) or os.path.basename(rel) == ref_file:
                _add_page(rel, ref_page, _lookup_page_text(cache_doc, ref_page))

    # 3. Fallback: scan cached PDFs with seeded unit terms
    if not pages_out and by_rel:
        terms = [t.lower() for t in get_unit_terms(unit_code)]
        if terms:
            for rel, cache_doc in by_rel.items():
                for p in cache_doc.get("pages") or []:
                    text = str(p.get("text") or "")
                    low = text.lower()
                    if text.strip() and any(t in low for t in terms):
                        pnum = p.get("page")
                        if isinstance(pnum, int):
                            _add_page(rel, pnum, text)

    return pages_out


def _option_texts(prob: dict[str, Any]) -> list[str]:
    spec = prob.get("answerSpec") or {}
    out: list[str] = []
    for opt in spec.get("options") or []:
        if isinstance(opt, dict):
            lbl = opt.get("label") or opt.get("text") or ""
            if isinstance(lbl, str) and lbl.strip():
                out.append(lbl.strip())
    return out


class _PreparedSourceIndex:
    """Precomputed shingles, item number multisets, and sentence windows for fast checking."""

    def __init__(self, source_pages: list[dict[str, Any]], shingle_size: int = DEFAULT_SHINGLE_SIZE) -> None:
        self.shingle_size = shingle_size
        self.shingles: dict[tuple[str, ...], str] = {}
        self.item_multisets: list[tuple[Counter[str], str]] = []
        self.windows: list[tuple[str, str]] = []

        for page in source_pages:
            rel = str(page.get("relPath") or "source")
            pnum = page.get("page", "?")
            loc = f"{rel} p.{pnum}"
            text = str(page.get("text") or "")
            if not text.strip():
                continue

            for sh in word_shingles(text, size=shingle_size):
                self.shingles.setdefault(sh, loc)

            seen_ms: set[tuple[tuple[str, int], ...]] = set()
            for item in _extract_source_items(text):
                ms = number_multiset(item)
                if sum(ms.values()) >= MIN_MULTISET_NUMBERS:
                    key = tuple(sorted(ms.items()))
                    if key not in seen_ms:
                        seen_ms.add(key)
                        self.item_multisets.append((ms, loc))

            for win in _sentence_windows(text):
                self.windows.append((win, loc))


def check_problem_originality(
    prob: dict[str, Any],
    source_pages: list[dict[str, Any]],
    *,
    shingle_size: int = DEFAULT_SHINGLE_SIZE,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    _prepared: _PreparedSourceIndex | None = None,
) -> list[str]:
    """Check one problem's prompt and choice options against ``source_pages``."""
    if not source_pages:
        return []
    prepared = _prepared or _PreparedSourceIndex(source_pages, shingle_size=shingle_size)
    pid = str(prob.get("variantId") or prob.get("id") or "?")
    prompt = str(prob.get("prompt") or "")
    options = _option_texts(prob)
    errors: list[str] = []

    # Candidate texts for shingle & similarity checks: prompt, combined prompt+options, and long options.
    shingle_targets: list[tuple[str, str]] = [("prompt", prompt)]
    if options:
        shingle_targets.append(("prompt+options", prompt + " " + " ".join(options)))
        for idx, opt in enumerate(options, 1):
            shingle_targets.append((f"option {idx}", opt))

    # 1. 8-word shingle overlap
    shingle_hit = False
    for label, text in shingle_targets:
        if shingle_hit:
            break
        for sh in word_shingles(text, size=shingle_size):
            if sh in prepared.shingles:
                loc = prepared.shingles[sh]
                errors.append(
                    f"[{pid}] Originality gate failed ({label}): {shingle_size}-word shingle overlap "
                    f'"{" ".join(sh)}" with {loc}.'
                )
                shingle_hit = True
                break

    # 2. Prompt number multiset equality against any source item's number set
    p_nums = number_multiset(prompt)
    if sum(p_nums.values()) >= MIN_MULTISET_NUMBERS:
        for src_ms, loc in prepared.item_multisets:
            if p_nums == src_ms:
                nums_display = sorted(p_nums.elements())
                errors.append(
                    f"[{pid}] Originality gate failed (prompt): number multiset {nums_display} "
                    f"matches a source item in {loc}; synthesize fresh numbers."
                )
                break

    # 3. Normalised similarity >= threshold to any source sentence window
    sim_targets: list[tuple[str, str]] = [("prompt", normalize_text(prompt))]
    for idx, opt in enumerate(options, 1):
        norm_opt = normalize_text(opt)
        if len(norm_opt) >= MIN_WINDOW_CHARS:
            sim_targets.append((f"option {idx}", norm_opt))

    for label, norm_cand in sim_targets:
        if len(norm_cand) < MIN_WINDOW_CHARS:
            continue
        if len(norm_cand) < MIN_SIMILARITY_CHARS:
            # Short prompts: only a verbatim copy counts (fuzzy similarity is meaningless here).
            hit = next((loc for win, loc in prepared.windows if norm_cand in win), "")
            if hit:
                errors.append(
                    f"[{pid}] Originality gate failed ({label}): verbatim copy of a source sentence in {hit}."
                )
            continue
        best_ratio = 0.0
        best_loc = ""
        for win, loc in prepared.windows:
            sm = difflib.SequenceMatcher(None, norm_cand, win)
            if sm.quick_ratio() < similarity_threshold:
                continue
            ratio = sm.ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_loc = loc
        if best_ratio >= similarity_threshold:
            errors.append(
                f"[{pid}] Originality gate failed ({label}): normalised similarity "
                f"{best_ratio:.2f} (>= {similarity_threshold:.2f}) to {best_loc}."
            )

    return errors


def check_document_originality(
    doc: dict[str, Any],
    unit_code: str | None = None,
    sources_dir: str | None = None,
    *,
    source_pages: list[dict[str, Any]] | None = None,
    shingle_size: int = DEFAULT_SHINGLE_SIZE,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> tuple[list[str], str | None]:
    """Check every problem/variant in a drill draft or variant bank document.

    Returns ``(errors, skip_notice)``. When the sources directory does not exist or has no
    cached pages for the unit, returns ``([], notice)`` so CI environments without ``sources/``
    skip cleanly with a notice.
    """
    resolved_unit = unit_code or doc.get("unitCode")
    if not isinstance(resolved_unit, str) or not resolved_unit.strip():
        return (["Document must specify 'unitCode' (or pass --unit)."], None)

    if source_pages is None:
        sdir = resolve_sources_dir(sources_dir=sources_dir)
        if not os.path.isdir(sdir):
            return ([], f"Originality gate skipped: sources directory not found ({sdir}).")
        source_pages = load_located_source_pages(resolved_unit, sources_dir=sdir)
        if resolved_unit == "MTH-BRIDGE" or not source_pages:
            raw_items = doc.get("problems") or doc.get("variants") or []
            component_units: list[str] = []
            seen_u: set[str] = set()
            for prob in raw_items:
                if not isinstance(prob, dict):
                    continue
                for candidate in [*(prob.get("unitCodes") or []), *(prob.get("references") or [])]:
                    if (
                        isinstance(candidate, str)
                        and "-U" in candidate
                        and candidate not in seen_u
                        and candidate != resolved_unit
                    ):
                        seen_u.add(candidate)
                        component_units.append(candidate)
            if component_units:
                seen_page_keys = {(p.get("relPath"), p.get("page")) for p in source_pages}
                for cu in component_units:
                    for page in load_located_source_pages(cu, sources_dir=sdir):
                        pkey = (page.get("relPath"), page.get("page"))
                        if pkey not in seen_page_keys:
                            seen_page_keys.add(pkey)
                            source_pages.append(page)
        if not source_pages:
            return (
                [],
                f"Originality gate skipped: no cached located source pages for {resolved_unit} under {index_dir(sdir)}.",
            )

    items = doc.get("problems")
    if items is None:
        items = doc.get("variants")
    if not isinstance(items, list):
        return (["Document must contain a 'problems' or 'variants' list."], None)

    prepared = _PreparedSourceIndex(source_pages, shingle_size=shingle_size)
    errors: list[str] = []
    for idx, prob in enumerate(items, 1):
        if not isinstance(prob, dict):
            continue
        if "id" not in prob and "variantId" not in prob:
            prob = {**prob, "id": f"Q{idx:02d}"}
        errors.extend(
            check_problem_originality(
                prob,
                source_pages,
                shingle_size=shingle_size,
                similarity_threshold=similarity_threshold,
                _prepared=prepared,
            )
        )
    return (errors, None)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m math_engine.source_cores.originality",
        description="Check a math drill draft or variant bank against cached source pages for originality.",
    )
    parser.add_argument("file", help="Path to a drill draft JSON or variant bank JSON.")
    parser.add_argument("--unit", help="Target unit code (defaults to unitCode in the JSON file).")
    parser.add_argument(
        "--sources-dir", help="Override sources directory (default: LEARNINGOS_SOURCES_DIR or <main>/sources)."
    )
    parser.add_argument(
        "--shingle-size",
        type=int,
        default=DEFAULT_SHINGLE_SIZE,
        help=f"Word shingle size for verbatim overlap check (default: {DEFAULT_SHINGLE_SIZE}).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_SIMILARITY_THRESHOLD,
        help=f"Normalised similarity rejection threshold (default: {DEFAULT_SIMILARITY_THRESHOLD}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        with open(args.file, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"FAIL Could not load '{args.file}': {exc}", file=sys.stderr)
        return 1

    errors, notice = check_document_originality(
        doc,
        unit_code=args.unit,
        sources_dir=args.sources_dir,
        shingle_size=args.shingle_size,
        similarity_threshold=args.threshold,
    )
    if notice:
        print(f"NOTE: {notice}")
        return 0
    if errors:
        for line in errors:
            print(f"  FAIL {line}")
        print(f"\n{len(errors)} originality error(s) found.")
        return 1
    items = doc.get("problems") or doc.get("variants") or []
    unit = args.unit or doc.get("unitCode") or "?"
    print(f"OK: all {len(items)} item(s) for {unit} passed the originality gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
