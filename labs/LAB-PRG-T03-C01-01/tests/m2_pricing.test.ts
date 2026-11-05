import test from "node:test";
import assert from "node:assert";
import { calculateCartTotals } from "../src/pricing.ts";
import type { CartItem, Coupon } from "../src/types.ts";

test("Milestone 2: Pricing & Tiered Discount Engine", async (t) => {
  await t.test("should return zero totals for empty cart", () => {
    const totals = calculateCartTotals([]);
    assert.strictEqual(totals.subtotalInCents, 0);
    assert.strictEqual(totals.grandTotalInCents, 0);
  });

  await t.test("should compute base subtotal with exact cent precision", () => {
    const items: CartItem[] = [
      { productId: "p1", quantity: 2, unitPriceInCents: 2500 }, // 5000
      { productId: "p2", quantity: 1, unitPriceInCents: 1550 }, // 1550
    ];
    const totals = calculateCartTotals(items, undefined, 0);
    assert.strictEqual(totals.subtotalInCents, 6550);
    assert.strictEqual(totals.discountInCents, 0);
    assert.strictEqual(totals.grandTotalInCents, 6550);
  });

  await t.test("should apply percentage coupon when threshold met", () => {
    const items: CartItem[] = [{ productId: "p1", quantity: 1, unitPriceInCents: 10000 }];
    const coupon: Coupon = {
      code: "SAVE20",
      discountType: "PERCENTAGE",
      value: 20, // 20%
      minSubtotalInCents: 5000,
    };
    const totals = calculateCartTotals(items, coupon, 7.0);
    // Subtotal: 10000
    // Discount: 20% of 10000 = 2000
    // Taxable: 8000
    // Tax: 7% of 8000 = 560
    // Grand Total: 8560
    assert.strictEqual(totals.subtotalInCents, 10000);
    assert.strictEqual(totals.discountInCents, 2000);
    assert.strictEqual(totals.taxableAmountInCents, 8000);
    assert.strictEqual(totals.taxInCents, 560);
    assert.strictEqual(totals.grandTotalInCents, 8560);
  });

  await t.test("should ignore coupon if subtotal is below minSubtotalInCents", () => {
    const items: CartItem[] = [{ productId: "p1", quantity: 1, unitPriceInCents: 3000 }];
    const coupon: Coupon = {
      code: "VIP50",
      discountType: "FIXED_AMOUNT",
      value: 1500,
      minSubtotalInCents: 5000,
    };
    const totals = calculateCartTotals(items, coupon, 0);
    assert.strictEqual(totals.subtotalInCents, 3000);
    assert.strictEqual(totals.discountInCents, 0);
    assert.strictEqual(totals.grandTotalInCents, 3000);
  });

  await t.test("should cap discount to not exceed subtotal", () => {
    const items: CartItem[] = [{ productId: "p1", quantity: 1, unitPriceInCents: 1000 }];
    const coupon: Coupon = {
      code: "SUPER500",
      discountType: "FIXED_AMOUNT",
      value: 5000, // $50 off on $10 item
      minSubtotalInCents: 500,
    };
    const totals = calculateCartTotals(items, coupon, 0);
    assert.strictEqual(totals.subtotalInCents, 1000);
    assert.strictEqual(totals.discountInCents, 1000); // Capped at subtotal
    assert.strictEqual(totals.grandTotalInCents, 0);
  });
});
