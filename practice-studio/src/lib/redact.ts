import {
  AnswerSpec,
  AttemptRecord,
  CheckResult,
  ChoiceOption,
  CodeExample,
  DrillDocument,
  Problem,
  ProblemState,
  RedactedVariant,
  ReviewFinding,
  ReviewRecord,
  Step,
  TestResult,
  TestRunRecord,
  TestRunReport,
  VariantSessionRecord,
  WorkedExampleVariant,
} from "../types/drill";
import {
  isHiddenTestFailureName,
  maskHiddenTestFailures,
  sanitizeCodeCheckError,
  type ReviewRunLintItem,
  type ReviewRunResult,
  type ReviewRunTypecheckItem,
} from "./codeStatus";
import {
  canRevealVerifiedAnswer,
  canShowReferenceSolution,
  isSubstantiveVerdict,
  isTimestampInCycle,
  sanitizeCheckMessage,
} from "./reviewGuard";
import { cycleAttempts, cycleOriginalAttempts, isInCycle } from "./similarTabs";
import { hasCheckpointHint } from "./studioRules";

/**
 * Secret fields stripped by `redactProblem` / `redactDrill` before sending a drill to the browser:
 *
 * 1. Problem-level fields ALWAYS stripped:
 *    - `hiddenTests`: hidden test cases for PRG execution problems
 *    - `trapValue`: expected trap answer value used by `math_engine.answer_check`
 *    - `trapMutant`: buggy mutant code for PRG trap verification
 *    - `mutants`: list of trap mutant objects (`{ name, code }`)
 *    - `trapDerivation`: derivation/formula of how the trap answer was constructed
 *    - `trapGivens`: intermediate parameters/givens used to construct the trap
 *    - `trapKind`: internal trap classification
 *    - `flawTag`: internal flaw classification tag
 *    - `verify`: verification metadata (`{ source, flaw, trapValue }`)
 *    - `blindSolve`: blind-solver output (`{ setup, strategy, steps, answer, check, reverse, ... }`)
 *    - `review`: reviewer subagent verdict and notes (`{ id, verdict, note }`)
 *    - `contextCheck`: context-check subagent verdict and notes (`{ verdict, note }`)
 *    - `qualityGates`: quality gate audit results (`G1`, `G2`, `G4`, `G6`, `antiLeak`, ...)
 *    - `givens`: template generator givens / intermediate values
 *    - `constants`: template generator constants / intermediate values
 *    - `starterLintExpected`: internal lint gate metadata
 *
 * 2. Problem-level fields stripped UNTIL unlocked by learner `state`:
 *    - `display`, `plainText` (the hidden "Show equation set-up" box and CAS plain-text):
 *      stripped until the problem is checked/answered (`canRevealVerifiedAnswer`) or
 *      explicitly revealed (`setupRevealedBeforeAnswer` / `attempts[].setupRevealed`).
 *    - `steps`, `answerDisplay`, `answerPlain` (step-by-step derivation and verified answer):
 *      stripped until the problem is checked/answered (`canRevealVerifiedAnswer`) or
 *      explicitly revealed (`solutionRevealedBeforeAnswer` / `attempts[].solutionRevealed`).
 *    - `solutionCode` (PRG reference implementation):
 *      stripped until the latest code review record has `verdict === "pass"` (`canShowReferenceSolution`).
 *
 * 3. `answerSpec` fields ALWAYS stripped:
 *    - `value`: expected scalar / expression / interval answer
 *    - `values`: expected tuple / solution_set answer values
 *    - `components`: expected vector components
 *    - `correct`: correct option ID for multiple-choice problems
 *    - `accepted`: list of accepted answer strings
 *    - `tokens`: expected output token sequence for `predict_output` / `code_output`
 *    - `correctLine`: buggy line number for `line_number` / `find_bug`
 *    - `flawExplanation`: explanation of the flaw on `correctLine`
 *    - `trapValue`: trap answer value if present on `answerSpec`
 *    - `flawTag`: flaw tag if present on `answerSpec`
 *
 * 4. `answerSpec.options[]` fields ALWAYS stripped:
 *    - `provenance`: distractor derivation string on multiple-choice options
 */

export const ALWAYS_STRIPPED_PROBLEM_FIELDS = [
  "hiddenTests",
  "trapValue",
  "trapMutant",
  "mutants",
  "trapDerivation",
  "trapGivens",
  "trapKind",
  "flawTag",
  "verify",
  "blindSolve",
  "review",
  "contextCheck",
  "qualityGates",
  "givens",
  "constants",
  "starterLintExpected",
] as const;

export const CONDITIONAL_STRIPPED_PROBLEM_FIELDS = [
  "display",
  "plainText",
  "steps",
  "answerDisplay",
  "answerPlain",
  "solutionCode",
] as const;

export const STRIPPED_ANSWER_SPEC_FIELDS = [
  "value",
  "values",
  "components",
  "correct",
  "accepted",
  "tokens",
  "correctLine",
  "flawExplanation",
  "trapValue",
  "flawTag",
] as const;

export const STRIPPED_OPTION_FIELDS = ["provenance"] as const;

export type RevealPart = "steps" | "display" | "solution";

const DEFAULT_MATH_PLACEHOLDER_BY_TYPE: Record<string, string> = {
  interval: "Enter interval, e.g. [a, b) or (-inf, a) U (a, inf)...",
};

