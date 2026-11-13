"""Solution-leak gate and formula `constants` (07 §4).

Examples are taken from real drills that passed the old contract while giving
away their own solution.
"""
from __future__ import annotations

import copy
import unittest

from math_engine.ai_drill_ingest import (
    AiContractError,
    find_solution_leaks,
    validate_ai_problem_contract,
)
from math_engine.verify import verify_problem

LEAKY_PROMPTS = [
    # unknown set equal to the worked computation
    "A rectangular garden plot has length $14$ meters and width $8$ meters. Calculate the perimeter "
    "$P$ in meters using $P = 2(14) + 2(8)$.",
    # numbers re-listed by algebraic role
    "Solve the two-step linear equation $5x + 15 = 60$ for $x$, with coefficient $5$, constant $15$, "
    "and target value $60$.",
    # arithmetic handed over with "using"
    "Two angles are complementary and sum to $90$ degrees. If the first angle measures $34$ degrees, "
    "calculate the complementary angle using $90 - 34$.",
    # arithmetic handed over with "by evaluating"
    "Find the midpoint of $x$-coordinates $4$ and $16$ by evaluating $(4 + 16) \\div 2$.",
    # second "calculate" spells out the substitution
    "Evaluate $7x + 15$ for $x = 4$. Calculate $7 \\times 4 + 15$.",
]

CLEAN_PROMPTS = [
    "Solve $5x + 15 = 60$ for $x$.",
    "Evaluate $18 - 3 \\times (4 + 2)$.",
    "Evaluate $2^3 \\times 2^4$.",
    "Simplify $\\frac{36}{4} + 5 \\times 3$.",
    "Use $A = \\pi r^2$ to find the area of a circle with radius $3$ meters.",
    "A tank holds $V = 1200$ liters.",
    "Evaluate $7x + 15$ when $x = 4$.",
    "A rectangular garden plot is $14$ meters long and $8$ meters wide. How many meters of fencing "
    "are needed to enclose it?",
    "A circle has radius $15$ meters and circumference $C = c\\pi$. Find $c$ by using the radius.",
]


def perimeter_problem(**overrides):
    """A clean C12-style problem whose method needs the constant 2 (P = 2L + 2W)."""
    prob = {
        "id": "Q01",
        "level": 1,
        "verificationLevel": "partial",
        "prompt": "A rectangular garden plot is $14$ meters long and $8$ meters wide. "
        "How many meters of fencing are needed to enclose it?",
        "display": "P = 2L + 2W",
        "plainText": "P = 2*14 + 2*8",
        "givens": {"len": 14, "wid": 8},
        "constants": {"factor": 2},
        "trapGivens": [14, 8],
        "trapDerivation": "14 + 8",
        "verify": {"source": "44", "trapValue": "22"},
        "answerSpec": {"type": "number", "value": "44", "tolerance": 0.001},
        "answerPlain": "44",
        "answerDisplay": "44",
        "checkpointHint": "Fencing goes around all four sides.",
        "steps": [
            {"latex": "2 \\times 14 = 28", "explain": "Double the length."},
            {"latex": "2 \\times 8 = 16", "explain": "Double the width."},
            {"latex": "28 + 16 = 44", "explain": "Add both pairs of sides.", "val": "44"},
        ],
    }
    prob.update(overrides)
    return prob


class FindSolutionLeaks(unittest.TestCase):
    def test_flags_leaky_prompts(self):
        for prompt in LEAKY_PROMPTS:
            with self.subTest(prompt=prompt):
                self.assertTrue(find_solution_leaks(prompt), "should be flagged")

    def test_accepts_clean_prompts(self):
        for prompt in CLEAN_PROMPTS:
            with self.subTest(prompt=prompt):
                self.assertEqual(find_solution_leaks(prompt), [])

    def test_display_setup_flagged_only_when_prompt_does_not_give_it(self):
        word = "A plot is $14$ m long and $8$ m wide. How much fencing is needed?"
        self.assertTrue(find_solution_leaks(word, "P = 2(14) + 2(8)"))
        self.assertTrue(find_solution_leaks("Find $x$ in $4x = 24$.", "4x = 24 \\implies x = \\frac{24}{4}"))
        self.assertEqual(find_solution_leaks(word, "P = 2L + 2W"), [])
        # the expression to evaluate IS the problem
        self.assertEqual(
            find_solution_leaks("Evaluate $18 - 3 \\times (4 + 2)$.", "18 - 3 \\times (4 + 2) = ?"), []
        )


