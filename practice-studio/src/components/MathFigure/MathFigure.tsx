"use client";

import React from "react";
import dynamic from "next/dynamic";
import { MathFigureSpec } from "@/types/figure";
import { VisualSpec } from "@/types/drill";
import { GeometryRenderer } from "./GeometryRenderer";
import { CartesianRenderer } from "./CartesianRenderer";

const VisualRenderer = dynamic(
  () => import("../VisualRenderer").then((mod) => mod.VisualRenderer),
  { ssr: true }
);

interface MathFigureProps {
  figure: MathFigureSpec | VisualSpec;
  className?: string;
}

export const MathFigure: React.FC<MathFigureProps> = ({
  figure,
  className = "",
}) => {
  if (!figure) return null;

  if ("kind" in figure) {
    return (
      <div
        className={`w-full p-4 bg-surface-panel rounded-xl border border-zinc-200 dark:border-zinc-800 flex flex-col items-center ${className}`}
      >
        {figure.title && (
          <div className="w-full flex items-center justify-start mb-2 px-1">
            <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
              {figure.title}
            </span>
          </div>
        )}

        {figure.kind === "geometry_2d" && <GeometryRenderer spec={figure} />}
        {figure.kind === "cartesian_graph" && <CartesianRenderer spec={figure} />}
        {figure.note && (
          <div className="w-full text-right px-1 mt-1 text-xs italic text-zinc-500 dark:text-zinc-400">
            {figure.note}
          </div>
        )}
      </div>
    );
  }

  return <VisualRenderer visual={figure} className={className} />;
};
