# DRL-PRG-T00-C02-01 — PRG-T00-C02: JavaScript & TypeScript Baseline

> **Environment Preset:** `node-vanilla` — Standard Node.js Native Runner (CommonJS/ESM)
> **100% Local IDE Mandate**: All problem solving, refactoring, and debugging must be performed natively in your IDE (VS Code / Cursor).

## Universal 6-Step Pedagogical Practice Loop
1. **คิดเองก่อนเขียน (Mental Model)**: Review the Acceptance Criteria and boundary traps before typing.
2. **ลงมือทำ (Local IDE)**: Open the source file in VS Code or Cursor and implement the logic.
3. **ทดสอบ (Automated Acceptance Testing)**: Run `npm test` or `npm run test:<qid>` in this directory.
4. **อธิบายโค้ด (AI Senior Lead PR Review)**: Articulate your algorithm and request an AI Senior Tech Lead architectural review.
5. **Refactor (Clean Architecture)**: Decouple helpers, clean code smells, and optimize hot paths while keeping tests green.
6. **เพิ่มความยาก (Progression)**: Scale up test inputs and edge cases.

## Quick Terminal Commands
```bash
# Run all acceptance test suites in this workspace
npm test

# Run tests in watch mode while editing
npm run test:watch

# Run tests for a specific question
npm run test:q01

# Request Senior Tech Lead AI PR Review (packages code & copies prompt to clipboard)
npm run review
npm run review q01

# Grade all exercises (runs visible + hidden trap tests) and sync to Notion
npm run submit
```

## Exercises in this Workspace

### Q01 — `Q01_sanitizeConfig.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q01_sanitizeConfig.test.js`
- **Requirement:** Implement `sanitizeConfig(rawConfig, schema)` for microservice environment configurations.

**System Requirements:**
- `schema` defines expected keys and their default primitive values: `{ [key: string]: string | number | boolean }`.
- For each key in `schema`: if `rawConfig[key]` is `null` or `undefined`, fall back to `schema[key]`.
- Crucial: Legitimate falsy primitive values (`0`, `false`, `""`) in `rawConfig` must be preserved and NOT overwritten by defaults.
- Discard any extraneous keys in `rawConfig` that are not present in `schema`.
- **Run Single Suite:** `npm run test:q01`

### Q02 — `Q02_createCounterRegistry.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q02_createCounterRegistry.test.js`
- **Requirement:** Implement `createCounterRegistry()` to track high-throughput microservice metrics.

**System Requirements:**
- `increment(metric, amount = 1)`: Increases the integer counter for `metric` by `amount`. Defaults to starting at 0.
- `getCount(metric)`: Returns the current count for `metric`, or `0` if not yet incremented.
- `getSnapshot()`: Returns a snapshot plain object containing `{ [metric]: count }`.
- Immutability & Encapsulation: Mutating the object returned by `getSnapshot()` must NOT alter internal registry state.
- **Run Single Suite:** `npm run test:q02`

### Q03 — `Q03_aggregateCategoryRevenue.js`
- **Archetype:** Debugging (Bug Triage & Root Cause)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q03_aggregateCategoryRevenue.test.js`
- **Requirement:** Debug `aggregateCategoryRevenue(transactions)` in an e-commerce revenue accounting service.

**System Requirements:**
- `transactions`: Array of `{ category: string, amount: number, status: 'completed' | 'refunded' | 'pending' }`.
- Sum total net revenue per category: completed transactions add `amount`, refunded transactions subtract `amount`, pending are ignored.
- Immutability Contract: Input `transactions` array and its items must remain strictly unmodified (no in-place sorting or mutations).
- Return format: Object `{ [category]: netRevenue }` rounded to 2 decimal places.
- **Run Single Suite:** `npm run test:q03`

### Q04 — `Q04_settleAllSettled.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q04_settleAllSettled.test.js`
- **Requirement:** Implement `settleAllSettled(taskFns)` for parallel microservice health telemetry.

**System Requirements:**
- `taskFns`: Array of zero-argument async functions returning Promises.
- Execute all task functions concurrently in parallel.
- Returns a Promise resolving to an array of result descriptors in original order:
  - For fulfilled tasks: `{ status: 'fulfilled', value: <result> }`
  - For rejected tasks: `{ status: 'rejected', reason: <error> }`
- Resilient Concurrency: Rejection of any single task must NOT abort or fast-fail the remaining tasks.
- **Run Single Suite:** `npm run test:q04`

### Q05 — `Q05_createPaymentStateMachine.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q05_createPaymentStateMachine.test.js`
- **Requirement:** Implement `createPaymentStateMachine(options = {})` for e-commerce checkout transaction lifecycles.

**State Transitions Specification:**
- Initial state: `INITIAL`.
- Allowed transition actions:
  - `INITIAL` -> `dispatch({ type: 'AUTHORIZE', orderId, amount })` -> transitions to `AUTHORIZED`.
  - `AUTHORIZED` -> `dispatch({ type: 'CAPTURE' })` -> transitions to `SETTLED`.
  - `AUTHORIZED` -> `dispatch({ type: 'VOID' })` -> transitions to `VOIDED`.
- Invalid Transitions: Dispatching an action incompatible with current state throws `Error('INVALID_STATE_TRANSITION')`.
- Terminal States: `SETTLED` and `VOIDED` are final; any subsequent dispatch must throw.
- `getState()`: Returns `{ status, orderId, amount }`.
- **Run Single Suite:** `npm run test:q05`

## Requesting an AI Architectural Review
Once your automated acceptance tests pass 100%, copy this prompt and ask Antigravity / Cursor AI:
```text
Please act as a Senior Tech Lead and conduct an Architecture & Code Craftsmanship Review on my implementation in `DRL-PRG-T00-C02-01`.
Evaluate my code across:
1. Separation of Concerns & Clean Code standards
2. State Management & Data Handling invariants
3. TypeScript typing / JSDoc precision and edge case resilience
4. Performance hot paths, algorithmic complexity, and decoupling suggestions
```
