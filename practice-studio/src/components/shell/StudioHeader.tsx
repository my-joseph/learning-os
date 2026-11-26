"use client";

import React from "react";
import Link from "next/link";
import { AnimatePresence, m } from "motion/react";
import {
  ArrowUpRight,
  FlaskConical,
  List,
  PanelLeft,
  Plus,
  RotateCcw,
} from "lucide-react";
import { DrillDocument } from "@/types/drill";
import { Workspace, isLabId } from "@/lib/routes";
import { statusTone } from "@/lib/statusTone";
import { isCurriculumId, plainTitle } from "@/lib/titleText";
import { EASE_OUT, quick } from "@/lib/motion";
import { cn } from "@/lib/cn";
import { Button, IconButton } from "@/components/ui/shadcn/Button";
import { ThemeToggleButton } from "@/components/ui/ThemeToggleButton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";

import { useTheme } from "@/hooks/useTheme";
import { StudioSearchTrigger } from "./StudioSearchPalette";

function StudioHeaderFrame({
  leading,
  beforeTheme,
  afterPlayground,
  theme,
  onToggleTheme,
  playgroundCurrent = false,
}: {
  leading: React.ReactNode;
  beforeTheme?: React.ReactNode;
  afterPlayground?: React.ReactNode;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  playgroundCurrent?: boolean;
}) {
  return (
    <header className="sticky top-0 z-sticky flex h-space-12 w-full shrink-0 items-center justify-between gap-space-2 border-b border-border/80 bg-surface-raised px-space-2 sm:px-space-3 lg:h-touch">
      <div className="flex min-w-0 flex-1 items-center gap-space-1 sm:gap-space-1_5">{leading}</div>
      <div className="flex shrink-0 items-center gap-space-0_5">
        {beforeTheme}
        <ThemeToggleButton variant="header" theme={theme} onToggle={onToggleTheme} />
        <Tooltip>
          <TooltipTrigger asChild>
            <Button asChild variant="headerUtility" size="headerIcon">
              <Link
                href="/playground"
                aria-label="Open Playground"
                aria-current={playgroundCurrent ? "location" : undefined}
                data-selected={playgroundCurrent}
              >
                <FlaskConical className="size-space-4" aria-hidden="true" />
              </Link>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom">Playground</TooltipContent>
        </Tooltip>
        {afterPlayground}
      </div>
    </header>
  );
}

export function StudioPlaygroundHeader() {
  const { theme, handleToggleTheme } = useTheme();
  return (
    <TooltipProvider>
      <StudioHeaderFrame
        playgroundCurrent
        theme={theme}
        onToggleTheme={handleToggleTheme}
        leading={
          <Button variant="exampleBack" size="exampleBack" asChild>
            <Link href="/" prefetch={false} className="text-sm">Practice Studio</Link>
          </Button>
        }
      />
    </TooltipProvider>
  );
}

interface StudioHeaderProps {
  workspace: Workspace;
  currentDrill: DrillDocument | null;
  selectedDrillId: string;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onResetAll: () => void;
  onOpenGenPopover: () => void;
  isSidebarOpen: boolean;
  onOpenDesktopSidebar: () => void;
  onOpenSidebarDrawer: () => void;
  searchShortcut?: string;
  onOpenSearch?: () => void;
  isRightPanelOpen: boolean;
  onToggleRightPanel?: () => void;
  onOpenSideDrawer?: () => void;
  sidePanelCount?: number;
}

