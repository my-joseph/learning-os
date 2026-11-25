import React from "react";

/**
 * Bullet for structured UI lists. Pick the kind that matches the role of the list.
 * - "task"  (default): filled indigo dot for actions such as Visible tests.
 * - "info":  filled zinc dot for observations or notes.
 * - "limit": hollow indigo ring for limits such as Constraints.
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
