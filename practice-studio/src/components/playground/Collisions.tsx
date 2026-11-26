"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { frame } from "@/lib/isometric/entity";
import { clamp, unproject, type Vec2 } from "@/lib/isometric/iso";
import { box, cylinder, frustum, rotateX, rotateZ, translate, zToX } from "@/lib/isometric/mesh";
import { label, scene, type Item, type Painter } from "@/lib/isometric/scene";
import { bag, el } from "@/lib/isometric/stage";
import { inject } from "@/lib/isometric/styles";
import {
  cartHeightMeters,
  cartWidthMeters,
  clampCartPosition,
  DEFAULT_COLLISION_INPUT,
  INITIAL_CART1_POS_M,
  INITIAL_CART2_POS_M,
  MASS_STEP_KG,
  MAX_MASS_KG,
  MAX_VELOCITY_MPS,
  MIN_MASS_KG,
  MIN_VELOCITY_MPS,
  normalizeCollisionPositions,
  POSITION_STEP_M,
  VELOCITY_STEP_MPS,
  type CollisionInput,
} from "@/lib/playground/collisions";
import {
  computeReleaseVelocityMps,
  computeVelocityAnnotationLayout,
  FLING_DEADZONE_MPS,
  formatSigned,
  ISO_UNIT,
  TRACK_END_X,
  TRACK_TICKS,
  type PointerTrackSample,
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
  onInputChange?: (next: CollisionInput, meta?: { autoPlay?: boolean }) => void;
  selectedCart?: 1 | 2;
  onSelectCart?: (cart: 1 | 2) => void;
  frameIndex?: number;
  onFrameIndexChange?: (frameIndex: number) => void;
  playing?: boolean;
  onPlayingChange?: (playing: boolean) => void;
  onRunReady?: (run: PrecomputedCollisionRun) => void;
  onSnapshot?: (snapshot: CollisionSimSnapshot) => void;
  /** `"card"` shows a drag-to-launch + click/Enter-to-play figure for the grid; `"detail"` adds cart selection and keyboard controls. */
  interactive?: "card" | "detail";
  className?: string;
};

type PartId = "cart1" | "cart2";
type DragPreview = { cart: 1 | 2; xM: number; liveV: number };

const roundToStep = (v: number, step: number) => Math.round(v / step) * step;
const VIEWBOX_W = 400;
const VIEWBOX_H_CARD = 320;
const VIEWBOX_H_DETAIL = 240;

const FIT_POINTS: [number, number, number][] = [
  [-TRACK_END_X - TRACK_PAD_X, -TRACK_HALF_D, 0],
  [TRACK_END_X + TRACK_PAD_X, TRACK_HALF_D, 0],
  [-TRACK_END_X - TRACK_PAD_X, -TRACK_HALF_D, 44],
  [TRACK_END_X + TRACK_PAD_X, TRACK_HALF_D, 44],
];

const COLLISION_CARD_CAMERA = frame({
  az: 8,
  k: 0.5,
  zoom: 1.04,
  at: [200, 160],
  fit: FIT_POINTS,
});

