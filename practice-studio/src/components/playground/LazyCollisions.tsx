"use client";

import dynamic from "next/dynamic";
import { FigureSkeleton } from "@/components/isometric/LazyFigures";

export const LazyCollisions = dynamic(
  () => import("./Collisions").then((module) => module.Collisions),
  {
    ssr: false,
    loading: () => <FigureSkeleton />,
  },
);
