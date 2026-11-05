# -*- coding: utf-8 -*-
"""
Uploads Part 11: Universal Programming Practice, Problem Generation & Terminal Lab Protocol
to Notion Central Rules Page ('Learning System — AI Implementation Rules' ID: 40c3818f-8ba0-8002-92f1-e971793125e3).
"""
import json
import re
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    get_all_blocks,
    rt,
    parse_rt,
    validate_blocks_clean,
    h3,
    p_block,
    callout_block,
    bullet,
    code_block,
    divider_block,
)

RULES_PAGE_ID = "40c3818f-8ba0-8002-92f1-e971793125e3"

def build_programming_rules(id_map):
    blocks = [
        h3("Universal Programming Practice, Problem Generation & Terminal Lab Protocol (Phase 1–3)", id_map),
        callout_block(
            "**Core Governing Principle — Architecture Over One-Off Content:** All programming drills, katas, and multi-milestone project labs are driven strictly by decoupled, subject-agnostic configuration schemas (`lab.config.json` and `DRL-*.json`). The test runner and telemetry engine must never hardcode curriculum topics or domain logic. All technical artifacts, code, prompts, and database records must be 100% English.",
            id_map,
            color="blue_background",
        ),
        bullet("**1. Subject-Agnostic Engine & Three-Tier Practice Topology:**", id_map, children=[
            bullet("**Tier 1 — Micro Drills (Phase 1):** Diagnostic Predict-Output, Type-Puzzle, and Find-the-Bug questions running in the interactive Next.js Practice Studio with 100% Node.js pre-execution verification.", id_map),
            bullet("**Tier 2 — Algorithmic Katas (Phase 2):** Single-function implementations in local IDE (`cursor://`, `vscode://`) or Studio with in-browser runner testing against hidden test cases.", id_map),
            bullet("**Tier 3 — Multi-Milestone Project Labs (Phase 3):** Full repository multi-file projects developed locally in Cursor / VS Code, tested via `npm test` and graded/synced via `npm run submit`.", id_map),
        ]),
        bullet("**2. Sources of Truth & Problem Generation Protocol:**", id_map, children=[
            bullet("**Mandatory Context Inspection:** Before authoring any problem, AI must inspect the parent Notion Unit Page for (a) Core Concepts, (b) Common Pitfalls & Traps, and (c) Learning Objectives, cross-referenced with `id_map.json`.", id_map),
            bullet("**Zero Toy Examples Standard:** AI is strictly forbidden from using `foo`, `bar`, `baz`, `test1`, or meaningless single-letter variables. Every problem must model realistic system domains (Auth tokens, Rate limiting, E-Commerce pricing, Mutex locks, WebSocket backoff).", id_map),
            bullet("**Four Cognitive Dimensions:** Problems must balance Predict Output (mental execution), Type Puzzle (compile-time invariants), Find-the-Bug (debugging & review), and Kata/Lab (authoring).", id_map),
            bullet("**Anti-Leak & Anti-Cheat Standard:** Three-tier progressive hints (Concept -> Strategy -> Skeleton). Test suites must include boundary edge cases (empty arrays, falsy values `0`, `\"\"`, `null`, boundary numbers) to prevent hardcoded return branches.", id_map),
        ]),
        bullet("**3. Universal Five-Tier Milestone Taxonomy (Architecture for Arbitrary Projects):**", id_map, children=[
            bullet("**M1 — Contracts & Schemas:** Domain models, TypeScript interfaces, DTOs, Zod schemas, invariant validators, configuration parsers.", id_map),
            bullet("**M2 — Pure Business Logic & State Calculators:** Deterministic business calculations, price/tax engines, state reducers, token parsers (strictly zero I/O side effects).", id_map),
            bullet("**M3 — Stateful Services, Orchestration & State Machine:** Order lifecycle state machine, repository adapters, service coordination, API handlers.", id_map),
            bullet("**M4 — Concurrency, Edge Cases & Resilience:** Atomic mutex locks, race condition prevention, transaction rollback on failure, malformed payload injections.", id_map),
            bullet("**M5 (Optional) — Capstone End-to-End Workflow:** Smoke integration traversing all modules across realistic user journeys.", id_map),
        ]),
        bullet("**4. Strict Eight-Step AI Authoring Pipeline & Mandatory Pre-Execution Verification:**", id_map, children=[
            bullet("**Steps 1 to 3 (Spec, Canonical & Tests):** Define `lab.config.json` -> Author complete production-grade solution in `.canonical/` -> Author milestone test suites in `tests/`.", id_map),
            bullet("**Step 4 (Mandatory Pre-Execution Verification):** Execute `node --test` or `vitest run` on canonical solution. MUST exit with code 0 and 100% pass rate. AI is strictly forbidden from publishing unverified code or tests.", id_map),
            bullet("**Steps 5 to 8 (Scaffolding, Scripts, Baseline & Notion):** Strip solution into starter skeleton with `// TODO [Milestone X]` -> Configure `package.json` (`test`, `submit`) -> Verify starter code fails gracefully -> Register in Notion `Learning Practice & Drills` (`Format: \"Code Test Suite\"`).", id_map),
        ]),
        bullet("**5. Terminal-First Workflow & Telemetry Engine (`submit_lab.py`):**", id_map, children=[
            bullet("**Standard Terminal Lifecycle:** Developer iterates locally with `npm test` (or `npm run test:watch`). Once milestones are implemented, developer runs `npm run submit`.", id_map),
            bullet("**Runner-Agnostic JUnit XML Standard:** Telemetry engine parses standard JUnit XML (`--test-reporter=junit`), ensuring universal compatibility across Node, Vitest, Jest, Pytest, and Go.", id_map),
            bullet("**Automated Notion Database Sync:** Evaluates points per milestone, maps failures to sanitized Mistake Categories, and updates Notion page properties and expandable toggle blocks with error traces.", id_map),
        ]),
        bullet("**6. Ironclad Technical Constraints & Error Gotchas:**", id_map, children=[
            bullet("**Notion Comma Ban (HTTP 400 Prevention):** Multi-select tags in Notion API strictly forbid commas `,`. All mistake category tags must be sanitized with `.replace(/,/g, \" /\")` before transmission.", id_map),
            bullet("**Dynamic Path Resolution:** Never hardcode absolute paths (`/Users/...`). All scripts must dynamically search upwards for workspace root anchor files (`id_map.json` or `.git`).", id_map),
            bullet("**100% English Artifact Standard:** Code, comments, prompts, test names, error messages, and Notion database blocks must be written in 100% clear English.", id_map),
            bullet("**Node 24 Native TypeScript Stripping:** Always use `import type { ... }` for pure types and interfaces to prevent runtime `SyntaxError: requested module does not provide export`.", id_map),
            bullet("**Notion Icon Whitelist:** Use only valid Notion icon names (`\"code\"`, `\"target\"`, `\"lightgray\"`) or standard emojis. Never use unlisted names like `\"terminal\"`.", id_map),
        ]),
    ]
    return blocks

