# AI Lab Generation Engine & Milestone Standard Operating Procedure (SOP)
> **Status:** Draft / Work in Progress (ทดระบบ — ยังไม่อัปเดตขึ้น Notion Central Rules Page)  
> **Target Audience:** Any AI Agent (Claude, GPT, Antigravity) authoring, scaffolding, or maintaining Phase 3 Project Labs.  
> **Philosophy:** Architecture-First, Terminal-First, Extensible, and 100% Pre-Execution Verified.

---

## 1. Core System Philosophy: "Architecture Over One-Off Content"
1. **Zero Hardcoded Subject Logic:**  
   The lab grading runner, submission scripts, and Notion bridges must NEVER assume what domain a lab is teaching (whether it is an E-Commerce backend, a compiler parser, Next.js Server Actions, or a high-frequency trading order book). All behavior is driven strictly by standardized configuration (`lab.config.json`) and test output.
2. **Terminal-First & Local IDE Experience:**  
   Phase 3 is NOT an in-browser toy editor. The student works inside **Cursor or VS Code** in their local repository. The primary developer interaction loop is driven completely by standard terminal commands:
   - `npm test`: Rapid local feedback / watch mode during development.
   - `npm run submit`: Automated grading of all milestones, packaging of JSON execution telemetry, and synchronization directly to the Notion database `Learning Practice & Drills`.
3. **No Blind AI Generation:**  
   An AI agent is strictly forbidden from spitting out code and unit tests without running the canonical solution through the automated test runner in the terminal. **If it hasn't passed 100% of tests in a real subprocess, it is not verified and cannot be shipped.**

---

## 2. Universal Milestone Taxonomy
Because every project differs fundamentally in scope and technology, milestones MUST NOT be arbitrary. Every Phase 3 Lab must structure its progressive learning path across this standardized **4-to-5 Tier Architectural Hierarchy**:

| Tier | Milestone Focus | Technical Scope & Deliverables | Verification Strategy |
| :--- | :--- | :--- | :--- |
| **M1** | **Contracts, Schemas & Domain Models** | TypeScript types, Zod/DTO schemas, domain entities, value objects, configuration parsers. | Schema validation tests, type guards, invariant assertions. |
| **M2** | **Pure Business Logic & State Calculators** | Deterministic business rules, price calculators, state reducers, text parsers, mathematical transformations (strictly side-effect free). | Extensive input/output matrices, boundary assertions, deterministic unit tests. |
| **M3** | **Stateful Services, Orchestration & I/O** | Service classes, repository adapters, HTTP route handlers, async pipeline coordination, external API integrations. | Mocked external dependencies, asynchronous event handling, lifecycle assertions. |
| **M4** | **Edge Cases, Security & Resilience** | Concurrency race conditions, idempotency keys, boundary overflow, falsy/poison payloads, rollback on failure, rate limiting. | Stress test cases, race-condition simulations, malformed payload injections. |
| **M5** | *(Optional Capstone)* **End-to-End Workflow** | Multi-step user journey, full pipeline smoke test (e.g., checkout -> payment -> inventory reserve -> receipt). | End-to-end integration tests traversing all layers. |

---

## 3. Strict AI Authoring Pipeline (ลำดับการสร้างของ AI)
Whenever an AI Agent is tasked with creating a new Lab, it MUST follow this exact 8-step sequence:

```
[1. Spec & Config] -> [2. Canonical Solution] -> [3. Milestone Test Suites]
                                                            │
[6. Terminal Scripts] <- [5. Starter Scaffolding] <- [4. Pre-Execution Verify (100%)]
         │
[7. Baseline Test Check] -> [8. Notion Page Registration]
```

### Step 1: Specification & `lab.config.json`
Define the lab metadata, learning unit linkage, milestone breakdown, point distribution, and mistake taxonomy:
```json
{
  "labId": "LAB-PRG-T03-C01-01",
  "title": "E-Commerce Core Domain & Checkout Engine",
  "subject": "PRG",
  "unitCode": "PRG-T03-C01",
  "chapterCode": "PRG-T03",
  "difficulty": "Level 4 - Applied Synthesis",
  "milestones": [
    {
      "id": "M1",
      "title": "Domain Models & Schema Validation",
      "points": 25,
      "testFile": "tests/m1_models.test.ts",
      "mistakeCategory": "Schema Invalidation / Type Flaw"
    },
    {
      "id": "M2",
      "title": "Pricing & Discount Engine",
      "points": 25,
      "testFile": "tests/m2_pricing.test.ts",
      "mistakeCategory": "Calculation & Precision Flaw"
    },
    {
      "id": "M3",
      "title": "Cart State Machine & Inventory Service",
      "points": 25,
      "testFile": "tests/m3_cart_service.test.ts",
      "mistakeCategory": "State Mutation & Transition Error"
    },
    {
      "id": "M4",
      "title": "Concurrency, Idempotency & Edge Cases",
      "points": 25,
      "testFile": "tests/m4_resilience.test.ts",
      "mistakeCategory": "Concurrency Race & Edge Case"
    }
  ]
}
```

### Step 2: Canonical Reference Implementation
Implement the **complete, working, production-grade code** first (e.g. in `.canonical/` or solution reference). Write clean, idiomatic, typed code adhering to modern best practices.

### Step 3: Milestone Test Suites Development
Write unit and integration tests mapped 1-to-1 with the milestones.
- Keep visible assertions clear to guide developer debugging.
- Add boundary and anti-cheat edge cases to verify real logic rather than hardcoded returns.

