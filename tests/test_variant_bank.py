"""Tests for math_engine.variant_bank gates, adding variants, coverage, and variantId answer checking."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from math_engine import ai_drill_ingest, answer_check, variant_bank

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


def test_add_variants_appends_next_id_and_rejects_duplicate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    variants_dir = tmp_path / "variants"
    monkeypatch.setenv("VARIANTS_DIR", str(variants_dir))

    seed_bank = _load_seed_bank()
    initial_count = len(seed_bank["variants"])
    variant_bank.save_bank("MTH-T01-C04", seed_bank, variants_dir=str(variants_dir))
    assert variant_bank.check_variant_bank(seed_bank) == []

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
        "review": {"verdict": "pass", "note": "Verified test variant."},
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
    assert len(updated["variants"]) == initial_count + 1
    assert updated["variants"][-1]["variantId"].startswith("VAR-MTH-T01-C04-c04-fraction-simplification-gcf-")

    # Re-adding the same draft is rejected and leaves the bank untouched.
    with pytest.raises(variant_bank.VariantBankError):
        variant_bank.add_variants(
            {"unitCode": "MTH-T01-C04", "variants": [fresh]},
            variants_dir=str(variants_dir),
        )
    assert len(variant_bank.load_bank("MTH-T01-C04", variants_dir=str(variants_dir))["variants"]) == initial_count + 1


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


def test_coverage_report_and_ingest_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    unit = "MTH-T01-C04"
    data_root = tmp_path / "drills_data"
    variants_dir = tmp_path / "variants"
    unit_dir = data_root / unit
    unit_dir.mkdir(parents=True)
    variants_dir.mkdir(parents=True)

    # Fixture bank: 3 variants for c04-fraction-simplification-gcf@L1 (covered),
    # 1 variant for c04-fraction-multiplication-product@L1 (uncovered: 1/3),
    # 0 variants for c04-fraction-division-reciprocal@L2 (uncovered: 0/3).
    seed_bank = _load_seed_bank()
    simp_l1 = [
        copy.deepcopy(v) for v in seed_bank["variants"] if v["archetypeKey"] == "c04-fraction-simplification-gcf"
    ][:3]
    for v in simp_l1:
        v["level"] = 1
    mult_l1 = [
        copy.deepcopy(v) for v in seed_bank["variants"] if v["archetypeKey"] == "c04-fraction-multiplication-product"
    ][:1]
    for v in mult_l1:
        v["level"] = 1
    (variants_dir / f"{unit}.json").write_text(
        json.dumps({"unitCode": unit, "variants": simp_l1 + mult_l1}),
        encoding="utf-8",
    )

    drill_path = unit_dir / "DRL-MTH-T01-C04-99.json"
    drill_doc = {
        "drillId": "DRL-MTH-T01-C04-99",
        "unitCode": unit,
        "problems": [
            {"id": "Q01", "archetypeKey": "c04-fraction-simplification-gcf", "level": 1},
            {"id": "Q02", "archetypeKey": "c04-fraction-multiplication-product", "level": 1},
            {"id": "Q03", "archetypeKey": "c04-fraction-division-reciprocal", "level": 2},
        ],
    }
    drill_path.write_text(json.dumps(drill_doc), encoding="utf-8")

    # 1. Coverage by unit code and by drill JSON path
    cov_unit = variant_bank.compute_coverage(unit, variants_dir=str(variants_dir), data_root=str(data_root))
    assert cov_unit["totalPairs"] == 3
    assert cov_unit["coveredPairs"] == 1
    uncovered_keys = {(e["archetypeKey"], e["level"]): e["variantCount"] for e in cov_unit["uncoveredPairs"]}
    assert uncovered_keys == {
        ("c04-fraction-multiplication-product", 1): 1,
        ("c04-fraction-division-reciprocal", 2): 0,
    }

    monkeypatch.setenv("VARIANTS_DIR", str(variants_dir))
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_root))

    rc_unit = variant_bank.main(["--coverage", unit])
    assert rc_unit == 0
    out_unit = capsys.readouterr().out
    assert "OK   c04-fraction-simplification-gcf @ L1: 3 variant(s)" in out_unit
    assert "LOW  c04-fraction-multiplication-product @ L1: 1 variant(s) (need 2 more" in out_unit
    assert "LOW  c04-fraction-division-reciprocal @ L2: 0 variant(s) (need 3 more" in out_unit
    assert "1/3 pair(s) covered (>= 3 variants), 2 uncovered (< 3)." in out_unit

    rc_file = variant_bank.main(["--coverage", str(drill_path), "--json"])
    assert rc_file == 0
    cov_json = json.loads(capsys.readouterr().out)
    assert cov_json["drillCount"] == 1
    assert len(cov_json["uncoveredPairs"]) == 2

    # 2. Non-blocking ingest warning on ai_drill_ingest when drill has uncovered pairs (and silent when covered)
    tpl_path = ROOT / ".claude" / "skills" / "new-math-drill" / "template" / "draft.json"
    tpl_draft = json.loads(tpl_path.read_text(encoding="utf-8"))
    # Keep just the L1 problem (ensure review verdict present) so ingest succeeds cleanly.
    p1 = copy.deepcopy(tpl_draft["problems"][0])
    p1.setdefault("review", {"verdict": "pass", "note": "Verified fixture problem."})
    single_draft = {**tpl_draft, "problems": [p1]}
    draft_file = tmp_path / "ingest_draft.json"
    draft_file.write_text(json.dumps(single_draft), encoding="utf-8")

    empty_variants = tmp_path / "empty_variants"
    empty_variants.mkdir()
    ingest_data_root = tmp_path / "ingest_data"
    monkeypatch.setenv("REASONING_VAULT_DIR", str(tpl_path.parent))
    monkeypatch.setenv("VARIANTS_DIR", str(empty_variants))
    monkeypatch.setenv("DRILLS_DATA_DIR", str(ingest_data_root))

    rc_ingest = ai_drill_ingest.main(["--unit", single_draft["unitCode"], "--ingest-file", str(draft_file)])
    assert rc_ingest == 0
    ingest_out = capsys.readouterr().out.strip().splitlines()
    assert ingest_out[-1].startswith("WARNING: Similar variant bank has 1 uncovered pair(s)"), ingest_out
    assert f"{p1['archetypeKey']}@L{p1['level']} (0/3)" in ingest_out[-1]
    assert "python -m math_engine.variant_bank --coverage-gate" in ingest_out[-1]

    # Now populate 3 variants for that exact (archetypeKey, level) -> ingest prints NO warning.
    covered_variants = tmp_path / "covered_variants"
    covered_variants.mkdir()
    (covered_variants / f"{single_draft['unitCode']}.json").write_text(
        json.dumps(
            {
                "unitCode": single_draft["unitCode"],
                "variants": [
                    {
                        "variantId": f"VAR-{single_draft['unitCode']}-{p1['archetypeKey']}-{i:02d}",
                        "archetypeKey": p1["archetypeKey"],
                        "sourceArchetype": p1["archetypeKey"],
                        "level": p1["level"],
                    }
                    for i in range(1, 4)
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("VARIANTS_DIR", str(covered_variants))
    rc_ingest_ok = ai_drill_ingest.main(["--unit", single_draft["unitCode"], "--ingest-file", str(draft_file)])
    assert rc_ingest_ok == 0
    ok_out = capsys.readouterr().out
    assert "WARNING:" not in ok_out


def test_add_variants_enforces_validate_review(tmp_path: Path) -> None:
    """variant_bank.add_variants must require review: {verdict: 'pass', note} on newly added variants."""
    variants_dir = tmp_path / "variants"
    variants_dir.mkdir()

    # Existing template-seeded bank (without 'review') still passes check_variant_bank.
    seed = _load_seed_bank()
    assert variant_bank.check_variant_bank(seed) == []

    # Prepare a valid fresh variant (adapted from _sample_variant with distinct numbers and answer).
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

    # 1. Missing review -> rejected
    with pytest.raises(variant_bank.VariantBankError, match="review"):
        variant_bank.add_variants({"unitCode": "MTH-T01-C04", "variants": [fresh]}, variants_dir=str(variants_dir))
    assert not (variants_dir / "MTH-T01-C04.json").exists()

    # 2. verdict='fix' -> rejected
    needs_fix = copy.deepcopy(fresh)
    needs_fix["review"] = {"verdict": "fix", "note": "Check prompt wording."}
    with pytest.raises(variant_bank.VariantBankError, match="Reviewer asked for a fix"):
        variant_bank.add_variants({"unitCode": "MTH-T01-C04", "variants": [needs_fix]}, variants_dir=str(variants_dir))
    assert not (variants_dir / "MTH-T01-C04.json").exists()

    # 3. verdict='pass' -> accepted
    passing = copy.deepcopy(fresh)
    passing["review"] = {"verdict": "pass", "note": "Verified distinct variant."}
    saved = variant_bank.add_variants(
        {"unitCode": "MTH-T01-C04", "variants": [passing]}, variants_dir=str(variants_dir)
    )
    assert len(saved["variants"]) == 1
