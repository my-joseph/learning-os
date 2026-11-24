"""Drill -> Notion sync must never report success for a half-built page, and AI ingests must
carry the hierarchy/level fields the sync needs (gap found when syncing DRL-MTH-T02-C01-U01-03)."""

import json

import pytest

from code_engine import fmt as code_fmt
from math_engine import fmt as math_fmt
from notion_sync import client, drill_sync, unit_page


def _doc(**overrides):
    doc = {
        "drillId": "DRL-MTH-T02-C01-U01-99",
        "unitCode": "MTH-T02-C01-U01",
        "chapterCode": "MTH-T02-C01",
        "topicCode": "MTH-T02",
        "problems": [
            {
                "id": "Q01",
                "levelLabel": "Level 1 - Foundation",
                "category": "Core Skill",
                "prompt": "Evaluate $3i^2 + 10$.",
                "steps": [{"latex": "i^2 = -1", "explain": "Use the definition of i."}],
            }
        ],
    }
    doc.update(overrides)
    return doc


@pytest.fixture
def no_disk(monkeypatch, tmp_path):
    monkeypatch.setenv("DRILLS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)


def test_unit_hierarchy_is_the_same_in_both_engines():
    for code in ("MTH-T02-C01-U01", "PRG-T00-C02", "MTH-SYNTHESIS", "PHY"):
        assert math_fmt.unit_hierarchy(code) == code_fmt.unit_hierarchy(code)
    assert math_fmt.unit_hierarchy("MTH-T02-C01-U01") == ("MTH-T02", "MTH-T02-C01")


def test_missing_fields_listed_before_any_notion_call(no_disk, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("must not reach Notion")

    monkeypatch.setattr(drill_sync, "_sync_drill_to_notion_inner", boom)
    doc = _doc()
    del doc["chapterCode"]
    del doc["problems"][0]["levelLabel"]
    res = drill_sync.sync_drill_to_notion(doc)
    assert res["ok"] is False
    assert "drill.chapterCode" in res["error"] and "Q01.levelLabel" in res["error"]


def test_complete_drill_passes_preflight():
    assert drill_sync.missing_sync_fields(_doc()) == []


def test_partial_sync_retries_only_failed_writes(no_disk, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    doc = _doc(sessionSummary={"attemptDate": "2026-11-24", "score": 1, "maxScore": 1})
    first_unit = doc["unitCode"]
    second_unit = "MTH-T02-C01-U02"
    doc["problems"][0]["unitCode"] = second_unit
    (tmp_path / "id_map.json").write_text(
        json.dumps({"DRILLS_DB": {"id": "db"}, first_unit: {"id": "unit-1"}, second_unit: {"id": "unit-2"}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "fake"})
    monkeypatch.setattr(
        "scripts.weak_spots.review_update",
        lambda *args: {"mastery": 2, "lastReviewed": "2026-11-24", "nextReview": "2026-11-29"},
    )
    calls = []
    old_blocks = [{"id": "old-1"}, {"id": "old-2"}]
    log_blocks = []
    fail_writes = True

    def fake_request(method, endpoint, token, payload=None):
        calls.append((method, endpoint))
        if endpoint == "databases/db/query":
            return {"results": [{"id": "drill-page"}]}
        if method == "GET" and endpoint.startswith("pages/unit-"):
            return {"properties": {"Mastery (0-4)": {"number": 1}, "Last Reviewed": {}, "Next Review": {}}}
        if endpoint.startswith("blocks/drill-page/children"):
            if method == "GET":
                return {"results": old_blocks.copy()}
            old_blocks.extend({"id": f"new-{i}"} for i, _ in enumerate(payload["children"]))
        if method == "DELETE":
            block_id = endpoint.rsplit("/", 1)[-1]
            if fail_writes and block_id == "old-2":
                raise RuntimeError("cleanup failed")
            old_blocks[:] = [block for block in old_blocks if block["id"] != block_id]
        if endpoint == "pages/unit-1" and method == "PATCH" and fail_writes:
            raise RuntimeError("review failed")
        if endpoint.startswith("blocks/unit-1/children"):
            if method == "GET":
                return {"results": log_blocks.copy()}
            log_blocks.extend(payload["children"])
            if fail_writes:
                # The write happened, but the response was lost.
                raise OSError("append response lost")
        return {}

    for module in (client, drill_sync, unit_page):
        monkeypatch.setattr(module, "notion_request", fake_request)
    partial = drill_sync.sync_drill_to_notion(doc, save_local=False)
    failed_steps = ["blockCleanup", f"unitReview:{first_unit}", "mistakeLog"]
    assert partial["partial"] is True
    assert partial["failedSteps"] == failed_steps
    assert list(partial["unitReviews"]) == [second_unit]
    assert len(log_blocks) == 1

    calls.clear()
    fail_writes = False
    done = drill_sync.sync_drill_to_notion(doc, save_local=False, retry=partial["retry"])
    assert done["ok"] and not done.get("partial")
    assert ("DELETE", "blocks/old-2") in calls
    assert ("PATCH", "blocks/drill-page/children") not in calls
    assert ("PATCH", "pages/drill-page") not in calls
    assert ("PATCH", "pages/unit-1") in calls
    assert ("PATCH", "pages/unit-2") not in calls
    assert ("PATCH", "blocks/unit-1/children") not in calls
    assert len(log_blocks) == 1


def test_notion_outage_is_degraded_not_failed(no_disk, monkeypatch):
    def outage(*a, **k):
        raise RuntimeError("HTTP 503 on POST pages")

    monkeypatch.setattr(drill_sync, "_sync_drill_to_notion_inner", outage)
    res = drill_sync.sync_drill_to_notion(_doc())
    assert res["ok"] is True and res["degraded"] is True
    assert "Notion was not updated" in res["warning"]


def test_expired_sync_deadline_returns_degraded(no_disk, monkeypatch):
    monkeypatch.setenv("NOTION_SYNC_DEADLINE_S", "0.001")

    def exhaust_then_request(*args, **kwargs):
        import time

        time.sleep(0.01)
        drill_sync.notion_request("GET", "pages/x", "tok")

    monkeypatch.setattr(drill_sync, "_sync_drill_to_notion_with_deadline", exhaust_then_request)
    res = drill_sync.sync_drill_to_notion(_doc())
    assert res["ok"] is True and res["degraded"] is True
    assert "deadline exceeded" in res["warning"]


def test_mistake_log_dedup_accepts_mention_and_plain_text():
    drill_id = "DRL-MTH-T02-C01-U01-99"
    id_map = {drill_id: {"id": "page-1"}}
    mention_block = {
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "plain_text": "[2026-11-17] "},
                {"type": "mention", "mention": {"type": "page", "page": {"id": "page-1"}}},
            ]
        },
    }
    plain_block = {
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "plain_text": f"[2026-11-17] {drill_id}"}]},
    }
    assert drill_sync._has_mistake_log_entry([mention_block], "2026-11-17", drill_id, id_map)
    assert drill_sync._has_mistake_log_entry([plain_block], "2026-11-17", drill_id, id_map)


