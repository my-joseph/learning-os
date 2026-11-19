"use client";

import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import { Check, Copy } from "lucide-react";
import { Reveal } from "@/components/motion/Reveal";
import { MathBlock } from "@/components/MathRender";
import { parseLineChoicePrompt } from "@/components/LineChoicePrompt";
import {
  AnswerResultCard,
  ResultCardSecondaryAction,
} from "@/components/AnswerResultCard";
import { ProblemAssistSection } from "@/components/workspace/ProblemAssistSection";
import { useChoiceController } from "@/components/workspace/useChoiceController";
import { MathQuestionBody } from "@/components/math/MathQuestionBody";
import { MathAnswerArea, MathAnswerAreaHandle } from "@/components/math/MathAnswerArea";
import { getProblemPlaceholder } from "@/lib/mathInput";
import { hasSubstantiveAttempt } from "@/lib/reviewGuard";
import { CheckResult, MistakeTag, Problem } from "@/types/drill";

export interface MathItemViewHandle {
  focusAnswer: () => void;
  selectAnswer: () => void;
  isPanelOpen: () => boolean;
  closePanel: () => void;
  openSteps: () => void;
  isStepsOpen: () => boolean;
}

export interface MathItemViewProps {
  problem: Problem;
  header: React.ReactNode;
  unitCode?: string;
  drillTitle?: string;
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  isLastQuestion?: boolean;
  isReviewSession?: boolean;
  useSessionInputMode?: boolean;
  isCorrectOnRetry?: boolean;
  reviewScheduleNote?: string | null;
  skipLabel?: string;
  nextLabel?: string;
  backLabel?: string;
  resultTitleOverride?: string;
  resultSecondaryActions?: ResultCardSecondaryAction[];
  autoFocusPrimaryAction?: boolean;
  autoRevealOnCorrect?: boolean;
  autoRevealOnSkip?: boolean;
  loadingSteps?: boolean;
  ariaLabel?: string;
  choiceKeyboardEnabled?: boolean;
  onInputChange: (val: string) => void;
  onCheckAnswer: (inputOverride?: string) => Promise<void> | void;
  onSkip?: () => void;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep?: (stepIdx: number) => void;
  onReset: () => void;
  onHintRevealed?: () => void;
  onSetupRevealed?: () => void;
  onSolutionRevealed?: () => void;
  onStepsOpenChange?: (open: boolean) => void;
  onNextQuestion?: () => void;
  onOpenReview?: () => void;
  onBack?: () => void;
  afterResultCard?: React.ReactNode;
  supplement?: React.ReactNode;
  footer?: React.ReactNode;
}

/**
 * Reusable Math question card body shared between drill questions and similar-question variants:
 * prompt/figure (`MathQuestionBody`), input (`MathAnswerArea`), `AnswerResultCard`, and
 * `ProblemAssistSection` (Reset, equation set-up, Hint, Show steps, Skip).
 */
