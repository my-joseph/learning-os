"use client";

import * as React from "react";
import { Command as CommandPrimitive } from "cmdk";
import { ListRow } from "../ListRow";
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
      "h-control-lg min-w-0 flex-1 bg-transparent text-base text-foreground outline-none placeholder:text-muted focus-visible:outline-none",
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
    className={cn("min-h-0 flex-1 scroll-py-space-2 overflow-y-auto overscroll-contain", className)}
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
      "px-space-3 pt-space-1 [&_[cmdk-group-heading]]:px-space-2 [&_[cmdk-group-heading]]:pb-space-1 [&_[cmdk-group-heading]]:pt-space-2 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-normal [&_[cmdk-group-heading]]:text-muted",
      className
    )}
    {...props}
  />
));
CommandGroup.displayName = "CommandGroup";

type CommandItemProps = React.ComponentPropsWithoutRef<typeof CommandPrimitive.Item> &
  Pick<React.ComponentPropsWithoutRef<typeof ListRow>, "label" | "leading" | "trailing" | "selected" | "emphasis" | "size" | "tone" | "loading">;

export const CommandItem = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Item>,
  CommandItemProps
>(({ label, leading, trailing, selected, emphasis, size, tone, loading, className, disabled, ...props }, ref) => (
  <ListRow
    ref={ref}
    asChild
    variant="command"
    label={label}
    leading={leading}
    trailing={trailing}
    selected={selected}
    emphasis={emphasis}
    size={size}
    tone={tone}
    loading={loading}
    className={className}
  >
    <CommandPrimitive.Item disabled={disabled || loading} {...props} />
  </ListRow>
));
CommandItem.displayName = "CommandItem";
