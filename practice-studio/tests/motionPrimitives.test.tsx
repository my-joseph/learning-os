import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "../src/components/ui/shadcn/AlertDialog";
import { Button } from "../src/components/ui/shadcn/Button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../src/components/ui/shadcn/Collapsible";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "../src/components/ui/shadcn/Dialog";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerTitle,
  DrawerTrigger,
} from "../src/components/ui/shadcn/Drawer";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "../src/components/ui/shadcn/HoverCard";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "../src/components/ui/shadcn/Popover";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../src/components/ui/shadcn/Tooltip";
import { ChoiceOptionGroup } from "../src/components/ChoiceOptionGroup";
import * as motionTokens from "../src/lib/motion";

const noop = () => {};

// 1. motion.ts exports (all existing + new variants and tap constants)
for (const key of [
  "EASE_OUT",
  "quick",
  "settle",
  "popover",
  "reveal",
  "fadeUp",
  "fade",
  "drawer",
  "dialogCard",
  "toastVariants",
  "presence",
  "drawerBottom",
  "tooltipPop",
  "tabPanel",
  "collapsibleReveal",
  "tapPress",
  "choiceTapPress",
] as const) {
  assert.ok(key in motionTokens, `src/lib/motion.ts must export ${key}`);
}
assert.deepEqual(motionTokens.tapPress, { scale: 0.98 });
assert.deepEqual(motionTokens.choiceTapPress, { scale: 0.99 });

// 2. SSR renderToStaticMarkup checks WITHOUT <MotionProvider> (verifies LazyMotion/m.* SSR safety)
// 2a. Dialog (closed & open)
const closedDialogHtml = renderToStaticMarkup(
  <Dialog open={false}>
    <DialogContent>
      <DialogTitle>Hidden dialog</DialogTitle>
      <DialogDescription>Hidden dialog description</DialogDescription>
    </DialogContent>
  </Dialog>
);
assert.equal(closedDialogHtml, "");

const openDialogHtml = renderToStaticMarkup(
  <Dialog open={true}>
    <DialogTrigger asChild>
      <Button variant="outline">Open dialog</Button>
    </DialogTrigger>
    <DialogContent>
      <DialogTitle>Sample dialog</DialogTitle>
      <DialogDescription>Dialog body</DialogDescription>
    </DialogContent>
  </Dialog>
);
assert.match(openDialogHtml, /role="dialog"/);
assert.match(openDialogHtml, /aria-label="Close dialog"/);
assert.match(openDialogHtml, /flex items-center justify-center p-4 pointer-events-none/);
assert.doesNotMatch(openDialogHtml, /-translate-x-1\/2|-translate-y-1\/2/);

// 2b. AlertDialog (closed & open, including max-w-sm override)
const closedAlertHtml = renderToStaticMarkup(
  <AlertDialog open={false}>
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>Hidden alert</AlertDialogTitle>
        <AlertDialogDescription>Hidden alert description</AlertDialogDescription>
      </AlertDialogHeader>
    </AlertDialogContent>
  </AlertDialog>
);
assert.equal(closedAlertHtml, "");

const openAlertHtml = renderToStaticMarkup(
  <AlertDialog open={true}>
    <AlertDialogTrigger asChild>
      <Button variant="destructive">Reset</Button>
    </AlertDialogTrigger>
    <AlertDialogContent className="max-w-sm p-5">
      <AlertDialogHeader>
        <AlertDialogTitle>Confirm reset?</AlertDialogTitle>
        <AlertDialogDescription>Reset progress.</AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel>Cancel</AlertDialogCancel>
        <AlertDialogAction>Confirm</AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
);
assert.match(openAlertHtml, /role="alertdialog"/);
assert.match(openAlertHtml, /flex items-center justify-center p-4 pointer-events-none/);
assert.match(openAlertHtml, /max-w-sm/);
assert.doesNotMatch(openAlertHtml, /-translate-x-1\/2|-translate-y-1\/2/);
assert.match(openAlertHtml, />Cancel<\/button>/);
assert.match(openAlertHtml, />Confirm<\/button>/);

// 2c. Drawer (closed & open)
const closedDrawerHtml = renderToStaticMarkup(
  <Drawer open={false}>
    <DrawerContent>
      <DrawerTitle>Hidden drawer</DrawerTitle>
      <DrawerDescription>Hidden drawer description</DrawerDescription>
    </DrawerContent>
  </Drawer>
);
assert.equal(closedDrawerHtml, "");

