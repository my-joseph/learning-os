"use client";

import React from "react";
import { MoreHorizontal, Sigma, Type, X } from "lucide-react";
import { Reveal } from "@/components/motion/Reveal";
import { MathKeyIcon } from "@/components/math/MathKeyIcons";
import type { MathInputMode, UnitKeyboardProfile } from "@/lib/mathInput";
import { getMathPaletteSections, QUICK_PALETTE_KEYS } from "@/lib/mathPalette";

export interface MathPaletteProps {
  inputMode: MathInputMode;
  onModeChange: (mode: MathInputMode) => void;
  keyboardProfile: UnitKeyboardProfile;
  panelOpen: boolean;
  onTogglePanel: () => void;
  onClosePanel: () => void;
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
  onClosePanel,
  onInsertLatex,
  disabled = false,
}) => {
  const isMathMode = inputMode === "math";
  const sections = getMathPaletteSections(keyboardProfile);

  return (
    <div>
      {/* Separate toolbar row below the field */}
      <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1.5">
        {/* Left: segmented mode switch */}
        <div
          role="group"
          aria-label="Answer input mode"
          className="inline-flex items-center rounded-lg bg-zinc-200/75 dark:bg-zinc-800 p-0.5"
        >
          <button
            type="button"
            onClick={() => onModeChange("math")}
            aria-pressed={inputMode === "math"}
            className={`inline-flex items-center gap-1.5 rounded-md h-7 px-2.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ${
              inputMode === "math"
                ? "bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 shadow-sm"
                : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
            }`}
          >
            <Sigma className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            <span>Math input</span>
          </button>
          <button
            type="button"
            onClick={() => onModeChange("plain")}
            aria-pressed={inputMode === "plain"}
            className={`inline-flex items-center gap-1.5 rounded-md h-7 px-2.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ${
              inputMode === "plain"
                ? "bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 shadow-sm"
                : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
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
            {QUICK_PALETTE_KEYS.map((key) => (
              <button
                key={key.id}
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
            ))}

            <span
              aria-hidden="true"
              className="w-px h-4 bg-zinc-200 dark:bg-zinc-800 mx-0.5"
            />

            <button
              type="button"
              disabled={disabled}
              aria-label={panelOpen ? "Close math palette" : "Open math palette"}
              title={panelOpen ? "Close math palette" : "More math symbols"}
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
          </div>
        )}
      </div>

      {/* Inline expandable full palette panel as its own quiet block */}
      <Reveal show={isMathMode && panelOpen} className="pt-2">
        {isMathMode && panelOpen && (
          <div
            role="region"
            aria-label="Math symbol palette"
            className="relative rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 px-3 py-2.5 space-y-3"
          >
            <button
              type="button"
              onMouseDown={(e) => e.preventDefault()}
              onClick={onClosePanel}
              aria-label="Close math palette"
              title="Close (Esc)"
              className="absolute top-2 right-2 inline-flex items-center justify-center w-7 h-7 rounded-lg text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-200/70 dark:hover:bg-zinc-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 transition-colors"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>

            {sections.map((section, sectionIdx) => (
              <div key={section.id} className="space-y-1.5">
                <div
                  className={`text-xs font-medium text-zinc-500 dark:text-zinc-400 ${
                    sectionIdx === 0 ? "pr-8" : ""
                  }`}
                >
                  {section.heading}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {section.keys.map((key) => (
                    <button
                      key={key.id}
                      type="button"
                      disabled={disabled}
                      aria-label={key.label}
                      title={key.label}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => onInsertLatex(key.insertLatex)}
                      className="inline-flex items-center justify-center w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 active:bg-indigo-50 dark:active:bg-indigo-950/60 text-zinc-700 dark:text-zinc-200 active:text-indigo-600 dark:active:text-indigo-400 transition-colors select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 disabled:opacity-40"
                    >
                      <MathKeyIcon
                        iconId={key.iconId}
                        className="h-[26px] sm:h-[30px] w-auto max-w-[30px] sm:max-w-[34px] shrink-0 pointer-events-none"
                      />
                    </button>
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
