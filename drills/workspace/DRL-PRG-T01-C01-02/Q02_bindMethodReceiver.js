/**
 * ============================================================================
 * [DRL-PRG-T01-C01-02] Q02: Problem Solving (Logic & Algorithm)
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
 * Implement `bindMethodReceiver(targetInstance, methodNames)` for detached pub/sub event listeners.

**System Requirements:**
- `targetInstance`: An object or class instance containing member methods.
- `methodNames`: Array of string method names to bind.
- Binds each method on `targetInstance` so that detached calls (e.g. `const cb = targetInstance.method; cb()`) retain `this === targetInstance`.
- Preserves prototype method inheritance and passes through all arguments and return values.
- Returns `targetInstance` for fluent chaining.
 * ============================================================================
 */

function bindMethodReceiver(targetInstance, methodNames) {
  // TODO: implement context binding for detached methods
  return targetInstance;
}

module.exports = { bindMethodReceiver };
