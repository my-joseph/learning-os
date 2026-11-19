import {
  CheckResult,
  DrillDocument,
  Problem,
  ProblemState,
} from "@/types/drill";
import {
  computeCheckAnswerTransition,
  computeSkipProblemTransition,
  mergeRevealedPatchIntoDrill,
  RevealPart,
} from "@/hooks/useDrill";
import { redactProblemForReview } from "@/lib/redact";
import { hasSubstantiveAttempt, isSubstantiveVerdict } from "@/lib/reviewGuard";
import type { ReviewItem } from "@/lib/reviewItems";
import { drillHref } from "@/lib/routes";
import { TelemetryTimerState } from "@/lib/telemetryTimer";
import { plainTitle } from "@/lib/titleText";

export const CLIENT_REVIEW_INTERVALS: Record<number, number> = {
  1: 1,
  2: 3,
  3: 7,
  4: 16,
  5: 35,
};

export function reviewItemKey(drillId: string, qid: string): string {
  return `${drillId}/${qid}`;
}

function addDaysClient(dateStr: string, days: number): string {
  const cand = typeof dateStr === "string" && /^\d{4}-\d{2}-\d{2}$/.test(dateStr.trim().slice(0, 10))
    ? dateStr.trim().slice(0, 10)
    : new Date().toISOString().slice(0, 10);
  const [y, m, d] = cand.split("-").map((x) => parseInt(x, 10));
  const utc = new Date(Date.UTC(y, m - 1, d + Math.trunc(days)));
  const yy = utc.getUTCFullYear();
  const mm = String(utc.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(utc.getUTCDate()).padStart(2, "0");
  return `${yy}-${mm}-${dd}`;
}

function stepReviewScheduleClient(
  currentLevel: number,
  outcome: { correct: boolean; hintsUsed?: boolean | number; date: string }
): { level: number; dueDate: string } {
  const lvl = Math.max(1, Math.min(5, Math.trunc(currentLevel || 1)));
  const assisted =
    typeof outcome.hintsUsed === "number"
      ? outcome.hintsUsed > 0
      : Boolean(outcome.hintsUsed);
  if (outcome.correct && !assisted) {
    const nextLevel = Math.min(5, lvl + 1);
    return {
      level: nextLevel,
      dueDate: addDaysClient(outcome.date, CLIENT_REVIEW_INTERVALS[nextLevel]),
    };
  }
  if (outcome.correct && assisted) {
    return {
      level: lvl,
      dueDate: addDaysClient(outcome.date, CLIENT_REVIEW_INTERVALS[lvl]),
    };
  }
  const nextLevel = Math.max(1, Math.floor(lvl / 2));
  return {
    level: nextLevel,
    dueDate: addDaysClient(outcome.date, 1),
  };
}

export interface ReviewSessionItemOutcome {
  drillId: string;
  qid: string;
  initialLevel: number;
  newLevel: number;
  correct: boolean;
  hintsUsed: number;
  dueDate: string;
  commonTrapTag?: string | null;
}

export interface ReviewSessionSummary {
  correctCount: number;
  totalCount: number;
  movedUpCount: number;
  movedDownCount: number;
  stayedCount: number;
  nextDueDate: string | null;
}

export const REVIEW_BATCH_SIZE = 8;

export interface MissedReviewItem {
  drillId: string;
  qid: string;
  unitCode: string;
  unitTitle: string;
  href: string;
}

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

/** Return signed calendar day difference `toDate - fromDate`, or null when either date is invalid. */
export function daysBetweenDates(
  fromDate?: string | null,
  toDate?: string | null
): number | null {
  if (typeof fromDate !== "string" || typeof toDate !== "string") return null;
  const a = fromDate.trim().slice(0, 10);
  const b = toDate.trim().slice(0, 10);
  if (!DATE_RE.test(a) || !DATE_RE.test(b)) return null;
  const [ay, am, ad] = a.split("-").map((x) => parseInt(x, 10));
  const [by, bm, bd] = b.split("-").map((x) => parseInt(x, 10));
  const utcA = Date.UTC(ay, am - 1, ad);
  const utcB = Date.UTC(by, bm - 1, bd);
  return Math.round((utcB - utcA) / 86_400_000);
}

/** Plain-language scheduling suffix for the `/review` result card ("next in N days" / "back tomorrow"). */
export function formatReviewScheduleHint(
  outcome: Pick<ReviewSessionItemOutcome, "correct" | "newLevel" | "dueDate"> | null | undefined,
  today?: string | null
): string | null {
  if (!outcome) return null;
  if (!outcome.correct) {
    return "back tomorrow";
  }
  const diff = daysBetweenDates(today, outcome.dueDate);
  const days =
    diff !== null && diff >= 1
      ? diff
      : CLIENT_REVIEW_INTERVALS[outcome.newLevel] ?? 1;
  return days === 1 ? "next in 1 day" : `next in ${days} days`;
}

/** Collect all missed (wrong or skipped) items from a completed review batch with deep links. */
export function getMissedReviewItems(
  items: ReadonlyArray<Pick<ReviewItem, "drillId" | "qid" | "unitCode">>,
  outcomes: Record<string, ReviewSessionItemOutcome>,
  unitTitles?: Record<string, string>
): MissedReviewItem[] {
  const missed: MissedReviewItem[] = [];
  for (const item of items) {
    const key = reviewItemKey(item.drillId, item.qid);
    const outcome = outcomes[key];
    if (!outcome || outcome.correct) continue;
    const rawTitle = unitTitles?.[item.unitCode] || item.unitCode;
    missed.push({
      drillId: item.drillId,
      qid: item.qid,
      unitCode: item.unitCode,
      unitTitle: plainTitle(rawTitle) || item.unitCode,
      href: drillHref(item.drillId, item.qid),
    });
  }
  return missed;
}

/**
 * Ensure an unattempted review problem never exposes answers, steps, display, solutionCode,
 * trap tags, or archetype keys before the learner makes an attempt in this review session.
 */
export function prepareProblemForReviewItem(
  problem: Problem,
  item?: Pick<ReviewItem, "subject" | "revisitNote"> | null
): Problem {
  const subj: "MATH" | "PRG" =
    item?.subject === "PRG" ? "PRG" : "MATH";
  if (!hasSubstantiveAttempt(problem.state)) {
    const redacted = redactProblemForReview(problem, subj);
    const note =
      item?.revisitNote ??
      (typeof problem.state?.revisitNote === "string" && problem.state.revisitNote.trim()
        ? problem.state.revisitNote.trim()
        : undefined);
    return {
      ...redacted,
      state: {
        ...redacted.state,
        ...(note ? { revisitNote: note } : {}),
      },
    };
  }
  return problem;
}

/**
 * Pure summary calculation for the Daily Review end screen:
 * counts correct / total, items moved up / down a level, and earliest upcoming next due date.
 */
export function summarizeReviewSession(
  items: ReadonlyArray<Pick<ReviewItem, "drillId" | "qid" | "level">>,
  outcomes: Record<string, ReviewSessionItemOutcome>,
  initialNextDueDate?: string | null
): ReviewSessionSummary {
  const outcomeList =
    items.length > 0
      ? items
          .map((it) => outcomes[reviewItemKey(it.drillId, it.qid)])
          .filter((o): o is ReviewSessionItemOutcome => Boolean(o))
      : Object.values(outcomes);

  const totalCount = items.length > 0 ? items.length : outcomeList.length;
  let correctCount = 0;
  let movedUpCount = 0;
  let movedDownCount = 0;
  let stayedCount = 0;
  const candidateDueDates: string[] = [];

  if (typeof initialNextDueDate === "string" && DATE_RE.test(initialNextDueDate.trim())) {
    candidateDueDates.push(initialNextDueDate.trim());
  }

  for (const outcome of outcomeList) {
    if (outcome.correct) {
      correctCount += 1;
    }
    if (outcome.newLevel > outcome.initialLevel) {
      movedUpCount += 1;
    } else if (outcome.newLevel < outcome.initialLevel) {
      movedDownCount += 1;
    } else {
      stayedCount += 1;
    }
    if (typeof outcome.dueDate === "string" && DATE_RE.test(outcome.dueDate.trim())) {
      candidateDueDates.push(outcome.dueDate.trim());
    }
  }

  candidateDueDates.sort();
  return {
    correctCount,
    totalCount,
    movedUpCount,
    movedDownCount,
    stayedCount,
    nextDueDate: candidateDueDates[0] ?? null,
  };
}

/**
 * Save a single reviewed problem's state (including `revisitNote` or attempt telemetry)
 * into `progress/<DRILL_ID>.json` via `/api/save-state` with `reviewMerge: true`.
 */
export async function saveReviewProblemState(
  drillId: string,
  unitCode: string,
  qid: string,
  state: ProblemState,
  fetchFn: typeof fetch = fetch
): Promise<boolean> {
  try {
    const res = await fetchFn("/api/save-state", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        drillId,
        unitCode,
        reviewMerge: true,
        problems: [{ id: qid, state }],
      }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

async function fetchRevealedParts(
  drillId: string,
  qid: string,
  parts: RevealPart[],
  fetchFn: typeof fetch = fetch
): Promise<Partial<Problem>> {
  const patch: Partial<Problem> = {};
  for (const part of parts) {
    try {
      const res = await fetchFn(
        `/api/reveal?drill=${encodeURIComponent(drillId)}&q=${encodeURIComponent(qid)}&part=${part}`
      );
      if (!res.ok) continue;
      const data = await res.json();
      if (part === "steps") {
        if (Array.isArray(data.steps)) patch.steps = data.steps;
        if (typeof data.answerDisplay === "string") patch.answerDisplay = data.answerDisplay;
        if (typeof data.answerPlain === "string") patch.answerPlain = data.answerPlain;
      } else if (part === "display") {
        if (typeof data.display === "string") patch.display = data.display;
        if (typeof data.plainText === "string") patch.plainText = data.plainText;
      } else if (part === "solution") {
        if (typeof data.solutionCode === "string") patch.solutionCode = data.solutionCode;
      }
    } catch {
      // ignore transient reveal error
    }
  }
  return patch;
}

/**
 * Full check wiring for a Daily Review item:
 * 1. POST `/api/check-answer`
 * 2. Compute problem state transition (`computeCheckAnswerTransition`)
 * 3. If substantive verdict:
 *    - POST `/api/save-state` (`reviewMerge: true`) so drill progress stays consistent
 *    - GET `/api/reveal` for earned `steps` / `display`
 *    - POST `/api/review-items` `{ drillId, qid, correct, hintsUsed }`
 */
export async function executeReviewItemCheck(params: {
  drillDoc: DrillDocument;
  item: ReviewItem;
  inputVal: string;
  hintsUsed: number;
  timerState: TelemetryTimerState;
  now?: number;
  today?: string;
  existingOutcome?: ReviewSessionItemOutcome | null;
  fetchFn?: typeof fetch;
}): Promise<{
  updatedDoc: DrillDocument;
  nextTimerState: TelemetryTimerState;
  result: CheckResult;
  outcome: ReviewSessionItemOutcome | null;
} | null> {
  const {
    drillDoc,
    item,
    inputVal,
    hintsUsed,
    timerState,
    now = Date.now(),
    today,
    existingOutcome = null,
    fetchFn = fetch,
  } = params;

  const trimmed = inputVal.trim();
  if (!trimmed) return null;

  const checkRes = await fetchFn("/api/check-answer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      drillId: drillDoc.drillId,
      problemId: item.qid,
      subject: drillDoc.subject,
      input: trimmed,
    }),
  });
  const rawResult: CheckResult = await checkRes.json();

  const transition = computeCheckAnswerTransition(
    drillDoc,
    item.qid,
    trimmed,
    rawResult,
    timerState,
    now
  );
  if (!transition) return null;

  let updatedDoc = transition.updatedDoc;
  const updatedProb = updatedDoc.problems.find((p) => p.id === item.qid);

  if (!isSubstantiveVerdict(transition.result.verdict) || !updatedProb) {
    return {
      updatedDoc,
      nextTimerState: transition.nextTimerState,
      result: transition.result,
      outcome: existingOutcome,
    };
  }

  let outcome = existingOutcome;
  if (!outcome) {
    const correct = transition.result.verdict === "correct";
    const fallbackStep = stepReviewScheduleClient(item.level, {
      correct,
      hintsUsed,
      date: today || item.dueDate,
    });
    let newLevel = fallbackStep.level;
    let dueDate = fallbackStep.dueDate;
    let commonTrapTag: string | null = item.commonTrapTag;

    try {
      const revRes = await fetchFn("/api/review-items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drillId: drillDoc.drillId,
          qid: item.qid,
          correct,
          hintsUsed,
          ...(today ? { date: today } : {}),
        }),
      });
      if (revRes.ok) {
        const revJson = (await revRes.json()) as {
          ok?: boolean;
          item?: ReviewItem;
        };
        if (revJson.item) {
          newLevel = revJson.item.level;
          dueDate = revJson.item.dueDate;
          if (revJson.item.commonTrapTag) {
            commonTrapTag = revJson.item.commonTrapTag;
          }
        }
      }
    } catch {
      // use fallbackStep on transient network error
    }

    outcome = {
      drillId: drillDoc.drillId,
      qid: item.qid,
      initialLevel: item.level,
      newLevel,
      correct,
      hintsUsed,
      dueDate,
      commonTrapTag,
    };
  }

  await saveReviewProblemState(
    drillDoc.drillId,
    item.unitCode || drillDoc.unitCode,
    item.qid,
    updatedProb.state,
    fetchFn
  );

  if (transition.partsToReveal.length > 0) {
    const patch = await fetchRevealedParts(
      drillDoc.drillId,
      item.qid,
      transition.partsToReveal,
      fetchFn
    );
    if (Object.keys(patch).length > 0) {
      updatedDoc =
        mergeRevealedPatchIntoDrill(updatedDoc, drillDoc.drillId, item.qid, patch) ??
        updatedDoc;
    }
  }

  return {
    updatedDoc,
    nextTimerState: transition.nextTimerState,
    result: transition.result,
    outcome,
  };
}