def test_bug_during_sync_is_reported_as_failure(no_disk, monkeypatch):
    def bug(*a, **k):
        raise KeyError("levelLabel")

    monkeypatch.setattr(drill_sync, "_sync_drill_to_notion_inner", bug)
    res = drill_sync.sync_drill_to_notion(_doc())
    assert res["ok"] is False and "KeyError" in res["error"]


def test_cli_dry_run_by_path_and_drill_id(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    unit_dir = data_dir / "MTH-T02-C01-U01"
    unit_dir.mkdir(parents=True)
    drill_file = unit_dir / "DRL-MTH-T02-C01-U01-99.json"
    drill_file.write_text(json.dumps(_doc()), encoding="utf-8")

    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_dir))
    monkeypatch.setattr(drill_sync, "save_progress", lambda doc: None)

    def boom(*a, **k):
        raise AssertionError("dry-run must not call Notion")

    monkeypatch.setattr(drill_sync, "_sync_drill_to_notion_inner", boom)

    assert drill_sync.main([str(drill_file), "--dry-run"]) == 0
    out1 = json.loads(capsys.readouterr().out)
    assert out1["ok"] is True and out1["dryRun"] is True

    assert drill_sync.main(["DRL-MTH-T02-C01-U01-99", "--dry-run"]) == 0
    out2 = json.loads(capsys.readouterr().out)
    assert out2["ok"] is True and out2["dryRun"] is True


