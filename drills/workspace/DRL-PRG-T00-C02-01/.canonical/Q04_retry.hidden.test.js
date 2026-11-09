// Hidden Trap Test Suite for DRL-PRG-T00-C02-01 Q04
const test = require('node:test');
const assert = require('node:assert');
const { retry } = require('../Q04_retry.js');


test("[Q04-HIDDEN-T01] exhausting all retries throws final error", async () => {
  let calls = 0; await assert.rejects(async () => { await retry(async () => { calls++; throw new Error('Fatal error ' + calls); }, 2, 20); }, /Fatal error 3/); assert.strictEqual(calls, 3);
});

test("[Q04-HIDDEN-T02] zero retries executes exactly once", async () => {
  let calls = 0; await assert.rejects(async () => { await retry(async () => { calls++; throw new Error('fail'); }, 0, 50); }); assert.strictEqual(calls, 1);
});
