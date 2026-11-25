"use client";

import * as React from "react";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

export type TabsVariant = "default" | "underline";

const segmentedListVariants = cva("", {
  variants: {
    variant: {
      default: "inline-flex min-h-[44px] items-center gap-1 rounded-lg bg-zinc-100 p-1 dark:bg-zinc-900",
      underline: "inline-flex items-center gap-1 rounded-none bg-transparent p-0",
      chips: "flex shrink-0 gap-space-0_5",
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
      className={cn(
        resolvedVariant === "underline"
          ? "min-h-[44px] rounded-none border-b-2 -mb-px bg-transparent px-3 text-sm font-medium text-zinc-600 shadow-none transition-colors hover:text-foreground motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 dark:text-zinc-400 dark:focus-visible:ring-indigo-400 data-[state=active]:border-indigo-600 data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none dark:data-[state=active]:border-indigo-400"
          : "min-h-[44px] rounded-md px-3 text-sm font-medium text-zinc-600 transition-colors hover:text-foreground motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:text-zinc-300 dark:focus-visible:ring-indigo-400 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm",
        className
      )}
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


type SegmentedChipsProps<T extends string> = VariantProps<typeof chipVariants> & {
  label: string;
  options: readonly { value: T; label: string; disabled?: boolean }[];
  value: T;
  onValueChange: (value: T) => void;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
};

export function SegmentedChips<T extends string>({
  label, options, value, onValueChange, size, tone, disabled, loading, className,
}: SegmentedChipsProps<T>) {
  return (
    <div role="group" aria-label={label} aria-busy={loading || undefined} className={cn(segmentedListVariants({ variant: "chips" }), className)}>
      {options.map((option, index) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={option.value === value}
          data-selected={option.value === value}
          disabled={disabled || loading || option.disabled}
          onClick={() => onValueChange(option.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") event.stopPropagation();
          }}
          className={cn(chipVariants({ size, tone }), index === 0 && "expand-touch-start")}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
