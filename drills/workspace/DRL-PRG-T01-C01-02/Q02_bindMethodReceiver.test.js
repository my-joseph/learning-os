// Auto-generated visible test suite for DRL-PRG-T01-C01-02 Q02
const test = require('node:test');
const assert = require('node:assert');
const { bindMethodReceiver } = require('./Q02_bindMethodReceiver.js');


test("[Q02-T01] should preserve this context when method is detached and invoked as bare function", async () => {
  class UserNotifier {
  constructor(serviceName) { this.serviceName = serviceName; }
  notify(user) { return `[${this.serviceName}] Alert sent to ${user}`; }
}
const notifier = new UserNotifier('AuthService');
bindMethodReceiver(notifier, ['notify']);
const detached = notifier.notify;
assert.strictEqual(detached('Alice'), '[AuthService] Alert sent to Alice');
});

test("[Q02-T02] should return the targetInstance for fluent method chaining", async () => {
  const obj = { value: 42, getValue() { return this.value; } };
const res = bindMethodReceiver(obj, ['getValue']);
assert.strictEqual(res, obj);
const getVal = res.getValue;
assert.strictEqual(getVal(), 42);
});
