import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { statusTone } from "@/lib/statusTone";

const standardBadge = "inline-flex shrink-0 items-center justify-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium [&>svg]:pointer-events-none [&>svg]:size-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400";

export const badgeVariants = cva(
  "",
  {
    variants: {
      variant: {
        default: `${standardBadge} bg-indigo-600 text-white dark:bg-indigo-500 dark:text-white`,
        status: standardBadge,
        secondary: `${standardBadge} bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200`,
        outline: `${standardBadge} border border-zinc-300 text-zinc-700 dark:border-zinc-700 dark:text-zinc-300`,
        destructive: `${standardBadge} ${statusTone.wrong.solidBadge}`,
        success: `${standardBadge} ${statusTone.correct.softCard}`,
        ghost: `${standardBadge} text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800`,
        choice: "inline-flex size-space-6 items-center justify-center rounded-md text-xs font-display font-semibold shrink-0 transition-colors",
        answerPart: "inline-flex items-center gap-space-1 rounded-md px-space-1_5 py-space-0_5 text-xs bg-surface-raised/70 dark:bg-surface-raised/50",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  asChild?: boolean;
}

export function Badge({ className, variant, asChild = false, ...props }: BadgeProps) {
  const Component = asChild ? Slot : "span";
  return <Component className={cn(badgeVariants({ variant }), className)} {...props} />;
}
