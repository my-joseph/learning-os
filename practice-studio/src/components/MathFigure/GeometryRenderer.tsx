"use client";

import React, { useMemo } from "react";
import {
  Geometry2DSpec,
  FigureTheme,
  GeometryRightAngleMarker,
  GeometryAngleArcMarker,
} from "@/types/figure";
import { FormattedText } from "../FormattedText";

const THEME_STYLES: Record<
  FigureTheme,
  {
    primary: string;
    stroke: string;
    fill: string;
    accent: string;
    marker: string;
  }
> = {
  indigo: {
    primary: "stroke-indigo-600 dark:stroke-indigo-400",
    stroke: "#6366f1",
    fill: "rgba(99, 102, 241, 0.09)",
    accent: "text-indigo-600 dark:text-indigo-400",
    marker: "#4f46e5",
  },
  blue: {
    primary: "stroke-sky-600 dark:stroke-sky-400",
    stroke: "#0284c7",
    fill: "rgba(14, 165, 233, 0.09)",
    accent: "text-sky-600 dark:text-sky-400",
    marker: "#0369a1",
  },
  emerald: {
    primary: "stroke-emerald-600 dark:stroke-emerald-400",
    stroke: "#059669",
    fill: "rgba(16, 185, 129, 0.09)",
    accent: "text-emerald-600 dark:text-emerald-400",
    marker: "#047857",
  },
  amber: {
    primary: "stroke-amber-600 dark:stroke-amber-400",
    stroke: "#d97706",
    fill: "rgba(245, 158, 11, 0.09)",
    accent: "text-amber-600 dark:text-amber-400",
    marker: "#b45309",
  },
  rose: {
    primary: "stroke-rose-600 dark:stroke-rose-400",
    stroke: "#e11d48",
    fill: "rgba(244, 63, 94, 0.09)",
    accent: "text-rose-600 dark:text-rose-400",
    marker: "#be123c",
  },
  purple: {
    primary: "stroke-purple-600 dark:stroke-purple-400",
    stroke: "#7c3aed",
    fill: "rgba(139, 92, 246, 0.09)",
    accent: "text-purple-600 dark:text-purple-400",
    marker: "#6d28d9",
  },
};

interface GeometryRendererProps {
  spec: Geometry2DSpec;
}

