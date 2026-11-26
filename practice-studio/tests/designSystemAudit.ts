import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import postcss from "postcss";
import tailwindcss from "tailwindcss";
import ts from "typescript";
import config from "../tailwind.config";

export const studioRoot = path.resolve(__dirname, "..");

export function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(directory, entry.name);
    return entry.isDirectory() ? sourceFiles(file) : /\.(?:[cm]?[jt]sx?|css|mdx)$/.test(file) ? [file] : [];
  });
}

const groups = {
  Colour: /^(?:--tw-gradient-(?:from|via|to)|--hue|background(?:-color|-image)?|(?:[\w-]+-)?color|fill|stroke)$/,
  "Spacing and size": /^(?:(?:min-|max-)?(?:width|height)|(?:padding|margin|inset|gap)(?:-[\w-]+)?|row-gap|column-gap|(?:top|bottom|left|right)|flex-basis|size|translate[xy]?|--tw-translate-[xy])$/,
  "Font family": /^font-family$/,
  "Font size": /^font-size$/,
  "Font weight": /^font-weight$/,
  "Line height": /^line-height$/,
  Radius: /^border(?:-[\w-]+)?-radius$/,
  "Border and stroke width": /^(?:(?:border(?:-[\w-]+)?|outline|stroke)-width|--tw-ring-offset-width)$/,
  Shadow: /^(?:--tw-(?:drop-)?shadow|box-shadow|text-shadow)$/,
  Opacity: /^(?:opacity|fill-opacity|stroke-opacity|flood-opacity|--placeholder-opacity|--tw-backdrop-opacity)$/,
  Blur: /^(?:--tw-(?:backdrop-)?blur|std-deviation)$/,
  "Motion duration": /^(?:(?:transition|animation)-(?:duration|delay)|duration|delay(?:-duration)?)$/,
  "Motion easing": /^(?:(?:transition|animation)-timing-function|ease)$/,
  "Stacking layer": /^z-index$/,
  Breakpoint: /^@media$/,
};

type Group = keyof typeof groups;
const hardcodedKinds = [
  "arbitrary utilities",
  "raw neutral text utilities",
  "raw hex colours",
  "other raw colours",
  "inline values",
  "CSS literals",
] as const;
type HardcodedKind = (typeof hardcodedKinds)[number];
type Counts = Map<string, number>;

const hex = /#[\da-f]{8}(?![\w-])|#[\da-f]{6}(?![\w-])|#[\da-f]{4}(?![\w-])|#[\da-f]{3}(?![\w-])/gi;
const colorFunction = /\b(?:rgba?|hsla?|oklch)\([^)]*\)/g;
const arbitraryValue = /(?:^|:)!?-?(?:[\w-]+-\[([^\]]+)\]|\[([\w-]+:[^\]]+)\])(?:\/[^\s]+)?$/;
const rawNeutralText = /(?:^|:)!?\btext-(?:zinc|gray|slate|neutral|stone)-\d{2,3}(?:\/[\w.%-]+)?$/;
const mediaWidth = /\b(?:min-|max-)?width\s*:\s*[\d.]+(?:px|rem|em)\b/g;

function increment(counts: Counts, value: string, by = 1) {
  counts.set(value, (counts.get(value) ?? 0) + by);
}

