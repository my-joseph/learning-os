"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { m } from "motion/react";
import { fadeUp } from "@/lib/motion";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus } from "lucide-react";
import { DrillDocument } from "@/types/drill";

const MathWorkspace = dynamic(
  () => import("@/components/math/MathWorkspace").then((mod) => mod.MathWorkspace),
  { ssr: true }
);

const CodeDashboard = dynamic(
  () => import("@/components/code/CodeDashboard").then((mod) => mod.CodeDashboard),
  { ssr: true }
);
const ReviewSyncPage = dynamic(
  () => import("@/components/review-sync/ReviewSyncPage").then((mod) => mod.ReviewSyncPage),
  { ssr: false }
);
import { StudioShell } from "@/components/shell/StudioShell";
import { DrillNotFoundCard } from "@/components/shell/DrillNotFoundCard";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { StatusProgressBar, type ProgressStage } from "@/components/ui/StatusProgressBar";
import { StatusMessage } from "@/hooks/types";
import { useTheme } from "@/hooks/useTheme";
import {
  useProgressSync,
  mergeSyncStampIntoLatestDrill,
} from "@/hooks/useProgressSync";
import { useDrill } from "@/hooks/useDrill";
import { useDrillList } from "@/hooks/useDrillList";
import {
  Workspace,
  drillHref,
  findProblemIndex,
  isLabId,
  resolveWorkspaceDrill,
} from "@/lib/routes";
import { readLastDrillId, writeLastDrillId } from "@/lib/lastDrillStorage";
import { getDrillTotalMs, getProblemDisplayMs } from "@/lib/telemetryTimer";
import { plainTitle } from "@/lib/titleText";
import { resetAnswerForReviewRetry } from "@/lib/applyCheckResult";
import { getPersistedStatusOverride } from "@/lib/sessionSummary";

const DRILL_LOAD_STAGES: ProgressStage[] = [
  { minPct: 0, message: "Fetching drill specification..." },
  { minPct: 35, message: "Loading saved progress..." },
  { minPct: 70, message: "Preparing workspace..." },
];

interface StudioClientProps {
  workspace: Workspace;
  drillId: string;
  initialQuestionId?: string;
  isLabRoute?: boolean;
}

