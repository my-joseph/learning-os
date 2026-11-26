import {
  MAX_VELOCITY_MPS,
  MIN_VELOCITY_MPS,
  TRACK_HALF_SPAN_M,
  VELOCITY_STEP_MPS,
} from "./collisions";

export const TRACK_TICKS = [-3, -2, -1, 0, 1, 2, 3] as const;
export const ISO_UNIT = 18; // 1 m = 18 isometric world units (matches Lever)
export const TRACK_END_X = TRACK_HALF_SPAN_M * ISO_UNIT;

export const FLING_WINDOW_MS = 80;
export const FLING_DEADZONE_MPS = 0.05;

export type PointerTrackSample = {
  /** Track-aligned x position in meters. */
  xM: number;
  /** Monotonic timestamp in milliseconds. */
  tMs: number;
};

/**
 * Converts recent pointer samples along the track into a cart release velocity (m/s),
 * using the last ~80 ms of pointer motion, clamping to [-3, +3] m/s, rounding to 0.1,
 * and returning 0 when |v| < 0.05 m/s or the pointer paused before release.
 */
export function computeReleaseVelocityMps(
  samples: readonly PointerTrackSample[],
  nowMs?: number,
): number {
  if (samples.length < 2) return 0;

  const newest = samples[samples.length - 1];
  const refTime = nowMs ?? newest.tMs;
  if (refTime - newest.tMs > FLING_WINDOW_MS) return 0;

  const cutoff = refTime - FLING_WINDOW_MS;
  let anchorIdx = samples.findIndex((s) => s.tMs >= cutoff);
  if (anchorIdx < 0) return 0;
  if (anchorIdx >= samples.length - 1 && anchorIdx > 0) {
    // Only one sample fell inside the window; pair with the previous sample if recent enough.
    if (newest.tMs - samples[anchorIdx - 1].tMs <= FLING_WINDOW_MS * 2) {
      anchorIdx -= 1;
    } else {
      return 0;
    }
  }

  const anchor = samples[anchorIdx];
  const dtMs = newest.tMs - anchor.tMs;
  if (dtMs <= 1) return 0;

  const rawV = (newest.xM - anchor.xM) / (dtMs / 1000);
  if (!Number.isFinite(rawV) || Math.abs(rawV) < FLING_DEADZONE_MPS) return 0;

  const clamped = Math.max(MIN_VELOCITY_MPS, Math.min(MAX_VELOCITY_MPS, rawV));
  const rounded = Math.round(clamped / VELOCITY_STEP_MPS) * VELOCITY_STEP_MPS;
  return Math.abs(rounded) < FLING_DEADZONE_MPS ? 0 : Number(rounded.toFixed(1));
}

export type VelocityArrowWorld = {
  hasArrow: boolean;
  dir: -1 | 1;
  startX: number;
  endX: number;
  tipX: number;
  labelX: number;
};

/**
 * Computes world-space x coordinates for a cart's velocity arrow above its center.
 */
export function computeVelocityArrowWorld(centerX: number, velocityMps: number): VelocityArrowWorld {
  const speed = Math.abs(velocityMps);
  if (speed < 0.025) {
    return {
      hasArrow: false,
      dir: 1,
      startX: centerX,
      endX: centerX,
      tipX: centerX,
      labelX: centerX,
    };
  }

  const dir: -1 | 1 = velocityMps >= 0 ? 1 : -1;
  const shaftLen = 7 + Math.min(3.0, speed) * 3.2;
  const startX = centerX - dir * (shaftLen * 0.45);
  const endX = startX + dir * shaftLen;
  const tipX = endX + dir * 3.0;

  return {
    hasArrow: true,
    dir,
    startX,
    endX,
    tipX,
    labelX: (startX + tipX) / 2,
  };
}

export type VelocityAnnotationPlacement = {
  arrow: VelocityArrowWorld;
  arrowZ: number;
  labelZ: number;
  stacked: boolean;
};

const LABEL_CHAR_WIDTH_WORLD = 2.2 * 0.72;
const ANNOTATION_PAD_X = 2.5;
const LABEL_BASE_OFFSET_Z = 5.4;
const LABEL_ABOVE_ARROW_Z = 2.6;
const STACK_CLEARANCE_Z = 4.8;

function annotationSpanX(arrow: VelocityArrowWorld, labelText: string): [number, number] {
  const halfLabelW = (labelText.length * LABEL_CHAR_WIDTH_WORLD) / 2;
  const minArrowX = arrow.hasArrow ? Math.min(arrow.startX, arrow.tipX) : arrow.labelX - 1.5;
  const maxArrowX = arrow.hasArrow ? Math.max(arrow.startX, arrow.tipX) : arrow.labelX + 1.5;
  return [
    Math.min(minArrowX, arrow.labelX - halfLabelW),
    Math.max(maxArrowX, arrow.labelX + halfLabelW),
  ];
}

/**
 * Places both carts' velocity arrows and labels in world z so they never overlap
 * horizontally when carts touch or pass close together.
 */
export function computeVelocityAnnotationLayout(params: {
  cx1: number;
  topZ1: number;
  v1: number;
  label1: string;
  cx2: number;
  topZ2: number;
  v2: number;
  label2: string;
}): [VelocityAnnotationPlacement, VelocityAnnotationPlacement] {
  const arrow1 = computeVelocityArrowWorld(params.cx1, params.v1);
  const arrow2 = computeVelocityArrowWorld(params.cx2, params.v2);

  const arrowZ1 = params.topZ1 + LABEL_BASE_OFFSET_Z;
  const labelZ1 = arrowZ1 + LABEL_ABOVE_ARROW_Z;

  const baseArrowZ2 = params.topZ2 + LABEL_BASE_OFFSET_Z;
  const [min1, max1] = annotationSpanX(arrow1, params.label1);
  const [min2, max2] = annotationSpanX(arrow2, params.label2);
  const horizOverlap = max1 + ANNOTATION_PAD_X > min2 && max2 + ANNOTATION_PAD_X > min1;

  const stacked = horizOverlap && baseArrowZ2 < labelZ1 + STACK_CLEARANCE_Z;
  const arrowZ2 = stacked ? labelZ1 + STACK_CLEARANCE_Z : baseArrowZ2;
  const labelZ2 = arrowZ2 + LABEL_ABOVE_ARROW_Z;

  return [
    { arrow: arrow1, arrowZ: arrowZ1, labelZ: labelZ1, stacked: false },
    { arrow: arrow2, arrowZ: arrowZ2, labelZ: labelZ2, stacked },
  ];
}

export function formatSigned(value: number, digits = 1): string {
  const rounded = Math.abs(value) < 0.5 * 10 ** -digits ? 0 : value;
  const sign = rounded > 0 ? "+" : "";
  return `${sign}${rounded.toFixed(digits)}`;
}