const DEFAULT_MATH_PLACEHOLDER = "Enter final answer (press Enter to check)...";
const DEFAULT_CODE_PLACEHOLDER = "Enter predicted terminal output (press Enter to check)...";

/**
 * Unlock rule for math/code step-by-step derivations (`steps`, `answerDisplay`, `answerPlain`):
 * available once the problem has been checked/answered in the current cycle
 * (`canRevealVerifiedAnswer`) or the learner explicitly revealed steps in the current cycle.
 * When `cycleStartedAt` is active, untimestamped prior-cycle `solutionRevealedBeforeAnswer`
 * does not unlock steps until revealed again in that cycle (`reviewStepsRevealedAt >= cycleStartedAt`).
 */
export function canRevealSteps(state?: ProblemState | null): boolean {
  if (!state) return false;
  if (canRevealVerifiedAnswer(state)) return true;
  if (state.cycleStartedAt) {
    if (
      state.reviewStepsRevealedAt &&
      isInCycle(state.reviewStepsRevealedAt, state.cycleStartedAt)
    ) {
      return true;
    }
    if (cycleOriginalAttempts(state).some((a) => a.solutionRevealed)) return true;
    return false;
  }
  if (state.solutionRevealedBeforeAnswer) return true;
  if (state.reviewStepsRevealedAt) return true;
  if (cycleOriginalAttempts(state).some((a) => a.solutionRevealed)) return true;
  return false;
}

/**
 * Unlock rule for math equation set-up (`display`, `plainText`):
 * available once the problem has been checked/answered in the current cycle
 * (`canRevealVerifiedAnswer`) or the learner explicitly revealed set-up in the current cycle.
 * When `cycleStartedAt` is active, untimestamped prior-cycle `setupRevealedBeforeAnswer`
 * does not unlock display until revealed again in that cycle (`reviewSetupRevealedAt >= cycleStartedAt`).
 */
export function canRevealDisplay(state?: ProblemState | null): boolean {
  if (!state) return false;
  if (canRevealVerifiedAnswer(state)) return true;
  if (state.cycleStartedAt) {
    if (
      state.reviewSetupRevealedAt &&
      isInCycle(state.reviewSetupRevealedAt, state.cycleStartedAt)
    ) {
      return true;
    }
    if (cycleOriginalAttempts(state).some((a) => a.setupRevealed)) return true;
    return false;
  }
  if (state.setupRevealedBeforeAnswer) return true;
  if (state.reviewSetupRevealedAt) return true;
  if (cycleOriginalAttempts(state).some((a) => a.setupRevealed)) return true;
  return false;
}

/**
 * Unlock rule for PRG reference `solutionCode`:
 * available only when `canShowReferenceSolution(state)` is true (latest review verdict is "pass").
 */
export function canRevealSolution(state?: ProblemState | null): boolean {
  return canShowReferenceSolution(state);
}

export function isPartUnlocked(part: RevealPart, state?: ProblemState | null): boolean {
  if (part === "steps") return canRevealSteps(state);
  if (part === "display") return canRevealDisplay(state);
  if (part === "solution") return canRevealSolution(state);
  return false;
}

/** Unlock rule for variant step-by-step derivation: after a substantive attempt in the current cycle or explicit reveal/give-up. */
export function canRevealVariantSteps(
  record?: VariantSessionRecord | null,
  cycleStartedAt?: string | null
): boolean {
  if (!record) return false;
  const attemptsInCycle = cycleAttempts(record.attempts, cycleStartedAt);
  if (attemptsInCycle.some((a) => isSubstantiveVerdict(a?.verdict))) {
    return true;
  }
  if (record.stepsRevealed) {
    if (isTimestampInCycle(record.servedAt, cycleStartedAt)) return true;
  }
  return false;
}

const MAX_PUBLIC_ERROR_LEN = 2000;
const MAX_PUBLIC_NAME_LEN = 500;

function nonNegInt(val: unknown, fallback = 0): number {
  return typeof val === "number" && Number.isFinite(val) && val >= 0 ? Math.floor(val) : fallback;
}

function nonNegNumber(val: unknown, fallback = 0): number {
  return typeof val === "number" && Number.isFinite(val) && val >= 0 ? val : fallback;
}

function boundedText(val: unknown, maxLen: number): string {
  if (typeof val !== "string") return "";
  return val.length > maxLen ? val.slice(0, maxLen) : val;
}

function projectVisibleResults(rawResults: unknown): TestResult[] {
  if (!Array.isArray(rawResults)) return [];
  const cleaned: TestResult[] = [];
  let hiddenFailCount = 0;
  for (const entry of rawResults) {
    if (!entry || typeof entry !== "object") continue;
    const r = entry as Record<string, unknown>;
    const rawName = typeof r.name === "string" ? r.name : "Test case";
    const rawError = typeof r.error === "string" ? r.error : undefined;
    if (isHiddenTestFailureName(rawName) || isHiddenTestFailureName(rawError)) {
      if (r.passed !== true) hiddenFailCount += 1;
      continue;
    }
    const passed = r.passed === true;
    const item: TestResult = {
      name: boundedText(sanitizeCodeCheckError(rawName), MAX_PUBLIC_NAME_LEN) || "Test case",
      passed,
    };
    if (typeof r.durationMs === "number" && Number.isFinite(r.durationMs) && r.durationMs >= 0) {
      item.durationMs = Math.round(r.durationMs * 100) / 100;
    }
    if (!passed && rawError && rawError.trim()) {
      const safeErr = boundedText(sanitizeCodeCheckError(rawError), MAX_PUBLIC_ERROR_LEN);
      if (safeErr) item.error = safeErr;
    }
    cleaned.push(item);
  }
  if (hiddenFailCount > 0) {
    cleaned.push({
      name:
        hiddenFailCount === 1
          ? "1 hidden check failed"
          : `${hiddenFailCount} hidden checks failed`,
      passed: false,
    });
  }
  return cleaned;
}

