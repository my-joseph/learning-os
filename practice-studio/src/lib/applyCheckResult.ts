import {
  DrillDocument,
  Problem,
  ProblemState,
  CheckResult,
  MistakeTag,
  AttemptRecord,
  TestRunReport,
} from "../types/drill";
import { isSubstantiveVerdict, sanitizeCheckMessage } from "./reviewGuard";
import { isLockedAfterCorrect, scoreProblem } from "./scoring";
import { isInCycle } from "./similarTabs";

export interface ApplyCheckOptions {
  durationMs?: number;
  ts?: string;
  hintsRevealed?: number;
}

/**
 * Pure function to apply SymPy / Code check result to problem state.
 */
export function applyCheckResult(
  prob: Problem,
  inputVal: string,
  result: CheckResult,
  mistakeTags: MistakeTag[] = [],
  options: ApplyCheckOptions = {}
): ProblemState {
  const trimmed = (inputVal || "").trim();
  const ts = options.ts || new Date().toISOString();
  const currentAttempts = prob.state?.attempts || [];
  const currentMistakes = new Set(prob.state?.mistakes || []);
  const hintsCount = options.hintsRevealed ?? prob.state?.hintsRevealed ?? 0;

  // 1. Empty input (and not skipped) -> return unchanged state
  if (!trimmed && result.verdict !== "skipped") {
    return { ...prob.state };
  }

  // 2. Lock after correct (Rule 2): ignore further checks once correct in the current cycle.
  if (result.verdict !== "skipped" && isLockedAfterCorrect(prob.state)) {
    return { ...prob.state };
  }

  const cycleStartedAt = prob.state?.cycleStartedAt ?? null;
  const setupRevealedInCycle = cycleStartedAt
    ? Boolean(
        prob.state?.reviewSetupRevealedAt &&
          isInCycle(prob.state.reviewSetupRevealedAt, cycleStartedAt)
      )
    : Boolean(prob.state?.setupRevealedBeforeAnswer);
  const solutionRevealedInCycle = cycleStartedAt
    ? Boolean(
        prob.state?.reviewStepsRevealedAt &&
          isInCycle(prob.state.reviewStepsRevealedAt, cycleStartedAt)
      )
    : Boolean(prob.state?.solutionRevealedBeforeAnswer);

  // 4. Skip action
  if (result.verdict === "skipped") {
    currentMistakes.add("concept-gap");
    const attempt: AttemptRecord = {
      input: trimmed || "(Skipped)",
      ts,
      verdict: "skipped",
      ...(setupRevealedInCycle ? { setupRevealed: true } : {}),
      ...(solutionRevealedInCycle ? { solutionRevealed: true } : {}),
    };
    return {
      ...prob.state,
      userInput: trimmed || "(Skipped)",
      score: 0,
      skipped: true,
      mistakes: Array.from(currentMistakes),
      lastCheck: result,
      attempts: [...currentAttempts, attempt],
      hintsRevealed: hintsCount,
      durationMs: (prob.state?.durationMs || 0) + (options.durationMs || 0),
    };
  }

  const exampleViewed = Boolean(
    prob.state?.exampleViewedAt &&
      isInCycle(prob.state.exampleViewedAt, cycleStartedAt)
  );

  const newMistakes = new Set(prob.state?.mistakes || []);
  let matchedTrapTag: string | undefined;

  // Diagnostics codes
  const diagCodes = (result.diagnostics || []).map((d) => d.code);
  const diagCodeSet = new Set(diagCodes);

  if (result.verdict === "incorrect") {
    // Choice option trapTag
    if (prob.answerSpec?.type === "choice" && Array.isArray(prob.answerSpec.options)) {
      const chosen = prob.answerSpec.options.find(
        (o) => String(o.id).trim() === trimmed
      );
      if (chosen && (chosen.trapTag || chosen.tag)) {
        const choiceTrap = chosen.trapTag || chosen.tag;
        if (choiceTrap) {
          newMistakes.add(choiceTrap);
          matchedTrapTag = choiceTrap;
        }
      }
    }

    // trapMatched -> problem.commonTrapTag
    if (result.trapMatched && prob.commonTrapTag) {
      newMistakes.add(prob.commonTrapTag);
      matchedTrapTag = prob.commonTrapTag;
    }

    // When trapMatched is true, attach ONLY commonTrapTag (do not attach autoFrom from diagnostics)
    // When trapMatched is false / absent, autoFrom works as before
    if (!result.trapMatched) {
      mistakeTags.forEach((tag) => {
        if (tag.autoFrom?.some((c) => diagCodeSet.has(c))) {
          newMistakes.add(tag.id);
        }
      });
    }

    // Fallback "unclassified" ONLY when no tag was attached
    if (newMistakes.size === 0) {
      newMistakes.add("unclassified");
    }
  } else if (result.verdict === "partial" && result.trapMatched && prob.commonTrapTag) {
    // Incomplete answer equal to the trap (e.g. one root of a solution set omitted): tag the trap.
    newMistakes.add(prob.commonTrapTag);
    matchedTrapTag = prob.commonTrapTag;
  } else if (result.verdict !== "correct") {
    mistakeTags.forEach((tag) => {
      if (tag.autoFrom?.some((c) => diagCodeSet.has(c))) {
        newMistakes.add(tag.id);
      }
    });
  }

  const calmMessage = sanitizeCheckMessage(result.verdict, result.message);
  const sanitizedResult: CheckResult =
    calmMessage === result.message ? result : { ...result, message: calmMessage };
  const substantive = isSubstantiveVerdict(result.verdict);

  const attempt: AttemptRecord = {
    input: trimmed,
    ts,
    verdict: result.verdict,
    ...(diagCodes.length > 0 ? { diagnosticCodes: diagCodes } : {}),
    ...(matchedTrapTag ? { matchedTrap: matchedTrapTag } : {}),
    ...(setupRevealedInCycle ? { setupRevealed: true } : {}),
    ...(solutionRevealedInCycle ? { solutionRevealed: true } : {}),
    ...(exampleViewed ? { exampleViewed: true } : {}),
  };

  const nextStateWithoutScore: ProblemState = {
    ...prob.state,
    userInput: trimmed,
    skipped: substantive ? false : Boolean(prob.state?.skipped),
    mistakes: Array.from(newMistakes),
    lastCheck: sanitizedResult,
    attempts: [...currentAttempts, attempt],
    hintsRevealed: hintsCount,
    durationMs: (prob.state?.durationMs || 0) + (options.durationMs || 0),
  };

  const computedScore = substantive
    ? scoreProblem(nextStateWithoutScore, { ignoreStateScore: true }).score
    : prob.state?.score ?? null;

  return {
    ...nextStateWithoutScore,
    score: computedScore,
  };
}

