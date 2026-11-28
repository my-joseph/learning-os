"""Tests for S3 aggregate authoring feedback brief (`scripts.authoring_signals`)."""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
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
    drill_file = data_root / unit / f"{drill_id}.json"
    drill = json.loads(drill_file.read_text())
    drill["problems"].append({**drill["problems"][1], "id": "Q03"})
    drill_file.write_text(json.dumps(drill))
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

    progress_file = progress_dir / f"{drill_id}.json"
    progress = json.loads(progress_file.read_text())
    progress["problems"]["Q03"] = progress["problems"]["Q02"]
    progress_file.write_text(json.dumps(progress))

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
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, data_root, progress_dir, issue_log = _seed_fixture(tmp_path)
    unit = "MTH-T99-C01-U01"
    monkeypatch.chdir(repo)

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
    assert summary["drillQuality"]["attempts"] == 3
    assert any(f["type"] == "too_hard" for f in summary["drillQuality"]["flags"])
    assert summary["recentMistakes"][0]["tag"] == "t99-dropped-sign"
    assert summary["recentMistakes"][0]["count"] == 3
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
    repo, data_root, progress_dir, issue_log = _seed_fixture(tmp_path)
    monkeypatch.chdir(repo)
    unit = "MTH-T99-C01-U01"
    drill_id = f"DRL-{unit}-01"
    drill_file = data_root / unit / f"{drill_id}.json"
    drill = json.loads(drill_file.read_text())
    vault_file = repo / "math_engine" / "reasoning_vault" / f"{unit}.json"
    vault = json.loads(vault_file.read_text())
    vault["archetypes"][0]["cognitiveTraps"].append("rare-registered-trap")
    vault["archetypes"] += [
        {"archetypeKey": "singleton-arch", "level": 1, "cognitiveTraps": ["singleton-trap"]},
        {"archetypeKey": "two-item-arch", "level": 4, "cognitiveTraps": ["pair-trap"]},
    ]
    vault_file.write_text(json.dumps(vault))
    progress_file = progress_dir / f"{drill_id}.json"
    progress = json.loads(progress_file.read_text())
    ts = date.today().isoformat() + "T10:00:00Z"
    for state in progress["problems"].values():
        state["attempts"][0]["ts"] = ts
        state["attempts"].append({**state["attempts"][0], "matchedTrap": "SECRET_UNREGISTERED_TAG"})
        state["attempts"].append({**state["attempts"][0], "matchedTrap": "another-unknown-tag"})
    progress["problems"]["Q01"]["attempts"].append(
        {**progress["problems"]["Q01"]["attempts"][0], "matchedTrap": "rare-registered-trap"}
    )
    for qid, level, arch, tag in [
        ("Q73", 1, "singleton-arch", "singleton-trap"),
        ("Q74", 4, "two-item-arch", "pair-trap"),
        ("Q75", 4, "two-item-arch", "pair-trap"),
    ]:
        drill["problems"].append({"id": qid, "level": level, "archetypeKey": arch, "answerPlain": "SECRET_SKIP_ANSWER"})
        progress["problems"][qid] = {
            "skipped": True,
            "revisitNote": "SECRET_SKIP_NOTE",
            "attempts": [{"input": "SECRET_INPUT", "ts": ts, "verdict": "incorrect", "matchedTrap": tag}] * 3,
        }
    drill_file.write_text(json.dumps(drill))
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
    for forbidden in (
        "Q01",
        "Q02",
        "Q03",
        "Q73",
        "Q74",
        "Q75",
        "SECRET_",
        "where",
        drill_id,
        locator,
        *issue_ids,
        "singleton-arch",
        "two-item-arch",
        "singleton-trap",
        "pair-trap",
        "another-unknown-tag",
        "rare-registered-trap",
    ):
        assert forbidden not in text
        assert forbidden not in dumped

    assert not re.search(r"\b\d{4}-\d{2}-\d{2}\b", text + dumped)

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
    assert all(set(trap) == {"unit", "tag", "matches", "last"} for trap in data["weakSpots"]["openTraps"])
    assert all(set(cap) == {"unit", "cappedAt"} for cap in data["weakSpots"]["masteryCaps"])
    quality = data["drillQuality"]
    assert set(quality) == {"drills", "attempts", "levelCleanRates", "flags"}
    assert all(
        set(rate) == {"items", "attempts", "firstTryCleanRate", "skips"} for rate in quality["levelCleanRates"].values()
    )
    assert all(set(flag) <= {"type", "archetype", "level", "missing", "items"} for flag in quality["flags"])
    assert set(quality["levelCleanRates"]) == {"L2"}
    assert set(data["weakSpots"]["levelAdvice"]) == {"L2"}
    assert all(rate["items"] >= 3 for rate in quality["levelCleanRates"].values())
    assert all(flag.get("items", 3) >= 3 for flag in quality["flags"])
    assert all(trap["matches"] >= 3 for trap in data["weakSpots"]["openTraps"])
    assert {trap["tag"] for trap in data["weakSpots"]["openTraps"]} == {"t99-dropped-sign"}
    assert all(set(row) == {"tag", "count", "last", "archetypes"} for row in data["recentMistakes"])
    assert {row["tag"] for row in data["recentMistakes"]} == {"t99-dropped-sign", "unrecognized"}
    assert all(row["count"] == 3 and row["last"] == "last 7 days" for row in data["recentMistakes"])
    assert data["issues"] == {"total": 2, "openCount": 2, "byKind": {}, "openByKind": {}}


