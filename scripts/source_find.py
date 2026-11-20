# -*- coding: utf-8 -*-
"""Locate candidate source pages for a unit across local PDFs (and PDFs inside zip archives).

Uses ``pypdf`` (imported lazily) with an extracted-text cache under ``sources/_index/`` and
writes a per-unit manifest ``sources/_index/located_<UNIT>.json`` for the originality gate.

Scope-only families (OpenStax, per ``docs/sources.md`` and ``rules/07`` §4) are reported strictly
as ``scope`` (TOC / learning objectives) and never as mining targets. Pages with no extractable
text are listed as ``image page — read visually``.

Usage:
    python -m scripts.source_find MTH-T02-C01-U01
    python -m scripts.source_find MTH-T02-C01-U01 --terms "complex,conjugate" --families mathsgenie,thai-exams
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import zipfile
from typing import Any

from math_engine.source_cores import (
    family_mode,
    family_root,
    get_unit_terms,
    index_dir,
    resolve_sources_dir,
)

_SCOPE_HINT_KEYWORDS = ("table of contents", "contents", "learning objectives", "by the end of this section")


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
    else:
        pages = extract_pdf_pages(abs_path)

    doc = {
        "relPath": rel_path,
        "family": family_root(rel_path),
        "mode": family_mode(rel_path),
        "mtime": stat.st_mtime,
        "size": stat.st_size,
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
        "coreMatches": core_matches,
        "scopeMatches": scope_matches,
        "imageOnlyFiles": image_only_files,
        "errors": errors,
    }


def _format_page_list(pages: list[int]) -> str:
    return ", ".join(f"p.{p}" for p in pages)


def format_find_report(result: dict[str, Any]) -> str:
    """Format ``find_sources`` results for CLI output."""
    lines = [
        f"Source find for {result['unitCode']} ({result['pdfsScanned']} PDF(s) scanned)",
        f"Terms: {', '.join(result['terms'])}",
        f"Sources dir: {result['sourcesDir']}",
        "",
    ]

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
        description="Locate candidate source PDF pages for a unit (with caching under sources/_index/).",
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
