"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, m } from "motion/react";
import {
  ArrowUpRight,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  RotateCcw,
  Search,
} from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import type { LabListItem } from "@/lib/labModel";
import { DrillFilter } from "@/hooks/types";
import { Workspace, isLabId } from "@/lib/routes";
import { statusTone } from "@/lib/statusTone";
import { settle, sidebarContent } from "@/lib/motion";
import { Button } from "@/components/ui/shadcn/Button";
import { ThemeToggleButton } from "@/components/ui/ThemeToggleButton";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";
import { WorkspaceSwitch } from "@/components/workspace/WorkspaceSwitch";
import { DrillSwitcher } from "./DrillSwitcher";

const SIDEBAR_STORAGE_KEY = "practice-studio:sidebar-collapsed";
const noop = () => {};

export interface StudioSidebarProps {
  workspace: Workspace;
  pillWorkspace: Workspace;
  onSelectWorkspace: (workspace: Workspace) => void;
  mathHref: string | null;
  codeHref: string | null;
  currentDrill: DrillDocument | null;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onResetAll: () => void;
  drills: DrillListItem[];
  labs?: LabListItem[];
  dueUnitCodes?: readonly string[];
  selectedDrillId: string;
  drillSearch: string;
  onSearchChange: (value: string) => void;
  drillFilter: DrillFilter;
  onFilterChange: (filter: DrillFilter) => void;
  onSelectDrill: (drillId: string) => void;
  onOpenGenPopover: () => void;
  embedded?: boolean;
  initialCollapsed?: boolean;
  onCloseDrawer?: () => void;
}

interface ExpandedSidebarBodyProps {
  workspace: Workspace;
  pillWorkspace: Workspace;
  onSelectWorkspace: (workspace: Workspace) => void;
  mathHref: string | null;
  codeHref: string | null;
  currentDrill: DrillDocument | null;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onResetAll: () => void;
  resetAllLabel: string;
  drills: DrillListItem[];
  labs: LabListItem[];
  dueUnitCodes: readonly string[];
  selectedDrillId: string;
  drillSearch: string;
  onSearchChange: (value: string) => void;
  drillFilter: DrillFilter;
  onFilterChange: (filter: DrillFilter) => void;
  onSelectDrill: (drillId: string) => void;
  onOpenGenPopover: () => void;
  embedded: boolean;
  onCollapse?: () => void;
  onCloseDrawer?: () => void;
  searchInputRef: React.RefObject<HTMLInputElement | null>;
  focusSearchOnMount: boolean;
  onFocusedSearch: () => void;
}

const ExpandedSidebarBody: React.FC<ExpandedSidebarBodyProps> = ({
  workspace,
  pillWorkspace,
  onSelectWorkspace,
  mathHref,
  codeHref,
  currentDrill,
  theme,
  onToggleTheme,
  onResetAll,
  resetAllLabel,
  drills,
  labs,
  dueUnitCodes,
  selectedDrillId,
  drillSearch,
  onSearchChange,
  drillFilter,
  onFilterChange,
  onSelectDrill,
  onOpenGenPopover,
  embedded,
  onCollapse,
  onCloseDrawer,
  searchInputRef,
  focusSearchOnMount,
  onFocusedSearch,
}) => {
  const switcherRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!focusSearchOnMount) return;
    const rafId = window.requestAnimationFrame(() => {
      searchInputRef.current?.focus();
      onFocusedSearch();
    });
    return () => window.cancelAnimationFrame(rafId);
  }, [focusSearchOnMount, onFocusedSearch, searchInputRef]);

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      {/* Top bar: MTH / PRG segmented switcher + Collapse button (hidden when embedded in mobile Drawer) */}
      <div
        className={`shrink-0 flex items-center justify-between gap-2 px-2.5 pt-2.5 pb-2 border-b border-zinc-200/80 dark:border-zinc-800/80 ${
          embedded ? "pr-12" : ""
        }`}
      >
        <WorkspaceSwitch
          variant="sidebar"
          workspace={workspace}
          pillWorkspace={pillWorkspace}
          onSelectWorkspace={onSelectWorkspace}
          mathHref={mathHref}
          codeHref={codeHref}
        />

        {!embedded && onCollapse && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="iconSm"
                onClick={onCollapse}
                aria-label="Collapse sidebar"
                className="min-h-[44px] min-w-[44px] lg:min-h-[32px] lg:min-w-[32px] lg:h-8 lg:w-8 rounded-lg text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 shrink-0"
              >
                <PanelLeftClose className="w-4 h-4" aria-hidden="true" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">Collapse sidebar</TooltipContent>
          </Tooltip>
        )}
      </div>

      {/* Middle curriculum tree */}
      <DrillSwitcher
        mode="sidebar"
        searchInputRef={searchInputRef}
        isOpen={true}
        onToggle={noop}
        onClose={embedded ? onCloseDrawer ?? noop : noop}
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

      {/* Bottom utility footer bar */}
      <div className="shrink-0 mx-2.5 mb-2.5 rounded-xl bg-zinc-50 dark:bg-zinc-950/70 border border-zinc-200/80 dark:border-zinc-800 p-1.5 flex items-center justify-between gap-1">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="compact"
              onClick={onOpenGenPopover}
              aria-label="Generate drill set"
              className="min-h-[44px] lg:min-h-[32px] lg:h-8 px-2.5 rounded-lg border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 shrink-0"
            >
              <Plus className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
              <span>Generate</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Generate drill set</TooltipContent>
        </Tooltip>

        <div className="flex items-center gap-0.5 shrink-0">
          {currentDrill?.unitNotionUrl && (
            <Tooltip>
              <TooltipTrigger asChild>
                <a
                  href={currentDrill.unitNotionUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Open unit page in Notion"
                  className="inline-flex items-center justify-center min-h-[44px] min-w-[44px] lg:min-h-[32px] lg:min-w-[32px] lg:h-8 lg:w-8 rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                >
                  <ArrowUpRight className="w-4 h-4" aria-hidden="true" />
                </a>
              </TooltipTrigger>
              <TooltipContent side="top">Open unit page in Notion</TooltipContent>
            </Tooltip>
          )}

          <ThemeToggleButton
            theme={theme}
            onToggle={onToggleTheme}
            className="inline-flex items-center justify-center min-h-[44px] min-w-[44px] lg:min-h-[32px] lg:min-w-[32px] lg:h-8 lg:w-8 rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          />

          {currentDrill && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="iconSm"
                  onClick={onResetAll}
                  aria-label={resetAllLabel}
                  className={`min-h-[44px] min-w-[44px] lg:min-h-[32px] lg:min-w-[32px] lg:h-8 lg:w-8 rounded-lg text-zinc-600 dark:text-zinc-400 ${statusTone.wrong.hoverText} hover:bg-zinc-100 dark:hover:bg-zinc-800`}
                >
                  <RotateCcw className="w-4 h-4" aria-hidden="true" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="top">{resetAllLabel}</TooltipContent>
            </Tooltip>
          )}
        </div>
      </div>
    </div>
  );
};

