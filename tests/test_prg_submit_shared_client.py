"""Hermetic tests for unified PRG submit paths (submit_lab.py and code_engine/submit.py)."""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from code_engine import submit as drill_submit
from labs.common import submit_lab
from notion_sync import client as notion_client
from progress_store import save_progress, score_problem


def _sample_lab_setup(tmp_path: Path) -> tuple[Path, Path, dict, dict]:
    repo_root = tmp_path / "repo"
    lab_dir = repo_root / "labs" / "LAB-PRG-TEST-01"
    lab_dir.mkdir(parents=True)
    (repo_root / "id_map.json").write_text(
        json.dumps({"DRILLS_DB": {"id": "db-123"}, "LAB-PRG-TEST-01": {"id": "page-123"}}),
        encoding="utf-8",
    )
    config = {
        "labId": "LAB-PRG-TEST-01",
        "title": "Test Lab",
        "unitCode": "PRG-T01-C04-U01",
        "chapterCode": "PRG-T01-C04",
        "topicCode": "PRG-T01",
    }
    eval_result = {
        "milestones": [
            {
                "id": "M1",
                "title": "Milestone 1",
                "points": 50,
                "earned": 50,
                "passed": True,
                "pass_count": 1,
                "test_count": 1,
                "testcases": [{"name": "ok", "time": 0.01, "passed": True}],
                "failures": [],
                "category": "Logic",
            }
        ],
        "total_score": 50,
        "max_score": 50,
        "accuracy_pct": 100.0,
        "failing_categories": [],
        "divergence_summary": "All milestones passed 100% verified.",
        "all_passed": True,
    }
    return repo_root, lab_dir, config, eval_result


def test_submit_lab_appends_before_deleting_and_preserves_content_on_append_failure(tmp_path, monkeypatch):
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)
    repo_root, lab_dir, config, eval_result = _sample_lab_setup(tmp_path)

    existing_blocks = [{"id": "old-block-1"}, {"id": "old-block-2"}]
    calls: list[tuple[str, str]] = []

    def fake_notion_request(method, endpoint, token, payload=None, **_):
        calls.append((method, endpoint))
        if method == "POST" and endpoint.startswith("databases/"):
            return {"results": [{"id": "page-123"}]}
        if method == "PATCH" and endpoint == "pages/page-123":
            return {"id": "page-123"}
        if method == "GET" and endpoint.startswith("blocks/page-123/children"):
            return {"results": existing_blocks, "has_more": False}
        if method == "PATCH" and endpoint == "blocks/page-123/children":
            raise RuntimeError("simulated append failure")
        if method == "DELETE":
            raise AssertionError("must not delete old blocks if append failed")
        return {}

    monkeypatch.setattr(submit_lab, "notion_request", fake_notion_request)
    monkeypatch.setattr(notion_client, "notion_request", fake_notion_request)

    with pytest.raises(RuntimeError, match="simulated append failure"):
        submit_lab.sync_to_notion(repo_root, lab_dir, config, eval_result, {"NOTION_TOKEN": "tok-test"})

    assert not any(m == "DELETE" for m, _ in calls)


def test_submit_lab_append_precedes_delete_on_success(tmp_path, monkeypatch):
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)
    repo_root, lab_dir, config, eval_result = _sample_lab_setup(tmp_path)
    calls: list[tuple[str, str]] = []

    def fake_notion_request(method, endpoint, token, payload=None, **_):
        calls.append((method, endpoint))
        if method == "POST" and endpoint.startswith("databases/"):
            return {"results": [{"id": "page-123"}]}
        if method == "GET" and endpoint.startswith("blocks/page-123/children"):
            return {"results": [{"id": "old-1"}], "has_more": False}
        return {"id": "page-123"}

    monkeypatch.setattr(submit_lab, "notion_request", fake_notion_request)
    monkeypatch.setattr(notion_client, "notion_request", fake_notion_request)

    url = submit_lab.sync_to_notion(repo_root, lab_dir, config, eval_result, {"NOTION_TOKEN": "tok-test"})
    assert url == "https://notion.so/page123"
    patch_idx = calls.index(("PATCH", "blocks/page-123/children"))
    delete_idx = calls.index(("DELETE", "blocks/old-1"))
    assert patch_idx < delete_idx