const openDrawerHtml = renderToStaticMarkup(
  <Drawer open={true}>
    <DrawerTrigger asChild>
      <Button variant="outline">Open drawer</Button>
    </DrawerTrigger>
    <DrawerContent>
      <DrawerTitle>Drawer title</DrawerTitle>
      <DrawerDescription>Drawer description</DrawerDescription>
    </DrawerContent>
  </Drawer>
);
assert.match(openDrawerHtml, /role="dialog"/);
assert.match(openDrawerHtml, /aria-label="Close drawer"/);
assert.match(openDrawerHtml, /Drawer title/);

// 2d. Popover (closed & open trigger; Radix Portal defers mount until browser layout effect)
const closedPopoverHtml = renderToStaticMarkup(
  <Popover open={false}>
    <PopoverTrigger asChild>
      <Button variant="outline">Open popover</Button>
    </PopoverTrigger>
    <PopoverContent>Hidden popover body</PopoverContent>
  </Popover>
);
assert.match(closedPopoverHtml, /Open popover/);
assert.doesNotMatch(closedPopoverHtml, /Hidden popover body/);

const openPopoverHtml = renderToStaticMarkup(
  <Popover open={true}>
    <PopoverTrigger asChild>
      <Button variant="outline">Open popover</Button>
    </PopoverTrigger>
    <PopoverContent>Visible popover body</PopoverContent>
  </Popover>
);
assert.match(openPopoverHtml, /aria-expanded="true"/);

// 2e. Tooltip (closed & open via SSR-safe TooltipPortal)
const closedTooltipHtml = renderToStaticMarkup(
  <TooltipProvider>
    <Tooltip open={false}>
      <TooltipTrigger asChild>
        <Button size="icon" aria-label="Help">?</Button>
      </TooltipTrigger>
      <TooltipContent>Hidden tip</TooltipContent>
    </Tooltip>
  </TooltipProvider>
);
assert.doesNotMatch(closedTooltipHtml, /Hidden tip/);

const openTooltipHtml = renderToStaticMarkup(
  <TooltipProvider>
    <Tooltip defaultOpen>
      <TooltipTrigger asChild>
        <Button size="icon" aria-label="Help">?</Button>
      </TooltipTrigger>
      <TooltipContent>Visible tip</TooltipContent>
    </Tooltip>
  </TooltipProvider>
);
assert.match(openTooltipHtml, /role="tooltip"/);
assert.match(openTooltipHtml, /Visible tip/);

// 2f. HoverCard (closed & open trigger)
const closedHoverCardHtml = renderToStaticMarkup(
  <HoverCard open={false}>
    <HoverCardTrigger asChild>
      <Button variant="outline">Hover preview</Button>
    </HoverCardTrigger>
    <HoverCardContent>Hidden preview</HoverCardContent>
  </HoverCard>
);
assert.match(closedHoverCardHtml, /Hover preview/);
assert.doesNotMatch(closedHoverCardHtml, /Hidden preview/);

const openHoverCardHtml = renderToStaticMarkup(
  <HoverCard open={true}>
    <HoverCardTrigger asChild>
      <Button variant="outline">Hover preview</Button>
    </HoverCardTrigger>
    <HoverCardContent>Visible preview</HoverCardContent>
  </HoverCard>
);
assert.match(openHoverCardHtml, /data-state="open"/);

// 2g. Collapsible (closed & open)
const closedCollapsibleHtml = renderToStaticMarkup(
  <Collapsible open={false}>
    <CollapsibleTrigger asChild>
      <Button variant="outline">Toggle</Button>
    </CollapsibleTrigger>
    <CollapsibleContent>Secret collapsible details</CollapsibleContent>
  </Collapsible>
);
assert.match(closedCollapsibleHtml, /aria-expanded="false"/);
assert.doesNotMatch(closedCollapsibleHtml, /Secret collapsible details/);

const openCollapsibleHtml = renderToStaticMarkup(
  <Collapsible open={true}>
    <CollapsibleTrigger asChild>
      <Button variant="outline">Toggle</Button>
    </CollapsibleTrigger>
    <CollapsibleContent>Visible collapsible details</CollapsibleContent>
  </Collapsible>
);
assert.match(openCollapsibleHtml, /aria-expanded="true"/);
assert.match(openCollapsibleHtml, /Visible collapsible details/);

