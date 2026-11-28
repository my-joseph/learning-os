"""L2 step floor gate: new L2 math drills and variants need >= 4 real steps; existing items use a shrink-only baseline."""

from __future__ import annotations

import copy
import json
import os
import shutil
from pathlib import Path

import pytest

from math_engine import ai_drill_ingest, variant_bank

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / ".claude" / "skills" / "new-math-drill" / "template"
UNIT = "MTH-T99-C01"
EXISTING_DRILL = f"DRL-{UNIT}-01"
NEW_DRILL = f"DRL-{UNIT}-02"
EXISTING_VARIANT = f"VAR-{UNIT}-arch-01"
NEW_VARIANT = f"VAR-{UNIT}-arch-02"


def _make_steps(count: int) -> list[dict[str, str]]:
    return [{"latex": f"x = {i}", "explain": f"Step {i} transformation."} for i in range(1, count + 1)]


def _write_drill(root: Path, scope: str, drill_id: str, step_count: int, qid: str = "Q02", level: int = 2) -> None:
    scope_dir = root / "drills" / "data" / scope
    scope_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "drillId": drill_id,
        "unitCode": scope,
        "problems": [{"id": qid, "level": level, "steps": _make_steps(step_count)}],
    }
    (scope_dir / f"{drill_id}.json").write_text(json.dumps(doc), encoding="utf-8")


def _write_bank(root: Path, unit: str, variants: list[dict]) -> None:
    vdir = root / "drills" / "variants"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / f"{unit}.json").write_text(json.dumps({"unitCode": unit, "variants": variants}), encoding="utf-8")


@pytest.fixture
def synthetic_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    baseline_path = tmp_path / ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH
    baseline_path.parent.mkdir(parents=True)
    baseline_path.write_text(
        json.dumps({"drills": {EXISTING_DRILL: ["Q02"]}, "variants": {UNIT: [EXISTING_VARIANT]}}),
        encoding="utf-8",
    )
    _write_drill(tmp_path, UNIT, EXISTING_DRILL, step_count=3)
    _write_bank(tmp_path, UNIT, [{"variantId": EXISTING_VARIANT, "level": 2, "steps": _make_steps(3)}])
    return tmp_path


def _template_draft() -> dict:
    return json.loads((TEMPLATE_DIR / "draft.json").read_text(encoding="utf-8"))


def test_repository_l2_step_floor_gate() -> None:
    passed, report = ai_drill_ingest.check_l2_step_floor_gate(ROOT)
    assert passed, report
    assert "drills 13/51 short" in report
    assert "variants 43/147 short" in report
    assert "Baseline: 11 drill(s), 13 problem(s); 11 bank(s), 43 variant(s)." in report
    # Zero-leak: report lists drill/variant IDs only, never prompt/step LaTeX.
    assert "DRL-MTH-T01-C04-01 Q04" in report
    assert "$" not in report


def test_new_draft_and_ingest_reject_short_l2_and_step_padding(tmp_path: Path) -> None:
    draft = _template_draft()
    assert ai_drill_ingest.check_ai_drill(copy.deepcopy(draft), vault_dir=str(TEMPLATE_DIR)) == []

    # 1. Truncating Q02 to 3 real steps fails check_ai_drill and ingest_ai_drill.
    short_draft = copy.deepcopy(draft)
    short_draft["problems"][1]["steps"] = short_draft["problems"][1]["steps"][:3]
    short_draft["problems"][1]["steps"][-1]["val"] = "8"
    errs = ai_drill_ingest.check_ai_drill(copy.deepcopy(short_draft), vault_dir=str(TEMPLATE_DIR))
    assert any("L2 problem has 3 real step(s)" in e for e in errs), errs

    vault = tmp_path / "vault"
    shutil.copytree(TEMPLATE_DIR, vault)
    with pytest.raises(ai_drill_ingest.AiContractError, match="L2 problem has 3 real step"):
        ai_drill_ingest.ingest_ai_drill(short_draft, data_root=str(tmp_path / "data"), vault_dir=str(vault))
    assert not (tmp_path / "data").exists()

    # 2. Padding with repeated identical LaTeX (ignoring whitespace/\left/\right) is rejected.
    padded_dup = copy.deepcopy(short_draft)
    dup_step = copy.deepcopy(padded_dup["problems"][1]["steps"][1])
    dup_step["latex"] = r"\left 4x \right = 32 "
    padded_dup["problems"][1]["steps"].insert(2, dup_step)
    assert ai_drill_ingest.count_real_steps(padded_dup["problems"][1]) == 3
    errs_dup = ai_drill_ingest.check_ai_drill(padded_dup, vault_dir=str(TEMPLATE_DIR))
    assert any("L2 problem has 3 real step(s)" in e for e in errs_dup), errs_dup

    # 3. Padding with a pure restatement of the given display/prompt expression is rejected.
    padded_restate = copy.deepcopy(short_draft)
    padded_restate["problems"][1]["steps"].insert(
        0,
        {"latex": "4x + 7 = 39", "explain": "Start from the given equation."},
    )
    assert ai_drill_ingest.count_real_steps(padded_restate["problems"][1]) == 3
    errs_restate = ai_drill_ingest.check_ai_drill(padded_restate, vault_dir=str(TEMPLATE_DIR))
    assert any("L2 problem has 3 real step(s)" in e for e in errs_restate), errs_restate


