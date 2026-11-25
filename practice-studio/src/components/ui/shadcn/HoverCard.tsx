"use client";

import * as React from "react";
import * as HoverCardPrimitive from "@radix-ui/react-hover-card";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { popover, popoverFromLeft } from "@/lib/motion";

export const HoverCard = HoverCardPrimitive.Root;

/*
 * Warm hand-off for a list of hover cards (sidebar tree): the first card waits for the
 * normal delay; while one is open, or shortly after it closes, the next row's card opens
 * at once, so the learner can sweep down the list without pausing on every row.
 */
let warmUntil = 0;
let openCount = 0;
const warmListeners = new Set<() => void>();
const notifyWarm = () => warmListeners.forEach((listener) => listener());
const WARM_GRACE_MS = 400;

function isWarm() {
  return openCount > 0 || Date.now() < warmUntil;
}

export function useWarmHoverCard(openDelay: number) {
  const [, rerender] = React.useReducer((n: number) => n + 1, 0);
  const isOpen = React.useRef(false);
  React.useEffect(() => {
    warmListeners.add(rerender);
    return () => {
      warmListeners.delete(rerender);
      if (isOpen.current) {
        openCount = Math.max(0, openCount - 1);
        isOpen.current = false;
      }
    };
  }, []);
  const onOpenChange = React.useCallback((open: boolean) => {
    if (open === isOpen.current) return;
    isOpen.current = open;
    openCount = Math.max(0, openCount + (open ? 1 : -1));
    if (!open) {
      warmUntil = Date.now() + WARM_GRACE_MS;
      setTimeout(notifyWarm, WARM_GRACE_MS + 10);
    }
    notifyWarm();
  }, []);
  return { openDelay: isWarm() ? 0 : openDelay, onOpenChange };
}
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
