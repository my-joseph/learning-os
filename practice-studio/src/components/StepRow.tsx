"use client";

import React from "react";
import { Flag } from "lucide-react";
import { Step } from "@/types/drill";
import { statusTone } from "@/lib/statusTone";
import { MathBlock } from "./MathRender";
import { FormattedText } from "./FormattedText";

interface StepRowProps {
  step: Step;
  index: number;
  isDiverged?: boolean;
  onMarkDiverged?: () => void;
}

export const StepRow: React.FC<StepRowProps> = ({
  step,
  index,
  isDiverged = false,
  onMarkDiverged,
}) => {
  const hasLatex = Boolean(step.latex && step.latex.trim());
  const gridCols = onMarkDiverged
    ? hasLatex
      ? "md:grid-cols-[1.2fr_1fr_auto]"
      : "md:grid-cols-[1fr_auto]"
    : hasLatex
    ? "md:grid-cols-[1.2fr_1fr]"
    : "md:grid-cols-1";

  return (
    // Hover focuses a step; other rows dim via globals.css.
    <div
      className={`group step-row ${isDiverged ? "step-row-active" : ""} grid grid-cols-1 ${gridCols} gap-3 items-center rounded-xl p-3 mb-2 last:mb-0 transition-[colors,opacity] duration-150 border ${
        isDiverged
          ? `${statusTone.wrong.borderSoft} bg-white dark:bg-zinc-900`
          : "bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700"
      }`}
    >
      {hasLatex && (
        <div className="min-w-0 overflow-x-auto overflow-y-hidden [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden text-left text-sm text-zinc-900 dark:text-zinc-100">
          <MathBlock latex={step.latex!} />
        </div>
      )}

      <div
        className={`text-xs ${hasLatex ? "border-l pl-3" : ""} transition-colors ${
          isDiverged
            ? `${statusTone.wrong.border} text-zinc-900 dark:text-zinc-100`
            : "border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-300 group-hover:border-accent group-hover:text-zinc-900 dark:group-hover:text-zinc-100"
        }`}
      >
        <span className="font-display tabular-nums font-medium text-zinc-500 dark:text-zinc-400 mr-1.5">
          Step {index + 1}:
        </span>
        <FormattedText text={step.explain} />
      </div>

      {onMarkDiverged && (
        <div className="flex justify-end">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onMarkDiverged();
            }}
            className={`inline-flex items-center justify-center gap-1.5 min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 text-xs px-2.5 py-1 rounded-lg whitespace-nowrap font-medium transition-all border ${
              isDiverged
                ? `opacity-100 ${statusTone.wrong.border} ${statusTone.wrong.text} bg-surface-panel`
                : `opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 focus:opacity-100 border-zinc-200 dark:border-zinc-800 text-zinc-500 dark:text-zinc-400 ${statusTone.wrong.hoverText} ${statusTone.wrong.hoverBorderSoft}`
            }`}
          >
            <Flag className="w-3.5 h-3.5 shrink-0" />
            <span>{isDiverged ? `Diverged at step ${index + 1}` : "Diverged here"}</span>
          </button>
        </div>
      )}
    </div>
  );
};
