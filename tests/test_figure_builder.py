# -*- coding: utf-8 -*-
import unittest

from math_engine.ai_drill_ingest import AiContractError, validate_ai_problem_contract
from math_engine.figure_builder import (
    build_cartesian_line_figure,
    build_cartesian_point_figure,
    build_circle_figure,
    build_rectangle_figure,
    build_right_triangle_figure,
    figure_to_svg,
)


class TestFigureBuilder(unittest.TestCase):
    def test_rectangle_figure_spec(self):
        fig = build_rectangle_figure(12, 5, label_w="12\\text{ m}", label_h="5\\text{ m}")
        self.assertEqual(fig["kind"], "geometry_2d")
        self.assertIn("A", fig["points"])
        self.assertEqual(fig["points"]["B"], [12, 0])
        self.assertEqual(fig["points"]["C"], [12, 5])
        self.assertEqual(fig["markers"][0]["type"], "right_angle")
        svg = figure_to_svg(fig)
        self.assertIn("<svg", svg)
        self.assertIn("<polygon", svg)
        self.assertIn("12\\text{ m}", svg)

    def test_right_triangle_figure_spec(self):
        fig = build_right_triangle_figure(6, 8, label_hypot="10")
        self.assertEqual(fig["kind"], "geometry_2d")
        self.assertEqual(fig["points"]["B"], [6, 0])
        self.assertEqual(fig["points"]["C"], [0, 8])
        svg = figure_to_svg(fig)
        self.assertIn("<polyline", svg)
        self.assertIn("10", svg)

    def test_circle_figure_spec(self):
        fig = build_circle_figure(4.5)
        self.assertEqual(fig["kind"], "geometry_2d")
        self.assertEqual(fig["shapes"][0]["type"], "circle")
        self.assertEqual(fig["shapes"][0]["radius"], 4.5)
        svg = figure_to_svg(fig)
        self.assertIn("<circle", svg)

    def test_cartesian_point_figure_spec(self):
        fig = build_cartesian_point_figure((3, 4), label="P(3, 4)")
        self.assertEqual(fig["kind"], "cartesian_graph")
        self.assertTrue(fig["axes"])
        self.assertTrue(fig["grid"])
        self.assertEqual(len(fig["plots"]), 3)  # 2 dashed projections + 1 point
        svg = figure_to_svg(fig)
        self.assertIn("P(3, 4)", svg)

    def test_cartesian_line_figure_spec(self):
        fig = build_cartesian_line_figure(2, -4, x_range=(-4, 6), y_range=(-6, 8))
        self.assertEqual(fig["kind"], "cartesian_graph")
        self.assertEqual(fig["plots"][0]["type"], "function")
        self.assertEqual(fig["plots"][0]["coefficients"], [2, -4])
        svg = figure_to_svg(fig)
        self.assertIn("<polyline", svg)

    def test_contract_validation_figure_valid(self):
        prob = {
            "id": "Q_FIG_01",
            "prompt": "Given length $10$ and height $5$, solve geometry.",
            "display": "P = 2(10) + 2(5)",
            "plainText": "P = 2*10 + 2*5",
            "context": "Context",
            "checkpointHint": "Hint",
            "givens": {"w": 10, "h": 5},
            "trapValue": "15",
            "trapDerivation": "10 + 5",
            "answerSpec": {"type": "number", "value": "10"},
            "verify": {"source": "10", "trapValue": "15"},
            "steps": [{"latex": "x = 10", "explain": "Solve for x."}],
            "figure": build_rectangle_figure(10, 5),
        }
        self.assertTrue(validate_ai_problem_contract(prob))

    def test_contract_validation_figure_invalid_kind(self):
        prob = {
            "id": "Q_FIG_02",
            "prompt": "Given length $10$ and height $5$, solve geometry.",
            "context": "Context",
            "checkpointHint": "Hint",
            "givens": {"w": 10, "h": 5},
            "answerSpec": {"type": "number", "value": "10"},
            "verify": {"source": "10"},
            "steps": [{"latex": "x = 10", "explain": "Solve for x."}],
            "figure": {"theme": "indigo"},  # Missing kind
        }
        with self.assertRaises(AiContractError):
            validate_ai_problem_contract(prob)


if __name__ == "__main__":
    unittest.main()
