"use client";

import React from "react";
import { Check } from "lucide-react";
import { FormattedText } from "./FormattedText";
import { ParsedLineChoicePrompt, parseLineChoicePrompt } from "@/lib/lineChoicePrompt";

export { parseLineChoicePrompt };
export type { ParsedLineChoiceItem, ParsedLineChoicePrompt } from "@/lib/lineChoicePrompt";

interface LineChoicePromptProps {
  parsed: ParsedLineChoicePrompt;
  selectedValue: string;
  onSelect: (optionId: string) => void;
}

export const LineChoicePrompt: React.FC<LineChoicePromptProps> = ({
  parsed,
  selectedValue,
  onSelect,
}) => {
  return (
    <div className="space-y-3">
      {parsed.intro && (
        <div>
          <FormattedText text={parsed.intro} />
        </div>
      )}

      <div className="space-y-2" role="radiogroup" aria-label="Select a line">
        {parsed.items.map((item) => {
          const isSelected = selectedValue === item.option.id;
          return (
            <button
              key={item.option.id}
              type="button"
              role="radio"
              aria-checked={isSelected}
              onClick={() => onSelect(item.option.id)}
              className={`w-full text-left rounded-xl border px-3.5 py-2.5 transition-colors flex items-center justify-between gap-3 group ${
                isSelected
                  ? "bg-zinc-100 dark:bg-zinc-800/80 border-indigo-600 dark:border-indigo-500"
                  : "bg-zinc-50 dark:bg-zinc-950 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600"
              }`}
            >
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <span
                  className={`shrink-0 inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-lg text-xs font-mono font-semibold transition-colors ${
                    isSelected
                      ? "bg-indigo-600 dark:bg-indigo-500 text-white"
                      : "bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-800"
                  }`}
                >
                  {item.lineNumber}
                </span>

                <div className="min-w-0 flex-1 overflow-x-auto text-base text-zinc-900 dark:text-zinc-100 py-0.5">
                  <FormattedText text={item.content} />
                </div>
              </div>

              <span
                className={`shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full transition-colors ${
                  isSelected
                    ? "bg-indigo-600 dark:bg-indigo-500 text-white"
                    : "border border-zinc-300 dark:border-zinc-700"
                }`}
              >
                {isSelected && <Check className="w-3.5 h-3.5" />}
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
