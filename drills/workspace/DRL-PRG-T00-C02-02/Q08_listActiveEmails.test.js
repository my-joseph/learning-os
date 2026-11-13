// Auto-generated visible test suite for DRL-PRG-T00-C02-02 Q08
const test = require('node:test');
const assert = require('node:assert');
const { listActiveEmails } = require('./Q08_listActiveEmails.js');


test("[Q08-T01] keeps only active subscribers", async () => {
  const list = [{ email: 'a@shop.io', isActive: true }, { email: 'b@shop.io', isActive: false }];
assert.deepStrictEqual(listActiveEmails(list), ['a@shop.io']);
});

test("[Q08-T02] normalizes emails", async () => {
  assert.deepStrictEqual(listActiveEmails([{ email: '  Sam@Shop.IO ', isActive: true }]), ['sam@shop.io']);
});
