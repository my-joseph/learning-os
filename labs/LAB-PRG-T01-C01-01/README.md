# LAB-PRG-T01-C01-01 — TinyEventEmitter & PromisePool

## Scenario

Build a typed event bus and a bounded asynchronous task coordinator for a backend notification service. The event bus routes domain notifications to subscribers; the pool processes independent delivery jobs while respecting capacity and cancellation.

## Milestones

### M1 — Event Map & Listener Contracts

Define event payload and listener types that preserve the relationship between each event name and its payload. The basic `on`/`emit` contract also delivers the original payload to the matching listener. The public API must reject unknown event names at compile time and support event names supplied as a literal union. M2 adds removal and delivery-iteration behavior.

Run this milestone's visible checks with `npm run test:m1` and all checks with `npm run check:m1`.

### M2 — `on`, `off` & `emit`

Implement subscription, removal, and synchronous delivery. Removing a subscription prevents future deliveries; removing it more than once is safe. Delivery follows registration order, and a listener added during an emission begins receiving events on the next emission.

Run this milestone's visible checks with `npm run test:m2` and all checks with `npm run check:m2`.

### M3 — Bounded `PromisePool`

Process task functions with a caller-supplied concurrency limit. Preserve result order by input position, continue after an individual task rejects, and report each task's outcome without exceeding the limit.

Run this milestone's visible checks with `npm run test:m3` and all checks with `npm run check:m3`.

### M4 — Cancellation & Resource Lifecycle

Allow a pool run to observe an optional `AbortSignal`. Stop starting queued work after cancellation, settle already-started work according to its own result, and release any abort listener when the run settles.

Run this milestone's visible checks with `npm run test:m4` and all checks with `npm run check:m4`.

## Commands

- `npm test` runs all visible milestone tests.
- `npm run check` runs tests, lint, and typecheck.
- `npm run test:m1` / `npm run check:m1` run one milestone; use `m2`, `m3`, or `m4` for the others.
- `npm run review -- m1` prints the review request for the milestone.
- Ask Claude Code: `ตรวจโค้ด LAB-PRG-T01-C01-01 M1` (replace `M1` with the milestone being reviewed).
