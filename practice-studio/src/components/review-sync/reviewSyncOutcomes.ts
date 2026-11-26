export const outcomeLabels = {
  correct: "Correct",
  assisted: "Correct with help",
  wrong: "Wrong",
  unattempted: "Skipped / not tried",
} as const;

export type OutcomeCounts = Record<keyof typeof outcomeLabels, number>;
import { scoreProblem } from "@/lib/scoring";
import type { DrillDocument } from "@/types/drill";


export function countReviewSyncOutcomes(drill: DrillDocument): OutcomeCounts {
  const counts: OutcomeCounts = { correct: 0, assisted: 0, wrong: 0, unattempted: 0 };
  const isPrg = drill.subject === "PRG";
  for (const { state } of drill.problems) {
    const { outcome } = scoreProblem(state, { isPrg });
    if (outcome === "correct" || outcome === "assisted" || outcome === "wrong") {
      counts[outcome] += 1;
    } else {
      counts.unattempted += 1;
    }
  }
  return counts;
}
