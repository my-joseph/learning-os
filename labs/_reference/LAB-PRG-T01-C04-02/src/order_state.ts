import type { OrderStatus, OrderEvent } from "./types.ts";

export class InvalidStateTransitionError extends Error {
  constructor(from: OrderStatus, event: OrderEvent) {
    super(`Cannot transition order from status '${from}' via event '${event}'`);
    this.name = "InvalidStateTransitionError";
  }
}

const TRANSITIONS: Record<OrderStatus, Partial<Record<OrderEvent, OrderStatus>>> = {
  DRAFT: {
    SUBMIT: "PENDING_PAYMENT",
    CANCEL: "CANCELLED",
  },
  PENDING_PAYMENT: {
    CONFIRM_PAYMENT: "PAID",
    CANCEL: "CANCELLED",
  },
  PAID: {
    START_PROCESSING: "PROCESSING",
    CANCEL: "CANCELLED",
  },
  PROCESSING: {
    DISPATCH: "SHIPPED",
    CANCEL: "CANCELLED",
  },
  SHIPPED: {
    DELIVER: "DELIVERED",
  },
  DELIVERED: {},
  CANCELLED: {},
};

/**
 * Transitions order from its current status according to strict e-commerce state rules.
 */
export function transitionOrderStatus(current: OrderStatus, event: OrderEvent): OrderStatus {
  const allowed = TRANSITIONS[current];
  const next = allowed ? allowed[event] : undefined;

  if (!next) {
    throw new InvalidStateTransitionError(current, event);
  }

  return next;
}
