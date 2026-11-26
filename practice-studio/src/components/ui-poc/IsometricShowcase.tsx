"use client";

import React, { useCallback, useState } from "react";
import { LazyCube, LazyLever, LazyPulley } from "@/components/isometric/LazyFigures";
import { Heading } from "@/components/ui/Heading";
import { Numeral } from "@/components/ui/Numeral";
import { ThemeToggleButton } from "@/components/ui/ThemeToggleButton";
import { Badge } from "@/components/ui/shadcn/Badge";
import { Card, CardContent } from "@/components/ui/shadcn/Card";
import { SegmentedChips } from "@/components/ui/shadcn/Tabs";
import { TooltipProvider } from "@/components/ui/shadcn/Tooltip";
import { useTheme } from "@/hooks/useTheme";
import { computeLeverState, DEFAULT_GRAVITY } from "@/lib/isometric/physics/lever";
import { statusTone } from "@/lib/statusTone";

const LOAD_KG = 40;
const RATIO_OPTIONS = [
  { value: "2", label: "2:1" },
  { value: "4", label: "4:1" },
] as const;

type PulleyTelemetry = {
  ropePulled: string;
  loadRaised: string;
  effortForce: string;
  caption: string;
};

type LeverTelemetry = {
  m1: number;
  d1: number;
  m2: number;
  d2: number;
  w1: number;
  w2: number;
  tau1: number;
  tau2: number;
  netTorque: number;
  balanced: boolean;
  tilt: "left" | "right" | "level";
  caption: string;
};

function formatNewtons(n: number): string {
  return Math.abs(n - Math.round(n)) < 0.05 ? `${Math.round(n)} N` : `${n.toFixed(1)} N`;
}

function formatPulleyEffort(loadKg: number, ratio: 2 | 4): string {
  return formatNewtons((loadKg * DEFAULT_GRAVITY) / ratio);
}

function parsePulleyRead(text: string, ratio: 2 | 4, loadKg: number): Partial<PulleyTelemetry> {
  const stepMatch = text.match(/^pull\s+([\d.]+)\s+·\s+lift\s+([\d.]+)\s+·\s+(\d+):1\s+·\s+([\d.]+)\s+N/);
  if (stepMatch) {
    return {
      ropePulled: stepMatch[1],
      loadRaised: stepMatch[2],
      effortForce: `${stepMatch[4]} N`,
      caption: text,
    };
  }
  const notchMatch = text.match(/^Pulled a notch\s+·\s+lift\s+([\d.]+)/);
  if (notchMatch) {
    const lift = Number(notchMatch[1]);
    return {
      ropePulled: String(Math.round(lift * ratio)),
      loadRaised: lift.toFixed(1),
      effortForce: formatPulleyEffort(loadKg, ratio),
      caption: text,
    };
  }
  if (text.startsWith("Ratchet released")) {
    return {
      ropePulled: "0",
      loadRaised: "0.0",
      effortForce: formatPulleyEffort(loadKg, ratio),
      caption: text,
    };
  }
  return { caption: text };
}

function buildLeverTelemetry(m1: number, d1: number, m2: number, d2: number, caption: string): LeverTelemetry {
  const s = computeLeverState({ m1, d1, m2, d2, g: DEFAULT_GRAVITY });
  return {
    m1,
    d1,
    m2,
    d2,
    w1: s.w1,
    w2: s.w2,
    tau1: s.tau1,
    tau2: s.tau2,
    netTorque: s.netTorque,
    balanced: s.balanced,
    tilt: s.tilt,
    caption,
  };
}

function parseLeverRead(text: string): Partial<LeverTelemetry> {
  const match = text.match(
    /^L\s+([\d.]+)\s+kg\s+@\s+([\d.]+)\s+m\s+\([\d.]+\s+N·m\)\s+·\s+R\s+([\d.]+)\s+kg\s+@\s+([\d.]+)\s+m\s+\([\d.]+\s+N·m\)/
  );
  if (!match) return { caption: text };
  const m1 = Number(match[1]);
  const d1 = Number(match[2]);
  const m2 = Number(match[3]);
  const d2 = Number(match[4]);
  return buildLeverTelemetry(m1, d1, m2, d2, text);
}

const INITIAL_LEVER = buildLeverTelemetry(
  20,
  1.5,
  10,
  1.5,
  "L 20 kg @ 1.5 m (294 N·m) · R 10 kg @ 1.5 m (147 N·m) · Tips left"
);

