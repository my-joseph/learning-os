import {
  DrillDocument,
  Problem,
  ProblemState,
  CheckResult,
  MistakeTag,
  AttemptRecord,
} from "../types/drill";
import { isSubstantiveVerdict, sanitizeCheckMessage } from "./reviewGuard";

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

  // 4. Skip action
  if (result.verdict === "skipped") {
    currentMistakes.add("concept-gap");
    const attempt: AttemptRecord = {
      input: trimmed || "(Skipped)",
      ts,
      verdict: "skipped",
      ...(prob.state?.setupRevealedBeforeAnswer ? { setupRevealed: true } : {}),
      ...(prob.state?.solutionRevealedBeforeAnswer ? { solutionRevealed: true } : {}),
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

  const isAssisted = Boolean(
    prob.state?.setupRevealedBeforeAnswer ||
      prob.state?.solutionRevealedBeforeAnswer ||
      hintsCount > 0 ||
      currentAttempts.some((a) => a.setupRevealed || a.solutionRevealed)
  );
  const hadPriorWrongOrPartial = currentAttempts.some(
    (a) =>
      a.verdict !== "correct" &&
      a.verdict !== "invalid input" &&
      a.verdict !== "parse_error"
  );

  // Calculate score (matches progress_store.item_score / weak_spots)
  let autoScore = prob.state?.score ?? null;
  if (result.verdict === "correct") {
    autoScore = isAssisted || hadPriorWrongOrPartial ? 0.5 : 1;
  } else if (result.verdict === "equivalent_not_in_form" || result.verdict === "partial") {
    autoScore = 0.5;
  } else if (result.verdict === "incorrect") {
    autoScore = 0;
  }

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
    ...(prob.state?.setupRevealedBeforeAnswer ? { setupRevealed: true } : {}),
    ...(prob.state?.solutionRevealedBeforeAnswer ? { solutionRevealed: true } : {}),
  };

  return {
    ...prob.state,
    userInput: trimmed,
    score: autoScore,
    skipped: substantive ? false : Boolean(prob.state?.skipped),
    mistakes: Array.from(newMistakes),
    lastCheck: sanitizedResult,
    attempts: [...currentAttempts, attempt],
    hintsRevealed: hintsCount,
    durationMs: (prob.state?.durationMs || 0) + (options.durationMs || 0),
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

/**
 * Pure function to toggle diverged step.
 * Diverged does NOT attach any mistake tags!
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
    score: prob.state?.score === null || prob.state?.score === 1 ? 0.5 : prob.state.score,
  };
}

/**
 * Reset a single problem back to a clean unattempted state and strip revealed solutions.
 */
export function resetProblemForRetry(prob: Problem): Problem {
  const rest = { ...prob };
  delete rest.display;
  delete rest.plainText;
  delete rest.steps;
  delete rest.answerDisplay;
  delete rest.answerPlain;
  delete rest.solutionCode;
  return {
    ...rest,
    state: {
      userInput: "",
      userCode: prob.starterCode || prob.codeSnippet || "",
      score: null,
      divergedStep: null,
      mistakes: [],
      mistakeNote: "",
      ...(prob.state?.revisitNote ? { revisitNote: prob.state.revisitNote } : {}),
      skipped: false,
      lastCheck: null,
      lastTestReport: null,
      attempts: [],
      hintsRevealed: 0,
      setupRevealedBeforeAnswer: false,
      solutionRevealedBeforeAnswer: false,
      durationMs: 0,
    },
  };
}

/** Clear the visible answer/result for a review retry while retaining the attempt history. */
export function resetAnswerForReviewRetry(state: ProblemState): ProblemState {
  return {
    ...state,
    userInput: "",
    score: null,
    divergedStep: null,
    skipped: false,
    lastCheck: null,
  };
}

/**
 * Reset every problem in a drill using `resetProblemForRetry` and reset `sessionSummary`.
 */
export function resetDrillForRetry(doc: DrillDocument): DrillDocument {
  return {
    ...doc,
    problems: doc.problems.map(resetProblemForRetry),
    sessionSummary: {
      ...doc.sessionSummary,
      score: 0,
      accuracyPct: 0,
      practiceStatus: "Ready",
      mistakeCategories: [],
      divergedStepsSummary: "",
      attemptDate: null,
    },
  };
}
