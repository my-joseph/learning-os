// Hidden Trap Test Suite for DRL-PRG-T00-C02-01 Q03
const test = require('node:test');
const assert = require('node:assert');
const { flatten } = require('../Q03_flatten.js');


test("[Q03-HIDDEN-T01] depth 0 returns shallow copy", async () => {
  const orig = [1, [2]]; const res = flatten(orig, 0); assert.deepStrictEqual(res, [1, [2]]); assert.notStrictEqual(res, orig);
});

test("[Q03-HIDDEN-T02] deeply nested tree with Infinity", async () => {
  assert.deepStrictEqual(flatten([[[[1]]], [[2]], 3], Infinity), [1, 2, 3]);
});

test("[Q03-HIDDEN-T03] does not mutate original nested arrays", async () => {
  const inner = [2, 3]; const orig = [1, inner]; flatten(orig, 1); assert.deepStrictEqual(orig, [1, [2, 3]]); assert.strictEqual(orig[1], inner);
});
