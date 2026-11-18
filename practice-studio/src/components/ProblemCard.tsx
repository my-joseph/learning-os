"use client";

import React from "react";
import { Problem, MistakeTag } from "@/types/drill";
import { CodeProblemCard } from "./CodeProblemCard";
import { MathProblemCard } from "./MathProblemCard";

interface ProblemCardProps {
  problem: Problem;
  drillId?: string;
  index: number;
  subject?: "MATH" | "PRG";
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  onInputChange: (val: string) => void;
  onCheckAnswer: (inputOverride?: string) => Promise<void> | void;
  onSkip?: () => void;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number | null) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
  onResetProblem: () => void;
  onHintRevealed?: () => void;
  onSetupRevealed?: () => void;
  onSolutionRevealed?: () => void;
}

export const ProblemCard: React.FC<ProblemCardProps> = (props) => {
  const isCode =
    props.subject === "PRG" ||
    Boolean(props.problem.codeSnippet) ||
    Boolean(props.problem.workspaceFile) ||
    props.problem.codeType === "predict-output" ||
    props.problem.codeType === "find-bug";

  if (isCode) {
    return <CodeProblemCard {...props} />;
  }

  return <MathProblemCard {...props} />;
};
