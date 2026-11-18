import { ProblemState } from "../types/drill";

export const NON_SUBSTANTIVE_VERDICTS = new Set(["invalid input", "parse_error"]);

export const CALM_PARSE_ERROR_MESSAGE =
  "Couldn't read that — check brackets and operators.";

const RAW_CHECK_ERROR_PATTERNS: RegExp[] = [
  /^\s*Invalid input:/i,
  /^\s*Calculation error:/i,
  /^\s*Failed to parse result:/i,
  /^\s*Internal server error:/i,
  /^\s*Error evaluating input:/i,
  /Could not tokenize expression/i,
  /unexpected EOF/i,
  /Syntax error/i,
  /invalid syntax/i,
  /Unwhitelisted/i,
  /Disallowed syntax/i,
  /Traceback/i,
  /\(<unknown>,\s*line \d+\)/i,
];

/**
 * Return true when a check verdict represents a substantive attempt
 * (anything other than "invalid input" / "parse_error", matching progress_store.py).
 */
export function isSubstantiveVerdict(verdict?: string | null): boolean {
  return Boolean(verdict && !NON_SUBSTANTIVE_VERDICTS.has(verdict));
}

/**
 * Replace raw SymPy / Python / internal check error strings with calm learner-facing copy.
 */
export function sanitizeCheckMessage(
  verdict?: string | null,
  message?: string | null
): string {
  const raw = typeof message === "string" ? message.trim() : "";
  if (verdict && NON_SUBSTANTIVE_VERDICTS.has(verdict)) {
    if (!raw || RAW_CHECK_ERROR_PATTERNS.some((re) => re.test(raw))) {
      return CALM_PARSE_ERROR_MESSAGE;
    }
  }
  return raw;
}

/**
 * Return true only if the problem has a substantive check/attempt, was skipped,
 * has a PRG test report, or has a code review. Draft input, parse/invalid-input
 * checks, and self-score alone do not count.
 */
export function hasSubstantiveAttempt(state?: ProblemState | null): boolean {
  if (!state) return false;
  if (state.skipped) return true;
  if (state.attempts?.some((a) => isSubstantiveVerdict(a.verdict))) return true;
  if (state.lastCheck != null && isSubstantiveVerdict(state.lastCheck.verdict)) return true;
  if (state.lastTestReport != null) return true;
  if ((state.reviews?.length ?? 0) > 0) return true;
  return false;
}

/**
 * Return true only if the problem has already been substantively attempted (checked /
 * test-run / reviewed) or skipped. Unanswered problems, malformed-input checks, and
 * self-scores without an attempt/skip must not reveal their verified answer.
 */
export function canRevealVerifiedAnswer(state?: ProblemState | null): boolean {
  return hasSubstantiveAttempt(state);
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
