"""Audit Mode (G5): Non-destructive quality gate scanner for all existing drill JSON files.

Usage:
    python -m math_engine.audit
    python -m math_engine.audit --initial-g2
"""

from __future__ import annotations

import argparse
import copy
import glob
import json
import os
from collections import Counter
from typing import Any

from quality_rules import (
    INITIAL_PROPOSAL_RULES,
    QUALITY_RULES,
    QualityError,
    check_gate_g1,
    check_gate_g2,
    check_gate_g4,
    compute_fingerprint,
)


def audit_drill_file(
    filepath: str,
    rules: dict[str, Any] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Scan a single drill JSON file without modifying it on disk.

    Separates results into:
      - actual_violations: Failed a gate even though data was present (e.g. G1 wrong archetype, G2 steps/trap mismatch)
      - legacy_missing: Failed purely because old file lacks new optional fields (form, trapValue)
    """
    active_rules = rules or QUALITY_RULES
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    drill = copy.deepcopy(data)
    rel_file = os.path.basename(filepath)
    is_code = str(drill.get("subject", "")).upper() == "PRG" or "prg" in str(drill.get("schemaVersion", "")).lower()
    problems = drill.get("problems") or []
    actual_violations: list[dict[str, str]] = []
    legacy_missing: list[dict[str, str]] = []

    default_form = active_rules["G3"].get("default_form", "direct")
    max_fp_allowed = active_rules["G3"].get("max_same_fingerprint_per_set", 1)
    seen_fps: dict[str, list[str]] = {}

    for prob in problems:
        pid = prob.get("id", "UNKNOWN")
        raw_has_form = "form" in prob
        raw_has_trap = ("trapValue" in prob) or ("trapValue" in prob.get("verify", {}))

        # 1. Check G1 (Type-Content Alignment)
        try:
            check_gate_g1(prob, is_code=is_code, rules=active_rules)
        except QualityError as e:
            # G1 data (archetype, codeSnippet, language) is complete in schema, so this is an actual violation
            actual_violations.append(
                {
                    "file": rel_file,
                    "problem_id": pid,
                    "gate": "G1",
                    "reason": e.reason,
                }
            )

        # 2. Check G2 (Level-Structure Alignment)
        try:
            check_gate_g2(prob, rules=active_rules)
        except QualityError as e:
            # G2 data (level, steps, category) is complete in schema, so this is an actual violation
            actual_violations.append(
                {
                    "file": rel_file,
                    "problem_id": pid,
                    "gate": "G2",
                    "reason": e.reason,
                }
            )

        # 3. Check G3 (Anti-Skeleton Duplication)
        fp = prob.get("fingerprint") or compute_fingerprint(prob, default_form=default_form)
        seen_fps.setdefault(fp, []).append(pid)
        if len(seen_fps[fp]) > max_fp_allowed:
            first_pid = seen_fps[fp][0]
            reason = f"โครงสร้างโจทย์ซ้ำกับ {first_pid} (fingerprint='{fp}')"
            if not raw_has_form:
                legacy_missing.append(
                    {
                        "file": rel_file,
                        "problem_id": pid,
                        "gate": "G3",
                        "reason": f"{reason} [ไฟล์เก่าไม่มีฟิลด์ form ทำให้ถูกจัดเป็น form เดียวกัน]",
                    }
                )
            else:
                actual_violations.append(
                    {
                        "file": rel_file,
                        "problem_id": pid,
                        "gate": "G3",
                        "reason": reason,
                    }
                )

        # 4. Check G4 (Trap & Distractor Provenance)
        try:
            check_gate_g4(prob, is_code=is_code, rules=active_rules)
        except QualityError as e:
            if not raw_has_trap:
                legacy_missing.append(
                    {
                        "file": rel_file,
                        "problem_id": pid,
                        "gate": "G4",
                        "reason": e.reason,
                    }
                )
            else:
                actual_violations.append(
                    {
                        "file": rel_file,
                        "problem_id": pid,
                        "gate": "G4",
                        "reason": e.reason,
                    }
                )

    return actual_violations, legacy_missing


def run_audit(
    data_dir: str | None = None,
    rules: dict[str, Any] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], Counter[str], Counter[str], int, int]:
    """Run G5 audit across all JSON files in `data_dir`."""
    if data_dir is None:
        data_dir = os.environ.get("DRILLS_DATA_DIR", "drills/data")
    active_rules = rules or QUALITY_RULES
    pattern = os.path.join(data_dir, "**", "*.json")
    files = sorted(glob.glob(pattern, recursive=True))

    all_actual: list[dict[str, str]] = []
    all_legacy: list[dict[str, str]] = []
    counts_actual: Counter[str] = Counter()
    counts_legacy: Counter[str] = Counter()
    total_problems = 0

    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
            total_problems += len(d.get("problems") or [])
        file_actual, file_legacy = audit_drill_file(fp, rules=active_rules)
        all_actual.extend(file_actual)
        all_legacy.extend(file_legacy)
        for item in file_actual:
            counts_actual[item["gate"]] += 1
        for item in file_legacy:
            counts_legacy[item["gate"]] += 1

    return all_actual, all_legacy, counts_actual, counts_legacy, len(files), total_problems


def format_audit_markdown(
    actual_violations: list[dict[str, str]],
    legacy_missing: list[dict[str, str]],
    counts_actual: Counter[str],
    counts_legacy: Counter[str],
    total_files: int,
    total_problems: int,
) -> str:
    """Format audit results as a Markdown table for actual violations, plus legacy summary."""
    lines = [
        f'### 1. ผล Audit: กลุ่ม "ละเมิดจริง" (ตกด่านทั้งที่ข้อมูลครบ — สแกน {total_files} ไฟล์, {total_problems} ข้อ)',
        "",
        "| ไฟล์ | ข้อ | ด่านที่ตก | เหตุผลสั้นๆ |",
        "| :--- | :--- | :--- | :--- |",
    ]
    if not actual_violations:
        lines.append("| - | - | - | ไม่มีข้อที่ละเมิดจริง (ผ่านทุกด่าน) |")
    else:
        for f in actual_violations:
            lines.append(f"| `{f['file']}` | `{f['problem_id']}` | **{f['gate']}** | {f['reason']} |")

    lines.extend(
        [
            "",
            '#### สรุปจำนวน "ละเมิดจริง" แยกตามด่าน',
            f"- **G1 (ชนิดโจทย์ตรงกับเนื้อหา)**: {counts_actual.get('G1', 0)} รายการ",
            f"- **G2 (ระดับตรงกับโครงสร้าง)**: {counts_actual.get('G2', 0)} รายการ",
            f"- **G3 (ห้ามซ้ำโครงในชุดเดียวกัน)**: {counts_actual.get('G3', 0)} รายการ",
            f"- **G4 (ตัวหลอกและ Trap มีที่มาจริง)**: {counts_actual.get('G4', 0)} รายการ",
            f"- **รวมละเมิดจริงทั้งหมด**: {sum(counts_actual.values())} รายการ",
            "",
            "---",
            "",
            '### 2. ผล Audit: กลุ่ม "ขาดฟิลด์ (legacy)" (ไฟล์เก่าไม่มี form/trapValue — ไม่นับเป็น violation)',
            f"- **G4 (ขาดฟิลด์ trapValue / provenance)**: {counts_legacy.get('G4', 0)} รายการ (ทุกข้อที่มี commonTrapTag ในไฟล์เก่า)",
            f"- **G3 (โครงซ้ำเพราะขาดฟิลด์ form)**: {counts_legacy.get('G3', 0)} รายการ (เนื่องจากไฟล์เก่าไม่ได้ระบุ form จึงถูกจัดเป็น form direct เหมือนกัน)",
            f"- **รวมรายการขาดฟิลด์เก่าทั้งหมด**: {sum(counts_legacy.values())} รายการ",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit existing drill JSON files against Quality Gates G1-G4.")
    parser.add_argument("--data-dir", default="drills/data", help="Directory containing drill JSON files.")
    parser.add_argument(
        "--initial-g2",
        action="store_true",
        help="Use initial uncalibrated G2 proposal (L1: 1-2 steps) instead of calibrated QUALITY_RULES.",
    )
    args = parser.parse_args()

    rules = INITIAL_PROPOSAL_RULES if args.initial_g2 else QUALITY_RULES
    actual, legacy, c_act, c_leg, n_files, n_probs = run_audit(args.data_dir, rules=rules)
    print(format_audit_markdown(actual, legacy, c_act, c_leg, n_files, n_probs))


if __name__ == "__main__":
    main()
