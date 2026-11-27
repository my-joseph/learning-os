# -*- coding: utf-8 -*-
"""Locate and rank candidate source pages/files for a unit across local PDFs (Math/PHY)
and local code/markdown repositories under ``sources/prg/<family>/`` (PRG).

Uses ``pypdf`` (imported lazily, PDFs only) with an extracted-text cache under ``sources/_index/``
and writes a per-unit manifest ``sources/_index/located_<UNIT>.json`` for the originality gate.

With ``--plan``, writes a bounded, diversity-balanced, ledger-aware extraction plan to
``sources/_index/plan_<UNIT>.json`` so extraction cost stays bounded regardless of how many
source files exist under ``sources/``.

Scope-only families (OpenStax, per ``docs/sources.md`` and ``rules/07`` §4) are reported strictly
as ``scope`` (TOC / learning objectives) and never selected as mining targets.
``NO-AUTOMATION`` families are never indexed, cached, or selected automatically.

Usage:
    python -m scripts.source_find MTH-T02-C01-U01
    python -m scripts.source_find PRG-T01-C01-U02 --plan
    python -m scripts.source_find MTH-T02-C01-U02 --plan --budget-pages 30 --budget-items 40 --refresh
    python -m scripts.source_find PRG-T01-C01-U02 --terms "closure,lexical" --families prg/javascript-questions
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from typing import Any

from math_engine.source_cores import (
    DEFAULT_FAMILY_PRIORITY,
    REPO_ROOT,
    SOURCE_FAMILIES,
    family_license,
    family_mode,
    family_priority,
    family_root,
    get_unit_terms,
    index_dir,
    is_prg_unit,
    is_thai_exam_family,
    load_registry_families,
    resolve_sources_dir,
)
from math_engine.source_cores import DOCS_SOURCES_PATH as DOCS_SOURCES_PATH
from math_engine.source_cores.ledger import (
    card_schema_fingerprint,
    compute_file_hash,
    compute_relpath_hash,
    is_page_extracted,
    load_ledger,
    normalize_rel_path,
)

DOCS_BACKLOG_PATH = os.path.join(REPO_ROOT, "docs", "source_backlog.md")

DEFAULT_BUDGET_PAGES = 30
DEFAULT_BUDGET_ITEMS = 40
DEFAULT_BATCH_SIZE = 10
THAI_EXAM_BOOST = 25.0
OCR_RENDER_DPI = 300
OCR_WEAK_CONFIDENCE = 50.0
OCR_WEAK_TOKEN_COUNT = 4
_THAI_CHAR_RE = re.compile(r"[\u0e00-\u0e7f]")
_SUSPICIOUS_THAI_GLYPHS = frozenset("'\"&=฿¦§¶¤")

CODE_SOURCE_EXTENSIONS: tuple[str, ...] = (
    ".js",
    ".mjs",
    ".cjs",
    ".jsx",
    ".ts",
    ".mts",
    ".cts",
    ".tsx",
    ".py",
    ".md",
    ".markdown",
    ".json",
)
SKIP_CODE_DIRS: frozenset[str] = frozenset(
    {
        "node_modules",
        "dist",
        "build",
        "coverage",
        "__pycache__",
        ".venv",
        "vendor",
        ".next",
        ".cache",
        "target",
        ".turbo",
    }
)
SKIP_CODE_FILENAMES: frozenset[str] = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "npm-shrinkwrap.json",
        "composer.lock",
        "poetry.lock",
        "cargo.lock",
    }
)
MAX_CODE_FILE_BYTES = 512 * 1024
MAX_CHUNK_CHARS = 6000
MAX_CHUNK_LINES = 180

_SCOPE_HINT_KEYWORDS = ("table of contents", "contents", "learning objectives", "by the end of this section")
_TABLE_FAMILY_RE = re.compile(r"^\|\s*`([^`]+)`")
_BACKLOG_ITEM_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*(\d+)\.\s*\*\*(.+?)\*\*(.*)$")
_BACKLOG_SOURCES_PATH_RE = re.compile(r"sources/([A-Za-z0-9_./-]+)")
_ITEM_MARKER_RE = re.compile(
    r"^\s*(?:(?:Q|Question|Problem|Ex(?:ample)?)\s*\.?\s*)?\d{1,3}\s*[\.\):](?:\s|$)"
    r"|^\s*ข้อ\s*\d{1,3}\b"
    r"|^\s*\(\d{1,2}\)\s+"
    r"|^\s*#{2,6}\s+\d+[\.\):]"
    r"|^\s*(?:it|test|xit|xtest|describe)\s*\("
    r"|^\s*def\s+test_",
    re.IGNORECASE | re.MULTILINE,
)
_EXERCISE_HEADING_RE = re.compile(
    r"^[^\S\n]*(?:#{1,6}[^\S\n]+)?"
    r"(?:\d+(?:\.\d+)*(?:[.):]|[–-])?[^\S\n]+)?"
    r"(?:chapter[^\S\n]+)?(?:แบบฝึกหัด|(?:exercises?|practice problems?|problem set)\b)",
    re.IGNORECASE | re.MULTILINE,
)
_MD_HEADING_RE = re.compile(r"^#{1,6}\s+")
_ANSWER_DIR_RE = re.compile(r"^(?:answers?|solutions?|เฉลย)$", re.IGNORECASE)
_PROBLEM_DIR_RE = re.compile(r"^(?:questions?|problems?|โจทย์)$", re.IGNORECASE)
_ANSWER_FILE_SUFFIX_RE = re.compile(r"(?:[-_. ]?(?:ans(?:wer)?s?|solutions?))+$", re.IGNORECASE)


def _is_answer_key_path(rel_path: str) -> bool:
    """Identify likely answer-key files/folders so they are not selected as primary targets."""
    path = normalize_rel_path(rel_path).replace("::", "/")
    parts = path.split("/")
    if any("เฉลย" in part for part in parts):
        return True
    if any(_ANSWER_DIR_RE.fullmatch(part) for part in parts[:-1]):
        return True
    stem = os.path.splitext(parts[-1])[0]
    return bool(_ANSWER_FILE_SUFFIX_RE.search(stem))


def _answer_pair_key(rel_path: str) -> str:
    """Return a normalized source key that pairs problem and answer-key folder/file naming."""
    path = normalize_rel_path(rel_path).replace("::", "/")
    parts = path.split("/")
    normalized: list[str] = []
    for part in parts[:-1]:
        if _ANSWER_DIR_RE.fullmatch(part) or _PROBLEM_DIR_RE.fullmatch(part) or "เฉลย" in part:
            continue
        normalized.append(part.lower())
    stem = os.path.splitext(parts[-1])[0]
    stem = re.sub(r"(?:[-_. ]?(?:ans(?:wer)?s?|solutions?))+$", "", stem, flags=re.IGNORECASE)
    normalized.append(stem.lower())
    return "/".join(normalized)


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
    """Parse registered family keys (lowercased) from ``docs/sources.md``.

    Returns top-level math folders plus ``prg`` (when any PRG family is registered) and
    individual ``prg/<family>`` entries.
    """
    reg = load_registry_families(registry_path=registry_path)
    registered: set[str] = set()
    for key in reg:
        registered.add(key)
        top = key.split("/", 1)[0]
        if top:
            registered.add(top)
    return registered


def load_registry_priorities(registry_path: str | None = None) -> dict[str, int]:
    """Parse per-family / per-subpath ``Priority`` values from ``docs/sources.md``."""
    reg = load_registry_families(registry_path=registry_path)
    priorities: dict[str, int] = {}
    for key, meta in reg.items():
        prio = meta.get("priority")
        if isinstance(prio, int):
            priorities[key] = prio
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
            # Explicit local path hints like `sources/thai-exams/tcas68-a-level/` or `sources/prg/exercism-typescript`
            for pm in _BACKLOG_SOURCES_PATH_RE.finditer(rest):
                rel = pm.group(1).strip("/").rstrip(".,;:)")
                if not rel:
                    continue
                _record(rel, rank)
                parts = rel.split("/")
                if parts[0].lower() == "prg" and len(parts) >= 2:
                    _record(f"prg/{parts[1]}", rank)
                    _record(parts[1], rank)
                else:
                    _record(parts[0], rank)
            for slug in _slug_variants(title):
                _record(slug, rank)
    return ranks


def estimate_page_items(text: str) -> int:
    """Estimate how many distinct problem items appear on a page/chunk (clamped to 1..15)."""
    matches = _ITEM_MARKER_RE.findall(text or "")
    if not matches:
        return 1
    return max(1, min(len(matches), 15))


def find_unregistered_source_folders(sources_dir: str, registry_path: str | None = None) -> list[str]:
    """Return sorted directories under ``sources_dir`` (and ``sources_dir/prg/``) not listed in ``docs/sources.md``.

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
        low = entry.lower()
        if low == "prg":
            for sub in sorted(os.listdir(full)):
                if sub.startswith("_") or sub.startswith("."):
                    continue
                sub_full = os.path.join(full, sub)
                if not os.path.isdir(sub_full):
                    continue
                if f"prg/{sub.lower()}" not in registered:
                    unregistered.append(f"prg/{sub}")
            continue
        if low not in registered:
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
                "pdfText": text,
                "isImagePage": not text.strip(),
            }
        )
    return pages


