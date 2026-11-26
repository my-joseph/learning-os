"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Crosshair, Pause, Play, RotateCcw } from "lucide-react";
import { FormattedText } from "@/components/FormattedText";
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
  INITIAL_CART1_POS_M,
  INITIAL_CART2_POS_M,
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
import type { CollisionFrame, PrecomputedCollisionRun } from "@/lib/playground/collisionsSim";
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

function inputsMatch(a: CollisionInput, b: CollisionInput): boolean {
  return (
    Math.abs(a.m1 - b.m1) < 1e-9 &&
    Math.abs(a.m2 - b.m2) < 1e-9 &&
    Math.abs(a.v1 - b.v1) < 1e-9 &&
    Math.abs(a.v2 - b.v2) < 1e-9 &&
    Math.abs(a.e - b.e) < 1e-9
  );
}

export function CollisionsShowcase() {
  const [input, setInput] = useState<CollisionInput>(DEFAULT_COLLISION_INPUT);
  const [selectedCart, setSelectedCart] = useState<1 | 2>(1);
  const [frameIndex, setFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [run, setRun] = useState<PrecomputedCollisionRun | null>(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mq.matches);
    const onChange = () => setReducedMotion(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const theory = useMemo(() => computeCollisionTheory(input), [input]);

  const fallbackFrame: CollisionFrame = useMemo(() => {
    const metrics = computeInstantaneousMetrics(input.m1, input.m2, input.v1, input.v2);
    return {
      t: 0,
      x1: INITIAL_CART1_POS_M,
      x2: INITIAL_CART2_POS_M,
      v1: input.v1,
      v2: input.v2,
      p1: metrics.p1,
      p2: metrics.p2,
      P: metrics.totalP,
      KE1: metrics.ke1,
      KE2: metrics.ke2,
      KE: metrics.totalKe,
    };
  }, [input]);

  const activeRun = run && inputsMatch(run.input, input) ? run : null;
  const maxFrameIndex = activeRun ? Math.max(0, activeRun.frames.length - 1) : 0;
  const clampedFrameIndex = Math.max(0, Math.min(maxFrameIndex, frameIndex));
  const currentFrame = activeRun?.frames[clampedFrameIndex] ?? fallbackFrame;
  const durationSec = activeRun && activeRun.frames.length > 0 ? activeRun.frames[activeRun.frames.length - 1].t : 0;

  const impactFrameIndex = activeRun?.impactFrameIndex ?? null;
  const impactTime = activeRun?.impactTime ?? null;
  const impactRatio =
    impactFrameIndex !== null && maxFrameIndex > 0 ? impactFrameIndex / maxFrameIndex : null;
  const atImpact = impactFrameIndex !== null && clampedFrameIndex === impactFrameIndex;
  const hasCollided = impactFrameIndex !== null && clampedFrameIndex >= impactFrameIndex;

  const mode = modeForRestitution(input.e);

  const handleInputChange = useCallback((next: CollisionInput) => {
    setIsPlaying(false);
    setFrameIndex(0);
    setInput(next);
  }, []);

  const handleModeChange = useCallback(
    (next: string) => {
      if (next === "elastic") {
        handleInputChange({ ...input, e: 1 });
      } else if (next === "stick") {
        handleInputChange({ ...input, e: 0 });
      } else if (next === "inelastic") {
        handleInputChange({ ...input, e: input.e > 0.05 && input.e < 0.95 ? input.e : 0.5 });
      }
    },
    [handleInputChange, input],
  );

  const handleCartField = useCallback(
    (field: keyof CollisionInput, value: number) => {
      handleInputChange({ ...input, [field]: value });
    },
    [handleInputChange, input],
  );

  const handlePlayPause = useCallback(() => {
    if (isPlaying) {
      setIsPlaying(false);
      return;
    }
    if (reducedMotion) {
      setIsPlaying(false);
      setFrameIndex(maxFrameIndex);
      return;
    }
    if (clampedFrameIndex >= maxFrameIndex) {
      setFrameIndex(0);
    }
    setIsPlaying(true);
  }, [clampedFrameIndex, isPlaying, maxFrameIndex, reducedMotion]);

  const handleReset = useCallback(() => {
    setIsPlaying(false);
    setFrameIndex(0);
  }, []);

  const handleScrubTo = useCallback(
    (nextIndex: number) => {
      setIsPlaying(false);
      setFrameIndex(Math.max(0, Math.min(maxFrameIndex, nextIndex)));
    },
    [maxFrameIndex],
  );

  const handleJumpToImpact = useCallback(() => {
    if (impactFrameIndex === null) return;
    setIsPlaying(false);
    setFrameIndex(impactFrameIndex);
  }, [impactFrameIndex]);

  const handleScrubberKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (maxFrameIndex <= 0) return;
      let next: number | null = null;
      if (e.key === "ArrowRight" || e.key === "ArrowUp") next = Math.min(maxFrameIndex, clampedFrameIndex + 1);
      else if (e.key === "ArrowLeft" || e.key === "ArrowDown") next = Math.max(0, clampedFrameIndex - 1);
      else if (e.key === "PageUp") next = Math.min(maxFrameIndex, clampedFrameIndex + 10);
      else if (e.key === "PageDown") next = Math.max(0, clampedFrameIndex - 10);
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = maxFrameIndex;

      if (next !== null) {
        e.preventDefault();
        handleScrubTo(next);
      }
    },
    [clampedFrameIndex, handleScrubTo, maxFrameIndex],
  );

  const hasMeasuredAfter =
    activeRun !== null && activeRun.measuredV1After !== null && activeRun.measuredV2After !== null;
  const err1Pct = hasMeasuredAfter ? velocityErrorPercent(activeRun.measuredV1After!, theory.v1After) : null;
  const err2Pct = hasMeasuredAfter ? velocityErrorPercent(activeRun.measuredV2After!, theory.v2After) : null;
  const maxErrPct = err1Pct !== null && err2Pct !== null ? Math.max(err1Pct, err2Pct) : null;

  const captionText = theory.willCollide
    ? `${input.m1.toFixed(1)} kg @ ${formatSigned(input.v1)} m/s · ${input.m2.toFixed(1)} kg @ ${formatSigned(input.v2)} m/s · e = ${input.e.toFixed(2)}`
    : `${input.m1.toFixed(1)} kg @ ${formatSigned(input.v1)} m/s · ${input.m2.toFixed(1)} kg @ ${formatSigned(input.v2)} m/s · Moving apart (no collision)`;

  const statusBadgeText = !theory.willCollide
    ? "No collision"
    : isPlaying
      ? "Running"
      : atImpact
        ? "At impact"
        : hasCollided
          ? theory.collisionKind === "elastic"
            ? "Elastic impact"
            : theory.collisionKind === "perfectly-inelastic"
              ? "Stuck together"
              : "Inelastic impact"
          : clampedFrameIndex > 0
            ? "Before impact"
            : "Ready";

  const keLostPct = theory.keBefore > 1e-9 ? (theory.keLost / theory.keBefore) * 100 : 0;

  return (
    <PlaygroundShowcase
      title="Collisions"
      caption={<span data-testid="collisions-caption">{captionText}</span>}
      figure={
        <div className="space-y-space-3">
          <LazyCollisions
            input={input}
            onInputChange={handleInputChange}
            selectedCart={selectedCart}
            onSelectCart={setSelectedCart}
            frameIndex={clampedFrameIndex}
            onFrameIndexChange={setFrameIndex}
            playing={isPlaying}
            onPlayingChange={setIsPlaying}
            onRunReady={setRun}
            interactive="detail"
          />

          {/* Time scrubber */}
          <div
            className="space-y-space-2 rounded-lg border border-border bg-surface-panel p-space-3"
            data-testid="collisions-scrubber-panel"
          >
            <div className="flex flex-wrap items-center justify-between gap-space-2">
              <div className="flex items-baseline gap-space-2">
                <label htmlFor="collision-time-scrubber" className="text-xs font-semibold text-foreground-secondary">
                  Time
                </label>
                <Numeral className="font-mono text-sm text-foreground" data-testid="collisions-time-value">
                  {currentFrame.t.toFixed(2)} s
                </Numeral>
                <span className="font-mono text-xs tabular-nums text-foreground-secondary">
                  / {durationSec.toFixed(2)} s
                </span>
              </div>
              <div className="flex items-center gap-space-2">
                <span
                  className="font-mono text-xs tabular-nums text-foreground-secondary"
                  data-testid="collisions-impact-time-label"
                >
                  {impactTime !== null ? `Impact ${impactTime.toFixed(2)} s` : "No track impact"}
                </span>
                <Button
                  type="button"
                  variant="outline"
                  size="compact"
                  disabled={impactFrameIndex === null}
                  onClick={handleJumpToImpact}
                  data-testid="collisions-jump-impact-btn"
                >
                  <Crosshair aria-hidden="true" className="size-space-3_5" />
                  Jump to impact
                </Button>
              </div>
            </div>

            <div className="relative flex items-center">
              {impactRatio !== null && (
                <span
                  aria-hidden="true"
                  data-testid="collisions-impact-marker"
                  className="collision-impact-marker pointer-events-none absolute top-1/2 z-base h-space-3 w-space-0_5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-warning-border"
                  style={
                    {
                      "--impact-left": `calc(var(--space-2) + (100% - var(--space-4)) * ${impactRatio})`,
                    } as React.CSSProperties
                  }
                />
              )}
              <input
                id="collision-time-scrubber"
                data-testid="collisions-time-scrubber"
                type="range"
                min={0}
                max={maxFrameIndex}
                step={1}
                value={clampedFrameIndex}
                disabled={maxFrameIndex === 0}
                aria-label="Time"
                aria-valuetext={`${currentFrame.t.toFixed(2)} seconds${atImpact ? ", at impact" : ""}`}
                onPointerDown={() => setIsPlaying(false)}
                onChange={(e) => handleScrubTo(Number(e.target.value))}
                onKeyDown={handleScrubberKeyDown}
                className="collision-scrubber relative z-local min-h-touch w-full cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-disabled"
              />
            </div>

            <p className="text-xs text-foreground-secondary">
              Drag to scrub or use Left/Right arrows (1 frame), PageUp/PageDown (10 frames), Home/End.
            </p>
          </div>
        </div>
      }
      readout={
        <PlaygroundReadout
          action={
            <div className="flex flex-wrap items-center gap-space-2">
              <Badge
                variant="status"
                data-testid="collisions-status"
                className={
                  hasCollided
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
                onClick={handlePlayPause}
                data-testid="collisions-play-btn"
              >
                {isPlaying ? (
                  <Pause aria-hidden="true" className="size-space-3_5" />
                ) : (
                  <Play aria-hidden="true" className="size-space-3_5" />
                )}
                {isPlaying ? "Pause" : clampedFrameIndex >= maxFrameIndex && maxFrameIndex > 0 ? "Replay" : "Play"}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="compact"
                onClick={handleReset}
                data-testid="collisions-reset-btn"
              >
                <RotateCcw aria-hidden="true" className="size-space-3_5" />
                Reset
              </Button>
            </div>
          }
        >
          {/* Current frame values at t */}
          <div
            className="space-y-space-2 rounded-lg border border-border bg-surface-panel p-space-3"
            data-testid="readout-current-frame"
          >
            <div className="flex flex-wrap items-center justify-between gap-space-2">
              <span className="font-mono text-xs font-semibold tabular-nums text-foreground" data-testid="readout-current-time">
                At t = {currentFrame.t.toFixed(2)} s
              </span>
              <span
                className={`font-mono text-xs tabular-nums ${statusTone.correct.text}`}
                data-testid="readout-momentum-constant"
              >
                P total stays {formatSigned(theory.pBefore, 2)} kg·m/s
              </span>
            </div>
            <dl className="grid grid-cols-2 gap-space-2 border-t border-border pt-space-2 text-xs">
              <div className="space-y-space-0_5">
                <dt className="text-foreground-secondary">Velocities (v₁, v₂)</dt>
                <dd className="font-mono tabular-nums text-foreground" data-testid="readout-current-vel">
                  {formatSigned(currentFrame.v1, 2)}, {formatSigned(currentFrame.v2, 2)} m/s
                </dd>
              </div>
              <div className="space-y-space-0_5">
                <dt className="text-foreground-secondary">Momenta (p₁, p₂)</dt>
                <dd className="font-mono tabular-nums text-foreground" data-testid="readout-current-momenta">
                  {formatSigned(currentFrame.p1, 2)}, {formatSigned(currentFrame.p2, 2)} kg·m/s
                </dd>
              </div>
              <div className="space-y-space-0_5">
                <dt className="text-foreground-secondary">Total momentum P</dt>
                <dd className="font-mono font-semibold tabular-nums text-foreground" data-testid="readout-current-P">
                  {formatSigned(currentFrame.P, 2)} kg·m/s
                </dd>
              </div>
              <div className="space-y-space-0_5">
                <dt className="text-foreground-secondary">Total KE</dt>
                <dd className="font-mono font-semibold tabular-nums text-foreground" data-testid="readout-current-KE">
                  {currentFrame.KE.toFixed(2)} J
                </dd>
              </div>
            </dl>
          </div>

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
                  ? `Matter: ${formatSigned(activeRun.measuredV1After!, 2)}, ${formatSigned(activeRun.measuredV2After!, 2)} m/s`
                  : `At t = ${currentFrame.t.toFixed(2)} s: ${formatSigned(currentFrame.v1, 2)}, ${formatSigned(currentFrame.v2, 2)} m/s`
              }
              testId="readout-after-vel"
            />
            <PlaygroundStat
              label="Momentum (before → after)"
              value={`${formatSigned(theory.pBefore, 2)} → ${formatSigned(theory.pAfter, 2)} kg·m/s`}
              detail={`P total stays ${formatSigned(currentFrame.P, 2)} kg·m/s`}
              testId="readout-momentum"
            />
            <PlaygroundStat
              label="Kinetic energy (before → after)"
              value={`${theory.keBefore.toFixed(2)} → ${theory.keAfter.toFixed(2)} J`}
              detail={`At t = ${currentFrame.t.toFixed(2)} s: ${currentFrame.KE.toFixed(2)} J`}
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
                  : "—"
              }
              detail={
                hasMeasuredAfter
                  ? `Δv₁ = ${Math.abs(activeRun.measuredV1After! - theory.v1After).toFixed(3)}, Δv₂ = ${Math.abs(activeRun.measuredV2After! - theory.v2After).toFixed(3)} m/s`
                  : "No impact on the 6 m track"
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
