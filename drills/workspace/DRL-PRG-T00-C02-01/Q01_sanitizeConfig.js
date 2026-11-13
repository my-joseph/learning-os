/**
 * ============================================================================
 * [DRL-PRG-T00-C02-01] Q01: Problem Solving (Logic & Algorithm)
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
 * Implement `sanitizeConfig(rawConfig, schema)` for microservice environment configurations.

**System Requirements:**
- `schema` defines expected keys and their default primitive values: `{ [key: string]: string | number | boolean }`.
- For each key in `schema`: if `rawConfig[key]` is `null` or `undefined`, fall back to `schema[key]`.
- Crucial: Legitimate falsy primitive values (`0`, `false`, `""`) in `rawConfig` must be preserved and NOT overwritten by defaults.
- Discard any extraneous keys in `rawConfig` that are not present in `schema`.
 * ============================================================================
 */

function sanitizeConfig(rawConfig, schema) {
  // TODO: implement defensive config sanitization
  return {};
}

module.exports = { sanitizeConfig };
