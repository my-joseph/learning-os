// Hidden Trap Test Suite for DRL-PRG-T01-C03-01 Q02
const test = require('node:test');
const assert = require('node:assert');
const { debounce } = require('../Q02_debounce.js');


test("[Q02-HIDDEN-T01] should preserve execution 'this' context and multiple arguments", async () => {
  let received = null;
            const ctx = { multiplier: 10 };
            const debounced = debounce(function(a, b) {
              received = (this.multiplier || 1) * (a + b);
            }, 30);
            debounced.call(ctx, 3, 4);
            await new Promise(r => setTimeout(r, 50));
            assert.strictEqual(received, 70, "Must preserve 'this' and all arguments");
});

test("[Q02-HIDDEN-T02] should support 0ms delay as a macrotask deferral", async () => {
  let called = false;
            const debounced = debounce(() => { called = true; }, 0);
            debounced();
            assert.strictEqual(called, false, "0ms timeout still defers to next macrotask");
            await new Promise(r => setTimeout(r, 20));
            assert.strictEqual(called, true, "Should fire in subsequent event loop cycle");
});
