"""Tests for per-item spaced-review scheduling (`scripts/review_items.py`)."""

from __future__ import annotations

import json
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
    assert u2_q1["level"] == 1 and u2_q1["dueDate"] == "2026-11-18"

    u2_q2 = schedule["DRL-MTH-T01-C04-U02-01/Q02"]
    assert u2_q2["level"] == 1 and u2_q2["dueDate"] == "2026-11-18"

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
