# -*- coding: utf-8 -*-
"""
Terminal Drill Submission & Telemetry Engine (Phase 3 Extension)

Allows developers to submit drills directly from their local workspace
via `npm run submit`, evaluates question-by-question acceptance criteria,
records execution telemetry, and syncs to Notion 'Learning Practice & Drills'.
100% self-contained with Python standard library.
"""
import os
import sys
import json
import ssl
import time
import urllib.request
import urllib.error
import subprocess
import datetime
import xml.etree.ElementTree as ET
from pathlib import Path

# ANSI Terminal Styling
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

SSL_CTX = (
    ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    if os.path.exists("/etc/ssl/cert.pem")
    else ssl.create_default_context()
)


def find_repo_root(start_dir: Path) -> Path:
    curr = start_dir.resolve()
    for _ in range(8):
        if (curr / "id_map.json").exists() and (curr / ".env").exists():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    return start_dir.resolve()


def load_env(repo_root: Path) -> dict:
    env = {}
    env_file = repo_root / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def notion_request(method: str, endpoint: str, token: str, payload: dict = None, max_retries: int = 5):
    url = f"https://api.notion.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (409, 429, 500, 502, 503, 504) and attempt < max_retries - 1:
                time.sleep(1.5 * (2 ** attempt))
                continue
            body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {e.code} on {method} {endpoint}: {body}") from e


def run_tests_junit(ws_dir: Path) -> list:
    """Executes test suite with JUnit reporter and parses visible + hidden testcases."""
    has_ts = bool(list(ws_dir.glob("*.test.ts")))
    canonical_dir = ws_dir / ".canonical"
    has_hidden = bool(list(canonical_dir.glob("*.hidden.test.*"))) if canonical_dir.exists() else False

    if has_ts:
        cmd = "node --experimental-strip-types --test --test-reporter=junit *.test.ts"
        if has_hidden:
            cmd += " .canonical/*.hidden.test.ts"
    else:
        cmd = "node --test --test-reporter=junit *.test.js"
        if has_hidden:
            cmd += " .canonical/*.hidden.test.js"

    proc = subprocess.run(cmd, shell=True, cwd=ws_dir, capture_output=True, text=True)
    raw = proc.stdout + "\n" + proc.stderr

    xml_start = raw.find("<?xml")
    if xml_start == -1:
        xml_start = raw.find("<testsuites")
    if xml_start == -1:
        return []

    xml_text = raw[xml_start:].strip()
    end_tag = "</testsuites>"
    end_idx = xml_text.rfind(end_tag)
    if end_idx != -1:
        xml_text = xml_text[:end_idx + len(end_tag)]

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
        
        is_hidden = "HIDDEN" in name.upper() or ".canonical" in tc.attrib.get("file", "")
        cases.append({
            "name": name,
            "passed": not is_fail,
            "failure_msg": fail_msg,
            "is_hidden": is_hidden,
        })
    return cases


