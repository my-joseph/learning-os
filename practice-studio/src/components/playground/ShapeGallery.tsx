"use client";

import { useEffect, useRef } from "react";
import { Shape } from "@/components/ui/Shape";
import { showcaseSpring, step } from "@/lib/isometric/motion";
import { easeInOut } from "@/lib/isometric/showcase";
import { showcaseLoop } from "@/lib/isometric/showcaseStage";
import { signatureShapePaths, type SignatureShapeName } from "@/lib/shapes/signatureShapes";

const names = Object.keys(signatureShapePaths) as SignatureShapeName[];
const namesForDisplay: Record<SignatureShapeName, string> = {
  "daisy-12": "Daisy",
  "petal-7": "Petal",
  "aster-9": "Aster",
  "sunburst-24": "Sunburst",
  "clover-soft": "Clover",
  "cloud-3": "Cloud",
  "pebble-soft": "Soft pebble",
  "pebble-tall": "Tall pebble",
  "ribbon-soft": "Ribbon",
  "scalloped-square": "Scalloped square",
  cushion: "Cushion",
  "seed-wing": "Seed wing",
};
const colours = ["text-accent", "text-foreground-subtle", "text-muted", "text-accent/65"];

export function ShapeGallery({ preview = false }: { preview?: boolean }) {
  const gallery = useRef<HTMLUListElement>(null);

  useEffect(() => {
    const stage = gallery.current!;
    const paths = stage.querySelectorAll<SVGPathElement>("[data-slot=shape] path");
    const breath = showcaseSpring(0, 0.003);
    let active = 0;
    const loop = showcaseLoop(stage, (dt) => {
      const moving = step(breath, dt);
      const path = paths[active];
      if (breath.x === 0) path.removeAttribute("transform");
      else path.setAttribute("transform", `translate(50 50) rotate(${3 * breath.x}) scale(${1 + 0.07 * breath.x}) translate(-50 -50)`);
      return moving;
    }, {
      defaults() { breath.to = 0; },
      play(seconds) {
        const slot = 1.1;
        const index = Math.floor(seconds / slot) % paths.length;
        const t = seconds % slot;
        const target = easeInOut(t / 0.37) * easeInOut((0.87 - t) / 0.45);
        const changed = active !== index || breath.to !== target;
        if (active !== index) {
          paths[active].removeAttribute("transform");
          active = index;
        }
        breath.to = target;
        return changed;
      },
    });
    return loop.stop;
  }, []);

  return (
    <ul
      ref={gallery}
      tabIndex={preview ? undefined : 0}
      aria-label={preview ? undefined : "Signature shape gallery"}
      className="mx-auto grid w-full grid-cols-4 items-center gap-space-2 rounded-lg p-space-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">
      {names.map((name, index) => (
        <li key={name} className="flex min-w-0 flex-col items-center gap-space-2">
          <Shape name={name} className={`aspect-square h-auto w-full max-w-20 ${colours[(index + Math.floor(index / 4)) % colours.length]}`} />
          {!preview && <span className="text-center text-xs text-foreground-secondary">{namesForDisplay[name]}</span>}
        </li>
      ))}
    </ul>
  );
}
