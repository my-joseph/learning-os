"use client";

import React, { useMemo } from "react";
import { CartesianGraphSpec, FigureTheme, CartesianPlot } from "@/types/figure";
import { FormattedText } from "../FormattedText";

const THEME_STYLES: Record<
  FigureTheme,
  {
    primary: string;
    stroke: string;
    fill: string;
    accent: string;
    grid: string;
    axis: string;
  }
> = {
  indigo: {
    primary: "#6366f1",
    stroke: "#4f46e5",
    fill: "rgba(99, 102, 241, 0.12)",
    accent: "#4338ca",
    grid: "#e2e8f0",
    axis: "#475569",
  },
  blue: {
    primary: "#0284c7",
    stroke: "#0369a1",
    fill: "rgba(14, 165, 233, 0.12)",
    accent: "#0284c7",
    grid: "#e2e8f0",
    axis: "#475569",
  },
  emerald: {
    primary: "#059669",
    stroke: "#047857",
    fill: "rgba(16, 185, 129, 0.12)",
    accent: "#0d9488",
    grid: "#e2e8f0",
    axis: "#475569",
  },
  amber: {
    primary: "#d97706",
    stroke: "#b45309",
    fill: "rgba(245, 158, 11, 0.12)",
    accent: "#ea580c",
    grid: "#e2e8f0",
    axis: "#475569",
  },
  rose: {
    primary: "#e11d48",
    stroke: "#be123c",
    fill: "rgba(244, 63, 94, 0.12)",
    accent: "#9f1239",
    grid: "#e2e8f0",
    axis: "#475569",
  },
  purple: {
    primary: "#7c3aed",
    stroke: "#6d28d9",
    fill: "rgba(139, 92, 246, 0.12)",
    accent: "#5b21b6",
    grid: "#e2e8f0",
    axis: "#475569",
  },
};

interface CartesianRendererProps {
  spec: CartesianGraphSpec;
}

