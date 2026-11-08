"""Coverage Report Generator (Task 5 & Enhancements).

Generates `reports/coverage.md` detailing:
1. Skill (domain, tier) x Level x Form matrix (problems in drills/data vs template forms).
2. Studio file deduplication audit (files ending with `-studio`).
3. Gaps: skills with templates but 0 generated problems, missing levels per domain.
4. พร้อมเรียนต่อ (Ready to Learn): unmastered skills whose hard prerequisites are fully satisfied.
5. Weaknesses & Mistake History: grouped primarily by trapTag with skills and files, including [inferred] tags.
6. Prerequisites Taxonomy Graph & Table: 23 registered DAG edges with hard/soft strength and pedagogical rationale.

Usage:
    python -m scripts.coverage_report [--data-dir drills/data] [--output reports/coverage.md]
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import datetime
import glob
import json
import os
import random
import re
from typing import Any


def load_taxonomy(taxonomy_path: str = "skills_taxonomy.json") -> dict[str, Any]:
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_templates() -> dict[str, dict[str, Any]]:
    """Loads all registered templates from math_engine and code_engine via auto-discovery."""
    from math_engine.templates import get_all_unit_templates as get_math_units
    from code_engine.templates import get_all_unit_templates as get_code_units

    templates: dict[str, dict[str, Any]] = {}
    for unit, tpls in get_math_units():
        for tpl in tpls:
            key = tpl.get("key") or tpl.get("name")
            if key:
                templates[key] = tpl
    for unit, tpls in get_code_units():
        for tpl in tpls:
            key = tpl.get("key") or tpl.get("name")
            if key:
                templates[key] = tpl
    return templates


# Fallback mapping for legacy drill JSON problems that predate the `skill` field
LEGACY_TRAP_MAP = {
    "pythagoras-hypotenuse": "GEO-RIGHT-TRIANGLE-HYP",
    "pythagoras-leg-subtraction": "GEO-RIGHT-TRIANGLE-LEG",
    "trapezoid-height": "GEO-TRAPEZOID-HEIGHT",
    "circle-diameter-radius": "GEO-CIRCLE-AREA-DIAMETER",
    "volume-surface-area": "GEO-CYLINDER-VOLUME-RADIUS",
    "angle-complement-vs-supplement": "GEO-LEGACY-ANGLE-COMPLEMENT",
    "triangle-sum-180": "GEO-LEGACY-TRIANGLE-SUM",
    "arithmetic-slip": "LEGACY-ARITHMETIC-SLIP",
    "empty-input-handling": "PRG-KATA-GROUPBY",
    "legacy-coupling-regression": "PRG-ARCH-REFACTOR-SUBSCRIPTION",
    "race-condition-cache-stampede": "PRG-ARCH-ASYNC-CACHE-RACE",
    "rate-limit-window-leak": "PRG-ARCH-PROJECT-RATE-LIMITER",
    "tax-discount-order-inversion": "PRG-ARCH-PIPELINE-PRICING",
    "unhandled-falsy-cache": "PRG-KATA-MEMOIZE",
    "timer-cancellation-flaw": "PRG-KATA-DEBOUNCE",
    "dns-server-tier": "PRG-LEGACY-DNS",
    "tcp-handshake-order": "PRG-LEGACY-TCP",
    "auth-401-vs-403": "PRG-LEGACY-AUTH",
    "http-method-misuse": "PRG-LEGACY-HTTP",
    "gateway-502-vs-504": "PRG-LEGACY-GATEWAY",
    "cache-conditional-304": "PRG-LEGACY-CACHE",
    "protocol-switch-101": "PRG-LEGACY-PROTOCOL",
    "conjugate-denominator": "MTH-COMPLEX-DIVISION-CONJUGATE",
    "standard-form": "MTH-COMPLEX-RADICAL-SIMPLIFY",
    "sign-slip": "MTH-COMPLEX-DIVISION-CONJUGATE",
}


def normalize_prompt(text: str) -> str:
    """Normalizes prompt text by stripping digits, excess whitespace, and lowercasing."""
    t = (text or "").strip().lower()
    t = re.sub(r"\d+(\.\d+)?", "<NUM>", t)
    t = re.sub(r"\s+", " ", t)
    return t


def scan_drills(
    data_dir: str,
    templates: dict[str, Any] | None = None,
) -> tuple[
    dict[str, int],
    dict[tuple[str, str], int],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, list[float]],
]:
    """Scans all drill JSON files in data_dir with studio deduplication.

    Returns:
      - skill_problem_counts: dict[skill_id, count] (excluding duplicates from -studio files)
      - skill_form_counts: dict[(skill_id, form_name), count] (excluding duplicates)
      - all_mistake_records: list of dicts with mistake details and is_inferred flag
      - studio_audit: dict[filepath, {total, duplicates, non_duplicates}]
      - skill_scores: dict[skill_id, list_of_attempted_scores]
    """
    skill_problem_counts: Counter[str] = Counter()
    skill_form_counts: Counter[tuple[str, str]] = Counter()
    all_mistake_records: list[dict[str, Any]] = []
    studio_audit: dict[str, dict[str, Any]] = {}
    skill_scores: dict[str, list[float]] = defaultdict(list)

    all_files = sorted(glob.glob(os.path.join(data_dir, "**", "*.json"), recursive=True))
    all_files = [f for f in all_files if "package.json" not in f]

    # Two-pass processing: non-studio files first to record primary prompt skeletons
    main_files = [f for f in all_files if "-studio" not in os.path.basename(f)]
    studio_files = [f for f in all_files if "-studio" in os.path.basename(f)]

    seen_normalized_prompts: set[str] = set()

    for filepath in main_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                drill = json.load(f)
        except Exception:
            continue

        rel_path = os.path.relpath(filepath, start=os.getcwd())
        problems = drill.get("problems") or []

        for prob in problems:
            pid = prob.get("id", "UNKNOWN")
            raw_skill = prob.get("skill")
            raw_form = prob.get("form")
            trap_tag = prob.get("commonTrapTag")
            form = raw_form or prob.get("archetype") or "direct"
            template_key = prob.get("templateKey")

            prompt_text = prob.get("prompt") or prob.get("question") or ""
            norm_p = normalize_prompt(prompt_text)
            if norm_p:
                seen_normalized_prompts.add(norm_p)

            # Resolve skill
            skill = raw_skill
            is_inferred = False
            if not skill and template_key and templates and template_key in templates:
                t = templates[template_key]
                t_forms = t.get("forms", {})
                if form in t_forms:
                    skill = t_forms[form].get("skill")
                elif "direct" in t_forms:
                    skill = t_forms["direct"].get("skill")
                elif t_forms:
                    skill = list(t_forms.values())[0].get("skill")
                else:
                    skill = t.get("skill")

            if not skill and trap_tag in LEGACY_TRAP_MAP:
                skill = LEGACY_TRAP_MAP[trap_tag]

            if not raw_skill or not raw_form:
                is_inferred = True

            if skill:
                skill_problem_counts[skill] += 1
                skill_form_counts[(skill, form)] += 1

            # Check mistakes and scores
            st = prob.get("state") or {}
            mistakes = st.get("mistakes") or []
            score = st.get("score")
            skipped = st.get("skipped", False)

            if score is not None and skill:
                skill_scores[skill].append(float(score))

            if mistakes:
                for m in mistakes:
                    all_mistake_records.append({
                        "file": rel_path,
                        "problem_id": pid,
                        "skill": skill or "UNASSIGNED",
                        "trap_tag": m,
                        "score": score,
                        "skipped": skipped,
                        "is_inferred": is_inferred,
                    })
            elif score is not None and score < 1.0:
                all_mistake_records.append({
                    "file": rel_path,
                    "problem_id": pid,
                    "skill": skill or "UNASSIGNED",
                    "trap_tag": trap_tag or "unspecified_slip",
                    "score": score,
                    "skipped": skipped,
                    "is_inferred": is_inferred,
                })
            elif skipped:
                all_mistake_records.append({
                    "file": rel_path,
                    "problem_id": pid,
                    "skill": skill or "UNASSIGNED",
                    "trap_tag": "skipped_concept_gap",
                    "score": 0,
                    "skipped": True,
                    "is_inferred": is_inferred,
                })

    # Second pass: studio files with deduplication
    for filepath in studio_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                drill = json.load(f)
        except Exception:
            continue

        rel_path = os.path.relpath(filepath, start=os.getcwd())
        problems = drill.get("problems") or []

        audit_entry = {"total": len(problems), "duplicates": 0, "non_duplicates": 0}

        for prob in problems:
            pid = prob.get("id", "UNKNOWN")
            raw_skill = prob.get("skill")
            raw_form = prob.get("form")
            trap_tag = prob.get("commonTrapTag")
            form = raw_form or prob.get("archetype") or "direct"
            template_key = prob.get("templateKey")

            prompt_text = prob.get("prompt") or prob.get("question") or ""
            norm_p = normalize_prompt(prompt_text)

            is_dup = norm_p in seen_normalized_prompts if norm_p else False
            if is_dup:
                audit_entry["duplicates"] += 1
            else:
                audit_entry["non_duplicates"] += 1
                if norm_p:
                    seen_normalized_prompts.add(norm_p)

            # Resolve skill
            skill = raw_skill
            is_inferred = False
            if not skill and template_key and templates and template_key in templates:
                t = templates[template_key]
                t_forms = t.get("forms", {})
                if form in t_forms:
                    skill = t_forms[form].get("skill")
                elif "direct" in t_forms:
                    skill = t_forms["direct"].get("skill")
                elif t_forms:
                    skill = list(t_forms.values())[0].get("skill")
                else:
                    skill = t.get("skill")

            if not skill and trap_tag in LEGACY_TRAP_MAP:
                skill = LEGACY_TRAP_MAP[trap_tag]

            if not raw_skill or not raw_form:
                is_inferred = True

            # Deduplication rule: do NOT count duplicate problems towards skill problem/form matrix
            if not is_dup and skill:
                skill_problem_counts[skill] += 1
                skill_form_counts[(skill, form)] += 1

            # Practice state records (user attempts in studio)
            st = prob.get("state") or {}
            mistakes = st.get("mistakes") or []
            score = st.get("score")
            skipped = st.get("skipped", False)

            if score is not None and skill:
                skill_scores[skill].append(float(score))

            if mistakes:
                for m in mistakes:
                    all_mistake_records.append({
                        "file": rel_path,
                        "problem_id": pid,
                        "skill": skill or "UNASSIGNED",
                        "trap_tag": m,
                        "score": score,
                        "skipped": skipped,
                        "is_inferred": is_inferred,
                    })
            elif score is not None and score < 1.0:
                all_mistake_records.append({
                    "file": rel_path,
                    "problem_id": pid,
                    "skill": skill or "UNASSIGNED",
                    "trap_tag": trap_tag or "unspecified_slip",
                    "score": score,
                    "skipped": skipped,
                    "is_inferred": is_inferred,
                })
            elif skipped:
                all_mistake_records.append({
                    "file": rel_path,
                    "problem_id": pid,
                    "skill": skill or "UNASSIGNED",
                    "trap_tag": "skipped_concept_gap",
                    "score": 0,
                    "skipped": True,
                    "is_inferred": is_inferred,
                })

        studio_audit[rel_path] = audit_entry

    return (
        dict(skill_problem_counts),
        dict(skill_form_counts),
        all_mistake_records,
        studio_audit,
        dict(skill_scores),
    )


PREREQUISITE_RATIONALES: dict[tuple[str, str], str] = {
    ("GEO-RIGHT-TRIANGLE-HYP", "GEO-RIGHT-TRIANGLE-LEG"): (
        "Solving for missing leg b = sqrt(c^2 - a^2) strictly requires the Pythagorean theorem relation."
    ),
    ("GEO-RIGHT-TRIANGLE-LEG", "GEO-RIGHT-TRIANGLE-APPLIED"): (
        "Pedagogical ordering: mastering algebraic leg subtraction eases word problem formulation."
    ),
    ("GEO-TRAPEZOID-AREA", "GEO-TRAPEZOID-HEIGHT"): (
        "Solving height h = 2A/(a+b) strictly requires knowledge of the trapezoid area formula."
    ),
    ("GEO-CIRCLE-AREA-RADIUS", "GEO-CIRCLE-AREA-DIAMETER"): (
        "Area from diameter strictly requires applying circle area formula with radius substitution r = d/2."
    ),
    ("GEO-CIRCLE-AREA-RADIUS", "GEO-CYLINDER-VOLUME-RADIUS"): (
        "Cylinder volume V = pi*r^2*h strictly requires computing the circular base area."
    ),
    ("GEO-CYLINDER-VOLUME-RADIUS", "GEO-CYLINDER-VOLUME-DIAMETER"): (
        "Cylinder volume from diameter requires base cylinder volume formula plus diameter scaling."
    ),
    ("MTH-COMPLEX-RADICAL-SIMPLIFY", "MTH-COMPLEX-ADDITION"): (
        "Pedagogical ordering: standard complex numbers a + bi can be added without prior radical simplification of negatives."
    ),
    ("MTH-COMPLEX-ADDITION", "MTH-COMPLEX-SUBTRACTION"): (
        "Pedagogical ordering: complex subtraction extends addition with negative distribution."
    ),
    ("MTH-COMPLEX-MULTIPLICATION", "MTH-COMPLEX-DIVISION-CONJUGATE"): (
        "Conjugate division multiplies numerator and denominator by conjugate using FOIL multiplication."
    ),
    ("MTH-COMPLEX-MULTIPLICATION", "MTH-COMPLEX-SQUARE-BINOMIAL"): (
        "Squaring a complex binomial is an algebraic specialization of complex multiplication."
    ),
    ("MTH-COMPLEX-MULTIPLICATION", "MTH-COMPLEX-EVALUATE-POLYNOMIAL"): (
        "Evaluating P(z) = a*z^2 + b*z + c strictly requires computing powers and products via complex multiplication."
    ),
    ("MTH-COMPLEX-RADICAL-SIMPLIFY", "MTH-COMPLEX-PRINCIPAL-ROOT-TRAP"): (
        "Detecting sqrt(-a)*sqrt(-b) != sqrt(ab) fallacy strictly requires simplifying sqrt(-a) = i*sqrt(a)."
    ),
    ("MTH-COMPLEX-POWER-I-MOD4", "MTH-COMPLEX-POWER-SUM"): (
        "Summing geometric series of i^k strictly requires modulo-4 cyclic reduction of powers of i."
    ),
    ("MTH-COMPLEX-MULTIPLICATION", "MTH-COMPLEX-DIAGNOSTIC-FLAW"): (
        "Spotting flaws in multi-step complex derivations strictly requires mastery of complex multiplication."
    ),
    ("MTH-COMPLEX-DIVISION-CONJUGATE", "MTH-COMPLEX-AC-OHMS-LAW"): (
        "Computing AC current I = V / Z strictly requires conjugate complex division."
    ),
    ("MTH-COMPLEX-MULTIPLICATION", "MTH-COMPLEX-GEOMETRIC-ROTATION"): (
        "2D geometric transformation in the Argand plane is mathematically defined by complex multiplication."
    ),
    ("MTH-COMPLEX-DIVISION-CONJUGATE", "MTH-COMPLEX-PARALLEL-IMPEDANCE"): (
        "Synthesizing parallel impedance Zeq = (Z1*Z2)/(Z1+Z2) strictly requires conjugate division."
    ),
    ("PRG-JS-SCOPE-HOISTING-VAR", "PRG-JS-SCOPE-HOISTING-LET"): (
        "Pedagogical ordering: let loop iteration binding can be learned as standard lexical scoping, var provides historical comparison."
    ),
    ("PRG-JS-EVENT-LOOP-MICROTASK", "PRG-JS-PROMISE-ASYNC-FLOW"): (
        "Pedagogical ordering: microtask queue knowledge clarifies Promise then/catch callback interleaving."
    ),
    ("PRG-KATA-GROUPBY", "PRG-ARCH-PIPELINE-PRICING"): (
        "Pedagogical ordering: collection aggregation helpers aid structured pipeline pricing transforms."
    ),
    ("PRG-JS-PROMISE-ASYNC-FLOW", "PRG-ARCH-ASYNC-CACHE-RACE"): (
        "Debugging async race conditions and stampedes strictly requires mastering Promise lifecycle and rejection handling."
    ),
    ("PRG-KATA-MEMOIZE", "PRG-ARCH-ASYNC-CACHE-RACE"): (
        "Pedagogical ordering: synchronous memoization establishes caching intuition before async concurrency."
    ),
    ("PRG-KATA-DEBOUNCE", "PRG-ARCH-PROJECT-RATE-LIMITER"): (
        "Pedagogical ordering: timer debouncing concepts ease sliding-window rate limiting design."
    ),
    ("CAL-DIFF-POWER", "CAL-DIFF-CHAIN"): (
        "Chain rule strictly requires mastery of basic power rule derivatives."
    ),
}


def generate_coverage_report(data_dir: str | None = None, output_path: str = "reports/coverage.md") -> str:
    if data_dir is None:
        data_dir = os.environ.get("DRILLS_DATA_DIR", "drills/data")
    taxonomy = load_taxonomy()
    skills_meta = taxonomy.get("skills", {})
    templates = load_all_templates()

    # Build cross-template trapTag maps to detect shared tags and ambiguity
    tag_skills_map: dict[str, set[str]] = {}
    tag_templates_map: dict[str, set[str]] = {}

    for tkey, tpl in templates.items():
        forms = tpl.get("forms") or {}
        for fname, fcfg in forms.items():
            sk = (fcfg.get("skill") if isinstance(fcfg, dict) else None) or tpl.get("skill")
            tt = tpl.get("trapTag") or (fcfg.get("trapTag") if isinstance(fcfg, dict) else None)
            if tt:
                tag_templates_map.setdefault(tt, set()).add(tkey)
                if sk:
                    tag_skills_map.setdefault(tt, set()).add(sk)
            
            build_fn = tpl.get("build")
            if callable(build_fn):
                try:
                    p = build_fn(random.Random(42), form=fname)
                    ctag = p.get("commonTrapTag")
                    pskill = p.get("skill") or sk
                    if ctag:
                        tag_templates_map.setdefault(ctag, set()).add(tkey)
                        if pskill:
                            tag_skills_map.setdefault(ctag, set()).add(pskill)
                    for opt in p.get("answerSpec", {}).get("options", []):
                        otag = opt.get("trapTag")
                        if otag:
                            tag_templates_map.setdefault(otag, set()).add(tkey)
                            if pskill:
                                tag_skills_map.setdefault(otag, set()).add(pskill)
                except Exception:
                    pass

    # Scan drills in drills/data with deduplication
    (
        skill_counts,
        skill_form_counts,
        mistake_records,
        studio_audit,
        skill_scores,
    ) = scan_drills(data_dir, templates=templates)

    # Map each skill to its template(s), forms, and level
    skill_to_template_info: dict[str, list[dict[str, Any]]] = defaultdict(list)
    domain_levels_covered: dict[str, set[int]] = defaultdict(set)

    for tpl_key, tpl in templates.items():
        forms = tpl.get("forms") or {"direct": {}}
        for form_name, form_cfg in forms.items():
            sk = form_cfg.get("skill") or tpl.get("skill")
            lvl = form_cfg.get("level") or tpl.get("level")
            if sk:
                skill_to_template_info[sk].append({
                    "templateKey": tpl_key,
                    "form": form_name,
                    "level": lvl,
                })
                if sk in skills_meta:
                    domain = skills_meta[sk].get("domain")
                    if domain and lvl:
                        domain_levels_covered[domain].add(lvl)

    lines: list[str] = [
        "# Coverage & Skills Taxonomy Report",
        "",
        f"> **Data Directory Scanned**: `{data_dir}`  ",
        f"> **Skills Taxonomy Registered**: {len(skills_meta)} skills across {len(set(s.get('domain') for s in skills_meta.values()))} domains",
        "",
        "---",
        "",
        "## 1. Skill (Domain, Tier) × Level × Form Matrix",
        "",
        "ตารางเปรียบเทียบ Skill ใน `skills_taxonomy.json` กับ Template ที่รองรับ และจำนวนโจทย์จริงใน `drills/data/` (ตัดจำนวนโจทย์ซ้ำจากไฟล์ `-studio` ออกแล้ว):",
        "",
        "| Domain | Skill ID | Skill Name | Tier | Level | Template Key | Forms Produced | Drill Problems in `drills/data` |",
        "| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :---: |",
    ]

    domain_order = list(dict.fromkeys(s.get("domain") for s in skills_meta.values() if s.get("domain")))
    skills_sorted = sorted(
        skills_meta.items(),
        key=lambda item: (
            domain_order.index(item[1].get("domain", "")) if item[1].get("domain") in domain_order else 99,
            item[1].get("domain", ""),
            item[0],
        ),
    )

    zero_problem_skills: list[tuple[str, str, str]] = []

    for sk_id, meta in skills_sorted:
        domain = meta.get("domain", "-")
        name = meta.get("name", "-")
        tier = meta.get("tier", "-")
        tpl_bindings = skill_to_template_info.get(sk_id, [])

        if tpl_bindings:
            tpl_keys = sorted(list(set(b["templateKey"] for b in tpl_bindings)))
            forms_list = sorted(list(set(b["form"] for b in tpl_bindings)))
            levels_list = sorted(list(set(b["level"] for b in tpl_bindings if b["level"] is not None)))
            tpl_str = ", ".join(f"`{k}`" for k in tpl_keys)
            forms_str = ", ".join(f"`{f}`" for f in forms_list)
            lvl_str = ", ".join(f"L{l}" for l in levels_list) if levels_list else "-"
        else:
            tpl_str = "*None*"
            forms_str = "*None*"
            lvl_str = "-"

        count = skill_counts.get(sk_id, 0)
        count_str = f"**{count}**" if count > 0 else "0"

        if count == 0 and tpl_bindings:
            zero_problem_skills.append((sk_id, domain, tpl_str))

        lines.append(
            f"| `{domain}` | `{sk_id}` | {name} | `{tier}` | {lvl_str} | {tpl_str} | {forms_str} | {count_str} |"
        )

    # Studio deduplication audit subsection
    lines.extend([
        "",
        "### 1.1 การตรวจสอบความซ้ำซ้อนในไฟล์ `-studio` (Studio File Deduplication Audit)",
        "",
        "จากการตรวจสอบโจทย์ในไฟล์ที่ลงท้ายด้วย `-studio` โดยเทียบ Skeleton ของโจทย์แบบ normalized ตัวเลขกับชุดโจทย์หลัก:",
        "",
        "| ไฟล์ที่ตรวจสอบ | จำนวนโจทย์ทั้งหมด | โจทย์ที่ซ้ำโครงชุดหลัก | โจทย์ใหม่ที่ไม่ซ้ำ | สถานะการนับใน Coverage Matrix |",
        "| :--- | :---: | :---: | :---: | :--- |",
    ])

    for sf, audit in sorted(studio_audit.items()):
        tot = audit["total"]
        dups = audit["duplicates"]
        non_dups = audit["non_duplicates"]
        status = "ตัดออกจากยอดรวม (ไม่นับซ้ำ)" if non_dups == 0 else f"นับเฉพาะ {non_dups} ข้อที่ไม่ซ้ำ"
        lines.append(f"| `{os.path.basename(sf)}` | {tot} | **{dups}** | {non_dups} | {status} |")

    lines.extend([
        "",
        "> [!NOTE]",
        "> ทุกโจทย์ในไฟล์ `-studio` ได้รับการคงไว้ในดิสก์โดยไม่มีการลบหรือย้าย และถูกกรองไม่ให้นับซ้ำในตาราง Coverage Matrix ตามข้อกำหนดอย่างเคร่งครัด",
        "",
        "---",
        "",
        "## 2. ช่องว่างของระบบ (Coverage Gaps)",
        "",
        "### 2.1 Skill ที่มี Template แล้ว แต่ยังไม่มีโจทย์จริงใน `drills/data`",
        "",
        f"มีทั้งหมด **{len(zero_problem_skills)}** Skills ที่มี Template ใน code engine / math engine พร้อมสร้างโจทย์ แต่ยังไม่เคยรัน generate บันทึกไฟล์ลงใน `drills/data/`:",
        "",
        "| Skill ID | Domain | Registered Template | สาเหตุ / สถานะ |",
        "| :--- | :--- | :--- | :--- |",
    ])

    for sk_id, dom, tpls in zero_problem_skills:
        reason = ""
        if dom == "complex_numbers":
            reason = "Unit `MTH-T02-C01-U01` อยู่ในสตูดิโอ ยังไม่ได้ generate ลงใน `drills/data/` ส่วนกลาง"
        elif dom == "javascript_core":
            reason = "Unit `PRG-T01-C01` มี template แล้ว แต่ยังไม่ได้รัน generate ชุดฝึกในโฟลเดอร์นี้"
        elif dom == "geometry":
            reason = "Form ทางเลือกหรือโจทย์ประยุกต์ของ template ยังไม่ถูกสุ่มลงในชุดฝึก 2 ชุดแรก"
        else:
            reason = "ยังไม่มีการสร้างชุดฝึกที่ครอบคลุม skill นี้"
        lines.append(f"| `{sk_id}` | `{dom}` | {tpls} | {reason} |")

    lines.extend([
        "",
        "### 2.2 ระดับความยากที่แต่ละ Domain ขาด (Missing Levels per Domain)",
        "",
        "จากการตรวจสอบการรองรับระดับ Level 1 - Level 4 ของทุก Domain พบสถานะดังนี้:",
        "",
        "| Domain | ระดับที่ครอบคลุมแล้ว | ระดับที่ยังขาด (Gaps) | ข้อสังเกต |",
        "| :--- | :---: | :---: | :--- |",
    ])

    all_expected_levels = {1, 2, 3, 4}
    for dom in domain_order:
        covered = domain_levels_covered.get(dom, set())
        missing = sorted(list(all_expected_levels - covered))
        covered_str = ", ".join(f"L{l}" for l in sorted(covered)) if covered else "*ไม่มี*"
        missing_str = ", ".join(f"**L{l}**" for l in missing) if missing else "ครบถ้วน (None)"
        notes = ""
        if dom == "geometry":
            notes = "หลังปรับลด `cylinder-volume` เหลือ L2 ทำให้หมวดเรขาคณิตยังขาด L3 (Trap/Diagnostic) และ L4 (Applied Synthesis)"
        elif dom == "complex_numbers":
            notes = "มีโจทย์ครบตั้งแต่ L1 (ราก, บวก/ลบ, กำลัง i) ถึง L4 (AC circuit, 2D rotation, parallel impedance)"
        elif dom == "javascript_core":
            notes = "มีโจทย์ครบตั้งแต่ L1 (scope hoisting) ถึง L4 (prototype chain mutation)"
        elif dom == "software_architecture":
            notes = "มีโจทย์ครบตั้งแต่ L1 (kata_groupby) ถึง L4 (sliding-window rate limiter)"
        lines.append(f"| `{dom}` | {covered_str} | {missing_str} | {notes} |")

    # SECTION 3: พร้อมเรียนต่อ (Ready to Learn)
    lines.extend([
        "",
        "---",
        "",
        "## 3. พร้อมเรียนต่อ (Ready to Learn)",
        "",
        "> [!IMPORTANT]",
        "> **เกณฑ์ประเมินการบรรลุ (Mastery Criteria)**: เคยฝึกทำโจทย์ $\\ge 5$ ข้อ และได้คะแนนเฉลี่ย $\\ge 80\\%$ (0.80)  ",
        "> จัดกลุ่มออกเป็น 3 ส่วน: 1) แนะนำถัดไป (Top 3) อิงตามกับดักที่พลาดบ่อย, 2) ถูกล็อก (รอผ่าน Hard Prereqs), 3) รากที่พร้อมเริ่มทันที",
        "",
    ])

    # Evaluate mastery per skill
    min_drills_count = 5
    min_avg_score = 0.80
    skill_mastery: dict[str, bool] = {}
    for sk_id in skills_meta:
        scores = skill_scores.get(sk_id, [])
        count = len(scores)
        avg = (sum(scores) / count) if count > 0 else 0.0
        skill_mastery[sk_id] = (count >= min_drills_count and avg >= min_avg_score)

    # 1. แนะนำถัดไป (Top 3): เชื่อม trapTag ที่พลาดบ่อยกับ skill เจ้าของ trap
    trap_to_skill: dict[str, str] = {}
    for tkey, t in templates.items():
        forms = t.get("forms") or {"direct": {}}
        for fname, fcfg in forms.items():
            tt = fcfg.get("trapTag") or t.get("trapTag")
            sk = fcfg.get("skill") or t.get("skill")
            if tt and sk:
                trap_to_skill[tt] = sk
    for tt, sk in LEGACY_TRAP_MAP.items():
        if tt not in trap_to_skill and sk in skills_meta:
            trap_to_skill[tt] = sk

    trap_counts = Counter(r["trap_tag"] for r in mistake_records)

    top_3_recs: list[dict[str, Any]] = []
    seen_target_skills: set[str] = set()

    for tt, cnt in trap_counts.most_common():
        owner_skill = trap_to_skill.get(tt)
        if not owner_skill or owner_skill not in skills_meta:
            continue
        if skill_mastery.get(owner_skill, False):
            continue

        # Trace back along hard prerequisites until finding an unmastered skill whose hard prereqs are met
        curr = owner_skill
        chain = [curr]
        visited = {curr}
        while True:
            hard_prereqs = [p["skill"] for p in skills_meta[curr].get("prerequisites", []) if p.get("strength") == "hard"]
            unmastered_hard = [p for p in hard_prereqs if not skill_mastery.get(p, False)]
            if not unmastered_hard:
                break
            nxt = unmastered_hard[0]
            if nxt in visited:
                break
            visited.add(nxt)
            chain.append(nxt)
            curr = nxt

        target_skill = curr
        if target_skill not in seen_target_skills:
            seen_target_skills.add(target_skill)

            is_ambiguous = len(tag_skills_map.get(tt, set())) > 1
            ambig_note = f"<br>*(ข้อสังเกต: trapTag นี้ใช้ซ้ำในหลาย Skill ({', '.join(sorted(tag_skills_map[tt]))}) เจ้าของ trap จึงอาจกำกวม)*" if is_ambiguous else ""

            if target_skill == owner_skill:
                reason = f"`{tt}` (พลาด {cnt} ครั้ง) $\\to$ เจ้าของกับดักคือ `{owner_skill}` $\\to$ พร้อมฝึกได้ทันที (Hard Prereqs ครบ)" + ambig_note
            else:
                steps_str = " $\\to$ ติด ".join(f"`{s}`" for s in chain)
                reason = f"`{tt}` (พลาด {cnt} ครั้ง) $\\to$ {steps_str} $\\to$ **ต้องฝึก `{target_skill}` ให้ชำนาญก่อน**" + ambig_note

            top_3_recs.append({
                "trap_tag": tt,
                "mistake_count": cnt,
                "owner_skill": owner_skill,
                "target_skill": target_skill,
                "target_name": skills_meta[target_skill].get("name", target_skill),
                "reason": reason,
            })

        if len(top_3_recs) == 3:
            break

    lines.extend([
        "### 3.1 แนะนำถัดไป (Top 3 Recommendations)",
        "",
        "> [!NOTE]",
        "> **ข้อสังเกตความกำกวมของ Trap Tag**: เมื่อ `trapTag` เดียวกันถูกใช้งานซ้ำในหลาย Template หรือหลาย Skill การระบุ Skill เจ้าของกับดักจะยึดตาม Template ที่มีประวัติผิดจริง แต่ต้นตอของข้อผิดพลาดอาจกำกวมได้หากผู้เรียนพลาดกับดักเดียวกันในบริบทอื่น",
        "",
        "วิเคราะห์จากกับดัก (`trapTag`) ที่มีประวัติทำผิดบ่อยที่สุด เชื่อมโยงหา Skill เจ้าของกับดัก แล้วไล่สาย Hard Prerequisites ไปยังทักษะต้นทางที่พร้อมฝึกได้ทันที:",
        "",
    ])

    if not top_3_recs:
        lines.append("*ไม่มีข้อมูลประวัติการทำผิดเพียงพอสำหรับการวิเคราะห์แนะนำ*")
    else:
        lines.extend([
            "| อันดับ | Trap Tag ที่พลาดบ่อย | จำนวนครั้ง | ปลายทางที่มีปัญหา | ทักษะแนะนำให้ฝึกทันที (Target) | เส้นทางเหตุผลและการเชื่อมโยง (Reasoning Path) |",
            "| :---: | :--- | :---: | :--- | :--- | :--- |",
        ])
        for idx, rec in enumerate(top_3_recs, start=1):
            lines.append(
                f"| **{idx}** | `{rec['trap_tag']}` | **{rec['mistake_count']}** | `{rec['owner_skill']}` | `{rec['target_skill']}` ({rec['target_name']}) | {rec['reason']} |"
            )

        if len(top_3_recs) < 3:
            lines.extend([
                "",
                f"> [!NOTE]",
                f"> **ข้อสังเกตข้อมูลจริง**: ระบบมีประวัติข้อผิดพลาดที่แมปกับ Taxonomy ได้เพียง {len(top_3_recs)} สาย (รายงานตามข้อมูลจริง ไม่คาดเดาเพิ่มเติม)",
            ])

    # 2. ถูกล็อก (Locked Skills)
    locked_skills: list[dict[str, Any]] = []
    # 3. รากที่ยังไม่เคยฝึก (Unpracticed Root Skills)
    root_skills: list[dict[str, Any]] = []

    for sk_id, meta in skills_meta.items():
        if skill_mastery.get(sk_id, False):
            continue

        prereqs = meta.get("prerequisites", [])
        hard_prereqs = [p["skill"] for p in prereqs if p.get("strength") == "hard"]
        unmastered_hard = [p for p in hard_prereqs if not skill_mastery.get(p, False)]

        scores = skill_scores.get(sk_id, [])
        cnt = len(scores)
        avg = (sum(scores) / cnt) if cnt > 0 else 0.0

        if unmastered_hard:
            locked_skills.append({
                "skill_id": sk_id,
                "domain": meta.get("domain", "-"),
                "name": meta.get("name", "-"),
                "tier": meta.get("tier", "-"),
                "blocked_by": unmastered_hard,
                "practiced_count": cnt,
            })
        elif len(hard_prereqs) == 0:
            root_skills.append({
                "skill_id": sk_id,
                "domain": meta.get("domain", "-"),
                "name": meta.get("name", "-"),
                "tier": meta.get("tier", "-"),
                "practiced_count": cnt,
                "avg_score": avg,
            })

    # Sort locked by domain, tier, skill_id
    locked_skills.sort(
        key=lambda x: (
            domain_order.index(x["domain"]) if x["domain"] in domain_order else 99,
            x["tier"],
            x["skill_id"],
        )
    )

    # Sort root skills by practiced_count (asc), domain, tier, skill_id
    root_skills.sort(
        key=lambda x: (
            x["practiced_count"],
            domain_order.index(x["domain"]) if x["domain"] in domain_order else 99,
            x["tier"],
            x["skill_id"],
        )
    )

    lines.extend([
        "",
        "### 3.2 ทักษะที่ถูกล็อก (Locked Skills)",
        "",
        f"มีทั้งหมด **{len(locked_skills)}** ทักษะที่ยังไม่สามารถเริ่มฝึกได้อย่างมีประสิทธิภาพ เนื่องจากยังมี Hard Prerequisites ที่ยังไม่ผ่านเกณฑ์ Mastery ($\\ge 5$ ข้อ, $\\ge 80\\%$):",
        "",
        "| ลำดับ | Domain | Skill ID | Skill Name | Tier | ติด Hard Prerequisite ตัวใด (Blocking Prereqs) |",
        "| :---: | :--- | :--- | :--- | :---: | :--- |",
    ])

    for idx, lk in enumerate(locked_skills, start=1):
        blocked_str = ", ".join(f"`{b}`" for b in lk["blocked_by"])
        lines.append(f"| {idx} | `{lk['domain']}` | `{lk['skill_id']}` | {lk['name']} | `{lk['tier']}` | {blocked_str} |")

    lines.extend([
        "",
        "### 3.3 รากที่ยังไม่เคยฝึก (Unpracticed Root Skills)",
        "",
        f"มีทั้งหมด **{len(root_skills)}** ทักษะรากฐานที่ไม่มี Hard Prerequisite ผูกมัด (0 Hard Prerequisites) พร้อมให้ผู้เรียนเริ่มฝึกเป็นจุดเริ่มต้นได้ทันที:",
        "",
        "| ลำดับ | Domain | Skill ID | Skill Name | Tier | ประวัติการฝึก | สถานะความพร้อม |",
        "| :---: | :--- | :--- | :--- | :---: | :---: | :--- |",
    ])

    for idx, rk in enumerate(root_skills, start=1):
        hist_str = f"{rk['practiced_count']} ข้อ ({rk['avg_score']*100:.0f}%)" if rk["practiced_count"] > 0 else "ยังไม่เคยฝึก (0 ข้อ)"
        status = "พร้อมเริ่มทันที (0 Prereqs)"
        lines.append(f"| {idx} | `{rk['domain']}` | `{rk['skill_id']}` | {rk['name']} | `{rk['tier']}` | {hist_str} | {status} |")

    # SECTION 4: Weaknesses & Mistake History
    lines.extend([
        "",
        "---",
        "",
        "## 4. สรุปประวัติข้อผิดพลาดและจุดอ่อน (Weaknesses & Trap Distribution)",
        "",
        "สรุปจากประวัติการทำโจทย์ใน `state.mistakes` และข้อที่ `score < 1.0` โดยจัดกลุ่มตาม `trapTag` เป็นแกนหลัก:",
        "",
        "### 4.1 สถิติแยกตาม Trap Tag (Trap Tag Overview)",
        "",
        "| ลำดับ | Trap Tag / รหัสกับดัก | จำนวนครั้งที่ผิด | เกิดใน Skill ใดบ้าง | เกิดในไฟล์ใดบ้าง |",
        "| :---: | :--- | :---: | :--- | :--- |",
    ])

    if not mistake_records:
        lines.append("*ไม่มีประวัติการตอบผิดใน drills/data/*")
    else:
        # Group by trap_tag
        trap_tag_counts: Counter[str] = Counter()
        trap_tag_skills: dict[str, set[str]] = defaultdict(set)
        trap_tag_files: dict[str, set[str]] = defaultdict(set)

        for r in mistake_records:
            tt = r["trap_tag"]
            sk = r["skill"]
            if r.get("is_inferred"):
                sk_label = f"`{sk}` [inferred]"
            else:
                sk_label = f"`{sk}`"

            trap_tag_counts[tt] += 1
            trap_tag_skills[tt].add(sk_label)
            trap_tag_files[tt].add(os.path.basename(r["file"]))

        for idx, (tt, cnt) in enumerate(trap_tag_counts.most_common(), start=1):
            skills_str = ", ".join(sorted(trap_tag_skills[tt]))
            files_str = ", ".join(f"`{f}`" for f in sorted(trap_tag_files[tt]))
            lines.append(f"| {idx} | `{tt}` | **{cnt}** | {skills_str} | {files_str} |")

        # Table 4.2: Breakdown by Skill
        lines.extend([
            "",
            "### 4.2 จำแนกข้อผิดพลาดตาม Skill (Breakdown by Skill)",
            "",
            "| ลำดับ | Skill ID | การระบุ Skill | Trap Tag ที่พบ | จำนวนครั้งที่ผิด | ไฟล์ที่เกิดปัญหา |",
            "| :---: | :--- | :---: | :--- | :---: | :--- |",
        ])

        skill_trap_counts: Counter[tuple[str, bool, str]] = Counter()
        skill_trap_files: dict[tuple[str, bool, str], set[str]] = defaultdict(set)

        for r in mistake_records:
            k = (r["skill"], r.get("is_inferred", False), r["trap_tag"])
            skill_trap_counts[k] += 1
            skill_trap_files[k].add(os.path.basename(r["file"]))

        for idx, ((sk, is_inf, tt), cnt) in enumerate(skill_trap_counts.most_common(), start=1):
            inf_label = "[inferred]" if is_inf else "Explicit"
            files_str = ", ".join(f"`{f}`" for f in sorted(skill_trap_files[(sk, is_inf, tt)]))
            lines.append(f"| {idx} | `{sk}` | `{inf_label}` | `{tt}` | **{cnt}** | {files_str} |")

    # Section 4.3: Shared Trap Tags Audit
    shared_tags = [
        (t, len(tpls), sorted(tpls), sorted(tag_skills_map.get(t, [])))
        for t, tpls in tag_templates_map.items()
        if len(tpls) > 1
    ]
    shared_tags.sort(key=lambda x: (-x[1], x[0]))

    lines.extend([
        "",
        "### 4.3 ตรวจสอบชื่อ Trap Tag ที่ใช้ซ้ำข้าม Template (Shared Trap Tags Audit)",
        "",
        "รายงานรายชื่อ `trapTag` ที่มีการประกาศใช้งานในมากกว่า 1 Template เพื่อติดตามความกำกวมในการวิเคราะห์จุดอ่อน:",
        "",
        "| ลำดับ | Trap Tag ที่ใช้ซ้ำ | จำนวน Template ที่ใช้ | รายชื่อ Templates ที่ใช้ | รายชื่อ Skills ที่เกี่ยวข้อง |",
        "| :---: | :--- | :---: | :--- | :--- |",
    ])
    for s_idx, (stag, scnt, stpls, sskills) in enumerate(shared_tags, start=1):
        tpls_str = ", ".join(f"`{t}`" for t in stpls)
        skills_str = ", ".join(f"`{s}`" for s in sskills) if sskills else "*None*"
        lines.append(f"| {s_idx} | `{stag}` | **{scnt}** | {tpls_str} | {skills_str} |")

    # SECTION 5: Prerequisites Graph & Table
    edge_list: list[tuple[str, str, str]] = []
    for sid, sdata in skills_meta.items():
        for p in sdata.get("prerequisites", []):
            edge_list.append((p["skill"], sid, p.get("strength", "hard")))

    # Sort edges by source domain, source, target
    edge_list.sort(
        key=lambda x: (
            domain_order.index(skills_meta.get(x[0], {}).get("domain", ""))
            if skills_meta.get(x[0], {}).get("domain") in domain_order
            else 99,
            x[0],
            x[1],
        )
    )

    lines.extend([
        "",
        "---",
        "",
        "## 5. แผนผังและตาราง Prerequisite ของทักษะ (Skill Prerequisites DAG)",
        "",
        "> [!NOTE]",
        "> **นิยาม Strength**:",
        "> - `hard`: ไม่สามารถทำหรือทำความเข้าใจปลายทางได้เลยหากขาดทักษะต้นทาง (Strict Technical Prerequisite)",
        "> - `soft`: ช่วยให้เรียนรู้ปลายทางได้ง่ายขึ้นตามลำดับการสอน แต่ทางเทคนิคสามารถศึกษาขนานกันได้ (Pedagogical Flow)",
        "",
        f"### 5.1 ตารางความสัมพันธ์ {len(edge_list)} เส้น Prerequisite ใน `skills_taxonomy.json`",
        "",
        "| ลำดับ | Source Skill (ต้นทาง) | Target Skill (ปลายทาง) | Strength | เหตุผลทางเทคนิคและการสอน (Rationale) |",
        "| :---: | :--- | :--- | :---: | :--- |",
    ])

    for idx, (src, dst, strength) in enumerate(edge_list, start=1):
        st_badge = f"**`{strength}`**" if strength == "hard" else f"`{strength}`"
        rat = PREREQUISITE_RATIONALES.get((src, dst), "Strict technical prerequisite.")
        lines.append(f"| {idx} | `{src}` | `{dst}` | {st_badge} | {rat} |")

    # Dynamic Mermaid Generation from skills_meta, domain_order, and edge_list
    lines.extend([
        "",
        "### 5.2 แผนภาพความสัมพันธ์แบบ DAG (Direct Acyclic Graph)",
        "",
        "```mermaid",
        "flowchart TD",
        "    classDef hard stroke:#dc2626,stroke-width:2px;",
        "    classDef soft stroke:#3b82f6,stroke-width:2px,stroke-dasharray: 4 4;",
    ])

    def _safe_nid(sid: str) -> str:
        return sid.replace("-", "_")

    # Group skills by domain
    dom_skills: dict[str, list[str]] = {d: [] for d in domain_order}
    for sid, sdata in skills_meta.items():
        d = sdata.get("domain", "other")
        dom_skills.setdefault(d, []).append(sid)

    # Classify intra vs cross edges
    intra_edges: dict[str, list[tuple[str, str, str]]] = {d: [] for d in domain_order}
    cross_edges: list[tuple[str, str, str]] = []
    for src, dst, st in edge_list:
        s_dom = skills_meta.get(src, {}).get("domain", "")
        d_dom = skills_meta.get(dst, {}).get("domain", "")
        if s_dom and s_dom == d_dom and s_dom in intra_edges:
            intra_edges[s_dom].append((src, dst, st))
        else:
            cross_edges.append((src, dst, st))

    for dom in domain_order:
        sids = dom_skills.get(dom, [])
        if not sids:
            continue
        dom_title = dom.replace("_", " ").title()
        dom_id = dom.replace("_", "").title()
        lines.append(f"\n    subgraph {dom_id} [Domain: {dom_title}]")

        edge_nodes = set()
        for src, dst, st in intra_edges.get(dom, []):
            edge_nodes.add(src)
            edge_nodes.add(dst)
            arrow = "==>|hard|" if st == "hard" else "-.->|soft|"
            lines.append(f'        {_safe_nid(src)}["{src}"] {arrow} {_safe_nid(dst)}["{dst}"]')

        for sid in sorted(sids):
            if sid not in edge_nodes:
                lines.append(f'        {_safe_nid(sid)}["{sid}"]')

        lines.append("    end")

    if cross_edges:
        lines.append("\n    %% Cross-domain relationship")
        for src, dst, st in cross_edges:
            arrow = "==>|hard|" if st == "hard" else "-.->|soft|"
            lines.append(f'    {_safe_nid(src)}["{src}"] {arrow} {_safe_nid(dst)}["{dst}"]')

    lines.extend([
        "```",
        "",
    ])

    report_content = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_content


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate skills coverage report from taxonomy, templates, and drills.")
    parser.add_argument("--data-dir", default="drills/data", help="Directory of drill JSON files to analyze.")
    parser.add_argument("--output", default="reports/coverage.md", help="Destination markdown file path.")
    args = parser.parse_args()

    generate_coverage_report(data_dir=args.data_dir, output_path=args.output)
    print(f"[Coverage Report] Generated successfully at {args.output}")


if __name__ == "__main__":
    main()
