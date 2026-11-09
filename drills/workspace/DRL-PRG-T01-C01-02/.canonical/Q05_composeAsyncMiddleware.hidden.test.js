// Hidden Trap Test Suite for DRL-PRG-T01-C01-02 Q05
const test = require('node:test');
const assert = require('node:assert');
const { composeAsyncMiddleware } = require('../Q05_composeAsyncMiddleware.js');


test("[Q05-HIDDEN-T01] should propagate downstream errors back to upstream catch blocks", async () => {
  let caughtError = null;
const errorHandler = async (ctx, next) => {
  try { await next(); } catch (err) { caughtError = err.message; }
};
const crasher = async () => { throw new Error('Database connection failed'); };
const pipeline = composeAsyncMiddleware([errorHandler, crasher]);
await pipeline({});
assert.strictEqual(caughtError, 'Database connection failed');
});
