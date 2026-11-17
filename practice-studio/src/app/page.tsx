"use client";

import React, { useState, useCallback } from "react";
import { Plus, ChevronLeft, ChevronRight, ClipboardCheck } from "lucide-react";
import { ProblemCard } from "@/components/ProblemCard";
import { StudioShell } from "@/components/shell/StudioShell";
import { ReviewPanel } from "@/components/shell/ReviewPanel";
import { StatusMessage } from "@/hooks/types";
import { useTheme } from "@/hooks/useTheme";
import { useProgressSync, computeSessionMetrics } from "@/hooks/useProgressSync";
import { useDrill } from "@/hooks/useDrill";
import { useDrillList } from "@/hooks/useDrillList";

export default function PracticeStudioPage() {
  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [showGenPopover, setShowGenPopover] = useState(false);

  const { theme, handleToggleTheme } = useTheme();
  const {
    statusOverride,
    setStatusOverride,
    isSyncing,
    triggerAutoSave,
    confirmSyncToNotion,
  } = useProgressSync({ setStatus });

  const handleDrillLoaded = useCallback(() => {
    setStatusOverride(null);
  }, [setStatusOverride]);

  const {
    currentDrill,
    setCurrentDrill,
    activeSteps,
    currentProblemIndex,
    viewMode,
    setViewMode,
    isLoadingDrill,
    setIsLoadingDrill,
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
  });

  const {
    selectedDrillId,
    setSelectedDrillId,
    drillSearch,
    setDrillSearch,
    drillFilter,
    setDrillFilter,
    filteredDrills,
    loadDrillsList,
  } = useDrillList({
    loadDrill,
    setIsLoadingDrill,
    setStatus,
  });

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
      onSynced: (drillId) => loadDrillsList(drillId),
    });

  const handleSelectDrill = (drillId: string) => {
    setSelectedDrillId(drillId);
    loadDrill(drillId);
  };

  const isLastQuestion =
    currentDrill && currentProblemIndex === currentDrill.problems.length - 1;

  return (
    <StudioShell
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
      selectedDrillId={selectedDrillId}
      drillSearch={drillSearch}
      onSearchChange={setDrillSearch}
      drillFilter={drillFilter}
      onFilterChange={setDrillFilter}
      onSelectDrill={handleSelectDrill}
      showGenPopover={showGenPopover}
      onShowGenPopoverChange={setShowGenPopover}
      onGenerated={loadDrillsList}
      onSelectQuestion={handleSelectQuestion}
      onPrevQuestion={handlePrevQuestion}
      onNextQuestion={handleNextQuestion}
      onToggleViewMode={(mode) => setViewMode(mode)}
      status={status}
      onStatusChange={setStatus}
    >
      {isLoadingDrill ? (
        <div className="bg-white dark:bg-[#151924] border border-slate-200 dark:border-[#2c354d] rounded-2xl p-8 space-y-4 animate-pulse">
          <div className="h-6 w-1/3 bg-slate-200 dark:bg-slate-800 rounded-lg" />
          <div className="h-4 w-2/3 bg-slate-200 dark:bg-slate-800 rounded-lg" />
          <div className="h-28 w-full bg-slate-100 dark:bg-[#10141f] rounded-xl" />
          <div className="h-10 w-1/2 bg-slate-200 dark:bg-slate-800 rounded-xl" />
        </div>
      ) : !currentDrill ? (
        <div className="bg-white dark:bg-[#151924] border border-slate-200 dark:border-[#2c354d] rounded-2xl p-10 text-center space-y-3">
          <p className="text-base font-semibold text-slate-800 dark:text-slate-200">
            No Practice Drill Selected
          </p>
          <button
            type="button"
            onClick={() => setShowGenPopover(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold"
          >
            <Plus className="w-4 h-4" />
            <span>Generate New Drill Set</span>
          </button>
        </div>
      ) : viewMode === "quiz" && currentDrill.problems[currentProblemIndex] ? (
        /* ================================================================= */
        /* MODE 1: SINGLE QUESTION FOCUS MODE                                */
        /* ================================================================= */
        <div>
          {(() => {
            const prob = currentDrill.problems[currentProblemIndex];
            const idx = currentProblemIndex;
            return (
              <div key={prob.id}>
                <ProblemCard
                  problem={prob}
                  index={idx}
                  subject={currentDrill.subject}
                  mistakeTags={currentDrill.mistakeTags || []}
                  activeStep={activeSteps[prob.id] ?? null}
                  onInputChange={(val) => handleInputChange(prob.id, val)}
                  onCheckAnswer={() => handleCheckAnswer(prob.id)}
                  onSkip={() => handleSkipProblem(prob.id)}
                  onToggleStepHighlight={(stepIdx) =>
                    handleToggleStepHighlight(prob.id, stepIdx)
                  }
                  onMarkDivergedStep={(stepIdx) => handleMarkDivergedStep(prob.id, stepIdx)}
                  drillId={currentDrill.drillId}
                  onSetScore={(score) => handleSetScore(prob.id, score)}
                  onToggleMistakeTag={(tagId) => handleToggleMistakeTag(prob.id, tagId)}
                  onMistakeNoteChange={(note) => handleMistakeNoteChange(prob.id, note)}
                  onResetProblem={() => handleResetProblem(prob.id)}
                  onHintRevealed={() => handleHintRevealed(prob.id)}
                  onSetupRevealed={() => handleSetupRevealed(prob.id)}
                  onSolutionRevealed={() => handleSolutionRevealed(prob.id)}
                />

                {/* Bottom Question Navigation Footer */}
                <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-white dark:bg-[#141926] border border-slate-200 dark:border-[#2b3752] rounded-2xl shadow-sm mt-4">
                  <button
                    type="button"
                    onClick={handlePrevQuestion}
                    disabled={currentProblemIndex === 0}
                    className="inline-flex items-center gap-1.5 h-10 px-4 rounded-xl text-sm font-semibold bg-slate-100 dark:bg-[#1c2438] hover:bg-slate-200 dark:hover:bg-[#25304a] disabled:opacity-40 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-[#2c3852] transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span>Previous Question</span>
                  </button>

                  <div className="text-xs font-mono text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                    <span>Question</span>
                    <strong className="text-slate-900 dark:text-white bg-slate-100 dark:bg-[#1c2438] px-2.5 py-1 rounded-lg border border-slate-200 dark:border-[#2c3852]">
                      {currentProblemIndex + 1}
                    </strong>
                    <span>of</span>
                    <strong className="text-slate-700 dark:text-slate-300">
                      {currentDrill.problems.length}
                    </strong>
                  </div>

                  {isLastQuestion ? (
                    <button
                      type="button"
                      onClick={() => setViewMode("review")}
                      className="inline-flex items-center gap-2 h-10 px-5 rounded-xl text-sm font-semibold bg-emerald-700 hover:bg-emerald-800 text-white transition-colors shadow-sm"
                    >
                      <ClipboardCheck className="w-4 h-4" />
                      <span>Review &amp; Sync to Notion</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleNextQuestion}
                      className="inline-flex items-center gap-1.5 h-10 px-5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors shadow-sm"
                    >
                      <span>Next Question</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })()}
        </div>
      ) : (
        /* ================================================================= */
        /* MODE 2: PRE-SYNC REVIEW & EDIT VIEW (Flow 3.3)                    */
        /* ================================================================= */
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
}
