import Link from "next/link";
import type { ReactNode } from "react";
import { Card, CardFooter } from "@/components/ui/shadcn/Card";
import { cn } from "@/lib/cn";
import type { LabExperiment } from "./experiments";

export function LabCardFooter({ title, caption, className }: {
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

export function LabCard({ experiment, children }: { experiment: LabExperiment; children: ReactNode }) {
  return (
    <Card asChild variant="lab" className="flex h-full flex-col overflow-hidden transition-colors hover:border-accent focus-visible:border-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background motion-reduce:transition-none">
      <Link href={`/lab/${experiment.id}`}>
        <div className="iso-figure-box bg-surface-raised">{children}</div>
        <LabCardFooter title={experiment.title} caption={experiment.caption} className="flex-1" />
      </Link>
    </Card>
  );
}
