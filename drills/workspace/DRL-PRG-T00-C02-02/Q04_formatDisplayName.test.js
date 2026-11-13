// Auto-generated visible test suite for DRL-PRG-T00-C02-02 Q04
const test = require('node:test');
const assert = require('node:assert');
const { formatDisplayName } = require('./Q04_formatDisplayName.js');


test("[Q04-T01] prefers full name", async () => {
  assert.strictEqual(formatDisplayName({ fullName: 'Ada Lovelace', username: 'ada' }), 'Ada Lovelace');
});

test("[Q04-T02] falls back to username", async () => {
  assert.strictEqual(formatDisplayName({ fullName: '', username: 'ada' }), 'ada');
});
