import * as React from "react";
import { cn } from "@/lib/cn";

export const Skeleton = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("animate-pulse motion-reduce:animate-none rounded-md bg-zinc-200 dark:bg-zinc-800", className)}
      {...props}
    />
  )
);
Skeleton.displayName = "Skeleton";
