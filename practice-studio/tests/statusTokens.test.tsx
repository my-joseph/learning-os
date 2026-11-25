/**
 * Guard tests for the Practice Studio status & warning colour token design system.
 * Ensures:
 * 1. Light & dark RGB channel CSS variables exist in src/app/globals.css.
 * 2. tailwind.config.ts exposes colors.status.*, colors.warning.*, colors.accent and scans src/lib.
 * 3. statusTone recipes (especially assisted) contain no amber/yellow or hard-coded palette literals.
 * 4. No file in src/ (outside figure/diagram components, statusTone.ts, and globals.css)
 *    uses raw amber-/yellow- or emerald-/rose- Tailwind colour classes.
 */
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import {
  DESTRUCTIVE_BUTTON_CLS,
  MUTED_UNTRIED_TAB_MARK,
  statusTone,
  warningTone,
  type StatusTone,
} from "../src/lib/statusTone";

const globalsCss = readFileSync("src/app/globals.css", "utf8");
const tailwindConfig = readFileSync("tailwind.config.ts", "utf8");

// 1. CSS custom properties present in both light and dark blocks as RGB channel triples
const lightBlockMatch = globalsCss.match(/:root,\s*html\.light\s*\{([\s\S]*?)\}/);
const darkBlockMatch = globalsCss.match(/html\.dark,\s*\.dark\s*\{([\s\S]*?)\}/);
assert.ok(lightBlockMatch, "globals.css must define a :root, html.light token block");
assert.ok(darkBlockMatch, "globals.css must define a html.dark, .dark token block");

const REQUIRED_CSS_VARS = [
  "--status-correct",
  "--status-correct-text",
  "--status-correct-soft",
  "--status-on-correct",
  "--status-assisted",
  "--status-assisted-soft",
  "--status-on-assisted",
  "--status-wrong",
  "--status-wrong-soft",
  "--status-on-wrong",
  "--status-skipped",
  "--status-neutral",
  "--warning",
  "--warning-soft",
  "--warning-border",
  "--accent",
] as const;

for (const varName of REQUIRED_CSS_VARS) {
  const re = new RegExp(`${varName}:\\s*\\d+\\s+\\d+\\s+\\d+\\s*;`);
  assert.match(lightBlockMatch[1], re, `light block missing RGB channel token ${varName}`);
  assert.match(darkBlockMatch[1], re, `dark block missing RGB channel token ${varName}`);
}

