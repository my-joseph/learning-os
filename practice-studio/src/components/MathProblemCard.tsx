"use client";

import React from "react";
import { MathWorkspace, MathWorkspaceProps } from "./math/MathWorkspace";

export type MathProblemCardProps = MathWorkspaceProps;

/** Wrapper delegating Math problem rendering to MathWorkspace. */
export const MathProblemCard: React.FC<MathProblemCardProps> = (props) => {
  return <MathWorkspace {...props} />;
};
