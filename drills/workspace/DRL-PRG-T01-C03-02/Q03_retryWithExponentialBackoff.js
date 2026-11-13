/**
 * ============================================================================
 * [DRL-PRG-T01-C03-02] Q03: Problem Solving (Logic & Algorithm)
 * Target Competencies: Engineering Fundamentals
 * ============================================================================
 * 
 * 6-STEP PEDAGOGICAL PRACTICE LOOP:
 * 1. คิดเองก่อนเขียน : Sketch invariants, mental model, and boundary edge cases.
 * 2. ลงมือทำ         : Write your implementation in this file.
 * 3. ทดสอบ           : Run `npm test` or `npm run test:q03` in this folder.
 * 4. อธิบายโค้ด      : Explain the algorithm and request an AI Senior Tech Lead PR Review.
 * 5. Refactor        : Decouple helpers, improve readability, and optimize performance.
 * 6. เพิ่มความยาก     : Scale up test inputs and handle harsher stress scenarios.
 * 
 * SPECIFICATION:
 * Implement `retryWithExponentialBackoff(asyncOperation, options)` for resilient inter-service RPC calls.

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
 * ============================================================================
 */

async function retryWithExponentialBackoff(asyncOperation, options = {}) {
  // TODO: implement retry orchestrator with exponential delay
  return asyncOperation();
}

module.exports = { retryWithExponentialBackoff };
