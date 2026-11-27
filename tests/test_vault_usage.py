"""S4 archetype usage report: current drills/variants vs git history of retired drills."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import vault_report as vr

ROOT = Path(__file__).resolve().parents[1]


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def test_usage_report_separates_active_historical_only_and_unused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Build a tiny isolated git repo with 3 archetypes:
    # - arch-active: present in current drill + variant bank
    # - arch-retired: present in a deleted historical drill only
    # - arch-unused: never served
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")

    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    (vault_dir / "MTH-T99-C01-U01.json").write_text(
        json.dumps(
            {
                "unitCode": "MTH-T99-C01-U01",
                "archetypes": [
                    {"archetypeKey": "arch-active", "unitCode": "MTH-T99-C01-U01", "level": 1},
                    {"archetypeKey": "arch-retired", "unitCode": "MTH-T99-C01-U01", "level": 2},
                    {"archetypeKey": "arch-unused", "unitCode": "MTH-T99-C01-U01", "level": 3},
                ],
            }
        ),
        encoding="utf-8",
    )

    data_unit = tmp_path / "drills" / "data" / "MTH-T99-C01-U01"
    data_unit.mkdir(parents=True)
    retired_drill = data_unit / "DRL-MTH-T99-C01-U01-01.json"
    retired_drill.write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T99-C01-U01-01",
                "unitCode": "MTH-T99-C01-U01",
                "problems": [{"id": "Q01", "archetypeKey": "arch-retired", "level": 2}],
            }
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "add retired drill")

    retired_drill.unlink()
    active_drill = data_unit / "DRL-MTH-T99-C01-U01-02.json"
    active_drill.write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T99-C01-U01-02",
                "unitCode": "MTH-T99-C01-U01",
                "problems": [{"id": "Q01", "archetypeKey": "arch-active", "level": 1}],
            }
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "retire first drill and add active drill")

    variants_dir = tmp_path / "drills" / "variants"
    variants_dir.mkdir(parents=True)
    (variants_dir / "MTH-T99-C01-U01.json").write_text(
        json.dumps(
            {
                "unitCode": "MTH-T99-C01-U01",
                "variants": [
                    {"variantId": "V1", "archetypeKey": "arch-active", "level": 1},
                    {"variantId": "V2", "archetypeKey": "arch-retired", "level": 2, "status": "quarantined"},
                ],
            }
        ),
        encoding="utf-8",
    )

    rep = vr.usage_report(
        "MTH-T99-C01-U01",
        vault_dir=str(vault_dir),
        data_root=str(tmp_path / "drills" / "data"),
        variants_dir=str(variants_dir),
        include_history=True,
        repo_root=str(tmp_path),
    )
    assert rep["archetypeCount"] == 3
    assert rep["activeCount"] == 1
    assert rep["historicalOnlyCount"] == 1
    assert rep["unusedCount"] == 1
    assert rep["everUsedCount"] == 2
    assert rep["unusedKeys"] == ["arch-unused"]
    rows = {r["key"]: r for r in rep["rows"]}
    assert rows["arch-active"]["status"] == "active"
    assert rows["arch-active"]["currentVariantLevels"] == {1: 1}
    assert rows["arch-retired"]["status"] == "historical-only"
    assert rows["arch-retired"]["currentVariantLevels"] == {}  # quarantined excluded
    assert rows["arch-retired"]["historicalDrillLevels"] == {2: 1}
    assert rows["arch-unused"]["status"] == "unused"

    # CLI --usage and --json output (unused listed first).
    monkeypatch.chdir(tmp_path)
    assert (
        vr.main(
            [
                "MTH-T99-C01-U01",
                "--usage",
                "--vault-dir",
                str(vault_dir),
                "--data-root",
                str(tmp_path / "drills" / "data"),
                "--variants-dir",
                str(variants_dir),
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "1/3 active" in out and "2/3 ever-used" in out
    assert out.index("UNUSED") < out.index("HIST-ONLY") < out.index("ACTIVE")

    assert (
        vr.main(
            [
                "MTH-T99-C01-U01",
                "--usage",
                "--no-history",
                "--json",
                "--vault-dir",
                str(vault_dir),
                "--data-root",
                str(tmp_path / "drills" / "data"),
                "--variants-dir",
                str(variants_dir),
            ]
        )
        == 0
    )
    no_hist = json.loads(capsys.readouterr().out)
    assert no_hist["historicalOnlyCount"] == 0
    assert no_hist["unusedCount"] == 2


def test_usage_report_on_real_repo_surfaces_active_and_retired_units() -> None:
    rep_u01 = vr.usage_report("MTH-T02-C01-U01", repo_root=str(ROOT))
    assert rep_u01["archetypeCount"] == 15
    assert rep_u01["activeCount"] == 12
    assert "t02-c01-u01-mixed-operations-chain" in rep_u01["unusedKeys"]

    rep_retired = vr.usage_report("MTH-T02-C02-U05", repo_root=str(ROOT))
    assert rep_retired["activeCount"] == 0
    assert rep_retired["historicalOnlyCount"] >= 2