def classify_text_quality(text: str) -> str:
    """Classify extracted PDF text as usable, empty, or likely legacy-font garbled."""
    compact = re.sub(r"\s+", "", text)
    thai_positions = [match.start() for match in _THAI_CHAR_RE.finditer(compact)]
    if len(thai_positions) >= 2:
        suspicious = 0
        for index, char in enumerate(compact):
            if char not in _SUSPICIOUS_THAI_GLYPHS:
                continue
            if any(abs(index - thai_index) <= 1 for thai_index in thai_positions):
                suspicious += 1
        if suspicious >= 2 and suspicious / len(thai_positions) >= 0.015:
            return "garbled"
    if len(compact) < 24:
        return "empty"
    return "ok"


def ocr_cache_key(file_hash: str, page: int) -> str:
    """Return a stable OCR cache key for a source PDF hash and 1-indexed page."""
    digest = hashlib.sha256(f"{file_hash}:{page}".encode("utf-8")).hexdigest()
    return f"{digest}_p{page}"


def _ocr_token_count(text: str) -> int:
    thai_words = len(re.findall(r"[\u0e00-\u0e7f]{2,}", text))
    math_tokens = len(re.findall(r"(?:\d+(?:\.\d+)?|[=+\-×÷*/^√π])", text))
    return thai_words + math_tokens


def _ocr_math_symbol_count(text: str) -> int:
    """Count visible operators and single-letter variables in OCR output."""
    return len(re.findall(r"[=+\-×÷*/^√π]|\b[A-Za-z]\b", text))


def _ocr_needs_image(text: str, confidence: float | None) -> bool:
    """Flag OCR pages with low confidence, little text, or missing math notation."""
    return (
        confidence is None
        or confidence < OCR_WEAK_CONFIDENCE
        or _ocr_token_count(text) < OCR_WEAK_TOKEN_COUNT
        or _ocr_math_symbol_count(text) < 2
    )


def _parse_tesseract_tsv(tsv: str) -> tuple[str, float | None]:
    lines: list[str] = []
    confidences: list[float] = []
    for line in tsv.splitlines()[1:]:
        cols = line.split("\t", 11)
        if len(cols) < 12 or not cols[11].strip():
            continue
        try:
            confidence = float(cols[10])
        except ValueError:
            confidence = -1
        if confidence >= 0:
            confidences.append(confidence)
        lines.append(cols[11].strip())
    return "\n".join(lines), (sum(confidences) / len(confidences) if confidences else None)


