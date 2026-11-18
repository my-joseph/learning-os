"use client";

import React from "react";
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

/** Quiet meta-line timer showing per-question elapsed time, pause toggle, and drill/lab total. */
export const QuestionTimer: React.FC<QuestionTimerProps> = ({
  questionMs,
  totalMs,
  isPaused = false,
  onTogglePause,
}) => {
  const questionClock = formatTimerClock(questionMs);
  const totalClock = formatTimerClock(totalMs);

  return (
    <div className="inline-flex items-center gap-2 ml-auto shrink-0">
      <span
        className={`inline-flex items-center gap-1 text-xs font-medium tabular-nums transition-colors ${
          isPaused
            ? "text-amber-700 dark:text-amber-400"
            : "text-zinc-500 dark:text-zinc-400"
        }`}
      >
        <Clock className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
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

      <span className="text-[11px] font-normal tabular-nums text-zinc-500 dark:text-zinc-400 whitespace-nowrap">
        Total {totalClock}
      </span>
    </div>
  );
};
