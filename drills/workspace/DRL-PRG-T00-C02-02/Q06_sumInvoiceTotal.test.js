// Auto-generated visible test suite for DRL-PRG-T00-C02-02 Q06
const test = require('node:test');
const assert = require('node:assert');
const { sumInvoiceTotal } = require('./Q06_sumInvoiceTotal.js');


test("[Q06-T01] sums several lines with tax", async () => {
  assert.strictEqual(sumInvoiceTotal(0.1, 100, 50, 50), 220);
});

test("[Q06-T02] handles a single line", async () => {
  assert.strictEqual(sumInvoiceTotal(0.5, 40), 60);
});
