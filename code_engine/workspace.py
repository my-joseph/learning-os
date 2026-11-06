# -*- coding: utf-8 -*-
"""
Local Workspace Manager for VS Code / Cursor Integration.

Standardizes local workspace scaffolding for Real-World Engineering Drills:
- Standard folder: drills/workspace/<DRILL_ID>/
  ├── package.json         (scripts: "test": "node --test *.test.js", "test:q01", etc.)
  ├── README.md            (Scenario description, 6-Step Loop, Acceptance Criteria, AI PR Review guide)
  ├── <PID>_<name>.js      (Starter code / legacy code / buggy code with rich JSDoc & invariant contracts)
  ├── <PID>_<name>.test.js (Node native test runner suite verifying functional acceptance criteria)
  └── .canonical/          (Hidden canonical reference solutions for verification and self-study)

Generates one-click IDE deep links (cursor://file/... and vscode://file/...)
so developers can write and debug in their real IDE with full LSP, keybindings, and tools.
"""
import json
import os

ARCHETYPE_LABELS = {
    "problem-solving": "Problem Solving (Logic & Algorithm)",
    "debugging": "Debugging (Bug Triage & Root Cause)",
    "code-tracing": "Code Tracing (Mental Model & Flow)",
    "refactoring": "Refactoring (Clean Code & Safe Extensibility)",
    "project-based": "Project-Based (Multi-Module Architecture)",
}

COMPETENCY_LABELS = {
    "data-handling": "Data Handling",
    "state-management": "State Management",
    "component-design": "Component Design",
    "api-integration": "API Integration",
    "typescript": "TypeScript Typing",
    "architecture": "Architecture & Separation of Concerns",
    "performance": "Performance & Optimization",
}

ENVIRONMENT_PRESETS = {
    "node-vanilla": {
        "description": "Standard Node.js Native Runner (CommonJS/ESM)",
        "defaultExt": "js",
        "scripts": {
            "test": "node --test *.test.js",
            "test:watch": "node --test --watch *.test.js",
            "review": "python3 ../../../code_engine/review.py",
            "submit": "python3 ../../../code_engine/submit.py",
        },
        "devDependencies": {},
    },
    "typescript-strict": {
        "description": "Strict TypeScript Native Runner with Typecheck Check",
        "defaultExt": "ts",
        "scripts": {
            "test": "node --experimental-strip-types --test *.test.ts",
            "test:watch": "node --experimental-strip-types --test --watch *.test.ts",
            "typecheck": "tsc --noEmit",
            "review": "python3 ../../../code_engine/review.py",
            "submit": "python3 ../../../code_engine/submit.py",
        },
        "devDependencies": {
            "typescript": "^5.0.0",
            "@types/node": "^20.0.0",
        },
    },
    "react-dom": {
        "description": "React Component & Custom Hook Environment (Vitest / React Testing Library)",
        "defaultExt": "tsx",
        "scripts": {
            "test": "vitest run",
            "test:watch": "vitest",
            "review": "python3 ../../../code_engine/review.py",
            "submit": "python3 ../../../code_engine/submit.py",
        },
        "devDependencies": {
            "vitest": "^1.3.0",
            "@testing-library/react": "^14.2.0",
            "@testing-library/react-hooks": "^8.0.1",
            "jsdom": "^24.0.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
        },
    },
    "backend-sqlite": {
        "description": "Backend Database & Transaction Environment with In-Memory SQLite",
        "defaultExt": "ts",
        "scripts": {
            "test": "node --experimental-strip-types --test *.test.ts",
            "test:watch": "node --experimental-strip-types --test --watch *.test.ts",
            "review": "python3 ../../../code_engine/review.py",
            "submit": "python3 ../../../code_engine/submit.py",
        },
        "devDependencies": {
            "better-sqlite3": "^9.4.0",
            "@types/better-sqlite3": "^7.6.9",
            "@types/node": "^20.0.0",
        },
    },
}


def get_entry_name(prob: dict) -> str:
    entry = prob.get("entryPoint")
    if entry:
        return entry
    pid = prob.get("id", "code")
    return pid.lower()


