# -*- coding: utf-8 -*-
"""
Local Workspace Manager for VS Code / Cursor Integration.

Materializes Kata problems into real local files:
- Source file: drills/workspace/<DRILL_ID>/<PROB_ID>_<name>.js (with starter code)
- Test file: drills/workspace/<DRILL_ID>/<PROB_ID>_<name>.test.js (with runnable visible tests)

Generates one-click IDE deep links (cursor://file/... and vscode://file/...)
so developers can write and debug in their real IDE with full LSP, keybindings, and tools.
"""
import json
import os


def get_entry_name(prob: dict) -> str:
    entry = prob.get("entryPoint")
    if entry:
        return entry
    pid = prob.get("id", "code")
    return pid.lower()


def materialize_drill_workspace(drill_doc: dict, root_dir: str = ".") -> dict:
    drill_id = drill_doc.get("drillId", "UNKNOWN_DRILL")
    ws_dir = os.path.join(root_dir, "drills", "workspace", drill_id)
    os.makedirs(ws_dir, exist_ok=True)

    manifest = {
        "drillId": drill_id,
        "workspaceDir": os.path.abspath(ws_dir),
        "files": {},
    }

    for prob in drill_doc.get("problems", []):
        ctype = prob.get("codeType")
        if ctype not in ("kata", "implement", "refactor"):
            continue

        pid = prob.get("id", "Q01")
        entry_name = get_entry_name(prob)
        src_filename = f"{pid}_{entry_name}.js"
        test_filename = f"{pid}_{entry_name}.test.js"

        src_path = os.path.join(ws_dir, src_filename)
        test_path = os.path.join(ws_dir, test_filename)

        # 1. Write starter code if source file does not already exist (preserve user's edits)
        starter = prob.get("starterCode") or f"function {entry_name}() {{\n  // TODO: implement\n}}\n\nmodule.exports = {{ {entry_name} }};\n"
        if not os.path.exists(src_path):
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(starter.strip() + "\n")

        # 2. Write test file with visible tests
        test_blocks = []
        for t in prob.get("visibleTests", []):
            t_name = json.dumps(t.get("name", "test case"))
            t_code = t.get("testCode", "").strip()
            test_blocks.append(f"""
test({t_name}, async () => {{
  {t_code}
}});
""")

        test_content = f"""// Auto-generated test file for {drill_id} {pid}
const test = require('node:test');
const assert = require('node:assert');
const {{ {entry_name} }} = require('./{src_filename}');

{ "".join(test_blocks) }
"""
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_content.strip() + "\n")

        abs_src = os.path.abspath(src_path)
        manifest["files"][pid] = {
            "sourcePath": abs_src,
            "testPath": os.path.abspath(test_path),
            "cursorUrl": f"cursor://file/{abs_src}",
            "vscodeUrl": f"vscode://file/{abs_src}",
            "relativeSrc": os.path.join("drills", "workspace", drill_id, src_filename),
        }

        # Update problem document in place
        prob["workspaceFile"] = os.path.join("drills", "workspace", drill_id, src_filename)
        prob["cursorUrl"] = f"cursor://file/{abs_src}"
        prob["vscodeUrl"] = f"vscode://file/{abs_src}"

    return manifest


def read_workspace_code(abs_or_rel_path: str) -> str:
    if os.path.exists(abs_or_rel_path):
        with open(abs_or_rel_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""
