# PRG Curriculum v2 — Design & Migration Proposal

**Status:** Draft for learner & Claude review (doc-only; no Notion writes, no `id_map.json` edits).  
**Date:** 2026-11-16  
**Target Cadence:** ~1.5 h/day for PRG (shared with math in a 3–4 h/day study block), 1–3 sessions per unit.

---

## 1. Summary

### Guiding Principles
1. **Depth & "how it works" over framework breadth:** Master JavaScript and TypeScript internals, recursion, Big-O intuition, and core data structures before touching React or Next.js.
2. **One language first:** Achieve fluency in JS/TS across runtime, frontend, backend, and databases; attach Python later as a clean second-language track.
3. **Test-first & rubric-reviewed:** Introduce unit testing right alongside JS/TS utilities, component testing inside React, and E2E testing during the capstone, enforced by the 3-layer review spec ([`docs/prg_reviewer_spec.md`](prg_reviewer_spec.md)).
4. **Two complementary project tracks:**
   - **Chapter Labs ("build it yourself"):** Implement a small working version of each tool before/while using the production library (e.g., event emitter, promise pool, LRU cache, tiny test runner, `node:http` router, middleware pipeline, query builder, session store, rate limiter, job queue).
   - **DevVault (continuous product):** Grow one personal snippets / bookmarks / study-notes application across every topic from CLI core to deployed full-stack app.
5. **7-section unit pages:** Every PRG unit page follows the 7-section standard (Core Concepts & Mental Model, Core Patterns with "Why this works" toggles, Worked Code Examples L1/L2/L3, Practice Guide, Active Recall toggles, My Implementation & Mistake Log, Completion Checklist).

### Unit Counts & Duration Arithmetic (at ~1.5 h/day)

- **v1 baseline:** 11 topics, 34 chapters, 243 units (`1 Done`, `7 Skip`, `235 Not started`).
- **v2 core track (`T00`–`T07`):** **8 topics, 26 chapters, 175 units** (`1 Done`, `7 Skip`, **167 active units**), plus **17 chapter labs** and **8 DevVault milestones**.
- **v2 extended track (`T08`–`T09`, optional after core):** **2 topics, 5 chapters, 35 active units**, plus **2 chapter labs** and **2 DevVault milestones**.
- **Total v2 (Core + Extended):** **10 topics, 31 chapters, 210 units** (`202 active` + `1 Done` + `7 Skip`).

**Estimated duration arithmetic (1 session = 1.5 h):**
- **Core concepts & drills:** `167 active units × 2.0 avg sessions/unit = 334 sessions` (`501 h`).
- **Chapter Labs (core):** `17 labs × 4.5 avg sessions/lab = 76.5 sessions` (`114.75 h`).
- **DevVault product milestones (core):** `8 milestones × 4.0 avg sessions/milestone = 32 sessions` (`48 h`).
- **Spaced review & PR-review rework buffer (~10%):** `44 sessions` (`66 h`).
- **Core Track (`T00`–`T07`) Total:** `334 + 76.5 + 32 + 44 = 486.5 sessions` = **~730 hours** ≈ **~16.0 months** at 1.5 h/day (7 days/week) or **~18.7 months** at 6 days/week.
- **Extended Track (`T08`–`T09`):** `35 units × 2.0 (70) + 2 labs × 5.0 (10) + 2 DevVault × 4.0 (8) + 9 buffer = 97 sessions` = **~145.5 hours** ≈ **~3.2 months** (7 days/week).
- **Full v2 Total:** `583.5 sessions` = **~875 hours** ≈ **~19.2–22.4 months** (fitting inside a 2–3 year CS study plan alongside Math and Python).

### What Changed and Why (One Line Each)
- **Moved Git/Workflow before JS baseline (`T00-C02`):** Learners need terminal, npm, branching, and PR habits before writing their first drill or lab.
- **Shrank `T00` JS/TS baseline (`T00-C03`, 7 → 4 units):** Removed duplication with `T01` so `T00` acts purely as a fast diagnostic check.
- **Added CS fundamentals to `T01` (`T01-C03`, 7 units):** Added Big-O intuition, recursion, stacks/queues, linked lists, trees, graphs, and `AbortController` cancellation (`T01-C01-U09`).
- **Pulled unit testing into `T01-C04` and component testing into `T02-C06`:** Learners test their own utilities and React components immediately instead of waiting until Topic 8.
- **Moved Node/Express (`T03`), PostgreSQL (`T04`), and Auth/Security (`T05`) before Next.js (`T06`):** Understanding HTTP, SQL, and sessions first makes Next.js Server Components and Route Handlers transparent rather than magical.
- **Added raw `pg` + pooling + parameterized queries before Prisma (`T04-C02-U05`):** Learners see real SQL, connection pools, and `$1` placeholders before using an ORM.
- **Split CORS vs. Security Headers and added Rate Limiting (`T05-C02`):** Gives each security control its own mental model and drillable boundary.
- **Replaced `T07` (27 generic product-management units) with a 5-milestone DevVault project track + E2E (`T07`):** Replaces passive reading with building and testing one real product.
- **Moved System Design/Redis/Realtime (`T08`) and Docker/CI/Cloud (`T09`) to Extended:** Keeps the core path focused on language, web, backend, DB, and security depth.
- **Applied technical accuracy fixes with primary sources:** Next.js 15+ uncached defaults, Express 5 native async error forwarding, OWASP Argon2id password storage, SameSite + Origin CSRF defense, MDN Semantic HTML & ARIA, and Docker Compose v2 (`docker compose`).

---

## 2. Code Strategy: Renumber (A) vs. Keep Codes + Sequence Property (B)

Today, `PRG-*` codes encode study order (e.g., `PRG-T03` is Next.js, `PRG-T08` is Testing). Moving Next.js after Auth/Security and pulling Testing into `T01`/`T02` forces a choice.

### Files Currently Referencing `PRG-` Codes (from `git grep -l "PRG-"`)
Excluding `archive/` (one-shot legacy scripts) and `tests/fixtures/legacy_drills/`:
- **Registry & Taxonomy:** `id_map.json` (288 `PRG-*` keys), `skills_taxonomy.json`
- **Reasoning Vaults & Templates:** `code_engine/reasoning_vault/PRG-T00-C02.json`, `PRG-T01-C01.json`, `PRG-T01-C03.json`; `code_engine/templates/prg_t01_c01.py`, `prg_t01_c03.py`
- **Drills & Progress:** `drills/data/PRG-T00-C02/DRL-PRG-T00-C02-02.json`, `drills/prg_t03_c01_u01_drill.ts`, `progress/DRL-PRG-T00-C02-02.json` (gitignored local progress)
- **Labs:** `labs/LAB-PRG-T03-C01-01/lab.config.json`, `labs/LAB-PRG-T03-C01-01/package.json`, `archive/AI_LAB_RULES_AND_FLOW_DRAFT.md` (superseded draft)
- **Engine, Studio & Scripts:** `code_engine/ai_drill_ingest.py`, `code_engine/generate.py`, `code_engine/lint_check.py`, `code_engine/review_run.py`, `code_engine/submit.py`, `notion_sync/drill_sync.py`, `practice-studio/src/app/api/drills/route.ts`, `practice-studio/src/app/api/generate-drill/route.ts`, `practice-studio/src/app/page.tsx`, `practice-studio/tests/progress.test.ts`, `scripts/benchmark_templates.py`, `scripts/benchmark_results.json`, `scripts/coverage_report.py`, `scripts/weak_spots.py`
- **Docs, Rules & Tests:** `CLAUDE.md`, `docs/prg_reviewer_spec.md`, `.claude/skills/review-code/SKILL.md`, `.github/workflows/ci.yml`, `reports/coverage.md`, `rules/01_arch.md`, `rules/05_qa.md`, `math_engine/templates/mth_t02_c01_u01.py`, and 10 `tests/test_*.py` files.

### Comparison

| Dimension | Option A: Renumber `PRG-T*` / `C*` / `U*` to v2 Order | Option B: Keep Existing Codes + Add `Sequence` Property |
| :--- | :--- | :--- |
| **Mental Clarity** | High: `T01` → `T09` always matches study order, folder names, and drill IDs. | Low: learner studies `T08-C01` inside `T01` and `T03` after `T06`. |
| **Notion Migration Cost** | Scripted update of ~210 v2 Notion page titles + archiving/removing ~33 removed/merged units, then regenerating `id_map.json` PRG keys. | Zero title renames; add one `Sequence` number property in Notion; create new pages for `NEW` units. |
| **Local Repo Cost** | Rename 3 vaults, 2 templates, 1 live drill folder, and 1 lab (`LAB-PRG-T03-C01-01` → `LAB-PRG-T06-C01-01`), plus update `id_map.json` via script. | Zero renames of existing files; `T00-C02` / `T01-C03` stay as-is. |
| **Long-Term Maintenance** | Clean for the next 2–3 years of drills, labs, and `@Page` mentions. | Every new agent/skill must remember to sort by `Sequence` instead of code. |

### Recommendation: **Option A (Renumber now)**
Because only **1 unit** (`PRG-T00-C01-U01`) is `Done`, only **3 vaults** and **1 live drill** exist, and `T01`–`T10` have not been started yet, the one-time migration cost is tiny. Keeping `PRG-T03` = Next.js while studying it 6th would create permanent confusion across drill IDs, lab folders, and `@Page` mentions for the next 2+ years. *(All tables below list both `v2 Code` and `Old Code(s)` so Option B remains trivial if zero-churn is preferred.)*

---

## 3. Full Curriculum Outline (v2)

**Practice Type Legend:**
`drill: predict-output` · `drill: fix-bug` · `drill: implement-with-tests` · `drill: refactor` · `drill: trace-explain` · `lab milestone` · `project milestone` · `reading-only`

### PRG-T00 — Foundation Audit & Developer Workflow (18 units: 1 Done, 7 Skip, 10 Active)

#### PRG-T00-C01 — Web Platform Fundamentals *(Keep statuses as-is)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T00-C01-U01` | How the Web Works | Given a URL entry, trace DNS, TCP/TLS, and HTTP request/response flow. | Annotated request lifecycle note | `reading-only` | — | `PRG-T00-C01-U01` `[Done]` |
| `PRG-T00-C01-U02` | Semantic HTML | Given a page wireframe, choose semantic landmark and control elements. | Semantic HTML outline | `reading-only` | `PRG-T00-C01-U01` | `PRG-T00-C01-U02` `[Skip]` |
| `PRG-T00-C01-U03` | CSS Fundamentals | Given conflicting CSS rules, predict specificity and cascade winners. | Specificity resolution note | `reading-only` | `PRG-T00-C01-U02` | `PRG-T00-C01-U03` `[Skip]` |
| `PRG-T00-C01-U04` | Box Model and Layout | Given box dimensions and `box-sizing`, calculate rendered width and spacing. | Box-sizing calculation note | `reading-only` | `PRG-T00-C01-U03` | `PRG-T00-C01-U04` `[Skip]` |
| `PRG-T00-C01-U05` | Flexbox and Grid | Given a 1D or 2D layout target, select Flexbox or Grid properties. | Layout mapping note | `reading-only` | `PRG-T00-C01-U04` | `PRG-T00-C01-U05` `[Skip]` |
| `PRG-T00-C01-U06` | Responsive Design | Given viewport breakpoints, adapt layout rules using fluid units and media queries. | Responsive breakpoint spec | `reading-only` | `PRG-T00-C01-U05` | `PRG-T00-C01-U06` `[Skip]` |
| `PRG-T00-C01-U07` | Accessibility and Keyboard Navigation | Given an interactive widget, identify keyboard focus order and label requirements. | Keyboard audit checklist | `reading-only` | `PRG-T00-C01-U02` | `PRG-T00-C01-U07` `[Skip]` |
| `PRG-T00-C01-U08` | Browser DevTools | Given a broken layout or failed request, inspect DOM, Styles, and Network panels. | DevTools triage note | `reading-only` | `PRG-T00-C01-U01` | `PRG-T00-C01-U08` `[Skip]` |

