#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure capacity across all units C01..C14 x template x form."""

import csv
import importlib
import random
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def measure_capacity(num_seeds=2000):
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    csv_path = reports_dir / "capacity.csv"
    summary_path = reports_dir / "capacity_summary.md"

    units = [f"mth_t01_c{i:02d}" for i in range(1, 15)]

    rows = []
    unit_stats = {}

    t0 = time.time()

    for mod_name in units:
        unit_code = f"MTH-T01-{mod_name[-3:].upper()}"
        try:
            mod = importlib.import_module(f"math_engine.templates.{mod_name}")
        except ModuleNotFoundError:
            continue

        unit_stats[unit_code] = {"total_forms": 0, "le_5": 0, "le_10": 0, "low_forms": []}

        for tpl in getattr(mod, "TEMPLATES", []):
            tpl_key = tpl["key"]
            build = tpl["build"]
            forms = tpl.get("forms", {})

            for form_name in forms.keys():
                unit_stats[unit_code]["total_forms"] += 1
                distinct_pairs = set()

                for s in range(num_seeds):
                    rng = random.Random(s)
                    p = build(rng, form=form_name)
                    prompt = p.get("prompt", "")
                    ans = p.get("answerPlain", "")
                    distinct_pairs.add((prompt, ans))

                cap = len(distinct_pairs)
                rows.append(
                    {
                        "unit": unit_code,
                        "template": tpl_key,
                        "form": form_name,
                        "capacity": cap,
                    }
                )

                if cap <= 5:
                    unit_stats[unit_code]["le_5"] += 1
                if cap <= 10:
                    unit_stats[unit_code]["le_10"] += 1
                    unit_stats[unit_code]["low_forms"].append((tpl_key, form_name, cap))

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["unit", "template", "form", "capacity"])
        writer.writeheader()
        writer.writerows(rows)

    # Write Summary Markdown
    sum_lines = []
    sum_lines.append("# Capacity Summary Report (2000 Seeds)")
    sum_lines.append(f"Generated across units MTH-T01-C01 through C14 in {time.time() - t0:.1f}s.\n")
    sum_lines.append("| Unit | Total Forms | Forms Capacity <= 5 | Forms Capacity <= 10 |")
    sum_lines.append("| :--- | :---: | :---: | :---: |")

    for u, stats in unit_stats.items():
        sum_lines.append(f"| {u} | {stats['total_forms']} | {stats['le_5']} | {stats['le_10']} |")

    sum_lines.append("\n## Forms with Low Capacity (<= 10)\n")
    found_any = False
    for u, stats in unit_stats.items():
        for tpl_key, form_name, cap in stats["low_forms"]:
            found_any = True
            sum_lines.append(f"- **{u}** `{tpl_key}` ({form_name}): capacity = {cap}")
    if not found_any:
        sum_lines.append("None. All forms have capacity > 10.")

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sum_lines) + "\n")

    print(f"Capacity CSV written to: {csv_path}")
    print(f"Capacity Summary written to: {summary_path}")


if __name__ == "__main__":
    measure_capacity()
