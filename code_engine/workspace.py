# -*- coding: utf-8 -*-
"""
Local Workspace Manager for VS Code / Cursor Integration.

Standardizes local workspace scaffolding for Real-World Engineering Drills:
- Standard folder: drills/workspace/<DRILL_ID>/
  ├── package.json         (scripts: "test": "node --test *.test.js", "test:q01", etc.)
  ├── README.md            (Scenario description, 6-Step Loop, Acceptance Criteria, AI PR Review guide)
  ├── <PID>_<name>.js      (Starter code / legacy code / buggy code with rich JSDoc & invariant contracts)
  └── <PID>_<name>.test.js (Node native test runner suite verifying functional acceptance criteria)

Generates one-click IDE deep links (cursor://file/... and vscode://file/...)
so developers can write and debug in their real IDE with full LSP, keybindings, and tools.
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

from progress_store import pilot_mode, workspace_root

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
            "test": "node --test --test-reporter=spec *.test.js",
            "test:watch": "node --test --watch *.test.js",
            "lint": "../../../tools/lint/node_modules/.bin/eslint --format ../../../tools/lint/format.js .",
            "check": "npm test; test_status=$?; npm run lint; lint_status=$?; test $test_status -eq 0 -a $lint_status -eq 0",
            "review": "../../../.venv/bin/python -m code_engine.review",
            "submit": "../../../.venv/bin/python -m code_engine.submit",
        },
        "devDependencies": {},
    },
    "typescript-strict": {
        "description": "Strict TypeScript Native Runner with Typecheck Check",
        "defaultExt": "ts",
        "scripts": {
            "test": "node --experimental-strip-types --test --test-reporter=spec *.test.ts",
            "test:watch": "node --experimental-strip-types --test --watch *.test.ts",
            "lint": "../../../tools/lint/node_modules/.bin/eslint --format ../../../tools/lint/format.js .",
            "typecheck": "../../../tools/lint/node_modules/.bin/tsc --noEmit",
            "check": "npm test; test_status=$?; npm run lint; lint_status=$?; npm run typecheck; type_status=$?; test $test_status -eq 0 -a $lint_status -eq 0 -a $type_status -eq 0",
            "review": "../../../.venv/bin/python -m code_engine.review",
            "submit": "../../../.venv/bin/python -m code_engine.submit",
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
            "test": "../../../tools/lint/node_modules/.bin/vitest run --environment jsdom",
            "test:watch": "../../../tools/lint/node_modules/.bin/vitest --environment jsdom",
            "lint": "../../../tools/lint/node_modules/.bin/eslint --format ../../../tools/lint/format.js .",
            "typecheck": "../../../tools/lint/node_modules/.bin/tsc --noEmit",
            "check": "npm test; test_status=$?; npm run lint; lint_status=$?; npm run typecheck; type_status=$?; test $test_status -eq 0 -a $lint_status -eq 0 -a $type_status -eq 0",
            "review": "../../../.venv/bin/python -m code_engine.review",
            "submit": "../../../.venv/bin/python -m code_engine.submit",
        },
        "devDependencies": {"@types/node": "^20.0.0"},
    },
    "backend-sqlite": {
        "description": "Backend Database & Transaction Environment with In-Memory SQLite",
        "defaultExt": "ts",
        "scripts": {
            "test": "node --experimental-strip-types --test --test-reporter=spec *.test.ts",
            "test:watch": "node --experimental-strip-types --test --watch *.test.ts",
            "lint": "../../../tools/lint/node_modules/.bin/eslint --format ../../../tools/lint/format.js .",
            "typecheck": "../../../tools/lint/node_modules/.bin/tsc --noEmit",
            "check": "npm test; test_status=$?; npm run lint; lint_status=$?; npm run typecheck; type_status=$?; test $test_status -eq 0 -a $lint_status -eq 0 -a $type_status -eq 0",
            "review": "../../../.venv/bin/python -m code_engine.review",
            "submit": "../../../.venv/bin/python -m code_engine.submit",
        },
        "devDependencies": {
            "better-sqlite3": "^9.4.0",
            "@types/better-sqlite3": "^7.6.9",
            "@types/node": "^20.0.0",
        },
    },
}


_COMMENT_OR_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`|//[^\n]*|/\*[\s\S]*?\*/')
_IDENT_RE = re.compile(r"^[A-Za-z_$][\w$]*$")


def _strip_js_comments(code: str) -> str:
    """Remove JS/TS line and block comments while preserving string/template literals."""
    return _COMMENT_OR_STRING_RE.sub(lambda m: m.group(0) if m.group(0)[0] in ('"', "'", "`") else "", code)


def _extract_object_keys(body: str) -> list[str]:
    """Extract top-level property/shorthand identifier names from an object literal body."""
    keys: list[str] = []
    depth = 0
    in_str: str | None = None
    escaped = False
    start = 0
    parts: list[str] = []
    for idx, ch in enumerate(body):
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in ('"', "'", "`"):
            in_str = ch
        elif ch in ("{", "(", "["):
            depth += 1
        elif ch in ("}", ")", "]"):
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            parts.append(body[start:idx])
            start = idx + 1
    parts.append(body[start:])

    for part in parts:
        token = part.strip()
        if not token or token.startswith("..."):
            continue
        head = token.split(":", 1)[0].split("=", 1)[0].strip()
        if _IDENT_RE.match(head):
            keys.append(head)
    return keys


def extract_exports(code: str) -> list[str]:
    """Extract exported symbol names from CommonJS (`module.exports`/`exports.x`) and ESM (`export ...`)."""
    if not code:
        return []
    clean = _strip_js_comments(code)
    found: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        if name and _IDENT_RE.match(name) and name not in seen:
            seen.add(name)
            found.append(name)

    # 1. CommonJS: module.exports = { ... }
    for m in re.finditer(r"\bmodule\.exports\s*=\s*\{", clean):
        brace_start = m.end() - 1
        depth = 0
        in_str: str | None = None
        escaped = False
        brace_end = -1
        for idx in range(brace_start, len(clean)):
            ch = clean[idx]
            if in_str:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == in_str:
                    in_str = None
                continue
            if ch in ('"', "'", "`"):
                in_str = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    brace_end = idx
                    break
        if brace_end != -1:
            for key in _extract_object_keys(clean[brace_start + 1 : brace_end]):
                _add(key)

    # 2. CommonJS: module.exports.foo = ... / exports.foo = ...
    for m in re.finditer(r"(?:^|[;\n])\s*(?:module\.)?exports\.([A-Za-z_$][\w$]*)\s*=", clean):
        _add(m.group(1))

    # 3. ESM: export [async] function[*] foo / export (const|let|var|class|enum) foo
    for m in re.finditer(
        r"(?:^|[;\n])\s*export\s+(?:(?:async\s+)?function\*?|const|let|var|class|enum)\s+([A-Za-z_$][\w$]*)",
        clean,
    ):
        _add(m.group(1))

    # 4. ESM: export { a, b as c } (skip `export type { ... }`)
    for m in re.finditer(r"(?:^|[;\n])\s*export\s*\{([^}]*)\}", clean):
        for item in m.group(1).split(","):
            tok = item.strip()
            if not tok or tok.startswith("type "):
                continue
            if " as " in tok:
                _, alias = tok.rsplit(" as ", 1)
                _add(alias.strip())
            else:
                _add(tok)

    return found


def resolve_test_imports(prob: dict, test_code: str, src_path: Path | None = None) -> list[str]:
    """Return exported symbols from starter/solution/source that are referenced in `test_code`."""
    candidates: list[str] = []
    seen: set[str] = set()
    sources: list[str] = [
        prob.get("solutionCode") or "",
        (prob.get("verify") or {}).get("solutionCode") or "",
        prob.get("starterCode") or "",
    ]
    if src_path is not None and src_path.is_file():
        sources.append(src_path.read_text(encoding="utf-8"))

    for src in sources:
        for name in extract_exports(src):
            if name not in seen:
                seen.add(name)
                candidates.append(name)

    referenced = [name for name in candidates if re.search(rf"\b{re.escape(name)}\b", test_code)]
    if referenced:
        return referenced
    return [get_entry_name(prob)]


def build_react_test_header(import_list: str, test_code: str, source_import: str) -> str:
    """Build the minimal shared imports needed by a Vitest/Testing Library suite."""
    lines = ["import { afterEach, test } from 'vitest';"]
    if re.search(r"\bassert\s*\.", test_code):
        lines.append("import assert from 'node:assert';")
    helpers = [
        name for name in ("render", "screen", "fireEvent", "waitFor", "act") if re.search(rf"\b{name}\b", test_code)
    ]
    if "cleanup" not in helpers:
        helpers.append("cleanup")
    lines.append(f"import {{ {', '.join(helpers)} }} from '@testing-library/react';")
    if re.search(r"\buserEvent\b", test_code):
        lines.append("import userEvent from '@testing-library/user-event';")
    if re.search(r"\bReact\.", test_code):
        lines.append("import React from 'react';")
    if import_list:
        lines.append(f"import {{ {import_list} }} from {json.dumps(source_import)};")
    lines.append("afterEach(() => cleanup());")
    return "\n".join(lines) + "\n\n"


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
    comp_str = (
        ", ".join(COMPETENCY_LABELS.get(c, c) for c in competencies) if competencies else "Engineering Fundamentals"
    )
    prompt = prob.get("prompt", "")

    header = f"""/**
 * ============================================================================
 * [{drill_id}] {pid}: {archetype_title}
 * Target Competencies: {comp_str}
 * ============================================================================
 * 
 * 6-STEP PEDAGOGICAL PRACTICE LOOP:
 * 1. Think Before Coding : Sketch invariants, mental model, and boundary edge cases.
 * 2. Implement           : Write your implementation in this file.
 * 3. Test                : Run `npm test` or `npm run test:{pid.lower()}` in this folder.
 * 4. Explain Code        : Explain the algorithm and request an AI Senior Tech Lead PR Review.
 * 5. Refactor            : Decouple helpers, improve readability, and optimize performance.
 * 6. Scale Difficulty    : Scale up test inputs and handle harsher stress scenarios.
 * 
 * SPECIFICATION:
 * {prompt.replace(chr(10), chr(10) + " * ")}
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

    # Workspace scripts/configs use stable relative paths from the repo root.
    # When callers materialize into an external root (for tests or a custom
    # workspace), expose the shared lint toolkit at that same relative path.
    external_root = Path(root_dir).resolve()
    shared_lint = Path(__file__).resolve().parents[1] / "tools" / "lint"
    local_lint = external_root / "tools" / "lint"
    if local_lint.is_symlink() and not local_lint.exists():
        local_lint.unlink()
    if not local_lint.exists() and not local_lint.is_symlink():
        local_lint.parent.mkdir(parents=True, exist_ok=True)
        local_lint.symlink_to(shared_lint, target_is_directory=True)

    ws_base = os.path.join("pilot", "workspace") if pilot_mode() else os.path.join("drills", "workspace")
    ws_dir = os.path.join(workspace_root(root_dir), drill_id)
    os.makedirs(ws_dir, exist_ok=True)
    if preset_key == "react-dom":
        shared_node_modules = Path(__file__).resolve().parents[1] / "tools" / "lint" / "node_modules"
        if shared_node_modules.is_dir():
            modules_link = Path(ws_dir) / "node_modules"
            if modules_link.is_symlink() and modules_link.resolve() != shared_node_modules.resolve():
                modules_link.unlink()
            if not modules_link.exists() and not modules_link.is_symlink():
                modules_link.symlink_to(shared_node_modules, target_is_directory=True)
    package_link = os.path.join(ws_dir, "code_engine")
    if not os.path.lexists(package_link):
        os.symlink(str(Path(__file__).resolve().parent), package_link, target_is_directory=True)
    stale_canonical = os.path.join(ws_dir, ".canonical")
    if os.path.exists(stale_canonical):
        shutil.rmtree(stale_canonical)

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
            ctype
            in (
                "kata",
                "implement",
                "refactor",
                "problem-solving",
                "debugging",
                "code-tracing",
                "refactoring",
                "project-based",
            )
            or bool(prob.get("visibleTests"))
            or bool(prob.get("starterCode"))
        )
        if not is_code:
            continue

        pid = prob.get("id", "Q01")
        entry_name = get_entry_name(prob)
        src_filename = f"{pid}_{entry_name}.{ext}"
        test_filename = f"{pid}_{entry_name}.test.{ext}"
        src_path = os.path.join(ws_dir, src_filename)
        test_path = os.path.join(ws_dir, test_filename)

        # 1. Author Starter Code
        starter_body = (
            prob.get("starterCode")
            or f"function {entry_name}() {{\n  // TODO: implement\n}}\n\nmodule.exports = {{ {entry_name} }};\n"
        )
        if not starter_body.strip().startswith("/**"):
            starter_content = build_starter_header(prob, drill_id) + "\n" + starter_body.strip() + "\n"
        else:
            starter_content = starter_body.strip() + "\n"

        if not os.path.exists(src_path):
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(starter_content)

        # 2. Write Visible Test File
        test_blocks = []
        for idx, t in enumerate(prob.get("visibleTests", []), 1):
            t_name = json.dumps(f"[{pid}-T{idx:02d}] " + t.get("name", f"scenario {idx}"))
            t_code = t.get("testCode", "").strip()
            fn_prefix = "async () =>" if re.search(r"\bawait\b", t_code) else "() =>"
            test_blocks.append(f"""
test({t_name}, {fn_prefix} {{
  {t_code}
}});
""")

        visible_code = "\n".join(t.get("testCode", "") for t in prob.get("visibleTests", []))
        import_names = resolve_test_imports(prob, visible_code, src_path=Path(src_path))
        import_list = ", ".join(import_names)

        test_header = f"// Auto-generated visible test suite for {drill_id} {pid}\n"
        if preset_key in ("typescript-strict", "backend-sqlite"):
            test_header += "import test from 'node:test';\nimport assert from 'node:assert';\n"
            test_header += f"import {{ {import_list} }} from './{src_filename}';\n\n"
        elif preset_key == "react-dom":
            test_header += build_react_test_header(import_list, visible_code, f"./{src_filename}")
        else:
            test_header += (
                "const test = require('node:test');\n"
                "const assert = require('node:assert');\n"
                f"const {{ {import_list} }} = require('./{src_filename}');\n\n"
            )

        test_content = test_header + "".join(test_blocks)
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_content.strip() + "\n")

        # Hidden tests live in drill JSON and are run at grading time from a temp dir.
        hidden_tests = prob.get("hiddenTests", [])

        # Register npm test script per problem
        if preset_key == "react-dom":
            test_scripts[f"test:{pid.lower()}"] = (
                f"../../../tools/lint/node_modules/.bin/vitest run {test_filename} --environment jsdom"
            )
        elif preset_key in ("typescript-strict", "backend-sqlite"):
            test_scripts[f"test:{pid.lower()}"] = (
                f"node --experimental-strip-types --test --test-reporter=spec {test_filename}"
            )
        else:
            test_scripts[f"test:{pid.lower()}"] = f"node --test --test-reporter=spec {test_filename}"
        lint_command = "npm run lint"
        type_command = "npm run typecheck" if "typecheck" in test_scripts else None
        checks = [f"npm run test:{pid.lower()}", lint_command, *([type_command] if type_command else [])]
        test_scripts[f"check:{pid.lower()}"] = "; ".join(
            [
                *(f"{command}; status_$i=$?" for i, command in enumerate(checks)),
                "test " + " -a ".join(f"$status_{i} -eq 0" for i in range(len(checks))),
            ]
        )

        abs_src = os.path.abspath(src_path)
        abs_ws = os.path.abspath(ws_dir)
        manifest["files"][pid] = {
            "sourcePath": abs_src,
            "testPath": os.path.abspath(test_path),
            "cursorUrl": f"cursor://file/{abs_src}",
            "vscodeUrl": f"vscode://file/{abs_src}",
            "cursorFolderUrl": f"cursor://file/{abs_ws}",
            "vscodeFolderUrl": f"vscode://file/{abs_ws}",
            "relativeSrc": os.path.join(ws_base, drill_id, src_filename),
        }

        prob["workspaceFile"] = os.path.join(ws_base, drill_id, src_filename)
        for abs_key in ("workspaceDir", "cursorUrl", "vscodeUrl", "cursorFolderUrl", "vscodeFolderUrl"):
            prob.pop(abs_key, None)
        prob["archetype"] = archetype

        readme_problems.append(
            {
                "pid": pid,
                "entry": entry_name,
                "src": src_filename,
                "test": test_filename,
                "archetype": ARCHETYPE_LABELS.get(archetype, archetype),
                "prompt": prob.get("prompt", ""),
                "criteria_count": len(prob.get("visibleTests", [])),
                "hidden_count": len(hidden_tests),
            }
        )

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

    # 4b. Write eslint.config.mjs (and tsconfig.json for TS presets) in workspace
    lint_overrides = drill_doc.get("lintOverrides") or []
    eslint_cfg_path = os.path.join(ws_dir, "eslint.config.mjs")
    eslint_cfg_content = (
        'import { prgConfig } from "../../../tools/lint/base.js";\n\n'
        f"export default prgConfig({{ overrides: {json.dumps(lint_overrides)} }});\n"
    )
    with open(eslint_cfg_path, "w", encoding="utf-8") as f:
        f.write(eslint_cfg_content)
    stale_cfg = os.path.join(ws_dir, "eslint.config.js")  # older generator; ESLint would pick it before .mjs
    if os.path.exists(stale_cfg):
        os.remove(stale_cfg)

    if preset_key in ("typescript-strict", "backend-sqlite", "react-dom"):
        tsconfig_path = os.path.join(ws_dir, "tsconfig.json")
        tsconfig_data = {
            "compilerOptions": {
                "target": "ES2024",
                "module": "NodeNext",
                "moduleResolution": "NodeNext",
                "strict": True,
                "noEmit": True,
                "allowImportingTsExtensions": True,
                "skipLibCheck": True,
            },
            "include": ["*.ts", "*.tsx"],
        }
        if preset_key == "react-dom":
            tsconfig_data["compilerOptions"]["jsx"] = "react-jsx"
        with open(tsconfig_path, "w", encoding="utf-8") as f:
            json.dump(tsconfig_data, f, indent=2)
            f.write("\n")
    if preset_key == "react-dom":
        (Path(ws_dir) / "vitest.config.ts").write_text(
            "import { defineConfig } from 'vitest/config';\n"
            "export default defineConfig({ esbuild: { jsx: 'automatic' }, test: { environment: 'jsdom' } });\n",
            encoding="utf-8",
        )

    # 5. Write README.md in workspace
    readme_path = os.path.join(ws_dir, "README.md")
    readme_lines = [
        f"# {drill_id} — {unit_code}: {unit_title}",
        "",
        f"> **Environment Preset:** `{preset_key}` — {preset['description']}",
        "> **100% Local IDE Mandate**: All problem solving, refactoring, and debugging must be performed natively in your IDE (VS Code / Cursor).",
        "",
        "## Universal 6-Step Pedagogical Practice Loop",
        "1. **Think Before Coding (Mental Model)**: Review the Acceptance Criteria and boundary traps before typing.",
        "2. **Hands-On Implementation (Local IDE)**: Open the source file in VS Code or Cursor and implement the logic.",
        "3. **Automated Testing (Acceptance Testing)**: Run `npm test` or `npm run check:q01` in this directory.",
        "4. **Code Review & Explanation (PR Review)**: Run `npm run review -- q01` or ask in Claude Code (`review code <DRILL_ID> Q01`), then explain why your solution works.",
        "5. **Refactor (Clean Architecture)**: Decouple helpers, clean code smells, and optimize hot paths while keeping tests green.",
        "6. **Scale Difficulty (Progression)**: Scale up test inputs and edge cases.",
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
        "npm run check:q01",
        "",
        "# Run tests + lint (+ typecheck for TypeScript)",
        "npm run check",
        "",
        "# Show how to request a code review",
        "npm run review -- q01",
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
        readme_lines.extend(
            [
                f"### {p['pid']} — `{p['src']}`",
                f"- **Archetype:** {p['archetype']}",
                f"- **Acceptance Scenarios:** {scenario_str} in `{p['test']}`",
                f"- **Requirement:** {p['prompt']}",
                f"- **Run Single Suite:** `npm run test:{p['pid'].lower()}`",
                "",
            ]
        )

    readme_lines.extend(
        [
            "## Requesting a Code Review",
            "Once your automated tests pass, ask for a rubric-bound review in Claude Code:",
            "```text",
            f"review code {drill_id} Q01",
            "```",
            "To run Layer 1 (visible + hidden tests) and Layer 2 (ESLint + tsc) plus see the applicable rubric from repo root:",
            "```bash",
            "npm run review -- q01",
            "```",
            "",
        ]
    )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(readme_lines))

    return manifest


def read_workspace_code(abs_or_rel_path: str) -> str:
    if os.path.exists(abs_or_rel_path):
        with open(abs_or_rel_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def _rewrite_pilot_lab_relpaths(text: str) -> str:
    """Adjust relative paths from `labs/<LAB_ID>/` (depth 2) to `pilot/labs/<LAB_ID>/` (depth 3)."""
    text = text.replace("../../tools/lint/", "../../../tools/lint/")
    text = text.replace("../../_reference/", "../../../labs/_reference/")
    text = text.replace("../_reference/", "../../../labs/_reference/")
    text = text.replace("../common/", "../../../labs/common/")
    return text


def materialize_pilot_lab(lab_id: str, root_dir: str = ".", *, force: bool = False) -> Path:
    """Create a pilot copy of `labs/<lab_id>` under `pilot/labs/<lab_id>` without touching the real lab."""
    root = Path(root_dir)
    src_lab = root / "labs" / lab_id
    if not (src_lab / "lab.config.json").is_file():
        raise FileNotFoundError(f"Lab '{lab_id}' not found at {src_lab}")

    dst_lab = root / "pilot" / "labs" / lab_id
    dst_lab.mkdir(parents=True, exist_ok=True)

    for fname in ("lab.config.json", "tsconfig.json", "README.md"):
        src_file = src_lab / fname
        if src_file.is_file():
            shutil.copy2(src_file, dst_lab / fname)

    for fname in ("eslint.config.js", "package.json"):
        src_file = src_lab / fname
        if src_file.is_file():
            (dst_lab / fname).write_text(
                _rewrite_pilot_lab_relpaths(src_file.read_text(encoding="utf-8")), encoding="utf-8"
            )

    tests_src = src_lab / "tests"
    if tests_src.is_dir():
        shutil.copytree(tests_src, dst_lab / "tests", dirs_exist_ok=True)

    src_dir = src_lab / "src"
    if src_dir.is_dir():
        dst_src = dst_lab / "src"
        for item in src_dir.rglob("*"):
            if item.is_dir():
                continue
            rel = item.relative_to(src_dir)
            target = dst_src / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if force or not target.exists():
                shutil.copy2(item, target)

    return dst_lab


def _find_drill_json(drill_id: str, data_root: Path) -> Path:
    matches = sorted(data_root.glob(f"*/{drill_id}.json"))
    if not matches:
        matches = sorted(data_root.glob(f"**/{drill_id}.json"))
    if not matches:
        raise FileNotFoundError(f"Drill '{drill_id}' not found under {data_root}")
    return matches[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m code_engine.workspace",
        description="Materialise a drill workspace or pilot lab copy.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--drill", help="Drill ID to materialise (uses pilot/workspace when LEARNINGOS_PILOT=1)")
    group.add_argument("--pilot-lab", help="Lab ID to copy into pilot/labs/<LAB_ID>/")
    parser.add_argument("--force", action="store_true", help="Overwrite existing pilot lab src stubs")
    args = parser.parse_args(argv)

    try:
        if args.drill:
            data_root = Path(os.environ.get("DRILLS_DATA_DIR", "drills/data"))
            drill_path = _find_drill_json(args.drill, data_root)
            doc = json.loads(drill_path.read_text(encoding="utf-8"))
            if not doc.get("drillId"):
                doc["drillId"] = drill_path.stem
            manifest = materialize_drill_workspace(doc)
            print(manifest["workspaceDir"])
        else:
            dst = materialize_pilot_lab(args.pilot_lab, force=args.force)
            print(dst.resolve())
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
