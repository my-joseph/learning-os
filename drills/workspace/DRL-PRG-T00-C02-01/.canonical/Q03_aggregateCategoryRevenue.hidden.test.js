// Hidden Trap Test Suite for DRL-PRG-T00-C02-01 Q03
const test = require('node:test');
const assert = require('node:assert');
const { aggregateCategoryRevenue } = require('../Q03_aggregateCategoryRevenue.js');


test("[Q03-HIDDEN-T01] should handle empty transactions array gracefully", async () => {
  const res = aggregateCategoryRevenue([]);
assert.deepStrictEqual(res, {});
});