def test_count_real_steps_rejects_padding_and_canonical_equivalents() -> None:
    def _prob(steps: list[str], *, display: str = "4x + 7 = 39", prompt: str = "Solve $4x + 7 = 39$.") -> dict:
        return {
            "display": display,
            "prompt": prompt,
            "steps": [{"latex": lx, "explain": f"Transform step {i}."} for i, lx in enumerate(steps, 1)],
        }

    # Genuine simplification steps (arithmetic unevaluated) all count as distinct real steps.
    genuine = _prob(["4x = 39 - 7", "4x = 32", r"x = \frac{32}{4}", "x = 8"])
    assert ai_drill_ingest.count_real_steps(genuine) == 4

    # 1. Non-adjacent repeat (A, B, A, C -> only A, B, C count).
    non_adjacent = _prob(["4x = 39 - 7", "4x = 32", "4x = 39 - 7", "x = 8"])
    assert ai_drill_ingest.count_real_steps(non_adjacent) == 3

    # 2. Leading "=" padding (expression and repeated step).
    leading_eq = _prob(["4x + 7", "= 4x + 7", "4x = 32", "= 4x = 32", "x = 8"], display="", prompt="Simplify $4x + 7$.")
    assert ai_drill_ingest.count_real_steps(leading_eq) == 2  # "4x = 32" and "x = 8" only

    # 3. Extra braces padding (both SymPy-parsed and string-fallback LaTeX).
    extra_braces = _prob(["4x = 39 - 7", "4x = 32", "{4x} = {32}", "{32 = 4x}", "4{x} + {7} = {39}", "{}", "x = 8"])
    assert ai_drill_ingest.count_real_steps(extra_braces) == 3
    fallback_braces = _prob(
        [r"f'(x) = 2x", r"= {f'(x)} = {2x}", r"2x = f'(x)", r"f'(3) = 6"],
        display=r"f(x) = x^2",
        prompt="",
    )
    assert ai_drill_ingest.count_real_steps(fallback_braces) == 2

    # 4. Flipped LHS/RHS of an equation (both against given and against earlier steps).
    flipped = _prob(["39 = 4x + 7", "4x = 39 - 7", "4x = 32", "32 = 4x", "x = 8", "8 = x"])
    assert ai_drill_ingest.count_real_steps(flipped) == 3

    # 5. Commutatively reordered terms / factors (Add and Mul, plus combined flip + reorder).
    reordered = _prob(
        [
            "7 + 4x = 39",
            "39 = 7 + 4x",
            "4x = 39 - 7",
            "4x = -7 + 39",
            "x \\cdot 4 = 32",
            "32 = 4x",
            "x = 8",
        ]
    )
    assert ai_drill_ingest.count_real_steps(reordered) == 3

    # Check end-to-end draft rejection for non-adjacent + canonical padding on Q02.
    draft = _template_draft()
    draft["problems"][1]["steps"] = [
        {"latex": "7 + 4x = 39", "explain": "Reorder the given left-hand side."},
        {"latex": "4x = 39 - 7", "explain": "Subtract $7$ from both sides.", "eq": "4*x - (39 - 7)"},
        {"latex": "32 = {4x}", "explain": "Simplify $39 - 7$ to $32$.", "eq": "4*x - 32"},
        {"latex": "4x = -7 + 39", "explain": "Repeat an earlier non-adjacent step."},
        {"latex": "x = 8", "explain": "Divide both sides by $4$.", "val": "8"},
    ]
    errs = ai_drill_ingest.check_ai_drill(draft, vault_dir=str(TEMPLATE_DIR))
    assert any("L2 problem has 3 real step(s)" in e for e in errs), errs