export const MathItemView = forwardRef<MathItemViewHandle, MathItemViewProps>(
  function MathItemView(
    {
      problem,
      header,
      unitCode,
      drillTitle,
      mistakeTags,
      activeStep,
      isLastQuestion = false,
      isReviewSession = false,
      useSessionInputMode,
      isCorrectOnRetry = false,
      reviewScheduleNote = null,
      skipLabel = "Skip",
      nextLabel = "Next question",
      backLabel,
      resultTitleOverride,
      resultSecondaryActions,
      autoFocusPrimaryAction = false,
      autoRevealOnCorrect = true,
      autoRevealOnSkip,
      loadingSteps = false,
      ariaLabel,
      choiceKeyboardEnabled = true,
      onInputChange,
      onCheckAnswer,
      onSkip,
      onToggleStepHighlight,
      onMarkDivergedStep,
      onReset,
      onHintRevealed,
      onSetupRevealed,
      onSolutionRevealed,
      onStepsOpenChange,
      onNextQuestion,
      onOpenReview,
      onBack,
      afterResultCard,
      supplement,
      footer,
    },
    ref
  ) {
    const allowAutoRevealOnSkip = autoRevealOnSkip ?? !isReviewSession;
    const shouldAutoReveal = (p: Problem) =>
      autoRevealOnCorrect &&
      (p.state.lastCheck?.verdict === "correct" ||
        (allowAutoRevealOnSkip && Boolean(p.state.skipped)));

    const [copied, setCopied] = useState(false);
    const [showHint, setShowHint] = useState(false);
    const [showSolution, setShowSolution] = useState(() => shouldAutoReveal(problem));
    const [isChecking, setIsChecking] = useState(false);
    // Equation set-up (display + plain-text) is hidden until the learner asks for it or finishes the problem.
    const [showSetup, setShowSetup] = useState(() => shouldAutoReveal(problem));
    const answerAreaRef = useRef<MathAnswerAreaHandle | null>(null);
    const stepsRef = useRef<HTMLDivElement | null>(null);

    const {
      isChoice,
      choiceOptions,
      checkingOptionId,
      choiceLocked,
      choiceResultStatus,
      handleChoiceSelect,
      unlockChoiceRetry,
      resetChoiceState,
    } = useChoiceController({
      problem,
      isChecking,
      setIsChecking,
      onInputChange,
      onCheckAnswer,
      enabled: choiceKeyboardEnabled,
    });

    const hasSetup = Boolean(problem.hasSetup || problem.display || problem.plainText);
    const answered = hasSubstantiveAttempt(problem.state);
    const hasAttempt = answered;
    const setupUnopenedUnattempted =
      hasSetup &&
      !hasAttempt &&
      !showSetup &&
      !problem.state.setupRevealedBeforeAnswer;
    const stepsUnopenedUnattempted =
      !hasAttempt &&
      !showSolution &&
      !problem.state.solutionRevealedBeforeAnswer;
    const hasCorrectAttempt =
      problem.state.score === 1 ||
      Boolean(problem.state.attempts?.some((a) => a.verdict === "correct"));

    useEffect(() => {
      const reveal =
        autoRevealOnCorrect &&
        (problem.state.lastCheck?.verdict === "correct" ||
          (allowAutoRevealOnSkip && Boolean(problem.state.skipped)));
      setShowSolution(reveal);
      setShowSetup(reveal);
      setShowHint(false);
    }, [
      autoRevealOnCorrect,
      allowAutoRevealOnSkip,
      problem.id,
      problem.state.lastCheck?.verdict,
      problem.state.skipped,
    ]);

    useEffect(() => {
      if (!isReviewSession || !hasAttempt) return;
      let secondFrame: number | null = null;
      const firstFrame = requestAnimationFrame(() => {
        const btn = document.querySelector<HTMLButtonElement>(
          '[data-review-primary-action="true"]'
        );
        if (btn) {
          btn.focus();
          return;
        }
        secondFrame = requestAnimationFrame(() => {
          document
            .querySelector<HTMLButtonElement>('[data-review-primary-action="true"]')
            ?.focus();
        });
      });
      return () => {
        cancelAnimationFrame(firstFrame);
        if (secondFrame !== null) cancelAnimationFrame(secondFrame);
      };
    }, [
      isReviewSession,
      hasAttempt,
      problem.id,
      problem.state.lastCheck?.verdict,
      problem.state.attempts?.length,
    ]);

    useEffect(() => {
      onStepsOpenChange?.(showSolution);
    }, [showSolution, onStepsOpenChange]);

    const toggleSetup = () => {
      if (!showSetup && (!answered || (!problem.display && !problem.plainText)) && onSetupRevealed) {
        onSetupRevealed();
      }
      setShowSetup(!showSetup);
    };

    const handleCopyCas = () => {
      if (!problem.plainText) return;
      navigator.clipboard.writeText(problem.plainText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    };

    const lastCheck: CheckResult | null | undefined = problem.state.lastCheck;
    const placeholder = getProblemPlaceholder(problem);

    const triggerCheck = async (inputOverride?: string) => {
      if (isChecking) return;
      const resolved =
        inputOverride !== undefined
          ? inputOverride
          : answerAreaRef.current?.getPlainText() ?? problem.state.userInput;
      if (!resolved.trim()) return;
      if (resolved !== problem.state.userInput) {
        onInputChange(resolved);
      }
      setIsChecking(true);
      try {
        await onCheckAnswer(resolved);
      } finally {
        setIsChecking(false);
      }
    };

    const lineChoiceData = useMemo(
      () =>
        isChoice
          ? parseLineChoicePrompt(problem.prompt, problem.answerSpec.options)
          : null,
      [isChoice, problem.prompt, problem.answerSpec.options]
    );

    const handleTryAgain = () => {
      if (isChoice) {
        unlockChoiceRetry();
        return;
      }
      answerAreaRef.current?.select();
    };

    const handleShowStepsFromCard = () => {
      if (!showSolution) {
        if ((!hasCorrectAttempt || !problem.steps?.length) && onSolutionRevealed) {
          onSolutionRevealed();
        }
        setShowSolution(true);
      }
      requestAnimationFrame(() => {
        stepsRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    };

    useImperativeHandle(
      ref,
      () => ({
        focusAnswer: () => {
          if (isChoice) {
            unlockChoiceRetry();
            return;
          }
          answerAreaRef.current?.focus();
        },
        selectAnswer: () => {
          if (isChoice) {
            unlockChoiceRetry();
            return;
          }
          answerAreaRef.current?.select();
        },
        isPanelOpen: () => answerAreaRef.current?.isPanelOpen() ?? false,
        closePanel: () => answerAreaRef.current?.closePanel(),
        openSteps: handleShowStepsFromCard,
        isStepsOpen: () => showSolution,
      }),
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [isChoice, unlockChoiceRetry, showSolution, hasCorrectAttempt, problem.steps, onSolutionRevealed]
    );

    return (
      <>
        {/* 1 & 2. Question header + prompt (text-base, leading-relaxed) + optional figure */}
        <MathQuestionBody
          header={header}
          prompt={problem.prompt}
          figure={problem.figure}
          visual={problem.visual}
          lineChoiceData={lineChoiceData}
          selectedValue={problem.state.userInput}
          onSelectChoice={(optId) => void handleChoiceSelect(optId)}
          choiceLocked={choiceLocked}
          checkingOptionId={checkingOptionId}
          choiceResultStatus={choiceResultStatus}
        />

        {/* 3. Answer input / choice options + calm Result Card */}
        <div className="space-y-3">
          <MathAnswerArea
            ref={answerAreaRef}
            itemKey={problem.id}
            ariaLabel={ariaLabel ?? `Answer for question ${problem.id}`}
            value={problem.state.userInput}
            answerSpec={problem.answerSpec}
            prompt={problem.prompt}
            inputHint={problem.inputHint}
            placeholder={placeholder}
            unitCode={unitCode}
            drillTitle={drillTitle}
            isChecking={isChecking}
            isChoice={isChoice}
            hasLineChoice={Boolean(lineChoiceData)}
            choiceOptions={choiceOptions}
            choiceLocked={choiceLocked}
            checkingOptionId={checkingOptionId}
            choiceResultStatus={choiceResultStatus}
            useSessionInputMode={useSessionInputMode ?? isReviewSession}
            autoFocusOnMount={isReviewSession && !hasAttempt}
            onSelectChoice={(optId) => void handleChoiceSelect(optId)}
            onChange={onInputChange}
            onCheck={(override) => void triggerCheck(override)}
          />

          {/* 4. Calm Result Card directly under the answer area */}
          <AnswerResultCard
            lastCheck={lastCheck}
            state={problem.state}
            problem={problem}
            mistakeTags={mistakeTags}
            isLastQuestion={isLastQuestion}
            isReviewSession={isReviewSession}
            isCorrectOnRetry={isCorrectOnRetry}
            nextLabel={nextLabel}
            scheduleNote={isReviewSession ? reviewScheduleNote : null}
            backLabel={backLabel}
            titleOverride={resultTitleOverride}
            autoFocusPrimaryAction={autoFocusPrimaryAction}
            secondaryActions={resultSecondaryActions}
            onNextQuestion={onNextQuestion}
            onOpenReview={onOpenReview}
            onTryAgain={handleTryAgain}
            onShowSteps={handleShowStepsFromCard}
            onBack={onBack}
          />

          {afterResultCard}
        </div>

        {supplement}

        {/* 5. Quiet secondary actions: Reset / equation set-up / hint / steps / skip */}
        <ProblemAssistSection
          problem={problem}
          hasAttempt={hasAttempt}
          showHint={showHint}
          onToggleHint={() => {
            if (!showHint && onHintRevealed) {
              onHintRevealed();
            }
            setShowHint(!showHint);
          }}
          showSolution={showSolution}
          onToggleSolution={() => {
            if (!showSolution && (!hasCorrectAttempt || !problem.steps?.length) && onSolutionRevealed) {
              onSolutionRevealed();
            }
            setShowSolution(!showSolution);
          }}
          stepsUnopenedUnattempted={stepsUnopenedUnattempted}
          stepsRef={stepsRef}
          showStepsHeader={true}
          loadingSteps={loadingSteps}
          activeStep={activeStep}
          onToggleStepHighlight={onToggleStepHighlight}
          onMarkDivergedStep={onMarkDivergedStep}
          onReset={() => {
            setShowHint(false);
            setShowSetup(false);
            setShowSolution(false);
            resetChoiceState();
            onReset();
          }}
          onSkip={
            onSkip
              ? () => {
                  if (allowAutoRevealOnSkip && !showHint && onHintRevealed) {
                    onHintRevealed();
                  }
                  if (allowAutoRevealOnSkip) {
                    setShowHint(true);
                    setShowSolution(true);
                  }
                  onSkip();
                }
              : undefined
          }
          skipLabel={skipLabel}
          hasSetup={hasSetup}
          showSetup={showSetup}
          setupUnopenedUnattempted={setupUnopenedUnattempted}
          onToggleSetup={toggleSetup}
          setupDisclosure={
            <Reveal show={Boolean(hasSetup && showSetup)}>
              {hasSetup && showSetup && (
                <div className="bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-2.5">
                  {problem.display && (
                    <div className="overflow-x-auto overflow-y-hidden text-sm text-zinc-900 dark:text-zinc-100">
                      <MathBlock latex={problem.display} />
                    </div>
                  )}
                  {/* CAS copy row: only for typed answers; on choice questions the plain text is just the prompt. */}
                  {problem.plainText && !isChoice && (
                    <div
                      className={`flex flex-wrap items-center justify-between gap-2 text-xs ${
                        problem.display
                          ? "pt-2.5 border-t border-zinc-200 dark:border-zinc-800"
                          : ""
                      }`}
                    >
                      <code className="font-mono text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 px-2 py-0.5 rounded">
                        {problem.plainText}
                      </code>
                      <button
                        type="button"
                        onClick={handleCopyCas}
                        className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 transition-colors shrink-0"
                      >
                        {copied ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-700 dark:text-emerald-400" />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </Reveal>
          }
        />

        {footer}
      </>
    );
  }
);
