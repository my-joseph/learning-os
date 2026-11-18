"use client";

import React from "react";
import { Flag } from "lucide-react";
import { Step } from "@/types/drill";
import { MathBlock } from "./MathRender";
import { FormattedText } from "./FormattedText";

interface StepRowProps {
  step: Step;
  index: number;
  isActive: boolean;
  isDiverged: boolean;
  onToggleHighlight: () => void;
  onMarkDiverged: () => void;
}

export const StepRow: React.FC<StepRowProps> = ({
  step,
  index,
  isActive,
  isDiverged,
  onToggleHighlight,
  onMarkDiverged,
}) => {
  return (
    <div
      onClick={onToggleHighlight}
      className={`group step-row ${isActive || isDiverged ? "step-row-active" : ""} grid grid-cols-1 md:grid-cols-[1.2fr_1fr_auto] gap-3 items-center rounded-xl p-3 mb-2 last:mb-0 cursor-pointer transition-colors border ${
        isDiverged
          ? "border-zinc-200 dark:border-zinc-800 border-l-4 border-l-rose-600 dark:border-l-rose-400 bg-white dark:bg-zinc-900"
          : isActive
          ? "border-zinc-200 dark:border-zinc-800 border-l-4 border-l-amber-600 dark:border-l-amber-400 bg-white dark:bg-zinc-900"
          : "bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700"
      }`}
    >
      <div className="overflow-x-auto text-left text-sm text-zinc-900 dark:text-zinc-100">
        <MathBlock latex={step.latex} />
      </div>

      <div
        className={`text-xs border-l pl-3 transition-colors ${
          isDiverged
            ? "border-rose-600 dark:border-rose-400 text-zinc-900 dark:text-zinc-100"
            : isActive
            ? "border-amber-600 dark:border-amber-400 text-zinc-900 dark:text-zinc-100"
            : "border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-300"
        }`}
      >
        <span className="font-medium text-zinc-500 dark:text-zinc-400 mr-1.5">
          Step {index + 1}:
        </span>
        <FormattedText text={step.explain} />
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onMarkDiverged();
          }}
          className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg whitespace-nowrap font-medium transition-all border ${
            isDiverged
              ? "opacity-100 border-rose-600 dark:border-rose-400 text-rose-600 dark:text-rose-400 bg-zinc-50 dark:bg-zinc-950"
              : "opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 focus:opacity-100 border-zinc-200 dark:border-zinc-800 text-zinc-500 dark:text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 hover:border-rose-300 dark:hover:border-rose-500/40"
          }`}
        >
          <Flag className="w-3.5 h-3.5 shrink-0" />
          <span>{isDiverged ? `Diverged at step ${index + 1}` : "Diverged here"}</span>
        </button>
      </div>
    </div>
  );
};
