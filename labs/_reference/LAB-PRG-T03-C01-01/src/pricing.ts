import type { CartItem, Coupon, PriceBreakdown } from "./types.ts";

/**
 * Calculates cart pricing totals, applying coupons and taxes with exact cent precision.
 */
export function calculateCartTotals(
  items: CartItem[],
  coupon?: Coupon,
  taxRatePercent: number = 7.0
): PriceBreakdown {
  if (!Array.isArray(items) || items.length === 0) {
    return {
      subtotalInCents: 0,
      discountInCents: 0,
      taxableAmountInCents: 0,
      taxInCents: 0,
      grandTotalInCents: 0,
    };
  }

  // 1. Calculate raw subtotal in cents
  const subtotalInCents = items.reduce((acc, item) => {
    return acc + item.quantity * item.unitPriceInCents;
  }, 0);

  // 2. Apply coupon discount if conditions met
  let discountInCents = 0;
  if (coupon && subtotalInCents >= coupon.minSubtotalInCents) {
    if (coupon.discountType === "PERCENTAGE") {
      discountInCents = Math.round((subtotalInCents * coupon.value) / 100);
    } else if (coupon.discountType === "FIXED_AMOUNT") {
      discountInCents = coupon.value;
    }
  }

  // Discount cannot exceed subtotal
  discountInCents = Math.min(discountInCents, subtotalInCents);

  // 3. Taxable amount
  const taxableAmountInCents = subtotalInCents - discountInCents;

  // 4. Tax calculated with standard half-up rounding
  const taxInCents = Math.round((taxableAmountInCents * taxRatePercent) / 100);

  // 5. Grand total
  const grandTotalInCents = taxableAmountInCents + taxInCents;

  return {
    subtotalInCents,
    discountInCents,
    taxableAmountInCents,
    taxInCents,
    grandTotalInCents,
  };
}
