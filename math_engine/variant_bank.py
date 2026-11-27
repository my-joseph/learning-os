# -*- coding: utf-8 -*-
"""Math Variant Bank: gated AI variant bank storage, uniqueness checks, and coverage reporting.

Bank files live at ``drills/variants/<UNIT_CODE>.json`` (override with ``VARIANTS_DIR``):

    {
      "unitCode": "MTH-T01-C04",
      "variants": [
        {
          "variantId": "VAR-MTH-T01-C04-<archetypeKey>-01",
          "sourceArchetype": "<archetypeKey>",
          ...full math problem schema (content only, never learner state)...
        }
      ]
    }

Every variant passes all single-problem gates from ``math_engine.ai_drill_ingest``
plus a non-copy uniqueness gate against existing drills and other variants of the
same archetype.
"""

from __future__ import annotations

import argparse
import copy
import glob
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from code_engine.sandbox import JSON_SUFFIXES, assert_safe_contained_path
from math_engine.ai_drill_ingest import (
    AiContractError,
    _run_problem_gates,
    check_distractor_provenance,
    load_l2_step_floor_baseline,
    load_scope_archetypes,
    normalize_prompt_numbers,
    story_text,
    validate_l2_step_floor,
    validate_review,
)
from math_engine.ai_drill_ingest import autofill_problem_figure as autofill_problem_figure
from math_engine.ai_drill_ingest import require_figure_decision as require_figure_decision
from math_engine.ai_drill_ingest import require_figure_if_declared as require_figure_if_declared
from math_engine.ai_drill_ingest import validate_against_vault as validate_against_vault
from math_engine.ai_drill_ingest import validate_ai_problem_contract as validate_ai_problem_contract
from math_engine.answer_check import check_answer
from math_engine.figure_autofill import collect_figure_title_warnings
from math_engine.fmt import LEVEL_LABELS
from math_engine.source_cores import index_dir, resolve_sources_dir
from math_engine.source_cores.originality import check_document_originality
from math_engine.verify import verify_problem as verify_problem
from progress_store import find_repo_root, strip_progress
from quality_rules import (
    QUALITY_RULES,
    compute_fingerprint,
    normalize_skeleton_text,
)


class VariantBankError(Exception):
    """Raised when a variant bank draft or operation fails validation gates."""


def variants_root(repo_root: Optional[str] = None) -> str:
    """Return ``VARIANTS_DIR`` if set, else ``<repo_root>/drills/variants``."""
    if os.environ.get("VARIANTS_DIR"):
        return os.environ["VARIANTS_DIR"]
    return os.path.join(repo_root or find_repo_root(), "drills", "variants")


def _bank_root(variants_dir: Optional[str] = None) -> Path:
    configured = variants_dir or os.environ.get("VARIANTS_DIR")
    repo = Path(find_repo_root())
    root = Path(configured) if configured else repo / "drills" / "variants"
    boundary = repo if root.absolute().is_relative_to(repo) else root
    return assert_safe_contained_path(root, boundary, expect_file=False, allow_missing=True)


def bank_path(unit_code: str, variants_dir: Optional[str] = None) -> str:
    """Return the JSON path for ``unit_code``'s variant bank."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", unit_code):
        raise ValueError("Invalid variant bank unit code")
    return str(
        assert_safe_contained_path(
            f"{unit_code}.json", _bank_root(variants_dir), relative=True, allow_missing=True, suffixes=JSON_SUFFIXES
        )
    )


def load_bank(unit_code_or_path: str, variants_dir: Optional[str] = None) -> Dict[str, Any]:
    """Load a variant bank from an explicit local file or a unit code."""
    requested = Path(unit_code_or_path)
    if requested.suffix == ".json":
        path = assert_safe_contained_path(requested, requested.parent, suffixes=JSON_SUFFIXES)
    else:
        path = Path(bank_path(unit_code_or_path, variants_dir=variants_dir))
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_bank(unit_code: str, bank_doc: Dict[str, Any], variants_dir: Optional[str] = None) -> str:
    """Atomically write ``bank_doc`` to ``drills/variants/<unit_code>.json`` (content only)."""
    clean_doc: Dict[str, Any] = {
        "unitCode": unit_code,
        "variants": copy.deepcopy(bank_doc.get("variants") or []),
    }
    if is_quarantined_variant(None, bank_doc):
        clean_doc.update({key: bank_doc[key] for key in ("status", "quarantineReason", "since") if key in bank_doc})
    for var in clean_doc["variants"]:
        if isinstance(var, dict) and not is_quarantined_variant(var, clean_doc):
            var.pop("state", None)
            var.pop("variantsSeen", None)
            var.pop("variantsAttempted", None)
            if (var.get("answerSpec") or {}).get("type") == "choice":
                var.pop("plainText", None)

    path = bank_path(unit_code, variants_dir=variants_dir)
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{unit_code}_", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(clean_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return path


QUARANTINED_STATUS = "quarantined"


def is_quarantined_variant(variant: Any, bank_doc: Optional[Dict[str, Any]] = None) -> bool:
    """True when ``variant`` (or its enclosing ``bank_doc``) is quarantined and must not be served."""
    if isinstance(bank_doc, dict) and bank_doc.get("status") == QUARANTINED_STATUS:
        return True
    return isinstance(variant, dict) and variant.get("status") == QUARANTINED_STATUS


def active_variant_document(bank_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Project a bank to the variants eligible for ordinary quality checks."""
    variants = bank_doc.get("variants")
    return {
        "unitCode": bank_doc.get("unitCode"),
        "variants": [v for v in variants if isinstance(v, dict) and not is_quarantined_variant(v, bank_doc)]
        if isinstance(variants, list)
        else [],
    }