// 2h. Button (native, disabled, asChild)
const buttonHtml = renderToStaticMarkup(
  <div>
    <Button>Primary</Button>
    <Button disabled>Disabled</Button>
    <Button asChild>
      <a href="#go">Link button</a>
    </Button>
  </div>
);
assert.match(buttonHtml, /<button[^>]*type="button"[^>]*>Primary<\/button>/);
assert.match(buttonHtml, /<button[^>]*disabled=""[^>]*>Disabled<\/button>/);
assert.match(buttonHtml, /<a href="#go" class="[^"]*min-h-\[44px\][^"]*">Link button<\/a>/);

// 2i. ChoiceOptionGroup (unselected + correct/assisted/wrong result states)
const choiceOptions = [
  { id: "A", label: "First" },
  { id: "B", label: "Second" },
];
const choiceDefaultHtml = renderToStaticMarkup(
  <ChoiceOptionGroup options={choiceOptions} selectedValue="" onSelect={noop} />
);
assert.match(choiceDefaultHtml, /role="radiogroup"/);
assert.match(choiceDefaultHtml, /role="radio"/);

for (const status of ["correct", "assisted", "wrong"] as const) {
  const resultHtml = renderToStaticMarkup(
    <ChoiceOptionGroup
      options={choiceOptions}
      selectedValue="A"
      onSelect={noop}
      disabled={true}
      resultStatus={status}
    />
  );
  assert.match(resultHtml, /aria-checked="true"/);
  assert.match(resultHtml, /inline-flex shrink-0/);
  assert.match(resultHtml, /<svg/);
}

// 3. Source invariants across all animated shadcn primitives
const motionPrimitiveFiles = [
  "src/components/ui/shadcn/Dialog.tsx",
  "src/components/ui/shadcn/AlertDialog.tsx",
  "src/components/ui/shadcn/Drawer.tsx",
  "src/components/ui/shadcn/Popover.tsx",
  "src/components/ui/shadcn/Tooltip.tsx",
  "src/components/ui/shadcn/HoverCard.tsx",
  "src/components/ui/shadcn/Collapsible.tsx",
  "src/components/ui/shadcn/Button.tsx",
] as const;

for (const file of motionPrimitiveFiles) {
  const src = readFileSync(file, "utf8");
  assert.match(
    src,
    /import\s+(?:type\s+)?\{[^}]*\bm\b[^}]*\}\s+from\s+"motion\/react"/,
    `${file} must import m from "motion/react"`
  );
  assert.doesNotMatch(
    src,
    /\bimport\s+(?:type\s+)?\{[^}]*\bmotion\b/,
    `${file} must NEVER import motion (LazyMotion strict requires m.*)`
  );
  assert.doesNotMatch(src, /<motion\./, `${file} must never render <motion.*>`);
  assert.doesNotMatch(src, /forceMount/, `${file} must never use forceMount`);
  assert.doesNotMatch(src, /\blayout(?:Id)?\b/, `${file} must never use layout or layoutId`);
  assert.doesNotMatch(
    src,
    /\banimate-in\b|\banimate-out\b/,
    `${file} must not contain dead animate-in/animate-out classes`
  );
  assert.match(
    src,
    /motion-reduce:transition-none/,
    `${file} must preserve motion-reduce:transition-none`
  );
}

for (const file of [
  "src/components/ui/shadcn/Dialog.tsx",
  "src/components/ui/shadcn/AlertDialog.tsx",
] as const) {
  const src = readFileSync(file, "utf8");
  assert.doesNotMatch(
    src,
    /-translate-x-1\/2|-translate-y-1\/2/,
    `${file} must not mix translate centering with Motion transforms`
  );
}

// 4. Non-primitive Motion components stay LazyMotion strict + zero-leak
for (const file of [
  "src/components/ChoiceOptionGroup.tsx",
  "src/components/math/MathWorkspace.tsx",
  "src/components/ui-poc/ShadcnPocShowcase.tsx",
] as const) {
  const src = readFileSync(file, "utf8");
  assert.doesNotMatch(
    src,
    /\bimport\s+(?:type\s+)?\{[^}]*\bmotion\b/,
    `${file} must NEVER import motion`
  );
  assert.doesNotMatch(src, /<motion\./, `${file} must never render <motion.*>`);
  assert.doesNotMatch(src, /forceMount/, `${file} must never use forceMount`);
  assert.doesNotMatch(src, /\blayoutId\b/, `${file} must never use layoutId`);
  assert.doesNotMatch(src, /\b(?:amber|yellow|emerald|rose)-\d/);
  assert.doesNotMatch(src, /[\u0E00-\u0E7F]/);
  assert.doesNotMatch(src, new RegExp("\\p{Extended_Pictographic}", "u"));
}

console.log("motionPrimitives tests passed");
