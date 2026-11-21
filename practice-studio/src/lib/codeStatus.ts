import type { Problem, ProblemState, ReviewRecord } from "../types/drill";
import { cycleReviews } from "./reviewGuard";
import { isAwaitingReview, scoreProblem } from "./scoring";
import { getReviewRequest } from "./studioRules";

export type LayerCheckStatus = "pass" | "fail" | "not_run";
export type ReviewStatus = "pass" | "revise" | "not_requested";
export type MilestoneTileState = "pass" | "awaiting_review" | "revise" | "not_started";
export type MilestoneStepperState = "passed" | "regressed" | "notYet";
export type StatusSymbol = "✓" | "✗" | "–";
export type PrimaryCodeActionKind = "open_vscode" | "copy_review" | "next_problem";

export interface ReviewRunTests {
  passed: number;
  total: number;
  failed: string[];
}

export interface ReviewRunLintItem {
  file?: string;
  rule: string;
  line: number;
  message: string;
}

export interface ReviewRunTypecheckItem {
  file?: string;
  line: number;
  message: string;
}

export interface ReviewRunResult {
  drillId: string;
  problemId: string;
  labId?: string;
  milestone?: string;
  archetypeKey?: string | null;
  level?: number | null;
  codeHash?: string;
  tests: ReviewRunTests;
  lint: ReviewRunLintItem[];
  typecheck: ReviewRunTypecheckItem[];
  types?: ReviewRunTypecheckItem[];
  checks?: Array<{
    id: string;
    check: string;
    why: string;
    severity: "must" | "should";
    accepted?: string[];
  }>;
}

export interface CodeLayeredStatus {
  tests: LayerCheckStatus;
  lint: LayerCheckStatus;
  types: LayerCheckStatus;
  review: ReviewStatus;
  testsSymbol: StatusSymbol;
  lintSymbol: StatusSymbol;
  typesSymbol: StatusSymbol;
  reviewSymbol: StatusSymbol;
  reviewLabel: "not requested" | "revise" | "pass";
  testsCount?: { passed: number; total: number };
  failures: string[];
}

export interface PrimaryCodeAction {
  kind: PrimaryCodeActionKind;
  label: "Open in VS Code" | "Copy review request" | "Next problem";
  reviewCommand?: string;
}

export interface IdeLinks {
  workspaceDir: string;
  filename: string;
  vscodeFolderUrl: string;
  vscodeUrl?: string;
}

const TS_CODE_RE = /^(TS\d+):\s*(.*)$/;

