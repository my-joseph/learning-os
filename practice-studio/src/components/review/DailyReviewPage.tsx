"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { sendPracticeAction } from "@/lib/practiceActions";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Check,
  PenLine,
} from "lucide-react";
import {
  DrillDocument,
  MistakeTag,
  Problem,
} from "@/types/drill";
import { MathWorkspace } from "@/components/math/MathWorkspace";
import { CodeDashboard } from "@/components/code/CodeDashboard";
import {
  computeResetProblemTransition,
  computeSetupRevealTransition,
  computeSolutionRevealTransition,
  mergeRevealedPatchIntoDrill,
  normalizeLoadedDrillDoc,
  RevealPart,
} from "@/hooks/useDrill";
import { useTheme } from "@/hooks/useTheme";
import { ThemeToggleButton } from "@/components/ui/ThemeToggleButton";
import { Button } from "@/components/ui/shadcn/Button";
import { Card } from "@/components/ui/shadcn/Card";
import { Input } from "@/components/ui/shadcn/Input";
import { Skeleton } from "@/components/ui/shadcn/Skeleton";
import { applyDivergedStep, toggleMistakeTag } from "@/lib/applyCheckResult";
import { applySelfScore, isLockedAfterCorrect } from "@/lib/scoring";
import { labToDrillDocument, type LabDetailResponse } from "@/lib/labModel";
import { readLastDrillId } from "@/lib/lastDrillStorage";
import { hasSubstantiveAttempt } from "@/lib/reviewGuard";
import { statusTone } from "@/lib/statusTone";
import type { ReviewItem } from "@/lib/reviewItems";
import {
  executeReviewItemCheck,
  executeReviewItemSkip,
  formatReviewScheduleHint,
  getMissedReviewItems,
  MissedReviewItem,
  prepareProblemForReviewItem,
  REVIEW_BATCH_SIZE,
  reviewItemKey,
  ReviewSessionItemOutcome,
  ReviewSessionSummary,
  saveReviewProblemState,
  summarizeReviewSession,
} from "@/lib/reviewSession";
import type { SimilarProgressPatch } from "@/hooks/useSimilarTabs";
import { isTimestampInCycle } from "@/lib/reviewGuard";
import { isInCycle } from "@/lib/similarTabs";
import { drillHref, isLabId } from "@/lib/routes";
import {
  createTelemetryTimerState,
  getAttemptElapsedMs,
  getProblemDisplayMs,
  pauseTimer,
  recordHint,
  resumeTimer,
  setActiveProblem,
  setVisibility,
  TelemetryTimerState,
} from "@/lib/telemetryTimer";
import { plainTitle, trapName } from "@/lib/titleText";
import { formatReviewDueDate } from "@/lib/reviewDate";

export interface DailyReviewViewProps {
  loading?: boolean;
  error?: string | null;
  items: ReviewItem[];
  currentIndex?: number;
  currentProblem?: Problem | null;
  currentDrillMistakeTags?: MistakeTag[];
  isLoadingProblem?: boolean;
  completed?: boolean;
  summary?: ReviewSessionSummary;
  nextDueDate?: string | null;
  today?: string | null;
  unitTitles?: Record<string, string>;
  currentUnitTitle?: string;
  currentOutcome?: ReviewSessionItemOutcome | null;
  stillDueCount?: number;
  missedItems?: MissedReviewItem[];
  onReviewMore?: () => void;
  lastDrillHref?: string;
  revealedTrapTag?: string | null;
  revisitNoteDraft?: string;
  questionTimerMs?: number;
  totalTimerMs?: number;
  isTimerPaused?: boolean;
  theme?: "light" | "dark";
  onToggleTheme?: () => void;
  onToggleTimerPause?: () => void;
  onInputChange?: (val: string) => void;
  onCheckAnswer?: (inputOverride?: string) => Promise<void> | void;
  onSkip?: () => void;
  onResetProblem?: () => void;
  onHintRevealed?: () => void;
  onSetupRevealed?: () => void;
  onSolutionRevealed?: () => void;
  onExampleViewed?: (viewedAt: string) => void;
  onSimilarProgressSync?: (patch: SimilarProgressPatch) => void;
  onVariantModeChange?: (inVariantMode: boolean) => void;
  onMarkDivergedStep?: (stepIdx: number) => void;
  onSetScore?: (score: number | null) => void;
  onToggleMistakeTag?: (tagId: string) => void;
  onMistakeNoteChange?: (note: string) => void;
  onRevisitNoteChange?: (note: string) => void;
  onPrevItem?: () => void;
  onNextItem?: () => void;
}

const noop = () => {};
const REVIEW_SESSION_STORAGE_PREFIX = "learningos:review-session:";
const reviewStorageKey = (scope: string | null) => `${REVIEW_SESSION_STORAGE_PREFIX}${scope || "all"}`;

function currentLocalDate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Pure presentational view for the `/review` Daily Review page across all states:
 * loading, empty ("Nothing to review today" + next due date), active item (with optional
 * "Your note from last time: …" above the problem, strict zero-leak before an attempt,
 * post-answer "Trap: <plain title>", and post-correct "Next time I will…" revisit note input),
 * and end screen (correct / total, moved up / down a level, next due date, link back to last drill).
 */
