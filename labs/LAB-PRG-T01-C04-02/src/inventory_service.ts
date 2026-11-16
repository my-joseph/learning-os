import type { Product } from "./types.ts";

export class InsufficientStockError extends Error {
  constructor(productId: string, requested: number, available: number) {
    super(`Insufficient stock for product '${productId}': requested ${requested}, available ${available}`);
    this.name = "InsufficientStockError";
  }
}

export interface ReservationRequest {
  productId: string;
  quantity: number;
}

export class InventoryService {
  constructor(_initialProducts?: Product[]) {
    // TODO [Milestone 4]: Initialize inventory stock tracking from initialProducts.
  }

  public getAvailableStock(_productId: string): number {
    throw new Error("TODO [Milestone 4]: Return currently available stock for productId.");
  }

  /**
   * Concurrently-safe atomic reservation with automatic rollback on failure.
   */
  public async reserveOrderStock(_orderId: string, _items: ReservationRequest[]): Promise<boolean> {
    throw new Error("TODO [Milestone 4]: Atomically reserve order stock with concurrency safety and rollback.");
  }

  /**
   * Releases previously reserved stock (e.g. on order cancellation).
   */
  public async releaseReservation(_orderId: string): Promise<void> {
    throw new Error("TODO [Milestone 4]: Release previously reserved stock for orderId.");
  }
}
