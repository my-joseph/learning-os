import type { CartItem, Coupon, PriceBreakdown } from "./types.ts";

/**
 * Calculates cart pricing totals, applying coupons and taxes with exact cent precision.
 */
export function calculateCartTotals(
  _items: CartItem[],
  _coupon?: Coupon,
  _taxRatePercent: number = 7.0
): PriceBreakdown {
  throw new Error("TODO [Milestone 2]: Calculate subtotal, discount, taxable amount, tax, and grand total in cents.");
}
