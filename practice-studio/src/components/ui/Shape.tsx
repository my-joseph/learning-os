import React from "react";
import { cn } from "@/lib/cn";
import { signatureShapePaths, type SignatureShapeName } from "@/lib/shapes/signatureShapes";

/**
 * Small decorative accent shape (Cojeev signature contours). Always decorative:
 * keep the meaning in the text beside it. Colour comes from `currentColor`, so pass a
 * Studio token text class (e.g. statusTone.correct.text). Experiment 2026-11-26.
 */
export function Shape({ name, className }: { name: SignatureShapeName; className?: string }) {
  return (
    <svg
      viewBox="0 0 100 100"
      aria-hidden="true"
      focusable="false"
      data-slot="shape"
      data-shape={name}
      className={cn("inline-block size-space-4 shrink-0", className)}
    >
      <path d={signatureShapePaths[name]} fill="currentColor" />
    </svg>
  );
}
