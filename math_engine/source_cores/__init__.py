# -*- coding: utf-8 -*-
"""Source-core card schema validation, storage, and local sources directory resolution.

Raw study materials live under ``sources/`` in the main checkout (gitignored; override with
``LEARNINGOS_SOURCES_DIR``). Core cards are stored as JSONL in ``sources/_cores/<UNIT>.jsonl``
and hold only abstract, source-free problem structures — never source wording or numbers.
"""

from __future__ import annotations

import json
import os
import re
import warnings
from typing import Any, Iterable

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(PACKAGE_DIR))
ID_MAP_PATH = os.path.join(REPO_ROOT, "id_map.json")
SCHEMA_PATH = os.path.join(PACKAGE_DIR, "schema.json")
UNIT_TERMS_PATH = os.path.join(PACKAGE_DIR, "unit_terms.json")

MAX_FIELD_LENGTH = 200
WORD_SHINGLE_SIZE = 6
UNMAPPED_PREFIX = "UNMAPPED:"
_UNIT_OR_CHAPTER_RE = re.compile(r"^(?:MTH|PHY|PRG)-T\d+-C\d+(?:-U\d+)?$")
_VALID_CODES_CACHE: dict[tuple[str, float], dict[str, str]] = {}

REASONING_MOVES: tuple[str, ...] = (
    "direct",
    "reverse",
    "translate",
    "diagnose",
    "multi-relation",
    "case-check",
    "generalise",
    "model",
)
FORMAT_KINDS: tuple[str, ...] = ("choice", "numeric", "expression", "proof-lite")
REPRESENTATIONS: tuple[str, ...] = ("symbolic", "graph/plane", "table", "verbal")

SOURCE_FAMILIES: dict[str, dict[str, str]] = {
    "openstax": {"mode": "scope", "label": "OpenStax textbooks (TOC & learning objectives only)"},
    "mathsgenie": {"mode": "cores", "label": "MathsGenie GCSE worksheets & exam questions"},
    "thai-exams": {"mode": "cores", "label": "Thai O-NET & TCAS A-Level exams"},
    "illustrative-math": {"mode": "cores", "label": "Illustrative Mathematics"},
}

_REQUIRED_TOP_KEYS: tuple[str, ...] = (
    "id",
    "unitCode",
    "sourceRef",
    "skill",
    "reasoningMove",
    "difficultyDriver",
    "level",
    "traps",
    "format",
    "representation",
)
_ALLOWED_TOP_KEYS: frozenset[str] = frozenset((*_REQUIRED_TOP_KEYS, "laterUnit", "notes", "units"))
_ALLOWED_SOURCE_REF_KEYS: frozenset[str] = frozenset(("family", "file", "page", "item"))
_ALLOWED_TRAP_KEYS: frozenset[str] = frozenset(("tag", "description"))
_ALLOWED_FORMAT_KEYS: frozenset[str] = frozenset(("kind", "optionCount", "distractorPatterns"))

_DIGIT_RUN_RE = re.compile(r"(?<![A-Za-z_])\d+(?:\.\d+)?")
_WORD_TOKEN_RE = re.compile(r"[a-z0-9]+|[\u0e00-\u0e7f]+")


class CoreCardError(ValueError):
    """Raised when a source core card violates schema or source-free invariants."""


def main_checkout_root(cwd: str = ".") -> str:
    """Return the main checkout root, resolving git worktrees via their ``.git`` file."""
    root = os.path.abspath(cwd)
    git_path = os.path.join(root, ".git")
    if os.path.isfile(git_path):
        try:
            with open(git_path, "r", encoding="utf-8") as fh:
                text = fh.read().strip()
        except OSError:
            return root
        if text.startswith("gitdir:"):
            gitdir = os.path.abspath(os.path.join(root, text.split(":", 1)[1].strip()))
            worktrees_dir = os.path.dirname(gitdir)
            if os.path.basename(worktrees_dir) == "worktrees":
                return os.path.dirname(os.path.dirname(worktrees_dir))
    return root