/**
 * Pure function to apply skip to a problem state.
 */
export function applySkip(
  prob: Problem,
  options: ApplyCheckOptions = {}
): ProblemState {
  const skipResult: CheckResult = {
    verdict: "skipped",
    message: "Skipped (Concept Gap / Unsure) — Review step-by-step solution below to solidify mental model.",
    components: [],
    diagnostics: [],
  };
  return applyCheckResult(prob, prob.state?.userInput || "(Skipped)", skipResult, [], options);
}

/** Apply a test report produced by an actual test runner. */
export function applyTestReport(state: ProblemState, report: TestRunReport, ts: string): ProblemState {
  const next = {
    ...state,
    lastTestReport: { ...report, ts },
    testRuns: [
      ...(state.testRuns || []),
      {
        ts,
        allPassed: Boolean(report.allPassed &&
          (typeof report.totalCount !== "number" || report.totalCount > 0)),
        passedCount: report.passedCount,
        totalCount: report.totalCount,
      },
    ],
    skipped: false,
  };
  return { ...next, score: scoreProblem(next, { isPrg: true, ignoreStateScore: true }).score };
}

/**
 * Pure function to toggle diverged step.
 * Diverged step is a learning note only (Rule 4): never modifies mistake tags or score.
 */
export function applyDivergedStep(
  prob: Problem,
  stepIdx: number
): ProblemState {
  const isCurrent = prob.state?.divergedStep === stepIdx;
  const newDiverged = isCurrent ? null : stepIdx;
  return {
    ...prob.state,
    divergedStep: newDiverged,
  };
}

