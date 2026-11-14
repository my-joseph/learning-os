import json
import unittest

from math_engine.figure_autofill import autofill_problem_figure, build_figure


class TestFigureAutofill(unittest.TestCase):
    ARCH = [
        {
            "archetypeKey": "k",
            "figureBuilders": [
                {
                    "fn": "build_circle_figure",
                    "args": {"radius": "diameter/2"},
                    "labels": {"label_radius": "d = {diameter:g}"},
                }
            ],
        }
    ]

    def test_attaches_from_givens(self):
        p = {"archetypeKey": "k", "givens": {"diameter": 14}}
        self.assertTrue(autofill_problem_figure(p, self.ARCH))
        self.assertEqual(p["figure"]["kind"], "geometry_2d")

    def test_skips_waiver_and_missing_givens(self):
        self.assertFalse(
            autofill_problem_figure({"archetypeKey": "k", "givens": {"x": 1}, "figureWaiver": "n/a"}, self.ARCH)
        )
        self.assertIsNone(build_figure(self.ARCH[0], {"x": 1}))

    def test_guard_rejects_declared_archetype_without_figure(self):
        from math_engine.ai_drill_ingest import AiContractError, require_figure_if_declared

        with self.assertRaises(AiContractError):
            require_figure_if_declared({"id": "Q1", "archetypeKey": "k", "givens": {"x": 1}}, self.ARCH)
        require_figure_if_declared(
            {"id": "Q1", "archetypeKey": "k", "givens": {"x": 1}, "figureWaiver": "text only"}, self.ARCH
        )

    def test_all_active_drills_satisfy_rule_11(self):
        import glob
        import os

        from math_engine.ai_drill_ingest import require_figure_if_declared

        for vf in glob.glob("math_engine/reasoning_vault/*.json"):
            archs = json.load(open(vf)).get("archetypes", [])
            unit = os.path.basename(vf)[:-5]
            for f in glob.glob(f"drills/data/{unit}/*.json"):
                for p in json.load(open(f))["problems"]:
                    require_figure_if_declared(p, archs)

    def test_new_builders_render_svg(self):
        from math_engine import figure_builder as fb

        for fig in (
            fb.build_cone_figure(6, 10),
            fb.build_angle_pair_figure(180, 65),
            fb.build_triangle_angles_figure(45, 65),
            fb.build_gable_facade_figure(10, 6, 4),
        ):
            self.assertIn("<svg", fb.figure_to_svg(fig))


if __name__ == "__main__":
    unittest.main()
