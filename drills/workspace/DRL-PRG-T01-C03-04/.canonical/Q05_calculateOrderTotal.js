function calculateOrderTotal(order) {
  if (!order || !Array.isArray(order.items) || order.items.length === 0) {
    throw new RangeError('Order must contain at least one item');
  }

  let subtotal = 0;
  let taxableSubtotal = 0;

  for (const item of order.items) {
    if (
      typeof item.price !== 'number' ||
      item.price < 0 ||
      typeof item.quantity !== 'number' ||
      item.quantity <= 0 ||
      !Number.isInteger(item.quantity)
    ) {
      throw new RangeError('Invalid item price or quantity');
    }
    const itemTotal = item.price * item.quantity;
    subtotal += itemTotal;
    if (item.taxable !== false) {
      taxableSubtotal += itemTotal;
    }
  }

  // Round subtotal to 2 decimals
  subtotal = Math.round(subtotal * 100) / 100;

  // 1. Calculate Discount
  let discount = 0;
  if (order.couponCode === 'PERCENT10') {
    discount = Math.min(20, Math.round(subtotal * 0.10 * 100) / 100);
  } else if (order.couponCode === 'FIXED15') {
    discount = subtotal >= 50 ? 15 : 0;
  }

  const discountedSubtotal = Math.max(0, Math.round((subtotal - discount) * 100) / 100);

  // 2. Shipping Calculation
  const isFreeShip = Boolean(
    order.isVip ||
    order.couponCode === 'FREESHIP' ||
    discountedSubtotal >= 100
  );
  const shipping = isFreeShip ? 0 : 8;

  // 3. Tax Calculation (7% on discounted taxable subtotal)
  const taxRatio = subtotal > 0 ? taxableSubtotal / subtotal : 0;
  const taxableDiscounted = Math.max(0, taxableSubtotal - (discount * taxRatio));
  const tax = Math.round(taxableDiscounted * 0.07 * 100) / 100;

  const total = Math.round((discountedSubtotal + shipping + tax) * 100) / 100;

  return { subtotal, discount, shipping, tax, total, currency: 'USD' };
}

module.exports = { calculateOrderTotal };
