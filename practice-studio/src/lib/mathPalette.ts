import type { UnitKeyboardProfile } from "./mathInput";

type ConvertLatexToMarkupFn = (latex: string) => string;

let loadedConvertToMarkup: ConvertLatexToMarkupFn | null = null;
let loadPromise: Promise<ConvertLatexToMarkupFn | null> | null = null;

export interface MathPaletteKey {
  id: string;
  label: string;
  displayLatex: string;
  insertLatex: string;
  wide?: boolean;
}

export interface MathPaletteSection {
  id: "basic" | "functions" | "symbols";
  heading: string;
  keys: readonly MathPaletteKey[];
}

export interface MathFieldInsertTarget {
  executeCommand?: (
    command: ["insert", string, { selectionMode: "placeholder"; focus: boolean }]
  ) => unknown;
  focus?: () => void;
}

/** Most-used math templates shown in the compact toolbar row. */
export const QUICK_PALETTE_KEYS: readonly MathPaletteKey[] = [
  {
    id: "quick-frac",
    label: "Fraction",
    displayLatex: "\\frac{\\placeholder{}}{\\placeholder{}}",
    insertLatex: "\\frac{#@}{#?}",
  },
  {
    id: "quick-power",
    label: "Exponent / power",
    displayLatex: "\\placeholder{}^{\\placeholder{}}",
    insertLatex: "#@^{#?}",
  },
  {
    id: "quick-sqrt",
    label: "Square root",
    displayLatex: "\\sqrt{\\placeholder{}}",
    insertLatex: "\\sqrt{#0}",
  },
  {
    id: "quick-abs",
    label: "Absolute value",
    displayLatex: "\\left|\\placeholder{}\\right|",
    insertLatex: "\\left|#0\\right|",
  },
  {
    id: "quick-pi",
    label: "Pi (π)",
    displayLatex: "\\pi",
    insertLatex: "\\pi",
  },
];

const BASIC_KEYS: readonly MathPaletteKey[] = [
  {
    id: "frac",
    label: "Fraction",
    displayLatex: "\\frac{\\placeholder{}}{\\placeholder{}}",
    insertLatex: "\\frac{#@}{#?}",
  },
  {
    id: "square",
    label: "Square",
    displayLatex: "\\placeholder{}^{2}",
    insertLatex: "#@^{2}",
  },
  {
    id: "power",
    label: "Power",
    displayLatex: "\\placeholder{}^{\\placeholder{}}",
    insertLatex: "#@^{#?}",
  },
  {
    id: "sqrt",
    label: "Square root",
    displayLatex: "\\sqrt{\\placeholder{}}",
    insertLatex: "\\sqrt{#0}",
  },
  {
    id: "cbrt",
    label: "Cube root",
    displayLatex: "\\sqrt[3]{\\placeholder{}}",
    insertLatex: "\\sqrt[3]{#0}",
  },
  {
    id: "nroot",
    label: "nth root",
    displayLatex: "\\sqrt[\\placeholder{}]{\\placeholder{}}",
    insertLatex: "\\sqrt[#?]{#0}",
  },
  {
    id: "abs",
    label: "Absolute value",
    displayLatex: "\\left|\\placeholder{}\\right|",
    insertLatex: "\\left|#0\\right|",
  },
  {
    id: "pi",
    label: "Pi (π)",
    displayLatex: "\\pi",
    insertLatex: "\\pi",
  },
  {
    id: "e",
    label: "Euler's number (e)",
    displayLatex: "e",
    insertLatex: "e",
  },
  {
    id: "exp",
    label: "Exponential (e^n)",
    displayLatex: "e^{\\placeholder{}}",
    insertLatex: "e^{#?}",
  },
  {
    id: "pm",
    label: "Plus or minus (±)",
    displayLatex: "\\pm",
    insertLatex: "\\pm",
  },
  {
    id: "le",
    label: "Less than or equal (≤)",
    displayLatex: "\\le",
    insertLatex: "\\le",
  },
  {
    id: "ge",
    label: "Greater than or equal (≥)",
    displayLatex: "\\ge",
    insertLatex: "\\ge",
  },
  {
    id: "ne",
    label: "Not equal (≠)",
    displayLatex: "\\ne",
    insertLatex: "\\ne",
  },
  {
    id: "parens",
    label: "Parentheses ( )",
    displayLatex: "(\\placeholder{})",
    insertLatex: "\\left(#0\\right)",
  },
  {
    id: "brackets",
    label: "Square brackets [ ]",
    displayLatex: "[\\placeholder{}]",
    insertLatex: "\\left[#0\\right]",
  },
  {
    id: "comma",
    label: "Comma",
    displayLatex: ",",
    insertLatex: ",",
  },
  {
    id: "inf",
    label: "Infinity (∞)",
    displayLatex: "\\infty",
    insertLatex: "\\infty",
  },
  {
    id: "ninf",
    label: "Negative infinity (-∞)",
    displayLatex: "-\\infty",
    insertLatex: "-\\infty",
  },
];

const LOG_FUNCTION_KEYS: readonly MathPaletteKey[] = [
  {
    id: "ln",
    label: "Natural logarithm ln",
    displayLatex: "\\ln(\\placeholder{})",
    insertLatex: "\\ln(#0)",
    wide: true,
  },
  {
    id: "log",
    label: "Common logarithm log",
    displayLatex: "\\log(\\placeholder{})",
    insertLatex: "\\log(#0)",
    wide: true,
  },
  {
    id: "logb",
    label: "Logarithm with base",
    displayLatex: "\\log_{\\placeholder{}}(\\placeholder{})",
    insertLatex: "\\log_{#?}(#0)",
    wide: true,
  },
];

