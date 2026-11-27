"""Regression tests for deterministic distractor & trap provenance gate (06 §3, §4 G4, 07 §4)."""

from __future__ import annotations

import copy
import glob
import json
from pathlib import Path

import pytest

from math_engine.ai_drill_ingest import (
    AiContractError,
    check_ai_drill,
    check_ai_drill_warnings,
    check_distractor_provenance,
    load_scope_archetypes,
    register_archetype,
    validate_against_vault,
    validate_ai_problem_contract,
    validate_distractor_provenance,
)

ROOT = Path(__file__).resolve().parents[1]


def _seed_vault(vault_dir: Path) -> list[dict]:
    arch = register_archetype(
        "MTH-T02-C01-U01",
        {
            "archetypeKey": "t02-c01-u01-power-periodicity",
            "unitCode": "MTH-T02-C01-U01",
            "name": "Periodic Powers of a Simple Complex Number",
            "level": 2,
            "governingRelation": "(1 + i)^2 = 2i",
            "cognitiveTraps": [
                {
                    "trapTag": "t02-c01-u01-report-reduced-exponent-trap",
                    "description": "Finds the exponent of the squared base 2^m = t but forgets to double it.",
                    "trapFormula": "log(t)/log(two)",
                },
                {
                    "trapTag": "t02-c01-u01-assume-period-four-trap",
                    "description": "Reports the period-4 cycle length instead of matching the magnitude.",
                    "trapFormula": "two * two",
                },
                {
                    "trapTag": "t02-c01-u01-double-exponent-twice-trap",
                    "description": "Doubles the reduced exponent twice.",
                    "trapFormula": "two * two * (log(t)/log(two))",
                },
                {
                    "trapTag": "t02-c01-u01-halve-target-instead-of-log-trap",
                    "description": "Halves the target instead of taking the base-2 logarithm.",
                    "trapFormula": "t / two",
                },
            ],
            "figureNone": "Algebraic reduction and periodicity; no figure needed.",
        },
        vault_dir=str(vault_dir),
    )
    return [arch]


def _valid_choice_problem(**overrides) -> dict:
    """Clean choice problem where every distractor has a vault trapTag and SymPy-evaluable provenance."""
    prob = {
        "id": "Q01",
        "level": 2,
        "category": "Core Skill",
        "form": "choose",
        "archetype": "problem-solving",
        "archetypeKey": "t02-c01-u01-power-periodicity",
        "context": "",
        "prompt": "Find the positive integer $n$ for which $(1 + i)^n = 256$.",
        "display": "(1 + i)^{2} = 2i",
        "givens": {"one": 1, "t": 256},
        "constants": {"two": 2},
        "trapGivens": [256, 2],
        "answerSpec": {
            "type": "choice",
            "options": [
                {
                    "id": "A",
                    "label": "$4$",
                    "trapTag": "t02-c01-u01-assume-period-four-trap",
                    "provenance": "2 * 2",
                },
                {
                    "id": "B",
                    "label": "$8$",
                    "trapTag": "t02-c01-u01-report-reduced-exponent-trap",
                    "provenance": "log(256)/log(2)",
                },
                {
                    "id": "C",
                    "label": "$16$",
                },
                {
                    "id": "D",
                    "label": "$32$",
                    "trapTag": "t02-c01-u01-double-exponent-twice-trap",
                    "provenance": "2 * 2 * (log(256)/log(2))",
                },
                {
                    "id": "E",
                    "label": "$128$",
                    "trapTag": "t02-c01-u01-halve-target-instead-of-log-trap",
                    "provenance": "t / two",
                },
            ],
            "correct": "C",
        },
        "answerPlain": "C",
        "answerDisplay": "C",
        "inputHint": "Choose one option.",
        "commonTrapTag": "t02-c01-u01-report-reduced-exponent-trap",
        "trapDerivation": "log(256)/log(2)",
        "trapValue": "8",
        "verify": {"source": "16", "trapValue": "8"},
        "checkpointHint": "Square the base once to get something simpler, and keep every factor that appears.",
        "references": ["MTH-T02-C01-U01"],
        "verificationLevel": "partial",
        "steps": [
            {"latex": "(1 + i)^2 = 2i", "explain": "Square the base first.", "eq": ["(1 + I)**2", "2*I"]},
            {"latex": "(1 + i)^n = (2i)^m", "explain": "Rewrite the power with $n = 2m$."},
            {"latex": "2^{m} = 256", "explain": "Match the magnitude so $m = 8$.", "eq": ["2**8", "256"]},
            {"latex": "n = 16", "explain": "Double the exponent of the squared base.", "eq": ["(1 + I)**16", "256"]},
        ],
        "review": {"verdict": "pass", "note": "All distractor provenances and trapTags verified."},
    }
    prob.update(overrides)
    return prob


