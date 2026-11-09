// Hidden Trap Test Suite for DRL-PRG-T01-C01-02 Q04
const test = require('node:test');
const assert = require('node:assert');
const { deepCloneCircular } = require('../Q04_deepCloneCircular.js');


test("[Q04-HIDDEN-T01] should handle primitives, functions, and null cleanly", async () => {
  const fn = () => 42;
assert.strictEqual(deepCloneCircular(100), 100);
assert.strictEqual(deepCloneCircular(null), null);
assert.strictEqual(deepCloneCircular(fn), fn);
});
