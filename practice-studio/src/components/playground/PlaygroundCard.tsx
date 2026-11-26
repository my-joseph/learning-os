import Link from "next/link";
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

export function PlaygroundCard({ experiment, children }: { experiment: PlaygroundExperiment; children: ReactNode }) {
  return (
    <Card asChild variant="playground" className="flex h-full flex-col overflow-hidden transition-colors hover:border-accent focus-visible:border-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background motion-reduce:transition-none">
      <Link href={`/playground/${experiment.id}`}>
        <div className="iso-figure-box bg-surface-raised">{children}</div>
        <PlaygroundCardFooter title={experiment.title} caption={experiment.caption} className="flex-1" />
      </Link>
    </Card>
  );
}
