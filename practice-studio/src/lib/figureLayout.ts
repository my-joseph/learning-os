export interface PointLabelPlacement {
  x: number;
  y: number;
  width: number;
  height: number;
  align: "left" | "center" | "right";
}

export interface RectBox {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

export interface SvgSegment {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

/** Estimate pill width in SVG pixels from a LaTeX/plain label string. */
export function estimateLabelPillWidth(label: string): number {
  const stripped = label
    .replace(/\$/g, "")
    .replace(/\\(?:text|mathrm|mathbf|sqrt|frac|overline|bar)\b/g, "")
    .replace(/\\[a-zA-Z]+/g, "X")
    .replace(/[{}]/g, "");
  const charCount = Math.max(1, stripped.trim().length);
  return Math.min(140, Math.max(36, Math.round(charCount * 7.2 + 14)));
}

/**
 * Place a Cartesian point label pill relative to its SVG coordinate `(sx, sy)` and
 * nudge it away from the x-axis / y-axis tick zones so it never overlaps axis numbers.
 */
export function placePointLabel(params: {
  sx: number;
  sy: number;
  label: string;
  position?: string;
  axisX: number;
  axisY: number;
  showY: boolean;
  svgWidth: number;
  svgHeight: number;
  padding: number;
}): PointLabelPlacement {
  const {
    sx,
    sy,
    label,
    position = "top-right",
    axisX,
    axisY,
    showY,
    svgWidth,
    svgHeight,
    padding,
  } = params;

  const width = estimateLabelPillWidth(label);
  const height = 22;

  let align: "left" | "center" | "right" = "left";
  let left: number;
  if (position.includes("left")) {
    align = "right";
    left = sx - 8 - width;
  } else if (position.includes("right")) {
    align = "left";
    left = sx + 8;
  } else {
    align = "center";
    left = sx - width / 2;
  }

  let top: number;
  if (position.includes("top")) {
    top = sy - 7 - height;
  } else if (position.includes("bottom")) {
    top = sy + 7;
  } else {
    top = sy - height / 2;
  }

  // Nudge away from x-axis line and its tick labels ([axisY - 4, axisY + 18]).
  const xAxisLeft = padding - 10;
  const xAxisRight = svgWidth - padding + 12;
  const overlapsXBand =
    left + width > xAxisLeft &&
    left < xAxisRight &&
    top < axisY + 18 &&
    top + height > axisY - 4;
  if (overlapsXBand) {
    if (sy <= axisY + 4) {
      top = Math.min(sy - 7, axisY - 6) - height;
    } else {
      top = Math.max(sy + 7, axisY + 19);
    }
  }

  // Nudge away from y-axis line and its tick labels ([axisX - 24, axisX + 4]).
  if (showY) {
    const yAxisTop = padding - 12;
    const yAxisBottom = svgHeight - padding + 10;
    const overlapsYBand =
      top + height > yAxisTop &&
      top < yAxisBottom &&
      left < axisX + 4 &&
      left + width > axisX - 24;
    if (overlapsYBand) {
      if (sx >= axisX - 4) {
        left = Math.max(sx + 8, axisX + 6);
        align = "left";
      } else {
        left = Math.min(sx - 8, axisX - 24) - width;
        align = "right";
      }
    }
  }

  return { x: left, y: top, width, height, align };
}

/** Shortest Euclidean distance from point `(px, py)` to segment `(x1, y1)-(x2, y2)`. */
export function pointToSegmentDistance(
  px: number,
  py: number,
  seg: SvgSegment
): number {
  const dx = seg.x2 - seg.x1;
  const dy = seg.y2 - seg.y1;
  const lenSq = dx * dx + dy * dy;
  if (lenSq <= 1e-9) {
    return Math.hypot(px - seg.x1, py - seg.y1);
  }
  const t = Math.max(0, Math.min(1, ((px - seg.x1) * dx + (py - seg.y1) * dy) / lenSq));
  const projX = seg.x1 + t * dx;
  const projY = seg.y1 + t * dy;
  return Math.hypot(px - projX, py - projY);
}

/** Check if two axis-aligned boxes come within `margin` pixels of each other. */
export function boxesCollide(a: RectBox, b: RectBox, margin = 10): boolean {
  return (
    a.right >= b.left - margin &&
    a.left <= b.right + margin &&
    a.bottom >= b.top - margin &&
    a.top <= b.bottom + margin
  );
}

/** Determine whether a tick label box should be skipped due to dashed lines or point label pills. */
export function shouldSkipTickLabel(params: {
  labelBox: RectBox;
  dashedSegments: readonly SvgSegment[];
  pointLabelBoxes: readonly RectBox[];
  axis: "x" | "y" | "origin";
  tickCoord: number;
  margin?: number;
}): boolean {
  const {
    labelBox,
    dashedSegments,
    pointLabelBoxes,
    axis,
    tickCoord,
    margin = 10,
  } = params;

  const cx = (labelBox.left + labelBox.right) / 2;
  const cy = (labelBox.top + labelBox.bottom) / 2;

  for (const seg of dashedSegments) {
    if (pointToSegmentDistance(cx, cy, seg) <= margin) {
      return true;
    }
    if (
      axis === "x" &&
      Math.abs(seg.x1 - seg.x2) <= 1.5 &&
      Math.abs(tickCoord - seg.x1) <= margin &&
      Math.max(seg.y1, seg.y2) >= labelBox.top - 16 &&
      Math.min(seg.y1, seg.y2) <= labelBox.bottom + 4
    ) {
      return true;
    }
    if (
      axis === "y" &&
      Math.abs(seg.y1 - seg.y2) <= 1.5 &&
      Math.abs(tickCoord - seg.y1) <= margin &&
      Math.max(seg.x1, seg.x2) >= labelBox.left - 4 &&
      Math.min(seg.x1, seg.x2) <= labelBox.right + 16
    ) {
      return true;
    }
  }

  for (const pillBox of pointLabelBoxes) {
    if (boxesCollide(labelBox, pillBox, margin)) {
      return true;
    }
  }

  return false;
}
