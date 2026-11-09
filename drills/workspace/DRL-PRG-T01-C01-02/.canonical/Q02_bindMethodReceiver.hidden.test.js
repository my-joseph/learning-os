// Hidden Trap Test Suite for DRL-PRG-T01-C01-02 Q02
const test = require('node:test');
const assert = require('node:assert');
const { bindMethodReceiver } = require('../Q02_bindMethodReceiver.js');


test("[Q02-HIDDEN-T01] should safely ignore non-function property names in methodNames array", async () => {
  const obj = { count: 10 };
bindMethodReceiver(obj, ['count', 'missingMethod']);
assert.strictEqual(obj.count, 10);
});
