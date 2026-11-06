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

## PART 2 — Five Real-World Problem Archetypes

All programming exercises generated in the system must belong to one of these 5 real-world archetypes, eliminating synthetic toy snippets:

| Archetype | Cognitive Focus | Description & Learner Experience | Evaluation Method |
| :--- | :--- | :--- | :--- |
| **1. Problem Solving** | Logic & Algorithms with Clear I/O | Practical algorithms and business logic with well-defined inputs, outputs, and edge conditions (e.g. streaming log parser, nested data aggregators, rate limiters, token evaluators). | Automated Acceptance Suite (`npm test`) |
| **2. Debugging** | Systemic Debugging & Root Cause Analysis | Analyzing broken, bug-ridden code, diagnosing root causes (e.g. race conditions, off-by-one, silent state mutations, unhandled promise rejections), and fixing them without modifying tests. | Failing Acceptance Tests turn Green |
| **3. Code Tracing** | Mental Execution Model & Flow Prediction | Reading complex real-world code and predicting output, call stack order, event loop microtask execution, or scope closure resolution before running. | Deterministic Value Check + Flow Step Verification |
| **4. Code Modification & Refactoring** | Clean Architecture & Safe Extensibility | Given a working but tangled legacy codebase covered by passing tests, add new business requirements and refactor into clean, decoupled design patterns without breaking existing tests. | Green Regression Suite + AI Architectural PR Review |
| **5. Project-Based** | Systems Synthesis & Multi-Module Architecture | Building a complete, working production subsystem from scratch (e.g. In-memory Cache with TTL, Pub-Sub Event Bus, Cart & Tiered Voucher Engine, REST Client with Retry/Circuit Breaker). | Milestone Acceptance Tests + AI Senior Lead Architecture Review |

### 1. Archetype Specification Blueprints & Contracts

Every problem generated must adhere to its archetype structural contract:
1. **Problem Solving Blueprint:**
   - Must specify `entryPoint` function or class with explicit parameter/return shapes.
   - Must define boundary invariants (empty array, zero/negative, type bounds).
   - Must include at least 3 visible scenarios covering happy path and edge conditions.
2. **Debugging Blueprint:**
   - Must provide `starterCode` containing a realistic production bug (not a typo or trivial syntax error).
   - Must provide a Reproducer Test case reproducing the failure.
   - Must provide Anti-Regression test cases verifying unaffected legacy behavior.
   - Fix must resolve the reproducer test without modifying test suites.
3. **Code Tracing Blueprint:**
   - Must provide deterministic multi-step snippet (e.g. event loop queue, closure scope).
   - Must specify exact expected stdout tokens or execution sequence.
4. **Refactoring Blueprint:**
   - Must provide working legacy codebase passing all baseline regression tests.
   - Must specify concrete code smells to eliminate (e.g. nested switch, shared mutable state).
   - Must specify new feature requirements that demand an extensible design pattern.
5. **Project-Based Blueprint:**
   - Multi-module domain architecture (e.g. schemas, services, state machine).
   - Tiered milestones with progressive acceptance tests.

---

## PART 3 — Seven Core Engineering Competencies

Every drill and lab in `PRG` must explicitly target and develop one or more of these 7 essential engineering competencies:

1. **Data Handling:** Advanced filtering, sorting, indexing, searching, grouping, normalization, and immutable transformations of complex or nested datasets.
2. **State Management:** Controlling application state, state machine transitions, immutable reducers, optimistic updates, and reactive store synchronization.
3. **Component & Modular Design:** Designing reusable, composable, and decoupled modules, utilities, and headless interfaces with clear boundaries and dependency injection.
4. **API Integration:** Connecting to and managing remote data, handling network latency, exponential backoff retries, cursor pagination, abort controllers, and error resilience.
5. **TypeScript & Type Systems:** Designing bulletproof types, interfaces, generics, discriminated unions, utility types, and runtime schema validation (e.g. Zod).
6. **Architecture & Separation of Concerns:** Domain-driven layering, Repository pattern, Clean/Hexagonal architecture, and single-responsibility decomposition.
7. **Performance & Optimization:** Profiling and optimizing hot paths, memoization, debouncing/throttling, indexing, eliminating $O(N^2)$ bottlenecks, and memory leak prevention.

