"use client";

import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { Reveal } from "@/components/motion/Reveal";
import {
  Copy,
  Check,
} from "lucide-react";
import { Problem, MistakeTag, CheckResult } from "@/types/drill";
import { MathBlock } from "@/components/MathRender";
import { FormattedText } from "@/components/FormattedText";
import { MathFigure } from "@/components/MathFigure";
import { LineChoicePrompt, parseLineChoicePrompt } from "@/components/LineChoicePrompt";
import { ChoiceOptionGroup } from "@/components/ChoiceOptionGroup";
import { AnswerResultCard } from "@/components/AnswerResultCard";
import { QuestionTimer } from "@/components/QuestionTimer";
import {
  ANSWER_FIELD_CONTAINER_CLASS,
  InlineCheckButton,
  PlainAnswerField,
} from "@/components/workspace/PlainAnswerField";
import { ProblemAssistSection } from "@/components/workspace/ProblemAssistSection";
import { ProblemNavFooter } from "@/components/workspace/ProblemNavFooter";
import { ProblemSelfEval } from "@/components/workspace/ProblemSelfEval";
import type { MathLiveInputHandle } from "@/components/math/MathLiveInput";
import { MathPalette } from "@/components/math/MathPalette";
import {
  getProblemPlaceholder,
  getUnitKeyboardProfile,
  isMathLiveSupportedAnswerSpec,
  MathInputMode,
  readMathInputMode,
  writeMathInputMode,
} from "@/lib/mathInput";
import { isTouchPrimaryDevice } from "@/lib/mathPalette";
import { hasSubstantiveAttempt } from "@/lib/reviewGuard";
import { plainTitle } from "@/lib/titleText";
import { useChoiceController } from "@/components/workspace/useChoiceController";

const DynamicMathLiveInput = dynamic(
  () => import("@/components/math/MathLiveInput"),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 min-w-0 h-11 pl-3 pr-12 py-2 flex items-center text-sm text-zinc-400 dark:text-zinc-500">
        Loading math input…
      </div>
    ),
  }
);

export interface MathWorkspaceProps {
  problem: Problem;
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
  onPrevQuestion?: () => void;
  onNextQuestion?: () => void;
  onOpenReview?: () => void;
  questionTimerMs?: number;
  totalTimerMs?: number;
  isTimerPaused?: boolean;
  onToggleTimerPause?: () => void;
  reviewSupplement?: React.ReactNode;
  isReviewSession?: boolean;
  reviewUnitTitle?: string;
  reviewScheduleNote?: string | null;
  nextCardLabel?: string;
  lastQuestionNavLabel?: string;
}

