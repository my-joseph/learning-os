import type { DrillDocument, SessionSummary } from "../types/drill";
import type { PracticeStatusOverride } from "../hooks/types";
import type { MasteryCap, ReviewScheduleEntry } from "./dueToday";
import { hasSubstantiveAttempt } from "./reviewGuard";
import { classifyReviewOutcome } from "./reviewOutcome";
import { plainTitle } from "./titleText";

export interface SessionMetrics {
  liveScore: number;
  maxScore: number;
  accuracyPct: number;
  skippedCount: number;
  computedPracticeStatus: "Graded" | "Needs Retry";
}

export interface CoveredUnitPreview {
  unitCode: string;
  title: string;
  mastery: number | null;
  lastReviewed: string | null;
  nextReview: string | null;
  masteryCap: MasteryCap | null;
}

export interface SyncPreview {
  summary: SessionSummary;
  statusReason: string;
  mistakeCategories: string[];
  logLines: string[];
  unitTitle: string;
  coveredUnits: CoveredUnitPreview[];
  unansweredCount: number;
  skippedCount: number;
  hasAnyAttempt: boolean;
}

export const NO_DIVERGED_STEPS_SUMMARY = "No diverged steps logged.";

/** Read the learner-owned manual status choice saved alongside the session summary. */
export function getPersistedStatusOverride(
  summary: Partial<SessionSummary> | null | undefined
): PracticeStatusOverride {
  return summary?.statusOverride === "Graded" || summary?.statusOverride === "Needs Retry"
    ? summary.statusOverride
    : null;
}

/** Compute live score, accuracy, skipped count, and target practice status for a drill. */
export function computeSessionMetrics(
  currentDrill: DrillDocument | null,
  statusOverride: PracticeStatusOverride
): SessionMetrics {
  const liveScore = currentDrill
    ? currentDrill.problems.reduce((acc, p) => acc + (p.state?.score || 0), 0)
    : 0;
  const maxScore = currentDrill?.problems.length || 0;
  const accuracyPct = maxScore > 0 ? Math.round((liveScore / maxScore) * 1000) / 10 : 0;
  const skippedCount = currentDrill
    ? currentDrill.problems.filter((p) => p.state?.skipped).length
    : 0;

  const computedPracticeStatus: "Graded" | "Needs Retry" =
    statusOverride || (maxScore > 0 && liveScore / maxScore >= 0.8 ? "Graded" : "Needs Retry");

  return {
    liveScore,
    maxScore,
    accuracyPct,
    skippedCount,
    computedPracticeStatus,
  };
}

/**
 * Build the canonical SessionSummary sent to `/api/sync-notion` and `notion_sync/drill_sync.py`.
 * Shared between the Review & Sync preview and `confirmSyncToNotion` so preview === payload.
 * Never includes `revisitNote` or sync metadata timestamps.
 */
export function buildSessionSummary(
  currentDrill: DrillDocument,
  statusOverride: PracticeStatusOverride = null,
  options?: { attemptDate?: string }
): SessionSummary {
  const { liveScore, maxScore, accuracyPct, computedPracticeStatus } = computeSessionMetrics(
    currentDrill,
    statusOverride
  );

  const tagMap = new Map((currentDrill.mistakeTags || []).map((t) => [t.id, t.name]));
  const mistakeNames = new Set<string>();
  const divergedList: string[] = [];
  const skippedProblems: string[] = [];

  currentDrill.problems.forEach((p) => {
    const parts: string[] = [];
    if (p.state?.skipped) {
      skippedProblems.push(`${p.id} (${p.context || p.category})`);
      parts.push("SKIPPED - Concept Gap");
    }
    (p.state?.mistakes || []).forEach((tid) => {
      const rawName = tagMap.get(tid) || tid;
      mistakeNames.add(rawName.replace(/,/g, " /").trim());
    });
    if (typeof p.state?.divergedStep === "number") {
      const st = p.steps?.[p.state.divergedStep];
      parts.push(`Step ${p.state.divergedStep + 1}: ${st ? st.explain : "Diverged"}`);
    } else if (
      p.state?.score !== null &&
      p.state?.score !== undefined &&
      p.state.score < 1 &&
      (p.state?.mistakes || []).length > 0 &&
      !p.state?.skipped
    ) {
      parts.push((p.state?.mistakes || []).map((t) => tagMap.get(t) || t).join(", "));
    }
    if (p.state?.mistakeNote && p.state.mistakeNote.trim()) {
      parts.push(`Note: ${p.state.mistakeNote.trim()}`);
    }
    if (parts.length > 0) {
      divergedList.push(`${p.id} (${parts.join(" · ")})`);
    }
  });

  return {
    practiceStatus: computedPracticeStatus,
    score: liveScore,
    maxScore,
    accuracyPct,
    skippedCount: skippedProblems.length,
    skippedProblems,
    mistakeCategories: Array.from(mistakeNames),
    divergedStepsSummary:
      divergedList.length > 0 ? divergedList.join(" | ") : NO_DIVERGED_STEPS_SUMMARY,
    attemptDate: options?.attemptDate ?? new Date().toISOString().slice(0, 10),
    ...(statusOverride ? { statusOverride } : {}),
  };
}

