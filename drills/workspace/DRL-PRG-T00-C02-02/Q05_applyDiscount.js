/**
 * ============================================================================
 * [DRL-PRG-T00-C02-02] Q05: Problem Solving (Logic & Algorithm)
 * Target Competencies: Engineering Fundamentals
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
 * Implement `applyDiscount(price, rate)` for a checkout service.

**Requirements:**
- `price` is a number in dollars; `rate` is a fraction (for example `0.2` means 20% off).
- When `rate` is not supplied, use a default rate of `0.1`.
- Return the discounted price rounded to 2 decimal places as a number.
- An explicit rate of `0` means no discount and must be respected.
 * ============================================================================
 */

function applyDiscount(price, rate) {
  // TODO: apply default rate and round to cents
  return null;
}

module.exports = { applyDiscount };
