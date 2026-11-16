import { TinyEventEmitter } from "../src/index.ts";

type Events = { sent: { messageId: string }; failed: { retryable: boolean } };
const emitter = new TinyEventEmitter<Events>();
emitter.emit("sent", { messageId: "msg-1" });
emitter.on("failed", ({ retryable }) => retryable);
// @ts-expect-error unknown event names are outside the event map
emitter.emit("missing", {});
// @ts-expect-error payload fields must match the selected event
emitter.emit("sent", { retryable: true });
