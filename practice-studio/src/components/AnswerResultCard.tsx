"use client";

import React from "react";
import { AnimatePresence, m } from "motion/react";
import { ArrowRight, Check, Minus, SkipForward, X } from "lucide-react";
import { FormattedText } from "@/components/FormattedText";
import { Reveal } from "@/components/motion/Reveal";
import {
  buildResultCardModel,
  CARD_STYLES,
  ICON_CIRCLE_STYLES,
  ResultCardTone,
} from "@/lib/answerFeedback";
import { dialogCard, presence } from "@/lib/motion";
import { CheckResult, MistakeTag, Problem, ProblemState } from "@/types/drill";

export interface AnswerResultCardProps {
  lastCheck: CheckResult | null | undefined;
  state: ProblemState;
  problem?: Pick<Problem, "commonTrapTag" | "answerSpec">;
  mistakeTags?: MistakeTag[];
  isLastQuestion?: boolean;
  nextLabel?: string;
  onNextQuestion?: () => void;
  onOpenReview?: () => void;
  onTryAgain?: () => void;
  onShowSteps?: () => void;
}

function ToneIcon({ tone }: { tone: ResultCardTone }) {
  if (tone === "correct") {
    return <Check className="w-4 h-4" aria-hidden="true" />;
  }
  if (tone === "almost") {
    return <Minus className="w-4 h-4" aria-hidden="true" />;
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
  nextLabel = "Next question",
  onNextQuestion,
  onOpenReview,
  onTryAgain,
  onShowSteps,
}) => {
  const model = lastCheck
    ? buildResultCardModel({
        lastCheck,
        state,
        problem,
        mistakeTags,
        isLastQuestion,
      })
    : null;

  const actionButtonClass =
    "inline-flex items-center justify-center gap-1.5 h-8 px-3 rounded-lg text-xs font-medium bg-white/90 dark:bg-zinc-900/80 border border-zinc-200/90 dark:border-zinc-700 text-zinc-800 dark:text-zinc-200 hover:bg-white dark:hover:bg-zinc-900 hover:border-zinc-300 dark:hover:border-zinc-600 transition-colors shrink-0";

  return (
    <Reveal show={Boolean(model)}>
      <AnimatePresence mode="wait" initial={false}>
        {model && (
          <m.div
            key={model.resultKey}
            variants={dialogCard}
            {...presence}
            role="status"
            className={`rounded-xl p-3.5 sm:p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 ${CARD_STYLES[model.tone]}`}
          >
            <div className="flex items-start gap-3 min-w-0 flex-1">
              <span
                className={`w-7 h-7 rounded-full inline-flex items-center justify-center shrink-0 ${ICON_CIRCLE_STYLES[model.tone]}`}
              >
                <ToneIcon tone={model.tone} />
              </span>

              <div className="min-w-0 flex-1 space-y-1">
                <div className="min-h-7 flex flex-wrap items-center gap-x-2.5 gap-y-0.5">
                  <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    {model.title}
                  </span>
                  {model.attemptNumber !== null && (
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
                          c.ok
                            ? "text-emerald-700 dark:text-emerald-400"
                            : "text-rose-700 dark:text-rose-400"
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

            {model.actionKind === "next" && onNextQuestion && (
              <div className="flex sm:justify-end pl-10 sm:pl-0 shrink-0">
                <button
                  type="button"
                  onClick={onNextQuestion}
                  className={actionButtonClass}
                >
                  <span>{nextLabel}</span>
                  <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                </button>
              </div>
            )}

            {model.actionKind === "review" && onOpenReview && (
              <div className="flex sm:justify-end pl-10 sm:pl-0 shrink-0">
                <button
                  type="button"
                  onClick={onOpenReview}
                  className={actionButtonClass}
                >
                  <span>Review</span>
                  <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                </button>
              </div>
            )}

            {model.actionKind === "retry" && onTryAgain && (
              <div className="flex sm:justify-end pl-10 sm:pl-0 shrink-0">
                <button
                  type="button"
                  onClick={onTryAgain}
                  className={actionButtonClass}
                >
                  <span>Try again</span>
                </button>
              </div>
            )}

            {model.actionKind === "show_steps" && onShowSteps && (
              <div className="flex sm:justify-end pl-10 sm:pl-0 shrink-0">
                <button
                  type="button"
                  onClick={onShowSteps}
                  className={actionButtonClass}
                >
                  <span>Show steps</span>
                </button>
              </div>
            )}
          </m.div>
        )}
      </AnimatePresence>
    </Reveal>
  );
};
