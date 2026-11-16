"""Regression coverage for the logged drill-content issues in batch fix/drill-content-batch."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def drill(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def question(data, qid):
    return next(problem for problem in data["problems"] if problem["id"] == qid)


def test_math_hints_are_format_only_and_explain_integer_domain():
    complex_drill = drill("drills/data/MTH-T02-C01-U01/DRL-MTH-T02-C01-U01-03.json")
    for qid in ("Q01", "Q02", "Q03", "Q04", "Q05"):
        hint = question(complex_drill, qid).get("inputHint", "")
        assert hint
        assert any(word in hint.lower() for word in ("number", "real", "integer"))

    rational_drill = drill("drills/data/MTH-T02-C01-U03/DRL-MTH-T02-C01-U03-01.json")
    assert question(rational_drill, "Q06")["inputHint"] == "Enter an integer."


def test_domain_range_checkpoint_hints_are_process_checks():
    data = drill("drills/data/MTH-T02-C02-U02/DRL-MTH-T02-C02-U02-01.json")
    for qid in ("Q02", "Q03", "Q07", "Q08"):
        hint = question(data, qid)["checkpointHint"].lower()
        assert any(word in hint for word in ("review", "reread", "confirm"))
        assert not any(word in hint for word in ("vertex", "radicand", "candidate", "model"))
        assert not any(char.isdigit() for char in hint)


def test_domain_range_traps_model_the_actual_misconceptions():
    data = drill("drills/data/MTH-T02-C02-U02/DRL-MTH-T02-C02-U02-01.json")
    numerator_zero_trap = question(data, "Q01")
    assert numerator_zero_trap["trapDerivation"] == "0 - 5"
    assert numerator_zero_trap["trapValue"] == "-5"

    extraneous_root_trap = question(data, "Q06")
    assert extraneous_root_trap["trapDerivation"] == "2 + 3 + 4 + 6 + 7 + 8"
    assert extraneous_root_trap["trapValue"] == "30"


def test_open_top_box_question_uses_corner_cutout_figure():
    data = drill("drills/data/MTH-T02-C02-U02/DRL-MTH-T02-C02-U02-01.json")
    q08 = question(data, "Q08")
    figure = q08["figure"]
    assert "figureWaiver" not in q08
    assert figure["title"] == "Rectangular Sheet for an Open-Top Box"
    assert len(figure["shapes"]) == 2
    assert figure["shapes"][1]["strokeDasharray"] == "4 3"
    assert [label["text"] for label in figure["labels"]] == ["14 in", "8 in", "x"]


def test_copy_prompt_matches_shallow_copy_contract_in_hidden_tests():
    data = drill("drills/data/PRG-T01-C01-U02/DRL-PRG-T01-C01-U02-01.json")
    prompt = question(data, "Q03")["prompt"].lower()
    assert prompt.count("shallow defensive copy") == 2
    assert prompt.count("nested object references are shared") == 2


def test_trace_prompt_says_to_return_array_literal_without_running_snippet():
    data = drill("drills/data/PRG-T01-C01-U03/DRL-PRG-T01-C01-U03-01.json")
    prompt = question(data, "Q01")["prompt"].lower()
    assert "without running it" in prompt
    assert "array literal" in prompt


def test_module_shape_matches_visible_fixtures():
    data = drill("drills/data/PRG-T01-C01-U05/DRL-PRG-T01-C01-U05-01.json")
    prompt = question(data, "Q03")["prompt"]
    assert "exports:" not in prompt
    assert "deps: string[]" in prompt
    assert "topLevelReads:" in prompt
