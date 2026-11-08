# -*- coding: utf-8 -*-
"""Permanent regression test: sweep all MTH-T01 units across fixed seeds."""

import os
import tempfile
import unittest
from math_engine.generate import generate_drill_set


class TestSweepMTHT01(unittest.TestCase):
    def test_sweep_all_units_fixed_seeds(self):
        """Sweep all 14 units of MTH-T01 with fixed seeds (execution time <= 40s)."""
        seeds = [42, 101, 202, 555, 999]
        os.environ["NOTION_DRY_RUN"] = "1"
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(1, 15):
                unit_code = f"MTH-T01-C{i:02d}"
                for s in seeds:
                    with self.subTest(unit=unit_code, seed=s):
                        drill_data = generate_drill_set(
                            unit_code=unit_code,
                            count=8,
                            seed=s,
                            data_root=tmpdir,
                        )
                        self.assertIn("localFilePath", drill_data)
                        self.assertTrue(os.path.exists(drill_data["localFilePath"]))
                        self.assertEqual(len(drill_data["problems"]), 8)


if __name__ == "__main__":
    unittest.main()
