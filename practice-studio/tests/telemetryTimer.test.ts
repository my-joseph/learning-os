/**
 * Unit tests for Telemetry Timer (5 cases)
 * Run: npx tsx practice-studio/tests/telemetryTimer.test.ts
 */

import {
  createTelemetryTimerState,
  setActiveProblem,
  setVisibility,
  consumeAttempt,
  MAX_ATTEMPT_DURATION_MS,
} from "../src/lib/telemetryTimer";

function assert(condition: boolean, msg: string) {
  if (!condition) {
    throw new Error(`FAIL: ${msg}`);
  }
}

let passed = 0;

function runCase(name: string, fn: () => void) {
  try {
    fn();
    console.log(`[PASS] Case ${passed + 1}: ${name}`);
    passed++;
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[FAIL] Case ${passed + 1}: ${name} -> ${msg}`);
    process.exit(1);
  }
}

// Case 1: Normal — Card active and visible for 2000 ms
runCase("Normal: counts active visible elapsed time accurately", () => {
  let state = createTelemetryTimerState("prob-1", true);
  const t0 = 1_000_000;
  state = setActiveProblem(state, "prob-1", t0);

  const t1 = t0 + 2000;
  const { durationMs } = consumeAttempt(state, "prob-1", t1);
  assert(durationMs === 2000, `Expected duration 2000 ms, got ${durationMs}`);
});

// Case 2: Tab hidden — document.hidden stops counting
runCase("Tab hidden: pauses timer during hidden tab intervals", () => {
  let state = createTelemetryTimerState("prob-1", true);
  const t0 = 1_000_000;
  state = setActiveProblem(state, "prob-1", t0);

  // Visible for 1000 ms
  const t1 = t0 + 1000;
  state = setVisibility(state, false, t1); // tab hidden

  // Hidden for 5000 ms
  const t2 = t1 + 5000;
  state = setVisibility(state, true, t2); // tab visible again

  // Visible for another 2000 ms
  const t3 = t2 + 2000;
  const { durationMs } = consumeAttempt(state, "prob-1", t3);

  // Total visible time: 1000 + 2000 = 3000 ms (5000 ms hidden not counted)
  assert(durationMs === 3000, `Expected duration 3000 ms, got ${durationMs}`);
});

// Case 3: Capped — Cap per attempt at 600,000 ms (10 min)
runCase("Capped: caps attempt duration at 600,000 ms (10 minutes)", () => {
  let state = createTelemetryTimerState("prob-1", true);
  const t0 = 1_000_000;
  state = setActiveProblem(state, "prob-1", t0);

  // 700,000 ms elapsed (> 600,000 ms)
  const t1 = t0 + 700_000;
  const { durationMs } = consumeAttempt(state, "prob-1", t1);

  assert(durationMs === MAX_ATTEMPT_DURATION_MS, `Expected capped duration ${MAX_ATTEMPT_DURATION_MS}, got ${durationMs}`);
  assert(durationMs === 600_000, `Expected 600000 ms, got ${durationMs}`);
});

// Case 4: 2 attempts — Incremental time on repeated attempts
runCase("2 attempts: measures incremental duration on repeated attempts", () => {
  let state = createTelemetryTimerState("prob-1", true);
  const t0 = 1_000_000;
  state = setActiveProblem(state, "prob-1", t0);

  // Attempt 1 submitted at t0 + 4000 ms
  const t1 = t0 + 4000;
  const res1 = consumeAttempt(state, "prob-1", t1);
  assert(res1.durationMs === 4000, `Attempt 1 expected 4000 ms, got ${res1.durationMs}`);
  state = res1.nextState;

  // Attempt 2 submitted at t1 + 3000 ms
  const t2 = t1 + 3000;
  const res2 = consumeAttempt(state, "prob-1", t2);
  assert(res2.durationMs === 3000, `Attempt 2 expected 3000 ms, got ${res2.durationMs}`);
});

// Case 5: Problem switch — Independent timers per problem
runCase("Problem switch: maintains independent timers across problems", () => {
  let state = createTelemetryTimerState("prob-A", true);
  const t0 = 1_000_000;
  state = setActiveProblem(state, "prob-A", t0);

  // Prob A active for 2000 ms
  const t1 = t0 + 2000;
  state = setActiveProblem(state, "prob-B", t1);

  // Prob B active for 5000 ms
  const t2 = t1 + 5000;
  state = setActiveProblem(state, "prob-A", t2);

  // Prob A active for another 3000 ms
  const t3 = t2 + 3000;

  // Check attempt for Prob A
  const resA = consumeAttempt(state, "prob-A", t3);
  assert(resA.durationMs === 5000, `Prob A expected 5000 ms (2000 + 3000), got ${resA.durationMs}`);

  // Check attempt for Prob B
  const resB = consumeAttempt(state, "prob-B", t3);
  assert(resB.durationMs === 5000, `Prob B expected 5000 ms, got ${resB.durationMs}`);
});

console.log(`\nAll ${passed} Telemetry Timer test cases PASSED.`);
