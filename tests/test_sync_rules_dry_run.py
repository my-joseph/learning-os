# -*- coding: utf-8 -*-
"""
Tests for sync_rules_to_notion.py:
1. Verify --dry-run makes zero network calls (urllib / requests / notion_request)
2. Verify --dry-run does not modify rules/rules_map.json
3. Verify rules_map merge preserves all existing entries (06, 07, custom keys)
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from sync_rules_to_notion import (
    RULES_MAP_FILE,
    SUB_MODULES,
    get_or_create_sub_pages,
    main,
)


class TestSyncRulesDryRun(unittest.TestCase):
    def test_sub_modules_contain_06_and_07(self):
        """SUB_MODULES must include 06_TEMPLATE_CONTRACT and 07_PROBLEM_GENERATION."""
        keys = [m["key"] for m in SUB_MODULES]
        self.assertIn("06_TEMPLATE_CONTRACT", keys)
        self.assertIn("07_PROBLEM_GENERATION", keys)
        self.assertEqual(len(SUB_MODULES), 7)

    @patch("apply_rules_and_test_pages.notion_request")
    @patch("urllib.request.urlopen")
    def test_dry_run_makes_no_network_calls(self, mock_urlopen, mock_notion):
        """Dry-run must not invoke urllib.request.urlopen or notion_request."""
        with open(RULES_MAP_FILE, "r", encoding="utf-8") as f:
            original_content = f.read()
        mtime_before = os.path.getmtime(RULES_MAP_FILE)

        res = main(dry_run=True)

        mock_urlopen.assert_not_called()
        mock_notion.assert_not_called()

        # Verify rules_map.json is untouched
        with open(RULES_MAP_FILE, "r", encoding="utf-8") as f:
            current_content = f.read()
        self.assertEqual(original_content, current_content)
        self.assertEqual(mtime_before, os.path.getmtime(RULES_MAP_FILE))

        # Verify plan details
        self.assertEqual(res["to_create"], 2)  # 06 and 07 have no ID yet
        self.assertEqual(res["to_replace"], 6)  # Master Hub + 5 sub-pages
        sub_keys = [p["key"] for p in res["sub_plans"]]
        self.assertIn("06_TEMPLATE_CONTRACT", sub_keys)
        self.assertIn("07_PROBLEM_GENERATION", sub_keys)

    def test_get_or_create_sub_pages_merge_preserves_entries(self):
        """get_or_create_sub_pages must merge and preserve all existing entries."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_map_path = os.path.join(tmp_dir, "rules_map.json")
            initial_data = {
                "MASTER": "dummy-master",
                "00_CORE": "rules/00_core.md",
                "CUSTOM_EXTRA_MODULE": {
                    "id": "custom-uuid-1234",
                    "title": "Custom Module Title",
                    "file": "rules/custom.md",
                },
                "06_TEMPLATE_CONTRACT": {
                    "title": "06_TEMPLATE_CONTRACT — Problem Template & Quality Gate Engineering Contract",
                    "file": "rules/06_template_contract.md",
                },
                "07_PROBLEM_GENERATION": {
                    "title": "07_PROBLEM_GENERATION — Drill Composition, Weak-Spot Targeting, Progression & AI-Written Problem Verification",
                    "file": "rules/07_problem_generation.md",
                },
            }
            with open(tmp_map_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

            # Mock get_all_blocks to return existing child pages for 01-05
            mock_blocks = [
                {"type": "child_page", "id": f"page-id-0{i}", "child_page": {"title": SUB_MODULES[i - 1]["title"]}}
                for i in range(1, 6)
            ]
            # Mock notion_request for creating 06 and 07
            created_ids = ["page-id-06", "page-id-07"]

            def mock_notion_post(method, endpoint, token, payload=None):
                return {"id": created_ids.pop(0)}

            with (
                patch("sync_rules_to_notion.get_all_blocks", return_value=mock_blocks),
                patch("sync_rules_to_notion.notion_request", side_effect=mock_notion_post),
            ):
                merged = get_or_create_sub_pages(
                    master_pid="dummy-master",
                    token="dummy-token",
                    dry_run=False,
                    rules_map_path=tmp_map_path,
                )

            # Check that custom extra module was NOT deleted
            self.assertIn("CUSTOM_EXTRA_MODULE", merged)
            self.assertEqual(merged["CUSTOM_EXTRA_MODULE"]["id"], "custom-uuid-1234")

            # Check that 06 and 07 exist and gained an id while preserving metadata
            self.assertIn("06_TEMPLATE_CONTRACT", merged)
            self.assertEqual(merged["06_TEMPLATE_CONTRACT"]["id"], "page-id-06")
            self.assertIn("07_PROBLEM_GENERATION", merged)
            self.assertEqual(merged["07_PROBLEM_GENERATION"]["id"], "page-id-07")

            # Verify saved file on disk also preserved all keys
            with open(tmp_map_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertIn("CUSTOM_EXTRA_MODULE", saved)
            self.assertIn("06_TEMPLATE_CONTRACT", saved)
            self.assertIn("07_PROBLEM_GENERATION", saved)


if __name__ == "__main__":
    unittest.main()
