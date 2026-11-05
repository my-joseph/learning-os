import test from "node:test";
import assert from "node:assert";
import { transitionOrderStatus, InvalidStateTransitionError } from "../src/order_state.ts";
import type { OrderStatus } from "../src/types.ts";

test("Milestone 3: Order State Machine & Transition Guards", async (t) => {
  await t.test("should follow valid end-to-end order fulfillment pipeline", () => {
    let status: OrderStatus = "DRAFT";
    status = transitionOrderStatus(status, "SUBMIT");
    assert.strictEqual(status, "PENDING_PAYMENT");

    status = transitionOrderStatus(status, "CONFIRM_PAYMENT");
    assert.strictEqual(status, "PAID");

    status = transitionOrderStatus(status, "START_PROCESSING");
    assert.strictEqual(status, "PROCESSING");

    status = transitionOrderStatus(status, "DISPATCH");
    assert.strictEqual(status, "SHIPPED");

    status = transitionOrderStatus(status, "DELIVER");
    assert.strictEqual(status, "DELIVERED");
  });

  await t.test("should permit cancellation prior to shipment", () => {
    assert.strictEqual(transitionOrderStatus("DRAFT", "CANCEL"), "CANCELLED");
    assert.strictEqual(transitionOrderStatus("PENDING_PAYMENT", "CANCEL"), "CANCELLED");
    assert.strictEqual(transitionOrderStatus("PAID", "CANCEL"), "CANCELLED");
    assert.strictEqual(transitionOrderStatus("PROCESSING", "CANCEL"), "CANCELLED");
  });

  await t.test("should strictly prohibit cancelling already delivered orders", () => {
    assert.throws(
      () => transitionOrderStatus("DELIVERED", "CANCEL"),
      InvalidStateTransitionError
    );
  });

  await t.test("should prohibit invalid skip transitions", () => {
    // Cannot skip payment and directly dispatch
    assert.throws(
      () => transitionOrderStatus("DRAFT", "DISPATCH"),
      InvalidStateTransitionError
    );
    assert.throws(
      () => transitionOrderStatus("PENDING_PAYMENT", "DELIVER"),
      InvalidStateTransitionError
    );
  });
});
