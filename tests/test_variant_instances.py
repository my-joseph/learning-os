"""Regression coverage for the numbers-only Similar authoring path."""

import copy
import json

import pytest

from math_engine import variant_bank
from math_engine.variant_instances import render_radical_problem

UNIT = "MTH-T02-C01-U03"
DRILL = f"DRL-{UNIT}-99"
PARAMETERS = {"a": 2, "b": 5, "d": 8, "c": 2}
NEW_PARAMETERS = PARAMETERS | {"b": 7}


def _reviewed_parent() -> dict:
    problem = render_radical_problem(PARAMETERS)
    problem["review"] = {"verdict": "pass", "note": "Independently checked parent fixture."}
    problem["blindSolve"] = {
        "answer": problem["answerPlain"],
        "ambiguous": False,
        "setup": "given",
        "strategy": "prescribed",
        "check": "edge",
        "edgeRejected": "The lower candidate has a negative right side.",
        "task": "compute",
        "reverse": False,
        "steps": 8,
    }
    return problem


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    data_root, variants_dir, sources = (tmp_path / name for name in ("data", "variants", "sources"))
    monkeypatch.setenv("DRILLS_DATA_DIR", str(data_root))
    monkeypatch.setenv("VARIANTS_DIR", str(variants_dir))
    monkeypatch.setenv("LEARNINGOS_SOURCES_DIR", str(sources))
    return data_root, variants_dir, sources


@pytest.fixture
def cached_sources(workspace):
    _, _, sources = workspace
    index = sources / "_index"
    index.mkdir(parents=True)
    rel_path = "demo/example.pdf"
    (index / "pdf_example.json").write_text(
        json.dumps({"relPath": rel_path, "pages": [{"page": 1, "text": "Evaluate the area of a rectangle."}]}),
        encoding="utf-8",
    )
    (index / f"located_{UNIT}.json").write_text(
        json.dumps({"matches": [{"relPath": rel_path, "cacheFile": "pdf_example.json", "pages": [1]}]}),
        encoding="utf-8",
    )
    return sources


def _add(*items):
    return variant_bank.add_variants({"unitCode": UNIT, "variants": list(items)})


def _request(parent, parameters):
    return {"parameterInstance": {"parent": parent, "parameters": parameters}}


def _bank_parent():
    return _add(_reviewed_parent())["variants"][0]["variantId"]


@pytest.mark.parametrize("parent_kind", ["drill", "variant"])
def test_add_records_own_certificate_and_rechecks_saved_instance(parent_kind, workspace, cached_sources):
    if parent_kind == "drill":
        data_root, _, _ = workspace
        directory = data_root / UNIT
        directory.mkdir(parents=True)
        parent = _reviewed_parent() | {"id": "Q01"}
        (directory / f"{DRILL}.json").write_text(
            json.dumps({"drillId": DRILL, "unitCode": UNIT, "problems": [parent]}),
            encoding="utf-8",
        )
        parent_id = f"{DRILL}/Q01"
    else:
        parent_id = _bank_parent()

    bank = _add(_request(parent_id, NEW_PARAMETERS))
    saved = variant_bank.load_bank(UNIT)
    assert saved == bank
    child = saved["variants"][-1]
    assert child["parameterInstance"] == {
        "parent": parent_id,
        "parameters": NEW_PARAMETERS,
        "family": "radical-equation-v1",
        "note": f"parameter instance of {parent_id}, invariants certified",
    }
    assert "blindSolve" not in child and "review" not in child
    assert variant_bank.check_variant_bank(saved, check_originality=True, sources_dir=str(cached_sources)) == []

    for field, value in (
        ("context", "A changed story."),
        ("steps", child["steps"][:-2]),
        ("answerSpec", {"type": "number", "value": "1"}),
        ("review", _reviewed_parent()["review"]),
    ):
        altered = copy.deepcopy(saved)
        altered["variants"][-1][field] = value
        assert any("certified numbers-only content" in err for err in variant_bank.check_variant_bank(altered))

    # The same numbers or answer cannot be appended again.
    with pytest.raises(variant_bank.VariantBankError, match="independent blind solve and review"):
        _add(_request(parent_id, NEW_PARAMETERS))
    assert variant_bank.load_bank(UNIT) == saved