def test_count_real_steps_keeps_radical_evaluation_distinct() -> None:
    problem = {
        "display": r"x = \sqrt{4}",
        "steps": [
            {"latex": r"\sqrt{4} = x", "explain": "Restate the given equation."},
            {"latex": "x = 2", "explain": "Evaluate the radical."},
        ],
    }
    assert ai_drill_ingest.count_real_steps(problem) == 1


@pytest.mark.parametrize(
    ("earlier", "padding"),
    [
        pytest.param("4x = 32", r"\boxed{4x = 32}", id="boxed"),
        pytest.param("4x = 32", r"\fbox{4x = 32}", id="fbox"),
        pytest.param("x = (39-7)/4", r"x = \frac{39-7}{4}", id="frac-vs-slash"),
        pytest.param(r"x = \frac{32}{4}", r"x = \dfrac{32}{4}", id="dfrac"),
        pytest.param(r"x = \frac{32}{4}", r"x = \tfrac{32}{4}", id="tfrac"),
        pytest.param("4x = 32", r"\begin{aligned}4x &= 32\end{aligned}", id="aligned"),
        pytest.param(
            "4x = 32",
            r"\begin{aligned}4x &= 32 \\ 32 &= 4x\end{aligned}",
            id="two-aligned-rows-repeat-one-line",
        ),
        pytest.param("4x = 32", r"{\fbox{\begin{aligned}&4x = 32\end{aligned}}}", id="braced-aligned"),
        pytest.param("4x = 32", r"\left(4x = 32\right)", id="sized-parentheses"),
        pytest.param("4x = 32", r"\left[4x\right] = 32", id="sized-brackets"),
        pytest.param("4x = 32", r"\left\{4x\right\} = 32", id="sized-braces"),
        pytest.param("4x = 32", r"\left.4x\right. = 32", id="invisible-delimiters"),
        pytest.param("4x = 32", r"\displaystyle \text{so } 4x = 32", id="display-and-text-label"),
        pytest.param("4x = 32", r"\mathrm{therefore}\;\textbf{so}\;4x = 32", id="styled-labels"),
        pytest.param("sin(x) = 0", r"\mathrm{sin}(\textbf{x}) = 0", id="styled-math"),
        pytest.param("4x = 32", "4x = 32.", id="trailing-period"),
        pytest.param("4x = 32", "4x = 32,", id="trailing-comma"),
        pytest.param("4x = 32", "4x = 32;", id="trailing-semicolon"),
        pytest.param("4*x = 32", r"4\cdot x = 32", id="cdot"),
        pytest.param("4x = 32", r"4\times x = 32", id="times"),
        pytest.param("4x = 32", "4*x = 32", id="implicit-multiplication"),
        pytest.param("x = 32/4", r"\boxed{\displaystyle x = \frac{32}{4}}", id="nested-wrappers"),
        pytest.param("4x = 32", r"\boxed{32 = 4x}", id="boxed-equation-flip"),
        pytest.param(r"x = \alpha", r"\boxed{\alpha = x.}", id="unsupported-command-fallback"),
        pytest.param("x = 2, 3", r"\fbox{x = 2, 3;}", id="safe-parse-error-fallback"),
        pytest.param("4x = 32", r"\mathbf{4x = 32}", id="mathbf"),
        pytest.param("4x = 32", r"\mathit{4x} = 32", id="mathit"),
        pytest.param("4x = 32", r"\textit{therefore} 4x = 32", id="textit-label"),
        pytest.param("sin(x) = 0", r"\operatorname{sin}(x) = 0", id="operatorname"),
        pytest.param("4x = 32", r"\bigl(4x\bigr) = 32", id="big-delimiter-sides"),
        pytest.param("4x = 32", r"\Big[4x\Big] = 32", id="Big-delimiters"),
        pytest.param("4x = 32", r"\bigg(4x\bigg) = 32", id="bigg-delimiters"),
        pytest.param("4x = 32", r"\Bigg(4x\Bigg) = 32", id="Bigg-delimiters"),
        pytest.param("4x = 32", r"\Biggl(4x\Biggm.\Biggr) = 32", id="sizing-lrm-and-invisible"),
        pytest.param("4x = 32", r"\textcolor{red}{4x = 32}", id="textcolor"),
        pytest.param("4x = 32", r"{\color{red} 4x = 32}", id="color-declaration"),
        pytest.param("4x = 32", r"\phantom{x = 8}4x = 32", id="phantom"),
        pytest.param("4x = 32", r"4x\hphantom{+1} = 32", id="hphantom"),
        pytest.param("4x = 32", r"4x = 32\vphantom{+1}", id="vphantom"),
        pytest.param("4x = 32", r"4x\ =\ 32", id="backslash-space"),
        pytest.param("4x = 32", r"\scriptstyle 4x = 32", id="scriptstyle"),
        pytest.param("4x = 32", r"\scriptscriptstyle 4x = 32", id="scriptscriptstyle"),
        pytest.param("4x = 32", r"\begin{array}{rcl}4x & = & 32\end{array}", id="array-preamble"),
        pytest.param(
            "4x = 32",
            r"\begin{alignedat*}[t]{2}4x &= 32 \\ 32 &= 4x\end{alignedat*}",
            id="alignedat-position-and-columns",
        ),
        pytest.param("4x = 32", r"\begin{matrix}4x &= 32 \\ 32 &= 4x\end{matrix}", id="other-environment"),
        pytest.param("4x = 32", r"\mathsf{\mathit{4x} = 32}", id="nested-font-wrappers"),
        pytest.param("4x = 32", r"\customstyle{4x = 32}\customspace", id="unlisted-wrapper-and-bare-command"),
        pytest.param("4x = 32", r"4x\hspace*{1em} = 32", id="spacing-length"),
        pytest.param("4x = 32", r"4x = 32\tag*{1}", id="equation-tag"),
        pytest.param(r"x = \alpha", r"\textcolor{blue}{\mathbf{\alpha = x}}", id="wrapped-symbol-fallback"),
        pytest.param("4x = 32", r"\phantom{32 = 4x}", id="invisible-only-row"),
        pytest.param("z = 2i", r"z = 2\mathrm{i}", id="styled-imaginary-unit"),
        pytest.param("4x = 32", "4x~=~32", id="tex-tie-spacing"),
        pytest.param("4x = 32", r"4x\overset{A}{=}32", id="overset-relation"),
        pytest.param("4x = 32", r"4x\underset{A}{=}32", id="underset-relation"),
        pytest.param("4x = 32", r"4x\stackrel{A}{=}32", id="stackrel-relation"),
        pytest.param("4x = 32", r"\underbrace{4x}_{A} = 32", id="underbrace-annotation"),
        pytest.param("4x = 32", r"4x = \overbrace{32}^{A}", id="overbrace-annotation"),
        pytest.param("4x = 32", r"\colorbox{red}{4x = 32}", id="colorbox"),
        pytest.param("4x = 32", r"\fcolorbox{black}{red}{4x = 32}", id="fcolorbox"),
        pytest.param("4x = 32", r"4x\mspace{5mu} = 32", id="mspace"),
        pytest.param("4x = 32", "4\u200bx = 32", id="zero-width-space"),
        pytest.param("4x = 32", "4\u200cx = 32", id="zero-width-non-joiner"),
        pytest.param("4x = 32", "4\u200dx = 32", id="zero-width-joiner"),
        pytest.param("4x = 32", "4\u2060x = 32", id="word-joiner"),
        pytest.param("4x = 32", "4\ufeffx = 32", id="unicode-bom"),
        # Additional probes exercise composition, script token boundaries, and the string fallback.
        pytest.param("4x = 32", r"4x\overset{\text{check}}{\underset{B}{=}}32", id="nested-relation-annotations"),
        pytest.param(r"x \le 3", r"x\underset{\mathrm{bound}}{\le}3", id="annotated-inequality-fallback"),
        pytest.param(
            "4x = 32",
            r"\begin{aligned}32 &\stackrel{\frac{1}{2}}{=} 4x \\ 4x &= 32\end{aligned}",
            id="annotated-flipped-aligned-row",
        ),
        pytest.param("4x = 32", r"\underbrace{\overbrace{4x}^{B}}_{A}=32", id="nested-brace-annotations"),
        pytest.param("4x = 32", r"\underbrace{4x} _ A =32", id="underbrace-single-token"),
        pytest.param("4x = 32", r"4x=\overbrace{32} ^ \alpha", id="overbrace-command-token"),
        pytest.param("4x = 32", "\\bo\u200dxed{4x\u2009=32}", id="unicode-format-inside-command"),
        pytest.param(r"x = \alpha", "\\colorbox{blue}{x~\u2060=\u202f\\alpha}", id="mixed-spacing-fallback"),
        pytest.param(r"x = \alpha", r"{\alpha} = {x}", id="fallback-redundant-equation-side-braces"),
    ],
)
def test_presentation_padding_does_not_count(earlier: str, padding: str) -> None:
    problem = {"steps": [{"latex": latex, "explain": "Show the transformation."} for latex in (earlier, padding)]}
    assert ai_drill_ingest.count_real_steps(problem) == 1


