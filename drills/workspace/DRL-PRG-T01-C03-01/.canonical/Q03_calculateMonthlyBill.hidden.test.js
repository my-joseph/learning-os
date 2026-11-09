// Hidden Trap Test Suite for DRL-PRG-T01-C03-01 Q03
const test = require('node:test');
const assert = require('node:assert');
const { calculateMonthlyBill } = require('../Q03_calculateMonthlyBill.js');


test("[Q03-HIDDEN-T01] should throw TypeError if account or plan is missing", async () => {
  assert.throws(() => calculateMonthlyBill(null), /TypeError/);
            assert.throws(() => calculateMonthlyBill({}), /TypeError/);
});

test("[Q03-HIDDEN-T02] should throw RangeError on unknown subscription plan", async () => {
  assert.throws(() => calculateMonthlyBill({ plan: 'ultimate_vip' }), /RangeError/);
});
