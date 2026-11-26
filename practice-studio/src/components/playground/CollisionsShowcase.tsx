"use client";

import React, { useCallback, useMemo, useState } from "react";
import { Pause, Play, RotateCcw } from "lucide-react";
import { FormattedText } from "@/components/FormattedText";
import type { CollisionSimSnapshot } from "@/components/playground/Collisions";
import { LazyCollisions } from "@/components/playground/LazyCollisions";
import { PlaygroundReadout, PlaygroundShowcase, PlaygroundStat, PlaygroundStats } from "@/components/playground/PlaygroundShowcase";
import { Numeral } from "@/components/ui/Numeral";
import { Badge } from "@/components/ui/shadcn/Badge";
import { Button } from "@/components/ui/shadcn/Button";
import { SegmentedChips } from "@/components/ui/shadcn/Tabs";
import {
  computeCollisionTheory,
  computeInstantaneousMetrics,
  DEFAULT_COLLISION_INPUT,
  MASS_STEP_KG,
  MAX_MASS_KG,
  MAX_RESTITUTION,
  MAX_VELOCITY_MPS,
  MIN_MASS_KG,
  MIN_RESTITUTION,
  MIN_VELOCITY_MPS,
  RESTITUTION_STEP,
  VELOCITY_STEP_MPS,
  velocityErrorPercent,
  type CollisionInput,
} from "@/lib/playground/collisions";
import { formatSigned } from "@/lib/playground/collisionsLayout";
import { statusTone } from "@/lib/statusTone";

type CollisionMode = "elastic" | "inelastic" | "stick";

const MODE_OPTIONS = [
  { value: "elastic", label: "Elastic" },
  { value: "inelastic", label: "Inelastic" },
  { value: "stick", label: "Stick together" },
] as const;

function modeForRestitution(e: number): CollisionMode {
  if (e >= 0.999) return "elastic";
  if (e <= 0.001) return "stick";
  return "inelastic";
}

