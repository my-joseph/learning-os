"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { frame } from "@/lib/isometric/entity";
import { clamp, unproject, type Vec2 } from "@/lib/isometric/iso";
import { box, cylinder, frustum, rotateX, rotateZ, translate, zToX } from "@/lib/isometric/mesh";
import { label, scene, type Item, type Painter } from "@/lib/isometric/scene";
import { bag, el, pointer } from "@/lib/isometric/stage";
import { inject } from "@/lib/isometric/styles";
import {
  cartHeightMeters,
  cartWidthMeters,
  DEFAULT_COLLISION_INPUT,
  INITIAL_CART1_POS_M,
  INITIAL_CART2_POS_M,
  MASS_STEP_KG,
  MAX_MASS_KG,
  MAX_VELOCITY_MPS,
  MIN_MASS_KG,
  MIN_VELOCITY_MPS,
  VELOCITY_STEP_MPS,
  type CollisionInput,
} from "@/lib/playground/collisions";
import {
  computeVelocityArrowWorld,
  formatSigned,
  ISO_UNIT,
  TRACK_END_X,
  TRACK_TICKS,
} from "@/lib/playground/collisionsLayout";
import {
  precomputeCollisionRun,
  type CollisionFrame,
  type PrecomputedCollisionRun,
} from "@/lib/playground/collisionsSim";
import "../isometric/isometric.css";
import "./collisions.css";

// Isometric scene world constants (same camera feel as Lever: az = 8°, k = 0.5).
const TRACK_PAD_X = 4.0;
const TRACK_HALF_D = 10.0;
const TRACK_TOP_Z = 3.4;
const BUMPER_W = 3.0;
const BUMPER_TOP_Z = 14.0;
const CART_HALF_D = 5.2;
const WHEEL_R = 2.1;
const WHEEL_THICK = 1.3;
const WHEEL_CZ = TRACK_TOP_Z + WHEEL_R;
const CART_BASE_Z = TRACK_TOP_Z + WHEEL_R * 1.25;
const CART_MID_Z = CART_BASE_Z + 6.5;

export type SimPhase = "ready" | "running" | "paused" | "done";

export type CollisionSimSnapshot = {
  phase: SimPhase;
  hasCollided: boolean;
  t: number;
  frameIndex: number;
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
  frameIndex?: number;
  onFrameIndexChange?: (frameIndex: number) => void;
  playing?: boolean;
  onPlayingChange?: (playing: boolean) => void;
  onRunReady?: (run: PrecomputedCollisionRun) => void;
  onSnapshot?: (snapshot: CollisionSimSnapshot) => void;
  /** `"card"` shows a calm click/Enter-to-play figure for the grid; `"detail"` enables cart selection/drag/scrubbing. */
  interactive?: "card" | "detail";
  className?: string;
};

type PartId = "cart1" | "cart2";

const roundToStep = (v: number, step: number) => Math.round(v / step) * step;

const COLLISION_CAMERA = frame({
  az: 8,
  k: 0.5,
  zoom: 1.04,
  fit: [
    [-TRACK_END_X - TRACK_PAD_X, -TRACK_HALF_D, 0],
    [TRACK_END_X + TRACK_PAD_X, TRACK_HALF_D, 0],
    [-TRACK_END_X - TRACK_PAD_X, -TRACK_HALF_D, 34],
    [TRACK_END_X + TRACK_PAD_X, TRACK_HALF_D, 34],
  ],
});

// Unit wheel along +y from 0 to WHEEL_THICK, centered at x=0, z=0.
const WHEEL_PROTO = rotateX(cylinder(0, 0, 0, WHEEL_R, WHEEL_THICK, 16), -Math.PI / 2);
// Unit arrowhead cone pointing +x from x=0 to x=3.0.
const ARROW_HEAD_POS = zToX(frustum(0, 0, 0, 1.35, 0, 3.0, 12));
const ARROW_HEAD_NEG = rotateZ(ARROW_HEAD_POS, Math.PI);
// Zero-velocity dot facing +y.
const REST_DOT_PROTO = rotateX(cylinder(0, 0, -0.5, 1.05, 1.0, 12), -Math.PI / 2);

