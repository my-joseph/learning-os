"use client";

import type { ReactNode } from "react";
import { Heading } from "@/components/ui/Heading";
import { Numeral } from "@/components/ui/Numeral";
import { Button } from "@/components/ui/shadcn/Button";
import { Card } from "@/components/ui/shadcn/Card";
import { resetShowcase } from "@/lib/isometric/showcaseStage";
import { cn } from "@/lib/cn";
import { PlaygroundCardFooter } from "./PlaygroundCard";

export function PlaygroundShowcase({ title, caption, figure, readout, reset, onReset }: {
  title: ReactNode;
  caption: ReactNode;
  figure: ReactNode;
  readout?: ReactNode;
  reset?: boolean;
  onReset?: () => void;
}) {
  return (
    <Card asChild variant="playground" className="iso-studio-surface">
      <section data-showcase="detail">
        <div className={cn("grid", readout && "lg:grid-cols-5")}>
          <div className={cn("flex min-w-0 flex-col justify-center p-space-4 sm:p-space-5", readout && "lg:col-span-3")}>
            <div className="mx-auto w-full max-w-2xl">{figure}</div>
            {reset && (
              <Button
                variant="outline"
                size="compact"
                className="self-end"
                onClick={(event) => { resetShowcase(event.currentTarget); onReset?.(); }}
              >
                Reset
              </Button>
            )}
          </div>
          {readout}
        </div>
        <PlaygroundCardFooter title={title} caption={caption} />
      </section>
    </Card>
  );
}

export function PlaygroundReadout({ action, children }: { action?: ReactNode; children: ReactNode }) {
  return (
    <div className="min-w-0 space-y-space-4 border-t border-border p-space-4 sm:p-space-5 lg:col-span-2 lg:border-l lg:border-t-0">
      <div className="flex flex-wrap items-center justify-between gap-space-2">
        <Heading variant="section">Live readout</Heading>
        {action}
      </div>
      {children}
    </div>
  );
}

export function PlaygroundStats({ children }: { children: ReactNode }) {
  return <dl className="grid grid-cols-2 gap-space-3">{children}</dl>;
}

export function PlaygroundStat({ label, value, detail, testId }: {
  label: ReactNode;
  value: ReactNode;
  detail?: ReactNode;
  testId?: string;
}) {
  return (
    <div className="min-w-0 space-y-space-1 rounded-lg border border-border bg-surface-panel p-space-3">
      <dt className="text-xs text-foreground-secondary">{label}</dt>
      <dd data-testid={testId}>
        <Numeral variant="lg" className="text-lg">{value}</Numeral>
        {detail && <span className="block text-xs text-foreground-secondary">{detail}</span>}
      </dd>
    </div>
  );
}
