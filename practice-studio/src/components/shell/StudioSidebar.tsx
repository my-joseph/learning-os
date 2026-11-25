"use client";

import React, { useEffect, useRef, useState } from "react";
import { m } from "motion/react";
import { PanelLeft } from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import type { LabListItem } from "@/lib/labModel";
import { DrillFilter } from "@/hooks/types";
import { Workspace } from "@/lib/routes";
import { settle } from "@/lib/motion";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/shadcn/Button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";
import { WorkspaceSwitch } from "@/components/workspace/WorkspaceSwitch";
import { DrillSwitcher } from "./DrillSwitcher";

const noop = () => {};

export interface StudioSidebarProps {
  isOpen?: boolean;
  onToggle?: () => void;
  workspace: Workspace;
  pillWorkspace: Workspace;
  onSelectWorkspace: (workspace: Workspace) => void;
  mathHref: string | null;
  codeHref: string | null;
  currentDrill: DrillDocument | null;
  drills: DrillListItem[];
  labs?: LabListItem[];
  dueUnitCodes?: readonly string[];
  selectedDrillId: string;
  drillSearch: string;
  onSearchChange: (value: string) => void;
  drillFilter: DrillFilter;
  onFilterChange: (filter: DrillFilter) => void;
  onSelectDrill: (drillId: string) => void;
  onResetDrill?: (drillId: string) => void;
  onDeleteDrill?: (drillId: string) => void;
  embedded?: boolean;
  onCloseDrawer?: () => void;
}

/** Full-height flat left navigation sidebar (287px open <-> 0px closed on desktop, plus embedded mobile drawer mode). */
export const StudioSidebar: React.FC<StudioSidebarProps> = ({
  isOpen = true,
  onToggle,
  workspace,
  pillWorkspace,
  onSelectWorkspace,
  mathHref,
  codeHref,
  currentDrill,
  drills,
  labs = [],
  dueUnitCodes = [],
  selectedDrillId,
  drillSearch,
  onSearchChange,
  drillFilter,
  onFilterChange,
  onSelectDrill,
  onResetDrill,
  onDeleteDrill,
  embedded = false,
  onCloseDrawer,
}) => {
  const switcherRef = useRef<HTMLDivElement | null>(null);
  const [settledClosed, setSettledClosed] = useState(!isOpen);

  useEffect(() => {
    if (isOpen) {
      setSettledClosed(false);
    }
  }, [isOpen]);

  useEffect(() => {
    if (embedded || !onToggle) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.defaultPrevented ||
        !(e.metaKey || e.ctrlKey) ||
        e.altKey ||
        e.shiftKey ||
        e.key.toLowerCase() !== "b"
      ) {
        return;
      }
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.tagName === "MATH-FIELD" ||
          target.isContentEditable)
      ) {
        return;
      }
      if (
        typeof window.matchMedia === "function" &&
        !window.matchMedia("(min-width: 1024px)").matches
      ) {
        return;
      }
      e.preventDefault();
      onToggle();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [embedded, onToggle]);

  if (embedded) {
    return (
      <div className="w-full h-full flex flex-col overflow-hidden bg-surface-panel">
        <div className="min-h-[56px] shrink-0 px-3 pr-14 flex items-center justify-between border-b border-zinc-200/80 dark:border-zinc-800">
          <WorkspaceSwitch
            variant="sidebar"
            workspace={workspace}
            pillWorkspace={pillWorkspace}
            onSelectWorkspace={onSelectWorkspace}
            mathHref={mathHref}
            codeHref={codeHref}
          />
        </div>
        <div className="flex-1 min-h-0 flex flex-col">
          <DrillSwitcher
            mode="sidebar"
            isOpen={true}
            onToggle={noop}
            onClose={onCloseDrawer ?? noop}
            switcherRef={switcherRef}
            workspace={workspace}
            currentDrill={currentDrill}
            drills={drills}
            labs={labs}
            dueUnitCodes={dueUnitCodes}
            selectedDrillId={selectedDrillId}
            drillSearch={drillSearch}
            onSearchChange={onSearchChange}
            drillFilter={drillFilter}
            onFilterChange={onFilterChange}
            onSelectDrill={onSelectDrill}
            onResetDrill={onResetDrill}
            onDeleteDrill={onDeleteDrill}
          />
        </div>
      </div>
    );
  }

  return (
    <m.aside
      aria-label="Practice navigation"
      aria-hidden={!isOpen || undefined}
      initial={false}
      animate={{ width: isOpen ? 287 : 0, opacity: isOpen ? 1 : 0 }}
      transition={settle}
      onAnimationComplete={() => {
        if (!isOpen) setSettledClosed(true);
      }}
      className={cn(
        "hidden lg:flex flex-col shrink-0 overflow-hidden bg-surface-panel motion-reduce:transition-none",
        isOpen && "border-r border-zinc-200/80 dark:border-zinc-800",
        !isOpen && "pointer-events-none select-none",
        settledClosed && !isOpen && "invisible"
      )}
    >
      <div className="w-[287px] h-full flex flex-col">
        {/* Top bar inside Left Sidebar: seamless top-to-tree flow (no horizontal border-b) */}
        <div className="h-11 shrink-0 px-2.5 flex items-center justify-between gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="iconSm"
                onClick={onToggle}
                aria-label="Collapse sidebar"
                className="lg:min-h-0 lg:min-w-0 lg:h-8 lg:w-8 rounded-lg text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-200/60 dark:hover:bg-zinc-700/50 shrink-0"
              >
                <PanelLeft className="w-4 h-4" aria-hidden="true" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Close sidebar</TooltipContent>
          </Tooltip>

          <WorkspaceSwitch
            variant="sidebar"
            workspace={workspace}
            pillWorkspace={pillWorkspace}
            onSelectWorkspace={onSelectWorkspace}
            mathHref={mathHref}
            codeHref={codeHref}
          />
        </div>

        {/* Curriculum Tree body */}
        <div className="flex-1 min-h-0 flex flex-col">
          <DrillSwitcher
            mode="sidebar"
            isOpen={isOpen}
            onToggle={noop}
            onClose={noop}
            switcherRef={switcherRef}
            workspace={workspace}
            currentDrill={currentDrill}
            drills={drills}
            labs={labs}
            dueUnitCodes={dueUnitCodes}
            selectedDrillId={selectedDrillId}
            drillSearch={drillSearch}
            onSearchChange={onSearchChange}
            drillFilter={drillFilter}
            onFilterChange={onFilterChange}
            onSelectDrill={onSelectDrill}
            onResetDrill={onResetDrill}
            onDeleteDrill={onDeleteDrill}
          />
        </div>
      </div>
    </m.aside>
  );
};
