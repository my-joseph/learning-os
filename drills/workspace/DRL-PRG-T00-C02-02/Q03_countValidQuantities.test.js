// Auto-generated visible test suite for DRL-PRG-T00-C02-02 Q03
const test = require('node:test');
const assert = require('node:assert');
const { countValidQuantities } = require('./Q03_countValidQuantities.js');


test("[Q03-T01] counts clean integers", async () => {
  assert.strictEqual(countValidQuantities([1, 2, 3]), 3);
});

test("[Q03-T02] skips numeric strings", async () => {
  assert.strictEqual(countValidQuantities([4, '12', 7]), 2);
});
