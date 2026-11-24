import { randomUUID } from "crypto";
import { applyCheckResult, applySkip, applyTestReport, resetProblemForRetry } from "@/lib/applyCheckResult";
import { labToDrillDocument } from "@/lib/labModel";
import { loadLabDetailFromDisk } from "@/lib/labs";
import { loadDrillFromDisk } from "@/lib/paths";
import { mutateProblemState, mutateProblemStates, readProgress } from "@/lib/progress";
import {
  compareIsoTimestamps,
  hasSubstantiveAttempt,
  isSubstantiveVerdict,
  isTimestampInCycle,
} from "@/lib/reviewGuard";
import { hasCheckpointHint } from "@/lib/studioRules";
import { isLabId } from "@/lib/routes";
import { MAX_ATTEMPT_DURATION_MS } from "@/lib/telemetryTimer";
import { applySelfScore, isLockedAfterCorrect } from "@/lib/scoring";
import type { CheckResult, DrillDocument, Problem, ProblemState, TestRunReport } from "@/types/drill";

export function loadPracticeDocument(drillId: string): DrillDocument | null {
  if (isLabId(drillId)) {
    const lab = loadLabDetailFromDisk(drillId);
    return lab ? labToDrillDocument(lab) : null;
  }
  const drill = loadDrillFromDisk(drillId);
  return drill?.drillId === drillId && Array.isArray(drill.problems)
    ? (drill as unknown as DrillDocument)
    : null;
}

export function currentPracticeCycle(drillId: string, qid: string): string | null {
  const state = readProgress(drillId)?.problems?.[qid] as ProblemState | undefined;
  return state?.cycleStartedAt ?? null;
}

export function practiceDuration(raw: unknown): number | undefined {
  return typeof raw === "number" && Number.isFinite(raw) && raw >= 0
    ? Math.min(raw, MAX_ATTEMPT_DURATION_MS)
    : undefined;
}

export function recordOriginalCheck(
  doc: Pick<DrillDocument, "drillId" | "unitCode" | "mistakeTags">,
  problem: Problem,
  cycle: string | null,
  input: string,
  result: CheckResult,
  durationMs?: number,
  skipOpensHint = false
): { eventId?: string; ts?: string } {
  let event: { eventId?: string; ts?: string } = {};
  mutateProblemState(doc.drillId, doc.unitCode, problem.id, (state) => {
    if ((state.cycleStartedAt ?? null) !== cycle || isLockedAfterCorrect(state)) return;
    const ts = practiceTimestamp(cycle);
    if (result.verdict === "skipped" && skipOpensHint && hasCheckpointHint(problem.checkpointHint)) {
      state.hintsRevealed = (state.hintsRevealed || 0) + 1;
      state.reviewHintRevealedAt = ts;
    }
    const target = { ...problem, state };
    const next = result.verdict === "skipped"
      ? applySkip({ ...target, state: { ...state, userInput: input } }, { ts, durationMs })
      : applyCheckResult(target, input, result, doc.mistakeTags, { ts, durationMs });
    const attempt = next.attempts?.at(-1);
    if (attempt && next.attempts !== state.attempts && isSubstantiveVerdict(attempt.verdict)) {
      const eventId = randomUUID();
      attempt.eventId = eventId;
      const hintUsed = cycle
        ? isTimestampInCycle(state.reviewHintRevealedAt, cycle)
        : Boolean(state.hintsRevealed);
      attempt.hintsUsed = Boolean(hintUsed || attempt.setupRevealed ||
        attempt.solutionRevealed || attempt.exampleViewed);
      event = { eventId, ts };
    }
    return next;
  });
  return event;
}

function practiceTimestamp(cycle: string | null): string {
  const now = new Date().toISOString();
  if (!cycle) return now;
  const cmp = compareIsoTimestamps(cycle, now);
  return (cmp !== null ? cmp > 0 : cycle > now) && Date.parse(cycle) - Date.parse(now) <= 3
    ? cycle
    : now;
}

