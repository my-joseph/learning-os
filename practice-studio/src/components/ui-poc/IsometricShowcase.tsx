"use client";

import React, { useCallback, useState } from "react";
import { LazyCube, LazyPulley } from "@/components/isometric/LazyFigures";
import { Heading } from "@/components/ui/Heading";
import { Numeral } from "@/components/ui/Numeral";
import { ThemeToggleButton } from "@/components/ui/ThemeToggleButton";
import { Card, CardContent } from "@/components/ui/shadcn/Card";
import { SegmentedChips } from "@/components/ui/shadcn/Tabs";
import { TooltipProvider } from "@/components/ui/shadcn/Tooltip";
import { useTheme } from "@/hooks/useTheme";

const LOAD_KG = 40;
const RATIO_OPTIONS = [
  { value: "2", label: "2:1" },
  { value: "4", label: "4:1" },
] as const;

type PulleyTelemetry = {
  ropePulled: string;
  loadRaised: string;
  effortKg: string;
  caption: string;
};

function parsePulleyRead(text: string, ratio: 2 | 4, loadKg: number): Partial<PulleyTelemetry> {
  const stepMatch = text.match(/^pull\s+([\d.]+)\s+·\s+lift\s+([\d.]+)\s+·\s+(\d+):1\s+·\s+([\d.]+)\s+kg/);
  if (stepMatch) {
    return {
      ropePulled: stepMatch[1],
      loadRaised: stepMatch[2],
      effortKg: `${stepMatch[4]} kg`,
      caption: text,
    };
  }
  const notchMatch = text.match(/^Pulled a notch\s+·\s+lift\s+([\d.]+)/);
  if (notchMatch) {
    const lift = Number(notchMatch[1]);
    return {
      ropePulled: String(Math.round(lift * ratio)),
      loadRaised: lift.toFixed(1),
      effortKg: `${Math.round(loadKg / ratio)} kg`,
      caption: text,
    };
  }
  if (text.startsWith("Ratchet released")) {
    return {
      ropePulled: "0",
      loadRaised: "0.0",
      effortKg: `${Math.round(loadKg / ratio)} kg`,
      caption: text,
    };
  }
  return { caption: text };
}

