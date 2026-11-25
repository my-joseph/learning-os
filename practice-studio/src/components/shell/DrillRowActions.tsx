"use client";

import React, { useState } from "react";
import { Copy, MoreHorizontal, RotateCcw, Trash2 } from "lucide-react";
import { IconButton } from "@/components/ui/shadcn/Button";
import { RowMenu, RowMenuContent, RowMenuItem, RowMenuTrigger } from "@/components/ui/shadcn/Popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/shadcn/Tooltip";

export function DrillRowActions({
  nodeId,
  rowTitle,
  onReset,
  onDelete,
  open,
  onOpenChange,
  variant = "sidebar",
  tabIndex,
  onTooltipEscape,
}: {
  nodeId: string;
  rowTitle?: string;
  onReset?: (nodeId: string) => void;
  onDelete?: (nodeId: string) => void;
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
  const label = `Actions for ${rowTitle ?? nodeId}`;
  const triggerProps = {
    "aria-label": label,
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
        <IconButton
          {...triggerProps}
          tone="secondary"
          hitArea="sidebarAction"
          title="More actions"
        >
          <MoreHorizontal className="size-space-4" aria-hidden="true" />
        </IconButton>
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
      <RowMenuContent placement={variant} aria-label={label}>
        <RowMenuItem density="compact" onClick={copyId}>
          <Copy className="size-space-3_5" aria-hidden="true" />
          {copied ? "Copied" : "Copy ID"}
        </RowMenuItem>
        {onReset && (
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
        )}
        {onDelete && (
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
        )}
      </RowMenuContent>
    </RowMenu>
  );
}
