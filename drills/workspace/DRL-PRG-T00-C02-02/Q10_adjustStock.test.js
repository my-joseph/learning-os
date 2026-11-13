// Auto-generated visible test suite for DRL-PRG-T00-C02-02 Q10
const test = require('node:test');
const assert = require('node:assert');
const { adjustStock } = require('./Q10_adjustStock.js');


test("[Q10-T01] increases existing quantity", async () => {
  assert.deepStrictEqual(adjustStock({ 'SKU-1': 4, 'SKU-2': 9 }, 'SKU-1', 3), { 'SKU-1': 7, 'SKU-2': 9 });
});

test("[Q10-T02] decreases quantity", async () => {
  assert.deepStrictEqual(adjustStock({ 'SKU-1': 4 }, 'SKU-1', -4), { 'SKU-1': 0 });
});
