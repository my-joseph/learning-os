"use client";

import React from "react";
import { m } from "motion/react";
import { MoreHorizontal, Sigma, Type } from "lucide-react";
import { Reveal } from "@/components/motion/Reveal";
import { MathKeyIcon } from "@/components/math/MathKeyIcons";
import { settle } from "@/lib/motion";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";
import type { MathInputMode, UnitKeyboardProfile } from "@/lib/mathInput";
import { getMathPaletteSections, QUICK_PALETTE_KEYS } from "@/lib/mathPalette";

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
      <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1.5">
        {/* Left: segmented mode switch matching WorkspaceSwitch */}
        <div
          role="group"
          aria-label="Answer input mode"
          className="relative inline-grid grid-cols-2 items-center rounded-lg bg-zinc-200/70 dark:bg-surface-panel p-0.5"
        >
          <m.span
            aria-hidden="true"
            initial={false}
            animate={{ x: inputMode === "plain" ? "100%" : "0%" }}
            transition={settle}
            className="pointer-events-none absolute top-0.5 bottom-0.5 left-0.5 w-[calc(50%-2px)] rounded-md bg-white dark:bg-zinc-700/80 shadow-sm"
          />
          <button
            type="button"
            onClick={() => onModeChange("math")}
            aria-pressed={inputMode === "math"}
            className={`relative z-10 inline-flex items-center justify-center gap-1.5 rounded-md h-7 min-h-[32px] sm:min-h-0 px-2.5 text-xs font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ${
              inputMode === "math"
                ? "text-zinc-900 dark:text-zinc-100"
                : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200"
            }`}
          >
            <Sigma className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            <span>Math input</span>
          </button>
          <button
            type="button"
            onClick={() => onModeChange("plain")}
            aria-pressed={inputMode === "plain"}
            className={`relative z-10 inline-flex items-center justify-center gap-1.5 rounded-md h-7 min-h-[32px] sm:min-h-0 px-2.5 text-xs font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ${
              inputMode === "plain"
                ? "text-zinc-900 dark:text-zinc-100"
                : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200"
            }`}
          >
            <Type className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            <span>Plain text</span>
          </button>
        </div>

        {/* Right: quick-insert keys + expand button (hidden in Plain text mode) */}
        {isMathMode && (
          <div
            role="toolbar"
            aria-label="Quick math templates"
            className="flex items-center gap-1"
          >
            {/* Native title stays as SSR/no-JS fallback; TooltipTrigger strips it after hydration. */}
            {QUICK_PALETTE_KEYS.map((key) => (
              <Tooltip key={key.id}>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    disabled={disabled}
                    aria-label={key.label}
                    title={key.label}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => onInsertLatex(key.insertLatex)}
                    className="inline-flex items-center justify-center w-7 h-7 rounded-md text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 active:bg-indigo-50 dark:active:bg-indigo-950/60 active:text-indigo-600 dark:active:text-indigo-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 transition-colors disabled:opacity-40 select-none"
                  >
                    <MathKeyIcon
                      iconId={key.iconId}
                      className="h-[22px] w-auto max-w-[26px] shrink-0 pointer-events-none"
                    />
                  </button>
                </TooltipTrigger>
                <TooltipContent>{key.label}</TooltipContent>
              </Tooltip>
            ))}

            <span
              aria-hidden="true"
              className="w-px h-4 bg-zinc-200 dark:bg-zinc-800 mx-0.5"
            />

            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  disabled={disabled}
                  aria-label={panelOpen ? "Close math palette" : "Open math palette"}
                  aria-expanded={panelOpen}
                  aria-pressed={panelOpen}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={onTogglePanel}
                  className={`inline-flex items-center justify-center w-7 h-7 rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 disabled:opacity-40 ${
                    panelOpen
                      ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400"
                      : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                  }`}
                >
                  <MoreHorizontal className="w-4 h-4" aria-hidden="true" />
                </button>
              </TooltipTrigger>
              <TooltipContent>
                {panelOpen ? "Close math palette" : "More math symbols"}
              </TooltipContent>
            </Tooltip>
          </div>
        )}
      </div>

      {/* Inline expandable full palette panel as its own quiet block */}
      <Reveal show={isMathMode && panelOpen} className="pt-2">
        {isMathMode && panelOpen && (
          <div
            role="region"
            aria-label="Math symbol palette"
            className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-surface-panel px-3 py-2.5 space-y-3"
          >

            {sections.map((section) => (
              <div key={section.id} className="space-y-1.5">
                <div className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                  {section.heading}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {section.keys.map((key) => (
                    <Tooltip key={key.id}>
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          disabled={disabled}
                          aria-label={key.label}
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={() => onInsertLatex(key.insertLatex)}
                          className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-white dark:bg-zinc-700/70 border border-zinc-200 dark:border-zinc-600/70 shadow-sm hover:bg-zinc-100 dark:hover:bg-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-500 active:bg-indigo-50 dark:active:bg-indigo-950/60 text-zinc-800 dark:text-zinc-100 active:text-indigo-600 dark:active:text-indigo-400 transition-colors select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 disabled:opacity-40"
                        >
                          <MathKeyIcon
                            iconId={key.iconId}
                            className="h-[24px] w-auto max-w-[28px] shrink-0 pointer-events-none"
                          />
                        </button>
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
