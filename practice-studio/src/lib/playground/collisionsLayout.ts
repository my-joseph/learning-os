import { cartHeightMeters, cartWidthMeters, TRACK_HALF_SPAN_M } from "./collisions";

export const SVG_WIDTH = 400;
export const SVG_HEIGHT = 210;
export const SVG_VIEWBOX = `0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`;

export const TRACK_LEFT_X = 34;
export const TRACK_RIGHT_X = 366;
export const TRACK_WIDTH = TRACK_RIGHT_X - TRACK_LEFT_X;
export const TRACK_Y = 148;
export const TRACK_TICKS = [-3, -2, -1, 0, 1, 2, 3] as const;

export const WHEEL_RADIUS = 4.5;
export const CART_CORNER_RX = 6;

const BUMPER_WIDTH = 6;
const BUMPER_HEIGHT = 30;

export function meterToSvgX(xMeters: number): number {
  const ratio = (xMeters + TRACK_HALF_SPAN_M) / (2 * TRACK_HALF_SPAN_M);
  return TRACK_LEFT_X + ratio * TRACK_WIDTH;
}

export function metersToSvgWidth(wMeters: number): number {
  return (wMeters / (2 * TRACK_HALF_SPAN_M)) * TRACK_WIDTH;
}

export type CartSvgGeometry = {
  x: number;
  y: number;
  width: number;
  height: number;
  rx: number;
  centerX: number;
  innerX: number;
  innerY: number;
  innerWidth: number;
  innerHeight: number;
  innerRx: number;
  wheelLeftX: number;
  wheelRightX: number;
  wheelY: number;
  wheelR: number;
  massTextY: number;
  idTextY: number;
  arrowY: number;
};

export function computeCartSvgBox(xMeters: number, massKg: number): CartSvgGeometry {
  const w = metersToSvgWidth(cartWidthMeters(massKg));
  const h = metersToSvgWidth(cartHeightMeters(massKg));
  const centerX = meterToSvgX(xMeters);
  const wheelY = TRACK_Y - WHEEL_RADIUS;
  const bottomY = TRACK_Y - WHEEL_RADIUS * 1.35;
  const y = bottomY - h;
  const x = centerX - w / 2;

  return {
    x,
    y,
    width: w,
    height: h,
    rx: CART_CORNER_RX,
    centerX,
    innerX: x + 3,
    innerY: y + 3,
    innerWidth: Math.max(8, w - 6),
    innerHeight: Math.max(8, h - 6),
    innerRx: Math.max(2, CART_CORNER_RX - 2),
    wheelLeftX: x + w * 0.24,
    wheelRightX: x + w * 0.76,
    wheelY,
    wheelR: WHEEL_RADIUS,
    massTextY: y + h * 0.67,
    idTextY: y + h * 0.31,
    arrowY: y - 18,
  };
}

export type VelocityArrowGeometry = {
  hasArrow: boolean;
  startX: number;
  endX: number;
  y: number;
  headPoints: string;
  labelX: number;
  labelY: number;
};

export function computeVelocityArrow(
  centerX: number,
  arrowY: number,
  velocityMps: number,
): VelocityArrowGeometry {
  const speed = Math.abs(velocityMps);
  const labelY = arrowY - 10;
  if (speed < 0.025) {
    return {
      hasArrow: false,
      startX: centerX,
      endX: centerX,
      y: arrowY,
      headPoints: "",
      labelX: centerX,
      labelY,
    };
  }

  const dir = velocityMps >= 0 ? 1 : -1;
  const len = 12 + Math.min(3.5, speed) * 14;
  const startX = centerX - dir * (len * 0.35);
  const endX = startX + dir * len;
  const tipX = endX + dir * 6;
  const headPoints = `${tipX},${arrowY} ${endX},${arrowY - 4} ${endX},${arrowY + 4}`;

  return {
    hasArrow: true,
    startX,
    endX,
    y: arrowY,
    headPoints,
    labelX: (startX + tipX) / 2,
    labelY,
  };
}

export function computeTrackBumpers() {
  return {
    left: {
      x: TRACK_LEFT_X - BUMPER_WIDTH,
      y: TRACK_Y - BUMPER_HEIGHT,
      width: BUMPER_WIDTH,
      height: BUMPER_HEIGHT,
      rx: 2,
    },
    right: {
      x: TRACK_RIGHT_X,
      y: TRACK_Y - BUMPER_HEIGHT,
      width: BUMPER_WIDTH,
      height: BUMPER_HEIGHT,
      rx: 2,
    },
    tickY1: TRACK_Y,
    tickY2: TRACK_Y + 6,
    tickLabelY: TRACK_Y + 19,
    trackTopY: TRACK_Y - 1,
  };
}

export function formatSigned(value: number, digits = 1): string {
  const rounded = Math.abs(value) < 0.5 * 10 ** -digits ? 0 : value;
  const sign = rounded > 0 ? "+" : "";
  return `${sign}${rounded.toFixed(digits)}`;
}
