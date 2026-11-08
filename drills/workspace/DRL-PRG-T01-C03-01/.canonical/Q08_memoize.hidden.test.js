// Hidden Trap Test Suite for DRL-PRG-T01-C03-01 Q08
const test = require('node:test');
const assert = require('node:assert');
const { memoize } = require('../Q08_memoize.js');


test("[Q08-HIDDEN-T01] should use resolver function to compute composite cache keys", async () => {
  let runs = 0;
            const add = memoize((a, b) => { runs++; return a + b; }, (a, b) => `${a}:${b}`);
            assert.strictEqual(add(1, 2), 3);
            assert.strictEqual(add(1, 2), 3);
            assert.strictEqual(runs, 1);
            assert.strictEqual(add(2, 1), 3);
            assert.strictEqual(runs, 2, "Different key order should trigger computation");
});

test("[Q08-HIDDEN-T02] should expose underlying cache Map on returned function", async () => {
  const fn = memoize((x) => x);
            assert.ok(fn.cache instanceof Map);
});
