# -*- coding: utf-8 -*-
"""
Pre-Generation Config -> Verified Programming Drill JSON Generator.

Generates ONLY the exact number of questions requested in the Pre-Generation Config
(e.g., 5, 10, 15, or 20), verifies every problem via real Node.js subprocess execution,
attaches resolved Notion deep links for cross-subject references, and writes the
clean JSON file to drills/data/<UNIT_CODE>/<DRILL_ID>.json.
"""

import argparse
import datetime
import glob
import json
import os
import random

from code_engine.fmt import DIFFICULTY_MODES, LEVEL_LABELS
from code_engine.templates import load_unit
from code_engine.verify import verify_problem, verify_tags


def load_id_map(path="id_map.json"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def notion_url_for(code, id_map):
    entry = id_map.get(code)
    if not entry:
        return None
    raw_id = (entry["id"] if isinstance(entry, dict) else str(entry)).replace("-", "")
    return f"https://www.notion.so/{raw_id}"


def next_drill_id(unit_code, data_root="drills/data"):
    unit_dir = os.path.join(data_root, unit_code)
    os.makedirs(unit_dir, exist_ok=True)
    existing = sorted(glob.glob(os.path.join(unit_dir, f"DRL-{unit_code}-*.json")))
    max_num = 0
    for p in existing:
        base = os.path.splitext(os.path.basename(p))[0]
        parts = base.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            max_num = max(max_num, int(parts[1]))
    return f"DRL-{unit_code}-{max_num + 1:02d}"


def _pick_template_schedule(templates, count, difficulty, focus_tags, rng):
    if focus_tags:
        tags_set = set(focus_tags) if isinstance(focus_tags, (list, tuple, set)) else {str(focus_tags)}
        matched = [t for t in templates if t.get("key") in tags_set or t.get("trapTag") in tags_set]
        if matched:
            schedule = []
            while len(schedule) < count:
                batch = list(matched)
                rng.shuffle(batch)
                schedule.extend(batch)
            return schedule[:count]

    if difficulty in ("1", "2", "3", "4"):
        lv = int(difficulty)
        pool = [t for t in templates if t["level"] == lv]
        if not pool:
            pool = list(templates)
        schedule = []
        while len(schedule) < count:
            batch = list(pool)
            rng.shuffle(batch)
            schedule.extend(batch)
        return schedule[:count]

    # Mixed Exam Mode: proportional allocation across Levels 1, 2, 3, 4 (25%, 40%, 20%, 15%)
    by_level = {lv: [t for t in templates if t["level"] == lv] for lv in (1, 2, 3, 4)}
    n1 = max(1, round(count * 0.25))
    n2 = max(1, round(count * 0.40))
    n3 = max(1, round(count * 0.20))
    n4 = max(0, count - (n1 + n2 + n3))
    counts = {1: n1, 2: n2, 3: n3, 4: n4}

    schedule = []
    for lv, k in counts.items():
        pool = by_level.get(lv) or templates
        picks = []
        while len(picks) < k:
            b = list(pool)
            rng.shuffle(b)
            picks.extend(b)
        schedule.extend(picks[:k])

    rng.shuffle(schedule)
    return schedule[:count]


def generate_drill_set(
    unit_code="PRG-T01-C01",
    count=5,
    difficulty="ALL",
    drill_id=None,
    seed=None,
    focus_tags=None,
    data_root="drills/data",
):
    count = int(count)
    difficulty = str(difficulty).upper()
    if difficulty not in DIFFICULTY_MODES:
        difficulty = "ALL"

    rng = random.Random(seed)
    id_map = load_id_map()
    mod = load_unit(unit_code)
    verify_tags(mod.MISTAKE_TAGS)

    if not drill_id:
        drill_id = next_drill_id(unit_code, data_root=data_root)

    schedule = _pick_template_schedule(mod.TEMPLATES, count, difficulty, focus_tags, rng)

    problems = []
    seen_snippets = set()

    for idx, tpl in enumerate(schedule, 1):
        prob = None
        for _ in range(12):
            candidate = tpl["build"](rng)
            snip = candidate.get("codeSnippet", "")
            if snip not in seen_snippets:
                prob = candidate
                seen_snippets.add(snip)
                break
        if prob is None:
            prob = tpl["build"](rng)

        prob_id = f"Q{idx:02d}"
        prob["id"] = prob_id
        prob["templateKey"] = tpl["key"]
        prob["level"] = tpl["level"]
        prob["levelLabel"] = LEVEL_LABELS[tpl["level"]]

        # Pre-Execution Verification via Node.js
        verify_problem(prob, id_map=id_map)

        # Resolve Notion reference badges
        ref_badges = []
        for ref_code in prob.get("references", []):
            entry = id_map.get(ref_code, {})
            ref_title = entry.get("title", ref_code) if isinstance(entry, dict) else ref_code
            ref_badges.append(
                {
                    "code": ref_code,
                    "title": ref_title,
                    "notionUrl": notion_url_for(ref_code, id_map),
                }
            )
        prob["referenceBadges"] = ref_badges

        # Remove internal verification fields
        prob.pop("verify", None)

        # Per-problem attempt state
        prob["state"] = {
            "userInput": "",
            "score": None,
            "divergedStep": None,
            "mistakes": [],
            "lastCheck": None,
        }
        problems.append(prob)

    parts = unit_code.split("-")
    topic_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else unit_code
    chapter_code = f"{parts[0]}-{parts[1]}-{parts[2]}" if len(parts) >= 3 else unit_code

    unit_dir = os.path.join(data_root, unit_code)
    os.makedirs(unit_dir, exist_ok=True)
    file_path = os.path.join(unit_dir, f"{drill_id}.json")

    drill_doc = {
        "schemaVersion": "2.0-prg",
        "drillId": drill_id,
        "subject": "PRG",
        "unitCode": unit_code,
        "unitTitle": getattr(mod, "TITLE", unit_code),
        "chapterCode": chapter_code,
        "topicCode": topic_code,
        "unitNotionUrl": notion_url_for(unit_code, id_map),
        "createdAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "questionCount": count,
            "difficulty": difficulty,
            "difficultyMode": DIFFICULTY_MODES[difficulty],
        },
        "mistakeTags": mod.MISTAKE_TAGS,
        "problems": problems,
        "sessionSummary": {
            "practiceStatus": "Ready",
            "score": 0,
            "maxScore": count,
            "accuracyPct": 0,
            "mistakeCategories": [],
            "divergedStepsSummary": "No diverged steps logged.",
            "attemptDate": None,
        },
        "localFilePath": file_path,
    }

    from code_engine.workspace import materialize_drill_workspace

    materialize_drill_workspace(drill_doc)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(drill_doc, f, ensure_ascii=False, indent=2)

    print(f"[Verified & Saved] {file_path}")
    return drill_doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate verified programming drill JSON.")
    parser.add_argument("--unit", default="PRG-T01-C01", help="Unit or Chapter code (e.g. PRG-T01-C01)")
    parser.add_argument("--count", type=int, default=5, help="Number of questions (e.g. 5, 10, 15, 20)")
    parser.add_argument("--difficulty", default="ALL", help="Difficulty: ALL, 1, 2, 3, or 4")
    parser.add_argument("--id", default=None, help="Explicit drill ID (e.g. DRL-PRG-T01-C01-01)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for deterministic generation")
    parser.add_argument("--focus-tag", action="append", default=[], help="Remediation mistake tag to prioritize")
    args = parser.parse_args()

    generate_drill_set(
        unit_code=args.unit,
        count=args.count,
        difficulty=args.difficulty,
        drill_id=args.id,
        seed=args.seed,
        focus_tags=args.focus_tag,
    )
