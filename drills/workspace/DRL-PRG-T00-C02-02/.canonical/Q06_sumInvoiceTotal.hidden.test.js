// Hidden Trap Test Suite for DRL-PRG-T00-C02-02 Q06
const test = require('node:test');
const assert = require('node:assert');
const { sumInvoiceTotal } = require('../Q06_sumInvoiceTotal.js');


test("[Q06-HIDDEN-T01] returns zero without lines", async () => {
  assert.strictEqual(sumInvoiceTotal(0.2), 0);
});

test("[Q06-HIDDEN-T02] rounds to cents", async () => {
  assert.strictEqual(sumInvoiceTotal(0.07, 9.99, 5.01), 16.05);
});

test("[Q06-HIDDEN-T03] supports zero tax", async () => {
  assert.strictEqual(sumInvoiceTotal(0, 1.25, 2.5), 3.75);
});
