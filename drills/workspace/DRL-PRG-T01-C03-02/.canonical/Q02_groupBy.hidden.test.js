// Hidden Trap Test Suite for DRL-PRG-T01-C03-02 Q02
const test = require('node:test');
const assert = require('node:assert');
const { groupBy } = require('../Q02_groupBy.js');


test("[Q02-HIDDEN-T01] should handle empty array and null inputs without throwing", async () => {
  assert.deepStrictEqual(groupBy([], 'any'), {});
            assert.deepStrictEqual(groupBy(null, 'any'), {});
            assert.deepStrictEqual(groupBy(undefined, 'any'), {});
});

test("[Q02-HIDDEN-T02] should omit items where property evaluates to undefined", async () => {
  const items = [{ a: 'x' }, { b: 'y' }];
            const result = groupBy(items, 'a');
            assert.deepStrictEqual(result, { x: [{ a: 'x' }] });
});
