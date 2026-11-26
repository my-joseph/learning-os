import type {
  AttemptRecord,
  ProblemState,
  ReviewRecord,
  TestRunRecord,
  TestRunReport,
  VariantSessionRecord,
} from "../types/drill";
import { compareIsoTimestamps, isSubstantiveVerdict, isTimestampInCycle } from "./reviewGuard";
import type { StatusTone } from "./statusTone";

export type ScoreValue = 1 | 0.5 | 0 | null;
export type ProblemOutcome = "correct" | "assisted" | "wrong" | "skipped" | "notTried";

export interface ScoreProblemOptions {
  /** True for PRG workspace problems / labs (also auto-detected when reviews/test reports exist). */
  isPrg?: boolean;
  /** Optional live test report overriding `state.lastTestReport`. */
  testReport?: TestRunReport | Record<string, unknown> | null;
  /** Optional explicit cycle boundary overriding `state.cycleStartedAt`. */
  cycleStartedAt?: string | null;
  /** True when scoring a variant session (includes `kind: "variant"` attempts). */
  isVariant?: boolean;
  /**
   * Internal flag: compute the auto score before checking lower-only `state.score` self-score
   * (used by `applyCheckResult`, `computeTestRunTransition`, and `maxAllowedSelfScore`).
   */
  ignoreStateScore?: boolean;
}

export interface ScoreResult {
  score: ScoreValue;
  outcome: ProblemOutcome;
  firstTry: boolean;
  usedHelp: boolean;
}

interface NormalisedReport {
  hasData: boolean;
  allPassed: boolean;
  ts: string | null;
}

function finiteNum(val: unknown): number | null {
  return typeof val === "number" && Number.isFinite(val) ? val : null;
}

function clampScoreValue(val: unknown): 1 | 0.5 | 0 | null {
  if (typeof val !== "number" || !Number.isFinite(val)) return null;
  if (val >= 1) return 1;
  if (val > 0) return 0.5;
  return 0;
}

function normaliseReport(
  raw: TestRunReport | Record<string, unknown> | null | undefined,
  cycleStartedAt: string | null
): NormalisedReport {
  if (!raw || typeof raw !== "object") {
    return { hasData: false, allPassed: false, ts: null };
  }
  const r = raw as Record<string, unknown>;
  const ts = typeof r.ts === "string" && r.ts.trim() ? r.ts.trim() : null;
  if (ts && cycleStartedAt && !isTimestampInCycle(ts, cycleStartedAt)) {
    return { hasData: false, allPassed: false, ts: null };
  }

  const passed = finiteNum(r.passedCount) ?? finiteNum(r.passed);
  const total = finiteNum(r.totalCount) ?? finiteNum(r.total);
  const failedCount = Array.isArray(r.failed) ? r.failed.length : finiteNum(r.failed);

  let allPassed = false;
  if (typeof r.allPassed === "boolean") {
    allPassed = r.allPassed && (total === null || total > 0);
  } else if (passed !== null && total !== null) {
    allPassed = total > 0 && passed === total && (failedCount === null || failedCount === 0);
  }

  return { hasData: true, allPassed, ts };
}

function reviewTimestamp(r: ReviewRecord | Record<string, unknown>): string {
  const rec = r as Record<string, unknown>;
  if (typeof rec.at === "string" && rec.at.trim()) return rec.at.trim();
  if (typeof rec.ts === "string" && rec.ts.trim()) return rec.ts.trim();
  return "";
}

function reviewTestsPass(r: ReviewRecord | Record<string, unknown>): boolean | null {
  const rec = r as Record<string, unknown>;
  if (!rec.tests || typeof rec.tests !== "object") return null;
  const t = rec.tests as Record<string, unknown>;
  const total = finiteNum(t.total);
  if (total === null) return null;
  const passed = finiteNum(t.passed) ?? 0;
  const failedCount = Array.isArray(t.failed) ? t.failed.length : finiteNum(t.failed) ?? 0;
  return total > 0 && passed === total && failedCount === 0;
}