export interface ProjectTestRunReportOptions {
  trustedHiddenTotal?: number;
  trustedVisibleCount?: number;
  recomputeFromRunnerResults?: boolean;
}

/**
 * Project a raw or persisted test-run report onto the allowlisted `TestRunReport` schema:
 * drops `rawOutput` and any unknown/extra fields, masks hidden test failures, sanitizes
 * visible error strings, and enforces consistent counts.
 */
export function projectTestRunReport(
  raw: unknown,
  options: ProjectTestRunReportOptions = {}
): TestRunReport {
  const rec = raw && typeof raw === "object" ? (raw as Record<string, unknown>) : {};
  const visibleResults = projectVisibleResults(rec.visibleResults);
  const hiddenTotal =
    options.trustedHiddenTotal !== undefined
      ? nonNegInt(options.trustedHiddenTotal, 0)
      : nonNegInt(rec.hiddenTotal, 0);
  const hiddenPassed = Math.min(nonNegInt(rec.hiddenPassed, 0), hiddenTotal);
  const executionTimeMs = nonNegNumber(rec.executionTimeMs, 0);
  const ts = typeof rec.ts === "string" && rec.ts.trim() ? rec.ts.trim() : undefined;

  if (options.recomputeFromRunnerResults) {
    const hasFailureEntry = visibleResults.some((r) => !r.passed);
    if (
      options.trustedVisibleCount !== undefined &&
      visibleResults.length !== options.trustedVisibleCount
    ) {
      const totalCount = options.trustedVisibleCount + hiddenTotal;
      // Preserve a runner-produced failure/timeout diagnostic when the runner already failed,
      // but never allow an incomplete report to claim any passing count or allPassed=true.
      const failureResults: TestResult[] =
        hasFailureEntry && rec.allPassed !== true
          ? visibleResults
              .filter((r) => !r.passed)
              .map((r) => ({ ...r, passed: false }))
          : [
              {
                name: "Execution failure",
                passed: false,
                error: "Test runner returned an incomplete report",
              },
            ];
      return {
        allPassed: false,
        score: 0,
        passedCount: 0,
        totalCount,
        visibleResults: failureResults,
        hiddenPassed: 0,
        hiddenTotal,
        executionTimeMs,
        ...(ts ? { ts } : {}),
      };
    }
    const visiblePassed = visibleResults.filter((r) => r.passed).length;
    const totalCount = visibleResults.length + hiddenTotal;
    const passedCount = visiblePassed + hiddenPassed;
    const allPassed = totalCount > 0 && passedCount === totalCount;
    const score = totalCount > 0 ? Math.round((passedCount / totalCount) * 100) / 100 : 0;
    return {
      allPassed,
      score,
      passedCount,
      totalCount,
      visibleResults,
      hiddenPassed,
      hiddenTotal,
      executionTimeMs,
      ...(ts ? { ts } : {}),
    };
  }

  const totalCount = nonNegInt(rec.totalCount, visibleResults.length + hiddenTotal);
  const passedCount = Math.min(nonNegInt(rec.passedCount, 0), totalCount);
  const hasVisibleFail = visibleResults.some((r) => !r.passed);
  const allPassed =
    rec.allPassed === true &&
    totalCount > 0 &&
    passedCount === totalCount &&
    !hasVisibleFail &&
    hiddenPassed === hiddenTotal;
  const rawScore = nonNegNumber(rec.score, totalCount > 0 ? passedCount / totalCount : 0);
  const score = Math.min(1, Math.round(rawScore * 100) / 100);

  return {
    allPassed,
    score,
    passedCount,
    totalCount,
    visibleResults,
    hiddenPassed,
    hiddenTotal,
    executionTimeMs,
    ...(ts ? { ts } : {}),
  };
}

function projectLintItems(rawLint: unknown): ReviewRunLintItem[] {
  if (!Array.isArray(rawLint)) return [];
  const out: ReviewRunLintItem[] = [];
  for (const entry of rawLint) {
    if (!entry || typeof entry !== "object") continue;
    const item = entry as Record<string, unknown>;
    const cleanFile =
      typeof item.file === "string" && item.file.trim()
        ? sanitizeCodeCheckError(item.file)
        : undefined;
    out.push({
      ...(cleanFile ? { file: cleanFile } : {}),
      rule: typeof item.rule === "string" && item.rule.trim() ? item.rule.trim() : "lint",
      line: nonNegInt(item.line, 0),
      message: boundedText(sanitizeCodeCheckError(typeof item.message === "string" ? item.message : ""), MAX_PUBLIC_ERROR_LEN),
    });
  }
  return out;
}

