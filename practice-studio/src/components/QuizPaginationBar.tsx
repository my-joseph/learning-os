"use client";

import React from "react";
import { ChevronLeft, ChevronRight, CheckCircle2, XCircle, HelpCircle, LayoutGrid, Eye } from "lucide-react";
import { Problem } from "@/types/drill";

interface QuizPaginationBarProps {
  totalQuestions: number;
  currentIndex: number;
  problems: Problem[];
  viewMode: "quiz" | "all";
  onSelectQuestion: (index: number) => void;
  onPrev: () => void;
  onNext: () => void;
  onToggleViewMode: (mode: "quiz" | "all") => void;
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
  // Compute counts
  let correctCount = 0;
  let incorrectCount = 0;
  let skippedCount = 0;
  let unattemptedCount = 0;

  problems.forEach((p) => {
    const isSkipped = p.state?.skipped === true;
    const hasScore = p.state?.score !== null && p.state?.score !== undefined;
    if (isSkipped) {
      skippedCount++;
    } else if (hasScore) {
      if ((p.state?.score ?? 0) > 0) {
        correctCount++;
      } else {
        incorrectCount++;
      }
    } else {
      unattemptedCount++;
    }
  });

  const progressPct = totalQuestions > 0 ? Math.round(((correctCount + incorrectCount + skippedCount) / totalQuestions) * 100) : 0;

  return (
    <nav
      aria-label="Quiz question navigation"
      className="sticky top-20 z-40 bg-[#151a27]/95 backdrop-blur-md border border-[#2b3752] rounded-2xl p-3.5 mb-6 shadow-xl transition-all"
    >
      {/* Top Row: Question counter, quick stats pills, and View Mode switcher */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3 pb-2.5 border-b border-[#242f47]">
        <div className="flex items-center gap-2.5">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">
            {viewMode === "quiz" ? (
              <>
                Question <span className="text-white text-sm font-black">{currentIndex + 1}</span> of {totalQuestions}
              </>
            ) : (
              <>All {totalQuestions} Questions</>
            )}
          </span>
          <span className="text-[11px] font-mono text-slate-400 bg-[#1c2438] px-2 py-0.5 rounded-full border border-[#2c3852]">
            {progressPct}% Completed
          </span>
        </div>

        {/* Live Status Indicators (Correct=Green, Incorrect=Red, Skipped=Gray) */}
        <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-medium font-mono">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            {correctCount} Correct
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
            {incorrectCount} Incorrect
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-500/20 text-slate-300 border border-slate-500/40">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
            {skippedCount} Skipped
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#131926] text-slate-400 border border-[#25324b]">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
            {unattemptedCount} Left
          </span>
        </div>

        {/* Mode Switcher: Focus (Quiz) vs Scroll All */}
        <div className="flex items-center bg-[#0e1320] p-0.5 rounded-lg border border-[#242f47]">
          <button
            type="button"
            onClick={() => onToggleViewMode("quiz")}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
              viewMode === "quiz"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Focus on 1 question at a time (Quiz Mode)"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Focus Mode</span>
          </button>
          <button
            type="button"
            onClick={() => onToggleViewMode("all")}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
              viewMode === "all"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="View all questions in a scrolling list"
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            <span>View All</span>
          </button>
        </div>
      </div>

      {/* Bottom Row: Prev Button, Numbered Pagination Buttons, Next Button */}
      <div className="flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={onPrev}
          disabled={viewMode === "quiz" ? currentIndex === 0 : false}
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#1b2336] hover:bg-[#232d44] disabled:opacity-40 disabled:hover:bg-[#1b2336] text-slate-200 border border-[#2b3852] transition-colors shadow-sm shrink-0"
        >
          <ChevronLeft className="w-4 h-4" />
          <span className="hidden sm:inline">Prev</span>
        </button>

        {/* Question Number Pills */}
        <div className="flex-1 flex flex-wrap items-center justify-center gap-1.5 px-1 overflow-x-auto py-1">
          {problems.map((prob, idx) => {
            const isSkipped = prob.state?.skipped === true;
            const hasScore = prob.state?.score !== null && prob.state?.score !== undefined;
            const isCorrect = hasScore && (prob.state?.score ?? 0) > 0 && !isSkipped;
            const isIncorrect = hasScore && (prob.state?.score ?? 0) === 0 && !isSkipped;
            const isActive = viewMode === "quiz" && currentIndex === idx;

            // Strict user color rule:
            // Correct = Green (สีเขียว)
            // Incorrect = Red (สีแดง)
            // Skipped = Gray (สีเทา)
            // Unattempted = Slate outline
            let colorCls = "bg-[#182032] text-slate-300 border-[#2b3752] hover:border-indigo-400/60 hover:text-white";
            let statusLabel = "Unanswered";

            if (isCorrect) {
              colorCls = "bg-emerald-500 hover:bg-emerald-400 text-slate-950 border-emerald-400 shadow-sm shadow-emerald-500/25";
              statusLabel = "Correct";
            } else if (isIncorrect) {
              colorCls = "bg-rose-500 hover:bg-rose-400 text-white border-rose-400 shadow-sm shadow-rose-500/25";
              statusLabel = "Incorrect";
            } else if (isSkipped) {
              colorCls = "bg-slate-500 hover:bg-slate-400 text-slate-100 border-slate-400 shadow-sm";
              statusLabel = "Skipped (Concept Gap)";
            }

            const activeRing = isActive
              ? "ring-2 ring-indigo-400 ring-offset-2 ring-offset-[#0d1017] scale-110 z-10 font-black"
              : "opacity-90 hover:opacity-100 font-semibold";

            return (
              <button
                key={prob.id}
                type="button"
                onClick={() => onSelectQuestion(idx)}
                title={`Q${idx + 1} (${prob.id}) — ${statusLabel}`}
                className={`relative w-8 h-8 rounded-lg border text-xs flex items-center justify-center font-mono transition-all transform ${colorCls} ${activeRing}`}
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
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#1b2336] hover:bg-[#232d44] disabled:opacity-40 disabled:hover:bg-[#1b2336] text-slate-200 border border-[#2b3852] transition-colors shadow-sm shrink-0"
        >
          <span className="hidden sm:inline">Next</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </nav>
  );
};
