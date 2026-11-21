import type { Problem } from "../types/drill";
import type { Workspace } from "./routes";
import { cycleReviews } from "./reviewGuard";
import { isAwaitingReview, scoreProblem } from "./scoring";
import { countPractisedSimilar, cycleOriginalAttempts } from "./similarTabs";
import { deriveCodeStatus, deriveMilestoneStepperState } from "./codeStatus";

export type DrillStepResult =
  | "correct"
  | "assisted"
  | "usedHelp"
  | "awaitingReview"
  | "partial"
  | "wrong"
  | "skipped"
  | "notTried";

export type LabStepResult =
  | "passed"
  | "regressed"
  | "inProgress"
  | "notStarted";

export type StepResult = DrillStepResult | LabStepResult;

export type LabStatusLine = "Tests passing" | "In progress" | "Not started";

export interface StepItem {
  key: string;
  circleLabel: string;
  title: string;
  result: StepResult;
  ariaLabel: string;
}

export interface ReviewStepMeta {
  ariaLabel: string;
  synced: boolean;
}

const DRILL_RESULT_LABEL: Record<DrillStepResult, string> = {
  correct: "correct",
  assisted: "correct with help",
  usedHelp: "used help",
  awaitingReview: "awaiting review",
  partial: "partly correct",
  wrong: "wrong",
  skipped: "skipped",
  notTried: "not tried",
};

/**
 * Derive a drill problem's stepper result from the single canonical `scoreProblem` rule.
 */
export function drillStepResult(
  problem: Problem,
  workspace?: Workspace
): DrillStepResult {
  const isPrg = workspace === "code";
  const scored = scoreProblem(problem.state, { isPrg });
  if (scored.outcome === "correct") return "correct";
  if (scored.outcome === "assisted") return "assisted";
  if (scored.outcome === "wrong") return "wrong";
  if (scored.outcome === "skipped") return "skipped";
  if (isAwaitingReview(problem.state, { isPrg })) return "awaitingReview";
  if (scored.usedHelp) return "usedHelp";
  return "notTried";
}

/**
 * Derive the secondary status line shown under a lab milestone step:
 * "Tests passing", "In progress", or "Not started".
 */
export function labStatusLine(problem: Problem): LabStatusLine {
  const state = problem.state;
  const status = deriveCodeStatus(state);
  if (status.tests === "pass") return "Tests passing";

  const hasActivity =
    status.tests !== "not_run" ||
    Boolean(state?.lastTestReport) ||
    cycleReviews(state).length > 0 ||
    cycleOriginalAttempts(state).length > 0 ||
    Boolean(state?.userCode && state.userCode.trim().length > 0);

  return hasActivity ? "In progress" : "Not started";
}

/**
 * Derive a lab milestone's stepper visual state.
 * "passed" only appears when every layer (tests, lint, types, review) passes.
 */
export function labStepResult(problem: Problem): LabStepResult {
  const stepperState = deriveMilestoneStepperState(problem.state);
  if (stepperState === "passed") return "passed";
  if (stepperState === "regressed") return "regressed";
  return labStatusLine(problem) === "Not started" ? "notStarted" : "inProgress";
}

/** Build stepper items for a Math or Programming drill. */
export function buildDrillSteps(
  problems: Problem[],
  workspace?: Workspace
): StepItem[] {
  const noun = workspace === "code" ? "Problem" : "Question";
  return problems.map((problem, idx) => {
    const result = drillStepResult(problem, workspace);
    const levelLabelMatch = problem.levelLabel?.match(/Level\s+\d+/i);
    const levelText =
      typeof problem.level === "number"
        ? `Level ${problem.level}`
        : levelLabelMatch?.[0] || "Level 1";
    const title = levelText;
    const practisedSimilar =
      workspace !== "code" ? countPractisedSimilar(problem.state) : 0;
    const similarSuffix =
      practisedSimilar > 0 ? `, practised ${practisedSimilar} similar` : "";
    const ariaLabel = `${noun} ${idx + 1}, ${levelText}, ${DRILL_RESULT_LABEL[result]}${similarSuffix}`;

    return {
      key: problem.id,
      circleLabel: `Q${idx + 1}`,
      title,
      result,
      ariaLabel,
    };
  });
}

/** Build stepper items for a Project Lab's milestones. */
export function buildLabSteps(problems: Problem[]): StepItem[] {
  return problems.map((problem, idx) => {
    const name = (problem.category || problem.id).trim();
    const secondary = labStatusLine(problem);
    const result = labStepResult(problem);
    const resultSuffix =
      result === "passed"
        ? ", passed"
        : result === "regressed"
        ? ", regressed"
        : "";
    const ariaLabel = `Milestone ${idx + 1}, ${name}, ${secondary.toLowerCase()}${resultSuffix}`;

    return {
      key: problem.id,
      circleLabel: `M${idx + 1}`,
      title: name,
      result,
      ariaLabel,
    };
  });
}

/** Build the visible label and accessible name for the trailing Review step. */
export function buildReviewStepMeta({ synced = false }: { synced?: boolean } = {}): ReviewStepMeta {
  return {
    ariaLabel: synced ? "Review & sync — synced" : "Review & sync",
    synced,
  };
}
