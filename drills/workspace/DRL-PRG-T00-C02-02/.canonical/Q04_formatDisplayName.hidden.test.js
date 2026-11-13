// Hidden Trap Test Suite for DRL-PRG-T00-C02-02 Q04
const test = require('node:test');
const assert = require('node:assert');
const { formatDisplayName } = require('../Q04_formatDisplayName.js');


test("[Q04-HIDDEN-T01] trims whitespace", async () => {
  assert.strictEqual(formatDisplayName({ fullName: '  Grace Hopper  ' }), 'Grace Hopper');
assert.strictEqual(formatDisplayName({ fullName: '   ', username: ' grace ' }), 'grace');
});

test("[Q04-HIDDEN-T02] returns Guest when nothing usable", async () => {
  assert.strictEqual(formatDisplayName({}), 'Guest');
assert.strictEqual(formatDisplayName({ fullName: ' ', username: '' }), 'Guest');
assert.strictEqual(formatDisplayName(undefined), 'Guest');
});