def sync_drill_telemetry_to_notion(repo_root: Path, ws_dir: Path, drill_doc: dict, env: dict) -> str:
    token = env.get("NOTION_TOKEN")
    if not token:
        return ""

    id_map_file = repo_root / "id_map.json"
    id_map = {}
    if id_map_file.exists():
        with open(id_map_file, "r", encoding="utf-8") as f:
            id_map = json.load(f)

    drills_db = id_map.get("DRILLS_DB", {})
    drills_db_id = drills_db.get("id") if isinstance(drills_db, dict) else drills_db
    if not drills_db_id:
        return ""

    drill_id = drill_doc["drillId"]
    unit_code = drill_doc.get("unitCode", "")
    chapter_code = drill_doc.get("chapterCode", "")
    topic_code = drill_doc.get("topicCode", "")
    unit_title = drill_doc.get("unitTitle", "Programming Practice")
    summary = drill_doc.get("sessionSummary", {})

    q = notion_request(
        "POST",
        f"databases/{drills_db_id}/query",
        token,
        {"filter": {"property": "Drill ID", "rich_text": {"equals": drill_id}}},
    )
    results = q.get("results", [])

    is_all_pass = summary.get("practiceStatus") == "Graded"
    title_text = f"{unit_title} — Verified Programming Drill ({summary.get('score')}/{summary.get('maxScore')} Solved)"
    rel_path = str(ws_dir.relative_to(repo_root)) if str(ws_dir).startswith(str(repo_root)) else str(ws_dir)
    now_iso = summary.get("attemptDate") or datetime.datetime.now(datetime.timezone.utc).isoformat()

    cleaned_tags = [{"name": cat.replace(",", " /")[:100].strip()} for cat in summary.get("mistakeCategories", [])]

    props = {
        "Drill": {"title": [{"type": "text", "text": {"content": title_text[:200]}}]},
        "Drill ID": {"rich_text": [{"type": "text", "text": {"content": drill_id}}]},
        "Scope Level": {"select": {"name": "Unit Drill" if "-U" in unit_code else "Chapter Mixed"}},
        "Format": {"select": {"name": "Code Test Suite"}},
        "Difficulty Mode": {"select": {"name": "Mixed Exam Mode"}},
        "Question Count": {"number": summary.get("maxScore", 5)},
        "Practice Status": {"select": {"name": summary.get("practiceStatus", "Needs Retry")}},
        "Score": {"number": summary.get("score", 0)},
        "Max Score": {"number": summary.get("maxScore", 5)},
        "Mistake Categories": {"multi_select": cleaned_tags},
        "Diverged Steps Summary": {"rich_text": [{"type": "text", "text": {"content": (summary.get("divergedStepsSummary") or "")[:1900]}}]},
        "Local File Path": {"rich_text": [{"type": "text", "text": {"content": rel_path}}]},
        "Attempt Date": {"date": {"start": now_iso}},
    }

    if unit_code and unit_code in id_map:
        u_entry = id_map[unit_code]
        props["Units"] = {"relation": [{"id": u_entry["id"] if isinstance(u_entry, dict) else u_entry}]}
    if chapter_code and chapter_code in id_map:
        c_entry = id_map[chapter_code]
        props["Chapters"] = {"relation": [{"id": c_entry["id"] if isinstance(c_entry, dict) else c_entry}]}
    if topic_code and topic_code in id_map:
        t_entry = id_map[topic_code]
        props["Topics"] = {"relation": [{"id": t_entry["id"] if isinstance(t_entry, dict) else t_entry}]}

    icon_color = "green" if is_all_pass else "blue"
    icon_payload = {"type": "icon", "icon": {"name": "code", "color": icon_color}}

    if results:
        page_id = results[0]["id"]
        notion_request("PATCH", f"pages/{page_id}", token, {"icon": icon_payload, "properties": props})
    else:
        created = notion_request(
            "POST",
            "pages",
            token,
            {"parent": {"database_id": drills_db_id}, "icon": icon_payload, "properties": props},
        )
        page_id = created["id"]

    return f"https://notion.so/{page_id.replace('-', '')}"


