import React, { type ComponentPropsWithoutRef } from "react";
import { cn } from "@/lib/cn";

interface HeadingProps extends ComponentPropsWithoutRef<"h1"> {
  variant?: "page" | "section";
}

/** Page or section title in Roboto Slab. Curriculum IDs are not shown above titles (learner 2026-11-25: copy them from the row menu). */
export function Heading({ variant = "page", className, children, ...props }: HeadingProps) {
  const Tag = variant === "page" ? "h1" : "h2";
  return (
    <Tag
      {...props}
      className={cn(
        "font-heading text-lg tracking-heading text-foreground",
        variant === "page" ? "font-semibold" : "font-heading-medium",
        className,
      )}
    >
      {children}
    </Tag>
  );
}
