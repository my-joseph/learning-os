# 04_CODE — Programming Practice, Test Suites & Terminal Labs

**Module Code:** `RULES-CODE`  
**Applies To:** Programming curricula (`PRG`), code kata suites, interactive practice studio, and terminal multi-milestone project labs  
**Prerequisite:** Must adhere to `rules/00_core.md`, `rules/01_arch.md`, and `rules/02_pedagogy.md`  

---

## PART 1 — Core Governing Principle: 100% Local IDE Execution & Three-Layer Evaluation

### 1. Zero In-Browser Code Editing Mandate
All code authoring, multi-file browsing, refactoring, and debugging must take place natively inside **your local IDE (e.g. VS Code)** in the local workspace. In-browser web textareas promote toy single-file scripting and lack Language Server Protocols (LSP), linters, formatting, and real terminal execution.

**Strict Separation of Concerns:**
- **Local IDE (e.g. VS Code):** The primary execution cockpit. Developers write real TypeScript/JavaScript, run real-time tests via terminal (`npm test`), and submit results via `npm run submit`.
- **Practice Studio (Web Dashboard):** The Mission Control & Telemetry Hub. Displays business scenarios, Acceptance Criteria, deep launcher links (`vscode://`), live test execution reports, mistake categorization, and spaced retention tracking.

