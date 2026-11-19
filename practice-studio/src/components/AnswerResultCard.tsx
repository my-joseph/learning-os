"use client";

import React, { useEffect, useRef } from "react";
import { AnimatePresence, m } from "motion/react";
import { AlertCircle, ArrowRight, Check, ChevronRight, Loader2, Minus, SkipForward, X } from "lucide-react";
import { FormattedText } from "@/components/FormattedText";
import { Reveal } from "@/components/motion/Reveal";
import {
  buildResultCardModel,
  CARD_STYLES,
  ICON_CIRCLE_STYLES,
  ResultCardTone,
} from "@/lib/answerFeedback";
import { statusTone } from "@/lib/statusTone";
import { dialogCard, presence } from "@/lib/motion";
import { CheckResult, MistakeTag, Problem, ProblemState } from "@/types/drill";

export interface ResultCardSecondaryAction {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  /** Render a quiet trailing chevron icon (used for navigation/swap actions). */
  trailingChevron?: boolean;
  autoFocus?: boolean;
}

export interface AnswerResultCardProps {
  lastCheck: CheckResult | null | undefined;
  state: ProblemState;
  problem?: Pick<Problem, "commonTrapTag" | "answerSpec">;
  mistakeTags?: MistakeTag[];
  isLastQuestion?: boolean;
  isReviewSession?: boolean;
  isVariant?: boolean;
  isCorrectOnRetry?: boolean;
  nextLabel?: string;
  scheduleNote?: string | null;
  backLabel?: string;
  retryLabel?: string;
  retryAriaLabel?: string;
  footnote?: string | null;
  titleOverride?: string;
  autoFocusPrimaryAction?: boolean;
  secondaryActions?: ResultCardSecondaryAction[];
  onNextQuestion?: () => void;
  onOpenReview?: () => void;
  onTryAgain?: () => void;
  onShowSteps?: () => void;
  onBack?: () => void;
}

function ToneIcon({ tone }: { tone: ResultCardTone }) {
  if (tone === "correct" || tone === "assisted") {
    return <Check className="w-4 h-4" aria-hidden="true" />;
  }
  if (tone === "almost") {
    return <Minus className="w-4 h-4" aria-hidden="true" />;
  }
  if (tone === "inputError") {
    return <AlertCircle className="w-4 h-4" aria-hidden="true" />;
  }
  if (tone === "skipped") {
    return <SkipForward className="w-3.5 h-3.5" aria-hidden="true" />;
  }
  return <X className="w-4 h-4" aria-hidden="true" />;
}

