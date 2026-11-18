import type { MathKeyIconId } from "@/components/math/MathKeyIcons";
import type { UnitKeyboardProfile } from "./mathInput";

export interface MathPaletteKey {
  id: string;
  iconId: MathKeyIconId;
  label: string;
  insertLatex: string;
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
    iconId: "frac",
    label: "Fraction",
    insertLatex: "\\frac{#@}{#?}",
  },
  {
    id: "quick-power",
    iconId: "power",
    label: "Exponent / power",
    insertLatex: "#@^{#?}",
  },
  {
    id: "quick-sqrt",
    iconId: "sqrt",
    label: "Square root",
    insertLatex: "\\sqrt{#0}",
  },
  {
    id: "quick-abs",
    iconId: "abs",
    label: "Absolute value",
    insertLatex: "\\left|#0\\right|",
  },
  {
    id: "quick-pi",
    iconId: "pi",
    label: "Pi (π)",
    insertLatex: "\\pi",
  },
];

const BASIC_KEYS: readonly MathPaletteKey[] = [
  {
    id: "frac",
    iconId: "frac",
    label: "Fraction",
    insertLatex: "\\frac{#@}{#?}",
  },
  {
    id: "square",
    iconId: "square",
    label: "Square",
    insertLatex: "#@^{2}",
  },
  {
    id: "power",
    iconId: "power",
    label: "Power",
    insertLatex: "#@^{#?}",
  },
  {
    id: "sqrt",
    iconId: "sqrt",
    label: "Square root",
    insertLatex: "\\sqrt{#0}",
  },
  {
    id: "cbrt",
    iconId: "cbrt",
    label: "Cube root",
    insertLatex: "\\sqrt[3]{#0}",
  },
  {
    id: "nroot",
    iconId: "nroot",
    label: "nth root",
    insertLatex: "\\sqrt[#?]{#0}",
  },
  {
    id: "abs",
    iconId: "abs",
    label: "Absolute value",
    insertLatex: "\\left|#0\\right|",
  },
  {
    id: "pi",
    iconId: "pi",
    label: "Pi (π)",
    insertLatex: "\\pi",
  },
  {
    id: "e",
    iconId: "e",
    label: "Euler's number (e)",
    insertLatex: "e",
  },
  {
    id: "exp",
    iconId: "exp",
    label: "Exponential (e^n)",
    insertLatex: "e^{#?}",
  },
  {
    id: "pm",
    iconId: "pm",
    label: "Plus or minus (±)",
    insertLatex: "\\pm",
  },
  {
    id: "le",
    iconId: "le",
    label: "Less than or equal (≤)",
    insertLatex: "\\le",
  },
  {
    id: "ge",
    iconId: "ge",
    label: "Greater than or equal (≥)",
    insertLatex: "\\ge",
  },
  {
    id: "ne",
    iconId: "ne",
    label: "Not equal (≠)",
    insertLatex: "\\ne",
  },
  {
    id: "parens",
    iconId: "parens",
    label: "Parentheses ( )",
    insertLatex: "\\left(#0\\right)",
  },
  {
    id: "brackets",
    iconId: "brackets",
    label: "Square brackets [ ]",
    insertLatex: "\\left[#0\\right]",
  },
  {
    id: "comma",
    iconId: "comma",
    label: "Comma",
    insertLatex: ",",
  },
  {
    id: "inf",
    iconId: "inf",
    label: "Infinity (∞)",
    insertLatex: "\\infty",
  },
  {
    id: "ninf",
    iconId: "ninf",
    label: "Negative infinity (-∞)",
    insertLatex: "-\\infty",
  },
];

const LOG_FUNCTION_KEYS: readonly MathPaletteKey[] = [
  {
    id: "ln",
    iconId: "ln",
    label: "Natural logarithm ln",
    insertLatex: "\\ln(#0)",
  },
  {
    id: "log",
    iconId: "log",
    label: "Common logarithm log",
    insertLatex: "\\log(#0)",
  },
  {
    id: "logb",
    iconId: "logb",
    label: "Logarithm with base",
    insertLatex: "\\log_{#?}(#0)",
  },
];

const TRIG_FUNCTION_KEYS: readonly MathPaletteKey[] = [
  {
    id: "sin",
    iconId: "sin",
    label: "Sine",
    insertLatex: "\\sin(#0)",
  },
  {
    id: "cos",
    iconId: "cos",
    label: "Cosine",
    insertLatex: "\\cos(#0)",
  },
  {
    id: "tan",
    iconId: "tan",
    label: "Tangent",
    insertLatex: "\\tan(#0)",
  },
  {
    id: "arcsin",
    iconId: "arcsin",
    label: "Inverse sine (arcsin)",
    insertLatex: "\\arcsin(#0)",
  },
  {
    id: "arccos",
    iconId: "arccos",
    label: "Inverse cosine (arccos)",
    insertLatex: "\\arccos(#0)",
  },
  {
    id: "arctan",
    iconId: "arctan",
    label: "Inverse tangent (arctan)",
    insertLatex: "\\arctan(#0)",
  },
];

const SYMBOL_KEYS: readonly MathPaletteKey[] = [
  {
    id: "i",
    iconId: "i",
    label: "Imaginary unit (i)",
    insertLatex: "i",
  },
  {
    id: "theta",
    iconId: "theta",
    label: "Theta (θ)",
    insertLatex: "\\theta",
  },
  {
    id: "alpha",
    iconId: "alpha",
    label: "Alpha (α)",
    insertLatex: "\\alpha",
  },
  {
    id: "beta",
    iconId: "beta",
    label: "Beta (β)",
    insertLatex: "\\beta",
  },
  {
    id: "Delta",
    iconId: "Delta",
    label: "Delta (Δ)",
    insertLatex: "\\Delta",
  },
  {
    id: "cup",
    iconId: "cup",
    label: "Union (∪)",
    insertLatex: "\\cup",
  },
  {
    id: "cap",
    iconId: "cap",
    label: "Intersection (∩)",
    insertLatex: "\\cap",
  },
  {
    id: "emptyset",
    iconId: "emptyset",
    label: "Empty set (∅)",
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
    { id: "basic", heading: "Basic", keys: BASIC_KEYS },
    { id: "functions", heading: "Functions", keys: functionsKeys },
    { id: "symbols", heading: "Symbols", keys: SYMBOL_KEYS },
  ];
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
