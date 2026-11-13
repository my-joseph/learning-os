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
      className={`step-row ${isActive || isDiverged ? "step-row-active" : ""} grid grid-cols-1 md:grid-cols-[1.2fr_1fr_auto] gap-3.5 items-center rounded-xl p-3.5 mb-2.5 last:mb-0 cursor-pointer transition-all border ${
        isDiverged
          ? "border-rose-500 bg-rose-50 dark:bg-rose-500/10 ring-1 ring-rose-500/30"
          : isActive
          ? "border-amber-500 bg-amber-50 dark:bg-amber-500/10 ring-1 ring-amber-500/30"
          : "bg-white dark:bg-[#1d2333] border-slate-200 dark:border-[#2c354d] hover:border-indigo-400 dark:hover:border-indigo-500/50"
      }`}
    >
      <div className="overflow-x-auto text-left text-slate-900 dark:text-slate-100">
        <MathBlock latex={step.latex} />
      </div>

      <div
        className={`text-sm border-l-2 pl-3 transition-colors ${
          isDiverged
            ? "border-rose-500 text-rose-900 dark:text-rose-200 font-medium"
            : isActive
            ? "border-amber-500 text-amber-900 dark:text-amber-100 font-medium"
            : "border-slate-200 dark:border-[#2c354d] text-slate-700 dark:text-slate-300"
        }`}
      >
        <span className="font-semibold text-slate-500 dark:text-slate-400 mr-1.5">
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
          className={`inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg whitespace-nowrap font-medium transition-colors border ${
            isDiverged
              ? "bg-rose-600 text-white border-rose-600 shadow-sm"
              : "bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-500/30 hover:bg-rose-100 dark:hover:bg-rose-500/20"
          }`}
        >
          <Flag className="w-3.5 h-3.5 shrink-0" />
          <span>{isDiverged ? `Diverged at Step ${index + 1}` : "Paper Diverged Here"}</span>
        </button>
      </div>
    </div>
  );
};
