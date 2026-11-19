"use client";

import React from "react";
import { Check, Loader2, X } from "lucide-react";
import { FormattedText } from "./FormattedText";
import { ChoiceResultStatus } from "@/lib/answerFeedback";
import { ParsedLineChoicePrompt, parseLineChoicePrompt } from "@/lib/lineChoicePrompt";

export { parseLineChoicePrompt };
export type { ParsedLineChoiceItem, ParsedLineChoicePrompt } from "@/lib/lineChoicePrompt";

interface LineChoicePromptProps {
  parsed: ParsedLineChoicePrompt;
  selectedValue: string;
  onSelect: (optionId: string) => void;
  disabled?: boolean;
  checkingOptionId?: string | null;
  resultStatus?: ChoiceResultStatus;
}

export const LineChoicePrompt: React.FC<LineChoicePromptProps> = ({
  parsed,
  selectedValue,
  onSelect,
  disabled = false,
  checkingOptionId = null,
  resultStatus = null,
}) => {
  const activeSelected = checkingOptionId ?? selectedValue;

  return (
    <div className="space-y-3">
      {parsed.intro && (
        <div>
          <FormattedText text={parsed.intro} />
        </div>
      )}

      <div className="space-y-2" role="radiogroup" aria-label="Select a line">
        {parsed.items.map((item) => {
          const isCheckingThis = checkingOptionId === item.option.id;
          const isSelected = activeSelected === item.option.id;
          const isCorrectChosen =
            isSelected && !isCheckingThis && resultStatus === "correct";
          const isWrongChosen =
            isSelected && !isCheckingThis && resultStatus === "wrong";

          let rowCls =
            "bg-zinc-50 dark:bg-zinc-950 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600";
          let lineNumCls =
            "bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-800";
          let circleCls = "border border-zinc-300 dark:border-zinc-700";

          if (isCheckingThis) {
            rowCls =
              "bg-zinc-100 dark:bg-zinc-800/80 border-indigo-600 dark:border-indigo-500";
            lineNumCls = "bg-indigo-600 dark:bg-indigo-500 text-white";
            circleCls = "bg-indigo-600 dark:bg-indigo-500 text-white";
          } else if (isCorrectChosen) {
            rowCls =
              "bg-emerald-50 dark:bg-emerald-500/10 border-emerald-500/60 dark:border-emerald-500/50";
            lineNumCls = "bg-emerald-700 dark:bg-emerald-500 text-white";
            circleCls = "bg-emerald-700 dark:bg-emerald-500 text-white";
          } else if (isWrongChosen) {
            rowCls =
              "bg-rose-50 dark:bg-rose-500/10 border-rose-500/60 dark:border-rose-500/50";
            lineNumCls = "bg-rose-600 dark:bg-rose-500 text-white";
            circleCls = "bg-rose-600 dark:bg-rose-500 text-white";
          } else if (isSelected) {
            rowCls =
              "bg-zinc-100 dark:bg-zinc-800/80 border-indigo-600 dark:border-indigo-500";
            lineNumCls = "bg-indigo-600 dark:bg-indigo-500 text-white";
            circleCls = "bg-indigo-600 dark:bg-indigo-500 text-white";
          }

          const disabledCls =
            disabled && !isSelected && !isCheckingThis
              ? "opacity-60 cursor-not-allowed"
              : disabled
              ? "cursor-default"
              : "";

          return (
            <button
              key={item.option.id}
              type="button"
              role="radio"
              aria-checked={isSelected}
              disabled={disabled}
              onClick={() => onSelect(item.option.id)}
              className={`w-full text-left rounded-xl border px-3.5 py-2.5 transition-colors flex items-center justify-between gap-3 group ${rowCls} ${disabledCls}`}
            >
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <span
                  className={`shrink-0 inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-lg text-xs font-mono font-semibold transition-colors ${lineNumCls}`}
                >
                  {item.lineNumber}
                </span>

                <div className="min-w-0 flex-1 overflow-x-auto overflow-y-hidden text-sm text-zinc-900 dark:text-zinc-100 py-1">
                  <FormattedText text={item.content} />
                </div>
              </div>

              <span
                className={`shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full transition-colors ${circleCls}`}
              >
                {isCheckingThis ? (
                  <Loader2 className="w-3 h-3 animate-spin" aria-hidden="true" />
                ) : isWrongChosen ? (
                  <X className="w-3.5 h-3.5" aria-hidden="true" />
                ) : isSelected ? (
                  <Check className="w-3.5 h-3.5" aria-hidden="true" />
                ) : null}
              </span>
            </button>
          );
        })}
      </div>

      {parsed.outro && (
        <div>
          <FormattedText text={parsed.outro} />
        </div>
      )}
    </div>
  );
};
