/**
 * Pure help-ladder rules for "Try a similar question" and "See a worked example"
 * (per pilot/ux-variants-2026-11-19/design.md §3).
 *
 * Original question (after a wrong answer, when `hasVariants` is true):
 * - Wrong #1: primary `Try again` + text link `Try a similar question` (or `Resume similar question` if one is open).
 * - Cluster wrongs >= 2 (2nd wrong on original, or wrong on original + wrong on similar):
 *   adds `See a worked example` (unless the example has already been viewed, in which case it stays
 *   as a collapsed disclosure right below the result card).
 * - After the example has been viewed AND the learner gets the original wrong again:
 *   adds `Show steps` (the learner's own steps) to the result card.
 * - When the bank is exhausted (`remainingCount === 0`) and no active try is open:
 *   never shows an error string; shows `See a worked example` if unlocked & not viewed, else nothing.
 *
 * Similar question:
 * - Correct: primary `Back to Question N` (focused), quiet `Show steps` link; NEVER `Another similar question`.
 * - Wrong (after attempt): primary `Try again`, plus `See a worked example` (if cluster wrongs >= 2)
 *   and `Another similar question` (if `remainingCount > 0`).
 */

export interface OriginalLadderInput {
  hasVariants?: boolean;
  originalWrongAttempts: number;
  clusterWrongAttempts: number;
  hasActiveSimilar: boolean;
  /** Remaining unseen bank variants, or null before any variant endpoint has been called. */
  remainingCount: number | null;
  exampleViewed: boolean;
  /** True when the learner got the original question wrong at least once AFTER viewing the worked example. */
  wrongAfterExample: boolean;
  /** Latest verdict on the original question (actions only appear on non-correct, non-skipped states). */
  lastVerdict?: string | null;
  skipped?: boolean;
}

export interface OriginalLadderActions {
  showTrySimilar: boolean;
  showResumeSimilar: boolean;
  showSeeExample: boolean;
  showOwnSteps: boolean;
}

export function getOriginalLadderActions(
  input: OriginalLadderInput
): OriginalLadderActions {
  const {
    hasVariants,
    originalWrongAttempts,
    clusterWrongAttempts,
    hasActiveSimilar,
    remainingCount,
    exampleViewed,
    wrongAfterExample,
    lastVerdict,
    skipped,
  } = input;

  if (
    !hasVariants ||
    skipped ||
    lastVerdict === "correct" ||
    originalWrongAttempts < 1
  ) {
    return {
      showTrySimilar: false,
      showResumeSimilar: false,
      showSeeExample: false,
      showOwnSteps: false,
    };
  }

  const hasMoreTryVariants = remainingCount === null || remainingCount > 0;
  const showResumeSimilar = hasActiveSimilar;
  const showTrySimilar = !hasActiveSimilar && hasMoreTryVariants;
  const showSeeExample = clusterWrongAttempts >= 2 && !exampleViewed;
  const showOwnSteps = exampleViewed && wrongAfterExample;

  return {
    showTrySimilar,
    showResumeSimilar,
    showSeeExample,
    showOwnSteps,
  };
}

export interface SimilarLadderInput {
  hasAttemptOnCurrent: boolean;
  isCurrentCorrect: boolean;
  clusterWrongAttempts: number;
  remainingCount: number;
  stepsOpen: boolean;
}

export interface SimilarLadderActions {
  showBackToOriginal: boolean;
  showStepsLink: boolean;
  showSeeExample: boolean;
  showAnotherSimilar: boolean;
}

export function getSimilarLadderActions(
  input: SimilarLadderInput
): SimilarLadderActions {
  const {
    hasAttemptOnCurrent,
    isCurrentCorrect,
    clusterWrongAttempts,
    remainingCount,
    stepsOpen,
  } = input;

  if (!hasAttemptOnCurrent) {
    return {
      showBackToOriginal: false,
      showStepsLink: false,
      showSeeExample: false,
      showAnotherSimilar: false,
    };
  }

  if (isCurrentCorrect) {
    return {
      showBackToOriginal: true,
      showStepsLink: !stepsOpen,
      showSeeExample: false,
      showAnotherSimilar: false,
    };
  }

  return {
    showBackToOriginal: false,
    showStepsLink: false,
    showSeeExample: clusterWrongAttempts >= 2,
    showAnotherSimilar: remainingCount > 0,
  };
}

export interface VariantButtonState {
  showTry: boolean;
  showExample: boolean;
}

/**
 * Compatibility helper summarizing top-level variant availability thresholds:
 * - Hidden when `hasVariants` is falsy.
 * - `showTry`: >= 1 wrong attempt on original.
 * - `showExample`: >= 2 wrong attempts across the cluster (original + variants).
 */
export function getVariantButtonState({
  hasVariants,
  wrongAttempts,
  clusterWrongAttempts,
}: {
  hasVariants?: boolean;
  wrongAttempts: number;
  clusterWrongAttempts?: number;
}): VariantButtonState {
  if (!hasVariants) {
    return { showTry: false, showExample: false };
  }
  const clusterWrongs =
    typeof clusterWrongAttempts === "number" ? clusterWrongAttempts : wrongAttempts;
  return {
    showTry: wrongAttempts >= 1,
    showExample: clusterWrongs >= 2,
  };
}
