// Auto-generated visible test suite for DRL-PRG-T01-C01-02 Q04
const test = require('node:test');
const assert = require('node:assert');
const { deepCloneCircular } = require('./Q04_deepCloneCircular.js');


test("[Q04-T01] should deeply clone nested objects and arrays with total mutation isolation", async () => {
  const original = { user: { name: 'Alice', roles: ['admin', 'dev'] } };
const copy = deepCloneCircular(original);
assert.deepStrictEqual(copy, original);
assert.notStrictEqual(copy, original);
assert.notStrictEqual(copy.user, original.user);
assert.notStrictEqual(copy.user.roles, original.user.roles);
copy.user.roles.push('security');
assert.strictEqual(original.user.roles.length, 2, 'Original array was mutated!');
});

test("[Q04-T02] should preserve circular references without infinite recursion or stack overflow", async () => {
  const circularObj = { id: 'root' };
circularObj.self = circularObj;
circularObj.child = { parent: circularObj };
const cloned = deepCloneCircular(circularObj);
assert.notStrictEqual(cloned, circularObj);
assert.strictEqual(cloned.self, cloned, 'Circular self-reference was not preserved!');
assert.strictEqual(cloned.child.parent, cloned, 'Child parent reference was not preserved!');
});
