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

**Configuration Options:**
- `capacity`: Maximum burst packet allowance ceiling (positive integer).
- `refillRate`: Continuous token replenishment rate in tokens per second (positive number).
- `initialTokens`: Initial transmission allowance (defaults to `capacity`).
- `now`: Optional timestamp provider returning milliseconds (defaults to `Date.now`).

**Behavior & SLA Invariants:**
- `consume(cost = 1)`: Replenishes tokens continuously proportional to elapsed time since the previous check.
- Clamps the token balance to `capacity` to prevent unbounded bursts after prolonged sleep.
- If `tokens >= cost`, atomically deducts `cost` and returns `true`.
- If `tokens < cost`, preserves balance without deduction and returns `false`.
- **Run Single Suite:** `npm run test:q01`

### Q02 — `Q02_createCoalescingAsyncCache.js`
- **Archetype:** Debugging (Bug Triage & Root Cause)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q02_createCoalescingAsyncCache.test.js`
- **Requirement:** Implement `createCoalescingAsyncCache(fetchFn)` for high-frequency cryptocurrency orderbook feeds.

**System Requirements:**
- `get(key)`: Retrieves data for `key`, delegating to `fetchFn(key)` on cache misses.
- Caches resolved values indefinitely for subsequent sequential lookups.
- Coalesces simultaneous concurrent requests for the same unresolved `key` onto a single active `fetchFn` execution to prevent cache stampedes.
- Cleans up in-flight state upon settlement so future requests can retry if an operation fails.
- **Run Single Suite:** `npm run test:q02`

### Q03 — `Q03_createCircuitBreaker.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q03_createCircuitBreaker.test.js`
- **Requirement:** Implement `createCircuitBreaker(asyncOperation, options)` for a core banking interbank switch connecting to a central clearing house.

**Configuration Options:**
- `failureThreshold`: Consecutive failures needed to trip breaker (default $3$).
- `resetTimeoutMs`: Milliseconds to remain `OPEN` before probing in `HALF_OPEN` (default $50$).
- `now`: Optional timestamp provider returning milliseconds (defaults to `Date.now`).

**State Machine Specification:**
- `getState()`: Returns current state: `'CLOSED' | 'OPEN' | 'HALF_OPEN'`.
- `execute(...args)`: In `CLOSED`, executes `asyncOperation(...args)`. Consecutive failures increment counter; reaching `failureThreshold` trips breaker to `OPEN`. A successful call resets failure count to `0`.
- In `OPEN`: Fast-fails immediately throwing `new Error('CIRCUIT_BREAKER_OPEN')` without invoking `asyncOperation` until `resetTimeoutMs` elapses.
- In `HALF_OPEN`: Allows exactly one single canary probe request to test upstream health. Concurrent requests during probing fast-fail with `CIRCUIT_BREAKER_OPEN`. If probe succeeds, transitions to `CLOSED` and resets failure count; if probe fails, returns to `OPEN` and resets cooldown timer.
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