def resolve_sources_dir(cwd: str = ".", sources_dir: str | None = None) -> str:
    """Resolve the local ``sources/`` directory.

    Priority: explicit ``sources_dir`` > ``LEARNINGOS_SOURCES_DIR`` env var > ``<main checkout>/sources``.
    """
    if sources_dir:
        return os.path.abspath(sources_dir)
    env_dir = os.environ.get("LEARNINGOS_SOURCES_DIR")
    if env_dir and env_dir.strip():
        return os.path.abspath(env_dir.strip())
    return os.path.join(main_checkout_root(cwd), "sources")


def cores_path(unit_code: str, sources_dir: str | None = None) -> str:
    """Return ``<sources_dir>/_cores/<unit_code>.jsonl``."""
    return os.path.join(resolve_sources_dir(sources_dir=sources_dir), "_cores", f"{unit_code}.jsonl")


def index_dir(sources_dir: str | None = None) -> str:
    """Return ``<sources_dir>/_index``."""
    return os.path.join(resolve_sources_dir(sources_dir=sources_dir), "_index")


def family_root(family_or_relpath: str) -> str:
    """Return the top-level family segment (normalized to lowercase POSIX)."""
    norm = family_or_relpath.replace("\\", "/").strip("/")
    return norm.split("/", 1)[0].lower() if norm else ""


def family_mode(family_or_relpath: str) -> str:
    """Return ``'scope'`` for scope-only families (OpenStax), else ``'cores'``."""
    root = family_root(family_or_relpath)
    meta = SOURCE_FAMILIES.get(root)
    if meta:
        return meta["mode"]
    return "scope" if root.startswith("openstax") else "cores"


