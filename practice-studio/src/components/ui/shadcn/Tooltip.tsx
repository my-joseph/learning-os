"use client";

import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { tooltipPop } from "@/lib/motion";

interface TooltipProviderContextValue {
  hasProvider: boolean;
  hydrated: boolean;
}

const TooltipProviderContext = React.createContext<TooltipProviderContextValue>({
  hasProvider: false,
  hydrated: false,
});

export const TooltipProvider: React.FC<
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Provider>
> = ({ delayDuration = 300, children, ...props }) => {
  const [hydrated, setHydrated] = React.useState(false);

  React.useEffect(() => {
    setHydrated(true);
  }, []);

  const contextValue = React.useMemo(
    () => ({ hasProvider: true, hydrated }),
    [hydrated]
  );

  return (
    <TooltipProviderContext.Provider value={contextValue}>
      <TooltipPrimitive.Provider delayDuration={delayDuration} {...props}>
        {children}
      </TooltipPrimitive.Provider>
    </TooltipProviderContext.Provider>
  );
};

export const Tooltip: React.FC<
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Root>
> = ({ children, ...props }) => {
  const { hasProvider } = React.useContext(TooltipProviderContext);
  if (hasProvider) {
    return <TooltipPrimitive.Root {...props}>{children}</TooltipPrimitive.Root>;
  }
  return (
    <TooltipProvider delayDuration={300}>
      <TooltipPrimitive.Root {...props}>{children}</TooltipPrimitive.Root>
    </TooltipProvider>
  );
};

/**
 * Wraps Radix TooltipTrigger and strips any SSR/no-JS fallback `title` attribute
 * after client hydration so the browser never shows a duplicate native tooltip
 * alongside the Radix tooltip.
 */
export const TooltipTrigger = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Trigger>
>(({ asChild, children, title, ...props }, ref) => {
  const { hydrated } = React.useContext(TooltipProviderContext);

  const resolvedChild =
    asChild &&
    hydrated &&
    React.isValidElement<{ title?: string }>(children) &&
    children.props.title !== undefined
      ? React.cloneElement(children, { title: undefined })
      : children;

  return (
    <TooltipPrimitive.Trigger
      ref={ref}
      asChild={asChild}
      title={hydrated ? undefined : title}
      {...props}
    >
      {resolvedChild}
    </TooltipPrimitive.Trigger>
  );
});
TooltipTrigger.displayName = TooltipPrimitive.Trigger.displayName;

/** SSR-safe TooltipPortal: renders inline on the server and portals into document.body in the browser. */
export const TooltipPortal: React.FC<
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Portal>
> = ({ children, ...props }) => {
  if (typeof document === "undefined") {
    return <>{children}</>;
  }
  return <TooltipPrimitive.Portal {...props}>{children}</TooltipPrimitive.Portal>;
};

export const TooltipContent = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 6, collisionPadding = 8, children, ...props }, ref) => (
  <TooltipPortal>
    <TooltipPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      collisionPadding={collisionPadding}
      asChild
      {...props}
    >
      <m.div
        variants={tooltipPop}
        initial="hidden"
        animate="shown"
        className={cn(
          "z-[60] max-w-xs rounded-lg border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-800 shadow-md motion-reduce:transition-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100",
          className
        )}
      >
        {children}
      </m.div>
    </TooltipPrimitive.Content>
  </TooltipPortal>
));
TooltipContent.displayName = TooltipPrimitive.Content.displayName;
