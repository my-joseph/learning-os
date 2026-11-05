"use client";

import React from "react";
import { Problem, MistakeTag } from "@/types/drill";
import { CodeProblemCard } from "./CodeProblemCard";
import { MathProblemCard } from "./MathProblemCard";

interface ProblemCardProps {
  problem: Problem;
  index: number;
  subject?: "MATH" | "PRG";
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  onInputChange: (val: string) => void;
  onCheckAnswer: () => void;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onResetProblem: () => void;
}

export const ProblemCard: React.FC<ProblemCardProps> = (props) => {
  const isCode =
    props.subject === "PRG" ||
    Boolean(props.problem.codeSnippet) ||
    props.problem.codeType === "predict-output" ||
    props.problem.codeType === "find-bug";

  if (isCode) {
    return <CodeProblemCard {...props} />;
  }

  return <MathProblemCard {...props} />;
};
