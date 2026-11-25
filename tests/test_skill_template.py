"""The new-math-drill draft template must always pass every gate, so agents can copy its shapes."""

import json
import os
import shutil

import pytest

from math_engine.ai_drill_ingest import AiContractError, check_ai_drill, ingest_ai_drill, main

TEMPLATE_DIR = os.path.join(".claude", "skills", "new-math-drill", "template")


def _draft():
    with open(os.path.join(TEMPLATE_DIR, "draft.json"), encoding="utf-8") as f:
        return json.load(f)


def test_template_passes_check():
    assert check_ai_drill(_draft(), vault_dir=TEMPLATE_DIR) == []


def test_template_ingests(tmp_path):
    vault = tmp_path / "vault"
    shutil.copytree(TEMPLATE_DIR, vault)
    saved = ingest_ai_drill(_draft(), data_root=str(tmp_path / "data"), vault_dir=str(vault))
    assert [p["level"] for p in saved["problems"]] == [1, 2, 3, 4]
    assert os.path.exists(saved["localFilePath"])


@pytest.mark.parametrize(
    "explain",
    [
        r"Use $i^2 = -1$ and keep $z \neq 0$.",
        r"Subtract $\$5$ from the total.",
        "I use a substitution in this equation because it is simpler.",
        "In Line 1, use a 3D diagram. A diagram doesn't change the result.",
    ],
)
def test_step_math_accepts_formatted_math_and_english(explain):
    draft = _draft()
    draft["problems"][0]["steps"][0]["explain"] = explain
    assert check_ai_drill(draft, vault_dir=TEMPLATE_DIR) == []


@pytest.mark.parametrize(
    ("explain", "token"),
    [
        ("Factor out i.", "i"),
        ("In this equation, substitute $w$ for z.", "z"),
        ("Keep the sign ^ as written.", "^"),
        ("Evaluate x^2.", "x"),
        ("Replace the coefficient with -1.", "-1"),
        ("Divide both sides by 12.", "12"),
        ("Subtract 2n.", "2n"),
        ("Use k_1.", "k_1"),
        ("Name the coefficient a.", "coefficient a"),
        ("Solve for a.", "Solve for a"),
        ("Subtract a - A.", "a - A"),
        ("Set a = $n$.", "="),
        (r"Compare $x$ and \$z\$.", "z"),
        *[(f"Use the symbol {symbol}.", symbol) for symbol in "≠≤≥±√"],
    ],
)
def test_step_math_reports_unformatted_notation(explain, token):
    draft = _draft()
    draft["problems"][0]["steps"][0]["explain"] = explain
    assert check_ai_drill(draft, vault_dir=TEMPLATE_DIR) == [
        f"[Q01] Step 1 explanation contains {token!r} outside $...$. Use inline math."
    ]


@pytest.mark.parametrize("configured_root", [None, "other-data"])
def test_step_math_grandfathers_saved_files_in_cli_check(tmp_path, monkeypatch, capsys, configured_root):
    draft = _draft()
    draft["problems"][0]["steps"][0]["explain"] = "Factor out x."
    draft["drillId"] = f"DRL-{draft['unitCode']}-01"
    monkeypatch.setenv("REASONING_VAULT_DIR", os.path.abspath(TEMPLATE_DIR))
    if configured_root:
        monkeypatch.setenv("DRILLS_DATA_DIR", configured_root)
    else:
        monkeypatch.delenv("DRILLS_DATA_DIR", raising=False)
    monkeypatch.chdir(tmp_path)

    saved_dir = tmp_path / (configured_root or "drills/data") / draft["unitCode"]
    saved_dir.mkdir(parents=True)
    saved_path = saved_dir / f"{draft['drillId']}.json"
    draft_path = tmp_path / saved_path.name
    raw = json.dumps(draft)
    saved_path.write_text(raw, encoding="utf-8")
    draft_path.write_text(raw, encoding="utf-8")

    assert main(["--ingest-file", str(saved_path), "--check", "--no-originality"]) == 0
    assert "Step 1 explanation" not in capsys.readouterr().out
    assert saved_path.read_text(encoding="utf-8") == raw
    assert main(["--ingest-file", str(draft_path), "--check", "--no-originality"]) == 1
    assert "[Q01] Step 1 explanation" in capsys.readouterr().out


def test_step_math_rejects_new_ingest_without_check(tmp_path):
    draft = _draft()
    draft["problems"][0]["steps"][0]["explain"] = "Factor out x."
    with pytest.raises(AiContractError, match=r"\[Q01\] Step 1 explanation"):
        ingest_ai_drill(draft, data_root=str(tmp_path / "data"), vault_dir=TEMPLATE_DIR)
    assert not (tmp_path / "data").exists()
