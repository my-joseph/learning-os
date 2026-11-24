"""Tests for PRG R3: review_run, review_record, weak_spots PRG support, Mastery, and retired review.py."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from code_engine import quality_checks as qc
from code_engine import review as retired_review
from code_engine import review_run
from code_engine.lint_check import LintToolsMissingError, get_lint_binaries
from code_engine.workspace import materialize_drill_workspace
from notion_sync import drill_sync
from scripts import review_record, weak_spots

REPO_ROOT = Path(__file__).resolve().parent.parent


def _require_node_and_lint():
    if shutil.which("node") is None:
        pytest.skip("node binary not installed on PATH")
    try:
        get_lint_binaries()
    except LintToolsMissingError as exc:
        pytest.skip(str(exc))


def _make_prg_drill(drill_id: str = "DRL-PRG-T00-C03-99", level: int = 1) -> dict:
    return {
        "drillId": drill_id,
        "subject": "PRG",
        "unitCode": "PRG-T00-C03-U01",
        "chapterCode": "PRG-T00-C03",
        "topicCode": "PRG-T00",
        "unitTitle": "JS Baseline",
        "environment": "node-vanilla",
        "problems": [
            {
                "id": "Q01",
                "level": level,
                "levelLabel": f"L{level}",
                "category": "Core Skill",
                "archetype": "problem-solving",
                "archetypeKey": "prg-c02-primitive-coercion-guard",
                "entryPoint": "clampPort",
                "prompt": "Implement `clampPort(port)`.",
                "starterCode": "function clampPort(_port) {\n  return null;\n}\nmodule.exports = { clampPort };\n",
                "solutionCode": (
                    "function clampPort(port) {\n"
                    "  if (typeof port !== 'number' || !Number.isFinite(port)) return null;\n"
                    "  return Math.min(65535, Math.max(0, port));\n"
                    "}\n"
                    "module.exports = { clampPort };\n"
                ),
                "visibleTests": [
                    {"name": "keeps valid port", "testCode": "assert.strictEqual(clampPort(80), 80);"},
                ],
                "hiddenTests": [
                    {"name": "keeps zero port", "testCode": "assert.strictEqual(clampPort(0), 0);"},
                    {"name": "rejects string", "testCode": "assert.strictEqual(clampPort('80'), null);"},
                ],
                "steps": [{"explain": "Check number then clamp."}],
            }
        ],
    }


def _setup_workspace(tmp_path: Path, drill_doc: dict, src_code: str) -> Path:
    drill_id = drill_doc["drillId"]
    data_dir = tmp_path / "drills" / "data" / "PRG-T00-C03"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / f"{drill_id}.json").write_text(json.dumps(drill_doc, indent=2), encoding="utf-8")

    tools_link = tmp_path / "tools"
    if not tools_link.exists():
        os.symlink(REPO_ROOT / "tools", tools_link)

    materialize_drill_workspace(drill_doc, root_dir=str(tmp_path))
    ws_dir = tmp_path / "drills" / "workspace" / drill_id
    prob = drill_doc["problems"][0]
    src_path = ws_dir / f"{prob['id']}_{prob['entryPoint']}.js"
    src_path.write_text(src_code, encoding="utf-8")
    return ws_dir


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    monkeypatch.setenv("LEARNINGOS_ISSUE_LOG", str(tmp_path / "issues" / "log.jsonl"))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_review_run_passing_and_failing_solutions(tmp_path):
    _require_node_and_lint()
    drill_doc = _make_prg_drill(level=1)
    _setup_workspace(tmp_path, drill_doc, drill_doc["problems"][0]["solutionCode"])

    res = review_run.run_review(drill_doc["drillId"], "Q01")
    assert res["drillId"] == drill_doc["drillId"]
    assert res["problemId"] == "Q01"
    assert res["archetypeKey"] == "prg-c02-primitive-coercion-guard"
    assert res["level"] == 1
    assert res["codeHash"].startswith("sha256:")
    assert res["tests"] == {"passed": 3, "total": 3, "failed": []}
    assert res["lint"] == []
    assert res["typecheck"] == []
    assert any(c["id"] == "U-names" for c in res["checks"])
    assert any(c["id"] == "QC-coercion-explicit-nullish-intent" for c in res["checks"])

    # Failing hidden test + ESLint no-param-reassign
    bad_code = (
        "function clampPort(port) {\n"
        "  port = Number(port);\n"
        "  return Math.min(65535, Math.max(0, port));\n"
        "}\n"
        "module.exports = { clampPort };\n"
    )
    _setup_workspace(tmp_path, drill_doc, bad_code)
    bad_res = review_run.run_review(drill_doc["drillId"], "Q01")
    assert bad_res["tests"]["passed"] == 2
    assert bad_res["tests"]["total"] == 3
    assert bad_res["tests"]["failed"] == ["1 hidden check failed"]
    assert not any("rejects string" in name or "HIDDEN" in name for name in bad_res["tests"]["failed"])
    assert any(item["rule"] == "no-param-reassign" for item in bad_res["lint"])


def test_review_run_and_record_mask_hidden_tests_in_drill_and_lab(tmp_path, monkeypatch):
    _require_node_and_lint()
    drill_doc = _make_prg_drill(level=1)
    # Fail 1 visible test and both hidden tests (stub returns -1 always)
    stub_code = "function clampPort(_port) {\n  return -1;\n}\nmodule.exports = { clampPort };\n"
    _setup_workspace(tmp_path, drill_doc, stub_code)

    res = review_run.run_review(drill_doc["drillId"], "Q01")
    assert res["tests"]["passed"] == 0
    assert res["tests"]["total"] == 3
    assert res["tests"]["failed"] == ["[Q01-T01] keeps valid port", "2 hidden checks failed"]
    serialized_res = json.dumps(res)
    for secret_name in ("keeps zero port", "rejects string", "HIDDEN"):
        assert secret_name not in serialized_res

    rec = review_record.add_record(drill_doc["drillId"], "Q01", [])
    assert rec["verdict"] == "revise"
    assert rec["tests"]["failed"] == ["[Q01-T01] keeps valid port", "2 hidden checks failed"]

    prog_path = Path(os.environ["PROGRESS_DIR"]) / f"{drill_doc['drillId']}.json"
    prog_text = prog_path.read_text(encoding="utf-8")
    for secret_name in ("keeps zero port", "rejects string", "HIDDEN"):
        assert secret_name not in prog_text
    prog_data = json.loads(prog_text)
    q_state = prog_data["problems"]["Q01"]
    assert q_state["lastTestReport"]["visibleResults"] == [
        {"name": "[Q01-T01] keeps valid port", "passed": False},
        {"name": "2 hidden checks failed", "passed": False},
    ]
    assert q_state["reviews"][0]["tests"]["failed"] == ["[Q01-T01] keeps valid port", "2 hidden checks failed"]
    assert "failed_tests=3" in review_record.format_history(drill_doc["drillId"], "Q01")

    # Lab path: failing hidden test in labs/_reference/<LAB_ID>/hidden/ must also be masked
    from tests.test_new_project_lab import _make_fixture_lab

    lab_root_tmp = tmp_path / "lab_fixture"
    lab_root_tmp.mkdir(parents=True)
    lab_dir, ref_dir, _ = _make_fixture_lab(lab_root_tmp)
    labs_root = lab_dir.parent
    monkeypatch.setenv("LABS_DIR", str(labs_root))
    # Passes visible M1 test (consumeRetry(3, 1) === 2), fails both hidden M1 tests (overspend & exact zero)
    (lab_dir / "src" / "budget.ts").write_text(
        "export function consumeRetry(remaining: number, spend: number): number | null {\n"
        "  const next = remaining - spend;\n"
        "  return next === 0 ? null : next;\n"
        "}\n",
        encoding="utf-8",
    )
    lab_res = review_run.run_review("LAB-PRG-T01-C01-99", "M1", labs_root=labs_root)
    assert lab_res["tests"]["passed"] == 1
    assert lab_res["tests"]["total"] == 3
    assert lab_res["tests"]["failed"] == ["2 hidden checks failed"]
    lab_res_json = json.dumps(lab_res)
    for secret_name in ("rejects overspend when budget is zero", "allows exact zero remaining", "HIDDEN"):
        assert secret_name not in lab_res_json

    lab_rec = review_record.add_record("LAB-PRG-T01-C01-99", "M1", [], labs_root=labs_root)
    assert lab_rec["tests"]["failed"] == ["2 hidden checks failed"]
    lab_prog_text = (Path(os.environ["PROGRESS_DIR"]) / "LAB-PRG-T01-C01-99.json").read_text(encoding="utf-8")
    for secret_name in ("rejects overspend when budget is zero", "allows exact zero remaining", "HIDDEN"):
        assert secret_name not in lab_prog_text


def test_review_run_degrades_gracefully_without_lint_tools(tmp_path, monkeypatch):
    if shutil.which("node") is None:
        pytest.skip("node binary not installed on PATH")
    # Create an empty tools/lint directory (no node_modules) inside tmp_path
    (tmp_path / "tools" / "lint").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LEARNINGOS_ROOT", str(tmp_path))

    drill_doc = _make_prg_drill(level=1)
    drill_id = drill_doc["drillId"]
    data_dir = tmp_path / "drills" / "data" / "PRG-T00-C03"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / f"{drill_id}.json").write_text(json.dumps(drill_doc, indent=2), encoding="utf-8")
    materialize_drill_workspace(drill_doc, root_dir=str(tmp_path))

    res = review_run.run_review(drill_id, "Q01")
    assert res["tests"]["passed"] == 1
    assert res["tests"]["total"] == 3
    assert res["tests"]["failed"] == ["[Q01-T01] keeps valid port", "1 hidden check failed"]
    assert res["lint"] == []
    assert res["typecheck"] == []
    assert any(c["id"] == "U-names" for c in res["checks"])


def test_u_one_job_severity_depends_on_level():
    rubric_l1 = qc.applicable_rubric("prg-c02-primitive-coercion-guard", 1)
    rubric_l3 = qc.applicable_rubric("prg-c02-primitive-coercion-guard", 3)
    sev_l1 = next(c["severity"] for c in rubric_l1 if c["id"] == "U-one-job")
    sev_l3 = next(c["severity"] for c in rubric_l3 if c["id"] == "U-one-job")
    assert sev_l1 == "should"
    assert sev_l3 == "must"


def test_review_record_unknown_check_refused_and_caller_severity_ignored(tmp_path):
    _require_node_and_lint()
    drill_doc = _make_prg_drill(level=1)
    _setup_workspace(tmp_path, drill_doc, drill_doc["problems"][0]["solutionCode"])
    drill_file = tmp_path / "drills" / "data" / "PRG-T00-C03" / f"{drill_doc['drillId']}.json"
    before_content = drill_file.read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown check id"):
        review_record.add_record(
            drill_doc["drillId"],
            "Q01",
            [{"check": "QC-not-real", "severity": "should", "line": 1, "note": "bad"}],
        )

    # Caller claims severity='should' for U-names (which is 'must' in rubric); rubric wins -> revise
    rec = review_record.add_record(
        drill_doc["drillId"],
        "Q01",
        [{"check": "U-names", "severity": "should", "line": 1, "note": "vague name"}],
    )
    assert rec["attempt"] == 1
    assert rec["findings"][0]["severity"] == "must"
    assert rec["verdict"] == "revise"
    assert drill_file.read_text(encoding="utf-8") == before_content


def test_review_record_dispute_unblocks_must_and_explain(tmp_path):
    _require_node_and_lint()
    drill_doc = _make_prg_drill(level=1)
    _setup_workspace(tmp_path, drill_doc, drill_doc["problems"][0]["solutionCode"])

    rec = review_record.add_record(
        drill_doc["drillId"],
        "Q01",
        [{"check": "U-names", "severity": "must", "line": 1, "note": "name too short"}],
    )
    assert rec["verdict"] == "revise"

    updated, issue_id = review_record.dispute_finding(
        drill_doc["drillId"], "Q01", "U-names", reason="port is the domain term in spec"
    )
    assert updated["verdict"] == "pass"
    assert updated["findings"][0]["disputed"] == {
        "reason": "port is the domain term in spec",
        "issueId": issue_id,
    }
    log_file = Path(os.environ["LEARNINGOS_ISSUE_LOG"])
    assert log_file.exists() and issue_id in log_file.read_text(encoding="utf-8")

    explained = review_record.set_explain(drill_doc["drillId"], "Q01", "Guards non-finite values then clamps.")
    assert explained["explain"] == "Guards non-finite values then clamps."

    hist = review_record.format_history(drill_doc["drillId"], "Q01")
    assert "#1 PASS" in hist and "U-names [disputed]" in hist


def _write_prg_progress(tmp_path: Path, drills: dict[str, list[tuple]]) -> tuple[str, str]:
    unit = "PRG-T09-C01-U01"
    data_dir = tmp_path / "drills" / "data" / unit
    prog_dir = tmp_path / "progress"
    data_dir.mkdir(parents=True, exist_ok=True)
    prog_dir.mkdir(parents=True, exist_ok=True)
    for did, probs in drills.items():
        (data_dir / f"{did}.json").write_text(
            json.dumps(
                {
                    "drillId": did,
                    "subject": "PRG",
                    "unitCode": unit,
                    "problems": [
                        {
                            "id": pid,
                            "level": lv,
                            "unitCode": unit,
                            "archetype": arch_type,
                            "archetypeKey": "prg-c02-primitive-coercion-guard",
                        }
                        for pid, lv, arch_type, _ in probs
                    ],
                }
            ),
            encoding="utf-8",
        )
        (prog_dir / f"{did}.json").write_text(
            json.dumps({"drillId": did, "problems": {pid: st for pid, *_, st in probs}}),
            encoding="utf-8",
        )
    return str(tmp_path / "drills" / "data"), str(prog_dir)


def _rev(at: str, verdict: str, checks: list[str] | None = None, lint_rules: list[str] | None = None) -> dict:
    return {
        "at": at,
        "attempt": 1,
        "codeHash": "sha256:x",
        "code": "function f() {}",
        "tests": {"passed": 1, "total": 1, "failed": []},
        "lint": [{"rule": r, "line": 1, "message": r} for r in (lint_rules or [])],
        "typecheck": [],
        "findings": [{"check": c, "severity": "must", "line": 1, "note": "n"} for c in (checks or [])],
        "verdict": verdict,
        "explain": None,
    }


def test_weak_spots_prg_open_close_reopen_and_scoring(tmp_path):
    # Two distinct problems with U-no-input-mutation -> opens weak spot
    hits = {
        "D1": [
            ("Q01", 1, "problem-solving", {"reviews": [_rev("2026-11-01", "revise", ["U-no-input-mutation"])]}),
            ("Q02", 1, "problem-solving", {"reviews": [_rev("2026-11-02", "revise", ["U-no-input-mutation"])]}),
        ]
    }
    roots = _write_prg_progress(tmp_path / "a", hits)
    rep_open = weak_spots.report(None, *roots)
    assert "WEAK     U-no-input-mutation (" in rep_open

    # Two subsequent passing problems without it -> closes
    clean = {
        "D2": [
            ("Q01", 1, "problem-solving", {"reviews": [_rev("2026-11-03", "pass")]}),
            ("Q02", 1, "problem-solving", {"reviews": [_rev("2026-11-04", "pass")]}),
        ]
    }
    roots_closed = _write_prg_progress(tmp_path / "b", {**hits, **clean})
    assert "closed   U-no-input-mutation (" in weak_spots.report(None, *roots_closed)

    # New occurrence -> reopens
    reopen = {
        "D3": [("Q01", 1, "problem-solving", {"reviews": [_rev("2026-11-05", "revise", ["U-no-input-mutation"])]})]
    }
    roots_reopen = _write_prg_progress(tmp_path / "c", {**hits, **clean, **reopen})
    assert "WEAK     U-no-input-mutation (" in weak_spots.report(None, *roots_reopen)

    # Scoring: first-pass=1.0, later-pass=0.5, never-passed=0.0, skipped=0.0
    scoring_roots = _write_prg_progress(
        tmp_path / "d",
        {
            "D4": [
                ("Q01", 1, "problem-solving", {"reviews": [_rev("2026-11-01", "pass")]}),
                (
                    "Q02",
                    1,
                    "problem-solving",
                    {"reviews": [_rev("2026-11-02", "revise", ["U-names"]), _rev("2026-11-03", "pass")]},
                ),
                ("Q03", 1, "problem-solving", {"reviews": [_rev("2026-11-04", "revise", ["U-names"])]}),
                ("Q04", 1, "problem-solving", {"skipped": True}),
            ]
        },
    )
    scores = {i.pid: i.score for i in weak_spots.load_items(*scoring_roots)}
    assert scores == {"Q01": 1.0, "Q02": 0.5, "Q03": 0.0, "Q04": 0.0}


def test_weak_spots_prg_level_advice(tmp_path):
    up_probs = [
        (f"Q0{i}", 2, "debugging" if i == 1 else "problem-solving", {"reviews": [_rev(f"2026-11-0{i}", "pass")]})
        for i in range(1, 6)
    ]
    roots_up = _write_prg_progress(tmp_path / "up", {"D1": up_probs})
    assert weak_spots.level_advice(weak_spots.load_items(*roots_up))[2]["move"] == "up"

    stay_probs = [(f"Q0{i}", 2, "problem-solving", {"reviews": [_rev(f"2026-11-0{i}", "pass")]}) for i in range(1, 6)]
    roots_stay = _write_prg_progress(tmp_path / "stay", {"D1": stay_probs})
    assert weak_spots.level_advice(weak_spots.load_items(*roots_stay))[2]["move"] == "stay"

    down_probs = [
        (f"Q0{i}", 2, "debugging", {"reviews": [_rev(f"2026-11-0{i}", "revise", ["U-names"])]}) for i in range(1, 6)
    ]
    roots_down = _write_prg_progress(tmp_path / "down", {"D1": down_probs})
    assert weak_spots.level_advice(weak_spots.load_items(*roots_down))[2]["move"] == "down"


def test_mastery_prg_only_from_pass_and_mocked_notion(tmp_path, monkeypatch):
    # A newer problem's explicit unit takes precedence over the legacy vault lookup.
    vault = tmp_path / "code_engine" / "reasoning_vault"
    vault.mkdir(parents=True)
    (vault / "synthetic.json").write_text(
        json.dumps(
            {"archetypes": [{"archetypeKey": "prg-c02-primitive-coercion-guard", "unitCode": "PRG-T00-C03-U01"}]}
        ),
        encoding="utf-8",
    )

    # Passing tests without review -> awaiting review (score None -> no mastery evidence yet; never Mastery 3)
    roots_no_rev = _write_prg_progress(
        tmp_path / "norev",
        {
            "D1": [
                ("Q01", 3, "debugging", {"score": 1, "lastTestReport": {"allPassed": True}}),
                ("Q02", 3, "problem-solving", {"score": 1, "lastTestReport": {"allPassed": True}}),
                ("Q03", 3, "problem-solving", {"score": 1, "lastTestReport": {"allPassed": True}}),
            ]
        },
    )
    upd_no_rev = weak_spots.review_update("PRG-T09-C01-U01", None, "2026-11-16", *roots_no_rev)
    assert upd_no_rev is None

    # Failing tests without review -> score 0 -> mastery 1
    roots_fail = _write_prg_progress(
        tmp_path / "fail",
        {
            "D1": [
                ("Q01", 3, "debugging", {"lastTestReport": {"allPassed": False}}),
                ("Q02", 3, "problem-solving", {"lastTestReport": {"allPassed": False}}),
                ("Q03", 3, "problem-solving", {"lastTestReport": {"allPassed": False}}),
            ]
        },
    )
    upd_fail = weak_spots.review_update("PRG-T09-C01-U01", None, "2026-11-16", *roots_fail)
    assert upd_fail is not None and upd_fail["mastery"] == 1

    # 3 L3+ problems (including an L4 challenge) with latest review 'pass' -> mastery 3 (via mocked Notion update_unit_reviews)
    roots_pass = _write_prg_progress(
        tmp_path / "pass",
        {
            "D2": [
                ("Q01", 3, "debugging", {"reviews": [_rev("2026-11-10", "pass")]}),
                ("Q02", 3, "problem-solving", {"reviews": [_rev("2026-11-11", "pass")]}),
                ("Q03", 4, "problem-solving", {"reviews": [_rev("2026-11-12", "pass")]}),
            ]
        },
    )
    monkeypatch.setenv("DRILLS_DATA_DIR", roots_pass[0])
    monkeypatch.setenv("PROGRESS_DIR", roots_pass[1])

    patched_payloads = []

    def fake_notion_request(method, endpoint, token, payload=None):
        if method == "GET":
            return {
                "properties": {
                    "Mastery (0-4)": {"number": 1},
                    "Last Reviewed": {"date": None},
                    "Next Review": {"date": None},
                }
            }
        patched_payloads.append((method, endpoint, payload))
        return {}

    monkeypatch.setattr(drill_sync, "notion_request", fake_notion_request)
    written = drill_sync.update_unit_reviews(
        ["PRG-T09-C01-U01"], "2026-11-16", {"PRG-T09-C01-U01": {"id": "page-123"}}, "fake-token"
    )
    assert written["PRG-T09-C01-U01"]["mastery"] == 3
    assert patched_payloads[0][2]["properties"]["Mastery (0-4)"]["number"] == 3


def test_retired_review_cli_prints_instructions_without_prompt_file(tmp_path, monkeypatch, capsys):
    ws_dir = tmp_path / "DRL-PRG-T00-C03-02"
    ws_dir.mkdir()
    monkeypatch.chdir(ws_dir)
    rc = retired_review.main(["Q01"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "In Claude Code, say: review code DRL-PRG-T00-C03-02 Q01" in out
    assert "python -m code_engine.review_run DRL-PRG-T00-C03-02 Q01" in out
    assert not (ws_dir / "PR_REVIEW_REQUEST.md").exists()


def test_verdict_never_passes_without_tests():
    from scripts.review_record import compute_verdict

    assert compute_verdict({"passed": 0, "total": 0, "failed": []}, [], [], []) == "revise"
    assert compute_verdict({"passed": 3, "total": 3, "failed": []}, [], [], []) == "pass"


def test_review_record_sets_state_score_via_shared_rule(tmp_path, monkeypatch):
    from progress_store import load_progress

    drill_doc = _make_prg_drill(level=1)
    drill_id = drill_doc["drillId"]

    def fake_run_review_with_source(*_args, **_kwargs):
        return (
            {
                "drillId": drill_id,
                "problemId": "Q01",
                "codeHash": "sha256:abc",
                "tests": {"passed": 3, "total": 3, "failed": []},
                "lint": [],
                "typecheck": [],
                "checks": [{"id": "U-names", "severity": "must", "check": "Clear names", "why": "readability"}],
            },
            "function clampPort(p) { return p; }",
            json.loads(json.dumps(drill_doc)),
        )

    monkeypatch.setattr(review_record, "run_review_with_source", fake_run_review_with_source)
    monkeypatch.setattr(
        review_record,
        "find_drill_doc",
        lambda _id: (json.loads(json.dumps(drill_doc)), tmp_path / f"{drill_id}.json"),
    )

    # 1. Clean first pass sets state.score = 1.0 even without prior Studio test run
    rec = review_record.add_record(drill_id, "Q01", [])
    assert rec["verdict"] == "pass"
    prog = load_progress(drill_id)
    assert prog["problems"]["Q01"]["score"] == 1.0

    # 2. Revise sets state.score = 0.0, then subsequent pass sets state.score = 0.5
    drill_doc_2 = _make_prg_drill(drill_id="DRL-PRG-T00-C03-98", level=1)
    did2 = drill_doc_2["drillId"]
    monkeypatch.setattr(
        review_record,
        "run_review_with_source",
        lambda *_a, **_kw: (
            {
                "drillId": did2,
                "problemId": "Q01",
                "codeHash": "sha256:def",
                "tests": {"passed": 3, "total": 3, "failed": []},
                "lint": [],
                "typecheck": [],
                "checks": [{"id": "U-names", "severity": "must", "check": "Clear names", "why": "readability"}],
            },
            "function clampPort(p) { return p; }",
            json.loads(json.dumps(drill_doc_2)),
        ),
    )
    monkeypatch.setattr(
        review_record,
        "find_drill_doc",
        lambda _id: (json.loads(json.dumps(drill_doc_2)), tmp_path / f"{did2}.json"),
    )

    r1 = review_record.add_record(did2, "Q01", [{"check": "U-names", "line": 1, "note": "vague"}])
    assert r1["verdict"] == "revise"
    assert load_progress(did2)["problems"]["Q01"]["score"] == 0.0

    r2 = review_record.add_record(did2, "Q01", [])
    assert r2["verdict"] == "pass"
    assert load_progress(did2)["problems"]["Q01"]["score"] == 0.5

    # 3. Dispute unblocking first revise flips verdict to pass and sets state.score = 1.0
    drill_doc_3 = _make_prg_drill(drill_id="DRL-PRG-T00-C03-97", level=1)
    did3 = drill_doc_3["drillId"]
    monkeypatch.setattr(
        review_record,
        "run_review_with_source",
        lambda *_a, **_kw: (
            {
                "drillId": did3,
                "problemId": "Q01",
                "codeHash": "sha256:ghi",
                "tests": {"passed": 3, "total": 3, "failed": []},
                "lint": [],
                "typecheck": [],
                "checks": [{"id": "U-names", "severity": "must", "check": "Clear names", "why": "readability"}],
            },
            "function clampPort(p) { return p; }",
            json.loads(json.dumps(drill_doc_3)),
        ),
    )
    monkeypatch.setattr(
        review_record,
        "find_drill_doc",
        lambda _id: (json.loads(json.dumps(drill_doc_3)), tmp_path / f"{did3}.json"),
    )
    review_record.add_record(did3, "Q01", [{"check": "U-names", "line": 1, "note": "vague"}])
    assert load_progress(did3)["problems"]["Q01"]["score"] == 0.0
    updated, _ = review_record.dispute_finding(did3, "Q01", "U-names", reason="domain term")
    assert updated["verdict"] == "pass"
    assert load_progress(did3)["problems"]["Q01"]["score"] == 1.0
