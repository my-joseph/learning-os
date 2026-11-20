"""Shared-fixture parity tests for covered units (`drill_sync.covered_units`) and
session summary metrics (`scripts.practice._summary`) vs Studio (`sessionSummary.ts`)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from notion_sync.drill_sync import covered_units
from scripts.practice import _summary

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "session_summary_cases.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
COVERED_CASES = FIXTURE["coveredUnitsCases"]
SUMMARY_CASES = FIXTURE["summaryCases"]


def _id_map_for(drill: dict) -> dict[str, dict[str, str]]:
    """Build an id_map containing every non-concept unit/chapter code referenced in the fixture."""
    codes: set[str] = set()
    if isinstance(drill.get("unitCode"), str):
        codes.add(drill["unitCode"])
    for p in drill.get("problems", []):
        if isinstance(p.get("unitCode"), str):
            codes.add(p["unitCode"])
        for u in p.get("unitCodes") or []:
            if isinstance(u, str):
                codes.add(u)
        for ref in p.get("references") or []:
            if isinstance(ref, str) and not ref.startswith("CON-"):
                codes.add(ref)
    return {code: {"id": f"page-{code}", "title": code} for code in codes}


@pytest.mark.parametrize("case", COVERED_CASES, ids=[c["id"] for c in COVERED_CASES])
def test_covered_units_fixture_parity(case: dict) -> None:
    drill = case["drill"]
    actual = covered_units(drill, drill["unitCode"], _id_map_for(drill))
    assert actual == case["expected"]


@pytest.mark.parametrize("case", SUMMARY_CASES, ids=[c["id"] for c in SUMMARY_CASES])
def test_practice_summary_fixture_parity(case: dict) -> None:
    actual = _summary(case["drill"])
    expected = case["expected"]
    assert actual["score"] == expected["score"]
    assert actual["maxScore"] == expected["maxScore"]
    assert actual["accuracyPct"] == expected["accuracyPct"]
    assert actual["practiceStatus"] == expected["practiceStatus"]
    assert actual["skippedCount"] == expected["skippedCount"]
