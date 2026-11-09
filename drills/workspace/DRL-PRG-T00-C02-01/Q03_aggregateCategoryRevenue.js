/**
 * ============================================================================
 * [DRL-PRG-T00-C02-01] Q03: Debugging (Bug Triage & Root Cause)
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
 * Debug `aggregateCategoryRevenue(transactions)` in an e-commerce revenue accounting service.

**System Requirements:**
- `transactions`: Array of `{ category: string, amount: number, status: 'completed' | 'refunded' | 'pending' }`.
- Sum total net revenue per category: completed transactions add `amount`, refunded transactions subtract `amount`, pending are ignored.
- Immutability Contract: Input `transactions` array and its items must remain strictly unmodified (no in-place sorting or mutations).
- Return format: Object `{ [category]: netRevenue }` rounded to 2 decimal places.
 * ============================================================================
 */

function aggregateCategoryRevenue(transactions) {
  // Naive implementation with destructive in-place mutation and sorting
  transactions.sort((a, b) => a.category.localeCompare(b.category));
  const revenue = {};
  for (const tx of transactions) {
    if (tx.status === 'pending') continue;
    revenue[tx.category] = (revenue[tx.category] || 0) + tx.amount;
  }
  return revenue;
}

module.exports = { aggregateCategoryRevenue };
