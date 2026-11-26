import type { ProblemState } from "@/types/drill";
import { getNotionAttemptEvidence, isTimestampInCycle } from "@/lib/reviewGuard";
import { trapName } from "@/lib/titleText";

export interface RecentMistake {
  key: string;
  name: string;
  recentMisses: number;
  recentTries: number;
  fixed: boolean;
}

export function mistakePracticeHref(key: string): string {
  return `/review?${new URLSearchParams({ scope: `mistake:${key}` })}`;
}

export function mistakeName(id: string, subject: "MTH" | "PRG", checkNames: Record<string, string>): string {
  if (subject === "MTH") return trapName(id) || "Repeated mistake";
  if (Object.hasOwn(checkNames, id)) return checkNames[id];
  const words = id
    .replace(/^(?:[^/]+\/)+/, "")
    .replace(/^(?:QC|U)-(?:PRG-(?:T\d+-)?(?:C\d+-)?(?:U\d+-)?)?/i, "")
    .replace(/[-_.]+/g, " ")
    .trim()
    .toLowerCase();
  return /[a-z]/.test(words) ? words[0].toUpperCase() + words.slice(1) : "Code check";
}

/** Keep historical mistake names out of view until the active problem is genuinely attempted. */
export function canShowMistakeHistory(state?: ProblemState, mode?: "code" | "similar"): boolean {
  if (mode === "similar") {
    return Boolean(state?.attempts?.some((attempt) =>
      attempt && ["correct", "incorrect", "partial", "equivalent_not_in_form"].includes(attempt.verdict) &&
      isTimestampInCycle(attempt.ts, state.cycleStartedAt)
    ));
  }
  return getNotionAttemptEvidence(state, mode === "code").attempted;
}

export function mistakeAttemptKey(state?: ProblemState, mode?: "code" | "similar"): string | null {
  if (!state || !canShowMistakeHistory(state, mode)) return null;
  return JSON.stringify([
    state.cycleStartedAt,
    state.attempts?.length,
    state.reviews?.length,
    state.testRuns?.length,
    state.lastTestReport?.ts,
  ]);
}
