import test from "node:test";
import assert from "node:assert";
import { validateProduct, validateCartItem, ValidationError } from "../src/schemas.ts";
import type { Product } from "../src/types.ts";

test("Milestone 1: Domain Models & Schema Validation", async (t) => {
  await t.test("should validate compliant product definition", () => {
    const raw = {
      id: "prod-1",
      sku: "ELC-9042",
      name: "Mechanical Keyboard",
      unitPriceInCents: 12900,
      stockQuantity: 15,
    };
    const product = validateProduct(raw);
    assert.strictEqual(product.id, "prod-1");
    assert.strictEqual(product.sku, "ELC-9042");
    assert.strictEqual(product.unitPriceInCents, 12900);
  });

  await t.test("should reject malformed SKU formats", () => {
    const invalidSkus = ["elc-9042", "ELC-904", "ELCX-9042", "123-4567", "ELC9042"];
    for (const sku of invalidSkus) {
      assert.throws(
        () => validateProduct({ id: "p", sku, name: "Item", unitPriceInCents: 100, stockQuantity: 5 }),
        ValidationError,
        `Expected rejection for SKU: ${sku}`
      );
    }
  });

  await t.test("should reject non-positive or float unitPriceInCents", () => {
    const invalidPrices = [0, -100, 19.99, NaN, Infinity];
    for (const price of invalidPrices) {
      assert.throws(
        () => validateProduct({ id: "p", sku: "PRD-1000", name: "Item", unitPriceInCents: price, stockQuantity: 5 }),
        ValidationError
      );
    }
  });

  await t.test("should validate CartItem against existing product catalog", () => {
    const catalog = new Map<string, Product>([
      ["prod-1", { id: "prod-1", sku: "PRD-1001", name: "Mug", unitPriceInCents: 1500, stockQuantity: 20 }],
    ]);

    const item = validateCartItem({ productId: "prod-1", quantity: 3 }, catalog);
    assert.strictEqual(item.productId, "prod-1");
    assert.strictEqual(item.quantity, 3);
    assert.strictEqual(item.unitPriceInCents, 1500);
  });

  await t.test("should reject CartItem with unreferenced product ID or invalid quantity", () => {
    const catalog = new Map<string, Product>();
    assert.throws(
      () => validateCartItem({ productId: "ghost-id", quantity: 1 }, catalog),
      ValidationError
    );
    assert.throws(
      () => validateCartItem({ productId: "ghost-id", quantity: 0 }, catalog),
      ValidationError
    );
  });
});
