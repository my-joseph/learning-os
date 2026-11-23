"use client";

import * as React from "react";
import * as AlertDialogPrimitive from "@radix-ui/react-alert-dialog";
import { m } from "motion/react";
import { Button, type ButtonProps } from "@/components/ui/shadcn/Button";
import { cn } from "@/lib/cn";
import { dialogCard, fade } from "@/lib/motion";

const AlertDialogOpenContext = React.createContext<boolean>(false);

export const AlertDialog: React.FC<
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Root>
> = ({ open, defaultOpen, children, ...props }) => (
  <AlertDialogOpenContext.Provider value={Boolean(open ?? defaultOpen)}>
    <AlertDialogPrimitive.Root open={open} defaultOpen={defaultOpen} {...props}>
      {children}
    </AlertDialogPrimitive.Root>
  </AlertDialogOpenContext.Provider>
);
export const AlertDialogTrigger = AlertDialogPrimitive.Trigger;

export const AlertDialogPortal: React.FC<
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Portal>
> = ({ children, ...props }) => {
  const ssrOpen = React.useContext(AlertDialogOpenContext);
  if (typeof document === "undefined") {
    return ssrOpen ? <>{children}</> : null;
  }
  return <AlertDialogPrimitive.Portal {...props}>{children}</AlertDialogPrimitive.Portal>;
};

export const AlertDialogOverlay = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Overlay ref={ref} asChild {...props}>
    <m.div
      variants={fade}
      initial="hidden"
      animate="shown"
      className={cn("fixed inset-0 z-50 bg-zinc-950/70 motion-reduce:transition-none", className)}
    />
  </AlertDialogPrimitive.Overlay>
));
AlertDialogOverlay.displayName = AlertDialogPrimitive.Overlay.displayName;

export const AlertDialogContent = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <AlertDialogPortal>
    <AlertDialogOverlay />
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
      <AlertDialogPrimitive.Content ref={ref} asChild {...props}>
        <m.div
          variants={dialogCard}
          initial="hidden"
          animate="shown"
          className={cn("pointer-events-auto relative grid w-full max-w-lg gap-4 rounded-2xl border border-zinc-200 bg-white p-6 text-foreground shadow-xl motion-reduce:transition-none dark:border-zinc-800 dark:bg-zinc-900", className)}
        >
          {children}
        </m.div>
      </AlertDialogPrimitive.Content>
    </div>
  </AlertDialogPortal>
));
AlertDialogContent.displayName = AlertDialogPrimitive.Content.displayName;

export const AlertDialogHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col gap-2 text-left", className)} {...props} />
);
AlertDialogHeader.displayName = "AlertDialogHeader";

export const AlertDialogFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col-reverse gap-2 sm:flex-row sm:justify-end", className)} {...props} />
);
AlertDialogFooter.displayName = "AlertDialogFooter";

export const AlertDialogTitle = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Title ref={ref} className={cn("text-lg font-semibold", className)} {...props} />
));
AlertDialogTitle.displayName = AlertDialogPrimitive.Title.displayName;

export const AlertDialogDescription = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Description ref={ref} className={cn("text-sm text-zinc-600 dark:text-zinc-400", className)} {...props} />
));
AlertDialogDescription.displayName = AlertDialogPrimitive.Description.displayName;

export const AlertDialogAction = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Action>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Action> & {
    variant?: ButtonProps["variant"];
    size?: ButtonProps["size"];
  }
>(({ className, variant = "destructive", size, ...props }, ref) => (
  <AlertDialogPrimitive.Action ref={ref} asChild>
    <Button variant={variant} size={size} className={className} {...props} />
  </AlertDialogPrimitive.Action>
));
AlertDialogAction.displayName = AlertDialogPrimitive.Action.displayName;

export const AlertDialogCancel = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Cancel>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Cancel> & {
    variant?: ButtonProps["variant"];
    size?: ButtonProps["size"];
  }
>(({ className, variant = "secondary", size, ...props }, ref) => (
  <AlertDialogPrimitive.Cancel ref={ref} asChild>
    <Button variant={variant} size={size} className={className} {...props} />
  </AlertDialogPrimitive.Cancel>
));
AlertDialogCancel.displayName = AlertDialogPrimitive.Cancel.displayName;
