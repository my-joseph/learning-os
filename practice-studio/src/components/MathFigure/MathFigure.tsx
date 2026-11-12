"use client";

import React from "react";
import { MathFigureSpec } from "@/types/figure";
import { VisualSpec } from "@/types/drill";
import { GeometryRenderer } from "./GeometryRenderer";
import { CartesianRenderer } from "./CartesianRenderer";
import { VisualRenderer } from "../VisualRenderer";

interface MathFigureProps {
  figure: MathFigureSpec | VisualSpec;
  className?: string;
}

export const MathFigure: React.FC<MathFigureProps> = ({
  figure,
  className = "",
}) => {
  if (!figure) return null;

  // Check if it's the new Semantic Spec (has 'kind')
  if ("kind" in figure) {
    return (
      <div
        className={`my-3 p-3.5 bg-slate-50/80 dark:bg-[#0d121c] rounded-2xl border border-slate-200/80 dark:border-[#222a3d] transition-all flex flex-col items-center shadow-xs ${className}`}
      >
        {figure.title && (
          <div className="w-full flex items-center justify-start mb-2 px-1">
            <span className="text-[11px] font-semibold tracking-wide text-slate-500 dark:text-slate-400 uppercase">
              {figure.title}
            </span>
          </div>
        )}

        {figure.kind === "geometry_2d" && <GeometryRenderer spec={figure} />}
        {figure.kind === "cartesian_graph" && <CartesianRenderer spec={figure} />}
      </div>
    );
  }

  // Fallback to legacy VisualRenderer if it's the old VisualSpec
  return <VisualRenderer visual={figure} className={className} />;
};