def load_schema() -> dict[str, Any]:
    """Load the core-card JSON Schema from ``math_engine/source_cores/schema.json``."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_unit_terms_map(path: str | None = None) -> dict[str, dict[str, Any]]:
    """Load the per-unit search-terms map from ``unit_terms.json``."""
    target = path or UNIT_TERMS_PATH
    with open(target, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_unit_terms(unit_code: str, path: str | None = None) -> list[str]:
    """Return seeded search terms for ``unit_code`` (or merged child units for a chapter code)."""
    data = load_unit_terms_map(path=path)
    if unit_code in data:
        return list(data[unit_code].get("terms") or [])
    merged: list[str] = []
    prefix = f"{unit_code}-U"
    for code, entry in sorted(data.items()):
        if code.startswith(prefix):
            for term in entry.get("terms") or []:
                if term not in merged:
                    merged.append(term)
    return merged


def _normalize_digit_run(token: str) -> str:
    if "." in token:
        whole, frac = token.split(".", 1)
        whole = whole.lstrip("0") or "0"
        frac = frac.rstrip("0")
        return f"{whole}.{frac}" if frac else whole
    return token.lstrip("0") or "0"


def extract_digit_runs(text: str) -> list[str]:
    """Extract normalized numeric digit runs from ``text`` (ignoring identifier suffixes like ``t02``)."""
    return [_normalize_digit_run(m.group(0)) for m in _DIGIT_RUN_RE.finditer(text or "")]


def _word_shingles(text: str, size: int = WORD_SHINGLE_SIZE) -> set[tuple[str, ...]]:
    tokens = _WORD_TOKEN_RE.findall((text or "").lower())
    if len(tokens) < size:
        return set()
    return {tuple(tokens[i : i + size]) for i in range(len(tokens) - size + 1)}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _walk_strings(obj: Any, prefix: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(obj, str):
        yield prefix, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            yield from _walk_strings(v, path)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            yield from _walk_strings(item, f"{prefix}[{idx}]")


def _content_string_fields(card: dict[str, Any]) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    for key in ("skill", "difficultyDriver", "notes"):
        val = card.get(key)
        if isinstance(val, str):
            fields.append((key, val))
    for idx, trap in enumerate(card.get("traps") or []):
        if isinstance(trap, dict):
            for sub in ("tag", "description"):
                val = trap.get(sub)
                if isinstance(val, str):
                    fields.append((f"traps[{idx}].{sub}", val))
    fmt = card.get("format")
    if isinstance(fmt, dict):
        for idx, pat in enumerate(fmt.get("distractorPatterns") or []):
            if isinstance(pat, str):
                fields.append((f"format.distractorPatterns[{idx}]", pat))
    return fields


def load_valid_unit_codes(id_map_path: str | None = None) -> dict[str, str]:
    """Return ``{code: title}`` for every unit/chapter code registered in ``id_map.json``."""
    target = os.path.abspath(id_map_path or ID_MAP_PATH)
    if not os.path.isfile(target):
        return {}
    mtime = os.path.getmtime(target)
    cache_key = (target, mtime)
    cached = _VALID_CODES_CACHE.get(cache_key)
    if cached is not None:
        return dict(cached)
    with open(target, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    codes: dict[str, str] = {}
    if isinstance(raw, dict):
        for key, entry in raw.items():
            if not isinstance(key, str) or not _UNIT_OR_CHAPTER_RE.match(key):
                continue
            title = entry.get("title", "") if isinstance(entry, dict) else ""
            codes[key] = str(title or "")
    _VALID_CODES_CACHE[cache_key] = codes
    return dict(codes)


def validate_core_card(
    card: Any,
    source_item_text: str | None = None,
    valid_unit_codes: Iterable[str] | None = None,
) -> list[str]:
    """Validate a core card against ``schema.json`` and source-free invariants.

    Returns a list of error strings (empty list means valid).
    """
    errors: list[str] = []
    if not isinstance(card, dict):
        return ["Card must be a JSON object."]

    unknown_top = sorted(set(card) - _ALLOWED_TOP_KEYS)
    if unknown_top:
        errors.append(f"Unknown top-level field(s): {unknown_top}.")

    for req in _REQUIRED_TOP_KEYS:
        if req not in card:
            errors.append(f"Missing required field '{req}'.")

    # Enforce 200-char limit across every string field in the card.
    for path, text in _walk_strings(card):
        if len(text) > MAX_FIELD_LENGTH:
            errors.append(f"{path}: exceeds {MAX_FIELD_LENGTH}-char limit ({len(text)} chars).")

    for key in ("id", "unitCode", "skill", "difficultyDriver"):
        if key in card and (not isinstance(card[key], str) or not card[key].strip()):
            errors.append(f"{key}: must be a non-empty string.")

    if "laterUnit" in card and card["laterUnit"] is not None:
        if not isinstance(card["laterUnit"], str) or not card["laterUnit"].strip():
            errors.append("laterUnit: must be a non-empty string or null.")
        else:
            later = card["laterUnit"].strip()
            if later.startswith(UNMAPPED_PREFIX):
                if not later[len(UNMAPPED_PREFIX) :].strip():
                    errors.append("laterUnit: 'UNMAPPED:' prefix must be followed by a non-empty label.")
            else:
                known_codes = (
                    {str(c).strip() for c in valid_unit_codes if isinstance(c, str) and c.strip()}
                    if valid_unit_codes is not None
                    else set(load_valid_unit_codes())
                )
                if known_codes and later not in known_codes:
                    warnings.warn(
                        f"Unknown laterUnit '{later}' is not in id_map.json unit/chapter codes.",
                        UserWarning,
                        stacklevel=2,
                    )
                    errors.append(
                        f"laterUnit: unknown unit/chapter code '{later}' (not in id_map.json; "
                        f"use a real unit/chapter code or prefix with '{UNMAPPED_PREFIX}')."
                    )

    if "units" in card:
        units = card["units"]
        if not isinstance(units, list) or len(units) < 2:
            errors.append("units: must be a list of at least 2 distinct unit codes.")
        else:
            seen_u: set[str] = set()
            for idx, u in enumerate(units):
                if not isinstance(u, str) or not u.strip():
                    errors.append(f"units[{idx}]: must be a non-empty string.")
                else:
                    cleaned = u.strip()
                    if cleaned in seen_u:
                        errors.append(f"units[{idx}]: duplicate unit code '{cleaned}'.")
                    seen_u.add(cleaned)

    if "notes" in card and not isinstance(card["notes"], str):
        errors.append("notes: must be a string.")

    if "reasoningMove" in card and card["reasoningMove"] not in REASONING_MOVES:
        errors.append(f"reasoningMove: must be one of {list(REASONING_MOVES)}, got {card['reasoningMove']!r}.")

    if "level" in card:
        lvl = card["level"]
        if not _is_int(lvl) or not (1 <= lvl <= 5):
            errors.append(f"level: must be an integer 1..5, got {lvl!r}.")

    if "representation" in card and card["representation"] not in REPRESENTATIONS:
        errors.append(f"representation: must be one of {list(REPRESENTATIONS)}, got {card['representation']!r}.")

    # sourceRef validation
    if "sourceRef" in card:
        ref = card["sourceRef"]
        if not isinstance(ref, dict):
            errors.append("sourceRef: must be an object.")
        else:
            unknown_ref = sorted(set(ref) - _ALLOWED_SOURCE_REF_KEYS)
            if unknown_ref:
                errors.append(f"sourceRef: unknown field(s) {unknown_ref}.")
            for rkey in ("family", "file", "item"):
                if rkey not in ref:
                    errors.append(f"sourceRef: missing required field '{rkey}'.")
                elif not isinstance(ref[rkey], str) or not ref[rkey].strip():
                    errors.append(f"sourceRef.{rkey}: must be a non-empty string.")
            if "family" in ref and isinstance(ref["family"], str) and family_mode(ref["family"]) == "scope":
                errors.append(
                    f"sourceRef.family: '{ref['family']}' is scope-only (TOC/learning objectives); "
                    "never extract core cards from OpenStax."
                )
            if "page" not in ref:
                errors.append("sourceRef: missing required field 'page'.")
            else:
                page = ref["page"]
                valid_page = (_is_int(page) and page >= 1) or (isinstance(page, str) and bool(page.strip()))
                if not valid_page:
                    errors.append(f"sourceRef.page: must be a positive integer or non-empty string, got {page!r}.")

    # traps validation
    if "traps" in card:
        traps = card["traps"]
        if not isinstance(traps, list):
            errors.append("traps: must be a list of {tag, description} objects.")
        else:
            for idx, trap in enumerate(traps):
                if not isinstance(trap, dict):
                    errors.append(f"traps[{idx}]: must be an object.")
                    continue
                unknown_t = sorted(set(trap) - _ALLOWED_TRAP_KEYS)
                if unknown_t:
                    errors.append(f"traps[{idx}]: unknown field(s) {unknown_t}.")
                for tkey in ("tag", "description"):
                    if tkey not in trap or not isinstance(trap[tkey], str) or not trap[tkey].strip():
                        errors.append(f"traps[{idx}].{tkey}: must be a non-empty string.")

    # format validation
    if "format" in card:
        fmt = card["format"]
        if not isinstance(fmt, dict):
            errors.append("format: must be an object.")
        else:
            unknown_f = sorted(set(fmt) - _ALLOWED_FORMAT_KEYS)
            if unknown_f:
                errors.append(f"format: unknown field(s) {unknown_f}.")
            if "kind" not in fmt:
                errors.append("format: missing required field 'kind'.")
            elif fmt["kind"] not in FORMAT_KINDS:
                errors.append(f"format.kind: must be one of {list(FORMAT_KINDS)}, got {fmt['kind']!r}.")
            if "optionCount" in fmt:
                oc = fmt["optionCount"]
                if not _is_int(oc) or not (2 <= oc <= 20):
                    errors.append(f"format.optionCount: must be an integer 2..20, got {oc!r}.")
            if "distractorPatterns" in fmt:
                dp = fmt["distractorPatterns"]
                if not isinstance(dp, list) or not all(isinstance(x, str) and x.strip() for x in dp):
                    errors.append("format.distractorPatterns: must be a list of non-empty strings.")

    # Source-free check when source_item_text is supplied
    if source_item_text and isinstance(source_item_text, str) and source_item_text.strip():
        src_digits = set(extract_digit_runs(source_item_text))
        src_shingles = _word_shingles(source_item_text)
        for path, text in _content_string_fields(card):
            if src_digits:
                copied = sorted(set(extract_digit_runs(text)) & src_digits)
                if copied:
                    errors.append(
                        f"{path}: contains digit run(s) {copied} copied from source item text; "
                        "abstract the core without source numbers."
                    )
            if src_shingles:
                overlap = _word_shingles(text) & src_shingles
                if overlap:
                    sample = " ".join(sorted(overlap)[0])
                    errors.append(
                        f"{path}: contains source wording overlap ('{sample}'); "
                        "abstract the core without copying source phrasing."
                    )

    return errors


def _iter_jsonl_cards(path: str) -> Iterable[tuple[int, dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                card = json.loads(line)
            except ValueError as exc:
                raise CoreCardError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(card, dict):
                raise CoreCardError(f"{path}:{line_no}: invalid core card: Card must be a JSON object.")
            yield line_no, card


def _card_targets_unit(card: dict[str, Any], unit_code: str) -> bool:
    later = card.get("laterUnit")
    if isinstance(later, str) and later.strip() == unit_code:
        return True
    units = card.get("units")
    if isinstance(units, list) and any(isinstance(u, str) and u.strip() == unit_code for u in units):
        return True
    return False


def load_core_cards(
    unit_code: str,
    sources_dir: str | None = None,
    validate: bool = True,
    *,
    include_carried: bool = True,
    valid_unit_codes: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Load core cards for ``unit_code`` from ``sources/_cores/<unit_code>.jsonl``.

    When ``include_carried`` is True (default), also scans other ``sources/_cores/*.jsonl``
    files for cards whose ``laterUnit == unit_code`` or whose ``units`` contains ``unit_code``,
    deduplicating by ``id`` and annotating carried-forward cards with ``carriedFrom``.
    """
    cards: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    path = cores_path(unit_code, sources_dir=sources_dir)
    if os.path.exists(path):
        for line_no, card in _iter_jsonl_cards(path):
            if validate:
                errs = validate_core_card(card, valid_unit_codes=valid_unit_codes)
                if errs:
                    raise CoreCardError(f"{path}:{line_no}: invalid core card: " + "; ".join(errs))
            cid = card.get("id")
            if isinstance(cid, str):
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)
            cards.append(card)

    if include_carried:
        cores_dir = os.path.dirname(path)
        if os.path.isdir(cores_dir):
            for fname in sorted(os.listdir(cores_dir)):
                if not fname.endswith(".jsonl"):
                    continue
                other_unit = fname[:-6]
                if other_unit == unit_code:
                    continue
                other_path = os.path.join(cores_dir, fname)
                if not os.path.isfile(other_path):
                    continue
                for line_no, card in _iter_jsonl_cards(other_path):
                    if not _card_targets_unit(card, unit_code):
                        continue
                    cid = card.get("id")
                    if isinstance(cid, str) and cid in seen_ids:
                        continue
                    if validate:
                        errs = validate_core_card(card, valid_unit_codes=valid_unit_codes)
                        if errs:
                            raise CoreCardError(f"{other_path}:{line_no}: invalid core card: " + "; ".join(errs))
                    if isinstance(cid, str):
                        seen_ids.add(cid)
                    cards.append({**card, "carriedFrom": other_unit})

    return cards


