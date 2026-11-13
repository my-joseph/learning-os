/**
 * ============================================================================
 * [DRL-PRG-T00-C02-02] Q01: Problem Solving (Logic & Algorithm)
 * Target Competencies: Engineering Fundamentals
 * ============================================================================
 * 
 * 6-STEP PEDAGOGICAL PRACTICE LOOP:
 * 1. คิดเองก่อนเขียน : Sketch invariants, mental model, and boundary edge cases.
 * 2. ลงมือทำ         : Write your implementation in this file.
 * 3. ทดสอบ           : Run `npm test` or `npm run test:q01` in this folder.
 * 4. อธิบายโค้ด      : Explain the algorithm and request an AI Senior Tech Lead PR Review.
 * 5. Refactor        : Decouple helpers, improve readability, and optimize performance.
 * 6. เพิ่มความยาก     : Scale up test inputs and handle harsher stress scenarios.
 * 
 * SPECIFICATION:
 * Implement `clampBatteryPercent(rawLevel)` for a device dashboard.

**Requirements:**
- If `rawLevel` is a finite `number`, return it limited to the range `0` to `100`.
- For anything else (numeric strings, `NaN`, `Infinity`, `null`, `undefined`), return `null`.
- Do not coerce strings into numbers.
 * ============================================================================
 */

function clampBatteryPercent(rawLevel) {
  const rawlimited = rawLevel > 0 && rawLevel <= 100;
  if (!rawlimited) {
    return null;
  }
  return rawlimited;
}

module.exports = { clampBatteryPercent };