#### PRG-T00-C02 — Developer Workflow & Git *(Moved first before JS/TS baseline)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T00-C02-U01` | Terminal and Project Structure | Given a fresh project directory, navigate, inspect, and organize files via shell commands. | Clean workspace directory tree | `drill: implement-with-tests` | — | `PRG-T00-C03-U01` `[MOVED]` |
| `PRG-T00-C02-U02` | npm and Package Scripts | Given a `package.json`, install dependencies, run scripts, and explain lockfiles. | Working `package.json` + scripts | `drill: fix-bug` | `PRG-T00-C02-U01` | `PRG-T00-C03-U02` `[MOVED]` |
| `PRG-T00-C02-U03` | Git Repository Basics | Given local file changes, stage, commit, and inspect history/diff cleanly. | Clean commit history on repo | `drill: trace-explain` | `PRG-T00-C02-U01` | `PRG-T00-C03-U03` `[MOVED]` |
| `PRG-T00-C02-U04` | Branches, Commits and Merge | Given a feature task and a branch conflict, branch, commit, and resolve merge conflicts. | Resolved merge on feature branch | `drill: fix-bug` | `PRG-T00-C02-U03` | `PRG-T00-C03-U04` `[MOVED]` |
| `PRG-T00-C02-U05` | GitHub Workflow and Pull Requests | Given a completed branch, push, open a PR, and respond to review feedback. | Open PR with clean diff | `project milestone` | `PRG-T00-C02-U04` | `PRG-T00-C03-U05` `[MOVED]` |
| `PRG-T00-C02-U06` | README and Issue Tracking | Given a starter project, write setup docs and actionable issue/PR descriptions. | `README.md` for DevVault | `project milestone` | `PRG-T00-C02-U05` | `PRG-T00-C03-U06` `[MOVED]` |

#### PRG-T00-C03 — JavaScript & TypeScript Baseline Check *(Diagnostic only; deduped from T01)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T00-C03-U01` | Variables, Types & Control Flow Check | Given JS expressions with coercion and nullish values, predict outputs and fix edge bugs. | Passing diagnostic drill | `drill: predict-output` | `PRG-T00-C02-U02` | `PRG-T00-C02-U01` `[MOVED]` |
| `PRG-T00-C03-U02` | Functions, Arrays & Objects Check | Given domain records, write pure transformations without mutating inputs. | Passing diagnostic drill | `drill: implement-with-tests` | `PRG-T00-C03-U01` | `PRG-T00-C02-U02` + `U03` `[MERGED]` |
| `PRG-T00-C03-U03` | Async & DOM Events Check | Given an async fetch/event snippet, predict execution order and fix unhandled rejections. | Passing diagnostic drill | `drill: fix-bug` | `PRG-T00-C03-U02` | `PRG-T00-C02-U04` + `U05` `[MERGED]` |
| `PRG-T00-C03-U04` | TypeScript & Debugging Baseline | Given untyped buggy JS code and a failing test, add TS types and fix the root cause. | Passing strict `tsc` + test | `drill: fix-bug` | `PRG-T00-C03-U03` | `PRG-T00-C02-U06` + `U07` `[MERGED]` |

---

### PRG-T01 — JavaScript, TypeScript, Data Structures & Unit Testing (31 units)

#### PRG-T01-C01 — JavaScript Execution & Async Internals
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T01-C01-U01` | Execution Context and Scope | Given nested blocks and declarations, trace lexical scope and TDZ errors. | Exact stdout/error trace | `drill: trace-explain` | `PRG-T00-C03-U02` | `PRG-T01-C01-U01` `[KEPT]` |
| `PRG-T01-C01-U02` | Closures | Given a stateful factory or loop callback, trace captured bindings and prevent stale state. | Passing closure module | `drill: implement-with-tests` | `PRG-T01-C01-U01` | `PRG-T01-C01-U02` `[KEPT]` |
| `PRG-T01-C01-U03` | `this` and Binding | Given method/callback calls, predict `this` binding and fix lost context bugs. | Fixed binding tests | `drill: fix-bug` | `PRG-T01-C01-U02` | `PRG-T01-C01-U03` `[KEPT]` |
| `PRG-T01-C01-U04` | Prototypes and Inheritance | Given a prototype chain, trace property lookup and avoid shared mutable prototype state. | Passing class/prototype tests | `drill: trace-explain` | `PRG-T01-C01-U03` | `PRG-T01-C01-U04` `[KEPT]` |
| `PRG-T01-C01-U05` | Modules and Module Systems | Given ESM/CJS files, structure exports cleanly and resolve circular import bugs. | Clean ESM module graph | `drill: fix-bug` | `PRG-T01-C01-U01` | `PRG-T01-C01-U05` `[KEPT]` |
| `PRG-T01-C01-U06` | Promises and Async/Await | Given concurrent async tasks, compose `Promise.all`/`allSettled`/`race` without sequential bottlenecks. | Passing async coordinator | `drill: implement-with-tests` | `PRG-T01-C01-U02` | `PRG-T01-C01-U06` `[KEPT]` |
| `PRG-T01-C01-U07` | Event Loop and Microtasks | Given timers, promises, and sync logs, predict exact microtask/macrotask execution order. | Exact execution order trace | `drill: predict-output` | `PRG-T01-C01-U06` | `PRG-T01-C01-U07` `[KEPT]` |
| `PRG-T01-C01-U08` | Error Handling Patterns | Given failing sync/async boundaries, propagate typed errors without swallowing causes. | Passing error-path suite | `drill: refactor` | `PRG-T01-C01-U06` | `PRG-T01-C01-U08` `[KEPT]` |
| `PRG-T01-C01-U09` | AbortController & Cancellation | Given a long-running async operation, cancel in-flight work cleanly via `AbortSignal`. | Lab 1 (`TinyEventEmitter` + `PromisePool`) | `lab milestone` | `PRG-T01-C01-U06`, `U08` | `NEW` |

#### PRG-T01-C02 — TypeScript for Application Code
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T01-C02-U01` | Type Annotations and Inference | Given functions and literals, let inference work and annotate public boundaries. | Zero-`any` typed module | `drill: implement-with-tests` | `PRG-T00-C03-U04` | `PRG-T01-C02-U01` `[KEPT]` |
| `PRG-T01-C02-U02` | Primitive, Literal and Object Types | Given domain entities, model `readonly` properties, `as const`, and exact object shapes. | Domain type definitions | `drill: implement-with-tests` | `PRG-T01-C02-U01` | `PRG-T01-C02-U02` `[KEPT]` |
| `PRG-T01-C02-U03` | Union Types | Given multi-shape inputs, model unions instead of optional-property bags. | Typed union model | `drill: refactor` | `PRG-T01-C02-U02` | `PRG-T01-C02-U03` `[KEPT]` |
| `PRG-T01-C02-U04` | Type Narrowing and Guards | Given `unknown` or union inputs, narrow safely with type predicates and `in`/`typeof`. | Type-safe parser functions | `drill: implement-with-tests` | `PRG-T01-C02-U03` | `PRG-T01-C02-U04` `[KEPT]` |
| `PRG-T01-C02-U05` | Generics | Given reusable data structures/functions, constrain generic type parameters accurately. | Generic utility module | `drill: implement-with-tests` | `PRG-T01-C02-U04` | `PRG-T01-C02-U05` `[KEPT]` |
| `PRG-T01-C02-U06` | Utility Types | Given existing domain types, derive DTOs using `Pick`, `Omit`, `Partial`, and `Record`. | Derived DTO types | `drill: refactor` | `PRG-T01-C02-U05` | `PRG-T01-C02-U06` `[KEPT]` |
| `PRG-T01-C02-U07` | Discriminated Unions | Given state machines or API results, enforce exhaustive handling with `never` checks. | Exhaustive reducer/handler | `drill: implement-with-tests` | `PRG-T01-C02-U03` | `PRG-T01-C02-U07` `[KEPT]` |
| `PRG-T01-C02-U08` | Strict Mode and `tsconfig` | Given a loose `tsconfig`, enable `strict` flags and fix `strictNullChecks`/`noUncheckedIndexedAccess` errors. | Passing `tsc --strict` build | `drill: fix-bug` | `PRG-T01-C02-U04` | `PRG-T01-C02-U08` `[KEPT]` |
| `PRG-T01-C02-U09` | Typing Functions and API Responses | Given external JSON payloads, separate `unknown` wire input from validated domain types. | Lab 2 (`Result` + `MiniSchema`) | `lab milestone` | `PRG-T01-C02-U07`, `U08` | `PRG-T01-C02-U09` `[KEPT]` |

#### PRG-T01-C03 — Recursion, Complexity & Core Data Structures *(New CS depth chapter)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T01-C03-U01` | Big-O Intuition & Time/Space Tradeoffs | Given two implementations (e.g., nested loop vs. index lookup), classify time/space complexity and fix $O(N^2)$ bottlenecks. | Optimized $O(N)$ function | `drill: refactor` | `PRG-T01-C02-U01` | `NEW` |
| `PRG-T01-C03-U02` | Recursion & Call-Stack Tracing | Given nested structures or recursive rules, trace base cases, stack frames, and termination. | Passing recursive solver | `drill: trace-explain` | `PRG-T01-C01-U01`, `T01-C03-U01` | `NEW` |
| `PRG-T01-C03-U03` | Arrays, Stacks & Queues | Given bracket matching or task scheduling, implement LIFO stacks and FIFO queues cleanly. | Stack/queue module + tests | `drill: implement-with-tests` | `PRG-T01-C03-U01` | `NEW` |
| `PRG-T01-C03-U04` | `Map`, `Set` & Hashing Patterns | Given frequency counting, grouping, or dedupe tasks, choose `Map`/`Set` over plain objects. | Indexed lookup utilities | `drill: implement-with-tests` | `PRG-T01-C03-U01` | `PRG-T01-C03-U04` `[MOVED]` |
| `PRG-T01-C03-U05` | Linked Lists & Pointer Manipulation | Given insertion/deletion requirements, implement a singly/doubly linked list without losing head/tail invariants. | Linked list + pointer tests | `drill: implement-with-tests` | `PRG-T01-C03-U03` | `NEW` |
| `PRG-T01-C03-U06` | Trees & Tree Traversals (DFS / BFS) | Given a hierarchical tree (DOM/folders/categories), traverse via DFS and BFS and compute aggregates. | Tree traversal utilities | `drill: implement-with-tests` | `PRG-T01-C03-U02`, `U03` | `NEW` |
| `PRG-T01-C03-U07` | Graphs & Shortest-Path Basics | Given dependency or route edges, detect cycles and find shortest unweighted paths via BFS. | Lab 3 (`LRUCache` + `TreeIndex`) | `lab milestone` | `PRG-T01-C03-U04`, `U05`, `U06` | `NEW` |

