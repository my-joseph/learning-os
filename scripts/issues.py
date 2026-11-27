"""Issue log: mistakes that an AI caught in its own work, or that a reviewer, a gate or the learner caught.

The learner clears the log in batches ("clear the issue log") instead of fixing problems every day.
Rules: `rules/00_core.md` §11. The log is local-only (`issues/log.jsonl` in the main checkout, gitignored)
and append-only, so several agents and worktrees can write to it at once.

    python -m scripts.issues add --kind ambiguity --severity batch --source reviewer \\
        --where DRL-MTH-T01-C07-03/Q05 --what "MB could be 1000 or 1024 kB" --action auto-fixed \\
        [--target skill:new-math-drill]
    python -m scripts.issues propose --target skill:new-math-drill \\
        --evidence "DRL-MTH-T01-C07-03/Q05" --proposal "Add unit-convention check to reviewer" [--impact med]
    python -m scripts.issues summary           # pending records grouped by kind, urgent first
    python -m scripts.issues list [--all]      # pending (or every) record
    python -m scripts.issues resolve <id> [<id> ...] --note "PR #31"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
from collections import Counter
from datetime import datetime, timezone

from progress_store import pilot_mode

KINDS = (
    "wrong-answer",  # a problem's answer, trap or steps are wrong
    "ambiguity",  # a prompt can be read more than one way (units, rounding, wording)
    "context",  # a story that is physically or factually wrong
    "leak",  # a hint, display or prompt that gives away the answer or the key step
    "reasoning",  # a hint, step or explanation that is wrong, misleading or too coarse (answer still right)
    "level",  # level label not earned, or brief levels not met
    "brief",  # drill does not match what the learner asked for
    "gate-gap",  # a bad problem passed every gate
    "tool-gap",  # the engine cannot express or check something (see docs/backlog.md)
    "rule-gap",  # rules or skill are unclear, contradict each other, or are missing a case
    "bug",  # a script or the Studio misbehaved
    "proposal",  # concrete improvement proposal for a skill or system area
    "other",
)
SEVERITIES = ("urgent", "batch")
SOURCES = ("author", "reviewer", "gate", "learner", "pilot", "other")
ACTIONS = ("open", "auto-fixed", "dropped")
IMPACTS = ("low", "med", "high")
TARGET_AREAS = ("engine", "pipeline", "studio", "content", "ci", "docs")
TARGET_PREFIXES = ("skill", "model", "job", "gate")
_PREFIXED_TARGET_RE = re.compile(r"^(skill|model|job|gate):[A-Za-z0-9][A-Za-z0-9_./-]*$")
_DRILL_FILE_PATH_RE = re.compile(r"(?:^|.*?/)drills/data/(?:MTH|PRG|PHY)-[^/]+/(DRL-[A-Za-z0-9-]+)\.json(?:/(.+))?$")
_VARIANT_FILE_PATH_RE = re.compile(r"(?:^|.*?/)drills/variants/((?:MTH|PRG|PHY)-[A-Za-z0-9-]+)\.json(?:/(.+))?$")
_VAULT_FILE_PATH_RE = re.compile(
    r"(?:^|.*?/)(?:math_engine|code_engine)/reasoning_vault/((?:MTH|PRG|PHY)-[A-Za-z0-9-]+)\.json(?:/(.+))?$"
)
_LAB_FILE_PATH_RE = re.compile(r"(?:^|.*?/)labs/(LAB-[A-Za-z0-9-]+)(?:/(.+))?$")
_SCOPE_CODE_RE = re.compile(
    r"(?<![A-Za-z0-9-])((?:MTH|PRG|PHY)-(?:T\d+-C\d+(?:-U\d+)?|BRIDGE|[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*))"
)
_DRILL_ID_RE = re.compile(r"\b(DRL-(?:MTH|PRG|PHY)-[A-Za-z0-9-]+)\b")
_QID_RANGE_RE = re.compile(r"\bQ(\d{1,2})\s*[-–]\s*Q?(\d{1,2})\b")
_QID_SINGLE_RE = re.compile(r"\bQ(\d{1,2})\b")
_LEVEL_SUFFIX_RE = re.compile(r"@L(\d+)\b")


def canonicalize_where(where: str, kind: str | None = None) -> str:
    """Normalise repository file paths in ``where`` into canonical drill ID / scope / archetype forms.

    Non-path identifiers (commands, module names, already-canonical `<SCOPE>/<archetypeKey>@L<n>`,
    or `<DRILL_ID>/<QID>`) are preserved verbatim after trimming whitespace.
    """
    _ = kind  # reserved for kind-specific rules without breaking callers
    cleaned = re.sub(r"\s+", " ", str(where or "").strip())
    if not cleaned:
        return ""
    # Normalise Windows separators and leading "./" on path-like values.
    candidate = cleaned.replace("\\", "/")
    if candidate.startswith("./"):
        candidate = candidate[2:]

    for pattern in (_DRILL_FILE_PATH_RE, _VARIANT_FILE_PATH_RE, _VAULT_FILE_PATH_RE, _LAB_FILE_PATH_RE):
        m = pattern.match(candidate)
        if m:
            head = m.group(1)
            tail = (m.group(2) or "").strip("/")
            return f"{head}/{tail}" if tail else head
    return cleaned


def _expand_qids(text: str) -> list[str]:
    qids: list[str] = []
    seen: set[str] = set()

    def _add(num: int) -> None:
        tok = f"Q{num:02d}"
        if tok not in seen:
            seen.add(tok)
            qids.append(tok)

    for m in _QID_RANGE_RE.finditer(text):
        lo, hi = int(m.group(1)), int(m.group(2))
        if 1 <= lo <= hi <= 99:
            for n in range(lo, hi + 1):
                _add(n)
    for m in _QID_SINGLE_RE.finditer(text):
        _add(int(m.group(1)))
    return qids


def parse_where_reference(where: str) -> dict[str, object]:
    """Parse canonical or legacy ``where`` values into structured scope/drill/QID/level tokens."""
    canon = canonicalize_where(where)
    drills = list(dict.fromkeys(_DRILL_ID_RE.findall(canon)))
    scopes = list(dict.fromkeys(_SCOPE_CODE_RE.findall(canon)))
    for did in drills:
        m = re.match(r"^DRL-((?:MTH|PRG|PHY)-.+)-\d+$", did)
        if m and m.group(1) not in scopes:
            scopes.append(m.group(1))

    level_match = _LEVEL_SUFFIX_RE.search(canon)
    explicit_level = int(level_match.group(1)) if level_match else None

    # Associate QIDs per drill when multiple drills appear in one `where` string.
    drill_qids: list[tuple[str, str]] = []
    if len(drills) == 1:
        for qid in _expand_qids(canon):
            drill_qids.append((drills[0], qid))
    elif len(drills) > 1:
        matches = list(_DRILL_ID_RE.finditer(canon))
        for idx, dm in enumerate(matches):
            seg_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(canon)
            seg = canon[dm.end() : seg_end]
            for qid in _expand_qids(seg):
                drill_qids.append((dm.group(1), qid))

    return {
        "canonical": canon,
        "scopes": scopes,
        "drills": drills,
        "qids": _expand_qids(canon),
        "drillQids": drill_qids,
        "level": explicit_level,
    }


def validate_target(target: str | None) -> str | None:
    """Validate optional --target (area or skill:/model:/job:/gate:<name>)."""
    if target is None:
        return None
    cleaned = target.strip()
    if not cleaned:
        raise ValueError("target must not be empty")
    if cleaned in TARGET_AREAS or _PREFIXED_TARGET_RE.fullmatch(cleaned):
        return cleaned
    allowed = ", ".join(TARGET_AREAS)
    prefixes = ", ".join(f"{p}:<name>" for p in TARGET_PREFIXES)
    raise ValueError(f"target must be one of [{allowed}] or {prefixes}, got {target!r}")


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
    kind: str,
    severity: str,
    source: str,
    where: str,
    what: str,
    action: str = "open",
    path: str | None = None,
    *,
    target: str | None = None,
    evidence: str | None = None,
    proposal: str | None = None,
    impact: str | None = None,
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
    if impact is not None and impact not in IMPACTS:
        raise ValueError(f"impact must be one of {list(IMPACTS)}, got {impact!r}")
    norm_target = validate_target(target)
    if pilot_mode():
        source = "pilot"
    where_s = canonicalize_where(where, kind=kind)
    what_s = what.strip()
    if not where_s or not what_s:
        raise ValueError("where and what must not be empty")
    for r in issues(path):
        if not r["resolved"] and (r["kind"], r["where"], r["what"], r.get("target")) == (
            kind,
            where_s,
            what_s,
            norm_target,
        ):
            return r["id"], False
    issue_id = secrets.token_hex(3)
    record: dict[str, str] = {
        "id": issue_id,
        "date": _now(),
        "kind": kind,
        "severity": severity,
        "source": source,
        "where": where_s,
        "what": what_s,
        "action": action,
    }
    if norm_target is not None:
        record["target"] = norm_target
    if evidence is not None and evidence.strip():
        record["evidence"] = evidence.strip()
    if proposal is not None and proposal.strip():
        record["proposal"] = proposal.strip()
    if impact is not None:
        record["impact"] = impact
    _append(record, path)
    return issue_id, True


def propose_issue(
    target: str,
    evidence: str,
    proposal: str,
    impact: str = "med",
    source: str = "author",
    path: str | None = None,
) -> tuple[str, bool]:
    """Record a concrete improvement proposal (`kind='proposal'`) for a skill or system area."""
    norm_target = validate_target(target)
    if norm_target is None:
        raise ValueError("target is required for a proposal")
    ev = evidence.strip()
    prop = proposal.strip()
    if not ev or not prop:
        raise ValueError("evidence and proposal must not be empty")
    return add_issue(
        kind="proposal",
        severity="batch",
        source=source,
        where=ev,
        what=prop,
        action="open",
        path=path,
        target=norm_target,
        evidence=ev,
        proposal=prop,
        impact=impact,
    )


def resolve_issue(issue_id: str, note: str, path: str | None = None) -> None:
    known = {r["id"]: r for r in issues(path)}
    if issue_id not in known:
        raise ValueError(f"no issue with id {issue_id!r}")
    if known[issue_id]["resolved"]:
        raise ValueError(f"issue {issue_id} is already resolved ({known[issue_id]['resolved']})")
    _append({"resolves": issue_id, "date": _now(), "note": note.strip() or "resolved"}, path)


def _line(r: dict) -> str:
    flag = "URGENT " if r["severity"] == "urgent" else ""
    meta_parts: list[str] = []
    if r.get("target"):
        meta_parts.append(str(r["target"]))
    if r.get("impact"):
        meta_parts.append(f"impact={r['impact']}")
    meta = f" [{' '.join(meta_parts)}]" if meta_parts else ""
    tail = f"  -> {r['resolved']}" if r["resolved"] else ""
    return f"[{r['id']}] {flag}{r['kind']}{meta} ({r['action']}, {r['source']}) {r['where']}: {r['what']}{tail}"


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
    a.add_argument(
        "--target",
        default=None,
        help="optional target: skill:<name>, model:<name>, job:<type>, gate:<name>, or area (engine|pipeline|studio|content|ci|docs)",
    )
    pr = sub.add_parser("propose", help="record a concrete improvement proposal")
    pr.add_argument(
        "--target",
        required=True,
        help="skill:<name>, model:<name>, job:<type>, gate:<name>, or area (engine|pipeline|studio|content|ci|docs)",
    )
    pr.add_argument("--evidence", required=True, help="what happened, file:line, PR number, or run id")
    pr.add_argument("--proposal", required=True, help="concrete change to make")
    pr.add_argument("--impact", default="med", choices=IMPACTS, help="expected impact (low|med|high)")
    pr.add_argument("--source", default="author", choices=SOURCES, help="who raised the proposal")
    sub.add_parser("summary", help="pending issues grouped by kind, urgent first")
    ls = sub.add_parser("list", help="pending issues (or --all)")
    ls.add_argument("--all", action="store_true")
    ls.add_argument("--target", default=None, help="filter to records matching this target")
    rs = sub.add_parser("resolve", help="mark issues as dealt with")
    rs.add_argument("ids", nargs="+")
    rs.add_argument("--note", required=True, help="how it was dealt with, e.g. 'PR #31' or 'pattern noted, no fix'")
    args = parser.parse_args(argv)

    try:
        if args.cmd == "add":
            issue_id, created = add_issue(
                args.kind,
                args.severity,
                args.source,
                args.where,
                args.what,
                args.action,
                target=args.target,
            )
            print(f"{'Logged' if created else 'Already logged'} issue {issue_id} in {log_path()}")
        elif args.cmd == "propose":
            issue_id, created = propose_issue(
                args.target,
                args.evidence,
                args.proposal,
                impact=args.impact,
                source=args.source,
            )
            print(f"{'Logged' if created else 'Already logged'} proposal {issue_id} in {log_path()}")
        elif args.cmd == "summary":
            print(summary())
        elif args.cmd == "list":
            filter_target = validate_target(args.target) if args.target else None
            rows = [
                r
                for r in issues()
                if (args.all or not r["resolved"]) and (filter_target is None or r.get("target") == filter_target)
            ]
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
