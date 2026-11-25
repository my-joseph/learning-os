import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      spacing: [(value: string) => /^(space-|control-)/.test(value) || value === "touch"],
    },
    classGroups: {
      z: ["z-base", "z-local", "z-sticky", "z-overlay", "z-overlay-menu", "z-tooltip"],
      shadow: ["shadow-ui-none", "shadow-ui-sm", "shadow-ui-md", "shadow-ui-lg", "shadow-ui-xl", "shadow-ui-inner"],
      "max-w": ["max-w-search", "max-w-practice"],
      "max-h": ["max-h-search"],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
