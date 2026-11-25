"use client";

import React from "react";
import { Flag } from "lucide-react";
import { Button } from "@/components/ui/shadcn/Button";
import { Card } from "@/components/ui/shadcn/Card";
import { Step } from "@/types/drill";
import { statusTone } from "@/lib/statusTone";
import { MathBlock } from "./MathRender";
import { FormattedText } from "./FormattedText";

interface StepRowProps {
  step: Step;
  index: number;
  isDiverged?: boolean;
  onMarkDiverged?: () => void;
}

export const StepRow: React.FC<StepRowProps> = ({
  step,
  index,
  isDiverged = false,
  onMarkDiverged,
}) => {
  const hasLatex = Boolean(step.latex && step.latex.trim());
  return (
    // Hover focuses a step; other rows dim via globals.css.
    <Card
      variant="assistStep"
      data-latex={hasLatex || undefined}
      data-action={Boolean(onMarkDiverged) || undefined}
      className={`group step-row ${isDiverged ? "step-row-active" : ""} grid grid-cols-1 items-center gap-space-3 mb-space-2 last:mb-0 transition-opacity duration-color ${
        isDiverged
          ? statusTone.wrong.borderSoft
          : "hover:border-border-control"
      }`}
    >
      {hasLatex && (
        <div className="min-w-0 overflow-x-auto overflow-y-hidden scrollbar-hidden text-left text-sm text-foreground">
          <MathBlock latex={step.latex!} />
        </div>
      )}

      <div
        className={`text-xs ${hasLatex ? "border-l pl-space-3" : ""} transition-colors ${
          isDiverged
            ? `${statusTone.wrong.border} text-foreground`
            : "border-border text-foreground-subtle dark:text-foreground-control group-hover:border-accent group-hover:text-foreground dark:group-hover:text-foreground"
        }`}
      >
        <span className="font-display tabular-nums font-medium text-muted mr-space-1_5">
          Step {index + 1}:
        </span>
        <FormattedText text={step.explain} />
      </div>

      {onMarkDiverged && (
        <div className="flex justify-end">
          <Button
            variant="assistFlag"
            size="assistFlag"
            onClick={(e) => {
              e.stopPropagation();
              onMarkDiverged();
            }}
            className={
              isDiverged
                ? `opacity-visible ${statusTone.wrong.border} ${statusTone.wrong.text} bg-surface-panel`
                : `opacity-hidden group-hover:opacity-visible group-focus-within:opacity-visible focus:opacity-visible border-border text-muted ${statusTone.wrong.hoverText} ${statusTone.wrong.hoverBorderSoft}`
            }
          >
            <Flag className="size-space-3_5 shrink-0" />
            <span>{isDiverged ? `Diverged at step ${index + 1}` : "Diverged here"}</span>
          </Button>
        </div>
      )}
    </Card>
  );
};