function projectTypecheckItems(rawTypes: unknown): ReviewRunTypecheckItem[] {
  if (!Array.isArray(rawTypes)) return [];
  const out: ReviewRunTypecheckItem[] = [];
  for (const entry of rawTypes) {
    if (!entry || typeof entry !== "object") continue;
    const item = entry as Record<string, unknown>;
    const cleanFile =
      typeof item.file === "string" && item.file.trim()
        ? sanitizeCodeCheckError(item.file)
        : undefined;
    out.push({
      ...(cleanFile ? { file: cleanFile } : {}),
      line: nonNegInt(item.line, 0),
      message: boundedText(sanitizeCodeCheckError(typeof item.message === "string" ? item.message : ""), MAX_PUBLIC_ERROR_LEN),
    });
  }
  return out;
}

function projectReviewFindings(rawFindings: unknown): ReviewFinding[] {
  if (!Array.isArray(rawFindings)) return [];
  const out: ReviewFinding[] = [];
  for (const entry of rawFindings) {
    if (!entry || typeof entry !== "object") continue;
    const f = entry as Record<string, unknown>;
    const rawDisputed =
      f.disputed && typeof f.disputed === "object" ? (f.disputed as Record<string, unknown>) : null;
    const disputed = rawDisputed
      ? {
          reason: typeof rawDisputed.reason === "string" ? rawDisputed.reason : "",
          issueId: typeof rawDisputed.issueId === "string" ? rawDisputed.issueId : "",
        }
      : undefined;
    out.push({
      check: typeof f.check === "string" ? f.check : "",
      severity: f.severity === "must" ? "must" : "should",
      line: nonNegInt(f.line, 0),
      note: typeof f.note === "string" ? f.note : "",
      ...(typeof f.hint === "string" && f.hint ? { hint: f.hint } : {}),
      ...(disputed ? { disputed } : {}),
    });
  }
  return out;
}

/** Project a persisted `ReviewRecord` onto the allowlisted schema and mask hidden failures. */
export function projectReviewRecord(raw: unknown): ReviewRecord | null {
  if (!raw || typeof raw !== "object") return null;
  const rev = raw as Record<string, unknown>;
  const rawTests =
    rev.tests && typeof rev.tests === "object" ? (rev.tests as Record<string, unknown>) : {};
  const total = nonNegInt(rawTests.total, 0);
  const passed = Math.min(nonNegInt(rawTests.passed, 0), total);
  const failed = Array.isArray(rawTests.failed)
    ? maskHiddenTestFailures(rawTests.failed.filter((x): x is string => typeof x === "string")).map(
        (entry) => sanitizeCodeCheckError(entry)
      )
    : [];

  return {
    at: typeof rev.at === "string" ? rev.at : "",
    ...(typeof rev.ts === "string" && rev.ts ? { ts: rev.ts } : {}),
    attempt: nonNegInt(rev.attempt, 0),
    codeHash: typeof rev.codeHash === "string" ? rev.codeHash : "",
    code: typeof rev.code === "string" ? rev.code : "",
    tests: { passed, total, failed },
    lint: projectLintItems(rev.lint),
    typecheck: projectTypecheckItems(rev.typecheck),
    findings: projectReviewFindings(rev.findings),
    verdict: rev.verdict === "pass" ? "pass" : "revise",
    explain: typeof rev.explain === "string" ? rev.explain : null,
    ...(typeof rev.explainQuestion === "string" || rev.explainQuestion === null
      ? { explainQuestion: rev.explainQuestion }
      : {}),
  };
}

/**
 * Project a `/api/review-run` runner payload onto the strict allowlisted `ReviewRunResult` schema,
 * dropping unknown/extra fields and masking hidden test names.
 */
export function projectReviewRunResponse(
  raw: unknown,
  context: {
    drillId: string;
    problemId: string;
    isLab: boolean;
    testReport?: TestRunReport | null;
  }
): ReviewRunResult {
  const rec = raw && typeof raw === "object" ? (raw as Record<string, unknown>) : {};
  const rawTests =
    rec.tests && typeof rec.tests === "object" ? (rec.tests as Record<string, unknown>) : {};
  const total = nonNegInt(rawTests.total, 0);
  const passed = Math.min(nonNegInt(rawTests.passed, 0), total);
  const failed = Array.isArray(rawTests.failed)
    ? maskHiddenTestFailures(rawTests.failed.filter((x): x is string => typeof x === "string")).map(
        (entry) => sanitizeCodeCheckError(entry)
      )
    : [];

  const lint = projectLintItems(rec.lint);
  const typecheck = projectTypecheckItems(rec.typecheck);
  const checks = Array.isArray(rec.checks)
    ? rec.checks
        .filter((c): c is Record<string, unknown> => Boolean(c && typeof c === "object"))
        .map((c) => {
          const accepted = Array.isArray(c.accepted)
            ? c.accepted.filter((x): x is string => typeof x === "string")
            : undefined;
          return {
            id: typeof c.id === "string" ? c.id : "",
            check: typeof c.check === "string" ? c.check : "",
            why: typeof c.why === "string" ? c.why : "",
            severity: (c.severity === "must" ? "must" : "should") as "must" | "should",
            ...(accepted ? { accepted } : {}),
          };
        })
    : undefined;

  const archetypeKey =
    typeof rec.archetypeKey === "string"
      ? rec.archetypeKey
      : rec.archetypeKey === null
      ? null
      : undefined;
  const level =
    typeof rec.level === "number" && Number.isFinite(rec.level)
      ? rec.level
      : rec.level === null
      ? null
      : undefined;
  const codeHash = typeof rec.codeHash === "string" ? rec.codeHash : undefined;

  return {
    ...(context.testReport ? { testReport: projectTestRunReport(context.testReport) } : {}),
    drillId: context.drillId,
    problemId: context.problemId,
    ...(context.isLab ? { labId: context.drillId, milestone: context.problemId } : {}),
    ...(archetypeKey !== undefined ? { archetypeKey } : {}),
    ...(level !== undefined ? { level } : {}),
    ...(codeHash !== undefined ? { codeHash } : {}),
    tests: { passed, total, failed },
    lint,
    typecheck,
    types: typecheck,
    ...(checks !== undefined ? { checks } : {}),
  };
}

