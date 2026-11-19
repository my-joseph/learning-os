"""Shared-fixture parity test for Python `progress_store.score_problem` / `item_score` / `score_variant`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import progress_store as ps

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "scoring_cases.json"
CASES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]


def test_fixture_has_at_least_25_cases():
    assert len(CASES) >= 25


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_scoring_case_parity(case: dict):
    expected = case["expected"]
    if case.get("kind") == "variant":
        actual = ps.score_variant(case["record"], case.get("cycleStartedAt"))
        assert actual == {
            "score": expected["score"],
            "outcome": expected["outcome"],
            "firstTry": expected["firstTry"],
            "usedHelp": expected["usedHelp"],
        }
        return

    opts = case.get("opts") or {}
    is_prg = bool(opts.get("isPrg", False))
    actual = ps.score_problem(case["state"], is_prg=is_prg)
    assert actual == {
        "score": expected["score"],
        "outcome": expected["outcome"],
        "firstTry": expected["firstTry"],
        "usedHelp": expected["usedHelp"],
    }

    expected_item_score = -1.0 if expected["score"] is None else float(expected["score"])
    assert ps.item_score(case["state"], is_prg=is_prg) == (expected_item_score, expected["usedHelp"])

    if "awaitingReview" in expected:
        assert ps.is_awaiting_review(case["state"]) is expected["awaitingReview"]
