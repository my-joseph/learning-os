// Hidden Trap Test Suite for DRL-PRG-T00-C02-02 Q02
const test = require('node:test');
const assert = require('node:assert');
const { resolveRetryLimit } = require('../Q02_resolveRetryLimit.js');


test("[Q02-HIDDEN-T01] preserves zero", async () => {
  assert.strictEqual(resolveRetryLimit({ maxRetries: 0 }), 0);
});

test("[Q02-HIDDEN-T02] handles missing settings", async () => {
  assert.strictEqual(resolveRetryLimit(undefined), 3);
assert.strictEqual(resolveRetryLimit(null), 3);
});

test("[Q02-HIDDEN-T03] keeps other falsy values", async () => {
  assert.strictEqual(resolveRetryLimit({ maxRetries: NaN }) !== 3, true);
});
