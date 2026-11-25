"use client";

import * as React from "react";
import * as HoverCardPrimitive from "@radix-ui/react-hover-card";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { popover, popoverFromLeft } from "@/lib/motion";

export const HoverCard = HoverCardPrimitive.Root;
export const HoverCardTrigger = HoverCardPrimitive.Trigger;

export const HoverCardContent = React.forwardRef<
  React.ElementRef<typeof HoverCardPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof HoverCardPrimitive.Content>
>(({ className, align = "center", side = "bottom", sideOffset = 4, children, ...props }, ref) => (
  <HoverCardPrimitive.Portal>
    <HoverCardPrimitive.Content ref={ref} align={align} side={side} sideOffset={sideOffset} asChild {...props}>
      <m.div
        variants={side === "right" ? popoverFromLeft : popover}
        initial="hidden"
        animate="shown"
        className={cn("z-overlay w-64 rounded-xl border border-border bg-surface-raised p-space-3 text-foreground shadow-ui-md outline-none motion-reduce:transition-none dark:bg-surface-panel", className)}
      >
        {children}
      </m.div>
    </HoverCardPrimitive.Content>
  </HoverCardPrimitive.Portal>
));
HoverCardContent.displayName = HoverCardPrimitive.Content.displayName;
