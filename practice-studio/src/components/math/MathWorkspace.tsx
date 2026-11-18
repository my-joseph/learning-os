"use client";

import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { Reveal } from "@/components/motion/Reveal";
import {
  Copy,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Loader2,
  PenLine,
} from "lucide-react";
import { Problem, MistakeTag, CheckResult } from "@/types/drill";
import { MathBlock } from "@/components/MathRender";
import { FormattedText } from "@/components/FormattedText";
import { StepRow } from "@/components/StepRow";
import { MathFigure } from "@/components/MathFigure";
import { LineChoicePrompt, parseLineChoicePrompt } from "@/components/LineChoicePrompt";
import { ChoiceOptionGroup } from "@/components/ChoiceOptionGroup";
import { AnswerResultCard } from "@/components/AnswerResultCard";
import { hasCheckpointHint } from "@/lib/studioRules";
import { hasSubstantiveAttempt } from "@/lib/reviewGuard";
import {
  getChoiceResultStatus,
  isChoiceInteractionLocked,
  isChoiceQuestion,
  isEditableEventTarget,
  resolveChoiceKeyOption,
  submitChoiceSelection,
} from "@/lib/answerFeedback";

export interface MathWorkspaceProps {
  problem: Problem;
  index: number;
  totalQuestions?: number;
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
}

const DEFAULT_PLACEHOLDER_BY_TYPE: Record<string, string> = {
  interval: "Enter interval, e.g. [a, b) or (-inf, a) U (a, inf)...",
};

const getSafeMathPlaceholder = (hint?: string, problem?: Problem): string => {
  if (problem?.placeholder) return problem.placeholder;
  const fallback =
    (problem?.answerSpec?.type && DEFAULT_PLACEHOLDER_BY_TYPE[problem.answerSpec.type]) ||
    "Enter your answer…";
  return hint || fallback;
};

