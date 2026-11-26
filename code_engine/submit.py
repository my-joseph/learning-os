# -*- coding: utf-8 -*-
"""
Terminal Drill Submission & Telemetry Engine (Phase 3 Extension)

Allows developers to submit drills directly from their local workspace
via `npm run submit`, evaluates question-by-question acceptance criteria,
records execution telemetry, and syncs to Notion 'Learning Practice & Drills'.
100% self-contained with Python standard library.
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from code_engine.runners import (  # noqa: E402
    parse_completed_junit_run as _parse_completed_junit_run,  # noqa: F401 - re-exported for callers/tests
)
from code_engine.runners import (  # noqa: E402
    parse_junit_xml as _parse_junit_xml,  # noqa: F401 - re-exported for callers/tests
)
from code_engine.runners import (  # noqa: E402
    run_node_junit_cmd,
    run_vitest_junit,
)
from code_engine.sandbox import (  # noqa: E402
    JSON_SUFFIXES,
    assert_safe_contained_path,
    create_sandbox_dir,
    run_node_isolated,
    run_vitest_isolated,
    stage_workspace_copy,
)
from code_engine.workspace import (  # noqa: E402
    build_react_test_header,
    find_drill_json,
    resolve_test_imports,
    resolve_workspace_source,
)
from notion_sync.drill_sync import sync_drill_to_notion  # noqa: E402
from progress_store import cycle_evidence, score_problem  # noqa: E402

# ANSI Terminal Styling
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

_QID_BRACKET_RE = re.compile(r"\[(Q\d+)(?:\b|[-_\]])", re.IGNORECASE)
_QID_PREFIX_RE = re.compile(r"^(Q\d+)(?:[-_:\s]|$)", re.IGNORECASE)
_QID_FILE_RE = re.compile(r"(?:^|[/\\])(Q\d+)_", re.IGNORECASE)


def find_repo_root(start_dir: Path) -> Path:
    curr = start_dir.resolve()
    for _ in range(8):
        if (curr / "id_map.json").exists():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    return _REPO_ROOT


def resolve_workspace(drill_id: str, cwd: Path | None = None) -> tuple[Path, Path]:
    """Resolve checkout and workspace paths from the caller's directory."""
    current = (cwd or Path.cwd()).absolute()
    repo_root = find_repo_root(current)
    if current.name == drill_id and (current / "package.json").exists():
        boundary = repo_root if current.is_relative_to(repo_root) else current.parent
        return repo_root, assert_safe_contained_path(current, boundary, expect_file=False)
    pilot = os.environ.get("LEARNINGOS_PILOT", "").strip().lower() in ("1", "true", "yes")
    base = "pilot/workspace" if pilot else "drills/workspace"
    override = os.environ.get("WORKSPACE_DIR")
    if override:
        workspace = Path(override)
        workspace = assert_safe_contained_path(workspace, workspace.parent, expect_file=False, allow_missing=True)
    else:
        workspace = assert_safe_contained_path(
            f"{base}/{drill_id}", repo_root, expect_file=False, relative=True, allow_missing=True
        )
    return repo_root, workspace


def _write_hidden_test_file(
    tmp_dir: Path, ws_dir: Path, drill_id: str, prob: dict, is_ts: bool, react_dom: bool = False
) -> Path:
    pid = prob.get("id", "Q01")
    ext = "tsx" if react_dom else ("ts" if is_ts else "js")
    src_abs = resolve_workspace_source(ws_dir, drill_id, prob, ext, allow_missing=True)

    hidden_tests = prob.get("hiddenTests", [])
    hidden_code = "\n".join(ht.get("testCode", "") for ht in hidden_tests)
    import_names = resolve_test_imports(prob, hidden_code, src_path=src_abs)
    import_list = ", ".join(import_names)

    blocks = []
    for idx, ht in enumerate(hidden_tests, 1):
        ht_name = json.dumps(f"[{pid}-HIDDEN-T{idx:02d}] " + ht.get("name", f"hidden trap scenario {idx}"))
        ht_code = ht.get("testCode", "").strip()
        if react_dom:
            blocks.append(f"\ntest({ht_name}, async () => {{\n  {ht_code}\n}});\n")
        else:
            blocks.append(f"\ntest({ht_name}, async () => {{\n  {ht_code}\n}});\n")

    header = f"// Hidden Trap Test Suite for {pid}\n"
    if react_dom:
        header += build_react_test_header(import_list, hidden_code, str(src_abs))
    elif is_ts:
        header += "import test from 'node:test';\nimport assert from 'node:assert';\n"
        header += f"import {{ {import_list} }} from {json.dumps(src_abs.as_uri())};\n\n"
    else:
        header += (
            "const test = require('node:test');\n"
            "const assert = require('node:assert');\n"
            f"const {{ {import_list} }} = require({json.dumps(str(src_abs))});\n\n"
        )

    out_path = tmp_dir / f"{pid}_{src_abs.stem}.hidden.test.{ext}"
    out_path.write_text((header + "".join(blocks)).strip() + "\n", encoding="utf-8")
    return out_path


