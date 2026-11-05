import test from "node:test";
import assert from "node:assert";
import { InventoryService, InsufficientStockError } from "../src/inventory_service.ts";
import type { Product } from "../src/types.ts";

test("Milestone 4: Async Concurrency & Inventory Lock", async (t) => {
  const initialProducts: Product[] = [
    { id: "item-a", sku: "SKU-1001", name: "Headphones", unitPriceInCents: 5000, stockQuantity: 10 },
    { id: "item-b", sku: "SKU-2002", name: "Mouse", unitPriceInCents: 2000, stockQuantity: 2 },
  ];

  await t.test("should reserve stock and deduct accurately", async () => {
    const service = new InventoryService(initialProducts);
    const success = await service.reserveOrderStock("ord-1", [{ productId: "item-a", quantity: 3 }]);
    assert.strictEqual(success, true);
    assert.strictEqual(service.getAvailableStock("item-a"), 7);
  });

  await t.test("should perform atomic rollback if secondary item is out of stock", async () => {
    const service = new InventoryService(initialProducts);
    
    // item-a has 10, item-b has 2. Request 5 of item-a and 5 of item-b (fails on item-b)
    await assert.rejects(
      async () => {
        await service.reserveOrderStock("ord-2", [
          { productId: "item-a", quantity: 5 },
          { productId: "item-b", quantity: 5 },
        ]);
      },
      InsufficientStockError
    );

    // item-a MUST NOT remain deducted! Atomic rollback check:
    assert.strictEqual(service.getAvailableStock("item-a"), 10, "item-a should have rolled back to 10");
    assert.strictEqual(service.getAvailableStock("item-b"), 2, "item-b should remain at 2");
  });

  await t.test("should handle concurrent checkout attempts without overselling", async () => {
    // Only 3 units available. 5 concurrent buyers requesting 1 unit each.
    const service = new InventoryService([
      { id: "hot-item", sku: "HOT-0001", name: "Limited Edition Drop", unitPriceInCents: 9900, stockQuantity: 3 },
    ]);

    const results = await Promise.allSettled([
      service.reserveOrderStock("user-1", [{ productId: "hot-item", quantity: 1 }]),
      service.reserveOrderStock("user-2", [{ productId: "hot-item", quantity: 1 }]),
      service.reserveOrderStock("user-3", [{ productId: "hot-item", quantity: 1 }]),
      service.reserveOrderStock("user-4", [{ productId: "hot-item", quantity: 1 }]),
      service.reserveOrderStock("user-5", [{ productId: "hot-item", quantity: 1 }]),
    ]);

    const fulfilled = results.filter((r) => r.status === "fulfilled");
    const rejected = results.filter((r) => r.status === "rejected");

    assert.strictEqual(fulfilled.length, 3, "Exactly 3 buyers should succeed");
    assert.strictEqual(rejected.length, 2, "Exactly 2 buyers should be rejected with InsufficientStockError");
    assert.strictEqual(service.getAvailableStock("hot-item"), 0, "Remaining stock must be strictly 0");
  });
});
