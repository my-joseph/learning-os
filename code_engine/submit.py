# -*- coding: utf-8 -*-
"""
Terminal Drill Submission & Telemetry Engine (Phase 3 Extension)

Allows developers to submit drills directly from their local workspace
via `npm run submit`, evaluates question-by-question acceptance criteria,
records execution telemetry, and syncs to Notion 'Learning Practice & Drills'.
100% self-contained with Python standard library.
"""

import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from code_engine.workspace import resolve_test_imports  # noqa: E402
from notion_sync.drill_sync import sync_drill_to_notion  # noqa: E402

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


def _parse_junit_xml(raw: str, force_hidden: bool = False) -> list:
    xml_start = raw.find("<?xml")
    if xml_start == -1:
        xml_start = raw.find("<testsuites")
    if xml_start == -1:
        return []

    xml_text = raw[xml_start:].strip()
    end_tag = "</testsuites>"
    end_idx = xml_text.rfind(end_tag)
    if end_idx != -1:
        xml_text = xml_text[: end_idx + len(end_tag)]

    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return []

    cases = []
    for tc in root.findall(".//testcase"):
        name = tc.attrib.get("name", "")
        f_elem = tc.find("failure")
        if f_elem is None:
            f_elem = tc.find("error")
        is_fail = f_elem is not None
        fail_msg = ""
        if is_fail:
            fail_msg = f_elem.attrib.get("message", f_elem.text or "Assertion failed")

        is_hidden = force_hidden or "HIDDEN" in name.upper()
        cases.append(
            {
                "name": name,
                "file": tc.attrib.get("file", ""),
                "classname": tc.attrib.get("classname", ""),
                "passed": not is_fail,
                "failure_msg": fail_msg,
                "is_hidden": is_hidden,
            }
        )
    return cases


def _write_hidden_test_file(tmp_dir: Path, ws_dir: Path, prob: dict, is_ts: bool) -> Path:
    pid = prob.get("id", "Q01")
    entry_name = prob.get("entryPoint") or pid.lower()
    ext = "ts" if is_ts else "js"
    src_abs = (ws_dir / f"{pid}_{entry_name}.{ext}").resolve()

    hidden_tests = prob.get("hiddenTests", [])
    hidden_code = "\n".join(ht.get("testCode", "") for ht in hidden_tests)
    import_names = resolve_test_imports(prob, hidden_code, src_path=src_abs)
    import_list = ", ".join(import_names)

    blocks = []
    for idx, ht in enumerate(hidden_tests, 1):
        ht_name = json.dumps(f"[{pid}-HIDDEN-T{idx:02d}] " + ht.get("name", f"hidden trap scenario {idx}"))
        ht_code = ht.get("testCode", "").strip()
        blocks.append(f"\ntest({ht_name}, async () => {{\n  {ht_code}\n}});\n")

    header = f"// Hidden Trap Test Suite for {pid}\n"
    if is_ts:
        header += "import test from 'node:test';\nimport assert from 'node:assert';\n"
        header += f"import {{ {import_list} }} from {json.dumps(src_abs.as_uri())};\n\n"
    else:
        header += (
            "const test = require('node:test');\n"
            "const assert = require('node:assert');\n"
            f"const {{ {import_list} }} = require({json.dumps(str(src_abs))});\n\n"
        )

    out_path = tmp_dir / f"{pid}_{entry_name}.hidden.test.{ext}"
    out_path.write_text((header + "".join(blocks)).strip() + "\n", encoding="utf-8")
    return out_path


def _run_node_junit_cmd(
    cmd: list[str],
    *,
    cwd: Path,
    force_hidden: bool,
    timeout_sec: float | None = None,
    file_hint: str = "",
    qid_hint: str = "Q01",
) -> list[dict]:
    run_kwargs: dict = {"cwd": cwd, "capture_output": True, "text": True}
    if timeout_sec is not None:
        run_kwargs["timeout"] = timeout_sec
    try:
        proc = subprocess.run(cmd, **run_kwargs)
    except subprocess.TimeoutExpired:
        return [
            {
                "name": f"[{qid_hint}] Timeout",
                "file": file_hint,
                "classname": "",
                "passed": False,
                "failure_msg": f"Execution exceeded {timeout_sec}s limit",
                "is_hidden": force_hidden,
            }
        ]
    parsed = _parse_junit_xml(proc.stdout + "\n" + proc.stderr, force_hidden=force_hidden)
    if not parsed and proc.returncode != 0:
        err_msg = (proc.stderr or proc.stdout or f"Exited with code {proc.returncode}").strip()
        return [
            {
                "name": f"[{qid_hint}] Execution failure",
                "file": file_hint,
                "classname": "",
                "passed": False,
                "failure_msg": err_msg,
                "is_hidden": force_hidden,
            }
        ]
    return parsed