def test_clean_choice_problem_with_sympy_provenances_passes_with_zero_warnings(tmp_path: Path) -> None:
    vault_dir = tmp_path / "vault"
    archs = _seed_vault(vault_dir)
    prob = _valid_choice_problem()

    assert validate_distractor_provenance(copy.deepcopy(prob), archs) == []
    validate_against_vault(copy.deepcopy(prob), archs, "MTH-T02-C01-U01")
    assert validate_ai_problem_contract(copy.deepcopy(prob)) is True

    doc = {"unitCode": "MTH-T02-C01-U01", "problems": [prob]}
    assert check_ai_drill(copy.deepcopy(doc), vault_dir=str(vault_dir)) == []
    assert check_ai_drill_warnings(copy.deepcopy(doc), vault_dir=str(vault_dir)) == []


def test_option_provenance_that_does_not_produce_option_value_fails_naming_option(tmp_path: Path) -> None:
    """Reproduces 982cd2 / 444619: option provenance formula evaluates to a different value than the option."""
    vault_dir = tmp_path / "vault"
    archs = _seed_vault(vault_dir)
    prob = _valid_choice_problem()
    # Option D has label "$32$", but its provenance evaluates to 256 / 2 = 128 != 32.
    prob["answerSpec"]["options"][3]["provenance"] = "256 / 2"

    with pytest.raises(AiContractError, match=r"Option 'D'.*provenance/derivation '256 / 2' evaluates to '128'"):
        validate_distractor_provenance(prob, archs)

    doc = {"unitCode": "MTH-T02-C01-U01", "problems": [prob]}
    errs = check_ai_drill(doc, vault_dir=str(vault_dir))
    assert any("Option 'D'" in e and "does not equal option value '$32$'" in e for e in errs)


def test_option_provenance_evaluating_to_correct_answer_fails_naming_option(tmp_path: Path) -> None:
    """Distractor derivation that produces the correct answer must fail naming the option."""
    vault_dir = tmp_path / "vault"
    archs = _seed_vault(vault_dir)
    prob = _valid_choice_problem()
    # Option D has label "$16$" and provenance evaluating to 16 (the correct Option C value).
    prob["answerSpec"]["options"][3]["label"] = "$16$"
    prob["answerSpec"]["options"][3]["provenance"] = "2 * (log(256)/log(2))"

    with pytest.raises(AiContractError, match=r"Option 'D'.*equals.*correct"):
        validate_distractor_provenance(prob, archs)


def test_option_provenance_bare_number_or_unrelated_numbers_fails_naming_option(tmp_path: Path) -> None:
    """Option provenance cannot be a bare literal or use numbers absent from givens/constants."""
    vault_dir = tmp_path / "vault"
    archs = _seed_vault(vault_dir)

    bare = _valid_choice_problem()
    bare["answerSpec"]["options"][3]["provenance"] = "32"
    with pytest.raises(AiContractError, match=r"Option 'D'.*cannot be a bare number"):
        validate_distractor_provenance(bare, archs)

    unrelated = _valid_choice_problem()
    unrelated["answerSpec"]["options"][3]["provenance"] = "10 + 22"
    with pytest.raises(AiContractError, match=r"Option 'D'.*does not reference any problem givens"):
        validate_distractor_provenance(unrelated, archs)


def test_common_trap_option_mismatch_with_trap_value_fails_naming_option(tmp_path: Path) -> None:
    """Reproduces 982cd2 (DRL-MTH-T02-C01-U01-05 Q05): commonTrapTag option value != trapValue."""
    vault_dir = tmp_path / "vault"
    archs = _seed_vault(vault_dir)
    prob = _valid_choice_problem()
    # Option B carries commonTrapTag, with label "$k = -3$ or $k = 2$", while trapValue is "8".
    prob["answerSpec"]["options"][1]["label"] = "$k = -3$ or $k = 2$"
    prob["answerSpec"]["options"][1]["provenance"] = (
        "Solves the real-part equation but never checks that the imaginary part stays nonzero."
    )

    with pytest.raises(
        AiContractError,
        match=r"Option 'B' carries commonTrapTag 't02-c01-u01-report-reduced-exponent-trap'.*does not equal trapValue '8'",
    ):
        validate_distractor_provenance(prob, archs)


