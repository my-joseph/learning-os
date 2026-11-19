"use client";

import React, { useEffect, useRef, useState } from "react";
import { m } from "motion/react";
import { Check, ClipboardCheck, Minus, X } from "lucide-react";
import type { ReviewStepMeta, StepItem, StepResult } from "@/lib/stepperModel";
import { statusTone } from "@/lib/statusTone";
import { quick, settle } from "@/lib/motion";

export interface StepperProps {
  navLabel: string;
  steps: StepItem[];
  currentIndex: number;
  isReview: boolean;
  review: ReviewStepMeta;
  onSelect: (index: number) => void;
  onToggleReview: () => void;
}

const CIRCLE_BASE_CLS =
  "relative flex items-center justify-center shrink-0 w-[22px] h-[22px] sm:w-6 sm:h-6 rounded-full border-2 font-display text-[10px] sm:text-[11px] font-semibold tabular-nums leading-none transition-[background-color,border-color,box-shadow,color,filter] duration-150";

const CURRENT_HALO_CLS = "ring-4 ring-indigo-600/15 dark:ring-indigo-400/25";

const BUTTON_CLS =
  "group relative z-10 flex w-full flex-col items-center justify-start min-w-11 min-h-11 py-1 sm:min-w-0 rounded-lg cursor-pointer focus:outline-none focus-visible:outline-none";

const STEP_LI_CLS =
  "relative first:ml-auto last:mr-auto flex-none w-11 sm:flex-1 sm:basis-0 sm:min-w-[72px] sm:max-w-[160px]";

function getCircleClass(result: StepResult, isCurrent: boolean): string {
  const halo = isCurrent ? ` ${CURRENT_HALO_CLS}` : "";

  switch (result) {
    case "correct":
    case "passed":
      return `${statusTone.correct.solidCircle}${halo}`;
    case "assisted":
    case "partial":
      return `${statusTone.assisted.solidCircle}${halo}`;
    case "wrong":
    case "regressed":
      return `${statusTone.wrong.solidCircle}${halo}`;
    case "skipped":
      return isCurrent
        ? `border-dashed border-indigo-600 dark:border-indigo-400 bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-300${halo}`
        : statusTone.skipped.solidCircle;
    case "inProgress":
      return isCurrent
        ? `border-indigo-600 dark:border-indigo-400 bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-300${halo}`
        : "border-zinc-400 dark:border-zinc-500 bg-white dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300 group-hover:border-zinc-500 dark:group-hover:border-zinc-400";
    case "usedHelp":
    case "notTried":
    case "notStarted":
    default:
      return isCurrent
        ? `border-indigo-600 dark:border-indigo-400 bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-300${halo}`
        : statusTone.notTried.solidCircle;
  }
}

function renderCircleContent(result: StepResult, circleLabel: string): React.ReactNode {
  if (result === "correct" || result === "passed" || result === "assisted") {
    return (
      <Check
        className="w-3 h-3 sm:w-3.5 sm:h-3.5 shrink-0"
        strokeWidth={2.5}
        aria-hidden="true"
      />
    );
  }
  if (result === "partial") {
    return (
      <Minus
        className="w-3 h-3 sm:w-3.5 sm:h-3.5 shrink-0"
        strokeWidth={2.5}
        aria-hidden="true"
      />
    );
  }
  if (result === "wrong") {
    return (
      <X
        className="w-3 h-3 sm:w-3.5 sm:h-3.5 shrink-0"
        strokeWidth={2.5}
        aria-hidden="true"
      />
    );
  }
  return circleLabel;
}

/**
 * Shared horizontal stepper for Math drills, Programming drills, and Project Labs.
 * Uses `nav > ol > li > button` (never a tablist) so global Left/Right arrow navigation
 * in `useDrill.ts` continues working while a step has focus.
 */
