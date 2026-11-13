// Auto-generated visible test suite for DRL-PRG-T00-C02-02 Q02
const test = require('node:test');
const assert = require('node:assert');
const { resolveRetryLimit } = require('./Q02_resolveRetryLimit.js');


test("[Q02-T01] uses configured value", async () => {
  assert.strictEqual(resolveRetryLimit({ maxRetries: 5 }), 5);
});

test("[Q02-T02] falls back when missing", async () => {
  assert.strictEqual(resolveRetryLimit({}), 3);
assert.strictEqual(resolveRetryLimit({ maxRetries: null }), 3);
});
