"use client";

import React, { useState, useEffect } from "react";
import {
  ArrowUpRight,
  PanelRight,
  Plus,
  RotateCcw,
} from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import type { LabListItem } from "@/lib/labModel";
import { DrillFilter } from "@/hooks/types";
import { Workspace, isLabId } from "@/lib/routes";
import { statusTone } from "@/lib/statusTone";
import { ThemeToggleButton } from "@/components/ui/ThemeToggleButton";
import { WorkspaceSwitch } from "@/components/workspace/WorkspaceSwitch";
import { DrillSwitcher } from "./DrillSwitcher";

interface StudioHeaderProps {
  headerRef?: React.RefObject<HTMLElement>;
  showHeader: boolean;
  workspace: Workspace;
  pillWorkspace?: Workspace;
  onSelectWorkspace?: (workspace: Workspace) => void;
  mathHref: string | null;
  codeHref: string | null;
  currentDrill: DrillDocument | null;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onResetAll: () => void;
  // DrillSwitcher props
  showDrillSwitcher: boolean;
  onToggleDrillSwitcher: () => void;
  onCloseDrillSwitcher: () => void;
  switcherRef: React.RefObject<HTMLDivElement>;
  drills: DrillListItem[];
  labs?: LabListItem[];
  dueUnitCodes?: readonly string[];
  selectedDrillId: string;
  drillSearch: string;
  onSearchChange: (value: string) => void;
  drillFilter: DrillFilter;
  onFilterChange: (filter: DrillFilter) => void;
  onSelectDrill: (drillId: string) => void;
  // Generate dialog trigger
  onOpenGenPopover: () => void;
  // Side drawer (mobile / <1024px)
  onOpenSideDrawer?: () => void;
  sidePanelCount?: number;
  // Row 2: Question tiles bar
  tiles?: React.ReactNode;
}

/** Slim one-row Studio header with drill switcher, Generate button, compact icon actions, and tiles row. */
export const StudioHeader: React.FC<StudioHeaderProps> = ({
  headerRef,
  showHeader,
  workspace,
  pillWorkspace: controlledPillWorkspace,
  onSelectWorkspace,
  mathHref,
  codeHref,
  currentDrill,
  theme,
  onToggleTheme,
  onResetAll,
  showDrillSwitcher,
  onToggleDrillSwitcher,
  onCloseDrillSwitcher,
  switcherRef,
  drills,
  labs = [],
  dueUnitCodes = [],
  selectedDrillId,
  drillSearch,
  onSearchChange,
  drillFilter,
  onFilterChange,
  onSelectDrill,
  onOpenGenPopover,
  onOpenSideDrawer,
  sidePanelCount = 0,
  tiles,
}) => {
  const [localPillWorkspace, setLocalPillWorkspace] = useState<Workspace>(workspace);
  useEffect(() => setLocalPillWorkspace(workspace), [workspace]);

  const pillWorkspace = controlledPillWorkspace ?? localPillWorkspace;
  const handleSelectWorkspace = (next: Workspace) => {
    setLocalPillWorkspace(next);
    onSelectWorkspace?.(next);
  };

  const resetAllLabel = isLabId(selectedDrillId)
    ? "Reset all milestones"
    : workspace === "code"
    ? "Reset all problems"
    : "Reset all questions";

  return (
    <header
      ref={headerRef}
      className={`sticky top-2 z-50 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 rounded-2xl px-2.5 sm:px-3.5 py-2.5 mb-6 shadow-sm transition-all duration-150 ${
        showHeader
          ? "translate-y-0 opacity-100"
          : "-translate-y-[130%] opacity-0 pointer-events-none"
      }`}
    >
      {/* Slim one-row header */}
      <div className="relative flex items-center justify-between gap-1.5 sm:gap-2">
        {/* Left: Workspace switch (<1024px, icon-only) + Drill switcher + Generate button */}
        <div className="flex items-center gap-1.5 sm:gap-2 min-w-0 flex-1">
          <WorkspaceSwitch
            variant="header"
            workspace={workspace}
            pillWorkspace={pillWorkspace}
            onSelectWorkspace={handleSelectWorkspace}
            mathHref={mathHref}
            codeHref={codeHref}
            className="relative grid lg:hidden grid-cols-2 items-center rounded-lg bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-800 p-0.5 shrink-0"
          />

          <DrillSwitcher
            isOpen={showDrillSwitcher}
            onToggle={onToggleDrillSwitcher}
            onClose={onCloseDrillSwitcher}
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
          />

          <button
            type="button"
            onClick={onOpenGenPopover}
            aria-label="Generate drill set"
            title="Generate drill set"
            className="inline-flex items-center justify-center gap-1.5 w-8 h-8 sm:w-auto sm:h-9 sm:px-3 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors shrink-0"
          >
            <Plus className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            <span className="hidden sm:inline">Generate</span>
          </button>
        </div>

        {/* Right: Side drawer (<1024px) + Theme toggle + Notion link + Reset all */}
        <div className="flex items-center gap-0.5 sm:gap-1 shrink-0">
          {onOpenSideDrawer && (
            <button
              type="button"
              onClick={onOpenSideDrawer}
              aria-label="Due today & weak spots"
              title={
                sidePanelCount > 0
                  ? `Due today & weak spots (${sidePanelCount})`
                  : "Due today & weak spots"
              }
              className="relative lg:hidden inline-flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <PanelRight className="w-4 h-4" aria-hidden="true" />
              {sidePanelCount > 0 && (
                <span
                  aria-hidden="true"
                  className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-indigo-600 dark:bg-indigo-400"
                />
              )}
            </button>
          )}

          <ThemeToggleButton
            theme={theme}
            onToggle={onToggleTheme}
            className="inline-flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          />

          {currentDrill?.unitNotionUrl && (
            <a
              href={currentDrill.unitNotionUrl}
              target="_blank"
              rel="noopener noreferrer"
              title="Open unit page in Notion"
              aria-label="Open unit page in Notion"
              className="inline-flex items-center justify-center gap-1 w-8 h-8 sm:w-auto sm:h-9 sm:px-2.5 rounded-lg text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <span className="hidden sm:inline">Notion</span>
              <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
            </a>
          )}

          {currentDrill && (
            <button
              type="button"
              onClick={onResetAll}
              aria-label={resetAllLabel}
              title={resetAllLabel}
              className={`inline-flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-lg text-zinc-600 dark:text-zinc-400 ${statusTone.wrong.hoverText} hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors`}
            >
              <RotateCcw className="w-4 h-4" aria-hidden="true" />
            </button>
          )}
        </div>
      </div>

      {/* Row 2: Question tiles row */}
      {tiles}
    </header>
  );
};