/** Docked left navigation sidebar supporting desktop expanded/collapsed rail and mobile embedded drawer mode. */
export const StudioSidebar: React.FC<StudioSidebarProps> = ({
  workspace,
  pillWorkspace,
  onSelectWorkspace,
  mathHref,
  codeHref,
  currentDrill,
  theme,
  onToggleTheme,
  onResetAll,
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
  embedded = false,
  initialCollapsed = false,
  onCloseDrawer,
}) => {
  const [collapsed, setCollapsed] = useState(initialCollapsed);
  const [focusSearchOnExpand, setFocusSearchOnExpand] = useState(false);
  const searchInputRef = useRef<HTMLInputElement | null>(null);

  const resetAllLabel = isLabId(selectedDrillId)
    ? "Reset all milestones"
    : workspace === "code"
    ? "Reset all problems"
    : "Reset all questions";

  const updateCollapsed = useCallback(
    (updater: boolean | ((prev: boolean) => boolean)) => {
      setCollapsed((prev) => {
        const next = typeof updater === "function" ? updater(prev) : updater;
        try {
          window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(next));
        } catch {
          // ignore localStorage access failures
        }
        return next;
      });
    },
    []
  );

  useEffect(() => {
    if (embedded) return;
    try {
      const saved = window.localStorage.getItem(SIDEBAR_STORAGE_KEY);
      if (saved === "true") {
        setCollapsed(true);
      } else if (saved === "false") {
        setCollapsed(false);
      }
    } catch {
      // ignore localStorage access failures
    }
  }, [embedded]);

  useEffect(() => {
    if (embedded) return;
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
      updateCollapsed((prev) => !prev);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [embedded, updateCollapsed]);

  const handleFocusedSearch = useCallback(() => {
    setFocusSearchOnExpand(false);
  }, []);

  if (embedded) {
    return (
      <div className="w-full h-full border-0 shadow-none rounded-none flex flex-col overflow-hidden bg-white dark:bg-zinc-900">
        <ExpandedSidebarBody
          workspace={workspace}
          pillWorkspace={pillWorkspace}
          onSelectWorkspace={onSelectWorkspace}
          mathHref={mathHref}
          codeHref={codeHref}
          currentDrill={currentDrill}
          theme={theme}
          onToggleTheme={onToggleTheme}
          onResetAll={onResetAll}
          resetAllLabel={resetAllLabel}
          drills={drills}
          labs={labs}
          dueUnitCodes={dueUnitCodes}
          selectedDrillId={selectedDrillId}
          drillSearch={drillSearch}
          onSearchChange={onSearchChange}
          drillFilter={drillFilter}
          onFilterChange={onFilterChange}
          onSelectDrill={onSelectDrill}
          onOpenGenPopover={onOpenGenPopover}
          embedded={true}
          onCloseDrawer={onCloseDrawer}
          searchInputRef={searchInputRef}
          focusSearchOnMount={false}
          onFocusedSearch={handleFocusedSearch}
        />
      </div>
    );
  }

  return (
    <m.aside
      aria-label="Practice navigation"
      initial={false}
      animate={{ width: collapsed ? 56 : 272 }}
      transition={settle}
      className="hidden lg:flex lg:flex-col shrink-0 sticky top-4 h-[calc(100vh-2rem)] rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm overflow-hidden motion-reduce:transition-none"
    >
      <AnimatePresence mode="wait" initial={false}>
        {collapsed ? (
          <m.div
            key="collapsed"
            variants={sidebarContent}
            initial="hidden"
            animate="shown"
            exit="exit"
            className="flex-1 min-h-0 flex flex-col items-center justify-between py-2.5 px-1.5 h-full"
          >
            <div className="flex flex-col items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="iconSm"
                    onClick={() => updateCollapsed(false)}
                    aria-label="Expand sidebar"
                    className="lg:min-h-[32px] lg:min-w-[32px] lg:h-8 lg:w-8 rounded-lg text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                  >
                    <PanelLeftOpen className="w-4 h-4" aria-hidden="true" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">Expand sidebar</TooltipContent>
              </Tooltip>

              <WorkspaceSwitch
                variant="rail"
                workspace={workspace}
                pillWorkspace={pillWorkspace}
                onSelectWorkspace={onSelectWorkspace}
                mathHref={mathHref}
                codeHref={codeHref}
                className="relative grid grid-rows-2 items-center rounded-xl bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-800 p-1"
              />

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="iconSm"
                    onClick={() => {
                      setFocusSearchOnExpand(true);
                      updateCollapsed(false);
                    }}
                    aria-label="Browse drills"
                    className="lg:min-h-[32px] lg:min-w-[32px] lg:h-8 lg:w-8 rounded-lg text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                  >
                    <Search className="w-4 h-4" aria-hidden="true" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">Browse drills</TooltipContent>
              </Tooltip>
            </div>

            <div className="flex flex-col items-center gap-1 rounded-xl bg-zinc-50 dark:bg-zinc-950/70 border border-zinc-200/80 dark:border-zinc-800 p-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="iconSm"
                    onClick={onOpenGenPopover}
                    aria-label="Generate drill set"
                    className="lg:min-h-[32px] lg:min-w-[32px] lg:h-8 lg:w-8 rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                  >
                    <Plus className="w-4 h-4" aria-hidden="true" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">Generate drill set</TooltipContent>
              </Tooltip>

              {currentDrill?.unitNotionUrl && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <a
                      href={currentDrill.unitNotionUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label="Open unit page in Notion"
                      className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                    >
                      <ArrowUpRight className="w-4 h-4" aria-hidden="true" />
                    </a>
                  </TooltipTrigger>
                  <TooltipContent side="right">Open unit page in Notion</TooltipContent>
                </Tooltip>
              )}

              <ThemeToggleButton
                theme={theme}
                onToggle={onToggleTheme}
                className="inline-flex items-center justify-center lg:min-h-[32px] lg:min-w-[32px] lg:h-8 lg:w-8 rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              />

              {currentDrill && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="iconSm"
                      onClick={onResetAll}
                      aria-label={resetAllLabel}
                      className={`lg:min-h-[32px] lg:min-w-[32px] lg:h-8 lg:w-8 rounded-lg text-zinc-600 dark:text-zinc-400 ${statusTone.wrong.hoverText} hover:bg-zinc-100 dark:hover:bg-zinc-800`}
                    >
                      <RotateCcw className="w-4 h-4" aria-hidden="true" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">{resetAllLabel}</TooltipContent>
                </Tooltip>
              )}
            </div>
          </m.div>
        ) : (
          <m.div
            key="expanded"
            variants={sidebarContent}
            initial="hidden"
            animate="shown"
            exit="exit"
            className="flex-1 min-h-0 flex flex-col"
          >
            <ExpandedSidebarBody
              workspace={workspace}
              pillWorkspace={pillWorkspace}
              onSelectWorkspace={onSelectWorkspace}
              mathHref={mathHref}
              codeHref={codeHref}
              currentDrill={currentDrill}
              theme={theme}
              onToggleTheme={onToggleTheme}
              onResetAll={onResetAll}
              resetAllLabel={resetAllLabel}
              drills={drills}
              labs={labs}
              dueUnitCodes={dueUnitCodes}
              selectedDrillId={selectedDrillId}
              drillSearch={drillSearch}
              onSearchChange={onSearchChange}
              drillFilter={drillFilter}
              onFilterChange={onFilterChange}
              onSelectDrill={onSelectDrill}
              onOpenGenPopover={onOpenGenPopover}
              embedded={false}
              onCollapse={() => updateCollapsed(true)}
              searchInputRef={searchInputRef}
              focusSearchOnMount={focusSearchOnExpand}
              onFocusedSearch={handleFocusedSearch}
            />
          </m.div>
        )}
      </AnimatePresence>
    </m.aside>
  );
};
