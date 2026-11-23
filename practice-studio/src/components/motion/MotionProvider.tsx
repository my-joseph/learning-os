"use client";

import React from "react";
import { LazyMotion, MotionConfig, domAnimation } from "motion/react";
import { TooltipProvider } from "@/components/ui/shadcn/Tooltip";

/** Loads only the DOM animation features, honours the OS "reduce motion" setting, and provides global Tooltip context. */
export function MotionProvider({ children }: { children: React.ReactNode }) {
  return (
    <LazyMotion features={domAnimation} strict>
      <MotionConfig reducedMotion="user">
        <TooltipProvider delayDuration={300}>{children}</TooltipProvider>
      </MotionConfig>
    </LazyMotion>
  );
}
