// Hidden Trap Test Suite for DRL-PRG-T00-C02-02 Q05
const test = require('node:test');
const assert = require('node:assert');
const { applyDiscount } = require('../Q05_applyDiscount.js');


test("[Q05-HIDDEN-T01] respects zero rate", async () => {
  assert.strictEqual(applyDiscount(80, 0), 80);
});

test("[Q05-HIDDEN-T02] rounds to cents", async () => {
  assert.strictEqual(applyDiscount(19.99, 0.15), 16.99);
});

test("[Q05-HIDDEN-T03] treats undefined as missing", async () => {
  assert.strictEqual(applyDiscount(100, undefined), 90);
});