class ContractWithConstants(unittest.TestCase):
    def test_clean_problem_with_formula_constant_passes_all_gates(self):
        prob = perimeter_problem()
        self.assertTrue(validate_ai_problem_contract(copy.deepcopy(prob)))
        self.assertTrue(verify_problem(copy.deepcopy(prob)))

    def test_constant_without_declaration_still_rejected(self):
        # 2 is stated nowhere and declared nowhere: the old two-way rule still applies to givens.
        prob = perimeter_problem(givens={"len": 14, "wid": 8, "factor": 2}, constants={})
        with self.assertRaisesRegex(AiContractError, "does not appear in prompt"):
            validate_ai_problem_contract(prob)

    def test_undeclared_number_in_prompt_rejected(self):
        prob = perimeter_problem(prompt=perimeter_problem()["prompt"] + " The gate is $3$ meters wide.")
        with self.assertRaisesRegex(AiContractError, "not defined in givens"):
            validate_ai_problem_contract(prob)

    def test_key_in_both_givens_and_constants_rejected(self):
        prob = perimeter_problem(constants={"len": 14})
        with self.assertRaisesRegex(AiContractError, "both 'givens' and 'constants'"):
            validate_ai_problem_contract(prob)

    def test_trap_may_use_a_constant(self):
        # Adding 2 + r instead of computing 2r is a real misconception.
        prob = perimeter_problem(
            prompt="A circular plaza has radius $15$ meters. Its circumference is $C = c\\pi$ meters. Find $c$.",
            display="C = 2\\pi r",
            plainText="c = 2 * 15",
            givens={"radius": 15},
            constants={"mult": 2},
            trapGivens=[2, 15],
            trapDerivation="2 + 15",
            verify={"source": "30", "trapValue": "17"},
            answerSpec={"type": "number", "value": "30", "tolerance": 0.001},
            answerPlain="30",
            answerDisplay="30",
            checkpointHint="Circumference uses the diameter.",
            steps=[
                {"latex": "d = 2 \\times 15", "explain": "The diameter is twice the radius."},
                {"latex": "c = 30", "explain": "Circumference is pi times the diameter.", "val": "30"},
            ],
        )
        self.assertTrue(validate_ai_problem_contract(copy.deepcopy(prob)))
        self.assertTrue(verify_problem(copy.deepcopy(prob)))

    def test_leaky_prompt_rejected_at_contract(self):
        prob = perimeter_problem(
            prompt="A rectangular garden plot has length $14$ meters and width $8$ meters. "
            "Calculate the perimeter $P$ using $P = 2(14) + 2(8)$."
        )
        with self.assertRaisesRegex(AiContractError, "gives away the solution"):
            validate_ai_problem_contract(prob)

    def test_leak_gate_can_be_skipped_for_legacy_drills(self):
        prob = perimeter_problem(
            prompt="A plot has length $14$ m and width $8$ m. Find the perimeter using $14 + 14 + 8 + 8$."
        )
        with self.assertRaises(AiContractError):
            validate_ai_problem_contract(copy.deepcopy(prob))
        self.assertTrue(validate_ai_problem_contract(copy.deepcopy(prob), enforce_leak_gate=False))

    def test_exponents_count_as_stated_givens(self):
        # Before: ^2/^3 were stripped, so "3" in 2^3 looked missing and the AI re-listed it.
        prob = perimeter_problem(
            prompt="Evaluate $2^3 \\times 2^4$.",
            display="2^3 \\times 2^4",
            plainText="2^3 * 2^4",
            givens={"base": 2, "exp1": 3, "exp2": 4},
            constants={},
            trapGivens=None,
            trapDerivation="2 ** (3 * 4)",
            verify={"source": "128", "trapValue": "4096"},
            answerSpec={"type": "number", "value": "128", "tolerance": 0.001},
            answerPlain="128",
            answerDisplay="128",
            checkpointHint="Same base: think about what happens to the exponents.",
            steps=[
                {"latex": "2^3 \\times 2^4 = 2^{7}", "explain": "Add exponents of a shared base."},
                {"latex": "2^{7} = 128", "explain": "Evaluate the power.", "val": "128"},
            ],
        )
        self.assertTrue(validate_ai_problem_contract(copy.deepcopy(prob)))


if __name__ == "__main__":
    unittest.main()
