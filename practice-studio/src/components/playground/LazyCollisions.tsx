"use client";

import dynamic from "next/dynamic";
import { FigureSkeleton } from "@/components/isometric/LazyFigures";

export const LazyCollisions = dynamic(
  () => import("./Collisions").then((module) => module.CollisionsPreview),
  {
    ssr: false,
    loading: () => <FigureSkeleton />,
  },
);

export const LazyCollisionsShowcase = dynamic(
  () => import("./CollisionsShowcase").then((module) => module.CollisionsShowcase),
  { ssr: false, loading: FigureSkeleton },
);
