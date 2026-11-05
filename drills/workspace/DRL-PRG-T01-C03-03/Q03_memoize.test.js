// Auto-generated test file for DRL-PRG-T01-C03-03 Q03
const test = require('node:test');
const assert = require('node:assert');
const { memoize } = require('./Q03_memoize.js');


test("should calculate result once and return cached value on subsequent calls with same argument", async () => {
  let runs = 0;
            const square = memoize((n) => { runs++; return n * n; });
            assert.strictEqual(square(5), 25);
            assert.strictEqual(square(5), 25);
            assert.strictEqual(runs, 1, "Underlying function must only run once for input 5");
            assert.strictEqual(square(4), 16);
            assert.strictEqual(runs, 2, "Underlying function must run for input 4");
});

test("should correctly cache falsy return values (e.g. 0, false, null, '')", async () => {
  let runs = 0;
            const getFalsy = memoize((type) => {
              runs++;
              if (type === 'zero') return 0;
              if (type === 'bool') return false;
              if (type === 'empty') return '';
              return null;
            });
            assert.strictEqual(getFalsy('zero'), 0);
            assert.strictEqual(getFalsy('zero'), 0);
            assert.strictEqual(runs, 1, "Should not recompute when return value is 0");
});
