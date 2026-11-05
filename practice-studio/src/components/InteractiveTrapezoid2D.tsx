"use client";

import React, { useState, useRef, useCallback } from "react";
import { RotateCcw, Sparkles } from "lucide-react";

interface InteractiveTrapezoid2DProps {
  initialB1?: number; // Top base
  initialB2?: number; // Bottom base
  initialH?: number;  // Height
}

export const InteractiveTrapezoid2D: React.FC<InteractiveTrapezoid2DProps> = ({
  initialB1 = 6,
  initialB2 = 10,
  initialH = 6,
}) => {
  const [b1, setB1] = useState(initialB1);
  const [b2, setB2] = useState(initialB2);
  const [h, setH] = useState(initialH);
  const [hovered, setHovered] = useState<string | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const draggingRef = useRef<"b1" | "b2" | "h" | null>(null);

  // Dynamic scale factor based on max dimension
  const maxDim = Math.max(b2, 12);
  const scale = Math.min(18, Math.max(9, Math.floor(220 / maxDim)));

  // SVG coordinates (viewBox: 380 x 240)
  const ox = 55;
  const oy = 195;

  const botW = b2 * scale;
  const topW = b1 * scale;
  const hPx = h * scale;

  // Slant offset on the left to make an attractive trapezoid
  const diffW = botW - topW;
  const leftSlant = Math.max(16, Math.round(diffW * 0.4));
  const rightSlant = diffW - leftSlant;

  const p1 = { x: ox, y: oy };                           // bottom-left
  const p2 = { x: ox + botW, y: oy };                    // bottom-right
  const p3 = { x: ox + leftSlant + topW, y: oy - hPx };  // top-right
  const p4 = { x: ox + leftSlant, y: oy - hPx };         // top-left

  const altLeftX = p4.x;
  const altRightX = p3.x;

  // Geometric sub-regions
  const totalArea = Math.round(0.5 * (b1 + b2) * h * 10) / 10;
  const rectArea = Math.round(b1 * h * 10) / 10;
  const leftBaseVal = Math.round(((leftSlant / botW) * b2) * 10) / 10;
  const rightBaseVal = Math.round(((rightSlant / botW) * b2) * 10) / 10;
  const leftTriArea = Math.round(0.5 * leftBaseVal * h * 10) / 10;
  const rightTriArea = Math.round(0.5 * rightBaseVal * h * 10) / 10;

  // Drag handlers
  const startDrag = (type: "b1" | "b2" | "h") => (e: React.PointerEvent) => {
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

    if (draggingRef.current === "b1") {
      // Adjust top base width
      const rawB1 = (svgP.x - (ox + leftSlant)) / scale;
      const clampedB1 = Math.max(3, Math.min(b2 - 2, Math.round(rawB1)));
      setB1(clampedB1);
    } else if (draggingRef.current === "b2") {
      // Adjust bottom base width
      const rawB2 = (svgP.x - ox) / scale;
      const clampedB2 = Math.max(b1 + 2, Math.min(22, Math.round(rawB2)));
      setB2(clampedB2);
    } else if (draggingRef.current === "h") {
      // Adjust height
      const rawH = (oy - svgP.y) / scale;
      const clampedH = Math.max(3, Math.min(12, Math.round(rawH)));
      setH(clampedH);
    }
  }, [b1, b2, leftSlant, ox, oy, scale]);

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (draggingRef.current) {
      try {
        (e.currentTarget as Element).releasePointerCapture(e.pointerId);
      } catch {
        // capture fallback
      }
      draggingRef.current = null;
    }
  }, []);

  const isChanged = b1 !== initialB1 || b2 !== initialB2 || h !== initialH;

  return (
    <div className="flex flex-col items-center w-full select-none">
      {/* SVG Interactive Canvas */}
      <div className="relative w-full bg-[#0a0d14] rounded-xl border border-[#232a3d] p-2 flex flex-col justify-center items-center overflow-hidden">
        
        {/* Dynamic Tooltip / Parameter Inspector Bar */}
        <div className="w-full mb-1.5 px-3 py-1.5 bg-[#121724]/90 backdrop-blur border border-emerald-500/25 rounded-lg text-xs flex justify-between items-center transition-all min-h-[36px]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="text-slate-200">
              {hovered === "trapezoid" ? (
                <span>
                  <strong className="text-emerald-300">Total Trapezoid Area:</strong> A = &frac12;(b&sub1; + b&sub2;)h = &frac12;({b1} + {b2})({h}) = <strong className="text-emerald-300">{totalArea}</strong>
                </span>
              ) : hovered === "b1" ? (
                <span>
                  <strong className="text-sky-300">Top Base b&sub1; = {b1}</strong> &mdash; <span className="text-slate-400">Drag blue handle to resize top</span>
                </span>
              ) : hovered === "b2" ? (
                <span>
                  <strong className="text-emerald-300">Bottom Base b&sub2; = {b2}</strong> &mdash; <span className="text-slate-400">Drag green handle to resize base</span>
                </span>
              ) : hovered === "height" ? (
                <span>
                  <strong className="text-amber-300">Altitude / Height h = {h}</strong> (Perpendicular &perp; bases) &mdash; <span className="text-slate-400">Drag yellow handle to adjust</span>
                </span>
              ) : hovered === "subRect" ? (
                <span>
                  <strong className="text-teal-300">Divided Center Rectangle:</strong> Area = b&sub1; &times; h = {b1} &times; {h} = <strong className="text-teal-200">{rectArea}</strong>
                </span>
              ) : hovered === "subTriLeft" ? (
                <span>
                  <strong className="text-indigo-300">Divided Left Triangle:</strong> Area &approx; &frac12; &times; {leftBaseVal} &times; {h} = <strong className="text-indigo-200">{leftTriArea}</strong>
                </span>
              ) : hovered === "subTriRight" ? (
                <span>
                  <strong className="text-purple-300">Divided Right Triangle:</strong> Area &approx; &frac12; &times; {rightBaseVal} &times; {h} = <strong className="text-purple-200">{rightTriArea}</strong>
                </span>
              ) : hovered === "rightAngle" ? (
                <span>
                  <strong className="text-amber-400">Right Angle &ang; = 90&deg;</strong> (Height meets base perpendicularly)
                </span>
              ) : (
                <span className="text-slate-400">
                  Drag <span className="text-sky-300 font-semibold">b&sub1;</span>, <span className="text-emerald-300 font-semibold">b&sub2;</span>, or <span className="text-amber-300 font-semibold">h</span>. Hover dashed sub-shapes to see area decomposition.
                </span>
              )}
            </span>
          </div>
          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-950/70 text-emerald-300 border border-emerald-800/50 shrink-0 hidden sm:inline-block">
            2D Interactive
          </span>
        </div>

        <svg
          ref={svgRef}
          viewBox="0 0 380 230"
          className="w-full max-w-[400px] h-auto overflow-visible touch-none cursor-default"
          style={{ maxHeight: "240px" }}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
        >
          <defs>
            <filter id="glow-trap" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Grid Pattern */}
          <g stroke="#161c2b" strokeWidth="0.8">
            {Array.from({ length: 18 }).map((_, i) => (
              <line key={`gx-${i}`} x1={ox + i * scale} y1={25} x2={ox + i * scale} y2={oy + 15} />
            ))}
            {Array.from({ length: 12 }).map((_, i) => (
              <line key={`gy-${i}`} x1={30} y1={oy - i * scale} x2={360} y2={oy - i * scale} />
            ))}
          </g>

          {/* --- Divided Sub-Shapes (Dashed line sections) --- */}
          {/* 1. Left Triangle Sub-Shape */}
          <polygon
            points={`${p1.x},${p1.y} ${altLeftX},${oy} ${p4.x},${p4.y}`}
            fill={hovered === "subTriLeft" ? "rgba(99, 102, 241, 0.28)" : "transparent"}
            stroke="none"
            className="cursor-pointer transition-colors"
            onPointerOver={() => setHovered("subTriLeft")}
            onPointerOut={() => setHovered(null)}
          />

          {/* 2. Middle Rectangle Sub-Shape */}
          <polygon
            points={`${altLeftX},${oy} ${altRightX},${oy} ${p3.x},${p3.y} ${p4.x},${p4.y}`}
            fill={hovered === "subRect" ? "rgba(20, 184, 166, 0.22)" : "transparent"}
            stroke="none"
            className="cursor-pointer transition-colors"
            onPointerOver={() => setHovered("subRect")}
            onPointerOut={() => setHovered(null)}
          />

          {/* 3. Right Triangle Sub-Shape */}
          <polygon
            points={`${altRightX},${oy} ${p2.x},${p2.y} ${p3.x},${p3.y}`}
            fill={hovered === "subTriRight" ? "rgba(168, 85, 247, 0.28)" : "transparent"}
            stroke="none"
            className="cursor-pointer transition-colors"
            onPointerOver={() => setHovered("subTriRight")}
            onPointerOut={() => setHovered(null)}
          />

          {/* Main Trapezoid Body */}
          <polygon
            points={`${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y} ${p4.x},${p4.y}`}
            stroke={hovered === "trapezoid" ? "#34d399" : "#10b981"}
            strokeWidth={hovered === "trapezoid" ? 3 : 2}
            fill={hovered === "trapezoid" ? "rgba(16, 185, 129, 0.2)" : "rgba(16, 185, 129, 0.08)"}
            strokeLinejoin="round"
            className="transition-colors cursor-pointer"
            onPointerOver={() => setHovered("trapezoid")}
            onPointerOut={() => setHovered(null)}
          />

          {/* Left Altitude Dashed Line & Right Angle */}
          <g
            onPointerOver={() => setHovered("height")}
            onPointerOut={() => setHovered(null)}
            onPointerDown={startDrag("h")}
            className="cursor-ns-resize"
          >
            <line x1={altLeftX} y1={p4.y} x2={altLeftX} y2={oy} stroke="transparent" strokeWidth={24} />
            <line
              x1={altLeftX}
              y1={p4.y}
              x2={altLeftX}
              y2={oy}
              stroke={hovered === "height" ? "#fbbf24" : "#94a3b8"}
              strokeWidth={hovered === "height" ? 3 : 1.8}
              strokeDasharray="4 4"
              filter={hovered === "height" ? "url(#glow-trap)" : undefined}
            />
            {/* Right Angle ∟ Marker */}
            <polyline
              points={`${altLeftX},${oy - 12} ${altLeftX + 12},${oy - 12} ${altLeftX + 12},${oy}`}
              stroke={hovered === "height" ? "#fbbf24" : "#94a3b8"}
              strokeWidth={1.5}
              fill="none"
            />
          </g>

          {/* Right Altitude Dashed Line (Subtle) */}
          <line
            x1={altRightX}
            y1={p3.y}
            x2={altRightX}
            y2={oy}
            stroke="#475569"
            strokeWidth={1.2}
            strokeDasharray="3 3"
          />

          {/* Top Base b1 - Hover & Drag */}
          <g
            onPointerOver={() => setHovered("b1")}
            onPointerOut={() => setHovered(null)}
            onPointerDown={startDrag("b1")}
            className="cursor-ew-resize"
          >
            <line x1={p4.x} y1={p4.y} x2={p3.x} y2={p3.y} stroke="transparent" strokeWidth={24} />
            <line
              x1={p4.x}
              y1={p4.y}
              x2={p3.x}
              y2={p3.y}
              stroke={hovered === "b1" ? "#38bdf8" : "#0284c7"}
              strokeWidth={hovered === "b1" ? 5 : 3.5}
              filter={hovered === "b1" ? "url(#glow-trap)" : undefined}
            />
            <text
              x={(p4.x + p3.x) / 2}
              y={p4.y - 14}
              textAnchor="middle"
              dominantBaseline="central"
              className={`font-mono text-xs font-bold transition-all ${
                hovered === "b1" ? "fill-sky-300 font-extrabold text-sm" : "fill-sky-400"
              }`}
            >
              b&sub1; = {b1}
            </text>
          </g>

          {/* Bottom Base b2 - Hover & Drag */}
          <g
            onPointerOver={() => setHovered("b2")}
            onPointerOut={() => setHovered(null)}
            onPointerDown={startDrag("b2")}
            className="cursor-ew-resize"
          >
            <line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke="transparent" strokeWidth={24} />
            <line
              x1={p1.x}
              y1={p1.y}
              x2={p2.x}
              y2={p2.y}
              stroke={hovered === "b2" ? "#34d399" : "#059669"}
              strokeWidth={hovered === "b2" ? 5 : 3.5}
              filter={hovered === "b2" ? "url(#glow-trap)" : undefined}
            />
            <text
              x={(p1.x + p2.x) / 2}
              y={oy + 18}
              textAnchor="middle"
              dominantBaseline="central"
              className={`font-mono text-xs font-bold transition-all ${
                hovered === "b2" ? "fill-emerald-300 font-extrabold text-sm" : "fill-emerald-400"
              }`}
            >
              b&sub2; = {b2}
            </text>
          </g>

          {/* Height Label beside altitude */}
          <text
            x={altLeftX + 16}
            y={(p4.y + oy) / 2}
            textAnchor="start"
            dominantBaseline="central"
            onPointerOver={() => setHovered("height")}
            onPointerOut={() => setHovered(null)}
            className={`font-mono text-xs font-bold transition-all cursor-pointer ${
              hovered === "height" ? "fill-amber-300 font-extrabold text-sm" : "fill-amber-400"
            }`}
          >
            h = {h}
          </text>

          {/* Draggable Handle for Top Base b1 (at p3: top-right) */}
          <g
            onPointerDown={startDrag("b1")}
            className="cursor-ew-resize"
            onPointerOver={() => setHovered("b1")}
            onPointerOut={() => setHovered(null)}
          >
            <circle cx={p3.x} cy={p3.y} r={18} fill="transparent" />
            <circle
              cx={p3.x}
              cy={p3.y}
              r={hovered === "b1" ? 9 : 7}
              fill="#38bdf8"
              stroke="#ffffff"
              strokeWidth={2}
              className="transition-all filter drop-shadow-[0_0_8px_rgba(56,189,248,0.9)]"
            />
          </g>

          {/* Draggable Handle for Bottom Base b2 (at p2: bottom-right) */}
          <g
            onPointerDown={startDrag("b2")}
            className="cursor-ew-resize"
            onPointerOver={() => setHovered("b2")}
            onPointerOut={() => setHovered(null)}
          >
            <circle cx={p2.x} cy={p2.y} r={18} fill="transparent" />
            <circle
              cx={p2.x}
              cy={p2.y}
              r={hovered === "b2" ? 9 : 7}
              fill="#10b981"
              stroke="#ffffff"
              strokeWidth={2}
              className="transition-all filter drop-shadow-[0_0_8px_rgba(16,185,129,0.9)]"
            />
          </g>

          {/* Draggable Handle for Height h (at p4: top-left) */}
          <g
            onPointerDown={startDrag("h")}
            className="cursor-ns-resize"
            onPointerOver={() => setHovered("height")}
            onPointerOut={() => setHovered(null)}
          >
            <circle cx={p4.x} cy={p4.y} r={18} fill="transparent" />
            <circle
              cx={p4.x}
              cy={p4.y}
              r={hovered === "height" ? 9 : 7}
              fill="#fbbf24"
              stroke="#ffffff"
              strokeWidth={2}
              className="transition-all filter drop-shadow-[0_0_8px_rgba(251,191,36,0.9)]"
            />
          </g>
        </svg>
      </div>

      {/* Live Telemetry & Equation Proof Bar */}
      <div className="w-full mt-2 p-2.5 bg-[#121622] border border-[#232a3d] rounded-xl flex flex-wrap justify-between items-center gap-2 font-mono text-xs">
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Formula:</span>
          <span className="text-emerald-300 font-bold">&frac12; &times; (b&sub1; + b&sub2;) &times; h</span>
          <span className="text-slate-500">=</span>
          <span className="text-slate-400">&frac12;({b1} + {b2})({h})</span>
          <span className="text-slate-500">=</span>
          <span className="text-slate-400">&frac12;({b1 + b2})({h})</span>
          <span className="text-slate-500">=</span>
          <span className="text-emerald-300 font-black text-sm">{totalArea}</span>
        </div>

        <button
          type="button"
          onClick={() => {
            setB1(initialB1);
            setB2(initialB2);
            setH(initialH);
          }}
          disabled={!isChanged}
          title="Reset trapezoid to problem default values"
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
            isChanged
              ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm"
              : "bg-[#1b2233] text-slate-500 cursor-not-allowed"
          }`}
        >
          <RotateCcw className="w-3 h-3" />
          Reset ({initialB1}, {initialB2}, {initialH})
        </button>
      </div>
    </div>
  );
};
