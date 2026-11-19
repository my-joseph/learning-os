"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { Problem, MistakeTag } from "@/types/drill";
import { QuestionTimer } from "@/components/QuestionTimer";
import { ResultCardSecondaryAction } from "@/components/AnswerResultCard";
import { ProblemNavFooter } from "@/components/workspace/ProblemNavFooter";
import { ProblemSelfEval } from "@/components/workspace/ProblemSelfEval";
import { MathItemView, MathItemViewHandle } from "@/components/math/MathItemView";
import { SimilarTabStrip } from "@/components/math/SimilarTabStrip";
import {
  WorkedExampleDisclosure,
  WorkedExampleView,
} from "@/components/math/WorkedExampleView";
import {
  SimilarProgressPatch,
  TabActivatedInfo,
  useSimilarTabs,
} from "@/hooks/useSimilarTabs";
import { hasSubstantiveAttempt } from "@/lib/reviewGuard";
import { maxAllowedSelfScore, scoreProblem } from "@/lib/scoring";
import {
  deriveRealTabStatus,
  isInCycle,
  resultCardActions,
  slotToTabId,
} from "@/lib/similarTabs";
import { plainTitle } from "@/lib/titleText";
import type { SkipOptions } from "@/hooks/types";

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
  onSkip?: (opts?: SkipOptions) => void;
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
  onSimilarProgressSync?: (patch: SimilarProgressPatch) => void;
  onVariantModeChange?: (inVariantMode: boolean) => void;
  autoOpenSimilar?: boolean;
  onAutoOpenSimilarConsumed?: () => void;
  onPrevQuestion?: () => void;
  onNextQuestion?: () => void;
  onOpenReview?: () => void;
  questionTimerMs?: number;
  totalTimerMs?: number;
  isTimerPaused?: boolean;
  onToggleTimerPause?: () => void;
  reviewSupplement?: React.ReactNode;
  isReviewSession?: boolean;
  isCorrectOnRetry?: boolean;
  reviewUnitTitle?: string;
  reviewScheduleNote?: string | null;
  nextCardLabel?: string;
  lastQuestionNavLabel?: string;
}

