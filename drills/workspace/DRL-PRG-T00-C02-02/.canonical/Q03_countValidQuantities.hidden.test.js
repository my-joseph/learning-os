// Hidden Trap Test Suite for DRL-PRG-T00-C02-02 Q03
const test = require('node:test');
const assert = require('node:assert');
const { countValidQuantities } = require('../Q03_countValidQuantities.js');


test("[Q03-HIDDEN-T01] counts zero but not negatives", async () => {
  assert.strictEqual(countValidQuantities([0, -1, 5]), 2);
});

test("[Q03-HIDDEN-T02] skips decimals, NaN and nullish", async () => {
  assert.strictEqual(countValidQuantities([1.5, NaN, null, undefined, 9]), 1);
});

test("[Q03-HIDDEN-T03] handles empty input", async () => {
  assert.strictEqual(countValidQuantities([]), 0);
});

test("[Q03-HIDDEN-T04] skips booleans and empty strings", async () => {
  assert.strictEqual(countValidQuantities([true, false, '', 2]), 1);
});
