// Auto-generated test suite for DRL-PRG-T01-C03-04 Q05
const test = require('node:test');
const assert = require('node:assert');
const { calculateOrderTotal } = require('./Q05_calculateOrderTotal.js');


test("[Q05-T01] should calculate subtotal, 10% coupon with cap, shipping, and tax", async () => {
  const order = {
              items: [
                { id: 'p1', name: 'Keyboard', price: 60, quantity: 1, taxable: true },
                { id: 'p2', name: 'Mousepad', price: 20, quantity: 2, taxable: false },
              ],
              couponCode: 'PERCENT10',
              isVip: false,
            };
            const result = calculateOrderTotal(order);
            assert.strictEqual(result.subtotal, 100);
            assert.strictEqual(result.discount, 10);
            assert.strictEqual(result.shipping, 8, 'Post-discount subtotal is 90 < 100, standard shipping $8');
            assert.strictEqual(result.tax, 3.78, '60 taxable - 6 discount = 54 taxable * 0.07 = 3.78');
            assert.strictEqual(result.total, 101.78);
            assert.strictEqual(result.currency, 'USD');
});

test("[Q05-T02] should grant free shipping for orders >= $100 post-discount or VIP", async () => {
  const vipOrder = {
              items: [{ id: 'p1', price: 30, quantity: 1, taxable: true }],
              couponCode: null,
              isVip: true,
            };
            const resVip = calculateOrderTotal(vipOrder);
            assert.strictEqual(resVip.shipping, 0, 'VIP member gets free shipping');

            const bigOrder = {
              items: [{ id: 'p2', price: 150, quantity: 1, taxable: true }],
              couponCode: 'PERCENT10',
              isVip: false,
            };
            const resBig = calculateOrderTotal(bigOrder);
            assert.strictEqual(resBig.discount, 15);
            assert.strictEqual(resBig.shipping, 0, 'Subtotal 135 >= 100 qualifies for free shipping');
});

test("[Q05-T03] should throw RangeError on empty items or invalid price/quantity", async () => {
  assert.throws(() => calculateOrderTotal({ items: [] }), /RangeError/);
            assert.throws(() => calculateOrderTotal({ items: [{ price: -5, quantity: 1 }] }), /RangeError/);
            assert.throws(() => calculateOrderTotal({ items: [{ price: 10, quantity: 0 }] }), /RangeError/);
});
