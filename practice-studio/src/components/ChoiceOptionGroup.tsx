"use client";

import React from "react";
import { Check, Loader2, X } from "lucide-react";
import { m } from "motion/react";
import { FormattedText } from "@/components/FormattedText";
import { ChoiceResultStatus } from "@/lib/answerFeedback";
import { choiceTapPress, quick } from "@/lib/motion";
import { statusTone } from "@/lib/statusTone";
import { ChoiceOption } from "@/types/drill";

export interface ChoiceOptionGroupProps {
  options: ChoiceOption[];
  selectedValue: string;
  onSelect: (optionId: string) => void;
  disabled?: boolean;
  checkingOptionId?: string | null;
  resultStatus?: ChoiceResultStatus;
  layout?: "wrap" | "stack";
  ariaLabel?: string;
}

/** Shared multiple-choice selector that auto-submits on click with checking and result states. */
export const ChoiceOptionGroup: React.FC<ChoiceOptionGroupProps> = ({
  options,
  selectedValue,
  onSelect,
  disabled = false,
  checkingOptionId = null,
  resultStatus = null,
  layout = "wrap",
  ariaLabel = "Select an option",
}) => {
  const activeSelected = checkingOptionId ?? selectedValue;

  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className={
        layout === "stack"
          ? "grid grid-cols-1 gap-2"
          : "flex flex-wrap gap-2 w-full"
      }
    >
      {options.map((opt) => {
        const isCheckingThis = checkingOptionId === opt.id;
        const isSelected = activeSelected === opt.id;
        const isCorrectChosen = isSelected && !isCheckingThis && resultStatus === "correct";
        const isAssistedChosen = isSelected && !isCheckingThis && resultStatus === "assisted";
        const isWrongChosen = isSelected && !isCheckingThis && resultStatus === "wrong";

        let buttonCls =
          "bg-zinc-50 dark:bg-zinc-950 text-zinc-800 dark:text-zinc-200 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600";
        let badgeCls =
          "bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-800";

        if (isCheckingThis) {
          buttonCls =
            "bg-zinc-100 dark:bg-zinc-800 border-indigo-600 dark:border-indigo-500 text-zinc-900 dark:text-zinc-100";
          badgeCls = "bg-indigo-600 dark:bg-indigo-500 text-white";
        } else if (isCorrectChosen) {
          buttonCls = `${statusTone.correct.choiceCard} text-zinc-900 dark:text-zinc-100`;
          badgeCls = statusTone.correct.solidBadge;
        } else if (isAssistedChosen) {
          buttonCls = `${statusTone.assisted.choiceCard} text-zinc-900 dark:text-zinc-100`;
          badgeCls = statusTone.assisted.solidBadge;
        } else if (isWrongChosen) {
          buttonCls = `${statusTone.wrong.choiceCard} text-zinc-900 dark:text-zinc-100`;
          badgeCls = statusTone.wrong.solidBadge;
        } else if (isSelected) {
          buttonCls =
            "bg-zinc-100 dark:bg-zinc-800 border-indigo-600 dark:border-indigo-500 text-zinc-900 dark:text-zinc-100";
          badgeCls = "bg-indigo-600 dark:bg-indigo-500 text-white";
        }

        const disabledCls =
          disabled && !isSelected && !isCheckingThis
            ? "opacity-60 cursor-not-allowed"
            : disabled
            ? "cursor-default"
            : "";

        return (
          <m.button
            key={opt.id}
            type="button"
            role="radio"
            aria-checked={isSelected}
            disabled={disabled}
            whileTap={disabled ? undefined : choiceTapPress}
            transition={quick}
            onClick={() => onSelect(opt.id)}
            className={
              layout === "stack"
                ? `w-full text-left p-3.5 rounded-xl border transition-colors flex items-center justify-between gap-3 ${buttonCls} ${disabledCls}`
                : `min-h-[40px] px-3.5 py-2 rounded-xl border text-xs font-medium transition-colors flex items-center gap-2 ${buttonCls} ${disabledCls}`
            }
          >
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <span
                className={`inline-flex items-center justify-center w-6 h-6 rounded-md text-xs font-display font-semibold shrink-0 transition-colors ${badgeCls}`}
              >
                {opt.id}
              </span>
              <div className="min-w-0 flex-1 text-left text-xs sm:text-sm leading-relaxed">
                <FormattedText text={opt.label} />
              </div>
            </div>

            {isCheckingThis && (
              <Loader2
                className="w-3.5 h-3.5 animate-spin text-indigo-600 dark:text-indigo-400 shrink-0"
                aria-hidden="true"
              />
            )}
            {isCorrectChosen && (
              <m.span
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={quick}
                className="inline-flex shrink-0"
              >
                <Check
                  className={`w-4 h-4 ${statusTone.correct.text} shrink-0`}
                  aria-hidden="true"
                />
              </m.span>
            )}
            {isAssistedChosen && (
              <m.span
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={quick}
                className="inline-flex shrink-0"
              >
                <Check
                  className={`w-4 h-4 ${statusTone.assisted.text} shrink-0`}
                  aria-hidden="true"
                />
              </m.span>
            )}
            {isWrongChosen && (
              <m.span
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={quick}
                className="inline-flex shrink-0"
              >
                <X
                  className={`w-4 h-4 ${statusTone.wrong.text} shrink-0`}
                  aria-hidden="true"
                />
              </m.span>
            )}
          </m.button>
        );
      })}
    </div>
  );
};