def test_aligned_padding_compares_each_line_with_seen_steps() -> None:
    problem = {
        "display": r"\begin{gathered}4x+7=39 \\ x=(39-7)/4\end{gathered}",
        "prompt": r"Use $\boxed{4x=39-7}$.",
        "steps": [
            {"latex": "4x=32", "explain": "Simplify the difference."},
            {
                "latex": r"\begin{aligned*}4x+7 &=39 \\ 4x &=39-7 \\ 4x &=32 \\ 4x &=32\end{aligned*}",
                "explain": "Repeat the equations.",
            },
            {"latex": r"\textbf{therefore}", "explain": "Add a label."},
        ],
    }
    assert ai_drill_ingest.count_real_steps(problem) == 1


@pytest.mark.parametrize(
    "lines",
    [
        pytest.param((r"x = \frac{32}{4}", "x = 8"), id="fraction-evaluation"),
        pytest.param(("4x = 39-7", "4x = 32"), id="subtraction-evaluation"),
        pytest.param(("2(x+3)", "2x+6"), id="expansion"),
        pytest.param(("4x = 32", r"\boxed{x = 8}"), id="boxed-final-line"),
        pytest.param(("x = 3", r"\left|x\right| = 3"), id="absolute-value-delimiters"),
        pytest.param((r"x = \alpha", r"\boxed{x = \beta}"), id="distinct-string-fallback"),
        pytest.param(("2^5", "32"), id="power-evaluation"),
        pytest.param(("3x+5x", "8x"), id="combining-like-terms"),
        pytest.param((r"\overline{z}", "z"), id="conjugate-overline"),
        pytest.param((r"\overline{z+w}", r"\overline{z}+w"), id="conjugate-group-scope"),
        pytest.param((r"x_{a+b}", r"x_{a}+b"), id="subscript-group-scope"),
        pytest.param((r"\underbrace{x}_{A}", r"\underbrace{x}_{A}^{2}"), id="power-after-underbrace"),
        pytest.param((r"\bar{z}", "z"), id="conjugate-bar"),
        pytest.param((r"\sqrt{x}", "x"), id="symbolic-radical"),
        pytest.param((r"x \le 3", r"x \ge 3"), id="inequality-direction"),
        pytest.param((r"x = 2\cdots", "x = 2*s"), id="ellipsis-command-boundary"),
        pytest.param(
            (r"x_{\mathrm{initial}} = 3", r"x_{\mathrm{final}} = 3"),
            id="math-subscripts",
        ),
        pytest.param(("", r"\begin{align}4x &= 32 \\[2pt] x &= 8\end{align}"), id="new-aligned-lines"),
    ],
)
def test_real_transformations_still_count(lines: tuple[str, str]) -> None:
    problem = {"steps": [{"latex": line, "explain": "Show the transformation."} for line in lines]}
    assert ai_drill_ingest.count_real_steps(problem) == 2


