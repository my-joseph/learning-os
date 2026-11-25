"use client";

import React, { useState } from "react";
import { Copy, MoreHorizontal, RotateCcw, Trash2 } from "lucide-react";
import { IconButton } from "@/components/ui/shadcn/Button";
import { RowMenu, RowMenuContent, RowMenuItem, RowMenuTrigger } from "@/components/ui/shadcn/Popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/shadcn/Tooltip";

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
  const triggerProps = {
    "aria-label": `Actions for ${nodeId}`,
    "aria-haspopup": "menu" as const,
    tabIndex,
    onClick: (event: React.MouseEvent) => event.stopPropagation(),
    onKeyDown: (event: React.KeyboardEvent) => event.stopPropagation(),
  };
  const trigger = (
    <RowMenuTrigger asChild>
      {inSearch ? (
        <IconButton {...triggerProps} size="xs" hitArea="padded">
          <MoreHorizontal className="size-space-4" aria-hidden="true" />
        </IconButton>
      ) : (
        <button
          {...triggerProps}
          type="button"
          title="More actions"
          className="relative mr-0.5 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-zinc-500 opacity-100 transition-colors hover:text-zinc-900 focus:outline-none dark:text-zinc-400 dark:hover:text-zinc-100 before:content-[''] before:absolute before:inset-2 before:rounded-full before:transition-colors hover:before:bg-zinc-300/70 dark:hover:before:bg-zinc-600/60 focus-visible:before:ring-2 focus-visible:before:ring-inset focus-visible:before:ring-zinc-500 dark:focus-visible:before:ring-zinc-400 lg:h-7 lg:w-7 lg:before:inset-0 lg:before:hidden lg:focus-visible:before:block lg:opacity-0 lg:group-hover/leaf:opacity-100 lg:focus-visible:opacity-100"
        >
          <MoreHorizontal className="relative h-4 w-4" aria-hidden="true" />
        </button>
      )}
    </RowMenuTrigger>
  );

  return (
    <RowMenu open={open} onOpenChange={onOpenChange}>
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
      <RowMenuContent placement={variant} aria-label={`Actions for ${nodeId}`}>
        <RowMenuItem density="compact" onClick={copyId}>
          <Copy className="size-space-3_5" aria-hidden="true" />
          {copied ? "Copied" : "Copy ID"}
        </RowMenuItem>
        <RowMenuItem
          density="compact"
          onClick={() => {
            onOpenChange(false);
            onReset(nodeId);
          }}
        >
          <RotateCcw className="size-space-3_5" aria-hidden="true" />
          Reset
        </RowMenuItem>
        <RowMenuItem
          density="compact"
          tone="destructive"
          onClick={() => {
            onOpenChange(false);
            onDelete(nodeId);
          }}
        >
          <Trash2 className="size-space-3_5" aria-hidden="true" />
          Delete
        </RowMenuItem>
      </RowMenuContent>
    </RowMenu>
  );
}