const TRIG_FUNCTION_KEYS: readonly MathPaletteKey[] = [
  {
    id: "sin",
    label: "Sine",
    displayLatex: "\\sin(\\placeholder{})",
    insertLatex: "\\sin(#0)",
    wide: true,
  },
  {
    id: "cos",
    label: "Cosine",
    displayLatex: "\\cos(\\placeholder{})",
    insertLatex: "\\cos(#0)",
    wide: true,
  },
  {
    id: "tan",
    label: "Tangent",
    displayLatex: "\\tan(\\placeholder{})",
    insertLatex: "\\tan(#0)",
    wide: true,
  },
  {
    id: "arcsin",
    label: "Inverse sine (arcsin)",
    displayLatex: "\\arcsin(\\placeholder{})",
    insertLatex: "\\arcsin(#0)",
    wide: true,
  },
  {
    id: "arccos",
    label: "Inverse cosine (arccos)",
    displayLatex: "\\arccos(\\placeholder{})",
    insertLatex: "\\arccos(#0)",
    wide: true,
  },
  {
    id: "arctan",
    label: "Inverse tangent (arctan)",
    displayLatex: "\\arctan(\\placeholder{})",
    insertLatex: "\\arctan(#0)",
    wide: true,
  },
];

const SYMBOL_KEYS: readonly MathPaletteKey[] = [
  {
    id: "i",
    label: "Imaginary unit (i)",
    displayLatex: "i",
    insertLatex: "i",
  },
  {
    id: "theta",
    label: "Theta (θ)",
    displayLatex: "\\theta",
    insertLatex: "\\theta",
  },
  {
    id: "alpha",
    label: "Alpha (α)",
    displayLatex: "\\alpha",
    insertLatex: "\\alpha",
  },
  {
    id: "beta",
    label: "Beta (β)",
    displayLatex: "\\beta",
    insertLatex: "\\beta",
  },
  {
    id: "Delta",
    label: "Delta (Δ)",
    displayLatex: "\\Delta",
    insertLatex: "\\Delta",
  },
  {
    id: "cup",
    label: "Union (∪)",
    displayLatex: "\\cup",
    insertLatex: "\\cup",
  },
  {
    id: "cap",
    label: "Intersection (∩)",
    displayLatex: "\\cap",
    insertLatex: "\\cap",
  },
  {
    id: "emptyset",
    label: "Empty set (∅)",
    displayLatex: "\\emptyset",
    insertLatex: "\\emptyset",
  },
];

/** Build the ordered inline palette sections for the active unit/question profile. */
export function getMathPaletteSections(
  profile: Pick<UnitKeyboardProfile, "trig">
): MathPaletteSection[] {
  const functionsKeys = profile.trig
    ? [...LOG_FUNCTION_KEYS, ...TRIG_FUNCTION_KEYS]
    : [...LOG_FUNCTION_KEYS];

  return [
    { id: "basic", heading: "BASIC", keys: BASIC_KEYS },
    { id: "functions", heading: "FUNCTIONS", keys: functionsKeys },
    { id: "symbols", heading: "SYMBOLS", keys: SYMBOL_KEYS },
  ];
}

const markupCache = new Map<string, string>();

/**
 * Lazily load MathLive's `convertLatexToMarkup` via dynamic ESM import so SSR
 * and CommonJS `tsx` test runners never evaluate the browser-only MathLive entry.
 */
export async function preloadPaletteRenderer(): Promise<ConvertLatexToMarkupFn | null> {
  if (loadedConvertToMarkup) return loadedConvertToMarkup;
  if (!loadPromise) {
    loadPromise = import("mathlive")
      .then((ml) => {
        if (typeof ml.convertLatexToMarkup === "function") {
          loadedConvertToMarkup = ml.convertLatexToMarkup;
          return loadedConvertToMarkup;
        }
        return null;
      })
      .catch(() => null);
  }
  return loadPromise;
}

/** Return true once MathLive's static LaTeX renderer is loaded. */
export function isPaletteRendererReady(): boolean {
  return loadedConvertToMarkup !== null;
}

/**
 * Render a palette key's LaTeX template into static MathLive HTML markup.
 * MathLive's `convertLatexToMarkup` renders `\placeholder{}` as an empty `&nbsp;`,
 * so we map `\placeholder{}` to `\square` to display crisp placeholder boxes.
 */
export function renderPaletteKeyMarkup(
  displayLatex: string,
  convertFn?: ConvertLatexToMarkupFn
): string {
  const fn = convertFn ?? loadedConvertToMarkup;
  if (!fn) return "";
  if (!convertFn) {
    const cached = markupCache.get(displayLatex);
    if (cached !== undefined) return cached;
  }
  const visualLatex = displayLatex.replace(/\\placeholder\{\}/g, "\\square");
  const markup = fn(visualLatex);
  if (!convertFn) {
    markupCache.set(displayLatex, markup);
  }
  return markup;
}

/** Insert a LaTeX template into a MathLive field at the caret and keep focus in the field. */
export function insertLatexIntoMathField(
  mf: MathFieldInsertTarget | null | undefined,
  latex: string
): boolean {
  if (!mf || typeof mf.executeCommand !== "function") return false;
  mf.executeCommand([
    "insert",
    latex,
    { selectionMode: "placeholder", focus: true },
  ]);
  mf.focus?.();
  return true;
}

/** Return true when the primary input device is coarse touch (phone/tablet). */
export function isTouchPrimaryDevice(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(hover: none) and (pointer: coarse)").matches;
}