function projectCheckResultForClient(raw: unknown): CheckResult | null {
  if (!raw || typeof raw !== "object") return null;
  const c = raw as Record<string, unknown>;
  const verdict = typeof c.verdict === "string" ? (c.verdict as CheckResult["verdict"]) : "incorrect";
  const message = sanitizeCheckMessage(verdict, typeof c.message === "string" ? c.message : "");
  const components = Array.isArray(c.components)
    ? c.components
        .filter((x): x is Record<string, unknown> => Boolean(x && typeof x === "object"))
        .map((x) => ({ label: String(x.label ?? ""), ok: Boolean(x.ok) }))
    : [];
  const diagnostics = Array.isArray(c.diagnostics)
    ? c.diagnostics
        .filter((x): x is Record<string, unknown> => Boolean(x && typeof x === "object"))
        .map((x) => ({ code: String(x.code ?? ""), message: String(x.message ?? "") }))
    : [];
  return {
    ...(typeof c.eventId === "string" ? { eventId: c.eventId } : {}),
    ...(typeof c.ts === "string" ? { ts: c.ts } : {}),
    verdict,
    message,
    components,
    diagnostics,
    ...(typeof c.trapMatched === "boolean" ? { trapMatched: c.trapMatched } : {}),
  };
}

function projectAttemptRecord(
  raw: unknown,
  { stripMatchedTrap }: { stripMatchedTrap: boolean }
): AttemptRecord | null {
  if (!raw || typeof raw !== "object") return null;
  const a = raw as Record<string, unknown>;
  const out: AttemptRecord = {
    ...(typeof a.eventId === "string" && a.eventId ? { eventId: a.eventId } : {}),
    ...(typeof a.hintsUsed === "boolean" ? { hintsUsed: a.hintsUsed } : {}),
    input: typeof a.input === "string" ? a.input : "",
    ts: typeof a.ts === "string" ? a.ts : "",
    verdict: typeof a.verdict === "string" ? a.verdict : "",
    ...(Array.isArray(a.diagnosticCodes)
      ? { diagnosticCodes: a.diagnosticCodes.filter((c): c is string => typeof c === "string") }
      : {}),
    ...(!stripMatchedTrap && typeof a.matchedTrap === "string" && a.matchedTrap
      ? { matchedTrap: a.matchedTrap }
      : {}),
    ...(a.kind === "variant" ? { kind: "variant" } : {}),
    ...(a.setupRevealed === true ? { setupRevealed: true } : {}),
    ...(a.solutionRevealed === true ? { solutionRevealed: true } : {}),
    ...(a.exampleViewed === true ? { exampleViewed: true } : {}),
  };
  return out;
}

/**
 * Strip bank `variantId`s, `variantsSeen`/`variantsAttempted`, legacy `activeVariant`,
 * and variant trap tags from `ProblemState` before sending it to the browser so
 * method/archetype names never leak, and sanitize nested check/test/review history.
 */
export function redactProblemStateForClient(
  state?: ProblemState | null
): ProblemState | undefined {
  if (!state || typeof state !== "object") return undefined;
  const copy: ProblemState = { ...state };
  delete copy.reviewBaseLevel;
  delete copy.variantsSeen;
  delete copy.variantsAttempted;
  delete (copy as unknown as Record<string, unknown>).activeVariant;
  if (state.variants && typeof state.variants === "object") {
    const cleanVariants: Record<string, VariantSessionRecord> = {};
    for (const [token, rec] of Object.entries(state.variants)) {
      if (!rec || typeof rec !== "object") continue;
      const cleanAttempts: AttemptRecord[] = Array.isArray(rec.attempts)
        ? rec.attempts
            .map((a) => projectAttemptRecord(a, { stripMatchedTrap: true }))
            .filter((a): a is AttemptRecord => a !== null)
        : [];
      cleanVariants[token] = {
        role: rec.role === "example" ? "example" : "try",
        attempts: cleanAttempts,
        ...(typeof rec.hintsRevealed === "number" ? { hintsRevealed: rec.hintsRevealed } : {}),
        ...(rec.setupRevealed ? { setupRevealed: true } : {}),
        ...(rec.stepsRevealed ? { stepsRevealed: true } : {}),
        ...(typeof rec.durationMs === "number" ? { durationMs: rec.durationMs } : {}),
        servedAt: rec.servedAt,
      };
    }
    copy.variants = cleanVariants;
  }
  if (Array.isArray(copy.attempts)) {
    copy.attempts = copy.attempts
      .map((a) => projectAttemptRecord(a, { stripMatchedTrap: false }))
      .filter((a): a is AttemptRecord => a !== null);
  }
  if (copy.lastCheck && typeof copy.lastCheck === "object") {
    copy.lastCheck = projectCheckResultForClient(copy.lastCheck);
  }
  if (copy.lastTestReport && typeof copy.lastTestReport === "object") {
    copy.lastTestReport = projectTestRunReport(copy.lastTestReport);
  }
  if (Array.isArray(copy.testRuns)) {
    copy.testRuns = copy.testRuns
      .filter((tr): tr is TestRunRecord => Boolean(tr && typeof tr === "object"))
      .map((tr) => ({
        ts: typeof tr.ts === "string" ? tr.ts : "",
        allPassed: Boolean(tr.allPassed),
        ...(typeof tr.passedCount === "number" ? { passedCount: nonNegInt(tr.passedCount, 0) } : {}),
        ...(typeof tr.totalCount === "number" ? { totalCount: nonNegInt(tr.totalCount, 0) } : {}),
      }));
  }
  if (Array.isArray(copy.reviews)) {
    copy.reviews = copy.reviews
      .map((rev) => projectReviewRecord(rev))
      .filter((rev): rev is ReviewRecord => rev !== null);
  }
  return copy;
}

