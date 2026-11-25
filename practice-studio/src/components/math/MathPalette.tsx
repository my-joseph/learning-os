"use client";

import React from "react";
import { MoreHorizontal, Sigma, Type } from "lucide-react";
import { Reveal } from "@/components/motion/Reveal";
import { MathKeyIcon } from "@/components/math/MathKeyIcons";
import { IconButton } from "@/components/ui/shadcn/Button";
import { SegmentedChips } from "@/components/ui/shadcn/Tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";
import type { MathInputMode, UnitKeyboardProfile } from "@/lib/mathInput";
import { getMathPaletteSections, QUICK_PALETTE_KEYS } from "@/lib/mathPalette";

const answerModes = [
  { value: "math", label: "Math input", icon: <Sigma className="size-space-3_5 shrink-0" aria-hidden="true" /> },
  { value: "plain", label: "Plain text", icon: <Type className="size-space-3_5 shrink-0" aria-hidden="true" /> },
] as const;

export interface MathPaletteProps {
  inputMode: MathInputMode;
  onModeChange: (mode: MathInputMode) => void;
  keyboardProfile: UnitKeyboardProfile;
  panelOpen: boolean;
  onTogglePanel: () => void;
  onInsertLatex: (latex: string) => void;
  disabled?: boolean;
}

/** Pure stateless view for the standalone mode/quick-keys row and quiet inline palette panel. */
export const MathPaletteView: React.FC<MathPaletteProps> = ({
  inputMode,
  onModeChange,
  keyboardProfile,
  panelOpen,
  onTogglePanel,
  onInsertLatex,
  disabled = false,
}) => {
  const isMathMode = inputMode === "math";
  const sections = getMathPaletteSections(keyboardProfile);

  return (
    <div>
      {/* Separate toolbar row below the field */}
      <div className="flex flex-wrap items-center justify-between gap-x-space-2 gap-y-space-1_5">
        <SegmentedChips
          variant="answerMode"
          label="Answer input mode"
          options={answerModes}
          value={inputMode}
          onValueChange={onModeChange}
        />

        {/* Right: quick-insert keys + expand button (hidden in Plain text mode) */}
        {isMathMode && (
          <div
            role="toolbar"
            aria-label="Quick math templates"
            className="flex items-center gap-space-1"
          >
            {/* Native title stays as SSR/no-JS fallback; TooltipTrigger strips it after hydration. */}
            {QUICK_PALETTE_KEYS.map((key) => (
              <Tooltip key={key.id}>
                <TooltipTrigger asChild>
                  <IconButton
                    size="xs"
                    tone="paletteQuick"
                    hitArea="answer"
                    disabled={disabled}
                    aria-label={key.label}
                    title={key.label}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => onInsertLatex(key.insertLatex)}
                  >
                    <MathKeyIcon
                      iconId={key.iconId}
                      className="h-icon-math-quick w-auto max-w-icon-math-quick-max shrink-0 pointer-events-none"
                    />
                  </IconButton>
                </TooltipTrigger>
                <TooltipContent>{key.label}</TooltipContent>
              </Tooltip>
            ))}

            <span
              aria-hidden="true"
              className="w-space-px h-space-4 bg-border mx-space-0_5"
            />

            <Tooltip>
              <TooltipTrigger asChild>
                <IconButton
                  size="xs"
                  tone="paletteDisclosure"
                  hitArea="answer"
                  selected={panelOpen}
                  disabled={disabled}
                  aria-label={panelOpen ? "Close math palette" : "Open math palette"}
                  aria-expanded={panelOpen}
                  aria-pressed={panelOpen}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={onTogglePanel}
                >
                  <MoreHorizontal className="size-space-4" aria-hidden="true" />
                </IconButton>
              </TooltipTrigger>
              <TooltipContent>
                {panelOpen ? "Close math palette" : "More math symbols"}
              </TooltipContent>
            </Tooltip>
          </div>
        )}
      </div>

      {/* Inline expandable full palette panel as its own quiet block */}
      <Reveal show={isMathMode && panelOpen} className="pt-space-2">
        {isMathMode && panelOpen && (
          <div
            role="region"
            aria-label="Math symbol palette"
            className="rounded-xl border border-border bg-surface-panel px-space-3 py-space-2_5 space-y-space-3"
          >
            {sections.map((section) => (
              <div key={section.id} className="space-y-space-1_5">
                <div className="text-xs font-medium text-muted">
                  {section.heading}
                </div>
                <div className="flex flex-wrap gap-space-1_5">
                  {section.keys.map((key) => (
                    <Tooltip key={key.id}>
                      <TooltipTrigger asChild>
                        <IconButton
                          size="sm"
                          tone="paletteKey"
                          hitArea="answer"
                          disabled={disabled}
                          aria-label={key.label}
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={() => onInsertLatex(key.insertLatex)}
                        >
                          <MathKeyIcon
                            iconId={key.iconId}
                            className="h-space-6 w-auto max-w-control-xs shrink-0 pointer-events-none"
                          />
                        </IconButton>
                      </TooltipTrigger>
                      <TooltipContent>{key.label}</TooltipContent>
                    </Tooltip>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </Reveal>
    </div>
  );
};

/**
 * Standalone mode-switch + quick-keys row and quiet inline math symbol palette.
 * Lives directly below the math input with tight spacing; never floats.
 */
export const MathPalette: React.FC<MathPaletteProps> = (props) => (
  <MathPaletteView {...props} />
);
