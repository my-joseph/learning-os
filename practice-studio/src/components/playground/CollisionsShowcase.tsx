"use client";

import React, { useMemo } from "react";
import { Crosshair, Pause, Play, RotateCcw } from "lucide-react";
import { FormattedText } from "@/components/FormattedText";
import { Collisions } from "./Collisions";
import { useCollisionPlayback } from "./useCollisionPlayback";
import { PlaygroundReadout, PlaygroundShowcase, PlaygroundStat, PlaygroundStats } from "@/components/playground/PlaygroundShowcase";
import { Numeral } from "@/components/ui/Numeral";
import { Badge } from "@/components/ui/shadcn/Badge";
import { Button } from "@/components/ui/shadcn/Button";
import { SegmentedChips } from "@/components/ui/shadcn/Tabs";
import {
  cartStartBounds,
  clampCartPosition,
  computeCollisionTheory,
  INITIAL_CART1_POS_M,
  INITIAL_CART2_POS_M,
  MASS_STEP_KG,
  MAX_MASS_KG,
  MAX_RESTITUTION,
  MAX_VELOCITY_MPS,
  MIN_MASS_KG,
  MIN_RESTITUTION,
  MIN_VELOCITY_MPS,
  POSITION_STEP_M,
  RESTITUTION_STEP,
  VELOCITY_STEP_MPS,
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
  const playback = useCollisionPlayback();
  const { run, frameIndex, playing: isPlaying, selectedCart, setSelectedCart, changeInput, seek, togglePlayback, reset } = playback;
  const input = run.input;
  const theory = useMemo(() => computeCollisionTheory(input), [input]);
  const x1Start = input.x1 ?? INITIAL_CART1_POS_M;
  const x2Start = input.x2 ?? INITIAL_CART2_POS_M;
  const maxFrameIndex = run.frames.length - 1;
  const currentFrame = run.frames[frameIndex];
  const durationSec = run.frames[maxFrameIndex].t;

  const { impactFrameIndex, impactTime } = run;
  const impactRatio = impactFrameIndex !== null ? impactFrameIndex / maxFrameIndex : null;
  const atImpact = impactFrameIndex === frameIndex;
  const hasCollided = impactFrameIndex !== null && frameIndex >= impactFrameIndex;
  const impactBeforeFrame = atImpact ? run.frames[Math.max(0, frameIndex - 1)] : null;
  const mode = modeForRestitution(input.e);

  const handleModeChange = (next: string) => {
    const e = next === "elastic" ? 1 : next === "stick" ? 0 : 0.5;
    if (next !== mode) changeInput({ ...input, e });
  };

  const handleCartField = (field: "m1" | "m2" | "v1" | "v2" | "e", value: number) => {
    changeInput({ ...input, [field]: value });
  };

  const handleCartPosition = (cart: 1 | 2, value: number) => {
    const other = cart === 1 ? x2Start : x1Start;
    const clamped = Number(clampCartPosition(cart, value, input.m1, input.m2, other).toFixed(2));
    changeInput(cart === 1 ? { ...input, x1: clamped } : { ...input, x2: clamped });
  };

  const handleScrubberKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    let next: number;
    switch (event.key) {
      case "ArrowRight":
      case "ArrowUp": next = frameIndex + 1; break;
      case "ArrowLeft":
      case "ArrowDown": next = frameIndex - 1; break;
      case "PageUp": next = frameIndex + 10; break;
      case "PageDown": next = frameIndex - 10; break;
      case "Home": next = 0; break;
      case "End": next = maxFrameIndex; break;
      default: return;
    }
    event.preventDefault();
    seek(Math.max(0, Math.min(maxFrameIndex, next)));
  };

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
          : frameIndex > 0
            ? "Before impact"
            : "Ready";

  const keLostPct = theory.keBefore > 1e-9 ? (theory.keLost / theory.keBefore) * 100 : 0;
  const cart1Bounds = cartStartBounds(1, input.m1, input.m2, x2Start);
  const cart2Bounds = cartStartBounds(2, input.m1, input.m2, x1Start);
  const cart1Min = Math.ceil(cart1Bounds.min * 100) / 100;
  const cart1Max = Math.floor(cart1Bounds.max * 100) / 100;
  const cart2Min = Math.ceil(cart2Bounds.min * 100) / 100;
  const cart2Max = Math.floor(cart2Bounds.max * 100) / 100;

  return (
    <PlaygroundShowcase
      title="Collisions"
      layout="wide"
      caption={<span data-testid="collisions-caption">{captionText}</span>}
      figure={
        <div className="space-y-space-3">
          <Collisions playback={playback} interactive="detail" />

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
                  onClick={() => { if (impactFrameIndex !== null) seek(impactFrameIndex); }}
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
                value={frameIndex}
                disabled={maxFrameIndex === 0}
                aria-label="Time"
                aria-valuetext={`${currentFrame.t.toFixed(2)} seconds${atImpact ? ", at impact" : ""}`}
                onChange={(e) => seek(Number(e.target.value))}
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
          layout="wide"
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
                onClick={togglePlayback}
                data-testid="collisions-play-btn"
              >
                {isPlaying ? (
                  <Pause aria-hidden="true" className="size-space-3_5" />
                ) : (
                  <Play aria-hidden="true" className="size-space-3_5" />
                )}
                {isPlaying ? "Pause" : frameIndex >= maxFrameIndex && maxFrameIndex > 0 ? "Replay" : "Play"}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="compact"
                onClick={(event) => {
                  reset();
                  if (event.detail > 0) event.currentTarget.blur();
                }}
                data-testid="collisions-reset-btn"
              >
                <RotateCcw aria-hidden="true" className="size-space-3_5" />
                Reset
              </Button>
            </div>
          }
        >
          {/* Current frame values at t (shows before | after columns when scrubbed to impact) */}
          <div
            className="space-y-space-2 rounded-lg border border-border bg-surface-panel p-space-3"
            data-testid="readout-current-frame"
          >
            <div className="flex flex-wrap items-center justify-between gap-space-2">
              <span className="font-mono text-xs font-semibold tabular-nums text-foreground" data-testid="readout-current-time">
                {atImpact ? `At impact (t = ${currentFrame.t.toFixed(2)} s)` : `At t = ${currentFrame.t.toFixed(2)} s`}
              </span>
              <span
                className={`font-mono text-xs tabular-nums ${statusTone.correct.text}`}
                data-testid="readout-momentum-constant"
              >
                P total stays {formatSigned(theory.pBefore, 2)} kg·m/s
              </span>
            </div>
            {impactBeforeFrame ? (
              <div className="grid grid-cols-2 gap-space-3 border-t border-border pt-space-2 text-xs">
                <div className="space-y-space-1_5" data-testid="readout-impact-before">
                  <div className="flex items-baseline justify-between gap-space-1">
                    <span className="font-semibold text-foreground">Before</span>
                    <span className="font-mono tabular-nums text-foreground-secondary">
                      t = {impactBeforeFrame.t.toFixed(2)} s
                    </span>
                  </div>
                  <dl className="space-y-space-1">
                    <div>
                      <dt className="text-foreground-secondary">Velocities (v₁, v₂)</dt>
                      <dd className="font-mono tabular-nums text-foreground">
                        {formatSigned(impactBeforeFrame.v1, 2)}, {formatSigned(impactBeforeFrame.v2, 2)} m/s
                      </dd>
                    </div>
                    <div>
                      <dt className="text-foreground-secondary">Momenta (p₁, p₂)</dt>
                      <dd className="font-mono tabular-nums text-foreground">
                        {formatSigned(impactBeforeFrame.p1, 2)}, {formatSigned(impactBeforeFrame.p2, 2)} kg·m/s
                      </dd>
                    </div>
                    <div>
                      <dt className="text-foreground-secondary">Total P / KE</dt>
                      <dd className="font-mono font-semibold tabular-nums text-foreground">
                        {formatSigned(impactBeforeFrame.P, 2)} kg·m/s · {impactBeforeFrame.KE.toFixed(2)} J
                      </dd>
                    </div>
                  </dl>
                </div>
                <div className="space-y-space-1_5 border-l border-border pl-space-3" data-testid="readout-impact-after">
                  <div className="flex items-baseline justify-between gap-space-1">
                    <span className="font-semibold text-foreground">After</span>
                    <span className="font-mono tabular-nums text-foreground-secondary">
                      t = {currentFrame.t.toFixed(2)} s
                    </span>
                  </div>
                  <dl className="space-y-space-1">
                    <div>
                      <dt className="text-foreground-secondary">Velocities (v₁, v₂)</dt>
                      <dd className="font-mono tabular-nums text-foreground">
                        {formatSigned(currentFrame.v1, 2)}, {formatSigned(currentFrame.v2, 2)} m/s
                      </dd>
                    </div>
                    <div>
                      <dt className="text-foreground-secondary">Momenta (p₁, p₂)</dt>
                      <dd className="font-mono tabular-nums text-foreground">
                        {formatSigned(currentFrame.p1, 2)}, {formatSigned(currentFrame.p2, 2)} kg·m/s
                      </dd>
                    </div>
                    <div>
                      <dt className="text-foreground-secondary">Total P / KE</dt>
                      <dd className="font-mono font-semibold tabular-nums text-foreground">
                        {formatSigned(currentFrame.P, 2)} kg·m/s · {currentFrame.KE.toFixed(2)} J
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
            ) : (
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
            )}
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
                    <Numeral className="font-mono" data-testid="cart1-vel-value">{formatSigned(input.v1)} m/s</Numeral>
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
                <div className="space-y-space-1">
                  <div className="flex items-center justify-between text-xs">
                    <label htmlFor="cart1-pos" className="text-foreground-secondary">Start x₁</label>
                    <Numeral className="font-mono" data-testid="cart1-pos-value">{formatSigned(x1Start, 2)} m</Numeral>
                  </div>
                  <input
                    id="cart1-pos"
                    type="range"
                    min={cart1Min}
                    max={cart1Max}
                    step={POSITION_STEP_M}
                    value={x1Start}
                    aria-label="Cart 1 start position in meters"
                    onChange={(e) => handleCartPosition(1, Number(e.target.value))}
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
                    <Numeral className="font-mono" data-testid="cart2-vel-value">{formatSigned(input.v2)} m/s</Numeral>
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
                <div className="space-y-space-1">
                  <div className="flex items-center justify-between text-xs">
                    <label htmlFor="cart2-pos" className="text-foreground-secondary">Start x₂</label>
                    <Numeral className="font-mono" data-testid="cart2-pos-value">{formatSigned(x2Start, 2)} m</Numeral>
                  </div>
                  <input
                    id="cart2-pos"
                    type="range"
                    min={cart2Min}
                    max={cart2Max}
                    step={POSITION_STEP_M}
                    value={x2Start}
                    aria-label="Cart 2 start position in meters"
                    onChange={(e) => handleCartPosition(2, Number(e.target.value))}
                    className="min-h-touch w-full cursor-pointer accent-accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Predicted collision outcomes */}
          <PlaygroundStats>
            <PlaygroundStat
              label="Before velocities"
              value={`${formatSigned(theory.v1)}, ${formatSigned(theory.v2)} m/s`}
              detail={`p₁ = ${formatSigned(theory.p1Before, 2)}, p₂ = ${formatSigned(theory.p2Before, 2)} kg·m/s`}
              testId="readout-before-vel"
            />
            <PlaygroundStat
              label="Predicted velocities after impact"
              value={
                theory.willCollide
                  ? `${formatSigned(theory.v1After, 2)}, ${formatSigned(theory.v2After, 2)} m/s`
                  : "No collision"
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
          </PlaygroundStats>

          <p className="text-xs text-foreground-secondary">
            Right is positive (<FormattedText text="$+x$" />). Track is level and frictionless. Drag a cart along the track and release to launch it (slow release repositions at 0 m/s), or Tab to a cart and use Left/Right arrows to adjust velocity by 0.1 m/s, Up/Down to adjust mass, and Space to play.
          </p>
        </PlaygroundReadout>
      }
    />
  );
}
