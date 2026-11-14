"""scripts/vault_report.py: archetype levels are proven by evidence (ingested drills, issue log), not by hand."""

import json

import pytest

from scripts import issues
from scripts import vault_report as vr

L4_TAGS = {"setup": "model", "strategy": "prescribed", "check": "edge", "task": "compute", "reverse": False, "steps": 5}
L2_TAGS = {**L4_TAGS, "setup": "translate", "check": "none"}


@pytest.fixture
def env(tmp_path, monkeypatch):
    log = tmp_path / "log.jsonl"
    monkeypatch.setenv("LEARNINGOS_ISSUE_LOG", str(log))
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "MTH-X.json").write_text(
        json.dumps(
            {
                "archetypes": [
                    {"archetypeKey": "x-basic", "level": 1},
                    {"archetypeKey": "x-model", "level": 4, "levelNote": "how it earns L4"},
                    {"archetypeKey": "x-weak", "level": 4},
                    {"archetypeKey": "x-untried", "level": 3},
                ]
            }
        )
    )
    data = tmp_path / "data" / "MTH-X"
    data.mkdir(parents=True)
    (data / "DRL-MTH-X-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-X-01",
                "problems": [
                    {"archetypeKey": "x-basic", "level": 1},
                    {"archetypeKey": "x-model", "level": 4, "blindSolve": L4_TAGS},
                    {"archetypeKey": "x-weak", "level": 2, "blindSolve": L2_TAGS},
                ],
            }
        )
    )
    issues.add_issue("level", "batch", "gate", "MTH-X/x-weak", "blind solve reached L2", action="dropped")
    return str(vault), str(tmp_path / "data")


def _rows(rep):
    return {r["key"]: r for r in rep["rows"]}


def test_evidence_and_flags(env):
    rep = vr.unit_report("MTH-X", *env)
    rows = _rows(rep)
    assert rows["x-basic"]["earned"] == 1 and rows["x-basic"]["flag"] == ""
    assert rows["x-model"]["earned"] == 1 and rows["x-model"]["flag"] == ""
    assert rows["x-weak"] == {**rows["x-weak"], "earned": 0, "earnedOther": {2: 1}, "failed": 1, "flag": "FAILING"}
    assert rows["x-untried"]["flag"] == "UNPROVEN"
    assert rep["thin"] == [1, 3]  # one archetype each at L1 and L3


def test_log_gaps_logs_thin_and_failing_once(env):
    rep = vr.unit_report("MTH-X", *env)
    first = vr.log_gaps(rep)
    assert len(first) == 3  # THIN L1, THIN L3, FAILING x-weak
    assert vr.log_gaps(rep) == first  # identical pending records are not duplicated
    assert "x-weak" in vr.format_report(rep) and "FAILING" in vr.format_report(rep)


def test_report_runs_on_every_real_vault():
    assert vr.main([]) == 0
