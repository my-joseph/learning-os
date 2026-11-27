"""Q5 gate visibility: originality skip summaries, distractor-provenance warnings on ingest, and orphaned variant banks."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from math_engine import ai_drill_ingest, variant_bank

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / ".claude" / "skills" / "new-math-drill" / "template"


def _seed_prose_warning_vault(vault_dir: Path) -> Path:
    vault_dir.mkdir(parents=True, exist_ok=True)
    vault = {
        "unitCode": "MTH-T02-C01-U01",
        "archetypes": [
            {
                "archetypeKey": "t02-c01-u01-power-periodicity",
                "unitCode": "MTH-T02-C01-U01",
                "name": "Periodic Powers of a Simple Complex Number",
                "level": 2,
                "governingRelation": "(1 + i)^2 = 2i",
                "cognitiveTraps": [
                    "t02-c01-u01-report-reduced-exponent-trap",
                    "t02-c01-u01-assume-period-four-trap",
                ],
                "figureNone": "Symbolic complex power simplification.",
            }
        ],
    }
    (vault_dir / "MTH-T02-C01-U01.json").write_text(json.dumps(vault), encoding="utf-8")
    return vault_dir


def _prose_choice_problem() -> dict:
    return {
        "id": "Q01",
        "level": 2,
        "category": "Core Skill",
        "form": "choose",
        "archetype": "problem-solving",
        "archetypeKey": "t02-c01-u01-power-periodicity",
        "context": "",
        "prompt": "Find the positive integer $n$ for which $(1 + i)^n = 256$.",
        "display": "(1 + i)^n = 256",
        "givens": {"one": 1, "t": 256},
        "constants": {"two": 2},
        "trapGivens": [256, 2],
        "answerSpec": {
            "type": "choice",
            "options": [
                {
                    "id": "A",
                    "label": "$4$",
                    "trapTag": "t02-c01-u01-assume-period-four-trap",
                    "provenance": "Assumed a cycle of four without squaring first.",
                },
                {
                    "id": "B",
                    "label": "$8$",
                    "trapTag": "t02-c01-u01-report-reduced-exponent-trap",
                    "provenance": "log(256)/log(2)",
                },
                {"id": "C", "label": "$16$"},
            ],
            "correct": "C",
        },
        "answerPlain": "C",
        "answerDisplay": "C",
        "inputHint": "Choose one option.",
        "commonTrapTag": "t02-c01-u01-report-reduced-exponent-trap",
        "trapDerivation": "log(256)/log(2)",
        "trapValue": "8",
        "verify": {"source": "16", "trapValue": "8"},
        "checkpointHint": "Square the base first and track the factor in front of the imaginary unit.",
        "references": ["MTH-T02-C01-U01"],
        "verificationLevel": "partial",
        "steps": [
            {"latex": "(1 + i)^2 = 2i", "explain": "Square the base first.", "eq": ["(1 + I)**2", "2*I"]},
            {"latex": "(1 + i)^n = (2i)^m", "explain": "Group factors in pairs with $n = 2m$."},
            {"latex": "2^m = 256", "explain": "Match magnitudes so $m = 8$.", "eq": ["2**8", "256"]},
            {"latex": "n = 16", "explain": "Double the paired exponent to recover $n$.", "eq": ["(1 + I)**16", "256"]},
        ],
        "review": {"verdict": "pass", "note": "Verified choice problem with prose distractor provenance."},
    }


def test_ai_drill_check_summary_and_report_expose_originality_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    draft_src = json.loads((TEMPLATE_DIR / "draft.json").read_text(encoding="utf-8"))
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(draft_src), encoding="utf-8")
    missing_sources = tmp_path / "no-such-sources"
    empty_sources = tmp_path / "empty-sources"
    empty_sources.mkdir()

    monkeypatch.setenv("REASONING_VAULT_DIR", str(TEMPLATE_DIR))

    # 1. Missing sources dir -> final summary line states skip count and reason.
    rc = ai_drill_ingest.main(
        [
            "--unit",
            draft_src["unitCode"],
            "--ingest-file",
            str(draft_path),
            "--check",
            "--sources-dir",
            str(missing_sources),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    last_line = out.strip().splitlines()[-1]
    assert "originality skipped (1/1 drill skipped:" in last_line
    assert "sources directory not found" in last_line

    # 2. Empty sources dir (no cached pages) -> summary line states skip count and reason.
    rc2 = ai_drill_ingest.main(
        [
            "--unit",
            draft_src["unitCode"],
            "--ingest-file",
            str(draft_path),
            "--check",
            "--sources-dir",
            str(empty_sources),
        ]
    )
    assert rc2 == 0
    last_line2 = capsys.readouterr().out.strip().splitlines()[-1]
    assert "originality skipped (1/1 drill skipped:" in last_line2
    assert "no cached located source pages" in last_line2

    # 3. --no-originality -> summary line still discloses the skip explicitly.
    rc3 = ai_drill_ingest.main(
        ["--unit", draft_src["unitCode"], "--ingest-file", str(draft_path), "--check", "--no-originality"]
    )
    assert rc3 == 0
    last_line3 = capsys.readouterr().out.strip().splitlines()[-1]
    assert "originality skipped (1/1 drill skipped: disabled by --no-originality)" in last_line3

    # 4. Structured API report preserves originality skip status.
    rep = ai_drill_ingest.check_ai_drill_report(
        copy.deepcopy(draft_src), vault_dir=str(TEMPLATE_DIR), sources_dir=str(empty_sources)
    )
    assert rep["errors"] == []
    assert rep["originality"]["status"] == "skipped"
    assert rep["originality"]["skippedDrills"] == 1
    assert "no cached located source pages" in rep["originality"]["reason"]


def test_originality_summary_counts_skipped_drills_and_variant_banks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data_root = tmp_path / "drills" / "data"
    variants_dir = tmp_path / "drills" / "variants"
    sources_dir = tmp_path / "sources"
    index_root = sources_dir / "_index"
    index_root.mkdir(parents=True)

    # Create 2 drills (U01 indexed, U02 unindexed) and 2 variant banks (U01 indexed, U02 unindexed).
    for unit, did in (("MTH-T99-C01-U01", "DRL-MTH-T99-C01-U01-01"), ("MTH-T99-C01-U02", "DRL-MTH-T99-C01-U02-01")):
        udir = data_root / unit
        udir.mkdir(parents=True)
        (udir / f"{did}.json").write_text(
            json.dumps({"drillId": did, "unitCode": unit, "problems": []}), encoding="utf-8"
        )
    variants_dir.mkdir(parents=True)
    (variants_dir / "MTH-T99-C01-U01.json").write_text(
        json.dumps({"unitCode": "MTH-T99-C01-U01", "variants": [{"variantId": "V1"}, {"variantId": "V2"}]}),
        encoding="utf-8",
    )
    (variants_dir / "MTH-T99-C01-U02.json").write_text(
        json.dumps(
            {
                "unitCode": "MTH-T99-C01-U02",
                "variants": [{"variantId": "V3"}, {"variantId": "V4"}, {"variantId": "V5", "status": "quarantined"}],
            }
        ),
        encoding="utf-8",
    )

    # Index one cached source page for U01 only (located_<UNIT>.json + pdf cache).
    (index_root / "pdf_demo.json").write_text(
        json.dumps({"relPath": "demo/book.pdf", "pages": [{"page": 1, "text": "Complex numbers sample text."}]}),
        encoding="utf-8",
    )
    (index_root / "located_MTH-T99-C01-U01.json").write_text(
        json.dumps(
            {
                "unitCode": "MTH-T99-C01-U01",
                "matches": [{"relPath": "demo/book.pdf", "cacheFile": "pdf_demo.json", "pages": [{"page": 1}]}],
            }
        ),
        encoding="utf-8",
    )

    summary = ai_drill_ingest.summarize_originality_skips(
        tmp_path, sources_dir=str(sources_dir), data_root=str(data_root), variants_dir=str(variants_dir)
    )
    assert summary["drills"]["total"] == 2
    assert summary["drills"]["checked"] == 1
    assert summary["drills"]["skipped"] == 1
    assert summary["drills"]["skippedIds"] == ["DRL-MTH-T99-C01-U02-01"]
    assert summary["variantBanks"]["total"] == 2
    assert summary["variantBanks"]["checked"] == 1
    assert summary["variantBanks"]["skipped"] == 1
    assert summary["variantBanks"]["variantsSkipped"] == 2
    assert summary["variantBanks"]["variantsChecked"] == 2
    assert summary["variantBanks"]["variantsQuarantined"] == 1
    text = ai_drill_ingest.format_originality_summary(summary)
    assert "Drills: 1/2 checked, 1/2 skipped" in text
    assert "Variant banks: 1/2 checked, 1/2 skipped (2/5 variants skipped)" in text
    assert "quarantine: 1 variant(s)" in text
    assert "no cached located source pages" in text

    # CLI --originality-summary --json runs cleanly with missing sources dir.
    rc = ai_drill_ingest.main(["--originality-summary", "--json", "--sources-dir", str(tmp_path / "absent")])
    assert rc == 0
    cli_data = json.loads(capsys.readouterr().out)
    assert cli_data["sourcesDirExists"] is False
    assert cli_data["drills"]["skipped"] == cli_data["drills"]["total"]


def test_ingest_and_variant_bank_preserve_distractor_provenance_warnings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    vault_dir = _seed_prose_warning_vault(tmp_path / "vault")
    data_root = tmp_path / "drills_data"
    variants_dir = tmp_path / "variants"
    variants_dir.mkdir()
    empty_sources = tmp_path / "empty_sources"
    empty_sources.mkdir()

    # 1. ingest_ai_drill prints distractor provenance WARNING (does not drop it).
    prob = _prose_choice_problem()
    draft = {"unitCode": "MTH-T02-C01-U01", "problems": [copy.deepcopy(prob)]}
    ai_drill_ingest.ingest_ai_drill(
        draft,
        data_root=str(data_root),
        vault_dir=str(vault_dir),
        variants_dir=str(variants_dir),
        warn_coverage=False,
    )
    ingest_out = capsys.readouterr().out
    assert "WARNING:" in ingest_out
    assert "unverifiable" in ingest_out

    # 2. variant_bank --add and --check preserve distractor provenance WARNING and show originality skip in summary.
    var = copy.deepcopy(prob)
    var["prompt"] = "Find the positive integer $n$ for which $(1 + i)^n = 16$."
    var["display"] = "(1 + i)^n = 16"
    var["givens"] = {"one": 1, "t": 16}
    var["trapGivens"] = [16, 2]
    var["answerSpec"] = {
        "type": "choice",
        "options": [
            {
                "id": "A",
                "label": "$2$",
                "trapTag": "t02-c01-u01-assume-period-four-trap",
                "provenance": "Assumed period four directly from the imaginary unit cycle.",
            },
            {
                "id": "B",
                "label": "$4$",
                "trapTag": "t02-c01-u01-report-reduced-exponent-trap",
                "provenance": "log(16)/log(2)",
            },
            {"id": "C", "label": "$8$"},
        ],
        "correct": "C",
    }
    var["trapDerivation"] = "log(16)/log(2)"
    var["trapValue"] = "4"
    var["verify"] = {"source": "8", "trapValue": "4"}
    var["steps"] = [
        {"latex": "(1 + i)^2 = 2i", "explain": "Square the base first.", "eq": ["(1 + I)**2", "2*I"]},
        {"latex": "(1 + i)^n = (2i)^m", "explain": "Rewrite with $n = 2m$."},
        {"latex": "2^m = 16", "explain": "Match magnitudes so $m = 4$.", "eq": ["2**4", "16"]},
        {"latex": "n = 8", "explain": "Double $m$ to obtain $n$.", "eq": ["(1 + I)**8", "16"]},
    ]
    var_draft_path = tmp_path / "var_draft.json"
    var_draft_path.write_text(json.dumps({"unitCode": "MTH-T02-C01-U01", "variants": [var]}), encoding="utf-8")

    monkeypatch.setenv("REASONING_VAULT_DIR", str(vault_dir))
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_root))
    monkeypatch.setenv("VARIANTS_DIR", str(variants_dir))

    rc_add = variant_bank.main(["--add", str(var_draft_path)])
    assert rc_add == 0
    add_out = capsys.readouterr().out
    assert "WARNING:" in add_out
    assert "unverifiable" in add_out

    rc_chk = variant_bank.main(["--check", "MTH-T02-C01-U01", "--sources-dir", str(empty_sources)])
    assert rc_chk == 0
    chk_out = capsys.readouterr().out
    assert "WARNING:" in chk_out
    assert "unverifiable" in chk_out
    last_line = chk_out.strip().splitlines()[-1]
    assert "originality skipped (1/1 variants skipped:" in last_line
    assert "no cached located source pages" in last_line


def test_orphaned_variant_banks_listing_is_read_only_and_matches_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # 1. Repository check: exact 3 banks / 33 variants after PR #338, zero files deleted.
    repo_report = variant_bank.find_orphaned_variant_banks(ROOT)
    assert repo_report["bankCount"] == 3
    assert repo_report["variantCount"] == 33
    assert repo_report["quarantinedVariantCount"] == 33
    by_unit = {b["unitCode"]: b["variantCount"] for b in repo_report["orphanedBanks"]}
    assert by_unit == {
        "MTH-T02-C02-U05": 6,
        "MTH-T02-C03-U03": 12,
        "MTH-T02-C04-U05": 15,
    }
    for entry in repo_report["orphanedBanks"]:
        assert (ROOT / entry["path"]).is_file()
        assert entry["quarantinedVariantCount"] == entry["variantCount"]

    # Coverage gate output includes the read-only orphan summary without failing.
    passed, gate_report = variant_bank.check_coverage_gate(ROOT)
    assert passed, gate_report
    assert "Orphaned variant banks (read-only): 3 bank(s), 33 variant(s)" in gate_report

    # 2. CLI --orphans [--json] on synthetic repo does not delete files.
    data_root = tmp_path / "drills" / "data"
    variants_dir = tmp_path / "drills" / "variants"
    (data_root / "MTH-T99-C01-U01").mkdir(parents=True)
    variants_dir.mkdir(parents=True)
    (data_root / "MTH-T99-C01-U01" / "DRL-MTH-T99-C01-U01-01.json").write_text(
        json.dumps(
            {
                "drillId": "DRL-MTH-T99-C01-U01-01",
                "unitCode": "MTH-T99-C01-U01",
                "problems": [{"archetypeKey": "k1", "level": 1}],
            }
        ),
        encoding="utf-8",
    )
    active_bank = variants_dir / "MTH-T99-C01-U01.json"
    orphan_bank = variants_dir / "MTH-T99-C01-U02.json"
    active_bank.write_text(
        json.dumps({"unitCode": "MTH-T99-C01-U01", "variants": [{"archetypeKey": "k1", "level": 1}]}), encoding="utf-8"
    )
    orphan_bank.write_text(
        json.dumps(
            {
                "unitCode": "MTH-T99-C01-U02",
                "variants": [{"archetypeKey": "k2", "level": 2}, {"archetypeKey": "k2", "level": 2}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_root))
    monkeypatch.setenv("VARIANTS_DIR", str(variants_dir))

    assert variant_bank.main(["--orphans"]) == 0
    txt_out = capsys.readouterr().out
    assert "1 bank(s), 2 variant(s)" in txt_out
    assert "MTH-T99-C01-U02" in txt_out
    assert orphan_bank.is_file()  # strictly read-only

    assert variant_bank.main(["--orphans", "--json"]) == 0
    json_out = json.loads(capsys.readouterr().out)
    assert json_out["bankCount"] == 1
    assert json_out["variantCount"] == 2
