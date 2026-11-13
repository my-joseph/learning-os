# -*- coding: utf-8 -*-
"""
AI Senior Tech Lead PR Review Engine (Phase 3)

Generates a structured, production-grade Code Review Request document
(PR_REVIEW_REQUEST.md) from the current workspace (Drill or Project Lab),
packages execution telemetry, user code, acceptance invariants,
and copies the formatted prompt to the system clipboard for immediate
in-editor AI review (Antigravity / Cursor / Claude chat).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

# ANSI Terminal Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def copy_to_clipboard(text: str) -> bool:
    """Copies text to system clipboard using pbcopy (macOS) or xclip/xsel (Linux)."""
    if sys.platform == "darwin" and shutil.which("pbcopy"):
        try:
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
            return proc.returncode == 0
        except Exception:
            return False
    elif shutil.which("xclip"):
        try:
            proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
            return proc.returncode == 0
        except Exception:
            return False
    return False


def run_tests_summary(cwd: Path) -> dict:
    """Executes local test suite and captures brief summary and errors."""
    pkg_json = cwd / "package.json"
    if not pkg_json.exists():
        return {"status": "Unknown", "output": "No package.json found"}

    try:
        proc = subprocess.run(
            ["npm", "test"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        combined = proc.stdout + "\n" + proc.stderr
        passed = proc.returncode == 0

        # Extract summary lines
        lines = [line.strip() for line in combined.splitlines() if line.strip()]
        summary_lines = [l for l in lines if l.startswith("ℹ") or "pass" in l.lower() or "fail" in l.lower()]

        return {
            "passed": passed,
            "returncode": proc.returncode,
            "summary": "\n".join(summary_lines[-5:])
            if summary_lines
            else ("All tests passed" if passed else "Tests failed"),
            "raw_output": combined,
        }
    except Exception as e:
        return {"passed": False, "returncode": -1, "summary": f"Failed to execute tests: {e}", "raw_output": str(e)}


def build_drill_review(ws_dir: Path, target_pid: str = None) -> tuple[str, str]:
    """Builds PR review prompt for a Drill Workspace (drills/workspace/<DRILL_ID>)."""
    drill_id = ws_dir.name
    readme_file = ws_dir / "README.md"
    readme_text = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

    # Find JS problem files in workspace (ignoring .test.js)
    src_files = sorted([f for f in ws_dir.glob("*.js") if not f.name.endswith(".test.js")])
    if target_pid:
        filtered = [f for f in src_files if target_pid.lower() in f.name.lower()]
        if filtered:
            src_files = filtered

    test_res = run_tests_summary(ws_dir)
    test_badge = "✅ ALL TESTS GREEN" if test_res["passed"] else "⚠️ SOME TESTS FAILING / PENDING"

    code_sections = []
    for sf in src_files:
        content = sf.read_text(encoding="utf-8")
        code_sections.append(f"### File: `{sf.name}`\n```javascript\n{content}\n```")

    doc = f"""# Senior Tech Lead Code Review Request: `{drill_id}`

> **Target Workspace:** `{ws_dir.resolve()}`  
> **Test Status:** {test_badge}  
> **Sub-components Under Review:** {", ".join(f"`{f.name}`" for f in src_files)}  

---

## 1. Test Suite Execution Telemetry
```text
{test_res["summary"]}
```

---

## 2. Implementation Code Submitted for Review

{"\n\n".join(code_sections)}

---

## 3. Senior Tech Lead Review Rubrics

Please review my implementation above acting as a **Senior Staff Engineer / Tech Lead**. Conduct a rigorous, constructive Architectural & Code Craftsmanship review evaluated across the following 5 dimensions:

1. **Architecture & Separation of Concerns**:
   - Is the business logic cleanly separated from I/O and state mutations?
   - Are function responsibilities focused (Single Responsibility Principle)?

2. **Defensive Invariants & Edge Case Resilience**:
   - Are boundary conditions (null, undefined, 0, empty array, floating point precision) guarded defensively?
   - Are domain exceptions thrown with meaningful types (`RangeError`, `TypeError`)?

3. **Readability & Craftsmanship (Clean Code)**:
   - Are variable and function names intention-revealing?
   - Is there unnecessary duplication or overly clever premature abstraction?

4. **Performance & Complexity ($O(N)$ Invariants)**:
   - What are the Time and Space complexity of the critical paths?
   - Are there hidden performance traps (e.g. repeated array scans inside loops, unnecessary memory allocations)?

5. **Actionable Recommendations & Refactored Blueprint**:
   - Highlight 1-2 things done well.
   - Point out 1-2 concrete code smells or fragility traps.
   - Provide a clean, production-grade refactored code snippet illustrating the recommended improvements.
