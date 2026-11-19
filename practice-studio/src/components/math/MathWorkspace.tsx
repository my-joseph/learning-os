"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft } from "lucide-react";
import { Problem, MistakeTag } from "@/types/drill";
import { QuestionTimer } from "@/components/QuestionTimer";
import { ResultCardSecondaryAction } from "@/components/AnswerResultCard";
import { ProblemNavFooter } from "@/components/workspace/ProblemNavFooter";
import { ProblemSelfEval } from "@/components/workspace/ProblemSelfEval";
import { MathItemView, MathItemViewHandle } from "@/components/math/MathItemView";
import {
  WorkedExampleDisclosure,
  WorkedExampleView,
} from "@/components/math/WorkedExampleView";
import {
  useVariantSession,
  VariantWorkspaceMode,
} from "@/hooks/useVariantSession";
import {
  countWrongAttempts,
  countWrongAttemptsAfter,
  hasSubstantiveAttempt,
} from "@/lib/reviewGuard";
import {
  getOriginalLadderActions,
  getSimilarLadderActions,
} from "@/lib/variantLadder";
import { plainTitle } from "@/lib/titleText";

export interface MathWorkspaceProps {
  problem: Problem;
  drillId?: string;
  index: number;
  totalQuestions?: number;
  unitCode?: string;
  drillTitle?: string;
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  onInputChange: (val: string) => void;
  onCheckAnswer: (inputOverride?: string) => Promise<void> | void;
  onSkip?: () => void;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number | null) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
  onResetProblem: () => void;
  onHintRevealed?: () => void;
  onSetupRevealed?: () => void;
  onSolutionRevealed?: () => void;
  onBeforeFetchVariant?: () => Promise<void>;
  onExampleViewed?: (viewedAt: string) => void;
  onVariantModeChange?: (inVariantMode: boolean) => void;
  onPrevQuestion?: () => void;
  onNextQuestion?: () => void;
  onOpenReview?: () => void;
  questionTimerMs?: number;
  totalTimerMs?: number;
  isTimerPaused?: boolean;
  onToggleTimerPause?: () => void;
  reviewSupplement?: React.ReactNode;
  isReviewSession?: boolean;
  nextCardLabel?: string;
  lastQuestionNavLabel?: string;
}

