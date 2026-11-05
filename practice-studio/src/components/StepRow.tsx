"use client";

import React from "react";
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
      className={`grid grid-cols-1 md:grid-cols-[1.2fr_1fr_auto] gap-3.5 items-center bg-[#1d2333] border rounded-xl p-3.5 cursor-pointer transition-all ${
        isDiverged
          ? "!border-rose-500 !bg-rose-500/10 !opacity-100 ring-1 ring-rose-500/30"
          : isActive
          ? "border-amber-500 bg-amber-500/10 shadow-[0_0_0_2px_rgba(245,158,11,0.25)] opacity-100"
          : "border-[#2c354d] hover:border-indigo-500/50"
      }`}
    >
      <div className="overflow-x-auto text-left">
        <MathBlock latex={step.latex} />
      </div>

      <div
        className={`text-sm text-slate-300 border-l-2 pl-3 transition-colors ${
          isActive
            ? "border-amber-400 text-amber-100 font-medium"
            : "border-[#2c354d]"
        }`}
      >
        <span className="font-semibold text-slate-400 mr-1.5">
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
          className={`text-xs px-2.5 py-1.5 rounded-lg whitespace-nowrap transition-colors border ${
            isDiverged
              ? "bg-rose-600 text-white border-rose-600"
              : "bg-rose-500/10 text-rose-300 border-rose-500/30 hover:bg-rose-500/20"
          }`}
        >
          {isDiverged ? `✗ Diverged at Step ${index + 1}` : "✗ My Paper Diverged Here"}
        </button>
      </div>
    </div>
  );
};
