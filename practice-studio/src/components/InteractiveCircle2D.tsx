"use client";

import React, { useState, useRef, useCallback } from "react";
import { RotateCcw, Sparkles } from "lucide-react";

interface InteractiveCircle2DProps {
  initialR?: number;
}

export const InteractiveCircle2D: React.FC<InteractiveCircle2DProps> = ({
  initialR = 4,
}) => {
  const [r, setR] = useState(initialR);
  const [angleDeg, setAngleDeg] = useState(0); // Can spin / rotate r around 360 deg!
  const [hovered, setHovered] = useState<string | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const isDraggingRef = useRef(false);

  // Dynamic scale factor based on initial radius
  const scale = Math.min(22, Math.max(10, Math.floor(84 / Math.max(initialR, 5))));

  // SVG Center in 380 x 240 canvas
  const cx = 190;
  const cy = 120;

  const rPx = r * scale;
  const rad = (angleDeg * Math.PI) / 180;
  const hx = cx + rPx * Math.cos(rad);
  const hy = cy + rPx * Math.sin(rad);

  const rSq = r * r;
  const diameter = 2 * r;
  const approxArea = Math.round(Math.PI * rSq * 10) / 10;
  const approxCirc = Math.round(2 * Math.PI * r * 10) / 10;

  // Sector path if angle > 0
  const normalizedAngle = ((angleDeg % 360) + 360) % 360;
  const largeArcFlag = normalizedAngle > 180 ? 1 : 0;
  const sectorPath =
    normalizedAngle > 2
      ? `M ${cx} ${cy} L ${cx + rPx} ${cy} A ${rPx} ${rPx} 0 ${largeArcFlag} 1 ${hx} ${hy} Z`
      : "";

  // Pointer drag to spin angle AND adjust radius distance
  const handlePointerDown = (e: React.PointerEvent) => {
    e.preventDefault();
    e.stopPropagation();
    isDraggingRef.current = true;
    (e.currentTarget as Element).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!isDraggingRef.current || !svgRef.current) return;
      const pt = svgRef.current.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;
      const ctm = svgRef.current.getScreenCTM();
      if (!ctm) return;
      const svgP = pt.matrixTransform(ctm.inverse());

      const dx = svgP.x - cx;
      const dy = svgP.y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);

      // Clamped radius
      const rawR = dist / scale;
      const clampedR = Math.max(2, Math.min(10, Math.round(rawR)));
      setR(clampedR);

      // Angle calculation in degrees
      let deg = Math.round((Math.atan2(dy, dx) * 180) / Math.PI);
      if (deg < 0) deg += 360;
      setAngleDeg(deg);
    },
    [cx, cy, scale]
  );

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (isDraggingRef.current) {
      try {
        (e.currentTarget as Element).releasePointerCapture(e.pointerId);
      } catch {
        // capture release fallback
      }
      isDraggingRef.current = false;
    }
  }, []);

  const isChanged = r !== initialR || angleDeg !== 0;

  return (
    <div className="flex flex-col items-center w-full select-none">
      {/* SVG Interactive Canvas */}
      <div className="relative w-full bg-[#0a0d14] rounded-xl border border-[#232a3d] p-2 flex flex-col justify-center items-center overflow-hidden">
        
        {/* Dynamic Tooltip / Parameter Inspector Bar */}
        <div className="w-full mb-1.5 px-3 py-1.5 bg-[#121724]/90 backdrop-blur border border-sky-500/25 rounded-lg text-xs flex justify-between items-center transition-all min-h-[36px]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-sky-400 shrink-0" />
            <span className="text-slate-200">
              {hovered === "disk" ? (
                <span>
                  <strong className="text-sky-300">Circle Surface:</strong> Area A = &pi;r&sup2; = &pi;({r})&sup2; = <strong className="text-sky-300">{rSq}&pi;</strong> &approx; {approxArea}
                </span>
              ) : hovered === "circ" ? (
                <span>
                  <strong className="text-amber-300">Circumference C = 2&pi;r:</strong> 2&pi;({r}) = <strong className="text-amber-300">{diameter}&pi;</strong> &approx; {approxCirc}
                </span>
              ) : hovered === "radius" || hovered === "handle" ? (
                <span>
                  <strong className="text-sky-300">Radius r = {r}</strong> (Angle &theta; = {angleDeg}&deg;) &mdash; <span className="text-slate-400">Drag to resize or spin around center</span>
                </span>
              ) : hovered === "diameter" ? (
                <span>
                  <strong className="text-indigo-300">Diameter d = 2r = {diameter}</strong> (Full width across center)
                </span>
              ) : hovered === "sector" ? (
                <span>
                  <strong className="text-teal-300">Swept Sector:</strong> &theta; = {angleDeg}&deg;, Sector Area = ({angleDeg}&deg;/360&deg;) &times; {rSq}&pi; &approx; {Math.round((angleDeg / 360) * approxArea * 10) / 10}
                </span>
              ) : hovered === "center" ? (
                <span>
                  <strong className="text-slate-300">Center Origin (O):</strong> Radius lines radiate outward from here
                </span>
              ) : (
                <span className="text-slate-400">
                  Drag the <span className="text-sky-300 font-semibold">cyan handle</span> to spin &theta; or change radius <span className="text-sky-300 font-semibold">r</span>. Hover components to inspect formulas.
                </span>
              )}
            </span>
          </div>
          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-950/70 text-sky-300 border border-sky-800/50 shrink-0 hidden sm:inline-block">
            2D Interactive
          </span>
        </div>

        <svg
          ref={svgRef}
          viewBox="0 0 380 240"
          className="w-full max-w-[400px] h-auto overflow-visible touch-none cursor-default"
          style={{ maxHeight: "240px" }}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
        >
          <defs>
            <filter id="glow-circ" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Concentric Radar / Rings (Subtle) */}
          <g stroke="#161c2b" strokeWidth="0.8">
            <line x1={cx - 150} y1={cy} x2={cx + 150} y2={cy} strokeDasharray="2 3" />
            <line x1={cx} y1={cy - 100} x2={cx} y2={cy + 100} strokeDasharray="2 3" />
          </g>

          {/* Swept Sector Arc (if rotated) */}
          {sectorPath && (
            <path
              d={sectorPath}
              fill="rgba(56, 189, 248, 0.16)"
              stroke="#38bdf8"
              strokeWidth={1}
              strokeDasharray="2 2"
              className="cursor-pointer transition-colors"
              onPointerOver={() => setHovered("sector")}
              onPointerOut={() => setHovered(null)}
            />
          )}

          {/* Main Circle Disk Fill (Hoverable Surface) */}
          <circle
            cx={cx}
            cy={cy}
            r={rPx}
            fill={hovered === "disk" ? "rgba(56, 189, 248, 0.18)" : "rgba(56, 189, 248, 0.08)"}
            className="cursor-pointer transition-colors"
            onPointerOver={() => setHovered("disk")}
            onPointerOut={() => setHovered(null)}
          />

          {/* Circumference Ring (Hoverable Perimeter) */}
          <circle
            cx={cx}
            cy={cy}
            r={rPx}
            fill="none"
            stroke={hovered === "circ" ? "#fbbf24" : "#38bdf8"}
            strokeWidth={hovered === "circ" ? 3.5 : 2}
            filter={hovered === "circ" ? "url(#glow-circ)" : undefined}
            className="cursor-pointer transition-colors"
            onPointerOver={() => setHovered("circ")}
            onPointerOut={() => setHovered(null)}
          />

          {/* Dashed Full Diameter Projection (Hoverable) */}
          <g
            onPointerOver={() => setHovered("diameter")}
            onPointerOut={() => setHovered(null)}
            className="cursor-pointer"
          >
            <line
              x1={cx - rPx}
              y1={cy}
              x2={cx + rPx}
              y2={cy}
              stroke={hovered === "diameter" ? "#818cf8" : "#2d3748"}
              strokeWidth={hovered === "diameter" ? 2.5 : 1.2}
              strokeDasharray="3 3"
              filter={hovered === "diameter" ? "url(#glow-circ)" : undefined}
            />
          </g>

          {/* Dynamic Radius Line (Spin & Drag) */}
          <g
            onPointerOver={() => setHovered("radius")}
            onPointerOut={() => setHovered(null)}
            onPointerDown={handlePointerDown}
            className="cursor-pointer"
          >
            {/* Invisible thick hit target */}
            <line x1={cx} y1={cy} x2={hx} y2={hy} stroke="transparent" strokeWidth={24} />
            {/* Visible line */}
            <line
              x1={cx}
              y1={cy}
              x2={hx}
              y2={hy}
              stroke={hovered === "radius" || hovered === "handle" ? "#38bdf8" : "#0284c7"}
              strokeWidth={hovered === "radius" || hovered === "handle" ? 4.5 : 3}
              filter={hovered === "radius" || hovered === "handle" ? "url(#glow-circ)" : undefined}
            />
          </g>

          {/* Radius Dimension Text positioned alongside line */}
          <text
            x={cx + (rPx * 0.5) * Math.cos(rad) - 10 * Math.sin(rad)}
            y={cy + (rPx * 0.5) * Math.sin(rad) + 10 * Math.cos(rad)}
            textAnchor="middle"
            dominantBaseline="central"
            className={`font-mono text-xs font-bold pointer-events-none transition-all ${
              hovered === "radius" || hovered === "handle" ? "fill-sky-300 font-extrabold text-sm" : "fill-sky-400"
            }`}
          >
            r = {r}
          </text>

          {/* Center Point Marker */}
          <g
            onPointerOver={() => setHovered("center")}
            onPointerOut={() => setHovered(null)}
            className="cursor-pointer"
          >
            <circle cx={cx} cy={cy} r={4} fill="#e2e8f0" stroke="#0f172a" strokeWidth={1.5} />
            <text x={cx - 10} y={cy - 8} className="fill-slate-400 font-mono text-[10px] pointer-events-none">
              O
            </text>
          </g>

          {/* Draggable & Rotatable Handle at Radius End */}
          <g
            onPointerDown={handlePointerDown}
            className="cursor-grab active:cursor-grabbing"
            onPointerOver={() => setHovered("handle")}
            onPointerOut={() => setHovered(null)}
          >
            <circle cx={hx} cy={hy} r={20} fill="transparent" />
            <circle
              cx={hx}
              cy={hy}
              r={hovered === "handle" ? 9 : 7.5}
              fill="#38bdf8"
              stroke="#ffffff"
              strokeWidth={2}
              className="transition-all filter drop-shadow-[0_0_8px_rgba(56,189,248,0.9)]"
            />
            {/* Rotation Arrow Halo on hover */}
            {hovered === "handle" && (
              <circle
                cx={hx}
                cy={hy}
                r={13}
                fill="none"
                stroke="#38bdf8"
                strokeWidth={1.2}
                strokeDasharray="3 3"
                className="animate-spin"
              />
            )}
          </g>
        </svg>
      </div>

      {/* Live Telemetry & Equation Proof Bar */}
      <div className="w-full mt-2 p-2.5 bg-[#121622] border border-[#232a3d] rounded-xl flex flex-wrap justify-between items-center gap-2 font-mono text-xs">
        <div className="flex items-center gap-2.5">
          <span className="text-slate-400">Exact Area:</span>
          <span className="text-sky-300 font-black text-sm">A = {rSq}&pi;</span>
          <span className="text-slate-500">(&approx; {approxArea})</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">Circumference:</span>
          <span className="text-amber-300 font-bold">{diameter}&pi;</span>
          <span className="text-slate-500">(&approx; {approxCirc})</span>
        </div>

        <button
          type="button"
          onClick={() => {
            setR(initialR);
            setAngleDeg(0);
          }}
          disabled={!isChanged}
          title="Reset circle to problem default values"
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
            isChanged
              ? "bg-sky-600 hover:bg-sky-500 text-white shadow-sm"
              : "bg-[#1b2233] text-slate-500 cursor-not-allowed"
          }`}
        >
          <RotateCcw className="w-3 h-3" />
          Reset (r={initialR})
        </button>
      </div>
    </div>
  );
};
