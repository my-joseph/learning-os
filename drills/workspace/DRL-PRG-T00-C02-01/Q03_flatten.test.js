// Auto-generated visible test suite for DRL-PRG-T00-C02-01 Q03
const test = require('node:test');
const assert = require('node:assert');
const { flatten } = require('./Q03_flatten.js');


test("[Q03-T01] default depth 1 flattening", async () => {
  assert.deepStrictEqual(flatten([1, [2, [3, [4]]]]), [1, 2, [3, [4]]]);
});

test("[Q03-T02] specified depth 2 flattening", async () => {
  assert.deepStrictEqual(flatten([1, [2, [3, [4]]]], 2), [1, 2, 3, [4]]);
});

test("[Q03-T03] preserves all falsy values and types", async () => {
  assert.deepStrictEqual(flatten([0, [false, [null, [undefined, '']]]], Infinity), [0, false, null, undefined, '']);
});
