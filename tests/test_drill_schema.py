"""Committed drill JSON files must keep the shape the Studio (src/types/drill.ts) relies on."""

import glob
import json

import pytest

PATHS = sorted(glob.glob("drills/data/*/DRL-*.json"))


@pytest.mark.parametrize("path", PATHS)
def test_drill_has_core_fields(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    for key in ("drillId", "unitCode", "problems"):
        assert key in doc, f"{path} missing {key}"
    assert doc["problems"], f"{path} has no problems"
    for p in doc["problems"]:
        assert "id" in p and "prompt" in p
        # Test-graded code problems are checked by visible/hidden tests, not an answerSpec.
        if p.get("visibleTests") or p.get("hiddenTests"):
            continue
        assert "answerSpec" in p, f"{path} {p['id']} has neither answerSpec nor tests"
        assert "type" in p["answerSpec"]