/** Clean centred Math workspace following docs/studio_design.md. */
export const MathWorkspace: React.FC<MathWorkspaceProps> = ({
  problem,
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
  onPrevQuestion,
  onNextQuestion,
  onOpenReview,
  questionTimerMs,
  totalTimerMs,
  isTimerPaused = false,
  onToggleTimerPause,
  reviewSupplement,
  isReviewSession = false,
  reviewUnitTitle,
  reviewScheduleNote = null,
  nextCardLabel,
  lastQuestionNavLabel,
}) => {
  const shouldAutoReveal = (p: Problem) =>
    p.state.lastCheck?.verdict === "correct" || Boolean(p.state.skipped);

  const [copied, setCopied] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [showSolution, setShowSolution] = useState(() => shouldAutoReveal(problem));
  const [isChecking, setIsChecking] = useState(false);
  // Equation set-up (display + plain-text) is hidden until the learner asks for it or finishes the problem.
  const [showSetup, setShowSetup] = useState(() => shouldAutoReveal(problem));
  const [inputMode, setInputMode] = useState<MathInputMode>("math");
  const [panelOpen, setPanelOpen] = useState(false);
  const answerInputRef = useRef<HTMLInputElement | null>(null);
  const mathLiveRef = useRef<MathLiveInputHandle | null>(null);
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
  });

  useEffect(() => {
    setInputMode(readMathInputMode());
  }, []);

  useEffect(() => {
    if (isTouchPrimaryDevice()) {
      setPanelOpen(false);
    }
  }, [problem.id]);
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
      problem.state.lastCheck?.verdict === "correct" || Boolean(problem.state.skipped);
    setShowSolution(reveal);
    setShowSetup(reveal);
    setShowHint(false);
  }, [problem.id, problem.state.lastCheck?.verdict, problem.state.skipped]);

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

  const score = problem.state.score;
  const lastCheck: CheckResult | null | undefined = problem.state.lastCheck;
  const isMathLiveSupported = isMathLiveSupportedAnswerSpec(problem.answerSpec);
  const useMathLive = !isChoice && isMathLiveSupported && inputMode === "math";
  const placeholder = getProblemPlaceholder(problem);
  const keyboardProfile = useMemo(
    () =>
      getUnitKeyboardProfile({
        unitCode,
        drillTitle,
        prompt: problem.prompt,
        inputHint: problem.inputHint,
      }),
    [unitCode, drillTitle, problem.prompt, problem.inputHint]
  );

  const triggerCheck = async (inputOverride?: string) => {
    if (isChecking) return;
    const resolved =
      inputOverride !== undefined
        ? inputOverride
        : useMathLive
        ? mathLiveRef.current?.getPlainText() ?? problem.state.userInput
        : problem.state.userInput;
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

  const handleInputModeChange = (nextMode: MathInputMode) => {
    if (nextMode === inputMode) {
      if (nextMode === "math") {
        mathLiveRef.current?.focus();
      } else {
        answerInputRef.current?.focus();
      }
      return;
    }

    if (nextMode === "plain") {
      const plain = mathLiveRef.current?.getPlainText();
      if (plain !== undefined && plain !== problem.state.userInput) {
        onInputChange(plain);
      }
      setPanelOpen(false);
      setInputMode("plain");
      writeMathInputMode("plain");
      requestAnimationFrame(() => {
        answerInputRef.current?.focus();
      });
    } else {
      setInputMode("math");
      writeMathInputMode("math");
      requestAnimationFrame(() => {
        mathLiveRef.current?.focus();
      });
    }
  };

  const handleMathFieldFocus = useCallback(() => {
    if (isTouchPrimaryDevice()) {
      setPanelOpen(true);
    }
  }, []);

  const handleInsertLatex = useCallback((latex: string) => {
    mathLiveRef.current?.insertLatex(latex);
  }, []);

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
    if (useMathLive) {
      mathLiveRef.current?.focus();
      mathLiveRef.current?.select();
      return;
    }
    answerInputRef.current?.focus();
    answerInputRef.current?.select();
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

  const isLastQuestion =
    typeof totalQuestions === "number" && totalQuestions > 0 && index === totalQuestions - 1;

  const displayTitle = plainTitle(drillTitle);

  return (
    <div className="mx-auto w-full max-w-[720px] space-y-4">
      {displayTitle && (
        <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight px-0.5">
          {displayTitle}
        </h1>
      )}

      <article className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-6">
        {/* 1. Question number + level + timer + prompt (text-base, leading-relaxed) */}
        <div className="space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              {isReviewSession ? (
                <>
                  {(plainTitle(reviewUnitTitle) || unitCode) && (
                    <span className="text-zinc-700 dark:text-zinc-300">
                      {plainTitle(reviewUnitTitle) || unitCode}
                    </span>
                  )}
                  {typeof problem.level === "number" && problem.level > 0 && (
                    <span title={problem.levelLabel?.trim() || undefined}>
                      Difficulty {problem.level}
                    </span>
                  )}
                </>
              ) : (
                <>
                  <span>
                    Question {index + 1}
                    {typeof totalQuestions === "number" && totalQuestions > 0
                      ? ` of ${totalQuestions}`
                      : ""}
                  </span>
                  {typeof problem.level === "number" && problem.level > 0 && (
                    <span title={problem.levelLabel?.trim() || undefined}>
                      Level {problem.level}
                    </span>
                  )}
                </>
              )}
            </div>
            <QuestionTimer
              questionMs={questionTimerMs ?? (problem.state?.durationMs || 0)}
              totalMs={totalTimerMs ?? (questionTimerMs ?? (problem.state?.durationMs || 0))}
              isPaused={isTimerPaused}
              onTogglePause={onToggleTimerPause}
            />
          </div>

          <div className="text-base leading-relaxed text-zinc-900 dark:text-zinc-100">
            {lineChoiceData ? (
              <LineChoicePrompt
                parsed={lineChoiceData}
                selectedValue={problem.state.userInput}
                onSelect={(optId) => void handleChoiceSelect(optId)}
                disabled={choiceLocked}
                checkingOptionId={checkingOptionId}
                resultStatus={choiceResultStatus}
              />
            ) : (
              <FormattedText text={problem.prompt} />
            )}
          </div>
        </div>

        {/* 2. Figure (larger: full column width) */}
        {(problem.figure || problem.visual) && (
          <div className="w-full">
            <MathFigure
              figure={problem.figure || problem.visual!}
              className="w-full"
            />
          </div>
        )}

        {/* 3. Answer input / choice options + calm Result Card */}
        <div className="space-y-3">
          {isChoice && !lineChoiceData && choiceOptions && (
            <ChoiceOptionGroup
              options={choiceOptions}
              selectedValue={problem.state.userInput}
              onSelect={(optId) => void handleChoiceSelect(optId)}
              disabled={choiceLocked}
              checkingOptionId={checkingOptionId}
              resultStatus={choiceResultStatus}
              layout="wrap"
            />
          )}

          {!isChoice && isMathLiveSupported && (
            <div
              onKeyDown={(e) => {
                if (e.key === "Escape" && panelOpen) {
                  e.preventDefault();
                  setPanelOpen(false);
                  mathLiveRef.current?.focus();
                }
              }}
              className="space-y-2"
            >
              {useMathLive ? (
                <div className={ANSWER_FIELD_CONTAINER_CLASS}>
                  <DynamicMathLiveInput
                    value={problem.state.userInput}
                    placeholder={placeholder}
                    ariaLabel={`Answer for question ${problem.id}`}
                    variables={problem.answerSpec.variables}
                    disabled={isChecking}
                    fieldRef={mathLiveRef}
                    onChange={onInputChange}
                    onCheck={(plain) => void triggerCheck(plain)}
                    onFocus={handleMathFieldFocus}
                    onEscape={() => {
                      if (!panelOpen) return false;
                      setPanelOpen(false);
                      return true;
                    }}
                  />
                  <InlineCheckButton
                    onClick={() => void triggerCheck()}
                    disabled={isChecking || !problem.state.userInput.trim()}
                    isChecking={isChecking}
                  />
                </div>
              ) : (
                <PlainAnswerField
                  inputRef={answerInputRef}
                  value={problem.state.userInput}
                  onChange={onInputChange}
                  onCheck={() => void triggerCheck()}
                  placeholder={placeholder}
                  aria-label={`Answer for question ${problem.id}`}
                  isChecking={isChecking}
                />
              )}

              <MathPalette
                inputMode={inputMode}
                onModeChange={handleInputModeChange}
                keyboardProfile={keyboardProfile}
                panelOpen={panelOpen}
                onTogglePanel={() => {
                  setPanelOpen((prev) => !prev);
                  mathLiveRef.current?.focus();
                }}
                onInsertLatex={handleInsertLatex}
                disabled={isChecking}
              />
            </div>
          )}

          {!isChoice && !isMathLiveSupported && (
            <PlainAnswerField
              inputRef={answerInputRef}
              value={problem.state.userInput}
              onChange={onInputChange}
              onCheck={() => void triggerCheck()}
              placeholder={placeholder}
              aria-label={`Answer for question ${problem.id}`}
              isChecking={isChecking}
            />
          )}

          {/* 4. Calm Result Card directly under the answer area */}
          <AnswerResultCard
            lastCheck={lastCheck}
            state={problem.state}
            problem={problem}
            mistakeTags={mistakeTags}
            isLastQuestion={isReviewSession ? false : isLastQuestion}
            nextLabel={nextCardLabel ?? "Next question"}
            scheduleNote={isReviewSession ? reviewScheduleNote : null}
            onNextQuestion={onNextQuestion}
            onOpenReview={onOpenReview}
            onTryAgain={handleTryAgain}
            onShowSteps={handleShowStepsFromCard}
          />
        </div>

        {reviewSupplement}

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
          activeStep={activeStep}
          onToggleStepHighlight={onToggleStepHighlight}
          onMarkDivergedStep={onMarkDivergedStep}
          onReset={() => {
            resetChoiceState();
            onResetProblem();
          }}
          onSkip={
            onSkip
              ? () => {
                  if (!showHint && onHintRevealed) {
                    onHintRevealed();
                  }
                  setShowHint(true);
                  setShowSolution(true);
                  onSkip();
                }
              : undefined
          }
          skipLabel={isReviewSession ? "Skip · due tomorrow" : "Skip"}
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

        {/* 6. Self-score, mistake tags & mistake note — shown ONLY after an attempt */}
        <ProblemSelfEval
          hasAttempt={hasAttempt}
          score={score}
          mistakes={problem.state.mistakes}
          mistakeNote={problem.state.mistakeNote}
          mistakeTags={mistakeTags}
          noteAriaLabel={`Note for question ${index + 1}`}
          onSetScore={onSetScore}
          onToggleMistakeTag={onToggleMistakeTag}
          onMistakeNoteChange={onMistakeNoteChange}
        />
      </article>

      {/* Quiet question navigation footer */}
      <ProblemNavFooter
        index={index}
        isLastQuestion={isLastQuestion}
        onPrevQuestion={onPrevQuestion}
        onNextQuestion={onNextQuestion}
        onOpenReview={onOpenReview}
        lastQuestionLabel={lastQuestionNavLabel}
        nextDisabled={isReviewSession && !hasAttempt}
      />
    </div>
  );
};