"""
    return doc, f"{drill_id} ({len(src_files)} files)"


def build_lab_review(ws_dir: Path) -> tuple[str, str]:
    """Builds PR review prompt for a Project Lab (labs/LAB-xxx)."""
    config_file = ws_dir / "lab.config.json"
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    lab_id = config.get("labId", ws_dir.name)
    title = config.get("title", lab_id)
    milestones = config.get("milestones", [])

    src_dir = ws_dir / "src"
    src_files = sorted(list(src_dir.glob("*.ts")) + list(src_dir.glob("*.js"))) if src_dir.exists() else []

    test_res = run_tests_summary(ws_dir)
    test_badge = "✅ ALL MILESTONES GREEN" if test_res["passed"] else "⚠️ INCOMPLETE / FAILING MILESTONES"

    ms_list = []
    for ms in milestones:
        ms_list.append(
            f"- **[{ms['id']}] {ms['title']}** ({ms['points']} pts) — *Mistake Trap:* `{ms.get('mistakeCategory', 'General')}`"
        )

    code_sections = []
    for sf in src_files:
        content = sf.read_text(encoding="utf-8")
        code_sections.append(f"### Module: `src/{sf.name}`\n```typescript\n{content}\n```")

    doc = f"""# Senior Tech Lead Architecture & PR Review: `{lab_id}` — {title}

> **Target Lab:** `{lab_id}`: {title}  
> **Workspace Directory:** `{ws_dir.resolve()}`  
> **Milestone Test Status:** {test_badge}  
> **Architecture Scope:** Multi-tier synthesized domain engine ({len(src_files)} modules)  

---

## 1. Architectural Milestones Under Evaluation
{"\n".join(ms_list)}

---

## 2. Test Execution Telemetry
```text
{test_res["summary"]}
```

---

## 3. Submitted Source Code Modules

{"\n\n".join(code_sections)}

---

## 4. Senior Staff Engineer Review Mandate

Please review this full-stack domain architecture acting as our **Principal Software Architect & Tech Lead**. Evaluate this codebase according to enterprise production standards:

1. **Domain-Driven Design & Schema Integrity**:
   - Are schemas, types, and domain invariants strictly validated at the boundaries?
   - Is invalid or corrupted data prevented from leaking into domain entities?

2. **Business Rule Correctness & Financial Safety**:
   - Are monetary calculations (discounts, cents, rounding) safe from floating-point inaccuracies?
   - Are boundary conditions (zero quantity, negative prices, coupon thresholds) completely sound?

3. **State Machine Consistency & Concurrency Protection**:
   - Are state transitions strictly guarded against illegal shortcuts or race conditions?
   - In concurrent operations, are resources locked and safely rolled back upon failure?

4. **Production Readiness, Clean Architecture & Extensibility**:
   - Is error handling consistent across services?
   - How easily could a new feature or payment provider be added without breaking existing contracts?

5. **Verdict & Senior Recommendations**:
   - **Architecture Grade:** (e.g., Production-Ready, Needs Hardening, Critical Flaws Found)
   - **Top 2 Architectural Strengths:** What design patterns were executed cleanly?
   - **Critical Vulnerabilities / Smells:** What would fail under high production load?
   - **Refactored Blueprint:** Concrete code improvements for the weakest component.
"""
    return doc, f"{lab_id}: {title}"


def main():
    ws_dir = Path.cwd()
    target_arg = None
    for arg in sys.argv[1:]:
        if arg.startswith("--target="):
            target_arg = arg.split("=", 1)[1]
        elif not arg.startswith("-"):
            target_arg = arg

    # Detect whether this is a Lab or a Drill Workspace
    is_lab = (ws_dir / "lab.config.json").exists()

    if is_lab:
        review_text, target_label = build_lab_review(ws_dir)
    else:
        review_text, target_label = build_drill_review(ws_dir, target_arg)

    output_path = ws_dir / "PR_REVIEW_REQUEST.md"
    output_path.write_text(review_text, encoding="utf-8")

    copied = copy_to_clipboard(review_text)

    print(f"\n{BOLD}{CYAN}========================================================================={RESET}")
    print(f"{BOLD}  AI SENIOR TECH LEAD PR REVIEW GENERATOR (Phase 3){RESET}")
    print(f"{DIM}  Target: {target_label}{RESET}")
    print(f"{BOLD}{CYAN}========================================================================={RESET}\n")

    print(f"{GREEN}✔ Successfully generated review request document:{RESET}")
    print(f"  📄 {CYAN}{output_path.resolve()}{RESET}\n")

    if copied:
        print(f"{GREEN}✔ Prompt copied to your system clipboard!{RESET} (macOS pbcopy)")
    else:
        print(f"{YELLOW}ℹ Note: Could not auto-copy to clipboard. File saved to disk.{RESET}")

    print(f"\n{BOLD}HOW TO SUBMIT TO YOUR AI SENIOR TECH LEAD IN CURSOR / ANTIGRAVITY:{RESET}")
    print(f"  1. Press {CYAN}Cmd + L{RESET} to open your AI Assistant Chat panel.")
    print(f"  2. Paste directly: {CYAN}Cmd + V{RESET} (the full review request is in your clipboard).")
    print(f"     {DIM}— OR —{RESET}")
    print(f"  3. Tag the file in chat: {CYAN}@PR_REVIEW_REQUEST.md{RESET} and ask:")
    print(f'     {BOLD}"Please conduct the Senior Tech Lead Review on this PR."{RESET}\n')
    print(f"{BOLD}{CYAN}========================================================================={RESET}\n")


if __name__ == "__main__":
    main()
