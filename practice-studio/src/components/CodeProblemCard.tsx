"use client";

import React from "react";
import { CodeDashboard, CodeDashboardProps } from "./code/CodeDashboard";

export type CodeProblemCardProps = CodeDashboardProps;

/** Wrapper delegating Programming problem rendering to CodeDashboard. */
export const CodeProblemCard: React.FC<CodeProblemCardProps> = (props) => {
  return <CodeDashboard {...props} />;
};