export function CollisionsShowcase() {
  const [input, setInput] = useState<CollisionInput>(DEFAULT_COLLISION_INPUT);
  const [selectedCart, setSelectedCart] = useState<1 | 2>(1);
  const [command, setCommand] = useState<{ type: "play" | "pause" | "reset"; seq: number } | null>(null);
  const [snapshot, setSnapshot] = useState<CollisionSimSnapshot>({
    phase: "ready",
    hasCollided: false,
    x1: -1.2,
    x2: 1.2,
    v1: DEFAULT_COLLISION_INPUT.v1,
    v2: DEFAULT_COLLISION_INPUT.v2,
    measuredV1After: null,
    measuredV2After: null,
    reducedMotion: false,
  });

  const theory = useMemo(() => computeCollisionTheory(input), [input]);
  const liveMetrics = useMemo(
    () => computeInstantaneousMetrics(input.m1, input.m2, snapshot.v1, snapshot.v2),
    [input.m1, input.m2, snapshot.v1, snapshot.v2],
  );

  const mode = modeForRestitution(input.e);

  const sendCommand = useCallback((type: "play" | "pause" | "reset") => {
    setCommand((prev) => ({ type, seq: (prev?.seq ?? 0) + 1 }));
  }, []);

  const handleModeChange = useCallback((next: string) => {
    if (next === "elastic") {
      setInput((prev) => ({ ...prev, e: 1 }));
    } else if (next === "stick") {
      setInput((prev) => ({ ...prev, e: 0 }));
    } else if (next === "inelastic") {
      setInput((prev) => ({ ...prev, e: prev.e > 0.05 && prev.e < 0.95 ? prev.e : 0.5 }));
    }
  }, []);

  const handleCartField = useCallback((field: keyof CollisionInput, value: number) => {
    setInput((prev) => ({ ...prev, [field]: value }));
  }, []);

  const hasMeasuredAfter = snapshot.hasCollided && snapshot.measuredV1After !== null && snapshot.measuredV2After !== null;
  const err1Pct = hasMeasuredAfter ? velocityErrorPercent(snapshot.measuredV1After!, theory.v1After) : null;
  const err2Pct = hasMeasuredAfter ? velocityErrorPercent(snapshot.measuredV2After!, theory.v2After) : null;
  const maxErrPct = err1Pct !== null && err2Pct !== null ? Math.max(err1Pct, err2Pct) : null;

  const captionText = theory.willCollide
    ? `${input.m1.toFixed(1)} kg @ ${formatSigned(input.v1)} m/s · ${input.m2.toFixed(1)} kg @ ${formatSigned(input.v2)} m/s · e = ${input.e.toFixed(2)}`
    : `${input.m1.toFixed(1)} kg @ ${formatSigned(input.v1)} m/s · ${input.m2.toFixed(1)} kg @ ${formatSigned(input.v2)} m/s · Moving apart (no collision)`;

  const statusBadgeText = !theory.willCollide
    ? "No collision"
    : snapshot.phase === "running"
      ? "Running"
      : snapshot.hasCollided
        ? theory.collisionKind === "elastic"
          ? "Elastic impact"
          : theory.collisionKind === "perfectly-inelastic"
            ? "Stuck together"
            : "Inelastic impact"
        : "Ready";

  const keLostPct = theory.keBefore > 1e-9 ? (theory.keLost / theory.keBefore) * 100 : 0;

  return (
    <PlaygroundShowcase
      title="Collisions"
      caption={<span data-testid="collisions-caption">{captionText}</span>}
      figure={
        <LazyCollisions
          input={input}
          onInputChange={setInput}
          selectedCart={selectedCart}
          onSelectCart={setSelectedCart}
          onSnapshot={setSnapshot}
          command={command}
          interactive="detail"
        />
      }
      readout={
        <PlaygroundReadout
          action={
            <div className="flex flex-wrap items-center gap-space-2">
              <Badge
                variant="status"
                data-testid="collisions-status"
                className={
                  snapshot.hasCollided
                    ? `${statusTone.correct.softCard} ${statusTone.correct.text}`
                    : "border border-border bg-surface-panel text-foreground"
                }
              >
                {statusBadgeText}
              </Badge>
              <Button
                type="button"
                variant="primary"
                size="compact"
                onClick={() => sendCommand(snapshot.phase === "running" ? "pause" : "play")}
                data-testid="collisions-play-btn"
              >
                {snapshot.phase === "running" ? (
                  <Pause aria-hidden="true" className="size-space-3_5" />
                ) : (
                  <Play aria-hidden="true" className="size-space-3_5" />
                )}
                {snapshot.phase === "running" ? "Pause" : snapshot.phase === "done" ? "Replay" : "Play"}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="compact"
                onClick={() => sendCommand("reset")}
                data-testid="collisions-reset-btn"
              >
                <RotateCcw aria-hidden="true" className="size-space-3_5" />
                Reset
              </Button>
            </div>
          }
        >
          {/* Parameter controls */}
          <div className="space-y-space-3 rounded-lg border border-border bg-surface-panel p-space-3">
            <div className="flex flex-wrap items-center justify-between gap-space-2">
              <span className="text-xs font-semibold text-foreground-secondary">Collision type</span>
              <SegmentedChips
                label="Collision type"
                options={MODE_OPTIONS}
                value={mode}
                onValueChange={handleModeChange}
              />
            </div>

            <div className="space-y-space-1 border-t border-border pt-space-2_5">
              <div className="flex items-center justify-between gap-space-2 text-xs">
                <label htmlFor="collision-e-slider" className="font-semibold text-foreground-secondary">
                  Restitution (<FormattedText text="$e$" />)
                </label>
                <Numeral className="font-mono text-foreground" data-testid="collisions-e-value">
                  {input.e.toFixed(2)}
                </Numeral>
              </div>
              <input
                id="collision-e-slider"
                type="range"
                min={MIN_RESTITUTION}
                max={MAX_RESTITUTION}
                step={RESTITUTION_STEP}
                value={input.e}
                aria-label="Coefficient of restitution e"
                aria-valuetext={`Coefficient of restitution ${input.e.toFixed(2)}`}
                onChange={(e) => handleCartField("e", Number(e.target.value))}
                className="min-h-touch w-full cursor-pointer accent-accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              />
            </div>

            <div className="grid grid-cols-1 gap-space-3 border-t border-border pt-space-2_5 sm:grid-cols-2">
              {/* Cart 1 */}
              <div
                className={
                  selectedCart === 1
                    ? "space-y-space-2 rounded-md border border-accent-field bg-accent-tint/40 p-space-2_5"
                    : "space-y-space-2 rounded-md border border-border bg-surface-raised p-space-2_5"
                }
                onFocus={() => setSelectedCart(1)}
              >
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className={selectedCart === 1 ? "text-accent" : "text-foreground"}>Cart 1 (left)</span>
                </div>
                <div className="space-y-space-1">
                  <div className="flex items-center justify-between text-xs">
                    <label htmlFor="cart1-mass" className="text-foreground-secondary">Mass m₁</label>
                    <Numeral className="font-mono">{input.m1.toFixed(1)} kg</Numeral>
                  </div>
                  <input
                    id="cart1-mass"
                    type="range"
                    min={MIN_MASS_KG}
                    max={MAX_MASS_KG}
                    step={MASS_STEP_KG}
                    value={input.m1}
                    aria-label="Cart 1 mass in kilograms"
                    onChange={(e) => handleCartField("m1", Number(e.target.value))}
                    className="min-h-touch w-full cursor-pointer accent-accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  />
                </div>
                <div className="space-y-space-1">
                  <div className="flex items-center justify-between text-xs">
                    <label htmlFor="cart1-vel" className="text-foreground-secondary">Initial v₁</label>
                    <Numeral className="font-mono">{formatSigned(input.v1)} m/s</Numeral>
                  </div>
                  <input
                    id="cart1-vel"
                    type="range"
                    min={MIN_VELOCITY_MPS}
                    max={MAX_VELOCITY_MPS}
                    step={VELOCITY_STEP_MPS}
                    value={input.v1}
                    aria-label="Cart 1 initial velocity in meters per second"
                    onChange={(e) => handleCartField("v1", Number(e.target.value))}
                    className="min-h-touch w-full cursor-pointer accent-accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  />
                </div>
              </div>

              {/* Cart 2 */}
              <div
                className={
                  selectedCart === 2
                    ? "space-y-space-2 rounded-md border border-accent-field bg-accent-tint/40 p-space-2_5"
                    : "space-y-space-2 rounded-md border border-border bg-surface-raised p-space-2_5"
                }
                onFocus={() => setSelectedCart(2)}
              >
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className={selectedCart === 2 ? "text-accent" : "text-foreground"}>Cart 2 (right)</span>
                </div>
                <div className="space-y-space-1">
                  <div className="flex items-center justify-between text-xs">
                    <label htmlFor="cart2-mass" className="text-foreground-secondary">Mass m₂</label>
                    <Numeral className="font-mono">{input.m2.toFixed(1)} kg</Numeral>
                  </div>
                  <input
                    id="cart2-mass"
                    type="range"
                    min={MIN_MASS_KG}
                    max={MAX_MASS_KG}
                    step={MASS_STEP_KG}
                    value={input.m2}
                    aria-label="Cart 2 mass in kilograms"
                    onChange={(e) => handleCartField("m2", Number(e.target.value))}
                    className="min-h-touch w-full cursor-pointer accent-accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  />
                </div>
                <div className="space-y-space-1">
                  <div className="flex items-center justify-between text-xs">
                    <label htmlFor="cart2-vel" className="text-foreground-secondary">Initial v₂</label>
                    <Numeral className="font-mono">{formatSigned(input.v2)} m/s</Numeral>
                  </div>
                  <input
                    id="cart2-vel"
                    type="range"
                    min={MIN_VELOCITY_MPS}
                    max={MAX_VELOCITY_MPS}
                    step={VELOCITY_STEP_MPS}
                    value={input.v2}
                    aria-label="Cart 2 initial velocity in meters per second"
                    onChange={(e) => handleCartField("v2", Number(e.target.value))}
                    className="min-h-touch w-full cursor-pointer accent-accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Authoritative theory + Matter measured readout */}
          <PlaygroundStats>
            <PlaygroundStat
              label="Before velocities"
              value={`${formatSigned(theory.v1)}, ${formatSigned(theory.v2)} m/s`}
              detail={`p₁ = ${formatSigned(theory.p1Before, 2)}, p₂ = ${formatSigned(theory.p2Before, 2)} kg·m/s`}
              testId="readout-before-vel"
            />
            <PlaygroundStat
              label="After velocities (theory)"
              value={
                theory.willCollide
                  ? `${formatSigned(theory.v1After, 2)}, ${formatSigned(theory.v2After, 2)} m/s`
                  : "No collision"
              }
              detail={
                hasMeasuredAfter
                  ? `Matter: ${formatSigned(snapshot.measuredV1After!, 2)}, ${formatSigned(snapshot.measuredV2After!, 2)} m/s`
                  : `Live: ${formatSigned(snapshot.v1, 2)}, ${formatSigned(snapshot.v2, 2)} m/s`
              }
              testId="readout-after-vel"
            />
            <PlaygroundStat
              label="Momentum (before → after)"
              value={`${formatSigned(theory.pBefore, 2)} → ${formatSigned(theory.pAfter, 2)} kg·m/s`}
              detail={`Live Matter P = ${formatSigned(liveMetrics.totalP, 2)} kg·m/s`}
              testId="readout-momentum"
            />
            <PlaygroundStat
              label="Kinetic energy (before → after)"
              value={`${theory.keBefore.toFixed(2)} → ${theory.keAfter.toFixed(2)} J`}
              detail={`Live Matter KE = ${liveMetrics.totalKe.toFixed(2)} J`}
              testId="readout-ke"
            />
            <PlaygroundStat
              label="KE lost"
              value={`${theory.keLost.toFixed(2)} J`}
              detail={`${keLostPct.toFixed(0)}% dissipated`}
              testId="readout-ke-lost"
            />
            <PlaygroundStat
              label="Measured vs theory"
              value={
                hasMeasuredAfter && maxErrPct !== null
                  ? `${maxErrPct.toFixed(2)}% diff`
                  : theory.willCollide
                    ? "Press Play"
                    : "—"
              }
              detail={
                hasMeasuredAfter
                  ? `Δv₁ = ${Math.abs(snapshot.measuredV1After! - theory.v1After).toFixed(3)}, Δv₂ = ${Math.abs(snapshot.measuredV2After! - theory.v2After).toFixed(3)} m/s`
                  : "Theory values are exact; Matter runs live"
              }
              testId="readout-accuracy"
            />
          </PlaygroundStats>

          <p className="text-xs text-foreground-secondary">
            Right is positive (<FormattedText text="$+x$" />). Track is level and frictionless. Click or Tab to a cart and use Left/Right arrows to adjust initial velocity, Up/Down to adjust mass, or Space to play.
          </p>
        </PlaygroundReadout>
      }
    />
  );
}
