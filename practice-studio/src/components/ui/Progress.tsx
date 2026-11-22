"use client";

import * as ProgressPrimitive from "@radix-ui/react-progress";
import React from "react";

export interface ProgressProps
  extends Omit<React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>, "value" | "max" | "aria-label"> {
  value: number;
  "aria-label": string;
}

export const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ value, className = "", ...props }, ref) => {
  const clamped = Math.min(100, Math.max(0, Number.isFinite(value) ? value : 0));

  return (
    <ProgressPrimitive.Root
      ref={ref}
      value={clamped}
      max={100}
      className={`h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800 ${className}`.trim()}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className="h-full w-full bg-indigo-600 dark:bg-indigo-400 transition-transform duration-300 ease-out"
        style={{ transform: `translateX(-${100 - clamped}%)` }}
      />
    </ProgressPrimitive.Root>
  );
});

Progress.displayName = "Progress";
