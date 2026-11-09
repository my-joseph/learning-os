// Auto-generated visible test suite for DRL-PRG-T01-C03-01 Q02
const test = require('node:test');
const assert = require('node:assert');
const { debounce } = require('./Q02_debounce.js');


test("[Q02-T01] should not execute synchronously and only fire once after 80ms", async () => {
  let callCount = 0;
            const debounced = debounce(() => { callCount++; }, 80);
            debounced();
            debounced();
            debounced();
            assert.strictEqual(callCount, 0, "Should not fire immediately");
            await new Promise(r => setTimeout(r, 110));
            assert.strictEqual(callCount, 1, "Should fire exactly once after delay");
});

test("[Q02-T02] should reset the timer on each subsequent call within delay window", async () => {
  let value = 0;
            const debounced = debounce((v) => { value = v; }, 80);
            debounced(1);
            await new Promise(r => setTimeout(r, 40));
            debounced(2);
            await new Promise(r => setTimeout(r, 40));
            assert.strictEqual(value, 0, "Should still be 0 before second delay expires");
            await new Promise(r => setTimeout(r, 65));
            assert.strictEqual(value, 2, "Should record latest value 2");
});
