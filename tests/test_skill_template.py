"""The new-math-drill draft template must always pass every gate, so agents can copy its shapes."""

import json
import os
import shutil

from math_engine.ai_drill_ingest import check_ai_drill, ingest_ai_drill

TEMPLATE_DIR = os.path.join(".claude", "skills", "new-math-drill", "template")


def _draft():
    with open(os.path.join(TEMPLATE_DIR, "draft.json"), encoding="utf-8") as f:
        return json.load(f)


def test_template_passes_check():
    assert check_ai_drill(_draft(), vault_dir=TEMPLATE_DIR) == []


def test_template_ingests(tmp_path):
    vault = tmp_path / "vault"
    shutil.copytree(TEMPLATE_DIR, vault)
    saved = ingest_ai_drill(_draft(), data_root=str(tmp_path / "data"), vault_dir=str(vault))
    assert [p["level"] for p in saved["problems"]] == [1, 2, 3, 4]
    assert os.path.exists(saved["localFilePath"])
