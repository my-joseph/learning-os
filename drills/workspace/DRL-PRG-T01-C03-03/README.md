# DRL-PRG-T01-C03-03 — PRG-T01-C03: Programming Practice

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

### Q01 — `Q01_createTelemetryRateLimiter.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q01_createTelemetryRateLimiter.test.js`
- **Requirement:** Implement `createTelemetryRateLimiter(options)` for connected IoT fleet telematics beacons transmitting sensor metrics over cellular satellite.

**System Architecture & Options:**
- `capacity`: Maximum burst packet allowance (positive integer).
- `refillRate`: Accrued transmission tokens per second (positive number).
- `initialTokens`: Initial transmission allowance; defaults to `capacity`.

**Operational Invariants:**
- `consume(cost = 1)`: Computes tokens accrued proportionally to elapsed milliseconds since the last token check.
- Clamps the token balance to `capacity` to prevent unbounded bursts after prolonged transmission sleep.
- If `tokens >= cost`, decrements balance by `cost` and returns `true`.
- If `tokens < cost`, preserves balance without decrement and returns `false`.
- Updates the last timestamp to current time only when refill calculations occur.
- **Run Single Suite:** `npm run test:q01`

### Q02 — `Q02_createCoalescingAsyncCache.js`
- **Archetype:** Debugging (Bug Triage & Root Cause)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q02_createCoalescingAsyncCache.test.js`
- **Requirement:** Debug `createCoalescingAsyncCache(fetchFn)` for high-frequency cryptocurrency orderbook feeds.

**Defect Analysis:**
- The legacy starter implementation directly calls `fetchFn(key)` whenever a cache miss occurs without tracking in-flight promises.
- When concurrent requests arrive simultaneously before the first fetch resolves, it triggers a catastrophic cache stampede (multiple redundant network requests).

**Target Invariants:**
- If `key` is present in `cache`, immediately return the cached data.
- If an asynchronous fetch for `key` is already in-flight, return the existing in-flight `Promise`.
- Otherwise, initiate `fetchFn(key)`, store the promise in `inFlightMap`, and clean up `inFlightMap` in a `finally` block once settled.
- **Run Single Suite:** `npm run test:q02`

### Q03 — `Q03_createCircuitBreaker.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q03_createCircuitBreaker.test.js`
- **Requirement:** Implement `createCircuitBreaker(asyncOperation, options)` for a core banking interbank switch connecting to a central clearing house.

**State Machine Architecture:**
- `CLOSED`: Normal operation. Remote calls execute directly. Consecutive successes reset the failure counter to `0`.
- `OPEN`: Dependency failure isolation. If consecutive failures reach `failureThreshold`, the breaker trips to `OPEN` and records `openedAt = Date.now()`. All incoming calls fast-fail immediately throwing `new Error('CIRCUIT_BREAKER_OPEN')` without invoking `asyncOperation`.
- `HALF_OPEN`: Trial recovery probe. Once `resetTimeoutMs` has elapsed since opening, the breaker permits a single canary execution to test upstream health.
  - If the canary probe succeeds: transitions immediately to `CLOSED` and resets failure count.
  - If the canary probe fails: trips back to `OPEN` and resets the `openedAt` cooldown timer.

**Configuration Options:**
- `failureThreshold`: Consecutive failures needed to trip breaker (default $3$).
- `resetTimeoutMs`: Milliseconds to remain `OPEN` before probing in `HALF_OPEN` (default $50$).
- **Run Single Suite:** `npm run test:q03`

## Requesting an AI Architectural Review
Once your automated acceptance tests pass 100%, copy this prompt and ask Antigravity / Cursor AI:
```text
Please act as a Senior Tech Lead and conduct an Architecture & Code Craftsmanship Review on my implementation in `DRL-PRG-T01-C03-03`.
Evaluate my code across:
1. Separation of Concerns & Clean Code standards
2. State Management & Data Handling invariants
3. TypeScript typing / JSDoc precision and edge case resilience
4. Performance hot paths, algorithmic complexity, and decoupling suggestions
```
