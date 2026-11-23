"use client";

import React, { useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Text } from "@react-three/drei";
import * as THREE from "three";
import { RotateCcw, Info, Eye } from "lucide-react";

interface Interactive3DCylinderProps {
  initialRadius?: number;
  initialHeight?: number;
}

export const Interactive3DCylinder: React.FC<Interactive3DCylinderProps> = ({
  initialRadius = 3,
  initialHeight = 8,
}) => {
  const [r, setR] = useState(initialRadius);
  const [h, setH] = useState(initialHeight);
  const [hoveredPart, setHoveredPart] = useState<string | null>(null);

  const baseArea = Math.round(Math.PI * r * r * 100) / 100;
  const lateralArea = Math.round(2 * Math.PI * r * h * 100) / 100;
  const totalSurfaceArea = Math.round((2 * baseArea + lateralArea) * 100) / 100;
  const volume = Math.round(Math.PI * r * r * h * 100) / 100;

  // Visual scaling to fit canvas view
  const scale = 0.35;
  const visualR = r * scale;
  const visualH = h * scale;

  return (
    <div className="flex flex-col items-center w-full my-2">
      {/* 3D WebGL Canvas */}
      <div className="relative w-full h-[280px] bg-surface-panel rounded-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden shadow-inner">
        <Canvas camera={{ position: [5, 4, 6], fov: 45 }}>
          {/* Ambient & Directional Lights */}
          <ambientLight intensity={0.7} />
          <directionalLight position={[10, 10, 5]} intensity={1.2} />
          <pointLight position={[-10, -10, -5]} intensity={0.5} />

          {/* Interactive 3D Cylinder Mesh Group */}
          <group position={[0, 0, 0]}>
            {/* Top Base Disc */}
            <mesh
              position={[0, visualH / 2, 0]}
              rotation={[-Math.PI / 2, 0, 0]}
              onPointerOver={(e) => {
                e.stopPropagation();
                setHoveredPart("top");
              }}
              onPointerOut={(e) => {
                e.stopPropagation();
                setHoveredPart(null);
              }}
            >
              <circleGeometry args={[visualR, 32]} />
              <meshStandardMaterial
                color={hoveredPart === "top" ? "#818cf8" : "#4f46e5"}
                emissive={hoveredPart === "top" ? "#3730a3" : "#000000"}
                roughness={0.3}
                metalness={0.2}
                side={THREE.DoubleSide}
              />
            </mesh>

            {/* Bottom Base Disc */}
            <mesh
              position={[0, -visualH / 2, 0]}
              rotation={[Math.PI / 2, 0, 0]}
              onPointerOver={(e) => {
                e.stopPropagation();
                setHoveredPart("bottom");
              }}
              onPointerOut={(e) => {
                e.stopPropagation();
                setHoveredPart(null);
              }}
            >
              <circleGeometry args={[visualR, 32]} />
              <meshStandardMaterial
                color={hoveredPart === "bottom" ? "#818cf8" : "#4f46e5"}
                emissive={hoveredPart === "bottom" ? "#3730a3" : "#000000"}
                roughness={0.3}
                metalness={0.2}
                side={THREE.DoubleSide}
              />
            </mesh>

            {/* Curved Lateral Surface */}
            <mesh
              position={[0, 0, 0]}
              onPointerOver={(e) => {
                e.stopPropagation();
                setHoveredPart("lateral");
              }}
              onPointerOut={(e) => {
                e.stopPropagation();
                setHoveredPart(null);
              }}
            >
              <cylinderGeometry args={[visualR, visualR, visualH, 32, 1, true]} />
              <meshStandardMaterial
                color={hoveredPart === "lateral" ? "#818cf8" : "#4f46e5"}
                emissive={hoveredPart === "lateral" ? "#3730a3" : "#000000"}
                transparent
                opacity={0.75}
                roughness={0.2}
                metalness={0.3}
                side={THREE.DoubleSide}
              />
            </mesh>

            {/* Wireframe Outline Rings */}
            <lineSegments position={[0, visualH / 2, 0]} rotation={[-Math.PI / 2, 0, 0]}>
              <ringGeometry args={[visualR - 0.02, visualR, 32]} />
              <meshBasicMaterial color="#a5b4fc" />
            </lineSegments>
            <lineSegments position={[0, -visualH / 2, 0]} rotation={[Math.PI / 2, 0, 0]}>
              <ringGeometry args={[visualR - 0.02, visualR, 32]} />
              <meshBasicMaterial color="#a5b4fc" />
            </lineSegments>

            {/* In-scene 3D Height Guide Line & Text */}
            <group position={[visualR + 0.5, 0, 0]}>
              <mesh position={[0, 0, 0]}>
                <boxGeometry args={[0.04, visualH, 0.04]} />
                <meshBasicMaterial color={hoveredPart === "height" ? "#d97706" : "#a1a1aa"} />
              </mesh>
              <Text
                position={[0.5, 0, 0]}
                fontSize={0.35}
                color={hoveredPart === "height" ? "#d97706" : "#d4d4d8"}
                anchorX="left"
                anchorY="middle"
              >
                {`h = ${h}`}
              </Text>
            </group>

            {/* In-scene Radius Line & Text */}
            <group position={[0, visualH / 2 + 0.02, 0]}>
              <mesh position={[visualR / 2, 0, 0]}>
                <boxGeometry args={[visualR, 0.04, 0.04]} />
                <meshBasicMaterial color="#d97706" />
              </mesh>
              <Text
                position={[visualR / 2, 0.35, 0]}
                fontSize={0.32}
                color="#fbbf24"
                anchorX="center"
                anchorY="bottom"
              >
                {`r = ${r}`}
              </Text>
            </group>
          </group>

          {/* Smooth 360 Orbit Controls */}
          <OrbitControls
            enablePan={false}
            minDistance={4}
            maxDistance={12}
            enableDamping
            dampingFactor={0.08}
          />
        </Canvas>

        {/* Orbit hint overlay */}
        <div className="absolute top-2.5 right-2.5 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white dark:bg-zinc-900 backdrop-blur border border-zinc-200 dark:border-zinc-800 text-[11px] text-zinc-700 dark:text-zinc-300 pointer-events-none">
          <Eye className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
          Click &amp; Drag to rotate 360°
        </div>

        {/* Hover Inspector Tooltip */}
        <div className="absolute bottom-2.5 left-2.5 right-2.5 bg-zinc-950/85 backdrop-blur border border-indigo-500/40 rounded-xl p-2.5 text-xs flex items-center justify-between pointer-events-none transition-all">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-indigo-600 dark:text-indigo-400 flex-shrink-0" />
            <div>
              {hoveredPart === "top" || hoveredPart === "bottom" ? (
                <span>
                  <strong className="text-indigo-600 dark:text-indigo-400">Base Circle (A = πr²):</strong>{" "}
                  π × {r}² = <span className="text-white font-mono">{r * r}π ≈ {baseArea}</span>
                </span>
              ) : hoveredPart === "lateral" ? (
                <span>
                  <strong className="text-indigo-600 dark:text-indigo-400">Lateral Surface (Unfolded Rectangle = 2πrh):</strong>{" "}
                  2π × {r} × {h} = <span className="text-white font-mono">{2 * r * h}π ≈ {lateralArea}</span>
                </span>
              ) : (
                <span className="text-zinc-500 dark:text-zinc-400">
                  Hover over the circular bases or curved surface to inspect formulas and parameters.
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Dynamic Sliders Bar */}
      <div className="w-full mt-3 p-3 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl space-y-2.5 text-xs">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          <label className="flex flex-col gap-1">
            <div className="flex justify-between items-center">
              <span className="text-zinc-700 dark:text-zinc-300">
                Radius <strong className="text-amber-700 dark:text-amber-400 font-mono">r = {r}</strong>
              </span>
              <span className="text-zinc-500 dark:text-zinc-400 font-mono">Base Area = {r * r}π</span>
            </div>
            <input
              type="range"
              min={1}
              max={6}
              step={0.5}
              value={r}
              onChange={(e) => setR(Number(e.target.value))}
              className="accent-amber-400 cursor-pointer"
            />
          </label>

          <label className="flex flex-col gap-1">
            <div className="flex justify-between items-center">
              <span className="text-zinc-700 dark:text-zinc-300">
                Height <strong className="text-emerald-700 dark:text-emerald-400 font-mono">h = {h}</strong>
              </span>
              <span className="text-zinc-500 dark:text-zinc-400 font-mono">Lateral Area = {2 * r * h}π</span>
            </div>
            <input
              type="range"
              min={2}
              max={14}
              step={0.5}
              value={h}
              onChange={(e) => setH(Number(e.target.value))}
              className="accent-emerald-400 cursor-pointer"
            />
          </label>
        </div>

        {/* Real-Time Parameter Telemetry */}
        <div className="pt-2 border-t border-zinc-200 dark:border-zinc-800 flex flex-wrap justify-between items-center gap-2 text-center font-mono">
          <div className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 rounded-lg">
            <span className="text-zinc-500 dark:text-zinc-400">Volume V = πr²h: </span>
            <span className="text-indigo-600 dark:text-indigo-400 font-bold">{r * r * h}π ≈ {volume}</span>
          </div>
          <div className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 rounded-lg">
            <span className="text-zinc-500 dark:text-zinc-400">Total Surface Area: </span>
            <span className="text-indigo-600 dark:text-indigo-400 font-bold">{2 * r * r + 2 * r * h}π ≈ {totalSurfaceArea}</span>
          </div>
          <button
            type="button"
            onClick={() => {
              setR(initialRadius);
              setH(initialHeight);
            }}
            title="Reset to problem values"
            className="flex items-center gap-1 px-2 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
        </div>
      </div>
    </div>
  );
};
