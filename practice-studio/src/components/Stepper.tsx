"use client";

import React, { useEffect, useRef, useState } from "react";
import { m } from "motion/react";
import { Check, ClipboardCheck, Minus, X } from "lucide-react";
import type { ReviewStepMeta, StepItem, StepResult } from "@/lib/stepperModel";
import { statusTone } from "@/lib/statusTone";
import { quick, settle } from "@/lib/motion";
import { Badge } from "@/components/ui/shadcn/Badge";
import { Button } from "@/components/ui/shadcn/Button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";

export interface StepperProps {
  navLabel: string;
  steps: StepItem[];
  currentIndex: number;
  isReview: boolean;
  review: ReviewStepMeta;
  onSelect: (index: number) => void;
  onToggleReview: () => void;
  compact?: boolean;
}

const CURRENT_HALO = "ring-4 ring-accent/15 dark:ring-accent/25";
const CURRENT_MARKER = "border-accent bg-surface-raised text-accent-current";

function getCircleClass(result: StepResult, isCurrent: boolean): string {
  const halo = isCurrent ? ` ${CURRENT_HALO}` : "";

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
        ? `border-dashed ${CURRENT_MARKER}${halo}`
        : statusTone.skipped.solidCircle;
    case "inProgress":
    case "awaitingReview":
      return isCurrent
        ? `${CURRENT_MARKER}${halo}`
        : "border-foreground-faint bg-surface-raised text-foreground-control group-hover:border-muted";
    case "usedHelp":
    case "notTried":
    case "notStarted":
    default:
      return isCurrent
        ? `${CURRENT_MARKER}${halo}`
        : statusTone.notTried.solidCircle;
  }
}

function renderCircleContent(
  result: StepResult,
  circleLabel: string,
  compact = false
): React.ReactNode {
  const iconCls = compact
    ? "size-space-2_5 shrink-0"
    : "size-space-3 sm:size-space-3_5 shrink-0";
  if (result === "correct" || result === "passed" || result === "assisted") {
    return (
      <Check
        className={iconCls}
        strokeWidth={2.5}
        aria-hidden="true"
      />
    );
  }
  if (result === "partial") {
    return (
      <Minus
        className={iconCls}
        strokeWidth={2.5}
        aria-hidden="true"
      />
    );
  }
  if (result === "wrong") {
    return (
      <X
        className={iconCls}
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
  compact = false,
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

  const reviewCircleCls = review.synced
    ? `${statusTone.correct.solidCircle}${isReview ? ` ${CURRENT_HALO}` : ""}`
    : isReview
    ? `${CURRENT_MARKER} ${CURRENT_HALO}`
    : "border-border-control bg-surface-raised text-muted group-hover:border-muted";

  const circleSize = compact
    ? "size-stepper-marker-compact text-micro-compact sm:size-space-5 sm:text-micro"
    : "size-stepper-marker text-micro sm:size-space-6 sm:text-2xs";
  const buttonSize = compact ? "stepperCompact" : "stepper";
  const connectorCls = compact ? "stepper-connector stepper-connector-compact" : "stepper-connector";
  const labelCls = `hidden sm:block max-w-full truncate px-space-1 font-sans tabular-nums ${
    compact ? "mt-space-0_5 text-micro" : "mt-space-1 text-xs"
  } font-normal leading-tight text-muted`;

  return (
    <div
      className={
        compact
          ? "min-w-0"
          : "pt-space-2 border-t border-border/80 min-w-0"
      }
    >
      <nav ref={navRef} aria-label={navLabel} className="min-w-0">
        <div
          ref={scrollerRef}
          data-overflow={overflow ? "true" : "false"}
          className={`overflow-x-auto overscroll-x-contain scrollbar-hidden min-w-0 ${
            overflow
              ? "scroll-fade-edges"
              : ""
          }`}
        >
          <ol className="flex w-full min-w-0 py-space-0_5 px-space-1 gap-space-4 sm:gap-0">
            {steps.map((step, idx) => {
              const isCurrent = !isReview && currentIndex === idx;
              const isSegmentIndigo = idx + 1 <= currentPosition;
              const fullLabel = isCurrent ? `${step.ariaLabel}, current` : step.ariaLabel;

              return (
                <li key={step.key} className="stepper-item">
                  <span
                    aria-hidden="true"
                    data-connector-active={isSegmentIndigo ? "true" : "false"}
                    className={connectorCls}
                  >
                    <span className="block w-full h-full bg-border rounded-full" />
                    <m.span
                      className="absolute inset-0 bg-accent-primary dark:bg-accent-primary-hover rounded-full origin-left"
                      initial={false}
                      animate={{ scaleX: isSegmentIndigo ? 1 : 0 }}
                      transition={settle}
                    />
                  </span>

                  {/* Native title stays as SSR/no-JS fallback; TooltipTrigger strips it after hydration. */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        ref={(el) => {
                          stepBtnRefs.current[idx] = el;
                        }}
                        variant="stepper"
                        size={buttonSize}
                        onClick={() => onSelect(idx)}
                        aria-label={fullLabel}
                        title={fullLabel}
                        aria-current={isCurrent ? "step" : undefined}
                      >
                        <Badge asChild variant="stepMarker" className={`${circleSize} leading-none ${getCircleClass(step.result, isCurrent)}`}>
                          <m.span
                            aria-hidden="true"
                            initial={false}
                            animate={{ scale: isCurrent ? 1 : 0.92 }}
                            transition={quick}
                          >
                            {renderCircleContent(step.result, step.circleLabel, compact)}
                          </m.span>
                        </Badge>

                        <span aria-hidden="true" className={labelCls}>
                          {step.title}
                        </span>
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">{fullLabel}</TooltipContent>
                  </Tooltip>
                </li>
              );
            })}

            <li className="stepper-item">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    ref={reviewBtnRef}
                    variant="stepper"
                    size={buttonSize}
                    onClick={onToggleReview}
                    aria-label={review.ariaLabel}
                    aria-pressed={isReview}
                    aria-current={isReview ? "step" : undefined}
                    title={review.ariaLabel}
                  >
                    <Badge asChild variant="stepMarker" className={`${circleSize} leading-none ${reviewCircleCls}`}>
                      <m.span
                        aria-hidden="true"
                        initial={false}
                        animate={{ scale: isReview ? 1 : 0.92 }}
                        transition={quick}
                      >
                        <ClipboardCheck
                          className={compact ? "size-space-2_5 shrink-0" : "size-space-3 shrink-0"}
                          strokeWidth={2}
                          aria-hidden="true"
                        />
                      </m.span>
                    </Badge>

                    <span aria-hidden="true" className={labelCls}>
                      Review
                    </span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">{review.ariaLabel}</TooltipContent>
              </Tooltip>
            </li>
          </ol>
        </div>
      </nav>
    </div>
  );
};
