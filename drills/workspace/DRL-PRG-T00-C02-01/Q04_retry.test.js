// Auto-generated visible test suite for DRL-PRG-T00-C02-01 Q04
const test = require('node:test');
const assert = require('node:assert');
const { retry } = require('./Q04_retry.js');


test("[Q04-T01] resolves immediately on first attempt without delay", async () => {
  let calls = 0; const res = await retry(async () => { calls++; return 'OK'; }); assert.strictEqual(res, 'OK'); assert.strictEqual(calls, 1);
});

test("[Q04-T02] recovers on subsequent retry and observes delay", async () => {
  let calls = 0; const start = Date.now(); const res = await retry(async () => { calls++; if (calls < 3) throw new Error('Transient error'); return 'Recovered'; }, 3, 30); assert.strictEqual(res, 'Recovered'); assert.strictEqual(calls, 3); assert.ok(Date.now() - start >= 50, 'Must have waited for delays');
});
