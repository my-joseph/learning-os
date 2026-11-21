"""Drill quality report tests use isolated curriculum and learner state."""

from __future__ import annotations

import json

from scripts.drill_quality import build_report, format_report


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_zero_data_report_is_empty_and_flags_vault_archetype(tmp_path):
    _write(
        tmp_path / "math_engine/reasoning_vault/MTH-T02-C01-U01.json",
        {
            "unitCode": "MTH-T02-C01-U01",
            "archetypes": [{"archetypeKey": "powers", "unitCode": "MTH-T02-C01-U01", "level": 1}],
        },
    )
    report = build_report("MTH-T02-C01-U01", repo_root=str(tmp_path))
    assert report["drills"] == 0
    assert report["attempts"] == 0
    assert report["levels"] == {}
    assert {flag["type"] for flag in report["flags"]} == {"archetype_never_drilled"}


def test_flags_quality_patterns_and_reports_level_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    _write(
        tmp_path / "math_engine/reasoning_vault/MTH-T02-C01-U01.json",
        {
            "unitCode": "MTH-T02-C01-U01",
            "archetypes": [{"archetypeKey": "powers", "unitCode": "MTH-T02-C01-U01", "level": 1}],
        },
    )
    _write(
        tmp_path / "drills/data/MTH-T02-C01-U01/DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "unitCode": "MTH-T02-C01-U01",
            "subject": "MATH",
            "problems": [
                {
                    "id": f"Q{i}",
                    "level": 1,
                    "archetypeKey": "powers",
                    "commonTrapTag": "sign-error" if i < 3 else "wrong-cycle",
                }
                for i in range(1, 4)
            ],
        },
    )
    _write(
        tmp_path / "drills/variants/MTH-T02-C01-U01.json",
        {"unitCode": "MTH-T02-C01-U01", "variants": [{"sourceArchetype": "powers"}]},
    )
    _write(
        tmp_path / "progress/DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "problems": {
                f"Q{i}": {"score": 1, "attempts": [{"verdict": "correct"}], "durationMs": 1200} for i in range(1, 4)
            },
        },
    )
    report = build_report("MTH-T02-C01-U01", repo_root=str(tmp_path))
    kinds = {flag["type"] for flag in report["flags"]}
    assert {"too_easy", "level_too_easy", "trap_never_triggered", "similar_never_opened"} <= kinds
    assert report["levels"]["L1"]["firstTryCleanRate"] == 1
    assert report["archetypes"]["powers"]["timeMsMean"] == 1200
    assert report["similarNeverOpened"] == ["powers"]
    trap_flags = [flag for flag in report["flags"] if flag["type"] == "trap_never_triggered"]
    assert len(trap_flags) == 1
    assert trap_flags[0]["trapCount"] == 2
    assert len(trap_flags[0]["traps"]) == 2
    assert format_report(report).count("powers@L1 — 2 expected trap(s)") == 1


def test_partially_attempted_problem_is_not_untouched(tmp_path, monkeypatch):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    _write(
        tmp_path / "drills/data/MTH-T02-C01-U01/DRL-MTH-T02-C01-U01-04.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-04",
            "unitCode": "MTH-T02-C01-U01",
            "problems": [
                {"id": "Q01", "level": 2, "archetypeKey": "powers"},
                {"id": "Q02", "level": 2, "archetypeKey": "powers"},
            ],
        },
    )
    _write(
        tmp_path / "progress/DRL-MTH-T02-C01-U01-04.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-04",
            "problems": {"Q01": {"attempts": [{"verdict": "incorrect"}], "score": None}},
        },
    )

    report = build_report("MTH-T02-C01-U01", repo_root=str(tmp_path))

    assert report["untouchedDrills"] == []
    assert report["untouchedItems"] == ["DRL-MTH-T02-C01-U01-04/Q02"]


def test_text_report_lists_archetypes_flags_and_missing_practice_data(tmp_path, monkeypatch):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "missing-progress"))
    _write(
        tmp_path / "math_engine/reasoning_vault/MTH-T02-C01-U01.json",
        {
            "unitCode": "MTH-T02-C01-U01",
            "archetypes": [{"archetypeKey": "powers", "unitCode": "MTH-T02-C01-U01", "level": 1}],
        },
    )
    _write(
        tmp_path / "drills/data/MTH-T02-C01-U01/DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "unitCode": "MTH-T02-C01-U01",
            "problems": [{"id": "Q01", "level": 1, "archetypeKey": "powers"}],
        },
    )

    report = build_report("MTH-T02-C01-U01", repo_root=str(tmp_path))
    output = format_report(report)

    assert f"no practice data found in {tmp_path / 'missing-progress'}" in output
    assert "Archetypes: key | levels seen | attempts | clean | reveals" in output
    assert "powers | L1 | 0 | n/a | 0" in output
    assert "powers@L1 — 1 item(s) have no practice activity" in output


