"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/cn";

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
}

export const DrawerContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  DrawerContentProps
>(({ className, overlayClassName, children, ...props }, ref) => (
  <DrawerPortal>
    <DialogPrimitive.Overlay className={cn("fixed inset-0 z-50 bg-zinc-950/70 motion-reduce:transition-none", overlayClassName)} />
    <DialogPrimitive.Content ref={ref} className={cn("fixed z-50 border border-zinc-200 bg-background p-6 text-foreground shadow-xl motion-reduce:transition-none dark:border-zinc-800", "inset-x-0 bottom-0 max-h-[85vh] overflow-y-auto rounded-t-2xl md:inset-y-0 md:left-auto md:right-0 md:h-full md:max-h-none md:w-[min(24rem,90vw)] md:rounded-none md:rounded-l-2xl", className)} {...props}>
      <DialogPrimitive.Close aria-label="Close drawer" className="absolute right-3 top-3 inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md text-zinc-500 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:focus-visible:ring-indigo-400">
        <X aria-hidden="true" className="h-4 w-4" />
      </DialogPrimitive.Close>
      {children}
    </DialogPrimitive.Content>
  </DrawerPortal>
));
DrawerContent.displayName = DialogPrimitive.Content.displayName;
export const DrawerTitle = DialogPrimitive.Title;
export const DrawerDescription = DialogPrimitive.Description;
