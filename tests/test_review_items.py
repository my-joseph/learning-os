"""Tests for per-item spaced-review scheduling (`scripts/review_items.py`)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from scripts import review_items as ri


def test_step_schedule_levels_and_intervals():
    # Intervals: L1=1d, L2=3d, L3=7d, L4=16d, L5=35d
    assert ri.REVIEW_INTERVALS == {1: 1, 2: 3, 3: 7, 4: 16, 5: 35}

    # Correct without hint -> +1 level (capped at 5)
    s1 = ri.step_schedule(1, correct=True, assisted=False, review_date="2026-11-01")
    assert s1 == {"level": 2, "lastReviewed": "2026-11-01", "dueDate": "2026-11-04"}

    s2 = ri.step_schedule(2, correct=True, assisted=False, review_date="2026-11-04")
    assert s2 == {"level": 3, "lastReviewed": "2026-11-04", "dueDate": "2026-11-11"}

    s3 = ri.step_schedule(3, correct=True, assisted=False, review_date="2026-11-11")
    assert s3 == {"level": 4, "lastReviewed": "2026-11-11", "dueDate": "2026-11-27"}

    s4 = ri.step_schedule(4, correct=True, assisted=False, review_date="2026-11-27")
    assert s4 == {"level": 5, "lastReviewed": "2026-11-27", "dueDate": "2027-01-01"}

    s5 = ri.step_schedule(5, correct=True, assisted=False, review_date="2027-01-01")
    assert s5 == {"level": 5, "lastReviewed": "2027-01-01", "dueDate": "2027-02-05"}

    # Correct with hint / assisted -> stays at same level
    for lv, days in ri.REVIEW_INTERVALS.items():
        same = ri.step_schedule(lv, correct=True, assisted=True, review_date="2026-11-10")
        assert same["level"] == lv
        assert same["dueDate"] == ri.add_days("2026-11-10", days)

    # Wrong -> level halved (floor, min 1) and due next day (+1d)
    for lv, expected_halved in [(1, 1), (2, 1), (3, 1), (4, 2), (5, 2)]:
        wrong = ri.step_schedule(lv, correct=False, assisted=False, review_date="2026-11-10")
        assert wrong == {
            "level": expected_halved,
            "lastReviewed": "2026-11-10",
            "dueDate": "2026-11-11",
        }


def test_attempt_dates_use_machine_local_day_and_undated_events_are_due(monkeypatch):
    prior_tz = os.environ.get("TZ")
    monkeypatch.setenv("TZ", "Asia/Bangkok")
    time.tzset()
    try:
        assert ri._normalize_date("2026-11-18T17:00:00Z") == "2026-11-19"  # midnight local
        assert ri._normalize_date("2026-11-18T23:59:00Z") == "2026-11-19"  # 06:59 local
        assert ri._normalize_date("2026-11-18T16:59:00Z") == "2026-11-18"  # 23:59 previous local day
        events = ri.extract_review_events({"attempts": [{"verdict": "correct"}]}, "2026-11-20T12:00:00Z")
        assert events[0]["date"] == "1970-01-01"
        assert ri.replay_events(events)["dueDate"] < "2026-11-19"
    finally:
        if prior_tz is None:
            monkeypatch.delenv("TZ", raising=False)
        else:
            monkeypatch.setenv("TZ", prior_tz)
        time.tzset()


def _seed_fixture(tmp_path: Path) -> tuple[str, str]:
    data_root = tmp_path / "drills" / "data"
    progress_dir = tmp_path / "progress"
    mth_u1 = data_root / "MTH-T01-C04-U01"
    mth_u2 = data_root / "MTH-T01-C04-U02"
    prg_u1 = data_root / "PRG-T01-C01-U01"
    mth_u1.mkdir(parents=True)
    mth_u2.mkdir(parents=True)
    prg_u1.mkdir(parents=True)
    progress_dir.mkdir(parents=True)

    # MTH unit 1 drill with 3 problems
    (mth_u1 / "DRL-MTH-T01-C04-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T01-C04-U01-01",
                "unitCode": "MTH-T01-C04-U01",
                "problems": [
                    {
                        "id": "Q01",
                        "level": 2,
                        "commonTrapTag": "c04-divide-not-invert-trap",
                        "archetypeKey": "fraction-division",
                        "answerDisplay": "SECRET_ANSWER_1",
                        "steps": [{"latex": "x=1", "explain": "SECRET_STEP"}],
                    },
                    {
                        "id": "Q02",
                        "level": 3,
                        "commonTrapTag": "c04-sign-drop-trap",
                        "archetypeKey": "signed-fractions",
                    },
                    {
                        "id": "Q03",
                        "level": 4,
                        "commonTrapTag": "c04-reciprocal-flip-trap",
                        "archetypeKey": "complex-fraction",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    # MTH unit 2 drill
    (mth_u2 / "DRL-MTH-T01-C04-U02-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T01-C04-U02-01",
                "unitCode": "MTH-T01-C04-U02",
                "problems": [
                    {
                        "id": "Q01",
                        "level": 2,
                        "commonTrapTag": "c04-lcd-mismatch-trap",
                        "archetypeKey": "unlike-denominators",
                    },
                    {
                        "id": "Q02",
                        "level": 2,
                        "commonTrapTag": "c04-cancel-term-trap",
                        "archetypeKey": "term-cancellation",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    # PRG unit 1 drill
    (prg_u1 / "DRL-PRG-T01-C01-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-PRG-T01-C01-U01-01",
                "subject": "PRG",
                "unitCode": "PRG-T01-C01-U01",
                "problems": [
                    {
                        "id": "Q01",
                        "level": 2,
                        "archetypeKey": "array-guard",
                        "solutionCode": "SECRET_SOLUTION_CODE",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    # Progress for MTH unit 1:
    # - Q01: 3 unassisted correct attempts across days, then wrong -> L1->L2->L3->L4, halved to L2, due next day (2026-11-18)
    # - Q02: correct with hintsRevealed=1 on 2026-11-17 -> stays at L1, due 2026-11-18, carries revisitNote
    # - Q03: clean correct without hints on 2026-11-18 -> L2, due 2026-11-21 (not due on 2026-11-19)
    (progress_dir / "DRL-MTH-T01-C04-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T01-C04-U01-01",
                "updatedAt": "2026-11-18T10:00:00Z",
                "problems": {
                    "Q01": {
                        "attempts": [
                            {"verdict": "correct", "ts": "2026-10-20T10:00:00Z"},
                            {"verdict": "correct", "ts": "2026-10-23T10:00:00Z"},
                            {"verdict": "correct", "ts": "2026-10-30T10:00:00Z"},
                            {"verdict": "incorrect", "ts": "2026-11-17T10:00:00Z"},
                        ],
                        "score": 0,
                        "hintsRevealed": 0,
                        "revisitNote": "Flip the divisor before cancelling common factors.",
                    },
                    "Q02": {
                        "attempts": [
                            {"verdict": "correct", "ts": "2026-11-17T12:00:00Z"},
                        ],
                        "score": 0.5,
                        "hintsRevealed": 1,
                        "revisitNote": "Keep negative sign attached to numerator.",
                    },
                    "Q03": {
                        "attempts": [
                            {"verdict": "correct", "ts": "2026-11-18T12:00:00Z"},
                        ],
                        "score": 1.0,
                        "hintsRevealed": 0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    # Progress for MTH unit 2:
    # - Q01: skipped on 2026-11-17 (no attempts array) -> L1, due 2026-11-18
    # - Q02: lastCheck correct with setupRevealedBeforeAnswer=True on 2026-11-17 -> L1, due 2026-11-18
    (progress_dir / "DRL-MTH-T01-C04-U02-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T01-C04-U02-01",
                "updatedAt": "2026-11-17T15:00:00Z",
                "problems": {
                    "Q01": {
                        "skipped": True,
                        "score": 0,
                    },
                    "Q02": {
                        "lastCheck": {"verdict": "correct"},
                        "setupRevealedBeforeAnswer": True,
                        "score": 0.5,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    # Progress for PRG unit 1:
    # - Q01: review revise on 2026-11-18 -> L1, due 2026-11-19
    (progress_dir / "DRL-PRG-T01-C01-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-PRG-T01-C01-U01-01",
                "updatedAt": "2026-11-18T09:00:00Z",
                "problems": {
                    "Q01": {
                        "reviews": [
                            {
                                "at": "2026-11-18T09:00:00Z",
                                "verdict": "revise",
                                "findings": [{"check": "U-edge-empty", "severity": "must", "line": 3, "note": "guard"}],
                                "lint": [],
                            }
                        ],
                        "revisitNote": "Check for empty array before indexing.",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    return str(data_root), str(progress_dir)


def test_backfill_from_attempts_and_revisit_note(tmp_path: Path):
    data_root, progress_dir = _seed_fixture(tmp_path)
    schedule = ri.build_schedule_from_progress(data_root=data_root, progress_dir=progress_dir)

    assert len(schedule) == 6
    q1 = schedule["DRL-MTH-T01-C04-U01-01/Q01"]
    assert q1["level"] == 2
    assert q1["lastReviewed"] == "2026-11-17"
    assert q1["dueDate"] == "2026-11-18"
    assert q1["commonTrapTag"] == "c04-divide-not-invert-trap"
    assert q1["archetypeKey"] == "fraction-division"
    assert q1["revisitNote"] == "Flip the divisor before cancelling common factors."
    assert "answerDisplay" not in q1 and "steps" not in q1

    q2 = schedule["DRL-MTH-T01-C04-U01-01/Q02"]
    assert q2["level"] == 1
    assert q2["dueDate"] == "2026-11-18"
    assert q2["revisitNote"] == "Keep negative sign attached to numerator."

    q3 = schedule["DRL-MTH-T01-C04-U01-01/Q03"]
    assert q3["level"] == 2
    assert q3["dueDate"] == "2026-11-21"
    assert q3["revisitNote"] is None

    u2_q1 = schedule["DRL-MTH-T01-C04-U02-01/Q01"]
    assert u2_q1["level"] == 1 and u2_q1["dueDate"] == "1970-01-02"

    u2_q2 = schedule["DRL-MTH-T01-C04-U02-01/Q02"]
    assert u2_q2["level"] == 1 and u2_q2["dueDate"] == "1970-01-02"

    prg_q1 = schedule["DRL-PRG-T01-C01-U01-01/Q01"]
    assert prg_q1["subject"] == "PRG"
    assert prg_q1["level"] == 1
    assert prg_q1["dueDate"] == "2026-11-19"
    assert prg_q1["commonTrapTag"] == "U-edge-empty"
    assert prg_q1["revisitNote"] == "Check for empty array before indexing."


def test_interleaving_avoids_consecutive_same_unit_and_mixes_subjects(tmp_path: Path):
    data_root, progress_dir = _seed_fixture(tmp_path)
    due = ri.get_due_items(
        today="2026-11-19",
        data_root=data_root,
        progress_dir=progress_dir,
    )
    # 5 items due on or before 2026-11-19 (2 from U01, 2 from U02, 1 from PRG)
    assert len(due) == 5
    for idx in range(len(due) - 1):
        assert due[idx]["unitCode"] != due[idx + 1]["unitCode"], (
            f"Consecutive items at {idx} and {idx + 1} share unit {due[idx]['unitCode']}"
        )
    subjects = {it["subject"] for it in due}
    assert subjects == {"MTH", "PRG"}

    limited = ri.get_due_items(
        today="2026-11-19",
        limit=3,
        data_root=data_root,
        progress_dir=progress_dir,
    )
    assert len(limited) == 3
    for idx in range(len(limited) - 1):
        assert limited[idx]["unitCode"] != limited[idx + 1]["unitCode"]

    # Dominant unit test: 3 items in U-A, 1 in U-B, 1 in U-C -> must interleave as A, X, A, Y, A
    synthetic = [
        {
            "drillId": "D1",
            "qid": "Q1",
            "unitCode": "MTH-U1",
            "subject": "MTH",
            "level": 1,
            "lastReviewed": "2026-11-10",
            "dueDate": "2026-11-15",
        },
        {
            "drillId": "D1",
            "qid": "Q2",
            "unitCode": "MTH-U1",
            "subject": "MTH",
            "level": 1,
            "lastReviewed": "2026-11-10",
            "dueDate": "2026-11-15",
        },
        {
            "drillId": "D1",
            "qid": "Q3",
            "unitCode": "MTH-U1",
            "subject": "MTH",
            "level": 1,
            "lastReviewed": "2026-11-10",
            "dueDate": "2026-11-15",
        },
        {
            "drillId": "D2",
            "qid": "Q1",
            "unitCode": "MTH-U2",
            "subject": "MTH",
            "level": 1,
            "lastReviewed": "2026-11-10",
            "dueDate": "2026-11-11",
        },
        {
            "drillId": "D3",
            "qid": "Q1",
            "unitCode": "PRG-U1",
            "subject": "PRG",
            "level": 1,
            "lastReviewed": "2026-11-10",
            "dueDate": "2026-11-11",
        },
    ]
    interleaved = ri.interleave_due_items(synthetic)
    assert [it["unitCode"] for it in interleaved] == ["MTH-U1", "PRG-U1", "MTH-U1", "MTH-U2", "MTH-U1"]


def test_cli_is_read_only_unless_rebuild_and_respects_pilot_mode(tmp_path: Path, monkeypatch, capsys):
    data_root, progress_dir = _seed_fixture(tmp_path)
    store_file = Path(progress_dir) / "review_items.json"
    assert not store_file.exists()

    # Running without --rebuild must not write review_items.json
    rc = ri.main(
        [
            "--due",
            "--limit",
            "4",
            "--today",
            "2026-11-19",
            "--data-root",
            data_root,
            "--progress-dir",
            progress_dir,
            "--json",
        ]
    )
    assert rc == 0
    assert not store_file.exists(), "CLI without --rebuild must be strictly read-only"
    due_payload = json.loads(capsys.readouterr().out)
    assert due_payload["today"] == "2026-11-19"
    assert due_payload["count"] == 4
    assert len(due_payload["items"]) == 4

    # Running with --rebuild writes review_items.json
    rc_rebuild = ri.main(
        ["--rebuild", "--today", "2026-11-19", "--data-root", data_root, "--progress-dir", progress_dir, "--json"]
    )
    assert rc_rebuild == 0
    assert store_file.is_file()
    rebuild_payload = json.loads(capsys.readouterr().out)
    assert rebuild_payload["count"] == 6
    saved = json.loads(store_file.read_text(encoding="utf-8"))
    assert "DRL-MTH-T01-C04-U01-01/Q01" in saved

    # Rebuild recalculates old evidence while preserving review-only results.
    saved_review = dict(saved["DRL-MTH-T01-C04-U01-01/Q01"], level=5, lastReviewed="2026-11-19", dueDate="2026-12-24")
    saved["DRL-MTH-T01-C04-U01-01/Q01"] = saved_review
    store_file.write_text(json.dumps(saved), encoding="utf-8")
    ri.main(["--rebuild", "--today", "2026-11-19", "--data-root", data_root, "--progress-dir", progress_dir, "--json"])
    capsys.readouterr()
    assert json.loads(store_file.read_text(encoding="utf-8"))["DRL-MTH-T01-C04-U01-01/Q01"]["level"] == 5

    # Pilot mode writes to pilot/progress/review_items.json and never touches progress/
    pilot_workspace = tmp_path / "pilot_repo"
    pilot_workspace.mkdir()
    (pilot_workspace / "id_map.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(pilot_workspace)
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.setenv("LEARNINGOS_PILOT", "1")

    ri.record_review_result(
        "DRL-MTH-T01-C04-U01-01",
        "Q01",
        correct=True,
        hints_used=False,
        review_date="2026-11-19",
        data_root=data_root,
        repo_root=str(pilot_workspace),
    )
    pilot_store = pilot_workspace / "pilot" / "progress" / "review_items.json"
    assert pilot_store.is_file()
    assert not (pilot_workspace / "progress").exists()
    pilot_data = json.loads(pilot_store.read_text(encoding="utf-8"))
    assert pilot_data["DRL-MTH-T01-C04-U01-01/Q01"]["level"] == 2
    assert pilot_data["DRL-MTH-T01-C04-U01-01/Q01"]["dueDate"] == "2026-11-22"


def test_newer_drill_attempt_wins_over_older_saved_review(tmp_path: Path):
    data_root, progress_dir = _seed_fixture(tmp_path)
    backfilled = ri.build_schedule_from_progress(data_root=data_root, progress_dir=progress_dir)
    key = "DRL-MTH-T01-C04-U01-01/Q01"
    newer = backfilled[key]["lastReviewed"]  # "2026-11-17"

    stale = dict(backfilled[key], level=5, lastReviewed="2026-11-01", dueDate="2026-12-06")
    ri.write_review_items({key: stale}, progress_dir=progress_dir)
    merged = ri.get_review_items_schedule(data_root=data_root, progress_dir=progress_dir)
    assert merged[key]["lastReviewed"] == newer
    assert merged[key]["level"] == backfilled[key]["level"]

    fresh = dict(backfilled[key], level=4, lastReviewed="2026-11-18", dueDate="2026-12-04")
    ri.write_review_items({key: fresh}, progress_dir=progress_dir)
    merged = ri.get_review_items_schedule(data_root=data_root, progress_dir=progress_dir)
    assert merged[key]["level"] == 4 and merged[key]["lastReviewed"] == "2026-11-18"


def test_saved_items_survive_reset_but_deleted_problems_are_ignored(tmp_path: Path):
    data_root, progress_dir = _seed_fixture(tmp_path)
    key = "DRL-MTH-T01-C04-U01-01/Q01"
    saved = ri.build_schedule_from_progress(data_root=data_root, progress_dir=progress_dir)
    ri.write_review_items(saved, progress_dir=progress_dir)
    progress_file = Path(progress_dir) / "DRL-MTH-T01-C04-U01-01.json"
    progress = json.loads(progress_file.read_text(encoding="utf-8"))
    progress["problems"]["Q01"]["cycleStartedAt"] = "2026-11-20T00:00:00Z"
    progress_file.write_text(json.dumps(progress), encoding="utf-8")
    active = ri.get_review_items_schedule(data_root=data_root, progress_dir=progress_dir)
    assert active[key] == saved[key]

    drill_file = Path(data_root) / "MTH-T01-C04-U01" / "DRL-MTH-T01-C04-U01-01.json"
    drill = json.loads(drill_file.read_text(encoding="utf-8"))
    drill["problems"] = [problem for problem in drill["problems"] if problem["id"] != "Q01"]
    drill_file.write_text(json.dumps(drill), encoding="utf-8")
    assert key not in ri.get_review_items_schedule(data_root=data_root, progress_dir=progress_dir)


def test_new_review_record_resolves_unit_for_unattempted_problem(tmp_path: Path):
    data_root, progress_dir = _seed_fixture(tmp_path)
    progress_file = Path(progress_dir) / "DRL-MTH-T01-C04-U01-01.json"
    progress = json.loads(progress_file.read_text(encoding="utf-8"))
    del progress["problems"]["Q03"]
    progress_file.write_text(json.dumps(progress), encoding="utf-8")
    item = ri.record_review_result(
        "DRL-MTH-T01-C04-U01-01",
        "Q03",
        correct=True,
        review_date="2026-11-19",
        data_root=data_root,
        progress_dir=progress_dir,
    )
    assert item["unitCode"] == "MTH-T01-C04-U01"


def _seed_priority_and_scope_fixture(tmp_path: Path) -> tuple[str, str]:
    """Fixture exercising priority tiers (wrong-last > open-weak-spot > most-overdue), pick-then-interleave, scopes, and durationMs."""
    data_root = tmp_path / "drills" / "data"
    progress_dir = tmp_path / "progress"
    for sub in ("MTH-T01-C04-U01", "MTH-T01-C04-U02", "MTH-T02-C01-U01", "PRG-T01-C01-U01"):
        (data_root / sub).mkdir(parents=True)
    progress_dir.mkdir(parents=True)

    # Drill 1 (MTH-T01-C04-U01):
    # - Q01: matched open weak trap twice in prior drill -> this item is correct (assisted), NOT wrong last, due 2026-11-18 (tier B)
    # - Q02: clean old overdue item (not wrong last, not open weak), due 2026-11-05 (tier C, very overdue)
    (data_root / "MTH-T01-C04-U01" / "DRL-MTH-T01-C04-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T01-C04-U01-01",
                "unitCode": "MTH-T01-C04-U01",
                "unitTitle": "Fraction Division",
                "problems": [
                    {"id": "Q01", "level": 2, "commonTrapTag": "c04-open-weak-trap", "archetypeKey": "a1"},
                    {"id": "Q02", "level": 2, "commonTrapTag": "c04-closed-trap", "archetypeKey": "a2"},
                ],
            }
        ),
        encoding="utf-8",
    )

    # Drill 2 (MTH-T01-C04-U02):
    # - Q01: wrong on last attempt, due 2026-11-19 (tier A, less overdue than Q02 above!)
    # - Q02: triggers 2nd match on c04-open-weak-trap (and was later retried correct same day -> not lastWrong, but makes trap open!)
    (data_root / "MTH-T01-C04-U02" / "DRL-MTH-T01-C04-U02-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T01-C04-U02-01",
                "unitCode": "MTH-T01-C04-U02",
                "unitTitle": "Signed Fractions",
                "problems": [
                    {"id": "Q01", "level": 2, "commonTrapTag": "c04-other-trap", "archetypeKey": "b1"},
                    {"id": "Q02", "level": 2, "commonTrapTag": "c04-open-weak-trap", "archetypeKey": "b2"},
                ],
            }
        ),
        encoding="utf-8",
    )

    # Drill 3 (MTH-T02-C01-U01, different chapter):
    # - Q01: normal overdue item due 2026-11-10 (tier C)
    (data_root / "MTH-T02-C01-U01" / "DRL-MTH-T02-C01-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T02-C01-U01-01",
                "unitCode": "MTH-T02-C01-U01",
                "unitTitle": "Complex Numbers",
                "problems": [
                    {"id": "Q01", "level": 2, "commonTrapTag": "t02-sign-trap", "archetypeKey": "c1"},
                ],
            }
        ),
        encoding="utf-8",
    )

    # Drill 4 (PRG-T01-C01-U01):
    # - Q01: revise finding U-edge-empty (hit 1) + wrong last (tier A)
    # - Q02: revise finding U-edge-empty (hit 2 -> makes U-edge-empty an open PRG weak spot!), then pass -> not lastWrong, tier B!
    (data_root / "PRG-T01-C01-U01" / "DRL-PRG-T01-C01-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-PRG-T01-C01-U01-01",
                "subject": "PRG",
                "unitCode": "PRG-T01-C01-U01",
                "unitTitle": "Array Guards",
                "problems": [
                    {"id": "Q01", "level": 2, "archetypeKey": "p1"},
                    {"id": "Q02", "level": 2, "archetypeKey": "p2"},
                ],
            }
        ),
        encoding="utf-8",
    )

    (progress_dir / "DRL-MTH-T01-C04-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T01-C04-U01-01",
                "updatedAt": "2026-11-17T10:00:00Z",
                "problems": {
                    "Q01": {
                        "attempts": [
                            {
                                "verdict": "incorrect",
                                "ts": "2026-11-10T10:00:00Z",
                                "matchedTrap": "c04-open-weak-trap",
                                "durationMs": 120000,
                            },
                            {
                                "verdict": "correct",
                                "ts": "2026-11-17T10:00:00Z",
                                "assisted": True,
                                "durationMs": 60000,
                            },
                        ],
                        "score": 0.5,
                        "hintsRevealed": 1,
                    },
                    "Q02": {
                        "attempts": [
                            {"verdict": "correct", "ts": "2026-11-02T10:00:00Z", "durationMs": 180000},
                        ],
                        "score": 1.0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    (progress_dir / "DRL-MTH-T01-C04-U02-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T01-C04-U02-01",
                "updatedAt": "2026-11-18T10:00:00Z",
                "problems": {
                    "Q01": {
                        "attempts": [
                            {"verdict": "incorrect", "ts": "2026-11-18T10:00:00Z", "durationMs": 120000},
                        ],
                        "score": 0,
                    },
                    "Q02": {
                        "attempts": [
                            {
                                "verdict": "incorrect",
                                "ts": "2026-11-15T10:00:00Z",
                                "matchedTrap": "c04-open-weak-trap",
                                "durationMs": 120000,
                            },
                            {
                                "verdict": "correct",
                                "ts": "2026-11-15T10:05:00Z",
                                "durationMs": 60000,
                            },
                        ],
                        "score": 0.5,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    (progress_dir / "DRL-MTH-T02-C01-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T02-C01-U01-01",
                "updatedAt": "2026-11-07T10:00:00Z",
                "problems": {
                    "Q01": {
                        "attempts": [
                            {"verdict": "correct", "ts": "2026-11-07T10:00:00Z", "durationMs": 120000},
                        ],
                        "score": 1.0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    (progress_dir / "DRL-PRG-T01-C01-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-PRG-T01-C01-U01-01",
                "updatedAt": "2026-11-18T09:00:00Z",
                "problems": {
                    "Q01": {
                        "reviews": [
                            {
                                "at": "2026-11-18T09:00:00Z",
                                "verdict": "revise",
                                "findings": [{"check": "U-edge-empty", "severity": "must", "line": 2, "note": "guard"}],
                                "lint": [],
                            }
                        ],
                        "durationMs": 240000,
                    },
                    "Q02": {
                        "reviews": [
                            {
                                "at": "2026-11-14T09:00:00Z",
                                "verdict": "revise",
                                "findings": [{"check": "U-edge-empty", "severity": "must", "line": 4, "note": "guard"}],
                                "lint": [],
                            },
                            {
                                "at": "2026-11-16T09:00:00Z",
                                "verdict": "pass",
                                "findings": [],
                                "lint": [],
                            },
                        ],
                        "durationMs": 180000,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    return str(data_root), str(progress_dir)


def test_priority_rule_picks_wrong_then_open_weak_then_overdue_before_interleaving(tmp_path: Path):
    data_root, progress_dir = _seed_priority_and_scope_fixture(tmp_path)

    # With limit=4:
    # Tier A (lastWrong=True): PRG/Q01 (also open weak trap U-edge-empty!), MTH-U02/Q01
    # Tier B (open weak spot, not lastWrong): MTH-U02/Q02 (due 11-16), MTH-U01/Q01 (due 11-18), PRG/Q02 (due 11-19)
    # Tier C (not lastWrong, not open weak): MTH-U01/Q02 (due 11-05), MTH-T02/Q01 (due 11-10)
    # Picking top 4 MUST select the 2 Tier-A items + the 2 earliest Tier-B items,
    # NOT the much older Tier-C items (due 11-05 and 11-10)!
    top4 = ri.get_due_items(
        today="2026-11-19",
        limit=4,
        data_root=data_root,
        progress_dir=progress_dir,
    )
    picked_keys = {ri.item_key(it["drillId"], it["qid"]) for it in top4}
    assert picked_keys == {
        "DRL-PRG-T01-C01-U01-01/Q01",
        "DRL-MTH-T01-C04-U02-01/Q01",
        "DRL-MTH-T01-C04-U02-01/Q02",
        "DRL-MTH-T01-C04-U01-01/Q01",
    }
    # And among Tier C items when limit=7 (all), Tier C still appears ordered by dueDate ascending when prioritized:
    loaded = ri.weak_spots.load_items(data_root=data_root, progress_dir=progress_dir)
    open_traps = ri.get_open_weak_traps(loaded)
    assert open_traps == {"c04-open-weak-trap", "U-edge-empty"}
    schedule = ri.build_schedule_from_progress(data_root=data_root, progress_dir=progress_dir)
    prioritized = ri.prioritize_due_items(list(schedule.values()), open_weak_traps=open_traps)
    assert [ri.item_key(it["drillId"], it["qid"]) for it in prioritized] == [
        "DRL-PRG-T01-C01-U01-01/Q01",  # Tier A + open weak
        "DRL-MTH-T01-C04-U02-01/Q01",  # Tier A
        "DRL-MTH-T01-C04-U02-01/Q02",  # Tier B (due 11-16)
        "DRL-MTH-T01-C04-U01-01/Q01",  # Tier B (due 11-18)
        "DRL-PRG-T01-C01-U01-01/Q02",  # Tier B (due 11-19)
        "DRL-MTH-T01-C04-U01-01/Q02",  # Tier C (due 11-05)
        "DRL-MTH-T02-C01-U01-01/Q01",  # Tier C (due 11-10)
    ]


def test_scope_filters_and_cli_scope_and_duration_estimates(tmp_path: Path, capsys):
    import pytest

    data_root, progress_dir = _seed_priority_and_scope_fixture(tmp_path)

    mth_due = ri.get_due_items(today="2026-11-19", scope="subject:MTH", data_root=data_root, progress_dir=progress_dir)
    assert len(mth_due) == 5
    assert all(it["subject"] == "MTH" for it in mth_due)

    prg_due = ri.get_due_items(today="2026-11-19", scope="subject:PRG", data_root=data_root, progress_dir=progress_dir)
    assert len(prg_due) == 2
    assert all(it["subject"] == "PRG" for it in prg_due)

    unit_due = ri.get_due_items(
        today="2026-11-19", scope="unit:MTH-T01-C04-U01", data_root=data_root, progress_dir=progress_dir
    )
    assert {ri.item_key(it["drillId"], it["qid"]) for it in unit_due} == {
        "DRL-MTH-T01-C04-U01-01/Q01",
        "DRL-MTH-T01-C04-U01-01/Q02",
    }

    chap_due = ri.get_due_items(
        today="2026-11-19", scope="chapter:MTH-T01-C04", data_root=data_root, progress_dir=progress_dir
    )
    assert len(chap_due) == 4
    assert all(it["unitCode"].startswith("MTH-T01-C04-U") for it in chap_due)

    trap_due = ri.get_due_items(
        today="2026-11-19", scope="trap:c04-open-weak-trap", data_root=data_root, progress_dir=progress_dir
    )
    assert {ri.item_key(it["drillId"], it["qid"]) for it in trap_due} == {
        "DRL-MTH-T01-C04-U01-01/Q01",
        "DRL-MTH-T01-C04-U02-01/Q02",
    }

    drill_due = ri.get_due_items(
        today="2026-11-19", scope="drill:DRL-MTH-T02-C01-U01-01", data_root=data_root, progress_dir=progress_dir
    )
    assert [ri.item_key(it["drillId"], it["qid"]) for it in drill_due] == ["DRL-MTH-T02-C01-U01-01/Q01"]

    for bad in ("invalid", "subject:BIO", "unit:../etc", "trap:a..b", "foo:bar", "unit:"):
        with pytest.raises(ValueError):
            ri.parse_scope(bad)

    # CLI --scope and duration estimates
    rc = ri.main(
        [
            "--due",
            "--scope",
            "subject:MTH",
            "--today",
            "2026-11-19",
            "--data-root",
            data_root,
            "--progress-dir",
            progress_dir,
            "--json",
        ]
    )
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["scope"] == "subject:MTH"
    assert out["totalDue"] == 5
    assert out["bySubject"] == {"MTH": 5, "PRG": 2}
    # MTH attempt durations: [60k, 60k, 120k, 120k, 120k, 120k, 180k] -> median 120_000 ms (2 min/item) -> 5 items = 10 min
    assert out["medianDurationMs"] == 120_000
    assert out["estimatedMinutes"] == 10

    # Fallback 1.5 min (90_000 ms) when no durationMs exists
    assert ri.estimate_median_duration_ms([]) == 90_000
    assert ri.estimate_review_minutes(0, 90_000) == 0
    assert ri.estimate_review_minutes(1, 90_000) == 2
    assert ri.estimate_review_minutes(8, 90_000) == 12


def test_variants_do_not_move_schedule_feed_weak_spots_and_example_marks_assisted(tmp_path: Path):
    from scripts import weak_spots

    data_root, progress_dir = _seed_fixture(tmp_path)
    # Overwrite U01 progress so Q01 has:
    # - 11-10 correct (L1 -> L2)
    # - 11-15 wrong (L2 -> L1, due 11-16) with matchedTrap
    # - variant attempts (correct + wrong with matchedTrap) -> MUST NOT change level, MUST feed weak_spots
    # - worked example viewed at 11-19T10:30:00Z
    # - 11-19T11:00:00Z correct on Q01 -> assisted (after exampleViewedAt) -> stays at L1 (due 11-20, NOT L2!)
    (Path(progress_dir) / "DRL-MTH-T01-C04-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T01-C04-U01-01",
                "updatedAt": "2026-11-19T11:00:00Z",
                "problems": {
                    "Q01": {
                        "attempts": [
                            {"verdict": "correct", "ts": "2026-11-10T10:00:00Z"},
                            {
                                "verdict": "incorrect",
                                "ts": "2026-11-15T10:00:00Z",
                                "matchedTrap": "c04-divide-not-invert-trap",
                            },
                            {"verdict": "correct", "ts": "2026-11-19T11:00:00Z"},
                        ],
                        "exampleViewedAt": "2026-11-19T10:30:00Z",
                        "variants": {
                            "v1": {
                                "variantId": "VAR-MTH-T01-C04-fraction-division-01",
                                "role": "try",
                                "servedAt": "2026-11-19T10:00:00Z",
                                "attempts": [
                                    {"verdict": "correct", "ts": "2026-11-19T10:05:00Z", "kind": "variant"},
                                    {
                                        "verdict": "incorrect",
                                        "ts": "2026-11-19T10:10:00Z",
                                        "kind": "variant",
                                        "matchedTrap": "c04-divide-not-invert-trap",
                                    },
                                ],
                            }
                        },
                        "score": 0.5,
                        "hintsRevealed": 0,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    # replay_events ignores kind=="variant" directly
    replayed = ri.replay_events(
        [
            {"date": "2026-11-15", "correct": False, "assisted": False},
            {"date": "2026-11-16", "correct": True, "assisted": False, "kind": "variant"},
            {"date": "2026-11-17", "correct": True, "assisted": False, "kind": "variant"},
        ]
    )
    assert replayed == {"level": 1, "lastReviewed": "2026-11-15", "dueDate": "2026-11-16", "lastWrong": True}

    # Schedule: Q01 stayed at L1 (assisted after exampleViewedAt) and due +1 day (2026-11-20)
    schedule = ri.build_schedule_from_progress(data_root=data_root, progress_dir=progress_dir)
    q1 = schedule["DRL-MTH-T01-C04-U01-01/Q01"]
    assert q1["level"] == 1
    assert q1["lastReviewed"] == "2026-11-19"
    assert q1["dueDate"] == "2026-11-20"

    # Weak spots: variant matchedTrap combines with original matchedTrap (>= 2 matches -> open weak spot!)
    items = weak_spots.load_items(data_root=data_root, progress_dir=progress_dir)
    q1_item = next(i for i in items if i.drill == "DRL-MTH-T01-C04-U01-01" and i.pid == "Q01")
    assert q1_item.assisted is True
    assert q1_item.matched.count("c04-divide-not-invert-trap") == 2
    traps = weak_spots.trap_status(items)
    assert traps["c04-divide-not-invert-trap"]["open"] is True
    assert traps["c04-divide-not-invert-trap"]["matches"] == 2


def test_record_review_result_preserves_level_after_in_cycle_review_help_reveal(tmp_path: Path):
    data_root, progress_dir = _seed_fixture(tmp_path)
    key = "DRL-MTH-T01-C04-U01-01/Q01"
    saved = ri.build_schedule_from_progress(data_root=data_root, progress_dir=progress_dir)
    saved[key]["level"] = 3
    saved[key]["lastReviewed"] = "2026-11-18"
    saved[key]["dueDate"] = "2026-11-20"
    ri.write_review_items(saved, progress_dir=progress_dir)

    progress_file = Path(progress_dir) / "DRL-MTH-T01-C04-U01-01.json"
    progress = json.loads(progress_file.read_text(encoding="utf-8"))
    progress["problems"]["Q01"]["cycleStartedAt"] = "2026-11-20T12:00:00Z"
    progress["problems"]["Q01"]["reviewHintRevealedAt"] = "2026-11-20T12:01:00Z"
    progress_file.write_text(json.dumps(progress), encoding="utf-8")

    schedule = ri.get_review_items_schedule(data_root=data_root, progress_dir=progress_dir)
    assert schedule[key]["level"] == 3
    assert schedule[key]["dueDate"] == "2026-11-20"
    updated = ri.record_review_result(
        "DRL-MTH-T01-C04-U01-01",
        "Q01",
        correct=True,
        hints_used=1,
        review_date="2026-11-20",
        data_root=data_root,
        progress_dir=progress_dir,
    )
    assert updated["level"] == 3
    assert updated["dueDate"] == "2026-11-27"
