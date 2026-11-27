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
# 1. Schema, shared normalisation, & validate_core_card
# ---------------------------------------------------------------------------


def test_schema_includes_chain_move_level2_and_operations_contract() -> None:
    schema = source_cores.load_schema("math")
    assert "chain" in schema["properties"]["reasoningMove"]["enum"]
    assert "chain" in source_cores.REASONING_MOVES

    ops_prop = schema["properties"]["operations"]
    assert ops_prop["type"] == "array"
    assert ops_prop["minItems"] == 2
    assert schema["if"]["properties"]["reasoningMove"]["const"] == "chain"
    assert "operations" in schema["then"]["required"]
    assert schema["then"]["properties"]["level"]["const"] == 2

    # Existing cards without operations remain valid
    assert source_cores.validate_core_card(_math_card()) == []

    # Valid L2 chain card with >= 2 distinct operations passes
    valid_chain = _math_card(
        id="CORE-CHAIN-OK",
        skill="Multiply two complex factors then divide by a complex denominator",
        reasoningMove="chain",
        level=2,
        operations=["complex-multiply", "complex-divide"],
    )
    assert source_cores.validate_core_card(valid_chain) == []

    # Optional operations on non-chain card passes when >= 2 distinct normalised items
    assert source_cores.validate_core_card(_math_card(operations=["expand", "simplify"])) == []


def test_schema_rejects_chain_without_operations_wrong_level_and_alias_duplicates() -> None:
    missing_ops = _math_card(reasoningMove="chain")
    errs_missing = source_cores.validate_core_card(missing_ops)
    assert any("operations" in e and "chain" in e for e in errs_missing), errs_missing

    too_short = _math_card(reasoningMove="chain", operations=["complex-divide"])
    errs_short = source_cores.validate_core_card(too_short)
    assert any("operations" in e and "2" in e for e in errs_short), errs_short

    # Chain move must be strictly level == 2 (rejects L1, L3, L4, L5)
    for bad_level in (1, 3, 4, 5):
        errs_lvl = source_cores.validate_core_card(
            _math_card(reasoningMove="chain", level=bad_level, operations=["multiply", "divide"])
        )
        assert any("level" in e and "chain" in e for e in errs_lvl), (
            f"Expected level error for L{bad_level}: {errs_lvl}"
        )

    # Duplicates after normalisation (case, separators, aliases) are rejected
    for dup_ops in (
        ["complex-divide", "Complex Divide"],
        ["multiply", "multiplication"],
        ["multiply", "divide", "division"],
    ):
        errs_dup = source_cores.validate_core_card(_math_card(reasoningMove="chain", operations=dup_ops))
        assert any("duplicate" in e for e in errs_dup), f"Expected duplicate error for {dup_ops}: {errs_dup}"

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


@pytest.mark.parametrize(
    ("op_a", "op_b"),
    [
        ("square", "square root"),
        ("conjugate", "divide via conjugate"),
        ("multiply by i", "divide by i"),
        ("complex binomial add", "complex binomial multiply"),
    ],
)
def test_operation_normalisation_rejects_false_positive_pairs(op_a: str, op_b: str) -> None:
    assert source_cores.normalize_operation(op_a) != source_cores.normalize_operation(op_b)
    assert not source_gap._op_matches(op_a, op_b)
    assert not source_gap._op_matches(op_b, op_a)


def test_operation_normalisation_equates_aliases_and_stopwords() -> None:
    assert source_cores.normalize_operation("multiply") == source_cores.normalize_operation("multiplication")
    assert source_cores.normalize_operation("divide") == source_cores.normalize_operation("division")
    assert source_cores.normalize_operation("power-of-i") == source_cores.normalize_operation("powers of i")
    assert source_gap._op_matches("complex-multiplication", "complex multiply")
    assert source_gap._op_matches("divide by conjugate", "division via conjugate")


