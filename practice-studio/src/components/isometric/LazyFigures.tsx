"use client";

import React from "react";
import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/shadcn/Skeleton";
import "./isometric.css";

function FigureSkeleton() {
  return (
    <div className="iso-figure-box w-full p-space-4" aria-hidden="true">
      <Skeleton className="h-full w-full rounded-xl" />
    </div>
  );
}

export const LazyCube = dynamic(
  () => import("@/components/isometric/cube").then((mod) => mod.Cube),
  {
    ssr: false,
    loading: () => <FigureSkeleton />,
  }
);

export const LazyPulley = dynamic(
  () => import("@/components/isometric/pulley").then((mod) => mod.Pulley),
  {
    ssr: false,
    loading: () => <FigureSkeleton />,
  }
);

export const LazyLever = dynamic(
  () => import("@/components/isometric/lever").then((mod) => mod.Lever),
  {
    ssr: false,
    loading: () => <FigureSkeleton />,
  }
);
