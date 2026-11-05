"use client";

import React, { useState, useRef, useCallback } from "react";
import { RotateCcw, Sparkles } from "lucide-react";

interface InteractivePythagoras2DProps {
  initialA?: number;
  initialB?: number;
}

export const InteractivePythagoras2D: React.FC<InteractivePythagoras2DProps> = ({
  initialA = 3,
  initialB = 4,
}) => {
  const [legA, setLegA] = useState(initialA); // Vertical
  const [legB, setLegB] = useState(initialB); // Horizontal
  const [hovered, setHovered] = useState<string | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const draggingRef = useRef<"vertA" | "vertB" | null>(null);

  // Responsive scale factor based on initial values
  const maxInitial = Math.max(initialA, initialB, 6);
  const scale = Math.min(22, Math.max(11, Math.floor(140 / maxInitial)));

  // SVG coordinates (viewBox: 380 x 260)
  const ox = 85;
  const oy = 215;

  const topY = oy - legA * scale;
  const rightX = ox + legB * scale;

  const aSq = legA * legA;
  const bSq = legB * legB;
  const cSq = aSq + bSq;
  const hyp = Math.round(Math.sqrt(cSq) * 100) / 100;
  const area = Math.round(0.5 * legA * legB * 10) / 10;

  // Pointer Drag Handlers with direct SVG coordinate mapping
  const startDrag = (type: "vertA" | "vertB") => (e: React.PointerEvent) => {
    e.preventDefault();
    e.stopPropagation();
    draggingRef.current = type;
    (e.currentTarget as Element).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!draggingRef.current || !svgRef.current) return;
    const pt = svgRef.current.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const ctm = svgRef.current.getScreenCTM();
    if (!ctm) return;
    const svgP = pt.matrixTransform(ctm.inverse());

    if (draggingRef.current === "vertA") {
      // Dragging top vertex vertically
      const rawA = (oy - svgP.y) / scale;
      const clampedA = Math.max(2, Math.min(15, Math.round(rawA)));
      setLegA(clampedA);
    } else if (draggingRef.current === "vertB") {
      // Dragging right vertex horizontally
      const rawB = (svgP.x - ox) / scale;
      const clampedB = Math.max(2, Math.min(18, Math.round(rawB)));
      setLegB(clampedB);
    }
  }, [oy, ox, scale]);

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (draggingRef.current) {
      try {
        (e.currentTarget as Element).releasePointerCapture(e.pointerId);
      } catch {
        // pointer capture release fallback
      }
      draggingRef.current = null;
    }
  }, []);

  const isChanged = legA !== initialA || legB !== initialB;

  return (
    <div className="flex flex-col items-center w-full select-none">
      {/* SVG Interactive Canvas */}
      <div className="relative w-full bg-[#0a0d14] rounded-xl border border-[#232a3d] p-2 flex flex-col justify-center items-center overflow-hidden">
        
        {/* Dynamic Tooltip / Parameter Inspector Bar */}
        <div className="w-full mb-1.5 px-3 py-1.5 bg-[#121724]/90 backdrop-blur border border-indigo-500/25 rounded-lg text-xs flex justify-between items-center transition-all min-h-[36px]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="text-slate-200">
              {hovered === "triangle" ? (
                <span>
                  <strong className="text-indigo-300">Triangle Interior:</strong> Area = &frac12; &times; a &times; b = &frac12;({legA})({legB}) = <strong className="text-emerald-300">{area}</strong>
                </span>
              ) : hovered === "legA" || hovered === "vertA" ? (
                <span>
                  <strong className="text-sky-300">Vertical Leg a = {legA}</strong> (Projected square a&sup2; = {aSq}) &mdash; <span className="text-slate-400">Drag to adjust height</span>
                </span>
              ) : hovered === "legB" || hovered === "vertB" ? (
                <span>
                  <strong className="text-emerald-300">Horizontal Leg b = {legB}</strong> (Projected square b&sup2; = {bSq}) &mdash; <span className="text-slate-400">Drag to adjust width</span>
                </span>
              ) : hovered === "hyp" ? (
                <span>
                  <strong className="text-amber-300">Hypotenuse c = {hyp}</strong> &mdash; c&sup2; = a&sup2; + b&sup2; = {aSq} + {bSq} = <strong className="text-indigo-300">{cSq}</strong>
                </span>
              ) : hovered === "rightAngle" ? (
                <span>
                  <strong className="text-amber-400">Right Angle &ang;C = 90&deg;</strong> (Perpendicular legs a &perp; b)
                </span>
              ) : hovered === "sqA" ? (
                <span>
                  <strong className="text-sky-300">Dashed Square on a:</strong> Area a&sup2; = {legA} &times; {legA} = <strong className="text-sky-300">{aSq}</strong>
                </span>
              ) : hovered === "sqB" ? (
                <span>
                  <strong className="text-emerald-300">Dashed Square on b:</strong> Area b&sup2; = {legB} &times; {legB} = <strong className="text-emerald-300">{bSq}</strong>
                </span>
              ) : (
                <span className="text-slate-400">
                  Directly drag <span className="text-sky-300 font-semibold">Leg a</span> or <span className="text-emerald-300 font-semibold">Leg b</span> handles. Hover elements to inspect properties.
                </span>
              )}
            </span>
          </div>
          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-950/70 text-indigo-300 border border-indigo-800/50 shrink-0 hidden sm:inline-block">
            2D Interactive
          </span>
        </div>

        <svg
          ref={svgRef}
          viewBox="0 0 380 250"
          className="w-full max-w-[400px] h-auto overflow-visible touch-none cursor-default"
          style={{ maxHeight: "250px" }}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
        >
          <defs>
            <filter id="glow-pyth" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Grid Pattern */}
          <g stroke="#161c2b" strokeWidth="0.8">
            {Array.from({ length: 16 }).map((_, i) => (
              <line key={`gx-${i}`} x1={ox + i * scale} y1={25} x2={ox + i * scale} y2={oy + 15} />
            ))}
            {Array.from({ length: 13 }).map((_, i) => (
              <line key={`gy-${i}`} x1={30} y1={oy - i * scale} x2={350} y2={oy - i * scale} />
            ))}
          </g>

          {/* Dashed Area Square a^2 on the left */}
          <rect
            x={ox - Math.min(48, legA * scale * 0.45)}
            y={topY}
            width={Math.min(48, legA * scale * 0.45)}
            height={legA * scale}
            fill={hovered === "sqA" || hovered === "legA" ? "rgba(56, 189, 248, 0.14)" : "rgba(56, 189, 248, 0.04)"}
            stroke={hovered === "sqA" || hovered === "legA" ? "#38bdf8" : "#223249"}
            strokeDasharray="3 3"
            strokeWidth={1.5}
            className="cursor-pointer transition-colors"
            onPointerOver={() => setHovered("sqA")}
            onPointerOut={() => setHovered(null)}
          />
          <text
            x={ox - Math.min(48, legA * scale * 0.45) / 2}
            y={(oy + topY) / 2}
            textAnchor="middle"
            dominantBaseline="central"
            className="fill-sky-400/60 font-mono text-[10px] pointer-events-none select-none"
          >
            a&sup2;={aSq}
          </text>

          {/* Dashed Area Square b^2 on the bottom */}
          <rect
            x={ox}
            y={oy}
            width={legB * scale}
            height={Math.min(42, legB * scale * 0.4)}
            fill={hovered === "sqB" || hovered === "legB" ? "rgba(16, 185, 129, 0.14)" : "rgba(16, 185, 129, 0.04)"}
            stroke={hovered === "sqB" || hovered === "legB" ? "#10b981" : "#223249"}
            strokeDasharray="3 3"
            strokeWidth={1.5}
            className="cursor-pointer transition-colors"
            onPointerOver={() => setHovered("sqB")}
            onPointerOut={() => setHovered(null)}
          />
          <text
            x={(ox + rightX) / 2}
            y={oy + Math.min(42, legB * scale * 0.4) / 2}
            textAnchor="middle"
            dominantBaseline="central"
            className="fill-emerald-400/60 font-mono text-[10px] pointer-events-none select-none"
          >
            b&sup2;={bSq}
          </text>

          {/* Main Triangle Body */}
          <polygon
            points={`${ox},${oy} ${rightX},${oy} ${ox},${topY}`}
            stroke={hovered === "triangle" ? "#a5b4fc" : "#818cf8"}
            strokeWidth={hovered === "triangle" ? 3 : 2}
            fill={hovered === "triangle" ? "rgba(99, 102, 241, 0.22)" : "rgba(99, 102, 241, 0.08)"}
            strokeLinejoin="round"
            className="transition-colors cursor-pointer"
            onPointerOver={() => setHovered("triangle")}
            onPointerOut={() => setHovered(null)}
          />

          {/* Right Angle ∟ Marker (Interactive Hoverable) */}
          <g
            onPointerOver={() => setHovered("rightAngle")}
            onPointerOut={() => setHovered(null)}
            className="cursor-pointer"
          >
            <polyline
              points={`${ox},${oy - 14} ${ox + 14},${oy - 14} ${ox + 14},${oy}`}
              stroke={hovered === "rightAngle" ? "#f59e0b" : "#94a3b8"}
              strokeWidth={hovered === "rightAngle" ? 2.5 : 1.5}
              fill="none"
            />
            {/* Square fill inside 90 deg corner */}
            <rect
              x={ox}
              y={oy - 14}
              width={14}
              height={14}
              fill={hovered === "rightAngle" ? "rgba(245, 158, 11, 0.25)" : "transparent"}
            />
          </g>

          {/* Leg A (Vertical) - Hover & Direct Drag */}
          <g
            onPointerOver={() => setHovered("legA")}
            onPointerOut={() => setHovered(null)}
            onPointerDown={startDrag("vertA")}
            className="cursor-ns-resize"
          >
            {/* Invisible thick hit target */}
            <line x1={ox} y1={oy} x2={ox} y2={topY} stroke="transparent" strokeWidth={24} />
            {/* Visible line */}
            <line
              x1={ox}
              y1={oy}
              x2={ox}
              y2={topY}
              stroke={hovered === "legA" || hovered === "vertA" ? "#38bdf8" : "#0284c7"}
              strokeWidth={hovered === "legA" || hovered === "vertA" ? 5 : 3.5}
              filter={hovered === "legA" || hovered === "vertA" ? "url(#glow-pyth)" : undefined}
            />
            {/* Dimension label */}
            <text
              x={ox - 14}
              y={(oy + topY) / 2}
              textAnchor="end"
              dominantBaseline="central"
              className={`font-mono text-xs font-bold transition-all ${
                hovered === "legA" || hovered === "vertA" ? "fill-sky-300 font-extrabold text-sm" : "fill-sky-400"
              }`}
            >
              a = {legA}
            </text>
          </g>

          {/* Leg B (Horizontal) - Hover & Direct Drag */}
          <g
            onPointerOver={() => setHovered("legB")}
            onPointerOut={() => setHovered(null)}
            onPointerDown={startDrag("vertB")}
            className="cursor-ew-resize"
          >
            {/* Invisible thick hit target */}
            <line x1={ox} y1={oy} x2={rightX} y2={oy} stroke="transparent" strokeWidth={24} />
            {/* Visible line */}
            <line
              x1={ox}
              y1={oy}
              x2={rightX}
              y2={oy}
              stroke={hovered === "legB" || hovered === "vertB" ? "#10b981" : "#059669"}
              strokeWidth={hovered === "legB" || hovered === "vertB" ? 5 : 3.5}
              filter={hovered === "legB" || hovered === "vertB" ? "url(#glow-pyth)" : undefined}
            />
            {/* Dimension label */}
            <text
              x={(ox + rightX) / 2}
              y={oy + 18}
              textAnchor="middle"
              dominantBaseline="central"
              className={`font-mono text-xs font-bold transition-all ${
                hovered === "legB" || hovered === "vertB" ? "fill-emerald-300 font-extrabold text-sm" : "fill-emerald-400"
              }`}
            >
              b = {legB}
            </text>
          </g>

          {/* Hypotenuse C - Hoverable */}
          <g
            onPointerOver={() => setHovered("hyp")}
            onPointerOut={() => setHovered(null)}
            className="cursor-pointer"
          >
            {/* Invisible thick hit target */}
            <line x1={ox} y1={topY} x2={rightX} y2={oy} stroke="transparent" strokeWidth={24} />
            {/* Visible line */}
            <line
              x1={ox}
              y1={topY}
              x2={rightX}
              y2={oy}
              stroke={hovered === "hyp" ? "#fbbf24" : "#d97706"}
              strokeWidth={hovered === "hyp" ? 5 : 3.5}
              filter={hovered === "hyp" ? "url(#glow-pyth)" : undefined}
            />
            {/* Dimension label */}
            <text
              x={(ox + rightX) / 2 + 12}
              y={(topY + oy) / 2 - 12}
              textAnchor="start"
              dominantBaseline="central"
              className={`font-mono text-xs font-bold transition-all ${
                hovered === "hyp" ? "fill-amber-300 font-extrabold text-sm" : "fill-amber-400"
              }`}
            >
              c = {hyp}
            </text>
          </g>

          {/* Draggable Vertex Handle A (Top - height adjustment) */}
          <g
            onPointerDown={startDrag("vertA")}
            className="cursor-ns-resize"
            onPointerOver={() => setHovered("vertA")}
            onPointerOut={() => setHovered(null)}
          >
            <circle cx={ox} cy={topY} r={18} fill="transparent" />
            <circle
              cx={ox}
              cy={topY}
              r={hovered === "vertA" ? 9 : 7}
              fill="#38bdf8"
              stroke="#ffffff"
              strokeWidth={2}
              className="transition-all filter drop-shadow-[0_0_8px_rgba(56,189,248,0.9)]"
            />
            {/* Direction Arrows Indicator on hover */}
            {hovered === "vertA" && (
              <g stroke="#ffffff" strokeWidth={1.5} fill="none" opacity={0.9}>
                <path d={`M ${ox} ${topY - 14} L ${ox} ${topY - 20} M ${ox - 3} ${topY - 17} L ${ox} ${topY - 20} L ${ox + 3} ${topY - 17}`} />
                <path d={`M ${ox} ${topY + 14} L ${ox} ${topY + 20} M ${ox - 3} ${topY + 17} L ${ox} ${topY + 20} L ${ox + 3} ${topY + 17}`} />
              </g>
            )}
          </g>

          {/* Draggable Vertex Handle B (Right - base adjustment) */}
          <g
            onPointerDown={startDrag("vertB")}
            className="cursor-ew-resize"
            onPointerOver={() => setHovered("vertB")}
            onPointerOut={() => setHovered(null)}
          >
            <circle cx={rightX} cy={oy} r={18} fill="transparent" />
            <circle
              cx={rightX}
              cy={oy}
              r={hovered === "vertB" ? 9 : 7}
              fill="#10b981"
              stroke="#ffffff"
              strokeWidth={2}
              className="transition-all filter drop-shadow-[0_0_8px_rgba(16,185,129,0.9)]"
            />
            {/* Direction Arrows Indicator on hover */}
            {hovered === "vertB" && (
              <g stroke="#ffffff" strokeWidth={1.5} fill="none" opacity={0.9}>
                <path d={`M ${rightX + 14} ${oy} L ${rightX + 20} ${oy} M ${rightX + 17} ${oy - 3} L ${rightX + 20} ${oy} L ${rightX + 17} ${oy + 3}`} />
                <path d={`M ${rightX - 14} ${oy} L ${rightX - 20} ${oy} M ${rightX - 17} ${oy - 3} L ${rightX - 20} ${oy} L ${rightX - 17} ${oy + 3}`} />
              </g>
            )}
          </g>
        </svg>
      </div>

      {/* Live Telemetry & Equation Proof Bar */}
      <div className="w-full mt-2 p-2.5 bg-[#121622] border border-[#232a3d] rounded-xl flex flex-wrap justify-between items-center gap-2 font-mono text-xs">
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Equation:</span>
          <span className="text-sky-300 font-bold">{legA}&sup2;</span>
          <span className="text-slate-500">+</span>
          <span className="text-emerald-300 font-bold">{legB}&sup2;</span>
          <span className="text-slate-500">=</span>
          <span className="text-sky-400">{aSq}</span>
          <span className="text-slate-500">+</span>
          <span className="text-emerald-400">{bSq}</span>
          <span className="text-slate-500">=</span>
          <span className="text-indigo-300 font-extrabold">{cSq}</span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-950/40 border border-amber-600/30">
            <span className="text-slate-400">c = &radic;{cSq} =</span>
            <span className="text-amber-300 font-black text-sm">{hyp}</span>
          </div>

          <button
            type="button"
            onClick={() => {
              setLegA(initialA);
              setLegB(initialB);
            }}
            disabled={!isChanged}
            title="Reset triangle to problem default values"
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
              isChanged
                ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm"
                : "bg-[#1b2233] text-slate-500 cursor-not-allowed"
            }`}
          >
            <RotateCcw className="w-3 h-3" />
            Reset ({initialA}, {initialB})
          </button>
        </div>
      </div>
    </div>
  );
};
