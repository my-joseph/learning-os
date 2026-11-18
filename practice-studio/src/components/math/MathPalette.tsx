"use client";

import React, { useEffect, useState } from "react";
import { MoreHorizontal, Sigma, Type, X } from "lucide-react";
import { Reveal } from "@/components/motion/Reveal";
import type { MathInputMode, UnitKeyboardProfile } from "@/lib/mathInput";
import {
  getMathPaletteSections,
  isPaletteRendererReady,
  preloadPaletteRenderer,
  QUICK_PALETTE_KEYS,
  renderPaletteKeyMarkup,
} from "@/lib/mathPalette";

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

/** Pure stateless view for the attached toolbar and inline palette panel. */
export const MathPaletteView: React.FC<
  MathPaletteProps & { rendererReady?: boolean }
> = ({
  inputMode,
  onModeChange,
  keyboardProfile,
  panelOpen,
  onTogglePanel,
  onClosePanel,
  onInsertLatex,
  disabled = false,
  rendererReady = isPaletteRendererReady(),
}) => {
  const isMathMode = inputMode === "math";

  const quickMarkups = QUICK_PALETTE_KEYS.map((key) => ({
    key,
    html: rendererReady ? renderPaletteKeyMarkup(key.displayLatex) : "",
  }));

  const sections = getMathPaletteSections(keyboardProfile).map((section) => ({
    ...section,
    items: section.keys.map((key) => ({
      key,
      html: rendererReady ? renderPaletteKeyMarkup(key.displayLatex) : "",
    })),
  }));

  return (
    <div>
      {/* Attached toolbar row */}
      <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1.5 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50/80 dark:bg-zinc-900/60 px-2.5 py-1.5">
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
            className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ${
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
            className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ${
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
            {quickMarkups.map(({ key, html }) => (
              <button
                key={key.id}
                type="button"
                disabled={disabled}
                aria-label={key.label}
                title={key.label}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => onInsertLatex(key.insertLatex)}
                className="studio-palette-key studio-palette-key--sm inline-flex items-center justify-center min-w-[30px] h-7 px-1.5 rounded-md text-zinc-700 dark:text-zinc-200 hover:bg-zinc-200/80 dark:hover:bg-zinc-800 active:bg-zinc-300/70 dark:active:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 transition-colors disabled:opacity-40 select-none"
              >
                {html ? (
                  <span
                    aria-hidden="true"
                    className="pointer-events-none leading-none"
                    dangerouslySetInnerHTML={{ __html: html }}
                  />
                ) : (
                  <span aria-hidden="true" className="w-3 h-3 rounded-sm bg-zinc-200 dark:bg-zinc-700" />
                )}
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
                  : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-200/80 dark:hover:bg-zinc-800"
              }`}
            >
              <MoreHorizontal className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>

      {/* Inline expandable full palette panel */}
      <Reveal show={isMathMode && panelOpen}>
        {isMathMode && panelOpen && (
          <div
            role="region"
            aria-label="Math symbol palette"
            className="relative border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/40 px-3 py-2.5 space-y-3"
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
                  className={`text-[11px] font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400 ${
                    sectionIdx === 0 ? "pr-8" : ""
                  }`}
                >
                  {section.heading}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {section.items.map(({ key, html }) => (
                    <button
                      key={key.id}
                      type="button"
                      disabled={disabled}
                      aria-label={key.label}
                      title={key.label}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => onInsertLatex(key.insertLatex)}
                      className={`studio-palette-key inline-flex items-center justify-center min-w-[40px] h-10 ${
                        key.wide ? "px-2.5" : "px-1.5"
                      } rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 active:bg-zinc-300/70 dark:active:bg-zinc-600 text-zinc-900 dark:text-zinc-100 transition-colors select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 disabled:opacity-40`}
                    >
                      {html ? (
                        <span
                          aria-hidden="true"
                          className="pointer-events-none leading-none"
                          dangerouslySetInnerHTML={{ __html: html }}
                        />
                      ) : (
                        <span aria-hidden="true" className="w-4 h-4 rounded-sm bg-zinc-200 dark:bg-zinc-700" />
                      )}
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
 * Attached Wolfram|Alpha-style toolbar + inline math symbol palette.
 * Lives directly below the math input inside the same outer card; never floats.
 */
export const MathPalette: React.FC<MathPaletteProps> = (props) => {
  const [rendererReady, setRendererReady] = useState(() => isPaletteRendererReady());

  useEffect(() => {
    if (rendererReady) return;
    let active = true;
    void preloadPaletteRenderer().then((fn) => {
      if (active && fn) {
        setRendererReady(true);
      }
    });
    return () => {
      active = false;
    };
  }, [rendererReady]);

  return <MathPaletteView {...props} rendererReady={rendererReady} />;
};
