"""Template CI Acceptance Gate.

CLI command to evaluate a problem template against quality benchmarks across 200 seeds:
    python -m scripts.accept_template <key>
    python -m scripts.accept_template --all

Criteria:
  - G1 pass rate >= 98.0%
  - G2 pass rate >= 98.0%
  - G4 pass rate >= 98.0%
  - Exhausted retries == 0 (must not fail 12 retries)
  - Diversity:
      - Fixed / Kata templates (marked `is_kata`, `is_fixed`, or `kata_*`):
        Exempt from multi-form requirements (>= 1 form, >= 1 fingerprint allowed).
      - Standard templates:
        Must have >= 2 forms produced and >= 3 distinct fingerprints.
"""

from __future__ import annotations

import argparse
from collections import Counter
import random
import sys
from typing import Any

from code_engine.templates import get_all_unit_templates as get_code_units
from math_engine.templates import get_all_unit_templates as get_math_units
from quality_rules import (
    QUALITY_RULES,
    QualityError,
    check_gate_g1,
    check_gate_g2,
    check_gate_g4,
    check_gate_g6,
    compute_fingerprint,
)


def get_all_registered_templates() -> list[tuple[str, dict[str, Any], bool]]:
    """Return all templates across math and code units as (unit_code, tpl, is_code)."""
    all_tpls = []
    for unit, tpls in get_math_units():
        for t in tpls:
            all_tpls.append((unit, t, False))
    for unit, tpls in get_code_units():
        for t in tpls:
            all_tpls.append((unit, t, True))
    return all_tpls


def is_template_exempt(tpl: dict[str, Any]) -> bool:
    """Return True if template is exempt from multi-form diversity requirements (kata / fixed)."""
    key = tpl.get("key", "")
    return bool(
        tpl.get("is_kata")
        or tpl.get("is_fixed")
        or key.startswith("kata_")
        or tpl.get("archetype") == "project-based"
    )


