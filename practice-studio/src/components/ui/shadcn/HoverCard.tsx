"use client";

import * as React from "react";
import * as HoverCardPrimitive from "@radix-ui/react-hover-card";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { popover } from "@/lib/motion";

export const HoverCard = HoverCardPrimitive.Root;
export const HoverCardTrigger = HoverCardPrimitive.Trigger;

export const HoverCardContent = React.forwardRef<
  React.ElementRef<typeof HoverCardPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof HoverCardPrimitive.Content>
>(({ className, align = "center", sideOffset = 4, children, ...props }, ref) => (
  <HoverCardPrimitive.Portal>
    <HoverCardPrimitive.Content ref={ref} align={align} sideOffset={sideOffset} asChild {...props}>
      <m.div
        variants={popover}
        initial="hidden"
        animate="shown"
        className={cn("z-50 w-64 rounded-xl border border-zinc-200 bg-white p-4 text-foreground shadow-md outline-none motion-reduce:transition-none dark:border-zinc-800 dark:bg-zinc-900", className)}
      >
        {children}
      </m.div>
    </HoverCardPrimitive.Content>
  </HoverCardPrimitive.Portal>
));
HoverCardContent.displayName = HoverCardPrimitive.Content.displayName;
