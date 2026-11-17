"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  PenLine,
} from "lucide-react";
import { Problem, MistakeTag, CheckResult } from "@/types/drill";
import { MathBlock } from "@/components/MathRender";
import { FormattedText } from "@/components/FormattedText";
import { StepRow } from "@/components/StepRow";
import { MathFigure } from "@/components/MathFigure";
import { LineChoicePrompt, parseLineChoicePrompt } from "@/components/LineChoicePrompt";
import { hasCheckpointHint } from "@/lib/studioRules";

export interface MathWorkspaceProps {
  problem: Problem;
  index: number;
  totalQuestions?: number;
  drillTitle?: string;
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  onInputChange: (val: string) => void;
  onCheckAnswer: () => Promise<void> | void;
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
  // Equation set-up (display + plain-text) is hidden until the learner asks for it or finishes the problem.
  const [showSetup, setShowSetup] = useState(() => shouldAutoReveal(problem));
  const hasSetup = Boolean(problem.hasSetup || problem.display || problem.plainText);
  const answered = Boolean(problem.state.lastCheck);
  const hasAttempt = Boolean(
    problem.state.lastCheck ||
      problem.state.skipped ||
      (problem.state.attempts && problem.state.attempts.length > 0) ||
      problem.state.score !== null
  );
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
  const lineChoiceData = useMemo(
    () =>
      problem.answerSpec.type === "choice"
        ? parseLineChoicePrompt(problem.prompt, problem.answerSpec.options)
        : null,
    [problem.answerSpec.type, problem.prompt, problem.answerSpec.options]
  );

  const isLastQuestion =
    typeof totalQuestions === "number" && totalQuestions > 0 && index === totalQuestions - 1;

