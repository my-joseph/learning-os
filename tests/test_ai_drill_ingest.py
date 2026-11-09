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
                                "\\text{Water} = 300 \\times (1 - 0.10) = 270\\text{ g}",
                                "Calculate the invariant mass of water which does not change.",
                                eq=["300 * (1 - 0.10)", "270"],
                            ),
                            S(
                                "270 = (1 - 0.25) \\times T_{\\text{new}} = 0.75 T_{\\text{new}} \\implies T_{\\text{new}} = 360\\text{ g}",
                                "Equate the water mass to 75% of the expanded new total mixture.",
                                eq=["270 / 0.75", "360"],
                            ),
                            S(
                                "x = T_{\\text{new}} - 300 = 360 - 300 = 60\\text{ g}",
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
                        "level": 1,
                        "givens": {"rate": 20, "base": 50},
                        "prompt": "Find 20% of 50.",
                        "display": "20% * 50 = ?",
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
            self.assertEqual(
                updated["archetypes"][0]["usedContexts"], ["fruit punch", "battery charge"]
            )

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


if __name__ == "__main__":
    unittest.main()