function extractCycleData(
  state: Partial<ProblemState> | null | undefined,
  opts: ScoreProblemOptions = {}
) {
  const cycleStartedAt =
    opts.cycleStartedAt !== undefined
      ? opts.cycleStartedAt ?? null
      : state?.cycleStartedAt ?? null;
  const isVariant = Boolean(opts.isVariant);

  const rawAttempts = Array.isArray(state?.attempts) ? state!.attempts : [];
  const allOrigAttempts = rawAttempts.filter(
    (a): a is AttemptRecord =>
      Boolean(a && typeof a === "object" && (isVariant || a.kind !== "variant"))
  );
  const cycleAtts = allOrigAttempts.filter((a) => isTimestampInCycle(a.ts, cycleStartedAt));
  const substantiveAtts = cycleAtts.filter((a) => isSubstantiveVerdict(a.verdict));

  const rawReviews = Array.isArray(state?.reviews) ? state!.reviews : [];
  const allReviews = rawReviews.filter(
    (r): r is ReviewRecord => Boolean(r && typeof r === "object" && Boolean(r.verdict))
  );
  const cycleRevs = allReviews.filter((r) =>
    isTimestampInCycle(reviewTimestamp(r), cycleStartedAt)
  );

  const rawTestRuns = Array.isArray(state?.testRuns) ? state!.testRuns : [];
  const allTestRuns = rawTestRuns.filter(
    (tr): tr is TestRunRecord => Boolean(tr && typeof tr === "object")
  );
  const cycleTestRuns = allTestRuns.filter((tr) => isTimestampInCycle(tr.ts, cycleStartedAt));

  const rawReport =
    opts.testReport !== undefined ? opts.testReport : state?.lastTestReport ?? null;
  const reportInfo = normaliseReport(rawReport, cycleStartedAt);

  const exampleViewedInCycle = Boolean(
    state?.exampleViewedAt && isTimestampInCycle(state.exampleViewedAt, cycleStartedAt)
  );
  const reviewHelpInCycle = Boolean(
    (state?.reviewHintRevealedAt &&
      isTimestampInCycle(state.reviewHintRevealedAt, cycleStartedAt)) ||
      (state?.reviewSetupRevealedAt &&
        isTimestampInCycle(state.reviewSetupRevealedAt, cycleStartedAt)) ||
      (state?.reviewStepsRevealedAt &&
        isTimestampInCycle(state.reviewStepsRevealedAt, cycleStartedAt))
  );
  // Untimestamped top-level help flags belong to the initial pre-cycle state (or a variant
  // session already cycle-filtered by `scoreVariant`). When a problem cycle (`cycleStartedAt`)
  // is active, only cycle-scoped timestamps and current-cycle attempt flags apply.
  const untimestampedHelp =
    (!cycleStartedAt || isVariant) &&
    Boolean(
      (state?.hintsRevealed ?? 0) > 0 ||
        state?.setupRevealedBeforeAnswer ||
        state?.solutionRevealedBeforeAnswer
    );
  const usedHelp = Boolean(
    untimestampedHelp ||
      exampleViewedInCycle ||
      reviewHelpInCycle ||
      cycleAtts.some((a) => Boolean(a.setupRevealed || a.solutionRevealed || a.exampleViewed))
  );

  const hasPriorHistory =
    allOrigAttempts.length > 0 || allReviews.length > 0 || allTestRuns.length > 0;
  const hasCurrentCycleRecord =
    cycleAtts.length > 0 ||
    cycleRevs.length > 0 ||
    cycleTestRuns.length > 0 ||
    reportInfo.hasData;
  const isStalePrevCycle = Boolean(cycleStartedAt && hasPriorHistory && !hasCurrentCycleRecord);
  const hasCurrentCycleSelfScore = Boolean(
    !cycleStartedAt ||
      (state?.selfScoreAt && isTimestampInCycle(state.selfScoreAt, cycleStartedAt))
  );

  return {
    cycleStartedAt,
    isVariant,
    allOrigAttempts,
    cycleAtts,
    substantiveAtts,
    allReviews,
    cycleRevs,
    allTestRuns,
    cycleTestRuns,
    reportInfo,
    usedHelp,
    hasPriorHistory,
    hasCurrentCycleSelfScore,
    isStalePrevCycle,
  };
}