export function recordTestReport(
  drillId: string, qid: string, unitCode: string | undefined, cycle: string | null,
  report: TestRunReport
): TestRunReport | null {
  if (currentPracticeCycle(drillId, qid) !== cycle) return null;
  if (!Number.isFinite(report.totalCount) || report.totalCount <= 0) return report;
  const ts = practiceTimestamp(cycle);
  mutateProblemState(drillId, unitCode, qid, (state) => applyTestReport(state, report, ts));
  return { ...report, ts };
}

export function resetPractice(
  doc: DrillDocument,
  problems: Problem[],
  options: { resetSummary?: boolean; reviewBaseLevel?: number; keepReviewHelp?: boolean } = {}
): string {
  const now = Date.now();
  const saved = readProgress(doc.drillId);
  let nextCycle = now;
  for (const problem of problems) {
    const state = saved?.problems?.[problem.id] as ProblemState | undefined;
    const latest = Math.max(
      ...[state?.cycleStartedAt, state?.attempts?.at(-1)?.ts, state?.lastTestReport?.ts,
        state?.reviews?.at(-1)?.at].map((ts) => Date.parse(ts ?? "") || 0)
    );
    // The new cycle must come after a server event written in the same millisecond.
    if (latest >= now && latest <= now + 2) nextCycle = Math.max(nextCycle, latest + 1);
  }
  const cycle = new Date(nextCycle).toISOString();
  const targets = new Map(problems.map((problem) => [problem.id, problem]));
  const summary = options.resetSummary ? {
    practiceStatus: "Ready",
    score: 0,
    accuracyPct: 0,
    skippedCount: 0,
    skippedProblems: [],
    mistakeCategories: [],
    divergedStepsSummary: "",
    attemptDate: null,
    statusOverride: null,
  } : undefined;
  mutateProblemStates(doc.drillId, doc.unitCode, Array.from(targets.keys()), (state, qid) => {
    const problem = targets.get(qid)!;
    const next = resetProblemForRetry({ ...problem, state }, cycle).state;
    delete next.reviewBaseLevel;
    if (options.reviewBaseLevel !== undefined) next.reviewBaseLevel = options.reviewBaseLevel;
    if (options.keepReviewHelp && state.cycleStartedAt) {
      if (isTimestampInCycle(state.reviewHintRevealedAt, state.cycleStartedAt)) {
        next.hintsRevealed = state.hintsRevealed;
        next.reviewHintRevealedAt = cycle;
      }
      if (isTimestampInCycle(state.reviewSetupRevealedAt, state.cycleStartedAt)) {
        next.setupRevealedBeforeAnswer = true;
        next.reviewSetupRevealedAt = cycle;
      }
    }
    return next;
  }, summary);
  return cycle;
}

export function recordPracticeHelp(
  doc: DrillDocument, qid: string, action: "hint" | "setup" | "steps"
): boolean {
  const problem = doc.problems.find((p) => p.id === qid);
  if (!problem || (action === "hint" && !hasCheckpointHint(problem.checkpointHint))) return false;
  if (action === "setup" && !problem.display && !problem.plainText) return false;
  let allowed = true;
  mutateProblemState(doc.drillId, doc.unitCode, qid, (state) => {
    const ts = practiceTimestamp(state.cycleStartedAt ?? null);
    if (action === "steps" && !hasSubstantiveAttempt(state)) {
      allowed = false;
      return;
    }
    if (action === "hint" && !isLockedAfterCorrect(state)) {
      state.hintsRevealed = (state.hintsRevealed || 0) + 1;
      state.reviewHintRevealedAt = ts;
    } else if (action === "setup" && !hasSubstantiveAttempt(state)) {
      state.setupRevealedBeforeAnswer = true;
      state.reviewSetupRevealedAt = ts;
    } else if (action === "steps" && !isLockedAfterCorrect(state)) {
      state.solutionRevealedBeforeAnswer = true;
      state.reviewStepsRevealedAt = ts;
    }
  });
  return allowed;
}

export function recordSelfScore(doc: DrillDocument, qid: string, score: number | null): void {
  mutateProblemState(doc.drillId, doc.unitCode, qid, (state) =>
    hasSubstantiveAttempt(state)
      ? applySelfScore(state, score, { isPrg: doc.subject === "PRG" })
      : state
  );
}
