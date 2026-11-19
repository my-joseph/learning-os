"""Tests for math_engine.variant_bank gates, template generation, and variantId answer checking."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from math_engine import answer_check, variant_bank

ROOT = Path(__file__).resolve().parent.parent


def _load_seed_bank() -> dict:
    with open(ROOT / "drills" / "variants" / "MTH-T01-C04.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


def _sample_variant(archetype_key: str = "c04-fraction-simplification-gcf") -> dict:
    bank = _load_seed_bank()
    return copy.deepcopy(next(v for v in bank["variants"] if v["archetypeKey"] == archetype_key))


def test_seed_bank_passes_all_gates() -> None:
    bank = _load_seed_bank()
    assert bank["unitCode"] == "MTH-T01-C04"
    assert len(bank["variants"]) >= 15
    errs = variant_bank.check_variant_bank(bank)
    assert errs == []

    # Verify at least 3 distinct variants per seeded archetype and content-only schema.
    counts: dict[str, int] = {}
    for var in bank["variants"]:
        assert "state" not in var
        assert var["sourceArchetype"] == var["archetypeKey"]
        assert var["variantId"].startswith(f"VAR-MTH-T01-C04-{var['archetypeKey']}-")
        counts[var["archetypeKey"]] = counts.get(var["archetypeKey"], 0) + 1
    assert all(c >= 3 for c in counts.values())


def test_gate_rejects_copy_of_existing_drill_problem() -> None:
    with open(ROOT / "drills" / "data" / "MTH-T01-C04" / "DRL-MTH-T01-C04-01.json", "r", encoding="utf-8") as fh:
        drill = json.load(fh)
    drill_q01 = copy.deepcopy(drill["problems"][0])
    drill_q01["variantId"] = "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-99"
    drill_q01["sourceArchetype"] = drill_q01["archetypeKey"]
    drill_q01["id"] = drill_q01["variantId"]

    errs = variant_bank.check_variant_bank({"unitCode": "MTH-T01-C04", "variants": [drill_q01]})
    assert any("duplicates" in e or "same answer" in e for e in errs), errs


def test_gate_rejects_different_numbers_with_same_answer_as_drill() -> None:
    # DRL-MTH-T01-C04-01 Q01 reduces 27/45 -> 3/5. A variant reducing 18/30 -> 3/5 shares the same answer.
    var = _sample_variant("c04-fraction-simplification-gcf")
    var["variantId"] = "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-98"
    var["id"] = var["variantId"]
    var["prompt"] = "Reduce $\\frac{18}{30}$ to lowest terms."
    var["display"] = "\\frac{18}{30}"
    var["plainText"] = "18/30"
    var["givens"] = {"a": 18, "b": 30}
    var["trapGivens"] = [18, 30]
    var["answerSpec"]["value"] = "3/5"
    var["answerPlain"] = "3/5"
    var["answerDisplay"] = "\\frac{3}{5}"
    var["trapDerivation"] = "(30 - 18) / 30"
    var["trapValue"] = "2/5"
    var["verify"] = {"source": "18 / 30", "trapValue": "2/5"}
    var["steps"] = [
        {
            "latex": "\\frac{18}{30} = \\frac{3 \\cdot 6}{5 \\cdot 6}",
            "explain": "Factor out the greatest common divisor.",
            "eq": ["18 / 30", "(3 * 6) / (5 * 6)"],
        },
        {
            "latex": "\\frac{3 \\cdot 6}{5 \\cdot 6} = \\frac{3}{5}",
            "explain": "Cancel the common factor.",
            "val": "3/5",
        },
    ]

    errs = variant_bank.check_variant_bank({"unitCode": "MTH-T01-C04", "variants": [var]})
    assert any("same answer" in e for e in errs), errs


def test_gate_rejects_duplicate_variant_within_bank() -> None:
    v1 = _sample_variant("c04-fraction-simplification-gcf")
    v2 = copy.deepcopy(v1)
    v2["variantId"] = "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-97"
    v2["id"] = v2["variantId"]

    errs = variant_bank.check_variant_bank({"unitCode": "MTH-T01-C04", "variants": [v1, v2]})
    assert any("duplicates" in e or "same answer" in e for e in errs), errs


def test_gate_rejects_hint_leaks_and_solution_leaks() -> None:
    # 1. Numeric leak in checkpointHint (00_core §6)
    v_hint_num = _sample_variant("c04-fraction-simplification-gcf")
    v_hint_num["checkpointHint"] = "Divide numerator and denominator by 11."
    errs_num = variant_bank.check_variant_bank({"unitCode": "MTH-T01-C04", "variants": [v_hint_num]})
    assert any("checkpointHint" in e for e in errs_num), errs_num

    # 2. Direct answer leak in inputHint
    v_input_leak = _sample_variant("c04-fraction-simplification-gcf")
    v_input_leak["inputHint"] = f"Enter a reduced fraction, e.g. {v_input_leak['answerPlain']}"
    errs_in = variant_bank.check_variant_bank({"unitCode": "MTH-T01-C04", "variants": [v_input_leak]})
    assert any("leak" in e.lower() or "anti-leak" in e.lower() for e in errs_in), errs_in

    # 3. Solution leak in prompt (07 §4.7)
    v_sol_leak = _sample_variant("c04-fraction-multiplication-product")
    v_sol_leak["prompt"] = (
        f"Compute the fraction product by evaluating "
        f"$\\frac{{{v_sol_leak['givens']['a']} \\times {v_sol_leak['givens']['c']}}}{{{v_sol_leak['givens']['b']} \\times {v_sol_leak['givens']['d']}}}$."
    )
    errs_sol = variant_bank.check_variant_bank({"unitCode": "MTH-T01-C04", "variants": [v_sol_leak]})
    assert any("gives away the solution" in e for e in errs_sol), errs_sol


def test_gate_rejects_choice_plaintext_and_learner_state_and_bad_vault() -> None:
    # 1. Learner state forbidden
    v_state = _sample_variant()
    v_state["state"] = {"score": 1}
    errs_state = variant_bank.check_variant_bank({"unitCode": "MTH-T01-C04", "variants": [v_state]})
    assert any("content only" in e for e in errs_state), errs_state

    # 2. Unknown archetype / trap tag
    v_bad_arch = _sample_variant()
    v_bad_arch["archetypeKey"] = "c04-nonexistent-archetype"
    v_bad_arch["sourceArchetype"] = "c04-nonexistent-archetype"
    v_bad_arch["variantId"] = "VAR-MTH-T01-C04-c04-nonexistent-archetype-01"
    errs_arch = variant_bank.check_variant_bank({"unitCode": "MTH-T01-C04", "variants": [v_bad_arch]})
    assert any("reasoning vault" in e for e in errs_arch), errs_arch

    # 3. Choice variant with plainText (2026-11-19 rule)
    with open(ROOT / "drills" / "data" / "MTH-T01-C04" / "DRL-MTH-T01-C04-01.json", "r", encoding="utf-8") as fh:
        drill = json.load(fh)
    choice_prob = copy.deepcopy(next(p for p in drill["problems"] if p["answerSpec"]["type"] == "choice"))
    choice_prob["variantId"] = f"VAR-MTH-T01-C04-{choice_prob['archetypeKey']}-01"
    choice_prob["sourceArchetype"] = choice_prob["archetypeKey"]
    choice_prob["plainText"] = "Should be omitted on choice variants"
    errs_choice = variant_bank.check_variant_bank({"unitCode": "MTH-T01-C04", "variants": [choice_prob]})
    assert any("plainText" in e for e in errs_choice), errs_choice


def test_from_templates_deterministic_generation_and_add(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    variants_dir = tmp_path / "variants"
    monkeypatch.setenv("VARIANTS_DIR", str(variants_dir))

    doc1 = variant_bank.generate_variants_from_templates(
        "MTH-T01-C04",
        per_archetype=3,
        seed=20261119,
        variants_dir=str(variants_dir),
    )
    assert len(doc1["variants"]) == 15
    assert variant_bank.check_variant_bank(doc1) == []

    # Determinism check: regenerating with the same seed and overwrite produces identical variants.
    doc2 = variant_bank.generate_variants_from_templates(
        "MTH-T01-C04",
        per_archetype=3,
        seed=20261119,
        variants_dir=str(variants_dir),
        overwrite=True,
    )
    assert [v["prompt"] for v in doc1["variants"]] == [v["prompt"] for v in doc2["variants"]]

    # --add appends a new distinct variant and auto-assigns the next variantId.
    fresh = {
        "level": 1,
        "category": "Fraction Simplification",
        "archetype": "problem-solving",
        "archetypeKey": "c04-fraction-simplification-gcf",
        "form": "direct",
        "context": "",
        "verificationLevel": "partial",
        "prompt": "Reduce $\\frac{26}{39}$ to lowest terms.",
        "display": "\\frac{26}{39}",
        "plainText": "26/39",
        "givens": {"a": 26, "b": 39},
        "constants": {},
        "trapGivens": [26, 39],
        "answerSpec": {"type": "number", "value": "2/3", "tol": 0, "forms": ["reduced_fraction", "exact"]},
        "answerPlain": "2/3",
        "answerDisplay": "\\frac{2}{3}",
        "inputHint": "Enter a reduced fraction",
        "commonTrapTag": "c04-partial-common-factor-reduction",
        "trapDerivation": "(39 - 26) / 39",
        "trapValue": "1/3",
        "verify": {"source": "26 / 39", "trapValue": "1/3"},
        "checkpointHint": "Factor out the greatest common divisor shared by numerator and denominator.",
        "references": ["MTH-T01-C04"],
        "steps": [
            {
                "latex": "\\frac{26}{39} = \\frac{2 \\cdot 13}{3 \\cdot 13}",
                "explain": "Factor out the greatest common divisor.",
                "eq": ["26 / 39", "(2 * 13) / (3 * 13)"],
            },
            {
                "latex": "\\frac{2 \\cdot 13}{3 \\cdot 13} = \\frac{2}{3}",
                "explain": "Cancel the common factor.",
                "val": "2/3",
            },
        ],
    }
    updated = variant_bank.add_variants(
        {"unitCode": "MTH-T01-C04", "variants": [fresh]},
        variants_dir=str(variants_dir),
    )
    assert len(updated["variants"]) == 16
    assert updated["variants"][-1]["variantId"] == "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-04"

    # Re-adding the same draft is rejected and leaves the bank untouched.
    with pytest.raises(variant_bank.VariantBankError):
        variant_bank.add_variants(
            {"unitCode": "MTH-T01-C04", "variants": [fresh]},
            variants_dir=str(variants_dir),
        )
    assert len(variant_bank.load_bank("MTH-T01-C04", variants_dir=str(variants_dir))["variants"]) == 16


def test_answer_check_with_variant_id_python_and_cli() -> None:
    var = _sample_variant("c04-fraction-simplification-gcf")
    vid = var["variantId"]

    res_ok = answer_check.check_variant_answer(vid, var["answerPlain"])
    assert res_ok["verdict"] == "correct"

    res_trap = answer_check.check_variant_answer(vid, var["trapValue"])
    assert res_trap["verdict"] == "incorrect"
    assert res_trap.get("trapMatched") is True

    res_missing = answer_check.check_variant_answer("VAR-NO-SUCH-01", "1")
    assert res_missing["verdict"] == "invalid input"
    assert "not found" in res_missing["message"].lower()

    # CLI subprocess check (mirrors Studio /api/check-answer invocation)
    proc = subprocess.run(
        [sys.executable, "-m", "math_engine.answer_check"],
        input=json.dumps({"variantId": vid, "input": var["answerPlain"]}),
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        check=True,
    )
    cli_res = json.loads(proc.stdout)
    assert cli_res["verdict"] == "correct"
