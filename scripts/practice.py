"""Pilot-only terminal tool for practising math drills outside Practice Studio.

NOTE (learner decision 2026-11-20): this CLI is a **pilot-only** terminal runner
intended for automated/AI stand-in practice (`LEARNINGOS_PILOT=1`). Real learner
sessions use Practice Studio (`practice-studio/`), which enforces full reveal gating.
This script intentionally does not implement pre-attempt reveal gating on `setup` or
`solution`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path
from typing import Any

from math_engine.answer_check import TRAP_VERDICTS, check_answer, match_trap
from math_engine.figure_svg import figure_to_svg
from progress_store import (
    apply_progress,
    is_locked_after_correct,
    progress_root,
    save_progress,
    score_problem,
    workspace_root,
)

PILOT_ONLY_BANNER = (
    "[pilot-only] scripts.practice is a pilot-only terminal tool (no reveal gating); "
    "use Practice Studio for real learner sessions."
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_drill(drill_id: str) -> dict[str, Any]:
    if not drill_id.startswith("DRL-") or any(part in drill_id for part in ("/", "\\", "..")):
        raise ValueError(f"Invalid drill ID: {drill_id}")
    root = _repo_root() / "drills" / "data"
    matches = list(root.glob(f"*/{drill_id}.json"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one drill named {drill_id}; found {len(matches)}")
    doc = json.loads(matches[0].read_text(encoding="utf-8"))
    return apply_progress(doc, _read_progress(drill_id))


def _read_progress(drill_id: str) -> dict[str, Any] | None:
    path = Path(progress_root(str(_repo_root()))) / f"{drill_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save(doc: dict[str, Any]) -> None:
    save_progress(doc, str(_repo_root()))


def _problem(doc: dict[str, Any], qid: str) -> dict[str, Any]:
    for problem in doc.get("problems", []):
        if problem.get("id") == qid:
            return problem
    raise ValueError(f"Unknown question {qid} in {doc.get('drillId')}")


def _state(problem: dict[str, Any]) -> dict[str, Any]:
    state = problem.setdefault("state", {})
    state.setdefault("userInput", "")
    state.setdefault("score", None)
    state.setdefault("divergedStep", None)
    state.setdefault("mistakes", [])
    state.setdefault("attempts", [])
    state.setdefault("hintsRevealed", 0)
    state.setdefault("durationMs", 0)
    return state


def _show(doc: dict[str, Any], qid: str | None) -> None:
    problems = [_problem(doc, qid)] if qid else doc.get("problems", [])
    for p in problems:
        print(f"{p.get('id', 'Question')}: {p.get('prompt', '')}")
        if p.get("figure"):
            svg = figure_to_svg(p["figure"])
            out = Path(workspace_root(str(_repo_root()))) / doc["drillId"] / f"{p.get('id', 'figure')}.svg"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(svg, encoding="utf-8")
            print(f"Figure SVG: {out}")
        if p.get("inputHint"):
            print(f"Input hint: {p['inputHint']}")
        print()


def _summary(doc: dict[str, Any]) -> dict[str, Any]:
    is_prg = doc.get("subject") == "PRG"
    problems = doc.get("problems", [])
    scored = [score_problem(p.get("state"), is_prg=is_prg) for p in problems]
    attempted = [res["score"] for res in scored if res["score"] is not None]
    total = len(problems)
    score = sum(attempted)
    skipped = [p["id"] for p, res in zip(problems, scored) if res["outcome"] == "skipped"]
    mistakes = sorted({tag for p in problems for tag in p.get("state", {}).get("mistakes", [])})
    if not attempted:
        status = "Ready"
    elif len(attempted) < total:
        status = "In Progress"
    elif total > 0 and score / total >= 0.8:
        status = "Graded"
    else:
        status = "Needs Retry"
    accuracy_pct = math.floor((score / total) * 1000 + 0.5) / 10 if total else 0
    return {
        "practiceStatus": status,
        "score": score,
        "maxScore": total,
        "accuracyPct": accuracy_pct,
        "skippedCount": len(skipped),
        "skippedProblems": skipped,
        "mistakeCategories": mistakes,
        "attemptDate": dt.datetime.now(dt.timezone.utc).date().isoformat() if attempted else None,
    }


def _record_answer(doc: dict[str, Any], qid: str, raw: str) -> dict[str, Any]:
    p = _problem(doc, qid)
    state = _state(p)
    trimmed = raw.strip()
    if not trimmed:
        print("Enter an answer; empty input was not recorded.")
        return {
            "verdict": "invalid input",
            "message": "Type your final answer first.",
            "components": [],
            "diagnostics": [],
        }

    result = check_answer(p.get("answerSpec", {}), trimmed)
    trap = p.get("trapValue")
    if (
        result.get("verdict") in TRAP_VERDICTS
        and trap is not None
        and match_trap(p.get("answerSpec", {}), trimmed, trap)
    ):
        result["trapMatched"] = True

    attempts = list(state.get("attempts") or [])
    if is_locked_after_correct(state):
        return state.get("lastCheck") or result

    mistakes = set(state.get("mistakes") or [])

    matched_tag = None
    diag_codes = [d.get("code") for d in result.get("diagnostics", [])]
    if result["verdict"] == "incorrect":
        spec = p.get("answerSpec", {})
        if spec.get("type") == "choice":
            chosen = next((o for o in spec.get("options", []) if str(o.get("id", "")).strip() == trimmed), None)
            choice_tag = (chosen or {}).get("trapTag") or (chosen or {}).get("tag")
            if choice_tag:
                mistakes.add(choice_tag)
                matched_tag = choice_tag
        if result.get("trapMatched") and p.get("commonTrapTag"):
            mistakes.add(p["commonTrapTag"])
            matched_tag = p["commonTrapTag"]
        if not result.get("trapMatched"):
            for tag in doc.get("mistakeTags", []):
                if any(code in diag_codes for code in tag.get("autoFrom", [])):
                    mistakes.add(tag["id"])
        if not mistakes:
            mistakes.add("unclassified")
    elif result["verdict"] == "partial" and result.get("trapMatched") and p.get("commonTrapTag"):
        mistakes.add(p["commonTrapTag"])
        matched_tag = p["commonTrapTag"]
    elif result["verdict"] != "correct":
        for tag in doc.get("mistakeTags", []):
            if any(code in diag_codes for code in tag.get("autoFrom", [])):
                mistakes.add(tag["id"])

    timestamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    attempt = {"input": trimmed, "ts": timestamp, "verdict": result["verdict"]}
    if diag_codes:
        attempt["diagnosticCodes"] = diag_codes
    if matched_tag:
        attempt["matchedTrap"] = matched_tag
    if state.get("setupRevealedBeforeAnswer"):
        attempt["setupRevealed"] = True
    if state.get("solutionRevealedBeforeAnswer"):
        attempt["solutionRevealed"] = True
    substantive = result["verdict"] not in ("invalid input", "parse_error")
    state.update(
        {
            "userInput": trimmed,
            "skipped": False if substantive else bool(state.get("skipped")),
            "mistakes": sorted(mistakes),
            "lastCheck": result,
            "attempts": [*attempts, attempt],
        }
    )
    state["score"] = score_problem(state, ignore_state_score=True)["score"]
    doc["sessionSummary"] = _summary(doc)
    _save(doc)
    print(json.dumps(result, ensure_ascii=False))
    print(f"Score: {state['score']}")
    return result


def _has_cycle_original_check(state: dict[str, Any]) -> bool:
    """Return True if the problem has an original (non-variant) check attempt in the current cycle."""
    raw_cycle = state.get("cycleStartedAt")
    cycle_start = raw_cycle if isinstance(raw_cycle, str) and raw_cycle else None
    raw_attempts = state.get("attempts") if isinstance(state.get("attempts"), list) else []
    orig_attempts = [a for a in raw_attempts if isinstance(a, dict) and a.get("kind") != "variant"]
    if orig_attempts:
        return any(
            not cycle_start or (isinstance(a.get("ts"), str) and bool(a["ts"]) and a["ts"] >= cycle_start)
            for a in orig_attempts
        )
    return not cycle_start and bool(state.get("lastCheck"))


def _mark_setup_reveal(state: dict[str, Any]) -> None:
    if not _has_cycle_original_check(state):
        state["setupRevealedBeforeAnswer"] = True


def _mark_solution_reveal(state: dict[str, Any]) -> None:
    if not is_locked_after_correct(state):
        state["solutionRevealedBeforeAnswer"] = True


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Pilot-only terminal tool to practise a math drill locally and save progress "
            "outside drill data. Use Practice Studio for real learner sessions."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("show", help="Show learner-facing prompt, figure SVG path, and input hint")
    show.add_argument("drill_id")
    show.add_argument("qid", nargs="?")
    for name in ("answer", "hint", "setup", "solution"):
        cmd = sub.add_parser(name)
        cmd.add_argument("drill_id")
        cmd.add_argument("qid")
        if name == "answer":
            cmd.add_argument("input", help="Learner answer (quote inputs containing spaces)")
    summary = sub.add_parser("summary", help="Summarize saved practice progress")
    summary.add_argument("drill_id")
    submit = sub.add_parser("submit", help="Save and print the completed practice session summary")
    submit.add_argument("drill_id")
    args = parser.parse_args(argv)
    print(PILOT_ONLY_BANNER, file=sys.stderr)
    try:
        doc = _load_drill(args.drill_id)
        if args.command == "show":
            _show(doc, args.qid)
        elif args.command == "answer":
            _record_answer(doc, args.qid, args.input)
        elif args.command == "hint":
            p = _problem(doc, args.qid)
            state = _state(p)
            state["hintsRevealed"] = int(state.get("hintsRevealed") or 0) + 1
            _save(doc)
            print(p.get("checkpointHint", "No hint is available."))
        elif args.command == "setup":
            p = _problem(doc, args.qid)
            state = _state(p)
            _mark_setup_reveal(state)
            _save(doc)
            print(p.get("display") or p.get("plainText") or "No equation set-up is available.")
        elif args.command == "solution":
            p = _problem(doc, args.qid)
            state = _state(p)
            _mark_solution_reveal(state)
            _save(doc)
            for i, step in enumerate(p.get("steps", []), 1):
                print(f"{i}. {step.get('latex', '')}\n   {step.get('explain', '')}")
        elif args.command == "summary":
            print(json.dumps(_summary(doc), ensure_ascii=False, indent=2))
        elif args.command == "submit":
            doc["sessionSummary"] = _summary(doc)
            _save(doc)
            print(json.dumps(doc["sessionSummary"], ensure_ascii=False, indent=2))
        return 0
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"practice: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