/**
 * Full skip wiring for a Daily Review item:
 * applies skip state, saves to `/api/save-state` (`reviewMerge: true`), reveals steps,
 * and records `correct: false` via `POST /api/review-items`.
 */
export async function executeReviewItemSkip(params: {
  drillDoc: DrillDocument;
  item: ReviewItem;
  hintsUsed: number;
  timerState: TelemetryTimerState;
  now?: number;
  today?: string;
  existingOutcome?: ReviewSessionItemOutcome | null;
  fetchFn?: typeof fetch;
}): Promise<{
  updatedDoc: DrillDocument;
  nextTimerState: TelemetryTimerState;
  outcome: ReviewSessionItemOutcome;
} | null> {
  const {
    drillDoc,
    item,
    hintsUsed,
    timerState,
    now = Date.now(),
    today,
    existingOutcome = null,
    fetchFn = fetch,
  } = params;

  const transition = computeSkipProblemTransition(
    drillDoc,
    item.qid,
    timerState,
    now
  );
  if (!transition) return null;

  let updatedDoc = transition.updatedDoc;
  const updatedProb = updatedDoc.problems.find((p) => p.id === item.qid);

  let outcome = existingOutcome;
  if (!outcome) {
    const fallbackStep = stepReviewScheduleClient(item.level, {
      correct: false,
      hintsUsed,
      date: today || item.dueDate,
    });
    let newLevel = fallbackStep.level;
    let dueDate = fallbackStep.dueDate;
    let commonTrapTag: string | null = item.commonTrapTag;

    try {
      const revRes = await fetchFn("/api/review-items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drillId: drillDoc.drillId,
          qid: item.qid,
          correct: false,
          hintsUsed,
          ...(today ? { date: today } : {}),
        }),
      });
      if (revRes.ok) {
        const revJson = (await revRes.json()) as {
          ok?: boolean;
          item?: ReviewItem;
        };
        if (revJson.item) {
          newLevel = revJson.item.level;
          dueDate = revJson.item.dueDate;
          if (revJson.item.commonTrapTag) {
            commonTrapTag = revJson.item.commonTrapTag;
          }
        }
      }
    } catch {
      // use fallbackStep
    }

    outcome = {
      drillId: drillDoc.drillId,
      qid: item.qid,
      initialLevel: item.level,
      newLevel,
      correct: false,
      hintsUsed,
      dueDate,
      commonTrapTag,
    };
  }

  if (updatedProb) {
    await saveReviewProblemState(
      drillDoc.drillId,
      item.unitCode || drillDoc.unitCode,
      item.qid,
      updatedProb.state,
      fetchFn
    );
  }

  if (transition.partsToReveal.length > 0) {
    const patch = await fetchRevealedParts(
      drillDoc.drillId,
      item.qid,
      transition.partsToReveal,
      fetchFn
    );
    if (Object.keys(patch).length > 0) {
      updatedDoc =
        mergeRevealedPatchIntoDrill(updatedDoc, drillDoc.drillId, item.qid, patch) ??
        updatedDoc;
    }
  }

  return {
    updatedDoc,
    nextTimerState: transition.nextTimerState,
    outcome,
  };
}
