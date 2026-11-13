// Hidden Trap Test Suite for DRL-PRG-T00-C02-02 Q07
const test = require('node:test');
const assert = require('node:assert');
const { summarizeTemperatures } = require('../Q07_summarizeTemperatures.js');


test("[Q07-HIDDEN-T01] rounds average to one decimal", async () => {
  assert.deepStrictEqual(summarizeTemperatures([20, 21, 21]), { min: 20, max: 21, average: 20.7 });
});

test("[Q07-HIDDEN-T02] single reading", async () => {
  assert.deepStrictEqual(summarizeTemperatures([18.4]), { min: 18.4, max: 18.4, average: 18.4 });
});

test("[Q07-HIDDEN-T03] does not mutate input", async () => {
  const readings = [30, 10, 20];
summarizeTemperatures(readings);
assert.deepStrictEqual(readings, [30, 10, 20]);
});