export const GeometryRenderer: React.FC<GeometryRendererProps> = ({ spec }) => {
  const theme = spec.theme || "indigo";
  const colors = THEME_STYLES[theme] || THEME_STYLES.indigo;

  // Viewport setup
  const svgWidth = 380;
  const svgHeight = 240;
  const padding = 42; // generous padding for external labels

  // 1. Calculate World Bounding Box
  const { minX, minY, scale, offsetX, offsetY } = useMemo(() => {
    const rawCoords: [number, number][] = Object.values(spec.points || {});

    // Include circle and ellipse bounds
    (spec.shapes || []).forEach((shape) => {
      if (shape.type === "circle" && spec.points[shape.center]) {
        const [cx, cy] = spec.points[shape.center];
        const r = shape.radius;
        rawCoords.push([cx - r, cy - r], [cx + r, cy + r]);
      } else if (shape.type === "ellipse" && spec.points[shape.center]) {
        const [cx, cy] = spec.points[shape.center];
        const rx = shape.radiusX;
        const ry = shape.radiusY;
        rawCoords.push([cx - rx, cy - ry], [cx + rx, cy + ry]);
      }
    });

    if (rawCoords.length === 0) {
      return { minX: 0, minY: 0, scale: 1, offsetX: 0, offsetY: 0 };
    }

    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;

    rawCoords.forEach(([x, y]) => {
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    });

    const worldW = Math.max(maxX - minX, 1e-4);
    const worldH = Math.max(maxY - minY, 1e-4);

    const availW = svgWidth - padding * 2;
    const availH = svgHeight - padding * 2;

    const scale = Math.min(availW / worldW, availH / worldH);

    // Center geometry in SVG canvas
    const drawW = worldW * scale;
    const drawH = worldH * scale;

    const offsetX = padding + (availW - drawW) / 2;
    const offsetY = padding + (availH - drawH) / 2;

    return { minX, minY, scale, offsetX, offsetY };
  }, [spec.points, spec.shapes, svgWidth, svgHeight, padding]);

  // Transform world coordinates (y-up) to SVG coordinates (y-down)
  const toSvg = (coord: [number, number]): [number, number] => {
    const [wx, wy] = coord;
    const sx = offsetX + (wx - minX) * scale;
    const sy = svgHeight - (offsetY + (wy - minY) * scale);
    return [Math.round(sx * 10) / 10, Math.round(sy * 10) / 10];
  };

  const getPt = (key: string): [number, number] | null => {
    if (!spec.points[key]) return null;
    return toSvg(spec.points[key]);
  };

  return (
    <div className="relative w-full flex flex-col items-center select-none overflow-hidden">
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="w-full max-w-[420px] h-auto overflow-visible"
        style={{ maxHeight: "280px" }}
      >
        <defs>
          <filter id="badge-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="1" stdDeviation="1.5" floodOpacity="0.1" />
          </filter>
        </defs>

        {/* 1. Shapes (Polygons, Segments, Circles) */}
        {(spec.shapes || []).map((shape, idx) => {
          if (shape.type === "polygon") {
            const svgPoints = shape.vertices
              .map((v) => getPt(v))
              .filter(Boolean) as [number, number][];
            if (svgPoints.length < 2) return null;
            const ptsStr = svgPoints.map(([x, y]) => `${x},${y}`).join(" ");

            return (
              <polygon
                key={`poly-${idx}`}
                points={ptsStr}
                stroke={shape.stroke || colors.stroke}
                strokeWidth={shape.strokeWidth || 2.2}
                fill={shape.fill ? colors.fill : "none"}
                strokeLinejoin="round"
                strokeDasharray={shape.strokeDasharray}
                className="transition-colors"
              />
            );
          }

          if (shape.type === "segment") {
            const p1 = getPt(shape.from);
            const p2 = getPt(shape.to);
            if (!p1 || !p2) return null;

            return (
              <line
                key={`seg-${idx}`}
                x1={p1[0]}
                y1={p1[1]}
                x2={p2[0]}
                y2={p2[1]}
                stroke={shape.stroke || colors.stroke}
                strokeWidth={shape.strokeWidth || 2}
                strokeDasharray={shape.strokeDasharray}
              />
            );
          }

          if (shape.type === "circle") {
            const center = getPt(shape.center);
            if (!center) return null;
            const rSvg = shape.radius * scale;

            return (
              <circle
                key={`circ-${idx}`}
                cx={center[0]}
                cy={center[1]}
                r={rSvg}
                stroke={shape.stroke || colors.stroke}
                strokeWidth={shape.strokeWidth || 2}
                fill={shape.fill ? colors.fill : "none"}
                strokeDasharray={shape.strokeDasharray}
              />
            );
          }

          if (shape.type === "ellipse") {
            const center = getPt(shape.center);
            if (!center) return null;
            const rxSvg = shape.radiusX * scale;
            const rySvg = shape.radiusY * scale;

            return (
              <ellipse
                key={`ell-${idx}`}
                cx={center[0]}
                cy={center[1]}
                rx={rxSvg}
                ry={rySvg}
                stroke={shape.stroke || colors.stroke}
                strokeWidth={shape.strokeWidth || 2}
                fill={shape.fill ? colors.fill : "none"}
                strokeDasharray={shape.strokeDasharray}
              />
            );
          }

          return null;
        })}

        {/* 2. Geometric Markers (Right Angle, Angle Arcs, Ticks) */}
        {(spec.markers || []).map((marker, idx) => {
          if (marker.type === "right_angle") {
            return (
              <RightAngleMarkerSvg
                key={`m-ra-${idx}`}
                marker={marker}
                getPt={getPt}
                strokeColor={colors.stroke}
              />
            );
          }

          if (marker.type === "angle_arc") {
            return (
              <AngleArcMarkerSvg
                key={`m-arc-${idx}`}
                marker={marker}
                getPt={getPt}
                strokeColor={colors.stroke}
              />
            );
          }

          return null;
        })}

        {/* 3. Point Vertices Dots */}
        {Object.entries(spec.points || {}).map(([key]) => {
          const pt = getPt(key);
          if (!pt) return null;

          return (
            <circle
              key={`dot-${key}`}
              cx={pt[0]}
              cy={pt[1]}
              r={3.5}
              className="fill-slate-900 dark:fill-white stroke-white dark:stroke-slate-900"
              strokeWidth={1.5}
            />
          );
        })}

        {/* 4. Labels (Point Names, Dimension Annotations, KaTeX) */}
        {(spec.labels || []).map((label, idx) => {
          if (label.type === "point") {
            const pt = getPt(label.point);
            if (!pt) return null;
            const textStr = label.text || label.point;

            const [ox, oy] = getPointLabelOffset(label.position || "auto");

            return (
              <foreignObject
                key={`lbl-pt-${idx}`}
                x={pt[0] + ox - 35}
                y={pt[1] + oy - 15}
                width={70}
                height={30}
                className="overflow-visible pointer-events-none"
              >
                <div className="w-full h-full flex items-center justify-center">
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                    <FormattedText text={textStr.startsWith("$") ? textStr : `$${textStr}$`} />
                  </span>
                </div>
              </foreignObject>
            );
          }

          if (label.type === "segment") {
            const p1 = getPt(label.p1);
            const p2 = getPt(label.p2);
            if (!p1 || !p2) return null;

            const midX = (p1[0] + p2[0]) / 2;
            const midY = (p1[1] + p2[1]) / 2;
            const dx = p2[0] - p1[0];
            const dy = p2[1] - p1[1];
            const len = Math.sqrt(dx * dx + dy * dy) || 1;

            const offsetDist = label.offset ?? 16;
            let targetX = midX;
            let targetY = midY;

            const side = label.side || "auto";

            if (side === "bottom") {
              targetY += offsetDist;
            } else if (side === "top") {
              targetY -= offsetDist;
            } else if (side === "left") {
              targetX -= offsetDist;
            } else if (side === "right") {
              targetX += offsetDist;
            } else {
              // Normal vector perpendicular to segment
              const nx = -dy / len;
              const ny = dx / len;
              targetX += nx * offsetDist;
              targetY += ny * offsetDist;
            }

            const isHighlight = label.highlight;
            const formatted = label.text.startsWith("$") ? label.text : `$${label.text}$`;

            return (
              <foreignObject
                key={`lbl-seg-${idx}`}
                x={targetX - 55}
                y={targetY - 14}
                width={110}
                height={28}
                className="overflow-visible pointer-events-none"
              >
                <div className="w-full h-full flex items-center justify-center">
                  <div
                    className={`px-1.5 py-0.5 rounded text-xs font-semibold backdrop-blur-[2px] ${
                      isHighlight
                        ? "bg-amber-100/90 dark:bg-amber-950/80 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-700/60 font-bold shadow-sm"
                        : "bg-white/70 dark:bg-slate-900/70 text-slate-800 dark:text-slate-200"
                    }`}
                  >
                    <FormattedText text={formatted} />
                  </div>
                </div>
              </foreignObject>
            );
          }

          return null;
        })}
      </svg>
    </div>
  );
};

