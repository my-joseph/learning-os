"use client";

import * as React from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { popover } from "@/lib/motion";

export const Popover = PopoverPrimitive.Root;
export const PopoverTrigger = PopoverPrimitive.Trigger;
export const PopoverAnchor = PopoverPrimitive.Anchor;
export const PopoverClose = PopoverPrimitive.Close;

export const PopoverContent = React.forwardRef<
  React.ElementRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(({ className, align = "center", sideOffset = 6, children, ...props }, ref) => (
  <PopoverPrimitive.Portal>
    <PopoverPrimitive.Content ref={ref} align={align} sideOffset={sideOffset} asChild {...props}>
      <m.div
        variants={popover}
        initial="hidden"
        animate="shown"
        className={cn("z-50 w-72 rounded-lg border border-zinc-200 bg-background p-4 text-foreground shadow-lg outline-none motion-reduce:transition-none dark:border-zinc-800", className)}
      >
        {children}
      </m.div>
    </PopoverPrimitive.Content>
  </PopoverPrimitive.Portal>
));
PopoverContent.displayName = PopoverPrimitive.Content.displayName;
