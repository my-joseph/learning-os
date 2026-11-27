# -*- coding: utf-8 -*-
"""Incremental extraction ledger for source core cards.

Tracks per ``(unitCode, file, page)`` when a source page was extracted, by which run,
which core cards it produced, and the source file's SHA-256 content hash. Stored at
``sources/_cores/_ledger.json`` (gitignored).
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from math_engine.source_cores import PRG_SCHEMA_PATH, REPO_ROOT, SCHEMA_PATH, is_prg_unit, resolve_sources_dir

LEDGER_FILENAME = "_ledger.json"
LEDGER_VERSION = 1
# Bump for extraction-relevant changes to validate_core_card alone.
CARD_RULES_VERSION = "1"
EXTRACTION_PROMPT_PATH = Path(REPO_ROOT) / "scripts" / "extract_cards_job.py"

_SCHEMA_DOC_KEYS = {"$schema", "$id", "title", "description", "$comment", "examples"}
_SCHEMA_MAP_KEYS = {"properties", "patternProperties", "$defs", "definitions", "dependentSchemas"}
_SCHEMA_LIST_KEYS = {"allOf", "anyOf", "oneOf", "prefixItems"}
_SCHEMA_CHILD_KEYS = {
    "additionalProperties",
    "unevaluatedProperties",
    "propertyNames",
    "items",
    "contains",
    "unevaluatedItems",
    "not",
    "if",
    "then",
    "else",
    "additionalItems",
    "contentSchema",
}


def _structural_schema(schema: Any) -> Any:
    """Skip annotations at schema nodes while preserving property names and literal values."""
    if not isinstance(schema, dict):
        return schema
    result = {}
    for key, value in schema.items():
        if key in _SCHEMA_DOC_KEYS:
            continue
        if key in _SCHEMA_MAP_KEYS:
            value = {name: _structural_schema(child) for name, child in value.items()}
        elif key in _SCHEMA_LIST_KEYS or (key == "items" and isinstance(value, list)):
            value = [_structural_schema(child) for child in value]
        elif key in _SCHEMA_CHILD_KEYS:
            value = _structural_schema(value)
        result[key] = value
    return result


def card_schema_fingerprint(unit_code: str) -> str:
    """Hash the active schema structure, prompt template, and validator rules version."""
    schema_path = PRG_SCHEMA_PATH if is_prg_unit(unit_code) else SCHEMA_PATH
    schema = _structural_schema(json.loads(Path(schema_path).read_text(encoding="utf-8")))
    prompt_module = ast.parse(EXTRACTION_PROMPT_PATH.read_text(encoding="utf-8"))
    template = next(
        node for node in prompt_module.body if isinstance(node, ast.FunctionDef) and node.name == "build_worker_prompt"
    )
    payload = json.dumps([schema, ast.dump(template), CARD_RULES_VERSION], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
    current_schema_fingerprint: str | None = None,
) -> bool:
    """Check that the recorded file hash and extraction contract still match."""
    entry = get_ledger_entry(ledger, unit_code, rel_path, page)
    if entry is None or not current_file_hash:
        return False
    fingerprint = current_schema_fingerprint or card_schema_fingerprint(unit_code)
    return entry.get("fileHash") == current_file_hash and entry.get("schemaFingerprint") == fingerprint


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
        "schemaFingerprint": card_schema_fingerprint(unit_code),
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
    fingerprint = card_schema_fingerprint(unit_code)
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
            "schemaFingerprint": fingerprint,
        }
        ledger["entries"][ledger_key(unit_code, norm_file, page)] = entry
        written.append(entry)
    save_ledger(ledger, sources_dir=sources_dir)
    return written
