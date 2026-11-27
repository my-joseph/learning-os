# -*- coding: utf-8 -*-
"""Remap invalid ``laterUnit`` codes in a core-cards JSONL file to real ``id_map.json`` unit codes.

Inspects each card whose ``laterUnit`` is neither a valid unit/chapter code in ``id_map.json``
nor prefixed with ``UNMAPPED:``, then resolves a target unit code by:
1. Checking an explicit override map (by card ``id`` or old ``laterUnit`` value).
2. Matching domain signals in the card's ``skill`` / ``notes`` / ``difficultyDriver`` against
   ``id_map.json`` unit titles (e.g. higher-degree polynomials with complex roots -> Zeros of
   Polynomial Functions; modulus/polar/trig form/De Moivre/nth roots/complex-plane regions ->
   Polar Form of Complex Numbers; quadratics with complex roots -> Quadratic Equations).
3. General token overlap against ``id_map.json`` unit titles in the same subject track.
4. Falling back to ``UNMAPPED:<old_value>`` when no unit matches confidently.

Dry-run by default; pass ``--apply`` to validate and rewrite the file atomically.

Usage:
    python -m scripts.source_cores_retag sources/_cores/MTH-T02-C01-U01.jsonl
    python -m scripts.source_cores_retag sources/_cores/MTH-T02-C01-U01.jsonl --apply
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from collections import Counter
from typing import Any

from math_engine.source_cores import (
    UNMAPPED_PREFIX,
    CoreCardError,
    load_valid_unit_codes,
    validate_core_card,
)

# Explicit override map: card ID or old laterUnit code -> target real unit code.
# CLI --overrides JSON is merged on top of this map.
DEFAULT_OVERRIDES: dict[str, str] = {}

_TITLE_STOPWORDS: frozenset[str] = frozenset(
    {
        "and",
        "the",
        "for",
        "with",
        "from",
        "into",
        "using",
        "other",
        "types",
        "intro",
        "introduction",
    }
)

# Higher-degree polynomials with complex roots (cubic/quartic/polynomial zeros, factors, real coefficients).
_HIGHER_POLY_COMPLEX_RE = re.compile(
    r"\b(?:"
    r"real\s+cubic|real\s+quartic|real\s+quintic|"
    r"monic\s+(?:real\s+)?(?:cubic|quartic|quintic)|"
    r"(?:cubic|quartic|quintic)'?s\s+value|"
    r"(?:cubic|quartic|quintic)\s+(?:polynomial|equation|function)|"
    r"polynomial\s+(?:function|equation|zeros?|roots?|factors?)|"
    r"complex\s+linear\s+factor|"
    r"conjugate-pair\s+quadratic"
    r")\b",
    re.IGNORECASE,
)

# Modulus / polar / trig form / De Moivre / nth roots / complex-plane regions & geometry.
_POLAR_MODULUS_COMPLEX_RE = re.compile(
    r"\b(?:"
    r"polar|trigonometric|trig\b|de\s+moivre|cis|argument|"
    r"modulus|unit-circle|roots?\s+of\s+unity|"
    r"(?:cube|fourth|fifth|sixth|nth)\s+roots?|"
    r"square\s+roots?\s+of\s+a\s+complex|"
    r"half-plane|plane\s+region|open\s+disc|small\s+disc|"
    r"circle\s+equations?|equidistant|equal-distance|distances?|parallelogram|"
    r"sizes?\s+squared|shifted\s+size|quotient-size|unit-size|size\s+of|known\s+sizes?|given\s+size|equality\s+of\s+sizes|size\s+condition|size\s+equation|ratio\s+of\s+sizes|sum\s+of\s+sizes|"
    r"z\s+cubed|z\s+to\s+the|shifted\s+cube|"
    r"angle\s+range|angle\s+restriction|region\s+defined|curve\s+where|"
    r"high\s+power|power\s+of\s+a\s+quotient"
    r")\b",
    re.IGNORECASE,
)

_QUADRATIC_COMPLEX_RE = re.compile(r"\bquadratic\b", re.IGNORECASE)
_QUADRATIC_ROOT_RE = re.compile(r"\b(?:roots?|discriminant|conjugate)\b", re.IGNORECASE)


def _card_text(card: dict[str, Any]) -> str:
    parts = [
        str(card.get("skill") or ""),
        str(card.get("notes") or ""),
        str(card.get("difficultyDriver") or ""),
    ]
    for trap in card.get("traps") or []:
        if isinstance(trap, dict):
            parts.append(str(trap.get("tag") or ""))
            parts.append(str(trap.get("description") or ""))
    return " ".join(p for p in parts if p).strip()


def _track_prefix(code: str) -> str:
    parts = (code or "").split("-")
    return f"{parts[0]}-" if parts and parts[0] in ("MTH", "PHY", "PRG") else ""


def _is_unit_code(code: str) -> bool:
    return bool(re.search(r"-U\d+$", code))


def _find_code_by_title(
    valid_codes: dict[str, str],
    track_prefix: str,
    required_substrings: tuple[str, ...],
) -> str | None:
    candidates = [
        (code, title)
        for code, title in sorted(valid_codes.items())
        if (not track_prefix or code.startswith(track_prefix)) and _is_unit_code(code)
    ]
    for code, title in candidates:
        low = title.lower()
        if all(sub in low for sub in required_substrings):
            return code
    return None


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z]{3,}", (text or "").lower())
    return {w for w in words if w not in _TITLE_STOPWORDS}


def _match_by_id_map_title(
    card_text: str,
    valid_codes: dict[str, str],
    track_prefix: str,
) -> tuple[str, str] | None:
    text_low = card_text.lower()
    card_toks = _tokens(card_text)
    if not card_toks:
        return None

    best_code: str | None = None
    best_title = ""
    best_score = 0.0

    for code, title in sorted(valid_codes.items()):
        if track_prefix and not code.startswith(track_prefix):
            continue
        if not _is_unit_code(code) or not title.strip():
            continue
        title_low = title.strip().lower()
        title_toks = _tokens(title)
        if not title_toks:
            continue

        if title_low in text_low:
            score = 100.0 + len(title_toks)
        else:
            overlap = card_toks & title_toks
            if not overlap:
                continue
            min_hits = 1 if len(title_toks) == 1 else 2
            if len(overlap) < min_hits:
                continue
            score = len(overlap) + (len(overlap) / len(title_toks))

        if score > best_score:
            best_score = score
            best_code = code
            best_title = title

    if best_code is not None:
        return best_code, f"title-match:{best_title}"
    return None


def suggest_later_unit(
    card: dict[str, Any],
    valid_codes: dict[str, str],
    overrides: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Suggest a valid ``id_map.json`` target code (or ``UNMAPPED:<old>``) for an invalid ``laterUnit``."""
    old_later = str(card.get("laterUnit") or "").strip()
    cid = str(card.get("id") or "").strip()
    merged_overrides = {**DEFAULT_OVERRIDES, **(overrides or {})}

    for key in (cid, old_later):
        if key and key in merged_overrides:
            target = str(merged_overrides[key]).strip()
            if target in valid_codes or target.startswith(UNMAPPED_PREFIX):
                return target, f"override:{key}"

    text = _card_text(card)
    track = _track_prefix(str(card.get("unitCode") or old_later))

    # 1. Higher-degree polynomials with complex roots -> Zeros of Polynomial Functions (e.g. MTH-T02-C04-U05)
    if _HIGHER_POLY_COMPLEX_RE.search(text):
        poly_code = _find_code_by_title(valid_codes, track, ("zeros", "polynomial")) or _find_code_by_title(
            valid_codes, track, ("polynomial",)
        )
        if poly_code:
            return poly_code, f"rule:higher-degree-polynomial ({valid_codes[poly_code]})"

    # 2. Modulus / polar / trig form / De Moivre / nth roots / complex-plane regions -> Polar Form of Complex Numbers
    if _POLAR_MODULUS_COMPLEX_RE.search(text):
        polar_code = _find_code_by_title(valid_codes, track, ("polar", "complex"))
        if polar_code:
            return polar_code, f"rule:polar-modulus-complex ({valid_codes[polar_code]})"

    # 3. Quadratics with complex roots -> Quadratic Equations
    if _QUADRATIC_COMPLEX_RE.search(text) and _QUADRATIC_ROOT_RE.search(text):
        quad_code = _find_code_by_title(valid_codes, track, ("quadratic", "equations"))
        if quad_code:
            return quad_code, f"rule:quadratic-complex-roots ({valid_codes[quad_code]})"

    # 4. General unit-title token overlap against id_map.json
    title_match = _match_by_id_map_title(text, valid_codes, track)
    if title_match:
        return title_match

    return f"{UNMAPPED_PREFIX}{old_later}", "unmapped"


