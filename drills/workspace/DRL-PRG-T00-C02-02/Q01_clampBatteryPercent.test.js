// Auto-generated visible test suite for DRL-PRG-T00-C02-02 Q01
const test = require('node:test');
const assert = require('node:assert');
const { clampBatteryPercent } = require('./Q01_clampBatteryPercent.js');


test("[Q01-T01] keeps in-range numbers", async () => {
  assert.strictEqual(clampBatteryPercent(55), 55);
assert.strictEqual(clampBatteryPercent(0), 0);
});

test("[Q01-T02] limits out-of-range numbers", async () => {
  assert.strictEqual(clampBatteryPercent(140), 100);
assert.strictEqual(clampBatteryPercent(-8), 0);
});
