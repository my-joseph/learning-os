"use client";

import React from "react";
import { MathWorkspace } from "@/components/math/MathWorkspace";
import { StudioClient, type StudioClientProps } from "./StudioClient";

/** Math-workspace entry wrapper for `StudioClient` so `/math/*` never bundles CodeDashboard. */
export const MathStudioClient: React.FC<
  Omit<StudioClientProps, "MathWorkspaceComponent" | "CodeDashboardComponent">
> = (props) => <StudioClient {...props} MathWorkspaceComponent={MathWorkspace} />;
