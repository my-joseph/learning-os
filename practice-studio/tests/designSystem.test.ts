import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import postcss from "postcss";
import tailwindcss from "tailwindcss";
import ts from "typescript";
import config from "../tailwind.config";
import { auditDesignSystem, sourceFiles, studioRoot } from "./designSystemAudit";
import { Heading } from "../src/components/ui/Heading";
import { Numeral } from "../src/components/ui/Numeral";

const read = (file: string) => readFileSync(path.join(studioRoot, file), "utf8");
const tokensDoc = read("../docs/design/system.md");
const componentsDoc = read("../docs/design/components.md");

test("Design tokens agree across CSS, Tailwind and the reference", () => {
  const defaults = new Map<string, string>();
  const lightOverrides = new Map<string, string>();
  const darkOverrides = new Map<string, string>();
  const declared = new Set<string>();
  postcss.parse(read("src/app/globals.css")).walkRules((rule) => {
    rule.walkDecls(/^--/, (decl) => {
      declared.add(decl.prop);
      if (rule.selectors.includes(":root")) defaults.set(decl.prop, decl.value);
      if (rule.selectors.includes("html.light")) lightOverrides.set(decl.prop, decl.value);
      if (rule.selectors.includes("html.dark") || rule.selectors.includes(".dark")) darkOverrides.set(decl.prop, decl.value);
    });
  });
  const light = new Map([...Array.from(defaults), ...Array.from(lightOverrides)]);
  const dark = new Map([...Array.from(defaults), ...Array.from(darkOverrides)]);

  const exposure = new Map<string, Set<string>>();
  function record(token: string, key: string) {
    const keys = exposure.get(token) ?? new Set<string>();
    keys.add(key);
    exposure.set(token, keys);
  }
  function inspect(value: unknown, key: string) {
    if (typeof value === "string") {
      if (key.startsWith("screens.")) {
        const token = `--screen-${key.slice("screens.".length)}`;
        assert.equal(light.get(token), value, `${key} must mirror ${token}`);
        assert.equal(dark.get(token), value, `${key} must be the same in both themes`);
        record(token, key);
        return;
      }
      const references = Array.from(value.matchAll(/var\((--[\w-]+)\)/g));
      assert.ok(references.length, `Tailwind extension ${key} must reference a CSS token`);
      for (const [, token] of references) record(token, key);
    } else if (Array.isArray(value)) {
      for (const [index, entry] of Array.from(value.entries())) {
        if (key.startsWith("fontSize.") && index === 1) inspect(entry.lineHeight, `${key} (line height)`);
        else inspect(entry, key);
      }
    } else if (value && typeof value === "object") {
      for (const [child, entry] of Object.entries(value)) {
        inspect(entry, child === "DEFAULT" && key.startsWith("colors.") ? key : [key, child].filter(Boolean).join("."));
      }
    }
  }
  inspect(config.theme?.extend, "");
  assert.deepEqual(Object.keys(config.theme?.extend?.fontFamily ?? {}).sort(), ["heading", "mono", "sans"]);
  assert.deepEqual(Object.keys(config.theme?.extend?.fontWeight ?? {}).sort(), ["heading-medium", "normal", "semibold"]);

  const documented = new Set<string>();
  for (const [, token, keys, lightValue, darkValue] of Array.from(tokensDoc.matchAll(
    /^\| `(--[\w-]+)` \| (.+?) \| `([^`]+)` \| `([^`]+)` \|/gm,
  ))) {
    assert.ok(!documented.has(token), `Duplicate token row for ${token}`);
    documented.add(token);
    assert.equal(light.get(token), lightValue, `${token} light value`);
    assert.equal(dark.get(token), darkValue, `${token} dark value`);
    const documentedKeys = Array.from(keys.matchAll(/`([^`]+)`/g)).map((match) => match[1]);
    assert.deepEqual(Array.from(exposure.get(token) ?? []).sort(), documentedKeys.sort(), `${token} Tailwind exposure`);
  }

  assert.deepEqual(Array.from(declared).sort(), Array.from(documented).sort(), "Undocumented or missing CSS tokens");
  assert.deepEqual(Array.from(exposure.keys()).sort(), Array.from(documented).sort(), "Undocumented or missing Tailwind tokens");
});

test("Typography roles preserve heading semantics and tabular numbers", () => {
  const page = renderToStaticMarkup(createElement(Heading, null, "Lab title"));
  assert.doesNotMatch(page, /font-mono/);
  assert.match(page, /<h1 class="[^"]*font-heading text-lg tracking-heading[^"]*font-semibold">Lab title<\/h1>/);
  const section = renderToStaticMarkup(createElement(Heading, { variant: "section" }, "Section title"));
  assert.match(section, /<h2 class="[^"]*font-heading text-lg[^"]*font-heading-medium">Section title<\/h2>/);

  const small = renderToStaticMarkup(createElement(Numeral, { variant: "sm" }, "Q1"));
  assert.match(small, /class="font-sans tabular-nums">Q1/);
  const large = renderToStaticMarkup(createElement(Numeral, { variant: "lg", className: "text-base" }, "8 / 10"));
  assert.match(large, /class="[^"]*font-heading[^"]*tracking-heading tabular-nums text-base">8 \/ 10/);
  assert.doesNotMatch(large, /\btext-sm\b/);
});

test("Shared UI exports appear in the component catalog", () => {
  const catalog = new Set(
    Array.from(componentsDoc.matchAll(/^\| `([^`]+)` \| ([^|]+) \|/gm)).flatMap(([, file, exports]) =>
      Array.from(exports.matchAll(/`(\w+)`/g)).map(([, name]) => `${file}:${name}`),
    ),
  );

  // Resolve exports through TypeScript so barrel re-exports and aliases are covered.
  const directory = path.join(studioRoot, "src/components/ui");
  const files = sourceFiles(directory).filter((file) => /\.[cm]?[jt]sx?$/.test(file));
  const tsconfig = ts.readConfigFile(path.join(studioRoot, "tsconfig.json"), ts.sys.readFile);
  const { options } = ts.parseJsonConfigFileContent(tsconfig.config, ts.sys, studioRoot);
  const program = ts.createProgram(files, { ...options, allowJs: true });
  const checker = program.getTypeChecker();
  const exports = files.flatMap((file) => {
    const source = program.getSourceFile(file);
    const module = source && checker.getSymbolAtLocation(source);
    if (!module) return [];
    return checker.getExportsOfModule(module).flatMap((symbol) => {
      const target = symbol.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(symbol) : symbol;
      if (!(target.flags & ts.SymbolFlags.Value)) return [];
      // Public runtime helpers are also listed so the catalog covers the full value API.
      return [`${path.relative(directory, file)}:${symbol.getName()}`];
    });
  });
  assert.deepEqual(Array.from(catalog).sort(), exports.sort(), "Update the component catalog for shared UI exports");
});

