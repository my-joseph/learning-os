"use client";

import * as React from "react";
import { Slot, Slottable } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { HoverCard, HoverCardContent, HoverCardRowTrigger } from "./shadcn/HoverCard";

const rowVariants = cva(
  "items-center rounded-md data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-disabled aria-busy:pointer-events-none aria-busy:opacity-disabled",
  {
    variants: {
      variant: {
        sidebar: "group/row inline-flex w-full shrink-0 gap-space-2 px-space-1_5 text-left text-sm transition-colors duration-color ease-standard focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-muted motion-reduce:transition-none",
        command: "flex cursor-pointer select-none gap-space-3 px-space-2 py-space-1 text-sm",
        tree: "flex h-control-sm min-w-0 gap-space-1_5 pr-space-1_5 text-left transition-colors focus:outline-none",
      },
      size: {
        xs: "min-h-control-xs",
        sm: "min-h-control-sm",
        md: "min-h-control-md",
      },
      tone: {
        default: "text-foreground-control",
        secondary: "text-foreground-secondary",
        primary: "text-accent",
        destructive: "text-status-wrong",
      },
      touchTarget: {
        roomy: "max-sm:min-h-touch max-sm:min-w-touch [@media(any-pointer:coarse)]:min-h-touch [@media(any-pointer:coarse)]:min-w-touch",
        expanded: "relative expand-touch-target",
      },
    },
    compoundVariants: [
      { variant: "sidebar", class: "hover:bg-surface-selected/50 data-[selected=true]:bg-surface-selected/50 dark:hover:bg-surface-selected/40 dark:data-[selected=true]:bg-surface-selected/40" },
      { variant: "command", class: "data-[selected=true]:bg-surface-selected/60" },
      { variant: "command", tone: ["default", "secondary"], class: "data-[selected=true]:text-foreground [@media(hover:hover)]:hover:text-foreground" },
    ],
    defaultVariants: { variant: "sidebar", size: "sm", tone: "default", touchTarget: "roomy" },
  }
);

const treeIndent = {
  1: "pl-space-1_5",
  2: "pl-space-4",
  3: "pl-tree-depth-3",
  4: "pl-control-md",
};

const treeHover = "hover:bg-surface-selected/50 dark:hover:bg-surface-selected/40";

type ListRowProps = React.ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof rowVariants> & {
  asChild?: boolean;
  label?: React.ReactNode;
  leading?: React.ReactNode;
  trailing?: React.ReactNode;
  emphasis?: "normal" | "medium";
  selected?: boolean;
  loading?: boolean;
  treeDepth?: keyof typeof treeIndent;
  treeRow?: {
    action?: React.ReactNode;
    actionOpen?: boolean;
    highlighted?: boolean;
    preview?: React.ReactNode;
    surfaceProps?: React.HTMLAttributes<HTMLDivElement> & {
      [attribute: `data-${string}`]: string | boolean | undefined;
    };
  };
};

export const ListRow = React.forwardRef<HTMLElement, ListRowProps>(
  ({
    asChild, variant = "sidebar", tone = variant === "command" ? "secondary" : "default",
    size = variant === "command" ? "md" : "sm", touchTarget, selected, disabled, loading,
    label, leading, trailing, emphasis = variant === "command" ? "medium" : "normal",
    treeDepth = 1, treeRow, className, type = "button", children, ...props
  }, ref) => {
    const hasTrailing = trailing != null && trailing !== false;
    const isTree = variant === "tree";
    const classes = cn(
      rowVariants({ variant, size: isTree ? null : size, tone, touchTarget: isTree ? null : touchTarget }),
      isTree && treeIndent[treeDepth],
      isTree && (treeRow ? "flex-1 overflow-hidden bg-transparent" : `w-full ${treeHover}`),
      isTree && "text-sm",
      variant === "command" && hasTrailing && "pr-space-12 [@media(hover:hover)]:group-hover/row:text-foreground sm:pr-space-10 sm:[@media(any-pointer:coarse)]:pr-space-12",
      className
    );
    const title = label != null && (
      <span
        data-tree-row-label={isTree || undefined}
        className={cn(
          "min-w-0 flex-1 truncate",
          (isTree ? selected : emphasis === "medium") && "font-medium",
          isTree && !selected && "font-normal"
        )}
      >
        {label}
      </span>
    );
    const sidebarTrailing = variant === "sidebar" && hasTrailing && (
      <span className="flex shrink-0 opacity-hidden [@media(hover:hover)]:group-hover/row:opacity-visible group-focus-visible/row:opacity-visible group-data-[selected=true]/row:opacity-visible">
        {trailing}
      </span>
    );

    const row = asChild ? (
      <Slot {...props} ref={ref} className={classes} aria-busy={loading || undefined}>
        {leading}
        {title}
        <Slottable>{children}</Slottable>
        {sidebarTrailing}
        {isTree && trailing}
      </Slot>
    ) : (
      <Slot ref={ref}>
        <button
          {...props}
          type={type}
          className={classes}
          data-selected={selected}
          data-disabled={disabled || loading || undefined}
          aria-busy={loading || undefined}
          disabled={disabled || loading}
        >
          {leading}
          {title}
          {children}
          {sidebarTrailing}
          {isTree && trailing}
        </button>
      </Slot>
    );

    if (isTree && treeRow) {
      const { action, actionOpen, highlighted, preview, surfaceProps } = treeRow;
      const Surface = preview ? HoverCardRowTrigger : "div";
      const surface = (
        <Surface
          {...surfaceProps}
          data-menu-open={actionOpen || undefined}
          data-selected={selected || undefined}
          data-tree-row-actions={action ? true : undefined}
          className={cn(
            "flex h-control-sm w-full min-w-0 items-center overflow-visible rounded-md transition-colors",
            selected || actionOpen
              ? "bg-surface-selected/70 dark:bg-surface-selected/60"
              : highlighted
                ? "bg-surface-hover dark:bg-surface-hover/80"
                : treeHover,
            surfaceProps?.className
          )}
        >
          {row}
          {action && <div data-tree-row-action className="shrink-0">{action}</div>}
        </Surface>
      );
      if (!preview) return surface;
      return (
        <HoverCard openDelay={500} closeDelay={100}>
          {surface}
          {!actionOpen && (
            <HoverCardContent
              side="right"
              align="start"
              sideOffset={22}
              collisionPadding={8}
              data-tree-row-preview
              className="pointer-events-none w-80 max-w-[var(--radix-hover-card-content-available-width)]"
            >
              {preview}
            </HoverCardContent>
          )}
        </HoverCard>
      );
    }

    if (variant !== "command" || !hasTrailing) return row;
    return (
      <div role="presentation" data-selected={selected} className="group/row relative">
        {row}
        <div className="pointer-events-none absolute inset-y-0 right-space-1 flex items-center opacity-hidden [@media(hover:hover)]:group-hover/row:pointer-events-auto [@media(hover:hover)]:group-hover/row:opacity-visible group-focus-within/row:pointer-events-auto group-focus-within/row:opacity-visible group-data-[selected=true]/row:pointer-events-auto group-data-[selected=true]/row:opacity-visible">
          {trailing}
        </div>
      </div>
    );
  }
);
ListRow.displayName = "ListRow";