// Sub-component: Right Angle Marker (Calculates exact geometry square)
const RightAngleMarkerSvg: React.FC<{
  marker: GeometryRightAngleMarker;
  getPt: (key: string) => [number, number] | null;
  strokeColor: string;
}> = ({ marker, getPt, strokeColor }) => {
  const v = getPt(marker.vertex);
  const a = getPt(marker.arm1);
  const b = getPt(marker.arm2);
  if (!v || !a || !b) return null;

  const v1 = [a[0] - v[0], a[1] - v[1]];
  const v2 = [b[0] - v[0], b[1] - v[1]];

  const len1 = Math.hypot(v1[0], v1[1]) || 1;
  const len2 = Math.hypot(v2[0], v2[1]) || 1;

  const u1 = [v1[0] / len1, v1[1] / len1];
  const u2 = [v2[0] / len2, v2[1] / len2];

  const s = marker.size || 12; // 12px marker size

  const p1 = [v[0] + u1[0] * s, v[1] + u1[1] * s];
  const corner = [v[0] + (u1[0] + u2[0]) * s, v[1] + (u1[1] + u2[1]) * s];
  const p2 = [v[0] + u2[0] * s, v[1] + u2[1] * s];

  return (
    <polyline
      points={`${p1[0]},${p1[1]} ${corner[0]},${corner[1]} ${p2[0]},${p2[1]}`}
      fill="none"
      stroke={strokeColor}
      strokeWidth={1.6}
      strokeLinecap="square"
    />
  );
};

