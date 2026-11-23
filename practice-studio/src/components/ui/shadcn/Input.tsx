import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

export const inputVariants = cva(
  "w-full min-w-0 transition-colors motion-reduce:transition-none disabled:cursor-not-allowed disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "flex min-h-[44px] rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-foreground shadow-sm placeholder:text-zinc-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:border-zinc-700 dark:bg-zinc-900 dark:placeholder:text-zinc-400 dark:focus-visible:ring-indigo-400",
        embedded:
          "bg-transparent text-zinc-800 placeholder:text-zinc-500 focus-visible:outline-none dark:text-zinc-200 dark:placeholder:text-zinc-400",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement>,
    VariantProps<typeof inputVariants> {}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant, type = "text", ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      {...props}
      className={cn(inputVariants({ variant }), className)}
    />
  )
);
Input.displayName = "Input";
