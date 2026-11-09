// Hidden Trap Test Suite for DRL-PRG-T00-C02-01 Q04
const test = require('node:test');
const assert = require('node:assert');
const { settleAllSettled } = require('../Q04_settleAllSettled.js');


test("[Q04-HIDDEN-T01] should preserve original input order when tasks complete out-of-order", async () => {
  const tasks = [
  () => new Promise(r => setTimeout(() => r('slow'), 30)),
  () => new Promise(r => setTimeout(() => r('fast'), 5))
];
const results = await settleAllSettled(tasks);
assert.strictEqual(results[0].value, 'slow');
assert.strictEqual(results[1].value, 'fast');
});