const COLLISION_DETAIL_CAMERA = frame({
  az: 8,
  k: 0.5,
  zoom: 1.04,
  at: [200, 122],
  fit: FIT_POINTS,
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
  dragPreview: DragPreview | null;
}): Item[] {
  const { input, frameData, hasCollided, impactX, postFrames, accentCart, dragPreview } = params;
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

  // 4. Two carts with cylinder wheels, mass labels, and non-overlapping velocity annotations
  const startX1 = input.x1 ?? INITIAL_CART1_POS_M;
  const startX2 = input.x2 ?? INITIAL_CART2_POS_M;
  const x1M = dragPreview ? (dragPreview.cart === 1 ? dragPreview.xM : startX1) : frameData.x1;
  const x2M = dragPreview ? (dragPreview.cart === 2 ? dragPreview.xM : startX2) : frameData.x2;
  const v1Mps = dragPreview ? (dragPreview.cart === 1 ? dragPreview.liveV : input.v1) : frameData.v1;
  const v2Mps = dragPreview ? (dragPreview.cart === 2 ? dragPreview.liveV : input.v2) : frameData.v2;

  const label1 = dragPreview?.cart === 1 ? `v ≈ ${formatSigned(v1Mps)} m/s` : `${formatSigned(v1Mps)} m/s`;
  const label2 = dragPreview?.cart === 2 ? `v ≈ ${formatSigned(v2Mps)} m/s` : `${formatSigned(v2Mps)} m/s`;

  const w1 = cartWidthMeters(input.m1) * ISO_UNIT;
  const h1 = cartHeightMeters(input.m1) * ISO_UNIT * 1.35;
  const topZ1 = CART_BASE_Z + h1;
  const w2 = cartWidthMeters(input.m2) * ISO_UNIT;
  const h2 = cartHeightMeters(input.m2) * ISO_UNIT * 1.35;
  const topZ2 = CART_BASE_Z + h2;

  const cx1 = x1M * ISO_UNIT;
  const cx2 = x2M * ISO_UNIT;
  const annotations = computeVelocityAnnotationLayout({
    cx1,
    topZ1,
    v1: v1Mps,
    label1,
    cx2,
    topZ2,
    v2: v2Mps,
    label2,
  });

  const carts: Array<{
    id: 1 | 2;
    cx: number;
    w: number;
    topZ: number;
    mass: number;
    velText: string;
    ann: (typeof annotations)[number];
  }> = [
    { id: 1, cx: cx1, w: w1, topZ: topZ1, mass: input.m1, velText: label1, ann: annotations[0] },
    { id: 2, cx: cx2, w: w2, topZ: topZ2, mass: input.m2, velText: label2, ann: annotations[1] },
  ];

  const highestCartTopZ = Math.max(topZ1, topZ2);

  for (const cart of carts) {
    const part: PartId = cart.id === 1 ? "cart1" : "cart2";
    const isAccent = dragPreview ? dragPreview.cart === cart.id : accentCart === cart.id;
    const cls = isAccent ? "accent" : "";

    const { cx, w, topZ, ann } = cart;

    // Rear & front cylinder wheels separated cleanly along y from the cart chassis
    const wheelXs = [cx - w * 0.28, cx + w * 0.28];
    for (const wx of wheelXs) {
      out.push({
        mesh: translate(WHEEL_PROTO, [wx, -CART_HALF_D - WHEEL_THICK, WHEEL_CZ]),
        smooth: true,
        part,
        inert: false,
        cls,
        bias: 0.08,
      });
      out.push({
        mesh: translate(WHEEL_PROTO, [wx, CART_HALF_D, WHEEL_CZ]),
        smooth: true,
        part,
        inert: false,
        cls,
        bias: 0.14,
      });
    }

    // Cart body box
    out.push({
      mesh: box(cx - w / 2, -CART_HALF_D, CART_BASE_Z, cx + w / 2, CART_HALF_D, topZ),
      shade: true,
      part,
      inert: false,
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

    if (ann.stacked) {
      out.push({
        pts: [
          [cx, 0, topZ + 1.0],
          [cx, 0, ann.arrowZ - 1.4],
        ],
        cls: isAccent ? "accent dash" : "lo dash",
        bias: 0.22,
      });
    }

    // Velocity arrow above each cart
    const { arrow, arrowZ, labelZ } = ann;
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
      label(cart.velText, [arrow.labelX, 0, labelZ], [1, 0, 0], [0, 0, 1], 2.2, {
        anchor: "middle",
        cls: isAccent ? "accent" : "hi",
        bias: 0.26,
      }),
    );
  }

  // 5. Brief impact spark at contact (visible at impact frame and for ~0.23 s after)
  if (!dragPreview && hasCollided && impactX !== null && postFrames >= 0 && postFrames <= 14) {
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
    (next: CollisionInput, meta?: { autoPlay?: boolean }) => {
      if (onInputChange) onInputChange(next, meta);
      else setInternalInput(normalizeCollisionPositions(next));
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
  const reducedMotionRef = useRef(false);
  reducedMotionRef.current = reducedMotion;
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mq.matches);
    reducedMotionRef.current = mq.matches;
    const onChange = () => {
      setReducedMotion(mq.matches);
      reducedMotionRef.current = mq.matches;
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  // Pre-compute all frames synchronously whenever input changes (no rendering during precompute).
  const run = useMemo(() => precomputeCollisionRun(input), [input]);
  const lastFrameIndex = Math.max(0, run.frames.length - 1);
  const frameIndex = clamp(rawFrameIndex, 0, lastFrameIndex);
  const x1Start = input.x1 ?? INITIAL_CART1_POS_M;
  const x2Start = input.x2 ?? INITIAL_CART2_POS_M;
  const currentFrame: CollisionFrame = useMemo(
    () =>
      run.frames[frameIndex] ?? {
        t: 0,
        x1: x1Start,
        x2: x2Start,
        v1: input.v1,
        v2: input.v2,
        p1: input.m1 * input.v1,
        p2: input.m2 * input.v2,
        P: input.m1 * input.v1 + input.m2 * input.v2,
        KE1: 0.5 * input.m1 * input.v1 * input.v1,
        KE2: 0.5 * input.m2 * input.v2 * input.v2,
        KE: 0.5 * input.m1 * input.v1 * input.v1 + 0.5 * input.m2 * input.v2 * input.v2,
      },
    [frameIndex, input.m1, input.m2, input.v1, input.v2, run.frames, x1Start, x2Start],
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

  const pendingAutoPlayRef = useRef(false);

  // Notify parent when precomputed run changes and handle playback reset or drag-release auto-play.
  useEffect(() => {
    onRunReady?.(run);
    if (pendingAutoPlayRef.current) {
      pendingAutoPlayRef.current = false;
      const isReduced = reducedMotionRef.current;
      const targetEnd = Math.max(0, run.frames.length - 1);
      if (controlledFrameIndex === undefined) {
        setInternalFrameIndex(isReduced ? targetEnd : 0);
      } else if (isReduced) {
        onFrameIndexChange?.(targetEnd);
      }
      if (controlledPlaying === undefined) {
        setInternalPlaying(!isReduced);
      } else {
        onPlayingChange?.(!isReduced);
      }
      return;
    }
    if (controlledFrameIndex === undefined) setInternalFrameIndex(0);
    if (controlledPlaying === undefined) setInternalPlaying(false);
  }, [controlledFrameIndex, controlledPlaying, onFrameIndexChange, onPlayingChange, onRunReady, run]);

  useEffect(() => {
    onSnapshot?.(snapshot);
  }, [onSnapshot, snapshot]);

  const stageRef = useRef<HTMLDivElement | null>(null);
  const painterRef = useRef<Painter | null>(null);
  const rafRef = useRef<number>(0);
  const frameIndexRef = useRef<number>(frameIndex);
  frameIndexRef.current = frameIndex;
  const suppressNextClickRef = useRef(false);

  const [hoverCart, setHoverCart] = useState<1 | 2 | null>(null);
  const [focusedCart, setFocusedCart] = useState<1 | 2 | null>(null);
  const [dragPreview, setDragPreview] = useState<DragPreview | null>(null);

  const activeCamera = interactive === "detail" ? COLLISION_DETAIL_CAMERA : COLLISION_CARD_CAMERA;
  const activeViewBoxH = interactive === "detail" ? VIEWBOX_H_DETAIL : VIEWBOX_H_CARD;

  const latestRef = useRef({
    input,
    currentFrame,
    lastFrameIndex,
    selectedCart,
    hoverCart,
    focusedCart,
    interactive,
    activeCamera,
    activeViewBoxH,
    setInput,
    selectCart,
    setFrameIndex,
    setPlaying,
  });
  latestRef.current = {
    input,
    currentFrame,
    lastFrameIndex,
    selectedCart,
    hoverCart,
    focusedCart,
    interactive,
    activeCamera,
    activeViewBoxH,
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

  // Mount Isometric SVG & drag-to-launch pointer handlers once on the host div.
  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;

    const b = bag();
    const root = stage.getRootNode();
    inject(root.nodeType === 9 || "host" in root ? (root as Document | ShadowRoot) : document);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${VIEWBOX_W} ${latestRef.current.activeViewBoxH}`);
    svg.setAttribute("aria-hidden", "true");
    stage.prepend(svg);

    const sc = scene(el("g", null, svg));
    painterRef.current = sc;

    let dragCart: 1 | 2 | null = null;
    let dragStartP: Vec2 | null = null;
    let dragStartWx = 0;
    let dragGrabXM = 0;
    let dragMoved = false;
    let dragSamples: PointerTrackSample[] = [];
    let dragIdleTimer = 0;
    let clickClearTimer = 0;

    const toViewBox = (e: PointerEvent): Vec2 => {
      const r = stage.getBoundingClientRect();
      const w = r.width || 1;
      const h = r.height || 1;
      return [
        ((e.clientX - r.left) / w) * VIEWBOX_W,
        ((e.clientY - r.top) / h) * latestRef.current.activeViewBoxH,
      ];
    };

    const stopIdleTimer = () => {
      if (dragIdleTimer) {
        window.clearTimeout(dragIdleTimer);
        dragIdleTimer = 0;
      }
    };

    const detachDragWindow = () => {
      window.removeEventListener("pointermove", onWindowMove);
      window.removeEventListener("pointerup", onWindowUp);
      window.removeEventListener("pointercancel", onWindowCancel);
      stopIdleTimer();
      stage.style.touchAction = "";
    };

    const scheduleIdleDecay = (cart: 1 | 2, clampedXM: number) => {
      stopIdleTimer();
      dragIdleTimer = window.setTimeout(() => {
        if (dragCart === cart && dragMoved) {
          setDragPreview((prev) => (prev && prev.cart === cart ? { cart, xM: clampedXM, liveV: 0 } : prev));
        }
      }, 90);
    };

    const onWindowMove = (e: PointerEvent) => {
      if (!dragCart || !dragStartP) return;
      const p = toViewBox(e);
      if (!dragMoved && Math.hypot(p[0] - dragStartP[0], p[1] - dragStartP[1]) > 3) {
        dragMoved = true;
        latestRef.current.setPlaying(false);
        if (latestRef.current.interactive === "card") {
          suppressNextClickRef.current = true;
        }
      }
      if (!dragMoved) return;

      const cam = latestRef.current.activeCamera;
      const wxNow = unproject(cam, p[0], p[1], CART_MID_Z)[0];
      const rawTrackXM = dragGrabXM + (wxNow - dragStartWx) / ISO_UNIT;

      const cur = latestRef.current.input;
      const otherXM = dragCart === 1 ? (cur.x2 ?? INITIAL_CART2_POS_M) : (cur.x1 ?? INITIAL_CART1_POS_M);
      const clampedXM = roundToStep(
        clampCartPosition(dragCart, rawTrackXM, cur.m1, cur.m2, otherXM),
        POSITION_STEP_M,
      );

      const nowMs = performance.now();
      dragSamples.push({ xM: rawTrackXM, tMs: nowMs });
      if (dragSamples.length > 24) {
        dragSamples = dragSamples.slice(-24);
      }

      const liveV = computeReleaseVelocityMps(dragSamples, nowMs);
      setDragPreview({ cart: dragCart, xM: clampedXM, liveV });
      scheduleIdleDecay(dragCart, clampedXM);
    };

    const finishDrag = (e: PointerEvent | null, cancelled: boolean) => {
      const cart = dragCart;
      const wasMoved = dragMoved;
      const grabXM = dragGrabXM;
      const startWx = dragStartWx;
      const samples = dragSamples;

      dragCart = null;
      dragStartP = null;
      dragMoved = false;
      dragSamples = [];
      detachDragWindow();
      setDragPreview(null);

      if (wasMoved && latestRef.current.interactive === "card") {
        window.clearTimeout(clickClearTimer);
        clickClearTimer = window.setTimeout(() => {
          suppressNextClickRef.current = false;
        }, 0);
      }

      if (!cart || !wasMoved || cancelled || !e) {
        stage.style.cursor = latestRef.current.hoverCart ? "grab" : "";
        return;
      }

      const cam = latestRef.current.activeCamera;
      const p = toViewBox(e);
      const wxNow = unproject(cam, p[0], p[1], CART_MID_Z)[0];
      const rawTrackXM = grabXM + (wxNow - startWx) / ISO_UNIT;
      const nowMs = performance.now();

      const lastSample = samples[samples.length - 1];
      if (!lastSample || Math.abs(rawTrackXM - lastSample.xM) > 1e-4) {
        samples.push({ xM: rawTrackXM, tMs: nowMs });
      }

      const releaseV = computeReleaseVelocityMps(samples, nowMs);
      const cur = latestRef.current.input;
      const otherXM = cart === 1 ? (cur.x2 ?? INITIAL_CART2_POS_M) : (cur.x1 ?? INITIAL_CART1_POS_M);
      const finalXM = roundToStep(
        clampCartPosition(cart, rawTrackXM, cur.m1, cur.m2, otherXM),
        POSITION_STEP_M,
      );

      const nextInput: CollisionInput =
        cart === 1
          ? { ...cur, x1: finalXM, v1: releaseV }
          : { ...cur, x2: finalXM, v2: releaseV };

      const autoPlay = Math.abs(releaseV) >= FLING_DEADZONE_MPS;
      const sameAsCurrent =
        Math.abs((cur.x1 ?? INITIAL_CART1_POS_M) - (nextInput.x1 ?? INITIAL_CART1_POS_M)) < 1e-9 &&
        Math.abs((cur.x2 ?? INITIAL_CART2_POS_M) - (nextInput.x2 ?? INITIAL_CART2_POS_M)) < 1e-9 &&
        Math.abs(cur.v1 - nextInput.v1) < 1e-9 &&
        Math.abs(cur.v2 - nextInput.v2) < 1e-9;

      if (autoPlay) {
        pendingAutoPlayRef.current = true;
        latestRef.current.setInput(nextInput, { autoPlay: true });
        if (sameAsCurrent) {
          pendingAutoPlayRef.current = false;
          const isReduced = reducedMotionRef.current;
          latestRef.current.setFrameIndex(isReduced ? latestRef.current.lastFrameIndex : 0);
          latestRef.current.setPlaying(!isReduced);
        }
      } else {
        pendingAutoPlayRef.current = false;
        latestRef.current.setInput(nextInput, { autoPlay: false });
        if (sameAsCurrent) {
          latestRef.current.setPlaying(false);
          latestRef.current.setFrameIndex(0);
        }
      }

      stage.style.cursor = latestRef.current.hoverCart ? "grab" : "";
    };

    const onWindowUp = (e: PointerEvent) => finishDrag(e, false);
    const onWindowCancel = () => finishDrag(null, true);

    const onStageDown = (e: PointerEvent) => {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      if (e.pointerType !== "mouse") stage.releasePointerCapture?.(e.pointerId);
      const p = toViewBox(e);
      const picked = sc.pick(p);
      if (picked === "cart1" || picked === "cart2") {
        const cart = picked === "cart1" ? 1 : 2;
        if (latestRef.current.interactive === "detail") {
          latestRef.current.selectCart(cart);
        }
        const cam = latestRef.current.activeCamera;
        dragCart = cart;
        dragStartP = p;
        dragStartWx = unproject(cam, p[0], p[1], CART_MID_Z)[0];
        dragGrabXM = cart === 1 ? latestRef.current.currentFrame.x1 : latestRef.current.currentFrame.x2;
        dragMoved = false;
        dragSamples = [{ xM: dragGrabXM, tMs: performance.now() }];
        setHoverCart(cart);
        stage.style.cursor = "grabbing";
        stage.style.touchAction = "none";
        window.addEventListener("pointermove", onWindowMove);
        window.addEventListener("pointerup", onWindowUp);
        window.addEventListener("pointercancel", onWindowCancel);
      }
    };

    const onStageMove = (e: PointerEvent) => {
      if (dragCart) return;
      const p = toViewBox(e);
      const picked = sc.pick(p);
      const nextHover: 1 | 2 | null = picked === "cart1" ? 1 : picked === "cart2" ? 2 : null;
      setHoverCart((prev) => {
        if (prev !== nextHover) {
          stage.style.cursor = nextHover ? "grab" : latestRef.current.interactive === "card" ? "pointer" : "";
        }
        return nextHover;
      });
    };

    const onStageLeave = () => {
      if (dragCart) return;
      setHoverCart(null);
      stage.style.cursor = "";
    };

    stage.addEventListener("pointerdown", onStageDown);
    stage.addEventListener("pointermove", onStageMove);
    stage.addEventListener("pointerleave", onStageLeave);

    b.add(() => {
      window.clearTimeout(clickClearTimer);
      detachDragWindow();
      stage.removeEventListener("pointerdown", onStageDown);
      stage.removeEventListener("pointermove", onStageMove);
      stage.removeEventListener("pointerleave", onStageLeave);
      painterRef.current = null;
      svg.remove();
    });

    return () => b.dispose();
  }, []);

  // Re-render Isometric SVG whenever the active frame, input, drag preview, or selection changes.
  useEffect(() => {
    const painter = painterRef.current;
    if (!painter) return;
    const svgEl = stageRef.current?.querySelector("svg");
    if (svgEl) {
      svgEl.setAttribute("viewBox", `0 0 ${VIEWBOX_W} ${activeViewBoxH}`);
    }
    const accent = dragPreview
      ? dragPreview.cart
      : interactive === "detail"
        ? (hoverCart ?? focusedCart ?? selectedCart)
        : hoverCart;
    const items = buildCollisionsScene({
      input,
      frameData: currentFrame,
      hasCollided,
      impactX: run.impactX,
      postFrames,
      accentCart: accent,
      dragPreview,
    });
    painter.render(activeCamera, items);
  }, [
    activeCamera,
    activeViewBoxH,
    currentFrame,
    dragPreview,
    focusedCart,
    hasCollided,
    hoverCart,
    input,
    interactive,
    postFrames,
    run.impactX,
    selectedCart,
  ]);

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
      const raw = (cart === 1 ? input.v1 : input.v2) + delta;
      const nextVal = Number(
        clamp(roundToStep(raw, VELOCITY_STEP_MPS), MIN_VELOCITY_MPS, MAX_VELOCITY_MPS).toFixed(1),
      );
      setInput(cart === 1 ? { ...input, v1: nextVal } : { ...input, v2: nextVal });
    },
    [input, setInput],
  );

  const adjustCartMass = useCallback(
    (cart: 1 | 2, delta: number) => {
      const nextVal = Number(
        clamp(roundToStep((cart === 1 ? input.m1 : input.m2) + delta, MASS_STEP_KG), MIN_MASS_KG, MAX_MASS_KG).toFixed(
          1,
        ),
      );
      setInput(normalizeCollisionPositions(cart === 1 ? { ...input, m1: nextVal } : { ...input, m2: nextVal }));
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
    if (suppressNextClickRef.current) {
      suppressNextClickRef.current = false;
      return;
    }
    togglePlayPause();
  };

  const ariaLabel =
    interactive === "card"
      ? `1D collision simulation: Cart 1 (${input.m1.toFixed(1)} kg at ${formatSigned(currentFrame.v1)} m/s) and Cart 2 (${input.m2.toFixed(1)} kg at ${formatSigned(currentFrame.v2)} m/s). Drag a cart to launch it, or click or press Enter to play or replay.`
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
        {dragPreview
          ? `Dragging Cart ${dragPreview.cart}: position ${formatSigned(dragPreview.xM, 2)} m, velocity approximately ${formatSigned(dragPreview.liveV)} m/s`
          : hasCollided
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