def test_trap_derivation_unrelated_to_trap_fails(tmp_path: Path) -> None:
    """Reproduces abf513, 6a3905, 0e774f: trapDerivation uses unrelated givens or disagrees with vault trapFormula."""
    vault_dir = tmp_path / "vault"
    arch_rem = register_archetype(
        "MTH-T02-C01-U01",
        {
            "archetypeKey": "t02-c01-u01-mixed-fraction-slip",
            "unitCode": "MTH-T02-C01-U01",
            "name": "Mixed Number Fraction Subtraction",
            "level": 2,
            "governingRelation": "(w1 + a/d) - (w2 + b/d)",
            "cognitiveTraps": [
                {
                    "trapTag": "c01-subtract-fractions-ignore-denom-trap",
                    "description": "Subtracts the fraction numerators a and b and ignores the denominator d.",
                    "trapFormula": "a - b",
                }
            ],
            "figureNone": "Symbolic fraction arithmetic.",
        },
        vault_dir=str(vault_dir),
    )

    # Case 1: Vault trapFormula operates on givens ['a', 'b'], but trapDerivation subtracts whole parts w1 - w2 (2 - 1).
    prob_unrelated_givens = {
        "id": "Q02",
        "level": 2,
        "verificationLevel": "partial",
        "archetypeKey": "t02-c01-u01-mixed-fraction-slip",
        "prompt": "Evaluate $2\\frac{7}{5} - 1\\frac{3}{5}$.",
        "display": "\\left(w_1 + \\frac{a}{d}\\right) - \\left(w_2 + \\frac{b}{d}\\right)",
        "plainText": "(2 + 7/5) - (1 + 3/5)",
        "givens": {"w1": 2, "a": 7, "d": 5, "w2": 1, "b": 3},
        "constants": {},
        "trapGivens": [7, 3],
        "answerSpec": {"type": "number", "value": "9/5"},
        "answerPlain": "9/5",
        "commonTrapTag": "c01-subtract-fractions-ignore-denom-trap",
        "trapDerivation": "2 - 1",
        "trapValue": "1",
        "verify": {"source": "(2 + 7/5) - (1 + 3/5)", "trapValue": "1"},
        "checkpointHint": "Convert both mixed numbers before subtracting the numerators over the common denominator.",
        "steps": [{"latex": "\\frac{17}{5} - \\frac{8}{5} = \\frac{9}{5}", "explain": "Subtract.", "val": "9/5"}],
    }
    with pytest.raises(AiContractError, match=r"unrelated to trap 'c01-subtract-fractions-ignore-denom-trap'"):
        validate_distractor_provenance(prob_unrelated_givens, [arch_rem])

    # Case 2: Vault trapFormula covers all givens ('(a + c) / (b + d)'), but trapDerivation computes a different operation ('a - c').
    arch_sum = register_archetype(
        "MTH-T02-C01-U01",
        {
            "archetypeKey": "t02-c01-u01-naive-fraction-add",
            "unitCode": "MTH-T02-C01-U01",
            "name": "Adding Fractions with Unlike Denominators",
            "level": 1,
            "governingRelation": "a/b + c/d = (ad + bc)/(bd)",
            "cognitiveTraps": [
                {
                    "trapTag": "naive-numerator-denominator-sum",
                    "description": "Adds numerators and adds denominators directly.",
                    "trapFormula": "(a + c) / (b + d)",
                }
            ],
            "figureNone": "Symbolic fraction arithmetic.",
        },
        vault_dir=str(vault_dir),
    )
    prob_wrong_formula = {
        "id": "Q03",
        "level": 1,
        "verificationLevel": "partial",
        "archetypeKey": "t02-c01-u01-naive-fraction-add",
        "prompt": "Evaluate $\\frac{7}{18} + \\frac{5}{12}$.",
        "display": "\\frac{a}{b} + \\frac{c}{d}",
        "plainText": "7/18 + 5/12",
        "givens": {"a": 7, "b": 18, "c": 5, "d": 12},
        "constants": {},
        "answerSpec": {"type": "number", "value": "29/36"},
        "answerPlain": "29/36",
        "commonTrapTag": "naive-numerator-denominator-sum",
        "trapDerivation": "(7 - 5) / (18 - 12)",
        "trapValue": "1/3",
        "verify": {"source": "7/18 + 5/12", "trapValue": "1/3"},
        "checkpointHint": "Find a common denominator before combining the numerators.",
        "steps": [{"latex": "\\frac{14 + 15}{36} = \\frac{29}{36}", "explain": "Add over LCD.", "val": "29/36"}],
    }
    with pytest.raises(
        AiContractError,
        match=r"unrelated to trap 'naive-numerator-denominator-sum': vault trapFormula '\(a \+ c\) / \(b \+ d\)' evaluates to '2/5'",
    ):
        validate_distractor_provenance(prob_wrong_formula, [arch_sum])