test("Hard-coded design values stay within the Studio baseline", async (t) => {
  const audit = await auditDesignSystem();
  const baseline: { total: number } = JSON.parse(read("tests/designSystem.baseline.json"));
  t.diagnostic(`${audit.total} hard-coded values (baseline ${baseline.total}): ${JSON.stringify(audit.totals)}`);
  assert.ok(audit.total <= baseline.total, "Hard-coded design values increased. Reuse design tokens or migrate existing literals.");
});

test("Assist geometry utilities compile to their mobile and desktop dimensions", async () => {
  const { root } = await postcss(tailwindcss(config)).process(read("src/app/globals.css"), { from: undefined });
  const expectSize = (selector: string, property: string, value: string, desktop = false) => {
    let found = false;
    root.walkRules(selector, (rule) => {
      if (desktop) {
        assert.equal(rule.parent?.type, "atrule");
        if (rule.parent?.type === "atrule") assert.equal(rule.parent.params, "(min-width: 640px)");
      }
      rule.walkDecls(property, (declaration) => {
        if (declaration.prop === property && declaration.value === value) found = true;
      });
    });
    assert.ok(found, `${selector} must set ${property} to ${value}`);
  };
  expectSize(".min-h-touch", "min-height", "var(--touch)");
  expectSize(".min-w-touch", "min-width", "var(--touch)");
  expectSize(".sm\\:min-h-control-xs", "min-height", "var(--control-xs)", true);
  expectSize(".sm\\:min-h-control-md", "min-height", "var(--control-md)", true);
  expectSize(".sm\\:h-space-9", "height", "var(--space-9)", true);
  expectSize(".sm\\:size-space-6", "height", "var(--space-6)", true);
  expectSize(".size-stepper-marker", "width", "var(--stepper-marker)");
  expectSize(".size-stepper-marker-compact", "width", "var(--stepper-marker-compact)");
  expectSize(".stepper-item", "min-width", "calc(2 * var(--control-md))");
  expectSize(".stepper-item:first-child", "margin-left", "auto");
  expectSize(".stepper-item:last-child", "margin-right", "auto");
  expectSize(".border-status", "border-width", "var(--border-width-status)");
});
