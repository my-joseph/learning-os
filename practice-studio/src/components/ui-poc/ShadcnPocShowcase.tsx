"use client";

import React, { useState } from "react";
import { Check, CircleHelp, LoaderCircle, Sparkles, TriangleAlert } from "lucide-react";
import { AnimatePresence, m } from "motion/react";
import { tabPanel } from "@/lib/motion";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/shadcn/AlertDialog";
import { Badge } from "@/components/ui/shadcn/Badge";
import { Button } from "@/components/ui/shadcn/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/shadcn/Card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/shadcn/Collapsible";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "@/components/ui/shadcn/Dialog";
import { Drawer, DrawerContent, DrawerDescription, DrawerTitle, DrawerTrigger } from "@/components/ui/shadcn/Drawer";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/shadcn/HoverCard";
import { Input } from "@/components/ui/shadcn/Input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/shadcn/Popover";
import { Skeleton } from "@/components/ui/shadcn/Skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/shadcn/Tabs";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/shadcn/Tooltip";
import { statusTone, warningTone } from "@/lib/statusTone";

export function ShadcnPocShowcase() {
  const [state, setState] = useState<"empty" | "loading" | "error" | "success">("empty");
  const [dialogConfirmed, setDialogConfirmed] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);

  return (
    <div className="space-y-space-4">
      <p className="text-sm text-foreground-secondary">Explore the shared shadcn/ui and Radix controls used in Practice Studio.</p>
      <div className="grid min-w-0 grid-cols-1 gap-space-4 lg:grid-cols-2">
        <Card variant="lab" aria-labelledby="badges-heading">
          <CardHeader><CardTitle id="badges-heading">Badge variants</CardTitle><CardDescription>Compact labels use shared status tokens and the neutral palette.</CardDescription></CardHeader>
          <CardContent className="flex min-w-0 flex-wrap items-center gap-2">
            <Badge>Default</Badge><Badge variant="secondary">Secondary</Badge><Badge variant="outline">Outline</Badge>
            <Badge variant="destructive">Needs review</Badge><Badge variant="success">Complete</Badge><Badge variant="ghost">Ghost</Badge>
            <Badge><Sparkles aria-hidden="true" /> Featured</Badge>
            <Badge variant="success" className={`${statusTone.correct.softCard} ${statusTone.correct.text}`}>Correct</Badge>
            <Badge variant="destructive" className={`${statusTone.wrong.softCard} ${statusTone.wrong.text}`}>Incorrect</Badge>
          </CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="buttons-heading">
          <CardHeader><CardTitle id="buttons-heading">Button variants</CardTitle><CardDescription>Each control keeps a minimum 44 pixel touch target.</CardDescription></CardHeader>
          <CardContent>
            <div className="flex min-w-0 flex-wrap gap-2"><Button>Primary action</Button><Button variant="secondary">Secondary</Button><Button variant="outline">Outline</Button><Button variant="ghost">Ghost</Button><Button variant="destructive">Destructive</Button></div>
            <p className="mt-3 text-xs text-foreground-secondary">Focus rings use the existing indigo accent.</p>
          </CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="tabs-heading">
          <CardHeader><CardTitle id="tabs-heading">Tabs and status tokens</CardTitle><CardDescription>Use the arrow keys to move between tabs.</CardDescription></CardHeader>
          <CardContent>
            <Tabs defaultValue="overview">
              <TabsList aria-label="Status examples"><TabsTrigger value="overview">Overview</TabsTrigger><TabsTrigger value="complete">Complete</TabsTrigger><TabsTrigger value="pending">Pending</TabsTrigger></TabsList>
              <TabsContent value="overview"><p className="text-sm">Keyboard navigation follows the logical tab order.</p></TabsContent>
              <TabsContent value="complete"><span className={`inline-flex rounded-full px-3 py-1 text-sm font-normal ${statusTone.correct.softCard} ${statusTone.correct.text}`}>Complete</span></TabsContent>
              <TabsContent value="pending"><span className={`inline-flex rounded-full px-3 py-1 text-sm font-normal ${statusTone.notTried.softCard} ${statusTone.notTried.text}`}>Not started</span></TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="dialog-heading">
          <CardHeader><CardTitle id="dialog-heading">Dialog confirmation</CardTitle><CardDescription>Radix manages focus containment, Escape dismissal, and focus restoration.</CardDescription></CardHeader>
          <CardContent>
            <Dialog><DialogTrigger asChild><Button variant="outline">Open confirmation</Button></DialogTrigger>
              <DialogContent aria-describedby="poc-dialog-description"><DialogTitle>Confirm this sample action?</DialogTitle><DialogDescription id="poc-dialog-description">This confirmation is a UI demonstration. It does not change saved work or learner progress.</DialogDescription>
                <div className="mt-5 flex flex-wrap justify-end gap-2"><Button variant="secondary" onClick={() => setDialogConfirmed(false)}>Cancel</Button><Button variant="destructive" onClick={() => setDialogConfirmed(true)}>Confirm</Button></div>
              </DialogContent>
            </Dialog>
            {dialogConfirmed && <p role="status" className={`mt-3 rounded-md p-2 text-sm ${statusTone.correct.softCard} ${statusTone.correct.text}`}>Sample action confirmed.</p>}
          </CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="popover-heading">
          <CardHeader><CardTitle id="popover-heading">Popover and tooltip</CardTitle><CardDescription>Both patterns support keyboard access and Escape dismissal.</CardDescription></CardHeader>
          <CardContent className="flex min-w-0 flex-wrap items-center gap-3">
            <Popover><PopoverTrigger asChild><Button variant="outline">Open details</Button></PopoverTrigger><PopoverContent aria-label="Interface details"><p className="font-normal">Interface details</p><p className="mt-1 text-sm text-foreground-secondary">The details panel anchors to its trigger.</p></PopoverContent></Popover>
            <TooltipProvider delayDuration={150}><Tooltip><TooltipTrigger asChild><Button size="icon" variant="ghost" aria-label="Help about focus"><CircleHelp aria-hidden="true" className="h-4 w-4" /></Button></TooltipTrigger><TooltipContent>Focus remains visible for keyboard users.</TooltipContent></Tooltip></TooltipProvider>
          </CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="drawer-heading">
          <CardHeader><CardTitle id="drawer-heading">Responsive drawer</CardTitle><CardDescription>Bottom sheet on narrow screens; right-side panel on desktop.</CardDescription></CardHeader>
          <CardContent><Drawer><DrawerTrigger asChild><Button variant="outline">Open drawer</Button></DrawerTrigger><DrawerContent aria-describedby="poc-drawer-description"><DrawerTitle className="pr-10 text-lg font-semibold">Drawer panel</DrawerTitle><DrawerDescription id="poc-drawer-description" className="mt-2 text-sm text-foreground-secondary">This panel adapts its position to the viewport and locks background interaction while open.</DrawerDescription><div className="mt-5 rounded-lg bg-surface-panel p-space-4 text-sm">The close control has a 44 pixel target.</div></DrawerContent></Drawer></CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="alert-dialog-heading">
          <CardHeader><CardTitle id="alert-dialog-heading">Alert dialog</CardTitle><CardDescription>Cancel is the safe default; outside clicks do not dismiss this confirmation.</CardDescription></CardHeader>
          <CardContent>
            <AlertDialog><AlertDialogTrigger asChild><Button variant="destructive">Reset sample</Button></AlertDialogTrigger>
              <AlertDialogContent><AlertDialogHeader><AlertDialogTitle>Reset the sample state?</AlertDialogTitle><AlertDialogDescription>This reset is a demonstration and does not change saved work or learner progress.</AlertDialogDescription></AlertDialogHeader>
                <AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction onClick={() => setDialogConfirmed(false)}>Reset sample</AlertDialogAction></AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="collapsible-heading">
          <CardHeader><CardTitle id="collapsible-heading">Collapsible details</CardTitle><CardDescription>Closed content stays unmounted until the learner opens it.</CardDescription></CardHeader>
          <CardContent>
            <Collapsible open={detailsOpen} onOpenChange={setDetailsOpen}>
              <CollapsibleTrigger asChild><Button variant="outline" aria-expanded={detailsOpen}>{detailsOpen ? "Hide details" : "Show details"}</Button></CollapsibleTrigger>
              <CollapsibleContent className="mt-3 rounded-lg border border-border p-space-3 text-sm">A collapsed section can hold optional supporting details.</CollapsibleContent>
            </Collapsible>
          </CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="hover-card-heading">
          <CardHeader><CardTitle id="hover-card-heading">Hover card</CardTitle><CardDescription>Supplementary previews are available on hover and keyboard focus.</CardDescription></CardHeader>
          <CardContent>
            <HoverCard openDelay={200}><HoverCardTrigger asChild><Button variant="outline">Preview a concept</Button></HoverCardTrigger><HoverCardContent><p className="font-normal">Concept preview</p><p className="mt-1 text-sm text-foreground-secondary">A short, optional summary can provide context without interrupting the page.</p></HoverCardContent></HoverCard>
          </CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="input-heading">
          <CardHeader><CardTitle id="input-heading">Input states</CardTitle><CardDescription>Text fields keep clear focus and disabled states.</CardDescription></CardHeader>
          <CardContent className="grid min-w-0 gap-3"><label htmlFor="poc-search" className="text-sm font-normal">Search sample content</label><Input id="poc-search" placeholder="Enter a search term" /><Input aria-label="Disabled sample input" disabled placeholder="Disabled field" /></CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="skeleton-heading">
          <CardHeader><CardTitle id="skeleton-heading">Skeleton loading</CardTitle><CardDescription>Reduced-motion settings disable the pulse animation.</CardDescription></CardHeader>
          <CardContent aria-label="Loading preview" role="status" className="grid gap-3"><Skeleton className="h-4 w-2/3" /><Skeleton className="h-4 w-full" /><Skeleton className="h-20 w-full" /></CardContent>
        </Card>

        <Card variant="lab" aria-labelledby="states-heading">
          <CardHeader><CardTitle id="states-heading">Interface states</CardTitle><CardDescription>Switch among empty, loading, error, and success examples.</CardDescription></CardHeader>
          <CardContent>
            <div className="flex min-w-0 flex-wrap gap-2">{(["empty", "loading", "error", "success"] as const).map((value) => <Button key={value} size="sm" variant={state === value ? "primary" : "outline"} onClick={() => setState(value)}>{value[0].toUpperCase() + value.slice(1)}</Button>)}</div>
            <div className="mt-4 min-h-16" aria-live="polite">
              <AnimatePresence mode="wait" initial={false}>
                <m.div key={state} variants={tabPanel} initial="hidden" animate="shown" exit="exit">
                  {state === "empty" && <div className="rounded-lg border border-dashed border-border-control p-space-4 text-sm text-foreground-secondary">No items to show yet.</div>}
                  {state === "loading" && <div role="status" className="flex min-w-0 flex-wrap items-center gap-2 rounded-lg border border-border p-space-4 text-sm"><LoaderCircle aria-hidden="true" className="h-4 w-4 animate-spin motion-reduce:animate-none" />Loading sample data.</div>}
                  {state === "error" && <div role="alert" className={`flex min-w-0 flex-wrap items-center gap-2 rounded-lg p-4 text-sm ${statusTone.wrong.softCard} ${statusTone.wrong.text}`}><TriangleAlert aria-hidden="true" className="h-4 w-4" />The sample data could not be loaded.</div>}
                  {state === "success" && <div role="status" className={`flex min-w-0 flex-wrap items-center gap-2 rounded-lg p-4 text-sm ${statusTone.correct.softCard} ${statusTone.correct.text}`}><Check aria-hidden="true" className="h-4 w-4" />Sample data is ready.</div>}
                </m.div>
              </AnimatePresence>
            </div>
            <div className={`mt-3 rounded-lg p-3 text-sm ${warningTone.softCard} ${warningTone.text}`} role="note">A warning tone is reserved for operational notices.</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function ShadcnPocPreview() {
  return (
    <div className="flex flex-col items-center gap-space-3">
      <div className="flex items-center gap-space-2">
        <Badge variant="outline">Badge</Badge>
        <Badge variant="secondary">Label</Badge>
      </div>
      <div className="flex items-center gap-space-2">
        <Button asChild variant="primary" size="compact"><span>Action</span></Button>
        <Button asChild variant="outline" size="compact"><span>Cancel</span></Button>
      </div>
    </div>
  );
}