// Sub-component: Angle Arc Marker
const AngleArcMarkerSvg: React.FC<{
  marker: GeometryAngleArcMarker;
  getPt: (key: string) => [number, number] | null;
  strokeColor: string;
}> = ({ marker, getPt, strokeColor }) => {
  const v = getPt(marker.vertex);
  const a = getPt(marker.arm1);
  const b = getPt(marker.arm2);
  if (!v || !a || !b) return null;

  const r = marker.radius || 24;

  const angleA = Math.atan2(a[1] - v[1], a[0] - v[0]);
  const angleB = Math.atan2(b[1] - v[1], b[0] - v[0]);

  // Directed angle sweep
  let sweep = angleB - angleA;
  while (sweep < -Math.PI) sweep += 2 * Math.PI;
  while (sweep > Math.PI) sweep -= 2 * Math.PI;

  const pStart = [v[0] + Math.cos(angleA) * r, v[1] + Math.sin(angleA) * r];
  const pEnd = [
    v[0] + Math.cos(angleA + sweep) * r,
    v[1] + Math.sin(angleA + sweep) * r,
  ];

  const midAngle = angleA + sweep / 2;
  const lblDist = r + 14;
  const lblX = v[0] + Math.cos(midAngle) * lblDist;
  const lblY = v[1] + Math.sin(midAngle) * lblDist;

  const sweepFlag = sweep > 0 ? 1 : 0;

  return (
    <g>
      <path
        d={`M ${pStart[0]} ${pStart[1]} A ${r} ${r} 0 0 ${sweepFlag} ${pEnd[0]} ${pEnd[1]}`}
        fill="none"
        stroke={strokeColor}
        strokeWidth={1.6}
      />
      {marker.label && (
        <foreignObject
          x={lblX - 35}
          y={lblY - 14}
          width={70}
          height={28}
          className="overflow-visible pointer-events-none"
        >
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-[11px] font-mono font-bold text-amber-600 dark:text-amber-400">
              <FormattedText
                text={marker.label.startsWith("$") ? marker.label : `$${marker.label}$`}
              />
            </span>
          </div>
        </foreignObject>
      )}
    </g>
  );
};

function getPointLabelOffset(position: string): [number, number] {
  switch (position) {
    case "top":
      return [0, -18];
    case "bottom":
      return [0, 18];
    case "left":
      return [-18, 0];
    case "right":
      return [18, 0];
    case "top-left":
      return [-14, -14];
    case "top-right":
      return [14, -14];
    case "bottom-left":
      return [-14, 14];
    case "bottom-right":
      return [14, 14];
    default:
      return [0, -16];
  }
}
