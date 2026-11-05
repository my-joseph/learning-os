// Auto-generated test suite for DRL-PRG-T01-C03-04 Q03
const test = require('node:test');
const assert = require('node:assert');
const { groupBy } = require('./Q03_groupBy.js');


test("[Q03-T01] should group array items by string property name", async () => {
  const items = [
              { name: 'apple', type: 'fruit' },
              { name: 'carrot', type: 'vegetable' },
              { name: 'banana', type: 'fruit' },
            ];
            const result = groupBy(items, 'type');
            assert.deepStrictEqual(result, {
              fruit: [
                { name: 'apple', type: 'fruit' },
                { name: 'banana', type: 'fruit' },
              ],
              vegetable: [
                { name: 'carrot', type: 'vegetable' },
              ],
            });
});

test("[Q03-T02] should group array items by custom function iteratee", async () => {
  const numbers = [6.1, 4.2, 6.3];
            const result = groupBy(numbers, Math.floor);
            assert.deepStrictEqual(result, {
              '4': [4.2],
              '6': [6.1, 6.3],
            });
});