def test_counts_only_current_substantive_original_attempts_and_reveals_once(tmp_path, monkeypatch):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    drill_id = "DRL-MTH-T02-C01-U01-01"
    _write(
        tmp_path / f"drills/data/MTH-T02-C01-U01/{drill_id}.json",
        {
            "drillId": drill_id,
            "unitCode": "MTH-T02-C01-U01",
            "problems": [{"id": "Q01", "level": 2, "archetypeKey": "powers"}],
        },
    )
    _write(
        tmp_path / f"progress/{drill_id}.json",
        {
            "drillId": drill_id,
            "problems": {
                "Q01": {
                    "cycleStartedAt": "2026-11-20T12:00:00Z",
                    "solutionRevealedBeforeAnswer": True,
                    "attempts": [
                        {"ts": "2026-11-19T12:00:00Z", "verdict": "incorrect"},
                        {"ts": "2026-11-20T12:01:00Z", "verdict": "correct", "kind": "variant"},
                        {"ts": "2026-11-20T12:02:00Z", "verdict": "parse_error"},
                        {"ts": "2026-11-20T12:03:00Z", "verdict": "correct"},
                    ],
                }
            },
        },
    )

    report = build_report("MTH-T02-C01-U01", repo_root=str(tmp_path))

    assert report["attempts"] == 1
    assert report["archetypes"]["powers"]["attempts"] == 1
    assert report["archetypes"]["powers"]["stepsRevealed"] == 0
    assert report["archetypes"]["powers"]["solutionRevealed"] == 1
    assert "powers | L2 | 1 | 0% | 1" in format_report(report)


def test_preallocated_similar_slots_do_not_count_as_opened(tmp_path, monkeypatch):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    drill_id = "DRL-MTH-T02-C01-U01-02"
    _write(
        tmp_path / "drills/variants/MTH-T02-C01-U01.json",
        {"unitCode": "MTH-T02-C01-U01", "variants": [{"sourceArchetype": "powers"}]},
    )
    _write(
        tmp_path / f"drills/data/MTH-T02-C01-U01/{drill_id}.json",
        {
            "drillId": drill_id,
            "unitCode": "MTH-T02-C01-U01",
            "problems": [{"id": "Q01", "level": 2, "archetypeKey": "powers"}],
        },
    )
    _write(
        tmp_path / f"progress/{drill_id}.json",
        {
            "drillId": drill_id,
            "problems": {"Q01": {"similarSlots": [{"servedAt": "", "attempts": []}]}},
        },
    )

    report = build_report("MTH-T02-C01-U01", repo_root=str(tmp_path))

    assert report["archetypes"]["powers"]["similarOpened"] is False
    assert report["similarNeverOpened"] == ["powers"]


def test_served_similar_slot_counts_as_opened(tmp_path, monkeypatch):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    drill_id = "DRL-MTH-T02-C01-U01-04"
    _write(
        tmp_path / "drills/variants/MTH-T02-C01-U01.json",
        {"unitCode": "MTH-T02-C01-U01", "variants": [{"sourceArchetype": "powers"}]},
    )
    _write(
        tmp_path / f"drills/data/MTH-T02-C01-U01/{drill_id}.json",
        {
            "drillId": drill_id,
            "unitCode": "MTH-T02-C01-U01",
            "problems": [{"id": "Q01", "level": 2, "archetypeKey": "powers"}],
        },
    )
    _write(
        tmp_path / f"progress/{drill_id}.json",
        {
            "drillId": drill_id,
            "problems": {"Q01": {"similarSlots": [{"servedAt": "2026-11-20T12:00:00Z", "attempts": []}]}},
        },
    )

    report = build_report("MTH-T02-C01-U01", repo_root=str(tmp_path))

    assert report["archetypes"]["powers"]["similarOpened"] is True
    assert report["similarNeverOpened"] == []


def test_level_ladder_gap_starts_at_archetype_base_level(tmp_path, monkeypatch):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    drill_id = "DRL-MTH-T02-C01-U01-03"
    _write(
        tmp_path / "math_engine/reasoning_vault/MTH-T02-C01-U01.json",
        {
            "unitCode": "MTH-T02-C01-U01",
            "archetypes": [{"archetypeKey": "powers", "unitCode": "MTH-T02-C01-U01", "level": 3}],
        },
    )
    _write(
        tmp_path / f"drills/data/MTH-T02-C01-U01/{drill_id}.json",
        {
            "drillId": drill_id,
            "unitCode": "MTH-T02-C01-U01",
            "problems": [{"id": "Q01", "level": 3, "archetypeKey": "powers"}],
        },
    )

    report = build_report("MTH-T02-C01-U01", repo_root=str(tmp_path))
    ladder_flags = [flag for flag in report["flags"] if flag["type"] == "level_ladder_gap"]

    assert ladder_flags == [{"type": "level_ladder_gap", "archetype": "powers", "missing": ["L4"]}]