export const CartesianRenderer: React.FC<CartesianRendererProps> = ({ spec }) => {
  const theme = spec.theme || "blue";
  const colors = THEME_STYLES[theme] || THEME_STYLES.blue;

  const svgWidth = 380;
  const svgHeight = 260;
  const padding = 36;

  const [xMin, xMax] = spec.xRange || [-5, 5];
  const [yMin, yMax] = spec.yRange || [-5, 5];

  const widthWorld = Math.max(xMax - xMin, 1e-4);
  const heightWorld = Math.max(yMax - yMin, 1e-4);

  // Auto-adaptive step calculation to prevent label collision / squishing
  const effectiveXStep = useMemo(() => {
    if (spec.xStep && widthWorld / spec.xStep <= 9) {
      return spec.xStep;
    }
    return calculateSmartStep(xMin, xMax, 6);
  }, [spec.xStep, xMin, xMax, widthWorld]);

  const effectiveYStep = useMemo(() => {
    if (spec.yStep && heightWorld / spec.yStep <= 8) {
      return spec.yStep;
    }
    return calculateSmartStep(yMin, yMax, 6);
  }, [spec.yStep, yMin, yMax, heightWorld]);

  const drawWidth = svgWidth - padding * 2;
  const drawHeight = svgHeight - padding * 2;

  // World to SVG Coordinate Conversion
  const toSvgX = React.useCallback(
    (xw: number) => padding + ((xw - xMin) / widthWorld) * drawWidth,
    [padding, xMin, widthWorld, drawWidth]
  );
  const toSvgY = React.useCallback(
    (yw: number) => svgHeight - padding - ((yw - yMin) / heightWorld) * drawHeight,
    [svgHeight, padding, yMin, heightWorld, drawHeight]
  );

  // Origin (0, 0) in SVG
  const originX = toSvgX(0);
  const originY = toSvgY(0);

  // Generate Grid lines
  const gridLines = useMemo(() => {
    const lines: { x1: number; y1: number; x2: number; y2: number }[] = [];
    if (!spec.grid && spec.grid !== undefined) return lines;

    const startX = Math.ceil(xMin / effectiveXStep) * effectiveXStep;
    for (let x = startX; x <= xMax; x += effectiveXStep) {
      if (Math.abs(x) < 1e-6) continue; // Skip axis line here
      const sx = toSvgX(x);
      lines.push({ x1: sx, y1: padding, x2: sx, y2: svgHeight - padding });
    }

    const startY = Math.ceil(yMin / effectiveYStep) * effectiveYStep;
    for (let y = startY; y <= yMax; y += effectiveYStep) {
      if (Math.abs(y) < 1e-6) continue; // Skip axis line here
      const sy = toSvgY(y);
      lines.push({ x1: padding, y1: sy, x2: svgWidth - padding, y2: sy });
    }

    return lines;
  }, [xMin, xMax, yMin, yMax, effectiveXStep, effectiveYStep, spec.grid, toSvgX, toSvgY, padding, svgWidth, svgHeight]);

  // Tick marks on axes
  const ticks = useMemo(() => {
    const list: { val: number; x: number; y: number; isX: boolean }[] = [];
    const startX = Math.ceil(xMin / effectiveXStep) * effectiveXStep;
    for (let x = startX; x <= xMax; x += effectiveXStep) {
      if (Math.abs(x) < 1e-6) continue;
      const cleanVal = Math.round(x * 1000) / 1000;
      list.push({ val: cleanVal, x: toSvgX(x), y: originY, isX: true });
    }

    const startY = Math.ceil(yMin / effectiveYStep) * effectiveYStep;
    for (let y = startY; y <= yMax; y += effectiveYStep) {
      if (Math.abs(y) < 1e-6) continue;
      const cleanVal = Math.round(y * 1000) / 1000;
      list.push({ val: cleanVal, x: originX, y: toSvgY(y), isX: false });
    }
    return list;
  }, [xMin, xMax, yMin, yMax, effectiveXStep, effectiveYStep, originX, originY, toSvgX, toSvgY]);

  return (
    <div className="relative w-full flex flex-col items-center select-none overflow-hidden">
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="w-full max-w-[420px] h-auto overflow-visible"
        style={{ maxHeight: "280px" }}
      >
        <defs>
          {/* Arrowhead marker for axes */}
          <marker
            id="axis-arrow"
            viewBox="0 0 10 10"
            refX="6"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748b" />
          </marker>

          {/* Clip path for plotted functions to remain within grid bounds */}
          <clipPath id="graph-viewport-clip">
            <rect
              x={padding}
              y={padding}
              width={drawWidth}
              height={drawHeight}
            />
          </clipPath>
        </defs>

        {/* 1. Grid Background */}
        <g className="stroke-slate-200 dark:stroke-slate-800" strokeWidth={1}>
          {gridLines.map((l, idx) => (
            <line
              key={`grid-${idx}`}
              x1={l.x1}
              y1={l.y1}
              x2={l.x2}
              y2={l.y2}
              strokeDasharray="2 2"
            />
          ))}
        </g>

        {/* 2. Axes (X and Y) with Arrowheads */}
        <g stroke="#64748b" strokeWidth={1.8}>
          {/* X Axis */}
          <line
            x1={padding - 10}
            y1={Math.max(padding, Math.min(svgHeight - padding, originY))}
            x2={svgWidth - padding + 12}
            y2={Math.max(padding, Math.min(svgHeight - padding, originY))}
            markerEnd="url(#axis-arrow)"
          />
          {/* Y Axis */}
          <line
            x1={Math.max(padding, Math.min(svgWidth - padding, originX))}
            y1={svgHeight - padding + 10}
            x2={Math.max(padding, Math.min(svgWidth - padding, originX))}
            y2={padding - 12}
            markerEnd="url(#axis-arrow)"
          />
        </g>

        {/* Axis Labels */}
        <text
          x={svgWidth - padding + 14}
          y={Math.max(padding, Math.min(svgHeight - padding, originY)) + 4}
          className="text-[11px] font-mono font-bold fill-slate-500"
        >
          x
        </text>
        <text
          x={Math.max(padding, Math.min(svgWidth - padding, originX)) - 4}
          y={padding - 16}
          textAnchor="end"
          className="text-[11px] font-mono font-bold fill-slate-500"
        >
          y
        </text>

        {/* 3. Ticks and Numbers */}
        <g className="fill-slate-400 dark:fill-slate-500 text-[9px] font-mono">
          {ticks.map((t, idx) => {
            if (t.isX) {
              return (
                <g key={`tick-${idx}`}>
                  <line
                    x1={t.x}
                    y1={t.y - 3}
                    x2={t.x}
                    y2={t.y + 3}
                    stroke="#64748b"
                    strokeWidth={1.2}
                  />
                  <text x={t.x} y={t.y + 12} textAnchor="middle">
                    {t.val}
                  </text>
                </g>
              );
            } else {
              return (
                <g key={`tick-${idx}`}>
                  <line
                    x1={t.x - 3}
                    y1={t.y}
                    x2={t.x + 3}
                    y2={t.y}
                    stroke="#64748b"
                    strokeWidth={1.2}
                  />
                  <text x={t.x - 6} y={t.y + 3} textAnchor="end">
                    {t.val}
                  </text>
                </g>
              );
            }
          })}

          {/* Origin 0 label */}
          {xMin < 0 && xMax > 0 && yMin < 0 && yMax > 0 && (
            <text
              x={originX - 5}
              y={originY + 12}
              textAnchor="end"
              className="fill-slate-400 dark:fill-slate-500 text-[9px] font-mono"
            >
              0
            </text>
          )}
        </g>

        {/* 4. Plotted Elements inside Clip Path */}
        <g clipPath="url(#graph-viewport-clip)">
          {(spec.plots || []).map((plot, idx) => (
            <PlotRenderer
              key={`plot-${idx}`}
              plot={plot}
              xMin={xMin}
              xMax={xMax}
              toSvgX={toSvgX}
              toSvgY={toSvgY}
              defaultColor={colors.primary}
            />
          ))}
        </g>

        {/* 5. Points and KaTeX Labels (Rendered on top outside clip path so labels don't get clipped) */}
        {(spec.plots || []).map((plot, idx) => {
          if (plot.type === "point") {
            const sx = toSvgX(plot.coord[0]);
            const sy = toSvgY(plot.coord[1]);
            const ptColor = plot.color || colors.primary;

            return (
              <g key={`pt-plot-${idx}`}>
                <circle
                  cx={sx}
                  cy={sy}
                  r={4.5}
                  fill={plot.hollow ? "#ffffff" : ptColor}
                  stroke={ptColor}
                  strokeWidth={2}
                  className="shadow-sm"
                />
                {plot.label && (
                  <foreignObject
                    x={sx + (plot.position === "left" || plot.position === "bottom-left" ? -75 : 8)}
                    y={sy + (plot.position === "top" || plot.position === "top-right" ? -26 : -13)}
                    width={80}
                    height={26}
                    className="overflow-visible pointer-events-none"
                  >
                    <div className="w-full h-full flex items-center">
                      <span className="text-[11px] font-bold px-1 py-0.5 rounded bg-white/80 dark:bg-slate-900/80 text-slate-800 dark:text-slate-100 shadow-sm border border-slate-200/50 dark:border-slate-700/50">
                        <FormattedText
                          text={plot.label.startsWith("$") ? plot.label : `$${plot.label}$`}
                        />
                      </span>
                    </div>
                  </foreignObject>
                )}
              </g>
            );
          }
          return null;
        })}
      </svg>
    </div>
  );
};

