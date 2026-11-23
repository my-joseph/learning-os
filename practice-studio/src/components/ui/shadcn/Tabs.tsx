"use client";

import * as React from "react";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "@/lib/cn";

export type TabsVariant = "default" | "underline";

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
      className={cn(
        variant === "underline"
          ? "inline-flex items-center gap-1 rounded-none bg-transparent p-0"
          : "inline-flex min-h-[44px] items-center gap-1 rounded-lg bg-zinc-100 p-1 dark:bg-zinc-900",
        className
      )}
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