def retag_cards(
    cards: list[dict[str, Any]],
    valid_codes: dict[str, str],
    overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Remap invalid ``laterUnit`` values across ``cards`` (pure function, returns updated copies)."""
    updated: list[dict[str, Any]] = []
    changes: list[dict[str, str]] = []
    counts_by_target: Counter[str] = Counter()
    unchanged_valid = 0
    unchanged_none = 0

    for raw in cards:
        card = dict(raw)
        later = card.get("laterUnit")
        if later is None or (isinstance(later, str) and not later.strip()):
            unchanged_none += 1
            updated.append(card)
            continue

        cleaned = str(later).strip()
        if cleaned in valid_codes or cleaned.startswith(UNMAPPED_PREFIX):
            unchanged_valid += 1
            updated.append(card)
            continue

        new_target, reason = suggest_later_unit(card, valid_codes, overrides=overrides)
        card["laterUnit"] = new_target
        updated.append(card)
        counts_by_target[new_target] += 1
        changes.append(
            {
                "id": str(card.get("id") or "?"),
                "oldLaterUnit": cleaned,
                "newLaterUnit": new_target,
                "reason": reason,
            }
        )

    return {
        "totalCards": len(cards),
        "unchangedNone": unchanged_none,
        "unchangedValid": unchanged_valid,
        "remappedCount": len(changes),
        "countsByTarget": dict(sorted(counts_by_target.items())),
        "changes": changes,
        "cards": updated,
    }


def retag_file(
    file_path: str,
    *,
    apply: bool = False,
    id_map_path: str | None = None,
    overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Inspect (and optionally rewrite with ``--apply``) invalid ``laterUnit`` values in a JSONL file."""
    abs_path = os.path.abspath(file_path)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Core cards file not found: {abs_path}")

    valid_codes = load_valid_unit_codes(id_map_path=id_map_path)
    if not valid_codes:
        raise RuntimeError("No unit/chapter codes loaded from id_map.json.")

    cards: list[dict[str, Any]] = []
    with open(abs_path, "r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError as exc:
                raise CoreCardError(f"{abs_path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(obj, dict):
                raise CoreCardError(f"{abs_path}:{line_no}: expected JSON object.")
            cards.append(obj)

    result = retag_cards(cards, valid_codes, overrides=overrides)
    result["filePath"] = abs_path
    result["applied"] = False

    if apply and result["remappedCount"] > 0:
        for idx, card in enumerate(result["cards"], 1):
            errs = validate_core_card(card, valid_unit_codes=valid_codes, enforce_move_contract=False)
            if errs:
                cid = card.get("id", f"#{idx}")
                raise CoreCardError(f"[{cid}] card still invalid after retag: " + "; ".join(errs))

        parent = os.path.dirname(abs_path) or "."
        fd, tmp_path = tempfile.mkstemp(prefix=".retag_", suffix=".jsonl.tmp", dir=parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                for card in result["cards"]:
                    fh.write(json.dumps(card, ensure_ascii=False) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, abs_path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        result["applied"] = True

    return result


def format_retag_summary(result: dict[str, Any]) -> str:
    """Format a concise human-readable summary of the remap (counts per target)."""
    mode = "APPLIED" if result.get("applied") else "DRY-RUN (pass --apply to write)"
    lines = [
        f"Source Core Retag [{mode}]: {result.get('filePath', '')}",
        f"Total cards: {result['totalCards']} "
        f"(no laterUnit: {result['unchangedNone']}, already valid: {result['unchangedValid']}, "
        f"remapped: {result['remappedCount']})",
    ]
    counts = result.get("countsByTarget") or {}
    lines.append("Remap counts per target:")
    if not counts:
        lines.append("  (none)")
    else:
        for target, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  - {target}: {count}")

    changes = result.get("changes") or []
    if changes:
        lines.append("")
        lines.append(f"Remapped cards ({len(changes)}):")
        for ch in changes:
            lines.append(f"  - [{ch['id']}] {ch['oldLaterUnit']} -> {ch['newLaterUnit']} ({ch['reason']})")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.source_cores_retag",
        description="Remap invalid laterUnit codes in a core-cards JSONL file against id_map.json.",
    )
    parser.add_argument("file", help="Path to sources/_cores/<UNIT>.jsonl file.")
    parser.add_argument("--apply", action="store_true", help="Write remapped cards back to the file atomically.")
    parser.add_argument("--id-map", default=None, help="Override path to id_map.json.")
    parser.add_argument(
        "--overrides",
        default=None,
        help="Optional path to JSON file mapping card ID or old laterUnit -> target unit code.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    overrides: dict[str, str] | None = None
    if args.overrides:
        with open(args.overrides, "r", encoding="utf-8") as fh:
            raw_ov = json.load(fh)
        if not isinstance(raw_ov, dict):
            print("Error: --overrides JSON must be an object mapping key -> unit code.", file=sys.stderr)
            return 1
        overrides = {str(k): str(v) for k, v in raw_ov.items()}

    try:
        result = retag_file(
            args.file,
            apply=args.apply,
            id_map_path=args.id_map,
            overrides=overrides,
        )
    except (FileNotFoundError, CoreCardError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(format_retag_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