export function IsometricShowcase() {
  const { theme, handleToggleTheme } = useTheme();
  const [cubeCaption, setCubeCaption] = useState("cube");
  const [ratio, setRatio] = useState<2 | 4>(2);
  const [lastActivated, setLastActivated] = useState<string | null>(null);
  const [telemetry, setTelemetry] = useState<PulleyTelemetry>({
    ropePulled: "0",
    loadRaised: "0.0",
    effortKg: `${Math.round(LOAD_KG / 2)} kg`,
    caption: "2:1 · 40 kg",
  });

  const handleRatioChange = useCallback((next: string) => {
    const nextRatio: 2 | 4 = next === "4" ? 4 : 2;
    setRatio(nextRatio);
    setTelemetry({
      ropePulled: "0",
      loadRaised: "0.0",
      effortKg: `${Math.round(LOAD_KG / nextRatio)} kg`,
      caption: `${nextRatio}:1 · ${LOAD_KG} kg`,
    });
  }, []);

  const handlePulleyRead = useCallback(
    (text: string) => {
      setTelemetry((prev) => ({
        ...prev,
        ...parsePulleyRead(text, ratio, LOAD_KG),
      }));
    },
    [ratio]
  );

  const handlePulleyActivate = useCallback((part: string) => {
    setLastActivated(part);
  }, []);

  return (
    <TooltipProvider>
      <main className="mx-auto min-h-screen w-full max-w-5xl bg-background px-space-4 py-space-8 text-foreground sm:px-space-6">
        <header className="mb-space-8 flex flex-wrap items-start justify-between gap-space-4">
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wider text-accent">
              UI Proof of Concept
            </p>
            <Heading className="mt-space-1 text-3xl sm:text-4xl">
              Isometric Figures
            </Heading>
            <p className="mt-space-2 max-w-2xl text-sm text-foreground-subtle">
              Client-only SVG figures themed with Practice Studio surface, foreground, border, and accent tokens.
            </p>
          </div>
          <ThemeToggleButton
            theme={theme}
            onToggle={handleToggleTheme}
            className="min-h-touch min-w-touch border border-border-control"
          />
        </header>

        <section
          aria-label="Isometric figure showcase"
          className="grid grid-cols-1 gap-space-6 lg:grid-cols-12"
        >
          <Card className="iso-studio-surface flex flex-col overflow-hidden bg-surface-raised border-border lg:col-span-5">
            <div className="p-space-3">
              <LazyCube onRead={setCubeCaption} />
            </div>
            <div className="mt-auto flex items-center justify-between gap-space-3 border-t border-border px-space-4 py-space-3">
              <span className="text-sm font-semibold text-foreground">Cube</span>
              <span className="font-mono text-xs text-foreground-secondary" data-testid="cube-caption">
                {cubeCaption}
              </span>
            </div>
          </Card>

          <Card className="iso-studio-surface overflow-hidden bg-surface-raised border-border lg:col-span-7">
            <div className="grid h-full grid-cols-1 md:grid-cols-12">
              <div className="flex flex-col md:col-span-7 md:border-r md:border-border">
                <div className="p-space-3">
                  <LazyPulley
                    ratio={ratio}
                    load={LOAD_KG}
                    onRead={handlePulleyRead}
                    onActivate={handlePulleyActivate}
                  />
                </div>
                <div className="mt-auto flex min-w-0 items-center justify-between gap-space-3 border-t border-border px-space-4 py-space-3">
                  <span className="shrink-0 text-sm font-semibold text-foreground">Pulley</span>
                  <span className="min-w-0 truncate font-mono text-xs text-foreground-secondary" data-testid="pulley-caption">
                    {telemetry.caption}
                  </span>
                </div>
              </div>

              <CardContent className="flex flex-col justify-between gap-space-4 p-space-5 md:col-span-5">
                <div className="space-y-space-4">
                  <div className="flex items-center justify-between gap-space-2">
                    <Heading variant="section" className="text-base">
                      Live readout
                    </Heading>
                    <SegmentedChips
                      label="Mechanical advantage ratio"
                      options={RATIO_OPTIONS}
                      value={String(ratio)}
                      onValueChange={handleRatioChange}
                    />
                  </div>

                  <dl className="grid grid-cols-2 gap-space-3">
                    <div className="rounded-lg border border-border bg-surface-panel p-space-3">
                      <dt className="text-xs text-foreground-secondary">Ratio</dt>
                      <dd className="mt-space-1" data-testid="readout-ratio">
                        <Numeral variant="lg" className="text-lg text-foreground">
                          {ratio}:1
                        </Numeral>
                      </dd>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-panel p-space-3">
                      <dt className="text-xs text-foreground-secondary">Load</dt>
                      <dd className="mt-space-1" data-testid="readout-load">
                        <Numeral variant="lg" className="text-lg text-foreground">
                          {LOAD_KG} kg
                        </Numeral>
                      </dd>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-panel p-space-3">
                      <dt className="text-xs text-foreground-secondary">Rope pulled</dt>
                      <dd className="mt-space-1" data-testid="readout-pulled">
                        <Numeral variant="lg" className="text-lg text-foreground">
                          {telemetry.ropePulled}
                        </Numeral>
                      </dd>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-panel p-space-3">
                      <dt className="text-xs text-foreground-secondary">Load raised</dt>
                      <dd className="mt-space-1" data-testid="readout-raised">
                        <Numeral variant="lg" className="text-lg text-foreground">
                          {telemetry.loadRaised}
                        </Numeral>
                      </dd>
                    </div>
                  </dl>

                  <div className="space-y-space-2 rounded-lg border border-border bg-surface-panel p-space-3 text-xs">
                    <div className="flex items-center justify-between gap-space-2">
                      <span className="text-foreground-secondary">Effort force</span>
                      <Numeral className="font-semibold text-foreground" data-testid="readout-effort">
                        {telemetry.effortKg}
                      </Numeral>
                    </div>
                    <div className="flex items-center justify-between gap-space-2">
                      <span className="text-foreground-secondary">Activated part</span>
                      <span className="font-mono text-accent" data-testid="readout-activated">
                        {lastActivated ?? "none"}
                      </span>
                    </div>
                    <div className="border-t border-border pt-space-2">
                      <span className="block text-foreground-secondary">Caption (onRead)</span>
                      <span className="mt-space-0_5 block font-mono text-foreground" data-testid="readout-onread">
                        {telemetry.caption}
                      </span>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-foreground-subtle">
                  Drag the rope handle down to raise the load, click a part (or Tab, use Arrow keys, and press Enter) to inspect or release the ratchet.
                </p>
              </CardContent>
            </div>
          </Card>
        </section>
      </main>
    </TooltipProvider>
  );
}
