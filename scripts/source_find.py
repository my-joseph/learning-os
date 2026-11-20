# -*- coding: utf-8 -*-
"""Locate and rank candidate source pages for a unit across local PDFs (and PDFs inside zip archives).

Uses ``pypdf`` (imported lazily) with an extracted-text cache under ``sources/_index/`` and
writes a per-unit manifest ``sources/_index/located_<UNIT>.json`` for the originality gate.

With ``--plan``, writes a bounded, diversity-balanced, ledger-aware extraction plan to
``sources/_index/plan_<UNIT>.json`` so extraction cost stays bounded regardless of how many
source files exist under ``sources/``.

Scope-only families (OpenStax, per ``docs/sources.md`` and ``rules/07`` §4) are reported strictly
as ``scope`` (TOC / learning objectives) and never selected as mining targets. Pages with no
extractable text are listed as ``image page — read visually``.

Usage:
    python -m scripts.source_find MTH-T02-C01-U01
    python -m scripts.source_find MTH-T02-C01-U02 --plan
    python -m scripts.source_find MTH-T02-C01-U02 --plan --budget-pages 30 --budget-items 40 --refresh
    python -m scripts.source_find MTH-T02-C01-U01 --terms "complex,conjugate" --families mathsgenie,thai-exams
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from collections import Counter
from typing import Any

from math_engine.source_cores import (
    DEFAULT_FAMILY_PRIORITY,
    REPO_ROOT,
    SOURCE_FAMILIES,
    family_mode,
    family_priority,
    family_root,
    get_unit_terms,
    index_dir,
    is_thai_exam_family,
    resolve_sources_dir,
)
from math_engine.source_cores.ledger import (
    compute_file_hash,
    compute_relpath_hash,
    is_page_extracted,
    load_ledger,
    normalize_rel_path,
)

DOCS_SOURCES_PATH = os.path.join(REPO_ROOT, "docs", "sources.md")
DOCS_BACKLOG_PATH = os.path.join(REPO_ROOT, "docs", "source_backlog.md")

DEFAULT_BUDGET_PAGES = 30
DEFAULT_BUDGET_ITEMS = 40
DEFAULT_BATCH_SIZE = 10
THAI_EXAM_BOOST = 25.0

_SCOPE_HINT_KEYWORDS = ("table of contents", "contents", "learning objectives", "by the end of this section")
_TABLE_FAMILY_RE = re.compile(r"^\|\s*`([^`]+)`")
_BACKLOG_ITEM_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*(\d+)\.\s*\*\*(.+?)\*\*(.*)$")
_BACKLOG_SOURCES_PATH_RE = re.compile(r"sources/([A-Za-z0-9_./-]+)")
_ITEM_MARKER_RE = re.compile(
    r"^\s*(?:(?:Q|Question|Problem|Ex(?:ample)?)\s*\.?\s*)?\d{1,3}\s*[\.\):](?:\s|$)"
    r"|^\s*ข้อ\s*\d{1,3}\b"
    r"|^\s*\(\d{1,2}\)\s+",
    re.IGNORECASE | re.MULTILINE,
)


def _clean_family_prefix(raw_token: str) -> str:
    """Strip wildcard/placeholder segments from a ``docs/sources.md`` family path."""
    parts = [p for p in raw_token.replace("\\", "/").strip("/").split("/") if p]
    cleaned: list[str] = []
    for part in parts:
        if any(ch in part for ch in ("*", "<", ">", "{", "}", "…", "...")):
            break
        if part.lower().startswith("grade_") and part[6:].upper() == "N":
            break
        cleaned.append(part.lower())
    return "/".join(cleaned)


def load_registered_source_families(registry_path: str | None = None) -> set[str]:
    """Parse top-level registered folder names (lowercased) from ``docs/sources.md``."""
    target = registry_path or DOCS_SOURCES_PATH
    if not os.path.isfile(target):
        return set()
    registered: set[str] = set()
    with open(target, "r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            m = _TABLE_FAMILY_RE.match(stripped)
            if not m:
                continue
            token = m.group(1).replace("\\", "/").strip("/")
            if not token:
                continue
            top = token.split("/", 1)[0].lower()
            if top:
                registered.add(top)
    return registered


def load_registry_priorities(registry_path: str | None = None) -> dict[str, int]:
    """Parse per-family / per-subpath ``Priority`` values from ``docs/sources.md``."""
    target = registry_path or DOCS_SOURCES_PATH
    if not os.path.isfile(target):
        return {}
    priorities: dict[str, int] = {}
    priority_col: int | None = None
    with open(target, "r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped.startswith("|"):
                priority_col = None
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not cells:
                continue
            if all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c):
                continue
            lower_cells = [c.lower() for c in cells]
            if any("priority" == c or c.startswith("priority ") for c in lower_cells):
                for idx, val in enumerate(lower_cells):
                    if val == "priority" or val.startswith("priority "):
                        priority_col = idx
                        break
                continue
            if priority_col is None or priority_col >= len(cells):
                continue
            m = _TABLE_FAMILY_RE.match(stripped)
            if not m:
                continue
            raw_prio = cells[priority_col].strip("` ").strip()
            if not re.fullmatch(r"\d+", raw_prio):
                continue
            prio_val = int(raw_prio)
            prefix = _clean_family_prefix(m.group(1))
            if not prefix:
                continue
            priorities[prefix] = max(priorities.get(prefix, -1), prio_val)
            top = prefix.split("/", 1)[0]
            priorities[top] = max(priorities.get(top, -1), prio_val)
    return priorities


def _slug_variants(title: str) -> set[str]:
    """Build normalized lookup tokens from a ``docs/source_backlog.md`` title."""
    base = re.sub(r"\([^)]*\)", " ", title).lower()
    words = re.findall(r"[a-z0-9]+", base)
    out: set[str] = set()
    if not words:
        return out
    out.add(words[0])
    if len(words) >= 2:
        out.add(f"{words[0]}-{words[1]}")
        out.add(f"{words[0]}{words[1]}")
    joined = "-".join(words)
    out.add(joined)
    out.add("".join(words))
    return out


def load_backlog_ranks(backlog_path: str | None = None, unit_code: str | None = None) -> dict[str, int]:
    """Parse ranked source positions (1 = highest) from ``docs/source_backlog.md``."""
    target = backlog_path or DOCS_BACKLOG_PATH
    if not os.path.isfile(target):
        return {}

    want_section: str | None = None
    if isinstance(unit_code, str) and unit_code.strip():
        prefix = unit_code.strip().upper().split("-", 1)[0]
        if prefix == "PRG":
            want_section = "prg"
        elif prefix in ("MTH", "PHY"):
            want_section = "math"

    ranks: dict[str, int] = {}
    current_section: str | None = None

    def _record(key: str, rank: int) -> None:
        k = key.strip("/").lower()
        if not k:
            return
        prev = ranks.get(k)
        if prev is None or rank < prev:
            ranks[k] = rank

    with open(target, "r", encoding="utf-8") as fh:
        for line in fh:
            low = line.strip().lower()
            if low.startswith("## "):
                if "math sources" in low:
                    current_section = "math"
                elif "prg sources" in low:
                    current_section = "prg"
                else:
                    current_section = "other"
                continue
            if want_section and current_section and current_section != want_section:
                continue
            m = _BACKLOG_ITEM_RE.match(line)
            if not m:
                continue
            rank = int(m.group(1))
            title = m.group(2)
            rest = m.group(3)
            # Explicit local path hints like `sources/thai-exams/tcas68-a-level/`
            for pm in _BACKLOG_SOURCES_PATH_RE.finditer(rest):
                rel = pm.group(1).strip("/").rstrip(".,;:)")
                if not rel:
                    continue
                _record(rel, rank)
                _record(rel.split("/", 1)[0], rank)
            for slug in _slug_variants(title):
                _record(slug, rank)
    return ranks


def estimate_page_items(text: str) -> int:
    """Estimate how many distinct problem items appear on a page (clamped to 1..15)."""
    matches = _ITEM_MARKER_RE.findall(text or "")
    if not matches:
        return 1
    return max(1, min(len(matches), 15))


def find_unregistered_source_folders(sources_dir: str, registry_path: str | None = None) -> list[str]:
    """Return sorted top-level directories under ``sources_dir`` not listed in ``docs/sources.md``.

    Ignores hidden entries (starting with ``.``) and internal folders (starting with ``_``).
    """
    if not os.path.isdir(sources_dir):
        return []
    registered = load_registered_source_families(registry_path=registry_path)
    unregistered: list[str] = []
    for entry in sorted(os.listdir(sources_dir)):
        if entry.startswith("_") or entry.startswith("."):
            continue
        full = os.path.join(sources_dir, entry)
        if not os.path.isdir(full):
            continue
        if entry.lower() not in registered:
            unregistered.append(entry)
    return unregistered


def _load_pypdf() -> Any:
    try:
        import pypdf
    except ImportError as exc:
        raise RuntimeError(
            "pypdf is required for PDF text extraction. "
            "Install dev dependencies: .venv/bin/python -m pip install -r requirements-dev.txt"
        ) from exc
    return pypdf


def extract_pdf_pages(source: str | bytes) -> list[dict[str, Any]]:
    """Extract per-page text from a PDF path or raw PDF bytes using ``pypdf``."""
    pypdf = _load_pypdf()
    stream: Any = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
    reader = pypdf.PdfReader(stream)
    pages: list[dict[str, Any]] = []
    for idx, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        pages.append(
            {
                "page": idx,
                "text": text,
                "isImagePage": not text.strip(),
            }
        )
    return pages


def _cache_filename(rel_path: str) -> str:
    digest = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:16]
    return f"pdf_{digest}.json"


def _load_or_extract_pdf(
    rel_path: str,
    abs_path: str,
    idx_dir: str,
    *,
    zip_member: str | None = None,
    use_cache: bool = True,
) -> tuple[str, dict[str, Any]]:
    stat = os.stat(abs_path)
    cache_name = _cache_filename(rel_path)
    cache_path = os.path.join(idx_dir, cache_name)

    if use_cache and os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as fh:
                cached = json.load(fh)
            if (
                cached.get("relPath") == rel_path
                and cached.get("mtime") == stat.st_mtime
                and cached.get("size") == stat.st_size
                and isinstance(cached.get("pages"), list)
            ):
                return cache_name, cached
        except (OSError, ValueError):
            pass

    if zip_member is not None:
        with zipfile.ZipFile(abs_path, "r") as zf:
            raw_bytes = zf.read(zip_member)
        pages = extract_pdf_pages(raw_bytes)
        file_hash = hashlib.sha256(raw_bytes).hexdigest()
    else:
        pages = extract_pdf_pages(abs_path)
        file_hash = compute_file_hash(abs_path)

    doc = {
        "relPath": rel_path,
        "family": family_root(rel_path),
        "mode": family_mode(rel_path),
        "mtime": stat.st_mtime,
        "size": stat.st_size,
        "fileHash": file_hash,
        "pages": pages,
    }
    os.makedirs(idx_dir, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
    return cache_name, doc


def _discover_source_pdfs(sources_dir: str, families: list[str] | None = None) -> list[tuple[str, str, str | None]]:
    """Return sorted list of ``(rel_path, abs_path, zip_member_or_none)`` under ``sources_dir``."""
    fam_filters = [f.replace("\\", "/").strip("/").lower() for f in (families or []) if f.strip()]

    def _family_allowed(rel: str) -> bool:
        if not fam_filters:
            return True
        low = rel.lower()
        root = family_root(rel)
        return any(root == f or low.startswith(f + "/") or low == f for f in fam_filters)

    found: list[tuple[str, str, str | None]] = []
    for dirpath, dirnames, filenames in os.walk(sources_dir):
        rel_dir = os.path.relpath(dirpath, sources_dir).replace("\\", "/")
        if rel_dir == ".":
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("_") and not d.startswith("."))
        else:
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))

        for fname in sorted(filenames):
            if fname.startswith("."):
                continue
            abs_file = os.path.join(dirpath, fname)
            rel_file = fname if rel_dir == "." else f"{rel_dir}/{fname}"
            low = fname.lower()
            if low.endswith(".pdf"):
                if _family_allowed(rel_file):
                    found.append((rel_file, abs_file, None))
            elif low.endswith(".zip"):
                if not _family_allowed(rel_file):
                    continue
                try:
                    with zipfile.ZipFile(abs_file, "r") as zf:
                        for member in sorted(zf.namelist()):
                            if member.startswith("__MACOSX/") or "/." in member or not member.lower().endswith(".pdf"):
                                continue
                            found.append((f"{rel_file}::{member}", abs_file, member))
                except (OSError, zipfile.BadZipFile):
                    continue
    return found


def _count_term_hits(text: str, terms: list[str]) -> dict[str, int]:
    low = text.lower()
    hits: dict[str, int] = {}
    for term in terms:
        needle = term.lower().strip()
        if not needle:
            continue
        count = low.count(needle)
        if count > 0:
            hits[term] = count
    return hits


def find_sources(
    unit_code: str,
    *,
    terms: list[str] | None = None,
    families: list[str] | None = None,
    sources_dir: str | None = None,
    use_cache: bool = True,
    registry_path: str | None = None,
) -> dict[str, Any]:
    """Search PDFs under ``sources_dir`` for ``unit_code`` terms and cache extracted text."""
    sdir = resolve_sources_dir(sources_dir=sources_dir)
    if not os.path.isdir(sdir):
        raise FileNotFoundError(
            f"Sources directory not found: {sdir}. Set LEARNINGOS_SOURCES_DIR or place sources under <main>/sources."
        )

    search_terms = [t.strip() for t in (terms if terms is not None else get_unit_terms(unit_code)) if t.strip()]
    if not search_terms:
        raise ValueError(
            f"No search terms found for '{unit_code}'. Pass --terms or add '{unit_code}' to "
            "math_engine/source_cores/unit_terms.json."
        )

    unregistered = find_unregistered_source_folders(sdir, registry_path=registry_path)
    idx_dir = index_dir(sources_dir=sdir)
    pdfs = _discover_source_pdfs(sdir, families=families)

    core_matches: list[dict[str, Any]] = []
    scope_matches: list[dict[str, Any]] = []
    image_only_files: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for rel_path, abs_path, zip_member in pdfs:
        try:
            cache_name, doc = _load_or_extract_pdf(
                rel_path,
                abs_path,
                idx_dir,
                zip_member=zip_member,
                use_cache=use_cache,
            )
        except RuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001 - report unreadable PDF without aborting scan
            errors.append({"relPath": rel_path, "error": str(exc)})
            continue

        pages = doc.get("pages") or []
        fam = doc.get("family") or family_root(rel_path)
        mode = doc.get("mode") or family_mode(rel_path)

        matched_pages: list[dict[str, Any]] = []
        image_pages: list[int] = []
        has_any_text = False

        for p in pages:
            pnum = int(p.get("page", 0))
            text = str(p.get("text") or "")
            if p.get("isImagePage") or not text.strip():
                image_pages.append(pnum)
                continue
            has_any_text = True
            term_counts = _count_term_hits(text, search_terms)
            if term_counts:
                entry: dict[str, Any] = {
                    "page": pnum,
                    "hits": sum(term_counts.values()),
                    "terms": term_counts,
                    "charLen": len(text.strip()),
                    "estimatedItems": estimate_page_items(text),
                }
                if mode == "scope":
                    low = text.lower()
                    entry["scopeSection"] = (
                        "toc/objectives" if any(k in low for k in _SCOPE_HINT_KEYWORDS) else "scope-only"
                    )
                matched_pages.append(entry)

        if matched_pages:
            record = {
                "relPath": rel_path,
                "family": fam,
                "mode": mode,
                "cacheFile": cache_name,
                "totalHits": sum(p["hits"] for p in matched_pages),
                "pages": matched_pages,
                "imagePages": image_pages,
            }
            if isinstance(doc.get("fileHash"), str) and doc["fileHash"]:
                record["fileHash"] = doc["fileHash"]
            if mode == "scope":
                scope_matches.append(record)
            else:
                core_matches.append(record)
        elif not has_any_text and image_pages:
            image_only_files.append(
                {
                    "relPath": rel_path,
                    "family": fam,
                    "mode": mode,
                    "cacheFile": cache_name,
                    "imagePages": image_pages,
                }
            )

    core_matches.sort(key=lambda r: (-r["totalHits"], r["relPath"]))
    scope_matches.sort(key=lambda r: (-r["totalHits"], r["relPath"]))

    manifest = {
        "unitCode": unit_code,
        "terms": search_terms,
        "matches": core_matches + scope_matches,
        "imageOnlyFiles": image_only_files,
    }
    os.makedirs(idx_dir, exist_ok=True)
    manifest_path = os.path.join(idx_dir, f"located_{unit_code}.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    return {
        "unitCode": unit_code,
        "sourcesDir": sdir,
        "manifestPath": manifest_path,
        "terms": search_terms,
        "pdfsScanned": len(pdfs),
        "unregisteredSources": unregistered,
        "coreMatches": core_matches,
        "scopeMatches": scope_matches,
        "imageOnlyFiles": image_only_files,
        "errors": errors,
    }


def _longest_prefix_lookup(rel_path: str, family: str, mapping: dict[str, int]) -> int | None:
    """Look up the longest matching path prefix in ``mapping`` (falling back to family root)."""
    if not mapping:
        return None
    norm = normalize_rel_path(rel_path).split("::", 1)[0].lower()
    parts = [p for p in norm.split("/") if p]
    for depth in range(len(parts), 0, -1):
        prefix = "/".join(parts[:depth])
        if prefix in mapping:
            return mapping[prefix]
    fam_low = family.lower()
    if fam_low in mapping:
        return mapping[fam_low]
    compact = fam_low.replace("-", "").replace("_", "")
    if compact in mapping:
        return mapping[compact]
    return None


def _score_candidate_page(
    rel_path: str,
    family: str,
    page_entry: dict[str, Any],
    *,
    registry_priorities: dict[str, int],
    backlog_ranks: dict[str, int],
) -> tuple[float, dict[str, Any]]:
    """Compute ranking score and breakdown for one candidate page."""
    reg_prio = _longest_prefix_lookup(rel_path, family, registry_priorities)
    backlog_rank = _longest_prefix_lookup(rel_path, family, backlog_ranks)

    if reg_prio is not None:
        base_priority = int(reg_prio)
    elif family.lower() in SOURCE_FAMILIES:
        base_priority = family_priority(rel_path)
    elif backlog_rank is not None:
        base_priority = max(10, 100 - (backlog_rank - 1) * 2)
    else:
        base_priority = DEFAULT_FAMILY_PRIORITY

    backlog_bonus = round(20.0 / (1.0 + 0.1 * (backlog_rank - 1)), 2) if backlog_rank is not None else 0.0

    hits = int(page_entry.get("hits") or 0)
    distinct_terms = len(page_entry.get("terms") or {})
    char_len = max(int(page_entry.get("charLen") or 0), 200)
    density = hits / (char_len / 500.0)
    density_score = round(min(density * 10.0, 50.0) + min(distinct_terms * 5.0, 25.0) + min(hits * 1.5, 25.0), 2)

    thai_boost = THAI_EXAM_BOOST if is_thai_exam_family(rel_path) else 0.0
    total_score = round(base_priority + backlog_bonus + density_score + thai_boost, 2)

    breakdown = {
        "familyPriority": base_priority,
        "backlogRank": backlog_rank,
        "backlogBonus": backlog_bonus,
        "termDensity": round(density, 4),
        "densityScore": density_score,
        "thaiExamBoost": thai_boost,
    }
    return total_score, breakdown


def _resolve_candidate_hash(
    sdir: str,
    idx_dir: str,
    match: dict[str, Any],
    hash_cache: dict[str, str],
) -> str:
    rel_path = str(match["relPath"])
    if rel_path in hash_cache:
        return hash_cache[rel_path]
    digest = compute_relpath_hash(sdir, rel_path)
    if not digest:
        cached_hash = match.get("fileHash")
        if isinstance(cached_hash, str) and cached_hash:
            digest = cached_hash
        else:
            cache_file = match.get("cacheFile")
            if isinstance(cache_file, str):
                cpath = os.path.join(idx_dir, cache_file)
                if os.path.isfile(cpath):
                    digest = compute_file_hash(cpath)
            if not digest:
                digest = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()
    hash_cache[rel_path] = digest
    return digest


def build_extraction_plan(
    find_result: dict[str, Any],
    *,
    budget_pages: int = DEFAULT_BUDGET_PAGES,
    budget_items: int = DEFAULT_BUDGET_ITEMS,
    batch_size: int = DEFAULT_BATCH_SIZE,
    refresh: bool = False,
    sources_dir: str | None = None,
    registry_path: str | None = None,
    backlog_path: str | None = None,
) -> dict[str, Any]:
    """Rank and select a bounded, diverse set of candidate pages and write ``plan_<UNIT>.json``.

    Ranking combines:
    (a) family priority from ``docs/sources.md`` + ``SOURCE_FAMILIES`` + ``docs/source_backlog.md``,
    (b) term-hit density,
    (c) Thai-exam relevance boost (SmartMathPro, thai-exams), and
    (d) round-robin diversity across families so one family cannot fill the budget.

    Scope-only families (OpenStax) are always skipped. Pages already present in
    ``sources/_cores/_ledger.json`` with an unchanged file hash are excluded unless
    ``refresh=True``.
    """
    if budget_pages < 0:
        raise ValueError(f"budget_pages must be >= 0, got {budget_pages}.")
    if budget_items < 0:
        raise ValueError(f"budget_items must be >= 0, got {budget_items}.")
    if batch_size < 1:
        raise ValueError(f"batch_size must be >= 1, got {batch_size}.")

    unit_code = str(find_result["unitCode"])
    sdir = resolve_sources_dir(sources_dir=sources_dir or find_result.get("sourcesDir"))
    idx_dir = index_dir(sources_dir=sdir)

    registry_priorities = load_registry_priorities(registry_path=registry_path)
    backlog_ranks = load_backlog_ranks(backlog_path=backlog_path, unit_code=unit_code)
    ledger = load_ledger(sources_dir=sdir)

    skipped_scope_pages = sum(len(m.get("pages") or []) for m in (find_result.get("scopeMatches") or []))
    skipped_ledger_pages = 0
    hash_cache: dict[str, str] = {}

    by_family: dict[str, list[dict[str, Any]]] = {}
    candidates_by_family: Counter[str] = Counter()

    for match in find_result.get("coreMatches") or []:
        rel_path = str(match.get("relPath") or "")
        fam = str(match.get("family") or family_root(rel_path))
        mode = str(match.get("mode") or family_mode(rel_path))
        if mode == "scope" or family_mode(rel_path) == "scope":
            skipped_scope_pages += len(match.get("pages") or [])
            continue

        file_hash = _resolve_candidate_hash(sdir, idx_dir, match, hash_cache)
        cache_file = str(match.get("cacheFile") or "")

        for p_entry in match.get("pages") or []:
            pnum = int(p_entry["page"])
            if not refresh and is_page_extracted(
                ledger,
                unit_code,
                rel_path,
                pnum,
                current_file_hash=file_hash,
            ):
                skipped_ledger_pages += 1
                continue

            score, breakdown = _score_candidate_page(
                rel_path,
                fam,
                p_entry,
                registry_priorities=registry_priorities,
                backlog_ranks=backlog_ranks,
            )
            est_items = max(1, int(p_entry.get("estimatedItems") or 1))
            candidate = {
                "family": fam,
                "relPath": rel_path,
                "page": pnum,
                "cacheFile": cache_file,
                "fileHash": file_hash,
                "hits": int(p_entry.get("hits") or 0),
                "terms": dict(p_entry.get("terms") or {}),
                "charLen": int(p_entry.get("charLen") or 0),
                "estimatedItems": est_items,
                "score": score,
                "scoreBreakdown": breakdown,
            }
            by_family.setdefault(fam, []).append(candidate)
            candidates_by_family[fam] += 1

    # Sort candidates within each family by descending score
    for fam, items in by_family.items():
        items.sort(key=lambda c: (-c["score"], -c["hits"], c["relPath"], c["page"]))

    # Order families by highest base priority + Thai boost + backlog bonus, then top page score
    def _family_sort_key(fam: str) -> tuple[float, float, str]:
        top = by_family[fam][0]
        bd = top["scoreBreakdown"]
        fam_rank_val = float(bd["familyPriority"]) + float(bd["backlogBonus"]) + float(bd["thaiExamBoost"])
        return (-fam_rank_val, -float(top["score"]), fam)

    family_order = sorted(by_family.keys(), key=_family_sort_key)

    # Round-robin selection across families for diversity
    cursors = {fam: 0 for fam in family_order}
    selected: list[dict[str, Any]] = []
    cumulative_items = 0

    while len(selected) < budget_pages and cumulative_items < budget_items:
        picked_any = False
        for fam in family_order:
            if len(selected) >= budget_pages or cumulative_items >= budget_items:
                break
            idx = cursors[fam]
            if idx >= len(by_family[fam]):
                continue
            cand = by_family[fam][idx]
            cursors[fam] = idx + 1
            picked_any = True

            remaining_items = budget_items - cumulative_items
            allowance = min(cand["estimatedItems"], remaining_items)
            cumulative_items += allowance

            selected.append(
                {
                    "rank": len(selected) + 1,
                    "batch": (len(selected) // batch_size) + 1,
                    **cand,
                    "itemAllowance": allowance,
                }
            )
        if not picked_any:
            break

    batches: list[dict[str, Any]] = []
    for start in range(0, len(selected), batch_size):
        chunk = selected[start : start + batch_size]
        batch_num = (start // batch_size) + 1
        batches.append(
            {
                "batch": batch_num,
                "pageCount": len(chunk),
                "estimatedItems": sum(c["itemAllowance"] for c in chunk),
                "pagesByFamily": dict(sorted(Counter(c["family"] for c in chunk).items())),
                "pages": chunk,
            }
        )

    pages_by_family = dict(sorted(Counter(c["family"] for c in selected).items()))
    total_candidates = sum(candidates_by_family.values())

    os.makedirs(idx_dir, exist_ok=True)
    plan_file = os.path.join(idx_dir, f"plan_{unit_code}.json")

    plan: dict[str, Any] = {
        "unitCode": unit_code,
        "sourcesDir": sdir,
        "planPath": plan_file,
        "terms": list(find_result.get("terms") or []),
        "budget": {
            "maxPages": budget_pages,
            "maxItems": budget_items,
            "batchSize": batch_size,
            "refresh": refresh,
        },
        "summary": {
            "totalCandidates": total_candidates,
            "skippedLedgerPages": skipped_ledger_pages,
            "skippedScopePages": skipped_scope_pages,
            "selectedPageCount": len(selected),
            "selectedEstimatedItems": cumulative_items,
            "batchCount": len(batches),
            "pagesByFamily": pages_by_family,
            "candidatesByFamily": dict(sorted(candidates_by_family.items())),
        },
        "unregisteredSources": list(find_result.get("unregisteredSources") or []),
        "selectedPages": selected,
        "batches": batches,
    }

    with open(plan_file, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    return plan


def _format_page_list(pages: list[int]) -> str:
    return ", ".join(f"p.{p}" for p in pages)


def format_find_report(result: dict[str, Any]) -> str:
    """Format ``find_sources`` results for CLI output."""
    lines = [
        f"Source find for {result['unitCode']} ({result['pdfsScanned']} PDF(s) scanned)",
        f"Terms: {', '.join(result['terms'])}",
        f"Sources dir: {result['sourcesDir']}",
    ]

    unregistered = result.get("unregisteredSources") or []
    if unregistered:
        lines.append("")
        lines.append(
            f"WARNING: Unregistered top-level folder(s) under sources/ not in docs/sources.md: "
            f"{', '.join(unregistered)}"
        )
        lines.append("  Please register each folder in docs/sources.md (family, licence, allowed use) before mining.")

    lines.append("")

    core_matches = result.get("coreMatches") or []
    lines.append(f"Mining targets (cores): {len(core_matches)} file(s)")
    if not core_matches:
        lines.append("  (none)")
    for item in core_matches:
        lines.append(f"  [cores:{item['family']}] {item['relPath']} ({item['totalHits']} hits)")
        for p in item["pages"]:
            breakdown = ", ".join(f"{t}={n}" for t, n in sorted(p["terms"].items()))
            lines.append(f"    - p.{p['page']}: {p['hits']} hit(s) ({breakdown})")
        for pnum in item.get("imagePages") or []:
            lines.append(f"    - p.{pnum}: image page — read visually")

    lines.append("")
    scope_matches = result.get("scopeMatches") or []
    lines.append(f"Scope only (TOC / learning objectives — NEVER mine for exercises): {len(scope_matches)} file(s)")
    if not scope_matches:
        lines.append("  (none)")
    for item in scope_matches:
        lines.append(f"  [scope:{item['family']}] {item['relPath']} ({item['totalHits']} hits)")
        for p in item["pages"]:
            tag = p.get("scopeSection", "scope-only")
            breakdown = ", ".join(f"{t}={n}" for t, n in sorted(p["terms"].items()))
            lines.append(f"    - p.{p['page']} [{tag}]: {p['hits']} hit(s) ({breakdown})")

    image_only = result.get("imageOnlyFiles") or []
    if image_only:
        lines.append("")
        lines.append(f"Image-only PDFs (no extractable text): {len(image_only)} file(s)")
        for item in image_only:
            tag = "scope" if item["mode"] == "scope" else "cores"
            lines.append(
                f"  [{tag}:{item['family']}] {item['relPath']}: "
                f"{_format_page_list(item['imagePages'])} — image page — read visually"
            )

    errors = result.get("errors") or []
    if errors:
        lines.append("")
        lines.append(f"Unreadable PDFs ({len(errors)}):")
        for err in errors:
            lines.append(f"  - {err['relPath']}: {err['error']}")

    return "\n".join(lines)


def format_plan_report(plan: dict[str, Any]) -> str:
    """Format ``build_extraction_plan`` output concisely for CLI display."""
    s = plan["summary"]
    b = plan["budget"]
    lines = [
        f"Extraction plan for {plan['unitCode']}",
        f"Plan file: {plan['planPath']}",
        f"Budget: max {b['maxPages']} page(s), max {b['maxItems']} item(s), "
        f"batch size {b['batchSize']}{' [REFRESH]' if b['refresh'] else ''}",
        f"Candidates: {s['totalCandidates']} eligible, {s['skippedLedgerPages']} skipped (ledger), "
        f"{s['skippedScopePages']} skipped (scope-only)",
        f"Selected: {s['selectedPageCount']} page(s), ~{s['selectedEstimatedItems']} item(s) "
        f"in {s['batchCount']} batch(es)",
    ]

    unregistered = plan.get("unregisteredSources") or []
    if unregistered:
        lines.append("")
        lines.append(
            f"WARNING: Unregistered top-level folder(s) under sources/ not in docs/sources.md: "
            f"{', '.join(unregistered)}"
        )

    lines.append("")
    lines.append("Selected pages per family (selected / eligible):")
    if not s["pagesByFamily"]:
        lines.append("  (none)")
    else:
        for fam, count in s["pagesByFamily"].items():
            elig = s["candidatesByFamily"].get(fam, count)
            lines.append(f"  - {fam}: {count} / {elig} page(s)")

    if plan["batches"]:
        lines.append("")
        lines.append("Batches:")
        for batch in plan["batches"]:
            fams = ", ".join(f"{k}={v}" for k, v in batch["pagesByFamily"].items())
            lines.append(
                f"  Batch {batch['batch']}: {batch['pageCount']} page(s), ~{batch['estimatedItems']} item(s) [{fams}]"
            )
            for p in batch["pages"]:
                lines.append(
                    f"    #{p['rank']:02d} [{p['family']}] {p['relPath']} p.{p['page']} "
                    f"(score={p['score']}, hits={p['hits']}, items<={p['itemAllowance']})"
                )

    return "\n".join(lines)


def _split_multi_arg(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None
    out: list[str] = []
    for v in values:
        for part in v.split(","):
            s = part.strip()
            if s:
                out.append(s)
    return out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.source_find",
        description="Locate candidate source PDF pages for a unit (with caching and budgeted planning).",
    )
    parser.add_argument("unit", help="Target unit code (e.g. MTH-T02-C01-U01).")
    parser.add_argument(
        "--terms",
        nargs="+",
        default=None,
        help="Search terms (comma-separated or multiple args). Defaults to math_engine/source_cores/unit_terms.json.",
    )
    parser.add_argument(
        "--families",
        nargs="+",
        default=None,
        help="Filter to specific source families or subpaths (e.g. mathsgenie,thai-exams).",
    )
    parser.add_argument(
        "--sources-dir",
        default=None,
        help="Override sources directory (default: LEARNINGOS_SOURCES_DIR or <main>/sources).",
    )
    parser.add_argument("--no-cache", action="store_true", help="Re-extract PDFs instead of reading sources/_index/.")
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Rank and select bounded, diverse candidate pages and write sources/_index/plan_<UNIT>.json.",
    )
    parser.add_argument(
        "--budget-pages",
        type=int,
        default=DEFAULT_BUDGET_PAGES,
        help=f"Max pages to select when --plan is set (default: {DEFAULT_BUDGET_PAGES}).",
    )
    parser.add_argument(
        "--budget-items",
        type=int,
        default=DEFAULT_BUDGET_ITEMS,
        help=f"Max estimated items to select when --plan is set (default: {DEFAULT_BUDGET_ITEMS}).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Pages per worker batch in plan_<UNIT>.json (default: {DEFAULT_BATCH_SIZE}).",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Include pages already recorded in sources/_cores/_ledger.json when building --plan.",
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result = find_sources(
            args.unit,
            terms=_split_multi_arg(args.terms),
            families=_split_multi_arg(args.families),
            sources_dir=args.sources_dir,
            use_cache=not args.no_cache,
        )
        if args.plan:
            plan = build_extraction_plan(
                result,
                budget_pages=args.budget_pages,
                budget_items=args.budget_items,
                batch_size=args.batch_size,
                refresh=args.refresh,
                sources_dir=args.sources_dir,
            )
            if args.json:
                print(json.dumps(plan, ensure_ascii=False, indent=2))
            else:
                print(format_plan_report(plan))
            return 0
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_find_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