def test_prg_reviews_use_registry_and_vault_check_ids(tmp_path, monkeypatch):
    unit = "PRG-T99-C01-U01"
    drill_id = f"DRL-{unit}-01"
    data_root = tmp_path / "drills" / "data"
    progress_dir = tmp_path / "progress"
    code_dir = tmp_path / "code_engine"
    vault = code_dir / "reasoning_vault"
    (data_root / unit).mkdir(parents=True)
    progress_dir.mkdir()
    vault.mkdir(parents=True)
    (code_dir / "check_names.json").write_text(json.dumps({"@tool/rule": "Registered lint rule"}))
    key = "prg-probe"
    (vault / "PRG-T99-C01.json").write_text(
        json.dumps(
            {
                "unitCode": "PRG-T99-C01",
                "archetypes": [
                    {
                        "archetypeKey": key,
                        "unitCode": unit,
                        "level": 2,
                        "qualityChecks": [
                            {"id": "QC-probe", "check": "Registered vault check"},
                        ],
                    }
                ],
            }
        )
    )
    qids = ["Q01", "Q02", "Q03"]
    (data_root / unit / f"{drill_id}.json").write_text(
        json.dumps(
            {
                "drillId": drill_id,
                "unitCode": unit,
                "subject": "PRG",
                "problems": [{"id": qid, "archetypeKey": key, "level": 2} for qid in qids],
            }
        )
    )
    review = {
        "at": (date.today() - timedelta(days=12)).isoformat() + "T10:00:00Z",
        "verdict": "revise",
        "findings": [{"check": "QC-probe"}, {"check": "SECRET_NOT_REGISTERED"}],
        "lint": [{"rule": "@tool/rule"}],
    }
    (progress_dir / f"{drill_id}.json").write_text(
        json.dumps(
            {
                "drillId": drill_id,
                "updatedAt": review["at"],
                "problems": {qid: {"reviews": [review]} for qid in qids},
            }
        )
    )
    monkeypatch.chdir(tmp_path)
    summary = authoring_signals.collect_authoring_signals(
        unit, data_root=str(data_root), progress_dir=str(progress_dir), issue_log=str(tmp_path / "issues.jsonl")
    )
    assert {row["tag"] for row in summary["weakSpots"]["openTraps"]} == {"QC-probe", "@tool/rule"}
    assert {row["tag"] for row in summary["recentMistakes"]} == {"QC-probe", "@tool/rule", "unrecognized"}
    assert all(row["count"] == 3 and row["last"] == "last 30 days" for row in summary["recentMistakes"])
    assert "SECRET_NOT_REGISTERED" not in json.dumps(summary)


def test_recency_suppresses_buckets_with_fewer_than_three_items():
    today = date(2026, 11, 28)
    dates = ["2026-11-28", "2026-11-27", "2026-09-01", "2026-09-02", "2026-09-03"]
    items = [
        authoring_signals.weak_spots.Item("drill", "unit", str(i), 2, "direct", None, None, ts, 0, False, False)
        for i, ts in enumerate(dates)
    ]
    assert authoring_signals._published_recency(items[:2], today) == ""
    assert authoring_signals._published_recency(items, today) == "older"