def main():
    ws_dir = Path.cwd().resolve()
    drill_id = ws_dir.name

    repo_root = find_repo_root(ws_dir)
    env = load_env(repo_root)

    # Locate drill JSON doc
    data_files = list(repo_root.glob(f"drills/data/**/{drill_id}.json"))
    drill_doc = None
    data_path = None
    if data_files:
        data_path = data_files[0]
        with open(data_path, "r", encoding="utf-8") as f:
            drill_doc = json.load(f)
    else:
        drill_doc = {
            "drillId": drill_id,
            "subject": "PRG",
            "unitCode": "PRG-T01-C03",
            "unitTitle": "Problem Solving & Utility Toolkit",
            "chapterCode": "PRG-T01-C03",
            "topicCode": "PRG-T01",
            "problems": [],
        }

    print(f"\n{BOLD}{CYAN}========================================================================={RESET}")
    print(f"{BOLD}  DRILL SUBMISSION ENGINE: {drill_id}{RESET}")
    print(f"{DIM}  {drill_doc.get('unitTitle', 'Programming Practice')} ({drill_doc.get('unitCode', 'PRG')}){RESET}")
    print(f"{BOLD}{CYAN}========================================================================={RESET}\n")

    print(f"{CYAN}▶ Executing Acceptance Test Suites...{RESET}")
    cases = run_tests_junit(ws_dir)

    if not cases:
        print(f"{RED}✗ No tests detected or test runner encountered an internal crash.{RESET}")
        sys.exit(1)

    # Group testcases by Question ID (e.g. Q01, Q02, ...)
    q_groups = {}
    for tc in cases:
        name = tc["name"]
        qid = "Q01"
        if "[" in name and "]" in name:
            bracket = name[name.find("[") + 1 : name.find("]")]
            qid = bracket.split("-")[0].strip()
        elif "_" in name:
            qid = name.split("_")[0].strip()

        if qid not in q_groups:
            q_groups[qid] = []
        q_groups[qid].append(tc)

    evaluated_questions = []
    total_passed = 0
    failing_reasons = []

    for qid in sorted(q_groups.keys()):
        tcs = q_groups[qid]
        vis_tcs = [tc for tc in tcs if not tc.get("is_hidden")]
        hid_tcs = [tc for tc in tcs if tc.get("is_hidden")]

        vis_pass = sum(1 for tc in vis_tcs if tc["passed"])
        hid_pass = sum(1 for tc in hid_tcs if tc["passed"])
        all_pass = all(tc["passed"] for tc in tcs)

        if all_pass:
            total_passed += 1
        else:
            first_fail = next(tc for tc in tcs if not tc["passed"])
            prefix = "[HIDDEN TRAP] " if first_fail.get("is_hidden") else ""
            failing_reasons.append(f"[{qid}] {prefix}{first_fail['name']}: {first_fail['failure_msg'][:80]}")

        evaluated_questions.append({
            "qid": qid,
            "passed": all_pass,
            "vis_pass": vis_pass,
            "vis_total": len(vis_tcs),
            "hid_pass": hid_pass,
            "hid_total": len(hid_tcs),
            "hidden_breached": (vis_pass == len(vis_tcs) and hid_pass < len(hid_tcs)) if hid_tcs else False,
        })

    max_score = len(evaluated_questions)
    all_green = (total_passed == max_score and max_score > 0)
    practice_status = "Graded" if all_green else "Needs Retry"

    print(f"\n{BOLD}Question Acceptance Breakdown:{RESET}")
    for eq in evaluated_questions:
        mark = f"{GREEN}✔ PASS{RESET}" if eq["passed"] else f"{RED}✗ FAIL{RESET}"
        detail = f"{eq['vis_pass']}/{eq['vis_total']} visible"
        if eq['hid_total'] > 0:
            detail += f" + {eq['hid_pass']}/{eq['hid_total']} hidden traps"
        print(f"  [{eq['qid']}] Exercise Acceptance Suite: {mark}  ({detail})")
        if eq["hidden_breached"]:
            print(f"      {YELLOW}⚠ Notice: Visible scenarios passed, but Hidden Trap tests failed (Boundary/Hardcode trap).{RESET}")

    pct = round((total_passed / max_score * 100), 1) if max_score > 0 else 0.0
    print(f"\n{BOLD}-------------------------------------------------------------------------{RESET}")
    score_col = GREEN if all_green else YELLOW if total_passed > 0 else RED
    print(f"  {BOLD}SCORE:{RESET}  {score_col}{total_passed} / {max_score} Questions Solved ({pct}%){RESET}")
    status_label = f"{GREEN}GRADED (PASSED){RESET}" if all_green else f"{RED}NEEDS RETRY{RESET}"
    print(f"  {BOLD}STATUS:{RESET} {status_label}")
    print(f"{BOLD}-------------------------------------------------------------------------{RESET}\n")

    # Update drill doc and sync to Notion
    drill_doc["sessionSummary"] = {
        "score": total_passed,
        "maxScore": max_score,
        "practiceStatus": practice_status,
        "mistakeCategories": ["Assertion Failure / Unhandled Edge Case"] if not all_green else [],
        "divergedStepsSummary": " | ".join(failing_reasons) if failing_reasons else "All question test suites passed 100% verified.",
        "attemptDate": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    if data_path:
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(drill_doc, f, ensure_ascii=False, indent=2)

    print(f"{CYAN}▶ Synchronizing Telemetry with Notion Database 'Learning Practice & Drills'...{RESET}")
    try:
        notion_url = sync_drill_telemetry_to_notion(repo_root, ws_dir, drill_doc, env)
        if notion_url:
            print(f"{GREEN}✔ Successfully synced to Notion!{RESET}")
            print(f"  {BOLD}Notion Page:{RESET} {CYAN}{notion_url}{RESET}\n")
        else:
            print(f"{YELLOW}⚠ Notion sync notice: DRILLS_DB ID or NOTION_TOKEN missing.{RESET}\n")
    except Exception as e:
        print(f"{RED}✗ Notion sync encountered an error: {e}{RESET}\n")

    if not all_green:
        sys.exit(1)
    else:
        print(f"{GREEN}{BOLD}🎉 ALL EXERCISES COMPLETED AND VERIFIED!{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
