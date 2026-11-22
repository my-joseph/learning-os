"use client";

import React, { useState } from "react";
import { Check, CircleHelp, LoaderCircle, Sparkles, TriangleAlert } from "lucide-react";
import { ThemeToggleButton } from "@/components/ui/ThemeToggleButton";
import { Badge } from "@/components/ui/shadcn/Badge";
import { Button } from "@/components/ui/shadcn/Button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/shadcn/Dialog";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/shadcn/Drawer";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/shadcn/Popover";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/shadcn/Tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";
import { useTheme } from "@/hooks/useTheme";
import { statusTone, warningTone } from "@/lib/statusTone";

const cardClass = "min-w-0 rounded-xl border border-zinc-200 bg-background p-5 shadow-sm dark:border-zinc-800";

export function ShadcnPocShowcase() {
  const { theme, handleToggleTheme } = useTheme();
  const [state, setState] = useState<"empty" | "loading" | "error" | "success">("empty");
  const [dialogConfirmed, setDialogConfirmed] = useState(false);

  return (
    <main className="mx-auto min-h-screen w-full max-w-5xl overflow-x-hidden bg-background px-4 py-8 text-foreground sm:px-6">
        <header className="mb-8 flex min-w-0 flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Component proof of concept</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">shadcn/ui + Radix</h1>
            <p className="mt-2 max-w-2xl text-zinc-600 dark:text-zinc-400">A focused interaction and token review on the current Practice Studio stack.</p>
          </div>
          <ThemeToggleButton theme={theme} onToggle={handleToggleTheme} className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md border border-zinc-300 text-foreground hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:border-zinc-700 dark:hover:bg-zinc-800 dark:focus-visible:ring-indigo-400" />
        </header>

        <div className="grid min-w-0 grid-cols-1 gap-5 lg:grid-cols-2">
          <section className={cardClass} aria-labelledby="badges-heading">
            <h2 id="badges-heading" className="text-lg font-semibold">Badge variants</h2>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">Compact labels use shared status tokens and the neutral palette.</p>
            <div className="mt-4 flex min-w-0 flex-wrap items-center gap-2">
              <Badge>Default</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
              <Badge variant="destructive">Needs review</Badge>
              <Badge variant="success">Complete</Badge>
              <Badge variant="ghost">Ghost</Badge>
              <Badge><Sparkles aria-hidden="true" /> Featured</Badge>
              <Badge className={`${statusTone.correct.solidBadge} ${statusTone.correct.text}`}>Correct</Badge>
              <Badge className={`${statusTone.wrong.solidBadge} ${statusTone.wrong.text}`}>Incorrect</Badge>
            </div>
          </section>
          <section className={cardClass} aria-labelledby="buttons-heading">
            <h2 id="buttons-heading" className="text-lg font-semibold">Button variants</h2>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">Each control keeps a minimum 44 pixel touch target.</p>
            <div className="mt-4 flex min-w-0 flex-wrap gap-2">
              <Button>Primary action</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="destructive">Destructive</Button>
            </div>
            <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">Focus rings use the existing indigo accent.</p>
          </section>

          <section className={cardClass} aria-labelledby="tabs-heading">
            <h2 id="tabs-heading" className="text-lg font-semibold">Tabs and status tokens</h2>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">Use the arrow keys to move between tabs.</p>
            <Tabs defaultValue="overview" className="mt-4">
              <TabsList aria-label="Status examples">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="complete">Complete</TabsTrigger>
                <TabsTrigger value="pending">Pending</TabsTrigger>
              </TabsList>
              <TabsContent value="overview"><p className="text-sm">Keyboard navigation follows the logical tab order.</p></TabsContent>
              <TabsContent value="complete"><span className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ${statusTone.correct.softCard} ${statusTone.correct.text}`}>Complete</span></TabsContent>
              <TabsContent value="pending"><span className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ${statusTone.notTried.softCard} ${statusTone.notTried.text}`}>Not started</span></TabsContent>
            </Tabs>
          </section>

          <section className={cardClass} aria-labelledby="dialog-heading">
            <h2 id="dialog-heading" className="text-lg font-semibold">Dialog confirmation</h2>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">Radix manages focus containment, Escape dismissal, and focus restoration.</p>
            <Dialog>
              <DialogTrigger asChild><Button variant="outline" className="mt-4">Open confirmation</Button></DialogTrigger>
              <DialogContent aria-describedby="poc-dialog-description">
                <DialogTitle>Confirm this sample action?</DialogTitle>
                <DialogDescription id="poc-dialog-description">This confirmation is a UI demonstration. It does not change saved work or learner progress.</DialogDescription>
                <div className="mt-5 flex flex-wrap justify-end gap-2">
                  <Button variant="secondary" onClick={() => setDialogConfirmed(false)}>Cancel</Button>
                  <Button variant="destructive" onClick={() => setDialogConfirmed(true)}>Confirm</Button>
                </div>
              </DialogContent>
            </Dialog>
            {dialogConfirmed && <p role="status" className={`mt-3 rounded-md p-2 text-sm ${statusTone.correct.softCard} ${statusTone.correct.text}`}>Sample action confirmed.</p>}
          </section>

          <section className={cardClass} aria-labelledby="popover-heading">
            <h2 id="popover-heading" className="text-lg font-semibold">Popover and tooltip</h2>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">Both patterns support keyboard access and Escape dismissal.</p>
            <div className="mt-4 flex min-w-0 flex-wrap items-center gap-3">
              <Popover>
                <PopoverTrigger asChild><Button variant="outline">Open details</Button></PopoverTrigger>
                <PopoverContent aria-label="Interface details"><p className="font-medium">Interface details</p><p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">Neutral surfaces use the existing zinc scale.</p></PopoverContent>
              </Popover>
              <TooltipProvider delayDuration={150}>
                <Tooltip>
                  <TooltipTrigger asChild><Button size="icon" variant="ghost" aria-label="Help about focus"><CircleHelp aria-hidden="true" className="h-4 w-4" /></Button></TooltipTrigger>
                  <TooltipContent>Focus remains visible for keyboard users.</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </section>

          <section className={cardClass} aria-labelledby="drawer-heading">
            <h2 id="drawer-heading" className="text-lg font-semibold">Responsive drawer</h2>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">Bottom sheet on narrow screens; right-side panel on desktop.</p>
            <Drawer>
              <DrawerTrigger asChild><Button variant="outline" className="mt-4">Open drawer</Button></DrawerTrigger>
              <DrawerContent aria-describedby="poc-drawer-description">
                <DrawerTitle className="pr-10 text-lg font-semibold">Drawer panel</DrawerTitle>
                <DrawerDescription id="poc-drawer-description" className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">This panel adapts its position to the viewport and locks background interaction while open.</DrawerDescription>
                <div className="mt-5 rounded-lg bg-zinc-100 p-4 text-sm dark:bg-zinc-900">The close control has a 44 pixel target.</div>
              </DrawerContent>
            </Drawer>
          </section>

          <section className={cardClass} aria-labelledby="states-heading">
            <h2 id="states-heading" className="text-lg font-semibold">Interface states</h2>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">Switch among empty, loading, error, and success examples.</p>
            <div className="mt-4 flex min-w-0 flex-wrap gap-2">
              {(["empty", "loading", "error", "success"] as const).map((value) => (
                <Button key={value} size="sm" variant={state === value ? "primary" : "outline"} onClick={() => setState(value)}>{value[0].toUpperCase() + value.slice(1)}</Button>
              ))}
            </div>
            <div className="mt-4 min-h-16" aria-live="polite">
              {state === "empty" && <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-sm text-zinc-600 dark:border-zinc-700 dark:text-zinc-400">No items to show yet.</div>}
              {state === "loading" && <div role="status" className="flex min-w-0 flex-wrap items-center gap-2 rounded-lg border border-zinc-200 p-4 text-sm dark:border-zinc-800"><LoaderCircle aria-hidden="true" className="h-4 w-4 animate-spin motion-reduce:animate-none" />Loading sample data.</div>}
              {state === "error" && <div role="alert" className={`flex min-w-0 flex-wrap items-center gap-2 rounded-lg p-4 text-sm ${statusTone.wrong.softCard} ${statusTone.wrong.text}`}><TriangleAlert aria-hidden="true" className="h-4 w-4" />The sample data could not be loaded.</div>}
              {state === "success" && <div role="status" className={`flex min-w-0 flex-wrap items-center gap-2 rounded-lg p-4 text-sm ${statusTone.correct.softCard} ${statusTone.correct.text}`}><Check aria-hidden="true" className="h-4 w-4" />Sample data is ready.</div>}
            </div>
            <div className={`mt-3 rounded-lg p-3 text-sm ${warningTone.softCard} ${warningTone.text}`} role="note">A warning tone is reserved for operational notices.</div>
          </section>
        </div>
        <footer className="mt-8 min-w-0 text-xs text-zinc-500 dark:text-zinc-400">Source-owned primitives · React 18 · Tailwind 3.4 · Reduced-motion support</footer>
    </main>
  );
}
