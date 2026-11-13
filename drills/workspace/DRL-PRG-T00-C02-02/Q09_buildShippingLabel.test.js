// Auto-generated visible test suite for DRL-PRG-T00-C02-02 Q09
const test = require('node:test');
const assert = require('node:assert');
const { buildShippingLabel } = require('./Q09_buildShippingLabel.js');


test("[Q09-T01] formats plural items", async () => {
  const order = { customer: { name: 'Mali Chai', address: { city: 'Chiang Mai', postalCode: '50200' } }, items: ['lamp', 'desk'] };
assert.strictEqual(buildShippingLabel(order), 'Mali Chai - Chiang Mai 50200 (2 items)');
});

test("[Q09-T02] formats singular item", async () => {
  const order = { customer: { name: 'Ken Ito', address: { city: 'Osaka', postalCode: '530-0001' } }, items: ['book'] };
assert.strictEqual(buildShippingLabel(order), 'Ken Ito - Osaka 530-0001 (1 item)');
});
