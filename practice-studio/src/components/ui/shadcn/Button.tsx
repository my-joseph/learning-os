"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { m, type HTMLMotionProps } from "motion/react";
import { cn } from "@/lib/cn";
import { choiceTapPress, quick, tapPress } from "@/lib/motion";
import { DESTRUCTIVE_BUTTON_CLS, warningTone } from "@/lib/statusTone";

const keyboardRing = "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent";
const actionBase = `inline-flex items-center justify-center rounded-md transition-colors motion-reduce:transition-none ${keyboardRing} disabled:pointer-events-none disabled:opacity-disabled focus-visible:ring-offset-background`;
const resultAction = "gap-space-1_5 rounded-lg shrink-0 focus-visible:ring-offset-2";
const palettePress = "active:bg-accent-tint dark:active:bg-accent-tint/60 active:text-accent dark:active:text-accent";

const standardButton = "inline-flex min-h-[44px] items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-2 focus-visible:ring-offset-background dark:focus-visible:ring-indigo-400 disabled:pointer-events-none disabled:opacity-50";
const footerAction = `${actionBase} hover:bg-surface-hover hover:text-foreground disabled:opacity-quiet focus-visible:ring-offset-2`;
const assistAction = `inline-flex items-center justify-center rounded-md text-xs text-muted hover:text-foreground transition-colors ${keyboardRing}`;
const assistChip = "border transition-colors disabled:cursor-not-allowed aria-[pressed=false]:border-border aria-[pressed=false]:bg-surface-raised aria-[pressed=false]:hover:border-foreground-faint aria-[pressed=false]:dark:hover:border-surface-hover-strong";

