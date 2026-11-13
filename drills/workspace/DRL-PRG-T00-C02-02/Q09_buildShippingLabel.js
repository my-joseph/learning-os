/**
 * ============================================================================
 * [DRL-PRG-T00-C02-02] Q09: Problem Solving (Logic & Algorithm)
 * Target Competencies: Engineering Fundamentals
 * ============================================================================
 * 
 * 6-STEP PEDAGOGICAL PRACTICE LOOP:
 * 1. คิดเองก่อนเขียน : Sketch invariants, mental model, and boundary edge cases.
 * 2. ลงมือทำ         : Write your implementation in this file.
 * 3. ทดสอบ           : Run `npm test` or `npm run test:q09` in this folder.
 * 4. อธิบายโค้ด      : Explain the algorithm and request an AI Senior Tech Lead PR Review.
 * 5. Refactor        : Decouple helpers, improve readability, and optimize performance.
 * 6. เพิ่มความยาก     : Scale up test inputs and handle harsher stress scenarios.
 * 
 * SPECIFICATION:
 * Implement `buildShippingLabel(order)` for a shipping label printer.

**Requirements:**
- `order` has the shape `{ customer: { name, address: { city, postalCode } }, items: [...] }`.
- Return a string formatted exactly as `NAME - CITY POSTALCODE (N items)` where `N` is the number of items.
- Use `1 item` (singular) when there is exactly one item.
 * ============================================================================
 */

function buildShippingLabel(order) {
  // TODO: destructure nested fields and format
  return null;
}

module.exports = { buildShippingLabel };