@pytest.mark.parametrize(
    ("parameters", "failed_check"),
    [
        (PARAMETERS | {"d": 0}, "denominator is zero"),
        ({"a": 4, "b": 11, "d": 3, "c": 3}, "Candidate rejection changed"),  # both roots satisfy the original
        ({"a": 4, "b": 6, "d": 2, "c": 2}, "repeated candidate"),
        ({"a": 2, "b": 7, "d": 3, "c": 3}, "canonical answer form changed"),
        (PARAMETERS | {"d": 1}, "clearing step trivial"),
        ({"a": 8, "b": 26, "d": 2, "c": 2}, "collapses the solution steps"),
        ({"a": 4, "b": 10, "d": 16, "c": 2}, "A common factor"),
    ],
    ids=[
        "zero-denominator",
        "extraneous-becomes-valid",
        "repeated-root",
        "answer-form",
        "shortcut",
        "step-collapse",
        "cancellation",
    ],
)
def test_number_changes_rejected_from_cheap_path(workspace, cached_sources, parameters, failed_check):
    parent = _bank_parent()
    before = variant_bank.load_bank(UNIT)
    with pytest.raises(variant_bank.VariantBankError, match=f"{failed_check}.*independent blind solve and review"):
        _add(_request(parent, parameters))
    assert variant_bank.load_bank(UNIT) == before


def test_requires_originality_to_run_and_pass(workspace, monkeypatch):
    parent = _bank_parent()
    before = variant_bank.load_bank(UNIT)
    with pytest.raises(variant_bank.VariantBankError, match="Originality gate skipped"):
        _add(_request(parent, NEW_PARAMETERS))

    monkeypatch.setattr(variant_bank, "check_document_originality", lambda *a, **kw: (["Originality violation"], None))
    with pytest.raises(variant_bank.VariantBankError, match="Originality violation"):
        _add(_request(parent, NEW_PARAMETERS))
    assert variant_bank.load_bank(UNIT) == before


def test_context_and_inherited_records_are_ineligible(workspace, cached_sources):
    parent_id = _bank_parent()
    with pytest.raises(variant_bank.VariantBankError, match="only its parent and parameters"):
        _add(_request(parent_id, NEW_PARAMETERS) | {"context": "A new story."})

    bank = variant_bank.load_bank(UNIT)
    bank["variants"][0].pop("review")
    variant_bank.save_bank(UNIT, bank)
    with pytest.raises(variant_bank.VariantBankError, match="Needs 'review'.*independent blind solve and review"):
        _add(_request(parent_id, NEW_PARAMETERS))

    story = _reviewed_parent() | {
        "context": "A story for this test.",
        "contextCheck": {"verdict": "ok", "note": "Parent context fixture."},
    }
    variant_bank.save_bank(UNIT, {"variants": []})
    story_id = _add(story)["variants"][0]["variantId"]
    with pytest.raises(variant_bank.VariantBankError, match="independent context check and review"):
        _add(_request(story_id, NEW_PARAMETERS))

    plain = render_radical_problem(NEW_PARAMETERS) | {"parentProblem": story_id}
    with pytest.raises(variant_bank.VariantBankError, match="no 'contextCheck'"):
        _add(plain)
    plain["contextCheck"] = {"verdict": "ok", "note": "Checked the plain wording for remaining assumptions."}
    with pytest.raises(variant_bank.VariantBankError, match="Needs 'review'"):
        _add(plain)
    plain["review"] = story["review"]
    with pytest.raises(variant_bank.VariantBankError, match="own independent context check and review"):
        _add(plain)
    plain["review"] = {"verdict": "pass", "note": "Checked the new plain item."}
    with pytest.raises(variant_bank.VariantBankError, match="needs a 'blindSolve'"):
        _add(plain)
    plain["blindSolve"] = _reviewed_parent()["blindSolve"] | {"answer": plain["answerPlain"]}
    saved = _add(plain)
    assert len(saved["variants"]) == 2
    assert "parameterInstance" not in saved["variants"][-1]