#### PRG-T01-C04 — Problem Solving, Clean Utilities & Unit Testing *(Merged `T01-C03` + `T08-C01`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T01-C04-U01` | Problem Decomposition & Data Pipelines | Given multi-rule business specs, decompose into pure, single-job array/object pipeline steps. | Clean multi-step pipeline | `drill: refactor` | `PRG-T01-C02-U05`, `T01-C03-U04` | `PRG-T01-C03-U01..U03` `[MERGED]` |
| `PRG-T01-C04-U02` | Reusable Generic Utilities & Edge Cases | Given boundary inputs (empty, `0`, `NaN`, cycles), build safe generic helpers. | Edge-hardened utility module | `drill: implement-with-tests` | `PRG-T01-C04-U01` | `PRG-T01-C03-U05` + `U06` `[MERGED]` |
| `PRG-T01-C04-U03` | Testing Pyramid & Pure Unit Tests | Given pure functions, write deterministic `node:test` suites covering happy, boundary, and invariant cases. | Passing `node:test` suite | `drill: implement-with-tests` | `PRG-T01-C04-U01` | `PRG-T01-C03-U07` + `T08-C01-U01..U02` `[MERGED]` |
| `PRG-T01-C04-U04` | Test Doubles: Stubs, Mocks & Fakes | Given time- or I/O-dependent code, inject fake clocks and stubs without brittle over-mocking. | Deterministic clock/stub tests | `drill: refactor` | `PRG-T01-C04-U03` | `PRG-T08-C01-U03` `[MOVED]` |
| `PRG-T01-C04-U05` | Error Paths, Fixtures & Test Quality | Given legacy code, write regression fixtures, test error branches, and kill weak assertions. | Lab 4 (`TinyTestRunner` + `DeepClone`) | `lab milestone` | `PRG-T01-C04-U04` | `PRG-T08-C01-U05..U07` `[MERGED]` |
| `PRG-T01-C04-U06` | Packaging, Exports & DevVault Core | Given a tested TS library, configure exports/docs and ship `devvault-core` v1. | `devvault-core` + unit tests | `project milestone` | `PRG-T01-C04-U05` | `PRG-T01-C03-U08` `[MOVED]` |

---

### PRG-T02 — Frontend Engineering with React & Component Testing (38 units)

#### PRG-T02-C01 — React Mental Model & Component Architecture
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T02-C01-U01` | JSX and Component Basics | Given UI data, render pure functional components with typed props. | Typed React component | `drill: implement-with-tests` | `PRG-T01-C02-U02` | `PRG-T02-C01-U01` `[KEPT]` |
| `PRG-T02-C01-U02` | Props and Component Composition | Given nested UI variants, compose with `children` and slots instead of prop-drilling flags. | Composable UI layout | `drill: refactor` | `PRG-T02-C01-U01` | `PRG-T02-C01-U02` `[KEPT]` |
| `PRG-T02-C01-U03` | State and Event Handling | Given user interactions, manage `useState` and avoid derived-state duplication. | Interactive stateful widget | `drill: implement-with-tests` | `PRG-T02-C01-U01` | `PRG-T02-C01-U03` `[KEPT]` |
| `PRG-T02-C01-U04` | State Updates and Immutability | Given nested state updates or stale closures, apply functional updaters and immutable patterns. | Fixed state update bugs | `drill: fix-bug` | `PRG-T02-C01-U03` | `PRG-T02-C01-U05` `[MOVED]` |
| `PRG-T02-C01-U05` | Effects and Synchronization | Given external subscriptions or timers, synchronize via `useEffect` with cleanup and avoid effect abuse. | Clean effect + cleanup test | `drill: fix-bug` | `PRG-T02-C01-U04` | `PRG-T02-C01-U06` `[MOVED]` |
| `PRG-T02-C01-U06` | Refs and DOM Access | Given focus/scroll/imperative needs, use `useRef` without breaking React's render model. | Focus-managed component | `drill: implement-with-tests` | `PRG-T02-C01-U05` | `PRG-T02-C01-U07` `[MOVED]` |
| `PRG-T02-C01-U07` | Custom Hooks | Given repeated stateful logic, extract a typed custom hook with clear contracts. | Lab 5 (`MiniStore` + `useStore`) | `lab milestone` | `PRG-T02-C01-U05`, `U06` | `PRG-T02-C01-U08` `[MOVED]` |
| `PRG-T02-C01-U08` | Rendering, Re-renders & Component Boundaries | Given a slow component tree, trace render triggers and isolate state at the right boundary. | Refactored render boundary | `drill: refactor` | `PRG-T02-C01-U07` | `PRG-T02-C01-U04` + `U09` + `T02-C05-U01..U02` `[MERGED]` |

#### PRG-T02-C02 — Client State & Server State
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T02-C02-U01` | Local State vs Server State | Given app state requirements, separate ephemeral UI state from cached remote data. | State ownership table | `drill: trace-explain` | `PRG-T02-C01-U08` | `PRG-T02-C02-U01` `[KEPT]` |
| `PRG-T02-C02-U02` | Fetching Data and Async UI States | Given an async endpoint, handle loading, error, empty, and `AbortController` race conditions. | Race-free async loader | `drill: fix-bug` | `PRG-T01-C01-U09`, `T02-C02-U01` | `PRG-T02-C02-U02` `[KEPT]` |
| `PRG-T02-C02-U03` | Caching and Query Keys | Given parameterized queries, design deterministic query keys and stale-time policies. | Query key & cache config | `drill: implement-with-tests` | `PRG-T02-C02-U02` | `PRG-T02-C02-U03` `[KEPT]` |
| `PRG-T02-C02-U04` | Refetching and Cache Invalidation | Given a mutation, invalidate affected query keys without over-fetching. | Invalidation handler | `drill: implement-with-tests` | `PRG-T02-C02-U03` | `PRG-T02-C02-U04` `[KEPT]` |
| `PRG-T02-C02-U05` | Mutations and Optimistic Updates | Given a toggle/create action, apply optimistic UI with deterministic rollback on error. | Optimistic update + rollback | `drill: implement-with-tests` | `PRG-T02-C02-U04` | `PRG-T02-C02-U05` `[KEPT]` |
| `PRG-T02-C02-U06` | Pagination and Filtering | Given large lists, sync filter/cursor params with URL and query cache keys. | Paginated filter view | `drill: implement-with-tests` | `PRG-T02-C02-U03` | `PRG-T02-C02-U06` `[KEPT]` |
| `PRG-T02-C02-U07` | Error and Retry Strategies | Given transient vs 4xx failures, configure bounded retries and fallback UI. | Lab 6 (`TinyQueryCache`) | `lab milestone` | `PRG-T02-C02-U05`, `U06` | `PRG-T02-C02-U07` `[KEPT]` |

#### PRG-T02-C03 — Forms, Validation & Data UX
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T02-C03-U01` | Controlled and Uncontrolled Inputs | Given form fields, choose controlled vs uncontrolled inputs and avoid mixed-mode warnings. | Clean input components | `drill: fix-bug` | `PRG-T02-C01-U03` | `PRG-T02-C03-U01` `[KEPT]` |
| `PRG-T02-C03-U02` | Form State and Submission | Given a multi-field form, track dirty/touched/submitting states and prevent double submits. | Submission state guard | `drill: implement-with-tests` | `PRG-T02-C03-U01` | `PRG-T02-C03-U02` `[KEPT]` |
| `PRG-T02-C03-U03` | Schema Validation with Zod | Given form/API rules, author Zod schemas and infer TypeScript types cleanly. | Zod schema + inferred types | `drill: implement-with-tests` | `PRG-T01-C02-U09`, `T02-C03-U02` | `PRG-T02-C03-U03` `[KEPT]` |
| `PRG-T02-C03-U04` | Field-level and Form-level Errors | Given validation failures, map Zod issues to specific fields and form banners. | Error mapper utility | `drill: implement-with-tests` | `PRG-T02-C03-U03` | `PRG-T02-C03-U04` `[KEPT]` |
| `PRG-T02-C03-U05` | React Hook Form Fundamentals | Given a complex form, wire React Hook Form with a Zod resolver. | Typed RHF form | `drill: implement-with-tests` | `PRG-T02-C03-U04` | `PRG-T02-C03-U05` `[KEPT]` |
| `PRG-T02-C03-U06` | Async Validation | Given uniqueness checks, validate asynchronously with debounce and `AbortSignal`. | Debounced async validator | `drill: implement-with-tests` | `PRG-T02-C03-U05` | `PRG-T02-C03-U06` `[KEPT]` |
| `PRG-T02-C03-U07` | Accessible Form UX | Given form errors, bind `aria-invalid`, `aria-describedby`, and focus-on-first-error. | Lab 7 (`MiniFormEngine`) | `lab milestone` | `PRG-T02-C03-U04`, `U06` | `PRG-T02-C03-U07` `[KEPT]` |

#### PRG-T02-C04 — UI Engineering, Responsive Design & Accessibility
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T02-C04-U01` | Design Tokens and Visual Consistency | Given UI specs, define spacing, typography, and semantic color tokens. | Token CSS/TS config | `drill: refactor` | `PRG-T02-C01-U02` | `PRG-T02-C04-U01` `[KEPT]` |
| `PRG-T02-C04-U02` | Tailwind Fundamentals | Given a component mockup, compose utility classes cleanly without unreadable class soup. | Styled UI primitives | `drill: implement-with-tests` | `PRG-T02-C04-U01` | `PRG-T02-C04-U02` `[KEPT]` |
| `PRG-T02-C04-U03` | Responsive Layout Patterns | Given mobile and desktop viewports, build fluid grid/sidebar layouts. | Responsive shell layout | `drill: implement-with-tests` | `PRG-T02-C04-U02` | `PRG-T02-C04-U03` `[KEPT]` |
| `PRG-T02-C04-U04` | Component Variants and States | Given button/badge states, model typed variants (`disabled`, `loading`, `error`). | Typed variant component | `drill: implement-with-tests` | `PRG-T02-C04-U02` | `PRG-T02-C04-U04` `[KEPT]` |
| `PRG-T02-C04-U05` | Keyboard and Focus Management | Given dialogs/menus, implement focus trapping, `Escape` close, and focus restoration. | Keyboard-navigable dialog | `drill: fix-bug` | `PRG-T02-C01-U06` | `PRG-T02-C04-U05` `[KEPT]` |
| `PRG-T02-C04-U06` | Semantic HTML & ARIA | Given custom interactive widgets, prefer native HTML elements and apply valid WAI-ARIA roles/states ([MDN ARIA](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA)). | Lab 8 (`AccessibleDialog` + `Combobox`) | `lab milestone` | `PRG-T02-C04-U05` | `PRG-T02-C04-U06` `[KEPT, RENAMED]` |
| `PRG-T02-C04-U07` | Dark Mode and Theming | Given theme preferences, switch semantic CSS variables without FOUC or contrast regressions. | Theme-aware token sheet | `drill: implement-with-tests` | `PRG-T02-C04-U01` | `PRG-T02-C04-U07` `[KEPT]` |