// 2. Tailwind config exposes status, warning, and accent tokens with <alpha-value> and scans src/lib
assert.match(
  tailwindConfig,
  /["']\.\/src\/lib\/\*\*\/\*\.\{[^}]*ts[^}]*\}["']/,
  "tailwind.config.ts content must include src/lib so recipe classes are generated"
);
for (const key of [
  "correct",
  "correct-soft",
  "assisted",
  "assisted-soft",
  "wrong",
  "wrong-soft",
  "skipped",
  "neutral",
  "on-correct",
  "on-assisted",
  "on-wrong",
]) {
  const re = new RegExp(`["']?${key}["']?:\\s*["']rgb\\(var\\(--status-${key}\\) / <alpha-value>\\)["']`);
  assert.match(tailwindConfig, re, `tailwind.config.ts must expose colors.status.${key}`);
}
assert.match(tailwindConfig, /accent:\s*["']rgb\(var\(--accent\) \/ <alpha-value>\)["']/);
assert.match(tailwindConfig, /DEFAULT:\s*["']rgb\(var\(--warning\) \/ <alpha-value>\)["']/);

// 3. Recipe invariants: all 5 tones complete, zero raw palette classes, assisted has zero amber
const ALL_TONES: StatusTone[] = ["correct", "assisted", "wrong", "skipped", "notTried"];
const REQUIRED_SHAPES = [
  "solidCircle",
  "tabMark",
  "softCard",
  "iconCircle",
  "text",
  "dot",
  "tile",
] as const;

const RAW_PALETTE_RE = /\b(?:amber|yellow|emerald|rose)-\d/;

for (const tone of ALL_TONES) {
  const recipe = statusTone[tone];
  assert.ok(recipe, `statusTone.${tone} must exist`);
  for (const shape of REQUIRED_SHAPES) {
    const val = recipe[shape];
    assert.equal(typeof val, "string", `statusTone.${tone}.${shape} must be a string`);
    assert.ok(val.trim().length > 0, `statusTone.${tone}.${shape} must be non-empty`);
    assert.doesNotMatch(
      val,
      RAW_PALETTE_RE,
      `statusTone.${tone}.${shape} must use semantic CSS tokens, not raw palette classes: ${val}`
    );
  }
}

for (const tone of ["correct", "assisted", "wrong"] as const) {
  const recipe = statusTone[tone];
  for (const shape of ["choiceCard", "solidBadge", "selfScoreActive"] as const) {
    assert.equal(typeof recipe[shape], "string", `statusTone.${tone}.${shape} must be a string`);
  }
}
assert.equal(typeof statusTone.correct.border, "string");
for (const shape of ["border", "borderSoft", "hoverText", "hoverBorderSoft"] as const) {
  assert.equal(typeof statusTone.wrong[shape], "string", `statusTone.wrong.${shape} must be a string`);
}
for (const tone of ["skipped", "notTried"] as const) {
  for (const shape of ["choiceCard", "solidBadge", "selfScoreActive"] as const) {
    assert.equal(shape in statusTone[tone], false, `statusTone.${tone}.${shape} is unused`);
  }
}

for (const shape of REQUIRED_SHAPES) {
  assert.doesNotMatch(
    statusTone.assisted[shape],
    /amber|yellow|warning/i,
    `statusTone.assisted.${shape} must never use amber, yellow, or warning`
  );
}
for (const shape of ["solidCircle", "tabMark", "softCard", "iconCircle", "text", "dot", "selfScoreActive", "tile"] as const) {
  assert.notEqual(
    statusTone.assisted[shape],
    statusTone.correct[shape],
    `statusTone.assisted.${shape} must remain visually distinct from statusTone.correct.${shape}`
  );
}

for (const [key, val] of Object.entries(warningTone)) {
  assert.ok(val.trim().length > 0, `warningTone.${key} must be non-empty`);
  assert.match(val, /warning/, `warningTone.${key} must reference the warning token`);
  assert.doesNotMatch(
    val,
    RAW_PALETTE_RE,
    `warningTone.${key} must use semantic warning tokens, not raw palette classes: ${val}`
  );
}
assert.doesNotMatch(MUTED_UNTRIED_TAB_MARK, RAW_PALETTE_RE);
assert.doesNotMatch(DESTRUCTIVE_BUTTON_CLS, RAW_PALETTE_RE);

// 4. Scan src/ (excluding diagram/figure palettes, statusTone.ts, and globals.css)
const EXCLUDED_PATHS = [
  /^src\/lib\/statusTone\.ts$/,
  /^src\/app\/globals\.css$/,
  /^src\/components\/MathFigure\//,
  /^src\/components\/Interactive[^/]*\.tsx$/,
  /^src\/components\/VisualRenderer\.tsx$/,
];

function walkSrc(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...walkSrc(full));
    } else if (/\.(ts|tsx|css)$/.test(entry)) {
      out.push(full.split(path.sep).join("/"));
    }
  }
  return out;
}

const AMBER_YELLOW_RE = /\b(?:amber|yellow)-\d{2,3}\b/g;
const STATUS_PALETTE_RE = /\b(?:emerald|rose)-\d{2,3}\b/g;

for (const file of walkSrc("src")) {
  if (EXCLUDED_PATHS.some((re) => re.test(file))) continue;
  const content = readFileSync(file, "utf8");
  const amberMatches = content.match(AMBER_YELLOW_RE);
  assert.equal(
    amberMatches,
    null,
    `${file} contains forbidden amber-/yellow- class(es) (${amberMatches?.join(", ")}). Use warningTone for non-status warnings or statusTone.assisted for assisted answers.`
  );
  const statusPaletteMatches = content.match(STATUS_PALETTE_RE);
  assert.equal(
    statusPaletteMatches,
    null,
    `${file} contains hard-coded status palette class(es) (${statusPaletteMatches?.join(", ")}). Import from src/lib/statusTone.ts instead.`
  );
}

console.log("statusTokens tests passed");
