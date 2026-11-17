import type { Problem, ProblemState, ReviewRecord } from "../types/drill";
import { getReviewRequest } from "./studioRules";

export type LayerCheckStatus = "pass" | "fail" | "not_run";
export type ReviewStatus = "pass" | "revise" | "not_requested";
export type MilestoneTileState = "pass" | "revise" | "not_started";
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
  cursorFolderUrl: string;
  vscodeUrl?: string;
  cursorUrl?: string;
}

const TS_CODE_RE = /^(TS\d+):\s*(.*)$/;

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
  const review = deriveReviewStatus(state?.reviews);
  if (review === "pass") return "pass";
  if (review === "revise") return "revise";
  return "not_started";
}

export function formatReviewRunFailures(
  reviewRun?: Partial<ReviewRunResult> | null,
  defaultFile = "solution.js"
): string[] {
  if (!reviewRun) return [];
  const fileFallback = defaultFile || "solution.js";
  const lines: string[] = [];

  if (Array.isArray(reviewRun.tests?.failed)) {
    for (const failedName of reviewRun.tests.failed) {
      lines.push(`${fileFallback}:0 test ${failedName}`);
    }
  }

  if (Array.isArray(reviewRun.lint)) {
    for (const item of reviewRun.lint) {
      const file = item.file || fileFallback;
      const line = typeof item.line === "number" ? item.line : 0;
      const rule = item.rule || "lint";
      lines.push(`${file}:${line} ${rule} ${item.message || ""}`.trim());
    }
  }

  const typeItems = Array.isArray(reviewRun.typecheck)
    ? reviewRun.typecheck
    : Array.isArray(reviewRun.types)
    ? reviewRun.types
    : [];

  for (const item of typeItems) {
    const file = item.file || fileFallback;
    const line = typeof item.line === "number" ? item.line : 0;
    const msg = (item.message || "").trim();
    const match = TS_CODE_RE.exec(msg);
    if (match) {
      lines.push(`${file}:${line} ${match[1]} ${match[2]}`.trim());
    } else {
      lines.push(`${file}:${line} tsc ${msg}`.trim());
    }
  }

  return lines;
}

export function deriveCodeStatus(
  state?: ProblemState | null,
  reviewRun?: Partial<ReviewRunResult> | null,
  defaultFile = "solution.js"
): CodeLayeredStatus {
  const review = deriveReviewStatus(state?.reviews);
  const latestReview =
    state?.reviews && state.reviews.length > 0
      ? state.reviews[state.reviews.length - 1]
      : undefined;

  let tests: LayerCheckStatus = "not_run";
  let testsCount: { passed: number; total: number } | undefined;

  if (reviewRun?.tests && typeof reviewRun.tests.total === "number") {
    const { passed = 0, total = 0, failed = [] } = reviewRun.tests;
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
    failures = (state.lastTestReport.visibleResults || [])
      .filter((r) => !r.passed)
      .map((r) => {
        const detail = r.error ? ` ${r.error.split("\n")[0].trim()}` : "";
        return `${fileFallback}:0 test ${r.name}${detail}`;
      });
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
  const cursorFolderUrl =
    problem.cursorFolderUrl || (normalizedDir ? `cursor://file${normalizedDir}` : "");

  return {
    workspaceDir: workspaceDir || ".",
    filename,
    vscodeFolderUrl,
    cursorFolderUrl,
    ...(problem.vscodeUrl ? { vscodeUrl: problem.vscodeUrl } : {}),
    ...(problem.cursorUrl ? { cursorUrl: problem.cursorUrl } : {}),
  };
}
