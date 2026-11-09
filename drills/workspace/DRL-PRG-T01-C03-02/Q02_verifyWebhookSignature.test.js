// Auto-generated visible test suite for DRL-PRG-T01-C03-02 Q02
const test = require('node:test');
const assert = require('node:assert');
const { verifyWebhookSignature } = require('./Q02_verifyWebhookSignature.js');


test("[Q02-T01] should verify valid signature within valid timestamp window", async () => {
  const crypto = require('crypto');
const secret = 'whsec_test_secret_key_123';
const payload = '{"event":"charge.succeeded","amount":2500}';
const now = Math.floor(Date.now() / 1000);
const sig = crypto.createHmac('sha256', secret).update(`${now}.${payload}`).digest('hex');
const header = `t=${now},v1=${sig}`;

assert.strictEqual(verifyWebhookSignature(payload, header, secret, 300), true);
});

test("[Q02-T02] should reject replayed request with expired timestamp (Reproducer Test)", async () => {
  const crypto = require('crypto');
const secret = 'whsec_test_secret_key_123';
const payload = '{"event":"charge.succeeded","amount":2500}';
const expiredTime = Math.floor(Date.now() / 1000) - 600;
const sig = crypto.createHmac('sha256', secret).update(`${expiredTime}.${payload}`).digest('hex');
const header = `t=${expiredTime},v1=${sig}`;

// Starter code BUG: returns true because signature matches; fixed code MUST return false
assert.strictEqual(verifyWebhookSignature(payload, header, secret, 300), false);
});
