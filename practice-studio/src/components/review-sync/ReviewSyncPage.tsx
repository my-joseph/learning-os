"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import type { DrillDocument, DrillListItem } from "@/types/drill";
import type { PracticeStatusOverride } from "@/hooks/types";
import { INITIAL_SYNC_STATE, type SyncState } from "@/hooks/useProgressSync";
import { useSidePanelData } from "@/hooks/useSidePanelData";
import type { ReviewScheduleEntry, WeakSpotUnit } from "@/lib/dueToday";
import {
  ensureExpandedRow,
  groupReviewProblems,
  toggleExpandedRow,
} from "@/lib/reviewOutcome";
import {
  detectSessionPattern,
  findFirstWrongItem,
  findL4ProblemTarget,
  findNextDrill,
  getDefaultExpandedRowIds,
  pickTopWeakSpot,
  sortNeedsAttention,
} from "@/lib/reviewRow";
import { deriveMilestoneTileState } from "@/lib/codeStatus";
import { isLabId, subjectOf } from "@/lib/routes";
import {
  buildSyncPreview,
  countSummaryChanges,
  getCoveredUnits,
  summaryFingerprint,
} from "@/lib/sessionSummary";
import { Reveal } from "@/components/motion/Reveal";
import {
  SessionSummaryCard,
  type EffectiveSyncPhase,
} from "./SessionSummaryCard";
import { ReviewItemRow } from "./ReviewItemRow";
import { SyncCard } from "./SyncCard";
import { NextActions } from "./NextActions";

export interface ReviewSyncPageProps {
  currentDrill: DrillDocument;
  statusOverride: PracticeStatusOverride;
  isSyncing: boolean;
  syncState?: SyncState;
  totalDurationMs?: number;
  initialExpandedIds?: string[];
  workspaceDrills?: DrillListItem[];
  /** Optional overrides for SSR/tests (skips local GET when supplied). */
  scheduleCache?: Record<string, ReviewScheduleEntry>;
  dueReviewCount?: number;
  weakSpotUnits?: WeakSpotUnit[];
  onStatusOverrideChange: (status: "Graded" | "Needs Retry") => void;
  onBackToQuiz: () => void;
  onConfirmSync: () => void;
  onSelectQuestion: (idx: number) => void;
  onTrySimilarQuestion?: (probId: string, idx: number) => void;
  onSetScore: (probId: string, score: number | null) => void;
  onToggleMistakeTag: (probId: string, tagId: string) => void;
  onMistakeNoteChange: (probId: string, note: string) => void;
  onRevisitNoteChange?: (probId: string, note: string) => void;
  onSelectDrill?: (drillId: string) => void;
  onOpenGenerate?: () => void;
}

