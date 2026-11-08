"""Sample Sheet Generator (Task 6).

Prints deterministic sample problems (1 problem per form) for any registered template
in clean Markdown format, complete with:
- Prompt
- Canonical Answer (answerPlain / answerDisplay)
- Trap Value (trapValue)
- Trap Tag (commonTrapTag)
- Step Count
- Level
- Skill
- Verification Level
- Form Name
- Step-by-step solution breakdown

Usage:
    python -m scripts.sample_sheet <template_key> [--seed 42]
"""

from __future__ import annotations

import argparse
import random
import sys
from typing import Any


def load_all_templates() -> dict[str, tuple[str, dict[str, Any]]]:
    """Loads all registered templates from math_engine and code_engine via auto-discovery.

    Returns dict mapping template_key -> (module_name, template_dict).
    """
    from math_engine.templates import get_all_unit_modules as get_math_modules
    from code_engine.templates import get_all_unit_modules as get_code_modules

    registry: dict[str, tuple[str, dict[str, Any]]] = {}

    for unit, mod in get_math_modules():
        mod_name = getattr(mod, "__name__", f"math_engine.{unit}")
        for tpl in getattr(mod, "TEMPLATES", []):
            key = tpl.get("key") or tpl.get("name")
            if key:
                registry[key] = (mod_name, tpl)

    for unit, mod in get_code_modules():
        mod_name = getattr(mod, "__name__", f"code_engine.{unit}")
        for tpl in getattr(mod, "TEMPLATES", []):
            key = tpl.get("key") or tpl.get("name")
            if key:
                registry[key] = (mod_name, tpl)

    return registry


def load_all_mistake_tag_descriptions() -> dict[str, str]:
    """Loads all mistake tag descriptions from registered modules."""
    from math_engine.templates import get_all_unit_modules as get_math_modules
    from code_engine.templates import get_all_unit_modules as get_code_modules

    tag_descriptions: dict[str, str] = {}
    for _, mod in list(get_math_modules()) + list(get_code_modules()):
        for tag_def in getattr(mod, "MISTAKE_TAGS", []):
            if isinstance(tag_def, dict) and "id" in tag_def:
                desc = tag_def.get("description") or tag_def.get("label") or ""
                if desc:
                    tag_descriptions[tag_def["id"]] = desc
    return tag_descriptions


