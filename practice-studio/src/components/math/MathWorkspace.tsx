"use client";

import { Heading } from "@/components/ui/Heading";
import { Input } from "@/components/ui/shadcn/Input";
import { PenLine } from "lucide-react";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, m } from "motion/react";
import { tabPanel } from "@/lib/motion";
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
import { isCurriculumId, plainTitle } from "@/lib/titleText";
import type { SkipOptions } from "@/hooks/types";

export interface MathWorkspaceProps {
  problem: Problem;
  drillId?: string;
  index: number;
  totalQuestions?: number;
  unitCode?: string;
  drillTitle?: string;
  mistakeTags: MistakeTag[];
  onInputChange: (val: string) => void;
  onCheckAnswer: (inputOverride?: string) => Promise<void> | void;
  onSkip?: (opts?: SkipOptions) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number | null) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
  onRevisitNoteChange?: (note: string) => void;
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
  frameless?: boolean;
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
  onInputChange,
  onCheckAnswer,
  onSkip,
  onMarkDivergedStep,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
  onRevisitNoteChange,
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
  frameless = false,
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
    exhausted,
    listError,
    isLoadingList,
    isOpeningNext,
    openNextError,
    openNext,
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
    announcement,
    similarTimerMs,
    isSimilarPaused,
    toggleSimilarPaused,
    selectTab,
    retrySimilarList,
    retryActiveTab,
    openWorkedExample,
    closeWorkedExample,
    handleSimilarInputChange,
    handleSimilarCheckAnswer,
    handleSimilarSkip,
    handleSimilarMarkDivergedStep,
    handleSimilarSetScore,
    handleSimilarToggleMistakeTag,
    handleSimilarMistakeNoteChange,
    handleSimilarRevisitNoteChange,
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

  // Match main-question "P" timer pause/resume shortcut while on a similar tab.
  useEffect(() => {
    if (selectedTab === "q" || showingExample) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.defaultPrevented || e.repeat || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key.toLowerCase() !== "p") return;
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.tagName === "MATH-FIELD" ||
          target.isContentEditable ||
          Boolean(target.closest('[role="alertdialog"], [role="dialog"], [role="tablist"]')))
      ) {
        return;
      }
      if (document.querySelector('[role="alertdialog"], [role="dialog"]')) return;
      e.preventDefault();
      toggleSimilarPaused();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selectedTab, showingExample, toggleSimilarPaused]);

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
  const showTabStrip = Boolean(!showingExample && hasVariantsAvailable);
  const canOpenNext = isUnlocked && !exhausted && !listError;
  const loadingSimilar = isLoadingList || isOpeningNext;
  const selectOrOpenSimilar = (slot: number | null) => {
    if (slot !== null) selectTab(slotToTabId(slot));
    else void openNext();
  };

  const rPlan = resultCardActions({
    tab: "q",
    hasVariants: hasVariantsAvailable,
    canOpenNext,
    isReviewSession,
    rState: problem.state,
    statuses: tabs,
    exampleViewed,
  });

  const originalSecondaryActions: ResultCardSecondaryAction[] = [];
  if (rPlan.showPractiseSimilarFirst) {
    const slot = rPlan.targetSimilarSlot;
    originalSecondaryActions.push({
      label: "Practise a similar question first",
      onClick: () => selectOrOpenSimilar(slot),
      disabled: slot === null && loadingSimilar,
      trailingChevron: true,
    });
  } else if (rPlan.showPractiseSimilarConfidence) {
    const slot = rPlan.targetSimilarSlot;
    originalSecondaryActions.push({
      label: "Practise a similar question for confidence",
      onClick: () => selectOrOpenSimilar(slot),
      disabled: slot === null && loadingSimilar,
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
  const reviewTitle = plainTitle(reviewUnitTitle) || unitCode || "";

  const questionHeader = (
    <div className="flex items-center justify-between gap-2 text-xs font-normal text-zinc-500 dark:text-zinc-400">
      <div className="flex items-center gap-x-2 sm:gap-x-3 min-w-0 truncate">
        {isReviewSession ? (
          <>
            {reviewTitle && (
              <span className={`text-foreground-control truncate ${
                isCurriculumId(reviewTitle) ? "font-mono" : ""
              }`}>
                {reviewTitle}
              </span>
            )}
            {typeof problem.level === "number" && problem.level > 0 && (
              <span className="shrink-0 font-sans tabular-nums" title={problem.levelLabel?.trim() || undefined}>
                Difficulty {problem.level}
              </span>
            )}
          </>
        ) : (
          <span className="truncate font-sans tabular-nums">
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
  const similarIsSkipped = Boolean(
    activeSimilarProblem?.state.skipped ||
      activeSimilarProblem?.state.lastCheck?.verdict === "skipped"
  );
  const similarIsDone = similarIsCorrect || similarIsSkipped;
  const similarAttempted = Boolean(
    activeSimilarProblem &&
      hasSubstantiveAttempt(activeSimilarProblem.state, { isVariant: true })
  );
  const similarScore = activeSimilarProblem
    ? scoreProblem(activeSimilarProblem.state, { isVariant: true }).score
    : null;
  const similarMaxSelfScore = activeSimilarProblem
    ? maxAllowedSelfScore(activeSimilarProblem.state, { isVariant: true })
    : 1;
  const similarReviewSupplement =
    isReviewSession && similarIsCorrect && activeSimilarProblem ? (
      <div className="space-y-space-1_5 pt-space-1">
        <label
          htmlFor={`revisit-note-${activeSimilarProblem.id}`}
          className="block text-xs font-normal text-foreground-subtle"
        >
          Next time I will…
        </label>
        <div className="flex items-center gap-space-2 bg-surface-panel dark:bg-surface-raised border border-border rounded-xl px-space-3 py-space-2 transition-colors focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/20 dark:focus-within:ring-accent/25">
          <PenLine className="size-space-3_5 text-muted shrink-0" aria-hidden="true" />
          <Input
            id={`revisit-note-${activeSimilarProblem.id}`}
            type="text"
            variant="embedded"
            value={activeSimilarProblem.state.revisitNote || ""}
            onChange={(e) => handleSimilarRevisitNoteChange(e.target.value)}
            aria-label="Next time I will…"
            placeholder="Next time I will…"
            className="text-xs"
          />
        </div>
      </div>
    ) : undefined;

  const sPlan = resultCardActions({
    tab: selectedTab,
    hasVariants: hasVariantsAvailable,
    canOpenNext,
    isReviewSession,
    rState: problem.state,
    statuses: tabs,
    exampleViewed,
    activeSimilarToken,
    activeSimilarVerdict: activeSimilarProblem?.state.lastCheck?.verdict ?? null,
    similarStepsOpen,
  });

  const similarSecondaryActions: ResultCardSecondaryAction[] = [];
  if (sPlan.showNextSimilar) {
    const slot = sPlan.nextSimilarSlot;
    similarSecondaryActions.push({
      label: "Next similar question",
      onClick: () => selectOrOpenSimilar(slot),
      disabled: slot === null && loadingSimilar,
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
        <Heading>
          {isCurriculumId(displayTitle) ? "Math drill" : displayTitle}
        </Heading>
      )}

      <article
        ref={cardRef}
        className={
          frameless
            ? `scroll-mt-4 ${showTabStrip ? "space-y-5" : "space-y-6"}`
            : `bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl scroll-mt-4 ${
                showTabStrip
                  ? "px-4 pb-4 pt-2 sm:px-6 sm:pb-6 sm:pt-3 space-y-5"
                  : "p-4 sm:p-6 space-y-6"
              }`
        }
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
                locked={!isUnlocked}
                exhausted={exhausted}
                error={listError ? `${listError} Try again.` : openNextError}
                loading={loadingSimilar}
                onAdd={listError ? retrySimilarList : () => void openNext()}
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
              <AnimatePresence mode="wait" initial={false}>
                <m.div
                  key={selectedTab}
                  variants={tabPanel}
                  initial="hidden"
                  animate="shown"
                  exit="exit"
                  className="space-y-6"
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
                        <div className="h-16 w-full bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
                        <div className="h-10 w-2/3 bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
                      </div>
                    ) : (
                      <MathItemView
                        key={activeSimilarTab.token}
                        ref={similarItemRef}
                        problem={activeSimilarProblem}
                        header={
                          <div className="flex items-center justify-between gap-2 text-xs font-normal text-zinc-500 dark:text-zinc-400">
                            <div className="min-w-0 truncate">
                              <span className="hidden sm:inline">
                                Similar question{" "}
                                <span className="font-sans tabular-nums">
                                  {activeSimilarTab.slot}
                                </span>{" "}
                                of{" "}
                                <span className="font-sans tabular-nums">
                                  {tabs.length}
                                </span>
                              </span>
                              <span className="sm:hidden">
                                Similar{" "}
                                <span className="font-sans tabular-nums">
                                  {activeSimilarTab.slot}/{tabs.length}
                                </span>
                              </span>
                            </div>
                            <QuestionTimer
                              questionMs={similarTimerMs}
                              totalMs={similarTimerMs}
                              isPaused={similarIsDone ? false : isSimilarPaused}
                              onTogglePause={similarIsDone ? undefined : toggleSimilarPaused}
                            />
                          </div>
                        }
                        unitCode={unitCode}
                        drillTitle={drillTitle}
                        mistakeTags={mistakeTags}
                        isVariant={true}
                        useSessionInputMode={isReviewSession}
                        skipLabel="Skip"
                        autoRevealOnSkip={!isReviewSession}
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
                        onSkip={(opts) => void handleSimilarSkip(opts)}
                        onMarkDivergedStep={handleSimilarMarkDivergedStep}
                        onReset={handleSimilarReset}
                        onHintRevealed={handleSimilarHintRevealed}
                        onSetupRevealed={() => void handleSimilarSetupRevealed()}
                        onSolutionRevealed={() => void handleSimilarSolutionRevealed()}
                        onStepsOpenChange={setSimilarStepsOpen}
                        supplement={similarReviewSupplement}
                        footer={
                          <ProblemSelfEval
                            hasAttempt={similarAttempted}
                            maxScore={similarMaxSelfScore}
                            skipped={similarIsSkipped}
                            score={similarScore}
                            mistakes={activeSimilarProblem.state.mistakes}
                            mistakeNote={activeSimilarProblem.state.mistakeNote}
                            mistakeTags={mistakeTags}
                            noteAriaLabel={`Note for similar question ${activeSimilarTab.slot}`}
                            onSetScore={handleSimilarSetScore}
                            onToggleMistakeTag={handleSimilarToggleMistakeTag}
                            onMistakeNoteChange={handleSimilarMistakeNoteChange}
                          />
                        }
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
                          revisitNote={problem.state.revisitNote}
                          onRevisitNoteChange={onRevisitNoteChange}
                        />
                      }
                    />
                  )}
                </m.div>
              </AnimatePresence>
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
