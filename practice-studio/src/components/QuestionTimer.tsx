"use client";

import React from "react";
import { AnimatePresence, m } from "motion/react";
import { Clock, Pause, Play } from "lucide-react";
import { formatTimerClock } from "@/lib/telemetryTimer";
import { IconButton } from "@/components/ui/shadcn/Button";
import { warningTone } from "@/lib/statusTone";
import { fade, presence } from "@/lib/motion";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";

export interface QuestionTimerProps {
  /** Current question's recorded duration plus active attempt elapsed time (ms). */
  questionMs: number;
  /** Whole drill/lab total recorded plus active elapsed time (ms). */
  totalMs: number;
  /** Whether the session timer is paused. */
  isPaused?: boolean;
  /** Toggle pause/resume for the session timer. */
  onTogglePause?: () => void;
}

/** Quiet meta-line timer: this question's time + pause toggle; the drill/lab total floats on hover/focus of the clock. */
export const QuestionTimer: React.FC<QuestionTimerProps> = ({
  questionMs,
  totalMs,
  isPaused = false,
  onTogglePause,
}) => {
  const questionClock = formatTimerClock(questionMs);
  const totalClock = formatTimerClock(totalMs);
  const pauseActionLabel = isPaused ? "Resume timer" : "Pause timer";
  const pauseTooltipLabel = isPaused ? "Resume timer (p)" : "Pause timer (p)";

  return (
    <div className="inline-flex items-center gap-space-2 ml-auto shrink-0">
      <span
        className={`inline-flex items-center gap-space-1 text-xs font-medium tabular-nums transition-colors ${
          isPaused ? warningTone.text : "text-muted"
        }`}
      >
        <Tooltip>
          <TooltipTrigger asChild>
            <span
              className="relative inline-flex rounded-sm cursor-default focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 dark:focus-visible:ring-accent/60"
              tabIndex={0}
              aria-label={`Total ${totalClock}`}
            >
              <Clock className="size-space-3_5 shrink-0" aria-hidden="true" />
            </span>
          </TooltipTrigger>
          <TooltipContent
            side="bottom"
            sideOffset={8}
            className="rounded-full px-space-3 py-space-1 font-display tabular-nums whitespace-nowrap"
          >
            Total {totalClock}
          </TooltipContent>
        </Tooltip>
        <AnimatePresence initial={false}>
          {isPaused && (
            <m.span key="paused" variants={fade} {...presence}>
              Paused
            </m.span>
          )}
        </AnimatePresence>
        <span className="font-display">{questionClock}</span>
      </span>

      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            hitArea="timer"
            size="timer"
            tone={isPaused ? "timerPaused" : "timer"}
            onClick={onTogglePause}
            aria-label={pauseActionLabel}
            aria-pressed={isPaused}
            className="-my-space-2_5 -mr-space-2_5 sm:my-0 sm:mr-0"
          >
            {isPaused ? (
              <Play className="size-space-3" aria-hidden="true" />
            ) : (
              <Pause className="size-space-3" aria-hidden="true" />
            )}
          </IconButton>
        </TooltipTrigger>
        <TooltipContent side="bottom">{pauseTooltipLabel}</TooltipContent>
      </Tooltip>
    </div>
  );
};