# ---------------------------------------------------------------------------
# 2. Worker extraction prompt & --commit enforcement
# ---------------------------------------------------------------------------


def test_extract_cards_job_prompt_defines_chain_boundaries_and_commit_enforces_rules(
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
    assert "rules/06" in prompt
    assert "case-check" in prompt
    assert "diagnose" in prompt
    assert "choosing among taught methods" in prompt
    assert "generalise" in prompt
    assert "NOT `chain`" in prompt

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

    # --commit rejects L3 chain card
    bad_level_chain = _math_card(
        id="CORE-BAD-CHAIN-L3",
        reasoningMove="chain",
        level=3,
        operations=["complex-multiply", "complex-divide"],
        sourceRef={"family": page0["family"], "file": page0["relPath"], "page": page0["page"], "item": "Q1"},
    )
    batch_file.write_text(json.dumps(bad_level_chain) + "\n", encoding="utf-8")
    with pytest.raises(source_cores.CoreCardError, match="level"):
        extract_cards_job.commit_batch_cards(
            UNIT,
            1,
            str(batch_file),
            sources_dir=str(sdir),
            done_file=str(done_file),
            registry_path=str(reg),
        )
    assert not done_file.exists()

    # --commit accepts valid L2 chain card with operations
    good_chain = _math_card(
        id="CORE-GOOD-CHAIN",
        skill="Multiply two complex factors then divide by a complex denominator",
        reasoningMove="chain",
        level=2,
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


def test_two_chain_cards_with_same_normalised_operations_are_duplicate() -> None:
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
    # Alias set ["multiplication", "division"] equals ["multiply", "divide"]
    chain_alias = _math_card(
        id="CORE-CHAIN-ALIAS",
        skill="Expand complex product and rationalize the resulting quotient",
        reasoningMove="chain",
        operations=["multiplication", "division"],
        traps=[
            {
                "tag": "t02-c01-u01-i-squared-sign-trap",
                "description": "Keeps i squared as positive one",
            }
        ],
    )
    is_dup, details = source_gap.cards_are_fuzzy_duplicate(chain_alias, chain_a)
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


def test_gap_report_warns_without_l2_chain_archetype_and_rejects_l1_l3_and_loose_ops(
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

    # Adding an L1 archetype with matching operations must NOT cover the L2 chain card; warning must still fire
    vault_payload["archetypes"].append(
        _valid_math_archetype(
            archetypeKey="t02-c01-u01-l1-not-l2-chain",
            level=1,
            name="L1 Multiply and Divide",
            operations=["multiply", "divide"],
        )
    )
    vault_file.write_text(json.dumps(vault_payload, indent=2), encoding="utf-8")
    report_l1 = source_gap.build_gap_report(UNIT, vault_dir=str(vault_dir))
    assert report_l1["chainCards"]["hasL2ChainArchetype"] is False
    assert any("no L2 chain archetype" in w for w in report_l1["chainCards"]["warnings"])
    assert report_l1["chainCards"]["coveredCards"] == []
    assert {c["id"] for c in report_l1["chainCards"]["uncoveredCards"]} == {"CORE-CHAIN-01", "CORE-L2-OPS-02"}
    assert report_l1["matchedCards"] == []

    # Adding an L3 archetype with matching operations must also NOT cover the L2 chain card; warning still fires
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
    assert report_l3["chainCards"]["coveredCards"] == []
    assert {c["id"] for c in report_l3["chainCards"]["uncoveredCards"]} == {"CORE-CHAIN-01", "CORE-L2-OPS-02"}

    # Adding an L2 chain archetype with alias-equivalent operations covers CORE-CHAIN-01 and clears the L2 warning
    vault_payload["archetypes"].append(
        _valid_math_archetype(
            archetypeKey="t02-c01-u01-chain-multiply-divide",
            level=2,
            name="Chained Complex Multiplication and Division",
            operations=["multiplication", "division"],
        )
    )
    vault_file.write_text(json.dumps(vault_payload, indent=2), encoding="utf-8")
    report_l2 = source_gap.build_gap_report(UNIT, vault_dir=str(vault_dir))
    assert report_l2["chainCards"]["hasL2ChainArchetype"] is True
    assert report_l2["chainCards"]["warnings"] == []
    assert [c["id"] for c in report_l2["chainCards"]["coveredCards"]] == ["CORE-CHAIN-01"]
    assert [c["id"] for c in report_l2["chainCards"]["uncoveredCards"]] == ["CORE-L2-OPS-02"]
    assert "chain" not in report_l2["reasoningMoves"]["cardMovesMissingInVault"]


def test_gap_report_does_not_falsely_cover_distinct_operations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdir = tmp_path / "sources"
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    monkeypatch.setenv("LEARNINGOS_SOURCES_DIR", str(sdir))

    vault_payload = {
        "unitCode": UNIT,
        "archetypes": [
            _valid_math_archetype(
                archetypeKey="t02-c01-u01-chain-square-conjugate",
                level=2,
                name="Square and Conjugate",
                operations=["square", "conjugate"],
            ),
            _valid_math_archetype(
                archetypeKey="t02-c01-u01-chain-mul-i-add",
                level=2,
                name="Multiply by i and Complex Binomial Add",
                operations=["multiply by i", "complex binomial add"],
            ),
        ],
    }
    (vault_dir / f"{UNIT}.json").write_text(json.dumps(vault_payload, indent=2), encoding="utf-8")

    cards = [
        _math_card(
            id="CORE-FALSE-1",
            skill="Take square root then divide via conjugate",
            reasoningMove="chain",
            level=2,
            operations=["square root", "divide via conjugate"],
        ),
        _math_card(
            id="CORE-FALSE-2",
            skill="Divide by i then perform complex binomial multiply",
            reasoningMove="chain",
            level=2,
            operations=["divide by i", "complex binomial multiply"],
        ),
    ]
    source_cores.save_core_cards(UNIT, cards, sources_dir=str(sdir))

    report = source_gap.build_gap_report(UNIT, vault_dir=str(vault_dir))
    assert report["chainCards"]["coveredCards"] == []
    assert {c["id"] for c in report["chainCards"]["uncoveredCards"]} == {"CORE-FALSE-1", "CORE-FALSE-2"}


def test_math_vault_validator_accepts_optional_operations_and_rejects_malformed(tmp_path: Path) -> None:
    arch_with_ops = _valid_math_archetype(
        archetypeKey="t02-c01-u01-chain-mul-div",
        operations=["complex-multiply", "complex-divide"],
    )
    errors, warnings_list = qc.validate_math_archetype(arch_with_ops)
    assert errors == []
    assert warnings_list == []

    # Invalid operations shapes, < 2 items, or duplicates after normalisation fail validation
    for bad_ops in (
        [],
        ["divide"],
        "multiply, divide",
        ["multiply", "   "],
        [123, "divide"],
        ["multiply", "multiplication"],
        ["multiply", "divide", "division"],
    ):
        bad_errs, _ = qc.validate_math_archetype(_valid_math_archetype(operations=bad_ops))
        assert any("operations" in e for e in bad_errs), f"Expected error for operations={bad_ops!r}"

    # End-to-end --check-vaults CLI accepts a vault containing an archetype with valid operations
    prg_dir = tmp_path / "prg"
    prg_dir.mkdir()
    math_dir = tmp_path / "math"
    math_dir.mkdir()
    (math_dir / f"{UNIT}.json").write_text(
        json.dumps({"unitCode": UNIT, "archetypes": [arch_with_ops]}),
        encoding="utf-8",
    )
    assert qc.main(["--check-vaults", "--vault-dir", str(prg_dir), "--math-vault-dir", str(math_dir)]) == 0

    # End-to-end --check-vaults CLI rejects a vault with duplicate-alias operations
    bad_arch = _valid_math_archetype(
        archetypeKey="t02-c01-u01-chain-dup",
        operations=["multiply", "multiplication"],
    )
    (math_dir / f"{UNIT}.json").write_text(
        json.dumps({"unitCode": UNIT, "archetypes": [bad_arch]}),
        encoding="utf-8",
    )
    assert qc.main(["--check-vaults", "--vault-dir", str(prg_dir), "--math-vault-dir", str(math_dir)]) == 1


def test_u01_chain_archetype_covers_prompt_example_and_bare_operations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vault_path = Path(__file__).resolve().parent.parent / "math_engine" / "reasoning_vault" / f"{UNIT}.json"
    vault_data = json.loads(vault_path.read_text(encoding="utf-8"))
    chain_archs = [a for a in vault_data["archetypes"] if a.get("archetypeKey") == "t02-c01-u01-mixed-operations-chain"]
    assert len(chain_archs) == 1
    arch = chain_archs[0]

    errors, warnings_list = qc.validate_math_archetype(arch)
    assert errors == []
    assert warnings_list == []

    # Build a real math extraction prompt and parse its chain example operations
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
    source_find.build_extraction_plan(
        find_res,
        budget_pages=2,
        budget_items=5,
        batch_size=2,
        sources_dir=str(sdir),
        registry_path=str(reg),
        backlog_path=str(backlog),
    )
    prompt = extract_cards_job.build_worker_prompt(UNIT, 1, sources_dir=str(sdir))

    chain_example = None
    for chunk in prompt.split("`"):
        if chunk.startswith("{") and '"reasoningMove": "chain"' in chunk:
            chain_example = json.loads(chunk)
            break
    assert chain_example is not None, "Expected JSON chain example in math worker prompt"

    prompt_card = _math_card(
        reasoningMove="chain",
        level=2,
        operations=chain_example["operations"],
    )
    assert source_gap._archetype_covers_chain_card(prompt_card, arch)

    # Bare operation forms and normalised aliases are all covered
    for ops in (
        ["add", "subtract"],
        ["multiply", "divide"],
        ["power-of-i", "subtract"],
        ["add", "subtract", "multiply", "divide", "power-of-i"],
        ["addition", "subtraction"],
        ["multiplication", "division"],
        ["powers of i", "multiply"],
    ):
        card = _math_card(reasoningMove="chain", level=2, operations=ops)
        assert source_gap._archetype_covers_chain_card(card, arch), f"Expected U01 chain archetype to cover {ops!r}"

    # Out-of-scope operation is not falsely covered
    out_of_scope = _math_card(reasoningMove="chain", level=2, operations=["multiply", "square root"])
    assert not source_gap._archetype_covers_chain_card(out_of_scope, arch)


def test_source_cards_link_is_validated_and_resolves_without_fuzzy_similarity() -> None:
    card = _math_card()
    arch = _valid_math_archetype(
        name="Unrelated feature",
        coreConcept="Unrelated feature",
        cognitiveTraps=["unrelated-feature-trap"],
        sourceCards=[card["id"]],
    )
    assert qc.validate_math_archetype(arch)[0] == []
    matches, unmatched = source_gap._match_cards_to_archetypes(UNIT, [card], [arch], is_prg=False)
    assert not unmatched
    assert matches[0]["matches"][0]["reason"].startswith("explicit sourceCards reference")

    arch["sourceCards"] = [card["id"], card["id"]]
    assert any("sourceCards" in error for error in qc.validate_math_archetype(arch)[0])
    assert any("sourceCards" in error for error in qc.validate_quality_checks(arch))


def test_explicit_chain_link_reports_a_level_and_operations_mismatch() -> None:
    card = _math_card(reasoningMove="chain", level=2, operations=["multiply", "divide"])
    arch = _valid_math_archetype(level=1, sourceCards=[card["id"]])
    matches, unmatched = source_gap._match_cards_to_archetypes(UNIT, [card], [arch], is_prg=False)
    assert not unmatched
    link = matches[0]["matches"][0]
    assert link["sourceCardLink"]
    assert link["score"] < 1
    assert "level differs: card L2, archetype L1" in link["compatibilityWarnings"]
    assert "chain requires an L2 archetype with matching operations" in link["compatibilityWarnings"]


@pytest.mark.parametrize(
    ("move", "level"),
    [
        ("direct", 3),
        ("translate", 1),
        ("reverse", 1),
        ("case-check", 2),
        ("diagnose", 2),
        ("multi-relation", 2),
        ("model", 2),
        ("generalise", 2),
    ],
)
def test_math_card_move_level_bounds(move: str, level: int) -> None:
    errors = source_cores.validate_core_card(_math_card(reasoningMove=move, level=level))
    assert any(error.startswith("level:") for error in errors)


def test_diagnose_card_requires_abstract_flaw_form() -> None:
    card = _math_card(reasoningMove="diagnose", level=3)
    assert any(error.startswith("flawForm:") for error in source_cores.validate_core_card(card))
    card["flawForm"] = "Wrong"
    assert any(error.startswith("flawForm:") for error in source_cores.validate_core_card(card))
    card["flawForm"] = {"step": "Rationalizing the denominator", "error": "Sign"}
    assert any(error.startswith("flawForm.error:") for error in source_cores.validate_core_card(card))
    card["flawForm"]["error"] = "Subtracts the squared imaginary coefficient instead of adding it."
    assert source_cores.validate_core_card(card) == []
    assert any(
        error.startswith("flawForm:") for error in source_cores.validate_core_card({**card, "reasoningMove": "model"})
    )


@pytest.mark.parametrize(("move", "level"), [("model", 4), ("model", 5), ("case-check", 4)])
def test_math_card_accepts_higher_levels_for_eligible_moves(move: str, level: int) -> None:
    assert source_cores.validate_core_card(_math_card(reasoningMove=move, level=level)) == []


def test_load_core_cards_accepts_legacy_bounds_and_missing_flaw_form(tmp_path: Path) -> None:
    legacy = [
        _math_card(reasoningMove="case-check", level=2),
        _math_card(id="CORE-LEGACY-DIAGNOSE", reasoningMove="diagnose", level=3),
    ]
    path = Path(source_cores.cores_path(UNIT, sources_dir=str(tmp_path)))
    path.parent.mkdir()
    path.write_text("".join(json.dumps(card) + "\n" for card in legacy), encoding="utf-8")
    for card in legacy:
        assert source_cores.validate_core_card(card)
        assert source_cores.validate_core_card(card, enforce_move_contract=False) == []
    assert source_cores.load_core_cards(UNIT, sources_dir=str(tmp_path)) == legacy


def test_fuzzy_duplicate_requires_same_level_and_routing() -> None:
    original = _math_card()
    for change in ({"level": 3}, {"laterUnit": "MTH-T02-C01-U02"}, {"unitCode": "MTH-T02-C01-U02"}):
        other = {**original, **change}
        assert not source_gap.cards_are_fuzzy_duplicate(original, other)[0]
        assert not source_gap.cards_are_fuzzy_duplicate(other, original)[0]


def test_fuzzy_duplicate_is_symmetric_with_missing_traps() -> None:
    original = _math_card()
    other = _math_card(traps=[])
    assert source_gap.cards_are_fuzzy_duplicate(original, other) == source_gap.cards_are_fuzzy_duplicate(
        other, original
    )


def test_shared_trap_cannot_duplicate_a_distinct_skill() -> None:
    original = _math_card(skill="Factor")
    other = _math_card(skill="Sum")
    assert not source_gap.cards_are_fuzzy_duplicate(original, other)[0]
