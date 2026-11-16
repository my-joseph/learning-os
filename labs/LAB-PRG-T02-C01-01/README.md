# MiniStore and useStore

## Scenario
A React workspace needs a small external store shared by independent panels. The store must expose reliable updates, and components must stay in sync with only the selected values they render.

## Milestones

### M1 — Store state and listener contracts
Create the store API so callers can read a snapshot, subscribe to changes, and release subscriptions. Separate store instances must operate independently.

Acceptance criteria: initial state is observable, listeners receive updates, and unsubscribe stops future notifications.

### M2 — Immutable updates and selectors
Support partial or updater-based state changes while preserving caller-owned inputs. Subscribers must receive coherent snapshots.

Acceptance criteria: state changes are visible, unchanged fields are retained, and updates do not mutate their input values.

### M3 — React subscription hook
Connect a component to the store with a typed selector. React must receive a stable snapshot and stop the subscription when the component unmounts.

Acceptance criteria: a rendered value follows store updates and cleanup is safe.

### M4 — Render boundary verification
Use components that read different selections from one store and verify that observable output stays correct without unrelated renders.

Acceptance criteria: a change to one selected value does not cause a component that selects another unchanged value to render again.

## Run the checks

- `npm test` runs the visible acceptance suite.
- `npm run check` runs tests, lint, and TypeScript checks.
- `npm run test:reference` runs visible tests against the reference workspace.
- `npm run check:reference` checks the reference implementation.
- `npm run check:hidden` runs the hidden boundary cases against the reference workspace.
- Ask for a review with `npm run review -- M1` or `python -m code_engine.review_run LAB-PRG-T02-C01-01 M1`.
