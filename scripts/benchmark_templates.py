"""Benchmark script: Measures template diversity across 200 seeds for all templates."""

from collections import Counter, defaultdict
import copy
import json
import random
from typing import Any

from code_engine.templates.prg_t01_c01 import TEMPLATES as PRG_C01
from code_engine.templates.prg_t01_c03 import TEMPLATES as PRG_C03
from math_engine.templates.mth_t01_c12 import TEMPLATES as MTH_C12
from math_engine.templates.mth_t02_c01_u01 import TEMPLATES as MTH_C01
from quality_rules import (
    QUALITY_RULES,
    QualityError,
    check_gate_g1,
    check_gate_g2,
    check_gate_g4,
    compute_fingerprint,
)


def run_benchmark(n_seeds: int = 200) -> dict[str, Any]:
    all_groups = [
        ("MTH-T01-C12", MTH_C12, False),
        ("MTH-T02-C01-U01", MTH_C01, False),
        ("PRG-T01-C01", PRG_C01, True),
        ("PRG-T01-C03", PRG_C03, True),
    ]

    results = []
    examples_by_tpl_form = {}

    for unit_code, tpls, is_code in all_groups:
        for tpl in tpls:
            tpl_key = tpl["key"]
            level = tpl["level"]
            declared_forms = list(tpl["forms"].keys()) if isinstance(tpl.get("forms"), dict) else (tpl.get("forms") or ["direct"])

            form_counter = Counter()
            fps_set = set()
            fp_counter = Counter()
            skill_cells_set = set()
            g1_passes = 0
            g2_passes = 0
            g4_passes = 0
            total_retries = 0
            exhausted_12 = 0
            sample_per_form = {}

            for s in range(1, n_seeds + 1):
                # Run with retries up to 12
                success = False
                retries_used = 0
                first_g1 = False
                first_g2 = False
                first_g4 = False

                for attempt in range(12):
                    rng = random.Random(s * 10000 + attempt)
                    try:
                        cand = tpl["build"](rng)
                    except Exception as ex:
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

                    # Check gates
                    g1_ok, g2_ok, g4_ok = False, False, False
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

                    if attempt == 0:
                        first_g1 = g1_ok
                        first_g2 = g2_ok
                        first_g4 = g4_ok

                    if g1_ok and g2_ok and g4_ok:
                        success = True
                        retries_used = attempt
                        fp = compute_fingerprint(cand, template_key=tpl_key)
                        fps_set.add(fp)
                        fp_counter[fp] += 1
                        form_counter[actual_form] += 1
                        trap_tag = cand.get("commonTrapTag") or tpl.get("trapTag", "no-trap")
                        skill_cells_set.add((tpl_key, actual_form, trap_tag))

                        if actual_form not in sample_per_form:
                            sample_per_form[actual_form] = {
                                "unit": unit_code,
                                "key": tpl_key,
                                "level": level,
                                "form": actual_form,
                                "prompt": cand.get("prompt", ""),
                                "display": cand.get("display", ""),
                                "plainText": cand.get("plainText", ""),
                                "answer": cand.get("answerDisplay") or cand.get("answerPlain"),
                                "steps_count": len(cand.get("steps") or []),
                                "steps": [
                                    st.get("latex") or st.get("explain")
                                    for st in (cand.get("steps") or [])
                                ],
                            }
                        break

                if first_g1:
                    g1_passes += 1
                if first_g2:
                    g2_passes += 1
                if first_g4:
                    g4_passes += 1

                total_retries += retries_used
                if not success:
                    exhausted_12 += 1

            examples_by_tpl_form[f"{unit_code}::{tpl_key}"] = sample_per_form

            # Form proportions
            total_produced = sum(form_counter.values())
            form_proportions = {
                f: round(cnt / total_produced * 100, 1)
                for f, cnt in form_counter.items()
            } if total_produced > 0 else {}

            results.append({
                "unit": unit_code,
                "key": tpl_key,
                "level": level,
                "is_code": is_code,
                "declared_forms_count": len(declared_forms),
                "declared_forms": declared_forms,
                "actual_forms_count": len(form_counter),
                "form_proportions": form_proportions,
                "g1_pass_rate": round(g1_passes / n_seeds * 100, 1),
                "g2_pass_rate": round(g2_passes / n_seeds * 100, 1),
                "g4_pass_rate": round(g4_passes / n_seeds * 100, 1),
                "avg_retries": round(total_retries / n_seeds, 2),
                "exhausted_12": exhausted_12,
                "distinct_fingerprints": len(fps_set),
                "fingerprint_examples": list(fps_set)[:3],
                "distinct_skill_cells": len(skill_cells_set),
                "skill_cells": [list(c) for c in sorted(skill_cells_set)],
            })

    return {
        "templates": results,
        "examples": examples_by_tpl_form,
        "n_seeds": n_seeds,
    }


if __name__ == "__main__":
    data = run_benchmark(n_seeds=200)
    print(json.dumps(data, indent=2, ensure_ascii=False))
