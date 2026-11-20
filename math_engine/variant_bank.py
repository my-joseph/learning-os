# -*- coding: utf-8 -*-
"""Math Variant Bank: gated bank storage, uniqueness checks, and template seeding.

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
import random
import re
import tempfile
from typing import Any, Callable, Dict, List, Optional, Tuple

from math_engine.ai_drill_ingest import (
    AiContractError,
    autofill_problem_figure,
    load_scope_archetypes,
    normalize_prompt_numbers,
    require_figure_decision,
    require_figure_if_declared,
    story_text,
    validate_against_vault,
    validate_ai_problem_contract,
    validate_review,
)
from math_engine.answer_check import check_answer
from math_engine.fmt import LEVEL_LABELS
from math_engine.source_cores import resolve_sources_dir
from math_engine.source_cores.originality import check_document_originality
from math_engine.templates import load_unit
from math_engine.verify import verify_problem
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


def bank_path(unit_code: str, variants_dir: Optional[str] = None) -> str:
    """Return the JSON path for ``unit_code``'s variant bank."""
    base = variants_dir or variants_root()
    return os.path.join(base, f"{unit_code}.json")


def load_bank(unit_code_or_path: str, variants_dir: Optional[str] = None) -> Dict[str, Any]:
    """Load a variant bank from a file path or a unit code."""
    if unit_code_or_path.endswith(".json") and os.path.exists(unit_code_or_path):
        path = unit_code_or_path
    else:
        path = bank_path(unit_code_or_path, variants_dir=variants_dir)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_bank(unit_code: str, bank_doc: Dict[str, Any], variants_dir: Optional[str] = None) -> str:
    """Atomically write ``bank_doc`` to ``drills/variants/<unit_code>.json`` (content only)."""
    clean_doc: Dict[str, Any] = {
        "unitCode": unit_code,
        "variants": copy.deepcopy(bank_doc.get("variants") or []),
    }
    for var in clean_doc["variants"]:
        if isinstance(var, dict):
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


