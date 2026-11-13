"use client";

import React, { useState } from "react";
import { VisualSpec, VisualElement } from "@/types/drill";
import { Sparkles, Image as ImageIcon } from "lucide-react";
import { InteractivePythagoras2D } from "./InteractivePythagoras2D";
import { InteractiveTrapezoid2D } from "./InteractiveTrapezoid2D";
import { InteractiveCircle2D } from "./InteractiveCircle2D";
import { Interactive3DCylinder } from "./Interactive3DCylinder";

interface VisualRendererProps {
  visual: VisualSpec;
  className?: string;
}

export const VisualRenderer: React.FC<VisualRendererProps> = ({
  visual,
  className = "",
}) => {
  const [showInteractive, setShowInteractive] = useState(false);

  if (!visual || !visual.elements || visual.elements.length === 0) return null;

  const { width = 320, height = 200 } = visual.viewBox || {};
  const hasInteractive = Boolean(visual.interactive);

  const renderInteractivePlayground = () => {
    if (!visual.interactive) return null;
    const { mode, initialParams } = visual.interactive;

    switch (mode) {
      case "pythagoras-drag":
        return (
          <InteractivePythagoras2D
            initialA={initialParams.a ?? 3}
            initialB={initialParams.b ?? 4}
          />
        );
      case "trapezoid-drag":
        return (
          <InteractiveTrapezoid2D
            initialB1={initialParams.b1 ?? 6}
            initialB2={initialParams.b2 ?? 10}
            initialH={initialParams.h ?? 6}
          />
        );
      case "circle-radius-drag":
        return (
          <InteractiveCircle2D
            initialR={initialParams.r ?? 4}
          />
        );
      case "cylinder-slider":
        return (
          <Interactive3DCylinder
            initialRadius={initialParams.r ?? 3}
            initialHeight={initialParams.h ?? 8}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className={`flex flex-col items-center my-3 p-3 bg-slate-50 dark:bg-[#0e121b] rounded-xl border border-slate-200 dark:border-[#232a3d] transition-all ${className}`}>
      {hasInteractive && (
        <div className="w-full flex justify-end mb-2">
          <button
            type="button"
            onClick={() => setShowInteractive(!showInteractive)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg border transition-colors bg-white dark:bg-[#151b28] text-slate-700 dark:text-slate-300 border-slate-200 dark:border-[#28324a] hover:border-indigo-400 dark:hover:border-indigo-500 hover:text-indigo-600 dark:hover:text-indigo-400"
          >
            {showInteractive ? (
              <>
                <ImageIcon className="w-3.5 h-3.5" />
                <span>Standard Diagram</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
                <span>Interactive Playground</span>
              </>
            )}
          </button>
        </div>
      )}

      {showInteractive && hasInteractive ? (
        <div className="w-full">{renderInteractivePlayground()}</div>
      ) : (
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full max-w-[360px] h-auto select-none overflow-visible"
          style={{ maxHeight: "240px" }}
        >
          {visual.elements.map((el, idx) => (
            <RenderElement key={idx} element={el} />
          ))}
        </svg>
      )}
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
            strokeDasharray={element.strokeDasharray}
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

    case "point": {
      const [cx, cy] = element.coord || [0, 0];
      const color = element.color || "#2563eb";
      return (
        <g>
          <circle cx={cx} cy={cy} r={4.5} fill={color} stroke="#ffffff" strokeWidth={1.5} />
          {element.label && (
            <text
              x={cx + 8}
              y={cy - 8}
              className="fill-slate-800 dark:fill-slate-200 font-sans font-semibold text-xs select-none"
              style={{ fontSize: "11px" }}
            >
              {element.label}
            </text>
          )}
        </g>
      );
    }

    case "angle-arc": {
      const [cx, cy] = element.center || [0, 0];
      const r = element.radius || 25;
      const startDeg = element.startAngle || 0;
      const endDeg = element.endAngle || 90;

      const r1 = (startDeg * Math.PI) / 180;
      const r2 = (endDeg * Math.PI) / 180;
      const x1 = cx + r * Math.cos(r1);
      const y1 = cy - r * Math.sin(r1);
      const x2 = cx + r * Math.cos(r2);
      const y2 = cy - r * Math.sin(r2);

      const diff = ((endDeg - startDeg) % 360 + 360) % 360;
      const largeArc = diff > 180 ? 1 : 0;

      const midRad = ((startDeg + endDeg) / 2 * Math.PI) / 180;
      const lblX = cx + (r + 14) * Math.cos(midRad);
      const lblY = cy - (r + 14) * Math.sin(midRad);

      return (
        <g>
          <path
            d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 0 ${x2} ${y2}`}
            fill="none"
            stroke="#d97706"
            strokeWidth={1.8}
          />
          {element.label && (
            <text
              x={lblX}
              y={lblY}
              textAnchor="middle"
              dominantBaseline="central"
              className="fill-amber-600 dark:fill-amber-400 font-mono font-bold"
              style={{ fontSize: "11px" }}
            >
              {element.label}
            </text>
          )}
        </g>
      );
    }

    case "text": {
      const x = element.x || 0;
      const y = element.y || 0;
      const fs = element.fontSize || 12;
      return (
        <text
          x={x}
          y={y}
          style={{ fontSize: `${fs}px` }}
          fill={element.color || "#1e293b"}
          className="font-sans font-semibold select-none"
        >
          {element.label}
        </text>
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
          style={{ fontSize: "11px" }}
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
