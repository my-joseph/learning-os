"use client";

import * as React from "react";
import { Command as CommandPrimitive } from "cmdk";
import { cn } from "@/lib/cn";

export const Command = CommandPrimitive;
export const CommandLoading = CommandPrimitive.Loading;

export const CommandInput = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Input>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Input>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Input
    ref={ref}
    className={cn(
      "h-12 min-w-0 flex-1 bg-transparent text-base text-foreground outline-none placeholder:text-zinc-500 focus-visible:outline-none dark:placeholder:text-zinc-400",
      className
    )}
    {...props}
  />
));
CommandInput.displayName = "CommandInput";

export const CommandList = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.List>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.List
    ref={ref}
    className={cn("min-h-0 flex-1 scroll-py-2 overflow-y-auto overscroll-contain", className)}
    {...props}
  />
));
CommandList.displayName = "CommandList";

export const CommandGroup = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Group>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Group>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Group
    ref={ref}
    className={cn(
      "px-3 pt-1 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:pb-1 [&_[cmdk-group-heading]]:pt-2 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-zinc-500 dark:[&_[cmdk-group-heading]]:text-zinc-400",
      className
    )}
    {...props}
  />
));
CommandGroup.displayName = "CommandGroup";

export const CommandItem = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Item>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Item
    ref={ref}
    className={cn(
      "flex min-h-11 cursor-pointer select-none items-center gap-3 rounded-md px-2 py-1 text-sm text-foreground-secondary data-[selected=true]:bg-zinc-200/60 data-[selected=true]:text-foreground [@media(hover:hover)]:hover:text-foreground dark:data-[selected=true]:bg-zinc-700/60 dark:data-[selected=true]:text-foreground dark:[@media(hover:hover)]:hover:text-foreground sm:min-h-9 sm:[@media(any-pointer:coarse)]:min-h-11",
      className
    )}
    {...props}
  />
));
CommandItem.displayName = "CommandItem";
