// Auto-generated visible test suite for DRL-PRG-T00-C02-01 Q03
const test = require('node:test');
const assert = require('node:assert');
const { aggregateCategoryRevenue } = require('./Q03_aggregateCategoryRevenue.js');


test("[Q03-T01] should calculate net revenue per category accounting for refunds and completed orders", async () => {
  const txs = [
  { category: 'hardware', amount: 150, status: 'completed' },
  { category: 'software', amount: 80, status: 'completed' },
  { category: 'hardware', amount: 50, status: 'refunded' },
  { category: 'software', amount: 200, status: 'pending' }
];
const res = aggregateCategoryRevenue(txs);
assert.strictEqual(res.hardware, 100);
assert.strictEqual(res.software, 80);
});

test("[Q03-T02] should not mutate the original order or elements of the input array (Reproducer Test)", async () => {
  const txs = [
  { category: 'zebra', amount: 100, status: 'completed' },
  { category: 'apple', amount: 50, status: 'completed' }
];
const originalFirst = txs[0].category;
aggregateCategoryRevenue(txs);
assert.strictEqual(txs[0].category, originalFirst, 'Input array was mutated in-place by sort!');
});
