// Auto-generated visible test suite for DRL-PRG-T00-C02-02 Q07
const test = require('node:test');
const assert = require('node:assert');
const { summarizeTemperatures } = require('./Q07_summarizeTemperatures.js');


test("[Q07-T01] computes all statistics", async () => {
  assert.deepStrictEqual(summarizeTemperatures([20, 25, 30]), { min: 20, max: 30, average: 25 });
});

test("[Q07-T02] handles negatives", async () => {
  assert.deepStrictEqual(summarizeTemperatures([-5, 0, 5, -10]), { min: -10, max: 5, average: -2.5 });
});
