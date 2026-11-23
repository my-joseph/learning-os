import type { Transition, Variants } from "motion/react";

/** One calm ease-out curve for the whole Studio (docs/studio_design.md: say less, never flashy). */
export const EASE_OUT = [0.16, 1, 0.3, 1] as const;

export const quick: Transition = { duration: 0.16, ease: EASE_OUT };
export const settle: Transition = { duration: 0.24, ease: EASE_OUT };

/** Dropdowns and menus: grow from where they were opened, shrink back on close. */
export const popover: Variants = {
  hidden: { opacity: 0, y: -4, scale: 0.98, transition: { duration: 0.12, ease: EASE_OUT } },
  shown: { opacity: 1, y: 0, scale: 1, transition: quick },
};

/** Hint, set-up, steps, feedback: open and close in place (height + fade). */
export const reveal: Variants = {
  hidden: { opacity: 0, height: 0, transition: { duration: 0.16, ease: EASE_OUT } },
  shown: { opacity: 1, height: "auto", transition: { duration: 0.22, ease: EASE_OUT } },
};

/** A new question, drill or workspace settles in. */
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 6 },
  shown: { opacity: 1, y: 0, transition: settle },
};

export const fade: Variants = {
  hidden: { opacity: 0, transition: { duration: 0.16 } },
  shown: { opacity: 1, transition: { duration: 0.2 } },
};

export const drawer: Variants = {
  hidden: { x: "100%", transition: { duration: 0.2, ease: EASE_OUT } },
  shown: { x: 0, transition: { duration: 0.26, ease: EASE_OUT } },
};

/** Centred alertdialog / modal card: scale 0.98 -> 1 + fade. */
export const dialogCard: Variants = {
  hidden: { opacity: 0, scale: 0.98, transition: { duration: 0.14, ease: EASE_OUT } },
  shown: { opacity: 1, scale: 1, transition: quick },
};

/** Status toast: slide up 8 px + fade in, fade out on exit. */
export const toastVariants: Variants = {
  hidden: { opacity: 0, y: 8 },
  shown: { opacity: 1, y: 0, transition: quick },
  exit: { opacity: 0, transition: { duration: 0.14, ease: EASE_OUT } },
};

/** Spread on an `m.*` element inside <AnimatePresence>. */
export const presence = { initial: "hidden", animate: "shown", exit: "hidden" } as const;

/** Mobile bottom-sheet drawer: slides up from bottom edge. */
export const drawerBottom: Variants = {
  hidden: { y: "100%", transition: { duration: 0.2, ease: EASE_OUT } },
  shown: { y: 0, transition: { duration: 0.24, ease: EASE_OUT } },
};

/** Left navigation drawer: slides in from left edge. */
export const drawerLeft: Variants = {
  hidden: { x: "-100%", transition: { duration: 0.2, ease: EASE_OUT } },
  shown: { x: 0, transition: { duration: 0.24, ease: EASE_OUT } },
};

/** Sidebar expanded/collapsed inner content transition inside AnimatePresence mode="wait". */
export const sidebarContent: Variants = {
  hidden: { opacity: 0, x: -6 },
  shown: { opacity: 1, x: 0, transition: quick },
  exit: { opacity: 0, x: -6, transition: { duration: 0.12, ease: EASE_OUT } },
};

/** Compact tooltip pop-in. */
export const tooltipPop: Variants = {
  hidden: { opacity: 0, scale: 0.96, y: 2 },
  shown: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.12, ease: EASE_OUT } },
};

/** Tab and state panel transitions inside AnimatePresence mode="wait". */
export const tabPanel: Variants = {
  hidden: { opacity: 0, y: 4 },
  shown: { opacity: 1, y: 0, transition: quick },
  exit: { opacity: 0, y: -2, transition: { duration: 0.1, ease: EASE_OUT } },
};

/** Collapsible disclosure reveal: height 0 -> auto + fade, restoring overflow on end so focus rings stay unclipped. */
export const collapsibleReveal: Variants = {
  hidden: { opacity: 0, height: 0, overflow: "hidden" },
  shown: {
    opacity: 1,
    height: "auto",
    transition: { duration: 0.22, ease: EASE_OUT },
    transitionEnd: { overflow: "visible" },
  },
};

export const tapPress = { scale: 0.98 } as const;
export const choiceTapPress = { scale: 0.99 } as const;
