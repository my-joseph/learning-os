// Hidden Trap Test Suite for DRL-PRG-T00-C02-01 Q02
const test = require('node:test');
const assert = require('node:assert');
const { pipe } = require('../Q02_pipe.js');


test("[Q02-HIDDEN-T01] empty pipe returns identity function", async () => {
  const id = pipe(); assert.strictEqual(id(42), 42); assert.strictEqual(id('abc'), 'abc');
});

test("[Q02-HIDDEN-T02] single function pipeline", async () => {
  const double = pipe(x => x * 2); assert.strictEqual(double(7), 14);
});

test("[Q02-HIDDEN-T03] string manipulation pipeline", async () => {
  const slugify = pipe(s => s.trim(), s => s.toLowerCase(), s => s.replace(/\s+/g, '-')); assert.strictEqual(slugify('  Hello World JS  '), 'hello-world-js');
});
