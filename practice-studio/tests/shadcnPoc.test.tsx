import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ShadcnPocShowcase } from "../src/components/ui-poc/ShadcnPocShowcase";
import { Button } from "../src/components/ui/shadcn/Button";
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

const primitiveMarkup = renderToStaticMarkup(
  <TooltipProvider>
    <Button>Accessible button</Button>
    <Tabs defaultValue="first"><TabsList aria-label="Sample tabs"><TabsTrigger value="first">First tab</TabsTrigger></TabsList></Tabs>
    <Dialog><DialogTrigger>Open dialog</DialogTrigger></Dialog>
    <Popover><PopoverTrigger>Open popover</PopoverTrigger></Popover>
    <Tooltip><TooltipTrigger>Tooltip trigger</TooltipTrigger></Tooltip>
    <Drawer><DrawerTrigger>Open drawer</DrawerTrigger></Drawer>
  </TooltipProvider>
);
for (const expected of ["Accessible button", "role=\"tablist\"", "role=\"tab\"", "Open dialog", "Open popover", "Tooltip trigger", "Open drawer"]) {
  assert.ok(primitiveMarkup.includes(expected), `SSR primitive markup must include ${expected}`);
}

const componentFiles = [
  "src/components/ui/shadcn/Button.tsx",
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
assert.doesNotMatch(source, /\b(?:amber|yellow|emerald|rose)-\d/);
assert.doesNotMatch(source, /[\u0E00-\u0E7F]/, "POC learning-facing strings must be English");
assert.doesNotMatch(source, /\p{Extended_Pictographic}/u, "POC strings must not contain emoji");

const packageJson = JSON.parse(readFileSync("package.json", "utf8")) as {
  dependencies: Record<string, string>;
  devDependencies: Record<string, string>;
};
assert.equal(packageJson.dependencies.next, "14.2.35");
assert.equal(packageJson.dependencies.react, "^18");
assert.equal(packageJson.dependencies["react-dom"], "^18");
assert.equal(packageJson.devDependencies.tailwindcss, "^3.4.1");
console.log("shadcn POC SSR and token checks passed");
