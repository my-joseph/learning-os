// Hidden Trap Test Suite for DRL-PRG-T00-C02-02 Q09
const test = require('node:test');
const assert = require('node:assert');
const { buildShippingLabel } = require('../Q09_buildShippingLabel.js');


test("[Q09-HIDDEN-T01] handles zero items", async () => {
  const order = { customer: { name: 'Lea Roy', address: { city: 'Lyon', postalCode: '69001' } }, items: [] };
assert.strictEqual(buildShippingLabel(order), 'Lea Roy - Lyon 69001 (0 items)');
});

test("[Q09-HIDDEN-T02] handles many items", async () => {
  const order = { customer: { name: 'Omar Said', address: { city: 'Cairo', postalCode: '11511' } }, items: [1, 2, 3, 4, 5] };
assert.strictEqual(buildShippingLabel(order), 'Omar Said - Cairo 11511 (5 items)');
});
