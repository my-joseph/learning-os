"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { AnimatePresence, m } from "motion/react";
import { drawer, fade } from "@/lib/motion";
import { PanelRight, X } from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import type { LabListItem } from "@/lib/labModel";
import { DrillFilter, StatusMessage, ViewMode } from "@/hooks/types";
import { useSidePanelData } from "@/hooks/useSidePanelData";
import { Workspace, isLabId } from "@/lib/routes";
import { QuizPaginationBar } from "@/components/QuizPaginationBar";
import { ToastStack } from "@/components/ui/ToastStack";
import { StudioHeader } from "./StudioHeader";
import { StudioSidePanel } from "./StudioSidePanel";

interface StudioShellProps {
  workspace: Workspace;
  mathHref: string | null;
  codeHref: string | null;
  viewMode: ViewMode;
  currentDrill: DrillDocument | null;
  currentProblemIndex: number;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onResetAll: () => void;
  // DrillSwitcher & list
  drills: DrillListItem[];
  labs?: LabListItem[];
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

/** Page shell composing the sticky header, question tiles bar, status toasts, sticky side panel, and main workspace. */
export const StudioShell: React.FC<StudioShellProps> = ({
  workspace,
  mathHref,
  codeHref,
  viewMode,
  currentDrill,
  currentProblemIndex,
  theme,
  onToggleTheme,
  onResetAll,
  drills,
  labs = [],
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
  const [headerHeight, setHeaderHeight] = useState(108);
  const [isSideDrawerOpen, setIsSideDrawerOpen] = useState(false);
  const lastScrollYRef = useRef(0);
  const headerRef = useRef<HTMLElement | null>(null);
  const switcherRef = useRef<HTMLDivElement | null>(null);
  const genPopoverRef = useRef<HTMLDivElement | null>(null);

  const handleClearStatus = useCallback(() => {
    onStatusChange(null);
  }, [onStatusChange]);

  // Measure sticky header height so the sticky desktop aside clears it when visible.
  useEffect(() => {
    const el = headerRef.current;
    if (!el) return;
    const update = () => setHeaderHeight(el.offsetHeight);
    update();
    if (typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const {
    dueUnits,
    dueLoading,
    dueError,
    weakSpotUnits,
    weakLoading,
    weakError,
  } = useSidePanelData(
    currentDrill?.unitCode,
    currentDrill?.sessionSummary?.syncedToNotionAt
  );

  const openWeakCount = weakSpotUnits.reduce((acc, u) => acc + u.open.length, 0);
  const sidePanelCount = dueUnits.length + openWeakCount;

  // Close mobile drawer when switching drills or pressing Escape
  useEffect(() => {
    setIsSideDrawerOpen(false);
  }, [selectedDrillId]);

  useEffect(() => {
    if (!isSideDrawerOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsSideDrawerOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSideDrawerOpen]);

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
      <div className="mt-2">
        <QuizPaginationBar
          totalQuestions={currentDrill.problems.length}
          currentIndex={currentProblemIndex}
          problems={currentDrill.problems}
          viewMode={viewMode}
          isLab={isLabId(currentDrill.drillId)}
          onSelectQuestion={onSelectQuestion}
          onPrev={onPrevQuestion}
          onNext={onNextQuestion}
          onToggleViewMode={onToggleViewMode}
        />
      </div>
    ) : null;

  const containerMaxWidth =
    viewMode === "review" ? "max-w-5xl" : "max-w-[720px] lg:max-w-[1016px]";
  // Sticky header sits at top-2 (8 px); add 12 px breathing room when visible.
  const asideTopPx = showHeader ? headerHeight + 20 : 16;

  const sidePanelNode = (
    <StudioSidePanel
      workspace={workspace}
      currentUnitCode={currentDrill?.unitCode}
      dueUnits={dueUnits}
      dueLoading={dueLoading}
      dueError={dueError}
      weakSpotUnits={weakSpotUnits}
      weakLoading={weakLoading}
      weakError={weakError}
      onNavigate={() => setIsSideDrawerOpen(false)}
    />
  );

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 px-4 py-4 sm:py-6 transition-colors">
      <div className={`mx-auto ${containerMaxWidth}`}>
        {/* Provide sr-only h1 when no active drill workspace renders a visible h1 */}
        {viewMode === "quiz" && !currentDrill && (
          <h1 className="sr-only">Practice Studio</h1>
        )}

        <StudioHeader
          headerRef={headerRef}
          showHeader={showHeader}
          workspace={workspace}
          mathHref={mathHref}
          codeHref={codeHref}
          currentDrill={currentDrill}
          theme={theme}
          onToggleTheme={onToggleTheme}
          onResetAll={onResetAll}
          showDrillSwitcher={showDrillSwitcher}
          onToggleDrillSwitcher={() => setShowDrillSwitcher((prev) => !prev)}
          onCloseDrillSwitcher={() => setShowDrillSwitcher(false)}
          switcherRef={switcherRef}
          drills={drills}
          labs={labs}
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
          onOpenSideDrawer={
            viewMode === "quiz" ? () => setIsSideDrawerOpen(true) : undefined
          }
          sidePanelCount={sidePanelCount}
          tiles={tiles}
        />

        {viewMode === "quiz" ? (
          <div className="lg:grid lg:grid-cols-[minmax(0,1fr)_272px] lg:gap-6 lg:items-start">
            <div className="min-w-0">
              <main>{children}</main>
              <div className="lg:hidden mt-4 flex justify-center">
                <button
                  type="button"
                  onClick={() => setIsSideDrawerOpen(true)}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 transition-colors"
                >
                  <PanelRight className="w-3.5 h-3.5" />
                  <span>Due today &amp; weak spots</span>
                  {sidePanelCount > 0 && (
                    <span className="font-mono text-[11px] text-zinc-600 dark:text-zinc-300">
                      ({sidePanelCount})
                    </span>
                  )}
                </button>
              </div>
            </div>

            <aside
              aria-label="Due today and weak spots"
              style={
                {
                  "--aside-top": `${asideTopPx}px`,
                  "--aside-max-h": `calc(100vh - ${asideTopPx + 16}px)`,
                } as React.CSSProperties
              }
              className="hidden lg:block lg:sticky lg:top-[var(--aside-top)] lg:max-h-[var(--aside-max-h)] lg:overflow-y-auto lg:overscroll-contain transition-[top] duration-150"
            >
              {sidePanelNode}
            </aside>
          </div>
        ) : (
          <main>{children}</main>
        )}
      </div>

      <ToastStack status={status} onClearStatus={handleClearStatus} />

      <AnimatePresence>
      {viewMode === "quiz" && isSideDrawerOpen && (
        <m.div
          key="side-drawer"
          initial="hidden"
          animate="shown"
          exit="hidden"
          className="fixed inset-0 z-50 lg:hidden flex justify-end"
          role="dialog"
          aria-modal="true"
          aria-label="Due today and weak spots"
        >
          <m.div
            variants={fade}
            className="fixed inset-0 bg-zinc-950/40 backdrop-blur-[1px]"
            onClick={() => setIsSideDrawerOpen(false)}
          />
          <m.div variants={drawer} className="relative z-10 w-[min(calc(100vw-2.5rem),340px)] h-full overflow-y-auto bg-zinc-50 dark:bg-zinc-950 border-l border-zinc-200 dark:border-zinc-800 p-4 space-y-3 shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Study queue
              </span>
              <button
                type="button"
                onClick={() => setIsSideDrawerOpen(false)}
                aria-label="Close side panel"
                className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            {sidePanelNode}
          </m.div>
        </m.div>
      )}
      </AnimatePresence>
    </div>
  );
};
