import type { Product, CartItem } from "./types.ts";

const SKU_REGEX = /^[A-Z]{3}-[0-9]{4}$/;

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}

function asRecord(input: unknown, label: string): Record<string, unknown> {
  if (!input || typeof input !== "object") {
    throw new ValidationError(`${label} must be a non-null object`);
  }
  return input as Record<string, unknown>;
}

function requireNonEmptyString(value: unknown, message: string): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new ValidationError(message);
  }
  return value;
}

function requirePositiveInt(value: unknown, message: string): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value <= 0) {
    throw new ValidationError(message);
  }
  return value;
}

function requireNonNegativeInt(value: unknown, message: string): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) {
    throw new ValidationError(message);
  }
  return value;
}

/**
 * Validates a Product payload against domain invariants.
 */
export function validateProduct(input: unknown): Product {
  const record = asRecord(input, "Product");
  const id = requireNonEmptyString(record.id, "Product id must be a non-empty string");

  if (typeof record.sku !== "string" || !SKU_REGEX.test(record.sku)) {
    throw new ValidationError(`Invalid SKU format: ${String(record.sku)}. Expected format like 'PRD-1001'`);
  }

  const name = requireNonEmptyString(record.name, "Product name must be a non-empty string");
  const unitPriceInCents = requirePositiveInt(
    record.unitPriceInCents,
    "unitPriceInCents must be a positive integer greater than 0"
  );
  const stockQuantity = requireNonNegativeInt(
    record.stockQuantity,
    "stockQuantity must be a non-negative integer >= 0"
  );

  return {
    id,
    sku: record.sku,
    name,
    unitPriceInCents,
    stockQuantity,
  };
}

/**
 * Validates a CartItem and cross-references with product inventory.
 */
export function validateCartItem(input: unknown, products: Map<string, Product>): CartItem {
  const record = asRecord(input, "CartItem");
  const productId = requireNonEmptyString(record.productId, "CartItem productId must be a non-empty string");

  const product = products.get(productId);
  if (!product) {
    throw new ValidationError(`Referenced product not found: ${productId}`);
  }

  const quantity = requirePositiveInt(record.quantity, "CartItem quantity must be a positive integer >= 1");

  return {
    productId: product.id,
    quantity,
    unitPriceInCents: product.unitPriceInCents,
  };
}
