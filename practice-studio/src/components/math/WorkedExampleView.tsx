"use client";

import React, { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { FormattedText } from "@/components/FormattedText";
import { MathFigure } from "@/components/MathFigure";
import { StepRow } from "@/components/StepRow";
import { Reveal } from "@/components/motion/Reveal";
import { Button } from "@/components/ui/shadcn/Button";
import { Card } from "@/components/ui/shadcn/Card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/shadcn/Collapsible";
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
    <div className="space-y-space-6" aria-label="Worked example — a similar question, not yours">
      {/* Breadcrumb header + honest label */}
      <div className="space-y-space-2">
        <div className="flex flex-wrap items-center gap-x-space-2 gap-y-space-1 text-xs font-normal text-muted">
          <Button
            onClick={onBackToQuestion}
            variant="exampleBack"
            size="exampleBack"
            className="-ml-space-1_5"
          >
            <ChevronLeft className="size-space-4 shrink-0" aria-hidden="true" />
            <span>Question {questionNumber}</span>
          </Button>
          <span aria-hidden="true">·</span>
          <span className="text-foreground">Worked example</span>
        </div>

        <p className="text-xs text-muted">
          A similar question, not yours
        </p>

        <div className="text-base leading-relaxed text-foreground">
          <FormattedText text={example.prompt} />
        </div>
      </div>

      {(example.figure || example.visual) && (
        <div className="w-full">
          <MathFigure figure={example.figure || example.visual!} className="w-full" />
        </div>
      )}

      {/* Progressive steps */}
      <div className="space-y-space-4">
        {revealedCount > 0 && (
          <Card variant="assistPanel" className="space-y-space-2">
            {steps.slice(0, revealedCount).map((st, sIdx) => (
              <StepRow
                key={sIdx}
                step={st}
                index={sIdx}
              />
            ))}
          </Card>
        )}

        {!allRevealed ? (
          <div className="flex flex-wrap items-center gap-space-3">
            <Button
              ref={nextStepBtnRef}
              onClick={() =>
                setRevealedCount((prev) => Math.min(steps.length, prev + 1))
              }
              variant="examplePrimary"
              size="examplePrimary"
            >
              <span>Show next step</span>
              <span className="font-sans tabular-nums text-accent-on-primary-muted/80">
                Step {Math.min(revealedCount + 1, steps.length)} of {steps.length}
              </span>
            </Button>
            <Button
              onClick={() => setRevealedCount(steps.length)}
              variant="exampleQuiet"
              size="exampleQuiet"
              className="px-space-2"
            >
              Show all steps
            </Button>
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-space-3 pt-space-2 border-t border-border">
            {(example.answerDisplay || example.answerPlain) && (
              <div className="text-sm text-foreground-subtle">
                <span>Answer </span>
                <strong className="text-foreground font-semibold">
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
            <Button
              ref={tryAgainBtnRef}
              onClick={onBackToQuestion}
              variant="examplePrimary"
              size="examplePrimary"
            >
              <span>Try Question {questionNumber} again</span>
              <ChevronRight className="size-space-3_5" aria-hidden="true" />
            </Button>
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
    <Collapsible open={open} onOpenChange={setOpen} className="space-y-space-2">
      <CollapsibleTrigger asChild>
        <Button
          variant="exampleQuiet"
          size="exampleQuiet"
          className="gap-space-1_5 rounded-md motion-reduce:transition-none"
        >
          <ChevronRight
            className={`size-space-3_5 transition-transform duration-panel motion-reduce:transition-none ${
              open ? "rotate-90" : ""
            }`}
            aria-hidden="true"
          />
          <span>Worked example</span>
        </Button>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <Reveal show={open}>
          {open && (
            <Card variant="assistPanel" className="space-y-space-4">
              <div className="flex flex-wrap items-center justify-between gap-space-2 text-xs text-muted">
                <span>A similar question, not yours</span>
                {(example.answerDisplay || example.answerPlain) && (
                  <span>
                    Answer:{" "}
                    <strong className="text-foreground font-semibold">
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

              <div className="text-sm leading-relaxed text-foreground">
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
            </Card>
          )}
        </Reveal>
      </CollapsibleContent>
    </Collapsible>
  );
};
