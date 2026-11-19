"use client";

import React, { useId, useState } from "react";
import { AnimatePresence, m } from "motion/react";
import { Clock, Pause, Play } from "lucide-react";
import { formatTimerClock } from "@/lib/telemetryTimer";
import { fade, presence } from "@/lib/motion";

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
  const [showTotal, setShowTotal] = useState(false);
  const tipId = useId();

  return (
    <div className="inline-flex items-center gap-2 ml-auto shrink-0">
      <span
        className={`inline-flex items-center gap-1 text-xs font-medium tabular-nums transition-colors ${
          isPaused
            ? "text-amber-700 dark:text-amber-400"
            : "text-zinc-500 dark:text-zinc-400"
        }`}
      >
        <span
          className="relative inline-flex rounded-sm cursor-default focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/50 dark:focus-visible:ring-indigo-400/60"
          tabIndex={0}
          aria-label={`Total ${totalClock}`}
          aria-describedby={showTotal ? tipId : undefined}
          onMouseEnter={() => setShowTotal(true)}
          onMouseLeave={() => setShowTotal(false)}
          onFocus={() => setShowTotal(true)}
          onBlur={() => setShowTotal(false)}
        >
          <Clock className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <AnimatePresence>
            {showTotal && (
              <m.span
                key="total"
                id={tipId}
                role="tooltip"
                variants={fade}
                {...presence}
                className="pointer-events-none absolute top-full left-1/2 -translate-x-1/2 mt-2 z-30 whitespace-nowrap rounded-full border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-1 text-xs font-medium tabular-nums text-zinc-700 dark:text-zinc-200 shadow-md"
              >
                Total {totalClock}
              </m.span>
            )}
          </AnimatePresence>
        </span>
        <AnimatePresence initial={false}>
          {isPaused && (
            <m.span key="paused" variants={fade} {...presence}>
              Paused
            </m.span>
          )}
        </AnimatePresence>
        <span>{questionClock}</span>
      </span>

      <button
        type="button"
        onClick={onTogglePause}
        aria-label={isPaused ? "Resume timer" : "Pause timer"}
        aria-pressed={isPaused}
        title={isPaused ? "Resume timer (p)" : "Pause timer (p)"}
        className={`inline-flex items-center justify-center w-6 h-6 rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/50 dark:focus-visible:ring-indigo-400/60 ${
          isPaused
            ? "text-amber-700 dark:text-amber-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
            : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800"
        }`}
      >
        {isPaused ? (
          <Play className="w-3 h-3" aria-hidden="true" />
        ) : (
          <Pause className="w-3 h-3" aria-hidden="true" />
        )}
      </button>

    </div>
  );
};
