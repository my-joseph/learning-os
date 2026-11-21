"""Tests for scripts/issues.py extensions (--target, propose) and scripts/self_review.py."""

from __future__ import annotations

import json
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
            # Branch 2 also reopened
            {
                "ts": "2026-11-21T12:00:00",
                "model": "gemini-4-argon-high",
                "branch": "feat/feature-b",
                "outcome": "rc=143 idle-after-pr",
                "status": None,
                "duration_seconds": None,
                "total_tokens": 3_200_000,
                "output_tokens": 60_000,
            },
        ],
    )

    sig, props = sr.collect_usage_signals(usage_path=str(usage_file), since="2026-11-19")
    assert sig["exists"] is True
    assert sig["runs"] == 6
    assert len(sig["fallbacks"]) == 2
    assert len(sig["reopenedBranches"]) == 2
    assert sig["byModel"]["gemini-4-neon-high"]["failedRuns"] == 2
    assert sig["byModel"]["gemini-4-argon-high"]["idleAfterPr"] == 1
    assert sig["byModel"]["gemini-4-argon-high"]["failedRuns"] == 0

    cats = {(p["target"], p["category"]) for p in props}
    assert ("model:gemini-4-neon-high", "usage-failure") in cats
    assert ("model:gemini-4-neon-high", "usage-fallback") in cats
    assert ("job:feat", "usage-rework") in cats
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