def save_core_cards(
    unit_code: str,
    cards: list[dict[str, Any]],
    sources_dir: str | None = None,
    source_texts: dict[str, str] | None = None,
    *,
    valid_unit_codes: Iterable[str] | None = None,
) -> str:
    """Validate and write ``cards`` to ``sources/_cores/<unit_code>.jsonl``."""
    source_texts = source_texts or {}
    for idx, card in enumerate(cards, 1):
        cid = card.get("id", f"#{idx}") if isinstance(card, dict) else f"#{idx}"
        errs = validate_core_card(
            card,
            source_item_text=source_texts.get(cid),
            valid_unit_codes=valid_unit_codes,
        )
        if errs:
            raise CoreCardError(f"[{cid}] invalid core card: " + "; ".join(errs))
    path = cores_path(unit_code, sources_dir=sources_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for card in cards:
            fh.write(json.dumps(card, ensure_ascii=False) + "\n")
    return path


def append_core_card(
    unit_code: str,
    card: dict[str, Any],
    sources_dir: str | None = None,
    source_item_text: str | None = None,
    *,
    valid_unit_codes: Iterable[str] | None = None,
) -> str:
    """Validate and append one core card to ``sources/_cores/<unit_code>.jsonl``."""
    errs = validate_core_card(card, source_item_text=source_item_text, valid_unit_codes=valid_unit_codes)
    if errs:
        raise CoreCardError("Invalid core card: " + "; ".join(errs))
    path = cores_path(unit_code, sources_dir=sources_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(card, ensure_ascii=False) + "\n")
    return path