def test_distractor_without_single_misconception_origin_fails_naming_option(tmp_path: Path) -> None:
    """Every distractor must name a vault trapTag of the problem's archetype and declare provenance."""
    vault_dir = tmp_path / "vault"
    archs = _seed_vault(vault_dir)

    # 1. Missing trapTag on distractor Option A
    no_tag = _valid_choice_problem()
    no_tag["answerSpec"]["options"][0].pop("trapTag")
    with pytest.raises(AiContractError, match=r"Option 'A' is a distractor without a trapTag"):
        validate_distractor_provenance(no_tag, archs)

    # 2. Bogus trapTag not in the archetype's vault cognitiveTraps on Option D
    foreign_tag = _valid_choice_problem()
    foreign_tag["answerSpec"]["options"][3]["trapTag"] = "invented-non-vault-trap"
    with pytest.raises(
        AiContractError,
        match=r"Option 'D' trapTag 'invented-non-vault-trap' is not one of archetype 't02-c01-u01-power-periodicity' cognitiveTraps",
    ):
        validate_distractor_provenance(foreign_tag, archs)

    # 3. Missing provenance on distractor Option E
    no_prov = _valid_choice_problem()
    no_prov["answerSpec"]["options"][4].pop("provenance")
    with pytest.raises(AiContractError, match=r"Option 'E' is a distractor with no provenance"):
        validate_distractor_provenance(no_prov, archs)

    # 4. Correct option C accidentally carries a distractor trapTag
    tagged_correct = _valid_choice_problem()
    tagged_correct["answerSpec"]["options"][2]["trapTag"] = "t02-c01-u01-assume-period-four-trap"
    with pytest.raises(AiContractError, match=r"Option 'C' is the correct answer .* carries distractor trapTag"):
        validate_distractor_provenance(tagged_correct, archs)


def test_missing_schema_evaluation_fields_report_unverifiable_warning(tmp_path: Path) -> None:
    """When RawChoiceOption only carries prose provenance (and vault lacks a matching trapFormula), report 'unverifiable' warning."""
    vault_dir = tmp_path / "vault"
    register_archetype(
        "MTH-T02-C01-U01",
        {
            "archetypeKey": "t02-c01-u01-string-only-traps",
            "unitCode": "MTH-T02-C01-U01",
            "name": "Archetype with Legacy String Trap Tags",
            "level": 2,
            "governingRelation": "(1 + i)^2 = 2i",
            "cognitiveTraps": [
                "t02-c01-u01-report-reduced-exponent-trap",
                "t02-c01-u01-assume-period-four-trap",
                "t02-c01-u01-double-exponent-twice-trap",
                "t02-c01-u01-halve-target-instead-of-log-trap",
            ],
            "figureNone": "Symbolic.",
        },
        vault_dir=str(vault_dir),
    )
    prob = _valid_choice_problem(archetypeKey="t02-c01-u01-string-only-traps")
    prob["answerSpec"]["options"][0]["provenance"] = (
        "Uses only the sign condition and reports the smallest power of i equal to one."
    )
    prob["answerSpec"]["options"][3]["provenance"] = "Doubles the exponent twice."
    prob["answerSpec"]["options"][4]["provenance"] = "Halves the target instead of working with powers."

    doc = {"unitCode": "MTH-T02-C01-U01", "problems": [prob]}
    assert check_ai_drill(copy.deepcopy(doc), vault_dir=str(vault_dir)) == []
    warns = check_ai_drill_warnings(copy.deepcopy(doc), vault_dir=str(vault_dir))
    assert any("Option 'A'" in w and "unverifiable" in w for w in warns)
    assert any("Option 'D'" in w and "unverifiable" in w for w in warns)
    assert any("Option 'E'" in w and "unverifiable" in w for w in warns)


def test_audit_existing_mth_drills_reports_exact_failing_problems() -> None:
    """Run the distractor/trap provenance gate over committed MTH drills without editing them."""
    failing_problems: dict[str, list[str]] = {}
    drill_paths = sorted(glob.glob(str(ROOT / "drills" / "data" / "MTH-*" / "*.json")))
    assert len(drill_paths) >= 26

    for path in drill_paths:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        drill_id = doc.get("drillId") or Path(path).stem
        unit_code = doc["unitCode"]
        archs = load_scope_archetypes(unit_code)
        for prob in doc.get("problems", []):
            errs, _ = check_distractor_provenance(prob, archs)
            if errs:
                failing_problems[f"{drill_id}/{prob['id']}"] = errs

    assert failing_problems == {}