#### PRG-T02-C05 — Frontend Performance
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T02-C05-U01` | Memoization: When and Why | Given a profiler trace, apply `React.memo`, `useMemo`, and `useCallback` only where measured. | Targeted memoization fix | `drill: refactor` | `PRG-T02-C01-U08` | `PRG-T02-C05-U03` `[MOVED]` |
| `PRG-T02-C05-U02` | Code Splitting and Lazy Loading | Given heavy routes/panels, split bundles with `React.lazy` and `Suspense` fallbacks. | Lazy-loaded route module | `drill: implement-with-tests` | `PRG-T02-C05-U01` | `PRG-T02-C05-U04` `[MOVED]` |
| `PRG-T02-C05-U03` | Image and Asset Optimization | Given media-heavy pages, prevent CLS and optimize loading priority/formats. | CLS-safe media component | `drill: fix-bug` | `PRG-T02-C05-U02` | `PRG-T02-C05-U05` `[MOVED]` |
| `PRG-T02-C05-U04` | Performance Measurement & Architecture | Given a sluggish list/tree, profile render commits and apply virtualization/splitting. | Lab 9 (`VirtualizedList`) | `lab milestone` | `PRG-T02-C05-U01..U03` | `PRG-T02-C05-U06` + `U07` `[MERGED]` |

#### PRG-T02-C06 — React Component Testing *(Moved from `T08-C02`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T02-C06-U01` | Testing Library Philosophy & Role Queries | Given a React component, query by accessible role/label instead of internal selectors. | Role-based query test suite | `drill: refactor` | `PRG-T01-C04-U03`, `T02-C04-U06` | `PRG-T08-C02-U01` + `U02` `[MERGED]` |
| `PRG-T02-C06-U02` | Testing User Interactions | Given interactive controls, simulate realistic `userEvent` clicks, typing, and keyboard nav. | Interaction test suite | `drill: implement-with-tests` | `PRG-T02-C06-U01` | `PRG-T08-C02-U03` `[MOVED]` |
| `PRG-T02-C06-U03` | Testing Forms and Validation | Given a Zod-validated form, assert field errors, disabled submit states, and valid submits. | Form test suite | `drill: implement-with-tests` | `PRG-T02-C03-U05`, `T02-C06-U02` | `PRG-T08-C02-U04` `[MOVED]` |
| `PRG-T02-C06-U04` | Async UI Testing | Given async data fetching, test loading, success, and error states with mocked network boundaries. | Async UI test suite | `drill: implement-with-tests` | `PRG-T02-C02-U02`, `T02-C06-U02` | `PRG-T08-C02-U05` `[MOVED]` |
| `PRG-T02-C06-U05` | Accessibility Assertions & DevVault Web | Given `devvault-web`, assert accessible states and ship the React SPA milestone. | `devvault-web` SPA + tests | `project milestone` | `PRG-T02-C06-U03`, `U04` | `PRG-T08-C02-U06` `[MOVED]` |

---

### PRG-T03 — Backend Engineering: Node.js, HTTP & Express 5 (21 units)

#### PRG-T03-C01 — Node Runtime, Raw HTTP & API Design *(Moved from `T04-C01`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T03-C01-U01` | Node.js Runtime and Event Loop | Given CPU vs I/O tasks in Node, predict libuv/event-loop blocking and non-blocking behavior. | Event loop trace note | `drill: trace-explain` | `PRG-T01-C01-U07` | `PRG-T04-C01-U01` `[MOVED]` |
| `PRG-T03-C01-U02` | Node Modules and Process Env | Given a Node CLI/server, read `process.env`, handle signals, and structure ESM entrypoints. | Bootstrapped Node entrypoint | `drill: implement-with-tests` | `PRG-T03-C01-U01` | `PRG-T04-C01-U02` `[MOVED]` |
| `PRG-T03-C01-U03` | Raw HTTP Server with `node:http` | Given `IncomingMessage` and `ServerResponse`, parse URLs/JSON bodies and write responses on `node:http`. | Lab 10 (`RawHttpRouter`) | `lab milestone` | `PRG-T03-C01-U02` | `PRG-T04-C01-U03` `[MOVED]` |
| `PRG-T03-C01-U04` | Methods, Status Codes and Headers | Given HTTP scenarios, choose idempotent methods, exact status codes, and content headers. | HTTP status/method triage | `drill: predict-output` | `PRG-T03-C01-U03` | `PRG-T04-C01-U04` `[MOVED]` |
| `PRG-T03-C01-U05` | REST Resource Design | Given domain entities, design noun-based endpoints, sub-resources, and query conventions. | REST endpoint spec | `drill: refactor` | `PRG-T03-C01-U04` | `PRG-T04-C01-U05` `[MOVED]` |
| `PRG-T03-C01-U06` | API Response and Error Conventions | Given success/failure cases, standardize JSON envelopes and problem-details error shapes. | Error envelope module | `drill: implement-with-tests` | `PRG-T03-C01-U05` | `PRG-T04-C01-U06` `[MOVED]` |
| `PRG-T03-C01-U07` | Async I/O and Stream Error Handling | Given file/network streams, handle backpressure and `error` events without crashing the process. | Safe stream pipe utility | `drill: fix-bug` | `PRG-T03-C01-U03` | `PRG-T04-C01-U07` `[MOVED]` |

