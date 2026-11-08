/**
 * Telemetry Timer (Practice Studio)
 * Pure state functions for measuring learner interaction time and hint telemetry.
 *
 * Rules:
 * 1. Counts only visible time (document.hidden stops counting).
 * 2. Independent timers per problem on question switch.
 * 3. Cap per attempt at 600,000 ms (10 min).
 * 4. Measures incremental time on repeated attempts.
 */

export const MAX_ATTEMPT_DURATION_MS = 600_000; // 10 minutes max cap per attempt

export interface ProblemTimerState {
  accumulatedMs: number;
  lastActiveStart: number | null; // non-null if this problem is currently active and document is visible
  hintsRevealed: number;
}

export interface TelemetryTimerState {
  activeProblemId: string | null;
  isDocumentVisible: boolean;
  problems: Record<string, ProblemTimerState>;
}

export function createTelemetryTimerState(initialProblemId?: string | null, isVisible = true): TelemetryTimerState {
  const state: TelemetryTimerState = {
    activeProblemId: initialProblemId || null,
    isDocumentVisible: isVisible,
    problems: {},
  };
  if (initialProblemId) {
    state.problems[initialProblemId] = {
      accumulatedMs: 0,
      lastActiveStart: isVisible ? Date.now() : null,
      hintsRevealed: 0,
    };
  }
  return state;
}

export function getOrCreateProblemState(state: TelemetryTimerState, problemId: string): ProblemTimerState {
  if (!state.problems[problemId]) {
    state.problems[problemId] = {
      accumulatedMs: 0,
      lastActiveStart: null,
      hintsRevealed: 0,
    };
  }
  return state.problems[problemId];
}

/**
 * Switch active problem card.
 */
export function setActiveProblem(
  state: TelemetryTimerState,
  newProblemId: string | null,
  now: number = Date.now()
): TelemetryTimerState {
  const next: TelemetryTimerState = {
    ...state,
    problems: { ...state.problems },
  };

  // Pause previous active problem
  if (next.activeProblemId && next.problems[next.activeProblemId]) {
    const prev = { ...next.problems[next.activeProblemId] };
    if (prev.lastActiveStart !== null) {
      const elapsed = Math.max(0, now - prev.lastActiveStart);
      prev.accumulatedMs += elapsed;
      prev.lastActiveStart = null;
    }
    next.problems[next.activeProblemId] = prev;
  }

  next.activeProblemId = newProblemId;

  // Start new active problem if provided
  if (newProblemId) {
    const current = { ...(next.problems[newProblemId] || { accumulatedMs: 0, lastActiveStart: null, hintsRevealed: 0 }) };
    if (next.isDocumentVisible) {
      current.lastActiveStart = now;
    } else {
      current.lastActiveStart = null;
    }
    next.problems[newProblemId] = current;
  }

  return next;
}

/**
 * Handle document visibility change (e.g. document.hidden / visibilitychange event).
 */
export function setVisibility(
  state: TelemetryTimerState,
  isVisible: boolean,
  now: number = Date.now()
): TelemetryTimerState {
  if (state.isDocumentVisible === isVisible) {
    return state;
  }

  const next: TelemetryTimerState = {
    ...state,
    isDocumentVisible: isVisible,
    problems: { ...state.problems },
  };

  if (!next.activeProblemId) {
    return next;
  }

  const prob = { ...(next.problems[next.activeProblemId] || { accumulatedMs: 0, lastActiveStart: null, hintsRevealed: 0 }) };

  if (!isVisible) {
    // Tab became hidden: stop running clock and accumulate visible elapsed time
    if (prob.lastActiveStart !== null) {
      const elapsed = Math.max(0, now - prob.lastActiveStart);
      prob.accumulatedMs += elapsed;
      prob.lastActiveStart = null;
    }
  } else {
    // Tab became visible: resume running clock
    prob.lastActiveStart = now;
  }

  next.problems[next.activeProblemId] = prob;
  return next;
}

/**
 * Record a hint revealed for a problem.
 */
export function recordHint(
  state: TelemetryTimerState,
  problemId: string
): TelemetryTimerState {
  const next: TelemetryTimerState = {
    ...state,
    problems: { ...state.problems },
  };
  const prob = { ...(next.problems[problemId] || { accumulatedMs: 0, lastActiveStart: null, hintsRevealed: 0 }) };
  prob.hintsRevealed += 1;
  next.problems[problemId] = prob;
  return next;
}

/**
 * Consume attempt telemetry (durationMs and hintsRevealed) and reset incremental timer for next attempt.
 */
export function consumeAttempt(
  state: TelemetryTimerState,
  problemId: string,
  now: number = Date.now()
): { durationMs: number; hintsRevealed: number; nextState: TelemetryTimerState } {
  const next: TelemetryTimerState = {
    ...state,
    problems: { ...state.problems },
  };

  const prob = { ...(next.problems[problemId] || { accumulatedMs: 0, lastActiveStart: null, hintsRevealed: 0 }) };

  let totalMs = prob.accumulatedMs;
  if (prob.lastActiveStart !== null) {
    totalMs += Math.max(0, now - prob.lastActiveStart);
  }

  // Cap at 600,000 ms (10 min), minimum 1 ms
  const cappedDuration = Math.min(MAX_ATTEMPT_DURATION_MS, Math.max(1, totalMs));
  const hints = prob.hintsRevealed;

  // Reset problem attempt timer for next attempt
  prob.accumulatedMs = 0;
  if (next.activeProblemId === problemId && next.isDocumentVisible) {
    prob.lastActiveStart = now;
  } else {
    prob.lastActiveStart = null;
  }

  next.problems[problemId] = prob;

  return {
    durationMs: cappedDuration,
    hintsRevealed: hints,
    nextState: next,
  };
}

/**
 * Reset a problem's timer and hint state (e.g. on manual problem reset).
 */
export function resetProblemTimer(
  state: TelemetryTimerState,
  problemId: string
): TelemetryTimerState {
  const next: TelemetryTimerState = {
    ...state,
    problems: { ...state.problems },
  };
  delete next.problems[problemId];
  return next;
}
