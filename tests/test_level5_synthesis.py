# -*- coding: utf-8 -*-
"""
Test Suite: Level 5 Non-Routine Problem Generation & Multi-Topic Synthesis
Validates:
1. Gate G2 compatibility with Level 5 (no arbitrary step cap, accommodating granular Photomath derivations).
2. Granular Step-by-Step Derivation Standard (rules/00_core.md §7, rules/03_stem.md §1):
   - Single transformation per step
   - Anti-clumping (rejection of horizontal equality chaining)
3. Multi-Topic Blending (Synthesis across Geometry C12 + Roots C09 + Decimals C05).
4. Auto-resolution of reference badges from id_map.json.
5. Ingestion of Level 5 Synthesis Drills and compatibility with Practice Studio data models.
"""

import json
import os
import shutil
import tempfile
import unittest

from math_engine.ai_drill_ingest import (
    AiContractError,
    ingest_ai_drill,
    load_reasoning_vault,
    register_archetype,
    validate_ai_problem_contract,
)
from math_engine.verify import verify_problem
from quality_rules import check_gate_g2


class TestLevel5Synthesis(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.vault_dir = os.path.join(self.test_dir, "vaults")
        self.data_dir = os.path.join(self.test_dir, "drills", "data")
        os.makedirs(self.vault_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        # Sample archetype blending Geometry C12 + Roots C09 + Decimals C05
        self.sample_archetype = {
            "archetypeKey": "syn-c12-c09-c05-spatial-radical-metric",
            "level": 5,
            "name": "Spatial Incline & Radical Metric Synthesis",
            "coreConcept": "Synthesize 3D spatial diagonal and incline distances, simplify to exact radical form, and compute precision decimal bounds.",
            "mentalModel": "Space diagonal in 3D Euclidean solid coupled with radical extraction and metric rounding.",
            "governingRelation": "d = \\sqrt{w^2 + l^2 + h^2}",
            "cognitiveTraps": [
                "c12-3d-dimension-omission-trap",
                "c12-height-divisor-only-trap",
                "c09-premature-radical-sum-trap",
                "c05-intermediate-rounding-error-trap",
            ],
            "versatileDomains": [
                "structural_space_truss_diagonal",
                "subsea_anchor_cable_triangulation",
                "aerospace_sensor_mast_clearance",
            ],
            "usedContexts": [],
        }
        register_archetype("MTH-SYNTHESIS", self.sample_archetype, vault_dir=self.vault_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _build_valid_l5_problem(self):
        """Constructs a fully compliant Level 5 problem blending Geometry + Roots + Decimals."""
        return {
            "id": "Q01",
            "level": 5,
            "levelLabel": "Level 5 - Non-Routine Synthesis",
            "category": "Interleaved Synthesis",
            "archetypeKey": "syn-c12-c09-c05-spatial-radical-metric",
            "skill": "GEO-RIGHT-TRIANGLE-LEG",
            "context": "structural_space_truss_diagonal",
            "contextCheck": {"verdict": "ok", "note": "Space diagonal of a box frame is the real 3D Pythagorean law."},
            "prompt": "An aerospace structural truss frame has dimensions of width 6 m, length 8 m, and height 24 m. First, determine the exact space diagonal distance $d$ across the opposite corners. Next, calculate the clearance aspect ratio $\\frac{d}{7}$ and express it rounded to two decimal places.",
            "display": "d = \\sqrt{6^2 + 8^2 + 24^2}, \\quad \\text{Ratio} = \\frac{d}{7}",
            "plainText": "d = sqrt(6^2 + 8^2 + 24^2), Ratio = d / 7",
            "givens": {"w": 6, "l": 8, "h": 24, "divisor": 7},
            "steps": [
                {
                    "latex": "d^2 = w^2 + l^2 + h^2",
                    "explain": "Set up the 3D space diagonal formula using the Pythagorean theorem.",
                },
                {
                    "latex": "d^2 = 6^2 + 8^2 + 24^2",
                    "explain": "Substitute given dimensions into the space diagonal equation.",
                },
                {"latex": "d^2 = 36 + 8^2 + 24^2", "explain": "Evaluate 6^2 to 36."},
                {"latex": "d^2 = 36 + 64 + 24^2", "explain": "Evaluate 8^2 to 64."},
                {"latex": "d^2 = 36 + 64 + 576", "explain": "Evaluate 24^2 to 576."},
                {"latex": "d^2 = 100 + 576", "explain": "Simplify 36 + 64 to 100."},
                {"latex": "d^2 = 676", "explain": "Simplify 100 + 576 to 676."},
                {"latex": "d = \\sqrt{676}", "explain": "Take the principal square root of both sides."},
                {"latex": "d = 26", "explain": "Simplify square root of 676 to 26 meters."},
                {"latex": "\\text{Ratio} = \\frac{26}{7}", "explain": "Form the clearance ratio with divisor 7."},
                {
                    "latex": "\\text{Ratio} \\approx 3.7142857",
                    "explain": "Evaluate fraction division to higher decimal precision.",
                },
                {
                    "latex": "\\text{Ratio} = 3.71",
                    "explain": "Round the final clearance ratio to two decimal places.",
                    "val": "3.71",
                },
            ],
            "verify": {"source": "3.71", "trapValue": "24/7"},
            "answerSpec": {
                "type": "number",
                "value": "3.71",
                "commonTrapTag": "c12-height-divisor-only-trap",
                "trapValue": "24/7",
            },
            "answerDisplay": "3.71",
            "answerPlain": "3.71",
            "inputHint": "Enter the final decimal rounded to 2 decimal places (e.g. 5.12)",
            "checkpointHint": "First compute the Euclidean space diagonal using the sum of squared orthogonal dimensions, then divide by the scale divisor and round.",
            "trapGivens": [24, 7],
            "commonTrapTag": "c12-height-divisor-only-trap",
            "blindSolve": {
                "answer": "3.71",
                "ambiguous": False,
                "setup": "model",
                "strategy": "invent",  # L5 must map exactly to L5
                "check": "none",
                "task": "compute",
                "reverse": False,
                "steps": 9,
            },
            "trapDerivation": "24 / 7",
            "references": ["MTH-T01-C12", "MTH-T01-C09", "MTH-T01-C05"],
            "verificationLevel": "partial",
            "review": {"verdict": "pass", "note": "Answer re-solved; prompt unambiguous; fits brief."},
            "state": {"userInput": "", "score": None, "divergedStep": None, "mistakes": []},
        }

    def test_gate_g2_accepts_level5_with_granular_steps(self):
        """Verify Gate G2 accepts Level 5 problems with 12 granular derivation steps."""
        prob = self._build_valid_l5_problem()
        res = check_gate_g2(prob)
        self.assertTrue(res["passed"])
        self.assertEqual(res["level"], 5)
        self.assertEqual(res["stepCount"], 12)

    def test_anti_clumping_rule_catches_horizontal_chaining(self):
        """Verify that horizontal equality chaining (e.g. A = B = C) triggers an AiContractError under rules/00_core.md §7."""
        prob = self._build_valid_l5_problem()
        # Introduce horizontal chaining into step 3:
        prob["steps"][2]["latex"] = "d^2 = 36 + 64 + 576 = 100 + 576 = 676"
        with self.assertRaises(AiContractError) as ctx:
            validate_ai_problem_contract(prob)
        self.assertIn("violates 00_core §7 / 03_stem §1", str(ctx.exception))
        self.assertIn("horizontal equality chaining is forbidden", str(ctx.exception))

    def test_cross_topic_blending_and_contract_validation(self):
        """Verify full AI Problem Contract validation for a Level 5 cross-topic problem."""
        prob = self._build_valid_l5_problem()
        # Must pass contract validation
        self.assertTrue(validate_ai_problem_contract(prob))
        # Must pass verify_problem (SymPy verification, LaTeX formatting, no answer leaks)
        verify_problem(prob)

    def test_auto_resolution_of_reference_badges(self):
        """Verify that ingest_ai_drill automatically populates referenceBadges from id_map.json."""
        prob = self._build_valid_l5_problem()
        drill_doc = {"unitCode": "MTH-SYNTHESIS", "unitTitle": "Multi-Topic Mathematical Synthesis", "problems": [prob]}
        res = ingest_ai_drill(drill_doc, data_root=self.data_dir, vault_dir=self.vault_dir)
        ingested_prob = res["problems"][0]

        # Verify referenceBadges populated
        badges = ingested_prob.get("referenceBadges")
        self.assertIsNotNone(badges)
        self.assertEqual(len(badges), 3)

        badge_codes = [b["code"] for b in badges]
        self.assertIn("MTH-T01-C12", badge_codes)
        self.assertIn("MTH-T01-C09", badge_codes)
        self.assertIn("MTH-T01-C05", badge_codes)

        # Verify badge titles from id_map.json
        c12_badge = next(b for b in badges if b["code"] == "MTH-T01-C12")
        self.assertEqual(c12_badge["title"], "Math Models and Geometry")
        self.assertTrue(c12_badge["notionUrl"].startswith("https://www.notion.so/"))

    def test_ingest_and_save_level5_synthesis_drill(self):
        """Verify that an L5 synthesis drill is materialized to disk and passes all invariants."""
        prob = self._build_valid_l5_problem()
        drill_doc = {"unitCode": "MTH-SYNTHESIS", "problems": [prob]}
        res = ingest_ai_drill(drill_doc, data_root=self.data_dir, vault_dir=self.vault_dir)
        self.assertTrue(os.path.exists(res["localFilePath"]))

        # Verify file content on disk
        with open(res["localFilePath"], "r", encoding="utf-8") as f:
            disk_doc = json.load(f)

        self.assertEqual(disk_doc["unitCode"], "MTH-SYNTHESIS")
        self.assertEqual(len(disk_doc["problems"]), 1)
        self.assertEqual(disk_doc["problems"][0]["level"], 5)

        # Verify vault updated context
        vault = load_reasoning_vault("MTH-SYNTHESIS", vault_dir=self.vault_dir)
        arch = vault["archetypes"][0]
        self.assertIn("structural_space_truss_diagonal", arch["usedContexts"])


if __name__ == "__main__":
    unittest.main()
