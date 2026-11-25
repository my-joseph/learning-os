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
import { Badge } from "@/components/ui/shadcn/Badge";
import { Card } from "@/components/ui/shadcn/Card";
import { Button } from "@/components/ui/shadcn/Button";
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
    return <Check className="size-space-4" aria-hidden="true" />;
  }
  if (tone === "almost") {
    return <Minus className="size-space-4" aria-hidden="true" />;
  }
  if (tone === "inputError") {
    return <AlertCircle className="size-space-4" aria-hidden="true" />;
  }
  if (tone === "skipped") {
    return <SkipForward className="size-space-3_5" aria-hidden="true" />;
  }
  return <X className="size-space-4" aria-hidden="true" />;
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
          <Card key={model.resultKey} variant="feedback" asChild className={CARD_STYLES[model.tone]}>
            <m.div variants={dialogCard} {...presence} role="status">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-space-3">
                <div className="flex items-start gap-space-3 min-w-0 flex-1">
                  <span
                    className={`size-control-xs rounded-full inline-flex items-center justify-center shrink-0 ${ICON_CIRCLE_STYLES[model.tone]}`}
                  >
                    <ToneIcon tone={model.tone} />
                  </span>

                  <div className="min-w-0 flex-1 space-y-space-1">
                    <div className="min-h-control-xs flex flex-wrap items-center gap-x-space-2_5 gap-y-space-0_5">
                      <span className="text-sm font-semibold text-foreground">
                        {displayTitle}
                        {scheduleNote && (
                          <span className="font-normal text-foreground-subtle">
                            {" "}· {scheduleNote}
                          </span>
                        )}
                      </span>
                      {model.attemptNumber !== null && !isReviewSession && (
                        <span className="text-xs font-display tabular-nums text-muted">
                          Attempt {model.attemptNumber}
                        </span>
                      )}
                    </div>

                    {model.body && (
                      <div className="text-sm text-foreground-answer-detail leading-snug">
                        <FormattedText text={model.body} />
                      </div>
                    )}

                    {/* Part-by-part breakdown only when it adds information (2+ parts, e.g. real/imaginary). */}
                    {model.components.length > 1 && (
                      <div className="flex flex-wrap gap-space-1_5 pt-space-0_5">
                        {model.components.map((c, i) => (
                          <Badge
                            key={i}
                            variant="answerPart"
                            className={c.ok ? statusTone.correct.text : statusTone.wrong.text}
                          >
                            {c.ok ? (
                              <Check className="size-space-3" aria-hidden="true" />
                            ) : (
                              <X className="size-space-3" aria-hidden="true" />
                            )}
                            <FormattedText text={c.label} />
                            <span className="sr-only">{c.ok ? " correct" : " not correct"}</span>
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {actionKind === "back" && onBack && (
                  <div className="flex sm:justify-end pl-space-10 sm:pl-space-0 shrink-0">
                    <Button
                      variant="resultPrimary"
                      size="resultAction"
                      ref={primaryBtnRef}
                      type="button"
                      onClick={onBack}
                      data-review-primary-action={isReviewSession ? "true" : undefined}
                    >
                      <span>{backLabel || "Back to question"}</span>
                      <ChevronRight className="size-space-3_5" aria-hidden="true" />
                    </Button>
                  </div>
                )}

                {actionKind === "next" && onNextQuestion && (
                  <div className="flex sm:justify-end pl-space-10 sm:pl-space-0 shrink-0">
                    <Button
                      variant="resultOutline"
                      size="resultAction"
                      ref={primaryBtnRef}
                      type="button"
                      onClick={onNextQuestion}
                      data-review-primary-action={isReviewSession ? "true" : undefined}
                    >
                      <span>{nextLabel}</span>
                      <ArrowRight className="size-space-3_5" aria-hidden="true" />
                    </Button>
                  </div>
                )}

                {actionKind === "review" && onOpenReview && (
                  <div className="flex sm:justify-end pl-space-10 sm:pl-space-0 shrink-0">
                    <Button
                      variant="resultOutline"
                      size="resultAction"
                      ref={primaryBtnRef}
                      type="button"
                      onClick={onOpenReview}
                      data-review-primary-action={isReviewSession ? "true" : undefined}
                    >
                      <span>Review</span>
                      <ArrowRight className="size-space-3_5" aria-hidden="true" />
                    </Button>
                  </div>
                )}

                {actionKind === "retry" && onTryAgain && (
                  <div className="flex sm:justify-end pl-space-10 sm:pl-space-0 shrink-0">
                    <Button
                      variant="resultOutline"
                      size="resultAction"
                      ref={primaryBtnRef}
                      type="button"
                      onClick={onTryAgain}
                      aria-label={retryAriaLabel || undefined}
                      data-review-primary-action={isReviewSession ? "true" : undefined}
                    >
                      <span>{retryLabel}</span>
                    </Button>
                  </div>
                )}

                {actionKind === "show_steps" && onShowSteps && (
                  <div className="flex sm:justify-end pl-space-10 sm:pl-space-0 shrink-0">
                    <Button
                      variant="resultOutline"
                      size="resultAction"
                      ref={primaryBtnRef}
                      type="button"
                      onClick={onShowSteps}
                      data-review-primary-action={isReviewSession ? "true" : undefined}
                    >
                      <span>Show steps</span>
                    </Button>
                  </div>
                )}
              </div>

              {visibleSecondary.length > 0 && (
                <div className="pl-space-10 flex flex-wrap items-center gap-x-space-4 gap-y-space-1">
                  {visibleSecondary.map((act) => (
                    <Button
                      variant="resultLink"
                      size="resultLink"
                      key={act.label}
                      type="button"
                      onClick={act.onClick}
                      disabled={act.disabled || act.loading}
                    >
                      {act.loading && (
                        <Loader2 className="size-space-3_5 animate-spin" aria-hidden="true" />
                      )}
                      <span>{act.label}</span>
                      {act.trailingChevron && !act.loading && (
                        <ChevronRight className="size-space-3_5" aria-hidden="true" />
                      )}
                    </Button>
                  ))}
                </div>
              )}

              {footnote && (
                <p className="pl-space-10 text-xs text-muted leading-relaxed">
                  {footnote}
                </p>
              )}
            </m.div>
          </Card>
        )}
      </AnimatePresence>
    </Reveal>
  );
};
