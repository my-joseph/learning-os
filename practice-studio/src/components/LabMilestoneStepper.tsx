"use client";

import React, { useEffect, useRef } from "react";
import { m } from "motion/react";
import { ClipboardCheck } from "lucide-react";
import type { Problem } from "@/types/drill";
import {
  deriveLabMilestoneStates,
  type MilestoneStepperState,
} from "@/lib/codeStatus";
import { quick, settle } from "@/lib/motion";

export interface LabMilestoneStepperProps {
  problems: Problem[];
  currentIndex: number;
  viewMode: "quiz" | "review";
  onSelectQuestion: (index: number) => void;
  onToggleViewMode: (mode: "quiz" | "review") => void;
}

const STEPPER_STATUS_TEXT: Record<MilestoneStepperState, string> = {
  passed: "passed",
  regressed: "regressed",
  notYet: "not passed yet",
};

function getDotColorClass(state: MilestoneStepperState, isCurrent: boolean): string {
  if (state === "passed") {
    return "bg-indigo-600 dark:bg-indigo-500 border-2 border-indigo-600 dark:border-indigo-500";
  }
  if (state === "regressed") {
    return "bg-amber-600 dark:bg-amber-400 border-2 border-amber-600 dark:border-amber-400";
  }
  if (isCurrent) {
    return "bg-white dark:bg-zinc-900 border-2 border-zinc-400 dark:border-zinc-500";
  }
  return "bg-white dark:bg-zinc-900 border-2 border-zinc-300 dark:border-zinc-700 group-hover:border-zinc-400 dark:group-hover:border-zinc-500";
}

const CURRENT_RING_CLS =
  "ring-2 ring-indigo-600 dark:ring-indigo-500 ring-offset-2 ring-offset-white dark:ring-offset-zinc-900";