export const DailyReviewView: React.FC<DailyReviewViewProps> = ({
  loading = false,
  error = null,
  items,
  currentIndex = 0,
  currentProblem = null,
  currentDrillMistakeTags = [],
  isLoadingProblem = false,
  completed = false,
  summary,
  nextDueDate = null,
  today = null,
  unitTitles = {},
  currentUnitTitle,
  currentOutcome = null,
  stillDueCount = 0,
  missedItems = [],
  onReviewMore,
  lastDrillHref,
  revealedTrapTag = null,
  revisitNoteDraft = "",
  questionTimerMs = 0,
  totalTimerMs = 0,
  isTimerPaused = false,
  theme = "light",
  onToggleTheme,
  onToggleTimerPause,
  onInputChange = noop,
  onCheckAnswer = noop,
  onSkip,
  onResetProblem = noop,
  onHintRevealed,
  onSetupRevealed,
  onSolutionRevealed,
  onExampleViewed,
  onSimilarProgressSync,
  onVariantModeChange,
  onMarkDivergedStep = noop,
  onSetScore = noop,
  onToggleMistakeTag = noop,
  onMistakeNoteChange = noop,
  onRevisitNoteChange,
  onPrevItem,
  onNextItem,
}) => {
  const fallbackLastDrillId =
    items.length > 0 ? items[items.length - 1]?.drillId : null;
  const resolvedBackHref =
    lastDrillHref ||
    (fallbackLastDrillId ? drillHref(fallbackLastDrillId) : "/");

  const currentItem =
    !loading && !completed && items.length > 0
      ? items[Math.max(0, Math.min(currentIndex, items.length - 1))]
      : null;

  const showProgressCounter =
    !loading && !completed && items.length > 0 && currentItem !== null;

  const computedSummary: ReviewSessionSummary =
    summary ?? summarizeReviewSession(items, {}, nextDueDate);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 px-4 lg:px-16 py-4 sm:py-6 transition-colors">
      <div className="mx-auto w-full max-w-[720px] space-y-4">
        {/* Slim header row: one h1 ("Daily review"), progress "3 of 8", back link, theme toggle */}
        <header className="bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 rounded-2xl px-3.5 py-2.5 shadow-sm flex items-center justify-between gap-3">
          <div className="flex items-baseline gap-3 min-w-0">
            <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight">
              Daily review
            </h1>
            {showProgressCounter && (
              <span
                aria-label="Review progress"
                className="text-sm font-display tabular-nums text-zinc-500 dark:text-zinc-400"
              >
                Review {currentIndex + 1} of {items.length}
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <Link
              href={resolvedBackHref}
              className="inline-flex items-center gap-1.5 h-8 px-2.5 rounded-lg text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Back to drill</span>
            </Link>

            {onToggleTheme && (
              <ThemeToggleButton
                theme={theme}
                onToggle={onToggleTheme}
                className="text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800"
              />
            )}
          </div>
        </header>

        <main className="space-y-4">
          {loading ? (
            <Card
              role="status"
              aria-label="Loading daily review"
              className="shadow-none p-6 space-y-4"
            >
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Loading daily review…
              </p>
              <div className="space-y-3">
                <Skeleton className="h-4 w-1/3 rounded-lg" />
                <Skeleton className="h-20 w-full rounded-xl bg-zinc-200 dark:bg-zinc-800" />
                <Skeleton className="h-10 w-1/2 rounded-xl" />
              </div>
            </Card>
          ) : error ? (
            <Card className="shadow-none p-6 space-y-3">
              <p className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                Could not load daily review
              </p>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">{error}</p>
              <Button asChild variant="primary" size="compact" className="rounded-xl px-3.5">
                <Link href={resolvedBackHref}>
                  <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>Back to drill</span>
                </Link>
              </Button>
            </Card>
          ) : items.length === 0 ? (
            /* Empty state when nothing is due */
            <Card className="shadow-none p-6 sm:p-8 space-y-4">
              <div className="space-y-1.5">
                <p className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  Nothing to review today
                </p>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  {nextDueDate
                    ? `Next due: ${nextDueDate}`
                    : "No upcoming reviews scheduled yet."}
                </p>
              </div>
              <div>
                <Button asChild variant="primary" size="compact" className="rounded-xl px-4">
                  <Link href={resolvedBackHref}>
                    <span>Back to drill</span>
                    <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                  </Link>
                </Button>
              </div>
            </Card>
          ) : completed ? (
            /* End screen */
            <Card className="shadow-none p-6 sm:p-8 space-y-6">
              <div className="flex items-start gap-3">
                <span className={`w-8 h-8 rounded-full ${statusTone.correct.iconCircle} inline-flex items-center justify-center shrink-0`}>
                  <Check className="w-4 h-4" aria-hidden="true" />
                </span>
                <div className="space-y-1">
                  <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                    Review complete
                  </h2>
                  <p className="text-sm font-display tabular-nums text-zinc-600 dark:text-zinc-400">
                    {computedSummary.correctCount} / {computedSummary.totalCount} correct
                    {stillDueCount > 0 ? ` · Still due ${stillDueCount}` : ""}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-surface-panel px-3.5 py-2.5 space-y-0.5">
                  <div className="text-xs text-zinc-500 dark:text-zinc-400">
                    Moved up
                  </div>
                  <div className={`font-display font-semibold ${statusTone.correct.text} tabular-nums`}>
                    {computedSummary.movedUpCount} moved up a level
                  </div>
                </div>

                <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-surface-panel px-3.5 py-2.5 space-y-0.5">
                  <div className="text-xs text-zinc-500 dark:text-zinc-400">
                    Moved down
                  </div>
                  <div className={`font-display font-semibold ${statusTone.wrong.text} tabular-nums`}>
                    {computedSummary.movedDownCount} moved down a level
                  </div>
                </div>

                <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-surface-panel px-3.5 py-2.5 space-y-0.5">
                  <div className="text-xs text-zinc-500 dark:text-zinc-400">
                    Next due
                  </div>
                  <div className="font-display font-semibold text-zinc-900 dark:text-zinc-100 tabular-nums">
                    {formatReviewDueDate(computedSummary.nextDueDate, today || undefined)}
                  </div>
                </div>
              </div>

              {missedItems.length > 0 && (
                <div className="space-y-2">
                  {(["Missed", "Skipped", "Correct on retry"] as const).map((group) => {
                    const rows = missedItems.filter((item) => item.group === group);
                    if (!rows.length) return null;
                    return (
                      <section key={group} className="space-y-1.5">
                        <h3 className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                          {group} ({rows.length})
                        </h3>
                        <ul className="divide-y divide-zinc-200 dark:divide-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-surface-panel/60">
                          {rows.map((missed) => (
                            <li key={`${missed.drillId}/${missed.qid}`}>
                              <Link
                                href={`${missed.href}&review=missed`}
                                className="flex items-start justify-between gap-3 px-3.5 py-2.5 text-xs hover:bg-zinc-100/80 dark:hover:bg-zinc-900 transition-colors"
                              >
                                <span className="min-w-0 whitespace-normal text-zinc-800 dark:text-zinc-200">
                                  <span className="block font-medium leading-snug">{missed.unitTitle}</span>
                                  {missed.questionLine && <span className="block mt-0.5 text-zinc-500 dark:text-zinc-400 leading-snug">{missed.questionLine}</span>}
                                </span>
                                <span className="inline-flex items-center gap-1 text-zinc-500 dark:text-zinc-400 shrink-0">
                                  <span>Open in drill</span>
                                  <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
                                </span>
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </section>
                    );
                  })}
                </div>
              )}

              <div className="flex flex-wrap items-center gap-3">
                {stillDueCount > 0 && onReviewMore ? (
                  <>
                    <button
                      type="button"
                      onClick={onReviewMore}
                      className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-colors"
                    >
                      <span>
                        Review {Math.min(REVIEW_BATCH_SIZE, stillDueCount)} more
                      </span>
                      <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                    </button>
                    <Link
                      href={resolvedBackHref}
                      className="inline-flex items-center gap-1.5 h-10 px-3 rounded-xl text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                    >
                      <span>Back to drill</span>
                    </Link>
                  </>
                ) : (
                  <Link
                    href={resolvedBackHref}
                    className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-colors"
                  >
                    <span>Back to drill</span>
                    <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                  </Link>
                )}
              </div>
            </Card>
          ) : isLoadingProblem || !currentProblem || !currentItem ? (
            <Card
              role="status"
              aria-label="Loading review problem"
              className="shadow-none p-6 space-y-4"
            >
              <Skeleton className="h-4 w-1/4 rounded-lg" />
              <Skeleton className="h-20 w-full rounded-xl bg-zinc-200 dark:bg-zinc-800" />
              <Skeleton className="h-10 w-1/2 rounded-xl" />
            </Card>
          ) : (
            (() => {
              // The problem was already redacted/reset once when its drill loaded
              // (prepareProblemForReviewItem). Re-running it here on every render wiped the
              // learner's typing, so render the live in-session problem as is.
              const safeProblem = currentProblem;
              const hasAttempt = hasSubstantiveAttempt(safeProblem.state);
              const isCorrect =
                hasAttempt &&
                (safeProblem.state.lastCheck?.verdict === "correct" ||
                  safeProblem.state.score === 1 ||
                  Boolean(
                    safeProblem.state.attempts?.some((a) => a.verdict === "correct")
                  ));

              // Strictly reveal trap title ONLY after the learner has answered (never before).
              const rawTrapTag = hasAttempt && currentProblem.state.lastCheck?.verdict === "incorrect" && currentProblem.state.lastCheck.trapMatched
                ? revealedTrapTag ||
                  currentItem.commonTrapTag ||
                  currentProblem.commonTrapTag ||
                  null
                : null;
              const plainTrapTitle = rawTrapTag ? trapName(rawTrapTag) : "";

              const reviewSupplement = hasAttempt ? (
                <div className="space-y-3 pt-1">
                  {plainTrapTitle && (
                    <p className="text-xs text-zinc-600 dark:text-zinc-400">
                      Trap:{" "}
                      <span className="font-medium text-zinc-800 dark:text-zinc-200">
                        {plainTrapTitle}
                      </span>
                    </p>
                  )}

                  {isCorrect && (
                    <div className="space-y-1.5">
                      <label
                        htmlFor={`revisit-note-${safeProblem.id}`}
                        className="block text-xs font-medium text-zinc-600 dark:text-zinc-400"
                      >
                        Next time I will…
                      </label>
                      <div className="flex items-center gap-2 bg-surface-panel dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl px-3 py-2 transition-colors focus-within:border-indigo-600 dark:focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-600/20 dark:focus-within:ring-indigo-400/25">
                        <PenLine className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400 shrink-0" />
                        <Input
                          id={`revisit-note-${safeProblem.id}`}
                          type="text"
                          variant="embedded"
                          value={revisitNoteDraft}
                          onChange={(e) => onRevisitNoteChange?.(e.target.value)}
                          aria-label="Next time I will…"
                          placeholder="Next time I will…"
                          className="text-xs"
                        />
                      </div>
                    </div>
                  )}
                </div>
              ) : null;

              const noteFromLastTime =
                typeof currentItem.revisitNote === "string" &&
                currentItem.revisitNote.trim()
                  ? currentItem.revisitNote.trim()
                  : null;

              const resolvedUnitTitle =
                plainTitle(
                  currentUnitTitle ||
                    unitTitles[currentItem.unitCode] ||
                    currentItem.unitCode
                ) || currentItem.unitCode;
              const reviewScheduleNote = hasAttempt
                ? formatReviewScheduleHint(currentOutcome, today)
                : null;

              return (
                <div className="space-y-3">
                  {/* Quiet revisitNote from last time ABOVE the problem */}
                  {noteFromLastTime && (
                    <Card
                      role="note"
                      className="rounded-xl shadow-none px-4 py-3 text-sm text-zinc-700 dark:text-zinc-300"
                    >
                      <span className="text-zinc-500 dark:text-zinc-400">
                        Your note from last time:{" "}
                      </span>
                      <span>{noteFromLastTime}</span>
                    </Card>
                  )}

                  {currentItem.subject === "PRG" ? (
                    <CodeDashboard
                      key={`${currentItem.drillId}:${safeProblem.id}`}
                      problem={safeProblem}
                      drillId={currentItem.drillId}
                      index={currentIndex}
                      totalQuestions={items.length}
                      drillTitle=""
                      mistakeTags={currentDrillMistakeTags}
                      onInputChange={onInputChange}
                      onCheckAnswer={onCheckAnswer}
                      onSkip={onSkip}
                      onMarkDivergedStep={onMarkDivergedStep}
                      onSetScore={onSetScore}
                      onToggleMistakeTag={onToggleMistakeTag}
                      onMistakeNoteChange={onMistakeNoteChange}
                      onResetProblem={onResetProblem}
                      onHintRevealed={onHintRevealed}
                      onSolutionRevealed={onSolutionRevealed}
                      onPrevQuestion={onPrevItem}
                      onNextQuestion={onNextItem}
                      onOpenReview={onNextItem}
                      questionTimerMs={questionTimerMs}
                      totalTimerMs={totalTimerMs}
                      isTimerPaused={isTimerPaused}
                      onToggleTimerPause={onToggleTimerPause}
                      openInDrillHref={drillHref(currentItem.drillId, currentItem.qid)}
                      reviewSupplement={reviewSupplement}
                      isReviewSession
                      isCorrectOnRetry={Boolean(currentOutcome?.correctOnRetry)}
                      reviewUnitTitle={resolvedUnitTitle}
                      reviewScheduleNote={reviewScheduleNote}
                      nextCardLabel={currentIndex === items.length - 1 ? "Finish" : "Next"}
                      lastQuestionNavLabel="Finish"
                    />
                  ) : (
                    <MathWorkspace
                      key={`${currentItem.drillId}:${safeProblem.id}`}
                      problem={safeProblem}
                      drillId={currentItem.drillId}
                      index={currentIndex}
                      totalQuestions={items.length}
                      unitCode={currentItem.unitCode}
                      drillTitle=""
                      mistakeTags={currentDrillMistakeTags}
                      onInputChange={onInputChange}
                      onCheckAnswer={onCheckAnswer}
                      onSkip={onSkip}
                      onMarkDivergedStep={onMarkDivergedStep}
                      onSetScore={onSetScore}
                      onToggleMistakeTag={onToggleMistakeTag}
                      onMistakeNoteChange={onMistakeNoteChange}
                      onResetProblem={onResetProblem}
                      onHintRevealed={onHintRevealed}
                      onSetupRevealed={onSetupRevealed}
                      onSolutionRevealed={onSolutionRevealed}
                      onExampleViewed={onExampleViewed}
                      onSimilarProgressSync={onSimilarProgressSync}
                      onVariantModeChange={onVariantModeChange}
                      onPrevQuestion={onPrevItem}
                      onNextQuestion={onNextItem}
                      onOpenReview={onNextItem}
                      questionTimerMs={questionTimerMs}
                      totalTimerMs={totalTimerMs}
                      isTimerPaused={isTimerPaused}
                      onToggleTimerPause={onToggleTimerPause}
                      reviewSupplement={reviewSupplement}
                      isReviewSession
                      isCorrectOnRetry={Boolean(currentOutcome?.correctOnRetry)}
                      reviewUnitTitle={resolvedUnitTitle}
                      reviewScheduleNote={reviewScheduleNote}
                      nextCardLabel={currentIndex === items.length - 1 ? "Finish" : "Next"}
                      lastQuestionNavLabel="Finish"
                    />
                  )}
                </div>
              );
            })()
          )}
        </main>
      </div>
    </div>
  );
};

/**
 * Interactive Daily Review page controller for `/review`:
 * fetches today's interleaved due items (`GET /api/review-items?limit=8`), loads each item's
 * original problem in zero-leak review mode, manages the per-question timer, records check
 * outcomes via `POST /api/review-items` + `POST /api/save-state`, and saves optional
 * `"Next time I will…"` revisit notes.
 */
export const DailyReviewPage: React.FC = () => {
  const { theme, handleToggleTheme } = useTheme();
  const searchParams = useSearchParams();

  const rawScope = searchParams.get("scope");
  const rawUnit = searchParams.get("unit");
  const rawTrap = searchParams.get("trap");
  const activeScope =
    rawScope?.trim() ||
    (rawUnit?.trim() ? `unit:${rawUnit.trim()}` : null) ||
    (rawTrap?.trim() ? `trap:${rawTrap.trim()}` : null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [today, setToday] = useState<string>("");
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [totalDue, setTotalDue] = useState<number>(0);
  const [unitTitles, setUnitTitles] = useState<Record<string, string>>({});
  const [initialNextDueDate, setInitialNextDueDate] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [completed, setCompleted] = useState(false);
  const [batchCounter, setBatchCounter] = useState(0);

  const [drillsByKey, setDrillsByKey] = useState<Record<string, DrillDocument>>({});
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const [outcomes, setOutcomes] = useState<Record<string, ReviewSessionItemOutcome>>({});
  const [hintsByKey, setHintsByKey] = useState<Record<string, number>>({});
  const [revisitDraftByKey, setRevisitDraftByKey] = useState<Record<string, string>>({});
  const [lastDrillHref, setLastDrillHref] = useState<string>("/");

  // Per-question telemetry timer
  const timerStateRef = useRef<TelemetryTimerState>(createTelemetryTimerState());
  const [timerState, setTimerState] = useState<TelemetryTimerState>(() => timerStateRef.current);
  const [timerNow, setTimerNow] = useState<number>(() => Date.now());

  const commitTimerState = useCallback(
    (next: TelemetryTimerState, now: number = Date.now()) => {
      timerStateRef.current = next;
      setTimerState(next);
      setTimerNow(now);
    },
    []
  );

  // Read last opened drill ID on mount
  useEffect(() => {
    const mathId = readLastDrillId("math");
    const codeId = readLastDrillId("code");
    const candidate = mathId || codeId;
    if (candidate) {
      setLastDrillHref(drillHref(candidate));
    }
  }, []);

  // Load due items from GET /api/review-items?limit=8 (preserving optional scope)
  useEffect(() => {
    let cancelled = false;
    if (batchCounter === 0) {
      try {
        const saved = window.sessionStorage.getItem(reviewStorageKey(activeScope));
        if (saved) {
          const snapshot = JSON.parse(saved) as {
            completed?: boolean; items?: ReviewItem[]; outcomes?: Record<string, ReviewSessionItemOutcome>;
            totalDue?: number; unitTitles?: Record<string, string>; today?: string;
            nextDueDate?: string | null; lastDrillHref?: string;
          };
          if (Array.isArray(snapshot.items) && snapshot.completed === true && snapshot.today === currentLocalDate()) {
            setItems(snapshot.items);
            setOutcomes(snapshot.outcomes || {});
            setTotalDue(snapshot.totalDue || snapshot.items.length);
            setUnitTitles(snapshot.unitTitles || {});
            setToday(snapshot.today || "");
            setInitialNextDueDate(snapshot.nextDueDate || null);
            setLastDrillHref(snapshot.lastDrillHref || "/");
            setCurrentIndex(snapshot.items.length - 1);
            setCompleted(true);
            setLoading(false);
            return () => { cancelled = true; };
          }
        }
      } catch {
        window.sessionStorage.removeItem(reviewStorageKey(activeScope));
      }
    }
    setLoading(true);
    setError(null);

    const qs = new URLSearchParams({ limit: String(REVIEW_BATCH_SIZE) });
    if (activeScope) {
      qs.set("scope", activeScope);
    }

    fetch(`/api/review-items?${qs.toString()}`, { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as {
          today?: string;
          items?: ReviewItem[];
          totalDue?: number;
          nextDueDate?: string | null;
          unitTitles?: Record<string, string>;
        };
      })
      .then((data) => {
        if (cancelled) return;
        const dueList = Array.isArray(data.items) ? data.items : [];
        setToday(typeof data.today === "string" ? data.today : "");
        setItems(dueList);
        setTotalDue(
          typeof data.totalDue === "number" ? data.totalDue : dueList.length
        );
        setUnitTitles(
          data.unitTitles && typeof data.unitTitles === "object"
            ? data.unitTitles
            : {}
        );
        setInitialNextDueDate(
          typeof data.nextDueDate === "string" ? data.nextDueDate : null
        );
        setDrillsByKey({});
        setOutcomes({});
        setHintsByKey({});
        setRevisitDraftByKey({});
        setCurrentIndex(0);
        setCompleted(false);
        if (dueList.length > 0) {
          const lastItem = dueList[dueList.length - 1];
          setLastDrillHref((prev) =>
            prev && prev !== "/" ? prev : drillHref(lastItem.drillId)
          );
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load review items");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeScope, batchCounter]);

  const reviewCycles = useRef(new Map<string, Promise<string | null>>());

  const handleReviewMore = useCallback(() => {
    reviewCycles.current.clear();
    window.sessionStorage.removeItem(reviewStorageKey(activeScope));
    setCompleted(false);
    setBatchCounter((n) => n + 1);
  }, [activeScope]);

  const currentItem =
    !loading && !completed && items.length > 0
      ? items[Math.max(0, Math.min(currentIndex, items.length - 1))] ?? null
      : null;
  const currentKey = currentItem
    ? reviewItemKey(currentItem.drillId, currentItem.qid)
    : null;
  const currentDrill = currentKey ? drillsByKey[currentKey] ?? null : null;
  const currentProblem =
    currentDrill && currentItem
      ? currentDrill.problems.find((p) => p.id === currentItem.qid) ?? null
      : null;

  // Load the current item's drill document if not yet loaded
  useEffect(() => {
    if (!currentItem || !currentKey) return;
    if (drillsByKey[currentKey]) return;

    let cancelled = false;
    setLoadingKey(currentKey);

    const endpoint = isLabId(currentItem.drillId)
      ? `/api/lab?id=${encodeURIComponent(currentItem.drillId)}`
      : `/api/drill?id=${encodeURIComponent(currentItem.drillId)}&review=1`;

    fetch(endpoint, { cache: "no-store" })
      .then(async (res) => {
        if (res.status === 404) {
          if (!cancelled) {
            const remaining = items.filter((item) => item.drillId !== currentItem.drillId || item.qid !== currentItem.qid);
            window.sessionStorage.removeItem(reviewStorageKey(activeScope));
            setItems(remaining);
            setTotalDue((count) => Math.max(0, count - 1));
            if (currentIndex >= remaining.length) setCompleted(true);
          }
          return;
        }
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const raw = await res.json();
        const doc: DrillDocument = isLabId(currentItem.drillId)
          ? labToDrillDocument(raw as LabDetailResponse)
          : (raw as DrillDocument);
        const normalized = normalizeLoadedDrillDoc(doc);
        const prepared: DrillDocument = {
          ...normalized,
          problems: normalized.problems.map((p) =>
            p.id === currentItem.qid
              ? prepareProblemForReviewItem(p, currentItem)
              : p
          ),
        };
        if (!cancelled) {
          setDrillsByKey((prev) => ({ ...prev, [currentKey]: prepared }));
          if (currentItem.unitCode && prepared.unitTitle) {
            const cleanTitle = plainTitle(prepared.unitTitle);
            if (cleanTitle) {
              setUnitTitles((prev) =>
                prev[currentItem.unitCode]
                  ? prev
                  : { ...prev, [currentItem.unitCode]: cleanTitle }
              );
            }
          }
        }
      })
      .catch(() => {
        // leave problem null if load fails
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingKey((prev) => (prev === currentKey ? null : prev));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [currentItem, currentKey, drillsByKey, items, currentIndex, activeScope]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (today && today !== currentLocalDate()) {
        window.sessionStorage.removeItem(reviewStorageKey(activeScope));
        setCompleted(false);
        setItems([]);
        setCurrentIndex(0);
        setToday(currentLocalDate());
        setBatchCounter((count) => count + 1);
      }
    }, 60_000);
    return () => window.clearInterval(timer);
  }, [activeScope, completed, today]);

  // Activate per-question timer on current item
  useEffect(() => {
    const activeProbId =
      !loading && !completed && currentKey ? currentKey : null;
    if (timerStateRef.current.activeProblemId === activeProbId) return;
    const now = Date.now();
    commitTimerState(setActiveProblem(timerStateRef.current, activeProbId, now), now);
  }, [loading, completed, currentKey, commitTimerState]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      const isVisible = !document.hidden;
      const now = Date.now();
      commitTimerState(setVisibility(timerStateRef.current, isVisible, now), now);
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [commitTimerState]);

  const isTimerRunning =
    Boolean(currentKey) &&
    !loading &&
    !completed &&
    timerState.activeProblemId !== null &&
    timerState.isDocumentVisible &&
    !timerState.paused;

  useEffect(() => {
    if (!isTimerRunning || !currentKey) return;
    let lastWholeSec = Math.floor(
      getAttemptElapsedMs(timerStateRef.current, currentKey, Date.now()) / 1000
    );
    const id = window.setInterval(() => {
      const now = Date.now();
      const wholeSec = Math.floor(
        getAttemptElapsedMs(timerStateRef.current, currentKey, now) / 1000
      );
      if (wholeSec !== lastWholeSec) {
        lastWholeSec = wholeSec;
        setTimerNow(now);
      }
    }, 250);
    return () => window.clearInterval(id);
  }, [isTimerRunning, currentKey]);

  const pausedBeforeVariantRef = useRef<boolean | null>(null);
  const handleToggleTimerPause = useCallback(() => {
    const now = Date.now();
    const next = timerStateRef.current.paused
      ? resumeTimer(timerStateRef.current, now)
      : pauseTimer(timerStateRef.current, now);
    commitTimerState(next, now);
  }, [commitTimerState]);

  const handleVariantModeChange = useCallback(
    (inVariantMode: boolean) => {
      const now = Date.now();
      if (inVariantMode) {
        if (pausedBeforeVariantRef.current === null) {
          pausedBeforeVariantRef.current = timerStateRef.current.paused;
        }
        if (!timerStateRef.current.paused) {
          commitTimerState(pauseTimer(timerStateRef.current, now), now);
        }
      } else if (pausedBeforeVariantRef.current !== null) {
        const wasPaused = pausedBeforeVariantRef.current;
        pausedBeforeVariantRef.current = null;
        if (!wasPaused && timerStateRef.current.paused) {
          commitTimerState(resumeTimer(timerStateRef.current, now), now);
        }
      }
    },
    [commitTimerState]
  );

  const updateCurrentProblem = useCallback(
    (
      updater: (prob: Problem) => Problem,
      saveField?: "divergedStep" | "mistakeNote" | "revisitNote"
    ) => {
      if (!currentKey || !currentItem) return;
      setDrillsByKey((prev) => {
        const doc = prev[currentKey];
        if (!doc) return prev;
        const updatedProblems = doc.problems.map((p) =>
          p.id === currentItem.qid ? updater(p) : p
        );
        const updatedDoc: DrillDocument = { ...doc, problems: updatedProblems };
        if (saveField) {
          const updatedProb = updatedProblems.find((p) => p.id === currentItem.qid);
          if (updatedProb) {
            void saveReviewProblemState(
              doc.drillId,
              currentItem.unitCode || doc.unitCode,
              currentItem.qid,
              {
                cycleStartedAt: updatedProb.state.cycleStartedAt,
                [saveField]: updatedProb.state[saveField],
              }
            );
          }
        }
        return { ...prev, [currentKey]: updatedDoc };
      });
    },
    [currentKey, currentItem]
  );

  const incrementHintsUsed = useCallback(() => {
    if (!currentKey) return;
    setHintsByKey((prev) => ({
      ...prev,
      [currentKey]: (prev[currentKey] || 0) + 1,
    }));
  }, [currentKey]);

  const ensureReviewCycle = useCallback(async (doc: DrillDocument, item: ReviewItem) => {
    const key = reviewItemKey(item.drillId, item.qid);
    let started = reviewCycles.current.get(key);
    if (!started) {
      started = sendPracticeAction(item.drillId, item.qid, { action: "start-review" })
        .then((result) => result?.cycleStartedAt ?? null);
      reviewCycles.current.set(key, started);
    }
    const cycle = await started;
    if (!cycle) {
      if (reviewCycles.current.get(key) === started) reviewCycles.current.delete(key);
      return null;
    }
    return {
      ...doc,
      problems: doc.problems.map((p) => p.id === item.qid
        ? { ...p, state: { ...p.state, cycleStartedAt: cycle } }
        : p),
    };
  }, []);

  const handleHintRevealed = useCallback(async () => {
    if (!currentKey || !currentItem || !currentProblem || !currentDrill) return;
    if (isLockedAfterCorrect(currentProblem.state)) return;
    const doc = await ensureReviewCycle(currentDrill, currentItem);
    const cycle = doc?.problems.find((p) => p.id === currentItem.qid)?.state.cycleStartedAt;
    if (!cycle || !await sendPracticeAction(currentItem.drillId, currentItem.qid, { action: "hint" }, cycle)) return;
    timerStateRef.current = recordHint(timerStateRef.current, currentItem.qid);
    incrementHintsUsed();
    updateCurrentProblem(
      (p) => {
        if (isLockedAfterCorrect(p.state)) return p;
        const cycleStartedAt = cycle;
        const nowIso = new Date().toISOString();
        const revealTs =
          cycleStartedAt && !isTimestampInCycle(nowIso, cycleStartedAt)
            ? cycleStartedAt
            : nowIso;
        return {
          ...p,
          state: {
            ...p.state,
            hintsRevealed: (p.state.hintsRevealed || 0) + 1,
            cycleStartedAt,
            reviewHintRevealedAt: revealTs,
          },
        };
      }
    );
  }, [currentKey, currentItem, currentProblem, currentDrill, ensureReviewCycle, incrementHintsUsed, updateCurrentProblem]);

  const handleExampleViewed = useCallback(
    (viewedAt: string) => {
      incrementHintsUsed();
      updateCurrentProblem((p) => ({
        ...p,
        state: {
          ...p.state,
          exampleViewedAt:
            p.state.exampleViewedAt &&
            isInCycle(p.state.exampleViewedAt, p.state.cycleStartedAt)
              ? p.state.exampleViewedAt
              : viewedAt,
        },
      }));
    },
    [incrementHintsUsed, updateCurrentProblem]
  );

  const handleSimilarProgressSync = useCallback(
    (patch: SimilarProgressPatch) => {
      updateCurrentProblem((p) => {
        const nextState = { ...p.state };
        if (Array.isArray(patch.similarSlots)) {
          nextState.similarSlots = patch.similarSlots;
        }
        if (patch.variantToken && patch.variantRecord) {
          nextState.variants = {
            ...(nextState.variants || {}),
            [patch.variantToken]: patch.variantRecord,
          };
        }
        return { ...p, state: nextState };
      });
    },
    [updateCurrentProblem]
  );

  const fetchAndMergeReveal = useCallback(
    async (doc: DrillDocument, key: string, qid: string, parts: RevealPart[]) => {
      for (const part of parts) {
        try {
          const res = await fetch(
            `/api/reveal?drill=${encodeURIComponent(doc.drillId)}&q=${encodeURIComponent(qid)}&part=${part}`
          );
          if (!res.ok) continue;
          const data = await res.json();
          const patch: Partial<Problem> = {};
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
          if (Object.keys(patch).length > 0) {
            setDrillsByKey((prev) => {
              const cur = prev[key];
              if (!cur) return prev;
              const merged = mergeRevealedPatchIntoDrill(cur, cur.drillId, qid, patch);
              return merged ? { ...prev, [key]: merged } : prev;
            });
          }
        } catch {
          // ignore transient reveal error
        }
      }
    },
    []
  );

  const handleSetupRevealed = useCallback(async () => {
    if (!currentDrill || !currentItem || !currentKey) return;
    const doc = await ensureReviewCycle(currentDrill, currentItem);
    if (!doc) return;
    const target = doc.problems.find((p) => p.id === currentItem.qid);
    const recorded = await sendPracticeAction(currentDrill.drillId, currentItem.qid,
      { action: "setup" }, target?.state.cycleStartedAt ?? null);
    if (!recorded) return;
    incrementHintsUsed();
    const transition = computeSetupRevealTransition(doc, currentItem.qid);
    if (!transition) return;
    setDrillsByKey((prev) => ({ ...prev, [currentKey]: transition.updatedDoc }));
    if (transition.partsToReveal.length > 0) {
      await fetchAndMergeReveal(
        transition.updatedDoc,
        currentKey,
        currentItem.qid,
        transition.partsToReveal
      );
    }
  }, [currentDrill, currentItem, currentKey, ensureReviewCycle, incrementHintsUsed, fetchAndMergeReveal]);

  const handleSolutionRevealed = useCallback(async () => {
    if (!currentDrill || !currentItem || !currentKey) return;
    const target = currentDrill.problems.find((p) => p.id === currentItem.qid);
    const recorded = await sendPracticeAction(currentDrill.drillId, currentItem.qid,
      { action: "steps" }, target?.state.cycleStartedAt ?? null);
    if (!recorded) return;
    incrementHintsUsed();
    const transition = computeSolutionRevealTransition(currentDrill, currentItem.qid);
    if (!transition) return;
    setDrillsByKey((prev) => ({ ...prev, [currentKey]: transition.updatedDoc }));
    if (transition.partsToReveal.length > 0) {
      await fetchAndMergeReveal(
        transition.updatedDoc,
        currentKey,
        currentItem.qid,
        transition.partsToReveal
      );
    }
  }, [currentDrill, currentItem, currentKey, incrementHintsUsed, fetchAndMergeReveal]);

  const handleCheckAnswer = useCallback(
    async (inputOverride?: string) => {
      if (!currentDrill || !currentItem || !currentKey || !currentProblem) return;
      if (isLockedAfterCorrect(currentProblem.state)) return;
      const inputVal = (
        inputOverride !== undefined ? inputOverride : currentProblem.state.userInput
      ).trim();
      if (!inputVal) return;

      const hintsUsed = hintsByKey[currentKey] || 0;
      const now = Date.now();
      const doc = await ensureReviewCycle(currentDrill, currentItem);
      if (!doc) return;
      const res = await executeReviewItemCheck({
        drillDoc: doc,
        item: currentItem,
        inputVal,
        hintsUsed,
        timerState: timerStateRef.current,
        now,
        today: today || undefined,
        existingOutcome: outcomes[currentKey] ?? null,
      });
      if (!res) return;

      commitTimerState(res.nextTimerState, now);
      setDrillsByKey((prev) => ({ ...prev, [currentKey]: res.updatedDoc }));
      if (res.outcome) {
        const outcome = res.outcome;
        setOutcomes((prev) => ({ ...prev, [currentKey]: outcome }));
      }
    },
    [
      currentDrill,
      currentItem,
      currentKey,
      currentProblem,
      hintsByKey,
      today,
      outcomes,
      commitTimerState,
      ensureReviewCycle,
    ]
  );

  const handleSkip = useCallback(async () => {
    if (!currentDrill || !currentItem || !currentKey) return;
    const hintsUsed = hintsByKey[currentKey] || 0;
    const now = Date.now();
    const doc = await ensureReviewCycle(currentDrill, currentItem);
    if (!doc) return;
    const res = await executeReviewItemSkip({
      drillDoc: doc,
      item: currentItem,
      hintsUsed,
      timerState: timerStateRef.current,
      now,
      today: today || undefined,
      existingOutcome: outcomes[currentKey] ?? null,
    });
    if (!res) return;

    commitTimerState(res.nextTimerState, now);
    setDrillsByKey((prev) => ({ ...prev, [currentKey]: res.updatedDoc }));
    setOutcomes((prev) => ({ ...prev, [currentKey]: res.outcome }));
  }, [currentDrill, currentItem, currentKey, hintsByKey, today, outcomes, commitTimerState, ensureReviewCycle]);

  const handleResetProblem = useCallback(async () => {
    if (!currentDrill || !currentItem || !currentKey) return;
    const started = sendPracticeAction(currentDrill.drillId, currentItem.qid, { action: "reset-review" })
      .then((result) => result?.cycleStartedAt ?? null);
    reviewCycles.current.set(currentKey, started);
    const cycle = await started;
    if (!cycle) {
      if (reviewCycles.current.get(currentKey) === started) reviewCycles.current.delete(currentKey);
      return;
    }
    const now = Date.parse(cycle);
    const transition = computeResetProblemTransition(
      currentDrill,
      currentItem.qid,
      timerStateRef.current,
      now
    );
    commitTimerState(transition.nextTimerState, now);
    setDrillsByKey((prev) => ({ ...prev, [currentKey]: transition.updatedDoc }));
  }, [currentDrill, currentItem, currentKey, commitTimerState]);

  const handleRevisitNoteChange = useCallback(
    (note: string) => {
      if (!currentKey) return;
      setRevisitDraftByKey((prev) => ({ ...prev, [currentKey]: note }));
      updateCurrentProblem(
        (p) => ({
          ...p,
          state: {
            ...p.state,
            revisitNote: note.trim(),
          },
        }),
        "revisitNote"
      );
    },
    [currentKey, updateCurrentProblem]
  );

  const handlePrevItem = useCallback(() => {
    setCurrentIndex((idx) => Math.max(0, idx - 1));
  }, []);

  const handleNextItem = useCallback(() => {
    if (currentIndex >= items.length - 1) {
      setCompleted(true);
    } else {
      setCurrentIndex((idx) => idx + 1);
    }
  }, [currentIndex, items.length]);

  const questionTimerMs =
    currentKey && currentProblem
      ? getProblemDisplayMs(
          currentProblem.state?.durationMs,
          timerState,
          currentKey,
          timerNow
        )
      : 0;

  const summary = summarizeReviewSession(items, outcomes, initialNextDueDate);
  const stillDueCount = Math.max(0, totalDue - Object.keys(outcomes).length);
  const promptsByKey = Object.fromEntries(items.map((item) => {
    const key = reviewItemKey(item.drillId, item.qid);
    const prompt = drillsByKey[key]?.problems.find((problem) => problem.id === item.qid)?.prompt || "";
    return [key, prompt];
  }));
  const missedItems = getMissedReviewItems(items, outcomes, unitTitles, promptsByKey);
  const currentOutcome = currentKey ? outcomes[currentKey] ?? null : null;
  const currentUnitTitle = currentItem
    ? plainTitle(
        currentDrill?.unitTitle ||
          unitTitles[currentItem.unitCode] ||
          currentItem.unitCode
      )
    : undefined;

  useEffect(() => {
    if (!completed || items.length === 0) return;
    try {
      window.sessionStorage.setItem(reviewStorageKey(activeScope), JSON.stringify({
        completed: true, items, outcomes, totalDue, unitTitles, today,
        nextDueDate: initialNextDueDate, lastDrillHref,
      }));
    } catch {
      // A full sessionStorage quota must not block the end screen.
    }
  }, [completed, items, outcomes, totalDue, unitTitles, today, initialNextDueDate, lastDrillHref, activeScope]);

  return (
    <DailyReviewView
      loading={loading}
      error={error}
      items={items}
      currentIndex={currentIndex}
      currentProblem={currentProblem}
      currentDrillMistakeTags={currentDrill?.mistakeTags || []}
      isLoadingProblem={Boolean(currentKey && loadingKey === currentKey && !currentProblem)}
      completed={completed}
      summary={summary}
      nextDueDate={initialNextDueDate}
      today={today || null}
      unitTitles={unitTitles}
      currentUnitTitle={currentUnitTitle}
      currentOutcome={currentOutcome}
      stillDueCount={stillDueCount}
      missedItems={missedItems}
      onReviewMore={handleReviewMore}
      lastDrillHref={lastDrillHref}
      revealedTrapTag={currentKey ? outcomes[currentKey]?.commonTrapTag ?? null : null}
      revisitNoteDraft={currentKey ? revisitDraftByKey[currentKey] ?? "" : ""}
      questionTimerMs={questionTimerMs}
      totalTimerMs={questionTimerMs}
      isTimerPaused={timerState.paused}
      theme={theme}
      onToggleTheme={handleToggleTheme}
      onToggleTimerPause={handleToggleTimerPause}
      onInputChange={(val) =>
        updateCurrentProblem((p) => ({ ...p, state: { ...p.state, userInput: val } }))
      }
      onCheckAnswer={handleCheckAnswer}
      onSkip={handleSkip}
      onResetProblem={handleResetProblem}
      onHintRevealed={handleHintRevealed}
      onSetupRevealed={handleSetupRevealed}
      onSolutionRevealed={handleSolutionRevealed}
      onExampleViewed={handleExampleViewed}
      onSimilarProgressSync={handleSimilarProgressSync}
      onVariantModeChange={handleVariantModeChange}
      onMarkDivergedStep={(stepIdx) =>
        updateCurrentProblem(
          (p) => ({ ...p, state: applyDivergedStep(p, stepIdx) }),
          "divergedStep"
        )
      }
      onSetScore={(score) => {
        if (!currentDrill || !currentItem || !currentProblem) return;
        void sendPracticeAction(currentDrill.drillId, currentItem.qid, { action: "self-score", score },
          currentProblem.state.cycleStartedAt ?? null);
        updateCurrentProblem(
          (p) => ({ ...p, state: applySelfScore(p.state, score) })
        );
      }}
      onToggleMistakeTag={(tagId) => {
        if (!currentDrill || !currentItem || !currentProblem || tagId === "concept-gap") return;
        void sendPracticeAction(currentDrill.drillId, currentItem.qid, { action: "toggle-mistake", tag: tagId },
          currentProblem.state.cycleStartedAt ?? null);
        updateCurrentProblem(
          (p) => ({ ...p, state: toggleMistakeTag(p.state, tagId) })
        );
      }}
      onMistakeNoteChange={(note) =>
        updateCurrentProblem(
          (p) => ({ ...p, state: { ...p.state, mistakeNote: note } }),
          "mistakeNote"
        )
      }
      onRevisitNoteChange={handleRevisitNoteChange}
      onPrevItem={handlePrevItem}
      onNextItem={handleNextItem}
    />
  );
};
