import React, { type ComponentPropsWithoutRef } from "react";
import { cn } from "@/lib/cn";

interface NumeralProps extends ComponentPropsWithoutRef<"span"> {
  variant?: "sm" | "lg";
}

export function Numeral({ variant = "sm", className, ...props }: NumeralProps) {
  return (
    <span
      {...props}
      className={cn(
        variant === "lg" ? "font-heading text-sm font-semibold tracking-heading" : "font-sans",
        "tabular-nums",
        className,
      )}
    />
  );
}