function groupFor(property: string, value: string): Group | undefined {
  if (property === "box-shadow" && value.includes("var(--tw-ring")) return;
  if (property === "transition") return "Motion duration";
  if (property === "animation" && value !== "none") return "Motion duration";
  const normalized = property.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`);
  return (Object.keys(groups) as Group[]).find((group) => groups[group].test(normalized));
}

function literalValues(node: ts.Node): string[] {
  if (ts.isJsxExpression(node) && node.expression) return literalValues(node.expression);
  if (ts.isStringLiteralLike(node) || ts.isNumericLiteral(node)) return [node.text];
  if (ts.isPrefixUnaryExpression(node) && ts.isNumericLiteral(node.operand)) return [node.getText()];
  if (ts.isConditionalExpression(node)) return [...literalValues(node.whenTrue), ...literalValues(node.whenFalse)];
  if (ts.isBinaryExpression(node) && (
    node.operatorToken.kind === ts.SyntaxKind.BarBarToken || node.operatorToken.kind === ts.SyntaxKind.QuestionQuestionToken
  )) return [...literalValues(node.left), ...literalValues(node.right)];
  if (ts.isArrayLiteralExpression(node) && node.elements.every(ts.isNumericLiteral)) return [node.getText()];
  return [];
}

function isStyleLiteral(group: Group, value: string) {
  if (group === "Colour") {
    return /^(?:#|(?:rgba?|hsla?|oklch)\(|none$|white$|black$|transparent$|currentColor$)/i.test(value);
  }
  if (group === "Font family" || group === "Motion easing") return true;
  return /^(?:[\d.[-]|auto$|none$|full$|inherit$)/.test(value);
}

export async function auditDesignSystem() {
  const inventory = new Map<Group, Counts>();
  const hardcoded = new Map<HardcodedKind, Counts>(hardcodedKinds.map((kind) => [kind, new Map()]));
  const words: Counts = new Map();

  function record(group: Group, value: string, count = 1) {
    const values = inventory.get(group) ?? new Map();
    increment(values, value, count);
    inventory.set(group, values);
  }

  function collectWords(value: string) {
    for (const word of value.split(/\s+/).filter(Boolean)) increment(words, word);
  }

  function recordRawColour(value: string) {
    increment(hardcoded.get(value.startsWith("#") ? "raw hex colours" : "other raw colours")!, value);
  }

  function styleValues(property: string, value: string): [Group, string][] {
    if (property === "outline" || /^border(?:-(?:top|right|bottom|left))?$/.test(property)) {
      const values: [Group, string][] = [];
      const width = value.match(/^([\d.]+(?:px|rem|em))\b/)?.[1];
      const colors = [...Array.from(value.matchAll(hex)), ...Array.from(value.matchAll(colorFunction))];
      if (width) values.push(["Border and stroke width", width]);
      for (const [color] of colors) values.push(["Colour", color]);
      return values;
    }
    if (property === "--tw-ring-shadow") {
      const ringWidth = value.match(/calc\(([^+]+) \+/)?.[1];
      return ringWidth ? [["Border and stroke width", ringWidth]] : [];
    }
    if (property === "transition" || property === "animation") {
      return [
        ...Array.from(value.matchAll(/[\d.]+m?s\b/g)).map(([duration]): [Group, string] => ["Motion duration", duration]),
        ...Array.from(value.matchAll(/\bease(?:-in|-out|-in-out)?\b|cubic-bezier\([^)]*\)/g))
          .map(([easing]): [Group, string] => ["Motion easing", easing]),
      ];
    }
    const group = groupFor(property, value);
    if (!group) return [];
    if (group === "Colour") {
      const alpha = value.match(/[/,]\s*(0?\.\d+|(?:\d+(?:\.\d+)?)%)\)\s*$/)?.[1];
      if (alpha) return [[group, value], ["Opacity", alpha]];
    }
    return [[group, value]];
  }

  const vendoredIsometric = `${path.sep}src${path.sep}lib${path.sep}isometric${path.sep}`;
  for (const file of sourceFiles(path.join(studioRoot, "src"))) {
    if (file.includes(vendoredIsometric)) continue;
    const source = readFileSync(file, "utf8");
    if (file.endsWith(".css")) {
      const css = postcss.parse(source, { from: file });
      css.walkAtRules("apply", (rule) => { collectWords(rule.params); });
      css.walkAtRules("media", (rule) => {
        for (const [width] of Array.from(rule.params.matchAll(mediaWidth))) {
          record("Breakpoint", width);
          increment(hardcoded.get("CSS literals")!, `@media ${width}`);
        }
      });
      css.walkDecls((decl) => {
        if (file.endsWith("/globals.css") && decl.prop.startsWith("--")) return;
        const values = styleValues(decl.prop, decl.value);
        if (!values.length || decl.value === "inherit") return;
        for (const [group, value] of values) record(group, value);
        if (/^var\(/.test(decl.value)) return;
        if (values.some(([group]) => group === "Colour")) {
          const colours = [...Array.from(decl.value.matchAll(hex)), ...Array.from(decl.value.matchAll(colorFunction))];
          if (colours.length) colours.forEach(([colour]) => recordRawColour(colour));
          else recordRawColour(decl.value);
        }
        if (values.some(([group]) => group !== "Colour")) {
          increment(hardcoded.get("CSS literals")!, `${decl.prop}: ${decl.value}`);
        }
      });
      continue;
    }

    const tree = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true);
    const visit = (node: ts.Node) => {
      if (ts.isStringLiteralLike(node) || ts.isTemplateLiteralToken(node)) {
        collectWords(node.text);
        for (const [color] of [...Array.from(node.text.matchAll(hex)), ...Array.from(node.text.matchAll(colorFunction))]) {
          record("Colour", color);
          recordRawColour(color);
        }
        for (const [media] of Array.from(node.text.matchAll(/(?:min-|max-)width\s*:\s*[\d.]+(?:px|rem|em)\b/g))) {
          if (node.text.includes("@media")) continue;
          record("Breakpoint", media);
          increment(hardcoded.get("inline values")!, `@media ${media}`);
        }
      }
      if (ts.isJsxAttribute(node) || ts.isPropertyAssignment(node) || ts.isBindingElement(node)) {
        const key = node.name.getText(tree).replace(/^["']|["']$/g, "");
        const initializer = node.initializer;
        if (initializer && (file.includes("/src/components/") || file.endsWith("/lib/motion.ts"))) {
          for (const literal of literalValues(initializer)) {
            const group = file.endsWith("/lib/motion.ts") && /^[xy]$/.test(key)
              ? "Spacing and size"
              : groupFor(key, literal);
            if (!group || !isStyleLiteral(group, literal)) continue;
            if (group === "Colour" && /^(?:#|(?:rgba?|hsla?|oklch)\()/i.test(literal)) continue;
            const value = `${key}: ${literal}`;
            record(group, value);
            increment(hardcoded.get("inline values")!, value);
          }
        }
      }
      if (ts.isVariableDeclaration(node) && node.initializer && node.name.getText(tree) === "EASE_OUT") {
        const value = node.initializer.getText(tree).replace(/ as const$/, "");
        record("Motion easing", value);
        increment(hardcoded.get("inline values")!, value);
      }
      ts.forEachChild(node, visit);
    };
    visit(tree);
  }

  // Let Tailwind determine which source words are utilities, including arbitrary variants
  // and recipes. Map the generated rules to their values and the original occurrence counts.
  const generated = await postcss([
    tailwindcss({ ...config, content: [{ raw: Array.from(words.keys()).join(" "), extension: "html" }] }),
  ]).process("@tailwind utilities;", { from: undefined });
  const perUtility = new Map<string, Map<string, [Group, string]>>();
  generated.root.walkRules((rule) => {
    const selectors = Array.from(rule.selector.matchAll(/\.((?:\\.|[\w-])+)/g));
    for (const [, escaped] of selectors) {
      const utility = escaped.replace(/\\(.)/g, "$1");
      if (!words.has(utility)) continue;
      const values = perUtility.get(utility) ?? new Map();
      perUtility.set(utility, values);
      rule.walkDecls((decl) => {
        const normalized = decl.value.replace(/var\(--tw-[\w-]+-opacity(?:, 1)?\)/g, "1");
        for (const [group, value] of styleValues(decl.prop, normalized)) {
          values.set(`${group}: ${value}`, [group, value]);
        }
      });
      for (let parent = rule.parent; parent && parent.type !== "root"; parent = parent.parent) {
        if (parent.type !== "atrule" || parent.name !== "media") continue;
        for (const [width] of Array.from(parent.params.matchAll(mediaWidth))) values.set(width, ["Breakpoint", width]);
      }
    }
  });

  for (const [utility, values] of Array.from(perUtility)) {
    const count = words.get(utility)!;
    for (const [group, value] of Array.from(values.values())) record(group, value, count);
    if (rawNeutralText.test(utility)) {
      increment(hardcoded.get("raw neutral text utilities")!, utility.split(":").at(-1)!, count);
    }
    const arbitrary = utility.match(arbitraryValue);
    if (arbitrary && !/var\(--/.test(arbitrary[1] ?? arbitrary[2]) && !/#[\da-f]{3}|(?:rgba?|hsla?|oklch)\(/i.test(utility)) {
      increment(hardcoded.get("arbitrary utilities")!, utility, count);
    }
  }

  const totals = Object.fromEntries(
    Array.from(hardcoded).map(([kind, values]) => [kind, Array.from(values.values()).reduce((sum, count) => sum + count, 0)]),
  );
  return { inventory, hardcoded, totals, total: Object.values(totals).reduce((sum, count) => sum + count, 0) };
}