def get_problem_archetype(prob: dict) -> str:
    if prob.get("archetype"):
        return prob["archetype"]
    ctype = prob.get("codeType", "")
    if ctype in ("debugging", "find-bug"):
        return "debugging"
    if ctype in ("code-tracing", "predict-output"):
        return "code-tracing"
    if ctype in ("refactoring", "refactor"):
        return "refactoring"
    if ctype in ("project-based",):
        return "project-based"
    return "problem-solving"


def build_starter_header(prob: dict, drill_id: str) -> str:
    pid = prob.get("id", "Q01")
    archetype = get_problem_archetype(prob)
    archetype_title = ARCHETYPE_LABELS.get(archetype, archetype.upper())
    competencies = prob.get("competencies", [])
    comp_str = ", ".join(COMPETENCY_LABELS.get(c, c) for c in competencies) if competencies else "Engineering Fundamentals"
    prompt = prob.get("prompt", "")

    header = f"""/**
 * ============================================================================
 * [{drill_id}] {pid}: {archetype_title}
 * Target Competencies: {comp_str}
 * ============================================================================
 * 
 * 6-STEP PEDAGOGICAL PRACTICE LOOP:
 * 1. คิดเองก่อนเขียน : Sketch invariants, mental model, and boundary edge cases.
 * 2. ลงมือทำ         : Write your implementation in this file.
 * 3. ทดสอบ           : Run `npm test` or `npm run test:{pid.lower()}` in this folder.
 * 4. อธิบายโค้ด      : Explain the algorithm and request an AI Senior Tech Lead PR Review.
 * 5. Refactor        : Decouple helpers, improve readability, and optimize performance.
 * 6. เพิ่มความยาก     : Scale up test inputs and handle harsher stress scenarios.
 * 
 * SPECIFICATION:
 * {prompt}
 * ============================================================================
 */
"""
    return header