def _run_node_junit_cmd(
    cmd: list[str],
    *,
    cwd: Path,
    sandbox_root: Path,
    force_hidden: bool,
    timeout_sec: float | None = None,
    file_hint: str = "",
    qid_hint: str = "Q01",
) -> list[dict]:
    node_args = cmd[1:] if cmd and Path(cmd[0]).name == "node" else list(cmd)
    return run_node_junit_cmd(
        node_args,
        cwd=cwd,
        sandbox_root=sandbox_root,
        force_hidden=force_hidden,
        timeout_sec=timeout_sec,
        file_hint=file_hint,
        qid_hint=qid_hint,
        run_node_fn=run_node_isolated,
    )


def run_tests_junit(
    ws_dir: Path,
    drill_doc: dict | None = None,
    problem_id: str | None = None,
    *,
    timeout_sec: float | None = None,
) -> list:
    """Executes visible and hidden tests against a per-run isolated temp copy of `ws_dir`.

    When `problem_id` is given (e.g. 'Q01'), only that problem's visible test file and
    hiddenTests are executed.
    """
    ws_path = Path(ws_dir)
    if ws_path.is_symlink():
        raise ValueError(f"Refusing symlinked workspace directory: {ws_path}")
    ws_dir = ws_path.resolve()
    react_dom = (drill_doc or {}).get("environment") == "react-dom"
    shared_tools = (_REPO_ROOT / "tools" / "lint").resolve()
    shared_modules = (shared_tools / "node_modules").resolve()

    cases: list[dict] = []
    with create_sandbox_dir(prefix="prg_junit_") as sbx_str:
        sbx_root = Path(os.path.realpath(sbx_str))
        work_dir = stage_workspace_copy(ws_dir, sbx_root / "work")

        tsx_files = sorted(work_dir.glob("*.test.tsx"))
        ts_files = sorted(work_dir.glob("*.test.ts"))
        js_files = sorted(work_dir.glob("*.test.js"))
        is_ts = bool(ts_files or tsx_files)
        visible_files = tsx_files if react_dom or tsx_files else (ts_files if is_ts else js_files)
        if problem_id is not None:
            target = problem_id.upper()
            visible_files = [f for f in visible_files if f.name.split("_", 1)[0].upper() == target]

        needs_react = react_dom or any(vf.suffix == ".tsx" for vf in visible_files)
        if needs_react and shared_modules.is_dir():
            (work_dir / "node_modules").symlink_to(shared_modules, target_is_directory=True)

        if needs_react:
            if visible_files:
                cases.extend(
                    _run_vitest_junit(
                        visible_files,
                        work_dir,
                        timeout_sec=timeout_sec,
                        sandbox_root=sbx_root,
                    )
                )
        else:
            for vf in visible_files:
                cmd = ["node"]
                if is_ts:
                    cmd.append("--experimental-strip-types")
                cmd.extend(["--test", "--test-reporter=junit", vf.name])
                stem_prefix = vf.name.split("_", 1)[0].upper()
                qid_hint = stem_prefix if re.match(r"^Q\d+$", stem_prefix) else (problem_id or "Q01").upper()
                parsed = _run_node_junit_cmd(
                    cmd,
                    cwd=work_dir,
                    sandbox_root=sbx_root,
                    force_hidden=False,
                    timeout_sec=timeout_sec,
                    file_hint=vf.name,
                    qid_hint=qid_hint,
                )
                if re.match(r"^Q\d+$", stem_prefix):
                    for tc in parsed:
                        if not tc.get("file"):
                            tc["file"] = vf.name
                cases.extend(parsed)

        hidden_probs = [
            p
            for p in (drill_doc or {}).get("problems", [])
            if p.get("hiddenTests") and (problem_id is None or str(p.get("id", "")).upper() == problem_id.upper())
        ]
        if hidden_probs:
            hidden_dir = sbx_root / "hidden"
            hidden_dir.mkdir(parents=True, exist_ok=True)
            if react_dom and shared_modules.is_dir():
                (hidden_dir / "node_modules").symlink_to(shared_modules, target_is_directory=True)
            drill_id = (drill_doc or {}).get("drillId") or ws_dir.name
            hidden_files = [
                _write_hidden_test_file(hidden_dir, work_dir, drill_id, prob, is_ts, react_dom=react_dom)
                for prob in hidden_probs
            ]
            qid_hint = str(hidden_probs[0].get("id") or problem_id or "Q01").upper()
            if react_dom:
                cases.extend(
                    _run_vitest_junit(
                        hidden_files,
                        hidden_dir,
                        timeout_sec=timeout_sec,
                        force_hidden=True,
                        sandbox_root=sbx_root,
                    )
                )
            else:
                for hf in hidden_files:
                    stem_prefix = hf.name.split("_", 1)[0].upper()
                    hf_qid = stem_prefix if re.match(r"^Q\d+$", stem_prefix) else qid_hint
                    cmd = ["node"]
                    if is_ts:
                        cmd.append("--experimental-strip-types")
                    cmd.extend(["--test", "--test-reporter=junit", hf.name])
                    cases.extend(
                        _run_node_junit_cmd(
                            cmd,
                            cwd=hidden_dir,
                            sandbox_root=sbx_root,
                            force_hidden=True,
                            timeout_sec=timeout_sec,
                            file_hint=hf.name,
                            qid_hint=hf_qid,
                        )
                    )

    return cases


