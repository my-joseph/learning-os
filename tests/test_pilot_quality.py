from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from scripts import pilot_quality


def _setup_repo(tmp_path: Path) -> Path:
    (tmp_path / "id_map.json").write_text("{}", encoding="utf-8")
    unit_dir = tmp_path / "drills" / "data" / "MTH-T01-C01-U01"
    unit_dir.mkdir(parents=True)
    drill_doc = {
        "drillId": "DRL-MTH-T01-C01-U01-01",
        "unitCode": "MTH-T01-C01-U01",
        "subject": "MTH",
        "problems": [
            {"id": "Q01", "form": "direct", "answerPlain": "SECRET_ANS_42"},
            {"id": "Q02", "form": "reverse", "answerPlain": "SECRET_ANS_99"},
        ],
    }
    (unit_dir / "DRL-MTH-T01-C01-U01-01.json").write_text(json.dumps(drill_doc), encoding="utf-8")
    (tmp_path / "progress").mkdir()
    (tmp_path / "progress" / "DRL-MTH-T01-C01-U01-01.json").write_text(
        json.dumps({"learner_secret": "DO_NOT_COPY_PROGRESS_BYTES"}), encoding="utf-8"
    )
    (tmp_path / "drills" / "workspace" / "DRL-MTH-T01-C01-U01-01").mkdir(parents=True)
    (tmp_path / "drills" / "workspace" / "DRL-MTH-T01-C01-U01-01" / "Q01.txt").write_text(
        "PROTECTED_WORKSPACE_CONTENT", encoding="utf-8"
    )
    return tmp_path


def _init_clean_run(repo: Path, run_id: str = "run-01", mode: str = "natural_attempt") -> dict:
    return pilot_quality.init_run(
        repo,
        run_id=run_id,
        mode=mode,
        drill_id="DRL-MTH-T01-C01-U01-01",
        unit_id="MTH-T01-C01-U01",
        model_id="gemini-test",
        effort="high",
        session_id="sess-1",
        sample_reason="calibration_unit",
        source_commit="abc1234",
        prior_exposure="none",
        contamination="no",
    )


def _base_payload(run_dir: Path, record_id: str = "rec-1", problem_id: str = "Q01") -> dict:
    sub_file = run_dir / "workspace" / f"{record_id}_sub.txt"
    sub_file.write_text("CANARY_RAW_SUBMISSION_TEXT_DO_NOT_LEAK", encoding="utf-8")
    return {
        "record_id": record_id,
        "problem_id": problem_id,
        "attempt_index": 1,
        "form": "direct",
        "first_submission_ref": f"workspace/{record_id}_sub.txt",
        "outcome": "correct",
        "confidence_before_feedback": "high",
        "error_origin": None,
        "planted": False,
        "solution_exposure": "none",
        "help_events": [],
        "review_verdict": "PASS",
        "caught_by": "none",
        "dispute_outcome": "not_applicable",
        "explain_status": "supported",
        "time_source": "measured",
        "active_ms": 1200,
        "tool_wait_ms": 100,
        "elapsed_ms": 1300,
        "evidence_refs": [],
    }


def _tree_hashes_outside_run(repo: Path, run_id: str) -> dict[str, str]:
    run_prefix = f"pilot/quality/{run_id}/"
    out: dict[str, str] = {}
    for p in sorted(repo.rglob("*")):
        if p.is_file() and not p.is_symlink():
            rel = p.relative_to(repo).as_posix()
            if rel == f"pilot/quality/{run_id}" or rel.startswith(run_prefix):
                continue
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_path_traversal_and_symlink_escapes_rejected(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)

    # Traversal in run_id
    for bad_id in ("../escape", "a/b", "a\\b", "..", ".hidden", "-dash", "run..1"):
        with pytest.raises(ValueError):
            _init_clean_run(repo, run_id=bad_id)

    # Symlink at pilot/quality escapes repo
    outside = tmp_path.parent / f"{tmp_path.name}_outside"
    outside.mkdir()
    (repo / "pilot").mkdir()
    (repo / "pilot" / "quality").symlink_to(outside)
    with pytest.raises(ValueError, match="Symlink"):
        _init_clean_run(repo, run_id="run-sym")
    (repo / "pilot" / "quality").unlink()

    # Valid init, then test traversal / symlink refs in record
    _init_clean_run(repo, run_id="run-safe")
    run_dir = repo / "pilot" / "quality" / "run-safe"

    outside_file = outside / "secret.txt"
    outside_file.write_text("outside", encoding="utf-8")
    (run_dir / "workspace" / "link.txt").symlink_to(outside_file)

    for bad_ref in ("../../progress/DRL-MTH-T01-C01-U01-01.json", "/etc/passwd", "~/secret", "workspace/link.txt"):
        payload = _base_payload(run_dir, record_id="rec-bad-ref")
        payload["first_submission_ref"] = bad_ref
        with pytest.raises(ValueError):
            pilot_quality.record_item(repo, run_id="run-safe", payload=payload)

    # Protected learner progress cannot be referenced as evidence
    payload = _base_payload(run_dir, record_id="rec-prot")
    payload["evidence_refs"] = ["progress/DRL-MTH-T01-C01-U01-01.json"]
    with pytest.raises(ValueError, match="protected"):
        pilot_quality.record_item(repo, run_id="run-safe", payload=payload)


