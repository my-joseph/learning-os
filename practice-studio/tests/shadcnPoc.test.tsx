import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ShadcnPocShowcase } from "../src/components/ui-poc/ShadcnPocShowcase";
import { Button } from "../src/components/ui/shadcn/Button";
import { Badge } from "../src/components/ui/shadcn/Badge";
import { Dialog, DialogTrigger } from "../src/components/ui/shadcn/Dialog";
import { Drawer, DrawerTrigger } from "../src/components/ui/shadcn/Drawer";
import { Popover, PopoverTrigger } from "../src/components/ui/shadcn/Popover";
import { Tabs, TabsList, TabsTrigger } from "../src/components/ui/shadcn/Tabs";
import { Tooltip, TooltipProvider, TooltipTrigger } from "../src/components/ui/shadcn/Tooltip";

const html = renderToStaticMarkup(<ShadcnPocShowcase />);
assert.match(html, /shadcn\/ui \+ Radix/);
assert.match(html, /role="tablist"/);
assert.match(html, /role="tab"/);
assert.match(html, /aria-selected="true"/);
assert.match(html, /aria-haspopup="dialog"/);
assert.match(html, /aria-label="Switch to (?:dark|light) mode"/);
assert.match(html, /min-h-\[44px\]/);
assert.match(html, /focus-visible:ring-2/);
assert.match(html, /Complete/);

const badgeMarkup = renderToStaticMarkup(
  <div>
    <Badge>Default badge</Badge>
    <Badge variant="status" className="text-zinc-700">Status badge</Badge>
    <Badge variant="secondary">Secondary badge</Badge>
    <Badge variant="outline">Outline badge</Badge>
    <Badge variant="destructive">Destructive badge</Badge>
    <Badge variant="success">Success badge</Badge>
    <Badge variant="ghost">Ghost badge</Badge>
    <Badge asChild><a href="#badge">Linked badge</a></Badge>
  </div>
);
for (const expected of ["Default badge", "Status badge", "Secondary badge", "Outline badge", "Destructive badge", "Success badge", "Ghost badge", "Linked badge"]) {
  assert.ok(badgeMarkup.includes(expected), `Badge SSR markup must include ${expected}`);
}
assert.match(badgeMarkup, /<a href="#badge" class="[^"]*rounded-full/);
assert.match(badgeMarkup, /bg-indigo-600 text-white dark:bg-indigo-500 dark:text-white/);
assert.match(badgeMarkup, /Status badge/);
const statusBadgeClasses = badgeMarkup.match(/<span class="([^"]*)">Status badge/)?.[1] ?? "";
assert.doesNotMatch(statusBadgeClasses, /bg-indigo-600/);
assert.match(badgeMarkup, /bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200/);
assert.match(badgeMarkup, /border border-zinc-300 text-zinc-700 dark:border-zinc-700 dark:text-zinc-300/);
assert.match(badgeMarkup, /bg-status-wrong text-status-on-wrong/);
assert.match(badgeMarkup, /bg-status-correct-soft border border-status-correct\/25/);
assert.match(badgeMarkup, /text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800/);

const primitiveMarkup = renderToStaticMarkup(
  <TooltipProvider>
    <Button>Accessible button</Button>
    <Button size="compact">Compact button</Button>
    <Button size="iconSm" aria-label="Compact icon action" />
    <Tabs defaultValue="first"><TabsList aria-label="Sample tabs"><TabsTrigger value="first">First tab</TabsTrigger></TabsList></Tabs>
    <Dialog><DialogTrigger>Open dialog</DialogTrigger></Dialog>
    <Popover><PopoverTrigger>Open popover</PopoverTrigger></Popover>
    <Tooltip><TooltipTrigger>Tooltip trigger</TooltipTrigger></Tooltip>
    <Drawer><DrawerTrigger>Open drawer</DrawerTrigger></Drawer>
  </TooltipProvider>
);
for (const expected of ["Accessible button", "Compact button", "aria-label=\"Compact icon action\"", "role=\"tablist\"", "role=\"tab\"", "Open dialog", "Open popover", "Tooltip trigger", "Open drawer"]) {
  assert.ok(primitiveMarkup.includes(expected), `SSR primitive markup must include ${expected}`);
}
const compactButtonAttrs = primitiveMarkup.match(/<button\b([^>]*)>Compact button<\/button>/)?.[1] ?? "";
assert.match(compactButtonAttrs, /\btype="button"/);
assert.match(compactButtonAttrs, /min-h-\[44px\]/);
assert.match(compactButtonAttrs, /sm:min-h-\[32px\]/);
const iconSmButtonAttrs = primitiveMarkup.match(/<button\b([^>]*)aria-label="Compact icon action"[^>]*>/)?.[1] ?? "";
assert.match(iconSmButtonAttrs, /\btype="button"/);
assert.match(iconSmButtonAttrs, /min-w-\[44px\]/);
assert.match(iconSmButtonAttrs, /sm:min-w-\[36px\]/);
assert.match(primitiveMarkup, /<button[^>]*type="button"[^>]*>Accessible button/);

const componentFiles = [
  "src/components/ui/shadcn/Button.tsx",
  "src/components/ui/shadcn/Badge.tsx",
  "src/components/ui/shadcn/Tabs.tsx",
  "src/components/ui/shadcn/Dialog.tsx",
  "src/components/ui/shadcn/Popover.tsx",
  "src/components/ui/shadcn/Tooltip.tsx",
  "src/components/ui/shadcn/Drawer.tsx",
  "src/components/ui-poc/ShadcnPocShowcase.tsx",
];
const source = componentFiles.map((file) => readFileSync(file, "utf8")).join("\n");
assert.match(source, /motion-reduce:transition-none/);
assert.match(source, /min-h-\[44px\] min-w-\[44px\]/);
assert.match(source, /DialogTitle/);
assert.match(source, /DialogDescription/);
assert.match(source, /DrawerTitle/);
assert.match(source, /DrawerDescription/);
assert.match(source, /statusTone/);
assert.match(source, /warningTone/);
assert.match(source, /dark:bg-indigo-600 dark:text-white dark:hover:bg-indigo-500/);
assert.match(source, /max-w-5xl overflow-x-hidden/);
assert.match(source, /px-4 py-8 text-foreground sm:px-6/);
assert.match(source, /grid-cols-1 gap-5 lg:grid-cols-2/);
assert.doesNotMatch(source, /\b(?:amber|yellow|emerald|rose)-\d/);
assert.doesNotMatch(source, /[\u0E00-\u0E7F]/, "POC learning-facing strings must be English");
assert.doesNotMatch(source, /\p{Extended_Pictographic}/u, "POC strings must not contain emoji");

const packageJson = JSON.parse(readFileSync("package.json", "utf8")) as {
  dependencies: Record<string, string>;
  devDependencies: Record<string, string>;
};
assert.equal(packageJson.dependencies["tailwind-merge"], "^2.6.0");
assert.equal(packageJson.dependencies.next, "14.2.35");
assert.equal(packageJson.dependencies.react, "^18");
assert.equal(packageJson.dependencies["react-dom"], "^18");
assert.equal(packageJson.devDependencies.tailwindcss, "^3.4.1");
assert.equal(packageJson.dependencies.motion, "14.8.0");
assert.equal(packageJson.devDependencies.typescript, "^5");
assert.equal(packageJson.devDependencies.eslint, "^8");
console.log("shadcn POC SSR and token checks passed");
