"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Matter from "matter-js";
import { Pause, Play, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/shadcn/Button";
import {
  cartHeightMeters,
  cartWidthMeters,
  computeCollisionTheory,
  DEFAULT_COLLISION_INPUT,
  INITIAL_CART1_POS_M,
  INITIAL_CART2_POS_M,
  MASS_STEP_KG,
  MAX_MASS_KG,
  MAX_VELOCITY_MPS,
  MIN_MASS_KG,
  MIN_VELOCITY_MPS,
  TRACK_HALF_SPAN_M,
  VELOCITY_STEP_MPS,
  type CollisionInput,
} from "@/lib/playground/collisions";
import {
  computeCartSvgBox,
  computeTrackBumpers,
  computeVelocityArrow,
  formatSigned,
  meterToSvgX,
  SVG_VIEWBOX,
  TRACK_LEFT_X,
  TRACK_RIGHT_X,
  TRACK_TICKS,
} from "@/lib/playground/collisionsLayout";
import "../isometric/isometric.css";
import "./collisions.css";

const MATTER_SCALE = 100; // 1 m = 100 Matter units
const DT_MS = 1000 / 60;
const VELOCITY_TO_MATTER = MATTER_SCALE * (DT_MS / 1000);
const POST_COLLISION_TRAVEL_FRAMES = 54; // ~0.9 s after collision so separation/sticking is clearly visible
const MAX_SIM_FRAMES = 2000;

export type SimPhase = "ready" | "running" | "paused" | "done";

export type CollisionSimSnapshot = {
  phase: SimPhase;
  hasCollided: boolean;
  x1: number;
  x2: number;
  v1: number;
  v2: number;
  measuredV1After: number | null;
  measuredV2After: number | null;
  reducedMotion: boolean;
};

export type CollisionsProps = {
  input?: CollisionInput;
  onInputChange?: (next: CollisionInput) => void;
  selectedCart?: 1 | 2;
  onSelectCart?: (cart: 1 | 2) => void;
  onSnapshot?: (snapshot: CollisionSimSnapshot) => void;
  /** Imperative command token from parent showcase controls. */
  command?: { type: "play" | "pause" | "reset"; seq: number } | null;
  /** Compact mode shows inline Play/Pause/Reset/Elastic-Stick controls inside the figure box (for the grid card). */
  showInlineControls?: boolean;
  className?: string;
};

type SimEngineState = {
  engine: Matter.Engine;
  body1: Matter.Body;
  body2: Matter.Body;
  hasCollided: boolean;
  impactX: number | null;
  postFrames: number;
  totalFrames: number;
  measuredV1After: number | null;
  measuredV2After: number | null;
  willCollide: boolean;
  phase: SimPhase;
};

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const roundToStep = (v: number, step: number) => Math.round(v / step) * step;

function createWorld(input: CollisionInput, willCollide: boolean): SimEngineState {
  // Disable resting-contact suppression so slow closing speeds preserve exact restitution e.
  (Matter.Resolver as unknown as { _restingThresh: number })._restingThresh = 0;

  const engine = Matter.Engine.create({
    gravity: { x: 0, y: 0, scale: 0 },
    positionIterations: 10,
    velocityIterations: 6,
  });

  const w1 = cartWidthMeters(input.m1) * MATTER_SCALE;
  const h1 = cartHeightMeters(input.m1) * MATTER_SCALE;
  const w2 = cartWidthMeters(input.m2) * MATTER_SCALE;
  const h2 = cartHeightMeters(input.m2) * MATTER_SCALE;

  const commonBodyOptions: Matter.IChamferableBodyDefinition = {
    friction: 0,
    frictionStatic: 0,
    frictionAir: 0,
    restitution: input.e,
    slop: 0,
    inertia: Infinity,
  };

  const body1 = Matter.Bodies.rectangle(INITIAL_CART1_POS_M * MATTER_SCALE, 0, w1, h1, {
    ...commonBodyOptions,
    label: "cart1",
  });
  const body2 = Matter.Bodies.rectangle(INITIAL_CART2_POS_M * MATTER_SCALE, 0, w2, h2, {
    ...commonBodyOptions,
    label: "cart2",
  });

  Matter.Body.setMass(body1, input.m1);
  Matter.Body.setInertia(body1, Infinity);
  Matter.Body.setMass(body2, input.m2);
  Matter.Body.setInertia(body2, Infinity);

  Matter.Body.setVelocity(body1, { x: input.v1 * VELOCITY_TO_MATTER, y: 0 });
  Matter.Body.setVelocity(body2, { x: input.v2 * VELOCITY_TO_MATTER, y: 0 });

  Matter.Composite.add(engine.world, [body1, body2]);

  const sim: SimEngineState = {
    engine,
    body1,
    body2,
    hasCollided: false,
    impactX: null,
    postFrames: 0,
    totalFrames: 0,
    measuredV1After: null,
    measuredV2After: null,
    willCollide,
    phase: "ready",
  };

  Matter.Events.on(engine, "collisionStart", () => {
    if (!sim.hasCollided) {
      sim.hasCollided = true;
      const rightEdge1 = body1.position.x / MATTER_SCALE + cartWidthMeters(input.m1) / 2;
      const leftEdge2 = body2.position.x / MATTER_SCALE - cartWidthMeters(input.m2) / 2;
      sim.impactX = (rightEdge1 + leftEdge2) / 2;
    }
  });

  return sim;
}

function stepSimulationOnce(sim: SimEngineState, input: CollisionInput): boolean {
  const halfW1 = cartWidthMeters(input.m1) / 2;
  const halfW2 = cartWidthMeters(input.m2) / 2;

  Matter.Engine.update(sim.engine, DT_MS);
  sim.totalFrames += 1;

  // Enforce 1D track constraint strictly (no vertical drift or rotation).
  if (sim.body1.position.y !== 0 || sim.body1.angle !== 0) {
    Matter.Body.setPosition(sim.body1, { x: sim.body1.position.x, y: 0 });
    Matter.Body.setAngle(sim.body1, 0);
  }
  if (sim.body2.position.y !== 0 || sim.body2.angle !== 0) {
    Matter.Body.setPosition(sim.body2, { x: sim.body2.position.x, y: 0 });
    Matter.Body.setAngle(sim.body2, 0);
  }

  let x1 = sim.body1.position.x / MATTER_SCALE;
  let x2 = sim.body2.position.x / MATTER_SCALE;
  const v1 = sim.body1.velocity.x / VELOCITY_TO_MATTER;
  const v2 = sim.body2.velocity.x / VELOCITY_TO_MATTER;

  if (sim.hasCollided) {
    sim.postFrames += 1;
    // Capture post-collision velocity right after collision resolution stabilizes.
    if (sim.postFrames === 1 || sim.postFrames === 2) {
      sim.measuredV1After = v1;
      sim.measuredV2After = v2;
    }
  }

  // Stop cleanly at track bumpers without bouncing off boundaries.
  const hitLeftBumper = x1 - halfW1 <= -TRACK_HALF_SPAN_M;
  const hitRightBumper = x2 + halfW2 >= TRACK_HALF_SPAN_M;
  if (hitLeftBumper) {
    x1 = -TRACK_HALF_SPAN_M + halfW1;
    Matter.Body.setPosition(sim.body1, { x: x1 * MATTER_SCALE, y: 0 });
  }
  if (hitRightBumper) {
    x2 = TRACK_HALF_SPAN_M - halfW2;
    Matter.Body.setPosition(sim.body2, { x: x2 * MATTER_SCALE, y: 0 });
  }

  if (hitLeftBumper || hitRightBumper) {
    if (sim.hasCollided && sim.measuredV1After === null) {
      sim.measuredV1After = v1;
      sim.measuredV2After = v2;
    }
    sim.phase = "done";
    return false;
  }

  if (sim.hasCollided) {
    const bothStopped = Math.abs(v1) < 1e-4 && Math.abs(v2) < 1e-4;
    if ((bothStopped && sim.postFrames >= 24) || sim.postFrames >= POST_COLLISION_TRAVEL_FRAMES) {
      sim.phase = "done";
      return false;
    }
  } else if (!sim.willCollide) {
    const bothStopped = Math.abs(v1) < 1e-4 && Math.abs(v2) < 1e-4;
    if (bothStopped || sim.totalFrames >= 75) {
      sim.phase = "done";
      return false;
    }
  }

  if (sim.totalFrames >= MAX_SIM_FRAMES) {
    sim.phase = "done";
    return false;
  }

  return true;
}

export function Collisions({
  input: controlledInput,
  onInputChange,
  selectedCart: controlledSelected,
  onSelectCart,
  onSnapshot,
  command,
  showInlineControls = true,
  className,
}: CollisionsProps) {
  const [internalInput, setInternalInput] = useState<CollisionInput>(DEFAULT_COLLISION_INPUT);
  const input = controlledInput ?? internalInput;
  const setInput = useCallback(
    (next: CollisionInput) => {
      if (onInputChange) onInputChange(next);
      else setInternalInput(next);
    },
    [onInputChange],
  );

  const [internalSelected, setInternalSelected] = useState<1 | 2>(1);
  const selectedCart = controlledSelected ?? internalSelected;
  const selectCart = useCallback(
    (cart: 1 | 2) => {
      if (onSelectCart) onSelectCart(cart);
      else setInternalSelected(cart);
    },
    [onSelectCart],
  );

  const theory = useMemo(() => computeCollisionTheory(input), [input]);

  const [reducedMotion, setReducedMotion] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mq.matches);
    const onChange = () => setReducedMotion(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const simRef = useRef<SimEngineState | null>(null);
  const rafRef = useRef<number>(0);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const dragRef = useRef<{ cart: 1 | 2; startClientX: number; startVel: number; moved: boolean } | null>(null);

  const [snapshot, setSnapshot] = useState<CollisionSimSnapshot>({
    phase: "ready",
    hasCollided: false,
    x1: INITIAL_CART1_POS_M,
    x2: INITIAL_CART2_POS_M,
    v1: input.v1,
    v2: input.v2,
    measuredV1After: null,
    measuredV2After: null,
    reducedMotion: false,
  });

  const emitSnapshot = useCallback(
    (next: CollisionSimSnapshot) => {
      setSnapshot(next);
      onSnapshot?.(next);
    },
    [onSnapshot],
  );

  const stopLoop = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
    }
  }, []);

  const syncSnapshotFromSim = useCallback(
    (sim: SimEngineState, isReduced: boolean) => {
      emitSnapshot({
        phase: sim.phase,
        hasCollided: sim.hasCollided,
        x1: sim.body1.position.x / MATTER_SCALE,
        x2: sim.body2.position.x / MATTER_SCALE,
        v1: sim.body1.velocity.x / VELOCITY_TO_MATTER,
        v2: sim.body2.velocity.x / VELOCITY_TO_MATTER,
        measuredV1After: sim.measuredV1After,
        measuredV2After: sim.measuredV2After,
        reducedMotion: isReduced,
      });
    },
    [emitSnapshot],
  );

  const resetWorld = useCallback(
    (nextInput: CollisionInput = input) => {
      stopLoop();
      const nextTheory = computeCollisionTheory(nextInput);
      const nextSim = createWorld(nextInput, nextTheory.willCollide);
      simRef.current = nextSim;
      syncSnapshotFromSim(nextSim, reducedMotion);
    },
    [input, reducedMotion, stopLoop, syncSnapshotFromSim],
  );

  // Reinitialize world whenever initial input parameters change.
  useEffect(() => {
    resetWorld(input);
    return () => stopLoop();
  }, [input, resetWorld, stopLoop]);

  const startPlay = useCallback(() => {
    let sim = simRef.current;
    if (!sim || sim.phase === "done") {
      sim = createWorld(input, theory.willCollide);
      simRef.current = sim;
    }

    if (reducedMotion) {
      stopLoop();
      sim.phase = "running";
      while (stepSimulationOnce(sim, input)) {
        // Step synchronously to end state under reduced motion.
      }
      syncSnapshotFromSim(sim, true);
      return;
    }

    if (sim.phase === "running") return;
    sim.phase = "running";
    syncSnapshotFromSim(sim, false);

    let lastTime = performance.now();
    let acc = 0;

    const tick = (now: number) => {
      const activeSim = simRef.current;
      if (!activeSim || activeSim.phase !== "running") return;
      const frameDelta = Math.min(50, Math.max(0, now - lastTime));
      lastTime = now;
      acc += frameDelta;

      let keepGoing = true;
      while (acc >= DT_MS && keepGoing) {
        keepGoing = stepSimulationOnce(activeSim, input);
        acc -= DT_MS;
      }

      syncSnapshotFromSim(activeSim, false);
      if (keepGoing && activeSim.phase === "running") {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        rafRef.current = 0;
      }
    };

    rafRef.current = requestAnimationFrame(tick);
  }, [input, reducedMotion, stopLoop, syncSnapshotFromSim, theory.willCollide]);

  const pausePlay = useCallback(() => {
    stopLoop();
    const sim = simRef.current;
    if (sim && sim.phase === "running") {
      sim.phase = "paused";
      syncSnapshotFromSim(sim, reducedMotion);
    }
  }, [reducedMotion, stopLoop, syncSnapshotFromSim]);

  const togglePlayPause = useCallback(() => {
    if (snapshot.phase === "running") pausePlay();
    else startPlay();
  }, [pausePlay, snapshot.phase, startPlay]);

  // Respond to imperative commands from parent showcase controls.
  const lastSeqRef = useRef<number>(-1);
  useEffect(() => {
    if (!command || command.seq === lastSeqRef.current) return;
    lastSeqRef.current = command.seq;
    if (command.type === "play") startPlay();
    else if (command.type === "pause") pausePlay();
    else if (command.type === "reset") resetWorld(input);
  }, [command, input, pausePlay, resetWorld, startPlay]);

  const adjustCartVelocity = useCallback(
    (cart: 1 | 2, delta: number) => {
      const nextVal = clamp(
        roundToStep((cart === 1 ? input.v1 : input.v2) + delta, VELOCITY_STEP_MPS),
        MIN_VELOCITY_MPS,
        MAX_VELOCITY_MPS,
      );
      setInput(cart === 1 ? { ...input, v1: nextVal } : { ...input, v2: nextVal });
    },
    [input, setInput],
  );

  const adjustCartMass = useCallback(
    (cart: 1 | 2, delta: number) => {
      const nextVal = clamp(
        roundToStep((cart === 1 ? input.m1 : input.m2) + delta, MASS_STEP_KG),
        MIN_MASS_KG,
        MAX_MASS_KG,
      );
      setInput(cart === 1 ? { ...input, m1: nextVal } : { ...input, m2: nextVal });
    },
    [input, setInput],
  );

  const handleCartPointerDown = (cart: 1 | 2, e: React.PointerEvent<SVGGElement>) => {
    e.stopPropagation();
    selectCart(cart);
    dragRef.current = {
      cart,
      startClientX: e.clientX,
      startVel: cart === 1 ? input.v1 : input.v2,
      moved: false,
    };
    e.currentTarget.setPointerCapture?.(e.pointerId);
  };

  const handleCartPointerMove = (e: React.PointerEvent<SVGGElement>) => {
    const drag = dragRef.current;
    if (!drag || !svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const dxPx = e.clientX - drag.startClientX;
    if (Math.abs(dxPx) > 4) drag.moved = true;
    if (!drag.moved || rect.width <= 0) return;

    // 45 px of horizontal drag changes velocity by 1.0 m/s (snapped to 0.5 m/s).
    const deltaVel = (dxPx / Math.max(180, rect.width)) * 6.0;
    const nextVel = clamp(
      roundToStep(drag.startVel + deltaVel, VELOCITY_STEP_MPS),
      MIN_VELOCITY_MPS,
      MAX_VELOCITY_MPS,
    );
    const currentVel = drag.cart === 1 ? input.v1 : input.v2;
    if (nextVel !== currentVel) {
      setInput(drag.cart === 1 ? { ...input, v1: nextVel } : { ...input, v2: nextVel });
    }
  };

  const handleCartPointerUp = () => {
    dragRef.current = null;
  };

  const handleCartKeyDown = (cart: 1 | 2, e: React.KeyboardEvent<SVGGElement>) => {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      adjustCartVelocity(cart, -VELOCITY_STEP_MPS);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      adjustCartVelocity(cart, VELOCITY_STEP_MPS);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      adjustCartMass(cart, MASS_STEP_KG);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      adjustCartMass(cart, -MASS_STEP_KG);
    } else if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      togglePlayPause();
    } else if (e.key === "r" || e.key === "R") {
      e.preventDefault();
      resetWorld(input);
    }
  };

  const box1 = computeCartSvgBox(snapshot.x1, input.m1);
  const box2 = computeCartSvgBox(snapshot.x2, input.m2);
  const arrow1 = computeVelocityArrow(box1.centerX, box1.arrowY, snapshot.v1);
  const arrow2 = computeVelocityArrow(box2.centerX, box2.arrowY, snapshot.v2);
  const bumpers = computeTrackBumpers();
  const impactXSvg = simRef.current?.impactX !== null && simRef.current?.impactX !== undefined
    ? meterToSvgX(simRef.current.impactX)
    : null;
  const showImpactSpark =
    snapshot.hasCollided &&
    impactXSvg !== null &&
    simRef.current !== null &&
    simRef.current.postFrames <= 14;

  const isElastic = Math.abs(input.e - 1) < 0.01;
  const isStick = input.e < 0.01;
  const modeSummary = isElastic ? "Elastic" : isStick ? "Stick (e=0)" : `e = ${input.e.toFixed(2)}`;

  return (
    <div
      data-testid="collisions-figure"
      className={`iso-studio-surface flex h-full w-full flex-col justify-between select-none ${className ?? ""}`.trim()}
    >
      <div className="flex items-center justify-between gap-space-2 px-space-3 pt-space-2_5 text-xs text-foreground-secondary">
        <span className="font-mono tabular-nums" data-testid="collisions-live-summary">
          {snapshot.hasCollided ? "After" : "Before"}: v₁ {formatSigned(snapshot.v1)} · v₂ {formatSigned(snapshot.v2)} m/s
        </span>
        <span className="font-mono">{modeSummary}</span>
      </div>

      <svg
        ref={svgRef}
        viewBox={SVG_VIEWBOX}
        role="img"
        aria-label={`1D collision track with Cart 1 (${input.m1.toFixed(1)} kg at ${formatSigned(snapshot.v1)} m/s) and Cart 2 (${input.m2.toFixed(1)} kg at ${formatSigned(snapshot.v2)} m/s), coefficient of restitution ${input.e.toFixed(2)}.`}
        className="w-full flex-1"
      >
        {/* Track rail, end bumpers, and 1 m ticks */}
        <line
          x1={TRACK_LEFT_X}
          y1={bumpers.trackTopY}
          x2={TRACK_RIGHT_X}
          y2={bumpers.trackTopY}
          className="collision-track-rail"
        />
        <rect
          x={bumpers.left.x}
          y={bumpers.left.y}
          width={bumpers.left.width}
          height={bumpers.left.height}
          rx={bumpers.left.rx}
          className="collision-bumper"
        />
        <rect
          x={bumpers.right.x}
          y={bumpers.right.y}
          width={bumpers.right.width}
          height={bumpers.right.height}
          rx={bumpers.right.rx}
          className="collision-bumper"
        />

        {TRACK_TICKS.map((m) => {
          const tx = meterToSvgX(m);
          return (
            <g key={m}>
              <line x1={tx} y1={bumpers.tickY1} x2={tx} y2={bumpers.tickY2} className="collision-tick-major" />
              <text x={tx} y={bumpers.tickLabelY} textAnchor="middle" className="collision-tick-label">
                {m === 0 ? "0m" : `${m > 0 ? "+" : ""}${m}`}
              </text>
            </g>
          );
        })}

        {/* Subtle impact mark briefly shown at contact */}
        {showImpactSpark && impactXSvg !== null && (
          <g className="collision-impact-mark" aria-hidden="true">
            <line x1={impactXSvg} y1={box1.y - 6} x2={impactXSvg} y2={box1.y - 14} />
            <line x1={impactXSvg - 5} y1={box1.y - 4} x2={impactXSvg - 10} y2={box1.y - 10} />
            <line x1={impactXSvg + 5} y1={box1.y - 4} x2={impactXSvg + 10} y2={box1.y - 10} />
          </g>
        )}

        {/* Velocity arrows above each cart */}
        {[
          { id: 1 as const, arrow: arrow1, vel: snapshot.v1 },
          { id: 2 as const, arrow: arrow2, vel: snapshot.v2 },
        ].map(({ id, arrow, vel }) => {
          const isSelected = selectedCart === id;
          return (
            <g key={`arrow-${id}`} aria-hidden="true">
              {arrow.hasArrow ? (
                <>
                  <line
                    x1={arrow.startX}
                    y1={arrow.y}
                    x2={arrow.endX}
                    y2={arrow.y}
                    className={isSelected ? "collision-arrow-selected" : "collision-arrow"}
                  />
                  <polygon
                    points={arrow.headPoints}
                    className={isSelected ? "collision-arrow-head-selected" : "collision-arrow-head"}
                  />
                </>
              ) : (
                <circle
                  cx={arrow.startX}
                  cy={arrow.y}
                  r={3}
                  className={isSelected ? "collision-arrow-head-selected" : "collision-arrow-head"}
                />
              )}
              <text
                x={arrow.labelX}
                y={arrow.labelY}
                textAnchor="middle"
                className={isSelected ? "collision-vel-label-selected" : "collision-vel-label"}
              >
                {formatSigned(vel)} m/s
              </text>
            </g>
          );
        })}

        {/* Cart 1 & Cart 2 */}
        {[
          { id: 1 as const, box: box1, mass: input.m1, vel: snapshot.v1 },
          { id: 2 as const, box: box2, mass: input.m2, vel: snapshot.v2 },
        ].map(({ id, box, mass, vel }) => {
          const isSelected = selectedCart === id;
          return (
            <g
              key={`cart-${id}`}
              data-testid={`collision-cart-${id}`}
              data-selected={isSelected ? "true" : "false"}
              role="slider"
              tabIndex={0}
              aria-label={`Cart ${id}. Drag horizontally or press Left and Right arrows to adjust velocity, Up and Down arrows to adjust mass, Space to play or pause.`}
              aria-valuemin={MIN_VELOCITY_MPS}
              aria-valuemax={MAX_VELOCITY_MPS}
              aria-valuenow={id === 1 ? input.v1 : input.v2}
              aria-valuetext={`Cart ${id}, mass ${mass.toFixed(1)} kg, velocity ${formatSigned(vel)} meters per second`}
              onFocus={() => selectCart(id)}
              onPointerDown={(e) => handleCartPointerDown(id, e)}
              onPointerMove={handleCartPointerMove}
              onPointerUp={handleCartPointerUp}
              onPointerCancel={handleCartPointerUp}
              onKeyDown={(e) => handleCartKeyDown(id, e)}
              className="collision-cart-focus cursor-grab active:cursor-grabbing"
            >
              <circle
                cx={box.wheelLeftX}
                cy={box.wheelY}
                r={box.wheelR}
                className={isSelected ? "collision-cart-wheel-selected" : "collision-cart-wheel"}
              />
              <circle
                cx={box.wheelRightX}
                cy={box.wheelY}
                r={box.wheelR}
                className={isSelected ? "collision-cart-wheel-selected" : "collision-cart-wheel"}
              />
              <rect
                x={box.x}
                y={box.y}
                width={box.width}
                height={box.height}
                rx={box.rx}
                className={isSelected ? "collision-cart-selected" : "collision-cart"}
              />
              <rect
                x={box.innerX}
                y={box.innerY}
                width={box.innerWidth}
                height={box.innerHeight}
                rx={box.innerRx}
                className={isSelected ? "collision-cart-inner-selected" : "collision-cart-inner"}
              />
              <text x={box.centerX} y={box.idTextY} textAnchor="middle" dominantBaseline="central" className="collision-cart-id">
                C{id}
              </text>
              <text x={box.centerX} y={box.massTextY} textAnchor="middle" dominantBaseline="central" className="collision-cart-mass">
                {mass.toFixed(1)}kg
              </text>
            </g>
          );
        })}
      </svg>

      {showInlineControls && (
        <div className="flex flex-wrap items-center justify-between gap-space-2 px-space-3 pb-space-2_5">
          <div className="flex items-center gap-space-1_5">
            <Button
              type="button"
              variant="primary"
              size="compact"
              onClick={togglePlayPause}
              aria-label={snapshot.phase === "running" ? "Pause simulation" : "Play simulation"}
              data-testid="collisions-inline-play"
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
              onClick={() => resetWorld(input)}
              aria-label="Reset carts"
              data-testid="collisions-inline-reset"
            >
              <RotateCcw aria-hidden="true" className="size-space-3_5" />
              Reset
            </Button>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="compact"
            onClick={() => setInput({ ...input, e: isStick ? 1 : 0 })}
            aria-label="Toggle elastic or stick together"
            data-testid="collisions-inline-mode"
          >
            {isStick ? "Stick (e = 0)" : "Elastic (e = 1)"}
          </Button>
        </div>
      )}
    </div>
  );
}