def find_variant(
    variant_id: str,
    variants_dir: Optional[str] = None,
    *,
    include_quarantined: bool = False,
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Locate ``(bank_doc, variant)`` for ``variant_id`` under ``variants_dir``."""
    if not isinstance(variant_id, str) or not variant_id.strip():
        return None
    try:
        base = _bank_root(variants_dir)
    except (OSError, ValueError):
        return None
    if not base.is_dir():
        return None

    files = sorted(glob.glob(os.path.join(base, "*.json")))
    # Prefer bank files whose unitCode matches the prefix after "VAR-".
    if variant_id.startswith("VAR-"):
        tail = variant_id[4:]
        files.sort(key=lambda p: (0 if tail.startswith(os.path.basename(p)[:-5] + "-") else 1, p))

    for path in files:
        try:
            bank = assert_safe_contained_path(path, base, suffixes=JSON_SUFFIXES)
            with bank.open("r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        for var in doc.get("variants") or []:
            if isinstance(var, dict) and var.get("variantId") == variant_id:
                if not include_quarantined and is_quarantined_variant(var, doc):
                    return None
                return doc, var
    return None


def _drills_data_root(data_root: Optional[str] = None) -> str:
    if data_root is not None:
        return data_root
    if os.environ.get("DRILLS_DATA_DIR"):
        return os.environ["DRILLS_DATA_DIR"]
    repo = Path(find_repo_root())
    return str(assert_safe_contained_path("drills/data", repo, relative=True, expect_file=False, allow_missing=True))


def load_scope_drill_problems(
    unit_code: str,
    data_root: Optional[str] = None,
) -> List[Tuple[str, Dict[str, Any]]]:
    """Load existing drill problems in scope for ``unit_code`` (exact unit, child units, or parent chapter)."""
    root = _drills_data_root(data_root)
    if not os.path.isdir(root):
        return []

    candidate_dirs: List[str] = []
    exact = os.path.join(root, unit_code)
    if os.path.isdir(exact):
        candidate_dirs.append(exact)

    # Chapter code -> include child unit directories (<CHAPTER>-U*).
    for entry in sorted(os.listdir(root)):
        full = os.path.join(root, entry)
        if os.path.isdir(full) and entry.startswith(unit_code + "-U") and full not in candidate_dirs:
            candidate_dirs.append(full)

    # Unit code (<CHAPTER>-Uxx) -> include parent chapter drills as well.
    m_unit = re.match(r"^(.+)-U\d+$", unit_code)
    if m_unit:
        parent_dir = os.path.join(root, m_unit.group(1))
        if os.path.isdir(parent_dir) and parent_dir not in candidate_dirs:
            candidate_dirs.append(parent_dir)

    items: List[Tuple[str, Dict[str, Any]]] = []
    for d in candidate_dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.json"))):
            try:
                file = assert_safe_contained_path(path, Path(root), suffixes=JSON_SUFFIXES)
                with file.open("r", encoding="utf-8") as fh:
                    doc = json.load(fh)
            except (OSError, ValueError):
                continue
            drill_id = doc.get("drillId") or os.path.splitext(os.path.basename(path))[0]
            for prob in doc.get("problems") or []:
                if isinstance(prob, dict):
                    items.append((f"{drill_id}/{prob.get('id', '?')}", prob))
    return items


def validate_variant_id(variant_id: Any, unit_code: str, archetype_key: str) -> Optional[str]:
    """Return an error string if ``variant_id`` violates ``VAR-<UNIT>-<archetypeKey>-NN``, else None."""
    if not isinstance(variant_id, str) or not variant_id.strip():
        return "Missing 'variantId' (expected 'VAR-<UNIT>-<archetypeKey>-NN')."
    pattern = rf"^VAR-{re.escape(unit_code)}-{re.escape(archetype_key)}-\d{{2,}}$"
    if not re.match(pattern, variant_id):
        return (
            f"Invalid variantId '{variant_id}': expected format "
            f"'VAR-{unit_code}-{archetype_key}-NN' (two or more digits)."
        )
    return None


def _norm_text(val: Any) -> str:
    return re.sub(r"\s+", " ", str(val or "")).strip().lower()


def _sorted_prompt_numbers(prob: Dict[str, Any]) -> List[float]:
    nums = normalize_prompt_numbers(story_text(prob), keep_exponents=True)
    return sorted(round(n, 6) for n in nums)


def _choice_correct_label(prob: Dict[str, Any]) -> str:
    spec = prob.get("answerSpec") or {}
    correct_id = str(spec.get("correct") or prob.get("answerPlain") or "").strip()
    for opt in spec.get("options") or []:
        if isinstance(opt, dict) and str(opt.get("id", "")).strip() == correct_id:
            return _norm_text(opt.get("label") or opt.get("text") or correct_id)
    return _norm_text(correct_id)


def answers_equivalent(prob_a: Dict[str, Any], prob_b: Dict[str, Any]) -> bool:
    """True when two problems share an equivalent canonical answer."""
    spec_a = prob_a.get("answerSpec") or {}
    spec_b = prob_b.get("answerSpec") or {}
    type_a = spec_a.get("type")
    type_b = spec_b.get("type")

    if type_a == "choice" or type_b == "choice":
        # For find-the-flaw choice problems, compare the underlying mathematical source & trap value.
        src_a = _norm_text((prob_a.get("verify") or {}).get("source"))
        src_b = _norm_text((prob_b.get("verify") or {}).get("source"))
        trap_a = _norm_text(prob_a.get("trapValue") or (prob_a.get("verify") or {}).get("trapValue"))
        trap_b = _norm_text(prob_b.get("trapValue") or (prob_b.get("verify") or {}).get("trapValue"))
        if src_a and src_b and src_a == src_b and trap_a == trap_b:
            return True
        if type_a == "choice" and type_b == "choice":
            label_a = _choice_correct_label(prob_a)
            label_b = _choice_correct_label(prob_b)
            # Non-flaw choices with identical option label and identical numbers are equivalent.
            if not (prob_a.get("verify") or {}).get("flaw") and not (prob_b.get("verify") or {}).get("flaw"):
                return bool(label_a and label_a == label_b)
        return False

    plain_a = str(prob_a.get("answerPlain") or spec_a.get("value") or "").strip()
    plain_b = str(prob_b.get("answerPlain") or spec_b.get("value") or "").strip()
    if not plain_a or not plain_b:
        return False
    if _norm_text(plain_a) == _norm_text(plain_b):
        return True

    try:
        if spec_b.get("type") and check_answer(spec_b, plain_a).get("verdict") == "correct":
            return True
    except Exception:
        pass
    try:
        if spec_a.get("type") and check_answer(spec_a, plain_b).get("verdict") == "correct":
            return True
    except Exception:
        pass
    return False


def check_variant_uniqueness(
    variant: Dict[str, Any],
    existing_items: List[Tuple[str, Dict[str, Any]]],
) -> List[str]:
    """Ensure ``variant`` differs from every drill problem and other variant of the same archetype."""
    vid = variant.get("variantId") or variant.get("id") or "?"
    arch = variant.get("archetypeKey") or variant.get("sourceArchetype") or ""
    v_prompt = _norm_text(variant.get("prompt"))
    v_plain = _norm_text(variant.get("plainText"))
    v_ctx = _norm_text(variant.get("context"))
    v_nums = _sorted_prompt_numbers(variant)
    v_fp = variant.get("fingerprint") or compute_fingerprint(variant)
    v_skel = normalize_skeleton_text(str(variant.get("prompt") or ""))

    errors: List[str] = []
    for label, other in existing_items:
        o_arch = other.get("archetypeKey") or other.get("sourceArchetype") or other.get("templateKey") or ""
        if arch and o_arch and o_arch != arch:
            continue

        o_prompt = _norm_text(other.get("prompt"))
        if v_prompt and o_prompt and v_prompt == o_prompt:
            errors.append(f"[{vid}] Prompt duplicates {label}; variants must not copy existing problems.")
            continue

        o_plain = _norm_text(other.get("plainText"))
        if v_plain and o_plain and v_plain == o_plain:
            errors.append(f"[{vid}] plainText duplicates {label}; variants must use different numbers/expressions.")
            continue

        o_fp = other.get("fingerprint") or compute_fingerprint(other)
        o_skel = normalize_skeleton_text(str(other.get("prompt") or ""))
        o_ctx = _norm_text(other.get("context"))
        o_nums = _sorted_prompt_numbers(other)
        same_structure = (v_fp == o_fp) or (v_skel and v_skel == o_skel)

        if same_structure and v_ctx == o_ctx and v_nums and v_nums == o_nums:
            errors.append(
                f"[{vid}] Uses the same numbers ({v_nums}) and structure as {label}; "
                "variants must change numbers or context."
            )
            continue

        if answers_equivalent(variant, other):
            errors.append(
                f"[{vid}] Has the same answer ('{variant.get('answerPlain')}') as {label}; "
                "variants of the same archetype must have a different answer."
            )

    return errors


def check_variant_bank(
    bank_doc: Dict[str, Any],
    data_root: Optional[str] = None,
    vault_dir: Optional[str] = None,
    rules: Optional[Dict[str, Any]] = None,
    check_originality: bool = False,
    sources_dir: Optional[str] = None,
    *,
    allow_l2_baseline: bool = True,
) -> List[str]:
    """Run every single-problem ingest gate + variant uniqueness checks on ``bank_doc``."""
    errors: List[str] = []
    if not isinstance(bank_doc, dict):
        return ["Variant bank document must be a JSON object."]

    unit_code = bank_doc.get("unitCode")
    if not isinstance(unit_code, str) or not unit_code.strip():
        return ["Variant bank document must specify a non-empty 'unitCode'."]

    if "sessionSummary" in bank_doc or "progress" in bank_doc:
        errors.append("Variant bank document must hold content only (found learner state field).")

    variants = bank_doc.get("variants")
    if not isinstance(variants, list) or len(variants) == 0:
        errors.append("Variant bank document must contain a non-empty 'variants' list.")
        return errors

    vault_archs = load_scope_archetypes(unit_code, vault_dir=vault_dir)
    drill_items = load_scope_drill_problems(unit_code, data_root=data_root)
    active_rules = rules or QUALITY_RULES
    l2_baseline = load_l2_step_floor_baseline() if allow_l2_baseline else None

    seen_ids: set[str] = set()
    accepted: List[Tuple[str, Dict[str, Any]]] = []

    for idx, original in enumerate(variants, 1):
        if not isinstance(original, dict):
            errors.append(f"[#{idx}] Variant entry must be a JSON object.")
            continue

        vid = original.get("variantId") or f"#{idx}"

        # Content-only invariant: never learner state
        for forbidden in ("state", "variantsSeen", "variantsAttempted", "sessionSummary"):
            if forbidden in original:
                errors.append(f"[{vid}] Variant must hold content only (found learner state key '{forbidden}').")

        arch_key = original.get("archetypeKey")
        src_arch = original.get("sourceArchetype")
        if not isinstance(arch_key, str) or not arch_key.strip():
            errors.append(f"[{vid}] Variant must specify 'archetypeKey'.")
        if not isinstance(src_arch, str) or not src_arch.strip():
            errors.append(f"[{vid}] Variant must specify 'sourceArchetype'.")
        elif isinstance(arch_key, str) and src_arch != arch_key:
            errors.append(f"[{vid}] 'sourceArchetype' ('{src_arch}') must match 'archetypeKey' ('{arch_key}').")

        if isinstance(arch_key, str) and arch_key.strip():
            vid_err = validate_variant_id(original.get("variantId"), unit_code, arch_key)
            if vid_err:
                errors.append(f"[{vid}] {vid_err}")

        if isinstance(original.get("variantId"), str):
            if original["variantId"] in seen_ids:
                errors.append(f"[{vid}] Duplicate variantId '{original['variantId']}' in bank.")
            seen_ids.add(original["variantId"])

        if is_quarantined_variant(original, bank_doc):
            continue

        # 2026-11-19 rule: choice problems omit plainText
        if (original.get("answerSpec") or {}).get("type") == "choice" and "plainText" in original:
            errors.append(f"[{vid}] Choice variant must omit 'plainText' (2026-11-19 rule).")

        prob = copy.deepcopy(original)
        prob["id"] = str(original.get("variantId") or original.get("id") or f"V{idx:02d}")
        prob.setdefault("verificationLevel", "partial")
        pid = prob["id"]

        _run_problem_gates(
            prob,
            vault_archs,
            unit_code,
            active_rules,
            errors=errors,
            enforce_l2_step_floor=True,
            bank_unit=unit_code if allow_l2_baseline else None,
            l2_baseline=l2_baseline,
        )
        errors.extend(check_variant_uniqueness(prob, drill_items + accepted))
        # Include failed variants when checking later entries for duplicates.
        accepted.append((pid, prob))

    if check_originality:
        active_doc = active_variant_document(bank_doc)
        if active_doc["variants"]:
            orig_errors, _ = check_document_originality(active_doc, unit_code=unit_code, sources_dir=sources_dir)
            errors.extend(orig_errors)

    return errors


def _next_variant_seq(existing_variants: List[Dict[str, Any]], unit_code: str, archetype_key: str) -> int:
    prefix = f"VAR-{unit_code}-{archetype_key}-"
    max_n = 0
    for var in existing_variants:
        vid = var.get("variantId")
        if isinstance(vid, str) and vid.startswith(prefix):
            tail = vid[len(prefix) :]
            if tail.isdigit():
                max_n = max(max_n, int(tail))
    return max_n + 1


def _prepare_variant_for_bank(
    raw: Dict[str, Any],
    unit_code: str,
    existing_variants: List[Dict[str, Any]],
    vault_archs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    prob = copy.deepcopy(raw)
    prob.pop("state", None)
    prob.pop("variantsSeen", None)
    prob.pop("variantsAttempted", None)
    prob.pop("sessionSummary", None)

    arch_key = prob.get("archetypeKey") or prob.get("sourceArchetype") or ""
    if arch_key:
        prob["archetypeKey"] = arch_key
        prob["sourceArchetype"] = arch_key

    if not prob.get("variantId") and arch_key:
        seq = _next_variant_seq(existing_variants, unit_code, arch_key)
        prob["variantId"] = f"VAR-{unit_code}-{arch_key}-{seq:02d}"

    if prob.get("variantId"):
        prob["id"] = prob["variantId"]

    prob.setdefault("verificationLevel", "partial")
    if not prob.get("levelLabel") and prob.get("level") in LEVEL_LABELS:
        prob["levelLabel"] = LEVEL_LABELS[prob["level"]]

    if (prob.get("answerSpec") or {}).get("type") == "choice":
        prob.pop("plainText", None)

    autofill_problem_figure(prob, vault_archs)
    prob["fingerprint"] = compute_fingerprint(prob)
    return prob


def add_variants(
    draft_doc: Dict[str, Any],
    unit_code: Optional[str] = None,
    variants_dir: Optional[str] = None,
    data_root: Optional[str] = None,
    vault_dir: Optional[str] = None,
    rules: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Gate and append variants from ``draft_doc`` into ``drills/variants/<UNIT>.json``."""
    resolved_unit = unit_code or draft_doc.get("unitCode")
    if not isinstance(resolved_unit, str) or not resolved_unit.strip():
        raise VariantBankError("Draft document must specify 'unitCode' (or pass --unit).")

    raw_items = draft_doc.get("variants")
    if raw_items is None:
        raw_items = draft_doc.get("problems")
    if not isinstance(raw_items, list) or len(raw_items) == 0:
        raise VariantBankError("Draft document must provide a non-empty 'variants' or 'problems' list.")

    path = bank_path(resolved_unit, variants_dir=variants_dir)
    if os.path.exists(path):
        existing_doc = load_bank(path, variants_dir=variants_dir)
        combined_variants = copy.deepcopy(existing_doc.get("variants") or [])
        if is_quarantined_variant(None, existing_doc):
            for variant in combined_variants:
                if isinstance(variant, dict):
                    variant["status"] = QUARANTINED_STATUS
                    for key in ("quarantineReason", "since"):
                        if key in existing_doc:
                            variant.setdefault(key, existing_doc[key])
    else:
        combined_variants = []

    vault_archs = load_scope_archetypes(resolved_unit, vault_dir=vault_dir)
    newly_added: List[Dict[str, Any]] = []
    for item in raw_items:
        prepared = _prepare_variant_for_bank(item, resolved_unit, combined_variants, vault_archs)
        combined_variants.append(prepared)
        newly_added.append(prepared)

    candidate_doc = {"unitCode": resolved_unit, "variants": combined_variants}
    strip_progress({"problems": candidate_doc["variants"]})
    errs = check_variant_bank(candidate_doc, data_root=data_root, vault_dir=vault_dir, rules=rules)
    for prepared in newly_added:
        if "review" not in prepared:
            try:
                validate_review(prepared)
            except AiContractError as exc:
                errs.append(str(exc))
        try:
            validate_l2_step_floor(prepared)
        except AiContractError as exc:
            if str(exc) not in errs:
                errs.append(str(exc))
    if errs:
        raise VariantBankError("Variant bank gates failed:\n" + "\n".join(f"  - {e}" for e in errs))

    save_bank(resolved_unit, candidate_doc, variants_dir=variants_dir)
    for warn in check_variant_bank_warnings(candidate_doc, vault_dir=vault_dir):
        print(f"WARNING: {warn}")
    return candidate_doc


DEFAULT_MIN_VARIANTS = 3
COVERAGE_BASELINE_PATH = Path("tests/data/variant_coverage_baseline.json")


def _candidate_bank_codes_for_scope(codes: Iterable[str], variants_dir: Optional[str] = None) -> List[str]:
    """Resolve bank file stems (exact unit/chapter, parent chapter, child units for chapter)."""
    base = variants_dir or variants_root()
    ordered: List[str] = []
    seen: set[str] = set()

    def _add(code: str) -> None:
        c = code.strip()
        if c and c not in seen:
            seen.add(c)
            ordered.append(c)

    for raw in codes:
        if not isinstance(raw, str) or not raw.strip():
            continue
        code = raw.strip()
        _add(code)
        m_unit = re.match(r"^(.+)-U\d+$", code)
        if m_unit:
            _add(m_unit.group(1))
        elif os.path.isdir(base):
            prefix = f"{code}-U"
            for path in sorted(glob.glob(os.path.join(base, "*.json"))):
                stem = os.path.basename(path)[:-5]
                if stem.startswith(prefix):
                    _add(stem)
    return ordered


def _load_scope_variants(
    codes: Iterable[str],
    variants_dir: Optional[str] = None,
    *,
    include_quarantined: bool = False,
) -> List[Dict[str, Any]]:
    """Load unique bank variants across all candidate bank files for ``codes``."""
    variants: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for code in _candidate_bank_codes_for_scope(codes, variants_dir=variants_dir):
        path = bank_path(code, variants_dir=variants_dir)
        if not os.path.isfile(path):
            continue
        try:
            doc = load_bank(path, variants_dir=variants_dir)
        except (OSError, ValueError):
            continue
        for var in doc.get("variants") or []:
            if not isinstance(var, dict):
                continue
            if not include_quarantined and is_quarantined_variant(var, doc):
                continue
            vid = str(var.get("variantId") or "")
            if vid:
                if vid in seen_ids:
                    continue
                seen_ids.add(vid)
            variants.append(var)
    return variants


def count_quarantined_variants(scope: str, variants_dir: Optional[str] = None) -> int:
    """Count quarantined variants stored across candidate bank files for ``scope``."""
    if not isinstance(scope, str) or not scope.strip() or scope.startswith("PRG-"):
        return 0
    seen_ids: set[str] = set()
    count = 0
    for code in _candidate_bank_codes_for_scope([scope], variants_dir=variants_dir):
        path = bank_path(code, variants_dir=variants_dir)
        if not os.path.isfile(path):
            continue
        try:
            doc = load_bank(path, variants_dir=variants_dir)
        except (OSError, ValueError):
            continue
        for idx, var in enumerate(doc.get("variants") or []):
            if not isinstance(var, dict):
                continue
            if not is_quarantined_variant(var, doc):
                continue
            vid = str(var.get("variantId") or f"{code}#{idx}")
            if vid in seen_ids:
                continue
            seen_ids.add(vid)
            count += 1
    return count


def reverify_quarantined_variants(
    unit_code: str,
    *,
    variants_dir: Optional[str] = None,
    data_root: Optional[str] = None,
    vault_dir: Optional[str] = None,
    rules: Optional[Dict[str, Any]] = None,
    check_originality: bool = True,
    sources_dir: Optional[str] = None,
    apply: bool = False,
) -> Dict[str, Any]:
    """Run all current gates (distractor provenance, L2 step floor, review, answer check, originality)
    on quarantined variants in ``unit_code``. When ``apply=True``, un-quarantines only variants that pass.
    """
    if apply and not check_originality:
        raise VariantBankError("--reverify --apply requires originality and cannot use --no-originality.")
    path = bank_path(unit_code, variants_dir=variants_dir)
    if not os.path.isfile(path):
        return {
            "unitCode": unit_code,
            "quarantinedTotal": 0,
            "passing": [],
            "failing": [],
            "unquarantined": [],
            "originalityNotice": None,
            "applied": False,
        }
    doc = load_bank(path, variants_dir=variants_dir)
    variants = doc.get("variants") or []
    id_counts = Counter(v["variantId"] for v in variants if isinstance(v, dict) and isinstance(v.get("variantId"), str))
    duplicates = sorted(vid for vid, count in id_counts.items() if count > 1)
    if duplicates:
        raise VariantBankError(f"Duplicate variantId in bank: {', '.join(duplicates)}.")
    bank_level_quarantined = doc.get("status") == QUARANTINED_STATUS
    vault_archs = load_scope_archetypes(unit_code, vault_dir=vault_dir)
    drill_items = load_scope_drill_problems(unit_code, data_root=data_root)
    active_rules = rules or QUALITY_RULES

    active_items: List[Tuple[str, Dict[str, Any]]] = [
        (str(v.get("variantId") or f"active#{i}"), v)
        for i, v in enumerate(variants, 1)
        if isinstance(v, dict) and not is_quarantined_variant(v, doc)
    ]

    resolved_sources = resolve_sources_dir(sources_dir=sources_dir) if check_originality else ""
    orig_notice: Optional[str] = None
    run_orig = False
    if check_originality:
        if not os.path.isdir(resolved_sources):
            orig_notice = f"Originality gate skipped: sources directory not found ({resolved_sources})."
        elif not Path(index_dir(resolved_sources), f"located_{unit_code}.json").is_file():
            orig_notice = f"Originality gate skipped: located_{unit_code}.json is missing from the source index."
        else:
            run_orig = True
        if apply and orig_notice:
            raise VariantBankError(orig_notice)
    else:
        orig_notice = "Originality gate skipped: disabled by --no-originality."

    passing: List[Dict[str, Any]] = []
    failing: List[Dict[str, Any]] = []
    passed_ids: set[str] = set()
    checked_peer_items: List[Tuple[str, Dict[str, Any]]] = list(active_items)

    for idx, original in enumerate(variants, 1):
        if not isinstance(original, dict) or not is_quarantined_variant(original, doc):
            continue
        vid = str(original.get("variantId") or f"#{idx}")
        item_errors: List[str] = []

        for forbidden in ("state", "variantsSeen", "variantsAttempted", "sessionSummary"):
            if forbidden in original:
                item_errors.append(f"[{vid}] Variant must hold content only (found learner state key '{forbidden}').")

        arch_key = original.get("archetypeKey")
        src_arch = original.get("sourceArchetype")
        if not isinstance(arch_key, str) or not arch_key.strip():
            item_errors.append(f"[{vid}] Variant must specify 'archetypeKey'.")
        if not isinstance(src_arch, str) or not src_arch.strip():
            item_errors.append(f"[{vid}] Variant must specify 'sourceArchetype'.")
        elif isinstance(arch_key, str) and src_arch != arch_key:
            item_errors.append(f"[{vid}] 'sourceArchetype' ('{src_arch}') must match 'archetypeKey' ('{arch_key}').")
        if isinstance(arch_key, str) and arch_key.strip():
            vid_err = validate_variant_id(original.get("variantId"), unit_code, arch_key)
            if vid_err:
                item_errors.append(f"[{vid}] {vid_err}")
        if (original.get("answerSpec") or {}).get("type") == "choice" and "plainText" in original:
            item_errors.append(f"[{vid}] Choice variant must omit 'plainText' (2026-11-19 rule).")

        prob = copy.deepcopy(original)
        prob["id"] = vid
        prob.setdefault("verificationLevel", "partial")
        _run_problem_gates(prob, vault_archs, unit_code, active_rules, errors=item_errors)
        if "review" not in prob:
            try:
                validate_review(prob)
            except AiContractError as exc:
                item_errors.append(str(exc))
        item_errors.extend(check_variant_uniqueness(prob, drill_items + checked_peer_items))

        if run_orig:
            o_errs, o_note = check_document_originality(
                {"unitCode": unit_code, "variants": [prob]},
                unit_code=unit_code,
                sources_dir=resolved_sources,
            )
            if o_note and not orig_notice:
                orig_notice = o_note
            if apply and o_note:
                raise VariantBankError(o_note)
            item_errors.extend(o_errs)

        dedup_errs = list(dict.fromkeys(item_errors))
        entry = {
            "variantId": vid,
            "archetypeKey": arch_key,
            "level": original.get("level"),
            "quarantineReason": original.get("quarantineReason") or doc.get("quarantineReason"),
            "since": original.get("since") or doc.get("since"),
            "errors": dedup_errs,
        }
        if dedup_errs:
            failing.append(entry)
        else:
            passing.append(entry)
            passed_ids.add(vid)
            checked_peer_items.append((vid, prob))

    unquarantined: List[str] = []
    if apply and passed_ids:
        updated = copy.deepcopy(doc)
        if bank_level_quarantined:
            updated.pop("status", None)
            updated.pop("quarantineReason", None)
            updated.pop("since", None)
        for v in updated.get("variants") or []:
            if not isinstance(v, dict):
                continue
            vid = str(v.get("variantId") or "")
            if vid in passed_ids:
                v.pop("status", None)
                v.pop("quarantineReason", None)
                v.pop("since", None)
                unquarantined.append(vid)
            elif bank_level_quarantined:
                v["status"] = QUARANTINED_STATUS
                if doc.get("quarantineReason"):
                    v.setdefault("quarantineReason", doc["quarantineReason"])
                if doc.get("since"):
                    v.setdefault("since", doc["since"])
        save_bank(unit_code, updated, variants_dir=variants_dir)

    return {
        "unitCode": unit_code,
        "quarantinedTotal": len(passing) + len(failing),
        "passing": passing,
        "failing": failing,
        "unquarantined": unquarantined,
        "originalityNotice": orig_notice,
        "applied": bool(apply and unquarantined),
    }


def format_reverify_report(report: Dict[str, Any]) -> str:
    """Format ``reverify_quarantined_variants`` output (zero-leak: IDs and gate statuses only)."""
    unit = report["unitCode"]
    total = report["quarantinedTotal"]
    if total == 0:
        return f"Reverify {unit}: 0 quarantined variant(s)."
    gate_label = "checked gates" if report.get("originalityNotice") else "current gates"
    lines = [
        f"Reverify {unit}: {len(report['passing'])}/{total} quarantined variant(s) pass {gate_label}, "
        f"{len(report['failing'])} failing."
    ]
    if report.get("originalityNotice"):
        lines.append(f"NOTE: {report['originalityNotice']}")
    for item in report["passing"]:
        tag = "UNQUARANTINED" if item["variantId"] in report.get("unquarantined", []) else "PASS"
        lines.append(f"  {tag} {item['variantId']} ({item['archetypeKey']} @ L{item['level']})")
    for item in report["failing"]:
        lines.append(
            f"  FAIL {item['variantId']} ({item['archetypeKey']} @ L{item['level']}): "
            f"{len(item['errors'])} gate error(s)"
        )
        for err in item["errors"]:
            lines.append(f"       - {err}")
    return "\n".join(lines)


def _summarize_coverage(
    target: str,
    unit_code: str,
    drill_count: int,
    problems: List[Dict[str, Any]],
    *,
    variants_dir: Optional[str] = None,
    min_variants: int = DEFAULT_MIN_VARIANTS,
) -> Dict[str, Any]:
    bank_codes: List[str] = [unit_code] if unit_code else []
    pair_drill_counts: Counter[Tuple[str, int]] = Counter()
    for prob in problems:
        if not isinstance(prob, dict):
            continue
        arch = str(prob.get("archetypeKey") or prob.get("templateKey") or "").strip()
        if not arch:
            continue
        try:
            lvl = int(prob.get("level") or 0)
        except (TypeError, ValueError):
            lvl = 0
        pair_drill_counts[(arch, lvl)] += 1
        p_unit = prob.get("unitCode")
        if isinstance(p_unit, str) and p_unit.strip():
            bank_codes.append(p_unit.strip())

    scope_variants = _load_scope_variants(bank_codes, variants_dir=variants_dir)
    variant_pair_counts: Counter[Tuple[str, int]] = Counter()
    variant_arch_counts: Counter[str] = Counter()
    for var in scope_variants:
        v_arch = str(var.get("archetypeKey") or var.get("sourceArchetype") or "").strip()
        if not v_arch:
            continue
        try:
            v_lvl = int(var.get("level") or 0)
        except (TypeError, ValueError):
            v_lvl = 0
        variant_pair_counts[(v_arch, v_lvl)] += 1
        variant_arch_counts[v_arch] += 1

    pairs: List[Dict[str, Any]] = []
    uncovered: List[Dict[str, Any]] = []
    for (arch, lvl), drill_uses in sorted(pair_drill_counts.items()):
        v_count = variant_pair_counts.get((arch, lvl), 0)
        entry = {
            "archetypeKey": arch,
            "level": lvl,
            "drillProblems": drill_uses,
            "variantCount": v_count,
            "archetypeTotalVariants": variant_arch_counts.get(arch, 0),
            "covered": v_count >= min_variants,
            "needed": max(0, min_variants - v_count),
        }
        pairs.append(entry)
        if not entry["covered"]:
            uncovered.append(entry)

    return {
        "target": target,
        "unitCode": unit_code,
        "minVariants": min_variants,
        "drillCount": drill_count,
        "problemCount": sum(pair_drill_counts.values()),
        "totalPairs": len(pairs),
        "coveredPairs": len(pairs) - len(uncovered),
        "uncoveredPairs": uncovered,
        "pairs": pairs,
    }


def compute_drill_coverage(
    drill_doc: Dict[str, Any],
    *,
    variants_dir: Optional[str] = None,
    min_variants: int = DEFAULT_MIN_VARIANTS,
    target_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute variant coverage for every ``(archetypeKey, level)`` pair in a single drill document."""
    unit_code = str(drill_doc.get("unitCode") or "").strip()
    label = target_label or str(drill_doc.get("drillId") or unit_code or "<drill>")
    problems = [p for p in (drill_doc.get("problems") or []) if isinstance(p, dict)]
    return _summarize_coverage(
        target=label,
        unit_code=unit_code,
        drill_count=1,
        problems=problems,
        variants_dir=variants_dir,
        min_variants=min_variants,
    )


def collect_uncovered_pairs(repo_root: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Return uncovered coverage entries keyed by drill ID for canonical math drills."""
    data_root = repo_root / "drills" / "data"
    variants_dir = str(repo_root / "drills" / "variants")
    uncovered = {}
    for scope in sorted(data_root.iterdir()):
        # PRG-* drills have no Similar banks. Only MTH-* is in scope for this gate.
        if not scope.name.startswith("MTH-"):
            continue
        for path in sorted(scope.glob("*.json")):
            drill_file = assert_safe_contained_path(path, data_root, suffixes=JSON_SUFFIXES)
            drill = json.loads(drill_file.read_text(encoding="utf-8"))
            gaps = compute_drill_coverage(drill, variants_dir=variants_dir)["uncoveredPairs"]
            if gaps:
                uncovered[drill.get("drillId") or path.stem] = gaps
    return uncovered


def check_variant_bank_warnings(
    bank_doc: Dict[str, Any],
    vault_dir: Optional[str] = None,
) -> List[str]:
    """Return non-blocking warnings (figure titles + distractor provenance) for a variant bank."""
    unit_code = bank_doc.get("unitCode")
    variants = [v for v in (bank_doc.get("variants") or []) if isinstance(v, dict)]
    if not unit_code or not variants:
        return []
    vault_archs = load_scope_archetypes(str(unit_code), vault_dir=vault_dir)
    checked: List[Dict[str, Any]] = []
    prov_warnings: List[str] = []
    for idx, original in enumerate(variants, 1):
        if is_quarantined_variant(original, bank_doc):
            continue
        prob = copy.deepcopy(original)
        prob["id"] = str(original.get("variantId") or original.get("id") or f"V{idx:02d}")
        autofill_problem_figure(prob, vault_archs)
        checked.append(prob)
        _, p_warns = check_distractor_provenance(prob, vault_archs)
        prov_warnings.extend(p_warns)
    return list(dict.fromkeys([*collect_figure_title_warnings(checked), *prov_warnings]))


def check_variant_bank_report(
    bank_doc: Dict[str, Any],
    data_root: Optional[str] = None,
    vault_dir: Optional[str] = None,
    rules: Optional[Dict[str, Any]] = None,
    check_originality: bool = True,
    sources_dir: Optional[str] = None,
    originality_unit: Optional[str] = None,
) -> Dict[str, Any]:
    """Run all variant bank gates and return structured errors, warnings, and originality skip status."""
    errors = check_variant_bank(
        bank_doc,
        data_root=data_root,
        vault_dir=vault_dir,
        rules=rules,
        check_originality=False,
    )
    doc = bank_doc if isinstance(bank_doc, dict) else {}
    warnings = check_variant_bank_warnings(doc, vault_dir=vault_dir)
    active_doc = active_variant_document(doc)
    n = len(active_doc["variants"])
    raw_variants = doc.get("variants")
    quarantined = (
        sum(isinstance(v, dict) and is_quarantined_variant(v, doc) for v in raw_variants)
        if isinstance(raw_variants, list)
        else 0
    )
    unit_code = str(doc.get("unitCode") or "")
    if not n:
        orig = {"status": "not-applicable", "checkedVariants": 0, "skippedVariants": 0, "reason": None, "errors": []}
    elif not check_originality:
        orig = {
            "status": "skipped",
            "checkedVariants": 0,
            "skippedVariants": n,
            "reason": "disabled by --no-originality",
            "errors": [],
        }
    else:
        resolved_sources = resolve_sources_dir(sources_dir=sources_dir)
        if not os.path.isdir(resolved_sources):
            orig = {
                "status": "skipped",
                "checkedVariants": 0,
                "skippedVariants": n,
                "reason": f"sources directory not found ({resolved_sources})",
                "errors": [],
            }
        else:
            orig_errors, orig_notice = check_document_originality(
                active_doc,
                unit_code=originality_unit or unit_code,
                sources_dir=resolved_sources,
            )
            if orig_notice:
                orig = {
                    "status": "skipped",
                    "checkedVariants": 0,
                    "skippedVariants": n,
                    "reason": orig_notice,
                    "errors": orig_errors,
                }
            else:
                orig = {
                    "status": "checked",
                    "checkedVariants": n,
                    "skippedVariants": 0,
                    "reason": None,
                    "errors": orig_errors,
                }
            errors = list(dict.fromkeys([*errors, *orig_errors]))
    return {
        "unitCode": unit_code,
        "variantCount": n,
        "quarantinedCount": quarantined,
        "errors": errors,
        "warnings": warnings,
        "originality": orig,
    }


def find_orphaned_variant_banks(
    repo_root: Optional[Path] = None,
    *,
    variants_dir: Optional[str] = None,
    data_root: Optional[str] = None,
) -> Dict[str, Any]:
    """Read-only listing of math variant banks with zero matching active drill (archetypeKey, level) pairs."""
    root = repo_root or Path(find_repo_root())
    droot = Path(data_root) if data_root else (root / "drills" / "data")
    vroot = Path(variants_dir) if variants_dir else (root / "drills" / "variants")

    active_pairs: set[Tuple[str, int]] = set()
    if droot.is_dir():
        for scope in sorted(droot.iterdir()):
            if not scope.is_dir() or not scope.name.startswith("MTH-"):
                continue
            for path in sorted(scope.glob("*.json")):
                drill_file = assert_safe_contained_path(path, droot, suffixes=JSON_SUFFIXES)
                doc = json.loads(drill_file.read_text(encoding="utf-8"))
                for prob in doc.get("problems") or []:
                    if not isinstance(prob, dict):
                        continue
                    key, lv = prob.get("archetypeKey"), prob.get("level")
                    if isinstance(key, str) and key.strip() and isinstance(lv, int):
                        active_pairs.add((key.strip(), lv))

    orphaned: List[Dict[str, Any]] = []
    total_variants = 0
    total_quarantined = 0
    if vroot.is_dir():
        for path in sorted(vroot.glob("MTH-*.json")):
            bank_file = assert_safe_contained_path(path, vroot, suffixes=JSON_SUFFIXES)
            doc = json.loads(bank_file.read_text(encoding="utf-8"))
            unit_code = str(doc.get("unitCode") or path.stem)
            variants = [v for v in (doc.get("variants") or []) if isinstance(v, dict)]
            active = active_variant_document(doc)["variants"]
            quarantined = len(variants) - len(active)
            bank_pairs = {
                (str(v.get("archetypeKey")).strip(), v.get("level"))
                for v in active
                if isinstance(v.get("archetypeKey"), str)
                and str(v.get("archetypeKey")).strip()
                and isinstance(v.get("level"), int)
            }
            if not (bank_pairs & active_pairs):
                rel_path = str(bank_file.relative_to(root)) if bank_file.is_relative_to(root) else str(bank_file)
                arch_keys = sorted({k for k, _ in bank_pairs})
                orphaned.append(
                    {
                        "unitCode": unit_code,
                        "path": rel_path,
                        "variantCount": len(variants),
                        "quarantinedVariantCount": quarantined,
                        "archetypeKeys": arch_keys,
                        "reason": "no matching active drill pair",
                    }
                )
                total_variants += len(variants)
                total_quarantined += quarantined

    return {
        "bankCount": len(orphaned),
        "variantCount": total_variants,
        "quarantinedVariantCount": total_quarantined,
        "orphanedBanks": orphaned,
    }


def format_orphaned_banks_report(report: Dict[str, Any]) -> str:
    """Format ``find_orphaned_variant_banks`` output as a read-only CLI listing (no deletions)."""
    banks = report.get("orphanedBanks") or []
    if not banks:
        return "Orphaned variant banks (read-only): 0 bank(s), 0 variant(s)."
    lines = [
        f"Orphaned variant banks (read-only; no files deleted): "
        f"{report['bankCount']} bank(s), {report['variantCount']} variant(s) "
        f"({report['quarantinedVariantCount']} quarantined)."
    ]
    for entry in banks:
        lines.append(
            f"  ORPHAN {entry['unitCode']}: {entry['variantCount']} variant(s), "
            f"{entry['quarantinedVariantCount']} quarantined ({entry['path']}) — {entry['reason']}"
        )
    return "\n".join(lines)


def check_coverage_gate(repo_root: Optional[Path] = None) -> Tuple[bool, str]:
    """Check canonical math drill coverage against the shrink-only baseline."""
    root = repo_root or Path(find_repo_root())
    baseline = json.loads((root / COVERAGE_BASELINE_PATH).read_text(encoding="utf-8"))
    expected = {(drill, arch, level) for drill, pairs in baseline.items() for arch, level in pairs}
    uncovered = collect_uncovered_pairs(root)
    actual = {
        (drill, entry["archetypeKey"], entry["level"]): entry
        for drill, entries in uncovered.items()
        for entry in entries
    }
    new = actual.keys() - expected
    stale = expected - actual.keys()
    passed = not (new or stale)
    lines = [
        f"{'PASS' if passed else 'FAIL'} Similar variant coverage gate "
        f"(minimum {DEFAULT_MIN_VARIANTS} variants per pair)."
    ]
    for key, entry in sorted(actual.items()):
        drill, arch, level = key
        status = "FAIL New uncovered pair" if key in new else "Baseline uncovered pair"
        lines.append(
            f"{status}: {drill} {arch} @ L{level} (have {entry['variantCount']}, need {entry['needed']} more)."
        )
    if new:
        lines.append("Add reviewed Similar variants to cover new pairs. Adding baseline entries is forbidden.")
    for drill, arch, level in sorted(stale):
        pair = json.dumps([arch, level])
        lines.append(
            f"FAIL Stale baseline entry: {drill} {arch} @ L{level} is covered or no longer used. "
            f"Delete {pair} under {drill} in {COVERAGE_BASELINE_PATH}."
        )
    if stale:
        lines.append("Remove any drill key left with an empty list.")
    lines.append(f"Baseline: {len(baseline)} drill(s), {len(expected)} pair(s).")
    orphans = find_orphaned_variant_banks(root)
    if orphans["bankCount"]:
        summary = ", ".join(f"{b['unitCode']} ({b['variantCount']})" for b in orphans["orphanedBanks"])
        lines.append(
            f"Orphaned variant banks (read-only): {orphans['bankCount']} bank(s), "
            f"{orphans['variantCount']} variant(s): {summary}."
        )
    return passed, "\n".join(lines)


def compute_coverage(
    target: str,
    *,
    variants_dir: Optional[str] = None,
    data_root: Optional[str] = None,
    min_variants: int = DEFAULT_MIN_VARIANTS,
) -> Dict[str, Any]:
    """Compute Similar-bank variant coverage for a unit/chapter code or a drill JSON file."""
    if target.endswith(".json") and os.path.isfile(target):
        with open(target, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        return compute_drill_coverage(
            doc,
            variants_dir=variants_dir,
            min_variants=min_variants,
            target_label=target,
        )

    root = _drills_data_root(data_root)
    candidate_dirs: List[str] = []
    exact = os.path.join(root, target)
    if os.path.isdir(exact):
        candidate_dirs.append(exact)
    if os.path.isdir(root):
        for entry in sorted(os.listdir(root)):
            full = os.path.join(root, entry)
            if os.path.isdir(full) and entry.startswith(target + "-U") and full not in candidate_dirs:
                candidate_dirs.append(full)

    drill_count = 0
    problems: List[Dict[str, Any]] = []
    for d in candidate_dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.json"))):
            try:
                file = assert_safe_contained_path(path, Path(root), suffixes=JSON_SUFFIXES)
                with file.open("r", encoding="utf-8") as fh:
                    doc = json.load(fh)
            except (OSError, ValueError):
                continue
            drill_count += 1
            for prob in doc.get("problems") or []:
                if isinstance(prob, dict):
                    problems.append(prob)

    return _summarize_coverage(
        target=target,
        unit_code=target,
        drill_count=drill_count,
        problems=problems,
        variants_dir=variants_dir,
        min_variants=min_variants,
    )


def format_coverage_report(report: Dict[str, Any]) -> str:
    """Format ``compute_coverage`` output as a readable CLI report."""
    min_v = int(report["minVariants"])
    lines = [
        f"Similar variant coverage for {report['target']} "
        f"({report['drillCount']} drill(s), {report['totalPairs']} (archetypeKey, level) pair(s), min={min_v})",
    ]
    pairs = report.get("pairs") or []
    if not pairs:
        lines.append("  (no drill problems found)")
        return "\n".join(lines)

    for entry in pairs:
        status = "OK " if entry["covered"] else "LOW"
        extra_bits = [f"{entry['drillProblems']} drill problem(s)"]
        if not entry["covered"]:
            extra_bits.insert(0, f"need {entry['needed']} more")
        if entry["archetypeTotalVariants"] != entry["variantCount"]:
            extra_bits.append(f"total across levels: {entry['archetypeTotalVariants']}")
        lines.append(
            f"  {status}  {entry['archetypeKey']} @ L{entry['level']}: "
            f"{entry['variantCount']} variant(s) ({'; '.join(extra_bits)})"
        )

    uncovered_n = len(report.get("uncoveredPairs") or [])
    lines.append(
        f"Summary: {report['coveredPairs']}/{report['totalPairs']} pair(s) covered (>= {min_v} variants), "
        f"{uncovered_n} uncovered (< {min_v})."
    )
    return "\n".join(lines)


def format_coverage_warning(
    drill_doc: Dict[str, Any],
    *,
    variants_dir: Optional[str] = None,
    min_variants: int = DEFAULT_MIN_VARIANTS,
    drill_path: Optional[str] = None,
) -> Optional[str]:
    """Return a non-blocking single-line warning if ``drill_doc`` has uncovered pairs, else None."""
    report = compute_drill_coverage(
        drill_doc,
        variants_dir=variants_dir,
        min_variants=min_variants,
        target_label=drill_path or drill_doc.get("drillId"),
    )
    uncovered = report.get("uncoveredPairs") or []
    if not uncovered:
        return None
    items = ", ".join(f"{e['archetypeKey']}@L{e['level']} ({e['variantCount']}/{min_variants})" for e in uncovered)
    target_hint = drill_path or drill_doc.get("unitCode") or ""
    return (
        f"WARNING: Similar variant bank has {len(uncovered)} uncovered pair(s) (< {min_variants} variants): "
        f"{items}. Run: python -m math_engine.variant_bank --coverage {target_hint}. "
        "Check CI readiness with: python -m math_engine.variant_bank --coverage-gate"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate, append, or inspect coverage of math variant banks.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", metavar="FILE_OR_UNIT", help="Validate a variant bank JSON file or unit code.")
    group.add_argument("--add", metavar="DRAFT_JSON", help="Gate and append variants from a draft JSON file.")
    group.add_argument(
        "--coverage",
        metavar="UNIT_OR_DRILL",
        help="Report variant counts per (archetypeKey, level) used by a unit's drills or a drill JSON file.",
    )
    group.add_argument(
        "--coverage-gate",
        action="store_true",
        help="Check all math drills against the shrink-only Similar coverage baseline.",
    )
    group.add_argument(
        "--reverify",
        metavar="UNIT",
        help="Run current gates on quarantined variants in UNIT and list which pass (add --apply to un-quarantine passing ones).",
    )
    group.add_argument(
        "--orphans",
        action="store_true",
        help="Read-only listing of math variant banks with no matching active drill (no deletions).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="With --reverify: un-quarantine variants that pass every current gate and save the bank.",
    )
    parser.add_argument("--unit", help="Unit code override (optional with --add).")
    parser.add_argument(
        "--min-variants",
        type=int,
        default=DEFAULT_MIN_VARIANTS,
        help=f"Minimum variants per (archetypeKey, level) for --coverage (default: {DEFAULT_MIN_VARIANTS}).",
    )
    parser.add_argument(
        "--json", action="store_true", help="With --coverage, --orphans, or --reverify: print structured JSON output."
    )
    parser.add_argument(
        "--originality",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="With --check: run the source originality gate (default: ON when sources dir exists, skipped with a notice when absent).",
    )
    parser.add_argument(
        "--sources-dir",
        default=None,
        help="Override sources directory for --originality (default: LEARNINGOS_SOURCES_DIR or <main>/sources).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.coverage_gate:
        try:
            passed, report = check_coverage_gate()
        except (OSError, ValueError) as exc:
            print(f"FAIL Could not check the Similar variant coverage gate: {exc}")
            return 1
        print(report)
        return 0 if passed else 1

    if args.reverify:
        try:
            report = reverify_quarantined_variants(
                args.reverify,
                check_originality=args.originality is not False,
                sources_dir=args.sources_dir,
                apply=args.apply,
            )
        except (OSError, ValueError, VariantBankError) as exc:
            print(f"FAIL Could not reverify quarantined variants for '{args.reverify}': {exc}")
            return 1
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(format_reverify_report(report))
        return 0

    if args.orphans:
        try:
            report = find_orphaned_variant_banks(
                variants_dir=os.environ.get("VARIANTS_DIR") or None,
                data_root=os.environ.get("DRILLS_DATA_DIR") or None,
            )
        except (OSError, ValueError) as exc:
            print(f"FAIL Could not list orphaned variant banks: {exc}")
            return 1
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(format_orphaned_banks_report(report))
        return 0

    if args.coverage:
        try:
            report = compute_coverage(args.coverage, min_variants=args.min_variants)
        except (OSError, ValueError) as exc:
            print(f"FAIL Could not compute variant coverage for '{args.coverage}': {exc}")
            return 1
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(format_coverage_report(report))
        return 0

    if args.check:
        try:
            doc = load_bank(args.check)
        except OSError as exc:
            print(f"FAIL Could not read variant bank '{args.check}': {exc}")
            return 1
        except ValueError as exc:
            print(f"FAIL Invalid JSON in '{args.check}': {exc}")
            return 1
        report = check_variant_bank_report(
            doc,
            check_originality=args.originality is not False,
            sources_dir=args.sources_dir,
            originality_unit=args.unit,
        )
        errs = report["errors"]
        originality = report["originality"]
        if originality["status"] == "skipped" and args.originality is not False:
            reason = originality["reason"]
            print(
                f"NOTE: {reason}"
                if reason.startswith("Originality gate skipped")
                else f"NOTE: Originality gate skipped: {reason}."
            )
        for warn in report["warnings"]:
            print(f"WARNING: {warn}")
        for line in errs:
            print(f"  FAIL {line}")
        n = report["variantCount"]
        counts = f"{n} checked, {report['quarantinedCount']} quarantined skipped"
        if originality["status"] == "skipped":
            orig_tail = f"originality skipped ({n}/{n} variants skipped: {originality['reason']})"
        elif originality["status"] == "checked":
            orig_tail = f"originality checked (0/{n} variants skipped)"
        else:
            orig_tail = "no eligible variants for originality"
        if errs:
            print(f"\n{len(errs)} error(s) in {report['unitCode']} ({counts}); {orig_tail}.")
            return 1
        print(f"OK: {report['unitCode']} ({counts}); {orig_tail}.")
        return 0

    if args.add:
        with open(args.add, "r", encoding="utf-8") as fh:
            draft = json.load(fh)
        try:
            saved = add_variants(draft, unit_code=args.unit)
        except VariantBankError as exc:
            print(f"FAIL {exc}")
            return 1
        print(f"OK: {saved['unitCode']} now holds {len(saved['variants'])} gated variant(s).")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
