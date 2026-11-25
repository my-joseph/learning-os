import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/cn";

export interface CardProps extends React.HTMLAttributes<HTMLElement> {
  asChild?: boolean;
  variant?: "default" | "feedback" | "assistPanel" | "assistStep";
}

const cardVariants = {
  default: "w-full min-w-0 rounded-2xl border border-zinc-200 bg-white text-foreground shadow-sm dark:border-zinc-800 dark:bg-zinc-900",
  feedback: "rounded-xl p-space-3_5 sm:p-space-4 space-y-space-2_5",
  assistPanel: "rounded-xl border border-border bg-surface-panel p-space-4",
  assistStep: "rounded-xl border border-border bg-surface-raised p-space-3",
};

export const Card = React.forwardRef<HTMLElement, CardProps>(
  ({ asChild = false, variant = "default", className, ...props }, ref) => {
    const cardClassName = cn(cardVariants[variant], className);

    if (asChild) {
      return <Slot ref={ref} className={cardClassName} {...props} />;
    }

    return <div ref={ref as React.Ref<HTMLDivElement>} className={cardClassName} {...props} />;
  }
);
Card.displayName = "Card";

export const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn("flex flex-col gap-1.5 p-5", className)} {...props} />
);
CardHeader.displayName = "CardHeader";

export const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => <h3 ref={ref} className={cn("text-lg font-semibold leading-none tracking-tight", className)} {...props} />
);
CardTitle.displayName = "CardTitle";

export const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => <p ref={ref} className={cn("text-sm text-zinc-600 dark:text-zinc-400", className)} {...props} />
);
CardDescription.displayName = "CardDescription";

export const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn("p-5 pt-0", className)} {...props} />
);
CardContent.displayName = "CardContent";

export const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn("flex items-center p-5 pt-0", className)} {...props} />
);
CardFooter.displayName = "CardFooter";
