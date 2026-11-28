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


def _write_drill(workspace, *problems):
    data_root, _, _ = workspace
    directory = data_root / UNIT
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{DRILL}.json").write_text(
        json.dumps({"drillId": DRILL, "unitCode": UNIT, "problems": problems}), encoding="utf-8"
    )


def _story_parent():
    return _reviewed_parent() | {
        "id": "Q01",
        "context": "A story for this test.",
        "contextCheck": {"verdict": "ok", "note": "Parent context fixture."},
    }


def _reviewed_variant():
    proposed = render_radical_problem(NEW_PARAMETERS)
    proposed["blindSolve"] = _reviewed_parent()["blindSolve"] | {"answer": proposed["answerPlain"]}
    proposed["review"] = {"verdict": "pass", "note": "Checked the variant independently."}
    return proposed


def _bank_draft(problem):
    archetype = problem["archetypeKey"]
    variant = problem | {"variantId": f"VAR-{UNIT}-{archetype}-99", "sourceArchetype": archetype}
    return {"unitCode": UNIT, "variants": [variant]}


@pytest.mark.parametrize("parent_kind", ["drill", "variant"])
def test_add_records_own_certificate_and_rechecks_saved_instance(parent_kind, workspace, cached_sources):
    if parent_kind == "drill":
        _write_drill(workspace, _reviewed_parent() | {"id": "Q01"})
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

    variant_bank.save_bank(UNIT, {"variants": []})
    story_id = _add(_story_parent())["variants"][0]["variantId"]
    with pytest.raises(variant_bank.VariantBankError, match="independent context check and review"):
        _add(_request(story_id, NEW_PARAMETERS))


@pytest.mark.parametrize("explicit_parent", [False, True])
def test_removed_story_requires_full_context_check_and_review(workspace, explicit_parent):
    story = _story_parent()
    _write_drill(workspace, story)
    plain = render_radical_problem(NEW_PARAMETERS)
    if explicit_parent:
        plain["parentProblem"] = f"{DRILL}/Q01"

    assert any(
        "Changed context has no 'contextCheck'" in e for e in variant_bank.check_variant_bank(_bank_draft(plain))
    )
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
    assert len(saved["variants"]) == 1
    assert "parameterInstance" not in saved["variants"][-1]


def test_changed_story_without_parent_needs_fresh_context_check(workspace):
    story = _story_parent()
    _write_drill(workspace, story)
    variant = _reviewed_variant() | {"context": "A different story."}
    with pytest.raises(variant_bank.VariantBankError, match="Changed context has no 'contextCheck'"):
        _add(variant)
    variant["contextCheck"] = story["contextCheck"]
    assert any(
        "own independent context check and review" in e for e in variant_bank.check_variant_bank(_bank_draft(variant))
    )
    with pytest.raises(variant_bank.VariantBankError, match="own independent context check and review"):
        _add(variant)


@pytest.mark.parametrize("parent_qid", ["Q99", "Q02", "Q03"])
def test_explicit_parent_must_exist_and_match_pair(workspace, parent_qid):
    story = _story_parent()
    _write_drill(
        workspace,
        story,
        story | {"id": "Q02", "level": 4},
        story | {"id": "Q03", "archetypeKey": "another-archetype"},
    )
    variant = _reviewed_variant() | {"parentProblem": f"{DRILL}/{parent_qid}"}
    with pytest.raises(variant_bank.VariantBankError, match="'parentProblem'.*same archetype and level"):
        _add(variant)


@pytest.mark.parametrize("with_story", [False, True])
def test_unchanged_context_allowed_with_implicit_parent(workspace, with_story):
    parent = _story_parent() if with_story else _reviewed_parent() | {"id": "Q01"}
    _write_drill(workspace, parent)
    variant = _reviewed_variant()
    if with_story:
        variant.update(context=parent["context"], contextCheck=parent["contextCheck"])
    assert variant_bank.check_variant_bank(_bank_draft(variant)) == []
    assert len(_add(variant)["variants"]) == 1


def test_ambiguous_parent_requires_full_context_check(workspace):
    plain_parent = render_radical_problem(PARAMETERS | {"b": 7, "c": 3}) | {"id": "Q02"}
    _write_drill(workspace, _story_parent(), plain_parent)
    variant = _reviewed_variant()
    with pytest.raises(variant_bank.VariantBankError, match="Changed context has no 'contextCheck'"):
        _add(variant)
    assert len(_add(variant | {"parentProblem": f"{DRILL}/Q02"})["variants"]) == 1


def test_stored_legacy_variant_is_grandfathered_but_new_entries_are_checked(workspace):
    legacy = _bank_draft(_reviewed_variant())
    variant_bank.save_bank(UNIT, legacy)
    _write_drill(workspace, _story_parent())
    assert variant_bank.check_variant_bank(legacy) == []

    new = _reviewed_variant() | {"context": "A different story."}
    with pytest.raises(variant_bank.VariantBankError, match="Changed context has no 'contextCheck'"):
        _add(new)
    assert variant_bank.load_bank(UNIT) == legacy
