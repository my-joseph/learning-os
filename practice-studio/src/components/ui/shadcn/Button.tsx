import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { DESTRUCTIVE_BUTTON_CLS } from "@/lib/statusTone";

export const buttonVariants = cva(
  "inline-flex min-h-[44px] items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-2 focus-visible:ring-offset-background dark:focus-visible:ring-indigo-400 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-indigo-600 text-white hover:bg-indigo-700 dark:bg-indigo-600 dark:text-white dark:hover:bg-indigo-500",
        secondary: "bg-zinc-200 text-zinc-900 hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-100 dark:hover:bg-zinc-700",
        outline: "border border-zinc-300 bg-transparent text-foreground hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800",
        ghost: "bg-transparent text-foreground hover:bg-zinc-100 dark:hover:bg-zinc-800",
        destructive: DESTRUCTIVE_BUTTON_CLS,
      },
      size: {
        default: "min-w-[44px]",
        sm: "min-w-[44px] px-3 text-xs",
        compact: "min-h-[44px] min-w-[44px] px-3 sm:min-h-[32px] sm:min-w-0 sm:px-2.5 py-1.5 sm:py-1 text-xs",
        lg: "min-h-[48px] min-w-[48px] px-6",
        icon: "min-w-[44px] px-2",
        iconSm: "min-h-[44px] min-w-[44px] p-0 sm:min-h-[36px] sm:min-w-[36px]",
      },
    },
    defaultVariants: { variant: "primary", size: "default" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, type, ...props }, ref) => {
    const Component = asChild ? Slot : "button";
    return (
      <Component
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        type={type ?? (!asChild ? "button" : undefined)}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
