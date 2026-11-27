# -*- coding: utf-8 -*-
"""Tests for L2 chain core cards: schema, prompt/commit, fuzzy dedup, gap report, and vault validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from code_engine import quality_checks as qc
from math_engine import source_cores
from math_engine.source_cores import ledger
from scripts import extract_cards_job, source_find, source_gap

UNIT = "MTH-T02-C01-U01"


def _math_card(**overrides: Any) -> dict[str, Any]:
    card: dict[str, Any] = {
        "id": "CORE-CHAIN-TEST-01",
        "unitCode": UNIT,
        "sourceRef": {
            "family": "mathsgenie",
            "file": "mathsgenie/Grade_8/Exam_Questions/complex.pdf",
            "page": 2,
            "item": "Q1",
        },
        "skill": "Divide two complex numbers via conjugate rationalization",
        "reasoningMove": "direct",
        "difficultyDriver": "Conjugate sign flip in denominator",
        "level": 2,
        "traps": [
            {
                "tag": "t02-c01-u01-denominator-conjugate-sign-error-trap",
                "description": "Subtracts instead of adds squares in denominator",
            }
        ],
        "format": {"kind": "expression"},
        "representation": "symbolic",
    }
    card.update(overrides)
    return card


def _valid_math_archetype(**overrides: Any) -> dict[str, Any]:
    arch: dict[str, Any] = {
        "unitCode": UNIT,
        "archetypeKey": "t02-c01-u01-dividing-complex-numbers",
        "level": 2,
        "name": "Dividing Complex Numbers via Conjugate Rationalization",
        "source": "OpenStax Algebra and Trigonometry 2e §2.4",
        "coreConcept": "Multiply numerator and denominator by denominator conjugate.",
        "mentalModel": "Turn a complex denominator into a real sum of squares.",
        "governingRelation": "(a + bi)/(c + di) = ((a + bi)(c - di))/(c^2 + d^2)",
        "cognitiveTraps": [
            {
                "trapTag": "t02-c01-u01-denominator-conjugate-sign-error-trap",
                "description": "Drops minus sign when multiplying conjugate pairs.",
            }
        ],
        "figureNone": "Purely symbolic complex arithmetic.",
    }
    arch.update(overrides)
    return arch


# ---------------------------------------------------------------------------
# 1. Schema & validate_core_card
# ---------------------------------------------------------------------------


def test_schema_includes_chain_move_and_operations_contract() -> None:
    schema = source_cores.load_schema("math")
    assert "chain" in schema["properties"]["reasoningMove"]["enum"]
    assert "chain" in source_cores.REASONING_MOVES

    ops_prop = schema["properties"]["operations"]
    assert ops_prop["type"] == "array"
    assert ops_prop["minItems"] == 2
    assert schema["if"]["properties"]["reasoningMove"]["const"] == "chain"
    assert "operations" in schema["then"]["required"]

    # Existing cards without operations remain valid
    assert source_cores.validate_core_card(_math_card()) == []

    # Valid chain card with >= 2 distinct operations passes
    valid_chain = _math_card(
        id="CORE-CHAIN-OK",
        skill="Multiply two complex factors then divide by a complex denominator",
        reasoningMove="chain",
        operations=["complex-multiply", "complex-divide"],
    )
    assert source_cores.validate_core_card(valid_chain) == []

    # Optional operations on non-chain card passes when >= 2 distinct items
    assert source_cores.validate_core_card(_math_card(operations=["expand", "simplify"])) == []


def test_schema_rejects_chain_without_operations_and_bad_operations() -> None:
    missing_ops = _math_card(reasoningMove="chain")
    errs_missing = source_cores.validate_core_card(missing_ops)
    assert any("operations" in e and "chain" in e for e in errs_missing), errs_missing

    too_short = _math_card(reasoningMove="chain", operations=["complex-divide"])
    errs_short = source_cores.validate_core_card(too_short)
    assert any("operations" in e and "2" in e for e in errs_short), errs_short

    duplicate_ops = _math_card(reasoningMove="chain", operations=["complex-divide", "Complex Divide"])
    errs_dup = source_cores.validate_core_card(duplicate_ops)
    assert any("distinct" in e for e in errs_dup), errs_dup

    blank_op = _math_card(reasoningMove="chain", operations=["complex-multiply", "   "])
    errs_blank = source_cores.validate_core_card(blank_op)
    assert any("operations[1]" in e for e in errs_blank), errs_blank

    # Source-free check covers operations[] too
    src_text = "Question 4. Compute (7 + 2i)(3 - 5i) / (1 + 4i)."
    leaked_ops = _math_card(
        reasoningMove="chain",
        operations=["multiply by 7", "divide by 4"],
    )
    errs_leak = source_cores.validate_core_card(leaked_ops, source_item_text=src_text)
    assert any("operations[" in e and "digit run" in e for e in errs_leak), errs_leak


# ---------------------------------------------------------------------------
# 2. Worker extraction prompt & --commit enforcement
# ---------------------------------------------------------------------------


def test_extract_cards_job_prompt_defines_chain_and_commit_enforces_operations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdir = tmp_path / "sources"
    pdf_path = sdir / "mathsgenie" / "Grade_8" / "complex.pdf"
    pdf_path.parent.mkdir(parents=True)
    pdf_path.write_bytes(b"%PDF-1.4 dummy")

    reg = tmp_path / "sources.md"
    reg.write_text(
        "| Family (under `sources/`) | What it is | Language | Licence / Terms | Allowed use | Priority | Notes |\n"
        "| :--- | :--- | :--- | :--- | :--- | :---: | :--- |\n"
        "| `mathsgenie/` | GCSE worksheets | EN | Free | `cores` | `60` | Math |\n",
        encoding="utf-8",
    )
    backlog = tmp_path / "backlog.md"
    backlog.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        source_find,
        "extract_pdf_pages",
        lambda _src: [{"page": 1, "text": "Simplify complex conjugate product and quotient.", "isImagePage": False}],
    )
    find_res = source_find.find_sources(UNIT, sources_dir=str(sdir), registry_path=str(reg))
    plan = source_find.build_extraction_plan(
        find_res,
        budget_pages=2,
        budget_items=5,
        batch_size=2,
        sources_dir=str(sdir),
        registry_path=str(reg),
        backlog_path=str(backlog),
    )
    page0 = plan["batches"][0]["pages"][0]

    prompt = extract_cards_job.build_worker_prompt(UNIT, 1, sources_dir=str(sdir))
    assert "`chain`" in prompt
    assert "`operations`" in prompt
    assert "multi-relation" in prompt
    assert '"reasoningMove": "chain"' in prompt
    assert '"reasoningMove": "multi-relation"' in prompt

    # --commit rejects chain card missing operations without writing ledger or DONE_FILE
    batch_file = tmp_path / "batch1.jsonl"
    done_file = tmp_path / "batch1.done"
    bad_chain = _math_card(
        id="CORE-BAD-CHAIN",
        reasoningMove="chain",
        sourceRef={"family": page0["family"], "file": page0["relPath"], "page": page0["page"], "item": "Q1"},
    )
    batch_file.write_text(json.dumps(bad_chain) + "\n", encoding="utf-8")
    with pytest.raises(source_cores.CoreCardError, match="operations"):
        extract_cards_job.commit_batch_cards(
            UNIT,
            1,
            str(batch_file),
            sources_dir=str(sdir),
            done_file=str(done_file),
            registry_path=str(reg),
        )
    assert not done_file.exists()
    assert not Path(ledger.ledger_path(sources_dir=str(sdir))).exists()

    # --commit accepts valid chain card with operations
    good_chain = _math_card(
        id="CORE-GOOD-CHAIN",
        skill="Multiply two complex factors then divide by a complex denominator",
        reasoningMove="chain",
        operations=["complex-multiply", "complex-divide"],
        sourceRef={"family": page0["family"], "file": page0["relPath"], "page": page0["page"], "item": "Q1"},
    )
    batch_file.write_text(json.dumps(good_chain) + "\n", encoding="utf-8")
    summary = extract_cards_job.commit_batch_cards(
        UNIT,
        1,
        str(batch_file),
        sources_dir=str(sdir),
        done_file=str(done_file),
        registry_path=str(reg),
    )
    assert summary["cardsAppended"] == 1
    assert done_file.is_file()


# ---------------------------------------------------------------------------
# 3. Fuzzy duplicate rule for chain & operation sets
# ---------------------------------------------------------------------------


def test_chain_vs_single_operation_not_duplicate_despite_inherited_traps() -> None:
    single_divide = _math_card(
        id="CORE-SINGLE-DIV",
        skill="Divide complex numbers via conjugate rationalization",
        reasoningMove="direct",
        traps=[
            {
                "tag": "t02-c01-u01-denominator-conjugate-sign-error-trap",
                "description": "Wrong sign on conjugate denominator",
            }
        ],
    )
    chain_mul_div = _math_card(
        id="CORE-CHAIN-MUL-DIV",
        skill="Multiply complex numbers then divide complex numbers via conjugate rationalization",
        reasoningMove="chain",
        operations=["multiply", "divide"],
        traps=[
            {
                "tag": "t02-c01-u01-denominator-conjugate-sign-error-trap",
                "description": "Wrong sign on conjugate denominator",
            }
        ],
    )

    is_dup, details = source_gap.cards_are_fuzzy_duplicate(chain_mul_div, single_divide)
    assert not is_dup, details
    is_dup_rev, details_rev = source_gap.cards_are_fuzzy_duplicate(single_divide, chain_mul_div)
    assert not is_dup_rev, details_rev

    # Even with same reasoningMove ("direct"), strictly broader operations set is NOT duplicate
    direct_compound = _math_card(
        id="CORE-DIRECT-MUL-DIV",
        skill="Multiply then divide complex numbers via conjugate rationalization",
        reasoningMove="direct",
        operations=["multiply", "divide"],
        traps=single_divide["traps"],
    )
    is_dup_direct, _ = source_gap.cards_are_fuzzy_duplicate(direct_compound, single_divide)
    assert not is_dup_direct

    # 3-op chain strictly containing 2-op chain is NOT duplicate
    chain_three = _math_card(
        id="CORE-CHAIN-3",
        skill="Simplify power of imaginary unit, multiply complex numbers, then divide via conjugate",
        reasoningMove="chain",
        operations=["power-of-i", "multiply", "divide"],
        traps=chain_mul_div["traps"],
    )
    is_dup_superset, _ = source_gap.cards_are_fuzzy_duplicate(chain_three, chain_mul_div)
    assert not is_dup_superset
    is_dup_subset, _ = source_gap.cards_are_fuzzy_duplicate(chain_mul_div, chain_three)
    assert not is_dup_subset

    # Two chain cards with different operation sets sharing a sub-skill trap are NOT duplicate
    chain_add_div = _math_card(
        id="CORE-CHAIN-ADD-DIV",
        skill="Add complex numbers then divide complex numbers via conjugate rationalization",
        reasoningMove="chain",
        operations=["add", "divide"],
        traps=chain_mul_div["traps"],
    )
    is_dup_diff_ops, _ = source_gap.cards_are_fuzzy_duplicate(chain_add_div, chain_mul_div)
    assert not is_dup_diff_ops


def test_two_chain_cards_with_same_operations_are_duplicate() -> None:
    chain_a = _math_card(
        id="CORE-CHAIN-A",
        skill="Multiply two complex binomials then divide by a complex denominator",
        reasoningMove="chain",
        operations=["multiply", "divide"],
        traps=[
            {
                "tag": "t02-c01-u01-denominator-conjugate-sign-error-trap",
                "description": "Wrong denominator sign",
            }
        ],
    )
    chain_b = _math_card(
        id="CORE-CHAIN-B",
        skill="Expand complex product and rationalize the resulting quotient",
        reasoningMove="chain",
        operations=["Multiply", "Divide"],
        traps=[
            {
                "tag": "t02-c01-u01-i-squared-sign-trap",
                "description": "Keeps i squared as positive one",
            }
        ],
    )
    is_dup, details = source_gap.cards_are_fuzzy_duplicate(chain_b, chain_a)
    assert is_dup, details

    # Same operation set in different order is also treated as the same operation set
    chain_reordered = _math_card(
        id="CORE-CHAIN-C",
        skill="Rationalize quotient then multiply by another complex factor",
        reasoningMove="chain",
        operations=["divide", "multiply"],
        traps=chain_a["traps"],
    )
    is_dup_reordered, details_reordered = source_gap.cards_are_fuzzy_duplicate(chain_reordered, chain_a)
    assert is_dup_reordered, details_reordered


# ---------------------------------------------------------------------------
# 4. Gap report chain coverage & warning + vault validator
# ---------------------------------------------------------------------------


def test_gap_report_warns_when_chain_cards_exist_without_l2_chain_archetype(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdir = tmp_path / "sources"
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    monkeypatch.setenv("LEARNINGOS_SOURCES_DIR", str(sdir))

    # Vault has only single-operation archetypes (no operations array)
    vault_file = vault_dir / f"{UNIT}.json"
    vault_payload = {
        "unitCode": UNIT,
        "archetypes": [
            _valid_math_archetype(
                archetypeKey="t02-c01-u01-multiplying-complex-numbers",
                name="Multiplying Complex Numbers",
                coreConcept="Expand binomial products using i^2 = -1.",
                cognitiveTraps=[{"trapTag": "t02-c01-u01-i-squared-sign-trap", "description": "Drops minus on i^2."}],
            ),
            _valid_math_archetype(),
        ],
    }
    vault_file.write_text(json.dumps(vault_payload, indent=2), encoding="utf-8")

    cards = [
        _math_card(
            id="CORE-CHAIN-01",
            skill="Multiply two complex numbers then divide by a complex denominator",
            reasoningMove="chain",
            operations=["multiply", "divide"],
            level=2,
        ),
        _math_card(
            id="CORE-L2-OPS-02",
            skill="Simplify powers of i then subtract complex expressions",
            reasoningMove="direct",
            operations=["power-of-i", "subtract"],
            level=2,
            traps=[{"tag": "t02-c01-u01-i-squared-sign-trap", "description": "Sign flip on i^2"}],
        ),
    ]
    source_cores.save_core_cards(UNIT, cards, sources_dir=str(sdir))

    report = source_gap.build_gap_report(UNIT, vault_dir=str(vault_dir))
    chain_section = report["chainCards"]
    assert chain_section["totalChainCards"] == 2
    assert chain_section["hasL2ChainArchetype"] is False
    assert {c["id"] for c in chain_section["uncoveredCards"]} == {"CORE-CHAIN-01", "CORE-L2-OPS-02"}
    assert chain_section["coveredCards"] == []
    assert any("no L2 chain archetype" in w for w in chain_section["warnings"])
    # Chain cards must not be silently folded into single-operation archetypes
    assert report["matchedCards"] == []

    formatted = source_gap.format_gap_report(report)
    assert "Chain cards not covered by vault archetypes (2/2):" in formatted
    assert "no L2 chain archetype" in formatted
    assert "CORE-CHAIN-01" in formatted
    assert "multiply -> divide" in formatted

    # Adding an L3 chain archetype does NOT silence the missing L2 chain archetype warning
    vault_payload["archetypes"].append(
        _valid_math_archetype(
            archetypeKey="t02-c01-u01-l3-compound",
            level=3,
            name="L3 Compound Multiply and Divide",
            operations=["multiply", "divide"],
        )
    )
    vault_file.write_text(json.dumps(vault_payload, indent=2), encoding="utf-8")
    report_l3 = source_gap.build_gap_report(UNIT, vault_dir=str(vault_dir))
    assert report_l3["chainCards"]["hasL2ChainArchetype"] is False
    assert any("no L2 chain archetype" in w for w in report_l3["chainCards"]["warnings"])
    assert {c["id"] for c in report_l3["chainCards"]["uncoveredCards"]} == {"CORE-CHAIN-01", "CORE-L2-OPS-02"}

    # Adding an L2 chain archetype for multiply+divide covers CORE-CHAIN-01 and clears the L2 warning
    vault_payload["archetypes"].append(
        _valid_math_archetype(
            archetypeKey="t02-c01-u01-chain-multiply-divide",
            level=2,
            name="Chained Complex Multiplication and Division",
            operations=["complex-multiply", "complex-divide"],
        )
    )
    vault_file.write_text(json.dumps(vault_payload, indent=2), encoding="utf-8")
    report_l2 = source_gap.build_gap_report(UNIT, vault_dir=str(vault_dir))
    assert report_l2["chainCards"]["hasL2ChainArchetype"] is True
    assert report_l2["chainCards"]["warnings"] == []
    assert [c["id"] for c in report_l2["chainCards"]["coveredCards"]] == ["CORE-CHAIN-01"]
    assert [c["id"] for c in report_l2["chainCards"]["uncoveredCards"]] == ["CORE-L2-OPS-02"]
    assert "chain" not in report_l2["reasoningMoves"]["cardMovesMissingInVault"]


def test_math_vault_validator_accepts_optional_operations_and_rejects_malformed(tmp_path: Path) -> None:
    arch_with_ops = _valid_math_archetype(
        archetypeKey="t02-c01-u01-chain-mul-div",
        operations=["complex-multiply", "complex-divide"],
    )
    errors, warnings_list = qc.validate_math_archetype(arch_with_ops)
    assert errors == []
    assert warnings_list == []

    # Invalid operations shapes fail validation
    for bad_ops in ([], "multiply, divide", ["multiply", "   "], [123]):
        bad_errs, _ = qc.validate_math_archetype(_valid_math_archetype(operations=bad_ops))
        assert any("operations" in e for e in bad_errs), f"Expected error for operations={bad_ops!r}"

    # End-to-end --check-vaults CLI accepts a vault containing an archetype with operations
    prg_dir = tmp_path / "prg"
    prg_dir.mkdir()
    math_dir = tmp_path / "math"
    math_dir.mkdir()
    (math_dir / f"{UNIT}.json").write_text(
        json.dumps({"unitCode": UNIT, "archetypes": [arch_with_ops]}),
        encoding="utf-8",
    )
    assert qc.main(["--check-vaults", "--vault-dir", str(prg_dir), "--math-vault-dir", str(math_dir)]) == 0
