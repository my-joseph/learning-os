# 04_CODE — Programming Practice, Test Suites & Terminal Labs

**Module Code:** `RULES-CODE`  
**Applies To:** Programming curricula (`PRG`), code kata suites, interactive practice studio, and terminal multi-milestone project labs  
**Prerequisite:** Must adhere to `rules/00_core.md`, `rules/01_arch.md`, and `rules/02_pedagogy.md`  

---

## PART 1 — Core Governing Principle: Architecture Over One-Off Content

All programming drills, katas, and multi-milestone project labs are driven strictly by decoupled, subject-agnostic configuration schemas (`lab.config.json` and `DRL-*.json`). The test runner and telemetry engine must never hardcode curriculum topics or domain logic. All technical artifacts, code, prompts, and database records must be 100% English.

---

## PART 2 — Three-Tier Practice Topology

### 1. Tier 1 — Micro Drills (Phase 1)
- **Format:** Diagnostic Predict-Output, Type-Puzzle, and Find-the-Bug questions running in the interactive Next.js Practice Studio.
- **Verification:** 100% Node.js pre-execution verification before registration.

### 2. Tier 2 — Algorithmic Katas (Phase 2)
- **Format:** Single-function or isolated algorithmic implementations in local IDE (`cursor://`, `vscode://`) or Studio.
- **Verification:** In-browser and terminal test runners testing against visible and hidden test cases.

### 3. Tier 3 — Multi-Milestone Project Labs (Phase 3)
- **Format:** Full repository multi-file projects developed locally in Cursor / VS Code.
- **Execution:** Tested locally via `npm test` and graded/synced automatically to Notion via `npm run submit`.

---

## PART 3 — Problem Generation & Quality Protocol

### 4. Sources of Truth & Context Inspection
- **Mandatory Context Inspection:** Before authoring any problem, AI must inspect the parent Notion Unit Page for (a) Core Concepts, (b) Common Pitfalls & Traps, and (c) Learning Objectives, cross-referenced with `id_map.json`.
- **Zero Toy Examples Standard:** AI is strictly forbidden from using `foo`, `bar`, `baz`, `test1`, or meaningless single-letter variables. Every problem must model realistic production domains (Auth tokens, Rate limiting, E-Commerce pricing, Mutex locks, WebSocket backoff).
- **Four Cognitive Dimensions:** Problems must balance:
  1. *Predict Output* (mental execution)
  2. *Type Puzzle* (compile-time invariants)
  3. *Find-the-Bug* (debugging & review)
  4. *Kata/Lab* (authoring & synthesis)
- **Anti-Leak & Anti-Cheat Standard:** Three-tier progressive hints (Concept $\rightarrow$ Strategy $\rightarrow$ Skeleton). Test suites must include boundary edge cases (empty arrays, falsy values `0`, `""`, `null`, boundary numbers) to prevent hardcoded return branches.

---

## PART 4 — Universal Five-Tier Milestone Taxonomy (Labs)

Every multi-milestone project lab adheres to a standardized milestone sequence:
- **M1 — Contracts & Schemas:** Domain models, TypeScript interfaces, DTOs, Zod schemas, invariant validators, configuration parsers.
- **M2 — Pure Business Logic & State Calculators:** Deterministic calculations, price/tax engines, state reducers, token parsers (strictly zero I/O side effects).
- **M3 — Stateful Services, Orchestration & State Machine:** Order lifecycle state machine, repository adapters, service coordination, API handlers.
- **M4 — Concurrency, Edge Cases & Resilience:** Atomic mutex locks, race condition prevention, transaction rollback on failure, malformed payload injections.
- **M5 (Optional) — Capstone End-to-End Workflow:** Smoke integration traversing all modules across realistic user journeys.

---

## PART 5 — Eight-Step AI Authoring Pipeline

AI must execute the following pipeline in strict sequential order:
1. **Spec Definition:** Create `lab.config.json` defining metadata, dependencies, and milestone point allocations.
2. **Canonical Solution:** Author complete, clean, production-grade reference implementation in `.canonical/`.
3. **Milestone Test Suites:** Author robust test suites in `tests/` covering every milestone requirement and edge cases.
4. **Mandatory Pre-Execution Verification:** Execute `node --test` or `vitest run` on `.canonical/`. **Must exit with code 0 and 100% pass rate.** AI is strictly forbidden from publishing unverified code or tests.
5. **Scaffolding Starter Code:** Strip the canonical solution into starter skeleton files with clear `// TODO [Milestone X]` markers.
6. **Package Scripts Configuration:** Configure `package.json` scripts (`test`, `test:watch`, `submit`).
7. **Baseline Negative Verification:** Run tests against starter code to confirm it fails gracefully with descriptive errors.
8. **Notion Registration:** Register the lab record in the `Learning Practice & Drills` database (`Format: "Code Test Suite"`).

---

## PART 6 — Terminal Telemetry Engine (`submit_lab.py`)

- **Standard Terminal Lifecycle:** Developer iterates locally with `npm test` (or `npm run test:watch`). Once milestones are implemented, developer runs `npm run submit`.
- **Runner-Agnostic JUnit XML Standard:** Telemetry engine parses standard JUnit XML (`--test-reporter=junit`), ensuring universal compatibility across Node, Vitest, Jest, Pytest, and Go.
- **Automated Notion Database Sync:** Evaluates points per milestone, maps failures to sanitized Mistake Categories, and updates Notion page properties and expandable toggle blocks with error traces.

---

## PART 7 — Interactive Studio & Storage Architecture

1. **Clean Architectural Separation:**
   - **JSON Data Layer (`drills/data/<UNIT>/`):** Pure verified problem sets and session states without HTML/JS pollution.
   - **Central Next.js Practice Studio (`practice-studio`):** React, TypeScript, and KaTeX learner workspace.
   - **Notion Database (`Learning Practice & Drills`):** Permanent retention record and spaced review ledger.
2. **Type-Driven SymPy Verification & Universal Problem Coverage:** Mathematical problems embedded in programming contexts must be verified via SymPy to ensure non-zero denominators, integer discriminants, and unambiguous single-step simplifications.
3. **Zero Unrendered Syntax:** Never leak unrendered LaTeX `$$` or raw Markdown inside raw code templates.
