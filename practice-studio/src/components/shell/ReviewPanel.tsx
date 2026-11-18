"use client";

import React from "react";
import {
  ArrowLeft,
  ArrowUpRight,
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
    <section className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-6">
      {/* Review Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div>
          <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Review &amp; Sync to Notion
          </h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            {currentDrill.unitTitle || currentDrill.unitCode} ·{" "}
            <span className="font-mono text-xs">{currentDrill.drillId}</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onBackToQuiz}
            className="inline-flex items-center gap-1.5 h-10 px-3.5 rounded-xl text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to problem</span>
          </button>

          <button
            type="button"
            onClick={onConfirmSync}
            disabled={isSyncing}
            className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-400 disabled:opacity-50 text-white text-xs font-semibold transition-colors"
          >
            {isSyncing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Syncing…</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Sync to Notion</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Session Summary Overview Box */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-xs">
        <div>
          <span className="text-xs text-zinc-500 dark:text-zinc-400 block mb-0.5">
            Score
          </span>
          <strong className="text-sm font-mono font-semibold text-zinc-900 dark:text-zinc-100">
            {liveScore} / {maxScore} ({accuracyPct}%)
          </strong>
          {skippedCount > 0 && (
            <span className="block text-xs text-zinc-500 dark:text-zinc-400">
              {skippedCount} skipped
            </span>
          )}
        </div>

        <div>
          <span className="text-xs text-zinc-500 dark:text-zinc-400 block mb-1">
            Practice status
          </span>
          <div className="flex items-center gap-1.5">
            {(["Graded", "Needs Retry"] as const).map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => onStatusOverrideChange(st)}
                className={`h-8 px-2.5 rounded-lg text-xs font-medium border transition-colors ${
                  computedPracticeStatus === st
                    ? st === "Graded"
                      ? "border-emerald-700 dark:border-emerald-400 text-emerald-700 dark:text-emerald-400 bg-zinc-100 dark:bg-zinc-900 font-semibold"
                      : "border-amber-600 dark:border-amber-400 text-amber-600 dark:text-amber-400 bg-zinc-100 dark:bg-zinc-900 font-semibold"
                    : "bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        <div>
          <span className="text-xs text-zinc-500 dark:text-zinc-400 block mb-0.5">
            Destination
          </span>
          <span className="text-xs text-zinc-700 dark:text-zinc-300 block">
            Practice &amp; Drills DB + {currentDrill.unitCode}
          </span>
        </div>
      </div>

      {/* Editable Question-by-Question Review Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 items-stretch">
        {currentDrill.problems.map((prob, idx) => {
          const pScore = prob.state.score;
          const isSkipped = Boolean(prob.state.skipped);
          const mistakeTags = currentDrill.mistakeTags || [];

          let statusBorderCls = "border-zinc-200 dark:border-zinc-800";
          if (!isSkipped && pScore === 1) {
            statusBorderCls =
              "border-zinc-200 dark:border-zinc-800 border-l-4 border-l-emerald-700 dark:border-l-emerald-400";
          } else if (!isSkipped && pScore === 0.5) {
            statusBorderCls =
              "border-zinc-200 dark:border-zinc-800 border-l-4 border-l-amber-600 dark:border-l-amber-400";
          } else if (!isSkipped && pScore === 0) {
            statusBorderCls =
              "border-zinc-200 dark:border-zinc-800 border-l-4 border-l-rose-600 dark:border-l-rose-400";
          }

          return (
            <div
              key={prob.id}
              className={`min-w-0 p-4 bg-zinc-50/70 dark:bg-zinc-950/60 border rounded-xl flex flex-col justify-between gap-3 ${statusBorderCls}`}
            >
              <div className="min-w-0 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => onSelectQuestion(idx)}
                    className="inline-flex items-center gap-1 min-w-0 text-xs font-semibold text-zinc-900 dark:text-zinc-100 hover:text-indigo-600 dark:hover:text-indigo-400 font-mono"
                  >
                    <span className="truncate">Question {idx + 1}</span>
                    <ArrowUpRight className="w-3.5 h-3.5 shrink-0" />
                  </button>

                  {currentDrill.subject !== "PRG" && (
                    <div className="flex items-center gap-1 shrink-0">
                      {[
                        {
                          val: 1,
                          label: "1.0",
                          cls: "border-emerald-700 dark:border-emerald-400 text-emerald-700 dark:text-emerald-400 font-semibold",
                        },
                        {
                          val: 0.5,
                          label: "0.5",
                          cls: "border-amber-600 dark:border-amber-400 text-amber-600 dark:text-amber-400 font-semibold",
                        },
                        {
                          val: 0,
                          label: "0",
                          cls: "border-rose-600 dark:border-rose-400 text-rose-600 dark:text-rose-400 font-semibold",
                        },
                      ].map((btn) => (
                        <button
                          key={btn.val}
                          type="button"
                          onClick={() => onSetScore(prob.id, btn.val)}
                          className={`h-7 px-2 rounded-md text-xs font-mono border transition-colors ${
                            pScore === btn.val
                              ? `${btn.cls} bg-white dark:bg-zinc-900`
                              : "bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800"
                          }`}
                        >
                          {btn.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {(isSkipped || typeof prob.state.divergedStep === "number") && (
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    {isSkipped && (
                      <span className="text-amber-600 dark:text-amber-400 font-medium">
                        Skipped
                      </span>
                    )}
                    {typeof prob.state.divergedStep === "number" && (
                      <span className="inline-flex items-center gap-1 text-rose-600 dark:text-rose-400 font-medium">
                        <Flag className="w-3 h-3" />
                        Diverged at step {prob.state.divergedStep + 1}
                      </span>
                    )}
                  </div>
                )}

                <ExpandablePrompt
                  key={`${currentDrill.drillId}-${prob.id}`}
                  text={prob.prompt}
                />

                <div className="space-y-1 pt-0.5 text-xs font-mono text-zinc-500 dark:text-zinc-400">
                  <div className="break-words">
                    <span>Your answer: </span>
                    <strong className="text-zinc-800 dark:text-zinc-200">
                      {prob.state.userInput ||
                        (prob.state.lastTestReport
                          ? `${prob.state.lastTestReport.passedCount}/${prob.state.lastTestReport.totalCount} tests passed`
                          : "Unanswered")}
                    </strong>
                  </div>
                  <div className="break-words">
                    <span>Verified: </span>
                    {canRevealVerifiedAnswer(prob.state) ? (
                      <strong className="text-emerald-700 dark:text-emerald-400">
                        {prob.answerPlain || prob.answerDisplay}
                      </strong>
                    ) : (
                      <span className="italic text-zinc-400 dark:text-zinc-500">
                        Not answered yet
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-auto pt-2.5 border-t border-zinc-200 dark:border-zinc-800 space-y-2">
                {mistakeTags.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1">
                    {mistakeTags.map((t) => {
                      const hasTag = prob.state.mistakes.includes(t.id);
                      return (
                        <button
                          key={t.id}
                          type="button"
                          onClick={() => onToggleMistakeTag(prob.id, t.id)}
                          className={`min-h-[24px] py-0.5 px-2.5 rounded-full text-xs font-medium border transition-colors inline-flex items-center ${
                            hasTag
                              ? "border-rose-600 dark:border-rose-400 text-rose-700 dark:text-rose-300 bg-white dark:bg-zinc-900 font-semibold"
                              : "bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800"
                          }`}
                        >
                          <FormattedText text={t.label} />
                        </button>
                      );
                    })}
                  </div>
                )}

                <div className="flex items-center gap-2 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-1.5">
                  <PenLine className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                  <input
                    type="text"
                    value={prob.state.mistakeNote || ""}
                    onChange={(e) => onMistakeNoteChange(prob.id, e.target.value)}
                    placeholder={`Note for question ${idx + 1}…`}
                    className="w-full min-w-0 bg-transparent text-xs text-zinc-800 dark:text-zinc-200 placeholder:text-zinc-400 focus:outline-none"
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
