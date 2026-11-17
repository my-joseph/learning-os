"""Hermetic tests for the local spaced-review schedule cache (`_review_schedule.json`)."""

from __future__ import annotations

import json
from pathlib import Path

import progress_store
from notion_sync import drill_sync
from scripts import review_cache


def test_update_unit_reviews_merges_into_schedule_cache_without_touching_drills(tmp_path, monkeypatch):
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.delenv("LEARNINGOS_PILOT", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "id_map.json").write_text("{}", encoding="utf-8")

    # Seed a drill file on disk and ensure it is never modified
    drill_dir = tmp_path / "drills" / "data" / "MTH-T09-C01-U01"
    drill_dir.mkdir(parents=True)
    drill_file = drill_dir / "DRL-MTH-T09-C01-U01-01.json"
    drill_payload = {"drillId": "DRL-MTH-T09-C01-U01-01", "unitCode": "MTH-T09-C01-U01", "problems": []}
    original_drill_text = json.dumps(drill_payload)
    drill_file.write_text(original_drill_text, encoding="utf-8")

    # Pre-existing entry for another unit must be preserved on merge
    progress_dir = tmp_path / "progress"
    progress_dir.mkdir()
    cache_path = progress_dir / "_review_schedule.json"
    cache_path.write_text(
        json.dumps(
            {
                "MTH-T09-C01-U99": {
                    "mastery": 1,
                    "lastReviewed": "2026-11-01",
                    "nextReview": "2026-11-03",
                    "title": "Existing Unit",
                }
            }
        ),
        encoding="utf-8",
    )

    def fake_notion_request(method, endpoint, token, payload=None):
        if method == "GET":
            return {
                "properties": {
                    "Mastery (0-4)": {"number": 1},
                    "Last Reviewed": {"date": None},
                    "Next Review": {"date": None},
                }
            }
        return {}

    monkeypatch.setattr(drill_sync, "notion_request", fake_notion_request)
    import scripts.weak_spots as ws

    monkeypatch.setattr(
        ws,
        "review_update",
        lambda unit, cur, d: {"mastery": 2, "lastReviewed": "2026-11-10", "nextReview": "2026-11-15"},
    )

    id_map = {"MTH-T09-C01-U01": {"id": "page-u1", "title": "Complex Numbers"}}
    out = drill_sync.update_unit_reviews(["MTH-T09-C01-U01"], "2026-11-10", id_map, "tok")
    assert out == {"MTH-T09-C01-U01": {"mastery": 2, "lastReviewed": "2026-11-10", "nextReview": "2026-11-15"}}

    saved = json.loads(cache_path.read_text(encoding="utf-8"))
    assert saved["MTH-T09-C01-U99"]["title"] == "Existing Unit"
    assert saved["MTH-T09-C01-U01"] == {
        "mastery": 2,
        "lastReviewed": "2026-11-10",
        "nextReview": "2026-11-15",
        "title": "Complex Numbers",
    }
    assert drill_file.read_text(encoding="utf-8") == original_drill_text
    # No stray temp files left behind
    assert [p.name for p in progress_dir.iterdir()] == ["_review_schedule.json"]


def test_review_schedule_respects_pilot_mode(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.setenv("LEARNINGOS_PILOT", "1")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "id_map.json").write_text("{}", encoding="utf-8")

    path = progress_store.merge_review_schedule(
        {
            "PRG-T01-C01-U01": {
                "mastery": 3,
                "lastReviewed": "2026-11-12",
                "nextReview": "2026-11-29",
                "title": "Arrays & Iteration",
            }
        }
    )
    assert Path(path) == tmp_path / "pilot" / "progress" / "_review_schedule.json"
    assert Path(path).is_file()
    assert not (tmp_path / "progress").exists()


def test_rebuild_reads_notion_units_without_writes(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.delenv("LEARNINGOS_PILOT", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "id_map.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("NOTION_TOKEN", "fake-token")

    calls: list[tuple[str, str, dict | None]] = []

    def fake_notion_request(method, endpoint, token, payload=None):
        calls.append((method, endpoint, payload))
        if payload and payload.get("start_cursor") == "page2":
            return {
                "has_more": False,
                "results": [
                    {
                        "archived": False,
                        "properties": {
                            "Unit": {"type": "title", "title": [{"plain_text": "Unit Two"}]},
                            "Full ID": {"type": "rich_text", "rich_text": [{"plain_text": "PRG-T01-C01-U02"}]},
                            "Mastery (0-4)": {"number": 3},
                            "Last Reviewed": {"date": {"start": "2026-11-01"}},
                            "Next Review": {"date": {"start": "2026-11-18"}},
                        },
                    },
                    {
                        "archived": False,
                        "properties": {
                            "Unit": {"type": "title", "title": [{"plain_text": "Old Unit"}]},
                            "Full ID": {"type": "rich_text", "rich_text": [{"plain_text": "RETIRED-PRG-01"}]},
                            "Mastery (0-4)": {"number": 2},
                            "Last Reviewed": {"date": {"start": "2026-10-01"}},
                            "Next Review": {"date": {"start": "2026-10-06"}},
                        },
                    },
                ],
            }
        return {
            "has_more": True,
            "next_cursor": "page2",
            "results": [
                {
                    "archived": False,
                    "properties": {
                        "Unit": {"type": "title", "title": [{"plain_text": "Unit One"}]},
                        "Full ID": {"type": "rich_text", "rich_text": [{"plain_text": "MTH-T01-C04-U01"}]},
                        "Mastery (0-4)": {"number": 2},
                        "Last Reviewed": {"date": {"start": "2026-11-10T08:00:00Z"}},
                        "Next Review": {"date": {"start": "2026-11-15"}},
                    },
                },
                {
                    "archived": True,
                    "properties": {
                        "Unit": {"type": "title", "title": [{"plain_text": "Archived"}]},
                        "Full ID": {"type": "rich_text", "rich_text": [{"plain_text": "MTH-T01-C04-U99"}]},
                        "Mastery (0-4)": {"number": 1},
                        "Last Reviewed": {"date": {"start": "2026-11-01"}},
                        "Next Review": {"date": {"start": "2026-11-03"}},
                    },
                },
                {
                    "archived": False,
                    "properties": {
                        "Unit": {"type": "title", "title": [{"plain_text": "Unstarted"}]},
                        "Full ID": {"type": "rich_text", "rich_text": [{"plain_text": "MTH-T01-C04-U02"}]},
                        "Mastery (0-4)": {"number": 0},
                        "Last Reviewed": {"date": None},
                        "Next Review": {"date": None},
                    },
                },
            ],
        }

    monkeypatch.setattr(review_cache, "notion_request", fake_notion_request)

    rc = review_cache.main(["--rebuild"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["units"] == 2

    # Only read queries to /databases/<id>/query — zero PATCH/DELETE/pages writes
    assert len(calls) == 2
    assert all(m == "POST" and ep.endswith("/query") for m, ep, _ in calls)

    cached = json.loads((tmp_path / "progress" / "_review_schedule.json").read_text(encoding="utf-8"))
    assert cached == {
        "MTH-T01-C04-U01": {
            "mastery": 2,
            "lastReviewed": "2026-11-10",
            "nextReview": "2026-11-15",
            "title": "Unit One",
        },
        "PRG-T01-C01-U02": {
            "mastery": 3,
            "lastReviewed": "2026-11-01",
            "nextReview": "2026-11-18",
            "title": "Unit Two",
        },
    }
