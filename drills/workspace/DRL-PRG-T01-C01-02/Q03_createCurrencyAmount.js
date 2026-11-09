/**
 * ============================================================================
 * [DRL-PRG-T01-C01-02] Q03: Debugging (Bug Triage & Root Cause)
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
 * Debug `createCurrencyAmount(amount, currency)` in a fintech ledger calculation engine.

**System Requirements:**
- Returns an immutable Value Object representing a monetary amount.
- In numeric arithmetic contexts (`+`, `-`, `>`, `<`), the object must evaluate to its numeric `amount`.
- In string contexts (template literals, string concatenation), it evaluates to formatted `"<amount> <currency>"`.
- Strict Numeric Addition: `createCurrencyAmount(100, 'USD') + 50` must yield `150`, NOT `"100 USD50"`.
 * ============================================================================
 */

function createCurrencyAmount(amount, currency) {
  // Defective implementation where valueOf returns string causing string concatenation
  return {
    amount,
    currency,
    valueOf() {
      return `${amount} ${currency}`;
    },
    toString() {
      return `${amount} ${currency}`;
    }
  };
}

module.exports = { createCurrencyAmount };