export const buttonVariants = cva(
  "",
  {
    variants: {
      variant: {
        primary: `${standardButton} bg-indigo-600 text-white hover:bg-indigo-700 dark:bg-indigo-600 dark:text-white dark:hover:bg-indigo-500`,
        secondary: `${standardButton} bg-zinc-200 text-zinc-900 hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-100 dark:hover:bg-zinc-700`,
        outline: `${standardButton} border border-zinc-300 bg-transparent text-foreground hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800`,
        ghost: `${standardButton} bg-transparent text-foreground hover:bg-zinc-100 dark:hover:bg-zinc-800`,
        destructive: `${standardButton} ${DESTRUCTIVE_BUTTON_CLS}`,
        answerNav: `${footerAction} bg-transparent font-semibold text-foreground`,
        answerNavReview: `${footerAction} bg-transparent font-normal text-foreground-answer-detail`,
        resultOutline: `${actionBase} ${resultAction} border border-border/90 dark:border-border-control bg-surface-raised/90 dark:bg-surface-raised/80 text-foreground-answer hover:bg-surface-raised dark:hover:bg-surface-raised hover:border-border-control dark:hover:border-surface-hover-strong px-space-3_5 sm:px-space-3 font-normal`,
        resultPrimary: `${actionBase} ${resultAction} focus-visible:ring-offset-1 bg-accent-primary text-accent-on-primary hover:bg-accent-strong px-space-4 sm:px-space-3_5 font-semibold`,
        resultLink: `${actionBase} gap-space-1 bg-transparent hover:bg-surface-hover text-foreground-answer-detail hover:text-foreground-action-hover font-normal focus-visible:ring-offset-2`,
        choice: "flex items-center rounded-xl border transition-colors",
        assist: `${assistAction} motion-reduce:transition-none`,
        assistScore: `${assistChip} rounded-lg font-sans tabular-nums disabled:opacity-subtle aria-[pressed=false]:text-foreground-subtle`,
        assistTag: `${assistChip} inline-flex items-center justify-center rounded-full text-xs disabled:opacity-disabled aria-[pressed=false]:text-muted`,
        assistFlag: "inline-flex items-center justify-center whitespace-nowrap rounded-lg border font-normal transition-all",
        exampleBack: "inline-flex items-center gap-space-1 rounded-lg text-foreground-control hover:bg-surface-hover hover:text-foreground-action-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
        exampleQuiet: `inline-flex items-center rounded-lg text-xs font-normal text-foreground-subtle hover:text-foreground transition-colors ${keyboardRing}`,
        examplePrimary: `inline-flex items-center justify-center gap-space-1_5 rounded-xl bg-accent-primary hover:bg-accent-strong text-accent-on-primary text-xs font-semibold transition-colors ${keyboardRing} focus-visible:ring-offset-1`,
        stepper: "group relative z-local flex w-full min-w-space-11 min-h-space-11 flex-col items-center justify-start rounded-lg cursor-pointer focus:outline-none focus-visible:outline-none sm:min-w-0",
      },
      size: {
        default: "min-w-[44px]",
        sm: "min-w-[44px] px-3 text-xs",
        compact: "min-h-[44px] min-w-[44px] px-3 sm:min-h-[32px] sm:min-w-0 sm:px-2.5 py-1.5 sm:py-1 text-xs",
        lg: "min-h-[48px] min-w-[48px] px-6",
        icon: "min-w-[44px] px-2",
        iconSm: "min-h-[44px] min-w-[44px] p-0 sm:min-h-[36px] sm:min-w-[36px]",
        answerNav: "min-h-touch min-w-touch sm:min-h-control-sm sm:min-w-0 gap-space-1 px-space-3 sm:px-space-2_5 py-space-1_5 sm:py-space-1 text-xs",
        resultAction: "h-touch min-w-touch sm:h-control-sm sm:min-w-0 py-space-1_5 sm:py-space-1 text-xs",
        resultLink: "min-h-touch min-w-touch sm:min-h-0 sm:min-w-0 px-space-3 sm:px-space-2_5 py-space-1 sm:py-space-0_5 text-xs",
        choiceWrap: "min-h-touch min-w-touch sm:min-h-space-10 sm:min-w-0 px-space-3_5 py-space-2 gap-space-2 text-xs font-normal",
        choiceStack: "w-full min-h-touch text-left p-space-3_5 justify-between gap-space-3",
        assistInline: "min-h-touch min-w-touch gap-space-1 sm:min-h-0 sm:min-w-0 sm:justify-start",
        assistSkip: "min-h-touch min-w-touch gap-space-1 px-space-2 sm:min-h-control-md sm:min-w-0",
        assistScore: "min-h-touch min-w-touch px-space-3 sm:min-h-control-xs sm:min-w-0 sm:px-space-2_5",
        assistTag: "min-h-touch min-w-touch px-space-2_5 py-space-1 sm:min-h-control-xs sm:min-w-0",
        assistFlag: "min-h-touch min-w-touch gap-space-1_5 px-space-2_5 py-space-1 text-xs sm:min-h-0 sm:min-w-0",
        exampleBack: "min-h-touch px-space-1_5 sm:min-h-0",
        exampleQuiet: "min-h-touch py-space-1 sm:min-h-0",
        examplePrimary: "min-h-touch h-space-11 px-space-4 sm:min-h-0 sm:h-space-9",
        stepper: "py-space-1",
        stepperCompact: "py-space-1 sm:min-h-0 sm:py-space-0_5",
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
        timer: "size-space-11 min-h-touch min-w-touch sm:min-h-0 sm:min-w-0 sm:size-space-6",
      },
      tone: {
        default: "text-foreground",
        secondary: "text-muted",
        primary: "bg-accent-primary text-accent-on-primary hover:bg-accent-primary-hover",
        destructive: "text-status-wrong",
        answerCheck: "bg-accent-primary text-accent-on-primary hover:bg-accent-strong",
        paletteQuick: `text-foreground-answer-detail dark:text-foreground-answer hover:bg-surface-hover select-none ${palettePress}`,
        paletteDisclosure: "text-foreground-subtle data-[selected=false]:hover:text-foreground data-[selected=false]:hover:bg-surface-hover data-[selected=true]:text-accent data-[selected=true]:bg-accent-tint dark:data-[selected=true]:bg-accent-tint/60",
        paletteKey: `rounded-lg border border-border bg-surface-raised dark:bg-surface-selected/70 dark:border-surface-hover-strong/70 shadow-ui-sm text-foreground-answer dark:text-foreground hover:bg-surface-hover dark:hover:bg-surface-selected hover:border-border-control dark:hover:border-foreground-faint select-none ${palettePress}`,
        tabAdd: "text-muted data-[invite=true]:bg-accent-tint data-[invite=true]:text-accent data-[error=true]:text-warning",
        timer: "text-muted hover:text-foreground",
        timerPaused: warningTone.text,
      },
      hitArea: {
        expanded: "expand-touch-target hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent data-[selected=true]:bg-surface-selected/60",
        padded: "max-sm:min-h-touch max-sm:min-w-touch [@media(any-pointer:coarse)]:min-h-touch [@media(any-pointer:coarse)]:min-w-touch outline-none before:absolute before:inset-0 before:m-auto before:rounded-md hover:before:bg-surface-hover-strong/70 dark:hover:before:bg-surface-hover-strong/60 focus-visible:before:ring-2 focus-visible:before:ring-inset focus-visible:before:ring-accent data-[selected=true]:before:bg-surface-selected/60 [&>svg]:relative",
        sidebarToggle: "size-touch rounded-lg transition-colors hover:bg-surface-selected/60 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background motion-reduce:transition-none lg:size-control-sm dark:hover:bg-surface-selected/50",
        sidebarAction: "mr-space-0_5 size-touch rounded-full transition-colors hover:text-foreground focus:outline-none before:absolute before:inset-space-2 before:rounded-full before:transition-colors hover:before:bg-surface-hover-strong/70 dark:hover:before:bg-surface-hover-strong/60 focus-visible:before:ring-2 focus-visible:before:ring-inset focus-visible:before:ring-muted lg:size-control-xs lg:before:inset-space-0 lg:before:hidden lg:focus-visible:before:block [&>svg]:relative",
        answer: `max-sm:size-touch transition-colors ${keyboardRing} disabled:pointer-events-auto disabled:opacity-subtle`,
        tabAdd: "max-sm:size-touch transition-colors enabled:hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent aria-disabled:cursor-not-allowed aria-disabled:opacity-disabled aria-disabled:hover:bg-transparent data-[invite=true]:hover:bg-accent-tint motion-reduce:transition-none",
        timer: "shrink transition-colors hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 dark:focus-visible:ring-accent/60",
      },
    },
    compoundVariants: [
      { size: "xs", hitArea: "padded", class: "before:size-control-xs" },
      { size: "sm", hitArea: "padded", class: "before:size-control-sm" },
      { size: "md", hitArea: "padded", class: "before:size-control-md" },
      { tone: "answerCheck", hitArea: "answer", class: "rounded-answer-action sm:rounded-lg focus-visible:ring-offset-1 disabled:hover:bg-accent-primary" },
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

    // These compact controls already provide feedback through their own state or indicator.
    if (
      (icon && icon.hitArea !== "sidebarToggle") ||
      variant?.startsWith("assist") ||
      variant?.startsWith("example") ||
      variant === "stepper"
    ) {
      return <button ref={ref} type={type ?? "button"} className={classes} {...props} />;
    }

    return (
      <m.button
        ref={ref}
        type={type ?? "button"}
        whileTap={props.disabled ? undefined : variant === "choice" ? choiceTapPress : tapPress}
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
      aria-busy={loading || props["aria-busy"]}
      disabled={disabled || loading}
    />
  )
);
IconButton.displayName = "IconButton";
