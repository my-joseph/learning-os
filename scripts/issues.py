"""Issue log: mistakes that an AI caught in its own work, or that a reviewer, a gate or the learner caught.

The learner clears the log in batches ("clear the issue log") instead of fixing problems every day.
Rules: `rules/00_core.md` §11. The log is local-only (`issues/log.jsonl` in the main checkout, gitignored)
and append-only, so several agents and worktrees can write to it at once.

    python -m scripts.issues add --kind ambiguity --severity batch --source reviewer \\
        --where DRL-MTH-T01-C07-03/Q05 --what "MB could be 1000 or 1024 kB" --action auto-fixed
    python -m scripts.issues summary           # pending records grouped by kind, urgent first
    python -m scripts.issues list [--all]      # pending (or every) record
    python -m scripts.issues resolve <id> [<id> ...] --note "PR #31"
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from collections import Counter
from datetime import datetime, timezone

KINDS = (
    "wrong-answer",  # a problem's answer, trap or steps are wrong
    "ambiguity",  # a prompt can be read more than one way (units, rounding, wording)
    "context",  # a story that is physically or factually wrong
    "leak",  # a hint, display or prompt that gives away the answer or the key step
    "level",  # level label not earned, or brief levels not met
    "brief",  # drill does not match what the learner asked for
    "gate-gap",  # a bad problem passed every gate
    "tool-gap",  # the engine cannot express or check something (see docs/backlog.md)
    "rule-gap",  # rules or skill are unclear, contradict each other, or are missing a case
    "bug",  # a script or the Studio misbehaved
    "other",
)
SEVERITIES = ("urgent", "batch")
SOURCES = ("author", "reviewer", "gate", "learner", "other")
ACTIONS = ("open", "auto-fixed", "dropped")


def main_checkout_root(cwd: str = ".") -> str:
    """The main checkout's root, also from inside a git worktree (`.git` is then a `gitdir:` file)."""
    root = os.path.abspath(cwd)
    git_path = os.path.join(root, ".git")
    if os.path.isfile(git_path):
        with open(git_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if text.startswith("gitdir:"):
            gitdir = os.path.abspath(os.path.join(root, text.split(":", 1)[1].strip()))
            worktrees_dir = os.path.dirname(gitdir)
            if os.path.basename(worktrees_dir) == "worktrees":
                return os.path.dirname(os.path.dirname(worktrees_dir))
    return root


def log_path() -> str:
    return os.environ.get("LEARNINGOS_ISSUE_LOG") or os.path.join(main_checkout_root(), "issues", "log.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def read_log(path: str | None = None) -> list[dict]:
    path = path or log_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _append(record: dict, path: str | None = None) -> None:
    path = path or log_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def issues(path: str | None = None) -> list[dict]:
    """Issue records with `resolved` (the resolve note, or None) folded in."""
    records = read_log(path)
    resolved = {r["resolves"]: r for r in records if "resolves" in r}
    out = []
    for r in records:
        if "resolves" in r:
            continue
        res = resolved.get(r["id"])
        out.append({**r, "resolved": f"{res['date']}: {res['note']}" if res else None})
    return out


def add_issue(
    kind: str, severity: str, source: str, where: str, what: str, action: str = "open", path: str | None = None
) -> tuple[str, bool]:
    """Append an issue. Returns (id, created). An identical pending issue is not added twice."""
    for field, value, allowed in (
        ("kind", kind, KINDS),
        ("severity", severity, SEVERITIES),
        ("source", source, SOURCES),
        ("action", action, ACTIONS),
    ):
        if value not in allowed:
            raise ValueError(f"{field} must be one of {list(allowed)}, got {value!r}")
    if not where.strip() or not what.strip():
        raise ValueError("where and what must not be empty")
    for r in issues(path):
        if not r["resolved"] and (r["kind"], r["where"], r["what"]) == (kind, where.strip(), what.strip()):
            return r["id"], False
    issue_id = secrets.token_hex(3)
    _append(
        {
            "id": issue_id,
            "date": _now(),
            "kind": kind,
            "severity": severity,
            "source": source,
            "where": where.strip(),
            "what": what.strip(),
            "action": action,
        },
        path,
    )
    return issue_id, True


def resolve_issue(issue_id: str, note: str, path: str | None = None) -> None:
    known = {r["id"]: r for r in issues(path)}
    if issue_id not in known:
        raise ValueError(f"no issue with id {issue_id!r}")
    if known[issue_id]["resolved"]:
        raise ValueError(f"issue {issue_id} is already resolved ({known[issue_id]['resolved']})")
    _append({"resolves": issue_id, "date": _now(), "note": note.strip() or "resolved"}, path)


def _line(r: dict) -> str:
    flag = "URGENT " if r["severity"] == "urgent" else ""
    tail = f"  -> {r['resolved']}" if r["resolved"] else ""
    return f"[{r['id']}] {flag}{r['kind']} ({r['action']}, {r['source']}) {r['where']}: {r['what']}{tail}"


def _sort_key(r: dict) -> tuple:
    return (r["severity"] != "urgent", r["action"] != "open", r["kind"], r["date"])


def summary(path: str | None = None) -> str:
    pending = [r for r in issues(path) if not r["resolved"]]
    if not pending:
        return "Issue log: nothing pending."
    counts = Counter(r["kind"] for r in pending)
    urgent = sum(r["severity"] == "urgent" for r in pending)
    open_ = sum(r["action"] == "open" for r in pending)
    lines = [
        f"Issue log: {len(pending)} pending ({urgent} urgent, {open_} still open, "
        f"{len(pending) - open_} already auto-fixed or dropped)",
        "By kind: " + ", ".join(f"{k} {n}" for k, n in counts.most_common()),
        "",
    ]
    lines += [_line(r) for r in sorted(pending, key=_sort_key)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.issues", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="record an issue")
    a.add_argument("--kind", required=True, choices=KINDS)
    a.add_argument("--severity", required=True, choices=SEVERITIES)
    a.add_argument("--source", required=True, choices=SOURCES)
    a.add_argument("--where", required=True, help="drill/problem, file or command, e.g. DRL-MTH-T01-C07-03/Q05")
    a.add_argument("--what", required=True, help="one sentence: what went wrong")
    a.add_argument("--action", default="open", choices=ACTIONS, help="what was already done about it")
    sub.add_parser("summary", help="pending issues grouped by kind, urgent first")
    ls = sub.add_parser("list", help="pending issues (or --all)")
    ls.add_argument("--all", action="store_true")
    rs = sub.add_parser("resolve", help="mark issues as dealt with")
    rs.add_argument("ids", nargs="+")
    rs.add_argument("--note", required=True, help="how it was dealt with, e.g. 'PR #31' or 'pattern noted, no fix'")
    args = parser.parse_args(argv)

    try:
        if args.cmd == "add":
            issue_id, created = add_issue(args.kind, args.severity, args.source, args.where, args.what, args.action)
            print(f"{'Logged' if created else 'Already logged'} issue {issue_id} in {log_path()}")
        elif args.cmd == "summary":
            print(summary())
        elif args.cmd == "list":
            rows = [r for r in issues() if args.all or not r["resolved"]]
            print("\n".join(_line(r) for r in sorted(rows, key=_sort_key)) or "No issues.")
        elif args.cmd == "resolve":
            for issue_id in args.ids:
                resolve_issue(issue_id, args.note)
            print(f"Resolved {len(args.ids)} issue(s).")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
