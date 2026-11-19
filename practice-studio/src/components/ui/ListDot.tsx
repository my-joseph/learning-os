import React from "react";

/**
 * Global list bullet (learner decision 2026-11-19): a small indigo dot, vertically centred on the
 * first line of the item's text. Use for every bulleted list in the Studio (prompt lists,
 * constraints, visible tests, review findings) instead of "•" glyphs or list-disc.
 */
export const ListDot: React.FC<{ className?: string }> = ({ className = "" }) => (
  <span className={`h-[1lh] flex items-center shrink-0 select-none ${className}`} aria-hidden="true">
    <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 dark:bg-indigo-400" />
  </span>
);
