# -*- coding: utf-8 -*-
"""
Tests for AI Drill Ingest and Reasoning Vault:
1. Verify reasoning archetypes load and register
2. Verify AI-generated problems pass Machine Quality Gates G1-G6 before saving
3. Verify context rotation and usedContext tracking
"""

import os
import tempfile
import unittest

from math_engine.ai_drill_ingest import (
    AiContractError,
    ingest_ai_drill,
    load_reasoning_vault,
    mark_context_used,
    register_archetype,
    validate_ai_problem_contract,
)
from math_engine.templates._prealg_helpers import S
from math_engine.verify import VerificationError
from quality_rules import QualityError


class TestAiDrillIngest(unittest.TestCase):
    def test_c06_vault_archetypes_exist(self):
        """MTH-T01-C06 Reasoning Vault must load all 7 core archetypes."""
        vault = load_reasoning_vault("MTH-T01-C06")
        archetypes = vault.get("archetypes", [])
        self.assertGreaterEqual(len(archetypes), 7)
        keys = [a["archetypeKey"] for a in archetypes]
        self.assertIn("c06-invariant-component-under-variable-total", keys)
        self.assertIn("c06-relative-change-base-shift", keys)
        self.assertIn("c06-parallel-vs-cascading-rates", keys)

    def test_ingest_valid_ai_problem(self):
        """A valid AI-generated problem (orange juice sweetness) is verified and saved."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample_drill = {
                "unitCode": "MTH-T01-C06",
                "drillId": "DRL-MTH-T01-C06-TEST-99",
                "sourceAttribution": {
                    "textbook": "Prealgebra 2e",
                    "publisher": "OpenStax",
                    "license": "CC BY 4.0",
                },
                "problems": [
                    {
                        "id": "Q01",
                        "verificationLevel": "partial",
                        "templateKey": "c06-invariant-component-under-variable-total",
                        "archetypeKey": "c06-invariant-component-under-variable-total",
                        "blindSolve": {
                            "answer": "60",
                            "ambiguous": False,
                            "setup": "model",
                            "strategy": "prescribed",
                            "check": "none",
                            "task": "compute",
                            "reverse": True,
                            "steps": 6,
                        },
                        "level": 4,
                        "levelLabel": "Level 4 - Applied Synthesis",
                        "category": "Interleaved Synthesis",
                        "references": ["MTH-T01-C06-U02", "MTH-T01-C06-U04"],
                        "givens": {"initial_mass": 300, "initial_conc": 10, "target_conc": 25},
                        "prompt": "Fresh orange juice of $300$ grams has a natural sugar concentration of $10\\%$. How many grams of pure sugar must be added so the sugar concentration becomes $25\\%$?",
                        "display": "\\frac{300 \\times 10\\% + x}{300 + x} = 25\\% \\implies x = ?",
                        "plainText": "(300*10 + 100*x)/(300 + x) = 25",
                        "answerSpec": {"type": "number", "value": "60"},
                        "answerDisplay": "60",
                        "answerPlain": "60",
                        "inputHint": "Enter the exact integer in grams",
                        "checkpointHint": "Identify the invariant water component whose absolute mass remains unchanged across dilution.",
                        "commonTrapTag": "c06-variable-base-neglect",
                        "trapDerivation": "300 * (25 / 100 - 10 / 100)",
                        "verify": {"source": "60", "trapValue": "45"},
                        "steps": [
                            S(
                                "\\text{Water} = 300 \\times (1 - 0.10)",
                                "Calculate the invariant mass of water which does not change.",
                            ),
                            S(
                                "\\text{Water} = 270\\text{ g}",
                                "Simplify the invariant water mass to 270 grams.",
                                eq=["300 * (1 - 0.10)", "270"],
                            ),
                            S(
                                "270 = 0.75 \\times T_{\\text{new}}",
                                "Equate the water mass to 75% of the expanded new total mixture.",
                            ),
                            S(
                                "T_{\\text{new}} = 360\\text{ g}",
                                "Solve for the new total mixture mass.",
                                eq=["270 / 0.75", "360"],
                            ),
                            S(
                                "x = T_{\\text{new}} - 300",
                                "Set up difference between new total mass and initial mass.",
                            ),
                            S(
                                "x = 60\\text{ g}",
                                "Subtract the initial mixture mass to find the pure sugar added.",
                                val="60",
                                eq=["360 - 300", "60"],
                            ),
                        ],
                    }
                ],
            }

            saved_doc = ingest_ai_drill(sample_drill, data_root=tmp_dir)
            self.assertEqual(saved_doc["drillId"], "DRL-MTH-T01-C06-TEST-99")
            self.assertEqual(saved_doc["sourceAttribution"]["publisher"], "OpenStax")
            saved_file = os.path.join(tmp_dir, "MTH-T01-C06", "DRL-MTH-T01-C06-TEST-99.json")
            self.assertTrue(os.path.exists(saved_file))

    def test_ingest_rejects_spoilers(self):
        """G4 Zero-Leak rejects problems where inputHint leaks the answer."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            leaking_drill = {
                "unitCode": "MTH-T01-C06",
                "problems": [
                    {
                        "id": "Q01",
                        "verificationLevel": "partial",
                        "templateKey": "c06-rate-base-part-triad",
                        "archetypeKey": "c06-rate-base-part-triad",
                        "level": 1,
                        "givens": {"rate": 20, "base": 50},
                        "prompt": "Find $20\\%$ of $50$.",
                        "display": "20\\% \\times 50 = ?",
                        "plainText": "0.20 * 50 = ?",
                        "answerSpec": {"type": "number", "value": "10"},
                        "answerDisplay": "10",
                        "answerPlain": "10",
                        "inputHint": "The answer is 10",  # SPOILER!
                        "checkpointHint": "Convert percentage to standard fractional representation.",
                        "commonTrapTag": "c06-percent-decimal-conversion",
                        "trapDerivation": "50 * 20",
                        "verify": {"source": "10", "trapValue": "1000"},
                        "steps": [
                            S("50 \\times 0.20 = 10", "Multiply base by rate.", val="10", eq=["50 * 0.20", "10"])
                        ],
                    }
                ],
            }
            with self.assertRaises((QualityError, VerificationError)):
                ingest_ai_drill(leaking_drill, data_root=tmp_dir)

    def test_register_and_mark_context_used(self):
        """Registering a new archetype and marking contexts used persists in the vault."""
        with tempfile.TemporaryDirectory() as tmp_vault_dir:
            unit = "MTH-T01-TEST"
            new_archetype = {
                "archetypeKey": "test-conservation-schema",
                "difficultyLevel": 3,
                "coreMentalModel": "Total quantity is conserved across transformations.",
                "versatileDomains": ["fruit punch", "battery charge", "investment pool"],
                "usedContexts": ["fruit punch"],
            }
            register_archetype(unit, new_archetype, vault_dir=tmp_vault_dir)

            loaded = load_reasoning_vault(unit, vault_dir=tmp_vault_dir)
            self.assertEqual(len(loaded["archetypes"]), 1)
            self.assertEqual(loaded["archetypes"][0]["usedContexts"], ["fruit punch"])

            mark_context_used(unit, "test-conservation-schema", "battery charge", vault_dir=tmp_vault_dir)
            updated = load_reasoning_vault(unit, vault_dir=tmp_vault_dir)
            self.assertEqual(updated["archetypes"][0]["usedContexts"], ["fruit punch", "battery charge"])

    def test_contract_guard_rejects_numeric_hint_and_unregistered_givens(self):
        """validate_ai_problem_contract and ingest_ai_drill reject hints with numbers or givens mismatch."""
        # 1. checkpointHint has number
        prob_with_num_hint = {
            "id": "Q01",
            "verificationLevel": "partial",
            "checkpointHint": "Divide by 100",  # violates 00_core §6
        }
        with self.assertRaises(AiContractError):
            validate_ai_problem_contract(prob_with_num_hint)

        # 2. Number in prompt not in givens
        prob_with_unregistered_given = {
            "id": "Q02",
            "verificationLevel": "partial",
            "checkpointHint": "Use fractional form.",
            "givens": {"base": 50},
            "prompt": "Find 20% of 50.",  # '20' is in prompt but missing from givens
        }
        with self.assertRaises(AiContractError):
            validate_ai_problem_contract(prob_with_unregistered_given)

        # 3. Given in givens not in prompt (ghost given)
        prob_with_ghost_given = {
            "id": "Q03",
            "verificationLevel": "partial",
            "checkpointHint": "Use fractional form.",
            "givens": {"rate": 20, "base": 50, "ghost": 99},
            "prompt": "Find 20% of 50.",  # '99' never appears in prompt
        }
        with self.assertRaises(AiContractError):
            validate_ai_problem_contract(prob_with_ghost_given)

        # 4. trapDerivation with < 2 distinct givens
        prob_with_single_given_trap = {
            "id": "Q04",
            "verificationLevel": "partial",
            "checkpointHint": "Use fractional form.",
            "givens": {"rate": 20, "base": 50},
            "prompt": "Find 20% of 50.",
            "trapDerivation": "50 * 2",  # '2' is not in givens
            "verify": {"source": "10", "trapValue": "100"},
            "answerSpec": {"type": "number", "value": "10"},
        }
        with self.assertRaises(AiContractError):
            validate_ai_problem_contract(prob_with_single_given_trap)

        # 5. trapDerivation mismatch with trapValue
        prob_with_trap_mismatch = {
            "id": "Q05",
            "verificationLevel": "partial",
            "checkpointHint": "Use fractional form.",
            "givens": {"rate": 20, "base": 50},
            "prompt": "Find 20% of 50.",
            "trapDerivation": "50 * 20",
            "verify": {"source": "10", "trapValue": "9999"},  # 50*20 = 1000 != 9999
            "answerSpec": {"type": "number", "value": "10"},
        }
        with self.assertRaises(AiContractError):
            validate_ai_problem_contract(prob_with_trap_mismatch)

        # 6. Verify ingest_ai_drill also raises AiContractError
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_drill = {
                "unitCode": "MTH-T01-C06",
                "problems": [prob_with_num_hint],
            }
            with self.assertRaises(AiContractError):
                ingest_ai_drill(bad_drill, data_root=tmp_dir)

    def test_contract_guard_rejects_missing_display_or_plaintext_or_latex(self):
        """validate_ai_problem_contract enforces display, plainText, and $ in prompt."""
        base_prob = {
            "id": "Q01",
            "verificationLevel": "partial",
            "checkpointHint": "Use fractional form.",
            "givens": {"rate": 20, "base": 50},
            "prompt": "Find $20\\%$ of $50$.",
            "display": "20\\% \\times 50 = ?",
            "plainText": "0.20 * 50 = ?",
            "trapDerivation": "50 * 20",
            "verify": {"source": "10", "trapValue": "1000"},
            "answerSpec": {"type": "number", "value": "10"},
            "steps": [{"latex": "0.20 \\times 50 = 10", "explain": "Multiply decimal rate by base", "val": "10"}],
        }
        self.assertTrue(validate_ai_problem_contract(dict(base_prob)))

        # Missing display
        no_display = dict(base_prob)
        no_display.pop("display")
        with self.assertRaises(AiContractError):
            validate_ai_problem_contract(no_display)

        # Missing plainText
        no_plain = dict(base_prob)
        no_plain.pop("plainText")
        with self.assertRaises(AiContractError):
            validate_ai_problem_contract(no_plain)

        # Missing LaTeX delimiter $ in prompt
        no_latex = dict(base_prob)
        no_latex["prompt"] = "Find 20% of 50."
        with self.assertRaises(AiContractError):
            validate_ai_problem_contract(no_latex)

    def test_ingest_auto_resolves_unit_title(self):
        """ingest_ai_drill automatically populates unitTitle from id_map.json."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            drill = {
                "unitCode": "MTH-T01-C01",
                "problems": [
                    {
                        "id": "Q01",
                        "level": 1,
                        "verificationLevel": "partial",
                        "checkpointHint": "Use expanded notation.",
                        "archetypeKey": "c01-place-value-partition",
                        "commonTrapTag": "c01-place-value-misalignment",
                        "givens": {"a": 10, "b": 5},
                        "prompt": "Calculate $10 + 5$.",
                        "display": "10 + 5 = ?",
                        "plainText": "10 + 5",
                        "trapDerivation": "10 * 5",
                        "verify": {"source": "15", "trapValue": "50"},
                        "answerSpec": {"type": "number", "value": "15"},
                        "answerPlain": "15",
                        "answerDisplay": "15",
                        "steps": [{"latex": "10 + 5 = 15", "explain": "Direct sum", "val": "15"}],
                    }
                ],
            }
            saved = ingest_ai_drill(drill, data_root=tmp_dir)
            self.assertEqual(saved.get("unitTitle"), "Whole Numbers")
            self.assertIn("Whole Numbers", saved.get("title", ""))

    def test_ingest_heals_and_protects_against_corrupted_latex(self):
        """Rule 8: Ingest heals Python escape artifact collisions (\f -> rac, \r -> ight) and rejects unrecoverable corruption."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corrupted_drill = {
                "unitCode": "MTH-T01-C01",
                "problems": [
                    {
                        "id": "Q01",
                        "level": 1,
                        "verificationLevel": "partial",
                        "checkpointHint": "Use expanded notation.",
                        "archetypeKey": "c01-place-value-partition",
                        "commonTrapTag": "c01-place-value-misalignment",
                        "givens": {"a": 10, "b": 5},
                        "prompt": "Calculate $10 + 5$.",
                        "display": "\x0crac{10}{5} = ?",  # Corrupted form-feed from unescaped \frac
                        "plainText": "10 / 5",
                        "trapDerivation": "10 * 5",
                        "verify": {"source": "2", "trapValue": "50"},
                        "answerSpec": {"type": "number", "value": "2"},
                        "answerPlain": "2",
                        "answerDisplay": "2",
                        "steps": [
                            {
                                "latex": "\\left(\x0crac{10}{5}\right) = 2",  # Corrupted form-feed & carriage-return
                                "explain": "Healed step",
                                "val": "2",
                            }
                        ],
                    }
                ],
            }
            saved = ingest_ai_drill(corrupted_drill, data_root=tmp_dir)
            p = saved["problems"][0]
            # Should be healed into proper \frac and \right
            self.assertIn(r"\frac{10}{5}", p["display"])
            self.assertNotIn("\x0c", p["display"])
            self.assertIn(r"\frac{10}{5}", p["steps"][0]["latex"])
            self.assertIn(r"\right", p["steps"][0]["latex"])
            self.assertNotIn("\x0c", p["steps"][0]["latex"])
            self.assertNotIn("\r", p["steps"][0]["latex"])

    def test_all_active_drills_have_zero_corrupted_latex(self):
        """Audit all active drill JSON files to certify zero LaTeX escape corruption (00_core §6)."""
        import glob
        import json
        import re

        control_pattern = re.compile(r"[\x0c\r\x08\x0b]")
        broken_pattern = re.compile(r"(?<!\\)\brac\{|(?<!\\)\bright[)\]}]")

        for filepath in glob.glob("drills/data/**/*.json", recursive=True):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            for prob in data.get("problems", []):
                pid = prob.get("id", "?")
                for field in ("display", "answerDisplay", "prompt"):
                    val = prob.get(field)
                    if isinstance(val, str):
                        self.assertFalse(
                            bool(control_pattern.search(val)),
                            f"{filepath} [{pid}] field '{field}' contains control characters: {repr(val)}",
                        )
                        self.assertFalse(
                            bool(broken_pattern.search(val)),
                            f"{filepath} [{pid}] field '{field}' contains broken LaTeX macro: {repr(val)}",
                        )
                for s_idx, st in enumerate(prob.get("steps", [])):
                    latex_val = st.get("latex")
                    if isinstance(latex_val, str):
                        self.assertFalse(
                            bool(control_pattern.search(latex_val)),
                            f"{filepath} [{pid}] step {s_idx + 1} contains control characters: {repr(latex_val)}",
                        )
                        self.assertFalse(
                            bool(broken_pattern.search(latex_val)),
                            f"{filepath} [{pid}] step {s_idx + 1} contains broken LaTeX macro: {repr(latex_val)}",
                        )


if __name__ == "__main__":
    unittest.main()
