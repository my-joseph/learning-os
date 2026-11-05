import type { Product, CartItem } from "./types.ts";

const SKU_REGEX = /^[A-Z]{3}-[0-9]{4}$/;

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}

/**
 * Validates a Product payload against domain invariants.
 */
export function validateProduct(input: any): Product {
  if (!input || typeof input !== "object") {
    throw new ValidationError("Product must be a non-null object");
  }
  if (typeof input.id !== "string" || !input.id.trim()) {
    throw new ValidationError("Product id must be a non-empty string");
  }
  if (typeof input.sku !== "string" || !SKU_REGEX.test(input.sku)) {
    throw new ValidationError(
      `Invalid SKU format: ${input.sku}. Expected format like 'PRD-1001'`,
    );
  }
  if (typeof input.name !== "string" || !input.name.trim()) {
    throw new ValidationError("Product name must be a non-empty string");
  }
  if (
    typeof input.unitPriceInCents !== "number" ||
    !Number.isInteger(input.unitPriceInCents) ||
    input.unitPriceInCents <= 0
  ) {
    throw new ValidationError(
      "unitPriceInCents must be a positive integer greater than 0",
    );
  }
  if (
    typeof input.stockQuantity !== "number" ||
    !Number.isInteger(input.stockQuantity) ||
    input.stockQuantity < 0
  ) {
    throw new ValidationError(
      "stockQuantity must be a non-negative integer >= 0",
    );
  }

  return {
    id: input.id,
    sku: input.sku,
    name: input.name,
    unitPriceInCents: input.unitPriceInCents,
    stockQuantity: input.stockQuantity,
  };
}

/**
 * Validates a CartItem and cross-references with product inventory.
 */
