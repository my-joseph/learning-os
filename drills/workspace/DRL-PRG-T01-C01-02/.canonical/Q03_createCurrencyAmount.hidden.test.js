// Hidden Trap Test Suite for DRL-PRG-T01-C01-02 Q03
const test = require('node:test');
const assert = require('node:assert');
const { createCurrencyAmount } = require('../Q03_createCurrencyAmount.js');


test("[Q03-HIDDEN-T01] should support subtraction between two currency objects", async () => {
  const m1 = createCurrencyAmount(300, 'GBP');
const m2 = createCurrencyAmount(120, 'GBP');
assert.strictEqual(m1 - m2, 180);
});