def test_under_labelling_bypass_rejected_at_all_levels() -> None:
    draft = _template_draft()

    # 1. Short L2 reverse item labelled L1 with blindSolve (reverse=True -> demand_level 2 > 1) rejected.
    under_bs = copy.deepcopy(draft)
    p = under_bs["problems"][1]
    p["level"] = 1
    p["form"] = "direct"
    p["steps"] = p["steps"][:3]
    p["steps"][-1]["val"] = "8"
    p["blindSolve"] = {
        "answer": "8",
        "ambiguous": False,
        "setup": "given",
        "strategy": "prescribed",
        "check": "none",
        "task": "compute",
        "reverse": True,
        "steps": 3,
    }
    errs_bs = ai_drill_ingest.check_ai_drill(under_bs, vault_dir=str(TEMPLATE_DIR))
    assert any("under-labelled" in e and "give L2" in e for e in errs_bs), errs_bs

    # 2. L1 item WITHOUT blindSolve using form="reverse" on an L1 archetype is rejected.
    under_form = copy.deepcopy(draft)
    p2 = under_form["problems"][0]
    p2.pop("blindSolve", None)
    p2["level"] = 1
    p2["form"] = "reverse"
    errs_form = ai_drill_ingest.check_ai_drill(under_form, vault_dir=str(TEMPLATE_DIR))
    assert any("under-labelled" in e and "form='reverse'" in e for e in errs_form), errs_form

    # 3. Item WITHOUT blindSolve carrying verify.flaw below L3 is rejected (both L1 and L2, even with form="direct").
    for low_idx, low_level in ((0, 1), (1, 2)):
        under_flaw = copy.deepcopy(draft)
        pf = under_flaw["problems"][low_idx]
        pf.pop("blindSolve", None)
        pf["level"] = low_level
        pf["form"] = "direct"
        pf["verify"] = {**pf.get("verify", {}), "flaw": {"values": ["1", "2", "3", "4"]}}
        errs_flaw = ai_drill_ingest.check_ai_drill(under_flaw, vault_dir=str(TEMPLATE_DIR))
        assert any("verify.flaw" in e and "at least L3" in e for e in errs_flaw), errs_flaw

    # 4. Item WITHOUT blindSolve labelled below its archetype's base level (arch["level"]) is rejected (L1<L2 and L2<L3).
    under_arch_l1 = copy.deepcopy(draft)
    pa1 = under_arch_l1["problems"][1]  # tpl-two-step-linear has arch["level"] == 2
    pa1.pop("blindSolve", None)
    pa1["level"] = 1
    pa1["form"] = "direct"
    errs_arch_l1 = ai_drill_ingest.check_ai_drill(under_arch_l1, vault_dir=str(TEMPLATE_DIR))
    assert any("below archetype 'tpl-two-step-linear' base level L2" in e for e in errs_arch_l1), errs_arch_l1

    under_arch_l2 = copy.deepcopy(draft)
    pa2 = under_arch_l2["problems"][1]  # clean number problem reassigned to L3 archetype
    pa2.pop("blindSolve", None)
    pa2["archetypeKey"] = "tpl-distribution-diagnose"
    pa2["commonTrapTag"] = "tpl-partial-distribution-trap"
    pa2["level"] = 2
    pa2["form"] = "direct"
    errs_arch_l2 = ai_drill_ingest.check_ai_drill(under_arch_l2, vault_dir=str(TEMPLATE_DIR))
    assert any("below archetype 'tpl-distribution-diagnose' base level L3" in e for e in errs_arch_l2), errs_arch_l2

    # 5. L2 problem with blindSolve giving L3 rejected as under-labelled.
    under_l2 = copy.deepcopy(draft)
    p3 = under_l2["problems"][1]
    p3["blindSolve"] = {
        "answer": "8",
        "ambiguous": False,
        "setup": "given",
        "strategy": "choose",
        "check": "none",
        "task": "compute",
        "reverse": True,
        "steps": 4,
    }
    errs_l2 = ai_drill_ingest.check_ai_drill(under_l2, vault_dir=str(TEMPLATE_DIR))
    assert any("under-labelled" in e and "give L3" in e for e in errs_l2), errs_l2


