"use client";

import * as React from "react";
import * as HoverCardPrimitive from "@radix-ui/react-hover-card";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { popover } from "@/lib/motion";

export const HoverCard = HoverCardPrimitive.Root;
export const HoverCardTrigger = HoverCardPrimitive.Trigger;

// A row contains real buttons, so it needs to keep its native touch activation.
export const HoverCardRowTrigger = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  (props, ref) => (
    <HoverCardTrigger
      asChild
      onPointerEnter={(event) => {
        if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) event.preventDefault();
      }}
      onFocus={(event) => event.preventDefault()}
    >
      <HoverCardRowSurface {...props} ref={ref} />
    </HoverCardTrigger>
  )
);
HoverCardRowTrigger.displayName = "HoverCardRowTrigger";

const HoverCardRowSurface = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  (props, ref) => <div {...props} ref={ref} onTouchStart={undefined} />
);
HoverCardRowSurface.displayName = "HoverCardRowSurface";

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
        className={cn("z-overlay w-64 rounded-xl border border-border bg-surface-raised p-space-4 text-foreground shadow-ui-md outline-none motion-reduce:transition-none dark:bg-surface-panel", className)}
      >
        {children}
      </m.div>
    </HoverCardPrimitive.Content>
  </HoverCardPrimitive.Portal>
));
HoverCardContent.displayName = HoverCardPrimitive.Content.displayName;
