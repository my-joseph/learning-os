// Auto-generated test file for DRL-PRG-T01-C03-01 Q03
const test = require('node:test');
const assert = require('node:assert');
const { debounce } = require('./Q03_debounce.js');


test("should not execute synchronously and only fire once after 60ms", async () => {
  let callCount = 0;
            const debounced = debounce(() => { callCount++; }, 60);
            debounced();
            debounced();
            debounced();
            assert.strictEqual(callCount, 0, "Should not fire immediately");
            await new Promise(r => setTimeout(r, 90));
            assert.strictEqual(callCount, 1, "Should fire exactly once after delay");
});

test("should reset the timer on each subsequent call within delay window", async () => {
  let value = 0;
            const debounced = debounce((v) => { value = v; }, 60);
            debounced(1);
            await new Promise(r => setTimeout(r, 30));
            debounced(2); // resets timer!
            await new Promise(r => setTimeout(r, 30));
            assert.strictEqual(value, 0, "Should still be 0 before second delay expires");
            await new Promise(r => setTimeout(r, 50));
            assert.strictEqual(value, 2, "Should record latest value 2");
});
