/**
 * ============================================================================
 * [DRL-PRG-T01-C03-01] Q05: Problem Solving (Logic & Algorithm)
 * Target Competencies: Data Handling, Performance & Optimization
 * ============================================================================
 * 
 * 6-STEP PEDAGOGICAL PRACTICE LOOP:
 * 1. คิดเองก่อนเขียน : Sketch invariants, mental model, and boundary edge cases.
 * 2. ลงมือทำ         : Write your implementation in this file.
 * 3. ทดสอบ           : Run `npm test` or `npm run test:q05` in this folder.
 * 4. อธิบายโค้ด      : Explain the algorithm and request an AI Senior Tech Lead PR Review.
 * 5. Refactor        : Decouple helpers, improve readability, and optimize performance.
 * 6. เพิ่มความยาก     : Scale up test inputs and handle harsher stress scenarios.
 * 
 * SPECIFICATION:
 * Implement a `groupBy(collection, iteratee)` utility in JavaScript.

**Behavioral Requirements:**
- Splits `collection` into sets grouped by the result of running each value through `iteratee`.
- `iteratee` can be either a function (e.g. `Math.floor`) or a string property name (e.g. `'type'`).
- Return an empty object `{}` if `collection` is `null`, `undefined`, or an empty array.
 * ============================================================================
 */

function groupBy(collection, iteratee) {
  // TODO: Group elements of collection into an object based on iteratee
  return {};
}

module.exports = { groupBy };