### Step 4: Mandatory Pre-Execution Verification
Execute the test runner on the canonical solution in a real terminal command:
```bash
node --experimental-strip-types --test tests/**/*.test.ts
# OR
npm test -- --run
```
**Gate Check:** The test runner must exit with code `0`, reporting **100% of test suites and test cases passing**. If any test fails or throws an unhandled promise rejection, fix the solution/test immediately before proceeding.

### Step 5: Scaffolding Starter Code
Derive the student-facing starter code:
- Preserve all interfaces, type definitions, and function signatures.
- Strip internal logic and replace with standard placeholders:
  ```typescript
  // TODO [Milestone 2]: Implement calculateCartTotal with tiered discounts
  // 1. Calculate base subtotal
  // 2. Apply percentage discount if coupon matches
  // 3. Compute tax rounded to 2 decimal places
  throw new Error("Not implemented: calculateCartTotal");
  ```
- Ensure the codebase compiles cleanly without TypeScript syntax or import errors.

### Step 6: Terminal CLI & Submission Harness Integration
Set up `package.json` with standard lifecycle scripts:
```json
{
  "scripts": {
    "test": "node --experimental-strip-types --test tests/*.test.ts",
    "test:watch": "node --experimental-strip-types --test --watch tests/*.test.ts",
    "submit": "python3 ../../labs/common/submit_lab.py"
  }
}
```

### Step 7: Baseline Verification of Starter Code
Run `npm test` against the starter code.
- Must execute without crashing the Node runtime (no module not found, no syntax errors).
- All tests must report failing/pending with clear descriptive error messages.

### Step 8: Notion Page Registration
Register the lab record in Notion database `Learning Practice & Drills`:
- `Format`: `"Code Test Suite"`
- `Practice Status`: `"Ready"`
- Initial `Score`: `0`, `Max Score`: Sum of milestone points.

---

## 4. Past Failures & Mandatory Lessons Learned (กฎเหล็กที่ต้องจำ)

### Gotcha 1: Notion Multi-Select Comma Ban (`HTTP 400 validation_error`)
- **The Bug:** Notion's API strictly rejects any `multi_select` option containing a comma `,` (e.g. `Cache Flaw (0, false, null)`). It returns:
  `HTTP 400: validation_error ("Invalid multi_select option, commas not allowed")`.
- **The Rule:** All tag names in `mistakeCategory` or Notion tags must NEVER include a comma. AI and scripts must sanitize via `.replace(/,/g, " /")` before payload delivery.

### Gotcha 2: Working Directory & Path Assumptions
- **The Bug:** Running a script from `practice-studio/` vs workspace root vs `labs/LAB-xxx` results in `ModuleNotFoundError` or file not found if relative paths `./` are hardcoded.
- **The Rule:** All scripts must dynamically locate root directories via filesystem anchor search (e.g. searching upwards for `id_map.json` or `.git`) and use absolute paths.

### Gotcha 3: 100% English for Technical Content
- **The Rule:** All code, inline comments, test descriptions, Notion titles, problem prompts, and error summaries must be written in **100% clear, idiomatic English**. Thai language is reserved strictly for conversational communication with the user.

### Gotcha 4: Zero Unrendered Syntax
- **The Rule:** Markdown syntax such as raw `**` bolding or unparsed bracket tokens must never appear in Notion database title properties or plain text columns. All text must be clean and validated.

### Gotcha 5: Unhandled Async Promises in Tests
- **The Rule:** All async test cases in Node/Vitest must be properly `await`ed and timers/connections cleaned up in `after()` or `finally`. A hanging test process causes terminal commands to freeze indefinitely.

### Gotcha 6: Native Node `--experimental-strip-types` Type-Only Imports
- **The Bug:** In Node 24 with native TypeScript type stripping without a bundler, doing `import { InterfaceName } from "./types.ts"` fails with `SyntaxError: The requested module './types.ts' does not provide an export named 'InterfaceName'` because Node expects a runtime JavaScript value.
- **The Rule:** All pure TypeScript types and interfaces must be explicitly imported using `import type { ... } from "./types.ts"` so that Node strips them away completely at compile time.

### Gotcha 7: Notion API Icon Name Whitelist
- **The Bug:** Passing unsupported icon names (such as `name: "terminal"`) to the Notion API icon object causes `HTTP 400: validation_error ("Invalid icon name ...")`.
- **The Rule:** Use only standard Notion icon names (e.g. `"code"`, `"target"`, `"lightgray"`) or standard emoji. Programming labs must use `name: "code"`.

---

## 5. Terminal Submission & Telemetry Architecture

When the user runs `npm run submit` in the lab directory:
1. `submit_lab.py` loads `lab.config.json` in the current directory.
2. Runs the configured test command (default: `node --experimental-strip-types --test --test-reporter=junit tests/*.test.ts`).
3. Parses the standardized **JUnit XML** test report (supported universally by Node, Vitest, Jest, Pytest, and Go).
4. Groups test results by Milestone and calculates:
   - Milestone Pass/Fail status
   - Score earned vs Max Score
   - Failure extraction: test name, assertion message, stack trace.
5. Reads `.env` and `id_map.json` from the repository root.
6. Sends PATCH / POST request to Notion `Learning Practice & Drills`:
   - Properties: `Format: "Code Test Suite"`, `Score`, `Max Score`, `Practice Status` (`Graded` if 100%, else `Needs Retry`), `Mistake Categories` (sanitized with comma-ban protection), `Diverged Steps Summary`.
   - Body Blocks: Structured Callout with milestone score breakdown, expandable toggle blocks with test case results and stack traces.
7. Prints a concise, beautifully formatted summary in the terminal with a direct clickable Notion link.
