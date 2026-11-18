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

/** Spread on an `m.*` element inside <AnimatePresence>. */
export const presence = { initial: "hidden", animate: "shown", exit: "hidden" } as const;
