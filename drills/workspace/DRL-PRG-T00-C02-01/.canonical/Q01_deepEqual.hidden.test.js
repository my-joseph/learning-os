// Hidden Trap Test Suite for DRL-PRG-T00-C02-01 Q01
const test = require('node:test');
const assert = require('node:assert');
const { deepEqual } = require('../Q01_deepEqual.js');


test("[Q01-HIDDEN-T01] array vs plain object distinction", async () => {
  assert.strictEqual(deepEqual([1, 2], { '0': 1, '1': 2 }), false);
});

test("[Q01-HIDDEN-T02] nested arrays comparison", async () => {
  assert.strictEqual(deepEqual([1, [2, 3]], [1, [2, 3]]), true); assert.strictEqual(deepEqual([1, [2, 3]], [1, [2, 4]]), false);
});

test("[Q01-HIDDEN-T03] missing property vs undefined value", async () => {
  assert.strictEqual(deepEqual({ x: undefined }, {}), false);
});
