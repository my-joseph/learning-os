/**
 * ============================================================================
 * [DRL-PRG-T00-C02-02] Q02: Problem Solving (Logic & Algorithm)
 * Target Competencies: Engineering Fundamentals
 * ============================================================================
 * 
 * 6-STEP PEDAGOGICAL PRACTICE LOOP:
 * 1. คิดเองก่อนเขียน : Sketch invariants, mental model, and boundary edge cases.
 * 2. ลงมือทำ         : Write your implementation in this file.
 * 3. ทดสอบ           : Run `npm test` or `npm run test:q02` in this folder.
 * 4. อธิบายโค้ด      : Explain the algorithm and request an AI Senior Tech Lead PR Review.
 * 5. Refactor        : Decouple helpers, improve readability, and optimize performance.
 * 6. เพิ่มความยาก     : Scale up test inputs and handle harsher stress scenarios.
 * 
 * SPECIFICATION:
 * Implement `resolveRetryLimit(settings)` for a background job queue.

**Requirements:**
- Return `settings.maxRetries` when it is provided.
- When it is `null` or `undefined` (or `settings` itself is missing), return the default `3`.
- `0` is a valid configured value and must be returned as `0`.
 * ============================================================================
 */

function resolveRetryLimit(settings) {
  // TODO: return configured limit or default
  return null;
}

module.exports = { resolveRetryLimit };