/** Flat full-width slim Top Bar with conditional Expand Sidebar button, drill title, and utility actions. */
export const StudioHeader: React.FC<StudioHeaderProps> = ({
  workspace,
  currentDrill,
  selectedDrillId,
  theme,
  onToggleTheme,
  onResetAll,
  onOpenGenPopover,
  isSidebarOpen,
  onOpenDesktopSidebar,
  onOpenSidebarDrawer,
  searchShortcut = "Ctrl K",
  onOpenSearch,
  isRightPanelOpen,
  onToggleRightPanel,
  onOpenSideDrawer,
  sidePanelCount = 0,
}) => {
  const drillTitle = currentDrill
    ? plainTitle(currentDrill.unitTitle) || currentDrill.unitCode
    : "Practice Studio";

  const resetAllLabel = isLabId(selectedDrillId)
    ? "Reset all milestones"
    : workspace === "code"
    ? "Reset all problems"
    : "Reset all questions";

  const showRightPanelToggle = Boolean(onToggleRightPanel || onOpenSideDrawer);

  const handleRightPanelClick = () => {
    if (
      typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      window.matchMedia("(min-width: 1024px)").matches
    ) {
      onToggleRightPanel?.();
    } else {
      onOpenSideDrawer?.();
    }
  };

  return (
    <StudioHeaderFrame
      theme={theme}
      onToggleTheme={onToggleTheme}
      leading={(
        <>
          <Tooltip>
            <TooltipTrigger asChild>
              <IconButton
                tone="secondary"
                hitArea="sidebarToggle"
                onClick={onOpenSidebarDrawer}
                aria-label="Open navigation sidebar"
                className="lg:hidden dark:hover:bg-surface-hover"
              >
                <PanelLeft className="size-space-4" aria-hidden="true" />
              </IconButton>
            </TooltipTrigger>
            <TooltipContent side="bottom">Open sidebar</TooltipContent>
          </Tooltip>

          <AnimatePresence initial={false}>
            {!isSidebarOpen && (
              <m.div
                key="desktop-expand-sidebar"
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto", transition: quick }}
                exit={{
                  opacity: 0,
                  width: 0,
                  transition: { duration: 0.14, ease: EASE_OUT },
                }}
                className="hidden lg:flex items-center overflow-hidden shrink-0"
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <IconButton
                      tone="secondary"
                      hitArea="sidebarToggle"
                      onClick={onOpenDesktopSidebar}
                      aria-label="Expand sidebar"
                    >
                      <PanelLeft className="size-space-4" aria-hidden="true" />
                    </IconButton>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">Open sidebar</TooltipContent>
                </Tooltip>
              </m.div>
            )}
          </AnimatePresence>

          {onOpenSearch && (
            <StudioSearchTrigger
              compact
              shortcut={searchShortcut}
              onClick={onOpenSearch}
              className={isSidebarOpen ? "lg:hidden" : undefined}
            />
          )}

          <span className={cn("text-xs sm:text-sm text-zinc-700 dark:text-zinc-200 truncate pl-0.5", isCurriculumId(drillTitle) && "font-mono")}>
            {drillTitle}
          </span>
        </>
      )}
      beforeTheme={(
        <>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="iconSm"
                onClick={onOpenGenPopover}
                aria-label="Generate drill set"
                className="min-h-[44px] min-w-[44px] lg:min-h-0 lg:min-w-0 lg:h-8 lg:w-8 rounded-lg text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-200/60 dark:hover:bg-zinc-800"
              >
                <Plus className="w-4 h-4" aria-hidden="true" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Generate drill set</TooltipContent>
          </Tooltip>

          {currentDrill && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="iconSm"
                  onClick={onResetAll}
                  aria-label={resetAllLabel}
                  className={`min-h-[44px] min-w-[44px] lg:min-h-0 lg:min-w-0 lg:h-8 lg:w-8 rounded-lg text-zinc-500 dark:text-zinc-400 ${statusTone.wrong.hoverText} hover:bg-zinc-200/60 dark:hover:bg-zinc-800`}
                >
                  <RotateCcw className="w-4 h-4" aria-hidden="true" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">{resetAllLabel}</TooltipContent>
            </Tooltip>
          )}

          {currentDrill?.unitNotionUrl && (
            <Tooltip>
              <TooltipTrigger asChild>
                <a
                  href={currentDrill.unitNotionUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Open unit page in Notion"
                  className="inline-flex items-center justify-center min-h-[44px] min-w-[44px] lg:min-h-0 lg:min-w-0 lg:h-8 lg:w-8 rounded-lg text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                >
                  <ArrowUpRight className="w-4 h-4" aria-hidden="true" />
                </a>
              </TooltipTrigger>
              <TooltipContent side="bottom">Open unit page in Notion</TooltipContent>
            </Tooltip>
          )}
        </>
      )}
      afterPlayground={showRightPanelToggle && (
          <>
            <span
              aria-hidden="true"
              className="hidden sm:block mx-1 h-4 w-px bg-zinc-200 dark:bg-zinc-800"
            />
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="iconSm"
                  onClick={handleRightPanelClick}
                  aria-label="Due today & weak spots"
                  aria-pressed={isRightPanelOpen}
                  className={cn(
                    "relative min-h-[44px] min-w-[44px] lg:min-h-0 lg:min-w-0 lg:h-8 lg:w-8 rounded-lg text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-200/60 dark:hover:bg-zinc-800",
                    isRightPanelOpen &&
                      "lg:text-zinc-800 lg:dark:text-zinc-100 lg:bg-zinc-200/50 lg:dark:bg-zinc-800/60"
                  )}
                >
                  <List className="w-4 h-4" aria-hidden="true" />
                  {sidePanelCount > 0 && (
                    <span
                      aria-hidden="true"
                      className={cn(
                        "absolute top-2.5 right-2.5 lg:top-1.5 lg:right-1.5 w-1.5 h-1.5 rounded-full bg-indigo-600 dark:bg-indigo-400",
                        isRightPanelOpen && "lg:hidden"
                      )}
                    />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                {sidePanelCount > 0
                  ? `Due today & weak spots (${sidePanelCount})`
                  : "Due today & weak spots"}
              </TooltipContent>
            </Tooltip>
          </>
      )}
    />
  );
};
