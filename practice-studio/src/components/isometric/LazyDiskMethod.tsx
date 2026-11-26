"use client";

import dynamic from "next/dynamic";
import { FigureSkeleton } from "./LazyFigures";

export const LazyDiskMethod = dynamic(
  () => import("@/components/isometric/disk-method").then((mod) => mod.DiskMethod),
  {
    ssr: false,
    loading: FigureSkeleton,
  },
);
