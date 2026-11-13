# DRL-PRG-T01-C03-02 — PRG-T01-C03: Problem Solving & Utility Toolkit

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

### Q01 — `Q01_createTokenBucketLimiter.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q01_createTokenBucketLimiter.test.js`
- **Requirement:** Implement `createTokenBucketLimiter(options)` for an API Gateway to regulate bursty HTTP traffic.

**System Architecture & Options:**
- `capacity`: Maximum burst capacity (positive integer).
- `refillRate`: Tokens added per second (positive number).
- `initialTokens`: Optional starting token count; defaults to `capacity`.

**Operational Invariants:**
- `consume(cost = 1)`: Calculates tokens accrued based on elapsed milliseconds since last check.
- Clamps the current token balance to `capacity` to prevent unbounded accumulation during idle periods.
- If `tokens >= cost`, atomically decrements balance by `cost` and returns `true`.
- If `tokens < cost`, leaves balance intact and returns `false`.
- **Run Single Suite:** `npm run test:q01`

### Q02 — `Q02_verifyWebhookSignature.js`
- **Archetype:** Debugging (Bug Triage & Root Cause)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q02_verifyWebhookSignature.test.js`
- **Requirement:** Debug `verifyWebhookSignature(payload, signatureHeader, secret, toleranceSeconds)` in a payment webhook receiver.

**Defect Analysis:**
- The legacy starter implementation compares signatures with naive equality `===`, vulnerable to timing side-channels.
- The legacy implementation ignores timestamp drift, permitting stale replayed requests.

**Target Invariants:**
- Extract `timestamp` and `v1` signature hex from `signatureHeader` formatted as `t=<timestamp>,v1=<signatureHex>`.
- Validate that `Math.abs(currentTimeSec - timestamp) <= toleranceSeconds` (default $300$ seconds). Reject if outside window.
- Compute expected HMAC-SHA256 hex digest using `crypto.createHmac('sha256', secret)`.
- Compare computed digest and received `v1` signature using `crypto.timingSafeEqual` over Buffers of equal byte length.
- **Run Single Suite:** `npm run test:q02`

### Q03 — `Q03_retryWithExponentialBackoff.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q03_retryWithExponentialBackoff.test.js`
- **Requirement:** Implement `retryWithExponentialBackoff(asyncOperation, options)` for resilient inter-service RPC calls.

**Configuration Options:**
- `maxRetries`: Maximum retry attempts before giving up (default $3$).
- `baseDelayMs`: Initial backoff delay in milliseconds (default $10$).
- `maxDelayMs`: Cap on maximum backoff delay (default $200$).
- `isRetryable`: Predicate function `(error) => boolean` determining if error is transient.

**Execution Flow & Invariants:**
- Executes `asyncOperation()`.
- On success: resolves with the operation result immediately.
- On failure: checks `isRetryable(error)`. If `false`, immediately throws the error without retrying.
- If retries are exhausted (`attempt >= maxRetries`), throws the last encountered error.
- Computes exponential delay: `Math.min(maxDelayMs, baseDelayMs * Math.pow(2, attempt))`.
- **Run Single Suite:** `npm run test:q03`

## Requesting an AI Architectural Review
Once your automated acceptance tests pass 100%, copy this prompt and ask Antigravity / Cursor AI:
```text
Please act as a Senior Tech Lead and conduct an Architecture & Code Craftsmanship Review on my implementation in `DRL-PRG-T01-C03-02`.
Evaluate my code across:
1. Separation of Concerns & Clean Code standards
2. State Management & Data Handling invariants
3. TypeScript typing / JSDoc precision and edge case resilience
4. Performance hot paths, algorithmic complexity, and decoupling suggestions
```
