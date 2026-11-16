import type { Product, CartItem } from "./types.ts";

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}

/**
 * Validates a Product payload against domain invariants.
 */
export function validateProduct(_input: any): Product {
  throw new Error("TODO [Milestone 1]: Validate product fields and invariants, returning a Product.");
}

/**
 * Validates a CartItem and cross-references with product inventory.
 */
export function validateCartItem(_input: any, _products: Map<string, Product>): CartItem {
  throw new Error("TODO [Milestone 1]: Validate cart item against the product catalog and return a CartItem.");
}
