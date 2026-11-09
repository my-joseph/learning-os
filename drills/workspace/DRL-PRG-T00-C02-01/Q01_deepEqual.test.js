// Auto-generated visible test suite for DRL-PRG-T00-C02-01 Q01
const test = require('node:test');
const assert = require('node:assert');
const { deepEqual } = require('./Q01_deepEqual.js');


test("[Q01-T01] primitives and NaN comparison", async () => {
  assert.strictEqual(deepEqual(1, 1), true); assert.strictEqual(deepEqual(NaN, NaN), true); assert.strictEqual(deepEqual(1, '1'), false);
});

test("[Q01-T02] null and undefined edge cases", async () => {
  assert.strictEqual(deepEqual(null, null), true); assert.strictEqual(deepEqual(null, undefined), false); assert.strictEqual(deepEqual({}, null), false);
});

test("[Q01-T03] nested objects and mismatched keys", async () => {
  assert.strictEqual(deepEqual({ a: 1, b: { c: 2 } }, { a: 1, b: { c: 2 } }), true); assert.strictEqual(deepEqual({ a: 1 }, { a: 1, b: 2 }), false);
});
