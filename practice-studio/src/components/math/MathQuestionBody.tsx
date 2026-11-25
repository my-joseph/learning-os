"use client";

import React from "react";
import { FormattedText } from "@/components/FormattedText";
import { MathFigure } from "@/components/MathFigure";
import { LineChoicePrompt, ParsedLineChoicePrompt } from "@/components/LineChoicePrompt";
import { ChoiceResultStatus } from "@/lib/answerFeedback";
import { MathFigureSpec } from "@/types/figure";
import { VisualSpec } from "@/types/drill";

export interface MathQuestionBodyProps {
  header?: React.ReactNode;
  prompt: string;
  figure?: MathFigureSpec;
  visual?: VisualSpec;
  lineChoiceData: ParsedLineChoicePrompt | null;
  selectedValue: string;
  onSelectChoice: (optId: string) => void;
  choiceLocked: boolean;
  checkingOptionId: string | null;
  choiceResultStatus: ChoiceResultStatus;
}

/** Shared Math question prompt (or inline LineChoicePrompt) and optional full-width MathFigure. */
export const MathQuestionBody: React.FC<MathQuestionBodyProps> = ({
  header,
  prompt,
  figure,
  visual,
  lineChoiceData,
  selectedValue,
  onSelectChoice,
  choiceLocked,
  checkingOptionId,
  choiceResultStatus,
}) => {
  return (
    <>
      <div className="space-y-2">
        {header}

        <div className="min-w-0 text-base leading-relaxed text-foreground">
          {lineChoiceData ? (
            <LineChoicePrompt
              parsed={lineChoiceData}
              selectedValue={selectedValue}
              onSelect={onSelectChoice}
              disabled={choiceLocked}
              checkingOptionId={checkingOptionId}
              resultStatus={choiceResultStatus}
            />
          ) : (
            <FormattedText text={prompt} block />
          )}
        </div>
      </div>

      {(figure || visual) && (
        <div className="w-full">
          <MathFigure figure={figure || visual!} className="w-full" />
        </div>
      )}
    </>
  );
};