def main():
    env = load_env()
    token = env.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN not set in .env")

    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    blocks = build_programming_rules(id_map)
    validate_blocks_clean(blocks, "Part11-ProgrammingRules")
    print(f"Validated {len(blocks)} rule blocks cleanly (0 unresolved tokens, 100% English).")

    # Locate insertion anchor
    print("Fetching existing blocks on Central Rules Page...")
    existing_blocks = get_all_blocks(RULES_PAGE_ID, token)

    # First check if previous Part 11 heading exists and delete if so
    anchor_id = None
    for i, b in enumerate(existing_blocks):
        bt = b["type"]
        txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
        if "Universal Programming Practice" in txt:
            print(f"Deleting existing Part 11 block: {b['id']}")
            notion_request("DELETE", f"blocks/{b['id']}", token)
        if "5. Interactive Equation Step Highlighting & Paper-First Mistake Diagnostics:" in txt:
            anchor_id = b["id"]

    if not anchor_id:
        # Fallback to block right before 11. Preserve User Content
        for i, b in enumerate(existing_blocks):
            bt = b["type"]
            txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", []))
            if "11. Preserve User Content" in txt:
                anchor_id = existing_blocks[i - 1]["id"]
                break

    print(f"Found anchor block ID: {anchor_id}")
    print("Uploading Part 11 rules to Notion Central Rules Page...")
    res = notion_request(
        "PATCH",
        f"blocks/{RULES_PAGE_ID}/children",
        token,
        {
            "after": anchor_id,
            "children": blocks,
        },
    )
    print("🎉 SUCCESS! Part 11 rules successfully uploaded to Notion Central Rules Page!")

if __name__ == "__main__":
    main()