/** Clean centred Math workspace following docs/studio_design.md and the swap-in-place variant flow. */
export const MathWorkspace: React.FC<MathWorkspaceProps> = ({
  problem,
  drillId,
  index,
  totalQuestions,
  unitCode,
  drillTitle,
  mistakeTags,
  activeStep,
  onInputChange,
  onCheckAnswer,
  onSkip,
  onToggleStepHighlight,
  onMarkDivergedStep,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
  onResetProblem,
  onHintRevealed,
  onSetupRevealed,
  onSolutionRevealed,
  onBeforeFetchVariant,
  onExampleViewed,
  onVariantModeChange,
  onPrevQuestion,
  onNextQuestion,
  onOpenReview,
  questionTimerMs,
  totalTimerMs,
  isTimerPaused = false,
  onToggleTimerPause,
  reviewSupplement,
  isReviewSession = false,
  nextCardLabel,
  lastQuestionNavLabel,
}) => {
  const questionNumber = index + 1;
  const cardRef = useRef<HTMLElement | null>(null);
  const originalItemRef = useRef<MathItemViewHandle | null>(null);
  const similarItemRef = useRef<MathItemViewHandle | null>(null);
  const [similarStepsOpen, setSimilarStepsOpen] = useState(false);

  const scrollCardIntoView = useCallback(() => {
    const el = cardRef.current;
    if (!el || typeof el.scrollIntoView !== "function") return;
    const reduced =
      typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollIntoView({
      block: "start",
      behavior: reduced ? "auto" : "smooth",
    });
  }, []);

  const handleModeSwap = useCallback(
    (nextMode: VariantWorkspaceMode, opts?: { selectOriginal?: boolean }) => {
      requestAnimationFrame(() => {
        scrollCardIntoView();
        if (nextMode === "similar") {
          similarItemRef.current?.focusAnswer();
        } else if (nextMode === "original" && opts?.selectOriginal) {
          originalItemRef.current?.selectAnswer();
        }
      });
    },
    [scrollCardIntoView]
  );

  const {
    mode,
    activeSimilar,
    example,
    exampleViewedAt,
    remainingCount,
    serverVariantWrongs,
    hasUnfinishedActiveSimilar,
    loadingAction,
    loadingSteps,
    activeStep: similarActiveStep,
    setActiveStep: setSimilarActiveStep,
    announcement,
    similarTimerMs,
    isSimilarPaused,
    toggleSimilarPaused,
    openSimilar,
    loadAnotherSimilar,
    openWorkedExample,
    backToOriginal,
    handleSimilarInputChange,
    handleSimilarCheckAnswer,
    handleSimilarHintRevealed,
    handleSimilarSetupRevealed,
    handleSimilarSolutionRevealed,
    handleSimilarReset,
    resetAllVariantUi,
  } = useVariantSession({
    drillId,
    problem,
    questionNumber,
    isReviewSession,
    onBeforeFetchVariant,
    onExampleViewed,
    onModeSwap: handleModeSwap,
  });

  // Pause Q_N's timer while in similar-question or worked-example mode.
  useEffect(() => {
    onVariantModeChange?.(mode !== "original");
    return () => {
      onVariantModeChange?.(false);
    };
  }, [mode, onVariantModeChange]);

  // Esc returns to Question N (in similar mode only when no palette is open and field is empty; always in example mode).
  useEffect(() => {
    if (mode === "original") return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Escape" || e.defaultPrevented) return;
      if (document.querySelector('[role="alertdialog"], [role="dialog"]')) return;
      if (mode === "example") {
        e.preventDefault();
        backToOriginal({ selectOriginal: true });
        return;
      }
      if (mode === "similar") {
        if (similarItemRef.current?.isPanelOpen()) return;
        const currentInput = activeSimilar?.problem.state.userInput || "";
        if (currentInput.trim()) return;
        e.preventDefault();
        backToOriginal({ selectOriginal: true });
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mode, activeSimilar, backToOriginal]);

  const hasAttempt = hasSubstantiveAttempt(problem.state);
  const score = problem.state.score;
  const originalWrongAttempts = countWrongAttempts(problem.state);
  const clusterWrongAttempts = originalWrongAttempts + serverVariantWrongs;
  const effectiveExampleViewedAt = exampleViewedAt || problem.state.exampleViewedAt || null;
  const exampleViewed = Boolean(effectiveExampleViewedAt || example);
  const wrongAfterExample =
    countWrongAttemptsAfter(problem.state, effectiveExampleViewedAt) > 0;

  const originalLadder = getOriginalLadderActions({
    hasVariants: Boolean(drillId && problem.hasVariants),
    originalWrongAttempts,
    clusterWrongAttempts,
    hasActiveSimilar: hasUnfinishedActiveSimilar,
    remainingCount,
    exampleViewed,
    wrongAfterExample,
    lastVerdict: problem.state.lastCheck?.verdict,
    skipped: problem.state.skipped,
  });

  const originalSecondaryActions: ResultCardSecondaryAction[] = [];
  if (originalLadder.showResumeSimilar) {
    originalSecondaryActions.push({
      label: "Resume similar question",
      onClick: () => void openSimilar(),
      loading: loadingAction === "try",
      disabled: loadingAction !== null,
      trailingChevron: true,
    });
  } else if (originalLadder.showTrySimilar) {
    originalSecondaryActions.push({
      label: "Try a similar question",
      onClick: () => void openSimilar(),
      loading: loadingAction === "try",
      disabled: loadingAction !== null,
      trailingChevron: true,
    });
  }
  if (originalLadder.showSeeExample) {
    originalSecondaryActions.push({
      label: "See a worked example",
      onClick: () => void openWorkedExample(),
      loading: loadingAction === "example",
      disabled: loadingAction !== null,
      trailingChevron: true,
    });
  }
  const isLastQuestion =
    typeof totalQuestions === "number" && totalQuestions > 0 && index === totalQuestions - 1;

  const displayTitle = plainTitle(drillTitle);

  const questionHeader = (
    <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span>
          Question {questionNumber}
          {typeof totalQuestions === "number" && totalQuestions > 0
            ? ` of ${totalQuestions}`
            : ""}
        </span>
        {typeof problem.level === "number" && problem.level > 0 && (
          <span title={problem.levelLabel?.trim() || undefined}>
            Level {problem.level}
          </span>
        )}
      </div>
      <QuestionTimer
        questionMs={questionTimerMs ?? (problem.state?.durationMs || 0)}
        totalMs={totalTimerMs ?? (questionTimerMs ?? (problem.state?.durationMs || 0))}
        isPaused={isTimerPaused}
        onTogglePause={onToggleTimerPause}
      />
    </div>
  );

  const similarIsCorrect =
    activeSimilar?.problem.state.lastCheck?.verdict === "correct";
  const similarHasAttempt = activeSimilar
    ? hasSubstantiveAttempt(activeSimilar.problem.state)
    : false;
  const similarEffectiveRemaining =
    remainingCount !== null ? remainingCount : activeSimilar?.remainingCount ?? 0;

  const similarLadder = getSimilarLadderActions({
    hasAttemptOnCurrent: similarHasAttempt,
    isCurrentCorrect: Boolean(similarIsCorrect),
    clusterWrongAttempts,
    remainingCount: similarEffectiveRemaining,
    stepsOpen: similarStepsOpen,
  });

  const similarSecondaryActions: ResultCardSecondaryAction[] = [];
  if (similarLadder.showSeeExample) {
    similarSecondaryActions.push({
      label: "See a worked example",
      onClick: () => void openWorkedExample(),
      loading: loadingAction === "example",
      disabled: loadingAction !== null,
      trailingChevron: true,
    });
  }
  if (similarLadder.showAnotherSimilar) {
    similarSecondaryActions.push({
      label: similarIsCorrect ? "Another one" : "Another similar question",
      onClick: () => void loadAnotherSimilar(),
      loading: loadingAction === "try",
      disabled: loadingAction !== null,
      trailingChevron: true,
    });
  }

  return (
    <div className="mx-auto w-full max-w-[720px] space-y-4">
      <div aria-live="polite" className="sr-only">
        {announcement}
      </div>

      {displayTitle && (
        <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight px-0.5">
          {displayTitle}
        </h1>
      )}

      <article
        ref={cardRef}
        className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-6 scroll-mt-4"
      >
        {mode === "example" && example ? (
          <WorkedExampleView
            key={example.token}
            questionNumber={questionNumber}
            example={example}
            onBackToQuestion={() => backToOriginal({ selectOriginal: true })}
          />
        ) : mode === "similar" && activeSimilar ? (
          <MathItemView
            key={activeSimilar.token}
            ref={similarItemRef}
            problem={activeSimilar.problem}
            header={
              <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1 min-w-0">
                  <button
                    type="button"
                    onClick={() => backToOriginal({ selectOriginal: true })}
                    className="inline-flex items-center gap-1 min-h-[44px] sm:min-h-0 -ml-1.5 px-1.5 rounded-lg text-zinc-700 dark:text-zinc-300 hover:text-zinc-950 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                  >
                    <ChevronLeft className="w-4 h-4 shrink-0" aria-hidden="true" />
                    <span>Question {questionNumber}</span>
                  </button>
                  <span aria-hidden="true">·</span>
                  <span className="text-zinc-900 dark:text-zinc-100">
                    Similar question {activeSimilar.index} of {activeSimilar.total}
                  </span>
                </div>
                <QuestionTimer
                  questionMs={similarTimerMs}
                  totalMs={similarTimerMs}
                  isPaused={isSimilarPaused}
                  onTogglePause={toggleSimilarPaused}
                />
              </div>
            }
            unitCode={unitCode}
            drillTitle={drillTitle}
            mistakeTags={[]}
            activeStep={similarActiveStep}
            autoRevealOnCorrect={false}
            loadingSteps={loadingSteps}
            ariaLabel={`Answer for similar question ${activeSimilar.index} of ${activeSimilar.total}`}
            resultTitleOverride={
              similarIsCorrect
                ? `Correct · now try Question ${questionNumber}`
                : undefined
            }
            backLabel={`Back to Question ${questionNumber}`}
            onBack={
              similarLadder.showBackToOriginal
                ? () =>
                    backToOriginal({
                      selectOriginal: true,
                      markSimilarDone: true,
                    })
                : undefined
            }
            resultSecondaryActions={similarSecondaryActions}
            onInputChange={handleSimilarInputChange}
            onCheckAnswer={handleSimilarCheckAnswer}
            onToggleStepHighlight={(sIdx) =>
              setSimilarActiveStep((prev) => (prev === sIdx ? null : sIdx))
            }
            onReset={handleSimilarReset}
            onHintRevealed={handleSimilarHintRevealed}
            onSetupRevealed={() => void handleSimilarSetupRevealed()}
            onSolutionRevealed={() => void handleSimilarSolutionRevealed()}
            onStepsOpenChange={setSimilarStepsOpen}
          />
        ) : (
          <MathItemView
            ref={originalItemRef}
            problem={problem}
            header={questionHeader}
            unitCode={unitCode}
            drillTitle={drillTitle}
            mistakeTags={mistakeTags}
            activeStep={activeStep}
            isLastQuestion={isReviewSession ? false : isLastQuestion}
            nextLabel={nextCardLabel ?? "Next question"}
            resultSecondaryActions={originalSecondaryActions}
            onInputChange={onInputChange}
            onCheckAnswer={onCheckAnswer}
            onSkip={onSkip}
            onToggleStepHighlight={onToggleStepHighlight}
            onMarkDivergedStep={onMarkDivergedStep}
            onReset={() => {
              resetAllVariantUi();
              if (drillId) {
                void fetch("/api/variant", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ drillId, qid: problem.id, action: "reset-question" }),
                }).then((res) => {
                  if (res.ok) onResetProblem();
                });
              } else {
                onResetProblem();
              }
            }}
            onHintRevealed={onHintRevealed}
            onSetupRevealed={onSetupRevealed}
            onSolutionRevealed={onSolutionRevealed}
            onNextQuestion={onNextQuestion}
            onOpenReview={onOpenReview}
            afterResultCard={
              example ? <WorkedExampleDisclosure example={example} /> : undefined
            }
            supplement={reviewSupplement}
            footer={
              <ProblemSelfEval
                hasAttempt={hasAttempt}
                score={score}
                mistakes={problem.state.mistakes}
                mistakeNote={problem.state.mistakeNote}
                mistakeTags={mistakeTags}
                noteAriaLabel={`Note for question ${questionNumber}`}
                onSetScore={onSetScore}
                onToggleMistakeTag={onToggleMistakeTag}
                onMistakeNoteChange={onMistakeNoteChange}
              />
            }
          />
        )}
      </article>

      {/* Quiet question navigation footer — hidden in similar & worked-example modes */}
      {mode === "original" && (
        <ProblemNavFooter
          index={index}
          isLastQuestion={isLastQuestion}
          onPrevQuestion={onPrevQuestion}
          onNextQuestion={onNextQuestion}
          onOpenReview={onOpenReview}
          lastQuestionLabel={lastQuestionNavLabel}
        />
      )}
    </div>
  );
};
