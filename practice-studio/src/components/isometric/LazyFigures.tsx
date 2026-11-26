"use client";

import React from "react";
import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/shadcn/Skeleton";
import "./isometric.css";

export function FigureSkeleton() {
  return (
    <Skeleton className="iso-figure-box w-full rounded-none bg-surface-hover dark:bg-surface-hover" aria-hidden="true" />
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