/** Clean centred Math workspace following docs/studio_design.md with Similar Questions v2 tab strip. */
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
  onSimilarProgressSync,
  onVariantModeChange,
  autoOpenSimilar = false,
  onAutoOpenSimilarConsumed,
  onPrevQuestion,
  onNextQuestion,
  onOpenReview,
  questionTimerMs,
  totalTimerMs,
  isTimerPaused = false,
  onToggleTimerPause,
  reviewSupplement,
  isReviewSession = false,
  isCorrectOnRetry = false,
  reviewUnitTitle,
  reviewScheduleNote = null,
  nextCardLabel,
  lastQuestionNavLabel,
}) => {
  const questionNumber = index + 1;
  const cardRef = useRef<HTMLElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const originalItemRef = useRef<MathItemViewHandle | null>(null);
  const similarItemRef = useRef<MathItemViewHandle | null>(null);
  const [similarStepsOpen, setSimilarStepsOpen] = useState(false);

  const handleTabActivated = useCallback((info: TabActivatedInfo) => {
    requestAnimationFrame(() => {
      if (info.isCorrect) {
        panelRef.current?.focus({ preventScroll: true });
      } else if (info.tabId === "q") {
        if (info.selectOriginal) {
          originalItemRef.current?.selectAnswer();
        } else {
          originalItemRef.current?.focusAnswer();
        }
      } else {
        similarItemRef.current?.focusAnswer();
      }
    });
  }, []);

  const {
    isUnlocked,
    listEmpty,
    selectedTab,
    tabs,
    activeSimilarTab,
    activeSimilarToken,
    activeSimilarProblem,
    isLoadingActiveTab,
    activeTabError,
    showingExample,
    example,
    exampleViewedAt,
    loadingExample,
    loadingSteps,
    activeStep: similarActiveStep,
    setActiveStep: setSimilarActiveStep,
    announcement,
    similarTimerMs,
    isSimilarPaused,
    toggleSimilarPaused,
    selectTab,
    retryActiveTab,
    openWorkedExample,
    closeWorkedExample,
    handleSimilarInputChange,
    handleSimilarCheckAnswer,
    handleSimilarHintRevealed,
    handleSimilarSetupRevealed,
    handleSimilarSolutionRevealed,
    handleSimilarReset,
    resetAllVariantUi,
  } = useSimilarTabs({
    drillId,
    problem,
    questionNumber,
    isReviewSession,
    autoOpenSimilar,
    onAutoOpenSimilarConsumed,
    onBeforeFetchVariant,
    onExampleViewed,
    onSimilarProgressSync,
    onTabActivated: handleTabActivated,
  });

  // Pause Q_N's timer while on a similar tab or viewing the worked example.
  useEffect(() => {
    onVariantModeChange?.(selectedTab !== "q" || showingExample);
    return () => {
      onVariantModeChange?.(false);
    };
  }, [selectedTab, showingExample, onVariantModeChange]);

  // Keep existing Esc-to-close behavior for the worked example view only (unchanged per scope change).
  useEffect(() => {
    if (!showingExample) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Escape" || e.defaultPrevented) return;
      if (document.querySelector('[role="alertdialog"], [role="dialog"]')) return;
      e.preventDefault();
      closeWorkedExample();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [showingExample, closeWorkedExample]);

  const hasAttempt = hasSubstantiveAttempt(problem.state);
  const score = scoreProblem(problem.state).score;
  const maxSelfScore = maxAllowedSelfScore(problem.state);
  const effectiveExampleViewedAt = exampleViewedAt || problem.state.exampleViewedAt || null;
  const exampleViewed = Boolean(
    example ||
      (effectiveExampleViewedAt &&
        isInCycle(effectiveExampleViewedAt, problem.state.cycleStartedAt))
  );

  const realTabStatus = deriveRealTabStatus(problem.state);
  const hasVariantsAvailable = Boolean(drillId && problem.hasVariants);
  const showTabStrip = Boolean(!showingExample && hasVariantsAvailable && !listEmpty);
  const stripLocked = !isUnlocked || tabs.length === 0;

  const rPlan = resultCardActions({
    tab: "q",
    hasVariants: hasVariantsAvailable,
    isReviewSession,
    rState: problem.state,
    statuses: tabs,
    exampleViewed,
  });

  const originalSecondaryActions: ResultCardSecondaryAction[] = [];
  if (rPlan.showPractiseSimilarFirst && rPlan.targetSimilarSlot) {
    const slot = rPlan.targetSimilarSlot;
    originalSecondaryActions.push({
      label: "Practise a similar question first",
      onClick: () => selectTab(slotToTabId(slot)),
      trailingChevron: true,
    });
  } else if (rPlan.showPractiseSimilarConfidence && rPlan.targetSimilarSlot) {
    const slot = rPlan.targetSimilarSlot;
    originalSecondaryActions.push({
      label: "Practise a similar question for confidence",
      onClick: () => selectTab(slotToTabId(slot)),
      trailingChevron: true,
    });
  }
  if (rPlan.showSeeExample) {
    originalSecondaryActions.push({
      label: "See a worked example",
      onClick: () => void openWorkedExample(),
      loading: loadingExample,
      disabled: loadingExample,
      trailingChevron: true,
    });
  }

  const isLastQuestion =
    typeof totalQuestions === "number" && totalQuestions > 0 && index === totalQuestions - 1;

  const displayTitle = plainTitle(drillTitle);

  const questionHeader = (
    <div className="flex items-center justify-between gap-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
      <div className="flex items-center gap-x-2 sm:gap-x-3 min-w-0 truncate">
        {isReviewSession ? (
          <>
            {(plainTitle(reviewUnitTitle) || unitCode) && (
              <span className="text-zinc-700 dark:text-zinc-300 truncate">
                {plainTitle(reviewUnitTitle) || unitCode}
              </span>
            )}
            {typeof problem.level === "number" && problem.level > 0 && (
              <span className="shrink-0" title={problem.levelLabel?.trim() || undefined}>
                Difficulty {problem.level}
              </span>
            )}
          </>
        ) : (
          <span className="truncate">
            Question {questionNumber}
            {typeof totalQuestions === "number" && totalQuestions > 0
              ? ` of ${totalQuestions}`
              : ""}
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
    activeSimilarProblem?.state.lastCheck?.verdict === "correct";

  const sPlan = resultCardActions({
    tab: selectedTab,
    hasVariants: hasVariantsAvailable,
    isReviewSession,
    rState: problem.state,
    statuses: tabs,
    exampleViewed,
    activeSimilarToken,
    activeSimilarVerdict: activeSimilarProblem?.state.lastCheck?.verdict ?? null,
    similarStepsOpen,
  });

  const similarSecondaryActions: ResultCardSecondaryAction[] = [];
  if (sPlan.showNextSimilar && sPlan.nextSimilarSlot) {
    const slot = sPlan.nextSimilarSlot;
    similarSecondaryActions.push({
      label: "Next similar question",
      onClick: () => selectTab(slotToTabId(slot)),
      trailingChevron: true,
    });
  }
  if (sPlan.showSimilarShowSteps) {
    similarSecondaryActions.push({
      label: "Show steps",
      onClick: () => similarItemRef.current?.openSteps(),
    });
  }
  if (sPlan.showSimilarBackLink) {
    similarSecondaryActions.push({
      label: `Back to Question ${questionNumber}`,
      onClick: () => selectTab("q", { selectOriginal: true }),
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
        className={`bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl scroll-mt-4 ${
          showTabStrip
            ? "px-4 pb-4 pt-2 sm:px-6 sm:pb-6 sm:pt-3 space-y-5"
            : "p-4 sm:p-6 space-y-6"
        }`}
      >
        {showingExample && example ? (
          <WorkedExampleView
            key={example.token}
            questionNumber={questionNumber}
            example={example}
            onBackToQuestion={closeWorkedExample}
          />
        ) : (
          <>
            {showTabStrip && (
              <SimilarTabStrip
                problemId={problem.id}
                questionNumber={questionNumber}
                realStatus={realTabStatus}
                tabs={tabs}
                selectedTab={selectedTab}
                locked={stripLocked}
                lockedSlotCount={problem.similarCount}
                onSelectTab={(tabId) => selectTab(tabId)}
              />
            )}

            <div
              ref={panelRef}
              role={showTabStrip ? "tabpanel" : undefined}
              id={showTabStrip ? `panel-${problem.id}` : undefined}
              aria-labelledby={
                showTabStrip ? `tab-${problem.id}-${selectedTab}` : undefined
              }
              tabIndex={showTabStrip ? -1 : undefined}
              className="space-y-6 focus:outline-none"
            >
              {selectedTab !== "q" && activeSimilarTab ? (
                activeTabError ? (
                  <div className="py-8 text-center space-y-3">
                    <p className="text-sm text-zinc-600 dark:text-zinc-400">
                      {activeTabError}
                    </p>
                    <button
                      type="button"
                      onClick={retryActiveTab}
                      className="inline-flex items-center justify-center min-h-[44px] sm:min-h-0 h-11 sm:h-9 px-4 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                    >
                      Retry
                    </button>
                  </div>
                ) : isLoadingActiveTab || !activeSimilarProblem ? (
                  <div className="space-y-4 animate-pulse py-2" aria-busy="true">
                    <div className="h-4 w-1/3 bg-zinc-200 dark:bg-zinc-800 rounded" />
                    <div className="h-16 w-full bg-zinc-100 dark:bg-zinc-950 rounded-xl" />
                    <div className="h-10 w-2/3 bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
                  </div>
                ) : (
                  <MathItemView
                    key={activeSimilarTab.token}
                    ref={similarItemRef}
                    problem={activeSimilarProblem}
                    header={
                      <div className="flex items-center justify-between gap-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                        <div className="min-w-0 truncate">
                          <span className="hidden sm:inline">
                            Similar question{" "}
                            <span className="font-display tabular-nums">
                              {activeSimilarTab.slot}
                            </span>{" "}
                            of{" "}
                            <span className="font-display tabular-nums">
                              {tabs.length}
                            </span>
                          </span>
                          <span className="sm:hidden">
                            Similar{" "}
                            <span className="font-display tabular-nums">
                              {activeSimilarTab.slot}/{tabs.length}
                            </span>
                          </span>
                        </div>
                        <QuestionTimer
                          questionMs={similarTimerMs}
                          totalMs={similarTimerMs}
                          isPaused={similarIsCorrect ? false : isSimilarPaused}
                          onTogglePause={similarIsCorrect ? undefined : toggleSimilarPaused}
                        />
                      </div>
                    }
                    unitCode={unitCode}
                    drillTitle={drillTitle}
                    mistakeTags={[]}
                    activeStep={similarActiveStep}
                    isVariant={true}
                    useSessionInputMode={isReviewSession}
                    hideShowStepsButton={sPlan.showSimilarShowSteps}
                    loadingSteps={loadingSteps}
                    ariaLabel={`Answer for similar question ${activeSimilarTab.slot} of ${tabs.length}`}
                    backLabel={`Back to Question ${questionNumber}`}
                    retryLabel={sPlan.retryLabel}
                    onBack={
                      similarIsCorrect
                        ? () => selectTab("q", { selectOriginal: true })
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
                )
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
                  isReviewSession={isReviewSession}
                  isCorrectOnRetry={isCorrectOnRetry}
                  reviewScheduleNote={isReviewSession ? reviewScheduleNote : null}
                  skipLabel={isReviewSession ? "Skip · due tomorrow" : "Skip"}
                  autoRevealOnSkip={!isReviewSession}
                  ariaLabel={
                    isReviewSession
                      ? `Answer for question ${index + 1} of ${totalQuestions ?? 1}`
                      : `Answer for question ${problem.id}`
                  }
                  nextLabel={nextCardLabel ?? "Next question"}
                  retryLabel={rPlan.retryLabel}
                  retryAriaLabel={rPlan.retryAriaLabel}
                  resultFootnote={rPlan.footnote}
                  resultSecondaryActions={originalSecondaryActions}
                  onInputChange={onInputChange}
                  onCheckAnswer={onCheckAnswer}
                  onSkip={onSkip}
                  onToggleStepHighlight={onToggleStepHighlight}
                  onMarkDivergedStep={onMarkDivergedStep}
                  onReset={() => {
                    resetAllVariantUi();
                    onResetProblem();
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
                      maxScore={maxSelfScore}
                      skipped={Boolean(problem.state.skipped)}
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
            </div>
          </>
        )}
      </article>

      {/* Question navigation footer — visible on R and on every similar tab */}
      {!showingExample && (
        <ProblemNavFooter
          index={index}
          isLastQuestion={isLastQuestion}
          onPrevQuestion={onPrevQuestion}
          onNextQuestion={onNextQuestion}
          onOpenReview={onOpenReview}
          lastQuestionLabel={lastQuestionNavLabel}
          nextDisabled={isReviewSession && !hasAttempt}
          hideNext={isReviewSession && hasAttempt}
        />
      )}
    </div>
  );
};
