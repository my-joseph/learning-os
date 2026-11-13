/**
 * ============================================================================
 * [DRL-PRG-T00-C02-02] Q10: Problem Solving (Logic & Algorithm)
 * Target Competencies: Engineering Fundamentals
 * ============================================================================
 * 
 * 6-STEP PEDAGOGICAL PRACTICE LOOP:
 * 1. คิดเองก่อนเขียน : Sketch invariants, mental model, and boundary edge cases.
 * 2. ลงมือทำ         : Write your implementation in this file.
 * 3. ทดสอบ           : Run `npm test` or `npm run test:q10` in this folder.
 * 4. อธิบายโค้ด      : Explain the algorithm and request an AI Senior Tech Lead PR Review.
 * 5. Refactor        : Decouple helpers, improve readability, and optimize performance.
 * 6. เพิ่มความยาก     : Scale up test inputs and handle harsher stress scenarios.
 * 
 * SPECIFICATION:
 * Implement `adjustStock(stockBySku, sku, delta)` for a stock ledger.

**Requirements:**
- `stockBySku` maps SKU strings to integer quantities, for example `{ 'SKU-1': 4 }`.
- Return a **new** object where `sku` has its quantity increased by `delta` (`delta` may be negative).
- A SKU that does not exist yet starts from `0`.
- The original `stockBySku` object must remain unchanged.
 * ============================================================================
 */

function adjustStock(stockBySku, sku, delta) {
  // TODO: return updated copy
  return null;
}

module.exports = { adjustStock };
