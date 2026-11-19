import type { ProblemState } from "../types/drill";
import { statusTone } from "./statusTone";

export type ReviewOutcome =
  | "correct_first"
  | "assisted_or_partial"
  | "wrong"
  | "skipped"
  | "unanswered";

export interface ReviewOutcomeMeta {
  outcome: ReviewOutcome;
  label: string;
  /** Shared 10px node styling for both the score strip and each question row. */
  nodeClassName: string;
  textClassName: string;
  needsAttention: boolean;
}

export const OUTCOME_META: Record<ReviewOutcome, ReviewOutcomeMeta> = {
  correct_first: {
    outcome: "correct_first",
    label: "Correct",
    nodeClassName: statusTone.correct.dot,
    textClassName: statusTone.correct.text,
    needsAttention: false,
  },
  assisted_or_partial: {
    outcome: "assisted_or_partial",
    label: "Assisted / partial",
    nodeClassName: statusTone.assisted.dot,
    textClassName: statusTone.assisted.text,
    needsAttention: true,
  },
  wrong: {
    outcome: "wrong",
    label: "Wrong",
    nodeClassName: statusTone.wrong.dot,
    textClassName: statusTone.wrong.text,
    needsAttention: true,
  },
  skipped: {
    outcome: "skipped",
    label: "Skipped",
    nodeClassName: statusTone.skipped.dot,
    textClassName: statusTone.skipped.text,
    needsAttention: true,
  },
  unanswered: {
    outcome: "unanswered",
    label: "Unanswered",
    nodeClassName: statusTone.notTried.dot,
    textClassName: statusTone.notTried.text,
    needsAttention: true,
  },
};

/** Classify a problem's practice state into a single display outcome. */
export function classifyReviewOutcome(state?: ProblemState | null): ReviewOutcome {
  if (!state) return "unanswered";
  if (state.skipped === true) return "skipped";

  const isAssisted = Boolean(
    state.setupRevealedBeforeAnswer ||
      state.solutionRevealedBeforeAnswer ||
      (state.hintsRevealed ?? 0) > 0 ||
      state.attempts?.some((a) => a.setupRevealed || a.solutionRevealed)
  );

  if (typeof state.score === "number") {
    if (state.score >= 1 && !isAssisted) return "correct_first";
    if (state.score > 0) return "assisted_or_partial";
    return "wrong";
  }

  const latestReview = state.reviews?.[state.reviews.length - 1];
  if (latestReview?.verdict === "pass") return "correct_first";
  if (latestReview?.verdict === "revise") return "assisted_or_partial";

  return "unanswered";
}

/** Return display metadata (label, colour tokens, grouping) for an outcome. */
export function getReviewOutcomeMeta(outcome: ReviewOutcome): ReviewOutcomeMeta {
  return OUTCOME_META[outcome];
}

/** Convenience helper to classify a problem state and return its display metadata. */
export function getProblemOutcomeMeta(state?: ProblemState | null): ReviewOutcomeMeta {
  return OUTCOME_META[classifyReviewOutcome(state)];
}

/** Format a short question label ("Q3") or lab milestone ID ("M2"). */
export function getQuestionLabel(
  problemId: string,
  index: number,
  isLab = false
): string {
  if (isLab || /^M\d+$/i.test(problemId)) return problemId;
  return `Q${index + 1}`;
}

export interface GroupedReviewItem<T> {
  problem: T;
  index: number;
  outcome: ReviewOutcome;
  meta: ReviewOutcomeMeta;
}

export interface GroupedReviewSummary<T> {
  needsAttention: GroupedReviewItem<T>[];
  correct: GroupedReviewItem<T>[];
  firstTryCount: number;
  unansweredCount: number;
  totalDurationMs: number;
}

/** Group drill problems into "Needs attention" and "Correct" while collecting summary counts. */
export function groupReviewProblems<
  T extends { id: string; state?: ProblemState | null },
>(problems: readonly T[]): GroupedReviewSummary<T> {
  const needsAttention: GroupedReviewItem<T>[] = [];
  const correct: GroupedReviewItem<T>[] = [];
  let firstTryCount = 0;
  let unansweredCount = 0;
  let totalDurationMs = 0;

  problems.forEach((problem, index) => {
    const outcome = classifyReviewOutcome(problem.state);
    const meta = OUTCOME_META[outcome];
    const item: GroupedReviewItem<T> = { problem, index, outcome, meta };

    if (meta.needsAttention) {
      needsAttention.push(item);
    } else {
      correct.push(item);
      firstTryCount += 1;
    }

    if (outcome === "unanswered") {
      unansweredCount += 1;
    }

    if (typeof problem.state?.durationMs === "number" && problem.state.durationMs > 0) {
      totalDurationMs += problem.state.durationMs;
    }
  });

  return {
    needsAttention,
    correct,
    firstTryCount,
    unansweredCount,
    totalDurationMs,
  };
}

/** Format accumulated milliseconds into a compact duration label ("4m 12s"). */
export function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms <= 0) return "—";
  const totalSec = Math.max(1, Math.round(ms / 1000));
  if (totalSec < 60) return `${totalSec}s`;
  const mins = Math.floor(totalSec / 60);
  const secs = totalSec % 60;
  if (mins < 60) return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  return remMins > 0 ? `${hrs}h ${remMins}m` : `${hrs}h`;
}

/** Collapse multi-line / code-fenced prompts into one clean line for row previews. */
export function toSingleLinePrompt(prompt: string): string {
  if (!prompt) return "";
  return prompt
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/\s*\n+\s*/g, " ")
    .replace(/\s{2,}/g, " ")
    .trim();
}

/** Toggle a single row ID in the expanded-rows map. */
export function toggleExpandedRow(
  expanded: Record<string, boolean>,
  probId: string
): Record<string, boolean> {
  return { ...expanded, [probId]: !expanded[probId] };
}

/** Ensure a single row ID is expanded without collapsing other open rows. */
export function ensureExpandedRow(
  expanded: Record<string, boolean>,
  probId: string
): Record<string, boolean> {
  if (expanded[probId]) return expanded;
  return { ...expanded, [probId]: true };
}
