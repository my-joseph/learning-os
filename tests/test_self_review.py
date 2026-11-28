"""Tests for scripts/issues.py extensions (--target, propose) and scripts/self_review.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import issues as il
from scripts import self_review as sr


@pytest.fixture
def tmp_issue_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "issues" / "log.jsonl"
    monkeypatch.setenv("LEARNINGOS_ISSUE_LOG", str(path))
    return path


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. scripts/issues.py: propose, --target, and backward compatibility
# ---------------------------------------------------------------------------


def test_issues_propose_roundtrip_and_cli(tmp_issue_log: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = il.main(
        [
            "propose",
            "--target",
            "skill:new-math-drill",
            "--evidence",
            "DRL-MTH-T02-C01-U01-05/Q04",
            "--proposal",
            "Require unit-convention check before blind solve",
            "--impact",
            "high",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Logged proposal" in out

    # Duplicate pending proposal is not added twice
    rc2 = il.main(
        [
            "propose",
            "--target",
            "skill:new-math-drill",
            "--evidence",
            "DRL-MTH-T02-C01-U01-05/Q04",
            "--proposal",
            "Require unit-convention check before blind solve",
            "--impact",
            "high",
        ]
    )
    assert rc2 == 0
    assert "Already logged proposal" in capsys.readouterr().out

    recs = il.issues(str(tmp_issue_log))
    assert len(recs) == 1
    rec = recs[0]
    assert rec["kind"] == "proposal"
    assert rec["target"] == "skill:new-math-drill"
    assert rec["impact"] == "high"
    assert rec["evidence"] == "DRL-MTH-T02-C01-U01-05/Q04"
    assert rec["proposal"] == "Require unit-convention check before blind solve"
    assert rec["where"] == rec["evidence"]
    assert rec["what"] == rec["proposal"]
    assert rec["resolved"] is None

    assert il.main(["list", "--target", "skill:new-math-drill"]) == 0
    listed = capsys.readouterr().out
    assert "proposal [skill:new-math-drill impact=high]" in listed

    assert il.main(["resolve", rec["id"], "--note", "PR #299"]) == 0
    capsys.readouterr()
    assert "nothing pending" in il.summary(str(tmp_issue_log))


def test_issues_add_with_target_and_validation(tmp_issue_log: Path) -> None:
    iid, created = il.add_issue(
        "gate-gap",
        "batch",
        "reviewer",
        "math_engine/ai_drill_ingest.py:120",
        "Missed duplicate option label",
        target="engine",
    )
    assert created
    (rec,) = il.issues(str(tmp_issue_log))
    assert rec["id"] == iid
    assert rec["target"] == "engine"

    # Valid namespaced targets
    for target in ("skill:health-check", "model:gpt-6-luna", "job:fix", "gate:ai_drill_ingest", "docs", "ci", "studio"):
        assert il.validate_target(target) == target

    # Invalid targets and impact rejected
    for bad in ("", "   ", "unknown-area", "foo:bar", "skill:", "skill:bad space"):
        with pytest.raises(ValueError):
            il.validate_target(bad)
    with pytest.raises(ValueError, match="impact"):
        il.propose_issue("engine", "ev", "prop", impact="critical", path=str(tmp_issue_log))


def test_old_log_lines_remain_backward_compatible(tmp_issue_log: Path) -> None:
    legacy_records = [
        {
            "id": "aa11bb",
            "date": "2026-11-18 10:00 UTC",
            "kind": "ambiguity",
            "severity": "batch",
            "source": "reviewer",
            "where": "DRL-MTH-T01-C07-03/Q05",
            "what": "MB could be 1000 or 1024 kB",
            "action": "auto-fixed",
        },
        {
            "id": "cc22dd",
            "date": "2026-11-19 11:00 UTC",
            "kind": "bug",
            "severity": "urgent",
            "source": "learner",
            "where": "practice-studio/src/app/api/sync-notion/route.ts",
            "what": "Sync overwrote server fields",
            "action": "open",
        },
        {
            "resolves": "aa11bb",
            "date": "2026-11-19 12:00 UTC",
            "note": "PR #120",
        },
    ]
    _write_jsonl(tmp_issue_log, legacy_records)

    loaded = il.issues(str(tmp_issue_log))
    assert len(loaded) == 2
    assert loaded[0]["resolved"] == "2026-11-19 12:00 UTC: PR #120"
    assert loaded[1]["resolved"] is None
    assert "target" not in loaded[1]

    # Dedup against legacy record without target
    dup_id, created = il.add_issue(
        "bug",
        "urgent",
        "learner",
        "practice-studio/src/app/api/sync-notion/route.ts",
        "Sync overwrote server fields",
        path=str(tmp_issue_log),
    )
    assert (dup_id, created) == ("cc22dd", False)

    # Legacy summary line format preserved
    summary_text = il.summary(str(tmp_issue_log))
    assert "[cc22dd] URGENT bug (open, learner)" in summary_text


# ---------------------------------------------------------------------------
# 2. scripts/self_review.py: issues, usage, git/gh, drill-quality, doc_refs
# ---------------------------------------------------------------------------


def test_self_review_issues_signals_recurring_proposals_and_since(tmp_path: Path) -> None:
    log_file = tmp_path / "issues" / "log.jsonl"
    _write_jsonl(
        log_file,
        [
            # Old record before --since cutoff
            {
                "id": "old001",
                "date": "2026-11-01 09:00 UTC",
                "kind": "rule-gap",
                "severity": "batch",
                "source": "author",
                "where": ".claude/skills/start-unit/SKILL.md",
                "what": "Old friction",
                "action": "open",
                "target": "skill:start-unit",
            },
            # Open explicit proposal
            {
                "id": "prop01",
                "date": "2026-11-20 10:00 UTC",
                "kind": "proposal",
                "severity": "batch",
                "source": "author",
                "where": "PR #282",
                "what": "Merge origin/main before opening PR",
                "action": "open",
                "target": "skill:dispatch-worker",
                "evidence": "PR #282",
                "proposal": "Merge origin/main before opening PR",
                "impact": "high",
            },
            # Two reviewer catches of kind reasoning -> gate-gap proposal
            {
                "id": "rev001",
                "date": "2026-11-21 08:00 UTC",
                "kind": "reasoning",
                "severity": "batch",
                "source": "reviewer",
                "where": "MTH-T02-C01-U01/Q02",
                "what": "trapDerivation subtracted unrelated givens",
                "action": "auto-fixed",
                "target": "content",
            },
            {
                "id": "rev002",
                "date": "2026-11-21 09:00 UTC",
                "kind": "reasoning",
                "severity": "batch",
                "source": "reviewer",
                "where": "MTH-T02-C01-U01/Q08",
                "what": "trapDerivation ignored rejected root",
                "action": "auto-fixed",
                "target": "content",
            },
            # Explicit open gate-gap
            {
                "id": "gg0001",
                "date": "2026-11-21 10:00 UTC",
                "kind": "gate-gap",
                "severity": "batch",
                "source": "reviewer",
                "where": "math_engine/ai_drill_ingest.py",
                "what": "Allowed malformed interval",
                "action": "open",
                "target": "engine",
            },
            # Recurring tool-gap on pipeline (2x)
            {
                "id": "tg0001",
                "date": "2026-11-21 11:00 UTC",
                "kind": "tool-gap",
                "severity": "batch",
                "source": "author",
                "where": "scripts/source_gap.py",
                "what": "Gap 1",
                "action": "open",
                "target": "pipeline",
            },
            {
                "id": "tg0002",
                "date": "2026-11-21 12:00 UTC",
                "kind": "tool-gap",
                "severity": "batch",
                "source": "author",
                "where": "scripts/source_find.py",
                "what": "Gap 2",
                "action": "open",
                "target": "pipeline",
            },
            # Resolved duplicate pair should not surface as active recurring issue by default
            {
                "id": "res001",
                "date": "2026-11-21 07:00 UTC",
                "kind": "bug",
                "severity": "batch",
                "source": "author",
                "where": "practice-studio/src/a.tsx",
                "what": "Old fixed bug 1",
                "action": "open",
                "target": "studio",
            },
            {
                "id": "res002",
                "date": "2026-11-21 07:30 UTC",
                "kind": "bug",
                "severity": "batch",
                "source": "author",
                "where": "practice-studio/src/b.tsx",
                "what": "Old fixed bug 2",
                "action": "open",
                "target": "studio",
            },
            {"resolves": "res001", "date": "2026-11-21 08:00 UTC", "note": "PR #250"},
            {"resolves": "res002", "date": "2026-11-21 08:00 UTC", "note": "PR #250"},
        ],
    )

    sig, props = sr.collect_issue_signals(issues_path=str(log_file), since="2026-11-15")
    assert sig["totalRecords"] == 8  # old001 excluded
    assert sig["openProposals"] == 1

    by_key = {(p["target"], p["category"]): p for p in props}
    assert ("skill:dispatch-worker", "open-proposal") in by_key
    assert (
        by_key[("skill:dispatch-worker", "open-proposal")]["playbook"] == "edit .claude/skills/dispatch-worker/SKILL.md"
    )
    assert ("content", "gate-gap") in by_key
    assert "missed 2 reviewer catch(es) of kind reasoning" in by_key[("content", "gate-gap")]["suggestedChange"]
    assert ("engine", "gate-gap") in by_key
    assert ("pipeline", "recurring-issue") in by_key
    assert by_key[("pipeline", "recurring-issue")]["playbook"] == "improve pipeline"
    assert ("studio", "recurring-issue") not in by_key

    all_sig, _ = sr.collect_issue_signals(issues_path=str(log_file), include_resolved=True)
    resolved_pattern = next(p for p in all_sig["recurringPatterns"] if p["target"] == "studio")
    assert resolved_pattern["count"] == 2
    assert resolved_pattern["pending"] == 0


def test_self_review_usage_signals_failures_fallbacks_revisions_and_cost(tmp_path: Path) -> None:
    usage_file = tmp_path / "pilot" / "agent-usage.jsonl"
    _write_jsonl(
        usage_file,
        [
            # Branch 1: model-a fails rc=3 -> falls back to model-b 5 min later
            {
                "ts": "2026-11-20T10:00:00",
                "model": "gemini-4-neon-high",
                "branch": "feat/feature-a",
                "outcome": "rc=3",
                "status": "ERROR",
                "duration_seconds": 600,
                "total_tokens": 500_000,
                "output_tokens": 20_000,
            },
            {
                "ts": "2026-11-20T10:05:00",
                "model": "gemini-4-argon-high",
                "branch": "feat/feature-a",
                "outcome": "rc=0",
                "status": "SUCCESS",
                "duration_seconds": 1800,
                "total_tokens": 3_500_000,
                "output_tokens": 90_000,
            },
            # Branch 1 reopened later for revisions
            {
                "ts": "2026-11-20T14:00:00",
                "model": "gemini-4-argon-high",
                "branch": "feat/feature-a",
                "outcome": "rc=0",
                "status": "SUCCESS",
                "duration_seconds": 1700,
                "total_tokens": 3_400_000,
                "output_tokens": 85_000,
            },
            # Branch 2: model-a fails rc=3 -> falls back to model-b 2 min later
            {
                "ts": "2026-11-21T09:00:00",
                "model": "gemini-4-neon-high",
                "branch": "feat/feature-b",
                "outcome": "rc=3",
                "status": "ERROR",
                "duration_seconds": 100,
                "total_tokens": 100_000,
                "output_tokens": 5_000,
            },
            {
                "ts": "2026-11-21T09:02:00",
                "model": "gemini-4-argon-high",
                "branch": "feat/feature-b",
                "outcome": "rc=0",
                "status": "SUCCESS",
                "duration_seconds": 1900,
                "total_tokens": 3_600_000,
                "output_tokens": 95_000,
            },
            # A runner kill after a PR exists is a stop, not a failed run or revision.
            {
                "ts": "2026-11-21T12:00:00",
                "model": "gemini-4-argon-high",
                "branch": "feat/feature-b",
                "outcome": "rc=143 idle-after-pr",
                "status": "ERROR",
                "duration_seconds": None,
                "total_tokens": 3_200_000,
                "output_tokens": 60_000,
            },
            # A non-quota nonzero rc remains a failure even without a status field.
            {
                "ts": "2026-11-21T13:00:00",
                "model": "gemini-4-neon-high",
                "branch": "fix/feature-c",
                "outcome": "rc=2",
                "duration_seconds": 60,
                "total_tokens": 10_000,
                "output_tokens": 1_000,
            },
            {
                "ts": "2026-11-21T13:30:00",
                "model": "gemini-4-neon-high",
                "branch": "fix/feature-d",
                "outcome": "rc=1",
                "duration_seconds": 60,
                "total_tokens": 10_000,
                "output_tokens": 1_000,
            },
        ],
    )

    sig, props = sr.collect_usage_signals(usage_path=str(usage_file), since="2026-11-19")
    assert sig["exists"] is True
    assert sig["runs"] == 8
    assert len(sig["fallbacks"]) == 2
    assert len(sig["reopenedBranches"]) == 1
    assert sig["reopenedBranches"][0]["branch"] == "feat/feature-a"
    assert sig["byModel"]["gemini-4-neon-high"]["failedRuns"] == 2
    assert sig["byModel"]["gemini-4-argon-high"]["idleAfterPr"] == 1
    assert sig["byModel"]["gemini-4-argon-high"]["failedRuns"] == 0

    cats = {(p["target"], p["category"]) for p in props}
    assert ("model:gemini-4-neon-high", "usage-failure") in cats
    assert ("model:gemini-4-neon-high", "usage-fallback") in cats
    assert ("job:feat", "usage-rework") not in cats
    assert ("job:feat", "usage-cost") in cats


def test_self_review_git_gh_review_fixes_and_48h_followup(tmp_path: Path) -> None:
    prs = [
        {
            "number": 200,
            "title": "feat(studio): add new panel",
            "body": "## What changed\nAdded panel.\n\n## Review fixes\nFixed padding.",
            "mergedAt": "2026-11-19T10:00:00Z",
            "headRefName": "feat/studio-panel",
            "files": [{"path": "practice-studio/src/components/Panel.tsx"}],
        },
        {
            "number": 201,
            "title": "fix(studio): patch panel crash",
            "body": "## What changed\nFixed null crash.",
            "mergedAt": "2026-11-20T18:00:00Z",  # 32h later -> within 48h!
            "headRefName": "fix/studio-panel-crash",
            "files": [{"path": "practice-studio/src/components/Panel.tsx"}],
        },
        {
            "number": 202,
            "title": "fix(studio): unrelated tweak much later",
            "body": "## What changed\nTweak.",
            "mergedAt": "2026-11-25T10:00:00Z",  # > 48h later -> not a 2-day follow-up
            "headRefName": "fix/studio-tweak",
            "files": [{"path": "practice-studio/src/components/Panel.tsx"}],
        },
    ]

    sig, props, skip = sr.collect_git_gh_signals(repo_root=str(tmp_path), prs=prs, since="2026-11-18")
    assert skip is None
    assert [p["number"] for p in sig["reviewFixPrs"]] == [200]
    assert [p["number"] for p in sig["followupFixPrs"]] == [201]
    assert len(props) == 1
    assert props[0]["target"] == "studio"
    assert props[0]["category"] == "pr-rework"
    assert props[0]["evidenceCount"] == 2
    assert props[0]["playbook"] == "improve ux"


def test_self_review_drill_quality_and_doc_refs_graceful(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Minimal repo WITHOUT scripts/doc_refs.py -> graceful skip
    unit = "MTH-T09-C01-U01"
    drills_dir = tmp_path / "drills" / "data" / unit
    drills_dir.mkdir(parents=True)
    drill_doc = {
        "drillId": "DRL-MTH-T09-C01-U01-01",
        "unitCode": unit,
        "subject": "MATH",
        "problems": [
            {"id": f"Q0{i}", "archetypeKey": "arch-easy", "level": 1, "commonTrapTag": "t1"} for i in range(1, 4)
        ]
        + [{"id": f"Q0{i}", "archetypeKey": "arch-hard", "level": 3, "commonTrapTag": "t2"} for i in range(4, 7)],
    }
    (drills_dir / "DRL-MTH-T09-C01-U01-01.json").write_text(json.dumps(drill_doc), encoding="utf-8")

    prog_dir = tmp_path / "progress"
    prog_dir.mkdir()
    prog_doc = {
        "drillId": "DRL-MTH-T09-C01-U01-01",
        "problems": {
            "Q01": {"score": 1, "attempts": [{"verdict": "correct", "answer": "SECRET_ANS_1"}]},
            "Q02": {"score": 1, "attempts": [{"verdict": "correct", "answer": "SECRET_ANS_2"}]},
            "Q03": {"score": 1, "attempts": [{"verdict": "correct", "answer": "SECRET_ANS_3"}]},
            "Q04": {"score": 0, "attempts": [{"verdict": "incorrect", "answer": "BAD_1"}]},
            "Q05": {"score": 0, "attempts": [{"verdict": "incorrect", "answer": "BAD_2"}]},
            "Q06": {"score": 0, "attempts": [{"verdict": "incorrect", "answer": "BAD_3"}]},
        },
    }
    (prog_dir / "DRL-MTH-T09-C01-U01-01.json").write_text(json.dumps(prog_doc), encoding="utf-8")
    monkeypatch.setenv("PROGRESS_DIR", str(prog_dir))
    monkeypatch.setenv("DRILLS_DATA_DIR", str(tmp_path / "drills" / "data"))

    report = sr.build_self_review(
        repo_root=str(tmp_path),
        issues_path=str(tmp_path / "missing-issues.jsonl"),
        usage_path=str(tmp_path / "missing-usage.jsonl"),
        use_gh=False,
    )
    assert any("doc_refs.py not found" in s for s in report["skipped"])
    dq_props = [p for p in report["proposals"] if p["category"] == "drill-quality"]
    assert len(dq_props) == 2
    assert all(p["target"] == "content" for p in dq_props)
    rendered = json.dumps(report)
    assert "SECRET_ANS_1" not in rendered and "BAD_1" not in rendered

    # Now add scripts/doc_refs.py stub + broken doc reference and verify doc_refs collector runs
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "doc_refs.py").write_text("# marker\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("Broken ref: `scripts/no_such_file.py`.\n", encoding="utf-8")
    doc_sig, doc_props, doc_skip = sr.collect_doc_refs_signals(repo_root=str(tmp_path), python_exe=sys.executable)
    assert doc_skip is None
    assert doc_sig["available"] is True
    assert doc_sig["count"] >= 1
    assert doc_props[0]["target"] == "docs"
    assert doc_props[0]["category"] == "doc-refs"


def test_self_review_cli_json_target_filter_and_bad_since(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    log_file = tmp_path / "issues" / "log.jsonl"
    monkeypatch.setenv("LEARNINGOS_ISSUE_LOG", str(log_file))
    il.propose_issue("studio", "PR #10", "Add loading skeleton", impact="med", path=str(log_file))
    il.propose_issue("engine", "PR #11", "Harden gate", impact="high", path=str(log_file))

    # Filter with --target ux should match studio
    report = sr.build_self_review(
        repo_root=str(tmp_path),
        issues_path=str(log_file),
        usage_path=str(tmp_path / "no-usage.jsonl"),
        target="ux",
        use_gh=False,
    )
    assert [p["target"] for p in report["proposals"]] == ["studio"]
    text = sr.format_self_review(report)
    assert "Add loading skeleton" in text

    # Invalid --since returns exit code 2
    rc = sr.main(["--since", "2026/11/20", "--no-gh"])
    assert rc == 2
    assert "YYYY-MM-DD" in capsys.readouterr().err


@pytest.fixture
def usage_checkouts(tmp_path: Path) -> tuple[Path, Path]:
    main = tmp_path.resolve() / "main checkout"
    linked = tmp_path.resolve() / "linked checkout"
    main.mkdir()
    commands = (
        ["init", "--quiet"],
        [
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            "Fixture commit",
        ],
        ["worktree", "add", "--quiet", "--detach", str(linked)],
    )
    for command in commands:
        subprocess.run(["git", *command], cwd=main, check=True, capture_output=True, timeout=10)
    return main, linked


@pytest.mark.parametrize("case", ["main", "linked", "missing", "override"])
def test_self_review_cli_usage_source(
    case: str,
    usage_checkouts: tuple[Path, Path],
    tmp_issue_log: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    main, linked = usage_checkouts
    checkout = main if case == "main" else linked
    monkeypatch.chdir(checkout)
    monkeypatch.setattr(sr, "__file__", str(checkout / "scripts" / "self_review.py"))
    main_usage = main / "pilot" / "agent-usage.jsonl"
    _write_jsonl(linked / "pilot" / "agent-usage.jsonl", [{"model": "linked-model"}])
    if case != "missing":
        _write_jsonl(main_usage, [{"model": "main-model"}])

    args = ["--no-progress", "--no-gh"]
    expected_path = main_usage
    expected_model = "main-model"
    if case == "override":
        expected_path = Path("custom usage.jsonl")
        expected_model = "override-model"
        _write_jsonl(expected_path, [{"model": expected_model}])
        args.extend(["--usage", str(expected_path)])

    assert sr.main([*args, "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    usage = report["signals"]["usage"]
    assert usage["path"] == str(expected_path)
    assert usage["exists"] is (case != "missing")
    assert set(usage["byModel"]) == (set() if case == "missing" else {expected_model})

    assert sr.main(args) == 0
    output = capsys.readouterr().out
    if case == "missing":
        assert f"usage: file not found at {expected_path}" in output
    else:
        assert f"Usage source: {expected_path}" in output


def test_self_review_cli_usage_skips_bare_repository(
    usage_checkouts: tuple[Path, Path],
    tmp_path: Path,
    tmp_issue_log: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    main, _ = usage_checkouts
    bare = tmp_path.resolve() / "bare repository.git"
    primary = tmp_path.resolve() / "primary worktree"
    secondary = tmp_path.resolve() / "secondary worktree"
    subprocess.run(
        ["git", "clone", "--quiet", "--bare", str(main), str(bare)],
        check=True,
        capture_output=True,
        timeout=10,
    )
    for checkout in (primary, secondary):
        subprocess.run(
            ["git", "worktree", "add", "--quiet", "--detach", str(checkout)],
            cwd=bare,
            check=True,
            capture_output=True,
            timeout=10,
        )
    usage_path = primary / "pilot" / "agent-usage.jsonl"
    _write_jsonl(usage_path, [{"model": "primary-model"}])
    monkeypatch.chdir(secondary)
    monkeypatch.setattr(sr, "__file__", str(secondary / "scripts" / "self_review.py"))

    assert sr.main(["--no-progress", "--no-gh", "--json"]) == 0
    usage = json.loads(capsys.readouterr().out)["signals"]["usage"]
    assert usage["path"] == str(usage_path)
    assert set(usage["byModel"]) == {"primary-model"}


def test_self_review_explicit_python_paths(tmp_path: Path) -> None:
    root_usage = tmp_path / "pilot" / "agent-usage.jsonl"
    override = tmp_path / "override.jsonl"
    _write_jsonl(root_usage, [{"model": "repo-root-model"}])
    _write_jsonl(override, [{"model": "override-model"}])
    for usage_path, expected in ((None, root_usage), (str(override), override)):
        report = sr.build_self_review(
            repo_root=str(tmp_path),
            issues_path=str(tmp_path / "missing-issues.jsonl"),
            usage_path=usage_path,
            use_gh=False,
            no_progress=True,
        )
        assert report["signals"]["usage"]["path"] == str(expected)
        assert report["signals"]["usage"]["runs"] == 1


def test_addressed_proposal_is_suppressed_without_post_since_evidence(tmp_path: Path) -> None:
    usage_file = tmp_path / "agent-usage.jsonl"
    rows = [
        {
            "ts": f"2026-11-{day:02d}T10:00:00Z",
            "model": "m",
            "branch": f"feat/a{day}",
            "outcome": "rc=0",
            "total_tokens": 3_000_000,
            "duration_seconds": 1800,
        }
        for day in (10, 11)
    ]
    _write_jsonl(usage_file, rows)
    addressed = tmp_path / "addressed.json"
    addressed.write_text(
        json.dumps({"job:feat|usage-cost": {"since": "2026-11-20", "pr": 293, "note": "rules"}}), encoding="utf-8"
    )
    report = sr.build_self_review(
        repo_root=str(tmp_path),
        issues_path=str(tmp_path / "missing-issues.jsonl"),
        usage_path=str(usage_file),
        addressed_path=str(addressed),
        use_gh=False,
    )
    assert not any(p["target"] == "job:feat" and p["category"] == "usage-cost" for p in report["proposals"])
    assert report["addressed"] == [{"key": "job:feat|usage-cost", "since": "2026-11-20", "pr": 293, "note": "rules"}]


def test_addressed_proposal_resurfaces_on_post_since_evidence(tmp_path: Path) -> None:
    usage_file = tmp_path / "agent-usage.jsonl"
    rows = [
        {
            "ts": f"2026-11-{day:02d}T10:00:00Z",
            "model": "m",
            "branch": f"feat/a{day}",
            "outcome": "rc=0",
            "total_tokens": 3_000_000,
            "duration_seconds": 1800,
        }
        for day in (10, 21, 22)
    ]
    _write_jsonl(usage_file, rows)
    addressed = tmp_path / "addressed.json"
    addressed.write_text(
        json.dumps({"job:feat|usage-cost": {"since": "2026-11-20", "pr": 293, "note": "rules"}}), encoding="utf-8"
    )
    report = sr.build_self_review(
        repo_root=str(tmp_path),
        issues_path=str(tmp_path / "missing-issues.jsonl"),
        usage_path=str(usage_file),
        addressed_path=str(addressed),
        use_gh=False,
    )
    assert any(p["target"] == "job:feat" and p["category"] == "usage-cost" for p in report["proposals"])
    assert not report["addressed"]


def test_resolved_issue_note_suppresses_old_evidence_and_uses_new_evidence(tmp_path: Path) -> None:
    issue_file = tmp_path / "issues.jsonl"
    usage_file = tmp_path / "agent-usage.jsonl"
    _write_jsonl(
        issue_file,
        [
            {
                "id": "old",
                "date": "2026-11-01 10:00 UTC",
                "kind": "tool-gap",
                "severity": "batch",
                "source": "author",
                "where": "scripts/old.py",
                "what": "Old evidence",
                "action": "open",
                "target": "pipeline",
            },
            {"resolves": "old", "date": "2026-11-20 10:00 UTC", "note": "PR #123"},
        ],
    )
    report = sr.build_self_review(
        repo_root=str(tmp_path), issues_path=str(issue_file), usage_path=str(usage_file), use_gh=False
    )
    resolved_row = next(row for row in report["addressed"] if row["key"] == "pipeline|tool-gap")
    assert resolved_row == {
        "key": "pipeline|tool-gap",
        "since": "2026-11-20",
        "pr": 123,
        "note": "2026-11-20 10:00 UTC: PR #123",
    }

    with issue_file.open("a", encoding="utf-8") as fh:
        for issue_id in ("new1", "new2"):
            fh.write(
                json.dumps(
                    {
                        "id": issue_id,
                        "date": "2026-11-21 10:00 UTC",
                        "kind": "tool-gap",
                        "severity": "batch",
                        "source": "author",
                        "where": "scripts/new.py",
                        "what": "New evidence",
                        "action": "open",
                        "target": "pipeline",
                    }
                )
                + "\n"
            )
    report = sr.build_self_review(
        repo_root=str(tmp_path), issues_path=str(issue_file), usage_path=str(usage_file), use_gh=False
    )
    proposal = next(p for p in report["proposals"] if p["target"] == "pipeline" and p["category"] == "recurring-issue")
    assert proposal["evidenceCount"] == 2
    assert not any(row["key"] == "pipeline|tool-gap" for row in report["addressed"])


def test_compare_metrics_math_and_insufficient_data(tmp_path: Path) -> None:
    usage_file = tmp_path / "agent-usage.jsonl"
    rows = [
        {
            "ts": "2026-11-01T10:00:00Z",
            "model": "m",
            "branch": "feat/old",
            "outcome": "rc=0",
            "total_tokens": 100,
            "duration_seconds": 60,
        },
        {
            "ts": "2026-11-21T10:00:00Z",
            "model": "m",
            "branch": "feat/new-1",
            "outcome": "rc=0",
            "total_tokens": 200,
            "duration_seconds": 120,
        },
        {
            "ts": "2026-11-22T10:00:00Z",
            "model": "m",
            "branch": "feat/new-2",
            "outcome": "rc=1",
            "total_tokens": 200,
            "duration_seconds": 120,
        },
        {
            "ts": "2026-11-23T10:00:00Z",
            "model": "m",
            "branch": "feat/new-3",
            "outcome": "rc=0",
            "total_tokens": 200,
            "duration_seconds": 120,
        },
        {
            "ts": "2026-11-24T10:00:00Z",
            "model": "m",
            "branch": "feat/new-4",
            "outcome": "rc=0",
            "total_tokens": 200,
            "duration_seconds": 120,
        },
        {
            "ts": "2026-11-24T11:00:00Z",
            "model": "quota",
            "branch": "fix/fallback",
            "outcome": "rc=3",
            "total_tokens": 100,
            "duration_seconds": 60,
        },
        {
            "ts": "2026-11-24T11:05:00Z",
            "model": "target",
            "branch": "fix/fallback",
            "outcome": "rc=0",
            "total_tokens": 100,
            "duration_seconds": 60,
        },
        {
            "ts": "2026-11-24T12:00:00Z",
            "model": "rev",
            "branch": "fix/revision",
            "outcome": "rc=0",
            "total_tokens": 100,
            "duration_seconds": 60,
        },
        {
            "ts": "2026-11-24T12:30:00Z",
            "model": "rev",
            "branch": "fix/revision",
            "outcome": "rc=0",
            "total_tokens": 100,
            "duration_seconds": 60,
        },
    ]
    _write_jsonl(usage_file, rows)
    result = sr.collect_compare_metrics(usage_path=str(usage_file), compare_at="2026-11-20")
    metrics = result["usage"]["job:feat"]
    assert metrics["runs"]["before"] == 1 and metrics["runs"]["after"] == 4
    assert metrics["avgTokensPerRun"] == {"before": 100.0, "after": 200.0, "deltaPercent": 100.0}
    assert metrics["avgMinutesPerRun"] == {"before": 1.0, "after": 2.0, "deltaPercent": 100.0}
    assert metrics["failureRate"]["after"] == 0.25
    assert metrics["insufficientData"] is True
    fix_metrics = result["usage"]["job:fix"]
    assert fix_metrics["fallbackRate"]["after"] == 0.25
    assert fix_metrics["revisionRate"]["after"] == 0.5


def test_format_self_review_handles_none_comparison_values(tmp_path: Path) -> None:
    # End-to-end: one group only appears before compare_at (after=None), another only after (before=None).
    usage_file = tmp_path / "agent-usage.jsonl"
    _write_jsonl(
        usage_file,
        [
            {
                "ts": "2026-11-10T10:00:00Z",
                "model": "legacy-model",
                "branch": "content/old-drill",
                "outcome": "rc=1",
                "total_tokens": 1000,
                "duration_seconds": 120,
            },
            {
                "ts": "2026-11-26T10:00:00Z",
                "model": "new-model",
                "branch": "fix/new-bug",
                "outcome": "rc=0",
                "total_tokens": 500,
                "duration_seconds": 60,
            },
        ],
    )
    report = sr.build_self_review(
        repo_root=str(tmp_path),
        issues_path=str(tmp_path / "missing-issues.jsonl"),
        usage_path=str(usage_file),
        compare_at="2026-11-25",
        use_gh=False,
    )
    rendered = sr.format_self_review(report)
    assert "model:legacy-model | failure rate | 100.0% | n/a | n/a (insufficient data)" in rendered
    assert "model:legacy-model | avg tokens/run | 1000.0 | n/a | n/a (insufficient data)" in rendered
    assert "model:new-model | failure rate | n/a | 0.0% | n/a (insufficient data)" in rendered
    assert "model:new-model | avg minutes/run | n/a | 1.0 | n/a (insufficient data)" in rendered
    assert " | None | " not in rendered

    # Synthetic comparison with both sides None (including followupFixPrs).
    synthetic = {
        "proposals": [],
        "signals": {},
        "comparison": {
            "compareAt": "2026-11-25",
            "usage": {
                "job:docs": {
                    "runs": {"before": 0, "after": 0, "deltaPercent": None},
                    "avgTokensPerRun": {"before": None, "after": None, "deltaPercent": None},
                    "avgMinutesPerRun": {"before": None, "after": None, "deltaPercent": None},
                    "revisionRate": {"before": None, "after": None, "deltaPercent": None},
                    "fallbackRate": {"before": 0.25, "after": None, "deltaPercent": None},
                    "failureRate": {"before": None, "after": 0.5, "deltaPercent": None},
                    "insufficientData": True,
                }
            },
            "followupFixPrs": {"before": None, "after": None, "deltaPercent": None},
        },
    }
    syn_text = sr.format_self_review(synthetic)
    assert "job:docs | fallback rate | 25.0% | n/a | n/a (insufficient data)" in syn_text
    assert "job:docs | failure rate | n/a | 50.0% | n/a (insufficient data)" in syn_text
    assert "job:docs | revision rate | n/a | n/a | n/a (insufficient data)" in syn_text
    assert "PR follow-up fix PRs (within 48h) | n/a | n/a | n/a" in syn_text
    assert "None" not in syn_text


def test_every_skill_has_self_review_step() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    skills_dir = repo_root / ".claude" / "skills"
    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    assert len(skill_files) >= 10
    for skill_md in skill_files:
        skill_name = skill_md.parent.name
        text = skill_md.read_text(encoding="utf-8")
        assert "## Self-review" in text, f"{skill_md} missing ## Self-review section"
        assert f"scripts.issues propose --target skill:{skill_name}" in text, (
            f"{skill_md} missing scripts.issues propose --target skill:{skill_name}"
        )


def test_self_review_no_progress_skips_collector(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("The progress collector must be skipped")

    monkeypatch.setattr(sr, "collect_drill_quality_signals", forbidden)
    report = sr.build_self_review(
        repo_root=str(tmp_path),
        issues_path=str(tmp_path / "issues.jsonl"),
        use_gh=False,
        no_progress=True,
    )
    assert "drill-quality: skipped (--no-progress)" in report["skipped"]
    assert report["signals"]["drillQuality"]["unitsChecked"] is None
    assert "drill_units=skipped" in sr.format_self_review(report)
    assert all(proposal["category"] != "drill-quality" for proposal in report["proposals"])
