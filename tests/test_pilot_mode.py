from __future__ import annotations

import json
from pathlib import Path

import labs.common.submit_lab as submit_lab
import notion_sync.drill_sync as drill_sync
import progress_store
from code_engine.workspace import materialize_drill_workspace, materialize_pilot_lab
from scripts.issues import add_issue, issues
from scripts.weak_spots import load_items


def _sample_drill(drill_id: str = "DRL-PRG-TEST-01", *, practised: bool = False) -> dict:
    doc = {
        "drillId": drill_id,
        "subject": "PRG",
        "unitCode": "PRG-T00-C02-U01",
        "chapterCode": "PRG-T00-C02",
        "topicCode": "PRG-T00",
        "unitTitle": "Test Unit",
        "environment": "node-vanilla",
        "config": {"questionCount": 1, "difficultyMode": "Mixed Exam Mode"},
        "problems": [
            {
                "id": "Q01",
                "levelLabel": "L1",
                "category": "problem-solving",
                "prompt": "Return x + 1",
                "entryPoint": "inc",
                "starterCode": "function inc(x) { return x; }\nmodule.exports = { inc };",
                "visibleTests": [{"name": "adds one", "testCode": "assert.strictEqual(inc(1), 2);"}],
                "steps": [{"explain": "Add 1 to x."}],
                "answerDisplay": "x + 1",
            }
        ],
    }
    if practised:
        doc["sessionSummary"] = {
            "score": 1,
            "maxScore": 1,
            "accuracyPct": 100.0,
            "practiceStatus": "Graded",
            "mistakeCategories": [],
            "divergedStepsSummary": "All passed.",
            "attemptDate": "2026-11-16T10:00:00Z",
        }
        doc["problems"][0]["state"] = {"reviews": [{"verdict": "pass", "at": "2026-11-16T10:00:00Z"}]}
    return doc


