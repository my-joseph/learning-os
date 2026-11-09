// Auto-generated visible test suite for DRL-PRG-T00-C02-01 Q02
const test = require('node:test');
const assert = require('node:assert');
const { pipe } = require('./Q02_pipe.js');


test("[Q02-T01] unary functions pipeline", async () => {
  const fn = pipe(x => x + 1, x => x * 2); assert.strictEqual(fn(5), 12);
});

test("[Q02-T02] multi-argument first function", async () => {
  const addThenSquare = pipe((a, b) => a + b, x => x * x); assert.strictEqual(addThenSquare(3, 4), 49);
});
