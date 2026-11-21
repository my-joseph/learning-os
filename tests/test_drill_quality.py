"""Drill quality report tests use isolated curriculum and learner state."""

from __future__ import annotations

import json

from scripts.drill_quality import build_report


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
                {"id": f"Q{i}", "level": 1, "archetypeKey": "powers", "commonTrapTag": "sign-error"}
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
