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
    ingest_ai_drill,
    load_reasoning_vault,
    mark_context_used,
    register_archetype,
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
                "problems": [
                    {
                        "id": "Q01",
                        "templateKey": "c06-invariant-component-under-variable-total",
                        "level": 4,
                        "levelLabel": "Level 4 - Applied Synthesis",
                        "category": "Interleaved Synthesis",
                        "references": ["MTH-T01-C06-U02", "MTH-T01-C06-U04"],
                        "prompt": "Fresh orange juice of $300$ grams has a natural sugar concentration of $10\\%$. How many grams of pure sugar must be added so the sugar concentration becomes $25\\%$?",
                        "display": "\\frac{300 \\times 10\\% + x}{300 + x} = 25\\% \\implies x = ?",
                        "plainText": "(300*10 + 100*x)/(300 + x) = 25",
                        "answerSpec": {"type": "number", "value": "60"},
                        "answerDisplay": "60",
                        "answerPlain": "60",
                        "inputHint": "Enter the exact integer in grams",
                        "checkpointHint": "Identify the invariant component (water) which stays at 90% of 300g = 270g, and will form 75% of the new total.",
                        "commonTrapTag": "c06-variable-base-neglect",
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
                        "templateKey": "c06-rate-base-part-triad",
                        "level": 1,
                        "prompt": "Find 20% of 50.",
                        "display": "20% * 50 = ?",
                        "answerSpec": {"type": "number", "value": "10"},
                        "answerDisplay": "10",
                        "answerPlain": "10",
                        "inputHint": "The answer is 10",  # SPOILER!
                        "checkpointHint": "Divide by 100",
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


if __name__ == "__main__":
    unittest.main()
