# DRL-PRG-T01-C03-01 — PRG-T01-C03: Problem Solving & Utility Toolkit

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

### Q01 — `Q01_RateLimiter.js`
- **Archetype:** Project-Based (Multi-Module Architecture)
- **Acceptance Scenarios:** 3 visible scenarios (+ 2 hidden trap tests) in `Q01_RateLimiter.test.js`
- **Requirement:** Build an event-driven `RateLimiter` class implementing a sliding window algorithm extending `EventEmitter`.

**Constructor:**
- `new RateLimiter({ maxRequests = 5, windowMs = 1000 })`

**Methods & Invariants:**
- `consume(key)`: Allows up to `maxRequests` within `windowMs`.
- Returns `{ allowed: true, remaining: number, resetMs: number }`.
- On limit breach: emit `'blocked'` event with `(key, resetMs)` and return `{ allowed: false, remaining: 0, resetMs }`.
- `reset(key)`: Clears recorded history for the specified key.
- **Run Single Suite:** `npm run test:q01`

### Q02 — `Q02_debounce.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 2 hidden trap tests) in `Q02_debounce.test.js`
- **Requirement:** Implement a production-grade `debounce(fn, delay)` utility in JavaScript.

**Behavioral Requirements:**
- Delays executing `fn` until `delay` milliseconds have elapsed since the last invocation.
- Repeated calls within the delay window must reset the timer and postpone execution.
- Must preserve the invocation `this` context and forward all received arguments.
- Supports `0ms` delay as a macrotask deferral.
- **Run Single Suite:** `npm run test:q02`

### Q03 — `Q03_calculateMonthlyBill.js`
- **Archetype:** Refactoring (Clean Code & Safe Extensibility)
- **Acceptance Scenarios:** 3 visible scenarios (+ 2 hidden trap tests) in `Q03_calculateMonthlyBill.test.js`
- **Requirement:** Refactor `calculateMonthlyBill(account)` to support new business requirements without breaking existing plans:

**New Plan: 'family':**
- Base price: 34.99 USD (includes 2 members).
- Add-on members: +8.99 USD per extra member over 2, up to 6 members max.
- Guard Invariant: If `account.members > 6`, throw `RangeError('Family plan allows max 6 members')`.

**New Feature: Annual Commitment:**
- If `account.annualCommitment` is `true`, apply a 15% discount on the plan subtotal before tax.

**Refactoring Objective:**
- Keep all legacy plans (`basic`, `pro`, `enterprise`) 100% green.
- Decouple the tangled `switch`/`if-else` statement into clean strategy configuration dictionaries.
- **Run Single Suite:** `npm run test:q03`

### Q04 — `Q04_memoize.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 2 hidden trap tests) in `Q04_memoize.test.js`
- **Requirement:** Implement `memoize(fn, resolver)` in JavaScript.

**Behavioral Requirements:**
- Returns a memoized function caching the result of calling `fn`.
- If `resolver` is provided, use it to compute the cache key; otherwise default to `args[0]`.
- Correctly cache falsy return values (`0`, `false`, `null`, `''`) without re-evaluating.
- Expose the underlying cache `Map` on `memoized.cache`.
- **Run Single Suite:** `npm run test:q04`

### Q05 — `Q05_groupBy.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 2 hidden trap tests) in `Q05_groupBy.test.js`
- **Requirement:** Implement a `groupBy(collection, iteratee)` utility in JavaScript.

**Behavioral Requirements:**
- Splits `collection` into sets grouped by the result of running each value through `iteratee`.
- `iteratee` can be either a function (e.g. `Math.floor`) or a string property name (e.g. `'type'`).
- Return an empty object `{}` if `collection` is `null`, `undefined`, or an empty array.
- **Run Single Suite:** `npm run test:q05`

### Q06 — `Q06_AsyncCache.js`
- **Archetype:** Debugging (Bug Triage & Root Cause)
- **Acceptance Scenarios:** 3 visible scenarios (+ 2 hidden trap tests) in `Q06_AsyncCache.test.js`
- **Requirement:** Diagnose and fix two critical defects in `AsyncCache`:

**1. Cache Stampede (Concurrency Bug):**
- Simultaneous calls to `getOrFetch(key, fetcher)` fire redundant `fetcher` calls.
- Deduplicate in-flight Promises using an `inFlight` Map so all concurrent requests share the single active Promise.
- Ensure `inFlight` key is deleted in a `finally` block even if the fetch fails.

**2. State Mutation Leak (Defensive Copying):**
- Returning cached references directly allows external callers to mutate internal cache state.
- Defensively clone cached results before returning to callers.
- **Run Single Suite:** `npm run test:q06`

## Requesting an AI Architectural Review
Once your automated acceptance tests pass 100%, copy this prompt and ask Antigravity / Cursor AI:
```text
Please act as a Senior Tech Lead and conduct an Architecture & Code Craftsmanship Review on my implementation in `DRL-PRG-T01-C03-01`.
Evaluate my code across:
1. Separation of Concerns & Clean Code standards
2. State Management & Data Handling invariants
3. TypeScript typing / JSDoc precision and edge case resilience
4. Performance hot paths, algorithmic complexity, and decoupling suggestions
```