export function extractRevealedPart(
  problem: Partial<Problem>,
  part: RevealPart
):
  | { part: "steps"; steps: Step[]; answerDisplay: string; answerPlain: string }
  | { part: "display"; display: string; plainText: string }
  | { part: "solution"; solutionCode: string } {
  if (part === "steps") {
    return {
      part: "steps",
      steps: Array.isArray(problem.steps) ? problem.steps : [],
      answerDisplay: problem.answerDisplay ?? "",
      answerPlain: problem.answerPlain ?? "",
    };
  }
  if (part === "display") {
    return {
      part: "display",
      display: problem.display ?? "",
      plainText: problem.plainText ?? "",
    };
  }
  return {
    part: "solution",
    solutionCode: problem.solutionCode ?? "",
  };
}

function collectSecretAnswerTokens(problem: Partial<Problem>): string[] {
  const acceptedList: string[] = [];
  const pushToken = (val: unknown) => {
    if (val === undefined || val === null) return;
    const s = String(val).toLowerCase().trim();
    if (s.length >= 2) {
      acceptedList.push(s);
    }
  };

  const spec = problem.answerSpec;
  if (spec) {
    if (Array.isArray(spec.accepted)) {
      spec.accepted.forEach(pushToken);
    }
    if (spec.value !== undefined) {
      pushToken(spec.value);
    }
    if (Array.isArray(spec.values)) {
      spec.values.forEach(pushToken);
    }
    if (Array.isArray(spec.tokens)) {
      spec.tokens.forEach(pushToken);
    }
  }
  if (problem.answerPlain) {
    pushToken(problem.answerPlain);
  }
  if (problem.answerDisplay) {
    pushToken(problem.answerDisplay);
    const raw = String(problem.answerDisplay)
      .replace(/[\$\\]/g, "")
      .replace(/\\[a-zA-Z]+/g, "")
      .replace(/\^\{\\circ\}/g, "")
      .trim()
      .toLowerCase();
    if (raw.length >= 2) {
      acceptedList.push(raw);
    }
  }
  return acceptedList;
}

/**
 * Scrub `inputHint` on the server against secret answer fields so no answer leak reaches the client.
 */
export function sanitizeInputHint(problem: Partial<Problem>): string | undefined {
  const hint = problem.inputHint;
  if (!hint || typeof hint !== "string") return undefined;

  const acceptedList = collectSecretAnswerTokens(problem);
  const lowerHint = hint.toLowerCase();
  const hasLeak = acceptedList.some((ans) => lowerHint.includes(ans));
  if (!hasLeak) return hint;

  const stripped = hint.replace(/\s*\([^)]*e\.g\.[^)]*\)/gi, "").trim();
  if (stripped && !acceptedList.some((ans) => stripped.toLowerCase().includes(ans))) {
    return stripped;
  }
  return undefined;
}

function isCodeProblem(problem: Partial<Problem>, subject?: "MATH" | "PRG"): boolean {
  return (
    subject === "PRG" ||
    Boolean(problem.codeSnippet) ||
    Boolean(problem.workspaceFile) ||
    problem.codeType === "predict-output" ||
    problem.codeType === "find-bug" ||
    ["code_output", "predict_output", "line_number", "find_bug"].includes(
      problem.answerSpec?.type || ""
    )
  );
}

/**
 * Compute the safe input placeholder on the server so the client does not need
 * `answerSpec.accepted`, `answerPlain`, or `answerDisplay`.
 */
export function computeSafePlaceholder(
  problem: Partial<Problem>,
  subject?: "MATH" | "PRG"
): string {
  const fallback = isCodeProblem(problem, subject)
    ? DEFAULT_CODE_PLACEHOLDER
    : (problem.answerSpec?.type && DEFAULT_MATH_PLACEHOLDER_BY_TYPE[problem.answerSpec.type]) ||
      DEFAULT_MATH_PLACEHOLDER;

  const safeHint = sanitizeInputHint(problem);
  return safeHint || fallback;
}

/**
 * Strip secret answer fields from `answerSpec`, keeping only `type`, choice `options`
 * (without `provenance`), and non-secret format/unit/variable metadata.
 */
