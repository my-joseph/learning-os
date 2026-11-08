# -*- coding: utf-8 -*-
"""Test float division precision in to_expr and verify_problem."""

import unittest
import sympy as sp
from math_engine.answer_check import to_expr, is_equal, safe_parse
from math_engine.verify import verify_problem
from math_engine.templates._prealg_helpers import S


class TestC05FloatPrecision(unittest.TestCase):
    def test_float_division_to_expr_is_rational(self):
        e1 = to_expr("5.4 / 0.09")
        self.assertIsInstance(e1, (sp.Integer, sp.Rational))
        self.assertEqual(e1, sp.Integer(60))

        e2 = to_expr("6.3 / 0.07")
        self.assertIsInstance(e2, (sp.Integer, sp.Rational))
        self.assertEqual(e2, sp.Integer(90))

    def test_float_division_equality_with_variables(self):
        el = to_expr("5.4 / 0.09", variables=["x"])
        er = to_expr("60", variables=["x"])
        self.assertTrue(is_equal(el, er, variables=["x"]))

        el2 = to_expr("6.3 / 0.07", variables=["x"])
        er2 = to_expr("90", variables=["x"])
        self.assertTrue(is_equal(el2, er2, variables=["x"]))

    def test_c05_step_equality_passes_verification(self):
        prob = {
            "id": "Q06",
            "templateKey": "c05-decimal-division-shift-trap",
            "form": "direct",
            "level": 3,
            "skill": "MTH-PREALG-C05-DIV-TRAP",
            "verificationLevel": "machine-verified",
            "category": "Core Skill",
            "context": "Decimals: Division",
            "prompt": "Evaluate $5.4 \\div 0.09$.",
            "display": "5.4 / 0.09",
            "plainText": "5.4 / 0.09",
            "answerSpec": {"type": "number", "value": "60"},
            "answerDisplay": "60",
            "answerPlain": "60",
            "checkpointHint": "Shift decimals",
            "commonTrapTag": "c05-decimal-shift-trap",
            "verify": {"source": "60", "trapValue": "6"},
            "steps": [
                S(r"\frac{5.4}{0.09} = 60", "Shift and divide.", eq=["5.4 / 0.09", "60"]),
                S("60 = 60", "Result.", val="60", eq=["60", "60"]),
            ],
        }
        # Should not raise VerificationError
        self.assertTrue(verify_problem(prob))


if __name__ == "__main__":
    unittest.main()
