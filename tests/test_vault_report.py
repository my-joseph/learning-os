"""scripts/vault_report.py: the levels an archetype reaches are proven by evidence (drills, issue log), not by labels."""

import json

import pytest

from scripts import issues
from scripts import vault_report as vr

L4_TAGS = {"setup": "model", "strategy": "prescribed", "check": "edge", "task": "compute", "reverse": False, "steps": 5}
L2_TAGS = {**L4_TAGS, "setup": "translate", "check": "none"}


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNINGOS_ISSUE_LOG", str(tmp_path / "log.jsonl"))
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "MTH-X.json").write_text(
        json.dumps(
            {
                "archetypes": [
                    {"archetypeKey": "x-basic", "unitCode": "MTH-X-U01", "level": 1},
                    {"archetypeKey": "x-model", "unitCode": "MTH-X-U01", "level": 2, "levelNote": "how to reach L4"},
                    {"archetypeKey": "x-weak", "unitCode": "MTH-X-U02", "level": 4},
                    {"archetypeKey": "x-untried", "unitCode": "MTH-X-U02", "level": 3},
                ]
            }
        )
    )
    unit_dir = tmp_path / "data" / "MTH-X-U01"
    unit_dir.mkdir(parents=True)
    (unit_dir / "DRL-MTH-X-U01-01.json").write_text(
        json.dumps(
            {
                "problems": [
                    {"archetypeKey": "x-basic", "level": 1},
                    {"archetypeKey": "x-model", "level": 2},
                    {"archetypeKey": "x-model", "level": 4, "blindSolve": L4_TAGS},  # base L2 pushed to L4
                ]
            }
        )
    )
    chapter_dir = tmp_path / "data" / "MTH-X"
    chapter_dir.mkdir()
    (chapter_dir / "DRL-MTH-X-01.json").write_text(
        json.dumps({"problems": [{"archetypeKey": "x-weak", "level": 2, "blindSolve": L2_TAGS}]})
    )
    issues.add_issue("level", "batch", "gate", "MTH-X-U02/x-weak@L4", "blind solve reached L2", action="dropped")
    issues.add_issue("level", "batch", "gate", "MTH-X-U01/x-model@L3", "reached L2", action="dropped")
    return str(vault), str(tmp_path / "data")


def _rows(rep):
    return {r["key"]: r for r in rep["rows"]}


def test_evidence_by_level_across_drill_folders(env):
    rows = _rows(vr.unit_report("MTH-X", *env))
    assert rows["x-model"]["earned"] == {2: 1, 4: 1} and rows["x-model"]["failed"] == {3: 1}
    assert rows["x-model"]["flags"] == [
        "FAILING@L3"
    ]  # failed L3 and never earned L3 (earning L4 elsewhere is separate)
    assert rows["x-weak"]["earned"] == {2: 1} and rows["x-weak"]["flags"] == ["FAILING@L4"]
    assert rows["x-untried"]["flags"] == ["UNPROVEN"]
    assert rows["x-basic"]["flags"] == []


def test_unit_scope_reports_only_that_unit(env):
    assert sorted(_rows(vr.unit_report("MTH-X-U02", *env))) == ["x-untried", "x-weak"]


def test_log_gaps_logs_failing_once(env):
    rep = vr.unit_report("MTH-X", *env)
    first = vr.log_gaps(rep)
    assert len(first) == 2
    assert vr.log_gaps(rep) == first
    assert "FAILING@L4" in vr.format_report(rep)


def test_log_gaps_records_match_followup_report(env):
    rep = vr.unit_report("MTH-X", *env)
    assert len(vr.log_gaps(rep)) == 2

    rows = _rows(vr.unit_report("MTH-X", *env))
    assert rows["x-weak"]["failed"] == {4: 2}
    assert rows["x-model"]["failed"] == {2: 1, 3: 1}


def test_vault_suffix_preserves_explicit_failure_level(env):
    issues.add_issue("level", "batch", "gate", "MTH-X-U02/x-weak@L4 (vault)", "level failure", action="dropped")
    rows = _rows(vr.unit_report("MTH-X", *env))
    assert rows["x-weak"]["failed"] == {4: 2}


def test_full_report_loads_evidence_once(monkeypatch):
    original_evidence = vr._evidence
    calls = 0

    def count_evidence(data_root):
        nonlocal calls
        calls += 1
        return original_evidence(data_root)

    monkeypatch.setattr(vr, "_evidence", count_evidence)
    assert vr.main([]) == 0
    assert calls == 1


def test_report_runs_on_every_real_vault():
    assert vr.main([]) == 0


def test_prg_scope_vault_report(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNINGOS_ISSUE_LOG", str(tmp_path / "log.jsonl"))
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "PRG-X-C01.json").write_text(
        json.dumps(
            {
                "archetypes": [
                    {"archetypeKey": "prg-u1", "unitCode": "PRG-X-C01-U01", "level": 3},
                    {"archetypeKey": "prg-u2", "unitCode": "PRG-X-C01-U02", "level": 4},
                ]
            }
        )
    )
    data = tmp_path / "data" / "PRG-X-C01-U01"
    data.mkdir(parents=True)
    (data / "DRL-PRG-X-C01-U01-01.json").write_text(
        json.dumps({"subject": "PRG", "problems": [{"archetypeKey": "prg-u1", "level": 3}]})
    )
    rows = _rows(vr.unit_report("PRG-X-C01", str(vault), str(tmp_path / "data")))
    assert rows["prg-u1"]["earned"] == {3: 1} and rows["prg-u1"]["flags"] == []
    assert rows["prg-u2"]["flags"] == ["UNPROVEN"]
    assert sorted(_rows(vr.unit_report("PRG-X-C01-U01", str(vault), str(tmp_path / "data")))) == ["prg-u1"]
