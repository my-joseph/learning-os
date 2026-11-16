/**
 * Domain Types for E-Commerce Checkout Engine
 */

export type DiscountType = "PERCENTAGE" | "FIXED_AMOUNT";

export interface Product {
  id: string;
  sku: string; // Must match /^[A-Z]{3}-[0-9]{4}$/
  name: string;
  unitPriceInCents: number; // Positive integer
  stockQuantity: number; // Non-negative integer
}

export interface CartItem {
  productId: string;
  quantity: number; // Positive integer >= 1
  unitPriceInCents: number;
}

export interface Coupon {
  code: string;
  discountType: DiscountType;
  value: number; // Percentage (e.g. 15 for 15%) or Cents (e.g. 500 for $5.00)
  minSubtotalInCents: number;
}

export interface PriceBreakdown {
  subtotalInCents: number;
  discountInCents: number;
  taxableAmountInCents: number;
  taxInCents: number;
  grandTotalInCents: number;
}

export type OrderStatus =
  | "DRAFT"
  | "PENDING_PAYMENT"
  | "PAID"
  | "PROCESSING"
  | "SHIPPED"
  | "DELIVERED"
  | "CANCELLED";

export type OrderEvent =
  | "SUBMIT"
  | "CONFIRM_PAYMENT"
  | "START_PROCESSING"
  | "DISPATCH"
  | "DELIVER"
  | "CANCEL";