/**
 * Reset a single problem for a new retry cycle: clears the visible/active state and
 * strips revealed solutions, sets `cycleStartedAt = now`, and preserves all history
 * (`attempts`, `mistakes`, `mistakeNote`, `revisitNote`, `reviews`, variant history).
 */
export function resetProblemForRetry(
  prob: Problem,
  nowIso: string = new Date().toISOString()
): Problem {
  const rest = { ...prob };
  delete rest.display;
  delete rest.plainText;
  delete rest.steps;
  delete rest.answerDisplay;
  delete rest.answerPlain;
  delete rest.solutionCode;
  const prevState = prob.state;
  const nextState: ProblemState = {
    ...prevState,
    userInput: "",
    userCode: prob.starterCode || prob.codeSnippet || "",
    score: null,
    divergedStep: null,
    mistakes: Array.isArray(prevState?.mistakes) ? [...prevState.mistakes] : [],
    mistakeNote: prevState?.mistakeNote || "",
    ...(prevState?.revisitNote ? { revisitNote: prevState.revisitNote } : {}),
    skipped: false,
    lastCheck: null,
    lastTestReport: null,
    ...(Array.isArray(prevState?.testRuns) ? { testRuns: [...prevState.testRuns] } : {}),
    attempts: Array.isArray(prevState?.attempts) ? [...prevState.attempts] : [],
    ...(Array.isArray(prevState?.reviews) ? { reviews: [...prevState.reviews] } : {}),
    hintsRevealed: 0,
    setupRevealedBeforeAnswer: false,
    solutionRevealedBeforeAnswer: false,
    durationMs: 0,
    cycleStartedAt: nowIso,
  };
  delete nextState.reviewHintRevealedAt;
  delete nextState.reviewSetupRevealedAt;
  delete nextState.reviewStepsRevealedAt;
  delete nextState.selfScoreAt;
  return {
    ...rest,
    state: nextState,
  };
}

/** Clear the visible answer/result for a review retry while retaining the attempt history. */
export function resetAnswerForReviewRetry(
  state: ProblemState,
  nowIso: string = new Date().toISOString()
): ProblemState {
  const next: ProblemState = {
    ...state,
    userInput: "",
    score: null,
    divergedStep: null,
    skipped: false,
    lastCheck: null,
    setupRevealedBeforeAnswer: false,
    solutionRevealedBeforeAnswer: false,
    hintsRevealed: 0,
    cycleStartedAt: nowIso,
  };
  delete next.reviewHintRevealedAt;
  delete next.reviewSetupRevealedAt;
  delete next.reviewStepsRevealedAt;
  delete next.selfScoreAt;
  return next;
}

/**
 * Reset every problem in a drill using `resetProblemForRetry` (starting a new cycle
 * while preserving history) and reset `sessionSummary`.
 */
export function resetDrillForRetry(
  doc: DrillDocument,
  nowIso: string = new Date().toISOString()
): DrillDocument {
  return {
    ...doc,
    problems: doc.problems.map((p) => resetProblemForRetry(p, nowIso)),
    sessionSummary: {
      ...doc.sessionSummary,
      score: 0,
      accuracyPct: 0,
      practiceStatus: "Ready",
      mistakeCategories: [],
      divergedStepsSummary: "",
      attemptDate: null,
      syncedToNotionAt: null,
      syncedFingerprint: null,
    },
  };
}
