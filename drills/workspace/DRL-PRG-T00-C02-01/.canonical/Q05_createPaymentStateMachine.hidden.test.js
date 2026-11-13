// Hidden Trap Test Suite for DRL-PRG-T00-C02-01 Q05
const test = require('node:test');
const assert = require('node:assert');
const { createPaymentStateMachine } = require('../Q05_createPaymentStateMachine.js');


test("[Q05-HIDDEN-T01] should prevent transitions on unknown action types in authorized state", async () => {
  const fsm = createPaymentStateMachine();
fsm.dispatch({ type: 'AUTHORIZE', orderId: 'ord-103', amount: 99 });
assert.throws(() => fsm.dispatch({ type: 'UNKNOWN_OP' }), /INVALID_STATE_TRANSITION/);
assert.strictEqual(fsm.getState().status, 'AUTHORIZED');
});
