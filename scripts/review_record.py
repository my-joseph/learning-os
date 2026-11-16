# -*- coding: utf-8 -*-
"""
Record and query PRG code review attempts in learner progress (`progress/<DRILL_ID>.json`).

Usage:
    python -m scripts.review_record add <DRILL_ID> <QID> --findings findings.json [--explain TEXT]
    python -m scripts.review_record explain <DRILL_ID> <QID> TEXT
    python -m scripts.review_record dispute <DRILL_ID> <QID> <CHECK_ID> --reason TEXT
    python -m scripts.review_record show <DRILL_ID> [QID]
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any

from code_engine.review_run import find_drill_doc, find_problem, run_review_with_source
from progress_store import apply_progress, load_progress, save_progress
from scripts.issues import add_issue


def compute_verdict(
    tests: dict[str, Any],
    lint: list[dict[str, Any]],
    typecheck: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> str:
    """Return 'pass' iff all tests pass, no lint/typecheck errors, and no non-disputed 'must' finding."""
    all_tests_pass = tests.get("passed", 0) == tests.get("total", 0) and not tests.get("failed")
    no_lint = len(lint) == 0
    no_typecheck = len(typecheck) == 0
    no_blocking_must = not any(f.get("severity") == "must" and not f.get("disputed") for f in findings)
    return "pass" if (all_tests_pass and no_lint and no_typecheck and no_blocking_must) else "revise"


def _normalize_findings(
    raw_findings: list[dict[str, Any]],
    rubric_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(raw_findings, list):
        raise ValueError("findings JSON must be a list of finding objects.")

    unknown = [str(f.get("check", "")) for f in raw_findings if f.get("check") not in rubric_by_id]
    if unknown:
        valid_ids = sorted(rubric_by_id.keys())
        raise ValueError(f"Unknown check id(s): {unknown}. Valid check ids for this problem: {valid_ids}")

    normalized: list[dict[str, Any]] = []
    for f in raw_findings:
        check_id = f["check"]
        rubric_entry = rubric_by_id[check_id]
        entry: dict[str, Any] = {
            "check": check_id,
            "severity": rubric_entry["severity"],
            "line": int(f.get("line", 0) or 0),
            "note": str(f.get("note", "")).strip(),
        }
        if f.get("hint"):
            entry["hint"] = str(f["hint"]).strip()
        if f.get("disputed"):
            entry["disputed"] = f["disputed"]
        normalized.append(entry)
    return normalized


def _load_or_init_doc(drill_id: str, drill_doc: dict[str, Any] | None = None) -> dict[str, Any]:
    if drill_doc is None:
        drill_doc, _ = find_drill_doc(drill_id)
    prog = load_progress(drill_id)
    apply_progress(drill_doc, prog)
    return drill_doc


def add_record(
    drill_id: str,
    qid: str,
    raw_findings: list[dict[str, Any]],
    explain: str | None = None,
    *,
    data_root: Path | None = None,
    workspace_root: Path | None = None,
    vault_dir: Path | None = None,
    universal_path: Path | None = None,
) -> dict[str, Any]:
    """Re-run review_run, validate findings against rubric, append record to progress, and return it."""
    review_res, src_text, drill_doc = run_review_with_source(
        drill_id,
        qid,
        data_root=data_root,
        workspace_root=workspace_root,
        vault_dir=vault_dir,
        universal_path=universal_path,
    )
    rubric_by_id = {c["id"]: c for c in review_res["checks"]}
    findings = _normalize_findings(raw_findings, rubric_by_id)
    verdict = compute_verdict(review_res["tests"], review_res["lint"], review_res["typecheck"], findings)

    apply_progress(drill_doc, load_progress(drill_id))
    prob = find_problem(drill_doc, review_res["problemId"])
    state = prob.setdefault("state", {})
    reviews = state.setdefault("reviews", [])

    record: dict[str, Any] = {
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "attempt": len(reviews) + 1,
        "codeHash": review_res["codeHash"],
        "code": src_text,
        "tests": review_res["tests"],
        "lint": review_res["lint"],
        "typecheck": review_res["typecheck"],
        "findings": findings,
        "verdict": verdict,
        "explain": explain,
    }
    reviews.append(record)
    save_progress(drill_doc)
    return record


def set_explain(drill_id: str, qid: str, text: str) -> dict[str, Any]:
    """Set `explain` on the latest passing review record for `qid`."""
    if not text or not text.strip():
        raise ValueError("Explanation text must not be empty.")
    prog = load_progress(drill_id)
    if not prog:
        raise ValueError(f"No progress found for '{drill_id}'.")
    doc = _load_or_init_doc(drill_id)
    prob = find_problem(doc, qid)
    reviews = (prob.get("state") or {}).get("reviews") or []
    for rec in reversed(reviews):
        if rec.get("verdict") == "pass":
            rec["explain"] = text.strip()
            save_progress(doc)
            return rec
    raise ValueError(f"No passing review record found for {drill_id} {prob['id']}.")


def dispute_finding(drill_id: str, qid: str, check_id: str, reason: str) -> tuple[dict[str, Any], str]:
    """Mark a finding in the latest review record as disputed, log an issue, and recompute verdict."""
    if not reason or not reason.strip():
        raise ValueError("Dispute reason must not be empty.")
    prog = load_progress(drill_id)
    if not prog:
        raise ValueError(f"No progress found for '{drill_id}'.")
    doc = _load_or_init_doc(drill_id)
    prob = find_problem(doc, qid)
    pid = prob["id"]
    reviews = (prob.get("state") or {}).get("reviews") or []
    if not reviews:
        raise ValueError(f"No review records found for {drill_id} {pid}.")

    latest = reviews[-1]
    matches = [f for f in latest.get("findings") or [] if f.get("check") == check_id]
    if not matches:
        raise ValueError(f"Check '{check_id}' not found in latest review of {drill_id} {pid}.")

    issue_id, _ = add_issue(
        kind="reasoning",
        severity="batch",
        source="learner",
        where=f"{drill_id}/{pid}/{check_id}",
        what=reason.strip(),
        action="open",
    )
    for f in matches:
        f["disputed"] = {"reason": reason.strip(), "issueId": issue_id}

    latest["verdict"] = compute_verdict(
        latest.get("tests") or {},
        latest.get("lint") or [],
        latest.get("typecheck") or [],
        latest.get("findings") or [],
    )
    save_progress(doc)
    return latest, issue_id


def format_history(drill_id: str, qid: str | None = None) -> str:
    """Format review history for `drill_id` (optionally filtered to `qid`)."""
    prog = load_progress(drill_id)
    if not prog:
        return f"No progress recorded for {drill_id}."
    problems = prog.get("problems") or {}
    target_keys = sorted(problems.keys())
    if qid is not None:
        target_upper = qid.upper()
        target_keys = [k for k in target_keys if k.upper() == target_upper]

    lines: list[str] = []
    for pid in target_keys:
        reviews = (problems[pid] or {}).get("reviews") or []
        if not reviews:
            continue
        lines.append(f"{drill_id} {pid} ({len(reviews)} attempt(s)):")
        for r in reviews:
            tests = r.get("tests") or {}
            failed_n = len(tests.get("failed") or [])
            lint_rules = [item.get("rule", "?") for item in (r.get("lint") or [])]
            must_ids = [
                f["check"] + (" [disputed]" if f.get("disputed") else "")
                for f in (r.get("findings") or [])
                if f.get("severity") == "must"
            ]
            should_ids = [
                f["check"] + (" [disputed]" if f.get("disputed") else "")
                for f in (r.get("findings") or [])
                if f.get("severity") == "should"
            ]
            lint_str = ", ".join(lint_rules) if lint_rules else "none"
            must_str = ", ".join(must_ids) if must_ids else "none"
            should_str = ", ".join(should_ids) if should_ids else "none"
            lines.append(
                f"  #{r.get('attempt', '?')} {r.get('verdict', '?').upper()} | "
                f"failed_tests={failed_n} | lint=[{lint_str}] | "
                f"must=[{must_str}] | should=[{should_str}]"
            )
    if not lines:
        scope = f" {qid}" if qid else ""
        return f"No review records found for {drill_id}{scope}."
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.review_record",
        description="Record and inspect PRG code review attempts.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Re-run review_run, validate findings, and append a review record")
    p_add.add_argument("drill_id")
    p_add.add_argument("qid")
    p_add.add_argument("--findings", required=True, help="Path to JSON file containing list of findings")
    p_add.add_argument("--explain", default=None, help="Optional learner explanation")

    p_exp = sub.add_parser("explain", help="Set explain on the latest passing record")
    p_exp.add_argument("drill_id")
    p_exp.add_argument("qid")
    p_exp.add_argument("text")

    p_disp = sub.add_parser("dispute", help="Dispute a finding in the latest record and log an issue")
    p_disp.add_argument("drill_id")
    p_disp.add_argument("qid")
    p_disp.add_argument("check_id")
    p_disp.add_argument("--reason", required=True)

    p_show = sub.add_parser("show", help="Show review history per problem")
    p_show.add_argument("drill_id")
    p_show.add_argument("qid", nargs="?", default=None)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "add":
            raw = json.loads(Path(args.findings).read_text(encoding="utf-8"))
            if isinstance(raw, dict) and "findings" in raw:
                raw = raw["findings"]
            rec = add_record(args.drill_id, args.qid, raw, explain=args.explain)
            print(
                f"Recorded attempt #{rec['attempt']} for {args.drill_id} {args.qid.upper()}: "
                f"verdict={rec['verdict']} (tests {rec['tests']['passed']}/{rec['tests']['total']}, "
                f"lint={len(rec['lint'])}, typecheck={len(rec['typecheck'])}, findings={len(rec['findings'])})"
            )
        elif args.cmd == "explain":
            rec = set_explain(args.drill_id, args.qid, args.text)
            print(f"Saved explanation on attempt #{rec['attempt']} for {args.drill_id} {args.qid.upper()}.")
        elif args.cmd == "dispute":
            latest, issue_id = dispute_finding(args.drill_id, args.qid, args.check_id, args.reason)
            print(
                f"Disputed {args.check_id} on attempt #{latest['attempt']} (issue {issue_id}); "
                f"verdict={latest['verdict']}"
            )
        elif args.cmd == "show":
            print(format_history(args.drill_id, args.qid))
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
