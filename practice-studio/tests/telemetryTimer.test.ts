/**
 * Unit tests for Telemetry Timer (11 cases)
 * Run: npx tsx practice-studio/tests/telemetryTimer.test.ts
 */

import {
  createTelemetryTimerState,
  setActiveProblem,
  setVisibility,
  pauseTimer,
  resumeTimer,
  consumeAttempt,
  resetProblemTimer,
  getAttemptElapsedMs,
  getProblemDisplayMs,
  getDrillTotalMs,
  formatTimerClock,
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

// Case 6: Pause stops accrual
runCase("Pause: stops time accrual immediately and freezes elapsed duration", () => {
  const t0 = 1_000_000;
  let state = createTelemetryTimerState("prob-1", true, false, t0);

  // Active for 3500 ms
  const t1 = t0 + 3500;
  state = pauseTimer(state, t1);
  assert(state.paused === true, "Expected state.paused to be true");

  // 20 seconds pass while paused -> must not accrue
  const t2 = t1 + 20_000;
  assert(
    getAttemptElapsedMs(state, "prob-1", t2) === 3500,
    `Expected frozen elapsed 3500 ms, got ${getAttemptElapsedMs(state, "prob-1", t2)}`
  );

  // Consuming an attempt while paused keeps the next attempt paused
  const res = consumeAttempt(state, "prob-1", t2);
  assert(res.durationMs === 3500, `Expected 3500 ms, got ${res.durationMs}`);
  assert(res.nextState.paused === true, "Expected nextState to remain paused");
  assert(
    res.nextState.problems["prob-1"].lastActiveStart === null,
    "Next attempt must stay paused until resumed"
  );
  assert(
    getAttemptElapsedMs(res.nextState, "prob-1", t2 + 10_000) === 0,
    "Next attempt must remain at 0 ms while paused"
  );
});

// Case 7: Resume continues from accumulated elapsed time
runCase("Resume: continues accruing from paused accumulated duration", () => {
  const t0 = 1_000_000;
  let state = createTelemetryTimerState("prob-1", true, false, t0);

  const t1 = t0 + 2500;
  state = pauseTimer(state, t1);

  const t2 = t1 + 15_000;
  state = resumeTimer(state, t2);
  assert(state.paused === false, "Expected state.paused to be false");

  const t3 = t2 + 4000;
  assert(
    getAttemptElapsedMs(state, "prob-1", t3) === 6500,
    `Expected 6500 ms (2500 + 4000), got ${getAttemptElapsedMs(state, "prob-1", t3)}`
  );
  const { durationMs } = consumeAttempt(state, "prob-1", t3);
  assert(durationMs === 6500, `Expected consumed 6500 ms, got ${durationMs}`);
});

// Case 8: Pause + tab hidden interactions
runCase("Pause + tab hidden: paused time never accrues across visibility changes", () => {
  const t0 = 1_000_000;
  let state = createTelemetryTimerState("prob-1", true, false, t0);

  // Visible & running for 2000 ms
  const t1 = t0 + 2000;
  state = pauseTimer(state, t1);

  // Tab hidden at t2, tab visible again at t3 while still paused
  const t2 = t1 + 5000;
  state = setVisibility(state, false, t2);
  const t3 = t2 + 8000;
  state = setVisibility(state, true, t3);

  assert(state.paused === true, "Returning visibility must keep manual pause active");
  assert(
    getAttemptElapsedMs(state, "prob-1", t3 + 4000) === 2000,
    "Time must stay frozen at 2000 ms after visibility cycle while paused"
  );

  // Also test pausing while tab is hidden, then resuming while still hidden
  const t4 = t3 + 4000;
  state = setVisibility(state, false, t4);
  state = resumeTimer(state, t4 + 1000);
  assert(
    state.problems["prob-1"].lastActiveStart === null,
    "Resuming while tab is hidden must wait until tab becomes visible"
  );
  const t5 = t4 + 5000;
  state = setVisibility(state, true, t5);
  const t6 = t5 + 3000;
  const { durationMs } = consumeAttempt(state, "prob-1", t6);
  assert(durationMs === 5000, `Expected 5000 ms (2000 + 3000), got ${durationMs}`);
});

// Case 9: Switching question while paused
runCase("Switch while paused: global pause applies to newly opened question until resumed", () => {
  const t0 = 1_000_000;
  let state = createTelemetryTimerState("prob-A", true, false, t0);

  // Work on A for 3000 ms, then pause
  const t1 = t0 + 3000;
  state = pauseTimer(state, t1);

  // Switch to B while paused
  const t2 = t1 + 5000;
  state = setActiveProblem(state, "prob-B", t2);
  assert(state.paused === true, "Switching questions must preserve global pause");
  assert(
    state.problems["prob-B"].lastActiveStart === null,
    "Newly opened problem must stay paused"
  );

  // Wait 10s while paused on B
  const t3 = t2 + 10_000;
  assert(getAttemptElapsedMs(state, "prob-A", t3) === 3000, "Prob A stays at 3000 ms");
  assert(getAttemptElapsedMs(state, "prob-B", t3) === 0, "Prob B stays at 0 ms while paused");

  // Resume while on B
  state = resumeTimer(state, t3);
  const t4 = t3 + 4000;
  assert(getAttemptElapsedMs(state, "prob-A", t4) === 3000, "Prob A remains frozen at 3000 ms");
  assert(getAttemptElapsedMs(state, "prob-B", t4) === 4000, "Prob B accrues 4000 ms after resume");
});

// Case 10: Display helpers and formatting
runCase("Display helpers: recorded + capped running time, drill total, mm:ss and h:mm:ss", () => {
  const t0 = 1_000_000;
  let state = createTelemetryTimerState("Q01", true, false, t0);
  const t1 = t0 + 700_000; // exceeds 10-min cap per attempt

  // Unconsumed attempt is capped at 600,000 ms
  assert(getAttemptElapsedMs(state, "Q01", t1) === MAX_ATTEMPT_DURATION_MS, "Attempt display capped at 10 min");

  // Recorded 45s + capped 600s = 645s
  assert(getProblemDisplayMs(45_000, state, "Q01", t1) === 645_000, "Recorded + running sum");

  // Drill total across multiple questions
  state = createTelemetryTimerState("Q01", true, false, t0);
  const t2 = t0 + 12_000;
  const totalMs = getDrillTotalMs(
    [
      { id: "Q01", state: { durationMs: 30_000 } },
      { id: "Q02", state: { durationMs: 18_000 } },
      { id: "Q03", state: {} },
    ],
    state,
    t2
  );
  assert(totalMs === 60_000, `Expected drill total 60000 ms, got ${totalMs}`);

  // Clock formatting
  assert(formatTimerClock(0) === "00:00", "0 ms -> 00:00");
  assert(formatTimerClock(950) === "00:00", "950 ms -> 00:00");
  assert(formatTimerClock(65_000) === "01:05", "65s -> 01:05");
  assert(formatTimerClock(3_599_000) === "59:59", "3599s -> 59:59");
  assert(formatTimerClock(3_600_000) === "1:00:00", "3600s -> 1:00:00");
  assert(formatTimerClock(3_723_000) === "1:02:03", "3723s -> 1:02:03");
});

// Case 11: resetProblemTimer resets active problem properly
runCase("resetProblemTimer: resets active problem and respects pause state", () => {
  const t0 = 1_000_000;
  let state = createTelemetryTimerState("Q01", true, false, t0);
  state = resetProblemTimer(state, "Q01", t0 + 5000);
  assert(
    getAttemptElapsedMs(state, "Q01", t0 + 7000) === 2000,
    "Running active problem restarts from reset timestamp"
  );

  state = pauseTimer(state, t0 + 7000);
  state = resetProblemTimer(state, "Q01", t0 + 8000);
  assert(
    getAttemptElapsedMs(state, "Q01", t0 + 15_000) === 0,
    "Paused active problem stays at 0 after reset"
  );
});

console.log(`\nAll ${passed} Telemetry Timer test cases PASSED.`);
