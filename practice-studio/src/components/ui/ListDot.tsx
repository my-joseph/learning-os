import React from "react";

/**
 * Global list bullet (learner decisions 2026-11-19). Three kinds, chosen by what the list means:
 * - "task"  (default): filled indigo dot — what the learner must do (Requirements, Your task, Visible tests).
 * - "info":  filled zinc dot — information / observations (Observed symptoms, notes, other headings).
 * - "limit": hollow indigo ring — limits and contracts (Return contract, Constraints, Input shape).
 * Always centred on the first text line of the item.
 */
export type ListKind = "task" | "info" | "limit";

const DOT_CLASS: Record<ListKind, string> = {
  task: "w-1.5 h-1.5 rounded-full bg-indigo-600 dark:bg-indigo-400",
  info: "w-1.5 h-1.5 rounded-full bg-zinc-400 dark:bg-zinc-500",
  limit: "w-[7px] h-[7px] rounded-full border-[1.5px] border-indigo-600 dark:border-indigo-400",
};

export const ListDot: React.FC<{ kind?: ListKind; className?: string }> = ({
  kind = "task",
  className = "",
}) => (
  <span
    className={`h-[1lh] flex items-center shrink-0 select-none ${className}`}
    aria-hidden="true"
    data-list-kind={kind}
  >
    <span className={DOT_CLASS[kind]} />
  </span>
);

/** Pick the list kind from the heading text above a list (case-insensitive keyword match). */
export function listKindForHeading(heading: string | null | undefined): ListKind {
  const h = (heading || "").toLowerCase();
  if (!h) return "info";
  if (/(contract|constraint|limit|bound|shape|edge case|return value|returns?\b)/.test(h)) return "limit";
  if (/(requirement|your task|task|must|rule|validation|implement|steps? to|goal)/.test(h)) return "task";
  return "info";
}
