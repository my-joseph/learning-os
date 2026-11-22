import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { statusTone } from "@/lib/statusTone";

export const badgeVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium [&>svg]:pointer-events-none [&>svg]:size-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400",
  {
    variants: {
      variant: {
        default: "bg-indigo-600 text-white dark:bg-indigo-500 dark:text-white",
        secondary: "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200",
        outline: "border border-zinc-300 text-zinc-700 dark:border-zinc-700 dark:text-zinc-300",
        destructive: statusTone.wrong.solidBadge,
        success: statusTone.correct.softCard,
        ghost: "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800",
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