function resolvePrgLatestTestsStatus(
  reportInfo: NormalisedReport,
  cycleRevs: readonly ReviewRecord[],
  cycleTestRuns: readonly TestRunRecord[]
): "pass" | "fail" | "unknown" {
  const latestRev = cycleRevs.length > 0 ? cycleRevs[cycleRevs.length - 1] : null;
  const latestRevAt = latestRev ? reviewTimestamp(latestRev) : "";
  const revTestPass = latestRev ? reviewTestsPass(latestRev) : null;

  if (reportInfo.hasData && latestRev) {
    const revCmp =
      reportInfo.ts && latestRevAt ? compareIsoTimestamps(latestRevAt, reportInfo.ts) : null;
    const isNewerRev = revCmp !== null ? revCmp > 0 : latestRevAt > (reportInfo.ts ?? "");
    if (reportInfo.ts && latestRevAt && isNewerRev && revTestPass !== null) {
      return revTestPass ? "pass" : "fail";
    }
    return reportInfo.allPassed ? "pass" : "fail";
  }
  if (reportInfo.hasData) {
    return reportInfo.allPassed ? "pass" : "fail";
  }
  if (latestRev) {
    if (revTestPass !== null) {
      return revTestPass ? "pass" : "fail";
    }
    return latestRev.verdict === "pass" ? "pass" : "unknown";
  }
  if (cycleTestRuns.length > 0) {
    return cycleTestRuns[cycleTestRuns.length - 1].allPassed ? "pass" : "fail";
  }
  return "unknown";
}

function applyLowerOnlySelfScore(
  autoScore: 1 | 0.5 | 0,
  autoOutcome: ProblemOutcome,
  firstTry: boolean,
  usedHelp: boolean,
  state: Partial<ProblemState>,
  opts: ScoreProblemOptions,
  hasCurrentCycleSelfScore: boolean
): ScoreResult {
  if (opts.ignoreStateScore || !hasCurrentCycleSelfScore) {
    return { score: autoScore, outcome: autoOutcome, firstTry, usedHelp };
  }
  const selfScore = clampScoreValue(state.score);
  if (selfScore !== null && selfScore < autoScore) {
    if (selfScore === 0) {
      return { score: 0, outcome: "wrong", firstTry: false, usedHelp };
    }
    return { score: 0.5, outcome: "assisted", firstTry: false, usedHelp };
  }
  return { score: autoScore, outcome: autoOutcome, firstTry, usedHelp };
}

/**
 * Single canonical scoring & classification rule for LearningOS (TS mirror of `progress_store.score_problem`).
 *
 * Operates strictly over the current cycle (`cycleStartedAt`).
 */