  return (
    <div className="mx-auto w-full max-w-[720px] space-y-4">
      {drillTitle && (
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight px-0.5">
          {drillTitle}
        </h1>
      )}

      <article className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-6">
        {/* 1. Question number + prompt (text-lg, leading-relaxed) */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
            Question {index + 1}
            {typeof totalQuestions === "number" && totalQuestions > 0
              ? ` of ${totalQuestions}`
              : ""}
          </div>

          <div className="text-lg leading-relaxed text-zinc-900 dark:text-zinc-100">
            {lineChoiceData ? (
              <LineChoicePrompt
                parsed={lineChoiceData}
                selectedValue={problem.state.userInput}
                onSelect={onInputChange}
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

        {/* 3. Answer input + one primary "Check" button */}
        <div className="space-y-3">
          {problem.answerSpec.type === "choice" && !lineChoiceData && (
            <div className="flex flex-wrap gap-2 w-full">
              {problem.answerSpec.options?.map((opt) => {
                const isSelected = problem.state.userInput === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => onInputChange(opt.id)}
                    className={`min-h-[40px] px-3.5 py-2 rounded-xl border text-sm font-medium transition-colors flex items-center gap-2 ${
                      isSelected
                        ? "bg-zinc-100 dark:bg-zinc-800 border-indigo-600 dark:border-indigo-500 text-zinc-900 dark:text-zinc-100"
                        : "bg-zinc-50 dark:bg-zinc-950 text-zinc-800 dark:text-zinc-200 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600"
                    }`}
                  >
                    <span
                      className={`inline-flex items-center justify-center w-5 h-5 rounded text-xs font-mono font-semibold ${
                        isSelected
                          ? "bg-indigo-600 dark:bg-indigo-500 text-white"
                          : "bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-800"
                      }`}
                    >
                      {opt.id}
                    </span>
                    <FormattedText text={opt.label} />
                  </button>
                );
              })}
            </div>
          )}

          <div className="flex items-center gap-2.5">
            {problem.answerSpec.type !== "choice" && (
              <input
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
                className="flex-1 min-w-0 h-11 font-mono text-base bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 border border-zinc-300 dark:border-zinc-700 rounded-xl px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-600/25 dark:focus:ring-indigo-500/30 focus:border-indigo-600 dark:focus:border-indigo-500 placeholder:text-zinc-400 dark:placeholder:text-zinc-500"
              />
            )}

            <button
              type="button"
              onClick={triggerCheck}
              disabled={isChecking || !problem.state.userInput.trim()}
              className="inline-flex items-center justify-center gap-2 h-11 px-5 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-400 disabled:opacity-40 text-white text-sm font-semibold transition-colors shrink-0"
            >
              {isChecking ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Checking…</span>
                </>
              ) : (
                <span>Check</span>
              )}
            </button>
          </div>

          {/* 4. Feedback directly below the input (thin left border + calm copy, never a red card) */}
          {lastCheck && (
            <div
              role="status"
              className={`border-l-2 pl-3.5 py-1 space-y-1.5 text-sm ${
                lastCheck.verdict === "correct"
                  ? "border-emerald-700 dark:border-emerald-400"
                  : lastCheck.verdict === "equivalent_not_in_form" ||
                    lastCheck.verdict === "partial" ||
                    lastCheck.verdict === "skipped"
                  ? "border-amber-600 dark:border-amber-400"
                  : "border-rose-600 dark:border-rose-400"
              }`}
            >
              <div className="flex items-start gap-2">
                {lastCheck.verdict === "correct" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-700 dark:text-emerald-400 shrink-0 mt-0.5" />
                ) : lastCheck.verdict === "equivalent_not_in_form" ||
                  lastCheck.verdict === "partial" ||
                  lastCheck.verdict === "skipped" ? (
                  <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
                )}
                <span className="font-medium text-zinc-900 dark:text-zinc-100">
                  <FormattedText text={lastCheck.message} />
                </span>
              </div>

              {lastCheck.components?.length > 0 && (
                <div className="flex flex-wrap gap-3 pl-6">
                  {lastCheck.components.map((c, i) => (
                    <span
                      key={i}
                      className={`text-xs font-mono ${
                        c.ok
                          ? "text-emerald-700 dark:text-emerald-400"
                          : "text-rose-600 dark:text-rose-400"
                      }`}
                    >
                      <FormattedText text={c.label} />: {c.ok ? "✓" : "✗"}
                    </span>
                  ))}
                </div>
              )}

              {lastCheck.diagnostics?.length > 0 && (
                <div className="pl-6 text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
                  {lastCheck.diagnostics.map((d, i) => (
                    <div key={i}>
                      <FormattedText text={d.message} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 5. Quiet secondary actions: Try again / equation set-up / hint / steps / skip */}
        <div className="space-y-3 pt-1">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-zinc-500 dark:text-zinc-400">
            {hasAttempt && (
              <button
                type="button"
                onClick={onResetProblem}
                className="inline-flex items-center gap-1.5 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Try again</span>
              </button>
            )}

            {hasSetup && (
              <button
                type="button"
                onClick={toggleSetup}
                aria-expanded={showSetup}
                className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
              >
                {showSetup ? (
                  <ChevronUp className="w-3.5 h-3.5" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5" />
                )}
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
              className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              {showSolution ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
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

          {/* Checkpoint Hint Disclosure */}
          {showHint && hasCheckpointHint(problem.checkpointHint) && (
            <div className="border-l-2 border-amber-600 dark:border-amber-400 pl-3.5 py-1 text-sm text-zinc-700 dark:text-zinc-300">
              <FormattedText text={problem.checkpointHint} />
            </div>
          )}

          {/* Equation Set-up Disclosure */}
          {hasSetup && showSetup && (
            <div className="bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-2.5">
              {problem.display && (
                <div className="overflow-x-auto text-zinc-900 dark:text-zinc-100">
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

          {/* Step-by-Step Derivation Disclosure */}
          {showSolution && (
            <div
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
                      "border-amber-600 dark:border-amber-400 text-amber-600 dark:text-amber-400 font-semibold bg-zinc-50 dark:bg-zinc-950",
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
              <PenLine className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
              <input
                type="text"
                value={problem.state.mistakeNote || ""}
                onChange={(e) => onMistakeNoteChange(e.target.value)}
                placeholder="Note what went wrong (optional)…"
                className="w-full bg-transparent text-xs text-zinc-800 dark:text-zinc-200 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none"
              />
            </div>
          </div>
        )}
      </article>

      {/* Quiet question navigation footer */}
      {(onPrevQuestion || onNextQuestion || onOpenReview) && (
        <div className="flex items-center justify-between px-1 text-sm text-zinc-500 dark:text-zinc-400">
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
              <span>Review &amp; Sync</span>
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
