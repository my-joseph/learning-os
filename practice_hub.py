#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Math Practice Player Server & Notion Auto-Sync Bridge (http://localhost:8765)
- Serves the single-instance Math Practice Player at http://localhost:8765/
- GET  /api/drills          -> Lists all .json drill sets under drills/data/<UNIT>/<DRILL_ID>.json
- GET  /api/drill?id=...    -> Returns the full .json drill document
- POST /api/generate-drill  -> Runs Pre-Generation Config -> verified .json via math_engine.generate
- POST /api/check-answer    -> Runs flexible SymPy answer checker via math_engine.answer_check
- POST /api/save-state      -> Persists in-progress user state into the drill's .json file
- POST /api/sync-notion     -> Saves .json AND syncs score, mistake tags, diverged steps, and verified
                               problem toggles to Notion ('Learning Practice & Drills' + Unit Mistake Log)
"""
import glob
import json
import os
import re
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

from apply_rules_and_test_pages import (
    bullet,
    callout_block,
    code_block,
    divider_block,
    eq_block,
    h2,
    load_env,
    notion_request,
    p_block,
    replace_page_blocks,
    toggle_block,
)
try:
    from math_engine.answer_check import check_answer
except ImportError:
    check_answer = None

try:
    from math_engine.generate import generate_drill_set
except ImportError:
    generate_drill_set = None

PORT = 8765
DATA_ROOT = "drills/data"


def find_drill_file(drill_id: str):
    pattern = os.path.join(DATA_ROOT, "*", f"{drill_id}.json")
    matches = glob.glob(pattern)
    return matches[0] if matches else None


def list_all_drills():
    files = glob.glob(os.path.join(DATA_ROOT, "*", "DRL-*.json"))
    items = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                doc = json.load(f)
            items.append({
                "drillId": doc.get("drillId"),
                "unitCode": doc.get("unitCode"),
                "unitTitle": doc.get("unitTitle"),
                "createdAt": doc.get("createdAt", ""),
                "questionCount": doc.get("config", {}).get("questionCount", len(doc.get("problems", []))),
                "difficultyMode": doc.get("config", {}).get("difficultyMode", "Mixed Exam Mode"),
                "localFilePath": path,
            })
        except Exception:
            continue
    items.sort(key=lambda x: (x["createdAt"], x["drillId"]), reverse=True)
    return items


def validate_and_sanitize_drill_doc(drill_doc: dict) -> None:
    """
    Strict Invariant: Zero-Leak Placeholder & Hint Policy.
    Detects and scrubs any answer spoilers or accidental e.g. leaks in inputHint.
    """
    for p in drill_doc.get("problems", []):
        accepted_tokens = set()
        for a in p.get("answerSpec", {}).get("accepted", []):
            s = str(a).strip().lower()
            if len(s) >= 2:
                accepted_tokens.add(s)
        plain = str(p.get("answerPlain", "")).strip().lower()
        if len(plain) >= 2:
            accepted_tokens.add(plain)
        disp = str(p.get("answerDisplay", "")).strip().lower()
        clean_disp = re.sub(r"\\[a-zA-Z]+|\$|\{|\}|\^", "", disp).strip()
        if len(clean_disp) >= 2:
            accepted_tokens.add(clean_disp)

        input_hint = p.get("inputHint")
        if input_hint:
            lower_hint = input_hint.lower()
            leaked = [tok for tok in accepted_tokens if tok in lower_hint]
            if leaked:
                cleaned = re.sub(r"\s*\([^)]*e\.g\.[^)]*\)", "", input_hint, flags=re.IGNORECASE).strip()
                if not any(tok in cleaned.lower() for tok in accepted_tokens) and len(cleaned) > 5:
                    p["inputHint"] = cleaned
                else:
                    if p.get("codeType") == "predict-output" or drill_doc.get("subject") == "PRG":
                        p["inputHint"] = "Type predicted output..."
                    else:
                        p["inputHint"] = "Type final answer..."


def save_drill_doc(drill_doc: dict):
    drill_id = drill_doc.get("drillId")
    if not drill_id:
        raise ValueError("Missing drillId")
    validate_and_sanitize_drill_doc(drill_doc)
    unit_code = drill_doc.get("unitCode", "MTH-T02-C01-U01")
    unit_dir = os.path.join(DATA_ROOT, unit_code)
    os.makedirs(unit_dir, exist_ok=True)
    path = os.path.join(unit_dir, f"{drill_id}.json")
    drill_doc["localFilePath"] = path
    with open(path, "w", encoding="utf-8") as f:
        json.dump(drill_doc, f, ensure_ascii=False, indent=2)
    return path


def sync_drill_to_notion(drill_doc: dict) -> dict:
    path = save_drill_doc(drill_doc)
    env = load_env()
    token = env.get("NOTION_TOKEN")
    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    drills_entry = id_map.get("DRILLS_DB")
    drills_db_id = drills_entry["id"] if isinstance(drills_entry, dict) else drills_entry
    if not drills_db_id:
        raise RuntimeError("DRILLS_DB not found in id_map.json")

    drill_id = drill_doc["drillId"]
    unit_code = drill_doc["unitCode"]
    chapter_code = drill_doc["chapterCode"]
    topic_code = drill_doc["topicCode"]
    unit_title = drill_doc.get("unitTitle", unit_code)
    cfg = drill_doc.get("config", {})
    summary = drill_doc.get("sessionSummary", {})
    problems = drill_doc.get("problems", [])

    q_count = int(cfg.get("questionCount", len(problems)))
    diff_mode = cfg.get("difficultyMode", "Mixed Exam Mode")
    score = float(summary.get("score", 0))
    max_score = float(summary.get("maxScore", q_count))
    status = summary.get("practiceStatus", "Ready")
    mistake_cats = summary.get("mistakeCategories", [])
    diverged_summary = summary.get("divergedStepsSummary", "No diverged steps logged.")
    attempt_date = summary.get("attemptDate")

    q = notion_request(
        "POST",
        f"databases/{drills_db_id}/query",
        token,
        {"filter": {"property": "Drill ID", "rich_text": {"equals": drill_id}}},
    )
    results = q.get("results", [])

    is_prg = drill_doc.get("subject") == "PRG" or unit_code.startswith("PRG-")
    drill_kind = "Programming" if is_prg else "Math"
    title = f"{unit_title} — Verified {drill_kind} Drill ({q_count} Qs · {diff_mode})"
    is_unit = "-U" in unit_code
    scope_name = "Unit Drill" if is_unit else "Chapter Mixed"

    props = {
        "Drill": {"title": [{"type": "text", "text": {"content": title}}]},
        "Drill ID": {"rich_text": [{"type": "text", "text": {"content": drill_id}}]},
        "Scope Level": {"select": {"name": scope_name}},
        "Format": {"select": {"name": "Interactive HTML"}},
        "Difficulty Mode": {"select": {"name": diff_mode}},
        "Question Count": {"number": q_count},
        "Practice Status": {"select": {"name": status}},
        "Score": {"number": score},
        "Max Score": {"number": max_score},
        "Mistake Categories": {"multi_select": [{"name": tag.replace(",", " /")[:100].strip()} for tag in mistake_cats]},
        "Diverged Steps Summary": {"rich_text": [{"type": "text", "text": {"content": diverged_summary[:1900]}}]},
        "Local File Path": {"rich_text": [{"type": "text", "text": {"content": path}}]},
    }
    if is_unit and unit_code in id_map:
        props["Units"] = {"relation": [{"id": id_map[unit_code]["id"]}]}
    if chapter_code in id_map:
        props["Chapters"] = {"relation": [{"id": id_map[chapter_code]["id"]}]}
    if topic_code in id_map:
        props["Topics"] = {"relation": [{"id": id_map[topic_code]["id"]}]}
    if attempt_date:
        props["Attempt Date"] = {"date": {"start": attempt_date}}

    icon_color = "blue" if is_prg else "purple"
    icon_payload = {"type": "icon", "icon": {"name": "code" if is_prg else "target", "color": icon_color}}
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

    id_map[drill_id] = {"id": page_id, "title": title}
    with open("id_map.json", "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)

    # Populate Notion Drill Page Body with clean 100% English formatting
    player_url = f"http://localhost:3000/?drill={drill_id}"
    callout_color = "blue_background" if is_prg else "purple_background"

    # Extract Focus & Trap badges
    mistake_tags = drill_doc.get("mistakeTags", [])
    trap_bullets = [
        bullet(f"**Trap:** `{tag.get('name', tag.get('id'))}` — {tag.get('label', '')}", id_map)
        for tag in mistake_tags[:4]
    ] if mistake_tags else [bullet("Enforce fundamental invariants and verify step-by-step logic.", id_map)]

    status_badge = (
        f"**Session Score:** `{score}/{max_score}` ({round((score/max_score)*100, 1)}%) — Status: **{status}**"
        if attempt_date or status != "Ready"
        else "**Session Status:** `Ready for Practice` — Awaiting learner attempt in Practice Studio / Terminal."
    )

    blocks = [
        callout_block(
            f"**Interactive {drill_kind} Drill (`{drill_id}`):** Data file `{path}` | Open in Practice Studio at `{player_url}`.\n"
            f"Scope: [[{unit_code}]] | Chapter: [[{chapter_code}]] | Topic: [[{topic_code}]] | Config: `{q_count} Questions ({diff_mode})`\n"
            f"{status_badge}",
            id_map,
            color=callout_color,
        ),
        divider_block(),
        h2("1. Drill Blueprint & Learning Focus", id_map),
        p_block(
            f"This drill tests foundational mastery for [[{unit_code}]]. "
            f"Solve each problem independently before consulting the step-by-step verification toggles below.",
            id_map,
        ),
        bullet("**Core Objectives:**", id_map, children=[
            bullet(f"Verify and solidify understanding of `{unit_title}`.", id_map),
            bullet(f"Solve all {q_count} questions adhering to exact formula and invariant boundaries.", id_map),
        ]),
        bullet("**Common Traps & Invariant Guardrails:**", id_map, children=trap_bullets),
        divider_block(),
        h2("2. Question Inventory & Step-by-Step Solutions", id_map),
    ]

    for p in problems:
        ref_str = " ".join(f"([[{r}]])" for r in p.get("references", []) if r in id_map)
        header_line = f"**{p['id']} ({p['levelLabel']} — {p['category']}):** {p['prompt']}" + (f" {ref_str}" if ref_str else "")
        children = []

        if p.get("codeSnippet"):
            children.append(code_block(p["codeSnippet"], lang=p.get("language", "javascript")))
        elif p.get("display"):
            children.append(eq_block(p["display"]))

        if p.get("plainText"):
            children.append(p_block(f"**Plain-Text / CAS Input:** `{p['plainText']}`", id_map))
        if p.get("checkpointHint"):
            children.append(p_block(f"**Intermediate Checkpoint:** {p['checkpointHint']}", id_map))

        if not is_prg and p.get("steps"):
            aligned_lines = []
            for st in p.get("steps", []):
                latex_line = st["latex"].replace("=", "&=", 1) if "=" in st["latex"] else "& " + st["latex"]
                aligned_lines.append(latex_line)
            aligned_tex = "\\begin{aligned}\n" + " \\\\\n".join(aligned_lines) + "\n\\end{aligned}"
            children.append(eq_block(aligned_tex))

        for s_i, st in enumerate(p.get("steps", []), 1):
            children.append(bullet(f"**Step {s_i}:** {st['explain']}", id_map))

        final_ans = p.get("answerDisplay", "")
        if is_prg:
            children.append(p_block(f"**Verified Final Answer:** `{final_ans}`", id_map))
        else:
            children.append(p_block(f"**Verified Final Answer:** ${final_ans}$", id_map))

        blocks.append(toggle_block(header_line, children, id_map))

    replace_page_blocks(page_id, blocks, drill_id, token)

    # Also append attempt log to parent Unit or Chapter page if an attempt was made
    parent_entry = id_map.get(unit_code) or id_map.get(chapter_code)
    parent_page_id = parent_entry["id"] if isinstance(parent_entry, dict) else parent_entry
    if attempt_date and parent_page_id:
        try:
            # Check if parent page schema has 'Last Reviewed' property (Units DB has it, Chapter DB does not)
            target_page = notion_request("GET", f"pages/{parent_page_id}", token)
            if "Last Reviewed" in target_page.get("properties", {}):
                notion_request(
                    "PATCH",
                    f"pages/{parent_page_id}",
                    token,
                    {"properties": {"Last Reviewed": {"date": {"start": attempt_date}}}},
                )
        except Exception:
            # Non-fatal if page schema doesn't have Last Reviewed
            pass

        pct = summary.get("accuracyPct", 0)
        mistakes_str = ", ".join(mistake_cats) if mistake_cats else "None"
        log_line = (
            f"**[{attempt_date}] [[{drill_id}]] ({diff_mode}, {q_count} Qs):** "
            f"Score **{score}/{max_score} ({pct}%)** — Status: **{status}** | "
            f"Mistake Tags: `{mistakes_str}` | Paper Divergence: {diverged_summary}"
        )
        try:
            notion_request(
                "PATCH",
                f"blocks/{parent_page_id}/children",
                token,
                {"children": [bullet(log_line, id_map)]},
            )
        except Exception:
            pass

    return {"ok": True, "drillPageId": page_id, "parentPageId": parent_page_id}


class MathPlayerHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, code: int, obj: dict):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.path = "/web/index.html"
            return super().do_GET()
        if parsed.path == "/api/drills":
            return self._send_json(200, {"drills": list_all_drills()})
        if parsed.path == "/api/drill":
            qs = urllib.parse.parse_qs(parsed.query)
            drill_id = (qs.get("id") or [""])[0]
            fpath = find_drill_file(drill_id)
            if not fpath:
                return self._send_json(404, {"error": f"Drill {drill_id} not found"})
            with open(fpath, "r", encoding="utf-8") as f:
                return self._send_json(200, json.load(f))
        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            payload = json.loads(raw)
        except Exception:
            return self._send_json(400, {"ok": False, "error": "Invalid JSON"})

        try:
            if self.path == "/api/check-answer":
                res = check_answer(payload.get("answerSpec", {}), payload.get("input", ""))
                return self._send_json(200, res)
            if self.path == "/api/generate-drill":
                doc = generate_drill_set(
                    unit_code=payload.get("unitCode", "MTH-T02-C01-U01"),
                    count=int(payload.get("count", 5)),
                    difficulty=payload.get("difficulty", "ALL"),
                )
                return self._send_json(200, {"ok": True, "drillId": doc["drillId"], "localFilePath": doc["localFilePath"]})
            if self.path == "/api/save-state":
                path = save_drill_doc(payload)
                return self._send_json(200, {"ok": True, "localFilePath": path})
            if self.path == "/api/sync-notion":
                res = sync_drill_to_notion(payload)
                return self._send_json(200, res)
            return self._send_json(404, {"ok": False, "error": "Unknown endpoint"})
        except Exception as e:
            return self._send_json(500, {"ok": False, "error": str(e)})


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(("127.0.0.1", PORT), MathPlayerHandler)
    print(f"Math Practice Player running at http://localhost:{PORT}")
    server.serve_forever()
