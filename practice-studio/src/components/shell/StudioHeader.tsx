"use client";

import React from "react";
import Link from "next/link";
import { ArrowUpRight, Moon, RotateCcw, Sun } from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import { DrillFilter, StatusMessage } from "@/hooks/types";
import { Workspace } from "@/lib/routes";
import { DrillSwitcher } from "./DrillSwitcher";
import { GeneratePopover } from "./GeneratePopover";

interface StudioHeaderProps {
  showHeader: boolean;
  workspace: Workspace;
  mathHref: string | null;
  codeHref: string | null;
  currentDrill: DrillDocument | null;
  liveScore: number;
  maxScore: number;
  accuracyPct: number;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onResetAll: () => void;
  // DrillSwitcher props
  showDrillSwitcher: boolean;
  onToggleDrillSwitcher: () => void;
  onCloseDrillSwitcher: () => void;
  switcherRef: React.RefObject<HTMLDivElement>;
  drills: DrillListItem[];
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
  // Row 2: Question tiles bar
  tiles?: React.ReactNode;
}

/** Sticky two-row Studio header with drill switcher, score summary, theme toggle, and tiles slot. */
export const StudioHeader: React.FC<StudioHeaderProps> = ({
  showHeader,
  workspace,
  mathHref,
  codeHref,
  currentDrill,
  liveScore,
  maxScore,
  accuracyPct,
  theme,
  onToggleTheme,
  onResetAll,
  showDrillSwitcher,
  onToggleDrillSwitcher,
  onCloseDrillSwitcher,
  switcherRef,
  drills,
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
  tiles,
}) => {
  const workspaceOptions: { id: Workspace; label: string; href: string | null }[] = [
    { id: "math", label: "Math", href: mathHref },
    { id: "code", label: "Programming", href: codeHref },
  ];

  return (
    <header
      className={`sticky top-2 z-50 bg-white/95 dark:bg-[#151924]/95 backdrop-blur-md border border-slate-200 dark:border-[#2c354d] rounded-2xl p-3.5 mb-5 shadow-md transition-all duration-300 ease-in-out ${
        showHeader
          ? "translate-y-0 opacity-100"
          : "-translate-y-[130%] opacity-0 pointer-events-none"
      }`}
    >
      {/* Row 1: Workspace Switch + Smart Drill Switcher + Notion Unit | Score + Reset + Theme */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3">
        {/* Left Zone: Workspace Switch, Smart Drill Switcher & Generate Popover */}
        <div className="flex flex-wrap items-center gap-2.5 min-w-0">
          <nav
            aria-label="Workspace"
            className="inline-flex items-center rounded-xl bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 p-1 shrink-0"
          >
            {workspaceOptions.map((opt) => {
              const isActive = workspace === opt.id;
              const cls = `px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${
                isActive
                  ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm"
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
            selectedDrillId={selectedDrillId}
            drillSearch={drillSearch}
            onSearchChange={onSearchChange}
            drillFilter={drillFilter}
            onFilterChange={onFilterChange}
            onSelectDrill={onSelectDrill}
          />

          {/* Notion Unit Quick Link */}
          {currentDrill?.unitNotionUrl && (
            <a
              href={currentDrill.unitNotionUrl}
              target="_blank"
              rel="noopener noreferrer"
              title="Open this unit page in Notion"
              className="inline-flex items-center gap-1.5 h-10 px-3 rounded-xl bg-sky-50 dark:bg-sky-500/10 hover:bg-sky-100 dark:hover:bg-sky-500/20 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-500/30 text-xs font-semibold transition-colors shrink-0"
            >
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Notion Unit</span>
            </a>
          )}

          <GeneratePopover
            isOpen={showGenPopover}
            onToggle={onToggleGenPopover}
            onClose={onCloseGenPopover}
            popoverRef={genPopoverRef}
            currentDrill={currentDrill}
            onGenerated={onGenerated}
            onStatusChange={onStatusChange}
          />
        </div>

        {/* Right Zone: Live Score + Reset + Theme (Strictly single line, no redundant Review & Sync button) */}
        <div className="flex items-center justify-end gap-2 shrink-0">
          <span className="inline-flex items-center h-9 text-xs font-bold px-3 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30 whitespace-nowrap">
            Score: {liveScore} / {maxScore} ({accuracyPct}%)
          </span>

          <button
            type="button"
            onClick={onResetAll}
            title="Reset all questions in this drill"
            className="inline-flex items-center justify-center w-9 h-9 bg-slate-100 dark:bg-[#1d2333] hover:bg-rose-50 dark:hover:bg-rose-500/20 text-slate-600 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-300 rounded-xl border border-slate-200 dark:border-[#2c354d] transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={onToggleTheme}
            title={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
            className="inline-flex items-center justify-center w-9 h-9 bg-slate-100 dark:bg-[#1d2333] hover:bg-slate-200 dark:hover:bg-[#252e42] text-slate-700 dark:text-slate-200 rounded-xl border border-slate-200 dark:border-[#2c354d] transition-colors"
          >
            {theme === "light" ? (
              <Moon className="w-4 h-4 text-indigo-600" />
            ) : (
              <Sun className="w-4 h-4 text-amber-400" />
            )}
          </button>
        </div>
      </div>

      {/* Row 2: Integrated Question Stepper Row */}
      {tiles}
    </header>
  );
};
