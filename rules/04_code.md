# 04_CODE — Programming Practice, Test Suites & Terminal Labs

**Module Code:** `RULES-CODE`  
**Applies To:** Programming curricula (`PRG`), code kata suites, interactive practice studio, and terminal multi-milestone project labs  
**Prerequisite:** Must adhere to `rules/00_core.md`, `rules/01_arch.md`, and `rules/02_pedagogy.md`  

---

## PART 1 — Core Governing Principle: 100% Local IDE Execution & Dual-Engine Evaluation

### 1. Zero In-Browser Code Editing Mandate
All code authoring, multi-file browsing, refactoring, and debugging must take place natively inside **VS Code or Cursor** in the local workspace. In-browser web textareas promote toy single-file scripting and lack Language Server Protocols (LSP), linters, formatting, and real terminal execution.

**Strict Separation of Concerns:**
- **Local IDE (VS Code / Cursor):** The primary execution cockpit. Developers write real TypeScript/JavaScript, run real-time tests via terminal (`npm test`), and submit results via `npm run submit`.
- **Practice Studio (Web Dashboard):** The Mission Control & Telemetry Hub. Displays business scenarios, Acceptance Criteria, deep launcher links (`vscode://` / `cursor://`), live test execution reports, mistake categorization, and spaced retention tracking.

### 2. Dual-Engine Evaluation: Automated Tests vs. AI Architectural Review
Programming cannot be evaluated solely by mechanical test scripts like mathematics:
1. **Engine A — Automated Test Scripts (Functional Correctness):**
   - **Scope:** Smoke tests, input/output validation, acceptance criteria verification, and regression prevention.
   - **Anti-Trap Invariant:** Scripts must **never** be over-assertive or attempt to rigidly assert internal class names, private members, or AST structures. Scripts verify *what the software does*, not *the exact internal code phrasing*. This prevents AI generators from retreating into trivial toy LeetCode problems.
2. **Engine B — AI Senior Tech Lead (Architectural Quality & Code Craftsmanship):**
   - **Scope:** Clean Architecture, Separation of Concerns, Design Patterns, SOLID principles, type-narrowing elegance, and refactoring trade-offs.
   - **Review Workflow:** Once automated tests pass (Layer 1), the developer requests an AI Pull Request Code Review inside the workspace. The AI provides senior-level architectural guidance, identifies hidden coupling, and recommends cleaner abstractions.

---

## PART 2 — Four Real-World Problem Archetypes

All programming exercises generated in the system must belong to one of these 4 real-world archetypes, eliminating synthetic toy snippets:

| Archetype | Cognitive Focus | Description & Learner Experience | Evaluation Method |
| :--- | :--- | :--- | :--- |
| **1. Business Requirements & Acceptance Criteria** | Feature Engineering & Invariants | AI presents a realistic business scenario (e.g. Tiered Subscription Billing, Cart Voucher Engine) with 4–6 clear Acceptance Criteria and boundary edge cases. | Automated Acceptance Suite (`npm test`) |
| **2. Refactoring on Legacy Code under Test** | Code Craftsmanship & Clean Code | Learner is given a working but messy, tightly coupled 150–200 line codebase covered by passing tests. The mission is to refactor into clean patterns without breaking any test. | Regression Tests (Green) + AI Structural Review |
| **3. Bug Triage & Root Cause Analysis** | Systemic Debugging & Tracing | Learner receives a multi-file project with a reproducing failing test (e.g. race condition, cache desynchronization, memory leak). Must isolate the root cause and fix it cleanly. | Failing Test turns Green + Root Cause Explanation |
| **4. Multi-Milestone Architecture Labs** | System Architecture & Synthesis | Full-repository projects developed in `labs/` progressing through a 4-to-5 tier milestone sequence. | Milestone JUnit Runner (`npm run submit`) + Notion Sync |

---

## PART 3 — Problem Generation & Quality Protocol

### 3. Sources of Truth & Context Inspection
- **Mandatory Context Inspection:** Before authoring any problem, AI must inspect the parent Notion Unit Page for (a) Core Concepts, (b) Common Pitfalls & Traps, and (c) Learning Objectives, cross-referenced with `id_map.json`.
- **Zero Toy Examples Standard:** AI is strictly forbidden from using `foo`, `bar`, `baz`, `test1`, or meaningless single-letter variables. Every problem must model realistic production domains (Auth tokens, Rate limiting, E-Commerce pricing, Mutex locks, WebSocket backoff).
- **Anti-Cheat & Boundary Standards:** Test suites must include boundary edge cases (empty collections, zero, falsy values, large integers, timeout traps) to verify real logic rather than hardcoded return branches.

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
4. **Mandatory Functional Pre-Execution Verification:** Execute `node --test` or `vitest run` on `.canonical/`. **Must exit with code 0 and 100% pass rate.**
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
   - **JSON Data Layer (`drills/data/<UNIT>/`):** Pure verified problem specs, Acceptance Criteria, and session states without HTML pollution.
   - **Workspace Layer (`drills/workspace/<DRILL_ID>/` or `labs/<LAB_ID>/`):** Real TypeScript/Node workspaces on disk ready for VS Code / Cursor.
   - **Central Next.js Practice Studio (`practice-studio`):** Mission Control Dashboard, launcher links, and live telemetry viewer.
   - **Notion Database (`Learning Practice & Drills`):** Permanent retention record and spaced review ledger.
2. **Zero In-Browser Textareas:** Studio renders clean requirement specifications, test runners reading from disk, and mistake logs, delegating all code editing to the local IDE.