def build_sample_sheet(template_key: str, seed: int = 42) -> str:
    registry = load_all_templates()
    tag_descriptions = load_all_mistake_tag_descriptions()
    if template_key not in registry:
        keys_list = "\n  - ".join(sorted(registry.keys()))
        raise KeyError(
            f"Template '{template_key}' not found in registry.\nAvailable templates:\n  - {keys_list}"
        )

    mod_name, tpl = registry[template_key]
    forms_dict = tpl.get("forms") or {"direct": {}}
    build_fn = tpl.get("build")

    lines = [
        f"# Sample Sheet: `{template_key}`",
        "",
        f"- **Module Source**: `{mod_name}`",
        f"- **Total Forms**: {len(forms_dict)} ({', '.join(f'`{f}`' for f in forms_dict.keys())})",
        f"- **Review Seed**: `{seed}`",
    ]

    # Pre-generate problems across all forms to inspect trap diversity
    form_problems: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    trap_signatures: dict[tuple[str, str], list[str]] = {}

    for form_name, form_cfg in forms_dict.items():
        rng = random.Random(seed)
        try:
            prob = build_fn(rng, form=form_name)
        except TypeError:
            prob = build_fn(rng)
        trap_tag = prob.get("commonTrapTag") or tpl.get("trapTag", "none")
        trap_value = str(prob.get("trapValue") or (prob.get("verify") or {}).get("trapValue") or "(None)")
        sig = (trap_tag, trap_value)
        trap_signatures.setdefault(sig, []).append(form_name)
        form_problems.append((form_name, form_cfg, prob))

    # Check for identical trapTag and trapValue across different forms
    warnings = []
    for (t_tag, t_val), f_names in trap_signatures.items():
        if len(f_names) > 1 and t_val != "(None)":
            forms_str = " and ".join(f"`{f}`" for f in f_names)
            warnings.append(
                f"> [!WARNING]\n"
                f"> **Trap Diversity Advisory**: Forms {forms_str} share the same trapTag (`{t_tag}`) "
                f"and identical trapValue (`{t_val}`). Consider tailoring the trap to the specific step error of each form."
            )

    if warnings:
        lines.append("")
        lines.extend(warnings)

    lines.extend([
        "",
        "---",
    ])

    for idx, (form_name, form_cfg, prob) in enumerate(form_problems, start=1):

        level = form_cfg.get("level") or prob.get("level") or tpl.get("level", 1)
        skill = form_cfg.get("skill") or prob.get("skill") or tpl.get("skill", "UNSPECIFIED")
        vlevel = prob.get("verificationLevel") or tpl.get("verificationLevel", "machine-verified")
        trap_tag = prob.get("commonTrapTag") or tpl.get("trapTag", "none")
        flaw_tag = prob.get("flawTag")
        trap_value = prob.get("trapValue") or (prob.get("verify") or {}).get("trapValue") or "(None)"
        ans_plain = prob.get("answerPlain") or prob.get("answerDisplay") or "-"
        ans_display = prob.get("answerDisplay") or ans_plain
        steps = prob.get("steps") or []
        step_count = len(steps)
        prompt = prob.get("prompt", "").strip()
        code_snippet = prob.get("codeSnippet")
        code_language = prob.get("language", "javascript")
        display = prob.get("display")
        options = (prob.get("answerSpec") or {}).get("options") or prob.get("options") or []
        input_hint = prob.get("inputHint") or "(None)"
        checkpoint_hint = prob.get("checkpointHint") or "(None)"

        # Anti-leak validation on learner hints
        from quality_rules import check_gate_anti_leak, QualityError
        is_code = prob.get("archetype") in ("code-tracing", "debugging", "refactoring") or bool(prob.get("codeSnippet"))
        try:
            check_gate_anti_leak(prob, is_code=is_code)
            anti_leak_status = "PASS (No answer leaks detected in hints)"
        except QualityError as exc:
            anti_leak_status = f"FAIL ({exc.reason})"
        except Exception as exc:
            anti_leak_status = f"ERROR ({exc})"

        trap_desc = tag_descriptions.get(trap_tag, "")
        trap_tag_display = f"`{trap_tag}`" + (f" — *{trap_desc}*" if trap_desc else "")

        meta_rows = [
            f"| **Form** | `{form_name}` |",
            f"| **Level** | **L{level}** |",
            f"| **Skill ID** | `{skill}` |",
            f"| **Verification Level** | `{vlevel}` |",
            f"| **Step Count** | `{step_count}` steps |",
            f"| **Canonical Answer** | `{ans_plain}` |",
            f"| **Trap Value** | `{trap_value}` |",
            f"| **Learner Trap Tag** | {trap_tag_display} |",
        ]
        trap_derivation = prob.get("trapDerivation")
        td_eval = ""
        if trap_derivation:
            try:
                from math_engine.answer_check import to_expr
                td_eval = str(to_expr(trap_derivation, variables=prob.get("variables") or prob.get("answerSpec", {}).get("variables") or ["x"]))
            except Exception:
                td_eval = "err"
            meta_rows.append(f"| **Trap Derivation** | `{trap_derivation}` $\\implies$ `{td_eval}` |")
        if flaw_tag:
            flaw_desc = tag_descriptions.get(flaw_tag, "")
            flaw_display = f"`{flaw_tag}`" + (f" — *{flaw_desc}*" if flaw_desc else "")
            meta_rows.append(f"| **Flaw Tag (To Diagnose)** | {flaw_display} |")

        lines.extend([
            "",
            f"## Form {idx}/{len(forms_dict)}: `{form_name}`",
            "",
            "| Property | Value |",
            "| :--- | :--- |",
            *meta_rows,
            "",
            "### Problem Prompt",
            "",
            prompt,
        ])

        if display:
            disp_clean = str(display).strip()
            disp_str = disp_clean if disp_clean.startswith("$$") else f"$${disp_clean}$$"
            lines.extend([
                "",
                "### Display & Student Work",
                "",
                disp_str,
            ])

        if options:
            lines.extend([
                "",
                "### Options",
            ])
            for opt in options:
                opt_id = opt.get("id", "")
                opt_label = opt.get("label") or opt.get("text") or opt.get("value") or ""
                opt_trap = opt.get("trapTag") or opt.get("tag")
                trap_suffix = f" (Trap: `{opt_trap}`)" if opt_trap else ""
                lines.append(f"- `[{opt_id}]` {opt_label}{trap_suffix}")

        lines.extend([
            "",
            "### Learner Hints & Anti-Leak Validation",
            f"- **Input Hint (`inputHint`)**: `{input_hint}`",
            f"- **Checkpoint Hint (`checkpointHint`)**: `{checkpoint_hint}`",
            f"- **Anti-Leak Verification**: `{anti_leak_status}`",
        ])

        if code_snippet:
            lines.extend([
                "",
                f"```{code_language}",
                code_snippet.strip(),
                "```",
            ])

        lines.extend([
            "",
            "### Expected Answer & Provenance",
            f"- **Display Form**: `{ans_display}`",
            f"- **Plain/Eval Form**: `{ans_plain}`",
            f"- **Trap & Distractor Value**: `{trap_value}` (Tag: `{trap_tag}`{f' — {trap_desc}' if trap_desc else ''})",
        ])
        if trap_derivation:
            lines.append(f"- **Trap Derivation**: `{trap_derivation}` = `{td_eval}`")
        lines.extend([
            "",
            "### Step-by-Step Derivation",
        ])

        if not steps:
            lines.append("- *(No discrete steps provided)*")
        else:
            for s_idx, st in enumerate(steps, start=1):
                raw_expr = st.get("latex") or st.get("expr") or st.get("code") or st.get("source") or ""
                explain = st.get("explain", "")
                rule = st.get("rule", "")
                rule_str = f" *({rule})*" if rule else ""
                if raw_expr:
                    if raw_expr.startswith("$") or "\\text" in raw_expr or "\\" in raw_expr or "=" in raw_expr:
                        expr_fmt = f"${raw_expr}$" if not raw_expr.startswith("$") else raw_expr
                    else:
                        expr_fmt = f"`{raw_expr}`"
                    lines.append(f"{s_idx}. {expr_fmt} — {explain}{rule_str}")
                else:
                    lines.append(f"{s_idx}. {explain}{rule_str}")

        lines.extend([
            "",
            "---",
        ])

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate human-reviewable Markdown sample sheet for a template.")
    parser.add_argument("template_key", help="Key of template to inspect (e.g. cylinder-volume, find_bug_this_binding)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for deterministic generation (default: 42)")
    args = parser.parse_args()

    try:
        content = build_sample_sheet(args.template_key, seed=args.seed)
        print(content)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
