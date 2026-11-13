"use client";

import React from "react";
import { ChevronLeft, ChevronRight, ClipboardCheck, Eye } from "lucide-react";
import { Problem } from "@/types/drill";

interface QuizPaginationBarProps {
  totalQuestions: number;
  currentIndex: number;
  problems: Problem[];
  viewMode: "quiz" | "review";
  onSelectQuestion: (index: number) => void;
  onPrev: () => void;
  onNext: () => void;
  onToggleViewMode: (mode: "quiz" | "review") => void;
}

export const QuizPaginationBar: React.FC<QuizPaginationBarProps> = ({
  totalQuestions,
  currentIndex,
  problems,
  viewMode,
  onSelectQuestion,
  onPrev,
  onNext,
  onToggleViewMode,
}) => {
  return (
    <div className="flex items-center justify-between gap-3 pt-2.5 border-t border-slate-200 dark:border-[#242f47]">
      {/* Left: Prev/Next & Question Number Pills (No Scrollbar, Generous Spacing & Uncropped Ring) */}
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <button
          type="button"
          onClick={onPrev}
          disabled={viewMode === "quiz" ? currentIndex === 0 : false}
          className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-[#1b2336] hover:bg-slate-200 dark:hover:bg-[#232d44] disabled:opacity-40 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-[#2b3852] transition-colors shrink-0"
          title="Previous Question (ArrowLeft)"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2 overflow-x-auto py-1.5 px-1.5 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
          {problems.map((prob, idx) => {
            const isSkipped = prob.state?.skipped === true;
            const hasScore = prob.state?.score !== null && prob.state?.score !== undefined;
            const isCorrect = hasScore && (prob.state?.score ?? 0) > 0 && !isSkipped;
            const isIncorrect = hasScore && (prob.state?.score ?? 0) === 0 && !isSkipped;
            const isActive = viewMode === "quiz" && currentIndex === idx;

            let colorCls =
              "bg-white dark:bg-[#182032] text-slate-700 dark:text-slate-300 border-slate-300 dark:border-[#2b3752] hover:border-indigo-400";
            let statusLabel = "Unanswered";

            if (isCorrect) {
              colorCls =
                "bg-emerald-600 hover:bg-emerald-500 text-white font-bold border-emerald-500 shadow-sm";
              statusLabel = `Score: ${prob.state?.score}`;
            } else if (isIncorrect) {
              colorCls =
                "bg-rose-600 hover:bg-rose-500 text-white font-bold border-rose-500 shadow-sm";
              statusLabel = "Incorrect (0)";
            } else if (isSkipped) {
              // Ghost style for skipped question: transparent background, dashed border, muted text
              colorCls =
                "bg-transparent hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 dark:text-slate-500 border border-dashed border-slate-300 dark:border-slate-600 font-medium";
              statusLabel = "Skipped (Concept Gap)";
            }

            const activeRing = isActive
              ? "ring-2 ring-indigo-500 ring-offset-2 ring-offset-white dark:ring-offset-[#151924] z-10 font-black"
              : "opacity-90 hover:opacity-100 font-semibold";

            return (
              <button
                key={prob.id}
                type="button"
                onClick={() => onSelectQuestion(idx)}
                title={`Question ${idx + 1} (${prob.id}) — ${statusLabel}`}
                className={`relative w-8 h-8 rounded-lg border text-xs flex items-center justify-center font-mono transition-all shrink-0 ${colorCls} ${activeRing}`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>

        <button
          type="button"
          onClick={onNext}
          disabled={viewMode === "quiz" ? currentIndex === totalQuestions - 1 : false}
          className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-[#1b2336] hover:bg-slate-200 dark:hover:bg-[#232d44] disabled:opacity-40 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-[#2b3852] transition-colors shrink-0"
          title="Next Question (ArrowRight)"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Right: Icon-Only Mode Switcher (Focus Mode vs Pre-Sync Review) */}
      <div className="flex items-center gap-1 bg-slate-100 dark:bg-[#0e1320] p-1 rounded-xl border border-slate-200 dark:border-[#242f47] shrink-0">
        <button
          type="button"
          onClick={() => onToggleViewMode("quiz")}
          title="Focus Mode (Single Question)"
          aria-label="Focus Mode (Single Question)"
          className={`inline-flex items-center justify-center w-8 h-8 rounded-lg transition-all ${
            viewMode === "quiz"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
          }`}
        >
          <Eye className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => onToggleViewMode("review")}
          title="Pre-Sync Review & Summary"
          aria-label="Pre-Sync Review & Summary"
          className={`inline-flex items-center justify-center w-8 h-8 rounded-lg transition-all ${
            viewMode === "review"
              ? "bg-emerald-600 text-white shadow-sm"
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
          }`}
        >
          <ClipboardCheck className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
