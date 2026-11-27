"""Tests for S3 aggregate authoring feedback brief (`scripts.authoring_signals`)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import authoring_signals, issues


def _seed_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Create isolated drills, vault, progress, and issue log with secret sentinel strings."""
    repo = tmp_path / "repo"
    unit = "MTH-T99-C01-U01"
    vault_dir = repo / "math_engine" / "reasoning_vault"
    vault_dir.mkdir(parents=True)
    (vault_dir / f"{unit}.json").write_text(
        json.dumps(
            {
                "unitCode": unit,
                "archetypes": [
                    {
                        "archetypeKey": "t99-sign-trap",
                        "unitCode": unit,
                        "level": 2,
                        "cognitiveTraps": ["t99-dropped-sign"],
                    },
                    {
                        "archetypeKey": "t99-unused-arch",
                        "unitCode": unit,
                        "level": 3,
                        "cognitiveTraps": ["t99-other-trap"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    data_root = repo / "drills" / "data"
    (data_root / unit).mkdir(parents=True)
    drill_id = f"DRL-{unit}-01"
    (data_root / unit / f"{drill_id}.json").write_text(
        json.dumps(
            {
                "drillId": drill_id,
                "unitCode": unit,
                "subject": "MATH",
                "problems": [
                    {
                        "id": "Q01",
                        "level": 2,
                        "form": "direct",
                        "archetypeKey": "t99-sign-trap",
                        "commonTrapTag": "t99-dropped-sign",
                        "prompt": "SECRET_PROMPT_TEXT_XYZ: Evaluate $2 - 5$.",
                        "answerPlain": "SECRET_ANSWER_98765",
                        "steps": [{"latex": "2 - 5 = -3", "explain": "SECRET_STEP_EXPLAIN"}],
                    },
                    {
                        "id": "Q02",
                        "level": 2,
                        "form": "direct",
                        "archetypeKey": "t99-sign-trap",
                        "commonTrapTag": "t99-dropped-sign",
                        "prompt": "SECRET_PROMPT_2: Evaluate $3 - 7$.",
                        "answerPlain": "SECRET_ANSWER_54321",
                        "steps": [{"latex": "3 - 7 = -4", "explain": "SECRET_STEP_2"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    progress_dir = tmp_path / "progress"
    progress_dir.mkdir()
    (progress_dir / f"{drill_id}.json").write_text(
        json.dumps(
            {
                "drillId": drill_id,
                "problems": {
                    "Q01": {
                        "userInput": "SECRET_LEARNER_INPUT_111",
                        "score": 0,
                        "mistakeNote": "SECRET_LEARNER_NOTE_ABC",
                        "attempts": [
                            {
                                "input": "SECRET_LEARNER_INPUT_111",
                                "ts": "2026-11-26T10:00:00Z",
                                "verdict": "incorrect",
                                "trapMatched": True,
                                "matchedTrap": "t99-dropped-sign",
                            }
                        ],
                    },
                    "Q02": {
                        "userInput": "SECRET_LEARNER_INPUT_222",
                        "score": 0,
                        "attempts": [
                            {
                                "input": "SECRET_LEARNER_INPUT_222",
                                "ts": "2026-11-27T10:00:00Z",
                                "verdict": "incorrect",
                                "trapMatched": True,
                                "matchedTrap": "t99-dropped-sign",
                            }
                        ],
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    issue_log = tmp_path / "issues" / "log.jsonl"
    issues.add_issue(
        "level",
        "batch",
        "gate",
        f"{unit}/t99-unused-arch@L3",
        "missed L3 demand",
        action="dropped",
        path=str(issue_log),
    )
    return repo, data_root, progress_dir, issue_log


def test_authoring_signals_aggregates_all_sources_with_zero_leak(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, data_root, progress_dir, issue_log = _seed_fixture(tmp_path)
    unit = "MTH-T99-C01-U01"

    summary = authoring_signals.collect_authoring_signals(
        unit,
        data_root=str(data_root),
        progress_dir=str(progress_dir),
        repo_root=str(repo),
        issue_log=str(issue_log),
    )
    assert summary["progressRead"] is True
    assert summary["weakSpots"]["openTrapCount"] == 1
    assert summary["weakSpots"]["openTraps"][0]["tag"] == "t99-dropped-sign"
    assert summary["drillQuality"]["attempts"] == 2
    assert any(f["type"] == "archetype_never_drilled" for f in summary["drillQuality"]["flags"])
    assert summary["recentMistakes"][0]["tag"] == "t99-dropped-sign"
    assert summary["recentMistakes"][0]["count"] == 2
    assert summary["issues"]["openCount"] == 1
    assert summary["signalsUsedLine"].startswith("Signals used: ")

    rendered = authoring_signals.format_authoring_signals(summary)
    dumped = json.dumps(summary)
    for secret in (
        "SECRET_PROMPT_TEXT_XYZ",
        "SECRET_ANSWER_98765",
        "SECRET_STEP_EXPLAIN",
        "SECRET_LEARNER_INPUT_111",
        "SECRET_LEARNER_NOTE_ABC",
    ):
        assert secret not in rendered
        assert secret not in dumped

    assert (
        authoring_signals.main(
            [
                unit,
                "--data-root",
                str(data_root),
                "--progress-dir",
                str(progress_dir),
                "--issue-log",
                str(issue_log),
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "Signals used:" in out
    assert "t99-dropped-sign" in out


def test_authoring_signals_no_progress_mode_skips_progress_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, data_root, progress_dir, issue_log = _seed_fixture(tmp_path)
    unit = "MTH-T99-C01-U01"

    summary = authoring_signals.collect_authoring_signals(
        unit,
        no_progress=True,
        data_root=str(data_root),
        progress_dir=str(progress_dir),
        repo_root=str(repo),
        issue_log=str(issue_log),
    )
    assert summary["progressRead"] is False
    assert summary["weakSpots"]["openTrapCount"] == 0
    assert summary["recentMistakes"] == []
    assert summary["issues"]["openCount"] == 1
    assert "--no-progress" in summary["signalsUsedLine"]

    rc = authoring_signals.main([unit, "--no-progress", "--json", "--issue-log", str(issue_log)])
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["progressRead"] is False
    assert parsed["issues"]["openCount"] == 1


def test_cli_outputs_only_allowed_aggregates(tmp_path, monkeypatch, capsys):
    _, data_root, progress_dir, issue_log = _seed_fixture(tmp_path)
    unit = "MTH-T99-C01-U01"
    drill_id = f"DRL-{unit}-01"
    drill_file = data_root / unit / f"{drill_id}.json"
    drill = json.loads(drill_file.read_text())
    drill["problems"].append({"id": "Q73", "level": 2, "answerPlain": "SECRET_SKIP_ANSWER"})
    drill_file.write_text(json.dumps(drill))
    progress_file = progress_dir / f"{drill_id}.json"
    progress = json.loads(progress_file.read_text())
    progress["problems"]["Q73"] = {"skipped": True, "revisitNote": "SECRET_SKIP_NOTE"}
    progress_file.write_text(json.dumps(progress))
    locator = f"some/private/drills/data/{unit}/{drill_id}.json/Q73"
    issues.add_issue("level", "batch", "gate", locator, "SECRET_ISSUE_NOTE", path=str(issue_log))
    issue_ids = [record["id"] for record in issues.issues(str(issue_log))]

    original_report = authoring_signals.drill_quality.build_report

    def report_with_private_fields(*args, **kwargs):
        report = original_report(*args, **kwargs)
        report["flags"].append(
            {
                "type": "untouched",
                "archetype": "Q73",
                "level": 2,
                "missing": ["L3", "Q73"],
                "items": [locator],
                "recommendation": "SECRET_RECOMMENDATION",
                "note": "SECRET_FLAG_NOTE",
            }
        )
        return report

    monkeypatch.setattr(authoring_signals.drill_quality, "build_report", report_with_private_fields)
    args = [unit, "--data-root", str(data_root), "--progress-dir", str(progress_dir), "--issue-log", str(issue_log)]
    assert authoring_signals.main(args) == 0
    text = capsys.readouterr().out
    assert authoring_signals.main([*args, "--json"]) == 0
    dumped = capsys.readouterr().out
    for forbidden in ("Q01", "Q02", "Q73", "SECRET_", "where", drill_id, locator, *issue_ids):
        assert forbidden not in text
        assert forbidden not in dumped

    data = json.loads(dumped)
    assert set(data) == {
        "scope",
        "progressRead",
        "weakSpots",
        "drillQuality",
        "recentMistakes",
        "issues",
        "signalsUsedLine",
    }
    assert set(data["weakSpots"]) == {
        "unitCount",
        "openTrapCount",
        "openTraps",
        "levelAdvice",
        "skippedArchetypes",
        "masteryCaps",
    }
    assert data["weakSpots"]["skippedArchetypes"] == []
    assert all(set(trap) == {"unit", "tag", "matches", "drills", "last"} for trap in data["weakSpots"]["openTraps"])
    assert all(set(cap) == {"unit", "cappedAt"} for cap in data["weakSpots"]["masteryCaps"])
    quality = data["drillQuality"]
    assert set(quality) == {"drills", "attempts", "levelCleanRates", "flags"}
    assert all(
        set(rate) == {"items", "attempts", "firstTryCleanRate", "skips"} for rate in quality["levelCleanRates"].values()
    )
    assert all(set(flag) <= {"type", "archetype", "level", "missing", "items"} for flag in quality["flags"])
    assert quality["flags"][-1] == {"type": "untouched", "level": 2, "missing": ["L3"]}
    assert all(set(row) == {"tag", "count", "last", "archetypes"} for row in data["recentMistakes"])
    assert any(row["tag"] == "concept-gap" for row in data["recentMistakes"])
    assert data["issues"] == {"total": 2, "openCount": 2, "byKind": {"level": 2}, "openByKind": {"level": 2}}
