import { Shape } from "@/components/ui/Shape";
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
  return (
    <ul className="mx-auto grid w-full grid-cols-4 items-center gap-space-2 p-space-4">
      {names.map((name, index) => (
        <li key={name} className="flex min-w-0 flex-col items-center gap-space-2">
          <Shape name={name} className={`aspect-square h-auto w-full max-w-20 ${colours[(index + Math.floor(index / 4)) % colours.length]}`} />
          {!preview && <span className="text-center text-xs text-foreground-secondary">{namesForDisplay[name]}</span>}
        </li>
      ))}
    </ul>
  );
}
