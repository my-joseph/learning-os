// Hidden Trap Test Suite for DRL-PRG-T01-C03-01 Q01
const test = require('node:test');
const assert = require('node:assert');
const { groupBy } = require('../Q01_groupBy.js');


test("[Q01-HIDDEN-T01] should handle empty array and null inputs without throwing", async () => {
  assert.deepStrictEqual(groupBy([], 'any'), {});
            assert.deepStrictEqual(groupBy(null, 'any'), {});
            assert.deepStrictEqual(groupBy(undefined, 'any'), {});
});

test("[Q01-HIDDEN-T02] should omit items where property evaluates to undefined", async () => {
  const items = [{ a: 'x' }, { b: 'y' }];
            const result = groupBy(items, 'a');
            assert.deepStrictEqual(result, { x: [{ a: 'x' }] });
});
