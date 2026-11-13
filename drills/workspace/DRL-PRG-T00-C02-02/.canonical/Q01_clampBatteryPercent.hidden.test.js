// Hidden Trap Test Suite for DRL-PRG-T00-C02-02 Q01
const test = require('node:test');
const assert = require('node:assert');
const { clampBatteryPercent } = require('../Q01_clampBatteryPercent.js');


test("[Q01-HIDDEN-T01] rejects non-number input", async () => {
  assert.strictEqual(clampBatteryPercent('80'), null);
assert.strictEqual(clampBatteryPercent(NaN), null);
assert.strictEqual(clampBatteryPercent(Infinity), null);
assert.strictEqual(clampBatteryPercent(null), null);
assert.strictEqual(clampBatteryPercent(undefined), null);
assert.strictEqual(clampBatteryPercent(true), null);
});

test("[Q01-HIDDEN-T02] keeps boundary values", async () => {
  assert.strictEqual(clampBatteryPercent(100), 100);
assert.strictEqual(clampBatteryPercent(99.5), 99.5);
});
