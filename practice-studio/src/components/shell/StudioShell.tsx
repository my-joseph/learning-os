"use client";

import React, { useState, useEffect, useId, useRef, useCallback } from "react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import type { SyncState } from "@/hooks/useProgressSync";
import type { LabListItem } from "@/lib/labModel";
import { DrillFilter, PracticeStatusOverride, StatusMessage, ViewMode } from "@/hooks/types";
import { useSidePanelData } from "@/hooks/useSidePanelData";
import { Workspace, isLabId } from "@/lib/routes";
import { QuizPaginationBar } from "@/components/QuizPaginationBar";
import { ToastStack } from "@/components/ui/ToastStack";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerTitle,
} from "@/components/ui/shadcn/Drawer";
import { WorkspaceSwitch } from "@/components/workspace/WorkspaceSwitch";
import { StudioHeader } from "./StudioHeader";
import { StudioSidePanel } from "./StudioSidePanel";
import { GeneratePopover } from "./GeneratePopover";

interface StudioShellProps {
  workspace: Workspace;
  mathHref: string | null;
  codeHref: string | null;
  viewMode: ViewMode;
  currentDrill: DrillDocument | null;
  statusOverride?: PracticeStatusOverride;
  syncState?: SyncState;
  isSyncing?: boolean;
  isLoadingDrill?: boolean;
  drillNotFound?: boolean;
  currentProblemIndex: number;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onResetAll: () => void;
  // DrillSwitcher & list
  drills: DrillListItem[];
  allWorkspaceDrills?: DrillListItem[];
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
  onToggleViewMode: (mode: ViewMode) => void;
  // Status banner
  status: StatusMessage | null;
  onStatusChange: (status: StatusMessage | null) => void;
  children: React.ReactNode;
}