/** Build the exact DrillDocument payload posted to `/api/sync-notion`. */
export function buildSyncPayload(
  currentDrill: DrillDocument,
  statusOverride: PracticeStatusOverride = null,
  options?: { attemptDate?: string }
): DrillDocument {
  return {
    ...currentDrill,
    sessionSummary: buildSessionSummary(currentDrill, statusOverride, options),
  };
}

/**
 * Stable JSON fingerprint of everything in a SessionSummary except `attemptDate`,
 * `syncedToNotionAt`, `notionPageId`, and `syncedFingerprint`.
 */
export function summaryFingerprint(
  summary: Partial<SessionSummary> | null | undefined
): string {
  if (!summary) return "";
  const canonical = {
    practiceStatus: summary.practiceStatus ?? "",
    score: typeof summary.score === "number" ? summary.score : 0,
    maxScore: typeof summary.maxScore === "number" ? summary.maxScore : 0,
    accuracyPct: typeof summary.accuracyPct === "number" ? summary.accuracyPct : 0,
    skippedCount: typeof summary.skippedCount === "number" ? summary.skippedCount : 0,
    skippedProblems: Array.isArray(summary.skippedProblems) ? summary.skippedProblems : [],
    mistakeCategories: Array.isArray(summary.mistakeCategories) ? summary.mistakeCategories : [],
    divergedStepsSummary:
      typeof summary.divergedStepsSummary === "string"
        ? summary.divergedStepsSummary
        : NO_DIVERGED_STEPS_SUMMARY,
  };
  return JSON.stringify(canonical);
}

/** Count how many meaningful sync fields differ between the previously synced summary and the current one. */
export function countSummaryChanges(
  prev: Partial<SessionSummary> | null | undefined,
  next: SessionSummary
): number {
  if (!prev) return 1;
  if (summaryFingerprint(prev) === summaryFingerprint(next)) return 0;

  let changes = 0;
  if ((prev.score ?? 0) !== next.score) changes += 1;
  if ((prev.practiceStatus ?? "") !== next.practiceStatus) changes += 1;

  const prevCats = new Set(Array.isArray(prev.mistakeCategories) ? prev.mistakeCategories : []);
  const nextCats = new Set(next.mistakeCategories);
  let catDiff = 0;
  prevCats.forEach((c) => {
    if (!nextCats.has(c)) catDiff += 1;
  });
  nextCats.forEach((c) => {
    if (!prevCats.has(c)) catDiff += 1;
  });
  if (catDiff > 0) changes += catDiff;

  const splitLines = (raw?: string | null) =>
    !raw || raw === NO_DIVERGED_STEPS_SUMMARY ? [] : raw.split(" | ").filter(Boolean);
  const prevLines = new Map<string, string>();
  for (const line of splitLines(prev.divergedStepsSummary)) {
    const id = line.split(" ", 1)[0] || line;
    prevLines.set(id, line);
  }
  const nextLines = new Map<string, string>();
  for (const line of splitLines(next.divergedStepsSummary)) {
    const id = line.split(" ", 1)[0] || line;
    nextLines.set(id, line);
  }
  const allIds = new Set([...Array.from(prevLines.keys()), ...Array.from(nextLines.keys())]);
  allIds.forEach((id) => {
    if (prevLines.get(id) !== nextLines.get(id)) {
      changes += 1;
    }
  });

  if ((prev.skippedCount ?? 0) !== (next.skippedCount ?? 0) && changes === 0) {
    changes += 1;
  }

  return Math.max(1, changes);
}

