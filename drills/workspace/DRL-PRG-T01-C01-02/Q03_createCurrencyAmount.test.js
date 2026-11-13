// Auto-generated visible test suite for DRL-PRG-T01-C01-02 Q03
const test = require('node:test');
const assert = require('node:assert');
const { createCurrencyAmount } = require('./Q03_createCurrencyAmount.js');


test("[Q03-T01] should perform numeric addition and comparison rather than string concatenation (Reproducer Test)", async () => {
  const money = createCurrencyAmount(100, 'USD');
const sum = money + 50;
assert.strictEqual(sum, 150, 'Failed: money + 50 must yield numeric 150!');
assert.strictEqual(money > 80, true);
});

test("[Q03-T02] should format cleanly in explicit string contexts", async () => {
  const money = createCurrencyAmount(250.5, 'EUR');
assert.strictEqual(`${money}`, '250.5 EUR');
assert.strictEqual(String(money), '250.5 EUR');
});