function buildCollisionsScene(params: {
  input: CollisionInput;
  frameData: CollisionFrame;
  hasCollided: boolean;
  impactX: number | null;
  postFrames: number;
  accentCart: 1 | 2 | null;
  interactive: "card" | "detail";
}): Item[] {
  const { input, frameData, hasCollided, impactX, postFrames, accentCart, interactive } = params;
  const out: Item[] = [];
  const halfTrackX = TRACK_END_X + TRACK_PAD_X;

  // 1. Track bed (long thin isometric box) and subtle wheel-groove lines
  out.push({
    mesh: box(-halfTrackX, -TRACK_HALF_D, 0, halfTrackX, TRACK_HALF_D, TRACK_TOP_Z),
    shade: true,
    inert: true,
  });
  for (const ry of [-4.4, 4.4]) {
    out.push({
      pts: [
        [-TRACK_END_X, ry, TRACK_TOP_Z + 0.04],
        [TRACK_END_X, ry, TRACK_TOP_Z + 0.04],
      ],
      cls: "lo",
      bias: 0.02,
    });
  }

  // 2. 1 m tick marks and meter labels along the front apron
  for (const m of TRACK_TICKS) {
    const mx = m * ISO_UNIT;
    const isOrigin = m === 0;
    out.push({
      pts: [
        [mx, 6.7, TRACK_TOP_Z + 0.05],
        [mx, TRACK_HALF_D + 0.04, TRACK_TOP_Z + 0.05],
        [mx, TRACK_HALF_D + 0.04, TRACK_TOP_Z - 1.4],
      ],
      cls: isOrigin ? "hi" : "edge",
      bias: 0.05,
    });
    out.push(
      label(isOrigin ? "0m" : `${m > 0 ? "+" : ""}${m}`, [mx, 9.25, TRACK_TOP_Z + 0.08], [1, 0, 0], [0, -1, 0], 1.85, {
        anchor: "middle",
        cls: isOrigin ? "hi" : "edge",
        bias: 0.06,
      }),
    );
  }

  // 3. Endpoint stops (bumpers) aligned with ±TRACK_HALF_SPAN_M
  out.push({
    mesh: box(-TRACK_END_X - BUMPER_W, -6.5, TRACK_TOP_Z, -TRACK_END_X - 0.8, 6.5, BUMPER_TOP_Z),
    shade: true,
    inert: true,
    bias: 0.04,
  });
  out.push({
    mesh: box(-TRACK_END_X - 0.8, -4.8, TRACK_TOP_Z + 1.8, -TRACK_END_X, 4.8, BUMPER_TOP_Z - 1.8),
    shade: true,
    inert: true,
    bias: 0.05,
  });
  out.push({
    mesh: box(TRACK_END_X + 0.8, -6.5, TRACK_TOP_Z, TRACK_END_X + BUMPER_W, 6.5, BUMPER_TOP_Z),
    shade: true,
    inert: true,
    bias: 0.04,
  });
  out.push({
    mesh: box(TRACK_END_X, -4.8, TRACK_TOP_Z + 1.8, TRACK_END_X + 0.8, 4.8, BUMPER_TOP_Z - 1.8),
    shade: true,
    inert: true,
    bias: 0.05,
  });

  // 4. Two carts with cylinder wheels, mass labels, and velocity arrows
  const carts: Array<{ id: 1 | 2; xM: number; mass: number; vel: number }> = [
    { id: 1, xM: frameData.x1, mass: input.m1, vel: frameData.v1 },
    { id: 2, xM: frameData.x2, mass: input.m2, vel: frameData.v2 },
  ];

  let highestCartTopZ = CART_BASE_Z + 15;

  for (const cart of carts) {
    const part: PartId = cart.id === 1 ? "cart1" : "cart2";
    const isAccent = accentCart === cart.id;
    const cls = isAccent ? "accent" : "";
    const pickable = interactive === "detail";

    const cx = cart.xM * ISO_UNIT;
    const w = cartWidthMeters(cart.mass) * ISO_UNIT;
    const h = cartHeightMeters(cart.mass) * ISO_UNIT * 1.35;
    const topZ = CART_BASE_Z + h;
    if (topZ > highestCartTopZ) highestCartTopZ = topZ;

    // Rear & front cylinder wheels separated cleanly along y from the cart chassis
    const wheelXs = [cx - w * 0.28, cx + w * 0.28];
    for (const wx of wheelXs) {
      out.push({
        mesh: translate(WHEEL_PROTO, [wx, -CART_HALF_D - WHEEL_THICK, WHEEL_CZ]),
        smooth: true,
        part: pickable ? part : undefined,
        inert: !pickable,
        cls,
        bias: 0.08,
      });
      out.push({
        mesh: translate(WHEEL_PROTO, [wx, CART_HALF_D, WHEEL_CZ]),
        smooth: true,
        part: pickable ? part : undefined,
        inert: !pickable,
        cls,
        bias: 0.14,
      });
    }

    // Cart body box
    out.push({
      mesh: box(cx - w / 2, -CART_HALF_D, CART_BASE_Z, cx + w / 2, CART_HALF_D, topZ),
      shade: true,
      part: pickable ? part : undefined,
      inert: !pickable,
      cls,
      bias: 0.12,
    });

    // Subtle chassis trim line on front face
    out.push({
      pts: [
        [cx - w / 2 + 1.0, CART_HALF_D + 0.06, CART_BASE_Z + 2.2],
        [cx + w / 2 - 1.0, CART_HALF_D + 0.06, CART_BASE_Z + 2.2],
      ],
      cls: isAccent ? "accent" : "lo",
      bias: 0.15,
    });

    // Cart ID on top face and mass on front face
    out.push(
      label(`C${cart.id}`, [cx, 0.7, topZ + 0.12], [1, 0, 0], [0, -1, 0], 1.65, {
        anchor: "middle",
        cls: isAccent ? "accent" : "edge",
        bias: 0.16,
      }),
    );
    out.push(
      label(`${cart.mass.toFixed(1)}kg`, [cx, CART_HALF_D + 0.12, (CART_BASE_Z + topZ) / 2 - 0.5], [1, 0, 0], [0, 0, 1], 2.25, {
        anchor: "middle",
        cls: isAccent ? "accent" : "hi",
        bias: 0.16,
      }),
    );

    // Velocity arrow above each cart
    const arrowZ = topZ + 5.4;
    const arrow = computeVelocityArrowWorld(cx, cart.vel);
    if (arrow.hasArrow) {
      out.push({
        pts: [
          [arrow.startX, 0, arrowZ],
          [arrow.endX, 0, arrowZ],
        ],
        cls: isAccent ? "accent vel-shaft" : "hi vel-shaft",
        bias: 0.24,
      });
      const headMesh = translate(arrow.dir > 0 ? ARROW_HEAD_POS : ARROW_HEAD_NEG, [arrow.endX, 0, arrowZ]);
      out.push({
        mesh: headMesh,
        smooth: true,
        inert: true,
        cls: isAccent ? "solid" : "ink hi",
        bias: 0.25,
      });
    } else {
      out.push({
        mesh: translate(REST_DOT_PROTO, [cx, 0, arrowZ]),
        smooth: true,
        inert: true,
        cls: isAccent ? "solid" : "ink hi",
        bias: 0.24,
      });
    }

    out.push(
      label(`${formatSigned(cart.vel)} m/s`, [arrow.labelX, 0, arrowZ + 2.6], [1, 0, 0], [0, 0, 1], 2.2, {
        anchor: "middle",
        cls: isAccent ? "accent" : "hi",
        bias: 0.26,
      }),
    );
  }

  // 5. Brief impact spark at contact (visible at impact frame and for ~0.23 s after)
  if (hasCollided && impactX !== null && postFrames >= 0 && postFrames <= 14) {
    const ix = impactX * ISO_UNIT;
    const iz = highestCartTopZ + 1.4;
    out.push({
      pts: [
        [ix, 0, iz],
        [ix, 0, iz + 2.8],
      ],
      cls: "accent",
      bias: 0.3,
    });
    out.push({
      pts: [
        [ix - 1.6, 0, iz + 0.5],
        [ix - 3.4, 0, iz + 2.2],
      ],
      cls: "accent",
      bias: 0.3,
    });
    out.push({
      pts: [
        [ix + 1.6, 0, iz + 0.5],
        [ix + 3.4, 0, iz + 2.2],
      ],
      cls: "accent",
      bias: 0.3,
    });
  }

  return out;
}

