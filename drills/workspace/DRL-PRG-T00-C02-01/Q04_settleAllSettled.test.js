// Auto-generated visible test suite for DRL-PRG-T00-C02-01 Q04
const test = require('node:test');
const assert = require('node:assert');
const { settleAllSettled } = require('./Q04_settleAllSettled.js');


test("[Q04-T01] should resolve all concurrent tasks with mixed fulfillment and rejection", async () => {
  const tasks = [
  async () => 'auth_healthy',
  async () => { throw new Error('db_timeout'); },
  async () => 'cache_healthy'
];
const results = await settleAllSettled(tasks);
assert.strictEqual(results.length, 3);
assert.strictEqual(results[0].status, 'fulfilled');
assert.strictEqual(results[0].value, 'auth_healthy');
assert.strictEqual(results[1].status, 'rejected');
assert.strictEqual(results[1].reason.message, 'db_timeout');
assert.strictEqual(results[2].status, 'fulfilled');
assert.strictEqual(results[2].value, 'cache_healthy');
});

test("[Q04-T02] should handle synchronous exceptions thrown inside task functions gracefully", async () => {
  const tasks = [
  () => { throw new Error('sync_crash'); }
];
const results = await settleAllSettled(tasks);
assert.strictEqual(results[0].status, 'rejected');
assert.strictEqual(results[0].reason.message, 'sync_crash');
});