/** Page shell composing the fixed left workspace rail, sticky header, tiles bar, status toasts, sticky side panel, and main workspace. */
export const StudioShell: React.FC<StudioShellProps> = ({
  workspace,
  mathHref,
  codeHref,
  viewMode,
  currentDrill,
  statusOverride,
  syncState,
  isSyncing,
  isLoadingDrill = false,
  drillNotFound = false,
  currentProblemIndex,
  theme,
  onToggleTheme,
  onResetAll,
  drills,
  allWorkspaceDrills,
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
  onToggleViewMode,
  status,
  onStatusChange,
  children,
}) => {
  const [showDrillSwitcher, setShowDrillSwitcher] = useState(false);
  const [showHeader, setShowHeader] = useState(true);
  const [headerHeight, setHeaderHeight] = useState(108);
  const [isSideDrawerOpen, setIsSideDrawerOpen] = useState(false);
  const [pillWorkspace, setPillWorkspace] = useState<Workspace>(workspace);
  useEffect(() => setPillWorkspace(workspace), [workspace]);

  const lastScrollYRef = useRef(0);
  const headerRef = useRef<HTMLElement | null>(null);
  const switcherRef = useRef<HTMLDivElement | null>(null);
  const drawerPrevFocusRef = useRef<HTMLElement | null>(null);
  const drawerDescId = useId();

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
    dueReviewCount,
    reviewSessionSize,
    otherWorkspaceDueCount,
    estimatedMinutes,
    nextDueDate,
    dueUnitCodes,
    currentUnitMastery,
    dueLoading,
    dueError,
    weakSpotUnits,
    weakLoading,
    weakError,
  } = useSidePanelData(
    workspace,
    currentDrill?.unitCode,
    currentDrill?.sessionSummary?.syncedToNotionAt
  );

  const openWeakCount = weakSpotUnits.reduce((acc, u) => acc + u.open.length, 0);
  const sidePanelCount = dueReviewCount + openWeakCount;

  // Close mobile drawer when switching drills or leaving quiz view
  useEffect(() => {
    setIsSideDrawerOpen(false);
  }, [selectedDrillId, viewMode]);

  const drawerActive = viewMode === "quiz" && isSideDrawerOpen;

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
      } else if (diff < -8) {
        setShowHeader(true);
      }

      lastScrollYRef.current = currentScrollY;
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close DrillSwitcher on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (switcherRef.current && !switcherRef.current.contains(e.target as Node)) {
        setShowDrillSwitcher(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const tiles =
    currentDrill && currentDrill.problems.length > 0 ? (
      <div className="mt-2">
        <QuizPaginationBar
          currentIndex={currentProblemIndex}
          problems={currentDrill.problems}
          currentDrill={currentDrill}
          statusOverride={statusOverride}
          syncState={syncState}
          isSyncing={isSyncing}
          viewMode={viewMode}
          workspace={workspace}
          isLab={isLabId(currentDrill.drillId)}
          onSelectQuestion={onSelectQuestion}
          onToggleViewMode={onToggleViewMode}
        />
      </div>
    ) : null;

  // Same width in every view so the header/tiles never jump when switching to Review.
  const containerMaxWidth = "max-w-[720px] lg:max-w-[1016px]";
  // Sticky header sits at top-2 (8 px); add 12 px breathing room when visible.
  const asideTopPx = showHeader ? headerHeight + 20 : 16;

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 px-4 lg:px-16 py-4 sm:py-6 transition-colors">
      {/* >=1024px: Fixed icon-only workspace rail at the left-middle edge */}
      <WorkspaceSwitch
        variant="rail"
        workspace={workspace}
        pillWorkspace={pillWorkspace}
        onSelectWorkspace={setPillWorkspace}
        mathHref={mathHref}
        codeHref={codeHref}
        className="hidden lg:grid fixed left-3 top-1/2 -translate-y-1/2 z-40 grid-rows-2 items-center rounded-xl bg-zinc-100/95 dark:bg-zinc-800/80 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 p-1 shadow-sm"
      />

      <div className={`mx-auto ${containerMaxWidth}`}>
        {/* Provide sr-only h1 when no active drill or not-found card renders a visible h1 */}
        {viewMode === "quiz" && !currentDrill && !drillNotFound && (
          <h1 className="sr-only">Practice Studio</h1>
        )}

        <StudioHeader
          headerRef={headerRef}
          showHeader={showHeader}
          workspace={workspace}
          pillWorkspace={pillWorkspace}
          onSelectWorkspace={setPillWorkspace}
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
          dueUnitCodes={dueUnitCodes}
          selectedDrillId={selectedDrillId}
          drillSearch={drillSearch}
          onSearchChange={onSearchChange}
          drillFilter={drillFilter}
          onFilterChange={onFilterChange}
          onSelectDrill={onSelectDrill}
          onOpenGenPopover={() => onShowGenPopoverChange(true)}
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
              <StudioSidePanel
                workspace={workspace}
                currentUnitCode={currentDrill?.unitCode}
                drillLoading={isLoadingDrill}
                dueReviewCount={dueReviewCount}
                reviewSessionSize={reviewSessionSize}
                otherWorkspaceDueCount={otherWorkspaceDueCount}
                estimatedMinutes={estimatedMinutes}
                nextDueDate={nextDueDate}
                currentUnitMastery={currentUnitMastery}
                dueLoading={dueLoading}
                dueError={dueError}
                weakSpotUnits={weakSpotUnits}
                weakLoading={weakLoading}
                weakError={weakError}
                onNavigate={() => setIsSideDrawerOpen(false)}
              />
            </aside>
          </div>
        ) : (
          <main>{children}</main>
        )}
      </div>

      <ToastStack status={status} onClearStatus={handleClearStatus} />

      <GeneratePopover
        isOpen={showGenPopover}
        onClose={() => onShowGenPopoverChange(false)}
        workspace={workspace}
        drills={allWorkspaceDrills ?? drills}
        currentDrill={currentDrill}
        onGenerated={onGenerated}
        onStatusChange={onStatusChange}
      />

      <Drawer
        open={drawerActive}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setIsSideDrawerOpen(false);
          }
        }}
      >
        <DrawerContent
          overlayClassName="lg:hidden"
          aria-modal="true"
          aria-label="Due today & weak spots"
          aria-describedby={drawerDescId}
          onOpenAutoFocus={() => {
            drawerPrevFocusRef.current =
              document.activeElement instanceof HTMLElement ? document.activeElement : null;
          }}
          onCloseAutoFocus={(e) => {
            e.preventDefault();
            const prev = drawerPrevFocusRef.current;
            drawerPrevFocusRef.current = null;
            if (prev && prev.isConnected) {
              prev.focus();
            }
          }}
          className="lg:hidden overflow-x-hidden bg-white p-4 space-y-4 dark:bg-zinc-900"
        >
          <div className="flex items-center justify-between gap-2 min-w-0 pb-2 pr-11 border-b border-zinc-200 dark:border-zinc-800">
            <DrawerTitle className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 truncate">
              Due today &amp; weak spots
            </DrawerTitle>
            <DrawerDescription id={drawerDescId} className="sr-only">
              Review queue and open weak spots for the current workspace and unit.
            </DrawerDescription>
          </div>
          <StudioSidePanel
            workspace={workspace}
            currentUnitCode={currentDrill?.unitCode}
            drillLoading={isLoadingDrill}
            dueReviewCount={dueReviewCount}
            reviewSessionSize={reviewSessionSize}
            otherWorkspaceDueCount={otherWorkspaceDueCount}
            estimatedMinutes={estimatedMinutes}
            nextDueDate={nextDueDate}
            currentUnitMastery={currentUnitMastery}
            dueLoading={dueLoading}
            dueError={dueError}
            weakSpotUnits={weakSpotUnits}
            weakLoading={weakLoading}
            weakError={weakError}
            embedded
            onNavigate={() => setIsSideDrawerOpen(false)}
          />
        </DrawerContent>
      </Drawer>
    </div>
  );
};
