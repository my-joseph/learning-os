// Hidden Trap Test Suite for DRL-PRG-T00-C02-02 Q10
const test = require('node:test');
const assert = require('node:assert');
const { adjustStock } = require('../Q10_adjustStock.js');


test("[Q10-HIDDEN-T01] creates missing SKU", async () => {
  assert.deepStrictEqual(adjustStock({ 'SKU-1': 4 }, 'SKU-7', 2), { 'SKU-1': 4, 'SKU-7': 2 });
});

test("[Q10-HIDDEN-T02] does not mutate original", async () => {
  const original = { 'SKU-1': 4 };
const updated = adjustStock(original, 'SKU-1', 1);
assert.deepStrictEqual(original, { 'SKU-1': 4 });
assert.notStrictEqual(updated, original);
});

test("[Q10-HIDDEN-T03] works from empty ledger", async () => {
  assert.deepStrictEqual(adjustStock({}, 'SKU-3', 5), { 'SKU-3': 5 });
});
