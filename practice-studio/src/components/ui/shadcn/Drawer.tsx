"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { drawer, drawerBottom, drawerLeft, fade } from "@/lib/motion";

export const Drawer = DialogPrimitive.Root;
export const DrawerTrigger = DialogPrimitive.Trigger;
export const DrawerClose = DialogPrimitive.Close;

export const DrawerPortal: React.FC<
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Portal>
> = ({ children, ...props }) => {
  if (typeof document === "undefined") {
    return <>{children}</>;
  }
  return <DialogPrimitive.Portal {...props}>{children}</DialogPrimitive.Portal>;
};

export interface DrawerContentProps
  extends React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> {
  overlayClassName?: string;
  side?: "right" | "left";
}

export const DrawerContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  DrawerContentProps
>(({ className, overlayClassName, side = "right", children, ...props }, ref) => {
  const isDesktop =
    typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia("(min-width: 768px)").matches
      : true;

  const isLeft = side === "left";
  const contentVariants = isLeft ? drawerLeft : isDesktop ? drawer : drawerBottom;
  const positionClass = isLeft
    ? "inset-y-0 left-0 right-auto h-full max-h-none w-[min(20rem,88vw)] rounded-none rounded-r-2xl"
    : "inset-x-0 bottom-0 max-h-[85vh] overflow-y-auto rounded-t-2xl md:inset-y-0 md:left-auto md:right-0 md:h-full md:max-h-none md:w-[min(24rem,90vw)] md:rounded-none md:rounded-l-2xl";

  return (
    <DrawerPortal>
      <DialogPrimitive.Overlay asChild>
        <m.div
          variants={fade}
          initial="hidden"
          animate="shown"
          className={cn("fixed inset-0 z-50 bg-zinc-950/70 motion-reduce:transition-none", overlayClassName)}
        />
      </DialogPrimitive.Overlay>
      <DialogPrimitive.Content ref={ref} asChild {...props}>
        <m.div
          variants={contentVariants}
          initial="hidden"
          animate="shown"
          className={cn("fixed z-50 border border-zinc-200 bg-background p-6 text-foreground shadow-xl motion-reduce:transition-none dark:border-zinc-800", positionClass, className)}
        >
          <DialogPrimitive.Close aria-label="Close drawer" className="absolute right-3 top-3 z-10 inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md text-zinc-500 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:focus-visible:ring-indigo-400">
            <X aria-hidden="true" className="h-4 w-4" />
          </DialogPrimitive.Close>
          {children}
        </m.div>
      </DialogPrimitive.Content>
    </DrawerPortal>
  );
});
DrawerContent.displayName = DialogPrimitive.Content.displayName;
export const DrawerTitle = DialogPrimitive.Title;
export const DrawerDescription = DialogPrimitive.Description;
