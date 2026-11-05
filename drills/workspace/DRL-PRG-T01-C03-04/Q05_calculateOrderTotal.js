/**
 * Calculates final pricing for an e-commerce order.
 * 
 * Invariants:
 * - order.items must be a non-empty array of items with price >= 0 and integer quantity > 0.
 * - Throw RangeError for invalid item price, quantity, or empty items array.
 * - Coupons:
 *     'PERCENT10': 10% off subtotal up to $20 max discount.
 *     'FIXED15': $15 off if subtotal >= $50, else $0.
 *     'FREESHIP': Free shipping.
 * - Shipping: $8 standard; free if post-discount subtotal >= $100, isVip is true, or coupon is 'FREESHIP'.
 * - Tax: 7% on taxable items (where item.taxable !== false) applied to discounted taxable subtotal.
 * - Return: { subtotal, discount, shipping, tax, total, currency: 'USD' } with 2 decimal precision.
 */
function calculateOrderTotal(order) {
  // TODO: Implement defensive validation and pricing pipeline
}

module.exports = { calculateOrderTotal };
