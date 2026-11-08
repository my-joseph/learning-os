# -*- coding: utf-8 -*-
"""
Pre-Generation Config -> Verified Programming Drill JSON Generator.

Generates ONLY the exact number of questions requested in the Pre-Generation Config
(e.g., 5, 10, 15, or 20), verifies every problem via real Node.js subprocess execution,
attaches resolved Notion deep links for cross-subject references, and writes the
clean JSON file to drills/data/<UNIT_CODE>/<DRILL_ID>.json (and mirrors to practice-studio/).
"""
import argparse
import datetime
import glob
import json
import logging
import os
import random
import shutil

from code_engine.fmt import DIFFICULTY_MODES, LEVEL_LABELS
from code_engine.templates import load_unit
from code_engine.verify import verify_problem, verify_tags
from quality_rules import (
    QUALITY_RULES,
    QualityError,
    compute_fingerprint,
    generate_with_quality_retries,
)

logger = logging.getLogger(__name__)


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


def next_drill_id(unit_code, data_root=None):
    if data_root is None:
        data_root = os.environ.get("DRILLS_DATA_DIR", "drills/data")
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


def _expand_template_pairs(templates):
    """Expand templates into (template, form) scheduling units."""
    pairs = []
    for t in templates:
        forms = t.get("forms")
        if isinstance(forms, dict):
            for fname, finfo in forms.items():
                pairs.append({
                    "template": t,
                    "key": t["key"],
                    "form": fname,
                    "level": finfo.get("level", t.get("level", 1)),
                    "skill": finfo.get("skill"),
                    "trapTag": t.get("trapTag"),
                    "verificationLevel": t.get("verificationLevel", "machine-verified"),
                })
        elif isinstance(forms, (list, tuple)):
            for fname in forms:
                pairs.append({
                    "template": t,
                    "key": t["key"],
                    "form": fname,
                    "level": t.get("level", 1),
                    "skill": t.get("skill"),
                    "trapTag": t.get("trapTag"),
                    "verificationLevel": t.get("verificationLevel", "machine-verified"),
                })
        else:
            pairs.append({
                "template": t,
                "key": t["key"],
                "form": "direct",
                "level": t.get("level", 1),
                "skill": t.get("skill"),
                "trapTag": t.get("trapTag"),
                "verificationLevel": t.get("verificationLevel", "machine-verified"),
            })
    return pairs


def _round_robin_pick(pool, k, rng):
    """Pick k items from pool using round-robin across shuffled pool items."""
    if not pool:
        return []
    shuffled_pool = list(pool)
    rng.shuffle(shuffled_pool)
    picks = []
    idx = 0
    while len(picks) < k:
        picks.append(shuffled_pool[idx % len(shuffled_pool)])
        idx += 1
        if idx % len(shuffled_pool) == 0:
            rng.shuffle(shuffled_pool)
    return picks[:k]


def _pick_template_schedule(templates, count, difficulty, focus_tags, rng, template_filter=None):
    all_pairs = _expand_template_pairs(templates)

    if template_filter:
        tpl_set = {t.strip() for t in template_filter} if isinstance(template_filter, (list, tuple, set)) else {t.strip() for t in str(template_filter).split(",")}
        filtered = [p for p in all_pairs if p["key"] in tpl_set]
        if filtered:
            all_pairs = filtered

    if focus_tags:
        tags_set = set(focus_tags) if isinstance(focus_tags, (list, tuple, set)) else {t.strip() for t in str(focus_tags).split(",")}
        matched = [
            p for p in all_pairs
            if p["key"] in tags_set
            or p["trapTag"] in tags_set
            or p.get("skill") in tags_set
            or p["form"] in tags_set
        ]
        if matched:
            return _round_robin_pick(matched, count, rng)

    if difficulty in ("1", "2", "3", "4"):
        lv = int(difficulty)
        pool = [p for p in all_pairs if p["level"] == lv]
        if not pool:
            pool = list(all_pairs)
        return _round_robin_pick(pool, count, rng)

    # Mixed Exam Mode: round-robin on (template, form) within a single set
    return _round_robin_pick(all_pairs, count, rng)