/** Redesigned Review & Sync page: Session summary -> To review -> Got right -> Sync to Notion (or Submit lab) -> What next. */
export const ReviewSyncPage: React.FC<ReviewSyncPageProps> = ({
  currentDrill,
  statusOverride,
  isSyncing,
  syncState = INITIAL_SYNC_STATE,
  totalDurationMs: totalDurationMsOverride,
  initialExpandedIds,
  workspaceDrills = [],
  scheduleCache: scheduleCacheProp,
  dueReviewCount: dueReviewCountProp,
  weakSpotUnits: weakSpotUnitsProp,
  onStatusOverrideChange,
  onBackToQuiz,
  onConfirmSync,
  onSelectQuestion,
  onTrySimilarQuestion,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
  onRevisitNoteChange,
  onSelectDrill,
  onOpenGenerate,
}) => {
  const isLab = isLabId(currentDrill.drillId);
  const isCode = currentDrill.subject === "PRG" && !isLab;
  const isEditLocked = isSyncing || syncState.phase === "syncing";
  const mistakeTags = currentDrill.mistakeTags || [];

  const groups = useMemo(
    () => groupReviewProblems(currentDrill.problems),
    [currentDrill.problems]
  );

  const sortedNeedsAttention = useMemo(
    () => sortNeedsAttention(groups.needsAttention),
    [groups.needsAttention]
  );

  const allCorrect =
    currentDrill.problems.length > 0 &&
    sortedNeedsAttention.length === 0 &&
    groups.correct.length === currentDrill.problems.length;

  const wrongAndAssistedCount = useMemo(
    () =>
      sortedNeedsAttention.filter(
        (i) => i.outcome === "wrong" || i.outcome === "assisted_or_partial"
      ).length,
    [sortedNeedsAttention]
  );

  const manyWrong =
    currentDrill.problems.length > 0 &&
    wrongAndAssistedCount * 2 >= currentDrill.problems.length;

  const [showCorrect, setShowCorrect] = useState<boolean>(() => allCorrect);
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>(() => {
    if (initialExpandedIds !== undefined) {
      const explicit: Record<string, boolean> = {};
      for (const id of initialExpandedIds) explicit[id] = true;
      return explicit;
    }
    return getDefaultExpandedRowIds(sortedNeedsAttention);
  });

  const [pendingScrollId, setPendingScrollId] = useState<string | null>(null);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const [fetchedSchedule, setFetchedSchedule] = useState<Record<string, ReviewScheduleEntry>>({});
  const rowRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const syncedRefreshKey =
    currentDrill.sessionSummary?.syncedToNotionAt || syncState.at || null;

  const sidePanelData = useSidePanelData(
    subjectOf(currentDrill.drillId) ?? "math",
    dueReviewCountProp === undefined || weakSpotUnitsProp === undefined
      ? currentDrill.unitCode
      : null,
    syncedRefreshKey
  );

  const dueReviewCount = dueReviewCountProp ?? sidePanelData.dueReviewCount;
  const weakSpotUnits = weakSpotUnitsProp ?? sidePanelData.weakSpotUnits;

  const coveredUnitKey = useMemo(
    () => getCoveredUnits(currentDrill).join(","),
    [currentDrill]
  );

  useEffect(() => {
    if (scheduleCacheProp !== undefined || isLab || !coveredUnitKey) return;
    let cancelled = false;
    fetch(`/api/review-schedule?units=${encodeURIComponent(coveredUnitKey)}`, {
      cache: "no-store",
    })
      .then(async (res) => {
        if (!res.ok) return null;
        return (await res.json()) as { units?: Record<string, ReviewScheduleEntry> };
      })
      .then((data) => {
        if (!cancelled && data?.units && typeof data.units === "object") {
          setFetchedSchedule(data.units);
        }
      })
      .catch(() => {
        // Schedule cache is optional preview context; fail quietly.
      });
    return () => {
      cancelled = true;
    };
  }, [coveredUnitKey, isLab, scheduleCacheProp, syncedRefreshKey]);

  const scheduleCache = scheduleCacheProp ?? fetchedSchedule;

  // Reset disclosure & expansion defaults when switching to a different drill
  const prevDrillIdRef = useRef(currentDrill.drillId);
  useEffect(() => {
    if (prevDrillIdRef.current === currentDrill.drillId) return;
    prevDrillIdRef.current = currentDrill.drillId;
    setShowCorrect(allCorrect);
    if (initialExpandedIds !== undefined) {
      const explicit: Record<string, boolean> = {};
      for (const id of initialExpandedIds) explicit[id] = true;
      setExpandedIds(explicit);
    } else {
      setExpandedIds(
        getDefaultExpandedRowIds(sortedNeedsAttention)
      );
    }
    setPendingScrollId(null);
    setHighlightedId(null);
  }, [
    allCorrect,
    currentDrill.drillId,
    currentDrill.problems.length,
    initialExpandedIds,
    sortedNeedsAttention,
  ]);

  useEffect(() => {
    if (!pendingScrollId) return;
    const timer = window.setTimeout(() => {
      const el =
        rowRefs.current.get(pendingScrollId) ??
        document.getElementById(`review-row-${pendingScrollId}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        setHighlightedId(pendingScrollId);
      }
      setPendingScrollId(null);
    }, 60);
    return () => window.clearTimeout(timer);
  }, [pendingScrollId, showCorrect]);

  useEffect(() => {
    if (!highlightedId) return;
    const timer = window.setTimeout(() => setHighlightedId(null), 1200);
    return () => window.clearTimeout(timer);
  }, [highlightedId]);

  const preview = useMemo(
    () => buildSyncPreview(currentDrill, statusOverride, scheduleCache),
    [currentDrill, statusOverride, scheduleCache]
  );

  const persistedSyncedAt = currentDrill.sessionSummary?.syncedToNotionAt || null;
  const effectiveSyncedAt =
    syncState.phase === "synced"
      ? syncState.at || persistedSyncedAt
      : persistedSyncedAt;

  const currentFingerprint = useMemo(
    () => summaryFingerprint(preview.summary),
    [preview.summary]
  );

  const savedFingerprint = useMemo(() => {
    if (!effectiveSyncedAt) return null;
    if (currentDrill.sessionSummary?.syncedFingerprint) {
      return currentDrill.sessionSummary.syncedFingerprint;
    }
    return summaryFingerprint(currentDrill.sessionSummary);
  }, [currentDrill.sessionSummary, effectiveSyncedAt]);

  const effectiveSyncPhase: EffectiveSyncPhase = useMemo(() => {
    if (isSyncing || syncState.phase === "syncing") return "syncing";
    if (syncState.phase === "degraded") return "degraded";
    if (syncState.phase === "error") return "error";
    if (syncState.phase === "offline") return "offline";
    if (syncState.phase === "dryRun") return "dryRun";
    if (effectiveSyncedAt) {
      if (savedFingerprint && currentFingerprint !== savedFingerprint) {
        return "changed";
      }
      return "synced";
    }
    return "idle";
  }, [currentFingerprint, effectiveSyncedAt, isSyncing, savedFingerprint, syncState.phase]);

  const changedCount = useMemo(() => {
    if (effectiveSyncPhase !== "changed") return 0;
    return countSummaryChanges(currentDrill.sessionSummary, preview.summary);
  }, [currentDrill.sessionSummary, effectiveSyncPhase, preview.summary]);

  const pattern = useMemo(
    () => detectSessionPattern(currentDrill, isLab),
    [currentDrill, isLab]
  );

  const totalDurationMs = totalDurationMsOverride ?? groups.totalDurationMs;

  const topWeakSpot = useMemo(() => pickTopWeakSpot(weakSpotUnits), [weakSpotUnits]);
  const firstWrong = useMemo(
    () => findFirstWrongItem(currentDrill, isLab),
    [currentDrill, isLab]
  );
  const nextDrill = useMemo(
    () => findNextDrill(currentDrill, workspaceDrills),
    [currentDrill, workspaceDrills]
  );
  const l4Challenge = useMemo(
    () => findL4ProblemTarget(currentDrill, isLab),
    [currentDrill, isLab]
  );

  const isCapped = useMemo(() => {
    if (syncState.unitReviews) {
      return Object.values(syncState.unitReviews).some((u) => Boolean(u.masteryCap?.capped));
    }
    return preview.coveredUnits.some((u) => Boolean(u.masteryCap?.capped));
  }, [preview.coveredUnits, syncState.unitReviews]);

  const labSummary = useMemo(() => {
    if (!isLab) return undefined;
    let passed = 0;
    let awaitingReview = 0;
    let revise = 0;
    let notTried = 0;
    for (const p of currentDrill.problems) {
      const tile = deriveMilestoneTileState(p.state);
      if (tile === "pass") passed += 1;
      else if (tile === "awaiting_review") awaitingReview += 1;
      else if (tile === "revise") revise += 1;
      else notTried += 1;
    }
    return { passed, awaitingReview, revise, notTried, total: currentDrill.problems.length };
  }, [currentDrill.problems, isLab]);

  const firstUnansweredIndex = useMemo(() => {
    const found = sortedNeedsAttention.find((i) => i.outcome === "unanswered");
    return found ? found.index : null;
  }, [sortedNeedsAttention]);

  const handleJumpToRow = (probId: string, inCorrectGroup: boolean) => {
    if (inCorrectGroup && !showCorrect) {
      setShowCorrect(true);
    }
    setExpandedIds((prev) => ensureExpandedRow(prev, probId));
    setPendingScrollId(probId);
  };

  const handleScrollToSync = () => {
    const el = document.getElementById("review-sync-section");
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleRevisitNote = (probId: string, note: string) => {
    onRevisitNoteChange?.(probId, note);
  };

  return (
    <div className="max-w-[720px] mx-auto space-y-6">
      {/* A. Session summary */}
      <SessionSummaryCard
        drill={currentDrill}
        groups={groups}
        durationMs={totalDurationMs}
        pattern={pattern}
        effectiveSyncPhase={effectiveSyncPhase}
        syncedAt={effectiveSyncedAt}
        isLab={isLab}
        isCode={isCode}
        hasAnyAttempt={preview.hasAnyAttempt}
        onJumpToRow={handleJumpToRow}
        onScrollToSync={handleScrollToSync}
        onBackToQuiz={onBackToQuiz}
        onStartFirst={() => onSelectQuestion(0)}
      />

      {/* B. To review */}
      {allCorrect ? (
        <section className="bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl px-4 py-3.5 sm:px-6 text-sm text-zinc-600 dark:text-zinc-300">
          Nothing to fix. Add a revisit note below if you want.
        </section>
      ) : (
        <section
          aria-labelledby="to-review-heading"
          className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden"
        >
          <div className="px-4 py-3 sm:px-6 bg-zinc-50/70 dark:bg-zinc-950/50 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
            <h2
              id="to-review-heading"
              className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
            >
              To review
            </h2>
            <span className="text-xs font-display tabular-nums text-zinc-500 dark:text-zinc-400">
              {sortedNeedsAttention.length}
            </span>
          </div>

          <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {sortedNeedsAttention.map(({ problem, index, outcome }) => (
              <ReviewItemRow
                key={problem.id}
                drillId={currentDrill.drillId}
                problem={problem}
                index={index}
                outcome={outcome}
                isLab={isLab}
                isCode={isCode}
                mistakeTags={mistakeTags}
                expanded={Boolean(expandedIds[problem.id])}
                highlighted={highlightedId === problem.id}
                disabled={isEditLocked}
                rowRef={(el) => {
                  if (el) rowRefs.current.set(problem.id, el);
                  else rowRefs.current.delete(problem.id);
                }}
                onToggle={() =>
                  setExpandedIds((prev) => toggleExpandedRow(prev, problem.id))
                }
                onOpen={() => onSelectQuestion(index)}
                onTrySimilar={
                  onTrySimilarQuestion
                    ? () => onTrySimilarQuestion(problem.id, index)
                    : undefined
                }
                onSetScore={(score) => onSetScore(problem.id, score)}
                onToggleMistakeTag={(tagId) => onToggleMistakeTag(problem.id, tagId)}
                onMistakeNoteChange={(note) => onMistakeNoteChange(problem.id, note)}
                onRevisitNoteChange={(note) => handleRevisitNote(problem.id, note)}
              />
            ))}
          </div>
        </section>
      )}

      {/* C. Got right (collapsed disclosure; opens by default when all-correct) */}
      {groups.correct.length > 0 && (
        <section
          aria-labelledby="got-right-heading"
          className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden"
        >
          <button
            type="button"
            id="got-right-heading"
            onClick={() => setShowCorrect((prev) => !prev)}
            aria-expanded={showCorrect}
            aria-controls="got-right-list"
            className="w-full min-h-[48px] px-4 py-3 sm:px-6 bg-zinc-50/70 dark:bg-zinc-950/50 hover:bg-zinc-100/70 dark:hover:bg-zinc-900 flex items-center justify-between text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
          >
            <span className="inline-flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              <ChevronDown
                aria-hidden="true"
                className={`w-4 h-4 text-zinc-500 dark:text-zinc-400 transition-transform duration-150 ${
                  showCorrect ? "rotate-0" : "-rotate-90"
                }`}
              />
              <span>Got right</span>
            </span>
            <span className="text-xs font-display tabular-nums text-zinc-500 dark:text-zinc-400">
              {groups.correct.length}
            </span>
          </button>

          <Reveal show={showCorrect}>
            {showCorrect && (
              <div
                id="got-right-list"
                className="divide-y divide-zinc-200 dark:divide-zinc-800 border-t border-zinc-200 dark:border-zinc-800"
              >
                {groups.correct.map(({ problem, index, outcome }) => (
                  <ReviewItemRow
                    key={problem.id}
                    drillId={currentDrill.drillId}
                    problem={problem}
                    index={index}
                    outcome={outcome}
                    isLab={isLab}
                    isCode={isCode}
                    isGotRightRow
                    mistakeTags={mistakeTags}
                    expanded={Boolean(expandedIds[problem.id])}
                    highlighted={highlightedId === problem.id}
                    disabled={isEditLocked}
                    rowRef={(el) => {
                      if (el) rowRefs.current.set(problem.id, el);
                      else rowRefs.current.delete(problem.id);
                    }}
                    onToggle={() =>
                      setExpandedIds((prev) => toggleExpandedRow(prev, problem.id))
                    }
                    onOpen={() => onSelectQuestion(index)}
                    onTrySimilar={
                      onTrySimilarQuestion
                        ? () => onTrySimilarQuestion(problem.id, index)
                        : undefined
                    }
                    onSetScore={(score) => onSetScore(problem.id, score)}
                    onToggleMistakeTag={(tagId) => onToggleMistakeTag(problem.id, tagId)}
                    onMistakeNoteChange={(note) => onMistakeNoteChange(problem.id, note)}
                    onRevisitNoteChange={(note) => handleRevisitNote(problem.id, note)}
                  />
                ))}
              </div>
            )}
          </Reveal>
        </section>
      )}

      {/* D. Sync to Notion (or Submit lab) */}
      <SyncCard
        preview={preview}
        syncState={syncState}
        effectiveSyncPhase={effectiveSyncPhase}
        syncedAt={effectiveSyncedAt}
        drillPageId={syncState.drillPageId || currentDrill.sessionSummary?.notionPageId}
        changedCount={changedCount}
        isLab={isLab}
        labId={currentDrill.drillId}
        labSummary={labSummary}
        l4Challenge={l4Challenge}
        onSync={onConfirmSync}
        onStatusOverrideChange={onStatusOverrideChange}
        onAnswerFirstUnanswered={
          firstUnansweredIndex !== null
            ? () => onSelectQuestion(firstUnansweredIndex)
            : undefined
        }
        onOpenL4Challenge={onSelectQuestion}
      />

      {/* E. What next */}
      <NextActions
        dueReviewCount={dueReviewCount}
        topWeakSpot={topWeakSpot}
        firstWrong={firstWrong}
        nextDrill={nextDrill}
        l4Challenge={l4Challenge}
        allCorrect={allCorrect}
        isCapped={isCapped}
        manyWrong={manyWrong}
        primary={!isLab && effectiveSyncPhase === "synced"}
        onOpenItem={onSelectQuestion}
        onSelectDrill={onSelectDrill}
        onGenerate={onOpenGenerate}
      />
    </div>
  );
};
