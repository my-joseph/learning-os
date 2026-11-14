"""Issue log (scripts/issues.py, rules/00_core.md §11)."""

import json
import os

import pytest

from scripts import issues as il


@pytest.fixture
def log(tmp_path, monkeypatch):
    path = str(tmp_path / "issues" / "log.jsonl")
    monkeypatch.setenv("LEARNINGOS_ISSUE_LOG", path)
    return path


def test_add_list_resolve_roundtrip(log):
    iid, created = il.add_issue("ambiguity", "batch", "reviewer", "DRL-X/Q05", "MB could be 1000 or 1024 kB")
    assert created and os.path.exists(log)
    assert [r["id"] for r in il.issues()] == [iid]
    il.resolve_issue(iid, "PR #31")
    (rec,) = il.issues()
    assert rec["resolved"].endswith("PR #31")
    assert "nothing pending" in il.summary()


def test_identical_pending_issue_is_not_duplicated(log):
    first, _ = il.add_issue("bug", "batch", "author", "sync", "timeout")
    again, created = il.add_issue("bug", "batch", "author", "sync", "timeout")
    assert (again, created) == (first, False)
    il.resolve_issue(first, "fixed")
    _, created = il.add_issue("bug", "batch", "author", "sync", "timeout")
    assert created  # a recurrence after resolution is a new issue


def test_summary_puts_urgent_first_and_counts_kinds(log):
    il.add_issue("context", "batch", "reviewer", "DRL-A/Q1", "fake story", action="auto-fixed")
    il.add_issue("wrong-answer", "urgent", "learner", "DRL-B/Q2", "answer is 12 not 21")
    text = il.summary()
    assert "2 pending (1 urgent, 1 still open" in text
    body = text.split("\n\n", 1)[1].splitlines()
    assert body[0].startswith("[") and "URGENT wrong-answer" in body[0]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kind": "nope"},
        {"severity": "high"},
        {"source": "me"},
        {"action": "ignored"},
        {"where": " "},
    ],
)
def test_invalid_fields_rejected(log, kwargs):
    args = {"kind": "bug", "severity": "batch", "source": "author", "where": "x", "what": "y", **kwargs}
    with pytest.raises(ValueError):
        il.add_issue(**args)


def test_resolve_unknown_or_twice_rejected(log):
    with pytest.raises(ValueError, match="no issue"):
        il.resolve_issue("abc123", "x")
    iid, _ = il.add_issue("bug", "batch", "author", "x", "y")
    il.resolve_issue(iid, "done")
    with pytest.raises(ValueError, match="already resolved"):
        il.resolve_issue(iid, "again")


def test_review_gate():
    from math_engine.ai_drill_ingest import AiContractError, validate_review

    validate_review({"id": "Q1", "review": {"verdict": "pass", "note": "ok"}})
    for rv in (None, {"verdict": "pass"}, {"verdict": "maybe", "note": "x"}):
        with pytest.raises(AiContractError, match="Needs 'review'"):
            validate_review({"id": "Q1", "review": rv})
    with pytest.raises(AiContractError, match="MB is ambiguous"):
        validate_review({"id": "Q1", "review": {"verdict": "fix", "note": "MB is ambiguous"}})


def test_log_is_append_only_jsonl(log):
    iid, _ = il.add_issue("bug", "batch", "author", "x", "y")
    il.resolve_issue(iid, "done")
    with open(log, encoding="utf-8") as f:
        lines = [json.loads(line) for line in f]
    assert lines[0]["id"] == iid and lines[1] == {**lines[1], "resolves": iid}


def test_cli_add_and_summary(log, capsys):
    assert (
        il.main(
            [
                "add",
                "--kind",
                "level",
                "--severity",
                "batch",
                "--source",
                "gate",
                "--where",
                "D/Q3",
                "--what",
                "edge decided nothing",
            ]
        )
        == 0
    )
    assert "Logged issue" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        il.main(["add", "--kind", "bad", "--severity", "batch", "--source", "gate", "--where", "D", "--what", "w"])
    capsys.readouterr()
    il.main(["summary"])
    assert "level 1" in capsys.readouterr().out


def test_main_checkout_root_from_worktree(tmp_path):
    main = tmp_path / "repo"
    wt = main / ".claude" / "worktrees" / "wt"
    (main / ".git" / "worktrees" / "wt").mkdir(parents=True)
    wt.mkdir(parents=True)
    (wt / ".git").write_text(f"gitdir: {main / '.git' / 'worktrees' / 'wt'}\n")
    assert il.main_checkout_root(str(wt)) == str(main)
    assert il.main_checkout_root(str(main)) == str(main)