def test_add_variants_enforces_l2_step_floor_for_new_variants(tmp_path: Path) -> None:
    draft = _template_draft()
    short_l2 = copy.deepcopy(draft["problems"][1])
    short_l2["steps"] = short_l2["steps"][:3]
    short_l2["steps"][-1]["val"] = "8"
    short_l2["review"] = {"verdict": "pass", "note": "Fixture short L2 variant."}

    variants_dir = tmp_path / "variants"
    variants_dir.mkdir()
    with pytest.raises(variant_bank.VariantBankError, match="L2 problem has 3 real step"):
        variant_bank.add_variants(
            {"unitCode": "MTH-TEMPLATE", "variants": [short_l2]},
            variants_dir=str(variants_dir),
            data_root=str(tmp_path / "empty_data"),
            vault_dir=str(TEMPLATE_DIR),
        )
    assert not (variants_dir / "MTH-TEMPLATE.json").exists()

    # Expanding to 4 real steps passes add_variants cleanly.
    good_l2 = copy.deepcopy(draft["problems"][1])
    saved = variant_bank.add_variants(
        {"unitCode": "MTH-TEMPLATE", "variants": [good_l2]},
        variants_dir=str(variants_dir),
        data_root=str(tmp_path / "empty_data"),
        vault_dir=str(TEMPLATE_DIR),
    )
    assert len(saved["variants"]) == 1


