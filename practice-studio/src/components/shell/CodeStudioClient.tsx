"use client";

import React from "react";
import { CodeDashboard } from "@/components/code/CodeDashboard";
import { StudioClient, type StudioClientProps } from "./StudioClient";

/** Code/Lab-workspace entry wrapper for `StudioClient` so `/code/*` never bundles MathWorkspace. */
export const CodeStudioClient: React.FC<
  Omit<StudioClientProps, "MathWorkspaceComponent" | "CodeDashboardComponent">
> = (props) => <StudioClient {...props} CodeDashboardComponent={CodeDashboard} />;