/**
 * Unit codes a drill covers (mirrors `notion_sync.drill_sync.covered_units`):
 * a unit drill covers its own unitCode; a chapter mixed drill covers every problem's unitCode.
 */
export function getCoveredUnits(drill: DrillDocument): string[] {
  const seen = new Set<string>();
  const codes: string[] = [];

  if (drill.unitCode && drill.unitCode.includes("-U")) {
    seen.add(drill.unitCode);
    codes.push(drill.unitCode);
  }

  for (const prob of drill.problems || []) {
    const pUnit = typeof prob.unitCode === "string" ? prob.unitCode.trim() : "";
    if (pUnit && !seen.has(pUnit)) {
      seen.add(pUnit);
      codes.push(pUnit);
    }
  }

  if (codes.length === 0 && drill.unitCode) {
    codes.push(drill.unitCode);
  }

  return codes;
}

/** Build the UI Sync Preview directly from `buildSessionSummary` + read-only schedule cache. */
export function buildSyncPreview(
  drill: DrillDocument,
  statusOverride: PracticeStatusOverride = null,
  scheduleCache?: Record<string, ReviewScheduleEntry> | null
): SyncPreview {
  const summary = buildSessionSummary(drill, statusOverride);
  const statusReason = statusOverride
    ? "set manually"
    : summary.practiceStatus === "Graded"
    ? "80% or higher"
    : "under 80%";

  const logLines =
    summary.divergedStepsSummary && summary.divergedStepsSummary !== NO_DIVERGED_STEPS_SUMMARY
      ? summary.divergedStepsSummary.split(" | ").filter(Boolean)
      : [];

  const unitTitle = plainTitle(drill.unitTitle) || drill.unitCode;
  const coveredCodes = getCoveredUnits(drill);
  const coveredUnits: CoveredUnitPreview[] = coveredCodes.map((code) => {
    const cached = scheduleCache?.[code];
    return {
      unitCode: code,
      title:
        plainTitle(typeof cached?.title === "string" ? cached.title : "") ||
        (code === drill.unitCode ? unitTitle : code),
      mastery: typeof cached?.mastery === "number" ? cached.mastery : null,
      lastReviewed: typeof cached?.lastReviewed === "string" ? cached.lastReviewed : null,
      nextReview: typeof cached?.nextReview === "string" ? cached.nextReview : null,
      masteryCap: cached?.masteryCap ?? null,
    };
  });

  let unansweredCount = 0;
  let hasAnyAttempt = false;
  for (const p of drill.problems || []) {
    if (classifyReviewOutcome(p.state) === "unanswered") {
      unansweredCount += 1;
    }
    if (hasSubstantiveAttempt(p.state)) {
      hasAnyAttempt = true;
    }
  }

  return {
    summary,
    statusReason,
    mistakeCategories: summary.mistakeCategories,
    logLines,
    unitTitle,
    coveredUnits,
    unansweredCount,
    skippedCount: summary.skippedCount ?? 0,
    hasAnyAttempt,
  };
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Format a YYYY-MM-DD date string as "21 Nov" without timezone drift. */
export function formatShortDate(isoDate?: string | null): string {
  if (typeof isoDate !== "string") return "";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(isoDate.trim());
  if (!m) return isoDate.trim();
  const monthIdx = Number(m[2]) - 1;
  const day = Number(m[3]);
  if (monthIdx < 0 || monthIdx > 11 || !Number.isFinite(day)) return isoDate.trim();
  return `${day} ${MONTHS[monthIdx]}`;
}

/** Format an ISO timestamp as "today 14:05" (if same local date) or "19 Nov 14:05". */
export function formatSyncTimestamp(
  iso?: string | null,
  now: Date = new Date()
): { shortTime: string; relativeLabel: string } {
  if (!iso) return { shortTime: "", relativeLabel: "" };
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return { shortTime: "", relativeLabel: "" };
  }
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  const shortTime = `${hh}:${mm}`;
  const isSameLocalDay =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();
  const relativeLabel = isSameLocalDay
    ? `today ${shortTime}`
    : `${date.getDate()} ${MONTHS[date.getMonth()]} ${shortTime}`;
  return { shortTime, relativeLabel };
}
