// Auto-generated visible test suite for DRL-PRG-T01-C01-02 Q05
const test = require('node:test');
const assert = require('node:assert');
const { composeAsyncMiddleware } = require('./Q05_composeAsyncMiddleware.js');


test("[Q05-T01] should execute middlewares in onion sequence downstream and upstream", async () => {
  const executionLog = [];
const m1 = async (ctx, next) => {
  executionLog.push('m1_enter');
  ctx.state += ':m1';
  await next();
  executionLog.push('m1_exit');
};
const m2 = async (ctx, next) => {
  executionLog.push('m2_enter');
  ctx.state += ':m2';
  await next();
  executionLog.push('m2_exit');
};
const pipeline = composeAsyncMiddleware([m1, m2]);
const ctx = { state: 'init' };
await pipeline(ctx);
assert.strictEqual(ctx.state, 'init:m1:m2');
assert.deepStrictEqual(executionLog, ['m1_enter', 'm2_enter', 'm2_exit', 'm1_exit']);
});

test("[Q05-T02] should reject when next is invoked multiple times in a single middleware", async () => {
  const badMiddleware = async (ctx, next) => {
  await next();
  await next(); // Illegal second call
};
const pipeline = composeAsyncMiddleware([badMiddleware]);
await assert.rejects(async () => pipeline({}), /next\(\) called multiple times/);
});