/** Horizontal milestone stepper for project labs: M1..Mn dots joined by progress lines, plus a trailing Review step. */
export const LabMilestoneStepper: React.FC<LabMilestoneStepperProps> = ({
  problems,
  currentIndex,
  viewMode,
  onSelectQuestion,
  onToggleViewMode,
}) => {
  const isReview = viewMode === "review";
  const states = deriveLabMilestoneStates(problems);
  const totalSteps = problems.length + 1;
  const needsHorizontalScroll = problems.length > 8;

  const stepBtnRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const reviewBtnRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!needsHorizontalScroll) return;
    if (isReview) {
      reviewBtnRef.current?.scrollIntoView({ inline: "nearest", block: "nearest" });
      return;
    }
    stepBtnRefs.current[currentIndex]?.scrollIntoView({
      inline: "nearest",
      block: "nearest",
    });
  }, [currentIndex, isReview, needsHorizontalScroll]);

  return (
    <div className="pt-2 border-t border-zinc-200/80 dark:border-zinc-800/80">
      <nav
        aria-label="Lab milestones"
        className={
          needsHorizontalScroll
            ? "overflow-x-auto py-0.5 px-2 -mx-2 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden"
            : "py-0.5"
        }
      >
        <div
          className="grid items-end"
          style={{
            gridTemplateColumns: needsHorizontalScroll
              ? `repeat(${totalSteps}, minmax(52px, 1fr))`
              : `repeat(${totalSteps}, minmax(0, 1fr))`,
          }}
        >
          {problems.map((prob, idx) => {
            const stepState = states[idx] ?? "notYet";
            const isActive = viewMode === "quiz" && currentIndex === idx;
            const statusText = STEPPER_STATUS_TEXT[stepState];
            const ariaLabel = `${prob.id} — ${statusText}`;
            const titleText = prob.category
              ? `${prob.id}: ${prob.category} — ${statusText}`
              : ariaLabel;
            const isSegmentIndigo = stepState === "passed" || stepState === "regressed";

            const labelCls = isActive
              ? "font-semibold text-zinc-900 dark:text-zinc-100"
              : stepState === "passed"
              ? "font-medium text-zinc-700 dark:text-zinc-300 group-hover:text-zinc-900 dark:group-hover:text-zinc-100"
              : "font-medium text-zinc-500 dark:text-zinc-400 group-hover:text-zinc-800 dark:group-hover:text-zinc-200";

            return (
              <div key={prob.id} className="relative flex flex-col items-center min-w-0">
                <div
                  aria-hidden="true"
                  className="pointer-events-none absolute left-1/2 w-full bottom-3 translate-y-1/2 h-[2px] z-0"
                >
                  <span className="block w-full h-full bg-zinc-200 dark:bg-zinc-800 rounded-full" />
                  <m.span
                    className="absolute inset-0 bg-indigo-600 dark:bg-indigo-500 rounded-full origin-left"
                    initial={false}
                    animate={{ scaleX: isSegmentIndigo ? 1 : 0 }}
                    transition={settle}
                  />
                </div>

                <button
                  ref={(el) => {
                    stepBtnRefs.current[idx] = el;
                  }}
                  type="button"
                  onClick={() => onSelectQuestion(idx)}
                  aria-label={ariaLabel}
                  title={titleText}
                  aria-current={isActive ? "step" : undefined}
                  className="group relative z-10 flex flex-col items-center w-full pt-0.5 rounded-lg cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/50 dark:focus-visible:ring-indigo-400/60"
                >
                  <span
                    className={`h-4 flex items-center justify-center mb-1 font-mono text-[11px] sm:text-xs leading-none whitespace-nowrap transition-colors ${labelCls}`}
                  >
                    {prob.id}
                  </span>
                  <span className="h-6 w-6 flex items-center justify-center">
                    <m.span
                      aria-hidden="true"
                      initial={false}
                      animate={{ scale: isActive ? 1 : 0.92 }}
                      transition={quick}
                      className={`rounded-full transition-[width,height,background-color,border-color,box-shadow] duration-150 ${
                        isActive ? "w-3.5 h-3.5" : "w-2.5 h-2.5"
                      } ${getDotColorClass(stepState, isActive)} ${
                        isActive ? CURRENT_RING_CLS : ""
                      }`}
                    />
                  </span>
                </button>
              </div>
            );
          })}

          <div className="relative flex flex-col items-center min-w-0">
            <button
              ref={reviewBtnRef}
              type="button"
              onClick={() => onToggleViewMode(isReview ? "quiz" : "review")}
              aria-label="Review & sync"
              aria-pressed={isReview}
              aria-current={isReview ? "step" : undefined}
              title="Review & sync"
              className="group relative z-10 flex flex-col items-center w-full pt-0.5 rounded-lg cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/50 dark:focus-visible:ring-indigo-400/60"
            >
              <span
                className={`h-4 inline-flex items-center justify-center gap-0.5 sm:gap-1 mb-1 text-[10px] sm:text-xs leading-none whitespace-nowrap transition-colors ${
                  isReview
                    ? "font-semibold text-zinc-900 dark:text-zinc-100"
                    : "font-medium text-zinc-500 dark:text-zinc-400 group-hover:text-zinc-800 dark:group-hover:text-zinc-200"
                }`}
              >
                <ClipboardCheck className="w-3 h-3 sm:w-3.5 sm:h-3.5 shrink-0" aria-hidden="true" />
                <span>Review</span>
              </span>
              <span className="h-6 w-6 flex items-center justify-center">
                <m.span
                  aria-hidden="true"
                  initial={false}
                  animate={{ scale: isReview ? 1 : 0.92 }}
                  transition={quick}
                  className={`rounded-full transition-[width,height,background-color,border-color,box-shadow] duration-150 ${
                    isReview ? "w-3.5 h-3.5" : "w-2.5 h-2.5"
                  } ${getDotColorClass("notYet", isReview)} ${
                    isReview ? CURRENT_RING_CLS : ""
                  }`}
                />
              </span>
            </button>
          </div>
        </div>
      </nav>
    </div>
  );
};
