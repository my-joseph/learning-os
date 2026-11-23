"use client";

import React from "react";
import { PanelLeft, PanelRight } from "lucide-react";
import { DrillDocument } from "@/types/drill";
import { plainTitle } from "@/lib/titleText";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/shadcn/Button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";

interface StudioHeaderProps {
  headerRef?: React.RefObject<HTMLElement>;
  showHeader: boolean;
  currentDrill: DrillDocument | null;
  onOpenSidebarDrawer?: () => void;
  onOpenSideDrawer?: () => void;
  sidePanelCount?: number;
  tiles?: React.ReactNode;
}

/** Sticky Studio header: pagination-only card on desktop (>=1024px) and slim drawer triggers + pagination on mobile/tablet. */
export const StudioHeader: React.FC<StudioHeaderProps> = ({
  headerRef,
  showHeader,
  currentDrill,
  onOpenSidebarDrawer,
  onOpenSideDrawer,
  sidePanelCount = 0,
  tiles,
}) => {
  const drillTitle = currentDrill
    ? plainTitle(currentDrill.unitTitle) || currentDrill.unitCode
    : "Practice Studio";

  return (
    <header
      ref={headerRef}
      className={cn(
        "sticky top-2 z-40 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 rounded-2xl px-2.5 sm:px-3.5 py-2 sm:py-2.5 mb-5 shadow-sm transition-all duration-150",
        !tiles && "lg:hidden",
        showHeader
          ? "translate-y-0 opacity-100"
          : "-translate-y-[130%] opacity-0 pointer-events-none"
      )}
    >
      {/* Mobile / Tablet (<1024px): Slim drawer-trigger bar */}
      <div className="flex lg:hidden items-center justify-between gap-2 min-w-0">
        <div className="flex items-center gap-1 min-w-0 flex-1">
          {onOpenSidebarDrawer && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="iconSm"
                  onClick={onOpenSidebarDrawer}
                  aria-label="Open navigation sidebar"
                  className="min-h-[44px] min-w-[44px] lg:hidden inline-flex items-center justify-center rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 shrink-0"
                >
                  <PanelLeft className="w-4 h-4" aria-hidden="true" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Open navigation sidebar</TooltipContent>
            </Tooltip>
          )}

          {onOpenSidebarDrawer ? (
            <button
              type="button"
              onClick={onOpenSidebarDrawer}
              aria-label={`Switch drill: ${drillTitle}`}
              className="min-h-[44px] inline-flex items-center min-w-0 text-left text-sm font-medium text-zinc-900 dark:text-zinc-100 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded-md px-1"
            >
              <span className="truncate">{drillTitle}</span>
            </button>
          ) : (
            <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate px-1">
              {drillTitle}
            </span>
          )}
        </div>

        {onOpenSideDrawer && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="iconSm"
                onClick={onOpenSideDrawer}
                aria-label="Due today & weak spots"
                className="relative min-h-[44px] min-w-[44px] lg:hidden inline-flex items-center justify-center rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 shrink-0"
              >
                <PanelRight className="w-4 h-4" aria-hidden="true" />
                {sidePanelCount > 0 && (
                  <span
                    aria-hidden="true"
                    className="absolute top-2.5 right-2.5 w-1.5 h-1.5 rounded-full bg-indigo-600 dark:bg-indigo-400"
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
        )}
      </div>

      {/* Pagination / Stepper row (sole desktop header content) */}
      {tiles}
    </header>
  );
};
