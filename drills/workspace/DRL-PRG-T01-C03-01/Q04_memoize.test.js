// Auto-generated visible test suite for DRL-PRG-T01-C03-01 Q04
const test = require('node:test');
const assert = require('node:assert');
const { memoize } = require('./Q04_memoize.js');


test("[Q04-T01] should cache expensive computation and only execute original function once per key", async () => {
  let runs = 0;
            const fib = memoize((n) => {
              runs++;
              return n <= 1 ? n : n * 2;
            });
            assert.strictEqual(fib(5), 10);
            assert.strictEqual(fib(5), 10);
            assert.strictEqual(runs, 1, "Cached call should not re-run original function");
});

test("[Q04-T02] should correctly cache falsy return values (0, false, null, '') without re-evaluating", async () => {
  let calls = 0;
            const zeroFn = memoize((x) => {
              calls++;
              return 0;
            });
            assert.strictEqual(zeroFn('a'), 0);
            assert.strictEqual(zeroFn('a'), 0);
            assert.strictEqual(calls, 1, "0 is falsy but must be treated as a valid cache hit");
});