def test_drill_and_variant_gates_report_the_same_unwrapped_count(tmp_path: Path) -> None:
    draft = _template_draft()
    item = draft["problems"][1]
    item["steps"] = item["steps"][:2] + item["steps"][-1:]
    duplicate = item["steps"][1]["latex"]
    item["steps"].insert(2, {"latex": rf"\boxed{{{duplicate}}}", "explain": "Repeat the same equation."})

    drill_errors = ai_drill_ingest.check_ai_drill(copy.deepcopy(draft), vault_dir=str(TEMPLATE_DIR))
    drill_count = [error.split("] ", 1)[1] for error in drill_errors if "L2 problem has" in error]
    assert len(drill_count) == 1
    assert drill_count[0].startswith("L2 problem has 3 real step(s)")

    with pytest.raises(variant_bank.VariantBankError) as exc:
        variant_bank.add_variants(
            {"unitCode": "MTH-TEMPLATE", "variants": [copy.deepcopy(item)]},
            variants_dir=str(tmp_path / "variants"),
            data_root=str(tmp_path / "empty_data"),
            vault_dir=str(TEMPLATE_DIR),
        )
    variant_count = [line.split("] ", 1)[1] for line in str(exc.value).splitlines() if "L2 problem has" in line]
    assert variant_count == drill_count


