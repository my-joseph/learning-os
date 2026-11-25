"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cva, type VariantProps } from "class-variance-authority";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { settle } from "@/lib/motion";

export type TabsVariant = "default" | "underline" | "similar";

const segmentedListVariants = cva("", {
  variants: {
    variant: {
      default: "inline-flex min-h-[44px] items-center gap-1 rounded-lg bg-zinc-100 p-1 dark:bg-zinc-900",
      underline: "inline-flex items-center gap-1 rounded-none bg-transparent p-0",
      similar: "flex min-w-0 items-center gap-space-1 overflow-x-auto overflow-y-hidden rounded-none bg-transparent p-space-0 scrollbar-hidden snap-x -mb-px",
      chips: "flex shrink-0 gap-space-0_5",
      answerMode: "relative inline-grid grid-cols-2 items-center rounded-lg bg-surface-selected/70 dark:bg-surface-panel p-space-0_5",
      rail: "fixed left-space-3 top-1/2 z-sticky hidden -translate-y-1/2 grid-rows-2 items-center rounded-xl border border-border bg-surface-hover/95 p-space-1 shadow-ui-sm backdrop-blur-glass dark:bg-surface-hover/80 lg:grid",
      header: "relative grid shrink-0 grid-cols-2 items-center rounded-lg border border-border bg-surface-hover p-space-0_5 dark:bg-surface-hover/80 lg:hidden",
      sidebar: "relative grid shrink-0 grid-cols-2 rounded-lg bg-surface-selected/70 p-space-0_5 dark:bg-surface-raised/75 lg:p-space-0",
    },
  },
  defaultVariants: { variant: "default" },
});

const chipVariants = cva(
  "relative expand-touch-target rounded-md px-space-2 text-sm transition-colors duration-color ease-standard [@media(hover:hover)]:hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent data-[selected=true]:bg-surface-selected/70 disabled:pointer-events-none disabled:opacity-disabled motion-reduce:transition-none",
  {
    variants: {
      size: { xs: "h-control-xs", sm: "h-control-sm", md: "h-control-md" },
      tone: {
        default: "text-foreground",
        secondary: "text-muted",
        primary: "text-accent",
        destructive: "text-status-wrong",
      },
    },
    defaultVariants: { size: "xs", tone: "default" },
  }
);

const TabsVariantContext = React.createContext<TabsVariant>("default");
const tabTriggerVariants: Record<TabsVariant, string> = {
  default: "min-h-[44px] rounded-md px-3 text-sm font-normal text-zinc-600 transition-colors hover:text-foreground motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:text-zinc-300 dark:focus-visible:ring-indigo-400 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm",
  underline: "min-h-[44px] rounded-none border-b-2 -mb-px bg-transparent px-3 text-sm font-normal text-zinc-600 shadow-none transition-colors hover:text-foreground motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 dark:text-zinc-400 dark:focus-visible:ring-indigo-400 data-[state=active]:border-indigo-600 data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none dark:data-[state=active]:border-indigo-400",
  similar: "inline-flex min-h-touch shrink-0 snap-start items-center justify-center gap-space-1_5 whitespace-nowrap rounded-none border-b-2 border-transparent -mb-px bg-transparent px-space-3 text-sm font-normal text-foreground-subtle hover:text-foreground transition-colors motion-reduce:transition-none focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent sm:h-space-9 sm:min-h-0 data-[state=active]:border-accent data-[state=active]:font-semibold data-[state=active]:text-foreground disabled:cursor-not-allowed disabled:select-none disabled:text-foreground-faint disabled:opacity-soft",
};
const slidingPill = "pointer-events-none absolute bottom-space-0_5 left-space-0_5 top-space-0_5 w-[calc(50%-var(--space-0-5))] rounded-md bg-surface-raised shadow-ui-sm";
const answerModeChip = "relative z-local inline-flex min-h-touch min-w-touch items-center justify-center gap-space-1_5 rounded-md px-space-2_5 text-xs font-normal text-muted transition-colors duration-panel focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent data-[selected=true]:text-foreground data-[selected=false]:hover:text-foreground dark:data-[selected=false]:hover:text-foreground-menu disabled:opacity-disabled sm:h-control-xs sm:min-h-0 sm:min-w-0";

export const Tabs = TabsPrimitive.Root;
export const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List> & {
    variant?: TabsVariant;
  }
>(({ className, variant = "default", children, ...props }, ref) => (
  <TabsVariantContext.Provider value={variant}>
    <TabsPrimitive.List
      ref={ref}
      className={cn(segmentedListVariants({ variant }), className)}
      {...props}
    >
      {children}
    </TabsPrimitive.List>
  </TabsVariantContext.Provider>
));
TabsList.displayName = TabsPrimitive.List.displayName;

