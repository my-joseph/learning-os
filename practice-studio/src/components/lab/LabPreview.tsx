"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { FigureSkeleton, LazyCube, LazyLever, LazyPulley } from "@/components/isometric/LazyFigures";
import { LazyDiskMethod } from "@/components/isometric/LazyDiskMethod";
import type { LabExperimentId } from "./experiments";

const LazyShapes = dynamic(
  () => import("./ShapeGallery").then((module) => module.ShapeGallery),
  { ssr: false, loading: FigureSkeleton },
);
const LazyComponents = dynamic(
  () => import("@/components/ui-poc/ShadcnPocShowcase").then((module) => module.ShadcnPocPreview),
  { ssr: false, loading: FigureSkeleton },
);

const previews = {
  lever: <LazyLever className="w-full" />,
  pulley: <LazyPulley className="w-full" />,
  "disk-method": <LazyDiskMethod />,
  cube: <LazyCube className="w-full" />,
  shapes: <LazyShapes preview />,
  "ui-components": <LazyComponents />,
} satisfies Record<LabExperimentId, React.ReactNode>;

export function LabPreview({ id }: { id: LabExperimentId }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const preview = ref.current;
    if (!preview) return;
    preview.inert = true;
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setVisible(true);
        observer.disconnect();
      }
    });
    observer.observe(preview);
    return () => observer.disconnect();
  }, []);

  // The same live figures are interactive on their detail pages. The card has one link and tab stop.
  return (
    <div ref={ref} aria-hidden="true" className="iso-studio-surface pointer-events-none flex h-full w-full items-center justify-center">
      {visible ? previews[id] : <FigureSkeleton />}
    </div>
  );
}
