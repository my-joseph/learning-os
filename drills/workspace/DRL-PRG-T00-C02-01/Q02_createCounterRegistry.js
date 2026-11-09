/**
 * ============================================================================
 * [DRL-PRG-T00-C02-01] Q02: Problem Solving (Logic & Algorithm)
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
 * Implement `createCounterRegistry()` to track high-throughput microservice metrics.

**System Requirements:**
- `increment(metric, amount = 1)`: Increases the integer counter for `metric` by `amount`. Defaults to starting at 0.
- `getCount(metric)`: Returns the current count for `metric`, or `0` if not yet incremented.
- `getSnapshot()`: Returns a snapshot plain object containing `{ [metric]: count }`.
- Immutability & Encapsulation: Mutating the object returned by `getSnapshot()` must NOT alter internal registry state.
 * ============================================================================
 */

function createCounterRegistry() {
  // TODO: implement encapsulated metric counter registry
  return {
    increment(metric, amount = 1) {},
    getCount(metric) { return 0; },
    getSnapshot() { return {}; }
  };
}

module.exports = { createCounterRegistry };