const PlotRenderer: React.FC<{
  plot: CartesianPlot;
  xMin: number;
  xMax: number;
  toSvgX: (xw: number) => number;
  toSvgY: (yw: number) => number;
  defaultColor: string;
}> = ({ plot, xMin, xMax, toSvgX, toSvgY, defaultColor }) => {
  if (plot.type === "function") {
    const domain = plot.domain || [xMin, xMax];
    const dStart = Math.max(domain[0], xMin);
    const dEnd = Math.min(domain[1], xMax);

    const steps = 80;
    const dx = (dEnd - dStart) / steps;
    const points: [number, number][] = [];

    for (let i = 0; i <= steps; i++) {
      const x = dStart + i * dx;
      let y = 0;

      if (plot.coefficients && plot.coefficients.length > 0) {
        // Polynomial: [a_n, ..., a_1, a_0]
        y = plot.coefficients.reduce((acc, coeff) => acc * x + coeff, 0);
      } else if (plot.fn) {
        y = evaluateSafeMath(plot.fn, x);
      }

      if (!isNaN(y) && isFinite(y)) {
        points.push([toSvgX(x), toSvgY(y)]);
      }
    }

    if (points.length < 2) return null;

    const pathD = points.reduce(
      (acc, [x, y], idx) => (idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`),
      ""
    );

    return (
      <path
        d={pathD}
        fill="none"
        stroke={plot.color || defaultColor}
        strokeWidth={plot.strokeWidth || 2.4}
        strokeDasharray={plot.strokeDasharray}
        strokeLinecap="round"
      />
    );
  }

  if (plot.type === "segment") {
    const [x1, y1] = plot.from;
    const [x2, y2] = plot.to;

    return (
      <line
        x1={toSvgX(x1)}
        y1={toSvgY(y1)}
        x2={toSvgX(x2)}
        y2={toSvgY(y2)}
        stroke={plot.color || defaultColor}
        strokeWidth={plot.strokeWidth || 2}
        strokeDasharray={plot.strokeDasharray}
      />
    );
  }

  if (plot.type === "slope_triangle") {
    const [x1, y1] = plot.p1;
    const [x2, y2] = plot.p2;

    const sx1 = toSvgX(x1);
    const sy1 = toSvgY(y1);
    const sx2 = toSvgX(x2);
    const sy2 = toSvgY(y2);
    const cornerX = sx2;
    const cornerY = sy1;

    return (
      <g>
        {/* Shaded triangle area */}
        <polygon
          points={`${sx1},${sy1} ${cornerX},${cornerY} ${sx2},${sy2}`}
          fill="rgba(245, 158, 11, 0.12)"
          stroke="none"
        />
        {/* Horizontal run leg */}
        <line
          x1={sx1}
          y1={sy1}
          x2={cornerX}
          y2={cornerY}
          stroke="#d97706"
          strokeWidth={2}
          strokeDasharray="4 3"
        />
        {/* Vertical rise leg */}
        <line
          x1={cornerX}
          y1={cornerY}
          x2={sx2}
          y2={sy2}
          stroke="#d97706"
          strokeWidth={2}
          strokeDasharray="4 3"
        />
        {/* Hypotenuse line */}
        <line
          x1={sx1}
          y1={sy1}
          x2={sx2}
          y2={sy2}
          stroke={defaultColor}
          strokeWidth={2.5}
        />
      </g>
    );
  }

  return null;
};

// Safe, clean expression evaluator for mathematical functions
function evaluateSafeMath(fn: string, x: number): number {
  try {
    const linearMatch = fn.match(/^(-?\d*\.?\d*)\*?x\s*([+-]\s*\d+\.?\d*)?$/i);
    if (linearMatch) {
      const mStr = linearMatch[1];
      const m = mStr === "" || mStr === "+" ? 1 : mStr === "-" ? -1 : parseFloat(mStr);
      const cStr = linearMatch[2] ? linearMatch[2].replace(/\s+/g, "") : "0";
      const c = parseFloat(cStr) || 0;
      return m * x + c;
    }

    const clean = fn.replace(/\s+/g, "").replace(/\^2/g, "*x");
    const val = clean.replace(/(\d)x/gi, "$1*" + x).replace(/x/gi, `(${x})`);
    return evaluateArithmetic(val);
  } catch {
    return 0;
  }
}

// Pure arithmetic parser (No eval, no Function constructor)
function evaluateArithmetic(expr: string): number {
  let pos = 0;

  function peek(): string {
    return expr[pos] || "";
  }

  function get(): string {
    return expr[pos++] || "";
  }

  function parseNumber(): number {
    let str = "";
    if (peek() === "-") {
      str += get();
    }
    while (/[0-9.]/.test(peek())) {
      str += get();
    }
    return parseFloat(str) || 0;
  }

  function parseFactor(): number {
    if (peek() === "(") {
      get(); // '('
      const val = parseExpr();
      if (peek() === ")") get(); // ')'
      return val;
    }
    return parseNumber();
  }

  function parseTerm(): number {
    let val = parseFactor();
    while (peek() === "*" || peek() === "/") {
      const op = get();
      const next = parseFactor();
      if (op === "*") val *= next;
      else if (op === "/" && next !== 0) val /= next;
    }
    return val;
  }

  function parseExpr(): number {
    let val = parseTerm();
    while (peek() === "+" || peek() === "-") {
      const op = get();
      const next = parseTerm();
      if (op === "+") val += next;
      else if (op === "-") val -= next;
    }
    return val;
  }

  return parseExpr();
}

// Adaptive nice step algorithm (1, 2, 5, 10 rule)
function calculateSmartStep(min: number, max: number, targetTicks: number = 6): number {
  const span = Math.max(max - min, 1e-4);
  const rawStep = span / targetTicks;
  const power = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const normalized = rawStep / power;

  let mult = 1;
  if (normalized < 1.6) {
    mult = 1;
  } else if (normalized < 3.5) {
    mult = 2;
  } else if (normalized < 7.5) {
    mult = 5;
  } else {
    mult = 10;
  }
  const step = mult * power;
  if (span >= 6 && step < 1) {
    return 1;
  }
  return Math.round(step * 1000) / 1000;
}
