# -*- coding: utf-8 -*-
"""Incremental extraction ledger for source core cards.

Tracks per ``(unitCode, file, page)`` when a source page was extracted, by which run,
which core cards it produced, and the source file's SHA-256 content hash. Stored at
``sources/_cores/_ledger.json`` (gitignored).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from typing import Any, Iterable

from math_engine.source_cores import resolve_sources_dir

LEDGER_FILENAME = "_ledger.json"
LEDGER_VERSION = 1


def ledger_path(sources_dir: str | None = None) -> str:
    """Return ``<sources_dir>/_cores/_ledger.json``."""
    return os.path.join(resolve_sources_dir(sources_dir=sources_dir), "_cores", LEDGER_FILENAME)


def normalize_rel_path(rel_path: str) -> str:
    """Normalize a relative source path to POSIX separators."""
    return rel_path.replace("\\", "/").strip("/")


def ledger_key(unit_code: str, rel_path: str, page: int | str) -> str:
    """Build a canonical ledger lookup key for ``(unit_code, rel_path, page)``."""
    return f"{unit_code.strip()}::{normalize_rel_path(rel_path)}::{str(page).strip()}"


def compute_file_hash(abs_path: str, zip_member: str | None = None) -> str:
    """Return SHA-256 hex digest for ``abs_path`` (or a PDF member inside a zip archive)."""
    hasher = hashlib.sha256()
    if zip_member is not None:
        with zipfile.ZipFile(abs_path, "r") as zf:
            hasher.update(zf.read(zip_member))
        return hasher.hexdigest()
    with open(abs_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_relpath_hash(sources_dir: str, rel_path: str) -> str | None:
    """Compute SHA-256 for a source ``rel_path`` (supporting ``archive.zip::member.pdf``).

    Returns ``None`` if the underlying file does not exist on disk.
    """
    norm = normalize_rel_path(rel_path)
    if "::" in norm:
        zip_rel, member = norm.split("::", 1)
        abs_zip = os.path.join(sources_dir, zip_rel)
        if not os.path.isfile(abs_zip):
            return None
        try:
            return compute_file_hash(abs_zip, zip_member=member)
        except (OSError, KeyError, zipfile.BadZipFile):
            return None
    abs_file = os.path.join(sources_dir, norm)
    if not os.path.isfile(abs_file):
        return None
    try:
        return compute_file_hash(abs_file)
    except OSError:
        return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_ledger(sources_dir: str | None = None) -> dict[str, Any]:
    """Load ``sources/_cores/_ledger.json`` (returns an empty ledger if absent)."""
    path = ledger_path(sources_dir=sources_dir)
    if not os.path.isfile(path):
        return {"version": LEDGER_VERSION, "entries": {}}
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        return {"version": LEDGER_VERSION, "entries": {}}
    entries = raw.get("entries")
    if not isinstance(entries, dict):
        entries = {}
    return {"version": int(raw.get("version") or LEDGER_VERSION), "entries": dict(entries)}


def save_ledger(ledger: dict[str, Any], sources_dir: str | None = None) -> str:
    """Atomically write ``ledger`` to ``sources/_cores/_ledger.json``."""
    path = ledger_path(sources_dir=sources_dir)
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)
    payload = {
        "version": int(ledger.get("version") or LEDGER_VERSION),
        "entries": dict(sorted((ledger.get("entries") or {}).items())),
    }
    fd, tmp_path = tempfile.mkstemp(prefix=".ledger_", suffix=".json", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return path


def get_ledger_entry(
    ledger: dict[str, Any],
    unit_code: str,
    rel_path: str,
    page: int | str,
) -> dict[str, Any] | None:
    """Return the ledger entry for ``(unit_code, rel_path, page)`` if present."""
    entries = ledger.get("entries")
    if not isinstance(entries, dict):
        return None
    entry = entries.get(ledger_key(unit_code, rel_path, page))
    return entry if isinstance(entry, dict) else None


def is_page_extracted(
    ledger: dict[str, Any],
    unit_code: str,
    rel_path: str,
    page: int | str,
    *,
    current_file_hash: str | None = None,
) -> bool:
    """Return True if ``(unit_code, rel_path, page)`` is recorded and its file hash still matches.

    If ``current_file_hash`` is provided and differs from the recorded ``fileHash`` (or the entry
    lacks a hash), returns False so the modified file will be re-extracted.
    """
    entry = get_ledger_entry(ledger, unit_code, rel_path, page)
    if entry is None:
        return False
    if current_file_hash:
        recorded_hash = entry.get("fileHash")
        if not isinstance(recorded_hash, str) or recorded_hash != current_file_hash:
            return False
    return True


def record_extraction(
    unit_code: str,
    rel_path: str,
    page: int | str,
    *,
    run_id: str,
    cards_produced: Iterable[str],
    file_hash: str,
    extracted_at: str | None = None,
    sources_dir: str | None = None,
) -> dict[str, Any]:
    """Record one extracted ``(unit_code, rel_path, page)`` in the ledger and save it."""
    ledger = load_ledger(sources_dir=sources_dir)
    norm_file = normalize_rel_path(rel_path)
    card_ids = [str(c).strip() for c in cards_produced if str(c).strip()]
    entry: dict[str, Any] = {
        "unitCode": unit_code.strip(),
        "file": norm_file,
        "page": int(page) if isinstance(page, int) or (isinstance(page, str) and page.isdigit()) else str(page),
        "extractedAt": extracted_at or _utc_now_iso(),
        "runId": run_id.strip(),
        "cardsProduced": card_ids,
        "cardCount": len(card_ids),
        "fileHash": file_hash,
    }
    ledger["entries"][ledger_key(unit_code, norm_file, page)] = entry
    save_ledger(ledger, sources_dir=sources_dir)
    return entry


def record_batch_extractions(
    unit_code: str,
    page_records: Iterable[dict[str, Any]],
    *,
    run_id: str,
    extracted_at: str | None = None,
    sources_dir: str | None = None,
) -> list[dict[str, Any]]:
    """Record multiple extracted pages for ``unit_code`` in one atomic ledger save.

    Each item in ``page_records`` should provide ``file`` (or ``relPath``), ``page``,
    ``fileHash``, and optional ``cardsProduced`` (list of card IDs).
    """
    ledger = load_ledger(sources_dir=sources_dir)
    ts = extracted_at or _utc_now_iso()
    written: list[dict[str, Any]] = []
    for rec in page_records:
        raw_file = rec.get("file") or rec.get("relPath") or ""
        norm_file = normalize_rel_path(str(raw_file))
        page = rec.get("page")
        if not norm_file or page is None:
            continue
        card_ids = [str(c).strip() for c in (rec.get("cardsProduced") or []) if str(c).strip()]
        entry: dict[str, Any] = {
            "unitCode": unit_code.strip(),
            "file": norm_file,
            "page": int(page) if isinstance(page, int) or (isinstance(page, str) and page.isdigit()) else str(page),
            "extractedAt": ts,
            "runId": run_id.strip(),
            "cardsProduced": card_ids,
            "cardCount": len(card_ids),
            "fileHash": str(rec.get("fileHash") or ""),
        }
        ledger["entries"][ledger_key(unit_code, norm_file, page)] = entry
        written.append(entry)
    save_ledger(ledger, sources_dir=sources_dir)
    return written
