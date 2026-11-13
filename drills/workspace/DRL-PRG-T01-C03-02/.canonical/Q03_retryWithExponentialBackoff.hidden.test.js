// Hidden Trap Test Suite for DRL-PRG-T01-C03-02 Q03
const test = require('node:test');
const assert = require('node:assert');
const { retryWithExponentialBackoff } = require('../Q03_retryWithExponentialBackoff.js');


test("[Q03-HIDDEN-T01] should throw last error when retries are exhausted", async () => {
  let calls = 0;
const persistentFailure = async () => {
  calls++;
  throw new Error('Permanent database failure');
};

await assert.rejects(
  async () => {
    await retryWithExponentialBackoff(persistentFailure, { maxRetries: 2, baseDelayMs: 5 });
  },
  /Permanent database failure/
);
assert.strictEqual(calls, 3);
});
