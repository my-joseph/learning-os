import type { Product } from "./types.ts";

export class InsufficientStockError extends Error {
  constructor(productId: string, requested: number, available: number) {
    super(
      `Insufficient stock for product '${productId}': requested ${requested}, available ${available}`,
    );
    this.name = "InsufficientStockError";
  }
}

export interface ReservationRequest {
  productId: string;
  quantity: number;
}

export class InventoryService {
  private stock: Map<string, number> = new Map();
  private reservations: Map<string, ReservationRequest[]> = new Map();
  private lock: Promise<void> = Promise.resolve();

  constructor(initialProducts?: Product[]) {
    if (initialProducts) {
      for (const p of initialProducts) {
        this.stock.set(p.id, p.stockQuantity);
      }
    }
  }

  public getAvailableStock(productId: string): number {
    return this.stock.get(productId) ?? 0;
  }

  /**
   * Concurrently-safe atomic reservation with automatic rollback on failure.
   */
  public async reserveOrderStock(
    orderId: string,
    items: ReservationRequest[],
  ): Promise<boolean> {
    // Acquire mutex lock to prevent concurrent race condition on stock depletion
    const release = await this.acquireLock();

    try {
      // 1. First pass: verify ALL items have sufficient stock
      for (const item of items) {
        const current = this.stock.get(item.productId) ?? 0;
        if (current < item.quantity) {
          throw new InsufficientStockError(
            item.productId,
            item.quantity,
            current,
          );
        }
      }

      // 2. Second pass: deduct stock atomically
      for (const item of items) {
        const current = this.stock.get(item.productId)!;
        this.stock.set(item.productId, current - item.quantity);
      }

      // 3. Record reservation
      this.reservations.set(orderId, [...items]);
      return true;
    } finally {
      release();
    }
  }

  /**
   * Releases previously reserved stock (e.g. on order cancellation).
   */
  public async releaseReservation(orderId: string): Promise<void> {
    const release = await this.acquireLock();
    try {
      const items = this.reservations.get(orderId);
      if (!items) return;

      for (const item of items) {
        const current = this.stock.get(item.productId) ?? 0;
        this.stock.set(item.productId, current + item.quantity);
      }
      this.reservations.delete(orderId);
    } finally {
      release();
    }
  }

  private acquireLock(): Promise<() => void> {
    let unlock: () => void;
    const currentLock = this.lock;
    this.lock = new Promise<void>((resolve) => {
      unlock = resolve;
    });
    return currentLock.then(() => unlock);
  }
}