export function IsometricShowcase() {
  const { theme, handleToggleTheme } = useTheme();
  const [cubeCaption, setCubeCaption] = useState("cube");
  const [ratio, setRatio] = useState<2 | 4>(2);
  const [lastActivated, setLastActivated] = useState<string | null>(null);
  const [telemetry, setTelemetry] = useState<PulleyTelemetry>({
    ropePulled: "0",
    loadRaised: "0.0",
    effortForce: formatPulleyEffort(LOAD_KG, 2),
    caption: `2:1 · ${LOAD_KG} kg`,
  });
  const [leverActivePart, setLeverActivePart] = useState<string | null>(null);
  const [lever, setLever] = useState<LeverTelemetry>(INITIAL_LEVER);

  const handleRatioChange = useCallback((next: string) => {
    const nextRatio: 2 | 4 = next === "4" ? 4 : 2;
    setRatio(nextRatio);
    setTelemetry({
      ropePulled: "0",
      loadRaised: "0.0",
      effortForce: formatPulleyEffort(LOAD_KG, nextRatio),
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

  const handleLeverRead = useCallback((text: string) => {
    setLever((prev) => ({
      ...prev,
      ...parseLeverRead(text),
    }));
  }, []);

  const handleLeverActivate = useCallback((part: string) => {
    setLeverActivePart(part);
  }, []);

  const leverStatusLabel = lever.balanced
    ? "Balanced"
    : lever.tilt === "left"
      ? "Tips left"
      : "Tips right";

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
            <div className="flex flex-1 items-center justify-center p-space-3">
              <LazyCube className="w-full" onRead={setCubeCaption} />
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
                <div className="flex flex-1 items-center justify-center p-space-3">
                  <LazyPulley
                    className="w-full"
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
                      <dt className="text-xs text-foreground-secondary">Load mass</dt>
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
                        {telemetry.effortForce}
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

          <Card className="iso-studio-surface overflow-hidden bg-surface-raised border-border lg:col-span-12">
            <div className="grid h-full grid-cols-1 md:grid-cols-12">
              <div className="flex flex-col md:col-span-7 md:border-r md:border-border">
                <div className="flex flex-1 items-center justify-center p-space-3">
                  <LazyLever
                    className="w-full"
                    onRead={handleLeverRead}
                    onActivate={handleLeverActivate}
                  />
                </div>
                <div className="mt-auto flex min-w-0 items-center justify-between gap-space-3 border-t border-border px-space-4 py-space-3">
                  <span className="shrink-0 text-sm font-semibold text-foreground">Lever</span>
                  <span className="min-w-0 truncate font-mono text-xs text-foreground-secondary" data-testid="lever-caption">
                    {lever.caption}
                  </span>
                </div>
              </div>

              <CardContent className="flex flex-col justify-between gap-space-4 p-space-5 md:col-span-5">
                <div className="space-y-space-4">
                  <div className="flex items-center justify-between gap-space-2">
                    <Heading variant="section" className="text-base">
                      Live readout
                    </Heading>
                    <Badge
                      variant="status"
                      data-testid="lever-status"
                      className={
                        lever.balanced
                          ? `${statusTone.correct.softCard} ${statusTone.correct.text}`
                          : "border border-border bg-surface-panel text-foreground"
                      }
                    >
                      {leverStatusLabel}
                    </Badge>
                  </div>

                  <dl className="grid grid-cols-2 gap-space-3">
                    <div className="rounded-lg border border-border bg-surface-panel p-space-3">
                      <dt className="text-xs text-foreground-secondary">Left load</dt>
                      <dd className="mt-space-1" data-testid="lever-readout-left-mass">
                        <Numeral variant="lg" className="text-lg text-foreground">
                          {lever.m1} kg
                        </Numeral>
                        <span className="mt-space-0_5 block text-xs text-foreground-secondary">
                          <Numeral>{formatNewtons(lever.w1)}</Numeral> · <Numeral>{lever.d1.toFixed(1)} m</Numeral> from fulcrum
                        </span>
                      </dd>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-panel p-space-3">
                      <dt className="text-xs text-foreground-secondary">Right load</dt>
                      <dd className="mt-space-1" data-testid="lever-readout-right-mass">
                        <Numeral variant="lg" className="text-lg text-foreground">
                          {lever.m2} kg
                        </Numeral>
                        <span className="mt-space-0_5 block text-xs text-foreground-secondary">
                          <Numeral>{formatNewtons(lever.w2)}</Numeral> · <Numeral>{lever.d2.toFixed(1)} m</Numeral> from fulcrum
                        </span>
                      </dd>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-panel p-space-3">
                      <dt className="text-xs text-foreground-secondary">Left torque</dt>
                      <dd className="mt-space-1" data-testid="lever-readout-tau1">
                        <Numeral variant="lg" className="text-lg text-foreground">
                          {lever.tau1.toFixed(0)} N·m
                        </Numeral>
                      </dd>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-panel p-space-3">
                      <dt className="text-xs text-foreground-secondary">Right torque</dt>
                      <dd className="mt-space-1" data-testid="lever-readout-tau2">
                        <Numeral variant="lg" className="text-lg text-foreground">
                          {lever.tau2.toFixed(0)} N·m
                        </Numeral>
                      </dd>
                    </div>
                  </dl>

                  <div className="space-y-space-2 rounded-lg border border-border bg-surface-panel p-space-3 text-xs">
                    <div className="flex items-center justify-between gap-space-2">
                      <span className="text-foreground-secondary">Net torque</span>
                      <Numeral className="font-semibold text-foreground" data-testid="lever-readout-net">
                        {lever.netTorque.toFixed(1)} N·m
                      </Numeral>
                    </div>
                    <div className="flex items-center justify-between gap-space-2">
                      <span className="text-foreground-secondary">State</span>
                      <span
                        className={lever.balanced ? `font-semibold ${statusTone.correct.text}` : "font-semibold text-foreground"}
                        data-testid="lever-readout-state"
                      >
                        {leverStatusLabel}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-space-2">
                      <span className="text-foreground-secondary">Active part</span>
                      <span className="font-mono text-accent" data-testid="lever-readout-active">
                        {leverActivePart ?? "none"}
                      </span>
                    </div>
                    <div className="border-t border-border pt-space-2">
                      <span className="block text-foreground-secondary">Caption (onRead)</span>
                      <span className="mt-space-0_5 block font-mono text-foreground" data-testid="lever-readout-onread">
                        {lever.caption}
                      </span>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-foreground-subtle">
                  Drag the fulcrum or either load along the beam, or Tab to a part, use Arrow keys to move by 0.5 m, and press Enter to cycle load mass.
                </p>
              </CardContent>
            </div>
          </Card>
        </section>
      </main>
    </TooltipProvider>
  );
}