def generate_drill_set(
    unit_code="PRG-T01-C01",
    count=5,
    difficulty="ALL",
    drill_id=None,
    seed=None,
    focus_tags=None,
    templates=None,
    data_root=None,
    rules=None,
):
    if data_root is None:
        data_root = os.environ.get("DRILLS_DATA_DIR", "drills/data")
    count = int(count)
    difficulty = str(difficulty).upper()
    if difficulty not in DIFFICULTY_MODES:
        difficulty = "ALL"

    active_rules = rules or QUALITY_RULES
    base_seed = seed if seed is not None else random.randint(1, 10_000_000)
    id_map = load_id_map()
    mod = load_unit(unit_code)
    if getattr(mod, "IS_PILOT", False) and not os.environ.get("ENABLE_PILOT_DRILLS"):
        raise ValueError(
            f"Unit '{unit_code}' is currently flagged as PILOT. Generation of persistent drill files is blocked unless ENABLE_PILOT_DRILLS=1 is set."
        )
    verify_tags(mod.MISTAKE_TAGS)

    if not drill_id:
        drill_id = next_drill_id(unit_code, data_root=data_root)

    # Warn if any template in the unit only supports 1 form
    warn_msg = active_rules["G3"].get("single_form_warning_msg", "template นี้ผลิตได้โครงเดียว")
    for tpl in mod.TEMPLATES:
        forms = tpl.get("forms") or ["direct"]
        if len(forms) <= 1 and active_rules["G3"].get("warn_single_form_template", True):
            msg = f"[QualityGate-G3] Template '{tpl['key']}': {warn_msg}"
            logger.warning(msg)
            print(msg)

    def _build_attempt(attempt_seed: int):
        rng = random.Random(attempt_seed)
        schedule = _pick_template_schedule(mod.TEMPLATES, count, difficulty, focus_tags, rng, template_filter=templates)
        unique_tpls = {s["key"]: s["template"] for s in schedule}.values()
        available_forms_count = sum(len(t.get("forms") or ["direct"]) for t in unique_tpls)

        attempt_problems = []
        seen_snippets = set()
        seen_fingerprints = set()

        for idx, sched_item in enumerate(schedule, 1):
            tpl = sched_item["template"]
            target_form = sched_item["form"]
            target_level = sched_item["level"]
            target_skill = sched_item.get("skill")
            build_fn = tpl["build"]

            prob = None
            for _ in range(12):
                try:
                    candidate = build_fn(rng, form=target_form)
                except TypeError:
                    candidate = build_fn(rng)
                candidate["form"] = candidate.get("form", target_form)
                candidate["level"] = target_level
                if target_skill:
                    candidate["skill"] = target_skill
                candidate["verificationLevel"] = sched_item.get("verificationLevel", "machine-verified")
                snip = candidate.get("codeSnippet", "") or candidate.get("starterCode", "")
                cand_fp = compute_fingerprint(candidate, template_key=tpl["key"])
                if snip not in seen_snippets and cand_fp not in seen_fingerprints:
                    prob = candidate
                    seen_snippets.add(snip)
                    seen_fingerprints.add(cand_fp)
                    break
            if prob is None:
                try:
                    prob = build_fn(rng, form=target_form)
                except TypeError:
                    prob = build_fn(rng)
                prob["form"] = prob.get("form", target_form)
                prob["level"] = target_level
                if target_skill:
                    prob["skill"] = target_skill
                prob["verificationLevel"] = sched_item.get("verificationLevel", "machine-verified")

            prob_id = f"Q{idx:02d}"
            prob["id"] = prob_id
            prob["templateKey"] = tpl["key"]
            prob["levelLabel"] = LEVEL_LABELS.get(target_level, f"Level {target_level}")

            # Pre-Execution Verification via Node.js + Quality Gates (G1, G2, G4)
            verify_problem(prob, id_map=id_map, rules=active_rules)

            # Resolve Notion reference badges
            ref_badges = []
            for ref_code in prob.get("references", []):
                entry = id_map.get(ref_code, {})
                ref_title = entry.get("title", ref_code) if isinstance(entry, dict) else ref_code
                ref_badges.append({
                    "code": ref_code,
                    "title": ref_title,
                    "notionUrl": notion_url_for(ref_code, id_map),
                })
            prob["referenceBadges"] = ref_badges

            # Remove internal verification fields while keeping form, fingerprint, qualityGates
            prob.pop("verify", None)

            # Per-problem attempt state
            prob["state"] = {
                "userInput": "",
                "score": None,
                "divergedStep": None,
                "mistakes": [],
                "lastCheck": None,
            }
            attempt_problems.append(prob)

        return attempt_problems, available_forms_count

    problems = generate_with_quality_retries(_build_attempt, base_seed=base_seed, rules=active_rules)

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

    if data_root == "drills/data":
        from code_engine.workspace import materialize_drill_workspace
        materialize_drill_workspace(drill_doc)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(drill_doc, f, ensure_ascii=False, indent=2)

    # Mirror to practice-studio if directory exists and using relative drills/data
    if data_root == "drills/data" and os.path.exists("practice-studio"):
        studio_dir = os.path.join("practice-studio", data_root, unit_code)
        os.makedirs(studio_dir, exist_ok=True)
        studio_path = os.path.join(studio_dir, f"{drill_id}.json")
        shutil.copyfile(file_path, studio_path)

    print(f"[Verified & Saved] {file_path}")
    return drill_doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate verified programming drill JSON.")
    parser.add_argument("--unit", default="PRG-T01-C01", help="Unit or Chapter code (e.g. PRG-T01-C01)")
    parser.add_argument("--count", type=int, default=5, help="Number of questions (e.g. 5, 10, 15, 20)")
    parser.add_argument("--difficulty", default="ALL", help="Difficulty: ALL, 1, 2, 3, or 4")
    parser.add_argument("--id", default=None, help="Explicit drill ID (e.g. DRL-PRG-T01-C01-01)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for deterministic generation")
    parser.add_argument("--templates", default=None, help="Comma-separated template keys (e.g. scope_hoisting_loop)")
    parser.add_argument("--focus-tag", action="append", default=[], help="Remediation mistake tag to prioritize")
    args = parser.parse_args()

    generate_drill_set(
        unit_code=args.unit,
        count=args.count,
        difficulty=args.difficulty,
        drill_id=args.id,
        seed=args.seed,
        templates=args.templates,
        focus_tags=args.focus_tag,
    )