def _run_vitest_junit(
    test_files: list[Path],
    cwd: Path,
    *,
    timeout_sec: float | None = None,
    force_hidden: bool = False,
    env: dict[str, str] | None = None,
    require_complete: bool = False,
    sandbox_root: Path | None = None,
) -> list[dict]:
    """Run React component tests with shared Vitest inside the sandbox and return JUnit cases."""
    return run_vitest_junit(
        test_files,
        cwd,
        timeout_sec=timeout_sec,
        force_hidden=force_hidden,
        env=env,
        require_complete=require_complete,
        sandbox_root=sandbox_root,
        tools_lint_dir=_REPO_ROOT / "tools" / "lint",
        run_vitest_fn=run_vitest_isolated,
    )


def extract_qid(tc: dict, default: str = "Q01") -> str:
    """Extract a canonical QID (e.g. 'Q01') from a parsed JUnit testcase dict."""
    if tc.get("qid"):
        return str(tc["qid"]).upper()
    name = str(tc.get("name", ""))
    m = _QID_BRACKET_RE.search(name)
    if m:
        return m.group(1).upper()
    m = _QID_PREFIX_RE.match(name.strip())
    if m:
        return m.group(1).upper()
    for field in (tc.get("file", ""), tc.get("classname", "")):
        if field:
            fm = _QID_FILE_RE.search(str(field))
            if fm:
                return fm.group(1).upper()
    return default.upper()


def group_cases_by_qid(cases: list[dict]) -> dict[str, list[dict]]:
    """Group parsed JUnit testcases by canonical Question ID."""
    q_groups: dict[str, list[dict]] = {}
    for tc in cases:
        qid = extract_qid(tc)
        q_groups.setdefault(qid, []).append(tc)
    return q_groups


