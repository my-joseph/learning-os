import type { Problem } from "../types/drill";
import type { Workspace } from "./routes";
import { countPractisedSimilar, cycleOriginalAttempts } from "./similarTabs";
import { deriveCodeStatus, deriveMilestoneStepperState } from "./codeStatus";

export type DrillStepResult =
  | "correct"
  | "assisted"
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
  title: string;
  secondary: string;
  result: StepResult;
  ariaLabel: string;
}

export interface ReviewStepMeta {
  secondary: string;
  ariaLabel: string;
}

const DRILL_RESULT_LABEL: Record<DrillStepResult, string> = {
  correct: "correct",
  assisted: "correct with help",
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
    (state?.reviews?.length ?? 0) > 0 ||
    (state?.attempts?.length ?? 0) > 0 ||
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
    const levelText =
      typeof problem.level === "number"
        ? `Level ${problem.level}`
        : problem.levelLabel || "Level 1";
    const title = `${noun} ${idx + 1}`;
    const practisedSimilar =
      workspace !== "code" ? countPractisedSimilar(problem.state) : 0;
    const similarSuffix =
      practisedSimilar > 0 ? `, practised ${practisedSimilar} similar` : "";
    const ariaLabel = `${noun} ${idx + 1}, ${levelText}, ${DRILL_RESULT_LABEL[result]}${similarSuffix}`;

    return {
      key: problem.id,
      title,
      secondary: levelText,
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
      title: name,
      secondary,
      result,
      ariaLabel,
    };
  });
}

/** Build the secondary line and accessible name for the trailing Review & sync step. */
export function buildReviewStepMeta(
  steps: readonly StepItem[],
  isLab: boolean
): ReviewStepMeta {
  const total = steps.length;
  if (isLab) {
    const passed = steps.filter((s) => s.result === "passed").length;
    const secondary = `${passed} of ${total} passed`;
    return {
      secondary,
      ariaLabel: `Review & sync, ${secondary}`,
    };
  }
  const answered = steps.filter(
    (s) => s.result !== "notTried" && s.result !== "skipped"
  ).length;
  const secondary = `${answered} of ${total} answered`;
  return {
    secondary,
    ariaLabel: `Review & sync, ${secondary}`,
  };
}