---

## PART 4 — Universal Six-Step Pedagogical Practice Loop

All programming drills and labs enforce this systematic, professional engineering loop:

$$\text{Think Before Coding} \longrightarrow \text{Hands-On Implementation} \longrightarrow \text{Automated Testing} \longrightarrow \text{Code Explanation} \longrightarrow \text{Refactor} \longrightarrow \text{Scale Difficulty}$$

1. **Think Before Coding (Mental Model & Invariant Planning):** Before writing a single line of code, review the business context, input/output contracts, and potential boundary traps. Sketch the mental model, data transformations, and state transitions.
2. **Hands-On Implementation (Local IDE Execution):** Launch VS Code or Cursor directly via one-click deep links. Implement the logic using real IDE tools, linting, type systems, and autocomplete.
3. **Automated Testing (Acceptance Testing):** Run local test suites in the terminal (`npm test`). Iterate until all visible scenarios and edge-case acceptance criteria pass with 100% green.
4. **Code Explanation (AI Senior Lead PR Review):** Articulate why the solution works, explain algorithmic trade-offs, and request an AI Senior Tech Lead architectural review focusing on the 7 core engineering competencies.
5. **Refactor (Clean Code & Decoupling):** Eliminate code smells, extract single-responsibility helpers, improve naming, optimize hot paths, and refine type annotations while keeping tests green.
6. **Scale Difficulty (Edge Scaling & Extension):** Progress to higher difficulty tiers, stricter performance constraints, or additional real-world business constraints.

---

## PART 5 — Problem Generation & Quality Protocol

### 3. Sources of Truth & Context Inspection
- **Mandatory Context Inspection:** Before authoring any problem, AI must inspect the parent Notion Unit Page for (a) Core Concepts, (b) Common Pitfalls & Traps, and (c) Learning Objectives, cross-referenced with `id_map.json`.
- **Zero Toy Examples Standard:** AI is strictly forbidden from using `foo`, `bar`, `baz`, `test1`, or meaningless single-letter variables. Every problem must model realistic production domains (Auth tokens, Rate limiting, E-Commerce pricing, Mutex locks, WebSocket backoff).
- **Anti-Cheat & Boundary Standards:** Test suites must include boundary edge cases (empty collections, zero, falsy values, large integers, timeout traps) to verify real logic rather than hardcoded return branches.

### 4. Problem Specification Formatting & Readability Protocol (Zero Wall-of-Text Standard)
To ensure maximum cognitive clarity and mirror real-world engineering specifications (Jira tickets, PRDs, RFCs), all programming prompts must follow strict typography and structural standards:
- **Zero Wall-of-Text Standard:** Continuous unbroken paragraphs (> 2 sentences) for complex multi-rule specifications are strictly forbidden. Never dump a single massive block of text.
- **Mandatory Four-Part Specification Structure:**
  1. **Objective / Overview:** 1-2 concise sentences summarizing the primary mission with the entry point function or class enclosed in inline backticks (e.g. `Implement calculateOrderTotal(order) for an e-commerce platform.`).
  2. **Categorized Markdown Sections & Bulleted Lists:** Requirements, calculation tiers, and business policies must be broken down into structured bulleted lists (`- `) with bold category prefixes (e.g. `**Input Validation:**`, `**Coupon Rules:**`, `**Shipping Policy:**`, `**Tax Rules:**`).
  3. **Strict Code Identifier Typography:** Every code symbol, variable/parameter (`order.items`, `subtotal`), literal value (`"PERCENT10"`, `true`, `8 USD`), and Error type (`RangeError`, `TypeError`) must be formatted as inline code with backticks.
  4. **Explicit Return Schema Contract:** Multi-key return objects or data structures must be explicitly written out as an inline code contract (e.g. `{ subtotal, discount, shipping, tax, total, currency: 'USD' }`) or code block so the developer never has to guess the shape.

---

## PART 6 — Universal Five-Tier Milestone Taxonomy (Labs)

