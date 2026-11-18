"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus } from "lucide-react";
import { DrillDocument } from "@/types/drill";
import { CodeDashboard } from "@/components/code/CodeDashboard";
import { MathWorkspace } from "@/components/math/MathWorkspace";
import { StudioShell } from "@/components/shell/StudioShell";
import { ReviewPanel } from "@/components/shell/ReviewPanel";
import { DrillNotFoundCard } from "@/components/shell/DrillNotFoundCard";
import { StatusMessage } from "@/hooks/types";
import { useTheme } from "@/hooks/useTheme";
import { useProgressSync, computeSessionMetrics } from "@/hooks/useProgressSync";
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

interface StudioClientProps {
  workspace: Workspace;
  drillId: string;
  initialQuestionId?: string;
}

/** Main interactive Practice Studio client bound to a workspace and drill route. */
export const StudioClient: React.FC<StudioClientProps> = ({
  workspace,
  drillId,
  initialQuestionId,
}) => {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [showGenPopover, setShowGenPopover] = useState(false);
  const [lastMathId, setLastMathId] = useState<string | null>(null);
  const [lastCodeId, setLastCodeId] = useState<string | null>(null);

  const initialQuestionIdRef = useRef<string | undefined>(initialQuestionId);
  initialQuestionIdRef.current = initialQuestionId;

  const pendingReplacedQsRef = useRef<string[]>([]);

  const { theme, handleToggleTheme } = useTheme();
  const {
    statusOverride,
    setStatusOverride,
    isSyncing,
    triggerAutoSave,
    confirmSyncToNotion,
  } = useProgressSync({ setStatus });

  const handleDrillLoaded = useCallback(
    (doc: DrillDocument) => {
      setStatusOverride(null);
      writeLastDrillId(doc.drillId, workspace);
      if (workspace === "math") {
        setLastMathId(doc.drillId);
      } else {
        setLastCodeId(doc.drillId);
      }
    },
    [setStatusOverride, workspace]
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
    activeSteps,
    currentProblemIndex,
    setCurrentProblemIndex,
    viewMode,
    setViewMode,
    isLoadingDrill,
    drillNotFound,
    loadDrill,
    handleHintRevealed,
    handleCheckAnswer,
    handleInputChange,
    handleMistakeNoteChange,
    handleSetupRevealed,
    handleSolutionRevealed,
    handleToggleStepHighlight,
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
    setStatus,
    onDrillLoaded: handleDrillLoaded,
    onQuestionChange: handleQuestionUrlSync,
  });

  const {
    drills,
    labs,
    drillSearch,
    setDrillSearch,
    drillFilter,
    setDrillFilter,
    filteredDrills,
    filteredLabs,
    loadDrillsList,
  } = useDrillList({
    workspace,
    setStatus,
  });

  // Load drill whenever route drillId changes
  useEffect(() => {
    setStatus(null);
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

  const {
    liveScore,
    maxScore,
    accuracyPct,
    skippedCount,
    computedPracticeStatus,
  } = computeSessionMetrics(currentDrill, statusOverride);

  const handleConfirmSyncToNotion = () =>
    confirmSyncToNotion(currentDrill, {
      onDrillUpdated: setCurrentDrill,
      onSynced: () => loadDrillsList(),
    });

  const handleSelectDrill = (nextDrillId: string) => {
    if (nextDrillId === drillId) return;
    router.push(drillHref(nextDrillId));
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
      currentProblemIndex={currentProblemIndex}
      liveScore={liveScore}
      maxScore={maxScore}
      accuracyPct={accuracyPct}
      theme={theme}
      onToggleTheme={handleToggleTheme}
      onResetAll={handleResetAll}
      drills={filteredDrills}
      labs={filteredLabs}
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
      onPrevQuestion={handlePrevQuestion}
      onNextQuestion={handleNextQuestion}
      onToggleViewMode={(mode) => setViewMode(mode)}
      status={status}
      onStatusChange={setStatus}
    >
      {isLoadingDrill ? (
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 space-y-4 animate-pulse">
          <div className="h-5 w-1/3 bg-zinc-200 dark:bg-zinc-800 rounded-lg" />
          <div className="h-4 w-2/3 bg-zinc-200 dark:bg-zinc-800 rounded-lg" />
          <div className="h-24 w-full bg-zinc-100 dark:bg-zinc-950 rounded-xl" />
          <div className="h-10 w-1/2 bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
        </div>
      ) : drillNotFound ? (
        <DrillNotFoundCard drillId={drillId} />
      ) : !currentDrill ? (
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-10 text-center space-y-3">
          <p className="text-base font-semibold text-zinc-800 dark:text-zinc-200">
            No practice drill selected
          </p>
          <button
            type="button"
            onClick={() => setShowGenPopover(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-400 text-white text-sm font-semibold"
          >
            <Plus className="w-4 h-4" />
            <span>Generate drill set</span>
          </button>
        </div>
      ) : viewMode === "quiz" && currentDrill.problems[currentProblemIndex] ? (
        <div
          key={`${workspace}:${currentDrill.drillId}:${currentDrill.problems[currentProblemIndex].id}`}
          className="motion-fade-up"
        >
          {(() => {
            const prob = currentDrill.problems[currentProblemIndex];
            const idx = currentProblemIndex;

            if (workspace === "math") {
              return (
                <MathWorkspace
                  key={prob.id}
                  problem={prob}
                  index={idx}
                  totalQuestions={currentDrill.problems.length}
                  drillTitle={currentDrill.unitTitle || currentDrill.unitCode}
                  mistakeTags={currentDrill.mistakeTags || []}
                  activeStep={activeSteps[prob.id] ?? null}
                  onInputChange={(val) => handleInputChange(prob.id, val)}
                  onCheckAnswer={() => handleCheckAnswer(prob.id)}
                  onSkip={() => handleSkipProblem(prob.id)}
                  onToggleStepHighlight={(stepIdx) =>
                    handleToggleStepHighlight(prob.id, stepIdx)
                  }
                  onMarkDivergedStep={(stepIdx) => handleMarkDivergedStep(prob.id, stepIdx)}
                  onSetScore={(score) => handleSetScore(prob.id, score)}
                  onToggleMistakeTag={(tagId) => handleToggleMistakeTag(prob.id, tagId)}
                  onMistakeNoteChange={(note) => handleMistakeNoteChange(prob.id, note)}
                  onResetProblem={() => handleResetProblem(prob.id)}
                  onHintRevealed={() => handleHintRevealed(prob.id)}
                  onSetupRevealed={() => handleSetupRevealed(prob.id)}
                  onSolutionRevealed={() => handleSolutionRevealed(prob.id)}
                  onPrevQuestion={handlePrevQuestion}
                  onNextQuestion={handleNextQuestion}
                  onOpenReview={() => setViewMode("review")}
                />
              );
            }

            return (
              <CodeDashboard
                key={prob.id}
                problem={prob}
                drillId={currentDrill.drillId}
                index={idx}
                totalQuestions={currentDrill.problems.length}
                drillTitle={currentDrill.unitTitle || currentDrill.unitCode}
                labReadme={currentDrill.labReadme}
                mistakeTags={currentDrill.mistakeTags || []}
                activeStep={activeSteps[prob.id] ?? null}
                onInputChange={(val) => handleInputChange(prob.id, val)}
                onCheckAnswer={() => handleCheckAnswer(prob.id)}
                onSkip={() => handleSkipProblem(prob.id)}
                onToggleStepHighlight={(stepIdx) =>
                  handleToggleStepHighlight(prob.id, stepIdx)
                }
                onMarkDivergedStep={(stepIdx) => handleMarkDivergedStep(prob.id, stepIdx)}
                onSetScore={(score) => handleSetScore(prob.id, score)}
                onTestReportChange={(rep) => handleTestReportChange(prob.id, rep)}
                onToggleMistakeTag={(tagId) => handleToggleMistakeTag(prob.id, tagId)}
                onMistakeNoteChange={(note) => handleMistakeNoteChange(prob.id, note)}
                onResetProblem={() => handleResetProblem(prob.id)}
                onHintRevealed={() => handleHintRevealed(prob.id)}
                onSetupRevealed={() => handleSetupRevealed(prob.id)}
                onSolutionRevealed={() => handleSolutionRevealed(prob.id)}
                onPrevQuestion={handlePrevQuestion}
                onNextQuestion={handleNextQuestion}
                onOpenReview={() => setViewMode("review")}
              />
            );
          })()}
        </div>
      ) : (
        <ReviewPanel
          currentDrill={currentDrill}
          liveScore={liveScore}
          maxScore={maxScore}
          accuracyPct={accuracyPct}
          skippedCount={skippedCount}
          computedPracticeStatus={computedPracticeStatus}
          isSyncing={isSyncing}
          onStatusOverrideChange={setStatusOverride}
          onBackToQuiz={() => setViewMode("quiz")}
          onConfirmSync={handleConfirmSyncToNotion}
          onSelectQuestion={handleSelectQuestion}
          onSetScore={handleSetScore}
          onToggleMistakeTag={handleToggleMistakeTag}
          onMistakeNoteChange={handleMistakeNoteChange}
        />
      )}
    </StudioShell>
  );
};
