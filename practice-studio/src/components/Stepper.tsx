"use client";

import React, { useEffect, useRef, useState } from "react";
import { m } from "motion/react";
import { Check, ClipboardCheck, Minus, X } from "lucide-react";
import type { ReviewStepMeta, StepItem, StepResult } from "@/lib/stepperModel";
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
  "relative flex items-center justify-center shrink-0 w-7 h-7 sm:w-9 sm:h-9 rounded-full border-2 font-display text-xs sm:text-sm font-semibold tabular-nums leading-none transition-[background-color,border-color,box-shadow,color] duration-150";

const CURRENT_HALO_CLS = "ring-4 ring-indigo-600/15 dark:ring-indigo-400/25";

const BUTTON_CLS =
  "group relative z-10 flex w-full flex-col items-center justify-center sm:justify-start min-w-11 h-11 sm:h-auto sm:min-w-0 sm:pt-1 sm:pb-1 rounded-lg cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 focus-visible:ring-offset-2 ring-offset-white dark:ring-offset-zinc-900";

const STEP_LI_CLS =
  "relative first:ml-auto last:mr-auto flex-none w-11 sm:flex-1 sm:basis-0 sm:min-w-[72px] sm:max-w-[160px]";

function getCircleClass(result: StepResult, isCurrent: boolean): string {
  const halo = isCurrent ? ` ${CURRENT_HALO_CLS}` : "";

  switch (result) {
    case "correct":
    case "passed":
      return `bg-indigo-600 border-indigo-600 text-white group-hover:bg-indigo-700 group-hover:border-indigo-700 dark:bg-indigo-500 dark:border-indigo-500 dark:group-hover:bg-indigo-400 dark:group-hover:border-indigo-400${halo}`;
    case "assisted":
    case "partial":
    case "regressed":
      return `bg-amber-600 border-amber-600 text-white group-hover:bg-amber-700 group-hover:border-amber-700 dark:bg-amber-400 dark:border-amber-400 dark:text-zinc-950 dark:group-hover:bg-amber-300 dark:group-hover:border-amber-300${halo}`;
    case "wrong":
      return `bg-rose-600 border-rose-600 text-white group-hover:bg-rose-700 group-hover:border-rose-700 dark:bg-rose-400 dark:border-rose-400 dark:text-zinc-950 dark:group-hover:bg-rose-300 dark:group-hover:border-rose-300${halo}`;
    case "skipped":
      return isCurrent
        ? `border-dashed border-indigo-600 dark:border-indigo-400 bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-300${halo}`
        : "border-dashed border-zinc-400 dark:border-zinc-500 bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 group-hover:border-zinc-500 dark:group-hover:border-zinc-400";
    case "inProgress":
      return isCurrent
        ? `border-indigo-600 dark:border-indigo-400 bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-300${halo}`
        : "border-zinc-400 dark:border-zinc-500 bg-white dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300 group-hover:border-zinc-500 dark:group-hover:border-zinc-400";
    case "notTried":
    case "notStarted":
    default:
      return isCurrent
        ? `border-indigo-600 dark:border-indigo-400 bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-300${halo}`
        : "border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 group-hover:border-zinc-500 dark:group-hover:border-zinc-400";
  }
}

function renderCircleContent(result: StepResult, index: number): React.ReactNode {
  if (result === "correct" || result === "passed" || result === "assisted") {
    return (
      <Check
        className="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0"
        strokeWidth={2.5}
        aria-hidden="true"
      />
    );
  }
  if (result === "partial") {
    return (
      <Minus
        className="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0"
        strokeWidth={2.5}
        aria-hidden="true"
      />
    );
  }
  if (result === "wrong") {
    return (
      <X
        className="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0"
        strokeWidth={2.5}
        aria-hidden="true"
      />
    );
  }
  return String(index + 1).padStart(2, "0");
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

  const totalColumns = steps.length + 1;
  const currentPosition = isReview ? steps.length : currentIndex;
  const titleSizeCls = totalColumns > 9 ? "text-xs" : "text-sm";

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
    <div className="pt-3 border-t border-zinc-200/80 dark:border-zinc-800/80 min-w-0">
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
          <ol className="flex w-full min-w-0 py-1.5 px-1 gap-4 sm:gap-0">
            {steps.map((step, idx) => {
              const isCurrent = !isReview && currentIndex === idx;
              const isSegmentIndigo = idx + 1 <= currentPosition;
              const fullLabel = isCurrent ? `${step.ariaLabel}, current` : step.ariaLabel;

              return (
                <li key={step.key} className={STEP_LI_CLS}>
                  <span
                    aria-hidden="true"
                    data-connector-active={isSegmentIndigo ? "true" : "false"}
                    className="pointer-events-none absolute top-[22px] -translate-y-1/2 left-[calc(50%_+_18px)] w-6 sm:left-[calc(50%_+_24px)] sm:w-[calc(100%_-_48px)] h-0.5 rounded-full z-0"
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
                      {renderCircleContent(step.result, idx)}
                    </m.span>

                    <span
                      aria-hidden="true"
                      className={`hidden sm:block mt-2 max-w-full truncate px-1 font-display ${titleSizeCls} font-semibold leading-snug transition-colors ${
                        isCurrent
                          ? "text-zinc-900 dark:text-zinc-100"
                          : "text-zinc-700 dark:text-zinc-300 group-hover:text-zinc-900 dark:group-hover:text-zinc-100"
                      }`}
                    >
                      {step.title}
                    </span>

                    <span
                      aria-hidden="true"
                      className="hidden sm:block max-w-full truncate px-1 font-display text-xs text-zinc-500 dark:text-zinc-400 leading-snug"
                    >
                      {step.secondary}
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
                    className="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0"
                    strokeWidth={2}
                    aria-hidden="true"
                  />
                </m.span>

                <span
                  aria-hidden="true"
                  className={`hidden sm:block mt-2 max-w-full truncate px-1 font-display ${titleSizeCls} font-semibold leading-snug transition-colors ${
                    isReview
                      ? "text-zinc-900 dark:text-zinc-100"
                      : "text-zinc-700 dark:text-zinc-300 group-hover:text-zinc-900 dark:group-hover:text-zinc-100"
                  }`}
                >
                  Review &amp; sync
                </span>

                <span
                  aria-hidden="true"
                  className="hidden sm:block max-w-full truncate px-1 font-display text-xs text-zinc-500 dark:text-zinc-400 leading-snug"
                >
                  {review.secondary}
                </span>
              </button>
            </li>
          </ol>
        </div>
      </nav>
    </div>
  );
};
