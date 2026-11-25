"use client";

import React from "react";
import { Check, Loader2, X } from "lucide-react";
import { m } from "motion/react";
import { FormattedText } from "@/components/FormattedText";
import { Badge } from "@/components/ui/shadcn/Badge";
import { Button } from "@/components/ui/shadcn/Button";
import { ChoiceResultStatus } from "@/lib/answerFeedback";
import { cn } from "@/lib/cn";
import { quick } from "@/lib/motion";
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
          ? "grid grid-cols-1 gap-space-2"
          : "flex flex-wrap gap-space-2 w-full"
      }
    >
      {options.map((opt) => {
        const isCheckingThis = checkingOptionId === opt.id;
        const isSelected = activeSelected === opt.id;
        const outcome = isSelected && !isCheckingThis ? resultStatus : null;
        const tone = outcome ? statusTone[outcome] : null;
        const OutcomeIcon = outcome === "wrong" ? X : Check;
        const buttonTone = tone
          ? cn(tone.choiceCard, "text-foreground")
          : isSelected
            ? "bg-surface-hover border-accent-field text-foreground"
            : "bg-surface-panel text-foreground-answer border-border hover:border-foreground-faint dark:hover:border-surface-hover-strong";
        const badgeTone = tone?.solidBadge ?? (isSelected
          ? "bg-accent-field text-accent-on-primary"
          : "bg-surface-raised text-muted border border-border");
        const disabledStyle = disabled && (isSelected ? "cursor-default" : "opacity-secondary cursor-not-allowed");

        return (
          <Button
            variant="choice"
            size={layout === "stack" ? "choiceStack" : "choiceWrap"}
            key={opt.id}
            type="button"
            role="radio"
            aria-checked={isSelected}
            disabled={disabled}
            aria-busy={isCheckingThis || undefined}
            onClick={() => onSelect(opt.id)}
            className={cn(buttonTone, disabledStyle)}
          >
            <div className="flex items-center gap-space-2_5 min-w-0 flex-1">
              <Badge variant="choice" className={badgeTone}>
                {opt.id}
              </Badge>
              <div className="min-w-0 flex-1 text-left text-xs sm:text-sm leading-relaxed">
                <FormattedText text={opt.label} />
              </div>
            </div>

            {(isCheckingThis || tone) && (
              <m.span
                key={outcome ?? "checking"}
                initial={isCheckingThis ? false : { opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={quick}
                className="inline-flex shrink-0 size-space-4 items-center justify-center"
              >
                {isCheckingThis ? (
                  <Loader2 className="size-space-3_5 animate-spin text-accent" aria-hidden="true" />
                ) : (
                  <OutcomeIcon className={cn("size-space-4 shrink-0", tone?.text)} aria-hidden="true" />
                )}
              </m.span>
            )}
          </Button>
        );
      })}
    </div>
  );
};
