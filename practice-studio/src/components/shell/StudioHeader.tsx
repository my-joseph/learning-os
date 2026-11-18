"use client";

import React, { useState, useRef, useEffect } from "react";
import { AnimatePresence, m } from "motion/react";
import { popover, presence, settle } from "@/lib/motion";
import Link from "next/link";
import {
  ArrowUpRight,
  Moon,
  MoreHorizontal,
  PanelRight,
  Plus,
  RotateCcw,
  Sun,
} from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import type { LabListItem } from "@/lib/labModel";
import { DrillFilter, StatusMessage } from "@/hooks/types";
import { Workspace } from "@/lib/routes";
import { DrillSwitcher } from "./DrillSwitcher";
import { GeneratePopover } from "./GeneratePopover";

interface StudioHeaderProps {
  headerRef?: React.RefObject<HTMLElement>;
  showHeader: boolean;
  workspace: Workspace;
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
  selectedDrillId: string;
  drillSearch: string;
  onSearchChange: (value: string) => void;
  drillFilter: DrillFilter;
  onFilterChange: (filter: DrillFilter) => void;
  onSelectDrill: (drillId: string) => void;
  // GeneratePopover props
  showGenPopover: boolean;
  onToggleGenPopover: () => void;
  onCloseGenPopover: () => void;
  genPopoverRef: React.RefObject<HTMLDivElement>;
  onGenerated: (drillId: string) => Promise<void>;
  onStatusChange: (status: StatusMessage | null) => void;
  // Side drawer (mobile / <1024px)
  onOpenSideDrawer?: () => void;
  sidePanelCount?: number;
  // Row 2: Question tiles bar
  tiles?: React.ReactNode;
}

