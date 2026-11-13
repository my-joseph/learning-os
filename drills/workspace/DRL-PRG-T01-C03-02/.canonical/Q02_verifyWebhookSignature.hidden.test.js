// Hidden Trap Test Suite for DRL-PRG-T01-C03-02 Q02
const test = require('node:test');
const assert = require('node:assert');
const { verifyWebhookSignature } = require('../Q02_verifyWebhookSignature.js');


test("[Q02-HIDDEN-T01] should reject tampered payload or altered secret", async () => {
  const crypto = require('crypto');
const secret = 'whsec_test_secret_key_123';
const payload = '{"event":"charge.succeeded","amount":2500}';
const now = Math.floor(Date.now() / 1000);
const sig = crypto.createHmac('sha256', secret).update(`${now}.${payload}`).digest('hex');
const header = `t=${now},v1=${sig}`;

assert.strictEqual(verifyWebhookSignature('{"event":"charge.tampered"}', header, secret, 300), false);
});
