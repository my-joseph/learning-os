// Auto-generated visible test suite for DRL-PRG-T01-C03-01 Q09
const test = require('node:test');
const assert = require('node:assert');
const { debounce } = require('./Q09_debounce.js');


test("[Q09-T01] should not execute synchronously and only fire once after 50ms", async () => {
  let callCount = 0;
            const debounced = debounce(() => { callCount++; }, 50);
            debounced();
            debounced();
            debounced();
            assert.strictEqual(callCount, 0, "Should not fire immediately");
            await new Promise(r => setTimeout(r, 80));
            assert.strictEqual(callCount, 1, "Should fire exactly once after delay");
});

test("[Q09-T02] should reset the timer on each subsequent call within delay window", async () => {
  let value = 0;
            const debounced = debounce((v) => { value = v; }, 50);
            debounced(1);
            await new Promise(r => setTimeout(r, 25));
            debounced(2);
            await new Promise(r => setTimeout(r, 25));
            assert.strictEqual(value, 0, "Should still be 0 before second delay expires");
            await new Promise(r => setTimeout(r, 50));
            assert.strictEqual(value, 2, "Should record latest value 2");
});
