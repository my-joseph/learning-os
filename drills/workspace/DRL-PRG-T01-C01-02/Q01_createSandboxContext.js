/**
 * ============================================================================
 * [DRL-PRG-T01-C01-02] Q01: Problem Solving (Logic & Algorithm)
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
 * Implement `createSandboxContext(parentConfig)` for isolated plugin execution environments.

**System Requirements:**
- `get(key)`: Retrieves `key` from the local child context, or delegates to `parentConfig` if not overridden locally.
- `set(key, value)`: Stores `key` strictly in the local child context without mutating or polluting `parentConfig`.
- `has(key)`: Returns `true` if `key` exists in either child context or parent context.
- Scope Isolation: Mutating child properties must NEVER alter `parentConfig` properties.
 * ============================================================================
 */

function createSandboxContext(parentConfig = {}) {
  // TODO: implement isolated scope sandbox context
  return {
    get(key) {},
    set(key, value) {},
    has(key) { return false; }
  };
}

module.exports = { createSandboxContext };
