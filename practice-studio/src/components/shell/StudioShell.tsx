"use client";

import React, { useState, useEffect, useRef } from "react";
import { AlertCircle, CheckCircle2, X } from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import { DrillFilter, StatusMessage, ViewMode } from "@/hooks/types";
import { Workspace } from "@/lib/routes";
import { QuizPaginationBar } from "@/components/QuizPaginationBar";
import { StudioHeader } from "./StudioHeader";

interface StudioShellProps {
  workspace: Workspace;
  mathHref: string | null;
  codeHref: string | null;
  viewMode: ViewMode;
  currentDrill: DrillDocument | null;
  currentProblemIndex: number;
  liveScore: number;
  maxScore: number;
  accuracyPct: number;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onResetAll: () => void;
  // DrillSwitcher & list
  drills: DrillListItem[];
  selectedDrillId: string;
  drillSearch: string;
  onSearchChange: (value: string) => void;
  drillFilter: DrillFilter;
  onFilterChange: (filter: DrillFilter) => void;
  onSelectDrill: (drillId: string) => void;
  // GeneratePopover
  showGenPopover: boolean;
  onShowGenPopoverChange: (open: boolean) => void;
  onGenerated: (drillId: string) => Promise<void>;
  // Pagination / tiles
  onSelectQuestion: (idx: number) => void;
  onPrevQuestion: () => void;
  onNextQuestion: () => void;
  onToggleViewMode: (mode: ViewMode) => void;
  // Status banner
  status: StatusMessage | null;
  onStatusChange: (status: StatusMessage | null) => void;
  children: React.ReactNode;
}

/** Page shell composing the sticky header, question tiles bar, status banner, and main workspace. */
export const StudioShell: React.FC<StudioShellProps> = ({
  workspace,
  mathHref,
  codeHref,
  viewMode,
  currentDrill,
  currentProblemIndex,
  liveScore,
  maxScore,
  accuracyPct,
  theme,
  onToggleTheme,
  onResetAll,
  drills,
  selectedDrillId,
  drillSearch,
  onSearchChange,
  drillFilter,
  onFilterChange,
  onSelectDrill,
  showGenPopover,
  onShowGenPopoverChange,
  onGenerated,
  onSelectQuestion,
  onPrevQuestion,
  onNextQuestion,
  onToggleViewMode,
  status,
  onStatusChange,
  children,
}) => {
  const [showDrillSwitcher, setShowDrillSwitcher] = useState(false);
  const [showHeader, setShowHeader] = useState(true);
  const lastScrollYRef = useRef(0);
  const switcherRef = useRef<HTMLDivElement | null>(null);
  const genPopoverRef = useRef<HTMLDivElement | null>(null);

  // Auto-hide sticky header on scroll down, reveal on scroll up
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      const prevScrollY = lastScrollYRef.current;
      const diff = currentScrollY - prevScrollY;

      if (currentScrollY <= 40) {
        setShowHeader(true);
      } else if (diff > 8) {
        setShowHeader(false);
        setShowDrillSwitcher(false);
        onShowGenPopoverChange(false);
      } else if (diff < -8) {
        setShowHeader(true);
      }

      lastScrollYRef.current = currentScrollY;
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [onShowGenPopoverChange]);

  // Close popovers on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (switcherRef.current && !switcherRef.current.contains(e.target as Node)) {
        setShowDrillSwitcher(false);
      }
      if (genPopoverRef.current && !genPopoverRef.current.contains(e.target as Node)) {
        onShowGenPopoverChange(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onShowGenPopoverChange]);

  const tiles =
    currentDrill && currentDrill.problems.length > 0 ? (
      <div className="mt-2.5">
        <QuizPaginationBar
          totalQuestions={currentDrill.problems.length}
          currentIndex={currentProblemIndex}
          problems={currentDrill.problems}
          viewMode={viewMode}
          onSelectQuestion={onSelectQuestion}
          onPrev={onPrevQuestion}
          onNext={onNextQuestion}
          onToggleViewMode={onToggleViewMode}
        />
      </div>
    ) : null;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0d1017] text-slate-900 dark:text-slate-100 p-3 md:p-5 lg:p-6 transition-colors">
      <div
        className={`mx-auto transition-[max-width] duration-200 ${
          viewMode === "review" ? "max-w-7xl" : "max-w-5xl"
        }`}
      >
        {/* ===================================================================== */}
        {/* SINGLE UNIFIED STICKY WORKSPACE BAR (Strictly 2 Rows, Auto-hides)     */}
        {/* ===================================================================== */}
        {viewMode === "quiz" && (
          <h1 className="sr-only">
            {currentDrill
              ? `${currentDrill.unitTitle || currentDrill.unitCode} Practice`
              : "Practice Studio"}
          </h1>
        )}

        <StudioHeader
          showHeader={showHeader}
          workspace={workspace}
          mathHref={mathHref}
          codeHref={codeHref}
          currentDrill={currentDrill}
          liveScore={liveScore}
          maxScore={maxScore}
          accuracyPct={accuracyPct}
          theme={theme}
          onToggleTheme={onToggleTheme}
          onResetAll={onResetAll}
          showDrillSwitcher={showDrillSwitcher}
          onToggleDrillSwitcher={() => setShowDrillSwitcher((prev) => !prev)}
          onCloseDrillSwitcher={() => setShowDrillSwitcher(false)}
          switcherRef={switcherRef}
          drills={drills}
          selectedDrillId={selectedDrillId}
          drillSearch={drillSearch}
          onSearchChange={onSearchChange}
          drillFilter={drillFilter}
          onFilterChange={onFilterChange}
          onSelectDrill={onSelectDrill}
          showGenPopover={showGenPopover}
          onToggleGenPopover={() => onShowGenPopoverChange(!showGenPopover)}
          onCloseGenPopover={() => onShowGenPopoverChange(false)}
          genPopoverRef={genPopoverRef}
          onGenerated={onGenerated}
          onStatusChange={onStatusChange}
          tiles={tiles}
        />

        {/* Status Notification Banner */}
        {status && (
          <div
            className={`p-3.5 rounded-xl mb-5 text-xs md:text-sm flex items-center justify-between border ${
              status.type === "pass"
                ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-500/30"
                : status.type === "fail"
                ? "bg-rose-50 dark:bg-rose-500/10 text-rose-800 dark:text-rose-300 border-rose-200 dark:border-rose-500/30"
                : "bg-amber-50 dark:bg-amber-500/10 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-500/30"
            }`}
          >
            <div className="flex items-center gap-2">
              {status.type === "pass" ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
              )}
              <span dangerouslySetInnerHTML={{ __html: status.text }} />
            </div>
            <button
              type="button"
              onClick={() => onStatusChange(null)}
              className="inline-flex items-center justify-center w-7 h-7 rounded-lg text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* ===================================================================== */}
        {/* MAIN WORKSPACE AREA: LOADING / QUIZ FOCUS / PRE-SYNC REVIEW           */}
        {/* ===================================================================== */}
        <main>{children}</main>
      </div>
    </div>
  );
};