def test_submit_lab_dry_run_skips_notion_calls(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTION_DRY_RUN", "1")
    repo_root, lab_dir, config, eval_result = _sample_lab_setup(tmp_path)

    with mock.patch.object(submit_lab, "notion_request", side_effect=AssertionError("must not call Notion")):
        url = submit_lab.sync_to_notion(repo_root, lab_dir, config, eval_result, {"NOTION_TOKEN": "tok-test"})

    assert url == "https://notion.so/mock-LAB-PRG-TEST-01"


def test_drill_submit_does_not_mark_correct_without_passing_review():
    drill_doc = {
        "drillId": "DRL-PRG-TEST-01",
        "problems": [
            {"id": "Q01", "state": {}},
            {"id": "Q02", "state": {"reviews": [{"attempt": 1, "verdict": "revise"}]}},
        ],
    }
    cases = [
        {"name": "[Q01-T01] works", "file": "Q01_fn.test.ts", "passed": True, "failure_msg": "", "is_hidden": False},
        {"name": "[Q02-T01] works", "file": "Q02_fn.test.ts", "passed": True, "failure_msg": "", "is_hidden": False},
    ]

    res = drill_submit.evaluate_and_record_submission(drill_doc, cases, now_iso="2026-11-16T00:00:00Z")

    assert res["total_tests_passed"] == 2
    assert res["total_reviewed_passed"] == 0
    assert res["all_green"] is False
    assert drill_doc["sessionSummary"]["score"] == 0
    assert drill_doc["sessionSummary"]["practiceStatus"] == "Needs Retry"
    assert drill_doc["problems"][0]["state"]["lastTestReport"]["allPassed"] is True
    assert drill_doc["problems"][0]["state"]["score"] is None

    # Now mark both problems with passing review records -> Graded
    drill_doc["problems"][0]["state"]["reviews"] = [{"attempt": 1, "verdict": "pass"}]
    drill_doc["problems"][1]["state"]["reviews"].append({"attempt": 2, "verdict": "pass"})
    res2 = drill_submit.evaluate_and_record_submission(drill_doc, cases, now_iso="2026-11-16T00:01:00Z")
    assert res2["total_reviewed_passed"] == 2
    assert res2["all_green"] is True
    assert drill_doc["sessionSummary"]["score"] == 1.5
    assert drill_doc["sessionSummary"]["practiceStatus"] == "Graded"


@pytest.mark.parametrize(
    ("review_at", "tests_passed", "hint", "expected_score", "expected_status"),
    [
        ("09:00", False, False, 0, "Needs Retry"),
        ("11:00", False, False, 0, "Needs Retry"),
        ("09:00", True, False, None, "Needs Retry"),
        ("11:00", True, True, 0.5, "Graded"),
    ],
    ids=["failed-after-reset", "failed-after-pass", "awaiting-review-after-reset", "assisted-pass"],
)
def test_drill_submit_uses_current_cycle_score(review_at, tests_passed, hint, expected_score, expected_status):
    state = {
        "cycleStartedAt": "2026-11-24T10:00:00.000Z",
        "reviews": [{"at": f"2026-11-24T{review_at}:00.000Z", "verdict": "pass"}],
        "score": 1,
    }
    if hint:
        state["reviewHintRevealedAt"] = "2026-11-24T10:30:00.000Z"
    doc = {"problems": [{"id": "Q01", "state": state}]}
    cases = [{"name": "[Q01-T01] check", "passed": tests_passed, "failure_msg": "Assertion failed"}]
    run_at = "2026-11-24T12:00:00.000Z"

    result = drill_submit.evaluate_and_record_submission(doc, cases, now_iso=run_at)

    assert doc["sessionSummary"]["practiceStatus"] == result["practice_status"] == expected_status
    assert doc["sessionSummary"]["score"] == (expected_score or 0)
    assert doc["sessionSummary"]["accuracyPct"] == (expected_score or 0) * 100
    assert state["score"] == expected_score
    assert score_problem(state, is_prg=True)["score"] == expected_score
    assert state["lastTestReport"]["ts"] == run_at
    assert state["testRuns"][-1]["ts"] == run_at
    if expected_score is None:
        assert result["evaluated_questions"][0]["review_verdict"] is None
        assert "awaiting" in doc["sessionSummary"]["divergedStepsSummary"].lower()


def test_drill_submit_cli_syncs_failure_after_same_second_review(tmp_path, monkeypatch, capsys):
    drill_id = "DRL-PRG-TEST-01"
    doc = {"drillId": drill_id, "problems": [{"id": "Q01"}]}
    (tmp_path / "id_map.json").write_text("{}", encoding="utf-8")
    data_dir = tmp_path / "drills" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / f"{drill_id}.json").write_text(json.dumps(doc), encoding="utf-8")
    workspace = tmp_path / drill_id
    workspace.mkdir()
    (workspace / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(workspace)
    saved_doc = {
        "drillId": drill_id,
        "problems": [
            {
                "id": "Q01",
                "state": {
                    "reviews": [{"at": "2026-11-24T12:00:00Z", "verdict": "pass", "tests": {"passed": 1, "total": 1}}]
                },
            }
        ],
    }
    save_progress(saved_doc)
    run_at = datetime.datetime(2026, 11, 24, 12, 0, 0, 500000, tzinfo=datetime.timezone.utc)
    monkeypatch.setattr(
        drill_submit,
        "datetime",
        SimpleNamespace(datetime=SimpleNamespace(now=lambda _: run_at), timezone=datetime.timezone),
    )
    monkeypatch.setattr(
        drill_submit,
        "run_tests_junit",
        lambda *_: [{"name": "[Q01-T01] check", "passed": False, "failure_msg": "Assertion failed"}],
    )
    synced = []

    def fake_sync(payload):
        synced.append(payload)
        return {"dryRun": True}

    monkeypatch.setattr(drill_submit, "sync_drill_to_notion", fake_sync)

    with pytest.raises(SystemExit) as exit_info:
        drill_submit.main([])

    assert exit_info.value.code == 1
    assert "NEEDS RETRY" in capsys.readouterr().out
    assert synced[0]["sessionSummary"]["practiceStatus"] == "Needs Retry"
    assert synced[0]["sessionSummary"]["score"] == 0


def test_junit_qid_grouping_handles_brackets_underscores_and_files():
    cases = [
        {"name": "[Q01-T01] basic", "file": "", "passed": True, "is_hidden": False},
        {"name": "[Q02-HIDDEN-T01] trap", "file": "", "passed": True, "is_hidden": True},
        {"name": "[edge case] handles empty array", "file": "Q02_parse.test.ts", "passed": True, "is_hidden": False},
        {"name": "parse_json handles null", "file": "Q03_parseJson.test.ts", "passed": True, "is_hidden": False},
        {"name": "Q04_check: handles undefined", "file": "", "passed": True, "is_hidden": False},
    ]
    grouped = drill_submit.group_cases_by_qid(cases)
    assert sorted(grouped.keys()) == ["Q01", "Q02", "Q03", "Q04"]
    assert len(grouped["Q02"]) == 2
    assert [c["name"] for c in grouped["Q03"]] == ["parse_json handles null"]
