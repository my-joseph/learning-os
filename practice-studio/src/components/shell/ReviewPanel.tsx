"use client";

import React from "react";
import {
  ArrowLeft,
  ArrowUpRight,
  Check,
  ClipboardCheck,
  Flag,
  PenLine,
  RefreshCw,
  Send,
} from "lucide-react";
import { DrillDocument } from "@/types/drill";
import { canRevealVerifiedAnswer } from "@/lib/reviewGuard";
import { ExpandablePrompt } from "@/components/ExpandablePrompt";
import { FormattedText } from "@/components/FormattedText";

interface ReviewPanelProps {
  currentDrill: DrillDocument;
  liveScore: number;
  maxScore: number;
  accuracyPct: number;
  skippedCount: number;
  computedPracticeStatus: "Graded" | "Needs Retry";
  isSyncing: boolean;
  onStatusOverrideChange: (status: "Graded" | "Needs Retry") => void;
  onBackToQuiz: () => void;
  onConfirmSync: () => void;
  onSelectQuestion: (idx: number) => void;
  onSetScore: (probId: string, score: number | null) => void;
  onToggleMistakeTag: (probId: string, tagId: string) => void;
  onMistakeNoteChange: (probId: string, note: string) => void;
}

/** Pre-Sync review and edit panel for checking scores, mistake tags, and notes before syncing to Notion. */
export const ReviewPanel: React.FC<ReviewPanelProps> = ({
  currentDrill,
  liveScore,
  maxScore,
  accuracyPct,
  skippedCount,
  computedPracticeStatus,
  isSyncing,
  onStatusOverrideChange,
  onBackToQuiz,
  onConfirmSync,
  onSelectQuestion,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
}) => {
  return (
    <section className="bg-white dark:bg-[#151924] border border-slate-200 dark:border-[#2c354d] rounded-2xl p-5 md:p-6 shadow-sm space-y-5">
      {/* Review Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200 dark:border-[#2c354d]">
        <div>
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
            <ClipboardCheck className="w-4 h-4" />
            <span>Pre-Sync Verification &amp; Mistake Log Review</span>
          </div>
          <h1 className="text-lg md:text-xl font-bold text-slate-900 dark:text-white">
            Review &amp; Edit Session Before Notion Sync ({currentDrill.drillId})
          </h1>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={onBackToQuiz}
            className="inline-flex items-center gap-1.5 h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-slate-200 dark:hover:bg-[#25304a] text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-[#2c354d] text-xs md:text-sm font-semibold transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Questions</span>
          </button>

          <button
            type="button"
            onClick={onConfirmSync}
            disabled={isSyncing}
            className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white text-xs md:text-sm font-bold transition-colors shadow-sm"
          >
            {isSyncing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Syncing to Notion...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Confirm &amp; Sync to Notion</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Session Summary Overview Box */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 p-4 bg-slate-50 dark:bg-[#10141f] border border-slate-200 dark:border-[#2c354d] rounded-xl text-xs">
        <div>
          <span className="text-slate-600 dark:text-slate-400 block mb-1">
            Unit &amp; Drill ID
          </span>
          <strong className="text-sm text-slate-900 dark:text-white block">
            {currentDrill.unitTitle || currentDrill.unitCode}
          </strong>
          <span className="font-mono text-slate-600 dark:text-slate-400">
            {currentDrill.drillId} · {currentDrill.unitCode}
          </span>
        </div>

        <div>
          <span className="text-slate-600 dark:text-slate-400 block mb-1">
            Total Score &amp; Accuracy
          </span>
          <strong className="text-base text-emerald-600 dark:text-emerald-400 font-mono">
            {liveScore} / {maxScore} ({accuracyPct}%)
          </strong>
          <span className="block text-slate-600 dark:text-slate-400">
            Skipped: {skippedCount} questions
          </span>
        </div>

        <div>
          <span className="text-slate-600 dark:text-slate-400 block mb-1">
            Practice Status (Editable)
          </span>
          <div className="flex items-center gap-1.5 mt-1">
            {(["Graded", "Needs Retry"] as const).map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => onStatusOverrideChange(st)}
                className={`h-8 px-2.5 rounded-lg text-xs font-semibold border transition-colors ${
                  computedPracticeStatus === st
                    ? st === "Graded"
                      ? "bg-emerald-700 text-white border-emerald-700"
                      : "bg-amber-600 text-white border-amber-600"
                    : "bg-white dark:bg-[#1d2333] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-[#2c354d]"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        <div>
          <span className="text-slate-600 dark:text-slate-400 block mb-1">
            Target Notion Destination
          </span>
          <span className="text-slate-800 dark:text-slate-200 font-medium block">
            1. Learning Practice &amp; Drills DB
          </span>
          <span className="text-slate-600 dark:text-slate-400 block">
            2. Unit Page ({currentDrill.unitCode}) Log
          </span>
        </div>
      </div>

      {/* Editable Question-by-Question Review Table/Cards */}
      <div className="space-y-3">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
          Question-by-Question Breakdown (Click to adjust scores, Mistake Tags, or custom notes)
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 items-stretch">
          {currentDrill.problems.map((prob, idx) => {
            const pScore = prob.state.score;
            const isSkipped = Boolean(prob.state.skipped);
            const mistakeTags = currentDrill.mistakeTags || [];

            // Status-based soft background & border tint for rapid visual scanning
            let statusCardCls =
              "bg-slate-50/80 dark:bg-[#10141f] border-slate-200 dark:border-[#2c354d]";
            if (!isSkipped && pScore === 1) {
              statusCardCls =
                "bg-emerald-50/75 dark:bg-emerald-950/25 border-emerald-200 dark:border-emerald-500/35";
            } else if (!isSkipped && pScore === 0.5) {
              statusCardCls =
                "bg-amber-50/75 dark:bg-amber-950/25 border-amber-200 dark:border-amber-500/35";
            } else if (!isSkipped && pScore === 0) {
              statusCardCls =
                "bg-rose-50/75 dark:bg-rose-950/25 border-rose-200 dark:border-rose-500/35";
            }

            return (
              <div
                key={prob.id}
                className={`min-w-0 p-3.5 border rounded-xl flex flex-col justify-between gap-2.5 transition-colors ${statusCardCls}`}
              >
                <div className="min-w-0 space-y-2">
                  {/* Card Header: Question Link + Inline Score Selector */}
                  <div className="flex items-center justify-between gap-2">
                    <button
                      type="button"
                      onClick={() => onSelectQuestion(idx)}
                      className="inline-flex items-center gap-1 min-w-0 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline font-mono"
                    >
                      <span className="truncate">
                        Q{idx + 1} ({prob.id})
                      </span>
                      <ArrowUpRight className="w-3.5 h-3.5 shrink-0" />
                    </button>

                    {currentDrill.subject !== "PRG" && (
                      <div className="flex items-center gap-1 shrink-0">
                        {[
                          {
                            val: 1,
                            label: "1.0",
                            cls: "bg-emerald-600 text-white border-emerald-600",
                          },
                          {
                            val: 0.5,
                            label: "0.5",
                            cls: "bg-amber-600 text-white border-amber-600",
                          },
                          {
                            val: 0,
                            label: "0",
                            cls: "bg-rose-600 text-white border-rose-600",
                          },
                        ].map((btn) => (
                          <button
                            key={btn.val}
                            type="button"
                            onClick={() => onSetScore(prob.id, btn.val)}
                            className={`h-7 px-2 rounded-lg text-[11px] font-semibold border transition-colors ${
                              pScore === btn.val
                                ? btn.cls
                                : "bg-white/90 dark:bg-[#1d2333] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-[#2c354d]"
                            }`}
                          >
                            {btn.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Status Badges */}
                  {(isSkipped || typeof prob.state.divergedStep === "number") && (
                    <div className="flex flex-wrap items-center gap-1.5">
                      {isSkipped && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 font-medium">
                          Skipped
                        </span>
                      )}
                      {typeof prob.state.divergedStep === "number" && (
                        <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300 font-medium">
                          <Flag className="w-3 h-3" />
                          Diverged at Step {prob.state.divergedStep + 1}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Prompt Preview */}
                  <ExpandablePrompt
                    key={`${currentDrill.drillId}-${prob.id}`}
                    text={prob.prompt}
                  />

                  {/* Stacked Answer Comparison */}
                  <div className="space-y-1 pt-0.5 text-[11px] font-mono text-slate-600 dark:text-slate-400">
                    <div className="break-words">
                      <span>Your Answer: </span>
                      <strong className="text-slate-800 dark:text-slate-200">
                        {prob.state.userInput ||
                          (prob.state.lastTestReport
                            ? `${prob.state.lastTestReport.passedCount}/${prob.state.lastTestReport.totalCount} Tests Passed`
                            : "(Unanswered)")}
                      </strong>
                    </div>
                    <div className="break-words">
                      <span>Verified: </span>
                      {canRevealVerifiedAnswer(prob.state) ? (
                        <strong className="text-emerald-700 dark:text-emerald-400">
                          {prob.answerPlain || prob.answerDisplay}
                        </strong>
                      ) : (
                        <span className="italic text-slate-400 dark:text-slate-500">
                          Not answered yet
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Inline Mistake Tags & Custom Mistake Note */}
                <div className="mt-auto pt-2.5 border-t border-slate-200/70 dark:border-[#1f283d] space-y-2">
                  {mistakeTags.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1">
                      <span className="text-[11px] text-slate-600 dark:text-slate-400 mr-0.5">
                        Tags:
                      </span>
                      {mistakeTags.map((t) => {
                        const hasTag = prob.state.mistakes.includes(t.id);
                        return (
                          <button
                            key={t.id}
                            type="button"
                            onClick={() => onToggleMistakeTag(prob.id, t.id)}
                            className={`min-h-[24px] py-0.5 px-2.5 rounded-full text-[11px] font-medium border transition-colors inline-flex items-center ${
                              hasTag
                                ? "bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-500/50 font-semibold"
                                : "bg-white/90 dark:bg-[#1d2333] text-slate-600 dark:text-slate-400 border-slate-200 dark:border-[#2c354d]"
                            }`}
                          >
                            <FormattedText text={t.label} />
                          </button>
                        );
                      })}
                    </div>
                  )}

                  <div className="flex items-center gap-2 bg-white/90 dark:bg-[#151924] border border-slate-200 dark:border-[#2c354d] rounded-lg px-2.5 py-1.5">
                    <PenLine className="w-3.5 h-3.5 text-rose-500 dark:text-rose-400 shrink-0" />
                    <input
                      type="text"
                      value={prob.state.mistakeNote || ""}
                      onChange={(e) => onMistakeNoteChange(prob.id, e.target.value)}
                      placeholder={`Mistake note for Q${idx + 1}...`}
                      className="w-full min-w-0 bg-transparent text-xs text-slate-800 dark:text-slate-200 placeholder:text-slate-400 focus:outline-none"
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom Confirm Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-200 dark:border-[#2c354d]">
        <button
          type="button"
          onClick={onBackToQuiz}
          className="inline-flex items-center gap-1.5 h-10 px-4 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-slate-200 dark:hover:bg-[#25304a] text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-[#2c354d] text-sm font-semibold transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Practice</span>
        </button>

        <button
          type="button"
          onClick={onConfirmSync}
          disabled={isSyncing}
          className="inline-flex items-center gap-2 h-10 px-6 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white text-sm font-bold transition-colors shadow-sm"
        >
          {isSyncing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Syncing to Notion...</span>
            </>
          ) : (
            <>
              <Check className="w-4 h-4" />
              <span>
                Confirm &amp; Sync to Notion ({liveScore}/{maxScore} · {accuracyPct}%)
              </span>
            </>
          )}
        </button>
      </div>
    </section>
  );
};
