"use client";

import React from "react";
import { AnimatePresence, m } from "motion/react";
import { Clock, Pause, Play } from "lucide-react";
import { formatTimerClock } from "@/lib/telemetryTimer";
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
    <div className="inline-flex items-center gap-2 ml-auto shrink-0">
      <span
        className={`inline-flex items-center gap-1 text-xs font-medium tabular-nums transition-colors ${
          isPaused ? warningTone.text : "text-zinc-500 dark:text-zinc-400"
        }`}
      >
        <Tooltip>
          <TooltipTrigger asChild>
            <span
              className="relative inline-flex rounded-sm cursor-default focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/50 dark:focus-visible:ring-indigo-400/60"
              tabIndex={0}
              aria-label={`Total ${totalClock}`}
            >
              <Clock className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            </span>
          </TooltipTrigger>
          <TooltipContent
            side="bottom"
            sideOffset={8}
            className="rounded-full px-3 py-1 font-display tabular-nums whitespace-nowrap"
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
          <button
            type="button"
            onClick={onTogglePause}
            aria-label={pauseActionLabel}
            aria-pressed={isPaused}
            className={`inline-flex items-center justify-center min-h-[44px] min-w-[44px] w-11 h-11 -my-2.5 -mr-2.5 sm:min-h-0 sm:min-w-0 sm:w-6 sm:h-6 sm:my-0 sm:mr-0 rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/50 dark:focus-visible:ring-indigo-400/60 ${
              isPaused
                ? `${warningTone.text} hover:bg-zinc-100 dark:hover:bg-zinc-800`
                : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800"
            }`}
          >
            {isPaused ? (
              <Play className="w-3 h-3" aria-hidden="true" />
            ) : (
              <Pause className="w-3 h-3" aria-hidden="true" />
            )}
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom">{pauseTooltipLabel}</TooltipContent>
      </Tooltip>
    </div>
  );
};
