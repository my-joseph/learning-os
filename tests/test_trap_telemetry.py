# -*- coding: utf-8 -*-
"""Unit tests for answer_check trapValue telemetry."""

import json
import subprocess
import sys
import unittest


class TestTrapValueTelemetry(unittest.TestCase):
    def _run_main(self, payload: dict) -> dict:
        proc = subprocess.run(
            [sys.executable, "-m", "math_engine.answer_check"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(proc.stdout)

    def test_number_wrong_matching_trap(self):
        payload = {
            "answerSpec": {"type": "number", "value": "360"},
            "trapValue": "460",
            "input": "460",
        }
        res = self._run_main(payload)
        self.assertEqual(res["verdict"], "incorrect")
        self.assertTrue(res.get("trapMatched"))

    def test_number_wrong_not_matching_trap(self):
        payload = {
            "answerSpec": {"type": "number", "value": "360"},
            "trapValue": "460",
            "input": "999",
        }
        res = self._run_main(payload)
        self.assertEqual(res["verdict"], "incorrect")
        self.assertFalse(res.get("trapMatched", False))

    def test_number_correct_untouched(self):
        payload = {
            "answerSpec": {"type": "number", "value": "360"},
            "trapValue": "460",
            "input": "360",
        }
        res = self._run_main(payload)
        self.assertEqual(res["verdict"], "correct")
        self.assertNotIn("trapMatched", res)

    def test_expression_wrong_matching_trap(self):
        payload = {
            "answerSpec": {"type": "expression", "value": "2*x + 1"},
            "trapValue": "2*x - 1",
            "input": "2x - 1",
        }
        res = self._run_main(payload)
        self.assertEqual(res["verdict"], "incorrect")
        self.assertTrue(res.get("trapMatched"))

    def test_expression_wrong_not_matching_trap(self):
        payload = {
            "answerSpec": {"type": "expression", "value": "2*x + 1"},
            "trapValue": "2*x - 1",
            "input": "5*x + 3",
        }
        res = self._run_main(payload)
        self.assertEqual(res["verdict"], "incorrect")
        self.assertFalse(res.get("trapMatched", False))

    def test_vector_wrong_matching_trap(self):
        payload = {
            "answerSpec": {"type": "vector", "value": "<3, 4>"},
            "trapValue": "<4, 3>",
            "input": "<4, 3>",
        }
        res = self._run_main(payload)
        self.assertEqual(res["verdict"], "incorrect")
        self.assertTrue(res.get("trapMatched"))

    def test_vector_wrong_not_matching_trap(self):
        payload = {
            "answerSpec": {"type": "vector", "value": "<3, 4>"},
            "trapValue": "<4, 3>",
            "input": "<1, 1>",
        }
        res = self._run_main(payload)
        self.assertEqual(res["verdict"], "incorrect")
        self.assertFalse(res.get("trapMatched", False))

    def test_off_by_factor_filter_and_rounding(self):
        from math_engine.answer_check import check_answer

        # 999 vs 403 must have NO diagnostics
        res_999 = check_answer({"type": "number", "value": "403"}, "999")
        self.assertEqual(res_999["verdict"], "incorrect")
        self.assertEqual(res_999.get("diagnostics", []), [])

        # 160 vs 80 must have off_by_factor (factor 2)
        res_160 = check_answer({"type": "number", "value": "80"}, "160")
        self.assertEqual(res_160["verdict"], "incorrect")
        diags_160 = [d["code"] for d in res_160.get("diagnostics", [])]
        self.assertIn("off_by_factor", diags_160)

        # 40 vs 80 must have off_by_factor (factor 1/2)
        res_40 = check_answer({"type": "number", "value": "80"}, "40")
        self.assertEqual(res_40["verdict"], "incorrect")
        diags_40 = [d["code"] for d in res_40.get("diagnostics", [])]
        self.assertIn("off_by_factor", diags_40)

        # 0.667 vs 2/3 must NOT be off_by_factor
        res_dec = check_answer({"type": "number", "value": "2/3"}, "0.667")
        self.assertEqual(res_dec["verdict"], "incorrect")
        diags_dec = [d["code"] for d in res_dec.get("diagnostics", [])]
        self.assertNotIn("off_by_factor", diags_dec)
        self.assertIn("rounding", diags_dec)

    def test_floor_division_evaluator(self):
        from math_engine.answer_check import to_expr, safe_parse, SafeParseError
        import sympy as sp

        # Trusted evaluator (used by trapDerivation) supports // and floor(a/b)
        val_floor_op = to_expr("17 // 5", trusted=True)
        self.assertEqual(val_floor_op, sp.Integer(3))

        val_floor_func = to_expr("floor(17 / 5)", trusted=True)
        self.assertEqual(val_floor_func, sp.Integer(3))

        # Untrusted safe_parse rejects floor and //
        with self.assertRaises(SafeParseError):
            safe_parse("17 // 5", trusted=False)

        with self.assertRaises(SafeParseError):
            safe_parse("floor(17 / 5)", trusted=False)

    def test_verify_problem_trap_derivation_rules(self):
        import logging
        from quality_rules import QualityError
        from math_engine.verify import verify_problem

        base_problem = {
            "id": "test-p1",
            "level": 1,
            "prompt": "Compute 2 + 2",
            "plainText": "2 + 2",
            "answerPlain": "4",
            "answerDisplay": "4",
            "answerSpec": {"type": "number", "value": "4"},
            "verify": {"source": "2 + 2", "trapValue": "5"},
            "commonTrapTag": "arithmetic-error",
            "steps": [{"latex": "2+2=4", "explain": "add", "val": "4"}],
            "inputHint": "Enter a number",
            "checkpointHint": "Think of 2 plus 2",
        }

        # 1. Pure numeric derivation raises QualityError("G4")
        prob_numeric = dict(base_problem, trapDerivation="5")
        with self.assertRaises(QualityError) as ctx:
            verify_problem(prob_numeric)
        self.assertEqual(ctx.exception.gate, "G4")
        self.assertIn("purely numeric", ctx.exception.reason)

        # 2. trapKind="selection" allows missing/None derivation without error
        prob_selection = dict(base_problem, trapKind="selection", trapDerivation=None)
        prob_selection["verify"] = {"source": "4", "trapValue": "2"}
        self.assertTrue(verify_problem(prob_selection))

        # 3. Missing trapDerivation logs warning only, does not raise QualityError
        prob_missing = dict(base_problem)
        prob_missing.pop("trapDerivation", None)
        with self.assertLogs("math_engine.verify", level=logging.WARNING) as log_ctx:
            self.assertTrue(verify_problem(prob_missing))
        self.assertTrue(any("Template form has no trapDerivation field" in msg for msg in log_ctx.output))


        # 4. trapGiven not appearing in prompt raises QualityError("G4")
        prob_bad_given = dict(
            base_problem,
            prompt="Compute 2 + 3",
            trapDerivation="2 + 7",
            trapGivens=[2, 7],
        )
        prob_bad_given["verify"] = {"source": "4", "trapValue": "9"}
        with self.assertRaises(QualityError) as ctx:
            verify_problem(prob_bad_given)
        self.assertEqual(ctx.exception.gate, "G4")
        self.assertIn("does not appear in prompt", ctx.exception.reason)

        # 5. trapDerivation with fewer than 2 distinct givens raises QualityError("G4")
        prob_single_given = dict(
            base_problem,
            prompt="Compute 2 + 2",
            trapDerivation="2 * 2 + 1",
            trapGivens=[2],
        )
        prob_single_given["verify"] = {"source": "4", "trapValue": "5"}
        with self.assertRaises(QualityError) as ctx:
            verify_problem(prob_single_given)
        self.assertEqual(ctx.exception.gate, "G4")
        self.assertIn("must contain at least 2 distinct givens", ctx.exception.reason)

        # 6. C01/C12 missing trapGivens raises QualityError("G4")
        prob_c01_missing = dict(
            base_problem,
            references=["MTH-T01-C01-U01"],
            trapDerivation="2 + 3",
        )
        with self.assertRaises(QualityError) as ctx:
            verify_problem(prob_c01_missing)
        self.assertEqual(ctx.exception.gate, "G4")
        self.assertIn("Templates in C01 and C12 must provide 'trapGivens'", ctx.exception.reason)

        # 7. Valid trapGivens with >= 2 distinct givens passes
        prob_valid = dict(
            base_problem,
            prompt="Find sum of 2 and 3",
            references=["MTH-T01-C01-U01"],
            trapDerivation="2 + 3",
            trapGivens=[2, 3],
        )
        self.assertTrue(verify_problem(prob_valid))


if __name__ == "__main__":
    unittest.main()
