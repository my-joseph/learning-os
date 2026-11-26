"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import { FigureSkeleton, LazyCube, LazyLever, LazyPulley } from "@/components/isometric/LazyFigures";
import { LazyDiskMethod } from "@/components/isometric/LazyDiskMethod";
import type { CollisionSimSnapshot } from "./Collisions";
import { LazyCollisions } from "./LazyCollisions";
import { PlaygroundCard } from "./PlaygroundCard";
import type { PlaygroundExperiment, PlaygroundExperimentId } from "./experiments";

const LazyShapes = dynamic(
  () => import("./ShapeGallery").then((module) => module.ShapeGallery),
  { ssr: false, loading: FigureSkeleton },
);
const LazyComponents = dynamic(
  () => import("@/components/ui-poc/ShadcnPocShowcase").then((module) => module.ShadcnPocPreview),
  { ssr: false, loading: FigureSkeleton },
);

const staticPreviews = {
  lever: <LazyLever className="w-full" />,
  pulley: <LazyPulley className="w-full" />,
  "disk-method": <LazyDiskMethod />,
  cube: <LazyCube className="w-full" />,
  shapes: <LazyShapes preview />,
  "ui-components": <LazyComponents />,
} satisfies Record<Exclude<PlaygroundExperimentId, "collisions">, React.ReactNode>;

function formatCollisionsCardCaption(snapshot: CollisionSimSnapshot): string {
  if (snapshot.phase === "running") return "Momentum · running";
  if (snapshot.phase === "paused") return "Momentum · paused";
  if (snapshot.phase === "done") return "Momentum · after impact";
  return "Momentum · elastic";
}

export function PlaygroundPreview({
  id,
  onCollisionsSnapshot,
}: {
  id: PlaygroundExperimentId;
  onCollisionsSnapshot?: (snapshot: CollisionSimSnapshot) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const preview = ref.current;
    if (!preview) return;
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

  const previewNode =
    id === "collisions" ? (
      <LazyCollisions interactive="card" onSnapshot={onCollisionsSnapshot} />
    ) : (
      staticPreviews[id]
    );

  // Live and interactive in the grid; the detail page adds the full readout.
  return (
    <div ref={ref} className="iso-studio-surface flex h-full w-full items-center justify-center">
      {visible ? previewNode : <FigureSkeleton />}
    </div>
  );
}

export function PlaygroundExperimentCard({ experiment }: { experiment: PlaygroundExperiment }) {
  const [collisionsCaption, setCollisionsCaption] = useState<string>(experiment.caption);

  const handleCollisionsSnapshot = useCallback((snapshot: CollisionSimSnapshot) => {
    setCollisionsCaption(formatCollisionsCardCaption(snapshot));
  }, []);

  return (
    <PlaygroundCard
      experiment={experiment}
      caption={experiment.id === "collisions" ? collisionsCaption : undefined}
    >
      <PlaygroundPreview
        id={experiment.id}
        onCollisionsSnapshot={experiment.id === "collisions" ? handleCollisionsSnapshot : undefined}
      />
    </PlaygroundCard>
  );
}