export function scoreProblem(
  state?: Partial<ProblemState> | null,
  opts: ScoreProblemOptions = {}
): ScoreResult {
  if (!state || typeof state !== "object") {
    return { score: null, outcome: "notTried", firstTry: false, usedHelp: false };
  }

  const data = extractCycleData(state, opts);
  const {
    cycleStartedAt,
    isVariant,
    substantiveAtts,
    cycleRevs,
    cycleTestRuns,
    reportInfo,
    usedHelp,
    hasPriorHistory,
    hasCurrentCycleSelfScore,
    isStalePrevCycle,
  } = data;

  if (isStalePrevCycle) {
    return { score: null, outcome: "notTried", firstTry: false, usedHelp };
  }

  // Skipped in the current cycle always scores 0 with outcome "skipped".
  // When `cycleStartedAt` is active and prior history exists, untimestamped `state.skipped`
  // may belong to a prior cycle (preserved by `reviewMerge`); current-cycle skips live in `cycleAtts`.
  if (state.skipped === true && (!cycleStartedAt || !hasPriorHistory)) {
    return { score: 0, outcome: "skipped", firstTry: false, usedHelp };
  }

  // PRG workspace / lab path: tests + code reviews.
  const hasPrgEvidence =
    cycleRevs.length > 0 || reportInfo.hasData || cycleTestRuns.length > 0;
  if (hasPrgEvidence) {
    const latestTestsStatus = resolvePrgLatestTestsStatus(
      reportInfo,
      cycleRevs,
      cycleTestRuns
    );
    const latestRev = cycleRevs.length > 0 ? cycleRevs[cycleRevs.length - 1] : null;

    if (latestTestsStatus === "fail") {
      return { score: 0, outcome: "wrong", firstTry: false, usedHelp };
    }
    if (!latestRev) {
      // Tests passing with no review yet -> score null, awaiting review (notTried).
      return { score: null, outcome: "notTried", firstTry: false, usedHelp };
    }
    if (latestRev.verdict !== "pass") {
      return { score: 0, outcome: "wrong", firstTry: false, usedHelp };
    }

    // Latest review is "pass" and tests pass.
    const hadEarlierRevise = cycleRevs.some((r) => r.verdict !== "pass");
    const hadEarlierFailedTestRun =
      cycleTestRuns.some((tr) => !tr.allPassed) ||
      (reportInfo.hasData && !reportInfo.allPassed) ||
      cycleRevs.some((r) => reviewTestsPass(r) === false);

    if (!usedHelp && !hadEarlierRevise && !hadEarlierFailedTestRun) {
      return { score: 1, outcome: "correct", firstTry: true, usedHelp: false };
    }
    return { score: 0.5, outcome: "assisted", firstTry: false, usedHelp };
  }

  // Math / choice / in-browser PRG path: substantive check attempts in current cycle.
  if (substantiveAtts.length > 0) {
    const firstCorrectIdx = substantiveAtts.findIndex((a) => a.verdict === "correct");
    if (firstCorrectIdx === 0) {
      const autoScore: 1 | 0.5 = usedHelp ? 0.5 : 1;
      const autoOutcome: ProblemOutcome = usedHelp ? "assisted" : "correct";
      return applyLowerOnlySelfScore(
        autoScore,
        autoOutcome,
        !usedHelp,
        usedHelp,
        state,
        opts,
        hasCurrentCycleSelfScore
      );
    }
    if (firstCorrectIdx > 0) {
      return applyLowerOnlySelfScore(
        0.5,
        "assisted",
        false,
        usedHelp,
        state,
        opts,
        hasCurrentCycleSelfScore
      );
    }

    const latestVerdict = substantiveAtts[substantiveAtts.length - 1].verdict;
    if (latestVerdict === "skipped") {
      return { score: 0, outcome: "skipped", firstTry: false, usedHelp };
    }
    if (latestVerdict === "partial" || latestVerdict === "equivalent_not_in_form") {
      return applyLowerOnlySelfScore(
        0.5,
        "assisted",
        false,
        usedHelp,
        state,
        opts,
        hasCurrentCycleSelfScore
      );
    }
    return { score: 0, outcome: "wrong", firstTry: false, usedHelp };
  }

  // Fallback for lightweight state carrying a substantive `lastCheck` without `attempts[]`.
  if (!cycleStartedAt && state.lastCheck && isSubstantiveVerdict(state.lastCheck.verdict)) {
    const v = state.lastCheck.verdict;
    if (v === "skipped") {
      return { score: 0, outcome: "skipped", firstTry: false, usedHelp };
    }
    if (v === "correct") {
      const autoScore: 1 | 0.5 = usedHelp ? 0.5 : 1;
      const autoOutcome: ProblemOutcome = usedHelp ? "assisted" : "correct";
      return applyLowerOnlySelfScore(
        autoScore,
        autoOutcome,
        !usedHelp,
        usedHelp,
        state,
        opts,
        hasCurrentCycleSelfScore
      );
    }
    if (v === "partial" || v === "equivalent_not_in_form") {
      return applyLowerOnlySelfScore(
        0.5,
        "assisted",
        false,
        usedHelp,
        state,
        opts,
        hasCurrentCycleSelfScore
      );
    }
    return { score: 0, outcome: "wrong", firstTry: false, usedHelp };
  }

  // Unverified item with manual self-score (no auto-check, no PRG evidence, not skipped).
  if (!isVariant && !opts.ignoreStateScore && hasCurrentCycleSelfScore) {
    const manual = clampScoreValue(state.score);
    if (manual !== null) {
      if (manual === 1) {
        if (usedHelp) {
          return { score: 0.5, outcome: "assisted", firstTry: false, usedHelp: true };
        }
        return { score: 1, outcome: "correct", firstTry: true, usedHelp: false };
      }
      if (manual === 0.5) {
        return { score: 0.5, outcome: "assisted", firstTry: false, usedHelp };
      }
      return { score: 0, outcome: "wrong", firstTry: false, usedHelp };
    }
  }

  return { score: null, outcome: "notTried", firstTry: false, usedHelp };
}

/**
 * Score a similar-question variant record using the exact same rule as the main question.
 */
export function scoreVariant(
  record?: VariantSessionRecord | null,
  cycleStartedAt?: string | null
): ScoreResult {
  if (!record) {
    return { score: null, outcome: "notTried", firstTry: false, usedHelp: false };
  }
  const inCurrentCycle = isTimestampInCycle(record.servedAt, cycleStartedAt);
  const hasSelfScore =
    inCurrentCycle && typeof record.selfScore === "number" && Number.isFinite(record.selfScore);

  const adaptedState: Partial<ProblemState> = {
    attempts: Array.isArray(record.attempts) ? record.attempts : [],
    hintsRevealed: inCurrentCycle ? record.hintsRevealed ?? 0 : 0,
    setupRevealedBeforeAnswer: inCurrentCycle ? Boolean(record.setupRevealed) : false,
    solutionRevealedBeforeAnswer: inCurrentCycle ? Boolean(record.stepsRevealed) : false,
    ...(hasSelfScore
      ? {
          score: record.selfScore,
          ...(cycleStartedAt ? { selfScoreAt: record.servedAt || cycleStartedAt } : {}),
        }
      : {}),
    cycleStartedAt: cycleStartedAt ?? null,
  };

  return scoreProblem(adaptedState, {
    cycleStartedAt: cycleStartedAt ?? null,
    isVariant: true,
    ignoreStateScore: !hasSelfScore,
  });
}

