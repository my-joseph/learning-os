"use client";

import * as React from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import { cva, type VariantProps } from "class-variance-authority";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { popover } from "@/lib/motion";

export const Popover = PopoverPrimitive.Root;
export const PopoverTrigger = PopoverPrimitive.Trigger;
export const PopoverAnchor = PopoverPrimitive.Anchor;
export const PopoverClose = PopoverPrimitive.Close;

export const PopoverContent = React.forwardRef<
  React.ElementRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(({ className, align = "center", sideOffset = 6, children, ...props }, ref) => (
  <PopoverPrimitive.Portal>
    <PopoverPrimitive.Content ref={ref} align={align} sideOffset={sideOffset} asChild {...props}>
      <m.div
        variants={popover}
        initial="hidden"
        animate="shown"
        className={cn("z-overlay w-72 rounded-lg border border-border bg-background p-4 text-foreground shadow-ui-lg outline-none motion-reduce:transition-none", className)}
      >
        {children}
      </m.div>
    </PopoverPrimitive.Content>
  </PopoverPrimitive.Portal>
));
PopoverContent.displayName = PopoverPrimitive.Content.displayName;


const rowMenuVariants = cva("w-space-40 p-space-1", {
  variants: {
    placement: { sidebar: "", search: "z-overlay-menu" },
  },
  defaultVariants: { placement: "sidebar" },
});

export const RowMenu = Popover;
export const RowMenuTrigger = PopoverTrigger;

export const RowMenuContent = React.forwardRef<
  React.ElementRef<typeof PopoverContent>,
  Omit<React.ComponentPropsWithoutRef<typeof PopoverContent>, "align" | "side" | "sideOffset" | "role"> &
    VariantProps<typeof rowMenuVariants>
>(({ placement = "sidebar", className, onKeyDown, ...props }, ref) => (
  <PopoverContent
    {...props}
    ref={ref}
    role="menu"
    align="end"
    side={placement === "search" ? "bottom" : "right"}
    sideOffset={4}
    className={cn(rowMenuVariants({ placement }), className)}
    onKeyDown={(event) => {
      event.stopPropagation();
      onKeyDown?.(event);
    }}
  />
));
RowMenuContent.displayName = "RowMenuContent";

const rowMenuItemVariants = cva(
  "flex w-full items-center gap-space-2 rounded px-space-2 text-left text-sm hover:bg-surface-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent data-[selected=true]:bg-surface-selected/60 disabled:pointer-events-none disabled:opacity-disabled",
  {
    variants: {
      size: { xs: "min-h-control-xs", sm: "min-h-control-sm", md: "min-h-control-md" },
      tone: {
        default: "text-foreground-menu",
        secondary: "text-muted",
        primary: "text-accent",
        destructive: "text-status-wrong",
      },
      density: { compact: "", touch: "[@media(any-pointer:coarse)]:min-h-touch" },
    },
    defaultVariants: { size: "sm", tone: "default", density: "touch" },
  }
);

type RowMenuItemProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof rowMenuItemVariants> & { selected?: boolean; loading?: boolean };

export const RowMenuItem = React.forwardRef<HTMLButtonElement, RowMenuItemProps>(
  ({ size, tone, density, selected, loading, disabled, className, ...props }, ref) => (
    <button
      {...props}
      ref={ref}
      type="button"
      role="menuitem"
      className={cn(rowMenuItemVariants({ size, tone, density }), className)}
      data-selected={selected}
      aria-busy={loading || undefined}
      disabled={disabled || loading}
    />
  )
);
RowMenuItem.displayName = "RowMenuItem";