def run_tests_junit(
    ws_dir: Path,
    drill_doc: dict | None = None,
    problem_id: str | None = None,
    *,
    timeout_sec: float | None = None,
) -> list:
    """Executes visible tests in ws_dir and hidden tests from a temporary dir outside ws_dir.

    When `problem_id` is given (e.g. 'Q01'), only that problem's visible test file and
    hiddenTests are executed.
    """
    ws_dir = Path(ws_dir).resolve()
    ts_files = sorted(ws_dir.glob("*.test.ts"))
    js_files = sorted(ws_dir.glob("*.test.js"))
    is_ts = bool(ts_files)
    visible_files = ts_files if is_ts else js_files
    if problem_id is not None:
        target = problem_id.upper()
        visible_files = [f for f in visible_files if f.name.split("_", 1)[0].upper() == target]

    cases = []
    for vf in visible_files:
        cmd = ["node"]
        if is_ts:
            cmd.append("--experimental-strip-types")
        cmd.extend(["--test", "--test-reporter=junit", str(vf)])
        stem_prefix = vf.name.split("_", 1)[0].upper()
        qid_hint = stem_prefix if re.match(r"^Q\d+$", stem_prefix) else (problem_id or "Q01").upper()
        parsed = _run_node_junit_cmd(
            cmd,
            cwd=ws_dir,
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
        with tempfile.TemporaryDirectory(prefix="prg_hidden_") as tmp_str:
            tmp_dir = Path(tmp_str)
            hidden_files = [_write_hidden_test_file(tmp_dir, ws_dir, prob, is_ts) for prob in hidden_probs]
            cmd = ["node"]
            if is_ts:
                cmd.append("--experimental-strip-types")
            cmd.extend(["--test", "--test-reporter=junit", *[str(f) for f in hidden_files]])
            qid_hint = str(hidden_probs[0].get("id") or problem_id or "Q01").upper()
            cases.extend(
                _run_node_junit_cmd(
                    cmd,
                    cwd=tmp_dir,
                    force_hidden=True,
                    timeout_sec=timeout_sec,
                    qid_hint=qid_hint,
                )
            )

    return cases


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
    """Evaluate testcases per QID, record `lastTestReport`, and compute review-gated sessionSummary.

    A PRG problem counts as passed ONLY when its latest review record in `state.reviews`
    has `verdict == "pass"`. Tests alone never mark a problem correct.
    """
    attempt_date = now_iso or datetime.datetime.now(datetime.timezone.utc).isoformat()
    q_groups = group_cases_by_qid(cases)
    prob_by_id = {str(p.get("id", "")).upper(): p for p in drill_doc.get("problems", []) if p.get("id")}
    all_qids = sorted(set(q_groups.keys()) | set(prob_by_id.keys()))

    evaluated_questions = []
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
                prefix = "[HIDDEN TRAP] " if first_fail.get("is_hidden") else ""
                failing_reasons.append(f"[{qid}] {prefix}{first_fail['name']}: {first_fail['failure_msg'][:80]}")
            else:
                failing_reasons.append(f"[{qid}] No tests executed.")

        prob = prob_by_id.get(qid)
        reviews = ((prob or {}).get("state") or {}).get("reviews") or []
        latest_review = reviews[-1] if reviews else None
        review_verdict = latest_review.get("verdict") if isinstance(latest_review, dict) else None
        review_passed = review_verdict == "pass"

        if prob is not None:
            state = prob.setdefault("state", {})
            state["lastTestReport"] = {
                "allPassed": tests_passed,
                "visiblePassed": vis_pass,
                "visibleTotal": len(vis_tcs),
                "hiddenPassed": hid_pass,
                "hiddenTotal": len(hid_tcs),
                "passedCount": vis_pass + hid_pass,
                "totalCount": len(tcs),
                "updatedAt": attempt_date,
            }

        if review_passed:
            total_reviewed_passed += 1
        elif tests_passed:
            failing_reasons.append(f"[{qid}] Tests passed; awaiting passing code review (scripts.review_record).")

        evaluated_questions.append(
            {
                "qid": qid,
                "passed": review_passed,
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
    pct = round((total_reviewed_passed / max_score * 100), 1) if max_score > 0 else 0.0

    if any_test_failed:
        mistake_cats = ["Assertion Failure / Unhandled Edge Case"]
    elif not all_green:
        mistake_cats = ["Pending Code Review"]
    else:
        mistake_cats = []

    drill_doc["sessionSummary"] = {
        "score": total_reviewed_passed,
        "maxScore": max_score,
        "accuracyPct": pct,
        "practiceStatus": practice_status,
        "mistakeCategories": mistake_cats,
        "divergedStepsSummary": " | ".join(failing_reasons)
        if failing_reasons
        else "All question test suites and code reviews passed 100% verified.",
        "attemptDate": attempt_date,
    }

    return {
        "evaluated_questions": evaluated_questions,
        "total_reviewed_passed": total_reviewed_passed,
        "total_tests_passed": total_tests_passed,
        "max_score": max_score,
        "pct": pct,
        "all_green": all_green,
        "practice_status": practice_status,
    }


def main():
    ws_dir = Path.cwd().resolve()
    drill_id = ws_dir.name

    repo_root = find_repo_root(ws_dir)
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from progress_store import apply_progress, load_progress

    # Locate drill JSON doc
    data_files = list(repo_root.glob(f"drills/data/**/{drill_id}.json"))
    drill_doc = None
    if data_files:
        data_path = data_files[0]
        with open(data_path, "r", encoding="utf-8") as f:
            drill_doc = json.load(f)
        apply_progress(drill_doc, load_progress(drill_id, str(repo_root)))
    else:
        drill_doc = {
            "drillId": drill_id,
            "subject": "PRG",
            "unitCode": "PRG-T01-C04",
            "unitTitle": "Problem Solving & Utility Toolkit",
            "chapterCode": "PRG-T01-C04",
            "topicCode": "PRG-T01",
            "problems": [],
        }

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
    total_reviewed_passed = summary_res["total_reviewed_passed"]
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
    score_col = GREEN if all_green else YELLOW if total_reviewed_passed > 0 else RED
    print(
        f"  {BOLD}SCORE:{RESET}  {score_col}{total_reviewed_passed} / {max_score} Questions Passed Review ({pct}%){RESET}"
    )
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
        sys.exit(0)


if __name__ == "__main__":
    main()
