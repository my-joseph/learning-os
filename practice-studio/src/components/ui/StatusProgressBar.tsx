"use client";

import React, { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { Progress } from "./Progress";

export interface ProgressStage {
  minPct: number;
  message: string;
}

export interface StatusProgressBarProps {
  label: string;
  active?: boolean;
  completed?: boolean;
  /** Pass a value to use backend-controlled progress instead of auto-staged progress. */
  value?: number;
  statusMessage?: string;
  stages?: ProgressStage[];
  autoCapPct?: number;
  className?: string;
}

export function getProgressStageMessage(pct: number, stages: ProgressStage[]): string {
  const clamped = Math.min(100, Math.max(0, Number.isFinite(pct) ? pct : 0));
  return stages
    .filter((stage) => stage.minPct <= clamped)
    .sort((a, b) => a.minPct - b.minPct)
    .at(-1)?.message ?? stages.slice().sort((a, b) => a.minPct - b.minPct)[0]?.message ?? "";
}

export const StatusProgressBar: React.FC<StatusProgressBarProps> = ({
  label,
  active = false,
  completed = false,
  value,
  statusMessage,
  stages = [],
  autoCapPct = 92,
  className = "",
}) => {
  const cap = Math.min(99, Math.max(0, Number.isFinite(autoCapPct) ? autoCapPct : 92));
  const [autoValue, setAutoValue] = useState(0);

  useEffect(() => {
    if (!active || completed || value !== undefined) return;

    const timer = window.setInterval(() => {
      setAutoValue((current) => Math.min(cap, current + Math.max(0.35, (cap - current) * 0.06)));
    }, 900);
    return () => window.clearInterval(timer);
  }, [active, cap, completed, value]);

  const pct = completed
    ? 100
    : Math.round(Math.min(100, Math.max(0, value === undefined ? autoValue : value)));
  const message = statusMessage ?? getProgressStageMessage(pct, stages);

  return (
    <div className={`space-y-2.5 ${className}`.trim()}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2 text-sm font-medium text-zinc-800 dark:text-zinc-200">
          {active && (
            <Loader2 className="h-4 w-4 shrink-0 animate-spin text-indigo-600 dark:text-indigo-400" aria-hidden="true" />
          )}
          <span className="truncate">{label}</span>
        </div>
        <span className="font-display tabular-nums text-xs text-zinc-500 dark:text-zinc-400">
          {pct}%
        </span>
      </div>
      <Progress value={pct} aria-label={label} />
      <p role="status" aria-live="polite" className="min-h-5 text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
        {message}
      </p>
    </div>
  );
};