/**
 * Return true for a PRG problem/milestone whose latest test run in the current cycle passed
 * all tests, with no review recorded in the current cycle yet ("Awaiting review").
 */
export function isAwaitingReview(
  state?: Partial<ProblemState> | null,
  opts: ScoreProblemOptions = {}
): boolean {
  if (!state || typeof state !== "object") return false;
  const data = extractCycleData(state, opts);
  if (data.isStalePrevCycle) return false;
  if (state.skipped === true && (!data.cycleStartedAt || !data.hasPriorHistory)) return false;
  if (data.cycleRevs.length > 0) return false;
  const hasTestEvidence = data.reportInfo.hasData || data.cycleTestRuns.length > 0;
  if (!hasTestEvidence) return false;
  return resolvePrgLatestTestsStatus(data.reportInfo, data.cycleRevs, data.cycleTestRuns) === "pass";
}

/**
 * Return true once a math/choice/in-browser/variant problem has a correct substantive check
 * in the current cycle (Rule 2: lock input and ignore further checks until Reset).
 */
export function isLockedAfterCorrect(
  state?: Partial<ProblemState> | null,
  opts: Pick<ScoreProblemOptions, "cycleStartedAt" | "isVariant"> = {}
): boolean {
  if (!state || typeof state !== "object") return false;
  const data = extractCycleData(state, opts);
  if (data.isStalePrevCycle) return false;
  if (data.substantiveAtts.some((a) => a.verdict === "correct")) {
    return true;
  }
  if (!data.cycleStartedAt && data.allOrigAttempts.length === 0 && state.lastCheck?.verdict === "correct") {
    return true;
  }
  return false;
}

/**
 * Maximum score a learner's self-score may assign (Rule 3):
 * - Skipped -> 0 (cannot raise or clear skipped)
 * - Verified item -> auto-computed score (may only lower, never raise)
 * - PRG awaiting review -> null (self-score not applicable)
 * - Unverified item (no auto score) -> 1 (learner sets any score)
 */
export function maxAllowedSelfScore(
  state?: Partial<ProblemState> | null,
  opts: ScoreProblemOptions = {}
): 1 | 0.5 | 0 | null {
  if (!state || typeof state !== "object") return 1;
  const auto = scoreProblem(state, { ...opts, ignoreStateScore: true });
  if (auto.outcome === "skipped") return 0;
  if (auto.score !== null) return auto.score;
  if (isAwaitingReview(state, opts)) return null;
  return 1;
}

/**
 * Apply a learner self-score respecting Rule 3:
 * - Never clears `skipped` and never raises a skipped item.
 * - Never raises an auto-scored item above its computed score.
 * - Sets the score on unverified items.
 */
export function applySelfScore(
  state: ProblemState,
  requestedScore: number | null,
  opts: ScoreProblemOptions = {}
): ProblemState {
  const auto = scoreProblem(state, { ...opts, ignoreStateScore: true });
  if (auto.outcome === "skipped") {
    return state;
  }
  const cycleStartedAt =
    opts.cycleStartedAt !== undefined
      ? opts.cycleStartedAt ?? null
      : state.cycleStartedAt ?? null;
  if (requestedScore === null) {
    return {
      ...state,
      score: null,
      ...(cycleStartedAt ? { selfScoreAt: null } : {}),
    };
  }
  const normalized = clampScoreValue(requestedScore);
  if (normalized === null) {
    return state;
  }
  const maxAllowed = maxAllowedSelfScore(state, opts);
  if (maxAllowed === null) {
    return state;
  }
  const finalScore = normalized > maxAllowed ? maxAllowed : normalized;
  const nowIso = new Date().toISOString();
  const stamp =
    cycleStartedAt && !isTimestampInCycle(nowIso, cycleStartedAt) ? cycleStartedAt : nowIso;
  return {
    ...state,
    score: finalScore,
    ...(cycleStartedAt ? { selfScoreAt: stamp } : {}),
  };
}

/** Map canonical `ProblemOutcome` directly to `StatusTone`. */
export function outcomeToStatusTone(outcome: ProblemOutcome): StatusTone {
  return outcome;
}