def test_cli_sync_uses_client_and_returns_nonzero_on_missing(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    unit_dir = data_dir / "MTH-T02-C01-U01"
    unit_dir.mkdir(parents=True)
    drill_file = unit_dir / "DRL-MTH-T02-C01-U01-99.json"
    drill_file.write_text(json.dumps(_doc()), encoding="utf-8")

    (tmp_path / "id_map.json").write_text(
        json.dumps({"DRILLS_DB": {"id": "db-1"}, "MTH-T02-C01-U01": {"id": "u-1"}}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_dir))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)
    monkeypatch.setattr(drill_sync, "save_progress", lambda doc: None)
    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "fake-token"})

    calls = []

    def fake_notion_request(method, path, token, payload=None):
        calls.append((method, path))
        if method == "POST" and path.endswith("/query"):
            return {"results": []}
        if method == "POST" and path == "pages":
            return {"id": "page-123"}
        return {}

    monkeypatch.setattr(drill_sync, "notion_request", fake_notion_request)
    monkeypatch.setattr(drill_sync, "replace_page_blocks", lambda *a, **k: None)

    assert drill_sync.main(["DRL-MTH-T02-C01-U01-99"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True and out["drillPageId"] == "page-123"
    assert ("POST", "pages") in calls

    assert drill_sync.main(["DRL-DOES-NOT-EXIST"]) == 1


def test_cli_sync_preserves_practised_progress_and_id_map_newline(tmp_path, monkeypatch, capsys):
    import progress_store

    data_dir = tmp_path / "data"
    unit_dir = data_dir / "MTH-T02-C01-U01"
    unit_dir.mkdir(parents=True)
    drill_file = unit_dir / "DRL-MTH-T02-C01-U01-99.json"
    drill_file.write_text(json.dumps(_doc()), encoding="utf-8")

    (tmp_path / "id_map.json").write_text(
        json.dumps({"DRILLS_DB": {"id": "db-1"}, "MTH-T02-C01-U01": {"id": "u-1"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_dir))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)

    practised = _doc()
    practised["problems"][0]["state"] = {
        "userInput": "7",
        "score": 1,
        "attempts": [{"input": "7", "verdict": "correct"}],
    }
    practised["sessionSummary"] = {"practiceStatus": "Graded", "score": 1, "maxScore": 1, "attemptDate": "2026-11-17"}
    progress_store.save_progress(practised)

    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "fake-token"})
    monkeypatch.setattr(
        drill_sync,
        "notion_request",
        lambda method, path, token, payload=None: (
            {"results": []} if method == "POST" and path.endswith("/query") else {"id": "page-123"}
        ),
    )
    monkeypatch.setattr(drill_sync, "replace_page_blocks", lambda *a, **k: None)
    monkeypatch.setattr(drill_sync, "update_unit_reviews", lambda *a, **k: {})
    monkeypatch.setattr(drill_sync, "get_all_blocks", lambda *a, **k: [])
    monkeypatch.setattr(unit_page, "notion_request", lambda *a, **k: {"results": []})

    assert drill_sync.main(["DRL-MTH-T02-C01-U01-99"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True

    reloaded = progress_store.load_progress("DRL-MTH-T02-C01-U01-99")
    assert reloaded is not None
    assert reloaded["sessionSummary"]["attemptDate"] == "2026-11-17"
    assert reloaded["sessionSummary"]["score"] == 1
    assert reloaded["problems"]["Q01"]["userInput"] == "7"

    id_map_raw = (tmp_path / "id_map.json").read_text(encoding="utf-8")
    assert id_map_raw.endswith("\n") and not id_map_raw.endswith("\n\n")
    assert id_map_raw == json.dumps(json.loads(id_map_raw), ensure_ascii=False, indent=2) + "\n"


def test_cli_content_only_skips_progress_and_unit_writes(tmp_path, monkeypatch, capsys):
    import progress_store
    from notion_sync import unit_page

    data_dir = tmp_path / "data"
    unit_dir = data_dir / "MTH-T02-C01-U01"
    unit_dir.mkdir(parents=True)
    drill_file = unit_dir / "DRL-MTH-T02-C01-U01-99.json"
    drill_file.write_text(json.dumps(_doc()), encoding="utf-8")

    (tmp_path / "id_map.json").write_text(
        json.dumps({"DRILLS_DB": {"id": "db-1"}, "MTH-T02-C01-U01": {"id": "u-1"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_dir))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)

    practised = _doc()
    practised["problems"][0]["state"] = {"userInput": "7", "score": 1}
    practised["sessionSummary"] = {
        "practiceStatus": "Graded",
        "score": 1,
        "maxScore": 1,
        "accuracyPct": 100,
        "attemptDate": "2026-11-17",
    }
    prog_file_path = progress_store.save_progress(practised)
    prog_before = open(prog_file_path, encoding="utf-8").read()

    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "fake-token"})

    notion_calls = []

    def fake_notion_request(method, path, token, payload=None):
        notion_calls.append((method, path, payload))
        if method == "POST" and path.endswith("/query"):
            return {"results": [{"id": "page-existing"}]}
        return {"id": "page-existing"}

    replaced = []
    monkeypatch.setattr(drill_sync, "notion_request", fake_notion_request)
    monkeypatch.setattr(drill_sync, "replace_page_blocks", lambda pid, blocks, did, tok: replaced.append((pid, blocks)))

    def fail(*a, **k):
        raise AssertionError("must not be called in --content-only mode")

    monkeypatch.setattr(drill_sync, "save_progress", fail)
    monkeypatch.setattr(drill_sync, "update_unit_reviews", fail)
    monkeypatch.setattr(drill_sync, "merge_review_schedule", fail)
    monkeypatch.setattr(drill_sync, "get_all_blocks", fail)
    monkeypatch.setattr(unit_page, "insert_after", fail)

    assert drill_sync.main(["DRL-MTH-T02-C01-U01-99", "--content-only"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True and out["drillPageId"] == "page-existing"
    assert out["unitReviews"] == {}

    # Drill page updated with merged progress and question blocks
    patch_calls = [c for c in notion_calls if c[0] == "PATCH" and c[1] == "pages/page-existing"]
    assert len(patch_calls) == 1
    props = patch_calls[0][2]["properties"]
    assert props["Score"]["number"] == 1.0
    assert props["Practice Status"]["select"]["name"] == "Graded"
    assert len(replaced) == 1

    # Local progress and review cache untouched
    assert open(prog_file_path, encoding="utf-8").read() == prog_before
    assert not (tmp_path / "progress" / "_review_schedule.json").exists()
    id_map_raw = (tmp_path / "id_map.json").read_text(encoding="utf-8")
    assert id_map_raw.endswith("\n") and not id_map_raw.endswith("\n\n")


def test_cli_content_only_creates_no_progress_file_for_pristine_drill(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    unit_dir = data_dir / "MTH-T02-C01-U01"
    unit_dir.mkdir(parents=True)
    (unit_dir / "DRL-MTH-T02-C01-U01-99.json").write_text(json.dumps(_doc()), encoding="utf-8")
    (tmp_path / "id_map.json").write_text(
        json.dumps({"DRILLS_DB": {"id": "db-1"}, "MTH-T02-C01-U01": {"id": "u-1"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_dir))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)
    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "fake-token"})
    monkeypatch.setattr(
        drill_sync,
        "notion_request",
        lambda method, path, token, payload=None: (
            {"results": []} if method == "POST" and path.endswith("/query") else {"id": "page-123"}
        ),
    )
    monkeypatch.setattr(drill_sync, "replace_page_blocks", lambda *a, **k: None)

    assert drill_sync.main(["DRL-MTH-T02-C01-U01-99", "--content-only"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert not (tmp_path / "progress").exists()


def test_sync_drill_to_notion_never_loses_variant_id_or_concurrent_review(tmp_path, monkeypatch):
    """Syncing a redacted client doc directly through drill_sync must never wipe variantId,
    variantsSeen/Attempted, variant matchedTrap, or concurrent reviews/attempts."""
    import progress_store

    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    monkeypatch.setenv("DRILLS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)

    disk_doc = _doc()
    disk_doc["problems"][0]["state"] = {
        "userInput": "7",
        "score": 0.5,
        "attempts": [
            {"input": "13", "ts": "2026-11-20T09:00:00Z", "verdict": "incorrect", "matchedTrap": "i2-plus-1"},
            {"input": "7", "ts": "2026-11-20T09:02:00Z", "verdict": "correct"},
            {"input": "7", "ts": "2026-11-20T12:00:00Z", "verdict": "correct"},
        ],
        "reviews": [
            {
                "at": "2026-11-20T11:00:00Z",
                "attempt": 1,
                "verdict": "pass",
                "explain": "Concurrent disk review",
                "findings": [],
            }
        ],
        "variants": {
            "vabc123": {
                "variantId": "VAR-MTH-T02-C01-U01-powers-01",
                "role": "try",
                "attempts": [
                    {
                        "input": "11",
                        "ts": "2026-11-20T09:05:00Z",
                        "verdict": "incorrect",
                        "matchedTrap": "i2-plus-1",
                        "kind": "variant",
                    }
                ],
                "servedAt": "2026-11-20T09:04:00Z",
            }
        },
        "similarSlots": ["vabc123"],
        "variantsSeen": ["VAR-MTH-T02-C01-U01-powers-01"],
        "variantsAttempted": ["VAR-MTH-T02-C01-U01-powers-01"],
        "exampleViewedAt": "2026-11-20T09:03:00Z",
    }
    disk_doc["sessionSummary"] = {"practiceStatus": "In Progress", "score": 0.5, "maxScore": 1}
    progress_store.save_progress(disk_doc)

    # Redacted client doc (as produced by Studio redactProblemStateForClient) synced with dryRun=True
    redacted_sync = _doc()
    redacted_sync["dryRun"] = True
    redacted_sync["sessionSummary"] = {
        "practiceStatus": "Graded",
        "score": 0.5,
        "maxScore": 1,
        "attemptDate": "2026-11-20",
    }
    redacted_sync["problems"][0]["state"] = {
        "userInput": "7",
        "score": 0.5,
        "mistakeNote": "Remember i^2 = -1",
        "attempts": [
            {"input": "13", "ts": "2026-11-20T09:00:00Z", "verdict": "incorrect"},
            {"input": "7", "ts": "2026-11-20T09:02:00Z", "verdict": "correct"},
        ],
        "reviews": [],
        "variants": {
            "vabc123": {
                "role": "try",
                "attempts": [{"input": "11", "ts": "2026-11-20T09:05:00Z", "verdict": "incorrect", "kind": "variant"}],
                "servedAt": "2026-11-20T09:04:00Z",
            }
        },
        "similarSlots": ["vabc123"],
    }

    res = drill_sync.sync_drill_to_notion(redacted_sync)
    assert res["ok"] is True and res["dryRun"] is True

    after = progress_store.load_progress("DRL-MTH-T02-C01-U01-99")
    assert after is not None
    q1 = after["problems"]["Q01"]
    assert q1["variants"]["vabc123"]["variantId"] == "VAR-MTH-T02-C01-U01-powers-01"
    assert q1["variants"]["vabc123"]["attempts"][0]["matchedTrap"] == "i2-plus-1"
    assert q1["variantsSeen"] == ["VAR-MTH-T02-C01-U01-powers-01"]
    assert q1["variantsAttempted"] == ["VAR-MTH-T02-C01-U01-powers-01"]
    assert q1["exampleViewedAt"] == "2026-11-20T09:03:00Z"
    assert len(q1["reviews"]) == 1 and q1["reviews"][0]["explain"] == "Concurrent disk review"
    assert len(q1["attempts"]) == 3
    assert q1["mistakeNote"] == "Remember i^2 = -1"
    assert after["sessionSummary"]["practiceStatus"] == "Graded"


def test_sync_drill_to_notion_save_local_false_skips_second_save(tmp_path, monkeypatch):
    """When Studio already merged progress via TS writeProgress, save_local=False skips
    Python save_drill_doc while still running validation and Notion sync."""
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    monkeypatch.setenv("DRILLS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)

    def fail_save(*a, **k):
        raise AssertionError("save_drill_doc must not run when save_local=False")

    monkeypatch.setattr(drill_sync, "save_drill_doc", fail_save)
    doc = _doc()
    doc["dryRun"] = True
    res = drill_sync.sync_drill_to_notion(doc, save_local=False)
    assert res["ok"] is True and res["dryRun"] is True
