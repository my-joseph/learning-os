"""Q6 legacy variant quarantine: serving exclusion, coverage exclusion, reverify gate, vault_report notice, and add_variants warnings."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from math_engine import variant_bank
from scripts import drill_review, vault_report

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / ".claude" / "skills" / "new-math-drill" / "template"
QUARANTINED_UNITS = {
    "MTH-T02-C02-U05": 6,
    "MTH-T02-C03-U03": 12,
    "MTH-T02-C04-U05": 15,
}


def test_repo_legacy_variants_marked_quarantined_and_excluded_from_selectors() -> None:
    total = 0
    for unit, expected_count in QUARANTINED_UNITS.items():
        path = ROOT / "drills" / "variants" / f"{unit}.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        variants = doc["variants"]
        assert len(variants) == expected_count
        for var in variants:
            assert var["status"] == "quarantined"
            assert "#338" in var["quarantineReason"]
            assert var["since"] == "2026-11-27"
            # Python find_variant skips quarantined variants by default.
            assert variant_bank.find_variant(var["variantId"]) is None
            assert variant_bank.find_variant(var["variantId"], include_quarantined=True) is not None
            total += 1

        # Scope loader skips all quarantined variants by default.
        assert variant_bank._load_scope_variants([unit]) == []
        assert variant_bank.count_quarantined_variants(unit) == expected_count

        # vault_report surfaces the Quarantined variants line.
        rep = vault_report.unit_report(unit, log=str(ROOT / "nonexistent-log.jsonl"))
        assert rep["quarantinedVariants"] == expected_count
        txt = vault_report.format_report(rep)
        assert f"Quarantined variants: {expected_count}" in txt
        assert f"--reverify {unit}" in txt

    assert total == 33


def test_quarantined_variants_do_not_count_toward_coverage_gate_or_drill_review(tmp_path: Path) -> None:
    unit = "MTH-T99-C01-U01"
    data_root = tmp_path / "drills" / "data"
    variants_dir = tmp_path / "drills" / "variants"
    (data_root / unit).mkdir(parents=True)
    variants_dir.mkdir(parents=True)
    baseline_path = tmp_path / variant_bank.COVERAGE_BASELINE_PATH
    baseline_path.parent.mkdir(parents=True)
    baseline_path.write_text("{}", encoding="utf-8")

    drill_doc = {
        "drillId": f"DRL-{unit}-01",
        "unitCode": unit,
        "problems": [{"id": "Q01", "archetypeKey": "arch-a", "level": 2}],
    }
    (data_root / unit / f"DRL-{unit}-01.json").write_text(json.dumps(drill_doc), encoding="utf-8")

    # 3 quarantined variants for arch-a@L2 must NOT satisfy coverage >= 3.
    q_vars = [
        {
            "variantId": f"VAR-{unit}-arch-a-0{i}",
            "archetypeKey": "arch-a",
            "sourceArchetype": "arch-a",
            "level": 2,
            "status": "quarantined",
            "quarantineReason": "pre-distractor-provenance gate; parent drill retired in #338",
            "since": "2026-11-27",
        }
        for i in (1, 2, 3)
    ]
    (variants_dir / f"{unit}.json").write_text(json.dumps({"unitCode": unit, "variants": q_vars}), encoding="utf-8")

    cov = variant_bank.compute_drill_coverage(drill_doc, variants_dir=str(variants_dir))
    assert cov["coveredPairs"] == 0
    assert cov["pairs"][0]["variantCount"] == 0

    passed, gate_report = variant_bank.check_coverage_gate(tmp_path)
    assert not passed
    assert "have 0, need 3 more" in gate_report

    # drill_review._similar_variants_for_missed must also skip quarantined variants.
    missed = drill_review._similar_variants_for_missed(
        [{"qid": "Q01", "outcome": "wrong", "archetypeKey": "arch-a", "level": 2}],
        {},
        unit,
        str(variants_dir),
    )
    assert missed[0]["availableAtLevel"] == 0
    assert missed[0]["unattemptedAtLevel"] == 0
    assert missed[0]["totalForArchetype"] == 0


def test_reverify_lists_passing_and_failing_and_apply_unquarantines_only_passing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    tpl = json.loads((TEMPLATE_DIR / "draft.json").read_text(encoding="utf-8"))
    unit = tpl["unitCode"]
    variants_dir = tmp_path / "variants"
    variants_dir.mkdir()
    empty_data = tmp_path / "data"
    empty_data.mkdir()

    # 1. Passing L1 variant (quarantined)
    good_v = copy.deepcopy(tpl["problems"][0])
    good_v["variantId"] = f"VAR-{unit}-{good_v['archetypeKey']}-01"
    good_v["id"] = good_v["variantId"]
    good_v["sourceArchetype"] = good_v["archetypeKey"]
    good_v["status"] = "quarantined"
    good_v["quarantineReason"] = "legacy check"
    good_v["since"] = "2026-11-27"

    # 2. Failing L2 variant (quarantined, only 3 steps + missing review)
    bad_v = copy.deepcopy(tpl["problems"][1])
    bad_v["variantId"] = f"VAR-{unit}-{bad_v['archetypeKey']}-01"
    bad_v["id"] = bad_v["variantId"]
    bad_v["sourceArchetype"] = bad_v["archetypeKey"]
    bad_v["steps"] = bad_v["steps"][:3]
    bad_v["steps"][-1]["val"] = "8"
    bad_v.pop("review", None)
    bad_v["status"] = "quarantined"
    bad_v["quarantineReason"] = "legacy check"
    bad_v["since"] = "2026-11-27"

    bank_file = variants_dir / f"{unit}.json"
    bank_file.write_text(json.dumps({"unitCode": unit, "variants": [good_v, bad_v]}), encoding="utf-8")

    # Dry-run reverify lists both and mutates nothing.
    rep = variant_bank.reverify_quarantined_variants(
        unit,
        variants_dir=str(variants_dir),
        data_root=str(empty_data),
        vault_dir=str(TEMPLATE_DIR),
        check_originality=False,
        apply=False,
    )
    assert rep["quarantinedTotal"] == 2
    assert [x["variantId"] for x in rep["passing"]] == [good_v["variantId"]]
    assert [x["variantId"] for x in rep["failing"]] == [bad_v["variantId"]]
    assert rep["applied"] is False
    assert variant_bank.count_quarantined_variants(unit, variants_dir=str(variants_dir)) == 2

    # Apply un-quarantines ONLY the passing variant and leaves the failing one quarantined.
    rep_apply = variant_bank.reverify_quarantined_variants(
        unit,
        variants_dir=str(variants_dir),
        data_root=str(empty_data),
        vault_dir=str(TEMPLATE_DIR),
        check_originality=False,
        apply=True,
    )
    assert rep_apply["applied"] is True
    assert rep_apply["unquarantined"] == [good_v["variantId"]]
    assert variant_bank.count_quarantined_variants(unit, variants_dir=str(variants_dir)) == 1
    assert variant_bank.find_variant(good_v["variantId"], variants_dir=str(variants_dir)) is not None
    assert variant_bank.find_variant(bad_v["variantId"], variants_dir=str(variants_dir)) is None

    # CLI --reverify runs read-only and formats output cleanly.
    monkeypatch.setenv("VARIANTS_DIR", str(variants_dir))
    monkeypatch.setenv("DRILLS_DATA_DIR", str(empty_data))
    monkeypatch.setenv("REASONING_VAULT_DIR", str(TEMPLATE_DIR))
    rc = variant_bank.main(["--reverify", unit, "--no-originality"])
    assert rc == 0
    out = capsys.readouterr().out
    assert f"Reverify {unit}: 0/1 quarantined variant(s) pass current gates, 1 failing." in out
    assert bad_v["variantId"] in out


def test_add_variants_library_call_prints_distractor_provenance_warnings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Q5 follow-up: add_variants() called directly prints distractor-provenance warnings like ingest_ai_drill()."""
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    (vault_dir / "MTH-T02-C01-U01.json").write_text(
        json.dumps(
            {
                "unitCode": "MTH-T02-C01-U01",
                "archetypes": [
                    {
                        "archetypeKey": "t02-c01-u01-power-periodicity",
                        "unitCode": "MTH-T02-C01-U01",
                        "name": "Periodic Powers",
                        "level": 2,
                        "governingRelation": "(1 + i)^2 = 2i",
                        "cognitiveTraps": [
                            "t02-c01-u01-report-reduced-exponent-trap",
                            "t02-c01-u01-assume-period-four-trap",
                        ],
                        "figureNone": "Symbolic.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    variants_dir = tmp_path / "variants"
    variants_dir.mkdir()
    var = {
        "level": 2,
        "category": "Core Skill",
        "form": "choose",
        "archetype": "problem-solving",
        "archetypeKey": "t02-c01-u01-power-periodicity",
        "context": "",
        "prompt": "Find the positive integer $n$ for which $(1 + i)^n = 16$.",
        "display": "(1 + i)^n = 16",
        "givens": {"one": 1, "t": 16},
        "constants": {"two": 2},
        "trapGivens": [16, 2],
        "answerSpec": {
            "type": "choice",
            "options": [
                {
                    "id": "A",
                    "label": "$2$",
                    "trapTag": "t02-c01-u01-assume-period-four-trap",
                    "provenance": "Assumed a cycle of four directly from powers of i.",
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
        },
        "answerPlain": "C",
        "answerDisplay": "C",
        "inputHint": "Choose one option.",
        "commonTrapTag": "t02-c01-u01-report-reduced-exponent-trap",
        "trapDerivation": "log(16)/log(2)",
        "trapValue": "4",
        "verify": {"source": "8", "trapValue": "4"},
        "checkpointHint": "Square the base first and track the factor in front of the imaginary unit.",
        "references": ["MTH-T02-C01-U01"],
        "verificationLevel": "partial",
        "steps": [
            {"latex": "(1 + i)^2 = 2i", "explain": "Square the base first.", "eq": ["(1 + I)**2", "2*I"]},
            {"latex": "(1 + i)^n = (2i)^m", "explain": "Rewrite with $n = 2m$."},
            {"latex": "2^m = 16", "explain": "Match magnitudes so $m = 4$.", "eq": ["2**4", "16"]},
            {"latex": "n = 8", "explain": "Double $m$ to recover $n$.", "eq": ["(1 + I)**8", "16"]},
        ],
        "review": {"verdict": "pass", "note": "Verified choice variant."},
    }

    variant_bank.add_variants(
        {"unitCode": "MTH-T02-C01-U01", "variants": [var]},
        variants_dir=str(variants_dir),
        data_root=str(tmp_path / "empty_data"),
        vault_dir=str(vault_dir),
    )
    out = capsys.readouterr().out
    assert "WARNING:" in out
    assert "unverifiable" in out
