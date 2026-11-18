"""Hermetic tests for choice prompt option-duplication gate (07 §4)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from code_engine.ai_drill_ingest import (
    AiContractError as CodeAiContractError,
)
from code_engine.ai_drill_ingest import (
    check_code_drill,
    ingest_ai_code_drill,
    register_code_archetype,
    validate_ai_code_contract,
)
from math_engine.ai_drill_ingest import (
    AiContractError as MathAiContractError,
)
from math_engine.ai_drill_ingest import (
    check_ai_drill,
    ingest_ai_drill,
    register_archetype,
    validate_ai_problem_contract,
)
from quality_rules import find_choice_prompt_option_duplicates

ROOT = Path(__file__).resolve().parents[1]


def _math_choice_problem(**overrides) -> dict:
    prob = {
        "id": "Q01",
        "level": 1,
        "category": "Core Skill",
        "form": "direct",
        "archetype": "problem-solving",
        "archetypeKey": "t02-c03-u03-interpret-scatter-pattern",
        "context": "",
        "prompt": (
            "The observations are: $x=0$ gives $y=15$; $x=2$ gives $y=12$; "
            "$x=4$ gives $y=9$; $x=6$ gives $y=6$. "
            "Which description best fits the scatter pattern as the input increases?"
        ),
        "display": "\\text{Choose the overall direction and shape of the point cloud.}",
        "plainText": "Choose the overall direction and shape of the point cloud.",
        "givens": {"x1": 0, "y1": 15, "x2": 2, "y2": 12, "x3": 4, "y3": 9, "x4": 6, "y4": 6},
        "constants": {},
        "trapGivens": [15, 6, 6, 0],
        "answerSpec": {
            "type": "choice",
            "options": [
                {"id": "A", "label": "A roughly linear downward trend"},
                {
                    "id": "B",
                    "label": "A roughly linear upward trend",
                    "provenance": "Reverses the overall direction of the association.",
                },
                {
                    "id": "C",
                    "label": "A curved trend",
                    "provenance": "Treats steady change as a curved pattern.",
                },
                {
                    "id": "D",
                    "label": "No clear trend",
                    "provenance": "Overlooks the consistent direction across the observations.",
                },
            ],
            "correct": "A",
        },
        "answerPlain": "A",
        "answerDisplay": "A",
        "inputHint": "Choose the description that matches the overall point pattern.",
        "commonTrapTag": "t02-c03-u03-reverse-trend-direction-trap",
        "trapDerivation": "(15-6)/(6-0)",
        "verify": {"source": "(6-15)/(6-0)", "trapValue": "3/2"},
        "checkpointHint": "Track whether the outputs tend to rise or fall as the inputs increase.",
        "references": ["MTH-T02-C03-U03"],
        "figureWaiver": "Scatter table is given directly.",
        "steps": [
            {"latex": "15>12", "explain": "The first outputs decrease as inputs increase.", "eq": ["15-12", "3"]},
            {"latex": "\\text{roughly linear downward trend}", "explain": "The pattern decreases steadily."},
        ],
        "verificationLevel": "partial",
        "review": {"verdict": "pass", "note": "Clean prompt without duplicated options."},
    }
    prob.update(overrides)
    return prob


def _seed_math_vault(vault_dir: Path) -> None:
    register_archetype(
        "MTH-T02-C03-U03",
        {
            "archetypeKey": "t02-c03-u03-interpret-scatter-pattern",
            "unitCode": "MTH-T02-C03-U03",
            "name": "Interpret Scatter Pattern",
            "level": 1,
            "cognitiveTraps": ["t02-c03-u03-reverse-trend-direction-trap"],
            "figureNone": "Test vault entry.",
        },
        vault_dir=str(vault_dir),
    )


def _prg_choice_problem(**overrides) -> dict:
    prob = {
        "id": "Q01",
        "level": 1,
        "category": "Core Skill",
        "archetype": "problem-solving",
        "codeType": "implement",
        "archetypeKey": "prg-choice-test",
        "commonTrapTag": "off-by-one-status",
        "context": "http_gateway_status",
        "entryPoint": "classifyGatewayStatus",
        "prompt": "Implement `classifyGatewayStatus(code)` and determine which HTTP category applies for `502`.",
        "inputHint": "Return the status category label.",
        "starterCode": "function classifyGatewayStatus(_code) {\n  return '';\n}\nmodule.exports = { classifyGatewayStatus };\n",
        "solutionCode": (
            "function classifyGatewayStatus(code) {\n"
            "  return code >= 500 ? 'server-error' : 'other';\n"
            "}\n"
            "module.exports = { classifyGatewayStatus };\n"
        ),
        "visibleTests": [
            {
                "name": "classifies 502 as server-error and 200 as other",
                "testCode": (
                    "assert.strictEqual(classifyGatewayStatus(502), 'server-error');\n"
                    "assert.strictEqual(classifyGatewayStatus(200), 'other');\n"
                ),
            }
        ],
        "hiddenTests": [
            {
                "name": "classifies 500 boundary as server-error",
                "testCode": "assert.strictEqual(classifyGatewayStatus(500), 'server-error');\n",
            }
        ],
        "examples": [
            {"input": "502", "output": "'server-error'", "call": "classifyGatewayStatus(502)"},
            {"input": "200", "output": "'other'", "call": "classifyGatewayStatus(200)"},
        ],
        "trapMutant": (
            "function classifyGatewayStatus(code) {\n"
            "  return code > 500 ? 'server-error' : 'other';\n"
            "}\n"
            "module.exports = { classifyGatewayStatus };\n"
        ),
        "answerSpec": {
            "type": "choice",
            "options": [
                {"id": "A", "label": "Upstream server failure"},
                {"id": "B", "label": "Client authorization error", "provenance": "Confuses 5xx with 4xx."},
                {"id": "C", "label": "Redirect response", "provenance": "Confuses 5xx with 3xx."},
            ],
            "correct": "A",
        },
        "answerPlain": "A",
        "answerDisplay": "A",
        "steps": [{"explain": "Status codes 500-599 indicate server-side failures."}],
        "verificationLevel": "partial",
    }
    prob.update(overrides)
    return prob


@pytest.mark.parametrize(
    "bad_prompt",
    [
        "The observations show $x=0, y=15; x=2, y=12; x=4, y=9; x=6, y=6$. Which trend fits? Choose one: A, roughly linear downward; B, roughly linear upward; C, curved; D, no clear trend.",
        "A fitted line is $f(x)=x-5$ on inputs $1$ to $8$. Predict at $9$. Choose the prediction type: A, interpolation; B, extrapolation; C, cannot classify.",
        "Which pattern fits $x=0, y=15; x=2, y=12; x=4, y=9; x=6, y=6$? (A) roughly linear downward (B) roughly linear upward (C) curved",
        "Which pattern fits $x=0, y=15; x=2, y=12; x=4, y=9; x=6, y=6$? A) downward B) upward C) curved",
        "Given $x=0, y=15; x=2, y=12; x=4, y=9; x=6, y=6$, is it a roughly linear downward trend, a roughly linear upward trend, or a curved trend?",
        "Given $x=0, y=15; x=2, y=12; x=4, y=9; x=6, y=6$, Options: A. downward; B. upward.",
    ],
)
def test_math_contract_rejects_choice_prompt_listing_options(bad_prompt: str) -> None:
    prob = _math_choice_problem(prompt=bad_prompt)
    with pytest.raises(MathAiContractError, match=r"answerSpec\.options"):
        validate_ai_problem_contract(prob)


def test_math_contract_accepts_clean_choice_and_find_the_flaw() -> None:
    clean = _math_choice_problem()
    assert validate_ai_problem_contract(clean) is True

    flaw_prob = {
        "id": "Q05",
        "level": 3,
        "verificationLevel": "partial",
        "givens": {"a": 6, "b": 1, "c": 5, "d": 2, "e": 3},
        "constants": {},
        "prompt": (
            "A student simplified $6\\frac{1}{5} - 2\\frac{3}{5}$ step by step:\n"
            "Line 1: $6\\frac{1}{5} - 2\\frac{3}{5} = (5 + \\frac{6}{5}) - (2 + \\frac{3}{5})$\n"
            "Line 2: $= (5 - 2) + (\\frac{6}{5} + \\frac{3}{5})$\n"
            "Line 3: $= 3 + \\frac{9}{5}$\n"
            "Line 4: $= \\frac{24}{5}$\n"
            "Which line is the first one that is wrong?"
        ),
        "display": "6\\frac{1}{5} - 2\\frac{3}{5}",
        "plainText": "(6 + 1/5) - (2 + 3/5)",
        "trapDerivation": "(5 - 2) + (6/5 + 3/5)",
        "verify": {
            "source": "18/5",
            "trapValue": "24/5",
            "flaw": {"values": ["18/5", "24/5", "24/5", "24/5"], "firstWrong": 2},
        },
        "answerSpec": {
            "type": "choice",
            "options": [
                {"id": "1", "label": "Line 1"},
                {"id": "2", "label": "Line 2"},
                {"id": "3", "label": "Line 3"},
                {"id": "4", "label": "Line 4"},
            ],
            "correct": "2",
        },
        "checkpointHint": "Check whether each line keeps the same value as the line above it.",
        "steps": [
            {"latex": "6\\frac{1}{5} - 2\\frac{3}{5} = \\frac{18}{5}", "explain": "Subtract fractions.", "val": "18/5"}
        ],
    }
    assert find_choice_prompt_option_duplicates(flaw_prob) == []
    assert validate_ai_problem_contract(flaw_prob) is True


def test_math_false_positive_guards_on_points_and_numbers() -> None:
    prob = {
        "prompt": "Points A, B, and C lie on a line with $P(A) = 12$ and $P(B) = 18$. Which value is larger?",
        "answerSpec": {
            "type": "choice",
            "options": [{"id": "A", "label": "$12$"}, {"id": "B", "label": "$18$"}],
            "correct": "B",
        },
    }
    assert find_choice_prompt_option_duplicates(prob) == []


def test_math_ingest_and_check_respect_choice_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    vault_dir = tmp_path / "vault"
    _seed_math_vault(vault_dir)

    bad_prob = _math_choice_problem(
        prompt=(
            "The observations are: $x=0$ gives $y=15$; $x=2$ gives $y=12$; "
            "$x=4$ gives $y=9$; $x=6$ gives $y=6$. "
            "Which trend fits? Choose one: A, downward; B, upward; C, curved; D, no clear trend."
        )
    )
    bad_doc = {"unitCode": "MTH-T02-C03-U03", "problems": [bad_prob]}

    errors = check_ai_drill(copy.deepcopy(bad_doc), vault_dir=str(vault_dir))
    assert any("answerSpec.options" in err for err in errors)
    with pytest.raises(MathAiContractError, match=r"answerSpec\.options"):
        ingest_ai_drill(copy.deepcopy(bad_doc), vault_dir=str(vault_dir))
    assert not (tmp_path / "drills" / "data").exists()

    good_doc = {"unitCode": "MTH-T02-C03-U03", "problems": [_math_choice_problem()]}
    assert check_ai_drill(copy.deepcopy(good_doc), vault_dir=str(vault_dir)) == []
    saved = ingest_ai_drill(copy.deepcopy(good_doc), vault_dir=str(vault_dir))
    assert Path(saved["localFilePath"]).exists()


def test_code_contract_and_ingest_reject_choice_prompt_listing_options(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    vault_dir = tmp_path / "code_vault"
    register_code_archetype(
        "PRG-T09-C01-U01",
        {
            "archetypeKey": "prg-choice-test",
            "unitCode": "PRG-T09-C01-U01",
            "name": "Gateway Status Classification",
            "level": 1,
            "cognitiveTraps": [{"trapTag": "off-by-one-status", "description": "Uses > 500 instead of >= 500."}],
            "qualityChecks": [
                {
                    "id": "QC-status-boundary",
                    "check": "Handles 500 boundary inclusively.",
                    "why": "500 is also a server error.",
                    "severity": "must",
                    "knownBad": {
                        "code": "function classify(code) { return code > 500 ? 'server-error' : 'other'; }",
                        "caughtBy": "review",
                    },
                }
            ],
        },
        vault_dir=str(vault_dir),
    )

    clean_prob = _prg_choice_problem()
    assert validate_ai_code_contract(copy.deepcopy(clean_prob)) is True

    bad_prob = _prg_choice_problem(
        prompt=(
            "Implement `classifyGatewayStatus(code)` for `502`. "
            "Choose one: A, Upstream server failure; B, Client authorization error; C, Redirect response."
        )
    )
    with pytest.raises(CodeAiContractError, match=r"answerSpec\.options"):
        validate_ai_code_contract(copy.deepcopy(bad_prob))

    bad_doc = {
        "unitCode": "PRG-T09-C01-U01",
        "environment": "node-vanilla",
        "blindSolve": [
            {
                "problemId": "Q01",
                "solutionCode": (
                    "function classifyGatewayStatus(code) {\n"
                    "  if (code >= 500) return 'server-error';\n"
                    "  return 'other';\n"
                    "}\n"
                    "module.exports = { classifyGatewayStatus };\n"
                ),
                "ambiguous": False,
                "note": "Blind solve.",
            }
        ],
        "review": {"verdict": "pass", "note": "Pass."},
        "problems": [bad_prob],
    }
    errors = check_code_drill(copy.deepcopy(bad_doc), vault_dir=str(vault_dir))
    assert any("answerSpec.options" in err for err in errors)
    with pytest.raises(CodeAiContractError, match=r"answerSpec\.options"):
        ingest_ai_code_drill(copy.deepcopy(bad_doc), vault_dir=str(vault_dir))
    assert not (tmp_path / "drills" / "data").exists()


def test_all_committed_choice_drills_do_not_duplicate_options_in_prompt() -> None:
    offenders = []
    for path in sorted((ROOT / "drills" / "data").glob("*/*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for prob in doc.get("problems", []):
            dups = find_choice_prompt_option_duplicates(prob)
            if dups:
                offenders.append(f"{path.name} {prob.get('id')}: {dups}")
    assert offenders == []
