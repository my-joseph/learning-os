import type { OrderStatus, OrderEvent } from "./types.ts";

export class InvalidStateTransitionError extends Error {
  constructor(from: OrderStatus, event: OrderEvent) {
    super(`Cannot transition order from status '${from}' via event '${event}'`);
    this.name = "InvalidStateTransitionError";
  }
}

/**
 * Transitions order from its current status according to strict e-commerce state rules.
 */
export function transitionOrderStatus(_current: OrderStatus, _event: OrderEvent): OrderStatus {
  throw new Error("TODO [Milestone 3]: Transition order status or throw InvalidStateTransitionError.");
}