#### PRG-T03-C02 — Express 5, Middleware & Validation *(Moved from `T04-C02`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T03-C02-U01` | Express 5 Application Setup | Given an Express 5 app, configure JSON parsing, health routes, and graceful shutdown. | Express 5 app skeleton | `drill: implement-with-tests` | `PRG-T03-C01-U03` | `PRG-T04-C02-U01` `[MOVED]` |
| `PRG-T03-C02-U02` | Routing and Route Parameters | Given nested resources, mount `express.Router` modules and validate params. | Modular router tree | `drill: implement-with-tests` | `PRG-T03-C02-U01` | `PRG-T04-C02-U02` `[MOVED]` |
| `PRG-T03-C02-U03` | Middleware and Request Lifecycle | Given cross-cutting concerns, order middleware (`next()`) and trace short-circuiting. | Lab 11 (`MiddlewarePipeline`) | `lab milestone` | `PRG-T03-C02-U02` | `PRG-T04-C02-U03` `[MOVED]` |
| `PRG-T03-C02-U04` | Request Validation | Given `body`/`query`/`params`, reject invalid payloads at the boundary with Zod middleware. | Validation middleware + tests | `drill: implement-with-tests` | `PRG-T02-C03-U03`, `T03-C02-U03` | `PRG-T04-C02-U04` `[MOVED]` |
| `PRG-T03-C02-U05` | Centralized & Async Error Handling (Express 5) | Given rejected async handlers, rely on Express 5 native promise-rejection forwarding to centralized error middleware ([Express 5 Error Handling](https://expressjs.com/en/5x/guide/error-handling/)). | Centralized error handler | `drill: fix-bug` | `PRG-T03-C02-U03` | `PRG-T04-C02-U05` `[MOVED]` |
| `PRG-T03-C02-U06` | Structured Logging | Given HTTP requests, emit structured JSON logs with request IDs and latency without leaking secrets. | Request logger middleware | `drill: implement-with-tests` | `PRG-T03-C02-U03` | `PRG-T04-C02-U06` `[MOVED, SPLIT]` |
| `PRG-T03-C02-U07` | Typed CRUD Endpoints | Given a resource spec, implement typed Create/Read/Update/Delete endpoints with proper status codes. | Typed CRUD router | `drill: implement-with-tests` | `PRG-T03-C02-U04`, `U05` | `PRG-T04-C02-U07` `[MOVED]` |

#### PRG-T03-C03 — Backend Architecture & API Integration Testing *(Moved from `T04-C03` + `T08-C01-U04`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T03-C03-U01` | Routes, Controllers and Services | Given fat route handlers, extract HTTP concerns from pure domain services. | Refactored service layer | `drill: refactor` | `PRG-T03-C02-U07` | `PRG-T04-C03-U01` `[MOVED]` |
| `PRG-T03-C03-U02` | Data Access Layer | Given service logic, isolate storage behind a repository interface for testability. | Repository interface + fake | `drill: refactor` | `PRG-T03-C03-U01` | `PRG-T04-C03-U02` `[MOVED]` |
| `PRG-T03-C03-U03` | Pagination, Sorting and Filtering | Given collection endpoints, implement cursor/offset pagination and allowlisted sort fields. | Paginated query service | `drill: implement-with-tests` | `PRG-T03-C03-U02` | `PRG-T04-C03-U03` `[MOVED]` |
| `PRG-T03-C03-U04` | Consistent API Contracts & Documentation | Given endpoints and DTOs, document request/response schemas consistently (OpenAPI/TS). | OpenAPI/contract spec | `drill: refactor` | `PRG-T03-C03-U01` | `PRG-T04-C03-U04` + `U06` `[MERGED]` |
| `PRG-T03-C03-U05` | Environment Configuration & Secrets Hygiene | Given env vars, validate startup config with Zod, fail fast on missing secrets, and never log/commit `.env`. | Typed `env.ts` loader | `drill: fix-bug` | `PRG-T03-C01-U02` | `PRG-T04-C03-U05` + `T06-C02-U07` `[MERGED]` |
| `PRG-T03-C03-U06` | Backend Module Boundaries | Given growing backend modules, enforce dependency direction via constructor injection. | Lab 12 (`ServiceContainer` + `HttpTestHarness`) | `lab milestone` | `PRG-T03-C03-U02`, `U05` | `PRG-T04-C03-U07` `[MOVED]` |
| `PRG-T03-C03-U07` | Service & API Integration Tests + DevVault API | Given `devvault-api`, write HTTP integration tests against an isolated test app and ship the API milestone. | `devvault-api` + integration tests | `project milestone` | `PRG-T03-C03-U06` | `PRG-T08-C01-U04` `[MOVED]` |

---

### PRG-T04 — Database Engineering: PostgreSQL, `pg` & Prisma (19 units)

#### PRG-T04-C01 — Relational Modeling & SQL Foundations *(Deduped `T05-C01`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T04-C01-U01` | Relational Database Concepts | Given flat JSON vs relational tables, explain tables, rows, ACID purpose, and relational integrity. | Schema comparison note | `drill: trace-explain` | `PRG-T03-C03-U02` | `PRG-T05-C01-U01` `[MOVED]` |
| `PRG-T04-C01-U02` | Entities, Attributes and Relationships | Given product requirements, classify 1:1, 1:N, and M:N relationships with join tables. | Entity relationship table | `drill: implement-with-tests` | `PRG-T04-C01-U01` | `PRG-T05-C01-U02` `[MOVED]` |
| `PRG-T04-C01-U03` | Primary and Foreign Keys | Given parent/child tables, define PKs, FKs, and `ON DELETE` behaviors safely. | DDL key constraints | `drill: fix-bug` | `PRG-T04-C01-U02` | `PRG-T05-C01-U03` `[MOVED]` |
| `PRG-T04-C01-U04` | Normalization and Constraints | Given denormalized tables, normalize to 3NF and add `NOT NULL`, `UNIQUE`, and `CHECK` constraints. | Normalized SQL schema | `drill: refactor` | `PRG-T04-C01-U03` | `PRG-T05-C01-U04` `[MOVED]` |
| `PRG-T04-C01-U05` | ERD Design and Schema Creation | Given DevVault's domain, design and execute the initial PostgreSQL DDL schema. | DevVault ERD + `schema.sql` | `project milestone` | `PRG-T04-C01-U04` | `PRG-T05-C01-U07` `[MOVED]` |

#### PRG-T04-C02 — PostgreSQL Queries, `pg` Driver & Transactions *(Merged `T05-C01-U05/U06` + `T05-C02` + `pg`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T04-C02-U01` | Filtering, Sorting and Aggregation | Given relational data, write `SELECT`, `WHERE`, `ORDER BY`, `GROUP BY`, and `HAVING` queries. | Passing SQL query suite | `drill: implement-with-tests` | `PRG-T04-C01-U04` | `PRG-T05-C01-U05` + `T05-C02-U01` `[MERGED]` |
| `PRG-T04-C02-U02` | `INNER` and `OUTER JOIN`s | Given multi-table queries, choose `INNER` vs `LEFT JOIN` and avoid row multiplication bugs. | Fixed JOIN queries | `drill: fix-bug` | `PRG-T04-C02-U01` | `PRG-T05-C01-U06` + `T05-C02-U02` `[MERGED]` |
| `PRG-T04-C02-U03` | Subqueries and CTEs | Given multi-step aggregations, write readable `WITH` CTEs and correlated subqueries. | CTE query refactor | `drill: refactor` | `PRG-T04-C02-U02` | `PRG-T05-C02-U03` `[MOVED]` |
| `PRG-T04-C02-U04` | Indexes and Query Plans | Given a slow query, read `EXPLAIN ANALYZE` and add B-tree/composite indexes. | Query plan optimization | `drill: fix-bug` | `PRG-T04-C02-U03` | `PRG-T05-C02-U04` `[MOVED]` |
| `PRG-T04-C02-U05` | Raw `pg`, Pooling & Parameterized Queries | Given `node-postgres` (`pg`), configure `Pool`, use `$1` parameterized queries, and prevent pool exhaustion. | Lab 13 (`MiniQueryBuilder` + `pg` pool) | `lab milestone` | `PRG-T04-C02-U02` | `NEW` |
| `PRG-T04-C02-U06` | Transactions and ACID | Given multi-step writes, wrap queries in `BEGIN`/`COMMIT`/`ROLLBACK` using a single `pg` client. | Atomic transfer function | `drill: implement-with-tests` | `PRG-T04-C02-U05` | `PRG-T05-C02-U05` `[MOVED]` |
| `PRG-T04-C02-U07` | Isolation, Concurrency & Optimization | Given concurrent updates, prevent lost updates with isolation levels or `SELECT ... FOR UPDATE`. | Concurrency-safe update test | `drill: fix-bug` | `PRG-T04-C02-U06` | `PRG-T05-C02-U06` + `U07` `[MERGED]` |

#### PRG-T04-C03 — Prisma, Migrations & Data Access *(Moved from `T05-C03`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T04-C03-U01` | Prisma Schema and Models | Given a SQL schema, define Prisma models, enums, and indexes accurately. | Valid `schema.prisma` | `drill: implement-with-tests` | `PRG-T04-C01-U05` | `PRG-T05-C03-U01` `[MOVED]` |
| `PRG-T04-C03-U02` | Prisma Relations | Given 1:N and M:N tables, configure Prisma relation fields and referential actions. | Typed relational models | `drill: implement-with-tests` | `PRG-T04-C03-U01` | `PRG-T05-C03-U02` `[MOVED]` |
| `PRG-T04-C03-U03` | Migrations and Schema Changes | Given schema evolutions, create safe non-destructive migrations and track applied versions. | Lab 14 (`MigrationRunner`) | `lab milestone` | `PRG-T04-C03-U02` | `PRG-T05-C03-U03` `[MOVED]` |
| `PRG-T04-C03-U04` | CRUD Queries | Given repository methods, implement typed Prisma queries without N+1 loops. | Optimized repository | `drill: refactor` | `PRG-T04-C03-U02` | `PRG-T05-C03-U04` `[MOVED]` |
| `PRG-T04-C03-U05` | Nested Reads and Writes | Given parent-child operations, use `select`/`include` and nested writes safely. | Scoped query module | `drill: implement-with-tests` | `PRG-T04-C03-U04` | `PRG-T05-C03-U05` `[MOVED]` |
| `PRG-T04-C03-U06` | Transactions with Prisma | Given atomic workflows, use `prisma.$transaction` and handle retryable conflicts. | Transactional service | `drill: implement-with-tests` | `PRG-T04-C02-U06`, `T04-C03-U05` | `PRG-T05-C03-U06` `[MOVED]` |
| `PRG-T04-C03-U07` | Seeding, Data Access & DevVault DB | Given `devvault-api`, replace in-memory storage with PostgreSQL (`pg` FTS + Prisma) and seed data. | DevVault Postgres persistence | `project milestone` | `PRG-T04-C03-U06` | `PRG-T05-C03-U07` `[MOVED]` |

---

### PRG-T05 — Authentication, Authorization & Web Security (16 units)

#### PRG-T05-C01 — Authentication & Session Management *(Moved from `T06-C01`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T05-C01-U01` | Authentication vs Authorization | Given access-control failures, distinguish `401 Unauthorized` (AuthN) from `403 Forbidden` (AuthZ). | Auth triage drill | `drill: predict-output` | `PRG-T03-C01-U04` | `PRG-T06-C01-U01` `[MOVED]` |
| `PRG-T05-C01-U02` | Password Storage and Hashing (OWASP) | Given user credentials, hash with Argon2id (min 19 MiB, 2 iterations, 1 parallelism) and verify in constant time ([OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)). | Argon2id auth helper | `drill: implement-with-tests` | `PRG-T05-C01-U01` | `PRG-T06-C01-U02` `[MOVED]` |
| `PRG-T05-C01-U03` | Sessions and Cookies | Given stateful login, issue opaque session IDs stored server-side with expiration and rotation. | Lab 15 (`SessionStore` + `SignedCookie`) | `lab milestone` | `PRG-T04-C02-U05`, `T05-C01-U02` | `PRG-T06-C01-U03` `[MOVED]` |
| `PRG-T05-C01-U04` | Secure Cookie Attributes | Given cookie flags, configure `HttpOnly`, `Secure`, `SameSite`, and `Path` to block theft. | Hardened cookie config | `drill: fix-bug` | `PRG-T05-C01-U03` | `PRG-T06-C01-U04` `[MOVED]` |
| `PRG-T05-C01-U05` | JWT and Token Concepts | Given stateless tokens, verify signatures/`exp`/`aud`, reject `alg: none`, and explain revocation tradeoffs. | Token verifier + tests | `drill: fix-bug` | `PRG-T05-C01-U01` | `PRG-T06-C01-U05` `[MOVED]` |
| `PRG-T05-C01-U06` | OAuth 2.0 / OIDC Flow Concepts | Given third-party login, trace Authorization Code + PKCE flow and validate `state`. | PKCE/state flow trace | `drill: trace-explain` | `PRG-T05-C01-U03`, `U05` | `PRG-T06-C01-U06` `[MOVED]` |
| `PRG-T05-C01-U07` | Implementing Auth with a Trusted Library | Given DevVault auth needs, integrate a vetted auth/session library rather than rolling custom crypto. | Auth integration module | `drill: implement-with-tests` | `PRG-T05-C01-U04`, `U06` | `PRG-T06-C01-U07` `[MOVED]` |

#### PRG-T05-C02 — Authorization, Rate Limiting & Web Security *(Moved from `T06-C02`; split CORS/Headers; added Rate Limiting)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T05-C02-U01` | Role-based Access Control | Given role hierarchies, enforce centralized RBAC policy guards on routes/services. | RBAC policy guard + tests | `drill: implement-with-tests` | `PRG-T05-C01-U01` | `PRG-T06-C02-U01` `[MOVED]` |
| `PRG-T05-C02-U02` | Resource Ownership Checks | Given IDOR-vulnerable endpoints, scope queries and mutations by `ownerId === session.userId`. | IDOR regression fix | `drill: fix-bug` | `PRG-T05-C02-U01` | `PRG-T06-C02-U02` `[MOVED]` |
| `PRG-T05-C02-U03` | XSS and Output Safety | Given untrusted user input, escape/sanitize HTML and block `javascript:` URLs. | XSS-safe renderer/sanitizer | `drill: fix-bug` | `PRG-T02-C01-U01` | `PRG-T06-C02-U03` `[MOVED]` |
| `PRG-T05-C02-U04` | CSRF, `SameSite` & Origin Checks | Given cookie-authenticated mutations, combine `SameSite=Lax/Strict`, `Origin`/Fetch-Metadata checks, and CSRF tokens, and keep `GET` side-effect-free ([OWASP CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)). | CSRF guard middleware | `drill: fix-bug` | `PRG-T05-C01-U04` | `PRG-T06-C02-U04` `[MOVED]` |
| `PRG-T05-C02-U05` | SQL Injection and Parameterization | Given concatenated SQL strings, refactor to parameterized queries and allowlisted identifiers. | SQLi-safe query refactor | `drill: fix-bug` | `PRG-T04-C02-U05` | `PRG-T06-C02-U05` `[MOVED]` |
| `PRG-T05-C02-U06` | CORS Configuration | Given cross-origin browser requests, configure explicit `Access-Control-Allow-Origin` and `credentials` rules. | Tested CORS policy | `drill: fix-bug` | `PRG-T03-C02-U03` | `PRG-T06-C02-U06` `[MOVED, SPLIT]` |
| `PRG-T05-C02-U07` | Security Headers (CSP, HSTS, Nosniff) | Given HTTP responses, set `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, and HSTS headers. | Security headers middleware | `drill: implement-with-tests` | `PRG-T05-C02-U03` | `PRG-T06-C02-U06` `[MOVED, SPLIT]` |
| `PRG-T05-C02-U08` | Rate Limiting & Brute-Force Protection | Given login/API abuse, implement a deterministic-clock token-bucket/sliding-window limiter. | Lab 16 (`TokenBucketRateLimiter` + `CsrfGuard`) | `lab milestone` | `PRG-T05-C02-U04` | `NEW` |
| `PRG-T05-C02-U09` | OWASP Risk Review & DevVault Auth | Given `devvault-api`, audit OWASP risks and ship multi-user auth, ownership, and rate limiting. | DevVault Auth & Security | `project milestone` | `PRG-T05-C02-U02..U08` | `PRG-T06-C02-U08` `[MOVED]` |

---

### PRG-T06 — Next.js & Full-Stack React (20 units)

#### PRG-T06-C01 — Next.js App Router Foundations *(Moved from `T03-C01`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T06-C01-U01` | Next.js Project Structure | Given a Next.js App Router repo, map `app/`, `next.config.*`, and server/client entrypoints. | Annotated App Router map | `drill: trace-explain` | `PRG-T02-C01-U08`, `T03-C03-U01` | `PRG-T03-C01-U01` `[MOVED]` |
| `PRG-T06-C01-U02` | App Router and File-system Routing | Given URL requirements, map route segments, route groups, and `page.tsx` conventions. | Route tree implementation | `drill: implement-with-tests` | `PRG-T06-C01-U01` | `PRG-T03-C01-U02` `[MOVED]` |
| `PRG-T06-C01-U03` | Layouts and Nested Routes | Given shared chrome, build nested `layout.tsx` preserving state across child navigations. | Nested layout shell | `drill: implement-with-tests` | `PRG-T06-C01-U02` | `PRG-T03-C01-U03` `[MOVED]` |
| `PRG-T06-C01-U04` | Loading and Error UI | Given slow or failing routes, add `loading.tsx`, `error.tsx`, and `not-found.tsx` boundaries. | Resilient route boundaries | `drill: fix-bug` | `PRG-T06-C01-U03` | `PRG-T03-C01-U04` `[MOVED]` |
| `PRG-T06-C01-U05` | Dynamic Routes and Route Parameters | Given `[slug]`/`[...rest]` segments, await async `params`/`searchParams` and handle invalid IDs. | Lab 17 (`MiniFileRouter`) | `lab milestone` | `PRG-T06-C01-U02` | `PRG-T03-C01-U05` `[MOVED]` |
| `PRG-T06-C01-U06` | Metadata and Navigation | Given dynamic pages, generate typed `Metadata` and navigate with `<Link>` / `useRouter`. | SEO & nav integration | `drill: implement-with-tests` | `PRG-T06-C01-U05` | `PRG-T03-C01-U06` `[MOVED]` |
| `PRG-T06-C01-U07` | Static and Dynamic Rendering | Given build/request signals (`cookies()`, `headers()`, `dynamic`), predict static vs dynamic rendering. | Rendering mode triage | `drill: predict-output` | `PRG-T06-C01-U05` | `PRG-T03-C01-U07` `[MOVED]` |

#### PRG-T06-C02 — Server/Client Components & Data Flow *(Moved from `T03-C02`; Next.js 15+ caching fix)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T06-C02-U01` | Server Components | Given data-fetching UI, render async Server Components with direct DB/service access. | Server Component view | `drill: implement-with-tests` | `PRG-T06-C01-U07` | `PRG-T03-C02-U01` `[MOVED]` |
| `PRG-T06-C02-U02` | Client Components | Given browser hooks/events, isolate `'use client'` leaves without bloating bundles. | Minimal client leaf | `drill: refactor` | `PRG-T06-C02-U01` | `PRG-T03-C02-U02` `[MOVED]` |
| `PRG-T06-C02-U03` | Server/Client Boundary Design | Given mixed server/client trees, compose Server Components as `children` inside Client wrappers. | Clean boundary refactor | `drill: refactor` | `PRG-T06-C02-U02` | `PRG-T03-C02-U03` `[MOVED]` |
| `PRG-T06-C02-U04` | Data Fetching on the Server | Given parallel data needs, fetch concurrently in Server Components and avoid waterfalls. | Waterfall-free data loader | `drill: fix-bug` | `PRG-T06-C02-U01` | `PRG-T03-C02-U04` `[MOVED]` |
| `PRG-T06-C02-U05` | Passing Data Across Component Boundaries | Given non-serializable values (`Date`, functions, secrets), serialize DTOs safely across the boundary. | Fixed serialization bug | `drill: fix-bug` | `PRG-T06-C02-U03` | `PRG-T03-C02-U05` `[MOVED]` |
| `PRG-T06-C02-U06` | Caching and Revalidation (Next.js 15+) | Given Next.js 15+ uncached defaults (`fetch` `no-store`, uncached `GET` Route Handlers, uncached Client Router Cache), opt into caching/revalidation explicitly ([Next.js 15](https://nextjs.org/blog/next-15)). | Explicit cache/revalidate config | `drill: predict-output` | `PRG-T06-C02-U04` | `PRG-T03-C02-U06` `[MOVED]` |
| `PRG-T06-C02-U07` | Streaming and Suspense Basics | Given slow secondary panels, stream UI progressively using `<Suspense>` boundaries. | Streamed page with Suspense | `drill: implement-with-tests` | `PRG-T06-C02-U04` | `PRG-T03-C02-U07` `[MOVED]` |

#### PRG-T06-C03 — Mutations, Route Handlers & Data Flow *(Moved from `T03-C03`; `U07` moved to DevVault)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T06-C03-U01` | Route Handlers | Given API/webhook needs in Next.js, write typed `GET`/`POST` Route Handlers (uncached by default in Next.js 15+). | Typed Route Handlers | `drill: implement-with-tests` | `PRG-T06-C02-U06` | `PRG-T03-C03-U01` `[MOVED]` |
| `PRG-T06-C03-U02` | Server Actions and Form Mutations | Given form mutations, implement Server Actions with authZ checks (never trusting client state). | Auth-guarded Server Action | `drill: fix-bug` | `PRG-T05-C02-U02`, `T06-C03-U01` | `PRG-T03-C03-U02` `[MOVED]` |
| `PRG-T06-C03-U03` | Input Validation with Zod | Given `FormData` or JSON payloads in Actions/Handlers, parse and return typed field errors. | Validated mutation handler | `drill: implement-with-tests` | `PRG-T02-C03-U03`, `T06-C03-U02` | `PRG-T03-C03-U03` `[MOVED]` |
| `PRG-T06-C03-U04` | Revalidation and Redirects | Given mutated data, call `revalidatePath`/`revalidateTag` and `redirect` outside `try/catch` traps. | Fixed redirect/revalidate bug | `drill: fix-bug` | `PRG-T06-C03-U02` | `PRG-T03-C03-U04` `[MOVED]` |
| `PRG-T06-C03-U05` | Error and Pending States | Given async Server Actions, surface `useActionState` errors and `useFormStatus` pending states. | Resilient form mutation UX | `drill: implement-with-tests` | `PRG-T06-C03-U03`, `U04` | `PRG-T03-C03-U05` + `U06` `[MERGED]` |
| `PRG-T06-C03-U06` | DevVault Next.js Full-Stack Migration | Given `devvault`, migrate UI + CRUD mutations to Next.js App Router with Server Components & Actions. | DevVault Next.js app | `project milestone` | `PRG-T06-C03-U05` | `PRG-T03-C03-U07` `[MOVED, PROJECT]` |

---

### PRG-T07 — E2E Testing & DevVault Capstone Track (12 units)

#### PRG-T07-C01 — End-to-End Testing & Quality Gates *(Moved from `T08-C03`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T07-C01-U01` | End-to-end Testing Concepts | Given unit/integration/E2E suites, decide which user journeys belong in E2E. | E2E scope plan | `drill: trace-explain` | `PRG-T02-C06-U05`, `T03-C03-U07` | `PRG-T08-C03-U01` `[MOVED]` |
| `PRG-T07-C01-U02` | Playwright Setup and Browser Contexts | Given a Next.js app, configure Playwright with isolated browser contexts and webServer startup. | Working `playwright.config.ts` | `drill: implement-with-tests` | `PRG-T07-C01-U01` | `PRG-T08-C03-U02` `[MOVED]` |
| `PRG-T07-C01-U03` | Locators and User Actions | Given fragile CSS selectors, replace with `getByRole`/`getByLabel` locators. | Resilient locator refactor | `drill: refactor` | `PRG-T07-C01-U02` | `PRG-T08-C03-U03` `[MOVED]` |
| `PRG-T07-C01-U04` | Assertions and Waiting | Given flaky tests with `waitForTimeout`, replace with Playwright auto-retrying web-first assertions. | Flake-free E2E spec | `drill: fix-bug` | `PRG-T07-C01-U03` | `PRG-T08-C03-U04` `[MOVED]` |
| `PRG-T07-C01-U05` | Authentication State and Test Data | Given authenticated E2E flows, seed isolated test data and reuse storageState safely. | Isolated auth fixture | `drill: implement-with-tests` | `PRG-T07-C01-U04` | `PRG-T08-C03-U05` `[MOVED]` |
| `PRG-T07-C01-U06` | Critical User Journey Tests | Given DevVault's core flows, write E2E tests for signup/login, create/search/edit/delete. | DevVault E2E suite | `project milestone` | `PRG-T07-C01-U05` | `PRG-T08-C03-U06` `[MOVED]` |
| `PRG-T07-C01-U07` | CI Quality Gates | Given lint, typecheck, unit, integration, and E2E suites, wire a fast failing CI gate. | Passing CI workflow | `drill: implement-with-tests` | `PRG-T07-C01-U06` | `PRG-T08-C03-U07` `[MOVED]` |

#### PRG-T07-C02 — DevVault Capstone Integration & Polish *(Replaces old `T07-C01..C04` concept units)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T07-C02-U01` | Domain Spec & Architecture Freeze | Given DevVault's final scope, lock entities (Snippets, Bookmarks, Notes, Tags) and acceptance criteria. | DevVault PRD & ADR | `project milestone` | `PRG-T06-C03-U06` | `PRG-T07-C01` `[MERGED, PROJECT]` |
| `PRG-T07-C02-U02` | Multi-Resource Workflows & Sharing | Given snippets, bookmarks, and notes, add collections, share links, and role/ownership guards. | Collections + sharing feature | `project milestone` | `PRG-T07-C02-U01` | `PRG-T07-C02` `[MERGED, PROJECT]` |
| `PRG-T07-C02-U03` | Search, Tagging & File Attachments | Given growing user vaults, add PostgreSQL full-text search, tag filters, and attachment metadata. | Search + attachments feature | `project milestone` | `PRG-T07-C02-U02` | `PRG-T07-C03-U01..U05` `[MERGED, PROJECT]` |
| `PRG-T07-C02-U04` | UX Polish & Accessibility Audit | Given DevVault UI, polish empty/loading/error states, responsive layout, and keyboard/ARIA audit. | Accessible polished UI | `project milestone` | `PRG-T07-C02-U03` | `PRG-T07-C04-U01..U05` `[MERGED, PROJECT]` |
| `PRG-T07-C02-U05` | Release Candidate & Walkthrough | Given all features + Playwright E2E, run full RC verification and record walkthrough notes. | DevVault v1.0 RC | `project milestone` | `PRG-T07-C01-U07`, `T07-C02-U04` | `PRG-T07-C04-U06..U07` `[MERGED, PROJECT]` |

---

### PRG-T08 `[Extended]` — System Design, Redis & Realtime (14 units; old `PRG-T09`)

#### PRG-T08-C01 — System Design & Redis Caching *(Moved from `T09-C01`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T08-C01-U01` | System Design Fundamentals | Given traffic/latency goals, estimate throughput, storage, and failure domains. | Capacity & bottleneck brief | `drill: trace-explain` | `PRG-T07-C02-U05` | `PRG-T09-C01-U01` `[MOVED]` |
| `PRG-T08-C01-U02` | Identifying Bottlenecks | Given slow endpoints, distinguish CPU, DB I/O, N+1, and lock contention bottlenecks. | Bottleneck triage report | `drill: fix-bug` | `PRG-T08-C01-U01` | `PRG-T09-C01-U02` `[MOVED]` |
| `PRG-T08-C01-U03` | Caching Concepts and Tradeoffs | Given read/write ratios, choose cache-aside vs write-through and quantify stale-read risk. | Cache strategy matrix | `drill: trace-explain` | `PRG-T08-C01-U02` | `PRG-T09-C01-U03` `[MOVED]` |
| `PRG-T08-C01-U04` | Redis Data Structures | Given caching/rate-limit/leaderboard tasks, pick Strings, Hashes, Sets, or Sorted Sets. | Redis DS mapping + code | `drill: implement-with-tests` | `PRG-T08-C01-U03` | `PRG-T09-C01-U04` `[MOVED]` |
| `PRG-T08-C01-U05` | Cache Keys and Expiration | Given multi-tenant keys, design versioned key namespaces, TTL jitter, and stampede protection. | Lab 18 (`InMemoryRespCache`) | `lab milestone` | `PRG-T08-C01-U04` | `PRG-T09-C01-U05` `[MOVED]` |
| `PRG-T08-C01-U06` | Cache Invalidation Strategies | Given mutations, invalidate keys reliably on writes without leaving orphan stale entries. | Invalidation hook + tests | `drill: fix-bug` | `PRG-T08-C01-U05` | `PRG-T09-C01-U06` `[MOVED]` |
| `PRG-T08-C01-U07` | Measuring Cache Effectiveness | Given hit/miss counters, compute hit ratio and verify latency improvement on DevVault tags. | DevVault Redis cache | `project milestone` | `PRG-T08-C01-U06` | `PRG-T09-C01-U07` `[MOVED]` |

#### PRG-T08-C02 — Realtime & Background Work *(Moved from `T09-C02`; deduped `T07-C03-U06/U07`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T08-C02-U01` | Realtime Communication Concepts | Given update requirements, compare short polling, SSE, and WebSockets. | Protocol selection matrix | `drill: trace-explain` | `PRG-T03-C01-U03` | `PRG-T09-C02-U01` `[MOVED]` |
| `PRG-T08-C02-U02` | WebSocket Lifecycle | Given a WebSocket connection, handle upgrade, heartbeats, reconnects, and cleanup. | Reconnecting WS client/server | `drill: fix-bug` | `PRG-T08-C02-U01` | `PRG-T09-C02-U02` `[MOVED]` |
| `PRG-T08-C02-U03` | Events and Message Design | Given realtime events, design versioned, Zod-validated event envelopes. | Typed event schema | `drill: implement-with-tests` | `PRG-T08-C02-U02` | `PRG-T09-C02-U03` `[MOVED]` |
| `PRG-T08-C02-U04` | Realtime UI Synchronization | Given incoming WS/SSE events, reconcile client cache without duplicate items or race conditions. | Synced UI state handler | `drill: fix-bug` | `PRG-T08-C02-U03` | `PRG-T09-C02-U04` `[MOVED]` |
| `PRG-T08-C02-U05` | Background Job Concepts | Given slow I/O (link metadata scraping, exports), offload to a background worker queue. | Enqueue/worker pipeline | `drill: implement-with-tests` | `PRG-T08-C01-U04` | `PRG-T09-C02-U05` + `T07-C03-U06` `[MERGED]` |
| `PRG-T08-C02-U06` | Retries and Idempotency | Given transient worker crashes, implement idempotency keys, exponential backoff, and DLQs. | Lab 19 (`PersistentJobQueue`) | `lab milestone` | `PRG-T08-C02-U05` | `PRG-T09-C02-U06` + `T07-C03-U07` `[MERGED]` |
| `PRG-T08-C02-U07` | Choosing Realtime vs Polling | Given DevVault's link-metadata jobs, wire async worker + SSE/polling status updates. | DevVault background jobs | `project milestone` | `PRG-T08-C02-U04`, `U06` | `PRG-T09-C02-U07` `[MOVED]` |

---

### PRG-T09 `[Extended]` — Deployment, Docker & Cloud (21 units; old `PRG-T10`)

#### PRG-T09-C01 — Production Readiness & Docker *(Moved from `T10-C01`; Compose v2 fix)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T09-C01-U01` | Production Environment Configuration | Given dev vs prod builds, separate build-time vs runtime config and `NODE_ENV=production`. | Production config checklist | `drill: fix-bug` | `PRG-T03-C03-U05` | `PRG-T10-C01-U01` `[MOVED]` |
| `PRG-T09-C01-U02` | Docker Images and Containers | Given containers vs VMs, inspect layers, processes, and ephemeral filesystems. | Container inspection note | `drill: trace-explain` | `PRG-T09-C01-U01` | `PRG-T10-C01-U02` `[MOVED]` |
| `PRG-T09-C01-U03` | Dockerfile Fundamentals | Given a Node/Next.js app, write a multi-stage `Dockerfile` running as non-root with `.dockerignore`. | Multi-stage `Dockerfile` | `drill: fix-bug` | `PRG-T09-C01-U02` | `PRG-T10-C01-U03` `[MOVED]` |
| `PRG-T09-C01-U04` | Volumes and Networking | Given app + DB containers, configure named volumes and bridge DNS networking. | Network/volume config | `drill: fix-bug` | `PRG-T09-C01-U03` | `PRG-T10-C01-U04` `[MOVED]` |
| `PRG-T09-C01-U05` | Docker Compose v2 for App and Database | Given multi-service local stacks, write `compose.yaml` (no `version` key) and run `docker compose` v2 ([Docker Compose v2](https://docs.docker.com/compose/intro/history/)). | `compose.yaml` (`app`+`pg`+`redis`) | `drill: implement-with-tests` | `PRG-T09-C01-U04` | `PRG-T10-C01-U05` `[MOVED]` |
| `PRG-T09-C01-U06` | Container Logs and Debugging | Given a failing container, diagnose via `docker compose logs`, `exec`, and healthchecks. | Healthcheck + triage note | `drill: fix-bug` | `PRG-T09-C01-U05` | `PRG-T10-C01-U06` `[MOVED]` |
| `PRG-T09-C01-U07` | Local Production-like Workflow | Given DevVault, boot the entire stack locally in production mode with `docker compose up`. | Containerized DevVault | `project milestone` | `PRG-T09-C01-U06` | `PRG-T10-C01-U07` `[MOVED]` |

#### PRG-T09-C02 — CI/CD, Monitoring & Operations *(Moved from `T10-C02`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T09-C02-U01` | CI Pipeline Fundamentals | Given team PRs, design fast deterministic CI stages (lint, typecheck, test, build). | CI stage diagram | `drill: trace-explain` | `PRG-T07-C01-U07` | `PRG-T10-C02-U01` `[MOVED]` |
| `PRG-T09-C02-U02` | GitHub Actions Workflow Syntax | Given `.github/workflows/*.yml`, configure triggers, caching, and matrix/service jobs. | Valid workflow YAML | `drill: fix-bug` | `PRG-T09-C02-U01` | `PRG-T10-C02-U02` `[MOVED]` |
| `PRG-T09-C02-U03` | Automated Tests and Build Checks | Given Postgres/Docker in CI, run migrations, tests, and production builds automatically. | Passing CI build | `drill: implement-with-tests` | `PRG-T09-C02-U02` | `PRG-T10-C02-U03` `[MOVED]` |
| `PRG-T09-C02-U04` | Deployment Workflow | Given main-branch merges, trigger gated CD deploys using repository secrets. | CD workflow YAML | `drill: implement-with-tests` | `PRG-T09-C02-U03` | `PRG-T10-C02-U04` `[MOVED]` |
| `PRG-T09-C02-U05` | Application Logs and Monitoring | Given production errors, emit structured logs, health probes, and latency/error alerts. | `/healthz` + structured logs | `drill: implement-with-tests` | `PRG-T09-C01-U06` | `PRG-T10-C02-U05` `[MOVED]` |
| `PRG-T09-C02-U06` | Database Backup Basics | Given a PostgreSQL database, script `pg_dump` backups and verify `pg_restore` recovery. | Verified backup/restore script | `drill: implement-with-tests` | `PRG-T09-C01-U05` | `PRG-T10-C02-U06` `[MOVED]` |
| `PRG-T09-C02-U07` | Rollback and Release Checklist | Given a bad deploy, execute rollback steps and database backward-compatibility checks. | Release/rollback runbook | `reading-only` | `PRG-T09-C02-U04`, `U06` | `PRG-T10-C02-U07` `[MOVED]` |

#### PRG-T09-C03 — Deploy & Final Showcase *(Moved from `T10-C03`)*
| v2 Code | Title | Learning Objective (Given X, learner can Y) | Expected Output | Practice Type | Prereqs | Old Code / Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRG-T09-C03-U01` | Choosing a Deployment Target | Given app requirements, compare PaaS, managed containers, and VPS tradeoffs. | Hosting decision note | `reading-only` | `PRG-T09-C01-U07` | `PRG-T10-C03-U01` `[MOVED]` |
| `PRG-T09-C03-U02` | Production Environment Variables | Given hosting secrets, configure production env vars and rotate keys safely. | Prod env checklist | `drill: fix-bug` | `PRG-T09-C03-U01` | `PRG-T10-C03-U02` `[MOVED]` |
| `PRG-T09-C03-U03` | Database Provisioning and Migrations | Given a managed Postgres instance, run production migrations safely before traffic cutover. | Live migrated DB | `project milestone` | `PRG-T09-C03-U02` | `PRG-T10-C03-U03` `[MOVED]` |
| `PRG-T09-C03-U04` | Deploying the Application | Given CI/CD and DB, deploy DevVault to production and verify startup. | Live DevVault URL | `project milestone` | `PRG-T09-C03-U03` | `PRG-T10-C03-U04` `[MOVED]` |
| `PRG-T09-C03-U05` | Domain and HTTPS Basics | Given a custom domain, configure DNS records and TLS termination. | HTTPS-enabled domain | `reading-only` | `PRG-T09-C03-U04` | `PRG-T10-C03-U05` `[MOVED]` |
| `PRG-T09-C03-U06` | Production Smoke Testing | Given a live deploy, run post-deploy smoke checks across auth, DB, and health endpoints. | Passing smoke test run | `project milestone` | `PRG-T09-C03-U05` | `PRG-T10-C03-U06` `[MOVED]` |
| `PRG-T09-C03-U07` | README, Demo and Retrospective | Given the finished product, write architecture docs, record a demo, and log retrospective lessons. | Final DevVault showcase | `project milestone` | `PRG-T09-C03-U06` | `PRG-T10-C03-U07` `[MOVED]` |

### Summary of Removed / Absorbed Units from v1
- `PRG-T00-C02-U01..U07` → compressed into `PRG-T00-C03-U01..U04` (depth remains in `PRG-T01`).
- `PRG-T01-C03-U01..U03, U05..U07` → merged into `PRG-T01-C04-U01..U03` alongside `PRG-T08-C01`.
- `PRG-T02-C05-U01..U02` → merged into `PRG-T02-C01-U08`.
- `PRG-T03-C03-U07` ("Building a Small Content Manager") → removed as concept unit; absorbed into `PRG-T06-C03-U06` (DevVault Next.js milestone).
- `PRG-T06-C02-U07` ("Secrets and Environment Safety") → consolidated into `PRG-T03-C03-U05` (with `PRG-T04-C01-U02`, `C02-U06`, `C03-U05`).
- `PRG-T07-C01..C04` (27 concept units) → replaced by 5 `DevVault` project milestones in `PRG-T07-C02-U01..U05`; `T07-C03-U06/U07` deduplicated into `PRG-T08-C02-U05/U06`.

---

## 4. Chapter Labs ("Build It Yourself")

Each lab uses the 5-tier milestone taxonomy (`rules/04_code.md` Part 6) with acceptance tests and ~3–8 sessions (~4.5–12 h).

| Lab | Chapter | What It Builds | Milestones (M1 → M4) | Units Used |
| :--- | :--- | :--- | :--- | :--- |
| **Lab 1: `TinyEventEmitter` & `PromisePool`** | `T01-C01` | Typed pub/sub emitter + concurrency-limited async pool | M1 Event map & listener contracts → M2 `on`/`off`/`emit` → M3 Bounded `PromisePool` → M4 `AbortSignal` cancellation & leak prevention | `T01-C01-U02`, `U06`, `U08`, `U09` |
| **Lab 2: `Result` & `MiniSchema`** | `T01-C02` | Discriminated `Result<T, E>` + runtime object validator | M1 Schema types & `Result` union → M2 Primitive/object parsers → M3 Union & nested error paths → M4 Strict `unknown` narrowing | `T01-C02-U04..U09` |
| **Lab 3: `LRUCache` & `TreeIndex`** | `T01-C03` | $O(1)$ doubly-linked-list + `Map` LRU cache & DFS/BFS tree index | M1 Node/cache contracts → M2 Doubly-linked list ops → M3 $O(1)$ `get`/`put` eviction → M4 Recursive DFS/BFS tree search | `T01-C03-U01..U07` |
| **Lab 4: `TinyTestRunner` & `DeepClone`** | `T01-C04` | Minimal `test()`/`assert` runner with spy/clock + cycle-safe `deepClone` | M1 Runner & reporter types → M2 `deepClone` (Maps, Sets, cycles) → M3 Fake clock & spy double → M4 Async test & error isolation | `T01-C04-U01..U05` |
| **Lab 5: `MiniStore` & `useStore`** | `T02-C01` | External subscription store + React hook | M1 Store state/listener types → M2 Immutable `setState` & selectors → M3 `useSyncExternalStore` hook → M4 Render-count boundary tests | `T02-C01-U03..U08` |
| **Lab 6: `TinyQueryCache`** | `T02-C02` | Stale-while-revalidate query cache | M1 Key serialization & state union → M2 In-flight deduplication → M3 `invalidateQueries` & optimistic rollback → M4 Bounded retry & abort | `T02-C02-U02..U07` |
| **Lab 7: `MiniFormEngine`** | `T02-C03` | Field-state & Zod validation hook | M1 Field/error types → M2 Dirty/touched state reducer → M3 Zod sync + async debounced validation → M4 Accessible error-focus binding | `T02-C03-U01..U07` |
| **Lab 8: `AccessibleDialog` & `Combobox`** | `T02-C04` | Headless keyboard + ARIA primitives | M1 ARIA state contracts → M2 Focus trap & `Escape` restore → M3 Arrow-key `Combobox` navigation → M4 Screen-reader role/state tests | `T02-C04-U04..U06` |
| **Lab 9: `VirtualizedList` + Suite** | `T02-C05`/`C06` | Windowed list + Testing Library suite | M1 Viewport math & item types → M2 Window slice calculation → M3 Role/userEvent component tests → M4 Async & a11y assertions | `T02-C05-U01..U04`, `T02-C06-U01..U04` |
| **Lab 10: `RawHttpRouter`** | `T03-C01` | HTTP server & param router on `node:http` | M1 Request/Response wrapper types → M2 Method + `:param` trie/matcher → M3 JSON body parser & size limit → M4 Stream backpressure & error envelope | `T03-C01-U03..U07` |
| **Lab 11: `MiddlewarePipeline`** | `T03-C02` | Composable Express-style onion middleware runner | M1 Context & `NextFn` types → M2 Sequential `use()` dispatch → M3 Async promise-rejection forwarding → M4 Request ID logger & Zod guard | `T03-C02-U03..U06` |
| **Lab 12: `ServiceContainer` & `HttpTestHarness`** | `T03-C03` | DI container + controller/service/repo test harness | M1 Port interfaces & `env.ts` → M2 In-memory repository → M3 Cursor pagination service → M4 Integration test harness | `T03-C03-U01..U06` |
| **Lab 13: `MiniQueryBuilder` (`pg`)** | `T04-C02` | Parameterized SQL builder + `pg` pool wrapper | M1 AST/clause types → M2 `$1..$n` parameterized `SELECT`/`JOIN` → M3 Identifier allowlisting → M4 Single-client transaction helper | `T04-C02-U01..U06` |
| **Lab 14: `MigrationRunner`** | `T04-C03` | Versioned SQL migration runner with checksums | M1 Migration metadata & checksums → M2 Ordered file discovery → M3 Transactional apply + ledger insert → M4 Drift/tamper detection | `T04-C03-U01..U03` |
| **Lab 15: `SessionStore` & `SignedCookie`** | `T05-C01` | HMAC-signed cookies + server session store | M1 Session & cookie flag types → M2 Timing-safe HMAC sign/verify → M3 Create/rotate/revoke store → M4 Expiry & `HttpOnly`/`SameSite` tests | `T05-C01-U02..U04` |
| **Lab 16: `TokenBucketRateLimiter` & `CsrfGuard`** | `T05-C02` | Deterministic-clock rate limiter + Origin/CSRF guard | M1 Bucket & policy types → M2 Injectable-clock token refill → M3 `Origin` + double-submit CSRF check → M4 Burst & clock-skew edge tests | `T05-C02-U04`, `U08` |
| **Lab 17: `MiniFileRouter`** | `T06-C01` | File-system route matcher + cache-tag invalidator | M1 Segment/layout tree types → M2 `[id]` / `[...slug]` matcher → M3 Nested layout wrapper → M4 Tag-based cache invalidation | `PRG-T06-C01-U02..U05`, `T06-C02-U06` |
| **Lab 18: `InMemoryRespCache` `[Extended]`** | `T08-C01` | Mini TTL key-value cache with jitter & stampede lock | M1 Entry & TTL types → M2 `get`/`set`/`del` with fake clock → M3 Tag invalidation index → M4 Singleflight stampede guard | `T08-C01-U04..U06` |
| **Lab 19: `PersistentJobQueue` `[Extended]`** | `T08-C02` | Job queue with idempotency, backoff & DLQ | M1 Job & status union → M2 Idempotency key deduplication → M3 Exponential backoff retries → M4 Dead-letter queue & graceful drain | `T08-C02-U05..U06` |

---

## 5. DevVault Product Ladder

**DevVault** is a personal developer knowledge vault (code snippets, bookmarks, and study notes with tags and search) grown continuously across every topic:

| Topic | DevVault Milestone | What Is Added | Units Used |
| :--- | :--- | :--- | :--- |
| `T00` | **M0: Repo & Workflow Setup** | Git repo, `package.json`, TypeScript strict config, ESLint, `README.md`, first PR. | `T00-C02-U01..U06` |
| `T01` | **M1: `devvault-core`** | In-memory snippet/bookmark/note store, tag index (`Map`/`Set`), JSON export/import with `AbortSignal`, `node:test` unit suite. | `T01-C01..C04` (`T01-C04-U06`) |
| `T02` | **M2: `devvault-web` SPA** | React UI to browse, filter, and create/edit items with Zod forms, accessible keyboard/ARIA dialogs, and React Testing Library suite. | `T02-C01..C06` (`T02-C06-U05`) |
| `T03` | **M3: `devvault-api` REST** | Express 5 API (`/snippets`, `/bookmarks`, `/notes`), Zod validation, typed `env.ts`, centralized async error handling, HTTP integration tests. | `T03-C01..C03` (`T03-C03-U07`) |
| `T04` | **M4: PostgreSQL Persistence** | Relational ERD (`users`, `items`, `tags`, `item_tags`), Prisma CRUD + migrations, raw `pg` full-text search query. | `T04-C01..C03` (`T04-C01-U05`, `T04-C03-U07`) |
| `T05` | **M5: Auth & Security** | Argon2id signup/login, `HttpOnly` `SameSite=Lax` sessions, per-user ownership checks, rate-limited auth, CORS & security headers. | `T05-C01..C02` (`T05-C02-U09`) |
| `T06` | **M6: Next.js Full-Stack** | Migrate UI + mutations into Next.js App Router with Server Components for reads, Server Actions/Route Handlers for writes, explicit Next.js 15+ revalidation. | `T06-C01..C03` (`T06-C03-U06`) |
| `T07` | **M7: E2E & v1.0 RC** | Collections, sharing, attachment metadata, full Playwright E2E journey suite, CI quality gates, accessibility & RC polish. | `T07-C01..C02` (`T07-C01-U06`, `T07-C02-U01..U05`) |
| `T08` *(Ext)* | **M8: Redis & Async Jobs** | Redis cache for popular tag queries + background job queue for bookmark metadata fetching with retries & live status updates. | `T08-C01..C02` (`T08-C01-U07`, `T08-C02-U07`) |
| `T09` *(Ext)* | **M9: Docker & Prod Deploy** | Multi-stage `Dockerfile`, `compose.yaml` (`docker compose` v2), GitHub Actions CI/CD, live Postgres deploy with HTTPS & smoke tests. | `T09-C01..C03` (`T09-C01-U07`, `T09-C03-U03..U07`) |

---

## 6. Where Python Attaches Later

Python attaches as a **second-language track (`PRG-PY` or `T10+`) after Core `T01`–`T05`** (or in parallel once `T01` JS/TS + `T04` SQL are solid). Because mental models for scope/closures, type systems, Big-O, recursion, data structures, HTTP, SQL, and testing are already mastered in TypeScript, the Python track skips re-teaching fundamentals and focuses directly on Python-specific semantics (data model, GIL/async `asyncio`, `pytest`, FastAPI/Pydantic, SQLAlchemy/psycopg, and scientific/AI tooling connecting to `MTH`/`PHY`).

---

## 7. Open Questions for the Learner

1. **Code strategy (Option A vs. Option B):** Approve **Option A** (renumber `PRG-T*`/`C*`/`U*` to match v2 order, run a one-time script for Notion + `id_map.json`, and rename `LAB-PRG-T03-C01-01` → `LAB-PRG-T06-C01-01`), or prefer **Option B** (keep old codes and add a Notion `Sequence` property)?
2. **Existing `LAB-PRG-T03-C01-01` (E-Commerce Checkout Engine):** Keep it as an optional bonus lab in `T01-C04`/`T04-C02`, or retire/re-tag it once DevVault + Chapter Labs are built?
3. **When to start Python:** Right after Core `T05` (before Next.js/Capstone), or after `T07` DevVault v1.0 RC?

---

## 8. Learner Decisions (2026-11-16)

1. **Code strategy:** Option A — renumber to the v2 order with a script (Notion titles, `id_map.json` regenerated, vaults, drill, progress and lab renamed together). Never by hand.
2. **`LAB-PRG-T03-C01-01` (checkout engine):** kept as an optional bonus lab at the end of `T01` (pure TS domain logic fits there); renamed with the migration.
3. **Python:** starts after `T07` (one language to expert level first).
4. **Units vs labs:** a unit always has its own drill; a chapter lab is separate work that uses the chapter's units (fixes rows where a unit's Expected Output was "Lab N").

## 9. More Projects on Request

The labs and DevVault milestones above are the minimum, not a cap. Whenever the learner finishes a lab or milestone and
does not feel confident yet, they can ask for another project ("ขอโปรเจคเพิ่ม <CHAPTER>"):

- **Scope:** built from the units the learner has already studied (status Done/In progress) in that chapter or topic, nothing ahead of them.
- **Targeted:** weighted toward the learner's open weak spots (`python -m scripts.weak_spots <SCOPE>`: rubric checks, lint rules and traps they keep hitting), so the extra project trains what is actually weak.
- **Same level or one step up,** chosen by the learner; a different domain from the previous project so it is not a repeat (e.g. after a `PromisePool`, a rate-limited crawler; after the `RawHttpRouter`, a static file server).
- **Same standard:** milestones with acceptance tests, a reference solution kept outside the learner's folder, lint, and the rubric review (`review-code`) per milestone; results recorded like drills.
- **Built by a skill** (`new-project`, to be written with the lab tooling), so every extra project meets the same gates as the planned ones.
