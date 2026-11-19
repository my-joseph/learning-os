"use client";

import React, { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { FormattedText } from "@/components/FormattedText";
import { MathFigure } from "@/components/MathFigure";
import { StepRow } from "@/components/StepRow";
import { Reveal } from "@/components/motion/Reveal";
import { WorkedExampleVariant } from "@/types/drill";

export interface WorkedExampleViewProps {
  questionNumber: number;
  example: WorkedExampleVariant;
  onBackToQuestion: () => void;
  /** Optional initial number of revealed steps (defaults to 0 so prompt + figure appear first). */
  initialRevealedCount?: number;
}

/**
 * Swap-in-place worked example view rendered inside the question card (`mode === "example"`):
 * breadcrumb back to Question N, honest "A similar question, not yours" label, prompt + figure,
 * progressive step-by-step reveal (`Show next step` / Enter, `Show all steps`), and final
 * `Answer` + `Try Question N again` action.
 */
export const WorkedExampleView: React.FC<WorkedExampleViewProps> = ({
  questionNumber,
  example,
  onBackToQuestion,
  initialRevealedCount = 0,
}) => {
  const steps = example.steps || [];
  const [revealedCount, setRevealedCount] = useState(() =>
    Math.max(0, Math.min(initialRevealedCount, steps.length))
  );
  const nextStepBtnRef = useRef<HTMLButtonElement | null>(null);
  const tryAgainBtnRef = useRef<HTMLButtonElement | null>(null);

  const allRevealed = revealedCount >= steps.length;

  useEffect(() => {
    setRevealedCount(Math.max(0, Math.min(initialRevealedCount, steps.length)));
  }, [example.token, initialRevealedCount, steps.length]);

  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      if (allRevealed) {
        tryAgainBtnRef.current?.focus({ preventScroll: true });
        tryAgainBtnRef.current?.scrollIntoView({ block: "nearest" });
      } else {
        nextStepBtnRef.current?.focus({ preventScroll: true });
        nextStepBtnRef.current?.scrollIntoView({ block: "nearest" });
      }
    });
    return () => cancelAnimationFrame(raf);
  }, [example.token, allRevealed]);

  // Allow Enter key to reveal the next step while stepping through the worked example
  useEffect(() => {
    if (allRevealed) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Enter" || e.metaKey || e.ctrlKey || e.altKey || e.shiftKey) return;
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "BUTTON" ||
          target.tagName === "A" ||
          target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          Boolean(target.closest('[role="alertdialog"], [role="dialog"]')))
      ) {
        return;
      }
      e.preventDefault();
      setRevealedCount((prev) => Math.min(steps.length, prev + 1));
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [allRevealed, steps.length]);

  return (
    <div className="space-y-6" aria-label="Worked example — a similar question, not yours">
      {/* Breadcrumb header + honest label */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
          <button
            type="button"
            onClick={onBackToQuestion}
            className="inline-flex items-center gap-1 min-h-[44px] sm:min-h-0 -ml-1.5 px-1.5 rounded-lg text-zinc-700 dark:text-zinc-300 hover:text-zinc-950 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
          >
            <ChevronLeft className="w-4 h-4 shrink-0" aria-hidden="true" />
            <span>Question {questionNumber}</span>
          </button>
          <span aria-hidden="true">·</span>
          <span className="text-zinc-900 dark:text-zinc-100">Worked example</span>
        </div>

        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          A similar question, not yours
        </p>

        <div className="text-base leading-relaxed text-zinc-900 dark:text-zinc-100">
          <FormattedText text={example.prompt} />
        </div>
      </div>

      {(example.figure || example.visual) && (
        <div className="w-full">
          <MathFigure figure={example.figure || example.visual!} className="w-full" />
        </div>
      )}

      {/* Progressive steps */}
      <div className="space-y-4">
        {revealedCount > 0 && (
          <div className="bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-2">
            {steps.slice(0, revealedCount).map((st, sIdx) => (
              <StepRow
                key={sIdx}
                step={st}
                index={sIdx}
              />
            ))}
          </div>
        )}

        {!allRevealed ? (
          <div className="flex flex-wrap items-center gap-3">
            <button
              ref={nextStepBtnRef}
              type="button"
              onClick={() =>
                setRevealedCount((prev) => Math.min(steps.length, prev + 1))
              }
              className="inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:min-h-0 h-11 sm:h-9 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 focus-visible:ring-offset-1"
            >
              <span>Show next step</span>
              <span className="font-display text-indigo-100/80 tabular-nums">
                Step {Math.min(revealedCount + 1, steps.length)} of {steps.length}
              </span>
            </button>
            <button
              type="button"
              onClick={() => setRevealedCount(steps.length)}
              className="inline-flex items-center min-h-[44px] sm:min-h-0 py-1 px-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
            >
              Show all steps
            </button>
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2 border-t border-zinc-200 dark:border-zinc-800">
            {(example.answerDisplay || example.answerPlain) && (
              <div className="text-sm text-zinc-600 dark:text-zinc-400">
                <span>Answer </span>
                <strong className="text-zinc-900 dark:text-zinc-100 font-semibold">
                  <FormattedText
                    text={
                      example.answerDisplay
                        ? `$${example.answerDisplay}$`
                        : example.answerPlain
                    }
                  />
                </strong>
              </div>
            )}
            <button
              ref={tryAgainBtnRef}
              type="button"
              onClick={onBackToQuestion}
              className="inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:min-h-0 h-11 sm:h-9 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 focus-visible:ring-offset-1"
            >
              <span>Try Question {questionNumber} again</span>
              <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export interface WorkedExampleDisclosureProps {
  example: WorkedExampleVariant;
  defaultOpen?: boolean;
}

/**
 * Collapsed disclosure kept under Question N's result card after viewing the worked example
 * so the learner can glance at it while retrying their own question.
 */
export const WorkedExampleDisclosure: React.FC<WorkedExampleDisclosureProps> = ({
  example,
  defaultOpen = false,
}) => {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 min-h-[44px] sm:min-h-0 py-1 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
      >
        <ChevronRight
          className={`w-3.5 h-3.5 transition-transform duration-200 ${
            open ? "rotate-90" : ""
          }`}
          aria-hidden="true"
        />
        <span>Worked example</span>
      </button>

      <Reveal show={open}>
        {open && (
          <div className="bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-500 dark:text-zinc-400">
              <span>A similar question, not yours</span>
              {(example.answerDisplay || example.answerPlain) && (
                <span>
                  Answer:{" "}
                  <strong className="text-zinc-900 dark:text-zinc-100 font-semibold">
                    <FormattedText
                      text={
                        example.answerDisplay
                          ? `$${example.answerDisplay}$`
                          : example.answerPlain
                      }
                    />
                  </strong>
                </span>
              )}
            </div>

            <div className="text-sm leading-relaxed text-zinc-900 dark:text-zinc-100">
              <FormattedText text={example.prompt} />
            </div>

            {(example.figure || example.visual) && (
              <div className="w-full">
                <MathFigure figure={example.figure || example.visual!} className="w-full" />
              </div>
            )}

            <div>
              {(example.steps || []).map((st, sIdx) => (
                <StepRow
                  key={sIdx}
                  step={st}
                  index={sIdx}
                />
              ))}
            </div>
          </div>
        )}
      </Reveal>
    </div>
  );
};
