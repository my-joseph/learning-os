import json
import unittest

from math_engine.figure_autofill import autofill_problem_figure, build_figure


class TestFigureAutofill(unittest.TestCase):
    ARCH = [{"archetypeKey": "k", "figureBuilders": [
        {"fn": "build_circle_figure", "args": {"radius": "diameter/2"},
         "labels": {"label_radius": "d = {diameter:g}"}}]}]

    def test_attaches_from_givens(self):
        p = {"archetypeKey": "k", "givens": {"diameter": 14}}
        self.assertTrue(autofill_problem_figure(p, self.ARCH))
        self.assertEqual(p["figure"]["kind"], "geometry_2d")

    def test_skips_waiver_and_missing_givens(self):
        self.assertFalse(autofill_problem_figure({"archetypeKey": "k", "givens": {"x": 1}, "figureWaiver": "n/a"}, self.ARCH))
        self.assertIsNone(build_figure(self.ARCH[0], {"x": 1}))

    def test_c12_area_volume_drill_has_figures(self):
        d = json.load(open("drills/data/MTH-T01-C12/DRL-MTH-T01-C12-04.json"))
        missing = [p["id"] for p in d["problems"] if "figure" not in p]
        self.assertEqual(missing, ["Q09"])  # cone: no builder yet


if __name__ == "__main__":
    unittest.main()
