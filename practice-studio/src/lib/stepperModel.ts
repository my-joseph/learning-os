import type { Problem } from "../types/drill";
import type { Workspace } from "./routes";
import { cycleReviews } from "./reviewGuard";
import { countPractisedSimilar, cycleOriginalAttempts } from "./similarTabs";
import { deriveCodeStatus, deriveMilestoneStepperState } from "./codeStatus";

export type DrillStepResult =
  | "correct"
  | "assisted"
  | "usedHelp"
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
}

const DRILL_RESULT_LABEL: Record<DrillStepResult, string> = {
  correct: "correct",
  assisted: "correct with help",
  usedHelp: "used help",
  partial: "partly correct",
  wrong: "wrong",
  skipped: "skipped",
  notTried: "not tried",
};

/**
 * Derive a drill problem's stepper result from its score, help signals, and skipped flag.
 * Uses `cycleOriginalAttempts` so review retries reflect the active review cycle.
 */
export function drillStepResult(problem: Problem): DrillStepResult {
  const state = problem.state;
  const isSkipped = state?.skipped === true;
  const hasScore = state?.score !== null && state?.score !== undefined;
  const scoreVal = state?.score ?? 0;
  const isAssisted = Boolean(
    state?.setupRevealedBeforeAnswer ||
      state?.solutionRevealedBeforeAnswer ||
      (state?.hintsRevealed ?? 0) > 0 ||
      cycleOriginalAttempts(state).some(
        (a) => a.setupRevealed || a.solutionRevealed || a.exampleViewed
      )
  );

  if (hasScore && scoreVal >= 1 && !isAssisted && !isSkipped) return "correct";
  if (hasScore && scoreVal > 0 && isAssisted && !isSkipped) return "assisted";
  if (hasScore && scoreVal > 0 && !isAssisted && !isSkipped) return "partial";
  if (hasScore && scoreVal === 0 && !isSkipped) return "wrong";
  if (isSkipped) return "skipped";
  if (isAssisted) return "usedHelp";
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
    const result = drillStepResult(problem);
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
export function buildReviewStepMeta(): ReviewStepMeta {
  return { ariaLabel: "Review & sync" };
}