def test_overwrite_duplicate_attempts_and_valid_revisions(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-dup")

    # Overwrite run rejected
    with pytest.raises(FileExistsError):
        _init_clean_run(repo, run_id="run-dup")

    run_dir = repo / "pilot" / "quality" / "run-dup"
    p1 = _base_payload(run_dir, record_id="rec-1", problem_id="Q01")
    pilot_quality.record_item(repo, run_id="run-dup", payload=p1)

    # Duplicate record_id rejected
    p_dup_id = _base_payload(run_dir, record_id="rec-1", problem_id="Q02")
    with pytest.raises(ValueError, match="Duplicate record_id"):
        pilot_quality.record_item(repo, run_id="run-dup", payload=p_dup_id)

    # Duplicate (problem_id, attempt_index) without supersedes_record_id rejected
    p_dup_att = _base_payload(run_dir, record_id="rec-2", problem_id="Q01")
    with pytest.raises(ValueError, match="Duplicate attempt"):
        pilot_quality.record_item(repo, run_id="run-dup", payload=p_dup_att)

    # Non-existent supersedes_record_id rejected
    p_bad_sup = _base_payload(run_dir, record_id="rec-2", problem_id="Q01")
    p_bad_sup["supersedes_record_id"] = "rec-missing"
    with pytest.raises(ValueError, match="supersedes_record_id"):
        pilot_quality.record_item(repo, run_id="run-dup", payload=p_bad_sup)

    # Valid revision referencing rec-1 succeeds and replaces rec-1 in active summary counts
    p_rev = _base_payload(run_dir, record_id="rec-1-rev", problem_id="Q01")
    p_rev["supersedes_record_id"] = "rec-1"
    pilot_quality.record_item(repo, run_id="run-dup", payload=p_rev)

    summary = pilot_quality.summarize_run(repo, "run-dup")
    assert summary["valid"] is True
    assert summary["coverage"]["superseded_record_ids"] == ["rec-1"]
    assert summary["coverage"]["active_record_ids"] == ["rec-1-rev"]
    assert summary["cohorts"]["natural_unassisted"]["eligible_denominator"] == 1


def test_immutable_refs_and_content_hash_detect_tampering(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-tamper")
    run_dir = repo / "pilot" / "quality" / "run-tamper"

    payload = _base_payload(run_dir, record_id="rec-1", problem_id="Q01")
    rec = pilot_quality.record_item(repo, run_id="run-tamper", payload=payload)

    snap_path = repo / rec["first_submission_snapshot"]
    assert snap_path.is_file()
    assert (snap_path.stat().st_mode & 0o777) == 0o444

    assert pilot_quality.validate_run(repo, "run-tamper")["valid"] is True

    # Tamper with referenced submission file after record
    (run_dir / "workspace" / "rec-1_sub.txt").write_text("MUTATED_AFTER_RECORD", encoding="utf-8")
    res_ref_tamper = pilot_quality.validate_run(repo, "run-tamper")
    assert res_ref_tamper["valid"] is False
    assert res_ref_tamper["tampering_detected"] is True
    assert res_ref_tamper["clean_run_eligible"] is False

    # Restore ref, then tamper with snapshot file
    (run_dir / "workspace" / "rec-1_sub.txt").write_text("CANARY_RAW_SUBMISSION_TEXT_DO_NOT_LEAK", encoding="utf-8")
    os.chmod(snap_path, 0o644)
    snap_path.write_text("TAMPERED_SNAPSHOT", encoding="utf-8")
    res_snap_tamper = pilot_quality.validate_run(repo, "run-tamper")
    assert res_snap_tamper["valid"] is False
    assert res_snap_tamper["tampering_detected"] is True

    # Restore snapshot, then edit drill source file -> content_sha256 mismatch
    snap_path.write_text("CANARY_RAW_SUBMISSION_TEXT_DO_NOT_LEAK", encoding="utf-8")
    os.chmod(snap_path, 0o444)
    drill_file = repo / "drills" / "data" / "MTH-T01-C01-U01" / "DRL-MTH-T01-C01-U01-01.json"
    drill_file.write_text(drill_file.read_text(encoding="utf-8") + " ", encoding="utf-8")
    res_hash = pilot_quality.validate_run(repo, "run-tamper")
    assert res_hash["valid"] is False
    assert res_hash["content_hash_ok"] is False
    assert res_hash["clean_run_eligible"] is False


def test_unknown_vs_false_injection_and_contamination_separation(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)

    # 1. Clean natural run: Q01 has planted=False (counted), Q02 has planted=None (unknown -> excluded)
    _init_clean_run(repo, run_id="run-nat")
    nat_dir = repo / "pilot" / "quality" / "run-nat"

    # Reject non-bool ints/strings for planted, and reject planted=True in natural_attempt
    for bad_planted in (0, 1, "false", True):
        bad = _base_payload(nat_dir, record_id="rec-bad-p", problem_id="Q01")
        bad["planted"] = bad_planted
        with pytest.raises(ValueError):
            pilot_quality.record_item(repo, run_id="run-nat", payload=bad)

    p_clean = _base_payload(nat_dir, record_id="rec-q1", problem_id="Q01")
    p_clean["outcome"] = "incorrect"
    p_clean["error_origin"] = "spontaneous"
    pilot_quality.record_item(repo, run_id="run-nat", payload=p_clean)

    p_unk = _base_payload(nat_dir, record_id="rec-q2", problem_id="Q02")
    p_unk["outcome"] = "incorrect"
    p_unk["error_origin"] = "unknown"
    p_unk["planted"] = None
    p_unk["missing_reasons"] = {"planted": "historical_provenance_unrecorded"}
    pilot_quality.record_item(repo, run_id="run-nat", payload=p_unk)

    nat_summary = pilot_quality.summarize_run(repo, "run-nat")
    assert nat_summary["clean_run_eligible"] is True
    assert nat_summary["cohorts"]["natural_unassisted"]["eligible_denominator"] == 1
    assert nat_summary["cohorts"]["natural_unassisted"]["incorrect"] == 1
    assert nat_summary["cohorts"]["excluded_or_unknown"]["planted_unknown"] == 1
    assert nat_summary["cohorts"]["fault_injection"]["total_records"] == 0

    # 2. Unknown-contamination run is NEVER counted clean
    pilot_quality.init_run(
        repo,
        run_id="run-unk-contam",
        mode="natural_attempt",
        drill_id="DRL-MTH-T01-C01-U01-01",
        unit_id="MTH-T01-C01-U01",
        model_id=None,
        effort=None,
        session_id=None,
        sample_reason="retrospective_check",
        prior_exposure="none",
        contamination="unknown",
        missing_reasons={"model_id": "not_logged", "effort": "not_logged", "session_id": "not_logged"},
    )
    unk_dir = repo / "pilot" / "quality" / "run-unk-contam"
    pilot_quality.record_item(repo, run_id="run-unk-contam", payload=_base_payload(unk_dir, "rec-u1", "Q01"))
    unk_summary = pilot_quality.summarize_run(repo, "run-unk-contam")
    assert unk_summary["valid"] is True
    assert unk_summary["clean_run_eligible"] is False
    assert "contamination=unknown" in unk_summary["exclusion_reasons"]
    assert unk_summary["cohorts"]["natural_unassisted"]["eligible_denominator"] == 0
    assert unk_summary["cohorts"]["excluded_or_unknown"]["run_contaminated_or_unknown"] == 1

    # 3. Fault-injection run is separated into fault_injection cohort, never natural
    _init_clean_run(repo, run_id="run-inj", mode="fault_injection")
    inj_dir = repo / "pilot" / "quality" / "run-inj"
    (inj_dir / "workspace" / "manifest.json").write_text('{"id": "M1"}', encoding="utf-8")
    p_inj = _base_payload(inj_dir, record_id="rec-i1", problem_id="Q01")
    p_inj["planted"] = True
    p_inj["error_origin"] = "planted"
    p_inj["outcome"] = "incorrect"
    p_inj["plant_manifest_ref"] = "workspace/manifest.json"
    p_inj["caught_by"] = "reviewer"
    p_inj["review_verdict"] = "REVISE"
    pilot_quality.record_item(repo, run_id="run-inj", payload=p_inj)

    inj_summary = pilot_quality.summarize_run(repo, "run-inj")
    assert inj_summary["clean_run_eligible"] is False
    assert inj_summary["cohorts"]["natural_unassisted"]["eligible_denominator"] == 0
    assert inj_summary["cohorts"]["fault_injection"]["planted_true"] == 1
    assert inj_summary["cohorts"]["fault_injection"]["caught"] == 1


def test_protected_path_isolation_mismatch_and_no_content_copy(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    run_doc = _init_clean_run(repo, run_id="run-iso")

    # Snapshot must never copy protected file contents
    run_json_text = (repo / "pilot" / "quality" / "run-iso" / "run.json").read_text(encoding="utf-8")
    assert "DO_NOT_COPY_PROGRESS_BYTES" not in run_json_text
    assert "PROTECTED_WORKSPACE_CONTENT" not in run_json_text
    assert run_doc["isolation_check"]["protected_snapshot"]["roots"]["progress"]["file_count"] == 1

    # Mutate protected learner progress after init -> validate detects mismatch
    (repo / "progress" / "DRL-MTH-T01-C01-U01-01.json").write_text('{"mutated": true}', encoding="utf-8")
    res = pilot_quality.validate_run(repo, "run-iso")
    assert res["valid"] is False
    assert res["isolation_ok"] is False
    assert res["clean_run_eligible"] is False
    assert any("Protected-path isolation mismatch" in e for e in res["errors"])


def test_no_writes_outside_run_tree_and_summary_never_leaks(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    before = _tree_hashes_outside_run(repo, "run-leak")

    assert (
        pilot_quality.main(
            [
                "--repo-root",
                str(repo),
                "init",
                "--run-id",
                "run-leak",
                "--mode",
                "natural_attempt",
                "--drill-id",
                "DRL-MTH-T01-C01-U01-01",
                "--unit-id",
                "MTH-T01-C01-U01",
                "--model-id",
                "gemini-test",
                "--effort",
                "high",
                "--session-id",
                "s1",
                "--sample-reason",
                "calibration",
                "--source-commit",
                "deadbeef",
                "--prior-exposure",
                "none",
                "--contamination",
                "no",
            ]
        )
        == 0
    )

    run_dir = repo / "pilot" / "quality" / "run-leak"

    # Reject raw answer / solution / arbitrary write_path payloads
    for forbidden_key, forbidden_val in (
        ("answer", "SECRET_ANS_42"),
        ("solution_code", "return 42;"),
        ("write_path", str(tmp_path / "pwned.txt")),
        ("output_path", "../../progress/evil.json"),
    ):
        bad = _base_payload(run_dir, record_id="rec-bad", problem_id="Q01")
        bad[forbidden_key] = forbidden_val
        with pytest.raises(ValueError, match="Forbidden"):
            pilot_quality.record_item(repo, run_id="run-leak", payload=bad)
    assert not (tmp_path / "pwned.txt").exists()

    # Valid record with additional safe metadata only
    good = _base_payload(run_dir, record_id="rec-ok", problem_id="Q01")
    good["additional"] = {"calibration_tag": "CANARY_SAFE_TAG_ONLY_CHECK"}
    input_json = run_dir / "workspace" / "input.json"
    input_json.write_text(json.dumps(good), encoding="utf-8")

    assert (
        pilot_quality.main(["--repo-root", str(repo), "record", "--run-id", "run-leak", "--input", str(input_json)])
        == 0
    )
    assert pilot_quality.main(["--repo-root", str(repo), "validate", "--run-id", "run-leak"]) == 0
    assert pilot_quality.main(["--repo-root", str(repo), "summary", "--run-id", "run-leak", "--write-md"]) == 0

    after = _tree_hashes_outside_run(repo, "run-leak")
    assert after == before

    summary = pilot_quality.summarize_run(repo, "run-leak")
    summary_str = json.dumps(summary)
    summary_md = (run_dir / "summary.md").read_text(encoding="utf-8")
    for serialized in (summary_str, summary_md):
        assert "SECRET_ANS_42" not in serialized
        assert "CANARY_RAW_SUBMISSION_TEXT_DO_NOT_LEAK" not in serialized
        assert "DO_NOT_COPY_PROGRESS_BYTES" not in serialized
        assert "CANARY_SAFE_TAG_ONLY_CHECK" not in serialized


def test_safe_default_materials_and_learner_restrictions(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    run_doc = _init_clean_run(repo, run_id="run-mat")
    assert run_doc["allowed_materials"] == []

    # Canonical drill JSON, vaults, hidden files, and reference paths blocked for learner prospective modes
    (repo / "drills" / "data" / "MTH-T01-C01-U01" / ".hidden_key.txt").write_text("x", encoding="utf-8")
    for mode in ("natural_attempt", "transfer_probe"):
        for bad_mat in (
            "drills/data/MTH-T01-C01-U01/DRL-MTH-T01-C01-U01-01.json",
            "vault/MTH-T01-C01-U01.md",
            "labs/_reference/solution.ts",
            "drills/data/MTH-T01-C01-U01/.hidden_key.txt",
            "hidden_tests/case1.py",
        ):
            with pytest.raises(ValueError, match="Disallowed"):
                pilot_quality.init_run(
                    repo,
                    run_id=f"run-bad-{mode}",
                    mode=mode,
                    drill_id="DRL-MTH-T01-C01-U01-01",
                    unit_id="MTH-T01-C01-U01",
                    model_id="m",
                    effort="high",
                    session_id="s",
                    sample_reason="cal",
                    prior_exposure="none",
                    contamination="no",
                    allowed_materials=[bad_mat],
                )

    ok_doc = pilot_quality.init_run(
        repo,
        run_id="run-ok-mat",
        mode="natural_attempt",
        drill_id="DRL-MTH-T01-C01-U01-01",
        unit_id="MTH-T01-C01-U01",
        model_id="m",
        effort="high",
        session_id="s",
        sample_reason="cal",
        prior_exposure="none",
        contamination="no",
        allowed_materials=["unit:MTH-T01-C01-U01", "workspace/visible_prompt.txt"],
    )
    assert ok_doc["allowed_materials"] == ["unit:MTH-T01-C01-U01", "workspace/visible_prompt.txt"]


def test_captured_digest_filenames_allowed_and_missing_reasons_checked(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    with pytest.raises(ValueError, match="Forbidden"):
        pilot_quality.init_run(
            repo,
            run_id="run-bad-mr",
            mode="natural_attempt",
            drill_id="DRL-MTH-T01-C01-U01-01",
            unit_id="MTH-T01-C01-U01",
            model_id=None,
            effort="high",
            session_id="s",
            sample_reason="cal",
            prior_exposure="none",
            contamination="no",
            missing_reasons={"model_id": "none", "answer_key": "nope"},
        )

    _init_clean_run(repo, run_id="run-tok")
    run_dir = repo / "pilot" / "quality" / "run-tok"
    for fname in ("tokenizer.ts", "answer_notes.txt", "solution_draft.py"):
        (run_dir / "workspace" / fname).write_text(f"safe content for {fname}", encoding="utf-8")

    payload = _base_payload(run_dir, record_id="rec-tok", problem_id="Q01")
    payload["first_submission_ref"] = "workspace/tokenizer.ts"
    payload["evidence_refs"] = ["workspace/answer_notes.txt", "workspace/solution_draft.py"]
    pilot_quality.record_item(repo, run_id="run-tok", payload=payload)

    val = pilot_quality.validate_run(repo, "run-tok")
    assert val["valid"] is True
    summary = pilot_quality.summarize_run(repo, "run-tok")
    assert summary["valid"] is True


def test_validate_run_enforces_full_schema_as_structured_errors(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-val-parity")
    run_dir = repo / "pilot" / "quality" / "run-val-parity"

    bad_rec = _base_payload(run_dir, record_id="rec-bad", problem_id="Q01")
    bad_rec.update(
        {
            "schema_version": "wrong-v0",
            "run_id": "run-val-parity",
            "mode": "natural_attempt",
            "recorded_at": "NOT-A-DATE",
            "time_source": "unavailable",
            "active_ms": -5,
            "planted": True,
            "plant_manifest_ref": None,
            "error_origin": "spontaneous",
            "help_events": [{"kind": "bogus", "observed_at": "bad"}],
            "dimensions": {"bogus_dim": {}},
            "decision": "keep",
            "decision_reason": None,
            "captured_digests": {},
            "first_submission_snapshot": "workspace/outside_snap.txt",
            "first_submission_sha256": "0" * 64,
            "supersedes_record_id": ["bad"],
            "unexpected_field": 123,
            "missing_reasons": {"secret_token": "leak"},
        }
    )
    (run_dir / "workspace" / "outside_snap.txt").write_text("x", encoding="utf-8")
    (run_dir / "items.jsonl").write_text(json.dumps(bad_rec) + "\n", encoding="utf-8")

    val = pilot_quality.validate_run(repo, "run-val-parity")
    assert val["valid"] is False
    joined = "\n".join(val["errors"])
    for expected in (
        "recorded_at",
        "unavailable",
        "planted=true is forbidden",
        "help_events[0].kind",
        "unknown dimension",
        "decision_reason",
        "captured_digests missing digest",
        "unsupported key: unexpected_field",
        "Forbidden",
        "supersedes_record_id must be a non-empty string",
    ):
        assert expected in joined


def test_linear_revision_chains_reject_branching_and_attempt_mutation(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-rev")
    run_dir = repo / "pilot" / "quality" / "run-rev"

    r1 = _base_payload(run_dir, record_id="rec-1", problem_id="Q01")
    r1["outcome"] = "incorrect"
    r1["error_origin"] = "spontaneous"
    pilot_quality.record_item(repo, run_id="run-rev", payload=r1)

    # Multi-step linear revision preserving (Q01, attempt_index=1) succeeds
    r1a = _base_payload(run_dir, record_id="rec-1a", problem_id="Q01")
    r1a["supersedes_record_id"] = "rec-1"
    pilot_quality.record_item(repo, run_id="run-rev", payload=r1a)

    r1b = _base_payload(run_dir, record_id="rec-1b", problem_id="Q01")
    r1b["supersedes_record_id"] = "rec-1a"
    pilot_quality.record_item(repo, run_id="run-rev", payload=r1b)

    # Branching from already-superseded rec-1 is rejected
    r_branch = _base_payload(run_dir, record_id="rec-1-branch", problem_id="Q01")
    r_branch["supersedes_record_id"] = "rec-1"
    with pytest.raises(ValueError, match="branching forbidden"):
        pilot_quality.record_item(repo, run_id="run-rev", payload=r_branch)

    # Changing attempt_index on a revision is rejected
    r2 = _base_payload(run_dir, record_id="rec-2", problem_id="Q02")
    pilot_quality.record_item(repo, run_id="run-rev", payload=r2)
    r2_mut = _base_payload(run_dir, record_id="rec-2-mut", problem_id="Q02")
    r2_mut["supersedes_record_id"] = "rec-2"
    r2_mut["attempt_index"] = 2
    with pytest.raises(ValueError, match="changes attempt_index"):
        pilot_quality.record_item(repo, run_id="run-rev", payload=r2_mut)

    # Direct tampering in items.jsonl with branching & attempt mutation is also caught by validate_run
    items_path = run_dir / "items.jsonl"
    tampered_branch = json.loads(items_path.read_text().splitlines()[1])
    tampered_branch["record_id"] = "rec-tamper-branch"
    tampered_branch["attempt_index"] = 2
    with items_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(tampered_branch) + "\n")
    val = pilot_quality.validate_run(repo, "run-rev")
    assert val["valid"] is False
    assert any("branching forbidden" in e for e in val["errors"])


def test_cohort_accounting_help_missingness_and_probe_cleanliness(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-cohort")
    run_dir = repo / "pilot" / "quality" / "run-cohort"

    # 1. Clean assisted non-correct first attempt must be counted (never vanish)
    p_assisted_inc = _base_payload(run_dir, record_id="rec-a1", problem_id="Q01")
    p_assisted_inc["outcome"] = "incorrect"
    p_assisted_inc["error_origin"] = "spontaneous"
    p_assisted_inc["help_events"] = [{"kind": "hint", "observed_at": "2026-11-17T12:00:00Z"}]
    pilot_quality.record_item(repo, run_id="run-cohort", payload=p_assisted_inc)

    # 2. Unknown help_events (None) without missing_reasons rejected; with missing_reasons excluded from clean natural
    p_no_help = _base_payload(run_dir, record_id="rec-u-help", problem_id="Q02")
    p_no_help["help_events"] = None
    with pytest.raises(ValueError, match="help_events"):
        pilot_quality.record_item(repo, run_id="run-cohort", payload=p_no_help)
    p_no_help["missing_reasons"] = {"help_events": "help_not_observed"}
    pilot_quality.record_item(repo, run_id="run-cohort", payload=p_no_help)

    # 3. Solution-exposed probe inside natural_attempt must go to excluded_or_unknown, NOT transfer_probe
    p_probe_exp = _base_payload(run_dir, record_id="rec-p-exp", problem_id="Q02")
    p_probe_exp["attempt_index"] = 2
    p_probe_exp["solution_exposure"] = "solution"
    p_probe_exp["probe"] = {
        "probe_id": "prb-1",
        "parent_problem_id": "Q02",
        "changed_dimension": "representation",
        "unchanged_objective": True,
        "delay_ms": 0,
        "exposure": "none",
        "outcome": "correct",
        "explanation_status": "supported",
    }
    pilot_quality.record_item(repo, run_id="run-cohort", payload=p_probe_exp)

    summary = pilot_quality.summarize_run(repo, "run-cohort")
    assert summary["valid"] is True
    nat = summary["cohorts"]["natural_unassisted"]
    exc = summary["cohorts"]["excluded_or_unknown"]
    prb = summary["cohorts"]["transfer_probe"]
    assert nat["total_records"] == 1
    assert nat["assisted_non_correct"] == 1
    assert nat["eligible_denominator"] == 0
    assert exc["total_records"] == 2
    assert exc["help_events_unknown"] == 1
    assert exc["solution_exposed"] == 1
    assert prb["total_records"] == 0
    assert summary["missingness_counts"]["help_events"] == 1

    # 4. planted=False with error_origin="planted" forbidden in all modes
    _init_clean_run(repo, run_id="run-inj-bad", mode="fault_injection")
    inj_dir = repo / "pilot" / "quality" / "run-inj-bad"
    p_bad_orig = _base_payload(inj_dir, record_id="rec-bad-orig", problem_id="Q01")
    p_bad_orig["planted"] = False
    p_bad_orig["error_origin"] = "planted"
    with pytest.raises(ValueError, match="error_origin='planted' is forbidden when planted=false"):
        pilot_quality.record_item(repo, run_id="run-inj-bad", payload=p_bad_orig)

    # 5. Clean transfer_probe run counted only when clean & unexposed
    _init_clean_run(repo, run_id="run-prb-ok", mode="transfer_probe")
    prb_dir = repo / "pilot" / "quality" / "run-prb-ok"
    p_prb = _base_payload(prb_dir, record_id="rec-prb-1", problem_id="P01")
    p_prb["probe"] = {
        "probe_id": "prb-ok",
        "parent_problem_id": "Q01",
        "changed_dimension": "context",
        "unchanged_objective": True,
        "delay_ms": 1000,
        "exposure": "none",
        "outcome": "correct",
        "explanation_status": "supported",
    }
    pilot_quality.record_item(repo, run_id="run-prb-ok", payload=p_prb)
    prb_summary = pilot_quality.summarize_run(repo, "run-prb-ok")
    assert prb_summary["valid"] is True
    assert prb_summary["cohorts"]["transfer_probe"]["total_records"] == 1
    assert prb_summary["cohorts"]["transfer_probe"]["explained_supported"] == 1
    assert prb_summary["cohorts"]["natural_unassisted"]["total_records"] == 0


def test_closed_run_lifecycle_and_finish_command(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-close")
    run_dir = repo / "pilot" / "quality" / "run-close"
    pilot_quality.record_item(repo, run_id="run-close", payload=_base_payload(run_dir, "rec-1", "Q01"))

    assert pilot_quality.main(["--repo-root", str(repo), "finish", "--run-id", "run-close"]) == 0
    val = pilot_quality.validate_run(repo, "run-close")
    assert val["valid"] is True
    assert val["closed"] is True
    run_doc = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert run_doc["ended_at"] is not None
    assert "ended_at" not in run_doc["missing_reasons"]

    # Cannot record after close or finish twice
    with pytest.raises(ValueError, match="closed run"):
        pilot_quality.record_item(repo, run_id="run-close", payload=_base_payload(run_dir, "rec-2", "Q02"))
    with pytest.raises(ValueError, match="already closed"):
        pilot_quality.end_run(repo, "run-close")

    # ended_at < started_at rejected by validate_run
    run_doc["ended_at"] = "1999-01-01T00:00:00Z"
    (run_dir / "run.json").write_text(json.dumps(run_doc), encoding="utf-8")
    bad_val = pilot_quality.validate_run(repo, "run-close")
    assert bad_val["valid"] is False
    assert any("cannot precede run.started_at" in e for e in bad_val["errors"])


def test_chronological_datetime_parsing_and_fractional_seconds(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-ts")
    run_dir = repo / "pilot" / "quality" / "run-ts"

    # Impossible calendar date rejected
    bad_cal = _base_payload(run_dir, record_id="rec-bad-cal", problem_id="Q01")
    bad_cal["help_events"] = [{"kind": "hint", "observed_at": "9999-99-99T99:99:99Z"}]
    with pytest.raises(ValueError, match="valid calendar UTC timestamp"):
        pilot_quality.record_item(repo, run_id="run-ts", payload=bad_cal)

    # Fractional second after integer second accepted chronologically ('.' vs 'Z' bug fixed)
    ok_frac = _base_payload(run_dir, record_id="rec-ok-frac", problem_id="Q01")
    ok_frac["help_events"] = [
        {"kind": "hint", "observed_at": "2026-11-17T12:00:00Z"},
        {"kind": "setup", "observed_at": "2026-11-17T12:00:00.5Z"},
    ]
    pilot_quality.record_item(repo, run_id="run-ts", payload=ok_frac)
    assert pilot_quality.validate_run(repo, "run-ts")["valid"] is True

    # Out-of-order fractional timestamp rejected
    bad_order = _base_payload(run_dir, record_id="rec-bad-order", problem_id="Q02")
    bad_order["help_events"] = [
        {"kind": "hint", "observed_at": "2026-11-17T12:00:01Z"},
        {"kind": "setup", "observed_at": "2026-11-17T12:00:00.5Z"},
    ]
    with pytest.raises(ValueError, match="out of chronological order"):
        pilot_quality.record_item(repo, run_id="run-ts", payload=bad_order)


def test_no_orphan_snapshots_on_validation_failure(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-orphan")
    run_dir = repo / "pilot" / "quality" / "run-orphan"

    payload = _base_payload(run_dir, record_id="rec-1", problem_id="Q01")
    payload["confidence_before_feedback"] = None
    with pytest.raises(ValueError, match="confidence_before_feedback"):
        pilot_quality.record_item(repo, run_id="run-orphan", payload=payload)

    assert list((run_dir / "snapshots").iterdir()) == []

    # Retry with same record_id after adding missing_reasons succeeds cleanly
    payload["missing_reasons"] = {"confidence_before_feedback": "not_collected"}
    pilot_quality.record_item(repo, run_id="run-orphan", payload=payload)
    assert len(list((run_dir / "snapshots").iterdir())) == 1
    assert pilot_quality.validate_run(repo, "run-orphan")["valid"] is True


def test_retrospective_import_preserves_external_timestamps_and_isolation(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)

    # Prospective modes cannot be initialized pre-closed
    with pytest.raises(ValueError, match="retrospective mode"):
        pilot_quality.init_run(
            repo,
            run_id="run-prosp-closed",
            mode="transfer_probe",
            drill_id="DRL-MTH-T01-C01-U01-01",
            unit_id="MTH-T01-C01-U01",
            model_id="m",
            effort="high",
            session_id="s",
            sample_reason="probe",
            prior_exposure="none",
            contamination="no",
            started_at="2026-11-17T10:00:00Z",
            ended_at="2026-11-17T10:05:00Z",
        )

    run_doc = pilot_quality.init_run(
        repo,
        run_id="run-retro",
        mode="retrospective",
        drill_id="DRL-MTH-T01-C01-U01-01",
        unit_id="MTH-T01-C01-U01",
        model_id="legacy-model",
        effort=None,
        session_id=None,
        sample_reason="retrospective_import",
        prior_exposure="unknown",
        contamination="unknown",
        started_at="2026-11-10T09:00:00Z",
        ended_at="2026-11-10T10:00:00Z",
        missing_reasons={"effort": "not_logged", "session_id": "not_logged"},
    )
    assert run_doc["started_at"] == "2026-11-10T09:00:00Z"
    assert run_doc["ended_at"] == "2026-11-10T10:00:00Z"

    run_dir = repo / "pilot" / "quality" / "run-retro"
    (run_dir / "workspace" / "legacy_report.md").write_text("external report", encoding="utf-8")
    # Retrospective import uses external evidence & timestamps and cannot accept new items when already ended_at
    # (Open retrospective import before close)
    pilot_quality.init_run(
        repo,
        run_id="run-retro-open",
        mode="retrospective",
        drill_id="DRL-MTH-T01-C01-U01-01",
        unit_id="MTH-T01-C01-U01",
        model_id="legacy-model",
        effort=None,
        session_id=None,
        sample_reason="retrospective_import",
        prior_exposure="unknown",
        contamination="unknown",
        started_at="2026-11-10T09:00:00Z",
        missing_reasons={"effort": "not_logged", "session_id": "not_logged"},
    )
    open_dir = repo / "pilot" / "quality" / "run-retro-open"
    (open_dir / "workspace" / "legacy_report.md").write_text("external report", encoding="utf-8")
    retro_item = {
        "record_id": "rec-retro-1",
        "problem_id": "Q01",
        "attempt_index": 1,
        "recorded_at": "2026-11-10T09:15:00Z",
        "first_submission_ref": None,
        "evidence_refs": ["workspace/legacy_report.md"],
        "outcome": "correct",
        "confidence_before_feedback": None,
        "planted": None,
        "solution_exposure": "unknown",
        "help_events": None,
        "missing_reasons": {
            "planted": "historical_unrecorded",
            "confidence_before_feedback": "not_logged",
            "help_events": "not_logged",
        },
    }
    rec = pilot_quality.record_item(repo, run_id="run-retro-open", payload=retro_item)
    assert rec["recorded_at"] == "2026-11-10T09:15:00Z"
    assert rec["help_events"] is None
    pilot_quality.end_run(repo, "run-retro-open", ended_at="2026-11-10T10:00:00Z")

    summary = pilot_quality.summarize_run(repo, "run-retro-open")
    assert summary["valid"] is True
    assert summary["closed"] is True
    assert summary["clean_run_eligible"] is False
    assert summary["cohorts"]["retrospective"]["total_records"] == 1
    assert summary["cohorts"]["natural_unassisted"]["total_records"] == 0


def test_revision_preserves_locked_first_submission(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-lock")
    run_dir = repo / "pilot" / "quality" / "run-lock"

    # Initial Q01 attempt with sub_v1
    (run_dir / "workspace" / "sub_v1.txt").write_text("SUBMISSION_V1_BYTES", encoding="utf-8")
    (run_dir / "workspace" / "sub_v2.txt").write_text("SUBMISSION_V2_DIFFERENT_BYTES", encoding="utf-8")
    r1 = _base_payload(run_dir, record_id="rec-1", problem_id="Q01")
    r1["first_submission_ref"] = "workspace/sub_v1.txt"
    r1["outcome"] = "incorrect"
    r1["error_origin"] = "spontaneous"
    r1_saved = pilot_quality.record_item(repo, run_id="run-lock", payload=r1)

    # 1. Replacement with different submission bytes is rejected without creating an orphan snapshot
    r1_replace = _base_payload(run_dir, record_id="rec-1-replace", problem_id="Q01")
    r1_replace["supersedes_record_id"] = "rec-1"
    r1_replace["first_submission_ref"] = "workspace/sub_v2.txt"
    r1_replace["outcome"] = "correct"
    r1_replace["error_origin"] = None
    with pytest.raises(ValueError, match="first_submission_sha256"):
        pilot_quality.record_item(repo, run_id="run-lock", payload=r1_replace)
    assert [p.name for p in (run_dir / "snapshots").iterdir()] == ["rec-1_first_submission.txt"]

    # 2. Erasure (non-null -> null first_submission_ref) is rejected without orphan snapshot
    r1_erase = _base_payload(run_dir, record_id="rec-1-erase", problem_id="Q01")
    r1_erase["supersedes_record_id"] = "rec-1"
    r1_erase["first_submission_ref"] = None
    r1_erase["outcome"] = "blocked"
    r1_erase["error_origin"] = "tooling"
    r1_erase["evidence_refs"] = ["workspace/sub_v1.txt"]
    with pytest.raises(ValueError, match="first_submission_ref null/non-null"):
        pilot_quality.record_item(repo, run_id="run-lock", payload=r1_erase)
    assert [p.name for p in (run_dir / "snapshots").iterdir()] == ["rec-1_first_submission.txt"]

    # 3. Legitimate metadata/outcome adjudication on identical submission bytes succeeds; new work uses new attempt_index
    (run_dir / "workspace" / "sub_v1_copy.txt").write_text("SUBMISSION_V1_BYTES", encoding="utf-8")
    r1_adj = _base_payload(run_dir, record_id="rec-1-adj", problem_id="Q01")
    r1_adj["supersedes_record_id"] = "rec-1"
    r1_adj["first_submission_ref"] = "workspace/sub_v1_copy.txt"
    r1_adj["outcome"] = "correct"
    r1_adj["error_origin"] = None
    r1_adj["review_verdict"] = "PASS"
    pilot_quality.record_item(repo, run_id="run-lock", payload=r1_adj)

    r1_retry = _base_payload(run_dir, record_id="rec-1-att2", problem_id="Q01")
    r1_retry["attempt_index"] = 2
    r1_retry["first_submission_ref"] = "workspace/sub_v2.txt"
    pilot_quality.record_item(repo, run_id="run-lock", payload=r1_retry)

    # 4. Null -> non-null transition on Q02 blocked item is rejected without orphan snapshot
    r2_blocked = _base_payload(run_dir, record_id="rec-2", problem_id="Q02")
    r2_blocked["first_submission_ref"] = None
    r2_blocked["outcome"] = "blocked"
    r2_blocked["error_origin"] = "tooling"
    r2_blocked["evidence_refs"] = ["workspace/sub_v1.txt"]
    pilot_quality.record_item(repo, run_id="run-lock", payload=r2_blocked)

    r2_attach = _base_payload(run_dir, record_id="rec-2-attach", problem_id="Q02")
    r2_attach["supersedes_record_id"] = "rec-2"
    r2_attach["first_submission_ref"] = "workspace/sub_v2.txt"
    with pytest.raises(ValueError, match="first_submission_ref null/non-null"):
        pilot_quality.record_item(repo, run_id="run-lock", payload=r2_attach)
    assert not (run_dir / "snapshots" / "rec-2-attach_first_submission.txt").exists()

    # Null -> null metadata revision on blocked item succeeds
    r2_rev = _base_payload(run_dir, record_id="rec-2-rev", problem_id="Q02")
    r2_rev["supersedes_record_id"] = "rec-2"
    r2_rev["first_submission_ref"] = None
    r2_rev["outcome"] = "blocked"
    r2_rev["error_origin"] = "ambiguous"
    r2_rev["evidence_refs"] = ["workspace/sub_v1.txt"]
    pilot_quality.record_item(repo, run_id="run-lock", payload=r2_rev)
    assert pilot_quality.validate_run(repo, "run-lock")["valid"] is True

    # 5. Raw stored-record tampering in items.jsonl (replacement & erasure) is caught by validate_run
    items_path = run_dir / "items.jsonl"
    orig_lines = items_path.read_text(encoding="utf-8").splitlines()

    v2_bytes = (run_dir / "workspace" / "sub_v2.txt").read_bytes()
    v2_sha = hashlib.sha256(v2_bytes).hexdigest()
    tamper_snap = run_dir / "snapshots" / "rec-tamper-replace_first_submission.txt"
    tamper_snap.write_bytes(v2_bytes)
    os.chmod(tamper_snap, 0o444)
    tampered_replace = dict(r1_saved)
    tampered_replace.update(
        {
            "record_id": "rec-tamper-replace",
            "supersedes_record_id": "rec-1-adj",
            "first_submission_ref": "pilot/quality/run-lock/workspace/sub_v2.txt",
            "first_submission_snapshot": "pilot/quality/run-lock/snapshots/rec-tamper-replace_first_submission.txt",
            "first_submission_sha256": v2_sha,
            "captured_digests": {"pilot/quality/run-lock/workspace/sub_v2.txt": v2_sha},
        }
    )
    items_path.write_text("\n".join([*orig_lines, json.dumps(tampered_replace)]) + "\n", encoding="utf-8")
    val_replace = pilot_quality.validate_run(repo, "run-lock")
    assert val_replace["valid"] is False
    assert any("first_submission_sha256" in e for e in val_replace["errors"])

    tampered_erase = dict(r1_saved)
    tampered_erase.update(
        {
            "record_id": "rec-tamper-erase",
            "supersedes_record_id": "rec-1-adj",
            "first_submission_ref": None,
            "first_submission_snapshot": None,
            "first_submission_sha256": None,
            "outcome": "blocked",
            "evidence_refs": ["pilot/quality/run-lock/workspace/sub_v1.txt"],
            "captured_digests": {
                "pilot/quality/run-lock/workspace/sub_v1.txt": hashlib.sha256(
                    (run_dir / "workspace" / "sub_v1.txt").read_bytes()
                ).hexdigest()
            },
        }
    )
    items_path.write_text("\n".join([*orig_lines, json.dumps(tampered_erase)]) + "\n", encoding="utf-8")
    val_erase = pilot_quality.validate_run(repo, "run-lock")
    assert val_erase["valid"] is False
    assert any("first_submission_ref null/non-null" in e for e in val_erase["errors"])


def test_closed_clean_run_remains_valid_after_subsequent_progress_edit(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-clean-closed")
    run_dir = repo / "pilot" / "quality" / "run-clean-closed"
    pilot_quality.record_item(repo, run_id="run-clean-closed", payload=_base_payload(run_dir, "rec-1", "Q01"))

    finished = pilot_quality.end_run(repo, "run-clean-closed")
    assert finished["closure_status"] == "closed"
    assert finished["closed_observed_at"] is not None
    assert finished["isolation_check"]["end_protected_snapshot"]["roots"]["progress"]["file_count"] == 1

    # Subsequent user activity in protected paths must NOT invalidate an already-finished run
    (repo / "progress" / "DRL-MTH-T01-C01-U01-01.json").write_text('{"studio_click": true}', encoding="utf-8")
    (repo / "drills" / "workspace" / "DRL-MTH-T01-C01-U01-01" / "Q01.txt").write_text(
        "USER_EDITED_AFTER_CLOSE", encoding="utf-8"
    )

    val = pilot_quality.validate_run(repo, "run-clean-closed")
    assert val["valid"] is True
    assert val["closed"] is True
    assert val["closure_status"] == "closed"
    assert val["isolation_ok"] is True
    assert val["isolation_status"] == "verified"
    assert val["clean_run_eligible"] is True

    summary = pilot_quality.summarize_run(repo, "run-clean-closed")
    assert summary["clean_run_eligible"] is True
    assert summary["cohorts"]["natural_unassisted"]["eligible_denominator"] == 1
    assert summary["cohorts"]["natural_unassisted"]["first_attempt_correct"] == 1


def test_open_isolation_mismatch_blocks_finish(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _init_clean_run(repo, run_id="run-open-mismatch")
    run_dir = repo / "pilot" / "quality" / "run-open-mismatch"
    pilot_quality.record_item(repo, run_id="run-open-mismatch", payload=_base_payload(run_dir, "rec-1", "Q01"))

    (repo / "progress" / "DRL-MTH-T01-C01-U01-01.json").write_text('{"late_studio_click": 1}', encoding="utf-8")

    with pytest.raises(ValueError, match="Protected-path isolation mismatch"):
        pilot_quality.end_run(repo, "run-open-mismatch")
    assert pilot_quality.main(["--repo-root", str(repo), "finish", "--run-id", "run-open-mismatch"]) != 0

    run_doc = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert run_doc["ended_at"] is None
    assert run_doc["closure_status"] == "open"
    assert "end_protected_snapshot" not in run_doc["isolation_check"]


def test_quarantine_captures_mismatch_and_excludes_from_clean_cohorts(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    init_nat = pilot_quality.init_run(
        repo,
        run_id="run-q-nat",
        mode="natural_attempt",
        drill_id="DRL-MTH-T01-C01-U01-01",
        unit_id="MTH-T01-C01-U01",
        model_id="gemini-test",
        effort="high",
        session_id="sess-1",
        sample_reason="calibration_unit",
        source_commit="abc1234",
        started_at="2026-11-17T07:35:00Z",
        prior_exposure="none",
        contamination="no",
    )
    nat_dir = repo / "pilot" / "quality" / "run-q-nat"
    rec_nat = pilot_quality.record_item(repo, run_id="run-q-nat", payload=_base_payload(nat_dir, "rec-1", "Q01"))

    _init_clean_run(repo, run_id="run-q-prb", mode="transfer_probe")
    prb_dir = repo / "pilot" / "quality" / "run-q-prb"
    p_prb = _base_payload(prb_dir, "rec-p1", "P01")
    p_prb["probe"] = {
        "probe_id": "prb-1",
        "parent_problem_id": "Q01",
        "changed_dimension": "representation",
        "unchanged_objective": True,
        "delay_ms": 500,
        "exposure": "none",
        "outcome": "correct",
        "explanation_status": "supported",
    }
    pilot_quality.record_item(repo, run_id="run-q-prb", payload=p_prb)

    # Real user activity changes protected progress before late closeout
    (repo / "progress" / "DRL-MTH-T01-C01-U01-01.json").write_text('{"user_clicked_studio": true}', encoding="utf-8")
    note_file = nat_dir / "workspace" / "interruption_note.md"
    note_file.write_text("User confirmed Studio click between 07:41Z and 11:23Z.", encoding="utf-8")

    # Empty reason and unsafe evidence_ref rejected
    with pytest.raises(ValueError, match="non-empty"):
        pilot_quality.quarantine_run(repo, "run-q-nat", reason="   ")
    with pytest.raises(ValueError, match="protected"):
        pilot_quality.quarantine_run(
            repo,
            "run-q-nat",
            reason="User activity",
            evidence_ref="progress/DRL-MTH-T01-C01-U01-01.json",
        )

    q_nat = pilot_quality.quarantine_run(
        repo,
        "run-q-nat",
        reason="Thread interrupted; user confirmed Studio click before late closeout",
        evidence_ref="workspace/interruption_note.md",
        ended_at="2026-11-17T07:41:00Z",
    )
    assert q_nat["closure_status"] == "quarantined"
    assert q_nat["ended_at"] == "2026-11-17T07:41:00Z"
    assert q_nat["closed_observed_at"] is not None
    assert q_nat["isolation_check"]["protected_snapshot"] == init_nat["isolation_check"]["protected_snapshot"]
    assert q_nat["isolation_check"]["end_protected_snapshot"]["captured_at"] is not None
    assert q_nat["quarantine"]["evidence_ref"] == "pilot/quality/run-q-nat/workspace/interruption_note.md"
    assert q_nat["quarantine"]["evidence_sha256"] == hashlib.sha256(note_file.read_bytes()).hexdigest()
    assert any("progress:" in m for m in q_nat["quarantine"]["isolation_mismatches"])

    # CLI close-incomplete / quarantine works on transfer_probe run
    assert (
        pilot_quality.main(
            [
                "--repo-root",
                str(repo),
                "close-incomplete",
                "--run-id",
                "run-q-prb",
                "--reason",
                "Interrupted probe before late closeout",
            ]
        )
        == 0
    )

    # Subsequent progress edit leaves quarantined runs readable/valid while permanently non-clean
    (repo / "progress" / "DRL-MTH-T01-C01-U01-01.json").write_text('{"more_later_edits": 2}', encoding="utf-8")

    for rid, expected_snap in (("run-q-nat", rec_nat["first_submission_sha256"]), ("run-q-prb", None)):
        val = pilot_quality.validate_run(repo, rid)
        assert val["valid"] is True
        assert val["closed"] is True
        assert val["closure_status"] == "quarantined"
        assert val["isolation_status"] == "quarantined"
        assert val["isolation_ok"] is False
        assert val["clean_run_eligible"] is False
        assert "quarantined" in val["exclusion_reasons"]
        assert "run_quarantined" in val["warnings"]
        if expected_snap:
            items = [
                json.loads(line) for line in (repo / "pilot" / "quality" / rid / "items.jsonl").read_text().splitlines()
            ]
            assert items[0]["first_submission_sha256"] == expected_snap

        summary = pilot_quality.summarize_run(repo, rid, write_md=True)
        assert summary["cohorts"]["natural_unassisted"]["total_records"] == 0
        assert summary["cohorts"]["natural_unassisted"]["eligible_denominator"] == 0
        assert summary["cohorts"]["transfer_probe"]["total_records"] == 0
        assert summary["cohorts"]["excluded_or_unknown"]["total_records"] == 1
        assert summary["cohorts"]["excluded_or_unknown"]["run_quarantined"] == 1
        md = (repo / "pilot" / "quality" / rid / "summary.md").read_text(encoding="utf-8")
        assert "CANARY_RAW_SUBMISSION_TEXT_DO_NOT_LEAK" not in md
        assert "SECRET_ANS_42" not in md

    # Cannot record, finish, or quarantine again after quarantine
    with pytest.raises(ValueError, match="closed run"):
        pilot_quality.record_item(repo, run_id="run-q-nat", payload=_base_payload(nat_dir, "rec-2", "Q02"))
    with pytest.raises(ValueError, match="already closed"):
        pilot_quality.end_run(repo, "run-q-nat")
    with pytest.raises(ValueError, match="already closed"):
        pilot_quality.quarantine_run(repo, "run-q-nat", reason="again")

    # Tampering with quarantine evidence file is caught
    note_file.write_text("TAMPERED_NOTE", encoding="utf-8")
    tampered_val = pilot_quality.validate_run(repo, "run-q-nat")
    assert tampered_val["valid"] is False
    assert tampered_val["tampering_detected"] is True


def test_legacy_run_missing_final_snapshot_is_readable_unknown_and_excluded(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)

    for rid, mode in (("run-leg-nat", "natural_attempt"), ("run-leg-retro", "retrospective")):
        _init_clean_run(repo, run_id=rid, mode=mode)
        rdir = repo / "pilot" / "quality" / rid
        pilot_quality.record_item(repo, run_id=rid, payload=_base_payload(rdir, f"rec-{rid}", "Q01"))
        run_path = rdir / "run.json"
        legacy_doc = json.loads(run_path.read_text(encoding="utf-8"))
        # Strip new lifecycle fields to simulate an already-ended pre-fix run.json
        for k in ("closure_status", "closed_observed_at", "quarantine"):
            legacy_doc.pop(k, None)
        legacy_doc["isolation_check"].pop("end_protected_snapshot", None)
        legacy_doc["started_at"] = "2026-11-17T07:30:00Z"
        legacy_doc["ended_at"] = "2026-11-17T07:40:00Z"
        legacy_doc["missing_reasons"].pop("ended_at", None)
        run_path.write_text(json.dumps(legacy_doc, indent=2) + "\n", encoding="utf-8")

    # Subsequent live progress change must not fail readability or invent an end snapshot
    (repo / "progress" / "DRL-MTH-T01-C01-U01-01.json").write_text('{"later_change": true}', encoding="utf-8")

    nat_val = pilot_quality.validate_run(repo, "run-leg-nat")
    assert nat_val["valid"] is True
    assert nat_val["closed"] is True
    assert nat_val["isolation_status"] == "unknown"
    assert nat_val["isolation_ok"] is None
    assert nat_val["clean_run_eligible"] is False
    assert "isolation_unknown" in nat_val["exclusion_reasons"]
    assert "missing_end_protected_snapshot" in nat_val["warnings"]

    # Confirm no invented end_protected_snapshot was backfilled on disk
    persisted = json.loads((repo / "pilot" / "quality" / "run-leg-nat" / "run.json").read_text(encoding="utf-8"))
    assert "end_protected_snapshot" not in persisted["isolation_check"]

    nat_sum = pilot_quality.summarize_run(repo, "run-leg-nat")
    assert nat_sum["cohorts"]["natural_unassisted"]["eligible_denominator"] == 0
    assert nat_sum["cohorts"]["excluded_or_unknown"]["run_isolation_unknown"] == 1

    retro_sum = pilot_quality.summarize_run(repo, "run-leg-retro")
    assert retro_sum["valid"] is True
    assert retro_sum["clean_run_eligible"] is False
    assert retro_sum["isolation_status"] == "unknown"
    assert retro_sum["cohorts"]["retrospective"]["total_records"] == 1
    assert retro_sum["cohorts"]["natural_unassisted"]["total_records"] == 0


def test_invalid_source_or_submission_cannot_quarantine_past_integrity_errors(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)

    # 1. Source content_sha256 mismatch cannot be quarantined
    _init_clean_run(repo, run_id="run-bad-src")
    (repo / "progress" / "DRL-MTH-T01-C01-U01-01.json").write_text('{"click": 1}', encoding="utf-8")
    drill_file = repo / "drills" / "data" / "MTH-T01-C01-U01" / "DRL-MTH-T01-C01-U01-01.json"
    orig_drill = drill_file.read_text(encoding="utf-8")
    drill_file.write_text(orig_drill + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity/schema"):
        pilot_quality.quarantine_run(repo, "run-bad-src", reason="try bypass source mismatch")
    assert json.loads((repo / "pilot" / "quality" / "run-bad-src" / "run.json").read_text())["ended_at"] is None
    drill_file.write_text(orig_drill, encoding="utf-8")

    # 2. Tampered submission snapshot cannot be quarantined
    _init_clean_run(repo, run_id="run-bad-sub")
    sub_dir = repo / "pilot" / "quality" / "run-bad-sub"
    rec = pilot_quality.record_item(repo, run_id="run-bad-sub", payload=_base_payload(sub_dir, "rec-1", "Q01"))
    snap_path = repo / rec["first_submission_snapshot"]
    os.chmod(snap_path, 0o644)
    snap_path.write_text("CORRUPTED_SNAPSHOT", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity/schema"):
        pilot_quality.quarantine_run(repo, "run-bad-sub", reason="try bypass tampered submission")
    assert json.loads((sub_dir / "run.json").read_text())["ended_at"] is None

    # 3. Corrupted items.jsonl schema cannot be quarantined
    _init_clean_run(repo, run_id="run-bad-items")
    bad_dir = repo / "pilot" / "quality" / "run-bad-items"
    (bad_dir / "items.jsonl").write_text("{not valid json\n", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity/schema"):
        pilot_quality.quarantine_run(repo, "run-bad-items", reason="try bypass corrupt items")
    assert json.loads((bad_dir / "run.json").read_text())["ended_at"] is None


def test_unchanged_workspace_scaffold_symlinks_pass_finish_while_unexpected_fail(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    (repo / "code_engine").mkdir()
    (repo / "tools" / "lint" / "node_modules").mkdir(parents=True)

    ws_drill = repo / "drills" / "workspace" / "DRL-PRG-T01-C01-U01-01"
    ws_drill.mkdir(parents=True)
    (ws_drill / "Q01_demo.js").write_text("module.exports = {};\n", encoding="utf-8")
    (ws_drill / "code_engine").symlink_to(repo / "code_engine", target_is_directory=True)
    (ws_drill / "node_modules").symlink_to(repo / "tools" / "lint" / "node_modules", target_is_directory=True)

    _init_clean_run(repo, run_id="run-ws-ok")
    run_dir = repo / "pilot" / "quality" / "run-ws-ok"
    pilot_quality.record_item(repo, run_id="run-ws-ok", payload=_base_payload(run_dir, "rec-1", "Q01"))
    closed = pilot_quality.end_run(repo, "run-ws-ok")
    assert closed["closure_status"] == "closed"

    # Unexpected symlink outside the allowed scaffold names/targets must still be rejected on finish/validate
    outside = tmp_path.parent / f"{tmp_path.name}_escape"
    outside.mkdir()
    (ws_drill / "extra_link").symlink_to(outside, target_is_directory=True)
    pilot_quality.init_run(
        repo,
        run_id="run-ws-bad-sym",
        mode="natural_attempt",
        drill_id="DRL-MTH-T01-C01-U01-01",
        unit_id="MTH-T01-C01-U01",
        model_id="gemini-4-hydrogen-high",
        effort="high",
        session_id="sess-test",
        sample_reason="bad-symlink-check",
        prior_exposure="none",
        contamination="no",
    )
    with pytest.raises(ValueError, match="symlinks found"):
        pilot_quality.end_run(repo, "run-ws-bad-sym")
    (ws_drill / "extra_link").unlink()

    # Mutating a scaffold symlink after init must fail finish
    _init_clean_run(repo, run_id="run-ws-mut")
    (ws_drill / "code_engine").unlink()
    with pytest.raises(ValueError, match="scaffold symlinks changed"):
        pilot_quality.end_run(repo, "run-ws-mut")
