// Auto-generated visible test suite for DRL-PRG-T00-C02-01 Q05
const test = require('node:test');
const assert = require('node:assert');
const { createPaymentStateMachine } = require('./Q05_createPaymentStateMachine.js');


test("[Q05-T01] should transition through complete authorization and capture lifecycle", async () => {
  const fsm = createPaymentStateMachine();
assert.strictEqual(fsm.getState().status, 'INITIAL');
fsm.dispatch({ type: 'AUTHORIZE', orderId: 'ord-101', amount: 250 });
assert.strictEqual(fsm.getState().status, 'AUTHORIZED');
assert.strictEqual(fsm.getState().amount, 250);
fsm.dispatch({ type: 'CAPTURE' });
assert.strictEqual(fsm.getState().status, 'SETTLED');
});

test("[Q05-T02] should reject invalid transitions and throw INVALID_STATE_TRANSITION", async () => {
  const fsm = createPaymentStateMachine();
assert.throws(() => fsm.dispatch({ type: 'CAPTURE' }), /INVALID_STATE_TRANSITION/);
fsm.dispatch({ type: 'AUTHORIZE', orderId: 'ord-102', amount: 50 });
fsm.dispatch({ type: 'VOID' });
assert.strictEqual(fsm.getState().status, 'VOIDED');
assert.throws(() => fsm.dispatch({ type: 'CAPTURE' }), /INVALID_STATE_TRANSITION/);
});
