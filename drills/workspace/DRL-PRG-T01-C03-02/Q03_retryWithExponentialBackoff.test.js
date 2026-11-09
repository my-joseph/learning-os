// Auto-generated visible test suite for DRL-PRG-T01-C03-02 Q03
const test = require('node:test');
const assert = require('node:assert');
const { retryWithExponentialBackoff } = require('./Q03_retryWithExponentialBackoff.js');


test("[Q03-T01] should resolve successfully after transient failures", async () => {
  let calls = 0;
const flakyTask = async () => {
  calls++;
  if (calls < 3) throw new Error('Network reset');
  return 'SUCCESS';
};

const result = await retryWithExponentialBackoff(flakyTask, { maxRetries: 3, baseDelayMs: 5 });
assert.strictEqual(result, 'SUCCESS');
assert.strictEqual(calls, 3);
});

test("[Q03-T02] should not retry non-transient client errors", async () => {
  let calls = 0;
const clientErrorTask = async () => {
  calls++;
  const err = new Error('Bad Request');
  err.statusCode = 400;
  throw err;
};

await assert.rejects(
  async () => {
    await retryWithExponentialBackoff(clientErrorTask, {
      maxRetries: 3,
      baseDelayMs: 5,
      isRetryable: (e) => e.statusCode >= 500
    });
  },
  (err) => {
    assert.strictEqual(err.statusCode, 400);
    return true;
  }
);
assert.strictEqual(calls, 1);
});
