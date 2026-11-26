import { TRACK_HALF_SPAN_M } from "./collisions";

export const TRACK_TICKS = [-3, -2, -1, 0, 1, 2, 3] as const;
export const ISO_UNIT = 18; // 1 m = 18 isometric world units (matches Lever)
export const TRACK_END_X = TRACK_HALF_SPAN_M * ISO_UNIT;

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

export function formatSigned(value: number, digits = 1): string {
  const rounded = Math.abs(value) < 0.5 * 10 ** -digits ? 0 : value;
  const sign = rounded > 0 ? "+" : "";
  return `${sign}${rounded.toFixed(digits)}`;
}