Every multi-milestone project lab adheres to a standardized milestone sequence:
- **M1 — Contracts & Schemas:** Domain models, TypeScript interfaces, DTOs, Zod schemas, invariant validators, configuration parsers.
- **M2 — Pure Business Logic & State Calculators:** Deterministic calculations, price/tax engines, state reducers, token parsers (strictly zero I/O side effects).
- **M3 — Stateful Services, Orchestration & State Machine:** Order lifecycle state machine, repository adapters, service coordination, API handlers.
- **M4 — Concurrency, Edge Cases & Resilience:** Atomic mutex locks, race condition prevention, transaction rollback on failure, malformed payload injections.
- **M5 (Optional) — Capstone End-to-End Workflow:** Smoke integration traversing all modules across realistic user journeys.

---

## PART 7 — Eight-Step AI Authoring Pipeline

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

## PART 8 — Terminal Telemetry Engine (`submit_lab.py`)

- **Standard Terminal Lifecycle:** Developer iterates locally with `npm test` (or `npm run test:watch`). Once milestones are implemented, developer runs `npm run submit`.
- **Runner-Agnostic JUnit XML Standard:** Telemetry engine parses standard JUnit XML (`--test-reporter=junit`), ensuring universal compatibility across Node, Vitest, Jest, Pytest, and Go.
- **Automated Notion Database Sync:** Evaluates points per milestone, maps failures to sanitized Mistake Categories, and updates Notion page properties and expandable toggle blocks with error traces.

### 1. Mandatory Engineering Gotchas & Invariants
- **Gotcha 1 (Notion Multi-Select Comma Ban):** Notion strictly rejects any multi_select option containing commas `,`. AI and scripts must sanitize via `.replace(/,/g, " /")` before payload delivery.
- **Gotcha 2 (Filesystem Anchor Search):** Never assume current working directory. Scripts must locate repository root via filesystem anchor search (`find_repo_root`).
- **Gotcha 3 (Node 24 Native Type-Stripping Imports):** Pure TypeScript types and interfaces must use `import type { ... }` so Node strips them away completely at compile time.
- **Gotcha 4 (Unhandled Async Promises in Tests):** All async test cases must be properly `await`ed and timers/connections cleaned up in `after()` to prevent frozen processes.
- **Gotcha 5 (Notion API Icon Whitelist):** Use only standard Notion icon names (e.g. `"code"`, `"target"`). Programming exercises must use `"code"`.

---

## PART 9 — Interactive Studio & Storage Architecture

1. **Clean Architectural Separation:**
   - **JSON Data Layer (`drills/data/<UNIT>/`):** Pure verified problem specs, Acceptance Criteria, and session states without HTML pollution.
   - **Workspace Layer (`drills/workspace/<DRILL_ID>/` or `labs/<LAB_ID>/`):** Real TypeScript/Node workspaces on disk ready for VS Code / Cursor.
   - **Central Next.js Practice Studio (`practice-studio`):** Mission Control Dashboard, launcher links, and live telemetry viewer.
   - **Notion Database (`Learning Practice & Drills`):** Permanent retention record and spaced review ledger.
2. **Zero In-Browser Textareas:** Studio renders clean requirement specifications, test runners reading from disk, and mistake logs, delegating all code editing to the local IDE.

---

## PART 10 — Workspace Environment Presets & Dual-Tier Testing

### 1. Standardized Environment Presets
Workspaces are scaffolded using one of 4 environment presets:
1. **`node-vanilla`:** Standard Node.js native runner (`node --test *.test.js`) for algorithmic utilities and core JavaScript.
2. **`typescript-strict`:** Native TypeScript execution with typecheck validation (`node --experimental-strip-types --test *.test.ts` and `tsc --noEmit`).
3. **`react-dom`:** Frontend Component & Custom Hook environment (`vitest run` with jsdom and `@testing-library/react`).
4. **`backend-sqlite`:** In-memory transactional database environment using `better-sqlite3`.

### 2. Dual-Tier Test Suite Architecture
To ensure high engineering integrity and prevent hardcoded return hacks:
- **Visible Acceptance Tests (`visibleTests`):** Scaffolded into `<PID>_<name>.test.*` for rapid local feedback and TDD iteration.
- **Hidden Trap Tests (`hiddenTests`):** Scaffolded into `.canonical/<PID>_<name>.hidden.test.*` and evaluated during `npm run submit`. Tests boundary invariants, scale limits, and poison payloads to verify true generalized logic.