def find_variant(
    variant_id: str,
    variants_dir: Optional[str] = None,
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Locate ``(bank_doc, variant)`` for ``variant_id`` under ``variants_dir``."""
    if not isinstance(variant_id, str) or not variant_id.strip():
        return None
    base = variants_dir or variants_root()
    if not os.path.isdir(base):
        return None

    files = sorted(glob.glob(os.path.join(base, "*.json")))
    # Prefer bank files whose unitCode matches the prefix after "VAR-".
    if variant_id.startswith("VAR-"):
        tail = variant_id[4:]
        files.sort(key=lambda p: (0 if tail.startswith(os.path.basename(p)[:-5] + "-") else 1, p))

    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        for var in doc.get("variants") or []:
            if isinstance(var, dict) and var.get("variantId") == variant_id:
                return doc, var
    return None


def _drills_data_root(data_root: Optional[str] = None) -> str:
    if data_root is not None:
        return data_root
    if os.environ.get("DRILLS_DATA_DIR"):
        return os.environ["DRILLS_DATA_DIR"]
    return os.path.join(find_repo_root(), "drills", "data")


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
                with open(path, "r", encoding="utf-8") as fh:
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

        # 2026-11-19 rule: choice problems omit plainText
        if (original.get("answerSpec") or {}).get("type") == "choice" and "plainText" in original:
            errors.append(f"[{vid}] Choice variant must omit 'plainText' (2026-11-19 rule).")

        prob = copy.deepcopy(original)
        prob["id"] = str(original.get("variantId") or original.get("id") or f"V{idx:02d}")
        prob.setdefault("verificationLevel", "partial")
        pid = prob["id"]

        var_errors_before = len(errors)
        try:
            validate_against_vault(prob, vault_archs, unit_code)
            if "review" in prob:
                validate_review(prob)
        except AiContractError as exc:
            errors.append(str(exc))

        try:
            require_figure_decision(prob, vault_archs)
            autofill_problem_figure(prob, vault_archs)
            require_figure_if_declared(prob, vault_archs)
            validate_ai_problem_contract(prob)
            verify_problem(prob, rules=active_rules)
        except Exception as exc:  # noqa: BLE001 - report every gate error in one pass
            msg = str(exc)
            errors.append(msg if pid in msg else f"[{pid}] {msg}")

        uniq_errors = check_variant_uniqueness(prob, drill_items + accepted)
        errors.extend(uniq_errors)

        if len(errors) == var_errors_before:
            accepted.append((pid, prob))
        else:
            # Still record for duplicate detection against later variants in the same bank
            accepted.append((pid, prob))

    if check_originality:
        orig_errors, _ = check_document_originality(bank_doc, unit_code=unit_code, sources_dir=sources_dir)
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
    else:
        combined_variants = []

    vault_archs = load_scope_archetypes(resolved_unit, vault_dir=vault_dir)
    for item in raw_items:
        prepared = _prepare_variant_for_bank(item, resolved_unit, combined_variants, vault_archs)
        combined_variants.append(prepared)

    candidate_doc = {"unitCode": resolved_unit, "variants": combined_variants}
    strip_progress({"problems": candidate_doc["variants"]})
    errs = check_variant_bank(candidate_doc, data_root=data_root, vault_dir=vault_dir, rules=rules)
    if errs:
        raise VariantBankError("Variant bank gates failed:\n" + "\n".join(f"  - {e}" for e in errs))

    save_bank(resolved_unit, candidate_doc, variants_dir=variants_dir)
    return candidate_doc


def _adapt_legacy_template_problem(
    raw: Dict[str, Any],
    tpl: Dict[str, Any],
    vault_archs: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Best-effort adapter from legacy ``math_engine/templates`` output to contract-compliant variant."""
    prob = copy.deepcopy(raw)
    trap_tag = prob.get("commonTrapTag") or tpl.get("trapTag")
    arch = next(
        (
            a
            for a in vault_archs
            if a.get("archetypeKey") == tpl.get("key")
            or trap_tag in [(t.get("trapTag") if isinstance(t, dict) else t) for t in (a.get("cognitiveTraps") or [])]
        ),
        None,
    )
    if arch is None:
        return None

    prob["archetypeKey"] = arch["archetypeKey"]
    prob["sourceArchetype"] = arch["archetypeKey"]
    prob["level"] = int(prob.get("level") or tpl.get("level") or arch.get("level") or 1)
    prob["verificationLevel"] = "partial"
    prob["context"] = ""
    if "trapValue" not in prob and (prob.get("verify") or {}).get("trapValue") is not None:
        prob["trapValue"] = prob["verify"]["trapValue"]

    if not prob.get("givens"):
        nums = normalize_prompt_numbers(story_text(prob), keep_exponents=True)
        prob["givens"] = {f"n{i}": int(v) if float(v).is_integer() else v for i, v in enumerate(nums, 1)}
    prob.setdefault("constants", {})
    return prob


def _resolve_template_builders(
    unit_code: str,
    vault_archs: List[Dict[str, Any]],
) -> Dict[str, Callable[[random.Random], Optional[Dict[str, Any]]]]:
    """Return ``{archetypeKey: builder(rng) -> problem_dict}`` for ``unit_code``."""
    mod = load_unit(unit_code)
    explicit = getattr(mod, "VARIANT_TEMPLATES", None)
    if isinstance(explicit, dict) and explicit:
        return dict(explicit)

    # Fallback: adapt legacy TEMPLATES entries that map cleanly onto vault archetypes.
    builders: Dict[str, Callable[[random.Random], Optional[Dict[str, Any]]]] = {}
    for tpl in getattr(mod, "TEMPLATES", []):
        sample = _adapt_legacy_template_problem(tpl["build"](random.Random(1)), tpl, vault_archs)
        if sample is None:
            continue
        arch_key = sample["archetypeKey"]
        if arch_key in builders:
            continue

        def _make_builder(template_spec: Dict[str, Any]) -> Callable[[random.Random], Optional[Dict[str, Any]]]:
            return lambda rng: _adapt_legacy_template_problem(template_spec["build"](rng), template_spec, vault_archs)

        builders[arch_key] = _make_builder(tpl)
    return builders


def generate_variants_from_templates(
    unit_code: str,
    per_archetype: int = 3,
    seed: int = 20261119,
    variants_dir: Optional[str] = None,
    data_root: Optional[str] = None,
    vault_dir: Optional[str] = None,
    rules: Optional[Dict[str, Any]] = None,
    overwrite: bool = False,
) -> Dict[str, Any]:
    """Deterministically generate and gate ``per_archetype`` variants per template archetype."""
    if per_archetype < 1:
        raise ValueError("--per-archetype must be >= 1.")

    vault_archs = load_scope_archetypes(unit_code, vault_dir=vault_dir)
    if not vault_archs:
        raise VariantBankError(f"No reasoning vault archetypes found for '{unit_code}'.")

    builders = _resolve_template_builders(unit_code, vault_archs)
    if not builders:
        raise VariantBankError(f"Unit '{unit_code}' templates do not map to any vault archetypes.")

    path = bank_path(unit_code, variants_dir=variants_dir)
    if not overwrite and os.path.exists(path):
        existing_doc = load_bank(path, variants_dir=variants_dir)
        variants = copy.deepcopy(existing_doc.get("variants") or [])
    else:
        variants = []

    drill_items = load_scope_drill_problems(unit_code, data_root=data_root)
    active_rules = rules or QUALITY_RULES
    rng = random.Random(seed)

    for arch_key, builder in builders.items():
        current_for_arch = [v for v in variants if (v.get("archetypeKey") or v.get("sourceArchetype")) == arch_key]
        needed = per_archetype - len(current_for_arch)
        if needed <= 0:
            continue

        added = 0
        attempts = 0
        max_attempts = max(120, needed * 40)
        while added < needed and attempts < max_attempts:
            attempts += 1
            raw = builder(rng)
            if not isinstance(raw, dict):
                continue

            prepared = _prepare_variant_for_bank(raw, unit_code, variants, vault_archs)
            prob_copy = copy.deepcopy(prepared)

            try:
                validate_against_vault(prob_copy, vault_archs, unit_code)
                require_figure_decision(prob_copy, vault_archs)
                autofill_problem_figure(prob_copy, vault_archs)
                require_figure_if_declared(prob_copy, vault_archs)
                validate_ai_problem_contract(prob_copy)
                verify_problem(prob_copy, rules=active_rules)
            except Exception:
                continue

            existing_items = drill_items + [(str(v.get("variantId") or v.get("id") or "?"), v) for v in variants]
            if check_variant_uniqueness(prob_copy, existing_items):
                continue

            # Keep clean verified fields (including fingerprint and qualityGates)
            prepared["fingerprint"] = prob_copy.get("fingerprint") or compute_fingerprint(prepared)
            if "qualityGates" in prob_copy:
                prepared["qualityGates"] = prob_copy["qualityGates"]
            if "figure" in prob_copy:
                prepared["figure"] = prob_copy["figure"]
            variants.append(prepared)
            added += 1

        if added < needed:
            raise VariantBankError(
                f"Could only generate {len(current_for_arch) + added}/{per_archetype} distinct gated "
                f"variants for '{arch_key}' in '{unit_code}' after {attempts} attempts."
            )

    bank_doc = {"unitCode": unit_code, "variants": variants}
    errs = check_variant_bank(bank_doc, data_root=data_root, vault_dir=vault_dir, rules=active_rules)
    if errs:
        raise VariantBankError("Generated variant bank failed final check:\n" + "\n".join(f"  - {e}" for e in errs))

    save_bank(unit_code, bank_doc, variants_dir=variants_dir)
    return bank_doc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate, append, or seed math variant banks.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", metavar="FILE_OR_UNIT", help="Validate a variant bank JSON file or unit code.")
    group.add_argument("--add", metavar="DRAFT_JSON", help="Gate and append variants from a draft JSON file.")
    group.add_argument(
        "--from-templates",
        metavar="UNIT",
        help="Deterministically generate gated variants from math_engine/templates for UNIT.",
    )
    parser.add_argument("--unit", help="Unit code override (optional with --add).")
    parser.add_argument(
        "--per-archetype",
        type=int,
        default=3,
        help="Number of variants per archetype for --from-templates (default: 3).",
    )
    parser.add_argument("--seed", type=int, default=20261119, help="Deterministic RNG seed for --from-templates.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing bank file on --from-templates.")
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

    if args.check:
        try:
            doc = load_bank(args.check)
        except OSError as exc:
            print(f"FAIL Could not read variant bank '{args.check}': {exc}")
            return 1
        except ValueError as exc:
            print(f"FAIL Invalid JSON in '{args.check}': {exc}")
            return 1
        errs = check_variant_bank(doc)
        resolved_sources = resolve_sources_dir(sources_dir=args.sources_dir)
        if args.originality is False:
            pass
        elif not os.path.isdir(resolved_sources):
            print(f"NOTE: Originality gate skipped (sources directory not found: {resolved_sources}).")
        else:
            orig_errors, orig_notice = check_document_originality(
                doc,
                unit_code=args.unit or doc.get("unitCode"),
                sources_dir=resolved_sources,
            )
            if orig_notice:
                print(f"NOTE: {orig_notice}")
            errs.extend(orig_errors)
        for line in errs:
            print(f"  FAIL {line}")
        n = len(doc.get("variants") or [])
        if errs:
            print(f"\n{len(errs)} error(s) across {n} variant(s).")
            return 1
        print(f"OK: all {n} variants in {doc.get('unitCode')} pass every gate.")
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

    if args.from_templates:
        try:
            saved = generate_variants_from_templates(
                args.from_templates,
                per_archetype=args.per_archetype,
                seed=args.seed,
                overwrite=args.overwrite,
            )
        except (VariantBankError, KeyError, ValueError) as exc:
            print(f"FAIL {exc}")
            return 1
        print(
            f"OK: generated and verified {len(saved['variants'])} variant(s) for "
            f"{saved['unitCode']} -> {bank_path(saved['unitCode'])}"
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