/** Slim one-row Studio header with workspace switch, drill switcher, theme toggle, Notion link, and ⋯ menu. */
export const StudioHeader: React.FC<StudioHeaderProps> = ({
  headerRef,
  showHeader,
  workspace,
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
  selectedDrillId,
  drillSearch,
  onSearchChange,
  drillFilter,
  onFilterChange,
  onSelectDrill,
  showGenPopover,
  onToggleGenPopover,
  onCloseGenPopover,
  genPopoverRef,
  onGenerated,
  onStatusChange,
  onOpenSideDrawer,
  sidePanelCount = 0,
  tiles,
}) => {
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  // The switch pill slides as soon as it is clicked, before the new route renders.
  const [pillWorkspace, setPillWorkspace] = useState<Workspace>(workspace);
  useEffect(() => setPillWorkspace(workspace), [workspace]);
  const moreMenuRef = useRef<HTMLDivElement | null>(null);
  const moreButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (moreMenuRef.current && !moreMenuRef.current.contains(e.target as Node)) {
        setShowMoreMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!showHeader) {
      setShowMoreMenu(false);
    }
  }, [showHeader]);

  const workspaceOptions: { id: Workspace; label: string; href: string | null }[] = [
    { id: "math", label: "Math", href: mathHref },
    { id: "code", label: "Programming", href: codeHref },
  ];

  return (
    <header
      ref={headerRef}
      className={`sticky top-2 z-50 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 rounded-2xl px-3.5 py-2.5 mb-6 shadow-sm transition-all duration-150 ${
        showHeader
          ? "translate-y-0 opacity-100"
          : "-translate-y-[130%] opacity-0 pointer-events-none"
      }`}
    >
      {/* Slim one-row header: below 640px collapses to switcher + ⋯ menu */}
      <div className="flex items-center justify-between gap-2">
        {/* Left: Workspace switch (>=640px) + Drill switcher */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <nav
            aria-label="Workspace"
            className="relative hidden sm:grid grid-cols-2 items-center rounded-lg bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-800 p-0.5 shrink-0"
          >
            <m.span
              aria-hidden
              className="absolute top-0.5 bottom-0.5 left-0.5 w-[calc(50%-2px)] rounded-md bg-white dark:bg-zinc-900 shadow-sm"
              initial={false}
              animate={{ x: pillWorkspace === "code" ? "100%" : "0%" }}
              transition={settle}
            />
            {workspaceOptions.map((opt) => {
              const isActive = workspace === opt.id;
              const isShown = pillWorkspace === opt.id;
              const cls = `relative z-10 px-2.5 py-1 rounded-md text-xs font-medium text-center transition-colors duration-200 whitespace-nowrap ${
                isShown
                  ? "text-zinc-900 dark:text-zinc-100"
                  : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200"
              }`;
              if (!opt.href) {
                return (
                  <span
                    key={opt.id}
                    aria-current={isActive ? "page" : undefined}
                    aria-disabled={!isActive ? true : undefined}
                    className={`${cls} ${!isActive ? "opacity-50 cursor-not-allowed" : ""}`}
                  >
                    {opt.label}
                  </span>
                );
              }
              return (
                <Link
                  key={opt.id}
                  href={opt.href}
                  aria-current={isActive ? "page" : undefined}
                  onClick={() => setPillWorkspace(opt.id)}
                  className={cls}
                >
                  {opt.label}
                </Link>
              );
            })}
          </nav>

          <DrillSwitcher
            isOpen={showDrillSwitcher}
            onToggle={onToggleDrillSwitcher}
            onClose={onCloseDrillSwitcher}
            switcherRef={switcherRef}
            currentDrill={currentDrill}
            drills={drills}
            labs={labs}
            selectedDrillId={selectedDrillId}
            drillSearch={drillSearch}
            onSearchChange={onSearchChange}
            drillFilter={drillFilter}
            onFilterChange={onFilterChange}
            onSelectDrill={onSelectDrill}
          />
        </div>

        {/* Right: Theme toggle (>=640px) + Notion link (>=640px) + ⋯ menu */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={onToggleTheme}
            title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
            aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
            className="hidden sm:inline-flex items-center justify-center w-9 h-9 rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            {theme === "light" ? (
              <Moon className="w-4 h-4" />
            ) : (
              <Sun className="w-4 h-4" />
            )}
          </button>

          {currentDrill?.unitNotionUrl && (
            <a
              href={currentDrill.unitNotionUrl}
              target="_blank"
              rel="noopener noreferrer"
              title="Open unit page in Notion"
              className="hidden sm:inline-flex items-center gap-1 h-9 px-2.5 rounded-lg text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <span>Notion</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          )}

          {/* Single ⋯ overflow menu for secondary controls & mobile items */}
          <div className="relative" ref={moreMenuRef}>
            <button
              ref={moreButtonRef}
              type="button"
              onClick={() => setShowMoreMenu((prev) => !prev)}
              aria-expanded={showMoreMenu}
              aria-label="More actions"
              title="More actions"
              className="inline-flex items-center justify-center w-9 h-9 rounded-lg text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>

            <AnimatePresence>
            {showMoreMenu && (
              <m.div
                variants={popover}
                {...presence}
                style={{ transformOrigin: "top right" }}
                className="absolute right-0 mt-2 w-64 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-lg p-2.5 z-50 text-xs space-y-2">
                {/* Below 640px items: workspace switch, theme toggle, Notion link */}
                <div className="sm:hidden space-y-1 pb-2 border-b border-zinc-200 dark:border-zinc-800">
                  <div className="grid grid-cols-2 gap-1 p-0.5 rounded-lg bg-zinc-100 dark:bg-zinc-800">
                    {workspaceOptions.map((opt) => {
                      const isActive = workspace === opt.id;
                      const cls = `px-2 py-1.5 rounded-md text-center text-xs font-medium transition-colors ${
                        isActive
                          ? "bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 shadow-sm"
                          : "text-zinc-500 dark:text-zinc-400"
                      }`;
                      if (!opt.href) {
                        return (
                          <span key={opt.id} className={`${cls} opacity-50`}>
                            {opt.label}
                          </span>
                        );
                      }
                      return (
                        <Link
                          key={opt.id}
                          href={opt.href}
                          onClick={() => setShowMoreMenu(false)}
                          className={cls}
                        >
                          {opt.label}
                        </Link>
                      );
                    })}
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      onToggleTheme();
                    }}
                    className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                  >
                    {theme === "light" ? (
                      <Moon className="w-3.5 h-3.5" />
                    ) : (
                      <Sun className="w-3.5 h-3.5" />
                    )}
                    <span>{theme === "light" ? "Dark mode" : "Light mode"}</span>
                  </button>

                  {currentDrill?.unitNotionUrl && (
                    <a
                      href={currentDrill.unitNotionUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => setShowMoreMenu(false)}
                      className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                    >
                      <span>Open unit in Notion</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>

                {/* Actions */}
                <div className="space-y-0.5">
                  {onOpenSideDrawer && (
                    <button
                      type="button"
                      onClick={() => {
                        setShowMoreMenu(false);
                        onOpenSideDrawer();
                      }}
                      className="lg:hidden w-full flex items-center justify-between gap-2 px-2 py-1.5 rounded-lg text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                    >
                      <span className="flex items-center gap-2">
                        <PanelRight className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400" />
                        <span>Due today &amp; weak spots</span>
                      </span>
                      {sidePanelCount > 0 && (
                        <span className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                          {sidePanelCount}
                        </span>
                      )}
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={onToggleGenPopover}
                    className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400" />
                    <span>Generate drill set</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setShowMoreMenu(false);
                      moreButtonRef.current?.focus();
                      onResetAll();
                    }}
                    className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-rose-600 dark:text-rose-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reset all questions</span>
                  </button>
                </div>

                <GeneratePopover
                  isOpen={showGenPopover}
                  onToggle={onToggleGenPopover}
                  onClose={onCloseGenPopover}
                  popoverRef={genPopoverRef}
                  currentDrill={currentDrill}
                  onGenerated={async (id) => {
                    setShowMoreMenu(false);
                    await onGenerated(id);
                  }}
                  onStatusChange={onStatusChange}
                />
              </m.div>
            )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Row 2: Question tiles row */}
      {tiles}
    </header>
  );
};