function redactAnswerSpec(spec?: AnswerSpec | null): AnswerSpec {
  if (!spec || typeof spec !== "object") {
    return { type: "text" };
  }
  const copy: Record<string, unknown> = { ...spec };
  for (const field of STRIPPED_ANSWER_SPEC_FIELDS) {
    delete copy[field];
  }
  if (Array.isArray(spec.options)) {
    copy.options = spec.options.map((opt) => {
      if (!opt || typeof opt !== "object") return opt;
      const optCopy: Record<string, unknown> = { ...(opt as ChoiceOption) };
      for (const field of STRIPPED_OPTION_FIELDS) {
        delete optCopy[field];
      }
      return optCopy as unknown as ChoiceOption;
    });
  }
  return copy as unknown as AnswerSpec;
}

/**
 * Pure function that removes secret answer material from a single problem according to `state`.
 */
export function redactProblem(
  problem: Problem,
  state?: ProblemState | null,
  subject?: "MATH" | "PRG"
): Problem {
  const effectiveState = state !== undefined ? state : problem.state;
  const safeHint = sanitizeInputHint(problem);
  const placeholder = computeSafePlaceholder(problem, subject);
  const hasSetup = Boolean(problem.hasSetup || problem.display || problem.plainText);
  const hiddenTestCount =
    typeof problem.hiddenTestCount === "number"
      ? problem.hiddenTestCount
      : Array.isArray(problem.hiddenTests)
      ? problem.hiddenTests.length
      : undefined;

  const raw: Record<string, unknown> = { ...problem };

  for (const field of ALWAYS_STRIPPED_PROBLEM_FIELDS) {
    delete raw[field];
  }

  if (!canRevealDisplay(effectiveState)) {
    delete raw.display;
    delete raw.plainText;
  }

  if (!canRevealSteps(effectiveState)) {
    delete raw.steps;
    delete raw.answerDisplay;
    delete raw.answerPlain;
  }

  if (!canRevealSolution(effectiveState)) {
    delete raw.solutionCode;
  }

  if (problem.answerSpec) {
    raw.answerSpec = redactAnswerSpec(problem.answerSpec);
  }
  if (Array.isArray(problem.examples)) {
    raw.examples = problem.examples.map((ex) => {
      if (!ex || typeof ex !== "object") return ex;
      const sanitized: CodeExample = {
        input: ex.input,
        output: ex.output,
        ...(ex.explanation !== undefined ? { explanation: ex.explanation } : {}),
      };
      return sanitized;
    });
  }
  raw.placeholder = placeholder;
  raw.hasSetup = hasSetup;

  if (safeHint !== undefined) {
    raw.inputHint = safeHint;
  } else {
    delete raw.inputHint;
  }

  if (hiddenTestCount !== undefined) {
    raw.hiddenTestCount = hiddenTestCount;
  }

  if (state !== undefined) {
    if (state === null) {
      delete raw.state;
    } else {
      raw.state = redactProblemStateForClient(state);
    }
  } else if (raw.state && typeof raw.state === "object") {
    raw.state = redactProblemStateForClient(raw.state as ProblemState);
  }

  return raw as unknown as Problem;
}

/**
 * Pure function that redacts every problem in a drill document before sending it to the browser.
 */
export function redactDrill<T extends DrillDocument>(doc: T): T {
  const subject: "MATH" | "PRG" =
    doc.subject === "PRG" || String(doc.unitCode || "").startsWith("PRG-") ? "PRG" : "MATH";
  return {
    ...doc,
    problems: Array.isArray(doc.problems)
      ? doc.problems.map((p) => redactProblem(p, p.state, subject))
      : [],
  };
}

/**
 * Pure function that prepares a single problem for a fresh Daily Review attempt:
 * resets the in-session state to unattempted (preserving only `revisitNote`) so no steps,
 * answers, equation set-up, or reference solutions are leaked from past attempts, and
 * strips trap tags and archetype keys before the learner answers.
 */
export function redactProblemForReview(
  problem: Problem,
  subject?: "MATH" | "PRG",
  cycleStartedAt?: string
): Problem {
  const startedAt =
    typeof cycleStartedAt === "string" && cycleStartedAt.trim()
      ? cycleStartedAt.trim()
      : new Date().toISOString();
  const cleanState: ProblemState = {
    userInput: "",
    userCode: problem.starterCode || problem.codeSnippet || "",
    score: null,
    divergedStep: null,
    mistakes: [],
    mistakeNote: "",
    ...(problem.state?.revisitNote ? { revisitNote: problem.state.revisitNote } : {}),
    skipped: false,
    lastCheck: null,
    lastTestReport: null,
    attempts: [],
    hintsRevealed: 0,
    setupRevealedBeforeAnswer: false,
    solutionRevealedBeforeAnswer: false,
    durationMs: 0,
    cycleStartedAt: startedAt,
  };

  const base = redactProblem(problem, cleanState, subject) as unknown as Record<string, unknown>;
  delete base.commonTrapTag;
  delete base.archetypeKey;
  delete base.archetype;
  base.templateKey = "";

  if (base.answerSpec && typeof base.answerSpec === "object") {
    const specCopy: Record<string, unknown> = { ...(base.answerSpec as Record<string, unknown>) };
    delete specCopy.commonTrapTag;
    if (Array.isArray(specCopy.options)) {
      specCopy.options = (specCopy.options as Array<Record<string, unknown>>).map((opt) => {
        if (!opt || typeof opt !== "object") return opt;
        const optCopy: Record<string, unknown> = { ...opt };
        delete optCopy.trapTag;
        delete optCopy.tag;
        return optCopy;
      });
    }
    base.answerSpec = specCopy;
  }

  return base as unknown as Problem;
}

