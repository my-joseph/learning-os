import { randomUUID } from "crypto";
import { applyCheckResult, applySkip, resetProblemForRetry } from "@/lib/applyCheckResult";
import { labToDrillDocument } from "@/lib/labModel";
import { loadLabDetailFromDisk } from "@/lib/labs";
import { loadDrillFromDisk, loadProblemFromDisk } from "@/lib/paths";
import { mutateProblemState, readProgress } from "@/lib/progress";
import { hasSubstantiveAttempt, isSubstantiveVerdict } from "@/lib/reviewGuard";
import { isLabId } from "@/lib/routes";
import { applySelfScore, isLockedAfterCorrect, scoreProblem } from "@/lib/scoring";
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
  return typeof raw === "number" && Number.isFinite(raw) && raw >= 0 ? raw : undefined;
}

export function recordOriginalCheck(
  doc: Pick<DrillDocument, "drillId" | "unitCode" | "mistakeTags">,
  problem: Problem,
  cycle: string | null,
  input: string,
  result: CheckResult,
  durationMs?: number
): { eventId?: string; ts?: string } {
  let event: { eventId?: string; ts?: string } = {};
  mutateProblemState(doc.drillId, doc.unitCode, problem.id, (state) => {
    if ((state.cycleStartedAt ?? null) !== cycle || isLockedAfterCorrect(state)) return;
    const ts = new Date().toISOString();
    const target = { ...problem, state };
    const next = result.verdict === "skipped"
      ? applySkip({ ...target, state: { ...state, userInput: input } }, { ts, durationMs })
      : applyCheckResult(target, input, result, doc.mistakeTags, { ts, durationMs });
    const attempt = next.attempts?.at(-1);
    if (attempt && next.attempts !== state.attempts && isSubstantiveVerdict(attempt.verdict)) {
      const eventId = randomUUID();
      attempt.eventId = eventId;
      attempt.hintsUsed = Boolean(state.hintsRevealed || attempt.setupRevealed ||
        attempt.solutionRevealed || attempt.exampleViewed);
      event = { eventId, ts };
    }
    return next;
  });
  return event;
}

export function applyTestReport(state: ProblemState, report: TestRunReport, ts: string): ProblemState {
  const next = {
    ...state,
    lastTestReport: { ...report, ts },
    testRuns: [
      ...(state.testRuns || []),
      {
        ts,
        allPassed: Boolean(report.allPassed &&
          (typeof report.totalCount !== "number" || report.totalCount > 0)),
        passedCount: report.passedCount,
        totalCount: report.totalCount,
      },
    ],
    skipped: false,
  };
  return { ...next, score: scoreProblem(next, { isPrg: true, ignoreStateScore: true }).score };
}

export function recordTestReport(
  drillId: string, qid: string, unitCode: string | undefined, cycle: string | null,
  report: TestRunReport
): TestRunReport | null {
  if (currentPracticeCycle(drillId, qid) !== cycle) return null;
  const ts = new Date().toISOString();
  mutateProblemState(drillId, unitCode, qid, (state) => applyTestReport(state, report, ts));
  return { ...report, ts };
}

export function resetPractice(doc: DrillDocument, problems: Problem[]): string {
  const now = Date.now();
  const cycle = new Date(Math.max(now, ...problems.map((p) => {
    const state = readProgress(doc.drillId)?.problems?.[p.id] as ProblemState | undefined;
    const latest = Math.max(
      ...[state?.cycleStartedAt, state?.attempts?.at(-1)?.ts, state?.lastTestReport?.ts,
        state?.reviews?.at(-1)?.at].map((ts) => Date.parse(ts ?? "") || 0)
    );
    // A reset and the last event can arrive in the same millisecond.
    return latest === now ? now + 1 : now;
  }))).toISOString();
  for (const problem of problems) {
    mutateProblemState(doc.drillId, doc.unitCode, problem.id, (state) =>
      resetProblemForRetry({ ...problem, state }, cycle).state
    );
  }
  return cycle;
}

export function recordPracticeHelp(
  doc: DrillDocument, qid: string, action: "hint" | "setup" | "steps"
): boolean {
  const loaded = isLabId(doc.drillId) ? null : loadProblemFromDisk(doc.drillId, qid);
  if (action !== "hint" && !loaded) return false;
  let allowed = true;
  mutateProblemState(doc.drillId, doc.unitCode, qid, (state) => {
    const ts = new Date().toISOString();
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
    applySelfScore(state, score, { isPrg: doc.subject === "PRG" })
  );
}
