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
const ReviewPanel = dynamic(
  () => import("@/components/shell/ReviewPanel").then((mod) => mod.ReviewPanel),
  { ssr: false }
);
import { StudioShell } from "@/components/shell/StudioShell";
import { DrillNotFoundCard } from "@/components/shell/DrillNotFoundCard";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
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
import { getDrillTotalMs, getProblemDisplayMs } from "@/lib/telemetryTimer";
import { plainTitle } from "@/lib/titleText";

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
    timerState,
    timerNow,
    handleToggleTimerPause,
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

  const {
    liveScore,
    maxScore,
    accuracyPct,
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
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 space-y-4 animate-pulse">
          <div className="h-5 w-1/3 bg-zinc-200 dark:bg-zinc-800 rounded-lg" />
          <div className="h-4 w-2/3 bg-zinc-200 dark:bg-zinc-800 rounded-lg" />
          <div className="h-24 w-full bg-zinc-100 dark:bg-zinc-950 rounded-xl" />
          <div className="h-10 w-1/2 bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
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
          key={`${workspace}:${currentDrill.drillId}:${currentDrill.problems[currentProblemIndex].id}`}
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

            if (workspace === "math") {
              return (
                <MathWorkspace
                  key={prob.id}
                  problem={prob}
                  index={idx}
                  totalQuestions={currentDrill.problems.length}
                  unitCode={currentDrill.unitCode}
                  drillTitle={plainTitle(currentDrill.unitTitle) || currentDrill.unitCode}
                  mistakeTags={currentDrill.mistakeTags || []}
                  activeStep={activeSteps[prob.id] ?? null}
                  onInputChange={(val) => handleInputChange(prob.id, val)}
                  onCheckAnswer={(inputOverride) => handleCheckAnswer(prob.id, inputOverride)}
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
                  questionTimerMs={questionTimerMs}
                  totalTimerMs={totalTimerMs}
                  isTimerPaused={timerState.paused}
                  onToggleTimerPause={handleToggleTimerPause}
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
                drillTitle={plainTitle(currentDrill.unitTitle) || currentDrill.unitCode}
                labReadme={currentDrill.labReadme}
                mistakeTags={currentDrill.mistakeTags || []}
                activeStep={activeSteps[prob.id] ?? null}
                onInputChange={(val) => handleInputChange(prob.id, val)}
                onCheckAnswer={(inputOverride) => handleCheckAnswer(prob.id, inputOverride)}
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
                onSolutionRevealed={() => handleSolutionRevealed(prob.id)}
                onPrevQuestion={handlePrevQuestion}
                onNextQuestion={handleNextQuestion}
                onOpenReview={() => setViewMode("review")}
                questionTimerMs={questionTimerMs}
                totalTimerMs={totalTimerMs}
                isTimerPaused={timerState.paused}
                onToggleTimerPause={handleToggleTimerPause}
              />
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
          <ReviewPanel
            currentDrill={currentDrill}
            liveScore={liveScore}
            maxScore={maxScore}
            accuracyPct={accuracyPct}
            computedPracticeStatus={computedPracticeStatus}
            isSyncing={isSyncing}
            totalDurationMs={getDrillTotalMs(currentDrill.problems, timerState, timerNow)}
            onStatusOverrideChange={setStatusOverride}
            onBackToQuiz={() => setViewMode("quiz")}
            onConfirmSync={handleConfirmSyncToNotion}
            onSelectQuestion={handleSelectQuestion}
            onSetScore={handleSetScore}
            onToggleMistakeTag={handleToggleMistakeTag}
            onMistakeNoteChange={handleMistakeNoteChange}
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
              handleResetAll();
            }}
          />
        );
      })()}
    </StudioShell>
  );
};
