"use client";

import React from "react";
import { VisualSpec, VisualElement } from "@/types/drill";

interface VisualRendererProps {
  visual: VisualSpec;
  className?: string;
}

export const VisualRenderer: React.FC<VisualRendererProps> = ({
  visual,
  className = "",
}) => {
  if (!visual || !visual.elements || visual.elements.length === 0) return null;

  const { width = 320, height = 200 } = visual.viewBox || {};

  return (
    <div className={`flex justify-center items-center my-3 p-3 bg-slate-50 dark:bg-[#0e121b] rounded-xl border border-slate-200 dark:border-[#232a3d] ${className}`}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full max-w-[360px] h-auto select-none overflow-visible"
        style={{ maxHeight: "240px" }}
      >
        {visual.elements.map((el, idx) => (
          <RenderElement key={idx} element={el} />
        ))}
      </svg>
    </div>
  );
};

const RenderElement: React.FC<{ element: VisualElement }> = ({ element }) => {
  switch (element.type) {
    case "polygon": {
      if (!element.points || element.points.length < 2) return null;
      const pointsStr = element.points.map((p) => `${p[0]},${p[1]}`).join(" ");
      return (
        <g>
          <polygon
            points={pointsStr}
            stroke={element.stroke || "#6366f1"}
            strokeWidth={element.strokeWidth || 2.5}
            fill={element.fill || "rgba(99, 102, 241, 0.1)"}
            strokeLinejoin="round"
          />
          {element.rightAngleAt && renderRightAngle(element.rightAngleAt, element.points)}
        </g>
      );
    }

    case "line": {
      if (!element.points || element.points.length < 2) return null;
      const [start, end] = element.points;
      return (
        <line
          x1={start[0]}
          y1={start[1]}
          x2={end[0]}
          y2={end[1]}
          stroke={element.stroke || "#64748b"}
          strokeWidth={element.strokeWidth || 2}
          strokeDasharray={element.strokeDasharray}
        />
      );
    }

    case "circle": {
      const [cx, cy] = element.center || [100, 100];
      const r = element.radius || 40;
      return (
        <circle
          cx={cx}
          cy={cy}
          r={r}
          stroke={element.stroke || "#0284c7"}
          strokeWidth={element.strokeWidth || 2.5}
          fill={element.fill || "rgba(56, 189, 248, 0.1)"}
        />
      );
    }

    case "dimension-label": {
      if (!element.start || !element.end) return null;
      const [x1, y1] = element.start;
      const [x2, y2] = element.end;
      const midX = (x1 + x2) / 2;
      const midY = (y1 + y2) / 2;
      const offset = element.offset ?? 14;

      let textX = midX;
      let textY = midY;
      let textAnchor: "middle" | "start" | "end" = "middle";

      const pos = element.position || "bottom";
      if (pos === "bottom") {
        textY += offset;
      } else if (pos === "top") {
        textY -= offset - 4;
      } else if (pos === "left") {
        textX -= offset;
        textAnchor = "end";
      } else if (pos === "right") {
        textX += offset;
        textAnchor = "start";
      } else if (pos === "hypotenuse") {
        const dx = x2 - x1;
        const dy = y2 - y1;
        const len = Math.sqrt(dx * dx + dy * dy) || 1;
        textX += (-dy / len) * offset;
        textY += (dx / len) * offset;
      }

      return (
        <text
          x={textX}
          y={textY}
          textAnchor={textAnchor}
          dominantBaseline="central"
          className={`text-xs font-mono font-bold ${
            element.highlight
              ? "fill-amber-600 dark:fill-amber-400 font-extrabold"
              : "fill-slate-800 dark:fill-slate-200"
          }`}
          style={{ fontSize: "12px" }}
        >
          {element.label}
        </text>
      );
    }

    case "cylinder": {
      const [cx, cy] = element.center || [150, 100];
      const rx = element.radiusX || 60;
      const ry = element.radiusY || 18;
      const h = element.height || 100;
      const topY = cy - h / 2;
      const bottomY = cy + h / 2;

      return (
        <g stroke={element.stroke || "#0284c7"} strokeWidth={element.strokeWidth || 2}>
          <path
            d={`M ${cx - rx} ${topY} L ${cx - rx} ${bottomY} A ${rx} ${ry} 0 0 0 ${cx + rx} ${bottomY} L ${cx + rx} ${topY}`}
            fill={element.fill || "rgba(56, 189, 248, 0.08)"}
          />
          <path
            d={`M ${cx - rx} ${bottomY} A ${rx} ${ry} 0 0 1 ${cx + rx} ${bottomY}`}
            fill="none"
            strokeDasharray="4 4"
            stroke="#64748b"
          />
          <ellipse cx={cx} cy={topY} rx={rx} ry={ry} fill={element.fill || "rgba(56, 189, 248, 0.14)"} />
        </g>
      );
    }

    default:
      return null;
  }
};

function renderRightAngle(vertex: [number, number], points: [number, number][]) {
  const [vx, vy] = vertex;
  const size = 12;
  const otherPoints = points.filter((p) => p[0] !== vx || p[1] !== vy);
  if (otherPoints.length < 2) return null;

  const [p1, p2] = otherPoints;
  const d1 = [Math.sign(p1[0] - vx), Math.sign(p1[1] - vy)];
  const d2 = [Math.sign(p2[0] - vx), Math.sign(p2[1] - vy)];

  const c1 = [vx + d1[0] * size, vy + d1[1] * size];
  const c2 = [c1[0] + d2[0] * size, c1[1] + d2[1] * size];
  const c3 = [vx + d2[0] * size, vy + d2[1] * size];

  return (
    <polyline
      points={`${c1[0]},${c1[1]} ${c2[0]},${c2[1]} ${c3[0]},${c3[1]}`}
      stroke="#64748b"
      strokeWidth={1.5}
      fill="none"
    />
  );
}
