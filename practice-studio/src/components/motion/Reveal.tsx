"use client";

import React from "react";
import { AnimatePresence, m } from "motion/react";
import { presence, reveal } from "@/lib/motion";

/**
 * Opens/closes content in place. Height animates on an outer wrapper (overflow hidden) so the
 * inner element keeps its own margins, borders and rings. Already-open content does not animate on mount.
 */
export function Reveal({
  show,
  children,
  className,
}: {
  show: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <AnimatePresence initial={false}>
      {show && (
        <m.div variants={reveal} {...presence} style={{ overflow: "hidden" }}>
          <div className={className}>{children}</div>
        </m.div>
      )}
    </AnimatePresence>
  );
}
