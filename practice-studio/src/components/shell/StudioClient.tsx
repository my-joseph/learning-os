"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { m } from "motion/react";
import { fadeUp } from "@/lib/motion";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus } from "lucide-react";
import { DrillDocument } from "@/types/drill";

import type { MathWorkspaceProps } from "@/components/math/MathWorkspace";
import type { CodeDashboardProps } from "@/components/code/CodeDashboard";

const ReviewSyncPage = dynamic(
  () => import("@/components/review-sync/ReviewSyncPage").then((mod) => mod.ReviewSyncPage),
  { ssr: false }
);
import { StudioShell } from "@/components/shell/StudioShell";
import { DrillNotFoundCard } from "@/components/shell/DrillNotFoundCard";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Card } from "@/components/ui/shadcn/Card";
import { Skeleton } from "@/components/ui/shadcn/Skeleton";
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
import { sendPracticeAction } from "@/lib/practiceActions";
import { getPersistedStatusOverride } from "@/lib/sessionSummary";

export interface StudioClientProps {
  workspace: Workspace;
  drillId: string;
  initialQuestionId?: string;
  isLabRoute?: boolean;
  MathWorkspaceComponent?: React.ComponentType<MathWorkspaceProps>;
  CodeDashboardComponent?: React.ComponentType<CodeDashboardProps>;
}

