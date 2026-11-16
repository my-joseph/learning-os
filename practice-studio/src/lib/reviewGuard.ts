import { ProblemState } from "../types/drill";

/**
 * Return true only if the problem has already been answered (checked / test-run / reviewed),
 * skipped, or explicitly scored. Unanswered problems must not reveal their verified answer
 * in the Pre-Sync Review panel.
 */
export function canRevealVerifiedAnswer(state?: ProblemState | null): boolean {
  if (!state) return false;
  if (state.skipped) return true;
  if ((state.attempts?.length ?? 0) > 0) return true;
  if (state.lastCheck != null) return true;
  if (state.lastTestReport != null) return true;
  if ((state.reviews?.length ?? 0) > 0) return true;
  if (state.score !== null && state.score !== undefined) return true;
  return false;
}

/**
 * Return true only if the problem's latest review record has verdict "pass"
 * (docs/prg_reviewer_spec.md rule 3: reference solution only after a pass).
 */
export function canShowReferenceSolution(state?: ProblemState | null): boolean {
  const reviews = state?.reviews;
  if (!reviews || reviews.length === 0) return false;
  return reviews[reviews.length - 1].verdict === "pass";
}