### 1.1 Local Workspace Deep Linking Contract (Folder vs. Single-File Invariant)
To maintain the 100% Local IDE Execution mandate without breaking IDE context, all launcher links between Practice Studio and the local IDE must obey this strict contract:
- **Primary Workspace Launcher MUST target the Folder Directory (`vscodeFolderUrl`)**:  
  Clicking "Open in VS Code" MUST open the entire workspace folder (`vscode://file/<abs_workspace_dir>`), NEVER an isolated single file (`vscode://file/<abs_file_path>`). (Code is edited in the learner's own editor; do not render an "Open in Cursor" button or emit `cursor://` links.)  
  *Why*: Opening an isolated file launches the IDE in "No Folder Opened" mode. The IDE fails to discover `package.json`, disables the NPM Scripts explorer, and defaults the integrated terminal to the user's home or root directory instead of the problem directory. Opening the workspace folder guarantees `package.json` scripts (`npm test`, `npm run test:q01`) and terminal paths work instantly.
- **Secondary Jump-to-File Link (`vscodeUrl`)**:  
  An optional "Open File" button may exist to jump directly into the source file or a specific line, but it must never replace or overwrite the primary folder-level launcher action.
- **Defensive Frontend Resolution**:  
  If problem metadata omits `vscodeFolderUrl`, Practice Studio must compute the folder directory from `workspaceDir` or `workspaceFile` (by trimming filename), and must **never** fall back to opening an isolated file in place of the folder.

### 2. Three-Layer Evaluation: Tests, Lint/Types, and Rubric Review
Programming work is evaluated in three layers:
1. **Layer 1 — Automated Tests (Functional Correctness):**
   - **Scope:** Smoke tests, input/output validation, acceptance criteria verification, and regression prevention.
   - **Lab review:** The milestone's visible and hidden suites must each produce a complete passing report. A missing suite, incomplete report, or test runner crash blocks a pass.
   - **Anti-Trap Invariant:** Scripts must **never** be over-assertive or attempt to rigidly assert internal class names, private members, or AST structures. Scripts verify *what the software does*, not *the exact internal code phrasing*. This prevents AI generators from retreating into trivial toy LeetCode problems.
2. **Layer 2 — Lint and Types:** ESLint and `tsc` check style, static correctness, and supported TypeScript configurations via `code_engine/lint_check.py` and `tools/lint/`.
3. **Layer 3 — Rubric Review:** `qualityChecks` evaluates architecture and code craft that tests cannot observe. Use `code_engine/quality_checks.py`, `code_engine/review_run.py`, and `scripts/review_record.py` for rubric-bound review and recording.

### 2.1 Review rubric (`qualityChecks`)
Layer 3 design review criteria live in `code_engine/quality_checks.json` (universal checks) and each archetype's `qualityChecks` in `code_engine/reasoning_vault/*.json` (see `docs/prg_reviewer_spec.md`):
- **Behaviour goes to hidden tests, not the rubric:** `qualityChecks` only covers what automated tests cannot observe (structure, separation of concerns, encapsulation, testability/injection, error design, timing/security properties). Functional behaviour bugs belong in `hiddenTests` and `cognitiveTraps`.
- **Properties, never a mandated API:** every check states a property of the code (e.g. "No reference to internal mutable state escapes the factory"), never a required API (e.g. never "must use `toSorted()`"); optional `accepted` lists give the reviewer acceptable examples as hints only.
- **`must` blocks a pass:** any `must` finding produces a `revise` verdict (`U-one-job` becomes `must` from level 3).
- **`should` never blocks:** `should` findings are advisory only.
- **Taste is not a finding:** stylistic preferences (e.g. `for` vs `forEach` when both are clear) are never reported.
- **Every finding cites a check id:** every finding must name a check id (`U-*` or `QC-*`), line, what is wrong, and why it matters.

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
2. **Hands-On Implementation (Local IDE Execution):** Open the workspace folder in your local editor (e.g. via the "Open in VS Code" deep link). Implement the logic using real IDE tools, linting, type systems, and autocomplete.
3. **Automated Testing (Acceptance Testing):** Run local test suites in the terminal (`npm test`). Iterate until all visible scenarios and edge-case acceptance criteria pass with 100% green.
4. **Code Explanation (Rubric-Bound PR Review):** Run `python -m code_engine.review_run <DRILL_ID> <QID>` (or ask in Claude Code: `review code <DRILL_ID> <QID>`), address any `must` or lint/typecheck findings via `scripts.review_record`, and record a concise explanation of why the solution works.
5. **Refactor (Clean Code & Decoupling):** Eliminate code smells, extract single-responsibility helpers, improve naming, optimize hot paths, and refine type annotations while keeping tests green.
6. **Scale Difficulty (Edge Scaling & Extension):** Progress to higher difficulty tiers, stricter performance constraints, or additional real-world business constraints.

---

## PART 5 — Problem Generation & Quality Protocol

### 3. Sources of Truth & Context Inspection
- **Mandatory Context Inspection:** Before authoring any problem, AI must inspect the parent Notion Unit Page for (a) Core Concepts, (b) Common Pitfalls & Traps, and (c) Learning Objectives, cross-referenced with `id_map.json`.
- **Zero Toy Examples Standard:** AI is strictly forbidden from using `foo`, `bar`, `baz`, `test1`, or meaningless single-letter variables. Every problem must model realistic production domains (Auth tokens, Rate limiting, E-Commerce pricing, Mutex locks, WebSocket backoff).
- **Anti-Cheat & Boundary Standards:** Test suites must include boundary edge cases (empty collections, zero, falsy values, large integers, timeout traps) to verify real logic rather than hardcoded return branches.
- **PRG Source Synthesis & Code Originality (`rules/07` §4):** Registered code and markdown repositories under `sources/prg/<family>/` (`docs/sources.md` allowed use: `REUSE`, `CORES`, or `NO-AUTOMATION`; `NO-AUTOMATION` families are never indexed automatically) feed `scripts.source_find <UNIT> --plan`, `scripts.extract_cards_job`, and `scripts.source_gap` to extract source-free PRG core cards (`prg_schema.json`: no copied source code, identifiers, test names, or strings; optional `reuse` licence/attribution block on `REUSE` families when a test idea is adapted and rewritten) and surface missing traps, bug patterns, `QC-*` checks, archetype kinds, and levels in `code_engine/reasoning_vault/`. Before ingest or finalise, `code_engine.ai_drill_ingest --check` and `code_engine.lab_ingest --check` run the code originality gate (`--originality`, default ON when `sources/` exists), rejecting both prompt-text overlap and normalized token-level Winnowing/k-gram similarity across solutions, starters, and tests.

### 4. Problem Specification Formatting & Readability Protocol (Zero Wall-of-Text Standard)
To ensure maximum cognitive clarity and mirror real-world engineering specifications (Jira tickets, PRDs, RFCs), all programming prompts must follow strict typography and structural standards:
- **Zero Wall-of-Text Standard:** Continuous unbroken paragraphs (> 2 sentences) for complex multi-rule specifications are strictly forbidden. Never dump a single massive block of text.
- **Mandatory Four-Part Specification Structure:**
  1. **Objective / Overview:** 1-2 concise sentences summarizing the primary mission with the entry point function or class enclosed in inline backticks (e.g. `Implement calculateOrderTotal(order) for an e-commerce platform.`).
  2. **Categorized Markdown Sections & Bulleted Lists:** Requirements, calculation tiers, and business policies must be broken down into structured bulleted lists (`- `) with bold category prefixes (e.g. `**Input Validation:**`, `**Coupon Rules:**`, `**Shipping Policy:**`, `**Tax Rules:**`).
  3. **Strict Code Identifier Typography:** Every code symbol, variable/parameter (`order.items`, `subtotal`), literal value (`"PERCENT10"`, `true`, `8 USD`), and Error type (`RangeError`, `TypeError`) must be formatted as inline code with backticks.
  4. **Explicit Return Schema Contract:** Multi-key return objects or data structures must be explicitly written out as an inline code contract (e.g. `{ subtotal, discount, shipping, tax, total, currency: 'USD' }`) or code block so the developer never has to guess the shape.

New PRG coding drill problems and every lab milestone also include 2–3 LeetCode-style `examples` (`[{ input, output, explanation?, call? }]`, with `input`/`output` in JS/TS literal syntax and `call` verified against the reference solution at ingest and stripped before browser delivery) and optional `constraints: string[]` when inputs have limits; examples are visible before any attempt and must use normal cases only (never hidden-test inputs or `commonTrap` cases). Pure `code-tracing` / `predict-output` / `trace-explain` drill problems with a fixed `codeSnippet` (or without `solutionCode`/`visibleTests`) are exempt from `examples` so they do not spoil the answer.

### 5. Concept Vault references
The Concept Vault registry uses `CON-*` keys in `id_map.json`. Current authoring skills do not run a universal keyword-matching or auto-registration pass across PRG drills, labs, and question READMEs. Add a registered concept mention when the specific task workflow asks for one and its target format supports it; see `rules/00_core.md` §8.

### 6. Immediate Pristine Notion Sync on Drill Creation
- **Mandatory Immediate Sync:** Whenever a drill file (`drills/data/**/*.json`) or code lab is authored or generated, AI must immediately synchronize a pristine initial snapshot into the `Learning Practice & Drills` Notion database. Never leave a newly generated drill existing only on local disk.
- **Initial Pristine State:** The initial Notion page must be unattempted (`Score = null`, `Practice Status = "Ready"`, `Mistake Categories = []`, `Attempt Date = null`). Here `null` means unattempted or awaiting review; `0` means wrong or skipped.
- **Comprehensive Body Content:** The initial page body must immediately provide:
  1. **Drill Overview & Focus:** Core learning objectives, primary skills drilled, and critical invariant failure modes to avoid.
  2. **Question Inventory & Breakdown:** Exact count and listing of all problems, hints, diagrams, and full vertical step-by-step solutions (in expandable toggle blocks).
  3. **Curriculum Cross-References:** Native `@Page` mentions linking to parent Units and Chapters. Add registered Concept Vault mentions only where the applicable workflow requires them.
- **Subsequent Result Sync:** The user will practice locally or in Practice Studio. The drill's `npm run submit` records timestamped test evidence and uses the canonical current-cycle scorer for the terminal and Notion summaries. A drill is Graded when every question has passing tests and a passing review in the current cycle, including assisted passes worth 0.5.

### 7. Strict Zero-Leak Placeholder & Hint Policy for Programming Drills
- **Anti-Spoiler Guardrail for Web Drills:** For `predict-output`, `code-tracing`, and conceptual triage questions rendered in Practice Studio:
  - `inputHint` is mapped directly to the interactive HTML input `placeholder`.
  - **Strictly Prohibited:** Never include the correct output token, HTTP status code, method, or sequence in `inputHint` or `placeholder`.
  - **Disjoint Counter-Examples:** If formatting examples are provided, they must be unrelated tokens or counter-examples from different domains.
    - *Bad (Leaking):* `"Type the 3-digit status code (e.g. 401)."` (when answer is 401)
    - *Good (Disjoint):* `"Enter 3-digit HTTP status code (e.g. 200, 500)"`
    - *Bad (Leaking):* `"Type the sequence: SYN -> SYN-ACK -> ACK"` (when that is the exact answer)
    - *Good (Disjoint):* `"Enter 3-packet flag sequence (e.g. AAA -> BBB -> CCC)"`
  - **Automated Validation Invariant:** `code_engine.ai_drill_ingest` runs `check_zero_leak_hint`; `notion_sync.drill_sync.validate_and_sanitize_drill_doc` validates/sanitizes before saving or syncing a drill to Notion.

### 8. Adaptive Choice vs. Input & Skip Telemetry Standards
- **Adaptive Question Decision Framework:** In programming drills, AI generator scripts must evaluate the learning objective of each problem:
  - Use `type: "choice"` with 4 options for:
    - Status code triage when comparing authentication vs. authorization (401 vs 403) or gateway failures (502 vs 504).
    - Conceptual questions where distinguishing subtle protocol transitions (e.g. WebSocket 101 vs 200 vs 301) requires evaluating precise statements.
    - Architecture triage: diagnosing whether an issue is caused by thread pool exhaustion, socket disconnection, or DNS resolution failure.
  - Use `answerSpec.type: "text"` / `predict_output` (underscore; curriculum practice labels may use `predict-output`) for:
    - Exact syntax parsing (HTTP method token, header name, status code number).
    - Sequential traces (TCP flag ordering, event loop execution order).
- **Skip Protocol Integration:**
  - Every programming drill supports the `Skip (Don't Know)` action in Practice Studio.
  - Skipped items are explicitly recorded in `sessionSummary.skippedProblems` and synchronized to Notion, ensuring that unlearned concepts are tracked as high-priority revision targets.

### 9. Anti-Spoonfeeding & Authentic Problem-Solving Standard
To foster genuine diagnostic intuition and systems-level debugging skills:
- **Zero Root-Cause Spoon-Feeding:** Prompts must specify observable behavioral symptoms, expected invariants, and SLA contracts. Never include `Defect Analysis:` or `Root Cause Analysis:` sections in debugging prompts that tell the learner what is wrong before they inspect the code.
- **Zero Inline Bug Pointer Comments:** Starter code must never contain comments like `// BUG:`, `// DEFECT:`, or `// FIX HERE:` marking the flaw. The learner must trace execution and diagnose root causes independently using the reproducer test.
- **Contract-Focused Hints:** Hints must prompt self-monitoring questions or highlight contract boundaries. Never name specific internal data structures (e.g. `secondary Map`, `use closure`, `new Map()`) that reduce the exercise to mechanical transcription.

### 10. Mutation Testing Standard (Anti-Green-Illusion Mandate)
- **Zero Green Illusion:** A test suite is only valid if it actively rejects incorrect or cheating implementations.
- **Automated Mutant Verification:** All suite-based programming exercises must undergo automated mutation testing during AI ingestion. Synthetic mutants (e.g. constant return `return true`, capacity bypass `tokens = capacity`, omission of failure counter reset, missing error cleanup) are executed against the suite.
- **Mandatory Mutant Killing:** If any mutant passes the test suite, the problem is rejected with `Anti-Green-Illusion Guard violated`. Authors must write stricter assertions, boundary checks, and state-transition tests.

### 11. Deterministic Clock Invariant for Time-Dependent Code
- **Zero Flaky Real-Time Execution:** Algorithms involving time (rate limiters, token buckets, cache expiration/TTL, circuit breaker cooldowns, exponential backoff) must accept an injectable clock (`options.now = Date.now`).
- **Test Suite Determinism:** Acceptance tests must manipulate simulated clock timestamps rather than relying on non-deterministic real-world `setTimeout` (> 50ms). This guarantees instantaneous (< 100ms), 100% reproducible test runs in CI/CD without timer jitter.

---

## PART 6 — Universal Five-Tier Milestone Taxonomy (Labs)

Every multi-milestone project lab adheres to a standardized milestone sequence:
- **M1 — Contracts & Schemas:** Domain models, TypeScript interfaces, DTOs, Zod schemas, invariant validators, configuration parsers.
- **M2 — Pure Business Logic & State Calculators:** Deterministic calculations, price/tax engines, state reducers, token parsers (strictly zero I/O side effects).
- **M3 — Stateful Services, Orchestration & State Machine:** Order lifecycle state machine, repository adapters, service coordination, API handlers.
- **M4 — Concurrency, Edge Cases & Resilience:** Atomic mutex locks, race condition prevention, transaction rollback on failure, malformed payload injections.
- **M5 (Optional) — Capstone End-to-End Workflow:** Smoke integration traversing all modules across realistic user journeys.

---

## PART 7 — Nine-Step AI Authoring Pipeline

For **PRG drills**, follow the `new-code-drill` skill (`.claude/skills/new-code-drill/SKILL.md`) and enforce all gates via `python -m code_engine.ai_drill_ingest --check <draft.json>` (scope & trap tag, starter compile & no-leak, reference green & starter red, `trapMutant` + generic mutants killed by hidden/visible tests, Layer 2 ESLint + `tsc`, Layer 3 `qualityChecks` rubric, `rules/07` mix, `blindSolve`, and `review`) before ingesting and syncing to Notion.

For **multi-milestone labs**, follow the `new-project` skill (`.claude/skills/new-project/SKILL.md`) and enforce all gates via `python -m code_engine.lab_ingest --check <lab_dir>` (config schema, `id_map` + Notion `Done`/`In progress` check for `extra-project`, rubric `qualityChecks`, reference visible+hidden+lint+`tsc`, stubs lint-clean & failing visible tests, per-milestone `trapMutant` caught by hidden tests, zero-leak, `blindSolve`, and `review`) before finalising (`python -m code_engine.lab_ingest <lab_dir>`) and syncing to Notion (`python -m notion_sync.lab_sync <lab_dir>`):
1. **Spec Definition:** Create `labs/<LAB_ID>/lab.config.json` (metadata, `scenario`, `unitsUsed`, milestones, `qualityChecks`, `examples`, `trapMutant`) and `README.md`.
2. **Reference & Hidden Tests:** Author complete, clean, production-grade reference implementation in `labs/_reference/<LAB_ID>/src/` and hidden trap/edge-case tests in `labs/_reference/<LAB_ID>/hidden/` (excluded from the learner's VS Code view via `.vscode/settings.json`).
3. **Visible Milestone Test Suites:** Author visible acceptance test suites in `labs/<LAB_ID>/tests/` importing from `process.env.LAB_SRC_DIR || "../src"`.
4. **Mandatory Pre-Execution Verification:** Run `node --experimental-strip-types --test` (or `vitest run` for `react-dom` labs) on the reference implementation via `npm run check:reference` and `npm run check:hidden` (plus ESLint + `tsc`). **Must exit with code 0 and 100% pass rate.**
5. **Scaffolding Starter Code:** Create starter stubs in `labs/<LAB_ID>/src/` with exported types/signatures, `_`-prefixed unused params, and `throw new Error("TODO [M1]: …");` bodies (ESLint-clean and `tsc`-clean).
6. **Package Scripts Configuration:** Configure `package.json` scripts (`test`, `test:reference`, `lint`, `typecheck`, `check`, `check:reference`, `check:hidden`, `review`, `submit`, plus per-milestone `test:mN`/`check:mN`).
7. **Baseline Negative & Gate Verification:** Run `python -m code_engine.lab_ingest --check labs/<LAB_ID>` to confirm stubs fail visible tests cleanly, `trapMutant` fails hidden tests, and blind-solve + reviewer gates pass, then finalise with `python -m code_engine.lab_ingest labs/<LAB_ID>`.
8. **Concept References:** Follow the task-specific Concept Vault instructions in `rules/00_core.md` §8; no blanket auto-link pass is implemented.
9. **Notion Registration:** Sync the pristine lab record to `Learning Practice & Drills` via `python -m notion_sync.lab_sync labs/<LAB_ID>` (`Format: "Code Test Suite"`).

---

## PART 8 — Terminal Telemetry Engine (`submit_lab.py`)

- **Standard Terminal Lifecycle:** Developer iterates locally with `npm test` (or `npm run test:watch`). Once milestones are implemented, developer runs `npm run submit`.
- **Partial Notion sync:** Pristine lab registration reports the failed page-content or cleanup step. Terminal drill and lab submission print **Synced with problems** with the failed steps. These commands exit with a nonzero status on a partial sync.
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
   - **JSON Data Layer (`drills/data/<UNIT>/`):** Content-only problem specifications and acceptance criteria, without learner state or HTML. Never store attempts, scores, or session summaries in drill files.
   - **Progress Layer (`progress/<DRILL_ID>.json`):** Learner attempts, scores, session summaries, and review state, managed by `progress_store.py` / Practice Studio (pilot data uses isolated `pilot/progress/`).
   - **Workspace Layer (`drills/workspace/<DRILL_ID>/` or `labs/<LAB_ID>/`):** Real TypeScript/Node workspaces on disk ready for your local IDE (e.g. VS Code).
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
- **Hidden Trap Tests (`hiddenTests`):** Stored in the drill JSON (`drills/data/<UNIT>/<DRILL_ID>.json`) for drills — or in `labs/_reference/<LAB_ID>/hidden/` for project labs — never materialized into the learner's drill workspace, and evaluated in an isolated temp directory during `npm run submit` / `code_engine.review_run`. Tests boundary invariants, scale limits, and poison payloads to verify true generalized logic.

### 3. Least-Privilege PRG Runner Isolation
All automated PRG execution paths (`practice-studio/src/app/api/run-tests/route.ts`, `practice-studio/src/app/api/review-run/route.ts`, `code_engine/test_runner.py`, `code_engine/submit.py`, `code_engine/review_run.py`, `code_engine/lab_ingest.py`, `code_engine/verify.py`, and `labs/common/submit_lab.py`) must execute learner and reference code through the shared sandbox helper (`code_engine/sandbox.py`; Studio spawns Python through `practice-studio/src/lib/runnerEnv.ts`):
- **Scrubbed environment:** Only an explicit allowlist (`PATH`, `HOME`, `TMPDIR`, locale/timezone, `CI`, `NO_COLOR`, and explicit non-secret vars like `LAB_SRC_DIR`) is passed to the child. Secrets (`NOTION_TOKEN`, `NOTION_DATABASE_ID`, API keys, `NODE_OPTIONS`) are never forwarded.
- **Per-run temp copy:** `cwd`, `HOME`, and `TMPDIR` point into an ephemeral per-run temp directory outside the repository. Workspaces and labs are copied into that temp directory before execution so learner code cannot mutate the repo, `progress/`, `sources/`, or `labs/`.
- **Resource & output bounds:** POSIX `resource.setrlimit` (`RLIMIT_CPU`, `RLIMIT_FSIZE`, `RLIMIT_NOFILE`, `RLIMIT_CORE`), V8 `--max-old-space-size`, wall-time deadlines with POSIX process-group cleanup (`SIGTERM` → `SIGKILL`), and capped stdout/stderr pipes prevent infinite loops and output floods.
- **Filesystem & network confinement:** Direct Node runs enable Node 24 `--permission` (`--allow-fs-read` / `--allow-fs-write` confined to the per-run sandbox; `child_process` and `worker_threads` disabled). On macOS, `/usr/bin/sandbox-exec` (Seatbelt) wraps all runners (including Vitest/ESLint/`tsc`) to confine writes to the per-run sandbox, deny reads of `.env`, `progress/`, and `sources/`, and block network access (allowing local Unix IPC). On Linux, `unshare -r -n` is applied when unprivileged user namespaces are permitted; where host policy restricts unprivileged user namespaces without root (e.g. AppArmor on Ubuntu CI), OS-level network blocking and Vitest-level OS write confinement cannot be enforced without root or containers and degrade to Node `--permission` (for direct Node runs), temp-copy `cwd`, scrubbed env, and POSIX `setrlimit`.
