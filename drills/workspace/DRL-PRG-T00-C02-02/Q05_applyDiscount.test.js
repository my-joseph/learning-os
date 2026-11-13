// Auto-generated visible test suite for DRL-PRG-T00-C02-02 Q05
const test = require('node:test');
const assert = require('node:assert');
const { applyDiscount } = require('./Q05_applyDiscount.js');


test("[Q05-T01] applies explicit rate", async () => {
  assert.strictEqual(applyDiscount(200, 0.25), 150);
});

test("[Q05-T02] applies default rate", async () => {
  assert.strictEqual(applyDiscount(50), 45);
});
