# -*- coding: utf-8 -*-
"""
Universal Terminal Lab Submission & Telemetry Engine (Phase 3)
Executes test suites (node:test, vitest, pytest, etc.) via JUnit XML reporter,
evaluates milestone scores, formats failure diagnostics, and syncs directly
to the Notion database 'Learning Practice & Drills' (Format: "Code Test Suite").
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
    else ssl._create_unverified_context()
)

def find_repo_root(start_dir: str = ".") -> Path:
    """Walk up from start_dir to locate workspace root containing id_map.json."""
    curr = Path(start_dir).resolve()
    for _ in range(8):
        if (curr / "id_map.json").exists() and (curr / ".env").exists():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    return Path(start_dir).resolve()

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
                wait = 1.5 * (2 ** attempt)
                time.sleep(wait)
                continue
            body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {e.code} on {method} {endpoint}: {body}") from e

def rt(text: str, bold: bool = False, code: bool = False):
    return {
        "type": "text",
        "text": {"content": text},
        "annotations": {"bold": bold, "code": code},
    }

def callout_block(content: str, color: str = "blue_background", icon: str = "code"):
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "icon": {"type": "icon", "icon": {"name": icon, "color": "blue" if "blue" in color else "green" if "green" in color else "orange"}},
            "color": color,
            "rich_text": [rt(content[:1990])],
        },
    }

def heading2(text: str):
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [rt(text)]},
    }

def divider_block():
    return {"object": "block", "type": "divider", "divider": {}}

def toggle_block(title: str, children: list):
    return {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [rt(title[:1990])],
            "children": children[:100],
        },
    }

def bullet_block(text: str):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [rt(text[:1990])]},
    }

def code_block(code: str, lang: str = "plain text"):
    return {
        "object": "block",
        "type": "code",
        "code": {
            "language": lang,
            "rich_text": [rt(code[:1990])],
        },
    }

def run_tests_and_parse(lab_dir: Path, config: dict):
    """Executes the test command and parses JUnit XML test results."""
    test_cmd = config.get("testCommand", "node --experimental-strip-types --test --test-reporter=junit tests/*.test.ts")
    
    print(f"{CYAN}▶ Executing Test Suite:{RESET} {test_cmd}")
    proc = subprocess.run(
        test_cmd,
        shell=True,
        cwd=lab_dir,
        capture_output=True,
        text=True,
    )
    raw_output = proc.stdout + "\n" + proc.stderr

    # Locate XML content
    xml_start = raw_output.find("<?xml")
    if xml_start == -1:
        xml_start = raw_output.find("<testsuites")
    
    if xml_start == -1:
        # Fallback if no XML found
        return {
            "success": False,
            "error": "No JUnit XML output detected from test command.\n" + raw_output[:1000],
            "testcases": [],
            "raw_output": raw_output,
        }

    xml_text = raw_output[xml_start:].strip()
    # If trailing non-xml text exists, trim to closing </testsuites>
    end_tag = "</testsuites>"
    end_idx = xml_text.rfind(end_tag)
    if end_idx != -1:
        xml_text = xml_text[:end_idx + len(end_tag)]

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return {
            "success": False,
            "error": f"Failed to parse JUnit XML: {e}\nRaw Output snippet:\n{xml_text[:500]}",
            "testcases": [],
            "raw_output": raw_output,
        }

    testcases = []
    for tc in root.findall(".//testcase"):
        tc_name = tc.attrib.get("name", "Unnamed Test")
        tc_file = tc.attrib.get("file", "")
        tc_time = float(tc.attrib.get("time", 0.0))
        failure_elem = tc.find("failure")
        error_elem = tc.find("error")
        
        is_fail = failure_elem is not None or error_elem is not None
        fail_msg = ""
        fail_trace = ""
        if failure_elem is not None:
            fail_msg = failure_elem.attrib.get("message", failure_elem.text or "Assertion failed")
            fail_trace = failure_elem.text or ""
        elif error_elem is not None:
            fail_msg = error_elem.attrib.get("message", error_elem.text or "Runtime error")
            fail_trace = error_elem.text or ""

        testcases.append({
            "name": tc_name,
            "file": tc_file,
            "time": tc_time,
            "passed": not is_fail,
            "failure_msg": fail_msg.strip(),
            "failure_trace": fail_trace.strip(),
        })

    return {
        "success": True,
        "testcases": testcases,
        "raw_output": raw_output,
    }

def evaluate_milestones(milestones: list, testcases: list):
    """Maps test cases to configured milestones and computes scores."""
    evaluated = []
    total_score = 0
    max_score = 0
    failing_categories = []
    diverged_summaries = []

    for ms in milestones:
        m_id = ms["id"]
        m_title = ms.get("title", f"Milestone {m_id}")
        m_pts = int(ms.get("points", 25))
        m_pattern = ms.get("testPattern", m_id.lower())
        m_cat = ms.get("mistakeCategory", "General Logic Flaw")
        max_score += m_pts

        # Filter test cases matching this milestone
        matched = [
            tc for tc in testcases
            if m_pattern.lower() in tc["file"].lower() or m_pattern.lower() in tc["name"].lower()
        ]

        if not matched:
            # If no pattern matched, try by index/loose match
            matched = [tc for tc in testcases if m_id.lower() in tc["name"].lower()]

        if not matched:
            # Fallback if tests didn't tag milestone explicitly
            matched_passed = False
            tc_pass_count = 0
            tc_total = 0
            failures = [{"name": "No tests detected", "failure_msg": "No test cases matched milestone pattern"}]
        else:
            tc_total = len(matched)
            tc_pass_count = sum(1 for tc in matched if tc["passed"])
            matched_passed = (tc_pass_count == tc_total and tc_total > 0)
            failures = [tc for tc in matched if not tc["passed"]]

        pts_earned = m_pts if matched_passed else 0
        total_score += pts_earned

        if not matched_passed:
            # STRICT RULE: Comma ban in multi_select options
            clean_cat = m_cat.replace(",", " /").strip()
            if clean_cat not in failing_categories:
                failing_categories.append(clean_cat)
            
            first_fail = failures[0] if failures else {"failure_msg": "Unknown failure"}
            short_msg = first_fail.get("failure_msg", "").split("\n")[0][:120]
            diverged_summaries.append(f"[{m_id}] {short_msg}")

        evaluated.append({
            "id": m_id,
            "title": m_title,
            "points": m_pts,
            "earned": pts_earned,
            "passed": matched_passed,
            "test_count": len(matched),
            "pass_count": sum(1 for tc in matched if tc["passed"]),
            "testcases": matched,
            "failures": failures,
            "category": m_cat,
        })

    accuracy_pct = round((total_score / max_score * 100), 1) if max_score > 0 else 0.0
    divergence_str = " | ".join(diverged_summaries) if diverged_summaries else "All milestones passed 100% verified."

    return {
        "milestones": evaluated,
        "total_score": total_score,
        "max_score": max_score,
        "accuracy_pct": accuracy_pct,
        "failing_categories": failing_categories,
        "divergence_summary": divergence_str,
        "all_passed": (total_score == max_score and max_score > 0),
    }

def sync_to_notion(repo_root: Path, lab_dir: Path, config: dict, eval_result: dict, env: dict):
    """Syncs lab grading results into Notion 'Learning Practice & Drills' database."""
    token = env.get("NOTION_TOKEN")
    if not token:
        print(f"{YELLOW}⚠ Warning: NOTION_TOKEN not set in .env. Skipping Notion synchronization.{RESET}")
        return None

    id_map_file = repo_root / "id_map.json"
    id_map = {}
    if id_map_file.exists():
        with open(id_map_file, "r", encoding="utf-8") as f:
            id_map = json.load(f)

    drills_db = id_map.get("DRILLS_DB", {})
    drills_db_id = drills_db.get("id") if isinstance(drills_db, dict) else drills_db
    if not drills_db_id:
        print(f"{YELLOW}⚠ Warning: DRILLS_DB ID not found in id_map.json. Skipping Notion sync.{RESET}")
        return None

    lab_id = config["labId"]
    lab_title = config.get("title", lab_id)
    unit_code = config.get("unitCode", "")
    chapter_code = config.get("chapterCode", "")
    topic_code = config.get("topicCode", "")
    diff_mode = config.get("difficulty", "Level 4 - Applied Synthesis")
    scope_level = config.get("scopeLevel", "Unit Drill")

    q = notion_request(
        "POST",
        f"databases/{drills_db_id}/query",
        token,
        {"filter": {"property": "Drill ID", "rich_text": {"equals": lab_id}}},
    )
    results = q.get("results", [])

    is_all_pass = eval_result["all_passed"]
    practice_status = "Graded" if is_all_pass else "Needs Retry"
    title_text = f"{lab_title} — Terminal Code Lab ({eval_result['total_score']}/{eval_result['max_score']} pts)"

    # Relative path from repo root
    try:
        rel_path = str(lab_dir.relative_to(repo_root))
    except ValueError:
        rel_path = str(lab_dir)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Clean mistake category tags (STRICT BAN ON COMMAS)
    cleaned_tags = [{"name": cat.replace(",", " /")[:100].strip()} for cat in eval_result["failing_categories"]]

    props = {
        "Drill": {"title": [{"type": "text", "text": {"content": title_text[:200]}}]},
        "Drill ID": {"rich_text": [{"type": "text", "text": {"content": lab_id}}]},
        "Scope Level": {"select": {"name": scope_level}},
        "Format": {"select": {"name": "Code Test Suite"}},
        "Difficulty Mode": {"select": {"name": diff_mode}},
        "Question Count": {"number": len(eval_result["milestones"])},
        "Practice Status": {"select": {"name": practice_status}},
        "Score": {"number": eval_result["total_score"]},
        "Max Score": {"number": eval_result["max_score"]},
        "Mistake Categories": {"multi_select": cleaned_tags},
        "Diverged Steps Summary": {"rich_text": [{"type": "text", "text": {"content": eval_result["divergence_summary"][:1900]}}]},
        "Local File Path": {"rich_text": [{"type": "text", "text": {"content": rel_path}}]},
        "Attempt Date": {"date": {"start": now_iso}},
    }

    if unit_code and unit_code in id_map:
        u_entry = id_map[unit_code]
        u_id = u_entry["id"] if isinstance(u_entry, dict) else u_entry
        props["Units"] = {"relation": [{"id": u_id}]}
    if chapter_code and chapter_code in id_map:
        c_entry = id_map[chapter_code]
        c_id = c_entry["id"] if isinstance(c_entry, dict) else c_entry
        props["Chapters"] = {"relation": [{"id": c_id}]}
    if topic_code and topic_code in id_map:
        t_entry = id_map[topic_code]
        t_id = t_entry["id"] if isinstance(t_entry, dict) else t_entry
        props["Topics"] = {"relation": [{"id": t_id}]}

    icon_color = "green" if is_all_pass else "orange"
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

    id_map[lab_id] = {"id": page_id, "title": title_text}
    with open(id_map_file, "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)

    # Build Body Blocks
    callout_color = "green_background" if is_all_pass else "orange_background"
    summary_msg = (
        f"Terminal Lab Suite ({lab_id}): Score {eval_result['total_score']}/{eval_result['max_score']} pts "
        f"({eval_result['accuracy_pct']}%) — Status: {practice_status}.\n"
        f"Scope: {unit_code} | Difficulty: {diff_mode} | Submitted: {now_iso[:19]} UTC\n"
        f"Path: {rel_path}"
    )

    blocks = [
        callout_block(summary_msg, color=callout_color, icon="code"),
        divider_block(),
        heading2("Milestone Execution Telemetry"),
    ]

    for ms in eval_result["milestones"]:
        status_icon = "✔" if ms["passed"] else "✗"
        m_title = f"{status_icon} [{ms['id']}] {ms['title']} — {ms['earned']}/{ms['points']} pts ({ms['pass_count']}/{ms['test_count']} tests passed)"
        
        children = []
        for tc in ms["testcases"]:
            tc_icon = "✔" if tc["passed"] else "✗"
            children.append(bullet_block(f"{tc_icon} {tc['name']} ({round(tc['time'] * 1000, 1)}ms)"))
            if not tc["passed"] and tc.get("failure_msg"):
                short_trace = tc["failure_msg"]
                if tc.get("failure_trace") and len(tc["failure_trace"]) > len(short_trace):
                    short_trace = tc["failure_trace"]
                children.append(code_block(short_trace[:1800], lang="plain text"))

        blocks.append(toggle_block(m_title, children))

    # Replace blocks
    # Fetch existing blocks and delete
    existing = notion_request("GET", f"blocks/{page_id}/children?page_size=100", token).get("results", [])
    for eb in existing:
        notion_request("DELETE", f"blocks/{eb['id']}", token)

    # Append fresh blocks
    notion_request("PATCH", f"blocks/{page_id}/children", token, {"children": blocks})

    page_url = f"https://notion.so/{page_id.replace('-', '')}"
    return page_url

def main():
    lab_dir = Path.cwd()
    if len(sys.argv) > 1 and sys.argv[1].startswith("--lab-dir="):
        lab_dir = Path(sys.argv[1].split("=", 1)[1]).resolve()
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        lab_dir = Path(sys.argv[1]).resolve()

    config_file = lab_dir / "lab.config.json"
    if not config_file.exists():
        print(f"{RED}Error: Cannot find lab.config.json in {lab_dir}{RESET}")
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    repo_root = find_repo_root(lab_dir)
    env = load_env(repo_root)

    print(f"\n{BOLD}{CYAN}========================================================================={RESET}")
    print(f"{BOLD}  PHASE 3 TERMINAL LAB SUBMISSION ENGINE: {config.get('labId')}{RESET}")
    print(f"{DIM}  {config.get('title')} ({config.get('unitCode', 'Unit')}){RESET}")
    print(f"{BOLD}{CYAN}========================================================================={RESET}\n")

    # Step 1: Run tests
    test_run = run_tests_and_parse(lab_dir, config)
    if not test_run["success"]:
        print(f"{RED}✗ Test Execution Failed:{RESET}\n{test_run.get('error')}")
        sys.exit(1)

    # Step 2: Evaluate Milestones
    eval_res = evaluate_milestones(config.get("milestones", []), test_run["testcases"])

    # Step 3: Print Terminal Summary
    print(f"\n{BOLD}Milestone Breakdown:{RESET}")
    for ms in eval_res["milestones"]:
        mark = f"{GREEN}✔ PASS{RESET}" if ms["passed"] else f"{RED}✗ FAIL{RESET}"
        pts_str = f"{ms['earned']}/{ms['points']} pts"
        test_ratio = f"{ms['pass_count']}/{ms['test_count']} tests"
        print(f"  [{ms['id']}] {ms['title']:<45} {mark}  ({pts_str:>10})  [{test_ratio}]")
        if not ms["passed"]:
            for f in ms["failures"][:2]:
                first_line = f.get("failure_msg", "").split("\n")[0]
                print(f"      {RED}→ {f['name']}: {first_line}{RESET}")

    print(f"\n{BOLD}-------------------------------------------------------------------------{RESET}")
    score_color = GREEN if eval_res["all_passed"] else YELLOW if eval_res["total_score"] > 0 else RED
    print(f"  {BOLD}TOTAL SCORE:{RESET} {score_color}{eval_res['total_score']} / {eval_res['max_score']} pts ({eval_res['accuracy_pct']}%){RESET}")
    status_label = f"{GREEN}GRADED (PASSED){RESET}" if eval_res["all_passed"] else f"{RED}NEEDS RETRY{RESET}"
    print(f"  {BOLD}STATUS:{RESET}      {status_label}")
    if eval_res["failing_categories"]:
        print(f"  {BOLD}TAGS:{RESET}        {YELLOW}{', '.join(eval_res['failing_categories'])}{RESET}")
    print(f"{BOLD}-------------------------------------------------------------------------{RESET}\n")

    # Step 4: Sync to Notion
    print(f"{CYAN}▶ Synchronizing Telemetry with Notion Database 'Learning Practice & Drills'...{RESET}")
    try:
        notion_url = sync_to_notion(repo_root, lab_dir, config, eval_res, env)
        if notion_url:
            print(f"{GREEN}✔ Successfully synced to Notion!{RESET}")
            print(f"  {BOLD}Notion Page:{RESET} {CYAN}{notion_url}{RESET}\n")
    except Exception as e:
        print(f"{RED}✗ Notion sync encountered an error: {e}{RESET}\n")

    if not eval_res["all_passed"]:
        sys.exit(1)
    else:
        print(f"{GREEN}{BOLD}🎉 ALL MILESTONES COMPLETED AND VERIFIED!{RESET}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