export const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger> & {
    variant?: TabsVariant;
  }
>(({ className, variant, ...props }, ref) => {
  const contextVariant = React.useContext(TabsVariantContext);
  const resolvedVariant = variant ?? contextVariant;
  return (
    <TabsPrimitive.Trigger
      ref={ref}
      className={cn(tabTriggerVariants[resolvedVariant], className)}
      {...props}
    />
  );
});
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

export const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content ref={ref} className={cn("mt-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400", className)} {...props} />
));
TabsContent.displayName = TabsPrimitive.Content.displayName;

type SegmentedNavVariant = "rail" | "header" | "sidebar";
const SegmentedNavContext = React.createContext<SegmentedNavVariant>("sidebar");

/** Two segments for navigation links, with a sliding indicator. */
export function SegmentedNav({ variant, activeIndex, className, children, ...props }:
  React.ComponentPropsWithoutRef<"nav"> & { variant: SegmentedNavVariant; activeIndex: 0 | 1 }
) {
  const rail = variant === "rail";
  const offset = activeIndex === 1 ? "100%" : "0%";
  return (
    <SegmentedNavContext.Provider value={variant}>
      <nav {...props} className={className ?? segmentedListVariants({ variant })}>
        <m.span
          aria-hidden
          className={cn(
            rail
              ? "pointer-events-none absolute bg-surface-raised shadow-ui-sm left-space-1 right-space-1 top-space-1 h-[calc(50%-var(--space-1))] rounded-lg"
              : slidingPill,
            variant === "sidebar" && "dark:bg-surface-selected/80"
          )}
          initial={false}
          animate={rail ? { y: offset } : { x: offset }}
          transition={settle}
        />
        {children}
      </nav>
    </SegmentedNavContext.Provider>
  );
}

const segmentedNavItemSize = {
  rail: "size-control-sm rounded-lg",
  header: "size-control-xs rounded-md sm:size-control-sm",
  sidebar: "size-touch rounded-md focus-visible:ring-inset lg:size-control-sm",
};

export const SegmentedNavItem = React.forwardRef<
  HTMLElement,
  React.ComponentPropsWithoutRef<typeof Slot> & { selected: boolean }
>(({ selected, className, ...props }, ref) => {
  const variant = React.useContext(SegmentedNavContext);
  return (
    <Slot
      {...props}
      ref={ref}
      className={cn(
        "relative z-local inline-flex items-center justify-center transition-colors duration-panel focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent aria-disabled:cursor-not-allowed aria-disabled:opacity-disabled",
        segmentedNavItemSize[variant],
        selected ? "text-foreground" : "text-muted hover:text-foreground dark:hover:text-foreground-menu",
        className
      )}
    />
  );
});
SegmentedNavItem.displayName = "SegmentedNavItem";

type SegmentedChipsProps<T extends string> = VariantProps<typeof chipVariants> & {
  label: string;
  options: readonly { value: T; label: string; icon?: React.ReactNode; disabled?: boolean }[];
  value: T;
  onValueChange: (value: T) => void;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  variant?: "chips" | "answerMode";
};

export function SegmentedChips<T extends string>({
  label, options, value, onValueChange, size, tone, disabled, loading, className, variant = "chips",
}: SegmentedChipsProps<T>) {
  const isAnswerMode = variant === "answerMode";
  const activeIndex = options.findIndex((option) => option.value === value);
  return (
    <div role="group" aria-label={label} aria-busy={loading || undefined} className={cn(segmentedListVariants({ variant }), className)}>
      {isAnswerMode && (
        <m.span
          aria-hidden="true"
          className={cn(slidingPill, "dark:bg-surface-selected/80")}
          initial={false}
          animate={{ x: activeIndex === 1 ? "100%" : "0%" }}
          transition={settle}
        />
      )}
      {options.map((option, index) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={option.value === value}
          data-selected={option.value === value}
          disabled={disabled || loading || option.disabled}
          onClick={() => onValueChange(option.value)}
          onKeyDown={(event) => {
            if (!isAnswerMode && (event.key === "Enter" || event.key === " ")) event.stopPropagation();
          }}
          className={isAnswerMode ? answerModeChip : cn(chipVariants({ size, tone }), index === 0 && "expand-touch-start")}
        >
          {option.icon}
          {isAnswerMode ? <span>{option.label}</span> : option.label}
        </button>
      ))}
    </div>
  );
}
