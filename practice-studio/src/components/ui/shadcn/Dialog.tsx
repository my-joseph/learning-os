"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { dialogCard, fade } from "@/lib/motion";

const DialogOpenContext = React.createContext<boolean>(false);

export const Dialog: React.FC<
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Root>
> = ({ open, defaultOpen, children, ...props }) => (
  <DialogOpenContext.Provider value={Boolean(open ?? defaultOpen)}>
    <DialogPrimitive.Root open={open} defaultOpen={defaultOpen} {...props}>
      {children}
    </DialogPrimitive.Root>
  </DialogOpenContext.Provider>
);
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export const DialogPortal: React.FC<
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Portal>
> = ({ children, ...props }) => {
  const ssrOpen = React.useContext(DialogOpenContext);
  if (typeof document === "undefined") {
    return ssrOpen ? <>{children}</> : null;
  }
  return <DialogPrimitive.Portal {...props}>{children}</DialogPrimitive.Portal>;
};

export const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay ref={ref} asChild {...props}>
    <m.div
      variants={fade}
      initial="hidden"
      animate="shown"
      className={cn("fixed inset-0 z-50 bg-zinc-950/70 motion-reduce:transition-none", className)}
    />
  </DialogPrimitive.Overlay>
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

export const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> & { position?: "center" | "top" }
>(({ className, children, position = "center", ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <div className={cn(
      "fixed inset-0 z-50 flex",
      position === "top"
        ? "h-dvh items-start justify-center px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-[max(1rem,env(safe-area-inset-top))] lg:pt-[max(12dvh,env(safe-area-inset-top))]"
        : "items-center justify-center p-4",
      "pointer-events-none"
    )}>
      <DialogPrimitive.Content ref={ref} asChild {...props}>
        <m.div
          variants={dialogCard}
          initial="hidden"
          animate="shown"
          className={cn("pointer-events-auto relative w-full max-w-lg rounded-xl border border-zinc-200 bg-background p-6 text-foreground shadow-xl motion-reduce:transition-none dark:border-zinc-800", position === "top" && "origin-top", className)}
        >
          {children}
          <DialogPrimitive.Close aria-label="Close dialog" className="absolute right-3 top-3 inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md text-zinc-500 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:focus-visible:ring-indigo-400">
            <X aria-hidden="true" className="h-4 w-4" />
          </DialogPrimitive.Close>
        </m.div>
      </DialogPrimitive.Content>
    </div>
  </DialogPortal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;

export const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => <DialogPrimitive.Title ref={ref} className={cn("text-lg font-semibold", className)} {...props} />);
DialogTitle.displayName = DialogPrimitive.Title.displayName;

export const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => <DialogPrimitive.Description ref={ref} className={cn("mt-2 text-sm text-zinc-600 dark:text-zinc-400", className)} {...props} />);
DialogDescription.displayName = DialogPrimitive.Description.displayName;