def evaluate_and_record_submission(
    drill_doc: dict,
    cases: list[dict],
    now_iso: str | None = None,
) -> dict:
    """Record tests per QID and compute the session summary from current-cycle scores."""
    # Use the same millisecond UTC timestamp format as Studio and terminal review records for evidence ordering.
    attempt_date = now_iso or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )
    q_groups = group_cases_by_qid(cases)
    prob_by_id = {str(p.get("id", "")).upper(): p for p in drill_doc.get("problems", []) if p.get("id")}
    all_qids = sorted(set(q_groups.keys()) | set(prob_by_id.keys()))

    evaluated_questions = []
    total_score = 0.0
    total_reviewed_passed = 0
    total_tests_passed = 0
    failing_reasons = []
    any_test_failed = False

    for qid in all_qids:
        tcs = q_groups.get(qid, [])
        vis_tcs = [tc for tc in tcs if not tc.get("is_hidden")]
        hid_tcs = [tc for tc in tcs if tc.get("is_hidden")]

        vis_pass = sum(1 for tc in vis_tcs if tc["passed"])
        hid_pass = sum(1 for tc in hid_tcs if tc["passed"])
        tests_passed = bool(tcs) and all(tc["passed"] for tc in tcs)
        if tests_passed:
            total_tests_passed += 1
        else:
            any_test_failed = True
            if tcs:
                first_fail = next(tc for tc in tcs if not tc["passed"])
                if first_fail.get("is_hidden"):
                    failing_reasons.append(f"[{qid}] Hidden checks failed.")
                else:
                    failing_reasons.append(f"[{qid}] {first_fail['name']}: {first_fail['failure_msg'][:80]}")
            else:
                failing_reasons.append(f"[{qid}] No tests executed.")

        prob = prob_by_id.get(qid)
        state = (prob or {}).get("state") or {}
        if prob is not None:
            prob["state"] = state
        run = {
            "ts": attempt_date,
            "allPassed": tests_passed,
            "passedCount": vis_pass + hid_pass,
            "totalCount": len(tcs),
        }
        state["lastTestReport"] = {
            **run,
            "visiblePassed": vis_pass,
            "visibleTotal": len(vis_tcs),
            "hiddenPassed": hid_pass,
            "hiddenTotal": len(hid_tcs),
        }
        test_runs = state.get("testRuns")
        state["testRuns"] = [*test_runs, run] if isinstance(test_runs, list) else [run]
        state["skipped"] = False

        score = score_problem(state, is_prg=True)["score"]
        state["score"] = score
        total_score += score or 0.0
        current_reviews = cycle_evidence(state)["reviews"]
        review_verdict = current_reviews[-1]["verdict"] if current_reviews else None
        passed = tests_passed and score in (0.5, 1.0)
        if passed:
            total_reviewed_passed += 1
        elif tests_passed:
            failing_reasons.append(f"[{qid}] Tests passed; awaiting passing code review (scripts.review_record).")

        evaluated_questions.append(
            {
                "qid": qid,
                "passed": passed,
                "tests_passed": tests_passed,
                "review_verdict": review_verdict,
                "vis_pass": vis_pass,
                "vis_total": len(vis_tcs),
                "hid_pass": hid_pass,
                "hid_total": len(hid_tcs),
                "hidden_breached": (vis_pass == len(vis_tcs) and hid_pass < len(hid_tcs)) if hid_tcs else False,
            }
        )

    max_score = len(evaluated_questions)
    all_green = total_reviewed_passed == max_score and max_score > 0
    practice_status = "Graded" if all_green else "Needs Retry"
    pct = round((total_score / max_score * 100), 1) if max_score > 0 else 0.0

    if any_test_failed:
        mistake_cats = ["Assertion Failure / Unhandled Edge Case"]
    elif not all_green:
        mistake_cats = ["Pending Code Review"]
    else:
        mistake_cats = []

    drill_doc["sessionSummary"] = {
        "score": total_score,
        "maxScore": max_score,
        "accuracyPct": pct,
        "practiceStatus": practice_status,
        "mistakeCategories": mistake_cats,
        "divergedStepsSummary": " | ".join(failing_reasons)
        if failing_reasons
        else "All question test suites and code reviews passed.",
        "attemptDate": attempt_date,
    }

    return {
        "evaluated_questions": evaluated_questions,
        "score": total_score,
        "total_reviewed_passed": total_reviewed_passed,
        "total_tests_passed": total_tests_passed,
        "max_score": max_score,
        "pct": pct,
        "all_green": all_green,
        "practice_status": practice_status,
    }


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Evaluate and record a PRG drill submission.")
    parser.add_argument("--drill", help="Drill ID (defaults to the current workspace folder)")
    args = parser.parse_args(argv)
    cwd = Path.cwd().resolve()
    drill_id = args.drill or cwd.name
    repo_root, ws_dir = resolve_workspace(drill_id, cwd)

    if not ws_dir.is_dir():
        raise SystemExit(f"Workspace not found: {ws_dir}")
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from progress_store import apply_progress, load_progress

    data_root = assert_safe_contained_path("drills/data", repo_root, expect_file=False, relative=True)
    data_path = find_drill_json(drill_id, data_root)
    drill_doc = json.loads(
        assert_safe_contained_path(data_path, data_root, suffixes=JSON_SUFFIXES).read_text(encoding="utf-8")
    )
    if drill_doc.get("drillId", drill_id) != drill_id:
        raise SystemExit("Drill ID does not match its filename")
    apply_progress(drill_doc, load_progress(drill_id, str(repo_root)))

    print(f"\n{BOLD}{CYAN}========================================================================={RESET}")
    print(f"{BOLD}  DRILL SUBMISSION ENGINE: {drill_id}{RESET}")
    print(f"{DIM}  {drill_doc.get('unitTitle', 'Programming Practice')} ({drill_doc.get('unitCode', 'PRG')}){RESET}")
    print(f"{BOLD}{CYAN}========================================================================={RESET}\n")

    print(f"{CYAN}▶ Executing Acceptance Test Suites...{RESET}")
    cases = run_tests_junit(ws_dir, drill_doc)

    if not cases:
        print(f"{RED}✗ No tests detected or test runner encountered an internal crash.{RESET}")
        sys.exit(1)

    summary_res = evaluate_and_record_submission(drill_doc, cases)
    evaluated_questions = summary_res["evaluated_questions"]
    score = summary_res["score"]
    total_tests_passed = summary_res["total_tests_passed"]
    max_score = summary_res["max_score"]
    pct = summary_res["pct"]
    all_green = summary_res["all_green"]

    print(f"\n{BOLD}Question Acceptance Breakdown:{RESET}")
    for eq in evaluated_questions:
        test_mark = f"{GREEN}✔ TESTS PASS{RESET}" if eq["tests_passed"] else f"{RED}✗ TESTS FAIL{RESET}"
        if eq["passed"]:
            rev_mark = f"{GREEN}review: PASS{RESET}"
        elif eq["review_verdict"]:
            rev_mark = f"{YELLOW}review: {eq['review_verdict'].upper()}{RESET}"
        else:
            rev_mark = f"{YELLOW}review: PENDING{RESET}"
        detail = f"{eq['vis_pass']}/{eq['vis_total']} visible"
        if eq["hid_total"] > 0:
            detail += f" + {eq['hid_pass']}/{eq['hid_total']} hidden traps"
        print(f"  [{eq['qid']}] {test_mark} | {rev_mark}  ({detail})")
        if eq["hidden_breached"]:
            print(
                f"      {YELLOW}⚠ Notice: Visible scenarios passed, but Hidden Trap tests failed (Boundary/Hardcode trap).{RESET}"
            )

    print(f"\n{BOLD}-------------------------------------------------------------------------{RESET}")
    print(f"  {BOLD}TESTS:{RESET}  {total_tests_passed} / {max_score} Questions Passing Tests")
    score_col = GREEN if all_green else YELLOW if score > 0 else RED
    print(f"  {BOLD}SCORE:{RESET}  {score_col}{score:g} / {max_score} ({pct}%){RESET}")
    status_label = f"{GREEN}GRADED (PASSED){RESET}" if all_green else f"{RED}NEEDS RETRY{RESET}"
    print(f"  {BOLD}STATUS:{RESET} {status_label}")
    print(f"{BOLD}-------------------------------------------------------------------------{RESET}\n")

    print(f"{CYAN}▶ Synchronizing Telemetry with Notion via notion_sync.drill_sync...{RESET}")
    old_cwd = Path.cwd()
    os.chdir(repo_root)
    try:
        sync_res = sync_drill_to_notion(drill_doc)
    finally:
        os.chdir(old_cwd)

    if sync_res.get("dryRun"):
        print(f"{YELLOW}[DRY RUN] Saved locally; Notion write skipped (mock-{drill_id}).{RESET}\n")
    elif sync_res.get("pilotSkipped"):
        print(f"{YELLOW}[PILOT] Saved locally to pilot/progress; Notion write skipped.{RESET}\n")
    elif sync_res.get("degraded"):
        print(f"{YELLOW}⚠ {sync_res.get('warning', 'Saved locally; Notion was not updated.')}{RESET}\n")
    elif sync_res.get("partial"):
        failed_steps = ", ".join(sync_res["failedSteps"])
        print(f"{YELLOW}Synced with problems. Incomplete steps: {failed_steps}.{RESET}\n")
    elif sync_res.get("ok") and sync_res.get("drillPageId"):
        page_url = f"https://notion.so/{sync_res['drillPageId'].replace('-', '')}"
        print(f"{GREEN}✔ Successfully synced to Notion!{RESET}")
        print(f"  {BOLD}Notion Page:{RESET} {CYAN}{page_url}{RESET}\n")
    else:
        print(f"{RED}✗ Notion sync encountered an error: {sync_res.get('error', 'Unknown error')}{RESET}\n")

    if not all_green:
        sys.exit(1)
    else:
        print(f"{GREEN}{BOLD}🎉 ALL EXERCISES COMPLETED AND VERIFIED!{RESET}\n")
        sys.exit(1 if sync_res.get("partial") else 0)


if __name__ == "__main__":
    main()