def materialize_drill_workspace(drill_doc: dict, root_dir: str = ".") -> dict:
    drill_id = drill_doc.get("drillId", "UNKNOWN_DRILL")
    unit_code = drill_doc.get("unitCode", "PRG")
    unit_title = drill_doc.get("unitTitle", "Programming Practice")
    preset_key = drill_doc.get("environment", "node-vanilla")
    preset = ENVIRONMENT_PRESETS.get(preset_key, ENVIRONMENT_PRESETS["node-vanilla"])
    ext = preset.get("defaultExt", "js")

    ws_dir = os.path.join(root_dir, "drills", "workspace", drill_id)
    canonical_dir = os.path.join(ws_dir, ".canonical")
    os.makedirs(ws_dir, exist_ok=True)
    os.makedirs(canonical_dir, exist_ok=True)

    manifest = {
        "drillId": drill_id,
        "environment": preset_key,
        "workspaceDir": os.path.abspath(ws_dir),
        "files": {},
    }

    test_scripts = dict(preset["scripts"])
    readme_problems = []

    for prob in drill_doc.get("problems", []):
        ctype = prob.get("codeType")
        archetype = get_problem_archetype(prob)
        is_code = (
            ctype in ("kata", "implement", "refactor", "problem-solving", "debugging", "code-tracing", "refactoring", "project-based")
            or bool(prob.get("visibleTests"))
            or bool(prob.get("starterCode"))
        )
        if not is_code:
            continue

        pid = prob.get("id", "Q01")
        entry_name = get_entry_name(prob)
        src_filename = f"{pid}_{entry_name}.{ext}"
        test_filename = f"{pid}_{entry_name}.test.{ext}"
        canonical_filename = f"{pid}_{entry_name}.{ext}"

        src_path = os.path.join(ws_dir, src_filename)
        test_path = os.path.join(ws_dir, test_filename)
        canonical_path = os.path.join(canonical_dir, canonical_filename)

        # 1. Author Starter Code
        starter_body = prob.get("starterCode") or f"function {entry_name}() {{\n  // TODO: implement\n}}\n\nmodule.exports = {{ {entry_name} }};\n"
        if not starter_body.strip().startswith("/**"):
            starter_content = build_starter_header(prob, drill_id) + "\n" + starter_body.strip() + "\n"
        else:
            starter_content = starter_body.strip() + "\n"

        if not os.path.exists(src_path):
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(starter_content)

        # 2. Write Canonical Reference Solution if available
        sol_code = prob.get("solutionCode")
        if sol_code:
            with open(canonical_path, "w", encoding="utf-8") as f:
                f.write(sol_code.strip() + "\n")

        # 3. Write Visible Test File
        test_blocks = []
        for idx, t in enumerate(prob.get("visibleTests", []), 1):
            t_name = json.dumps(f"[{pid}-T{idx:02d}] " + t.get("name", f"scenario {idx}"))
            t_code = t.get("testCode", "").strip()
            test_blocks.append(f"""
test({t_name}, async () => {{
  {t_code}
}});
""")

        test_header = f"// Auto-generated visible test suite for {drill_id} {pid}\n"
        if preset_key in ("typescript-strict", "backend-sqlite"):
            test_header += "import test from 'node:test';\nimport assert from 'node:assert';\n"
            test_header += f"import {{ {entry_name} }} from './{src_filename}';\n\n"
        else:
            test_header += f"const test = require('node:test');\nconst assert = require('node:assert');\nconst {{ {entry_name} }} = require('./{src_filename}');\n\n"

        test_content = test_header + "".join(test_blocks)
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_content.strip() + "\n")

        # 4. Write Hidden Trap Tests (Anti-Cheat / Advanced Boundary Invariants)
        hidden_tests = prob.get("hiddenTests", [])
        if hidden_tests:
            hidden_blocks = []
            for idx, ht in enumerate(hidden_tests, 1):
                ht_name = json.dumps(f"[{pid}-HIDDEN-T{idx:02d}] " + ht.get("name", f"hidden trap scenario {idx}"))
                ht_code = ht.get("testCode", "").strip()
                hidden_blocks.append(f"""
test({ht_name}, async () => {{
  {ht_code}
}});
""")
            hidden_header = f"// Hidden Trap Test Suite for {drill_id} {pid}\n"
            if preset_key in ("typescript-strict", "backend-sqlite"):
                hidden_header += "import test from 'node:test';\nimport assert from 'node:assert';\n"
                hidden_header += f"import {{ {entry_name} }} from '../{src_filename}';\n\n"
            else:
                hidden_header += f"const test = require('node:test');\nconst assert = require('node:assert');\nconst {{ {entry_name} }} = require('../{src_filename}');\n\n"

            hidden_test_path = os.path.join(canonical_dir, f"{pid}_{entry_name}.hidden.test.{ext}")
            with open(hidden_test_path, "w", encoding="utf-8") as f:
                f.write((hidden_header + "".join(hidden_blocks)).strip() + "\n")

        # Register npm test script per problem
        if preset_key == "react-dom":
            test_scripts[f"test:{pid.lower()}"] = f"vitest run {test_filename}"
        elif preset_key in ("typescript-strict", "backend-sqlite"):
            test_scripts[f"test:{pid.lower()}"] = f"node --experimental-strip-types --test {test_filename}"
        else:
            test_scripts[f"test:{pid.lower()}"] = f"node --test {test_filename}"

        abs_src = os.path.abspath(src_path)
        abs_ws = os.path.abspath(ws_dir)
        manifest["files"][pid] = {
            "sourcePath": abs_src,
            "testPath": os.path.abspath(test_path),
            "cursorUrl": f"cursor://file/{abs_src}",
            "vscodeUrl": f"vscode://file/{abs_src}",
            "cursorFolderUrl": f"cursor://file/{abs_ws}",
            "vscodeFolderUrl": f"vscode://file/{abs_ws}",
            "relativeSrc": os.path.join("drills", "workspace", drill_id, src_filename),
        }

        prob["workspaceFile"] = os.path.join("drills", "workspace", drill_id, src_filename)
        prob["workspaceDir"] = abs_ws
        prob["cursorUrl"] = f"cursor://file/{abs_src}"
        prob["vscodeUrl"] = f"vscode://file/{abs_src}"
        prob["cursorFolderUrl"] = f"cursor://file/{abs_ws}"
        prob["vscodeFolderUrl"] = f"vscode://file/{abs_ws}"
        prob["archetype"] = archetype

        readme_problems.append({
            "pid": pid,
            "entry": entry_name,
            "src": src_filename,
            "test": test_filename,
            "archetype": ARCHETYPE_LABELS.get(archetype, archetype),
            "prompt": prob.get("prompt", ""),
            "criteria_count": len(prob.get("visibleTests", [])),
            "hidden_count": len(hidden_tests),
        })

    # 4. Write package.json in workspace
    pkg_json_path = os.path.join(ws_dir, "package.json")
    pkg_data = {
        "name": f"{drill_id.lower()}-workspace",
        "version": "1.0.0",
        "private": True,
        "description": f"Local IDE Workspace for {drill_id} ({unit_code} - {unit_title}) [{preset_key}]",
        "scripts": test_scripts,
        "devDependencies": preset.get("devDependencies", {}),
    }
    with open(pkg_json_path, "w", encoding="utf-8") as f:
        json.dump(pkg_data, f, indent=2)
        f.write("\n")

    # 5. Write README.md in workspace
    readme_path = os.path.join(ws_dir, "README.md")
    readme_lines = [
        f"# {drill_id} — {unit_code}: {unit_title}",
        "",
        f"> **Environment Preset:** `{preset_key}` — {preset['description']}",
        "> **100% Local IDE Mandate**: All problem solving, refactoring, and debugging must be performed natively in your IDE (VS Code / Cursor).",
        "",
        "## Universal 6-Step Pedagogical Practice Loop",
        "1. **คิดเองก่อนเขียน (Mental Model)**: Review the Acceptance Criteria and boundary traps before typing.",
        "2. **ลงมือทำ (Local IDE)**: Open the source file in VS Code or Cursor and implement the logic.",
        "3. **ทดสอบ (Automated Acceptance Testing)**: Run `npm test` or `npm run test:<qid>` in this directory.",
        "4. **อธิบายโค้ด (AI Senior Lead PR Review)**: Articulate your algorithm and request an AI Senior Tech Lead architectural review.",
        "5. **Refactor (Clean Architecture)**: Decouple helpers, clean code smells, and optimize hot paths while keeping tests green.",
        "6. **เพิ่มความยาก (Progression)**: Scale up test inputs and edge cases.",
        "",
        "## Quick Terminal Commands",
        "```bash",
        "# Run all acceptance test suites in this workspace",
        "npm test",
        "",
        "# Run tests in watch mode while editing",
        "npm run test:watch",
        "",
        "# Run tests for a specific question",
        "npm run test:q01",
        "",
        "# Request Senior Tech Lead AI PR Review (packages code & copies prompt to clipboard)",
        "npm run review",
        "npm run review q01",
        "",
        "# Grade all exercises (runs visible + hidden trap tests) and sync to Notion",
        "npm run submit",
        "```",
        "",
        "## Exercises in this Workspace",
        "",
    ]

    for p in readme_problems:
        scenario_str = f"{p['criteria_count']} visible scenarios"
        if p.get("hidden_count"):
            scenario_str += f" (+ {p['hidden_count']} hidden trap tests)"
        readme_lines.extend([
            f"### {p['pid']} — `{p['src']}`",
            f"- **Archetype:** {p['archetype']}",
            f"- **Acceptance Scenarios:** {scenario_str} in `{p['test']}`",
            f"- **Requirement:** {p['prompt']}",
            f"- **Run Single Suite:** `npm run test:{p['pid'].lower()}`",
            "",
        ])

    readme_lines.extend([
        "## Requesting an AI Architectural Review",
        "Once your automated acceptance tests pass 100%, copy this prompt and ask Antigravity / Cursor AI:",
        "```text",
        f"Please act as a Senior Tech Lead and conduct an Architecture & Code Craftsmanship Review on my implementation in `{drill_id}`.",
        "Evaluate my code across:",
        "1. Separation of Concerns & Clean Code standards",
        "2. State Management & Data Handling invariants",
        "3. TypeScript typing / JSDoc precision and edge case resilience",
        "4. Performance hot paths, algorithmic complexity, and decoupling suggestions",
        "```",
        "",
    ])

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(readme_lines))

    return manifest


def read_workspace_code(abs_or_rel_path: str) -> str:
    if os.path.exists(abs_or_rel_path):
        with open(abs_or_rel_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""
