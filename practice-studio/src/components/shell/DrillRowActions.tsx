"use client";

import React, { useState } from "react";
import { Copy, MoreHorizontal, RotateCcw, Trash2 } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/shadcn/Popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/shadcn/Tooltip";
import { statusTone } from "@/lib/statusTone";

export function DrillRowActions({
  nodeId,
  onReset,
  onDelete,
  open,
  onOpenChange,
  variant = "sidebar",
  tabIndex,
  onTooltipEscape,
}: {
  nodeId: string;
  onReset: (nodeId: string) => void;
  onDelete: (nodeId: string) => void;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  variant?: "sidebar" | "search";
  tabIndex?: number;
  onTooltipEscape?: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const copyId = async () => {
    try {
      await navigator.clipboard.writeText(nodeId);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      // Clipboard permissions can be unavailable in non-secure browser contexts.
    }
  };

  const inSearch = variant === "search";
  const trigger = (
    <PopoverTrigger asChild>
      <button
        type="button"
        aria-label={`Actions for ${nodeId}`}
        aria-haspopup="menu"
        title={inSearch ? undefined : "More actions"}
        tabIndex={tabIndex}
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => event.stopPropagation()}
        className={inSearch
          ? "relative inline-flex size-11 shrink-0 items-center justify-center rounded-md text-foreground outline-none before:absolute before:inset-2 before:rounded-md hover:before:bg-zinc-300/70 focus-visible:before:ring-2 focus-visible:before:ring-inset focus-visible:before:ring-indigo-600 dark:hover:before:bg-zinc-600/60 dark:focus-visible:before:ring-indigo-400 sm:size-7 sm:before:inset-0 sm:[@media(any-pointer:coarse)]:size-11 sm:[@media(any-pointer:coarse)]:before:inset-2"
          : "relative mr-0.5 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-zinc-500 opacity-100 transition-colors hover:text-zinc-900 focus:outline-none dark:text-zinc-400 dark:hover:text-zinc-100 before:content-[''] before:absolute before:inset-2 before:rounded-full before:transition-colors hover:before:bg-zinc-300/70 dark:hover:before:bg-zinc-600/60 focus-visible:before:ring-2 focus-visible:before:ring-inset focus-visible:before:ring-zinc-500 dark:focus-visible:before:ring-zinc-400 lg:h-7 lg:w-7 lg:before:inset-0 lg:before:hidden lg:focus-visible:before:block lg:opacity-0 lg:group-hover/leaf:opacity-100 lg:focus-visible:opacity-100"
        }
      >
        <MoreHorizontal className="relative h-4 w-4" aria-hidden="true" />
      </button>
    </PopoverTrigger>
  );

  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      {inSearch ? (
        <Tooltip>
          <TooltipTrigger asChild>{trigger}</TooltipTrigger>
          {!open && (
            <TooltipContent side="top" onEscapeKeyDown={onTooltipEscape}>
              Actions
            </TooltipContent>
          )}
        </Tooltip>
      ) : trigger}
      <PopoverContent
        align="end"
        side={inSearch ? "bottom" : "right"}
        sideOffset={4}
        className={inSearch ? "z-[55] w-40 p-1" : "w-40 p-1"}
        role="menu"
        aria-label={`Actions for ${nodeId}`}
        onKeyDown={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          role="menuitem"
          onClick={copyId}
          className="flex min-h-8 w-full items-center gap-2 rounded px-2 text-left text-sm text-zinc-700 hover:bg-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 dark:text-zinc-200 dark:hover:bg-zinc-800 dark:focus-visible:ring-indigo-400"
        >
          <Copy className="h-3.5 w-3.5" aria-hidden="true" />
          {copied ? "Copied" : "Copy ID"}
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            onOpenChange(false);
            onReset(nodeId);
          }}
          className="flex min-h-8 w-full items-center gap-2 rounded px-2 text-left text-sm text-zinc-700 hover:bg-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 dark:text-zinc-200 dark:hover:bg-zinc-800 dark:focus-visible:ring-indigo-400"
        >
          <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
          Reset
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            onOpenChange(false);
            onDelete(nodeId);
          }}
          className={`flex min-h-8 w-full items-center gap-2 rounded px-2 text-left text-sm ${statusTone.wrong.text} hover:bg-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 dark:hover:bg-zinc-800 dark:focus-visible:ring-indigo-400`}
        >
          <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
          Delete
        </button>
      </PopoverContent>
    </Popover>
  );
}