export function Collisions({
  input: controlledInput,
  onInputChange,
  selectedCart: controlledSelected,
  onSelectCart,
  frameIndex: controlledFrameIndex,
  onFrameIndexChange,
  playing: controlledPlaying,
  onPlayingChange,
  onRunReady,
  onSnapshot,
  interactive = "detail",
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

  const [internalFrameIndex, setInternalFrameIndex] = useState(0);
  const rawFrameIndex = controlledFrameIndex ?? internalFrameIndex;
  const setFrameIndex = useCallback(
    (next: number) => {
      if (onFrameIndexChange) onFrameIndexChange(next);
      else setInternalFrameIndex(next);
    },
    [onFrameIndexChange],
  );

  const [internalPlaying, setInternalPlaying] = useState(false);
  const playing = controlledPlaying ?? internalPlaying;
  const setPlaying = useCallback(
    (next: boolean) => {
      if (onPlayingChange) onPlayingChange(next);
      else setInternalPlaying(next);
    },
    [onPlayingChange],
  );

  const [reducedMotion, setReducedMotion] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mq.matches);
    const onChange = () => setReducedMotion(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  // Pre-compute all frames synchronously whenever input changes (no rendering during precompute).
  const run = useMemo(() => precomputeCollisionRun(input), [input]);
  const lastFrameIndex = Math.max(0, run.frames.length - 1);
  const frameIndex = clamp(rawFrameIndex, 0, lastFrameIndex);
  const currentFrame: CollisionFrame = useMemo(
    () =>
      run.frames[frameIndex] ?? {
        t: 0,
        x1: INITIAL_CART1_POS_M,
        x2: INITIAL_CART2_POS_M,
        v1: input.v1,
        v2: input.v2,
        p1: input.m1 * input.v1,
        p2: input.m2 * input.v2,
        P: input.m1 * input.v1 + input.m2 * input.v2,
        KE1: 0.5 * input.m1 * input.v1 * input.v1,
        KE2: 0.5 * input.m2 * input.v2 * input.v2,
        KE: 0.5 * input.m1 * input.v1 * input.v1 + 0.5 * input.m2 * input.v2 * input.v2,
      },
    [frameIndex, input.m1, input.m2, input.v1, input.v2, run.frames],
  );

  const hasCollided = run.impactFrameIndex !== null && frameIndex >= run.impactFrameIndex;
  const postFrames = hasCollided && run.impactFrameIndex !== null ? frameIndex - run.impactFrameIndex : 0;
  const phase: SimPhase = playing
    ? "running"
    : frameIndex === 0
      ? "ready"
      : frameIndex >= lastFrameIndex
        ? "done"
        : "paused";

  const snapshot: CollisionSimSnapshot = useMemo(
    () => ({
      phase,
      hasCollided,
      t: currentFrame.t,
      frameIndex,
      x1: currentFrame.x1,
      x2: currentFrame.x2,
      v1: currentFrame.v1,
      v2: currentFrame.v2,
      measuredV1After: run.measuredV1After,
      measuredV2After: run.measuredV2After,
      reducedMotion,
    }),
    [currentFrame.t, currentFrame.v1, currentFrame.v2, currentFrame.x1, currentFrame.x2, frameIndex, hasCollided, phase, reducedMotion, run.measuredV1After, run.measuredV2After],
  );

  // Notify parent when precomputed run changes and reset uncontrolled playback.
  useEffect(() => {
    onRunReady?.(run);
    if (controlledFrameIndex === undefined) setInternalFrameIndex(0);
    if (controlledPlaying === undefined) setInternalPlaying(false);
  }, [controlledFrameIndex, controlledPlaying, onRunReady, run]);

  useEffect(() => {
    onSnapshot?.(snapshot);
  }, [onSnapshot, snapshot]);

  const stageRef = useRef<HTMLDivElement | null>(null);
  const painterRef = useRef<Painter | null>(null);
  const rafRef = useRef<number>(0);
  const frameIndexRef = useRef<number>(frameIndex);
  frameIndexRef.current = frameIndex;

  const [hoverCart, setHoverCart] = useState<1 | 2 | null>(null);
  const [focusedCart, setFocusedCart] = useState<1 | 2 | null>(null);

  const latestRef = useRef({
    input,
    selectedCart,
    hoverCart,
    focusedCart,
    interactive,
    setInput,
    selectCart,
    setFrameIndex,
    setPlaying,
  });
  latestRef.current = {
    input,
    selectedCart,
    hoverCart,
    focusedCart,
    interactive,
    setInput,
    selectCart,
    setFrameIndex,
    setPlaying,
  };

  // Real-time playback across precomputed frames; reduced motion jumps straight to the end.
  useEffect(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
    }
    if (!playing) return;

    if (reducedMotion) {
      latestRef.current.setFrameIndex(lastFrameIndex);
      latestRef.current.setPlaying(false);
      return;
    }

    const startIdx = frameIndexRef.current >= lastFrameIndex ? 0 : frameIndexRef.current;
    if (frameIndexRef.current >= lastFrameIndex) {
      latestRef.current.setFrameIndex(0);
    }

    let lastEmitted = startIdx;
    const startTime = performance.now();

    const tick = (now: number) => {
      const elapsedSec = Math.max(0, (now - startTime) / 1000);
      const nextIdx = Math.min(lastFrameIndex, startIdx + Math.floor(elapsedSec / run.dtSeconds));
      if (nextIdx !== lastEmitted) {
        lastEmitted = nextIdx;
        latestRef.current.setFrameIndex(nextIdx);
      }
      if (nextIdx < lastFrameIndex) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        rafRef.current = 0;
        latestRef.current.setPlaying(false);
      }
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = 0;
      }
    };
  }, [lastFrameIndex, playing, reducedMotion, run.dtSeconds]);

  // Mount Isometric SVG & pointer handler once on the host div.
  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;

    const b = bag();
    const root = stage.getRootNode();
    inject(root.nodeType === 9 || "host" in root ? (root as Document | ShadowRoot) : document);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 400 320");
    svg.setAttribute("aria-hidden", "true");
    stage.prepend(svg);

    const sc = scene(el("g", null, svg));
    painterRef.current = sc;

    let dragCart: 1 | 2 | null = null;
    let dragStartP: Vec2 | null = null;
    let dragStartVel = 0;
    let dragMoved = false;

    b.add(
      pointer(stage, {
        down: (p) => {
          if (latestRef.current.interactive !== "detail") return;
          const picked = sc.pick(p);
          if (picked === "cart1" || picked === "cart2") {
            const cart = picked === "cart1" ? 1 : 2;
            latestRef.current.selectCart(cart);
            dragCart = cart;
            dragStartP = p;
            dragMoved = false;
            dragStartVel = cart === 1 ? latestRef.current.input.v1 : latestRef.current.input.v2;
            setHoverCart(cart);
          }
        },
        move: (p) => {
          if (latestRef.current.interactive !== "detail") return;
          if (dragCart && dragStartP) {
            if (Math.hypot(p[0] - dragStartP[0], p[1] - dragStartP[1]) > 4) dragMoved = true;
            if (!dragMoved) return;
            const wxNow = unproject(COLLISION_CAMERA, p[0], p[1], CART_MID_Z)[0];
            const wxStart = unproject(COLLISION_CAMERA, dragStartP[0], dragStartP[1], CART_MID_Z)[0];
            const deltaVel = (wxNow - wxStart) / 14;
            const nextVel = clamp(
              roundToStep(dragStartVel + deltaVel, VELOCITY_STEP_MPS),
              MIN_VELOCITY_MPS,
              MAX_VELOCITY_MPS,
            );
            const cur = latestRef.current.input;
            const currentVel = dragCart === 1 ? cur.v1 : cur.v2;
            if (nextVel !== currentVel) {
              latestRef.current.setInput(dragCart === 1 ? { ...cur, v1: nextVel } : { ...cur, v2: nextVel });
            }
            return;
          }
          const picked = sc.pick(p);
          const nextHover: 1 | 2 | null = picked === "cart1" ? 1 : picked === "cart2" ? 2 : null;
          setHoverCart((prev) => {
            if (prev !== nextHover) {
              stage.style.cursor = nextHover ? "grab" : "";
            }
            return nextHover;
          });
        },
        up: () => {
          dragCart = null;
          dragStartP = null;
          dragMoved = false;
          if (latestRef.current.interactive === "detail") {
            stage.style.cursor = latestRef.current.hoverCart ? "grab" : "";
          }
        },
        leave: () => {
          dragCart = null;
          dragStartP = null;
          dragMoved = false;
          setHoverCart(null);
          if (latestRef.current.interactive === "detail") {
            stage.style.cursor = "";
          }
        },
      }),
    );

    b.add(() => {
      painterRef.current = null;
      svg.remove();
    });

    return () => b.dispose();
  }, []);

  // Re-render Isometric SVG whenever the active frame, input, or selection changes.
  useEffect(() => {
    const painter = painterRef.current;
    if (!painter) return;
    const accent = interactive === "detail" ? (hoverCart ?? focusedCart ?? selectedCart) : null;
    const items = buildCollisionsScene({
      input,
      frameData: currentFrame,
      hasCollided,
      impactX: run.impactX,
      postFrames,
      accentCart: accent,
      interactive,
    });
    painter.render(COLLISION_CAMERA, items);
  }, [currentFrame, focusedCart, hasCollided, hoverCart, input, interactive, postFrames, run.impactX, selectedCart]);

  const togglePlayPause = useCallback(() => {
    if (playing) {
      setPlaying(false);
    } else {
      if (reducedMotion) {
        setFrameIndex(lastFrameIndex);
        setPlaying(false);
        return;
      }
      if (frameIndex >= lastFrameIndex) {
        setFrameIndex(0);
      }
      setPlaying(true);
    }
  }, [frameIndex, lastFrameIndex, playing, reducedMotion, setFrameIndex, setPlaying]);

  const resetPlayback = useCallback(() => {
    setPlaying(false);
    setFrameIndex(0);
  }, [setFrameIndex, setPlaying]);

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

  const handleCartKeyDown = (cart: 1 | 2, e: React.KeyboardEvent<HTMLDivElement>) => {
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
      resetPlayback();
    }
  };

  const handleCardKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (interactive !== "card") return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      togglePlayPause();
    } else if (e.key === "r" || e.key === "R") {
      e.preventDefault();
      resetPlayback();
    }
  };

  const handleCardClick = () => {
    if (interactive !== "card") return;
    togglePlayPause();
  };

  const ariaLabel =
    interactive === "card"
      ? `1D elastic collision simulation: Cart 1 (${input.m1.toFixed(1)} kg at ${formatSigned(currentFrame.v1)} m/s) and Cart 2 (${input.m2.toFixed(1)} kg at ${formatSigned(currentFrame.v2)} m/s). Click or press Enter to play or replay.`
      : `1D collision track at t = ${currentFrame.t.toFixed(2)} s with Cart 1 (${input.m1.toFixed(1)} kg at ${formatSigned(currentFrame.v1)} m/s) and Cart 2 (${input.m2.toFixed(1)} kg at ${formatSigned(currentFrame.v2)} m/s), coefficient of restitution ${input.e.toFixed(2)}.`;

  return (
    <div
      ref={stageRef}
      data-testid="collisions-figure"
      data-iso="collisions"
      data-interactive={interactive}
      role={interactive === "card" ? "button" : "group"}
      tabIndex={interactive === "card" ? 0 : -1}
      aria-label={ariaLabel}
      onClick={handleCardClick}
      onKeyDown={handleCardKeyDown}
      className={`iso-studio-surface iso-figure-box w-full ${className ?? ""}`.trim()}
    >
      <span data-iso-live="" aria-live="polite">
        {hasCollided
          ? `After collision (t = ${currentFrame.t.toFixed(2)} s): Cart 1 ${formatSigned(currentFrame.v1)} m/s, Cart 2 ${formatSigned(currentFrame.v2)} m/s`
          : `t = ${currentFrame.t.toFixed(2)} s: Cart 1 ${formatSigned(currentFrame.v1)} m/s, Cart 2 ${formatSigned(currentFrame.v2)} m/s`}
      </span>

      {interactive === "detail" &&
        ([
          { id: 1 as const, mass: input.m1, vel: currentFrame.v1, inputVel: input.v1 },
          { id: 2 as const, mass: input.m2, vel: currentFrame.v2, inputVel: input.v2 },
        ] as const).map(({ id, mass, vel, inputVel }) => (
          <div
            key={id}
            className="sr-only"
            data-testid={`collision-cart-${id}`}
            data-selected={selectedCart === id ? "true" : "false"}
            role="slider"
            tabIndex={0}
            aria-label={`Cart ${id}. Press Left or Right arrows to adjust initial velocity, Up or Down arrows to adjust mass, Space or Enter to play or pause.`}
            aria-valuemin={MIN_VELOCITY_MPS}
            aria-valuemax={MAX_VELOCITY_MPS}
            aria-valuenow={inputVel}
            aria-valuetext={`Cart ${id}, mass ${mass.toFixed(1)} kg, velocity ${formatSigned(vel)} meters per second`}
            onFocus={() => {
              setFocusedCart(id);
              selectCart(id);
            }}
            onBlur={() => setFocusedCart((prev) => (prev === id ? null : prev))}
            onKeyDown={(e) => handleCartKeyDown(id, e)}
          />
        ))}
    </div>
  );
}
