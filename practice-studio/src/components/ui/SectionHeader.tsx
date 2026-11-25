"use client";

import React, { type ButtonHTMLAttributes } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/cn";

interface SectionHeaderProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  expanded: boolean;
  controls: string;
}

export function SectionHeader({ expanded, controls, className, children, ...props }: SectionHeaderProps) {
  return (
    <button
      {...props}
      type="button"
      aria-expanded={expanded}
      aria-controls={controls}
      className={cn(
        "flex min-h-touch w-full items-center gap-space-1 rounded-md px-space-1_5 text-left text-xs font-medium text-muted transition-colors hover:text-foreground-section-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-muted motion-reduce:transition-none lg:min-h-0 lg:py-space-1",
        className
      )}
    >
      <span>{children}</span>
      <ChevronRight
        className={cn(
          "size-space-3_5 shrink-0 text-foreground-faint transition-transform duration-color motion-reduce:transition-none",
          expanded && "rotate-90"
        )}
        aria-hidden="true"
      />
    </button>
  );
}
