// Auto-generated test file for DRL-PRG-T01-C03-02 Q01
const test = require('node:test');
const assert = require('node:assert');
const { groupBy } = require('./Q01_groupBy.js');


test("should group elements by a property name string", async () => {
  const items = [
              { stage: 'dev', name: 'app1' },
              { stage: 'prod', name: 'app2' },
              { stage: 'dev', name: 'app3' },
            ];
            const grouped = groupBy(items, 'stage');
            assert.deepStrictEqual(grouped.dev, [
              { stage: 'dev', name: 'app1' },
              { stage: 'dev', name: 'app3' },
            ]);
            assert.deepStrictEqual(grouped.prod, [
              { stage: 'prod', name: 'app2' },
            ]);
});

test("should group elements by a custom callback function", async () => {
  const numbers = [6.1, 4.2, 6.3];
            const grouped = groupBy(numbers, Math.floor);
            assert.deepStrictEqual(grouped['6'], [6.1, 6.3]);
            assert.deepStrictEqual(grouped['4'], [4.2]);
});