def test_pilot_paths_and_default_unchanged(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.delenv("LABS_DIR", raising=False)
    monkeypatch.delenv("LEARNINGOS_PILOT", raising=False)

    assert progress_store.pilot_mode() is False
    assert progress_store.progress_root(str(tmp_path)) == str(tmp_path / "progress")
    assert progress_store.workspace_root(str(tmp_path)) == str(tmp_path / "drills" / "workspace")
    assert progress_store.labs_root(str(tmp_path)) == str(tmp_path / "labs")

    monkeypatch.setenv("LEARNINGOS_PILOT", "1")
    assert progress_store.pilot_mode() is True
    assert progress_store.progress_root(str(tmp_path)) == str(tmp_path / "pilot" / "progress")
    assert progress_store.workspace_root(str(tmp_path)) == str(tmp_path / "pilot" / "workspace")
    assert progress_store.labs_root(str(tmp_path)) == str(tmp_path / "pilot" / "labs")


def test_materialize_drill_workspace_pilot_vs_normal(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LEARNINGOS_PILOT", "1")

    doc = _sample_drill()
    manifest = materialize_drill_workspace(doc, root_dir=str(tmp_path))
    assert (tmp_path / "pilot" / "workspace" / "DRL-PRG-TEST-01" / "Q01_inc.js").is_file()
    assert not (tmp_path / "drills" / "workspace").exists()
    assert "pilot/workspace/DRL-PRG-TEST-01/Q01_inc.js" in manifest["files"]["Q01"]["relativeSrc"].replace("\\", "/")

    monkeypatch.delenv("LEARNINGOS_PILOT", raising=False)
    materialize_drill_workspace(_sample_drill("DRL-PRG-TEST-02"), root_dir=str(tmp_path))
    assert (tmp_path / "drills" / "workspace" / "DRL-PRG-TEST-02" / "Q01_inc.js").is_file()


def test_materialize_pilot_lab_copies_and_preserves_edits(tmp_path: Path) -> None:
    lab_dir = tmp_path / "labs" / "LAB-PRG-TEST-01"
    (lab_dir / "src").mkdir(parents=True)
    (lab_dir / "tests").mkdir(parents=True)
    (lab_dir / "lab.config.json").write_text(json.dumps({"labId": "LAB-PRG-TEST-01"}), encoding="utf-8")
    (lab_dir / "eslint.config.js").write_text(
        'import { prgConfig } from "../../tools/lint/base.js";\n', encoding="utf-8"
    )
    (lab_dir / "package.json").write_text(
        '{"scripts": {"submit": "python3 ../common/submit_lab.py"}}', encoding="utf-8"
    )
    (lab_dir / "src" / "index.ts").write_text("// stub\n", encoding="utf-8")
    (lab_dir / "tests" / "m1.test.ts").write_text("// test\n", encoding="utf-8")

    dst = materialize_pilot_lab("LAB-PRG-TEST-01", root_dir=str(tmp_path))
    assert dst == tmp_path / "pilot" / "labs" / "LAB-PRG-TEST-01"
    assert (dst / "src" / "index.ts").read_text(encoding="utf-8") == "// stub\n"
    assert "../../../tools/lint/base.js" in (dst / "eslint.config.js").read_text(encoding="utf-8")
    assert "../../../labs/common/submit_lab.py" in (dst / "package.json").read_text(encoding="utf-8")

    # Pilot edits to src are preserved when re-materialising without --force
    (dst / "src" / "index.ts").write_text("// pilot work\n", encoding="utf-8")
    materialize_pilot_lab("LAB-PRG-TEST-01", root_dir=str(tmp_path), force=False)
    assert (dst / "src" / "index.ts").read_text(encoding="utf-8") == "// pilot work\n"
    assert (lab_dir / "src" / "index.ts").read_text(encoding="utf-8") == "// stub\n"


def test_weak_spots_reads_pilot_progress(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.setenv("LEARNINGOS_PILOT", "1")

    data_dir = tmp_path / "drills" / "data" / "PRG-T00-C02-U01"
    data_dir.mkdir(parents=True)
    doc = _sample_drill(practised=True)
    (data_dir / "DRL-PRG-TEST-01.json").write_text(json.dumps(doc), encoding="utf-8")

    progress_store.save_progress(doc, repo_root=str(tmp_path))
    assert (tmp_path / "pilot" / "progress" / "DRL-PRG-TEST-01.json").is_file()
    assert not (tmp_path / "progress").exists()

    items = load_items(data_root=str(tmp_path / "drills" / "data"), labs_root=str(tmp_path / "labs"))
    assert len(items) == 1
    assert items[0].drill == "DRL-PRG-TEST-01"


def test_pilot_skips_notion_learner_writes_but_allows_pristine(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.setenv("LEARNINGOS_PILOT", "1")

    def fail_notion(*args, **kwargs):
        raise AssertionError("Notion learner-state call must not be made in pilot mode")

    monkeypatch.setattr(drill_sync, "notion_request", fail_notion)
    monkeypatch.setattr(submit_lab, "notion_request", fail_notion)

    # 1. Practised drill sync -> skipped
    res = drill_sync.sync_drill_to_notion(_sample_drill(practised=True))
    assert res["ok"] is True
    assert res.get("pilotSkipped") is True
    assert (tmp_path / "pilot" / "progress" / "DRL-PRG-TEST-01.json").is_file()
    assert not (tmp_path / "progress").exists()
    out = capsys.readouterr().out
    assert "[PILOT] skipped Notion write:" in out

    # 2. Direct unit review update -> skipped
    assert drill_sync.update_unit_reviews(["PRG-T00-C02-U01"], "2026-11-16", {}, "tok") == {}
    assert "[PILOT] skipped Notion write:" in capsys.readouterr().out

    # 3. Lab result sync -> skipped
    lab_cfg = {"labId": "LAB-PRG-TEST-01", "title": "Lab"}
    eval_res = {
        "all_passed": False,
        "total_score": 0,
        "max_score": 25,
        "accuracy_pct": 0.0,
        "failing_categories": [],
        "divergence_summary": "x",
        "milestones": [],
    }
    assert (
        submit_lab.sync_to_notion(tmp_path, tmp_path / "pilot" / "labs" / "LAB-PRG-TEST-01", lab_cfg, eval_res, {})
        is None
    )
    assert "[PILOT] skipped Notion write:" in capsys.readouterr().out

    # 4. Pristine drill sync (authoring write) -> NOT skipped
    calls: list[tuple[str, str]] = []
    (tmp_path / "id_map.json").write_text(json.dumps({"DRILLS_DB": {"id": "db-1"}}), encoding="utf-8")
    monkeypatch.setattr(drill_sync, "load_env", lambda: {"NOTION_TOKEN": "tok"})

    def fake_notion(method: str, endpoint: str, token: str, payload=None):
        calls.append((method, endpoint))
        if method == "POST" and endpoint.endswith("/query"):
            return {"results": []}
        if method == "POST" and endpoint == "pages":
            return {"id": "page-new"}
        return {}

    monkeypatch.setattr(drill_sync, "notion_request", fake_notion)
    monkeypatch.setattr(drill_sync, "replace_page_blocks", lambda *a, **kw: None)

    pristine_res = drill_sync.sync_drill_to_notion(_sample_drill("DRL-PRG-PRISTINE-01", practised=False))
    assert pristine_res["ok"] is True
    assert pristine_res.get("drillPageId") == "page-new"
    assert ("POST", "pages") in calls


def test_issues_get_source_pilot_in_pilot_mode(monkeypatch, tmp_path: Path) -> None:
    log_file = tmp_path / "log.jsonl"

    monkeypatch.setenv("LEARNINGOS_PILOT", "1")
    _, created = add_issue("bug", "batch", "learner", "DRL-PRG-T00-C02-U01-01/Q01", "pilot issue", path=str(log_file))
    assert created is True

    monkeypatch.delenv("LEARNINGOS_PILOT", raising=False)
    _, created2 = add_issue("bug", "batch", "learner", "DRL-PRG-T00-C02-U01-01/Q02", "real issue", path=str(log_file))
    assert created2 is True

    rows = issues(str(log_file))
    assert [r["source"] for r in rows] == ["pilot", "learner"]
