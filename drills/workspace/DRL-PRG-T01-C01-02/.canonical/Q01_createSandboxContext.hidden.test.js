// Hidden Trap Test Suite for DRL-PRG-T01-C01-02 Q01
const test = require('node:test');
const assert = require('node:assert');
const { createSandboxContext } = require('../Q01_createSandboxContext.js');


test("[Q01-HIDDEN-T01] should handle missing parent properties returning undefined", async () => {
  const sandbox = createSandboxContext({});
assert.strictEqual(sandbox.get('missing'), undefined);
});
