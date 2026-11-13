// Auto-generated visible test suite for DRL-PRG-T01-C01-02 Q01
const test = require('node:test');
const assert = require('node:assert');
const { createSandboxContext } = require('./Q01_createSandboxContext.js');


test("[Q01-T01] should shadow parent properties locally without mutating parent config", async () => {
  const parent = { env: 'production', timeout: 5000 };
const sandbox = createSandboxContext(parent);
assert.strictEqual(sandbox.get('env'), 'production');
sandbox.set('env', 'testing');
assert.strictEqual(sandbox.get('env'), 'testing');
assert.strictEqual(parent.env, 'production', 'Parent config must remain immutable!');
});

test("[Q01-T02] should verify property presence across local and parent scopes", async () => {
  const parent = { version: '1.0' };
const sandbox = createSandboxContext(parent);
sandbox.set('debug', true);
assert.strictEqual(sandbox.has('version'), true);
assert.strictEqual(sandbox.has('debug'), true);
assert.strictEqual(sandbox.has('unknown'), false);
});