/** Clean centred Math workspace following docs/studio_design.md. */
export const MathWorkspace: React.FC<MathWorkspaceProps> = ({
  problem,
  index,
  totalQuestions,
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
}) => {
  const shouldAutoReveal = (p: Problem) =>
    p.state.lastCheck?.verdict === "correct" || Boolean(p.state.skipped);

  const [copied, setCopied] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [showSolution, setShowSolution] = useState(() => shouldAutoReveal(problem));
  const [isChecking, setIsChecking] = useState(false);
  const [checkingOptionId, setCheckingOptionId] = useState<string | null>(null);
  const [choiceRetryUnlocked, setChoiceRetryUnlocked] = useState(false);
  // Equation set-up (display + plain-text) is hidden until the learner asks for it or finishes the problem.
  const [showSetup, setShowSetup] = useState(() => shouldAutoReveal(problem));
  const answerInputRef = useRef<HTMLInputElement | null>(null);
  const stepsRef = useRef<HTMLDivElement | null>(null);
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
  const showAssistedNote =
    !hasAttempt &&
    !showSetup &&
    !showSolution &&
    !problem.state.setupRevealedBeforeAnswer &&
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

  useEffect(() => {
    setCheckingOptionId(null);
    setChoiceRetryUnlocked(false);
  }, [problem.id]);

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

  const triggerCheck = async () => {
    if (!problem.state.userInput.trim() || isChecking) return;
    setIsChecking(true);
    try {
      await onCheckAnswer();
    } finally {
      setIsChecking(false);
    }
  };

  const score = problem.state.score;
  const lastCheck: CheckResult | null | undefined = problem.state.lastCheck;
  const isChoice = isChoiceQuestion(problem);
  const choiceOptions = problem.answerSpec.options;
  const choiceLocked = isChoiceInteractionLocked({
    isChecking,
    lastCheck,
    skipped: problem.state.skipped,
    retryUnlocked: choiceRetryUnlocked,
  });
  const choiceResultStatus = getChoiceResultStatus({
    isChecking,
    lastCheck,
    skipped: problem.state.skipped,
  });

  const lineChoiceData = useMemo(
    () =>
      isChoice
        ? parseLineChoicePrompt(problem.prompt, problem.answerSpec.options)
        : null,
    [isChoice, problem.prompt, problem.answerSpec.options]
  );

  const handleChoiceSelect = useCallback(
    async (optionId: string) => {
      await submitChoiceSelection({
        optionId,
        disabled: choiceLocked,
        isChecking,
        onStart: (id) => {
          setChoiceRetryUnlocked(false);
          setCheckingOptionId(id);
          setIsChecking(true);
        },
        onInputChange,
        onCheckAnswer,
        onFinish: () => {
          setIsChecking(false);
          setCheckingOptionId(null);
        },
      });
    },
    [choiceLocked, isChecking, onInputChange, onCheckAnswer]
  );

  useEffect(() => {
    if (!isChoice || !choiceOptions?.length) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (!/^[1-9]$/.test(e.key)) return;
      if (isEditableEventTarget(e.target)) return;
      if (document.querySelector('[role="alertdialog"], [role="dialog"]')) return;
      if (choiceLocked || isChecking) return;
      const matched = resolveChoiceKeyOption(e.key, choiceOptions);
      if (!matched) return;
      e.preventDefault();
      void handleChoiceSelect(matched.id);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isChoice, choiceOptions, choiceLocked, isChecking, handleChoiceSelect]);

  const handleTryAgain = () => {
    if (isChoice) {
      setChoiceRetryUnlocked(true);
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

  return (
    <div className="mx-auto w-full max-w-[720px] space-y-4">
      {drillTitle && (
        <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight px-0.5">
          {drillTitle}
        </h1>
      )}

      <article className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-6">
        {/* 1. Question number + level + prompt (text-base, leading-relaxed) */}
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
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

          {!isChoice && (
            <div className="flex items-center gap-2.5">
              <input
                ref={answerInputRef}
                type="text"
                value={problem.state.userInput}
                onChange={(e) => onInputChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    triggerCheck();
                  }
                }}
                placeholder={getSafeMathPlaceholder(problem.inputHint, problem)}
                aria-label={`Answer for question ${problem.id}`}
                className="flex-1 min-w-0 h-11 font-mono text-sm bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 border border-zinc-300 dark:border-zinc-700 rounded-xl px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-600/25 dark:focus:ring-indigo-500/30 focus:border-indigo-600 dark:focus:border-indigo-500 placeholder:text-zinc-400 dark:placeholder:text-zinc-500"
              />

              <button
                type="button"
                onClick={triggerCheck}
                disabled={isChecking || !problem.state.userInput.trim()}
                aria-label="Check answer"
                title="Check answer (Enter)"
                className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 disabled:opacity-40 text-white transition-colors shrink-0"
              >
                {isChecking ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Check className="w-4 h-4" />
                )}
              </button>
            </div>
          )}

          {/* 4. Calm Result Card directly under the answer area */}
          <AnswerResultCard
            lastCheck={lastCheck}
            state={problem.state}
            problem={problem}
            mistakeTags={mistakeTags}
            isLastQuestion={isLastQuestion}
            nextLabel="Next question"
            onNextQuestion={onNextQuestion}
            onOpenReview={onOpenReview}
            onTryAgain={handleTryAgain}
            onShowSteps={handleShowStepsFromCard}
          />
        </div>

        {/* 5. Quiet secondary actions: Reset / equation set-up / hint / steps / skip */}
        <div className="space-y-3 pt-1">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-zinc-500 dark:text-zinc-400">
            {hasAttempt && (
              <button
                type="button"
                onClick={() => {
                  setChoiceRetryUnlocked(false);
                  setCheckingOptionId(null);
                  onResetProblem();
                }}
                className="inline-flex items-center gap-1.5 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset</span>
              </button>
            )}

            {hasSetup && (
              <button
                type="button"
                onClick={toggleSetup}
                aria-expanded={showSetup}
                title={
                  setupUnopenedUnattempted
                    ? "Opening before checking counts as assisted"
                    : undefined
                }
                className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
              >
                <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${showSetup ? "rotate-180" : ""}`} />
                <span>{showSetup ? "Hide equation set-up" : "Show equation set-up"}</span>
              </button>
            )}

            {hasCheckpointHint(problem.checkpointHint) && <button
              type="button"
              onClick={() => {
                if (!showHint && onHintRevealed) {
                  onHintRevealed();
                }
                setShowHint(!showHint);
              }}
              aria-expanded={showHint}
              className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${showHint ? "rotate-180" : ""}`} />
              <span>{showHint ? "Hide hint" : "Hint"}</span>
            </button>}

            <button
              type="button"
              onClick={() => {
                if (!showSolution && (!hasCorrectAttempt || !problem.steps?.length) && onSolutionRevealed) {
                  onSolutionRevealed();
                }
                setShowSolution(!showSolution);
              }}
              aria-expanded={showSolution}
              title={
                stepsUnopenedUnattempted
                  ? "Opening before checking counts as assisted"
                  : undefined
              }
              className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${showSolution ? "rotate-180" : ""}`} />
              <span>{showSolution ? "Hide steps" : "Show steps"}</span>
            </button>

            {onSkip && !hasAttempt && (
              <button
                type="button"
                onClick={() => {
                  if (!showHint && onHintRevealed) {
                    onHintRevealed();
                  }
                  setShowHint(true);
                  setShowSolution(true);
                  onSkip();
                }}
                className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors ml-auto"
              >
                <span>Skip</span>
              </button>
            )}
          </div>

          {showAssistedNote && (
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              {hasSetup
                ? "Opening equation set-up or steps before checking counts as assisted."
                : "Opening steps before checking counts as assisted."}
            </p>
          )}

          {/* Checkpoint Hint Disclosure */}
          <Reveal show={Boolean(showHint && hasCheckpointHint(problem.checkpointHint))}>
          {showHint && hasCheckpointHint(problem.checkpointHint) && (
            <div className="border-l-2 border-amber-600 dark:border-amber-400 pl-3.5 py-1 text-sm text-zinc-700 dark:text-zinc-300">
              <FormattedText text={problem.checkpointHint} />
            </div>
          )}
          </Reveal>

          {/* Equation Set-up Disclosure */}
          <Reveal show={Boolean(hasSetup && showSetup)}>
          {hasSetup && showSetup && (
            <div className="bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-2.5">
              {problem.display && (
                <div className="overflow-x-auto text-sm text-zinc-900 dark:text-zinc-100">
                  <MathBlock latex={problem.display} />
                </div>
              )}
              {problem.plainText && (
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

          {/* Step-by-Step Derivation Disclosure */}
          <Reveal show={Boolean(showSolution)}>
          {showSolution && (
            <div
              ref={stepsRef}
              className={`bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-3 ${
                activeStep !== null ? "has-active" : ""
              }`}
            >
              <div className="flex flex-wrap justify-between items-center gap-2 pb-2 border-b border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 dark:text-zinc-400">
                <span className="font-medium">Steps</span>
                {problem.answerDisplay && (
                  <span>
                    Answer:{" "}
                    <strong className="text-zinc-900 dark:text-zinc-100 font-semibold">
                      <FormattedText text={`$${problem.answerDisplay}$`} />
                    </strong>
                  </span>
                )}
              </div>
              <div>
                {(problem.steps || []).map((st, sIdx) => (
                  <StepRow
                    key={sIdx}
                    step={st}
                    index={sIdx}
                    isActive={activeStep === sIdx}
                    isDiverged={problem.state.divergedStep === sIdx}
                    onToggleHighlight={() => onToggleStepHighlight(sIdx)}
                    onMarkDiverged={() => onMarkDivergedStep(sIdx)}
                  />
                ))}
              </div>
            </div>
          )}
          </Reveal>
        </div>

        {/* 6. Self-score, mistake tags & mistake note — shown ONLY after an attempt */}
        {hasAttempt && (
          <div className="pt-4 border-t border-zinc-200 dark:border-zinc-800 space-y-3 text-xs text-zinc-500 dark:text-zinc-400">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-1.5">
                <span className="mr-1">Self-score:</span>
                {[
                  {
                    val: 1,
                    label: "1.0",
                    activeCls:
                      "border-emerald-700 dark:border-emerald-400 text-emerald-700 dark:text-emerald-400 font-semibold bg-zinc-50 dark:bg-zinc-950",
                  },
                  {
                    val: 0.5,
                    label: "0.5",
                    activeCls:
                      "border-amber-700 dark:border-amber-400 text-amber-700 dark:text-amber-400 font-semibold bg-zinc-50 dark:bg-zinc-950",
                  },
                  {
                    val: 0,
                    label: "0",
                    activeCls:
                      "border-rose-600 dark:border-rose-400 text-rose-600 dark:text-rose-400 font-semibold bg-zinc-50 dark:bg-zinc-950",
                  },
                ].map((btn) => (
                  <button
                    key={btn.val}
                    type="button"
                    onClick={() => onSetScore(btn.val)}
                    aria-pressed={score === btn.val}
                    className={`h-7 px-2.5 rounded-lg font-mono border transition-colors ${
                      score === btn.val
                        ? btn.activeCls
                        : "bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600"
                    }`}
                  >
                    {btn.label}
                  </button>
                ))}
              </div>

              {mistakeTags.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="mr-1">Mistake:</span>
                  {mistakeTags.map((t) => {
                    const hasTag = problem.state.mistakes.includes(t.id);
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => onToggleMistakeTag(t.id)}
                        aria-pressed={hasTag}
                        className={`min-h-[28px] py-1 px-2.5 rounded-full text-xs border transition-colors inline-flex items-center ${
                          hasTag
                            ? "border-rose-600 dark:border-rose-400 text-rose-700 dark:text-rose-300 bg-zinc-50 dark:bg-zinc-950 font-semibold"
                            : "bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600"
                        }`}
                      >
                        <FormattedText text={t.label} />
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-3 py-2">
              <PenLine className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400 shrink-0" />
              <input
                type="text"
                value={problem.state.mistakeNote || ""}
                onChange={(e) => onMistakeNoteChange(e.target.value)}
                aria-label={`Note for question ${index + 1}`}
                placeholder="Note what went wrong (optional)…"
                className="w-full bg-transparent text-xs text-zinc-800 dark:text-zinc-200 placeholder:text-zinc-500 dark:placeholder:text-zinc-400 focus:outline-none"
              />
            </div>
          </div>
        )}
      </article>

      {/* Quiet question navigation footer */}
      {(onPrevQuestion || onNextQuestion || onOpenReview) && (
        <div className="flex items-center justify-between px-1 text-xs text-zinc-500 dark:text-zinc-400">
          <button
            type="button"
            onClick={onPrevQuestion}
            disabled={index === 0}
            className="inline-flex items-center gap-1 py-1.5 hover:text-zinc-900 dark:hover:text-zinc-100 disabled:opacity-30 disabled:pointer-events-none transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          {isLastQuestion && onOpenReview ? (
            <button
              type="button"
              onClick={onOpenReview}
              className="inline-flex items-center gap-1 py-1.5 font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              <span>Review &amp; sync</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={onNextQuestion}
              disabled={isLastQuestion}
              className="inline-flex items-center gap-1 py-1.5 hover:text-zinc-900 dark:hover:text-zinc-100 disabled:opacity-30 disabled:pointer-events-none transition-colors"
            >
              <span>Next</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}
    </div>
  );
};