const MISSING_LINT_TOOLS_RE =
  /LintToolsMissingError|Lint toolkit not installed|TypeScript compiler not installed|Vitest is missing|tools[/\\]lint[/\\]node_modules|run [`'"]?npm ci[`'"]? in tools[/\\]lint/i;

const REPO_REL_PATH_RE =
  /(?:file:\/\/)?(?:\/[^\s:"'()<>`]+)*?\/((?:tools|drills|pilot|labs|src|tests|code_engine|math_engine)\/[^\s:"'()<>`]+)/g;

const WORKTREE_ROOT_RE =
  /(?:file:\/\/)?\/(?:Users|home)\/[^\s:"'()<>`]+\/\.claude\/worktrees\/[^/\s:"'()<>`]+\/?/g;

const USER_HOME_PATH_RE =
  /(?:file:\/\/)?\/(?:Users|home)\/[^/\s:"'()<>`]+(?:\/[^\s:"'()<>`]*)*\/([^\s/:"'()<>`]+)/g;

const TMP_ABS_PATH_RE =
  /(?:file:\/\/)?\/(?:private\/var|var\/folders|tmp)\/(?:[^\s:"'()<>`]*\/)?([^\s/:"'()<>`]+)/g;

const HIDDEN_TEST_NAME_RE =
  /\[(?:[A-Z]\d+-)?HIDDEN(?:-[A-Z]?\d+)?\]|\bHIDDEN[-_](?:T?\d+|TRAP)\b/i;

const HIDDEN_TAG_LINE_RE =
  /^.*(?:\[(?:[A-Z]\d+-)?HIDDEN(?:-[A-Z]?\d+)?\]|\bHIDDEN[-_](?:T?\d+|TRAP)\b).*$/gim;

export function isHiddenTestFailureName(name?: string | null): boolean {
  return typeof name === "string" && HIDDEN_TEST_NAME_RE.test(name);
}

/**
 * Mask any internal hidden-test failure names so learner-facing payloads and UI
 * only reveal how many hidden checks failed, never their names or trap details.
 */
export function maskHiddenTestFailures(failed: ReadonlyArray<string>): string[] {
  const visible: string[] = [];
  let hiddenCount = 0;
  for (const entry of failed) {
    if (isHiddenTestFailureName(entry)) {
      hiddenCount += 1;
    } else if (typeof entry === "string" && entry.trim()) {
      visible.push(entry);
    }
  }
  if (hiddenCount > 0) {
    visible.push(
      hiddenCount === 1
        ? "1 hidden check failed"
        : `${hiddenCount} hidden checks failed`
    );
  }
  return visible;
}

/**
 * Strip absolute machine paths from code check errors and return a concise setup hint
 * when `tools/lint` dependencies are missing.
 */
export function sanitizeCodeCheckError(raw?: string | null): string {
  const msg = typeof raw === "string" ? raw.trim() : "";
  if (!msg) return "";
  if (MISSING_LINT_TOOLS_RE.test(msg)) {
    return "Code check tools aren't set up yet. Run `npm ci` in `tools/lint/`.";
  }
  return msg
    .replace(HIDDEN_TAG_LINE_RE, "hidden check failed")
    .replace(REPO_REL_PATH_RE, "$1")
    .replace(WORKTREE_ROOT_RE, "")
    .replace(USER_HOME_PATH_RE, "$1")
    .replace(TMP_ABS_PATH_RE, "$1");
}

export function layerSymbol(status: LayerCheckStatus | ReviewStatus): StatusSymbol {
  if (status === "pass") return "✓";
  if (status === "fail" || status === "revise") return "✗";
  return "–";
}

export function deriveReviewStatus(reviews?: ReviewRecord[] | null): ReviewStatus {
  if (!reviews || reviews.length === 0) return "not_requested";
  const latest = reviews[reviews.length - 1];
  return latest?.verdict === "pass" ? "pass" : "revise";
}

export function reviewStatusLabel(status: ReviewStatus): "not requested" | "revise" | "pass" {
  if (status === "pass") return "pass";
  if (status === "revise") return "revise";
  return "not requested";
}

export function deriveMilestoneTileState(state?: ProblemState | null): MilestoneTileState {
  const scored = scoreProblem(state, { isPrg: true });
  if (scored.outcome === "correct" || scored.outcome === "assisted") return "pass";
  if (isAwaitingReview(state, { isPrg: true })) return "awaiting_review";
  if (scored.outcome === "wrong") return "revise";
  return "not_started";
}

/**
 * Derive a lab milestone's stepper state from its persisted state and optional live reviewRun:
 * - "passed": latest review verdict is "pass" and all layers (tests, lint, types) are green per deriveCodeStatus
 * - "regressed": review passed before, but the latest test/lint/type run (or latest review) now fails
 * - "notYet": milestone has not passed review yet
 */
export function deriveMilestoneStepperState(
  state?: ProblemState | null,
  reviewRun?: Partial<ReviewRunResult> | null
): MilestoneStepperState {
  const reviews = cycleReviews(state);
  const hasPassedBefore = reviews.some((r) => r.verdict === "pass");
  const status = deriveCodeStatus(state, reviewRun);
  const anyLayerFails =
    status.tests === "fail" || status.lint === "fail" || status.types === "fail";

  const allLayersGreen =
    status.review === "pass" &&
    status.tests === "pass" &&
    status.lint === "pass" &&
    status.types === "pass";

  if (allLayersGreen) {
    return "passed";
  }

  if (hasPassedBefore && (anyLayerFails || status.review === "revise")) {
    return "regressed";
  }

  return "notYet";
}

/** Compute stepper states for a sequence of lab milestones (or their ProblemState objects). */
export function deriveLabMilestoneStates(
  milestones: ReadonlyArray<{ state?: ProblemState | null } | ProblemState | null | undefined>
): MilestoneStepperState[] {
  return milestones.map((item) => {
    if (!item || typeof item !== "object") return "notYet";
    if ("state" in item) {
      return deriveMilestoneStepperState(item.state);
    }
    return deriveMilestoneStepperState(item as ProblemState);
  });
}

export function formatReviewRunFailures(
  reviewRun?: Partial<ReviewRunResult> | null,
  defaultFile = "solution.js"
): string[] {
  if (!reviewRun) return [];
  const fileFallback = defaultFile || "solution.js";
  const lines: string[] = [];

  if (Array.isArray(reviewRun.tests?.failed)) {
    for (const failedName of maskHiddenTestFailures(reviewRun.tests.failed)) {
      lines.push(sanitizeCodeCheckError(`${fileFallback}:0 test ${failedName}`));
    }
  }

  if (Array.isArray(reviewRun.lint)) {
    for (const item of reviewRun.lint) {
      const file = sanitizeCodeCheckError(item.file || fileFallback);
      const line = typeof item.line === "number" ? item.line : 0;
      const rule = item.rule || "lint";
      lines.push(
        sanitizeCodeCheckError(`${file}:${line} ${rule} ${item.message || ""}`.trim())
      );
    }
  }

  const typeItems = Array.isArray(reviewRun.typecheck)
    ? reviewRun.typecheck
    : Array.isArray(reviewRun.types)
    ? reviewRun.types
    : [];

  for (const item of typeItems) {
    const file = sanitizeCodeCheckError(item.file || fileFallback);
    const line = typeof item.line === "number" ? item.line : 0;
    const msg = (item.message || "").trim();
    const match = TS_CODE_RE.exec(msg);
    if (match) {
      lines.push(sanitizeCodeCheckError(`${file}:${line} ${match[1]} ${match[2]}`.trim()));
    } else {
      lines.push(sanitizeCodeCheckError(`${file}:${line} tsc ${msg}`.trim()));
    }
  }

  return lines;
}

export function deriveCodeStatus(
  state?: ProblemState | null,
  reviewRun?: Partial<ReviewRunResult> | null,
  defaultFile = "solution.js"
): CodeLayeredStatus {
  const activeReviews = cycleReviews(state);
  const review = deriveReviewStatus(activeReviews);
  const latestReview =
    activeReviews.length > 0 ? activeReviews[activeReviews.length - 1] : undefined;

  let tests: LayerCheckStatus = "not_run";
  let testsCount: { passed: number; total: number } | undefined;

  const latestReviewAt = latestReview ? latestReview.at || latestReview.ts || "" : "";
  const reportTs = state?.lastTestReport?.ts || "";
  const reviewTestsNewerThanReport = Boolean(
    latestReview?.tests &&
      typeof latestReview.tests.total === "number" &&
      reportTs &&
      latestReviewAt &&
      latestReviewAt > reportTs
  );

  if (reviewRun?.tests && typeof reviewRun.tests.total === "number") {
    const { passed = 0, total = 0, failed = [] } = reviewRun.tests;
    testsCount = { passed, total };
    tests = total > 0 && passed === total && failed.length === 0 ? "pass" : "fail";
  } else if (reviewTestsNewerThanReport && latestReview?.tests) {
    const { passed = 0, total = 0, failed = [] } = latestReview.tests;
    testsCount = { passed, total };
    tests = total > 0 && passed === total && failed.length === 0 ? "pass" : "fail";
  } else if (state?.lastTestReport) {
    const rep = state.lastTestReport;
    testsCount = { passed: rep.passedCount, total: rep.totalCount };
    tests = rep.allPassed && rep.totalCount > 0 ? "pass" : "fail";
  } else if (latestReview?.tests && typeof latestReview.tests.total === "number") {
    const { passed = 0, total = 0, failed = [] } = latestReview.tests;
    testsCount = { passed, total };
    tests = total > 0 && passed === total && failed.length === 0 ? "pass" : "fail";
  }

  let lint: LayerCheckStatus = "not_run";
  if (reviewRun && Array.isArray(reviewRun.lint)) {
    lint = reviewRun.lint.length === 0 ? "pass" : "fail";
  } else if (latestReview && Array.isArray(latestReview.lint)) {
    lint = latestReview.lint.length === 0 ? "pass" : "fail";
  }

  let types: LayerCheckStatus = "not_run";
  const runTypeItems =
    reviewRun && Array.isArray(reviewRun.typecheck)
      ? reviewRun.typecheck
      : reviewRun && Array.isArray(reviewRun.types)
      ? reviewRun.types
      : undefined;

  if (runTypeItems !== undefined) {
    types = runTypeItems.length === 0 ? "pass" : "fail";
  } else if (latestReview && Array.isArray(latestReview.typecheck)) {
    types = latestReview.typecheck.length === 0 ? "pass" : "fail";
  }

  let failures: string[] = [];
  if (reviewRun) {
    failures = formatReviewRunFailures(reviewRun, defaultFile);
  } else if (latestReview) {
    failures = formatReviewRunFailures(latestReview, defaultFile);
  } else if (state?.lastTestReport && !state.lastTestReport.allPassed) {
    const fileFallback = defaultFile || "solution.js";
    const failingResults = (state.lastTestReport.visibleResults || []).filter(
      (r) => !r.passed
    );
    let hiddenFailedCount = 0;
    for (const r of failingResults) {
      if (isHiddenTestFailureName(r.name) || isHiddenTestFailureName(r.error)) {
        hiddenFailedCount += 1;
      } else {
        const detail = r.error ? ` ${r.error.split("\n")[0].trim()}` : "";
        failures.push(sanitizeCodeCheckError(`${fileFallback}:0 test ${r.name}${detail}`));
      }
    }
    if (hiddenFailedCount > 0) {
      const label =
        hiddenFailedCount === 1
          ? "1 hidden check failed"
          : `${hiddenFailedCount} hidden checks failed`;
      failures.push(sanitizeCodeCheckError(`${fileFallback}:0 test ${label}`));
    }
  }

  return {
    tests,
    lint,
    types,
    review,
    testsSymbol: layerSymbol(tests),
    lintSymbol: layerSymbol(lint),
    typesSymbol: layerSymbol(types),
    reviewSymbol: layerSymbol(review),
    reviewLabel: reviewStatusLabel(review),
    testsCount,
    failures,
  };
}

function isStatusInput(
  val: unknown
): val is Pick<CodeLayeredStatus, "tests" | "review"> {
  return (
    Boolean(val) &&
    typeof val === "object" &&
    "tests" in (val as Record<string, unknown>) &&
    "review" in (val as Record<string, unknown>) &&
    typeof (val as { tests?: unknown }).tests === "string" &&
    typeof (val as { review?: unknown }).review === "string"
  );
}

export function choosePrimaryAction(
  statusOrState?: Pick<CodeLayeredStatus, "tests" | "review"> | ProblemState | null,
  drillId = "",
  problemId = "",
  reviewRun?: Partial<ReviewRunResult> | null
): PrimaryCodeAction {
  const status: Pick<CodeLayeredStatus, "tests" | "review"> = isStatusInput(statusOrState)
    ? statusOrState
    : deriveCodeStatus(statusOrState ?? null, reviewRun);

  if (status.review === "pass" && status.tests !== "fail") {
    return {
      kind: "next_problem",
      label: "Next problem",
    };
  }

  if (status.tests === "pass") {
    return {
      kind: "copy_review",
      label: "Copy review request",
      reviewCommand: drillId && problemId ? getReviewRequest(drillId, problemId) : undefined,
    };
  }

  return {
    kind: "open_vscode",
    label: "Open in VS Code",
  };
}

/**
 * Return true when a PRG problem is solved in the local IDE workspace rather than an
 * in-browser input (choice, line_number / find_bug, or standalone predict_output).
 */
export function isWorkspaceProblem(problem: Partial<Problem>): boolean {
  if (problem.workspaceFile) return true;
  if (problem.visibleTests && problem.visibleTests.length > 0) return true;
  const specType = problem.answerSpec?.type;
  if (
    specType === "choice" ||
    specType === "line_number" ||
    specType === "find_bug" ||
    specType === "predict_output" ||
    specType === "code_output" ||
    specType === "text"
  ) {
    return false;
  }
  if (problem.codeType === "predict-output" || problem.codeType === "find-bug") {
    return false;
  }
  return (
    problem.codeType === "kata" ||
    problem.codeType === "implement" ||
    problem.codeType === "refactor" ||
    problem.archetype === "problem-solving" ||
    problem.archetype === "debugging" ||
    problem.archetype === "refactoring" ||
    problem.archetype === "project-based"
  );
}

/**
 * Compute defensive folder-level IDE deep links per rules/04_code.md §1.1.
 * Never falls back to opening a single file.
 */
export function resolveIdeLinks(problem: Partial<Problem>): IdeLinks {
  const workspacePath = problem.workspaceFile || "";
  const workspaceDir =
    problem.workspaceDir ||
    (workspacePath.includes("/")
      ? workspacePath.substring(0, workspacePath.lastIndexOf("/"))
      : "");
  const filename = workspacePath.includes("/")
    ? workspacePath.substring(workspacePath.lastIndexOf("/") + 1)
    : workspacePath || "solution.js";

  const normalizedDir =
    workspaceDir && workspaceDir !== "."
      ? workspaceDir.startsWith("/")
        ? workspaceDir
        : `/${workspaceDir}`
      : "";

  const vscodeFolderUrl =
    problem.vscodeFolderUrl || (normalizedDir ? `vscode://file${normalizedDir}` : "");

  return {
    workspaceDir: workspaceDir || ".",
    filename,
    vscodeFolderUrl,
    ...(problem.vscodeUrl ? { vscodeUrl: problem.vscodeUrl } : {}),
  };
}
