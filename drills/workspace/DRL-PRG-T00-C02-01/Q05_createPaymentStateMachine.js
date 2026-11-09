/**
 * ============================================================================
 * [DRL-PRG-T00-C02-01] Q05: Problem Solving (Logic & Algorithm)
 * Target Competencies: TypeScript Typing, state-machine
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
 * Implement `createPaymentStateMachine(options = {})` for e-commerce checkout transaction lifecycles.

**State Transitions Specification:**
- Initial state: `INITIAL`.
- Allowed transition actions:
  - `INITIAL` -> `dispatch({ type: 'AUTHORIZE', orderId, amount })` -> transitions to `AUTHORIZED`.
  - `AUTHORIZED` -> `dispatch({ type: 'CAPTURE' })` -> transitions to `SETTLED`.
  - `AUTHORIZED` -> `dispatch({ type: 'VOID' })` -> transitions to `VOIDED`.
- Invalid Transitions: Dispatching an action incompatible with current state throws `Error('INVALID_STATE_TRANSITION')`.
- Terminal States: `SETTLED` and `VOIDED` are final; any subsequent dispatch must throw.
- `getState()`: Returns `{ status, orderId, amount }`.
 * ============================================================================
 */

function createPaymentStateMachine(options = {}) {
  // TODO: implement payment transaction state machine
  return {
    dispatch(action) {},
    getState() { return { status: 'INITIAL' }; }
  };
}

module.exports = { createPaymentStateMachine };