def test_l2_step_floor_gate_accepts_baseline_and_skips_prg(
    synthetic_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_drill(synthetic_repo, "PRG-T99-C01", "DRL-PRG-T99-C01-01", step_count=1)
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 0
    report = capsys.readouterr().out
    assert f"Baseline short L2 problem: {EXISTING_DRILL} Q02 (3 real steps, need >= 4)." in report
    assert f"Baseline short L2 variant: {UNIT} {EXISTING_VARIANT} (3 real steps, need >= 4)." in report
    assert "PRG-T99-C01" not in report


def test_l2_step_floor_gate_rejects_new_short_l2_drill_and_variant(
    synthetic_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_drill(synthetic_repo, UNIT, NEW_DRILL, step_count=2, qid="Q05")
    _write_bank(
        synthetic_repo,
        UNIT,
        [
            {"variantId": EXISTING_VARIANT, "level": 2, "steps": _make_steps(3)},
            {"variantId": NEW_VARIANT, "level": 2, "steps": _make_steps(2)},
        ],
    )
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 1
    report = capsys.readouterr().out
    assert f"FAIL New short L2 problem: {NEW_DRILL} Q05 (2 real steps, need >= 4)." in report
    assert f"FAIL New short L2 variant: {UNIT} {NEW_VARIANT} (2 real steps, need >= 4)." in report
    assert "Adding baseline entries is forbidden." in report


def test_l2_step_floor_gate_requires_pruning_stale_baseline(
    synthetic_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_drill(synthetic_repo, UNIT, EXISTING_DRILL, step_count=4)
    _write_bank(synthetic_repo, UNIT, [{"variantId": EXISTING_VARIANT, "level": 2, "steps": _make_steps(4)}])
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 1
    report = capsys.readouterr().out
    assert f"FAIL Stale drill baseline entry: {EXISTING_DRILL} Q02" in report
    assert f"FAIL Stale variant baseline entry: {UNIT} {EXISTING_VARIANT}" in report

    (synthetic_repo / ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH).write_text(
        json.dumps({"drills": {}, "variants": {}}), encoding="utf-8"
    )
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 0


def test_check_ai_drill_grandfathers_saved_baseline_only_when_allowed() -> None:
    draft = _template_draft()
    draft["drillId"] = "DRL-MTH-T01-C04-01"
    draft["problems"][1]["id"] = "Q04"
    draft["problems"][1]["steps"] = draft["problems"][1]["steps"][:3]
    draft["problems"][1]["steps"][-1]["val"] = "8"

    errs_draft = ai_drill_ingest.check_ai_drill(copy.deepcopy(draft), vault_dir=str(TEMPLATE_DIR))
    assert any("L2 problem has 3 real step(s)" in e for e in errs_draft), errs_draft

    errs_saved = ai_drill_ingest.check_ai_drill(
        copy.deepcopy(draft), vault_dir=str(TEMPLATE_DIR), allow_l2_baseline=True
    )
    assert errs_saved == []
    assert os.path.isfile(ROOT / ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH)


@pytest.mark.parametrize(
    ("raw_text", "expected_snippet"),
    [
        (
            json.dumps({"drills": {EXISTING_DRILL: ["Q02", "Q02"]}, "variants": {UNIT: [EXISTING_VARIANT]}}),
            "Duplicate baseline ID: drills",
        ),
        (
            json.dumps({"drills": {EXISTING_DRILL: ["Q02"]}, "variants": {UNIT: [EXISTING_VARIANT, EXISTING_VARIANT]}}),
            "Duplicate baseline ID: variants",
        ),
        (json.dumps(["not", "a", "dict"]), "top-level value must be an object"),
        (json.dumps({"drills": {}, "variants": {}, "extra": {}}), "unknown top-level key"),
        (json.dumps({"drills": "bad", "variants": {}}), "'drills' must be an object"),
        (json.dumps({"drills": {EXISTING_DRILL: "Q02"}, "variants": {}}), "must be a non-empty list"),
        (json.dumps({"drills": {EXISTING_DRILL: []}, "variants": {}}), "must be a non-empty list"),
        (json.dumps({"drills": {EXISTING_DRILL: [""]}, "variants": {}}), "Malformed baseline ID"),
        (json.dumps({"drills": {EXISTING_DRILL: [123]}, "variants": {}}), "Malformed baseline ID"),
        ('{"drills": {}, "drills": {}, "variants": {}}', "Duplicate baseline key"),
        (
            f'{{"drills": {{"{EXISTING_DRILL}": ["Q02"], "{EXISTING_DRILL}": ["Q03"]}}}}',
            "Duplicate baseline key",
        ),
        ("{invalid json", "Malformed baseline JSON"),
    ],
)
def test_l2_step_floor_gate_rejects_duplicate_ids_and_malformed_baseline(
    synthetic_repo: Path,
    raw_text: str,
    expected_snippet: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (synthetic_repo / ai_drill_ingest.L2_STEP_FLOOR_BASELINE_PATH).write_text(raw_text, encoding="utf-8")
    assert ai_drill_ingest.main(["--l2-step-gate"]) == 1
    report = capsys.readouterr().out
    assert expected_snippet in report