/** Main interactive Practice Studio client bound to a workspace and drill route. */
export const StudioClient: React.FC<StudioClientProps> = ({
  workspace,
  drillId,
  initialQuestionId,
  isLabRoute = false,
  MathWorkspaceComponent,
  CodeDashboardComponent,
}) => {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [showGenPopover, setShowGenPopover] = useState(false);
  const [resetTargetId, setResetTargetId] = useState<string | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isSidebarActionPending, setIsSidebarActionPending] = useState(false);
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
    setResetTargetId(null);
    setDeleteTargetId(null);
    setDeleteError(null);
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

  const handleResetTarget = async () => {
    if (!resetTargetId || isSidebarActionPending) return;
    const targetId = resetTargetId;
    setIsSidebarActionPending(true);
    try {
      if (currentDrill?.drillId === targetId) {
        setResetTargetId(null);
        if (!(await handleResetAll())) return;
        setStatusOverride(null);
        setResetAllVersion((version) => version + 1);
        const url = new URL(window.location.href);
        if (url.searchParams.has("similar") || url.searchParams.has("tab")) {
          url.searchParams.delete("similar");
          url.searchParams.delete("tab");
          window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
        }
      } else {
        await flushAutoSave();
        const reset = await sendPracticeAction(targetId, "", { action: "reset-all" });
        if (!reset?.cycleStartedAt) throw new Error("Reset could not be saved. Try again.");
        setStatus({ text: "Drill reset to initial state.", type: "pass" });
        setResetTargetId(null);
        await loadDrillsList();
      }
    } catch (error) {
      setStatus({
        text: error instanceof Error ? error.message : "Reset failed. Try again.",
        type: "fail",
      });
    } finally {
      setIsSidebarActionPending(false);
    }
  };

  const handleDeleteTarget = async () => {
    if (!deleteTargetId || isSidebarActionPending) return;
    const targetId = deleteTargetId;
    const isCurrent = currentDrill?.drillId === targetId;
    setIsSidebarActionPending(true);
    setDeleteError(null);
    try {
      if (isCurrent) await flushAutoSave();
      const response = await fetch(`/api/drill?id=${encodeURIComponent(targetId)}`, { method: "DELETE" });
      const result = (await response.json().catch(() => null)) as { error?: string; deleted?: boolean } | null;
      if (!response.ok || !result?.deleted) {
        throw new Error(result?.error || "Delete failed. Try again.");
      }
      setDeleteTargetId(null);
      await loadDrillsList();
      if (isCurrent) {
        const nextId = workspaceDrills.find((drill) => drill.drillId !== targetId)?.drillId;
        router.replace(nextId ? drillHref(nextId) : "/");
      }
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : "Delete failed. Try again.");
    } finally {
      setIsSidebarActionPending(false);
    }
  };

  const handleReviewRetry = async () => {
    const problem = currentDrill?.problems[currentProblemIndex];
    if (!currentDrill || !problem) return;
    if (!(await handleResetProblem(problem.id))) return;
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
        if (currentDrill) {
          setResetTargetId(currentDrill.drillId);
        }
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
      onResetDrill={(targetId) => {
        setResetTargetId(targetId);
      }}
      onDeleteDrill={(targetId) => {
        setDeleteError(null);
        setDeleteTargetId(targetId);
      }}
      showGenPopover={showGenPopover}
      onShowGenPopoverChange={setShowGenPopover}
      onGenerated={handleGenerated}
      onSelectQuestion={handleSelectQuestion}
      onToggleViewMode={(mode) => setViewMode(mode)}
      status={status}
      onStatusChange={setStatus}
    >
      {isLoadingDrill ? (
        <Card
          role="status"
          aria-label="Loading drill"
          className="shadow-none p-6 space-y-4"
        >
          <Skeleton className="h-5 w-1/3 rounded-lg" />
          <Skeleton className="h-4 w-2/3 rounded-lg" />
          <Skeleton className="h-24 w-full rounded-xl bg-zinc-200 dark:bg-zinc-800" />
          <Skeleton className="h-10 w-1/2 rounded-xl" />
        </Card>
      ) : drillNotFound ? (
        <DrillNotFoundCard drillId={drillId} isLab={isLabRoute || isLabId(drillId)} />
      ) : !currentDrill ? (
        <Card className="shadow-none p-10 text-center space-y-3">
          <p className="text-base font-semibold text-zinc-800 dark:text-zinc-200">
            No practice drill selected
          </p>
          <button
            type="button"
            onClick={() => setShowGenPopover(true)}
            className="inline-flex min-h-[44px] sm:min-h-0 items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-sm font-semibold transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
          >
            <Plus className="w-4 h-4" />
            <span>Generate drill set</span>
          </button>
        </Card>
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

            if (workspace === "math" && MathWorkspaceComponent) {
              return (
                <>
                  {reviewContext}
                  <MathWorkspaceComponent
                  key={prob.id}
                  frameless
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

            if (!CodeDashboardComponent) return null;

            return (
              <>
                {reviewContext}
                <CodeDashboardComponent
                key={prob.id}
                frameless
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
          <>
          <ConfirmDialog
            open={Boolean(resetTargetId)}
            title={`Reset all ${resetTargetId && isLabId(resetTargetId) ? "milestones" : resetTargetId?.startsWith("DRL-PRG-") ? "problems" : "questions"}?`}
            description={resetTargetId === currentDrill?.drillId
              ? `Reset all ${itemPlural} in ${drillLabel} to start over.`
              : `Reset all items in ${resetTargetId || "this drill"} to start over.`}
            confirmLabel={isSidebarActionPending ? "Resetting…" : "Reset all"}
            cancelLabel="Cancel"
            destructive
            onCancel={() => {
              setResetTargetId(null);
            }}
            onConfirm={() => void handleResetTarget()}
          />
          <ConfirmDialog
            open={Boolean(deleteTargetId)}
            title="Delete this drill?"
            description={deleteError
              ? `${deleteTargetId}: ${deleteError}`
              : `Delete drill ${deleteTargetId || ""}? This removes its local drill content. Saved progress and workspace files are retained.`}
            confirmLabel={isSidebarActionPending ? "Deleting…" : "Delete drill"}
            cancelLabel="Cancel"
            destructive
            onCancel={() => {
              setDeleteTargetId(null);
              setDeleteError(null);
            }}
            onConfirm={() => void handleDeleteTarget()}
          />
          </>
        );
      })()}
    </StudioShell>
  );
};