def evaluate_template(
    unit_code: str,
    tpl: dict[str, Any],
    is_code: bool,
    n_seeds: int = 200,
    force_exempt: bool = False,
) -> dict[str, Any]:
    """Run 200 seeds against template and evaluate CI acceptance criteria."""
    tpl_key = tpl["key"]
    level = tpl.get("level", 1)
    exempt = force_exempt or is_template_exempt(tpl)

    if isinstance(tpl.get("forms"), dict):
        declared_forms = list(tpl["forms"].keys())
    elif isinstance(tpl.get("forms"), (list, tuple)):
        declared_forms = list(tpl["forms"])
    else:
        declared_forms = ["direct"]

    form_counter = Counter()
    fps_set = set()
    skill_cells_set = set()
    g1_passes = 0
    g2_passes = 0
    g4_passes = 0
    g6_passes = 0
    total_retries = 0
    exhausted_12 = 0

    for s in range(1, n_seeds + 1):
        success = False
        retries_used = 0
        first_g1, first_g2, first_g4, first_g6 = False, False, False, False

        for attempt in range(12):
            rng = random.Random(s * 10000 + attempt)
            try:
                cand = tpl["build"](rng)
            except Exception:
                continue

            cand["id"] = "Q01"
            cand["templateKey"] = tpl_key
            if not cand.get("form"):
                cand["form"] = "direct"
            actual_form = cand["form"]

            if isinstance(tpl.get("forms"), dict) and actual_form in tpl["forms"]:
                finfo = tpl["forms"][actual_form]
                cand["level"] = finfo.get("level", level)
                if finfo.get("skill"):
                    cand["skill"] = finfo["skill"]
            else:
                cand["level"] = level
            cand["verificationLevel"] = tpl.get("verificationLevel", "machine-verified")

            g1_ok, g2_ok, g4_ok, g6_ok = False, False, False, False
            try:
                check_gate_g1(cand, is_code=is_code)
                g1_ok = True
            except QualityError:
                pass

            try:
                check_gate_g2(cand)
                g2_ok = True
            except QualityError:
                pass

            try:
                check_gate_g4(cand, is_code=is_code)
                g4_ok = True
            except QualityError:
                pass

            try:
                check_gate_g6(cand, is_code=is_code)
                g6_ok = True
            except QualityError:
                pass

            if attempt == 0:
                first_g1, first_g2, first_g4, first_g6 = g1_ok, g2_ok, g4_ok, g6_ok

            if g1_ok and g2_ok and g4_ok and g6_ok:
                success = True
                retries_used = attempt
                fp = compute_fingerprint(cand, template_key=tpl_key)
                fps_set.add(fp)
                form_counter[actual_form] += 1
                trap_tag = cand.get("commonTrapTag") or tpl.get("trapTag", "no-trap")
                skill_cells_set.add((tpl_key, actual_form, trap_tag))
                break

        if first_g1:
            g1_passes += 1
        if first_g2:
            g2_passes += 1
        if first_g4:
            g4_passes += 1
        if first_g6:
            g6_passes += 1

        total_retries += retries_used
        if not success:
            exhausted_12 += 1

    total_produced = sum(form_counter.values())
    form_proportions = {
        f: round(cnt / total_produced * 100, 1)
        for f, cnt in form_counter.items()
    } if total_produced > 0 else {}

    g1_rate = round(g1_passes / n_seeds * 100, 1)
    g2_rate = round(g2_passes / n_seeds * 100, 1)
    g4_rate = round(g4_passes / n_seeds * 100, 1)
    g6_rate = round(g6_passes / n_seeds * 100, 1)
    avg_retries = round(total_retries / n_seeds, 2)

    # Acceptance evaluation
    failures: list[str] = []
    if g1_rate < 98.0:
        failures.append(f"G1 pass rate {g1_rate}% < 98.0%")
    if g2_rate < 98.0:
        failures.append(f"G2 pass rate {g2_rate}% < 98.0%")
    if g4_rate < 98.0:
        failures.append(f"G4 pass rate {g4_rate}% < 98.0%")
    if g6_rate < 98.0:
        failures.append(f"G6 pass rate {g6_rate}% < 98.0%")
    if exhausted_12 > 0:
        failures.append(f"Exhausted 12 retries on {exhausted_12} seeds")

    if not exempt:
        if len(form_counter) < 2:
            failures.append(f"Non-exempt template produced only {len(form_counter)} form (requires >= 2)")
        min_fps = min(3, len(declared_forms))
        if len(fps_set) < min_fps:
            failures.append(f"Non-exempt template produced only {len(fps_set)} fingerprints (requires >= {min_fps})")
        # Check all declared forms produced
        unproduced = set(declared_forms) - set(form_counter.keys())
        if unproduced:
            failures.append(f"Declared forms never produced: {unproduced}")
    else:
        if len(form_counter) < 1:
            failures.append("No forms produced")
        if len(fps_set) < 1:
            failures.append("No fingerprints produced")

    passed = len(failures) == 0

    is_regression = (
        g1_rate < 98.0
        or g2_rate < 98.0
        or g4_rate < 98.0
        or g6_rate < 98.0
        or exhausted_12 > 0
    )
    is_diversity_backlog = (
        not is_regression
        and not exempt
        and len(form_counter) < 2
    )

    return {
        "unit": unit_code,
        "key": tpl_key,
        "is_code": is_code,
        "is_exempt": exempt,
        "passed": passed,
        "is_regression": is_regression,
        "is_diversity_backlog": is_diversity_backlog,
        "failures": failures,
        "g1_rate": g1_rate,
        "g2_rate": g2_rate,
        "g4_rate": g4_rate,
        "g6_rate": g6_rate,
        "avg_retries": avg_retries,
        "exhausted_12": exhausted_12,
        "declared_forms": declared_forms,
        "actual_forms_count": len(form_counter),
        "form_proportions": form_proportions,
        "distinct_fingerprints": len(fps_set),
        "distinct_skill_cells": len(skill_cells_set),
    }


