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
  const selectedItem = parsed.items.find((it) => it.option.id === selectedValue);

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
              className={`w-full text-left rounded-xl border px-3.5 py-2.5 transition-all flex items-center justify-between gap-3 group ${
                isSelected
                  ? "bg-indigo-50/95 dark:bg-indigo-500/15 border-indigo-500 dark:border-indigo-400 ring-2 ring-indigo-500/20 shadow-sm"
                  : "bg-slate-50/80 dark:bg-[#10141f] border-slate-200 dark:border-[#2c354d] hover:border-indigo-400 dark:hover:border-indigo-500/60 hover:bg-indigo-50/40 dark:hover:bg-indigo-500/10"
              }`}
            >
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <span
                  className={`shrink-0 inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-lg text-xs font-mono font-bold transition-colors ${
                    isSelected
                      ? "bg-indigo-600 text-white"
                      : "bg-white dark:bg-[#1d2333] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-[#2c354d] group-hover:border-indigo-300 dark:group-hover:border-indigo-500/50"
                  }`}
                >
                  {item.lineNumber}
                </span>

                <div className="min-w-0 flex-1 overflow-x-auto text-slate-900 dark:text-slate-100 py-0.5">
                  <FormattedText text={item.content} />
                </div>
              </div>

              <span
                className={`shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full transition-colors ${
                  isSelected
                    ? "bg-indigo-600 text-white"
                    : "border-2 border-slate-300 dark:border-slate-600 group-hover:border-indigo-400"
                }`}
              >
                {isSelected && <Check className="w-3.5 h-3.5" />}
              </span>
            </button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        {parsed.outro && (
          <div>
            <FormattedText text={parsed.outro} />
          </div>
        )}
        <span
          className={`text-xs font-medium ${
            selectedItem
              ? "text-indigo-600 dark:text-indigo-400"
              : "text-slate-600 dark:text-slate-400"
          }`}
        >
          {selectedItem ? `Selected: ${selectedItem.lineNumber}` : "Click a line above to select"}
        </span>
      </div>
    </div>
  );
};