def _ocr_page(
    pdf_path: str,
    page: int,
    file_hash: str,
    idx_dir: str,
    *,
    pdf_bytes: bytes | None = None,
) -> dict[str, Any] | None:
    """Render and OCR one PDF page, caching both PNG and text under the sources index."""
    key = ocr_cache_key(file_hash, page)
    png_path = os.path.join(idx_dir, f"ocr_{key}.png")
    json_path = os.path.join(idx_dir, f"ocr_{key}.json")
    if os.path.isfile(png_path) and os.path.isfile(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as fh:
                cached = json.load(fh)
            if isinstance(cached, dict) and isinstance(cached.get("text"), str):
                cached["tokenCount"] = _ocr_token_count(cached["text"])
                cached["mathSymbolCount"] = _ocr_math_symbol_count(cached["text"])
                cached["needsImage"] = _ocr_needs_image(cached["text"], cached.get("confidence"))
                return {**cached, "imageFile": os.path.basename(png_path)}
        except (OSError, ValueError):
            pass

    os.makedirs(idx_dir, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="learningos-ocr-") as tmp_dir:
        input_pdf = pdf_path
        if pdf_bytes is not None:
            input_pdf = os.path.join(tmp_dir, "source.pdf")
            with open(input_pdf, "wb") as fh:
                fh.write(pdf_bytes)
        prefix = os.path.join(tmp_dir, "page")
        try:
            subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    str(page),
                    "-l",
                    str(page),
                    "-r",
                    str(OCR_RENDER_DPI),
                    "-png",
                    "-singlefile",
                    input_pdf,
                    prefix,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            rendered = prefix + ".png"
            if not os.path.isfile(rendered):
                return None
            # Keep the rendered image even if OCR is unavailable or fails.
            with open(rendered, "rb") as src, open(png_path, "wb") as dst:
                dst.write(src.read())
            plain = subprocess.run(
                ["tesseract", png_path, "-", "-l", "tha+eng"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            tsv = subprocess.run(
                ["tesseract", png_path, "-", "-l", "tha+eng", "tsv"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            message = getattr(exc, "stderr", None) or str(exc)
            print(f"WARNING: OCR fallback unavailable for page {page}: {message.strip()}", file=sys.stderr)
            if os.path.isfile(png_path):
                return {
                    "text": "",
                    "confidence": None,
                    "tokenCount": 0,
                    "needsImage": True,
                    "imageFile": os.path.basename(png_path),
                    "ocrUnavailable": True,
                }
            return None

    _tsv_text, confidence = _parse_tesseract_tsv(tsv)
    token_count = _ocr_token_count(plain)
    math_symbol_count = _ocr_math_symbol_count(plain)
    needs_image = _ocr_needs_image(plain, confidence)
    result = {
        "text": plain,
        "confidence": confidence,
        "tokenCount": token_count,
        "mathSymbolCount": math_symbol_count,
        "needsImage": needs_image,
        "imageFile": os.path.basename(png_path),
    }
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False)
    return result


def _infer_file_language(rel_path: str) -> str:
    ext = os.path.splitext(rel_path)[1].lower()
    if ext in (".ts", ".mts", ".cts", ".tsx"):
        return "typescript"
    if ext in (".js", ".mjs", ".cjs", ".jsx"):
        return "javascript"
    if ext == ".py":
        return "python"
    if ext in (".md", ".markdown"):
        return "markdown"
    if ext == ".json":
        return "json"
    if ext == ".sql":
        return "sql"
    return "text"


def _infer_file_kind(rel_path: str) -> str:
    ext = os.path.splitext(rel_path)[1].lower()
    if ext in (".md", ".markdown"):
        return "markdown"
    if ext == ".json":
        return "json"
    return "code"


def split_code_or_markdown_pages(text: str, ext: str) -> list[dict[str, Any]]:
    """Split a code, JSON, or Markdown file into numbered chunks (``page: 1..N``) for indexing and budgeting."""
    lines = text.splitlines()
    if not lines:
        return [{"page": 1, "text": "", "isImagePage": True, "lineStart": 1, "lineEnd": 1}]
    if len(text) <= MAX_CHUNK_CHARS and len(lines) <= MAX_CHUNK_LINES:
        return [{"page": 1, "text": text, "isImagePage": False, "lineStart": 1, "lineEnd": len(lines)}]

    is_md = ext.lower() in (".md", ".markdown")
    chunks: list[dict[str, Any]] = []
    buf: list[str] = []
    buf_chars = 0
    start_line = 1

    def _flush(end_line: int) -> None:
        nonlocal buf, buf_chars
        if not buf:
            return
        chunk_text = "\n".join(buf)
        chunks.append(
            {
                "page": len(chunks) + 1,
                "text": chunk_text,
                "isImagePage": not chunk_text.strip(),
                "lineStart": start_line,
                "lineEnd": end_line,
            }
        )
        buf = []
        buf_chars = 0

    for idx, line in enumerate(lines, 1):
        at_boundary = (is_md and bool(_MD_HEADING_RE.match(line))) or (not is_md and not line.strip())
        would_exceed = (buf_chars + len(line) + 1 > MAX_CHUNK_CHARS) or (len(buf) >= MAX_CHUNK_LINES)
        if buf and (
            would_exceed or (at_boundary and (buf_chars >= MAX_CHUNK_CHARS // 2 or len(buf) >= MAX_CHUNK_LINES // 2))
        ):
            _flush(idx - 1)
            start_line = idx
        buf.append(line)
        buf_chars += len(line) + 1

    if buf:
        _flush(len(lines))

    return chunks


def _cache_filename(rel_path: str, prefix: str = "pdf") -> str:
    digest = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}.json"


def _load_or_extract_pdf(
    rel_path: str,
    abs_path: str,
    idx_dir: str,
    *,
    zip_member: str | None = None,
    use_cache: bool = True,
    registry_path: str | None = None,
) -> tuple[str, dict[str, Any]]:
    stat = os.stat(abs_path)
    cache_name = _cache_filename(rel_path, prefix="pdf")
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
                if not cached.get("fileHash"):
                    if zip_member is not None:
                        with zipfile.ZipFile(abs_path, "r") as archive:
                            cached["fileHash"] = hashlib.sha256(archive.read(zip_member)).hexdigest()
                    else:
                        cached["fileHash"] = compute_file_hash(abs_path)
                    with open(cache_path, "w", encoding="utf-8") as fh:
                        json.dump(cached, fh, ensure_ascii=False)
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
        "mode": family_mode(rel_path, registry_path=registry_path),
        "kind": "pdf",
        "mtime": stat.st_mtime,
        "size": stat.st_size,
        "fileHash": file_hash,
        "pages": pages,
    }
    os.makedirs(idx_dir, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
    return cache_name, doc


def _load_or_extract_code(
    rel_path: str,
    abs_path: str,
    idx_dir: str,
    *,
    use_cache: bool = True,
    registry_path: str | None = None,
) -> tuple[str, dict[str, Any]]:
    stat = os.stat(abs_path)
    cache_name = _cache_filename(rel_path, prefix="code")
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

    with open(abs_path, "rb") as fh:
        raw_bytes = fh.read()
    file_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    ext = os.path.splitext(rel_path)[1].lower()
    pages = split_code_or_markdown_pages(text, ext)

    doc: dict[str, Any] = {
        "relPath": rel_path,
        "family": family_root(rel_path),
        "mode": family_mode(rel_path, registry_path=registry_path),
        "kind": _infer_file_kind(rel_path),
        "language": _infer_file_language(rel_path),
        "mtime": stat.st_mtime,
        "size": stat.st_size,
        "fileHash": file_hash,
        "pages": pages,
    }
    lic = family_license(rel_path, registry_path=registry_path)
    if lic:
        doc["license"] = lic
    os.makedirs(idx_dir, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
    return cache_name, doc


def _family_matches_filter(rel: str, fam_filters: list[str]) -> bool:
    if not fam_filters:
        return True
    low = rel.replace("\\", "/").lower()
    root = family_root(rel)
    short = root.split("/", 1)[1] if root.startswith("prg/") else root
    return any(
        root == f or short == f or low.startswith(f + "/") or low == f or (f.startswith("prg/") and root == f)
        for f in fam_filters
    )


def _discover_source_pdfs(
    sources_dir: str,
    families: list[str] | None = None,
    *,
    registry_path: str | None = None,
) -> tuple[list[tuple[str, str, str | None]], list[str]]:
    """Return ``(pdfs, skipped_no_automation)`` under ``sources_dir``, skipping ``no-automation`` families."""
    fam_filters = [f.replace("\\", "/").strip("/").lower() for f in (families or []) if f.strip()]
    found: list[tuple[str, str, str | None]] = []
    skipped_no_auto: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(sources_dir):
        rel_dir = os.path.relpath(dirpath, sources_dir).replace("\\", "/")
        if rel_dir == ".":
            kept: list[str] = []
            for d in sorted(dirnames):
                if d.startswith("_") or d.startswith(".") or d.lower() == "prg":
                    continue
                if family_mode(d, registry_path=registry_path) == "no-automation":
                    skipped_no_auto.add(d.lower())
                    continue
                kept.append(d)
            dirnames[:] = kept
        else:
            kept = []
            for d in sorted(dirnames):
                if d.startswith("."):
                    continue
                sub_rel = f"{rel_dir}/{d}"
                if family_mode(sub_rel, registry_path=registry_path) == "no-automation":
                    skipped_no_auto.add(family_root(sub_rel))
                    continue
                kept.append(d)
            dirnames[:] = kept

        for fname in sorted(filenames):
            if fname.startswith("."):
                continue
            abs_file = os.path.join(dirpath, fname)
            rel_file = fname if rel_dir == "." else f"{rel_dir}/{fname}"
            if family_mode(rel_file, registry_path=registry_path) == "no-automation":
                skipped_no_auto.add(family_root(rel_file))
                continue
            low = fname.lower()
            if low.endswith(".pdf"):
                if _family_matches_filter(rel_file, fam_filters):
                    found.append((rel_file, abs_file, None))
            elif low.endswith(".zip"):
                if not _family_matches_filter(rel_file, fam_filters):
                    continue
                try:
                    with zipfile.ZipFile(abs_file, "r") as zf:
                        for member in sorted(zf.namelist()):
                            if member.startswith("__MACOSX/") or "/." in member or not member.lower().endswith(".pdf"):
                                continue
                            found.append((f"{rel_file}::{member}", abs_file, member))
                except (OSError, zipfile.BadZipFile):
                    continue
    return found, sorted(skipped_no_auto)


def _discover_source_code_files(
    sources_dir: str,
    families: list[str] | None = None,
    *,
    registry_path: str | None = None,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Return ``(files, skipped_no_automation)`` for code/markdown/json sources under ``sources/prg/<family>/``.

    ``NO-AUTOMATION`` families are pruned immediately and never walked or indexed.
    """
    prg_root = os.path.join(sources_dir, "prg")
    if not os.path.isdir(prg_root):
        return [], []

    fam_filters = [f.replace("\\", "/").strip("/").lower() for f in (families or []) if f.strip()]
    found: list[tuple[str, str]] = []
    skipped_no_auto: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(prg_root):
        rel_dir = os.path.relpath(dirpath, sources_dir).replace("\\", "/")
        if rel_dir == "prg":
            kept: list[str] = []
            for d in sorted(dirnames):
                if d.startswith("_") or d.startswith("."):
                    continue
                fam_key = f"prg/{d.lower()}"
                if family_mode(fam_key, registry_path=registry_path) == "no-automation":
                    skipped_no_auto.add(fam_key)
                    continue
                kept.append(d)
            dirnames[:] = kept
        else:
            dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_CODE_DIRS)

        for fname in sorted(filenames):
            if fname.startswith("."):
                continue
            low = fname.lower()
            if low in SKIP_CODE_FILENAMES or low.endswith((".min.js", ".bundle.js", ".min.css")):
                continue
            if not low.endswith(CODE_SOURCE_EXTENSIONS):
                continue
            abs_file = os.path.join(dirpath, fname)
            rel_file = f"{rel_dir}/{fname}"
            if family_mode(rel_file, registry_path=registry_path) == "no-automation":
                skipped_no_auto.add(family_root(rel_file))
                continue
            if not _family_matches_filter(rel_file, fam_filters):
                continue
            try:
                if os.path.getsize(abs_file) > MAX_CODE_FILE_BYTES:
                    continue
            except OSError:
                continue
            found.append((rel_file, abs_file))

    return found, sorted(skipped_no_auto)


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
    ocr: bool = True,
) -> dict[str, Any]:
    """Search PDFs (MTH/PHY) or code/markdown files under ``sources/prg/`` (PRG) and cache extracted text."""
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
    prg_mode = is_prg_unit(unit_code)

    core_matches: list[dict[str, Any]] = []
    scope_matches: list[dict[str, Any]] = []
    image_only_files: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    page_quality: Counter[str] = Counter()
    scanned_families: set[str] = set()
    ocr_retry: list[dict[str, Any]] = []

    if prg_mode:
        code_files, skipped_no_auto = _discover_source_code_files(sdir, families=families, registry_path=registry_path)
        scanned_count = len(code_files)
        pdfs_scanned = 0
        work_items: list[tuple[str, str, str | None]] = [(rel, absp, None) for rel, absp in code_files]
    else:
        pdfs, skipped_no_auto = _discover_source_pdfs(sdir, families=families, registry_path=registry_path)
        scanned_count = len(pdfs)
        pdfs_scanned = len(pdfs)
        work_items = pdfs

    for rel_path, abs_path, zip_member in work_items:
        try:
            if prg_mode:
                cache_name, doc = _load_or_extract_code(
                    rel_path,
                    abs_path,
                    idx_dir,
                    use_cache=use_cache,
                    registry_path=registry_path,
                )
            else:
                cache_name, doc = _load_or_extract_pdf(
                    rel_path,
                    abs_path,
                    idx_dir,
                    zip_member=zip_member,
                    use_cache=use_cache,
                    registry_path=registry_path,
                )
        except RuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001 - report unreadable file without aborting scan
            errors.append({"relPath": rel_path, "error": str(exc)})
            continue

        pages = doc.get("pages") or []
        fam = doc.get("family") or family_root(rel_path)
        mode = family_mode(rel_path, registry_path=registry_path)
        if mode == "no-automation":
            continue

        scanned_families.add(fam)
        matched_pages: list[dict[str, Any]] = []
        image_pages: list[int] = []
        has_any_text = False

        for p in pages:
            pnum = int(p.get("page", 0))
            text = str(p.get("text") or "")
            quality = classify_text_quality(text) if not prg_mode else ("empty" if not text.strip() else "ok")
            page_quality[quality] += 1
            ocr_result = None
            if not prg_mode and ocr and quality in {"empty", "garbled"} and mode != "no-automation":
                pdf_bytes = None
                if zip_member is not None:
                    with zipfile.ZipFile(abs_path, "r") as archive:
                        pdf_bytes = archive.read(zip_member)
                file_hash = str(doc.get("fileHash") or "")
                if file_hash:
                    ocr_result = _ocr_page(abs_path, pnum, file_hash, idx_dir, pdf_bytes=pdf_bytes)
                    if ocr_result and not ocr_result.get("ocrUnavailable"):
                        text = str(ocr_result.get("text") or "")
                        p["text"] = text
                        p["textSource"] = "ocr"
                        p["needsImage"] = bool(ocr_result.get("needsImage"))
                        p["imageFile"] = ocr_result.get("imageFile")
                        p["ocrConfidence"] = ocr_result.get("confidence")
                    elif ocr_result:
                        p["needsImage"] = True
                        p["imageFile"] = ocr_result.get("imageFile")
            if not prg_mode and mode != "scope" and quality in {"empty", "garbled"}:
                needs_retry = (
                    not ocr_result
                    or ocr_result.get("ocrUnavailable")
                    or ocr_result.get("needsImage")
                    or classify_text_quality(text) != "ok"
                )
                if needs_retry:
                    retry = {"relPath": rel_path, "page": pnum, "originalQuality": quality}
                    if ocr_result and ocr_result.get("imageFile"):
                        retry["imageFile"] = ocr_result["imageFile"]
                    ocr_retry.append(retry)
            text_source = str(p.get("textSource") or "pdf")
            if not text.strip():
                if not prg_mode:
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
                    "exerciseHeading": bool(_EXERCISE_HEADING_RE.search(text)),
                    "textSource": text_source,
                    "textQuality": quality,
                }
                if text_source == "ocr":
                    entry["needsImage"] = bool(p.get("needsImage"))
                    entry["imageFile"] = p.get("imageFile")
                    entry["ocrConfidence"] = p.get("ocrConfidence")
                elif quality == "garbled":
                    entry["needsImage"] = True
                    if p.get("imageFile"):
                        entry["imageFile"] = p["imageFile"]
                if p.get("lineStart") is not None and p.get("lineEnd") is not None:
                    entry["lineStart"] = int(p["lineStart"])
                    entry["lineEnd"] = int(p["lineEnd"])
                if mode == "scope":
                    low = text.lower()
                    entry["scopeSection"] = (
                        "toc/objectives" if any(k in low for k in _SCOPE_HINT_KEYWORDS) else "scope-only"
                    )
                matched_pages.append(entry)

        if matched_pages:
            record: dict[str, Any] = {
                "relPath": rel_path,
                "family": fam,
                "mode": mode,
                "cacheFile": cache_name,
                "totalHits": sum(p["hits"] for p in matched_pages),
                "pages": matched_pages,
                "imagePages": image_pages,
            }
            if doc.get("language"):
                record["language"] = doc["language"]
            if doc.get("kind"):
                record["kind"] = doc["kind"]
            if doc.get("license"):
                record["license"] = doc["license"]
            if isinstance(doc.get("fileHash"), str) and doc["fileHash"]:
                record["fileHash"] = doc["fileHash"]
            if mode == "scope":
                scope_matches.append(record)
            else:
                core_matches.append(record)
        elif not prg_mode and not has_any_text and image_pages:
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

    diagnostics = {
        "emptyPages": page_quality["empty"],
        "garbledPages": page_quality["garbled"],
        "sourceFamilyCount": len(scanned_families),
        "ocrRetry": sorted(ocr_retry, key=lambda item: (item["relPath"], item["page"])),
    }
    manifest = {
        "unitCode": unit_code,
        "track": "prg" if prg_mode else "math",
        "terms": search_terms,
        "matches": core_matches + scope_matches,
        "imageOnlyFiles": image_only_files,
        "diagnostics": diagnostics,
        "skippedNoAutomation": skipped_no_auto,
    }
    os.makedirs(idx_dir, exist_ok=True)
    manifest_path = os.path.join(idx_dir, f"located_{unit_code}.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    return {
        "unitCode": unit_code,
        "track": "prg" if prg_mode else "math",
        "sourcesDir": sdir,
        "manifestPath": manifest_path,
        "terms": search_terms,
        "pdfsScanned": pdfs_scanned,
        "filesScanned": scanned_count,
        "unregisteredSources": unregistered,
        "skippedNoAutomation": skipped_no_auto,
        "coreMatches": core_matches,
        "scopeMatches": scope_matches,
        "imageOnlyFiles": image_only_files,
        "diagnostics": diagnostics,
        "errors": errors,
        "ocrEnabled": ocr,
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
    if fam_low.startswith("prg/"):
        short = fam_low.split("/", 1)[1]
        if short in mapping:
            return mapping[short]
        compact_short = short.replace("-", "").replace("_", "")
        if compact_short in mapping:
            return mapping[compact_short]
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
    registry_path: str | None = None,
) -> tuple[float, dict[str, Any]]:
    """Compute ranking score and breakdown for one candidate page/chunk."""
    reg_prio = _longest_prefix_lookup(rel_path, family, registry_priorities)
    backlog_rank = _longest_prefix_lookup(rel_path, family, backlog_ranks)

    if reg_prio is not None:
        base_priority = int(reg_prio)
    elif family.lower() in SOURCE_FAMILIES:
        base_priority = family_priority(rel_path, registry_path=registry_path)
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
    exercise_boost = 15.0 if page_entry.get("exerciseHeading") else 0.0
    exercise_boost += 3.0 * min(5, max(0, int(page_entry.get("estimatedItems") or 1) - 1))
    total_score = round(base_priority + backlog_bonus + density_score + thai_boost + exercise_boost, 2)

    breakdown = {
        "familyPriority": base_priority,
        "backlogRank": backlog_rank,
        "backlogBonus": backlog_bonus,
        "termDensity": round(density, 4),
        "densityScore": density_score,
        "thaiExamBoost": thai_boost,
        "exerciseBoost": exercise_boost,
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


def _continuation_page_key(page: dict[str, Any], fingerprint: str) -> tuple[str, int, str, str]:
    return (page["relPath"], page["page"], page["fileHash"], fingerprint)


def _load_plan_continuation(plan_file: str, *, include_answer_keys: bool) -> dict[str, Any]:
    try:
        with open(plan_file, encoding="utf-8") as fh:
            previous = json.load(fh)
    except (OSError, ValueError):
        return {}
    if not isinstance(previous, dict) or previous.get("summary", {}).get("includeAnswerKeys") != include_answer_keys:
        return {}
    continuation = previous.get("continuation")
    return continuation if isinstance(continuation, dict) else {}


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
    include_answer_keys: bool = False,
) -> dict[str, Any]:
    """Rank and select a bounded, diverse set of candidate pages/chunks and write ``plan_<UNIT>.json``.

    Ranking combines:
    (a) family priority from ``docs/sources.md`` + ``SOURCE_FAMILIES`` + ``docs/source_backlog.md``,
    (b) term-hit density,
    (c) Thai-exam relevance boost (SmartMathPro, thai-exams), and
    (d) round-robin diversity across families so one family cannot fill the budget.

    Scope-only (OpenStax) and ``NO-AUTOMATION`` families are always skipped. Pages already
    present in ``sources/_cores/_ledger.json`` with matching file and card-schema fingerprints are excluded unless
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
    plan_file = os.path.join(idx_dir, f"plan_{unit_code}.json")
    prior = {} if refresh else _load_plan_continuation(plan_file, include_answer_keys=include_answer_keys)
    fingerprint = card_schema_fingerprint(unit_code)
    prior_pages = {
        tuple(key)
        for key in prior.get("plannedPages", [])
        if isinstance(key, list) and len(key) == 4 and key[3] == fingerprint
    }

    registry_priorities = load_registry_priorities(registry_path=registry_path)
    backlog_ranks = load_backlog_ranks(backlog_path=backlog_path, unit_code=unit_code)
    ledger = load_ledger(sources_dir=sdir)

    skipped_scope_pages = sum(len(m.get("pages") or []) for m in (find_result.get("scopeMatches") or []))
    skipped_no_auto = set(find_result.get("skippedNoAutomation") or [])
    skipped_ledger_pages = 0
    skipped_planned_pages = 0
    hash_cache: dict[str, str] = {}

    by_family: dict[str, list[dict[str, Any]]] = {}
    answer_key_pages: list[dict[str, Any]] = []
    skipped_answer_key_pages = 0
    candidates_by_family: Counter[str] = Counter()

    for match in find_result.get("coreMatches") or []:
        rel_path = str(match.get("relPath") or "")
        fam = str(match.get("family") or family_root(rel_path))
        mode = str(match.get("mode") or family_mode(rel_path, registry_path=registry_path))
        reg_mode = family_mode(rel_path, registry_path=registry_path)
        if mode == "scope" or reg_mode == "scope":
            skipped_scope_pages += len(match.get("pages") or [])
            continue
        if mode == "no-automation" or reg_mode == "no-automation":
            skipped_no_auto.add(fam)
            continue

        file_hash = _resolve_candidate_hash(sdir, idx_dir, match, hash_cache)
        cache_file = str(match.get("cacheFile") or "")
        lic = match.get("license") or family_license(rel_path, registry_path=registry_path)

        is_answer_key = _is_answer_key_path(rel_path)

        for p_entry in match.get("pages") or []:
            pnum = int(p_entry["page"])
            if is_answer_key:
                answer_key_pages.append(
                    {
                        "family": fam,
                        "relPath": rel_path,
                        "page": pnum,
                        "cacheFile": cache_file,
                        "hits": int(p_entry.get("hits") or 0),
                    }
                )
                if not include_answer_keys:
                    skipped_answer_key_pages += 1
                    continue
            if not refresh and is_page_extracted(
                ledger,
                unit_code,
                rel_path,
                pnum,
                current_file_hash=file_hash,
                current_schema_fingerprint=fingerprint,
            ):
                skipped_ledger_pages += 1
                continue

            if (rel_path, pnum, file_hash, fingerprint) in prior_pages:
                skipped_planned_pages += 1
                continue

            score, breakdown = _score_candidate_page(
                rel_path,
                fam,
                p_entry,
                registry_priorities=registry_priorities,
                backlog_ranks=backlog_ranks,
                registry_path=registry_path,
            )
            est_items = max(1, int(p_entry.get("estimatedItems") or 1))
            candidate: dict[str, Any] = {
                "family": fam,
                "mode": reg_mode,
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
            for key in ("textSource", "needsImage", "imageFile", "ocrConfidence"):
                if key in p_entry:
                    candidate[key] = p_entry[key]
            if p_entry.get("textSource") == "ocr":
                ocr_name = str(p_entry.get("imageFile") or "").replace(".png", ".json")
                ocr_path = os.path.join(idx_dir, ocr_name)
                try:
                    with open(ocr_path, "r", encoding="utf-8") as fh:
                        candidate["ocrText"] = json.load(fh).get("text", "")
                except (OSError, ValueError):
                    candidate["ocrText"] = ""
            if lic:
                candidate["license"] = lic
            if match.get("language"):
                candidate["language"] = match["language"]
            if p_entry.get("lineStart") is not None and p_entry.get("lineEnd") is not None:
                candidate["lineStart"] = int(p_entry["lineStart"])
                candidate["lineEnd"] = int(p_entry["lineEnd"])
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
    stop_family = prior.get("stopAfter", {}).get("family") if prior_pages else None
    if stop_family in family_order:
        next_idx = family_order.index(stop_family) + 1
        family_order = family_order[next_idx:] + family_order[:next_idx]

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

    if not include_answer_keys:
        for candidate in selected:
            pair_key = _answer_pair_key(candidate["relPath"])
            matches = [
                answer
                for answer in answer_key_pages
                if answer["family"] == candidate["family"] and _answer_pair_key(answer["relPath"]) == pair_key
            ]
            if matches:
                same_page = [match for match in matches if match["page"] == candidate["page"]]
                candidate["answerKeyPages"] = sorted(same_page or matches, key=lambda p: (p["page"], p["relPath"]))

    pages_by_family = dict(sorted(Counter(c["family"] for c in selected).items()))
    total_candidates = sum(candidates_by_family.values())

    os.makedirs(idx_dir, exist_ok=True)
    continuation = None
    has_unplanned_pages = len(selected) < total_candidates
    stopped_at_item_cap = bool(selected) and has_unplanned_pages and cumulative_items == budget_items
    if prior_pages or stopped_at_item_cap:
        stop_after = prior.get("stopAfter")
        if selected:
            stop_after = {key: selected[-1][key] for key in ("family", "relPath", "page")}
        continuation = {
            "stopAfter": stop_after,
            "plannedPages": sorted(prior_pages | {_continuation_page_key(page, fingerprint) for page in selected}),
            "exhausted": not has_unplanned_pages,
        }

    plan: dict[str, Any] = {
        "unitCode": unit_code,
        "track": "prg" if is_prg_unit(unit_code) else "math",
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
            "skippedPlannedPages": skipped_planned_pages,
            "skippedScopePages": skipped_scope_pages,
            "skippedAnswerKeyPages": skipped_answer_key_pages,
            "includeAnswerKeys": include_answer_keys,
            "skippedNoAutomationFamilies": sorted(skipped_no_auto),
            "selectedPageCount": len(selected),
            "selectedEstimatedItems": cumulative_items,
            "batchCount": len(batches),
            "pagesByFamily": pages_by_family,
            "candidatesByFamily": dict(sorted(candidates_by_family.items())),
        },
        "unregisteredSources": list(find_result.get("unregisteredSources") or []),
        "continuation": continuation,
        "diagnostics": find_result.get(
            "diagnostics",
            {
                "emptyPages": 0,
                "garbledPages": 0,
                "sourceFamilyCount": len(candidates_by_family),
                "ocrRetry": [],
            },
        ),
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
    is_prg = result.get("track") == "prg" or is_prg_unit(str(result.get("unitCode") or ""))
    scanned = result.get("filesScanned", result.get("pdfsScanned", 0))
    unit_label = "code/doc file(s)" if is_prg else "PDF(s)"
    lines = [
        f"Source find for {result['unitCode']} ({scanned} {unit_label} scanned)",
        f"Terms: {', '.join(result['terms'])}",
        f"Sources dir: {result['sourcesDir']}",
    ]

    skipped_no_auto = result.get("skippedNoAutomation") or []
    if skipped_no_auto:
        lines.append(f"Skipped NO-AUTOMATION families (never indexed automatically): {', '.join(skipped_no_auto)}")

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
    lines.append(f"Mining targets (cores/reuse): {len(core_matches)} file(s)")
    if not core_matches:
        lines.append("  (none)")
    for item in core_matches:
        tag = item.get("mode") or "cores"
        lines.append(f"  [{tag}:{item['family']}] {item['relPath']} ({item['totalHits']} hits)")
        for p in item["pages"]:
            breakdown = ", ".join(f"{t}={n}" for t, n in sorted(p["terms"].items()))
            span = f" (L{p['lineStart']}-L{p['lineEnd']})" if p.get("lineStart") and p.get("lineEnd") else ""
            lines.append(f"    - p.{p['page']}{span}: {p['hits']} hit(s) ({breakdown})")
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
        lines.append(f"Unreadable files ({len(errors)}):")
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
        f"{s['skippedScopePages']} skipped (scope-only), "
        f"{s.get('skippedAnswerKeyPages', 0)} skipped (answer-key primary targets)",
        f"Selected: {s['selectedPageCount']} page(s), ~{s['selectedEstimatedItems']} item(s) "
        f"in {s['batchCount']} batch(es)",
    ]

    if s.get("skippedPlannedPages"):
        lines.append(f"Continued past {s['skippedPlannedPages']} previously planned page(s)")
    continuation = plan.get("continuation") or {}
    if continuation.get("exhausted"):
        lines.append("Continuation exhausted. Use --refresh to restart planning.")
    elif stop := continuation.get("stopAfter"):
        lines.append(f"Next --plan continues after {stop['relPath']} page/chunk {stop['page']}")
    diagnostics = plan.get("diagnostics", {})
    retry = diagnostics.get("ocrRetry", [])
    lines.append(
        f"Source scan: {diagnostics.get('sourceFamilyCount', 0)} families, "
        f"{diagnostics.get('emptyPages', 0)} empty and {diagnostics.get('garbledPages', 0)} garbled "
        f"pages/chunks before OCR. OCR retry: {len(retry)} page(s)."
    )
    for item in retry[:10]:
        lines.append(f"  - {item['relPath']} page {item['page']} ({item['originalQuality']})")
    if len(retry) > 10:
        lines.append(f"  See diagnostics.ocrRetry in the plan JSON for all {len(retry)} pages.")

    skipped_no_auto = s.get("skippedNoAutomationFamilies") or []
    if skipped_no_auto:
        lines.append(f"Skipped NO-AUTOMATION families: {', '.join(skipped_no_auto)}")

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
                mode_tag = f" {p['mode']}" if p.get("mode") else ""
                lines.append(
                    f"    #{p['rank']:02d} [{p['family']}{mode_tag}] {p['relPath']} p.{p['page']} "
                    f"(score={p['score']}, hits={p['hits']}, items<={p['itemAllowance']})"
                )
                for answer in p.get("answerKeyPages") or []:
                    lines.append(
                        f"      ↳ answer key: {answer['relPath']} p.{answer['page']} (consult for trap confirmation)"
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
        description="Locate candidate source PDF pages (MTH/PHY) or code/markdown files (PRG) with caching and budgeted planning.",
    )
    parser.add_argument("unit", help="Target unit code (e.g. MTH-T02-C01-U01 or PRG-T01-C01-U02).")
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
        help="Filter to specific source families or subpaths (e.g. mathsgenie,thai-exams or prg/eslint).",
    )
    parser.add_argument(
        "--sources-dir",
        default=None,
        help="Override sources directory (default: LEARNINGOS_SOURCES_DIR or <main>/sources).",
    )
    parser.add_argument("--no-cache", action="store_true", help="Re-extract files instead of reading sources/_index/.")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR fallback for empty or garbled PDF pages.")
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Rank and select bounded, diverse candidate pages/files and write sources/_index/plan_<UNIT>.json.",
    )
    parser.add_argument(
        "--budget-pages",
        type=int,
        default=DEFAULT_BUDGET_PAGES,
        help=f"Max pages/chunks to select when --plan is set (default: {DEFAULT_BUDGET_PAGES}).",
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
        help=f"Pages/chunks per worker batch in plan_<UNIT>.json (default: {DEFAULT_BATCH_SIZE}).",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Include pages/chunks already recorded in sources/_cores/_ledger.json when building --plan.",
    )
    parser.add_argument(
        "--include-answer-keys",
        action="store_true",
        help="Allow answer-key pages/files to be selected as primary mining targets in --plan.",
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
            ocr=not args.no_ocr,
        )
        if args.plan:
            plan = build_extraction_plan(
                result,
                budget_pages=args.budget_pages,
                budget_items=args.budget_items,
                batch_size=args.batch_size,
                refresh=args.refresh,
                sources_dir=args.sources_dir,
                include_answer_keys=args.include_answer_keys,
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
