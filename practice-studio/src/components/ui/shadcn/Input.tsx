import * as React from "react";
import { cn } from "@/lib/cn";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn("flex min-h-[44px] w-full min-w-0 rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-foreground shadow-sm placeholder:text-zinc-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:placeholder:text-zinc-400 dark:focus-visible:ring-indigo-400", className)}
      {...props}
    />
  )
);
Input.displayName = "Input";
