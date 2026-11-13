// Hidden Trap Test Suite for DRL-PRG-T00-C02-02 Q08
const test = require('node:test');
const assert = require('node:assert');
const { listActiveEmails } = require('../Q08_listActiveEmails.js');


test("[Q08-HIDDEN-T01] preserves order", async () => {
  const list = [{ email: 'z@x.io', isActive: true }, { email: 'a@x.io', isActive: true }, { email: 'm@x.io', isActive: true }];
assert.deepStrictEqual(listActiveEmails(list), ['z@x.io', 'a@x.io', 'm@x.io']);
});

test("[Q08-HIDDEN-T02] empty and all-inactive", async () => {
  assert.deepStrictEqual(listActiveEmails([]), []);
assert.deepStrictEqual(listActiveEmails([{ email: 'q@x.io', isActive: false }]), []);
});

test("[Q08-HIDDEN-T03] does not mutate input", async () => {
  const list = [{ email: ' T@X.io ', isActive: true }];
listActiveEmails(list);
assert.deepStrictEqual(list, [{ email: ' T@X.io ', isActive: true }]);
});
