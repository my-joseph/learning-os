import React, { type ComponentPropsWithoutRef } from "react";
import { cn } from "@/lib/cn";

interface HeadingProps extends ComponentPropsWithoutRef<"h1"> {
  variant?: "page" | "section";
  eyebrow?: string;
}

export function Heading({ variant = "page", eyebrow, className, children, ...props }: HeadingProps) {
  const Tag = variant === "page" ? "h1" : "h2";
  const heading = (
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

  return eyebrow ? (
    <div className="min-w-0">
      <p className="font-mono text-2xs font-normal leading-snug text-muted">{eyebrow}</p>
      {heading}
    </div>
  ) : heading;
}
