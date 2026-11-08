// Hidden Trap Test Suite for DRL-PRG-T01-C03-01 Q05
const test = require('node:test');
const assert = require('node:assert');
const { calculateOrderTotal } = require('../Q05_calculateOrderTotal.js');


test("[Q05-HIDDEN-T01] should cap PERCENT10 coupon discount at exactly $20.00", async () => {
  const hugeOrder = {
              items: [{ id: 'p1', price: 500, quantity: 1, taxable: true }],
              couponCode: 'PERCENT10',
              isVip: false,
            };
            const res = calculateOrderTotal(hugeOrder);
            assert.strictEqual(res.discount, 20, 'Max discount is capped at $20');
});

test("[Q05-HIDDEN-T02] should handle FIXED15 threshold rule ($50 minimum subtotal)", async () => {
  const smallOrder = {
              items: [{ id: 'p1', price: 40, quantity: 1, taxable: true }],
              couponCode: 'FIXED15',
              isVip: false,
            };
            assert.strictEqual(calculateOrderTotal(smallOrder).discount, 0, 'Subtotal 40 < 50, discount is 0');
});