/**
 * Pure function that redacts every problem in a drill document for a fresh Daily Review session.
 */
export function redactDrillForReview<T extends DrillDocument>(
  doc: T,
  cycleStartedAt?: string
): T {
  const subject: "MATH" | "PRG" =
    doc.subject === "PRG" || String(doc.unitCode || "").startsWith("PRG-") ? "PRG" : "MATH";
  const startedAt =
    typeof cycleStartedAt === "string" && cycleStartedAt.trim()
      ? cycleStartedAt.trim()
      : new Date().toISOString();
  return {
    ...doc,
    problems: Array.isArray(doc.problems)
      ? doc.problems.map((p) => redactProblemForReview(p, subject, startedAt))
      : [],
    ...(doc.sessionSummary
      ? {
          sessionSummary: {
            ...doc.sessionSummary,
            mistakeCategories: [],
            divergedStepsSummary: "",
          },
        }
      : {}),
  };
}

/**
 * Zero-leak redaction for a bank variant served in `mode=try`:
 * strips every answer, step, display/plainText, trap, archetype, bank `variantId`, and internal metadata field.
 * Uses only the opaque per-problem `token` (e.g. "v1") as client identifier.
 */
export function redactVariantForTry(
  variant: Record<string, unknown>,
  token: string
): RedactedVariant {
  const safeToken = String(token || "v1");
  const asProblem = {
    ...(variant as unknown as Problem),
    id: safeToken,
    templateKey: "",
  };
  const redacted = redactProblem(asProblem, null, "MATH") as unknown as Record<string, unknown>;

  // Strip archetype / trap / bank ID / internal identifiers so mode=try never leaks method or trap.
  delete redacted.variantId;
  delete redacted.commonTrapTag;
  delete redacted.archetypeKey;
  delete redacted.sourceArchetype;
  delete redacted.archetype;
  delete redacted.templateKey;
  delete redacted.fingerprint;
  delete redacted.references;
  delete redacted.referenceBadges;

  if (redacted.answerSpec && typeof redacted.answerSpec === "object") {
    const specCopy: Record<string, unknown> = { ...(redacted.answerSpec as Record<string, unknown>) };
    delete specCopy.commonTrapTag;
    if (Array.isArray(specCopy.options)) {
      specCopy.options = (specCopy.options as Array<Record<string, unknown>>).map((opt) => {
        if (!opt || typeof opt !== "object") return opt;
        const optCopy: Record<string, unknown> = { ...opt };
        delete optCopy.trapTag;
        delete optCopy.tag;
        return optCopy;
      });
    }
    redacted.answerSpec = specCopy;
  }

  const hasHint = hasCheckpointHint(
    typeof variant.checkpointHint === "string" ? variant.checkpointHint : undefined
  );

  return {
    token: safeToken,
    id: safeToken,
    level: typeof redacted.level === "number" ? redacted.level : 1,
    ...(typeof redacted.levelLabel === "string" ? { levelLabel: redacted.levelLabel } : {}),
    ...(typeof redacted.category === "string" ? { category: redacted.category } : {}),
    ...(typeof redacted.context === "string" && redacted.context ? { context: redacted.context } : {}),
    prompt: String(redacted.prompt || ""),
    ...(redacted.figure ? { figure: redacted.figure as Problem["figure"] } : {}),
    ...(redacted.visual ? { visual: redacted.visual as Problem["visual"] } : {}),
    answerSpec: (redacted.answerSpec as AnswerSpec) || { type: "number" },
    ...(typeof redacted.inputHint === "string" ? { inputHint: redacted.inputHint } : {}),
    ...(typeof redacted.placeholder === "string" ? { placeholder: redacted.placeholder } : {}),
    hasSetup: Boolean(redacted.hasSetup),
    hasHint,
  };
}

/**
 * Format a bank variant as a fully solved worked example (`mode=example`),
 * returning only learner-facing prompt, figure, final answer, and steps with explain
 * under an opaque per-problem `token` (never leaking bank `variantId` or archetype).
 */
export function formatWorkedExampleVariant(
  variant: Record<string, unknown>,
  token: string
): WorkedExampleVariant {
  const safeToken = String(token || "v1");
  const rawSteps = Array.isArray(variant.steps) ? (variant.steps as Array<Record<string, unknown>>) : [];
  const steps: Step[] = rawSteps
    .filter((st) => st && typeof st === "object")
    .map((st) => ({
      ...(typeof st.latex === "string" ? { latex: st.latex } : {}),
      explain: typeof st.explain === "string" ? st.explain : "",
    }));

  return {
    token: safeToken,
    id: safeToken,
    level: typeof variant.level === "number" ? variant.level : 1,
    ...(typeof variant.levelLabel === "string" ? { levelLabel: variant.levelLabel } : {}),
    ...(typeof variant.category === "string" ? { category: variant.category } : {}),
    ...(typeof variant.context === "string" && variant.context ? { context: variant.context } : {}),
    prompt: String(variant.prompt || ""),
    ...(variant.figure ? { figure: variant.figure as Problem["figure"] } : {}),
    ...(variant.visual ? { visual: variant.visual as Problem["visual"] } : {}),
    answerDisplay: String(variant.answerDisplay ?? variant.answerPlain ?? ""),
    answerPlain: String(variant.answerPlain ?? ""),
    steps,
  };
}
