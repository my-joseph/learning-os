"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { m, type HTMLMotionProps } from "motion/react";
import { cn } from "@/lib/cn";
import { quick, tapPress } from "@/lib/motion";
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

const iconButtonVariants = cva(
  "relative inline-flex shrink-0 items-center justify-center rounded-md disabled:pointer-events-none disabled:opacity-disabled",
  {
    variants: {
      size: {
        xs: "size-control-xs",
        sm: "size-control-sm",
        md: "size-control-md",
      },
      tone: {
        default: "text-foreground",
        secondary: "text-muted",
        primary: "bg-accent-primary text-accent-on-primary hover:bg-accent-primary-hover",
        destructive: "text-status-wrong",
      },
      hitArea: {
        expanded: "expand-touch-target hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent data-[selected=true]:bg-surface-selected/60",
        padded: "max-sm:min-h-touch max-sm:min-w-touch [@media(any-pointer:coarse)]:min-h-touch [@media(any-pointer:coarse)]:min-w-touch outline-none before:absolute before:inset-0 before:m-auto before:rounded-md hover:before:bg-surface-hover-strong/70 dark:hover:before:bg-surface-hover-strong/60 focus-visible:before:ring-2 focus-visible:before:ring-inset focus-visible:before:ring-accent data-[selected=true]:before:bg-surface-selected/60 [&>svg]:relative",
      },
    },
    compoundVariants: [
      { size: "xs", hitArea: "padded", class: "before:size-control-xs" },
      { size: "sm", hitArea: "padded", class: "before:size-control-sm" },
      { size: "md", hitArea: "padded", class: "before:size-control-md" },
    ],
    defaultVariants: { size: "md", tone: "default", hitArea: "expanded" },
  }
);

type IconButtonVariants = VariantProps<typeof iconButtonVariants>;

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  icon?: IconButtonVariants;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, icon, asChild = false, type, ...props }, ref) => {
    const classes = cn(icon ? iconButtonVariants(icon) : buttonVariants({ variant, size }), className);
    if (asChild) {
      return (
        <Slot
          ref={ref}
          className={classes}
          {...props}
          {...(type !== undefined ? { type } : {})}
        />
      );
    }

    if (icon) return <button ref={ref} type={type ?? "button"} className={classes} {...props} />;

    return (
      <m.button
        ref={ref}
        type={type ?? "button"}
        whileTap={props.disabled ? undefined : tapPress}
        transition={quick}
        className={classes}
        {...(props as HTMLMotionProps<"button">)}
      />
    );
  }
);
Button.displayName = "Button";


type IconButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & IconButtonVariants & {
  selected?: boolean;
  loading?: boolean;
};

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ size, tone, hitArea, selected, disabled, loading, ...props }, ref) => (
    <Button
      {...props}
      ref={ref}
      icon={{ size, tone, hitArea }}
      data-selected={selected}
      aria-busy={loading || undefined}
      disabled={disabled || loading}
    />
  )
);
IconButton.displayName = "IconButton";