/** Main interactive Practice Studio client bound to a workspace and drill route. */
export const StudioClient: React.FC<StudioClientProps> = ({
  workspace,
  drillId,
  initialQuestionId,
  isLabRoute = false,
}) => {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [showGenPopover, setShowGenPopover] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resetAllVersion, setResetAllVersion] = useState(0);
  const [lastMathId, setLastMathId] = useState<string | null>(null);
  const [lastCodeId, setLastCodeId] = useState<string | null>(null);
  const [pendingSimilarProbId, setPendingSimilarProbId] = useState<string | null>(() =>
    searchParams.get("similar") === "1" ? initialQuestionId ?? null : null
  );
  const [reviewRetryStarted, setReviewRetryStarted] = useState(false);
  const isMissedReviewLink = searchParams.get("review") === "missed";

  const initialQuestionIdRef = useRef<string | undefined>(initialQuestionId);
  initialQuestionIdRef.current = initialQuestionId;

  const pendingReplacedQsRef = useRef<string[]>([]);

  const { theme, handleToggleTheme } = useTheme();
  const {
    statusOverride,
    setStatusOverride,
    isSyncing,
    syncState,
    resetSyncState,
    triggerAutoSave,
    saveNow,
    flushAutoSave,
    confirmSyncToNotion,
  } = useProgressSync({ setStatus });

  const handleDrillLoaded = useCallback(
    (doc: DrillDocument) => {
      setStatusOverride(getPersistedStatusOverride(doc.sessionSummary));
      resetSyncState();
      writeLastDrillId(doc.drillId, workspace);
      if (workspace === "math") {
        setLastMathId(doc.drillId);
      } else {
        setLastCodeId(doc.drillId);
      }
    },
    [resetSyncState, setStatusOverride, workspace]
  );

  const handleQuestionUrlSync = useCallback(
    (activeDrillId: string, problemId: string) => {
      pendingReplacedQsRef.current.push(problemId);
      router.replace(drillHref(activeDrillId, problemId), { scroll: false });
    },
    [router]
  );

  const {
    currentDrill,
    setCurrentDrill,
    getLatestDrill,
    currentProblemIndex,
    setCurrentProblemIndex,
    viewMode,
    setViewMode,
    isLoadingDrill,
    drillNotFound,
    loadDrill,
    timerState,
    timerNow,
    handleToggleTimerPause,
    handleVariantModeChange,
    handleExampleViewed,
    handleSimilarProgressSync,
    handleHintRevealed,
    handleCheckAnswer,
    handleInputChange,
    handleMistakeNoteChange,
    handleRevisitNoteChange,
    handleSetupRevealed,
    handleSolutionRevealed,
    handleMarkDivergedStep,
    handleSetScore,
    handleTestReportChange,
    handleToggleMistakeTag,
    handleSkipProblem,
    handleResetProblem,
    handleResetAll,
    handlePrevQuestion,
    handleNextQuestion,
    handleSelectQuestion,
  } = useDrill({
    triggerAutoSave,
    saveNow,
    setStatus,
    onDrillLoaded: handleDrillLoaded,
    onQuestionChange: handleQuestionUrlSync,
  });

  const {
    drills,
    labs,
    workspaceDrills,
    workspaceLabs,
    drillSearch,
    setDrillSearch,
    drillFilter,
    setDrillFilter,
    loadDrillsList,
  } = useDrillList({
    workspace,
    setStatus,
  });

  // Load drill whenever route drillId changes
  useEffect(() => {
    setStatus(null);
    setReviewRetryStarted(false);
    setShowResetConfirm(false);
    pendingReplacedQsRef.current = [];
    loadDrill(drillId, initialQuestionIdRef.current);
  }, [drillId, loadDrill]);

  // Read saved per-workspace drill IDs on client mount
  useEffect(() => {
    setLastMathId(readLastDrillId("math"));
    setLastCodeId(readLastDrillId("code"));
  }, [drillId]);

  // Sync external ?q= / ?m= updates (e.g., browser navigation or direct link clicks on same drill/lab)
  const qParam = isLabId(drillId)
    ? searchParams.get("m") ?? searchParams.get("q")
    : searchParams.get("q");
  const prevQParamRef = useRef<string | null | undefined>(undefined);
  useEffect(() => {
    if (prevQParamRef.current === undefined) {
      prevQParamRef.current = qParam;
      return;
    }
    if (prevQParamRef.current === qParam) return;
    prevQParamRef.current = qParam;

    if (qParam) {
      const pendingIdx = pendingReplacedQsRef.current.indexOf(qParam);
      if (pendingIdx >= 0) {
        pendingReplacedQsRef.current = pendingReplacedQsRef.current.slice(pendingIdx + 1);
        return;
      }
    }
    pendingReplacedQsRef.current = [];

    if (currentDrill && currentDrill.drillId === drillId) {
      setCurrentProblemIndex(findProblemIndex(currentDrill.problems, qParam));
    }
  }, [qParam, currentDrill, drillId, setCurrentProblemIndex]);

  const handleConfirmSyncToNotion = () =>
    confirmSyncToNotion(getLatestDrill() ?? currentDrill, {
      getLatestDrill,
      onDrillUpdated: (stampedDoc) =>
        setCurrentDrill(
          (prev) =>
            mergeSyncStampIntoLatestDrill(
              prev,
              stampedDoc.drillId,
              stampedDoc.sessionSummary
            ) ?? prev
        ),
      onSynced: () => loadDrillsList(),
    });

  const handleStatusOverrideChange = (override: "Graded" | "Needs Retry") => {
    setStatusOverride(override);
    let updated: DrillDocument | null = null;
    setCurrentDrill((prev) => {
      if (!prev) return prev;
      updated = {
        ...prev,
        sessionSummary: { ...prev.sessionSummary, statusOverride: override },
      };
      return updated;
    });
    if (updated) {
      triggerAutoSave(updated);
    }
  };

  const handleTrySimilarQuestion = (probId: string, idx: number) => {
    setPendingSimilarProbId(probId);
    handleSelectQuestion(idx);
    if (currentDrill) {
      const base = drillHref(currentDrill.drillId, probId);
      const sep = base.includes("?") ? "&" : "?";
      router.replace(`${base}${sep}similar=1`, { scroll: false });
    }
  };

  const handleSelectDrill = (nextDrillId: string) => {
    if (nextDrillId === drillId) return;
    router.push(drillHref(nextDrillId));
  };

  const handleReviewRetry = () => {
    const problem = currentDrill?.problems[currentProblemIndex];
    if (!currentDrill || !problem) return;
    let updatedDoc: DrillDocument | null = null;
    setCurrentDrill((prev) => {
      if (!prev) return prev;
      updatedDoc = {
        ...prev,
        problems: prev.problems.map((candidate) =>
          candidate.id === problem.id
            ? { ...candidate, state: resetAnswerForReviewRetry(candidate.state) }
            : candidate
        ),
      };
      return updatedDoc;
    });
    if (updatedDoc) {
      void saveNow(updatedDoc);
    }
    setReviewRetryStarted(true);
    requestAnimationFrame(() => {
      document.querySelector<HTMLElement>('[aria-label^="Answer for"]')?.focus();
    });
  };

  const handleGenerated = async (newDrillId: string) => {
    await loadDrillsList();
    router.push(drillHref(newDrillId));
  };

  const mathTargetId =
    workspace === "math" && currentDrill
      ? currentDrill.drillId
      : resolveWorkspaceDrill(drills, "math", lastMathId);
  const codeTargetId =
    workspace === "code" && currentDrill
      ? currentDrill.drillId
      : lastCodeId && isLabId(lastCodeId) && labs.some((l) => l.id === lastCodeId)
      ? lastCodeId
      : resolveWorkspaceDrill(drills, "code", lastCodeId);

  const activeProblemId = currentDrill?.problems[currentProblemIndex]?.id;
  const mathHref = mathTargetId
    ? drillHref(mathTargetId, workspace === "math" && currentDrill ? activeProblemId : undefined)
    : null;
  const codeHref = codeTargetId
    ? drillHref(codeTargetId, workspace === "code" && currentDrill ? activeProblemId : undefined)
    : null;

  return (
    <StudioShell
      workspace={workspace}
      mathHref={mathHref}
      codeHref={codeHref}
      viewMode={viewMode}
      currentDrill={currentDrill}
      statusOverride={statusOverride}
      syncState={syncState}
      isSyncing={isSyncing}
      isLoadingDrill={isLoadingDrill}
      drillNotFound={drillNotFound}
      currentProblemIndex={currentProblemIndex}
      theme={theme}
      onToggleTheme={handleToggleTheme}
      onResetAll={() => {
        if (currentDrill) setShowResetConfirm(true);
      }}
      drills={workspaceDrills}
      allWorkspaceDrills={workspaceDrills}
      labs={workspaceLabs}
      selectedDrillId={drillId}
      drillSearch={drillSearch}
      onSearchChange={setDrillSearch}
      drillFilter={drillFilter}
      onFilterChange={setDrillFilter}
      onSelectDrill={handleSelectDrill}
      showGenPopover={showGenPopover}
      onShowGenPopoverChange={setShowGenPopover}
      onGenerated={handleGenerated}
      onSelectQuestion={handleSelectQuestion}
      onToggleViewMode={(mode) => setViewMode(mode)}
      status={status}
      onStatusChange={setStatus}
    >
      {isLoadingDrill ? (
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 space-y-5">
          <StatusProgressBar label="Loading practice data" active stages={DRILL_LOAD_STAGES} />
          <div className="space-y-3" aria-hidden="true">
            <div className="h-5 w-1/3 bg-zinc-200 dark:bg-zinc-800 rounded-lg animate-pulse" />
            <div className="h-4 w-2/3 bg-zinc-200 dark:bg-zinc-800 rounded-lg animate-pulse" />
            <div className="h-24 w-full bg-zinc-100 dark:bg-zinc-950 rounded-xl animate-pulse" />
            <div className="h-10 w-1/2 bg-zinc-200 dark:bg-zinc-800 rounded-xl animate-pulse" />
          </div>
        </div>
      ) : drillNotFound ? (
        <DrillNotFoundCard drillId={drillId} isLab={isLabRoute || isLabId(drillId)} />
      ) : !currentDrill ? (
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-10 text-center space-y-3">
          <p className="text-base font-semibold text-zinc-800 dark:text-zinc-200">
            No practice drill selected
          </p>
          <button
            type="button"
            onClick={() => setShowGenPopover(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-sm font-semibold"
          >
            <Plus className="w-4 h-4" />
            <span>Generate drill set</span>
          </button>
        </div>
      ) : viewMode === "quiz" && currentDrill.problems[currentProblemIndex] ? (
        <m.div
          key={`${workspace}:${currentDrill.drillId}:${currentDrill.problems[currentProblemIndex].id}:${resetAllVersion}`}
          variants={fadeUp}
          initial="hidden"
          animate="shown"
        >
          {(() => {
            const prob = currentDrill.problems[currentProblemIndex];
            const idx = currentProblemIndex;
            const questionTimerMs = getProblemDisplayMs(
              prob.state?.durationMs,
              timerState,
              prob.id,
              timerNow
            );
            const totalTimerMs = getDrillTotalMs(currentDrill.problems, timerState, timerNow);

            const reviewContext = isMissedReviewLink ? (
              <div role="note" className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 px-4 py-3">
                <p className="text-sm text-zinc-700 dark:text-zinc-300">You missed this in today&apos;s review</p>
                {!reviewRetryStarted && (
                  <button
                    type="button"
                    onClick={handleReviewRetry}
                    className="inline-flex min-h-[36px] items-center rounded-lg border border-zinc-300 dark:border-zinc-700 px-3 text-xs font-medium text-zinc-800 dark:text-zinc-200 hover:bg-white dark:hover:bg-zinc-800"
                  >
                    Try again
                  </button>
                )}
              </div>
            ) : null;

            if (workspace === "math") {
              return (
                <>
                  {reviewContext}
                  <MathWorkspace
                  key={prob.id}
                  problem={prob}
                  drillId={currentDrill.drillId}
                  index={idx}
                  totalQuestions={currentDrill.problems.length}
                  unitCode={currentDrill.unitCode}
                  drillTitle={plainTitle(currentDrill.unitTitle) || currentDrill.unitCode}
                  mistakeTags={currentDrill.mistakeTags || []}
                  onInputChange={(val) => handleInputChange(prob.id, val)}
                  onCheckAnswer={(inputOverride) => handleCheckAnswer(prob.id, inputOverride)}
                  onSkip={(opts) => handleSkipProblem(prob.id, opts)}
                  onMarkDivergedStep={(stepIdx) => handleMarkDivergedStep(prob.id, stepIdx)}
                  onSetScore={(score) => handleSetScore(prob.id, score)}
                  onToggleMistakeTag={(tagId) => handleToggleMistakeTag(prob.id, tagId)}
                  onMistakeNoteChange={(note) => handleMistakeNoteChange(prob.id, note)}
                  onResetProblem={() => handleResetProblem(prob.id)}
                  onHintRevealed={() => handleHintRevealed(prob.id)}
                  onSetupRevealed={() => handleSetupRevealed(prob.id)}
                  onSolutionRevealed={() => handleSolutionRevealed(prob.id)}
                  onBeforeFetchVariant={flushAutoSave}
                  onExampleViewed={(viewedAt) => handleExampleViewed(prob.id, viewedAt)}
                  onSimilarProgressSync={(patch) => handleSimilarProgressSync(prob.id, patch)}
                  onVariantModeChange={handleVariantModeChange}
                  autoOpenSimilar={pendingSimilarProbId === prob.id}
                  onAutoOpenSimilarConsumed={() => setPendingSimilarProbId(null)}
                  onPrevQuestion={handlePrevQuestion}
                  onNextQuestion={handleNextQuestion}
                  onOpenReview={() => setViewMode("review")}
                  questionTimerMs={questionTimerMs}
                  totalTimerMs={totalTimerMs}
                  isTimerPaused={timerState.paused}
                  onToggleTimerPause={handleToggleTimerPause}
                  />
                </>
              );
            }

            return (
              <>
                {reviewContext}
                <CodeDashboard
                key={prob.id}
                problem={prob}
                drillId={currentDrill.drillId}
                index={idx}
                totalQuestions={currentDrill.problems.length}
                drillTitle={plainTitle(currentDrill.unitTitle) || currentDrill.unitCode}
                labReadme={currentDrill.labReadme}
                mistakeTags={currentDrill.mistakeTags || []}
                onInputChange={(val) => handleInputChange(prob.id, val)}
                onCheckAnswer={(inputOverride) => handleCheckAnswer(prob.id, inputOverride)}
                onSkip={(opts) => handleSkipProblem(prob.id, opts)}
                onMarkDivergedStep={(stepIdx) => handleMarkDivergedStep(prob.id, stepIdx)}
                onSetScore={(score) => handleSetScore(prob.id, score)}
                onTestReportChange={(rep, score) => handleTestReportChange(prob.id, rep, score)}
                onToggleMistakeTag={(tagId) => handleToggleMistakeTag(prob.id, tagId)}
                onMistakeNoteChange={(note) => handleMistakeNoteChange(prob.id, note)}
                onResetProblem={() => handleResetProblem(prob.id)}
                onHintRevealed={() => handleHintRevealed(prob.id)}
                onSolutionRevealed={() => handleSolutionRevealed(prob.id)}
                onPrevQuestion={handlePrevQuestion}
                onNextQuestion={handleNextQuestion}
                onOpenReview={() => setViewMode("review")}
                questionTimerMs={questionTimerMs}
                totalTimerMs={totalTimerMs}
                isTimerPaused={timerState.paused}
                onToggleTimerPause={handleToggleTimerPause}
                />
              </>
            );
          })()}
        </m.div>
      ) : (
        <m.div
          key={`${workspace}:${currentDrill.drillId}:review`}
          variants={fadeUp}
          initial="hidden"
          animate="shown"
        >
          <ReviewSyncPage
            currentDrill={currentDrill}
            statusOverride={statusOverride}
            isSyncing={isSyncing}
            syncState={syncState}
            totalDurationMs={getDrillTotalMs(currentDrill.problems, timerState, timerNow)}
            workspaceDrills={workspaceDrills}
            onStatusOverrideChange={handleStatusOverrideChange}
            onBackToQuiz={() => setViewMode("quiz")}
            onConfirmSync={handleConfirmSyncToNotion}
            onSelectQuestion={handleSelectQuestion}
            onTrySimilarQuestion={handleTrySimilarQuestion}
            onSetScore={handleSetScore}
            onToggleMistakeTag={handleToggleMistakeTag}
            onMistakeNoteChange={handleMistakeNoteChange}
            onRevisitNoteChange={handleRevisitNoteChange}
            onSelectDrill={handleSelectDrill}
            onOpenGenerate={() => setShowGenPopover(true)}
          />
        </m.div>
      )}
      {(() => {
        const isCurrentLab = Boolean(currentDrill && isLabId(currentDrill.drillId));
        const itemPlural = isCurrentLab
          ? "milestones"
          : workspace === "code"
          ? "problems"
          : "questions";
        const drillLabel = currentDrill
          ? plainTitle(currentDrill.unitTitle) || currentDrill.unitCode
          : "";
        return (
          <ConfirmDialog
            open={showResetConfirm && Boolean(currentDrill)}
            title={`Reset all ${itemPlural}?`}
            description={
              currentDrill
                ? `Reset all ${itemPlural} in ${drillLabel} to start over.`
                : ""
            }
            confirmLabel="Reset all"
            cancelLabel="Cancel"
            destructive
            onCancel={() => setShowResetConfirm(false)}
            onConfirm={() => {
              setShowResetConfirm(false);
              void handleResetAll().then(() => {
                setResetAllVersion((version) => version + 1);
                const url = new URL(window.location.href);
                if (url.searchParams.has("similar") || url.searchParams.has("tab")) {
                  url.searchParams.delete("similar");
                  url.searchParams.delete("tab");
                  window.history.replaceState(
                    window.history.state,
                    "",
                    url.pathname + url.search + url.hash
                  );
                }
              });
            }}
          />
        );
      })()}
    </StudioShell>
  );
};
