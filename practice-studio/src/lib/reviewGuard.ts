import { ProblemState, ReviewRecord, TestRunRecord } from "../types/drill";

export const NON_SUBSTANTIVE_VERDICTS = new Set(["invalid input", "parse_error"]);

const ISO_TIMESTAMP_RE =
  /^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?$/i;

/** Parse an ISO-8601 date or timestamp to UTC epoch milliseconds, or null when invalid. */
export function parseIsoTimestampMs(ts?: unknown): number | null {
  if (typeof ts !== "string") return null;
  const trimmed = ts.trim();
  if (!trimmed || !ISO_TIMESTAMP_RE.test(trimmed)) return null;
  const normalized = trimmed.replace(/([+-]\d{2})(\d{2})$/, "$1:$2");
  const ms = Date.parse(normalized);
  return Number.isFinite(ms) ? ms : null;
}

/** Compare two ISO timestamps by instant (-1, 0, 1), or null when either fails to parse. */
export function compareIsoTimestamps(a?: unknown, b?: unknown): number | null {
  const ta = parseIsoTimestampMs(a);
  const tb = parseIsoTimestampMs(b);
  if (ta === null || tb === null) return null;
  return ta < tb ? -1 : ta > tb ? 1 : 0;
}

/** Return true when `ts` falls at or after `cycleStartedAt` (absent `cycleStartedAt` counts all history). */
export function isTimestampInCycle(
  ts?: string | null,
  cycleStartedAt?: string | null
): boolean {
  if (!cycleStartedAt || !cycleStartedAt.trim()) return true;
  const tsMs = parseIsoTimestampMs(ts);
  const cycleMs = parseIsoTimestampMs(cycleStartedAt);
  return tsMs !== null && cycleMs !== null && tsMs >= cycleMs;
}

/** Return PRG/lab review records belonging to the current cycle (all reviews when `cycleStartedAt` is absent). */
export function cycleReviews(state?: ProblemState | null): ReviewRecord[] {
  const reviews = Array.isArray(state?.reviews) ? state!.reviews : [];
  if (reviews.length === 0) return [];
  const cycleStartedAt = state?.cycleStartedAt;
  if (!cycleStartedAt) return reviews;
  return reviews.filter((r) => r && isTimestampInCycle(r.at || r.ts, cycleStartedAt));
}

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
 * Return true when a check verdict represents a wrong/unsuccessful attempt
 * (excludes "correct", "skipped", "invalid input", "parse_error", and "equivalent_not_in_form").
 */
export function isWrongAttemptVerdict(verdict?: string | null): boolean {
  return verdict === "incorrect" || verdict === "partial";
}

/** Count wrong substantive attempts on the original problem state in the current cycle (excludes kind: "variant"). */
export function countWrongAttempts(state?: ProblemState | null): number {
  if (!state) return 0;
  const origAttempts = Array.isArray(state.attempts)
    ? state.attempts.filter((a) => a && a.kind !== "variant")
    : [];
  if (origAttempts.length > 0) {
    return origAttempts.filter(
      (a) => isWrongAttemptVerdict(a.verdict) && isTimestampInCycle(a.ts, state.cycleStartedAt)
    ).length;
  }
  if (state.lastCheck && isWrongAttemptVerdict(state.lastCheck.verdict)) {
    return 1;
  }
  return 0;
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
 * Return true only if the problem has a substantive check/attempt in the current cycle,
 * was skipped in the current cycle, has a PRG test report/run in the current cycle,
 * or has a code review in the current cycle.
 * Draft input, parse/invalid-input checks, self-score alone, and prior-cycle records
 * behind `cycleStartedAt` do not count.
 */
export function hasSubstantiveAttempt(
  state?: ProblemState | null,
  opts?: { isVariant?: boolean }
): boolean {
  if (!state) return false;
  const cycleStartedAt = state.cycleStartedAt;
  const isVariant = Boolean(opts?.isVariant);
  if (
    state.attempts?.some(
      (a) =>
        (isVariant || a?.kind !== "variant") &&
        isSubstantiveVerdict(a.verdict) &&
        isTimestampInCycle(a.ts, cycleStartedAt)
    )
  ) {
    return true;
  }
  if (cycleReviews(state).length > 0) return true;
  if (
    Array.isArray(state.testRuns) &&
    state.testRuns.some((tr) => tr && isTimestampInCycle(tr.ts, cycleStartedAt))
  ) {
    return true;
  }
  if (state.lastTestReport != null) {
    if (!cycleStartedAt) return true;
    const reportTs =
      typeof (state.lastTestReport as { ts?: unknown }).ts === "string"
        ? (state.lastTestReport as { ts?: string }).ts
        : null;
    if (reportTs && isTimestampInCycle(reportTs, cycleStartedAt)) return true;
  }
  // When a review/retry cycle is active (`cycleStartedAt`), untimestamped top-level
  // fields (`skipped`, `lastCheck`, untimestamped `lastTestReport`) may belong to a
  // prior cycle (e.g. after `startProblemCycle` on /review) and must not unlock it.
  if (cycleStartedAt) return false;
  if (state.skipped) return true;
  if (state.lastCheck != null && isSubstantiveVerdict(state.lastCheck.verdict)) return true;
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

const NOTION_CHECK_VERDICTS = new Set(["correct", "incorrect", "partial", "equivalent_not_in_form"]);

/** A skip can sync as a concept gap. Item content requires a graded answer,
 * an executed test run, or a code review in the current cycle. */
export function getNotionAttemptEvidence(state: ProblemState | undefined, isPrg: boolean) {
  const cycleStartedAt = state?.cycleStartedAt;
  const inCycle = (ts?: string | null) => isTimestampInCycle(ts, cycleStartedAt);
  const attempts = Array.isArray(state?.attempts) ? state.attempts : [];
  const current = attempts.filter((a) => a && a.kind !== "variant" && inCycle(a.ts));
  const legacyVerdict = cycleStartedAt ? undefined : state?.lastCheck?.verdict;
  const skipped = current.some((a) => a.verdict === "skipped") ||
    (!cycleStartedAt && (state?.skipped === true || legacyVerdict === "skipped"));
  const checked = current.some((a) => NOTION_CHECK_VERDICTS.has(a.verdict)) ||
    (legacyVerdict !== undefined && NOTION_CHECK_VERDICTS.has(legacyVerdict));

  const ranTests = (report?: Partial<TestRunRecord> & { total?: number; updatedAt?: string } | null) => {
    if (typeof report?.allPassed !== "boolean") return false;
    const total = report.totalCount ?? report.total;
    return (total == null || (Number.isFinite(total) && total > 0)) && inCycle(report.ts || report.updatedAt);
  };
  const runs = Array.isArray(state?.testRuns) ? state.testRuns : [];
  const reviews = Array.isArray(state?.reviews) ? state.reviews : [];
  const attempted = checked || (isPrg && (
    runs.some(ranTests) || ranTests(state?.lastTestReport) ||
    reviews.some((r) => (r?.verdict === "pass" || r?.verdict === "revise") && inCycle(r.at || r.ts))
  ));
  return { attempted, skipped };
}

/**
 * Return true only if the problem's latest review record in the current cycle has verdict "pass"
 * (docs/prg_reviewer_spec.md rule 3: reference solution only after a pass).
 */
export function canShowReferenceSolution(state?: ProblemState | null): boolean {
  const reviews = cycleReviews(state);
  if (reviews.length === 0) return false;
  return reviews[reviews.length - 1].verdict === "pass";
}