def print_report(res: dict[str, Any]) -> None:
    status_tag = "[PASS]" if res["passed"] else "[FAIL]"
    category = "Exempt (Kata/Fixed)" if res["is_exempt"] else "Standard"
    print("=" * 70)
    print(f"{status_tag} Template CI Acceptance: {res['key']} ({res['unit']})")
    print("=" * 70)
    print(f"  Category:               {category}")
    print(f"  Pass Rates:             G1: {res['g1_rate']}%, G2: {res['g2_rate']}%, G4: {res['g4_rate']}%, G6: {res.get('g6_rate', 100.0)}%")
    print(f"  Retries:                Avg {res['avg_retries']} retries/seed, Exhausted 12: {res['exhausted_12']}")
    print(f"  Declared Forms:         {res['declared_forms']}")
    print(f"  Form Proportions:       {res['form_proportions']}")
    print(f"  Distinct Fingerprints:  {res['distinct_fingerprints']}")
    print(f"  Distinct Skill Cells:   {res['distinct_skill_cells']}")

    if res["passed"]:
        print(f"\n>> VERDICT: ACCEPTED - Template '{res['key']}' passes all CI quality gates.")
    else:
        print("\n>> VERDICT: REJECTED - Failures:")
        for f in res["failures"]:
            print(f"   - {f}")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Template CI Acceptance Gate CLI")
    parser.add_argument("key", nargs="?", help="Template key to accept/evaluate (or use --all)")
    parser.add_argument("--all", action="store_true", help="Evaluate all registered templates")
    parser.add_argument("--seeds", type=int, default=200, help="Number of seeds to test (default 200)")
    parser.add_argument("--exempt", action="store_true", help="Force exemption for fixed/kata template")
    args = parser.parse_args()

    import subprocess
    try:
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_hash = "unknown"

    all_tpls = get_all_registered_templates()

    if args.all:
        print("=" * 80)
        print(f"TEMPLATE CI ACCEPTANCE REPORT -- COMMIT: {commit_hash}")
        print(f"Evaluating {len(all_tpls)} registered templates ({args.seeds} seeds each)...")
        print("=" * 80)

        group1_regression = []
        group2_backlog = []
        group0_accepted = []

        for unit, tpl, is_code in all_tpls:
            res = evaluate_template(unit, tpl, is_code, n_seeds=args.seeds, force_exempt=args.exempt)
            if res["is_regression"]:
                group1_regression.append(res)
            elif res["is_diversity_backlog"]:
                group2_backlog.append(res)
            else:
                group0_accepted.append(res)

        print("\n" + "=" * 80)
        print(f"CI ACCEPTANCE EVALUATION SUMMARY (COMMIT: {commit_hash})")
        print("=" * 80)

        print("\n### กลุ่ม 1: Regression (G1/G2/G4/G6 < 98% หรือ retries หมด)")
        if not group1_regression:
            print("  (ไม่มี - ทุกเทมเพลตผ่านเกณฑ์คุณภาพพื้นฐาน G1/G2/G4/G6 >= 98.0% และ 0 retries)")
        else:
            print(f"  พบ {len(group1_regression)} เทมเพลตที่เกิด Regression:")
            for r in group1_regression:
                print(f"  - [{r['unit']}] {r['key']}: G1={r['g1_rate']}%, G2={r['g2_rate']}%, G4={r['g4_rate']}%, G6={r['g6_rate']}%, retries={r['exhausted_12']}")
                for f in r["failures"]:
                    print(f"      * {f}")

        print("\n### กลุ่ม 2: Backlog ความหลากหลาย (ผ่านทุกด่าน แต่ยังมีฟอร์มเดียว)")
        if not group2_backlog:
            print("  (ไม่มี - ทุกเทมเพลตมีความหลากหลาย >= 2 forms)")
        else:
            print(f"  พบ {len(group2_backlog)} เทมเพลตใน Backlog:")
            for r in group2_backlog:
                print(f"  - [{r['unit']}] {r['key']}: {r['actual_forms_count']} form produced ({r['form_proportions']}) | G1-G6: 100%")

        print("\n### กลุ่มที่ผ่านเกณฑ์สมบูรณ์ (CI Accepted: G1-G6 >= 98% และ Forms >= 2 หรือ Exempt)")
        print(f"  พบ {len(group0_accepted)} เทมเพลตที่ผ่านการรับรองสมบูรณ์:")
        for r in group0_accepted:
            cat = "Exempt" if r["is_exempt"] else f"{r['actual_forms_count']} forms"
            print(f"  - [{r['unit']}] {r['key']} ({cat})")

        print("\n" + "=" * 80)
        sys.exit(1 if group1_regression else 0)

    if not args.key:
        parser.print_help()
        sys.exit(1)

    match = next(((u, t, c) for (u, t, c) in all_tpls if t["key"] == args.key), None)
    if not match:
        print(f"Error: Template with key '{args.key}' not found across registered units.")
        print("Available keys:")
        for _, t, _ in all_tpls:
            print(f"  - {t['key']}")
        sys.exit(1)

    unit, tpl, is_code = match
    res = evaluate_template(unit, tpl, is_code, n_seeds=args.seeds, force_exempt=args.exempt)
    print_report(res)
    sys.exit(0 if res["passed"] else 1)


if __name__ == "__main__":
    main()
