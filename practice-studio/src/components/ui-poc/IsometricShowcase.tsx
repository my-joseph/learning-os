"use client";

import React, { useCallback, useRef, useState } from "react";
import type { PulleyProps } from "@/components/isometric/pulley";
import { LazyCube, LazyLever, LazyPulley } from "@/components/isometric/LazyFigures";
import { PlaygroundReadout, PlaygroundShowcase, PlaygroundStat, PlaygroundStats } from "@/components/playground/PlaygroundShowcase";
import { Numeral } from "@/components/ui/Numeral";
import { Badge } from "@/components/ui/shadcn/Badge";
import { SegmentedChips } from "@/components/ui/shadcn/Tabs";
import { computeLeverState, DEFAULT_GRAVITY } from "@/lib/isometric/physics/lever";
import { statusTone } from "@/lib/statusTone";

const LOAD_KG = 40;
const RATIO_OPTIONS = [
  { value: "2", label: "2:1" },
  { value: "4", label: "4:1" },
] as const;

type PulleyTelemetry = {
  ratio: 2 | 4;
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
      ratio: stepMatch[3] === "4" ? 4 : 2,
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
  const rest = text.match(/^(2|4):1 · /);
  if (rest) {
    const nextRatio = rest[1] === "4" ? 4 : 2;
    return { ratio: nextRatio, ropePulled: "0", loadRaised: "0.0", effortForce: formatPulleyEffort(loadKg, nextRatio), caption: text };
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

export function CubeShowcase() {
  const [caption, setCaption] = useState("cube");

  return (
    <PlaygroundShowcase
      title="Cube"
      caption={<span data-testid="cube-caption">{caption}</span>}
      figure={<LazyCube className="w-full" onRead={setCaption} />}
    />
  );
}

export function PulleyShowcase() {
  const inputRef = useRef<((props: PulleyProps) => void) | null>(null);
  const [lastActivated, setLastActivated] = useState<string | null>(null);
  const [telemetry, setTelemetry] = useState<PulleyTelemetry>({
    ratio: 2,
    ropePulled: "0",
    loadRaised: "0.0",
    effortForce: formatPulleyEffort(LOAD_KG, 2),
    caption: `2:1 · ${LOAD_KG} kg`,
  });

  function handleRatioChange(next: string) {
    inputRef.current?.({ ratio: next === "4" ? 4 : 2, load: LOAD_KG });
  }

  const handleRead = useCallback((caption: string) => {
    setTelemetry((previous) => ({ ...previous, ...parsePulleyRead(caption, previous.ratio, LOAD_KG) }));
  }, []);
  const { ratio } = telemetry;

  return (
    <PlaygroundShowcase
      title="Pulley"
      reset
      onReset={() => setLastActivated(null)}
      caption={<span data-testid="pulley-caption">{telemetry.caption}</span>}
      figure={
        <LazyPulley
          className="w-full"
          inputRef={inputRef}
          load={LOAD_KG}
          onRead={handleRead}
          onActivate={setLastActivated}
        />
      }
      readout={
        <PlaygroundReadout action={
          <SegmentedChips
            label="Mechanical advantage ratio"
            options={RATIO_OPTIONS}
            value={String(ratio)}
            onValueChange={handleRatioChange}
          />
        }>
          <PlaygroundStats>
            <PlaygroundStat label="Ratio" value={`${ratio}:1`} testId="readout-ratio" />
            <PlaygroundStat label="Load mass" value={`${LOAD_KG} kg`} testId="readout-load" />
            <PlaygroundStat label="Rope pulled" value={telemetry.ropePulled} testId="readout-pulled" />
            <PlaygroundStat label="Load raised" value={telemetry.loadRaised} testId="readout-raised" />
            <PlaygroundStat label="Effort force" value={telemetry.effortForce} testId="readout-effort" />
          </PlaygroundStats>
          {lastActivated && (
            <p className="text-xs text-foreground-secondary">
              Active part <span className="font-mono text-accent" data-testid="readout-activated">{lastActivated}</span>
            </p>
          )}
          <p className="text-xs text-foreground-secondary">
            Pull the handle down to raise the load. To inspect a part or release the ratchet, click it or tab to the figure, use the arrow keys, then press Enter.
          </p>
        </PlaygroundReadout>
      }
    />
  );
}

function LoadDetail({ weight, distance }: { weight: number; distance: number }) {
  return <><Numeral>{formatNewtons(weight)}</Numeral> · <Numeral>{distance.toFixed(1)} m</Numeral> from fulcrum</>;
}

export function LeverShowcase() {
  const [activePart, setActivePart] = useState<string | null>(null);
  const [lever, setLever] = useState<LeverTelemetry>(INITIAL_LEVER);
  const handleRead = useCallback((caption: string) => {
    setLever((previous) => ({ ...previous, ...parseLeverRead(caption) }));
  }, []);

  const statusLabel = lever.balanced ? "Balanced" : lever.tilt === "left" ? "Tips left" : "Tips right";

  return (
    <PlaygroundShowcase
      title="Lever"
      reset
      onReset={() => setActivePart(null)}
      caption={<span data-testid="lever-caption">{lever.caption}</span>}
      figure={<LazyLever className="w-full" onRead={handleRead} onActivate={setActivePart} />}
      readout={
        <PlaygroundReadout action={
          <Badge
            variant="status"
            data-testid="lever-status"
            className={lever.balanced
              ? `${statusTone.correct.softCard} ${statusTone.correct.text}`
              : "border border-border bg-surface-panel text-foreground"}
          >
            {statusLabel}
          </Badge>
        }>
          <PlaygroundStats>
            <PlaygroundStat label="Left load" value={`${lever.m1} kg`} testId="lever-readout-left-mass"
              detail={<LoadDetail weight={lever.w1} distance={lever.d1} />} />
            <PlaygroundStat label="Right load" value={`${lever.m2} kg`} testId="lever-readout-right-mass"
              detail={<LoadDetail weight={lever.w2} distance={lever.d2} />} />
            <PlaygroundStat label="Left torque" value={`${lever.tau1.toFixed(0)} N·m`} testId="lever-readout-tau1" />
            <PlaygroundStat label="Right torque" value={`${lever.tau2.toFixed(0)} N·m`} testId="lever-readout-tau2" />
            <PlaygroundStat label="Net torque" value={`${lever.netTorque.toFixed(1)} N·m`} testId="lever-readout-net" />
          </PlaygroundStats>
          {activePart && (
            <p className="text-xs text-foreground-secondary">
              Active part <span className="font-mono text-accent" data-testid="lever-readout-active">{activePart.replace(/-/g, " ")}</span>
            </p>
          )}
          <p className="text-xs text-foreground-secondary">
            The beam is massless and g = 9.8 m/s². Drag the fulcrum or either load. On the keyboard, tab to a part, use the arrow keys to move it by 0.5 m, and press Enter on a load to change its mass.
          </p>
        </PlaygroundReadout>
      }
    />
  );
}