/** Calm rounded-xl answer result card directly under the answer area. */
export const AnswerResultCard: React.FC<AnswerResultCardProps> = ({
  lastCheck,
  state,
  problem,
  mistakeTags = [],
  isLastQuestion = false,
  isReviewSession = false,
  isVariant = false,
  isCorrectOnRetry = false,
  nextLabel = "Next question",
  scheduleNote = null,
  backLabel,
  retryLabel = "Try again",
  retryAriaLabel,
  footnote = null,
  titleOverride,
  autoFocusPrimaryAction = false,
  secondaryActions = [],
  onNextQuestion,
  onOpenReview,
  onTryAgain,
  onShowSteps,
  onBack,
}) => {
  const model = lastCheck
    ? buildResultCardModel({
        lastCheck,
        state,
        problem,
        mistakeTags,
        isLastQuestion,
        preferBackAction: Boolean(onBack),
        isVariant,
      })
    : null;
  const actionKind = isReviewSession && model?.tone === "skipped" ? "next" : model?.actionKind;

  const primaryBtnRef = useRef<HTMLButtonElement | null>(null);
  const cleanupFrame = useRef<number | null>(null);
  const resultKey = model?.resultKey ?? "";
  const shouldAutoFocusPrimary =
    Boolean(model) && (autoFocusPrimaryAction || model?.actionKind === "back");

  useEffect(() => {
    if (!shouldAutoFocusPrimary || !resultKey) return;
    const firstFrame = requestAnimationFrame(() => {
      const secondFrame = requestAnimationFrame(() => {
        primaryBtnRef.current?.focus({ preventScroll: true });
      });
      cleanupFrame.current = secondFrame;
    });
    return () => {
      cancelAnimationFrame(firstFrame);
      if (cleanupFrame.current !== null) cancelAnimationFrame(cleanupFrame.current);
    };
  }, [shouldAutoFocusPrimary, resultKey]);

  const actionButtonClass =
    "inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:min-h-0 h-11 sm:h-8 px-3.5 sm:px-3 rounded-lg text-xs font-medium bg-white/90 dark:bg-zinc-900/80 border border-zinc-200/90 dark:border-zinc-700 text-zinc-800 dark:text-zinc-200 hover:bg-white dark:hover:bg-zinc-900 hover:border-zinc-300 dark:hover:border-zinc-600 transition-colors shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400";

  const backButtonClass =
    "inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:min-h-0 h-11 sm:h-8 px-4 sm:px-3.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white transition-colors shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 focus-visible:ring-offset-1";

  const secondaryLinkClass =
    "inline-flex items-center gap-1 min-h-[44px] sm:min-h-0 py-1 sm:py-0.5 text-xs font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-950 dark:hover:text-zinc-100 disabled:opacity-50 transition-colors rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400";

  const displayTitle =
    titleOverride ||
    (isReviewSession && (model?.tone === "correct" || model?.tone === "assisted") && isCorrectOnRetry
      ? "Correct on retry"
      : model?.title || "");
  const visibleSecondary = secondaryActions.filter(Boolean);

  return (
    <Reveal show={Boolean(model)}>
      <AnimatePresence mode="wait" initial={false}>
        {model && (
          <m.div
            key={model.resultKey}
            variants={dialogCard}
            {...presence}
            role="status"
            className={`rounded-xl p-3.5 sm:p-4 space-y-2.5 ${CARD_STYLES[model.tone]}`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-start gap-3 min-w-0 flex-1">
                <span
                  className={`w-7 h-7 rounded-full inline-flex items-center justify-center shrink-0 ${ICON_CIRCLE_STYLES[model.tone]}`}
                >
                  <ToneIcon tone={model.tone} />
                </span>

                <div className="min-w-0 flex-1 space-y-1">
                  <div className="min-h-7 flex flex-wrap items-center gap-x-2.5 gap-y-0.5">
                    <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                      {displayTitle}
                      {scheduleNote && (
                        <span className="font-normal text-zinc-600 dark:text-zinc-400">
                          {" "}· {scheduleNote}
                        </span>
                      )}
                    </span>
                    {model.attemptNumber !== null && !isReviewSession && (
                      <span className="text-xs text-zinc-500 dark:text-zinc-400 tabular-nums">
                        Attempt {model.attemptNumber}
                      </span>
                    )}
                  </div>

                  {model.body && (
                    <div className="text-sm text-zinc-700 dark:text-zinc-300 leading-snug">
                      <FormattedText text={model.body} />
                    </div>
                  )}

                  {/* Part-by-part breakdown only when it adds information (2+ parts, e.g. real/imaginary). */}
                  {model.components.length > 1 && (
                    <div className="flex flex-wrap gap-1.5 pt-0.5">
                      {model.components.map((c, i) => (
                        <span
                          key={i}
                          className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs bg-white/70 dark:bg-zinc-900/50 ${
                            c.ok ? statusTone.correct.text : statusTone.wrong.text
                          }`}
                        >
                          {c.ok ? (
                            <Check className="w-3 h-3" aria-hidden="true" />
                          ) : (
                            <X className="w-3 h-3" aria-hidden="true" />
                          )}
                          <FormattedText text={c.label} />
                          <span className="sr-only">{c.ok ? " correct" : " not correct"}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {actionKind === "back" && onBack && (
                <div className="flex sm:justify-end pl-10 sm:pl-0 shrink-0">
                  <button
                    ref={primaryBtnRef}
                    type="button"
                    onClick={onBack}
                    data-review-primary-action={isReviewSession ? "true" : undefined}
                    className={backButtonClass}
                  >
                    <span>{backLabel || "Back to question"}</span>
                    <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
                  </button>
                </div>
              )}

              {actionKind === "next" && onNextQuestion && (
                <div className="flex sm:justify-end pl-10 sm:pl-0 shrink-0">
                  <button
                    ref={primaryBtnRef}
                    type="button"
                    onClick={onNextQuestion}
                    data-review-primary-action={isReviewSession ? "true" : undefined}
                    className={actionButtonClass}
                  >
                    <span>{nextLabel}</span>
                    <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                  </button>
                </div>
              )}

              {actionKind === "review" && onOpenReview && (
                <div className="flex sm:justify-end pl-10 sm:pl-0 shrink-0">
                  <button
                    ref={primaryBtnRef}
                    type="button"
                    onClick={onOpenReview}
                    data-review-primary-action={isReviewSession ? "true" : undefined}
                    className={actionButtonClass}
                  >
                    <span>Review</span>
                    <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                  </button>
                </div>
              )}

              {actionKind === "retry" && onTryAgain && (
                <div className="flex sm:justify-end pl-10 sm:pl-0 shrink-0">
                  <button
                    ref={primaryBtnRef}
                    type="button"
                    onClick={onTryAgain}
                    aria-label={retryAriaLabel || undefined}
                    data-review-primary-action={isReviewSession ? "true" : undefined}
                    className={actionButtonClass}
                  >
                    <span>{retryLabel}</span>
                  </button>
                </div>
              )}

              {actionKind === "show_steps" && onShowSteps && (
                <div className="flex sm:justify-end pl-10 sm:pl-0 shrink-0">
                  <button
                    ref={primaryBtnRef}
                    type="button"
                    onClick={onShowSteps}
                    data-review-primary-action={isReviewSession ? "true" : undefined}
                    className={actionButtonClass}
                  >
                    <span>Show steps</span>
                  </button>
                </div>
              )}
            </div>

            {visibleSecondary.length > 0 && (
              <div className="pl-10 flex flex-wrap items-center gap-x-4 gap-y-1">
                {visibleSecondary.map((act) => (
                  <button
                    key={act.label}
                    type="button"
                    onClick={act.onClick}
                    disabled={act.disabled || act.loading}
                    className={secondaryLinkClass}
                  >
                    {act.loading && (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
                    )}
                    <span>{act.label}</span>
                    {act.trailingChevron && !act.loading && (
                      <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
                    )}
                  </button>
                ))}
              </div>
            )}

            {footnote && (
              <p className="pl-10 text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                {footnote}
              </p>
            )}
          </m.div>
        )}
      </AnimatePresence>
    </Reveal>
  );
};
