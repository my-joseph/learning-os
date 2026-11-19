"use client";

import React from "react";
import { PenLine } from "lucide-react";
import { FormattedText } from "@/components/FormattedText";
import { MistakeTag } from "@/types/drill";

export interface ProblemSelfEvalProps {
  hasAttempt: boolean;
  showSelfScore?: boolean;
  score: number | null;
  mistakes: string[];
  mistakeNote?: string;
  mistakeTags: MistakeTag[];
  noteAriaLabel: string;
  onSetScore: (score: number | null) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
}

const SELF_SCORE_BUTTONS = [
  {
    val: 1,
    label: "1.0",
    activeCls:
      "border-emerald-700 dark:border-emerald-400 text-emerald-700 dark:text-emerald-400 font-semibold bg-zinc-50 dark:bg-zinc-950",
  },
  {
    val: 0.5,
    label: "0.5",
    activeCls:
      "border-amber-700 dark:border-amber-400 text-amber-700 dark:text-amber-400 font-semibold bg-zinc-50 dark:bg-zinc-950",
  },
  {
    val: 0,
    label: "0",
    activeCls:
      "border-rose-600 dark:border-rose-400 text-rose-600 dark:text-rose-400 font-semibold bg-zinc-50 dark:bg-zinc-950",
  },
] as const;

/** Shared self-score buttons, mistake tag chips, and mistake note input shown after an attempt. */
export const ProblemSelfEval: React.FC<ProblemSelfEvalProps> = ({
  hasAttempt,
  showSelfScore = true,
  score,
  mistakes,
  mistakeNote,
  mistakeTags,
  noteAriaLabel,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
}) => {
  if (!hasAttempt) {
    return null;
  }

  return (
    <div className="pt-4 border-t border-zinc-200 dark:border-zinc-800 space-y-3 text-xs text-zinc-500 dark:text-zinc-400">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {showSelfScore && (
          <div className="flex items-center gap-1.5">
            <span className="mr-1">Self-score:</span>
            {SELF_SCORE_BUTTONS.map((btn) => (
              <button
                key={btn.val}
                type="button"
                onClick={() => onSetScore(btn.val)}
                aria-pressed={score === btn.val}
                className={`min-h-[44px] sm:min-h-[28px] px-3 sm:px-2.5 rounded-lg font-display tabular-nums border transition-colors ${
                  score === btn.val
                    ? btn.activeCls
                    : "bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600"
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>
        )}

        {mistakeTags.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1">Mistake:</span>
            {mistakeTags.map((t) => {
              const hasTag = mistakes.includes(t.id);
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => onToggleMistakeTag(t.id)}
                  aria-pressed={hasTag}
                  className={`min-h-[44px] sm:min-h-[28px] py-1 px-2.5 rounded-full text-xs border transition-colors inline-flex items-center ${
                    hasTag
                      ? "border-rose-600 dark:border-rose-400 text-rose-700 dark:text-rose-300 bg-zinc-50 dark:bg-zinc-950 font-semibold"
                      : "bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600"
                  }`}
                >
                  <FormattedText text={t.label} />
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-3 py-2 transition-colors focus-within:border-indigo-600 dark:focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-600/20 dark:focus-within:ring-indigo-400/25">
        <PenLine className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400 shrink-0" />
        <input
          type="text"
          value={mistakeNote || ""}
          onChange={(e) => onMistakeNoteChange(e.target.value)}
          aria-label={noteAriaLabel}
          placeholder="Note what went wrong (optional)…"
          className="w-full bg-transparent text-xs text-zinc-800 dark:text-zinc-200 placeholder:text-zinc-500 dark:placeholder:text-zinc-400 focus:outline-none"
        />
      </div>
    </div>
  );
};
