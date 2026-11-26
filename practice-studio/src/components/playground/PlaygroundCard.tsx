import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import type { ReactNode } from "react";
import { Card, CardFooter } from "@/components/ui/shadcn/Card";
import { cn } from "@/lib/cn";
import type { PlaygroundExperiment } from "./experiments";

export function PlaygroundCardFooter({ title, caption, className }: {
  title: ReactNode;
  caption: ReactNode;
  className?: string;
}) {
  return (
    <CardFooter className={cn("justify-between gap-space-2 border-t border-border px-space-4 py-space-3", className)}>
      <span className="shrink-0 font-sans text-sm font-semibold">{title}</span>
      <span className="min-w-0 break-words text-right font-mono text-xs text-foreground-secondary">{caption}</span>
    </CardFooter>
  );
}

/**
 * Playground card: the figure is live and interactive right in the grid (drag, hover,
 * keyboard). The footer title links to the detail page with the full readout.
 */
export function PlaygroundCard({ experiment, children }: {
  experiment: PlaygroundExperiment;
  children: ReactNode;
}) {
  return (
    <Card variant="playground" data-showcase={experiment.id === "ui-components" ? undefined : "grid"} className="flex h-full flex-col overflow-hidden transition-colors hover:border-accent focus-within:border-accent motion-reduce:transition-none">
      <div className="iso-figure-box bg-surface-raised">{children}</div>
      <PlaygroundCardFooter
        className="flex-1"
        title={
          <Link
            href={`/playground/${experiment.id}`}
            className="inline-flex items-center gap-space-1 rounded-sm hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {experiment.title}
            <ArrowUpRight aria-hidden="true" className="size-space-3_5 text-foreground-secondary" />
          </Link>
        }
        caption={experiment.caption}
      />
    </Card>
  );
}