export const Stepper: React.FC<StepperProps> = ({
  navLabel,
  steps,
  currentIndex,
  isReview,
  review,
  onSelect,
  onToggleReview,
}) => {
  const navRef = useRef<HTMLElement | null>(null);
  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const stepBtnRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const reviewBtnRef = useRef<HTMLButtonElement | null>(null);
  const hasMountedRef = useRef(false);
  const [overflow, setOverflow] = useState(false);

  const currentPosition = isReview ? steps.length : currentIndex;

  // Keep keyboard focus on the current step (including Review) when navigation happens
  // while focus is already inside this nav.
  useEffect(() => {
    const nav = navRef.current;
    if (!nav) return;
    const active = document.activeElement;
    if (active && nav.contains(active)) {
      const current = nav.querySelector<HTMLButtonElement>('button[aria-current="step"]');
      if (current && current !== active) {
        current.focus({ preventScroll: true });
      }
    }
  }, [currentIndex, isReview]);

  // Measure horizontal overflow to show edge fades only when the strip actually scrolls.
  useEffect(() => {
    const scroller = scrollerRef.current;
    if (!scroller) return;

    const measure = () => {
      setOverflow(scroller.scrollWidth > scroller.clientWidth + 1);
    };
    measure();

    if (typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", measure);
      return () => window.removeEventListener("resize", measure);
    }

    const ro = new ResizeObserver(measure);
    ro.observe(scroller);
    if (scroller.firstElementChild) {
      ro.observe(scroller.firstElementChild);
    }
    return () => ro.disconnect();
  }, [steps.length]);

  // Centre the current step inside the horizontal scroller without touching window scroll.
  useEffect(() => {
    const scroller = scrollerRef.current;
    const btn = isReview ? reviewBtnRef.current : stepBtnRefs.current[currentIndex];
    const isFirstMount = !hasMountedRef.current;
    hasMountedRef.current = true;

    if (!scroller || !btn) return;
    if (scroller.scrollWidth <= scroller.clientWidth + 1) return;

    const scrollerRect = scroller.getBoundingClientRect();
    const btnRect = btn.getBoundingClientRect();
    const btnCenterInScroller =
      btnRect.left - scrollerRect.left + scroller.scrollLeft + btnRect.width / 2;
    const targetLeft = Math.max(0, btnCenterInScroller - scroller.clientWidth / 2);
    if (Math.abs(targetLeft - scroller.scrollLeft) < 1) return;

    const prefersReduced =
      typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    scroller.scrollTo({
      left: targetLeft,
      behavior: isFirstMount || prefersReduced ? "auto" : "smooth",
    });
  }, [currentIndex, isReview, steps.length]);

  const reviewCircleCls = isReview
    ? `border-indigo-600 dark:border-indigo-400 bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-300 ${CURRENT_HALO_CLS}`
    : "border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 group-hover:border-zinc-500 dark:group-hover:border-zinc-400";

  return (
    <div className="pt-2 border-t border-zinc-200/80 dark:border-zinc-800/80 min-w-0">
      <nav ref={navRef} aria-label={navLabel} className="min-w-0">
        <div
          ref={scrollerRef}
          data-overflow={overflow ? "true" : "false"}
          className={`overflow-x-auto overscroll-x-contain [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden min-w-0 ${
            overflow
              ? "[mask-image:linear-gradient(to_right,transparent,#000_16px,#000_calc(100%_-_16px),transparent)]"
              : ""
          }`}
        >
          <ol className="flex w-full min-w-0 py-0.5 px-1 gap-4 sm:gap-0">
            {steps.map((step, idx) => {
              const isCurrent = !isReview && currentIndex === idx;
              const isSegmentIndigo = idx + 1 <= currentPosition;
              const fullLabel = isCurrent ? `${step.ariaLabel}, current` : step.ariaLabel;

              return (
                <li key={step.key} className={STEP_LI_CLS}>
                  <span
                    aria-hidden="true"
                    data-connector-active={isSegmentIndigo ? "true" : "false"}
                    className="pointer-events-none absolute top-[15px] sm:top-4 -translate-y-1/2 left-[calc(50%_+_15px)] w-[30px] sm:left-[calc(50%_+_18px)] sm:w-[calc(100%_-_36px)] h-0.5 rounded-full z-0"
                  >
                    <span className="block w-full h-full bg-zinc-200 dark:bg-zinc-800 rounded-full" />
                    <m.span
                      className="absolute inset-0 bg-indigo-600 dark:bg-indigo-500 rounded-full origin-left"
                      initial={false}
                      animate={{ scaleX: isSegmentIndigo ? 1 : 0 }}
                      transition={settle}
                    />
                  </span>

                  <button
                    ref={(el) => {
                      stepBtnRefs.current[idx] = el;
                    }}
                    type="button"
                    onClick={() => onSelect(idx)}
                    aria-label={fullLabel}
                    title={fullLabel}
                    aria-current={isCurrent ? "step" : undefined}
                    className={BUTTON_CLS}
                  >
                    <m.span
                      aria-hidden="true"
                      initial={false}
                      animate={{ scale: isCurrent ? 1 : 0.92 }}
                      transition={quick}
                      className={`${CIRCLE_BASE_CLS} ${getCircleClass(step.result, isCurrent)}`}
                    >
                      {renderCircleContent(step.result, step.circleLabel)}
                    </m.span>

                    <span
                      aria-hidden="true"
                      className={`hidden sm:block mt-1 max-w-full truncate px-1 font-display text-xs font-medium leading-tight text-zinc-500 dark:text-zinc-400`}
                    >
                      {step.title}
                    </span>

                  </button>
                </li>
              );
            })}

            <li className={STEP_LI_CLS}>
              <button
                ref={reviewBtnRef}
                type="button"
                onClick={onToggleReview}
                aria-label={review.ariaLabel}
                aria-pressed={isReview}
                aria-current={isReview ? "step" : undefined}
                title={review.ariaLabel}
                className={BUTTON_CLS}
              >
                <m.span
                  aria-hidden="true"
                  initial={false}
                  animate={{ scale: isReview ? 1 : 0.92 }}
                  transition={quick}
                  className={`${CIRCLE_BASE_CLS} ${reviewCircleCls}`}
                >
                  <ClipboardCheck
                    className="w-3 h-3 shrink-0"
                    strokeWidth={2}
                    aria-hidden="true"
                  />
                </m.span>

                <span
                  aria-hidden="true"
                  className={`hidden sm:block mt-1 max-w-full truncate px-1 font-display text-xs font-medium leading-tight text-zinc-500 dark:text-zinc-400`}
                >
                  Review
                </span>
              </button>
            </li>
          </ol>
        </div>
      </nav>
    </div>
  );
};
