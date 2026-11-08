#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit traps for MTH-T01-C01 and MTH-T01-C12."""

import importlib
import os
import random
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from math_engine.answer_check import to_expr


def run_audit():
    units = ["mth_t01_c01", "mth_t01_c12"]
    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "audit_c01_c12.md"

    lines = []
    lines.append("# Trap Telemetry Audit Report: MTH-T01-C01 and MTH-T01-C12\n")
    lines.append("Audited using existing registered templates and forms across 3 deterministic seeds (42, 43, 44).\n")

    for mod_name in units:
        mod = importlib.import_module(f"math_engine.templates.{mod_name}")
        unit_code = getattr(mod, "UNIT", mod_name)
        unit_title = getattr(mod, "TITLE", "")
        tag_desc_map = {}
        for tag in getattr(mod, "MISTAKE_TAGS", []):
            tag_desc_map[tag["id"]] = tag.get("description") or tag.get("label", "")

        lines.append(f"## Unit: {unit_code} - {unit_title}\n")

        for tpl in getattr(mod, "TEMPLATES", []):
            key = tpl["key"]
            build = tpl["build"]
            forms = tpl.get("forms", {})

            for form_name in forms.keys():
                lines.append(f"### Template: `{key}` | Form: `{form_name}`\n")

                for seed in [42, 43, 44]:
                    rng = random.Random(seed)
                    p = build(rng, form=form_name)

                    prompt = p.get("prompt", "")
                    ans = p.get("answerPlain", "")
                    trap_val = p.get("verify", {}).get("trapValue", "")
                    deriv = p.get("trapDerivation")
                    trap_kind = p.get("trapKind")
                    tag_id = p.get("commonTrapTag", "")
                    tag_desc = tag_desc_map.get(tag_id, "")

                    eval_val = ""
                    if deriv:
                        if trap_kind == "selection":
                            eval_val = str(deriv)
                        else:
                            try:
                                expr = to_expr(str(deriv), trusted=True)
                                eval_val = str(expr)
                            except Exception as e:
                                eval_val = f"ERROR: {e}"

                    lines.append(f"#### Seed {seed}")
                    lines.append(f"- **Prompt**: {prompt}")
                    lines.append(f"- **Answer**: `{ans}`")
                    lines.append(f"- **trapValue**: `{trap_val}`")
                    lines.append(f"- **trapDerivation**: `{deriv}`")
                    lines.append(f"- **Evaluated Value**: `{eval_val}`")
                    lines.append(f"- **Common Trap Tag**: `{tag_id}`")
                    lines.append(f"- **Tag Description**: {tag_desc}")
                    lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Audit written to {out_path}")


if __name__ == "__main__":
    run_audit()
