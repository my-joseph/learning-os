"use client";

import React, { useState, useEffect, useId, useRef, useCallback } from "react";
import { m } from "motion/react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import type { SyncState } from "@/hooks/useProgressSync";
import type { LabListItem } from "@/lib/labModel";
import { DrillFilter, PracticeStatusOverride, StatusMessage, ViewMode } from "@/hooks/types";
import { useSidePanelData } from "@/hooks/useSidePanelData";
import { Workspace, isLabId } from "@/lib/routes";
import { settle } from "@/lib/motion";
import { cn } from "@/lib/cn";
import { QuizPaginationBar } from "@/components/QuizPaginationBar";
import { ToastStack } from "@/components/ui/ToastStack";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerTitle,
} from "@/components/ui/shadcn/Drawer";
import { StudioHeader } from "./StudioHeader";
import { StudioSidebar } from "./StudioSidebar";
import { StudioSidePanel } from "./StudioSidePanel";
import { GeneratePopover } from "./GeneratePopover";

const SIDEBAR_OPEN_KEY = "practice-studio:sidebar-open";
const RIGHT_PANEL_OPEN_KEY = "practice-studio:right-panel-open";

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
  onResetDrill?: (drillId: string) => void;
  onDeleteDrill?: (drillId: string) => void;
  // GeneratePopover
  showGenPopover: boolean;
  onShowGenPopoverChange: (open: boolean) => void;
  onGenerated: (drillId: string) => Promise<void>;
  // Pagination / tiles
  showPaginationBar?: boolean;
  onSelectQuestion: (idx: number) => void;
  onToggleViewMode: (mode: ViewMode) => void;
  // Status banner
  status: StatusMessage | null;
  onStatusChange: (status: StatusMessage | null) => void;
  children: React.ReactNode;
}

/** Edge-to-edge 3-pane flat Studio shell composing Left Sidebar, Top Bar, optional compact Pagination sub-bar, Center canvas, and Right Panel across quiz & review views. */
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
  onResetDrill,
  onDeleteDrill,
  showGenPopover,
  onShowGenPopoverChange,
  onGenerated,
  showPaginationBar = false,
  onSelectQuestion,
  onToggleViewMode,
  status,
  onStatusChange,
  children,
}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [rightSettledClosed, setRightSettledClosed] = useState(false);
  const [isSideDrawerOpen, setIsSideDrawerOpen] = useState(false);
  const [isSidebarDrawerOpen, setIsSidebarDrawerOpen] = useState(false);
  const [pillWorkspace, setPillWorkspace] = useState<Workspace>(workspace);
  useEffect(() => setPillWorkspace(workspace), [workspace]);

  const drawerPrevFocusRef = useRef<HTMLElement | null>(null);
  const sidebarDrawerPrevFocusRef = useRef<HTMLElement | null>(null);
  const drawerDescId = useId();
  const sidebarDrawerDescId = useId();

  useEffect(() => {
    try {
      const savedSidebar = window.localStorage.getItem(SIDEBAR_OPEN_KEY);
      if (savedSidebar === "false") {
        setIsSidebarOpen(false);
      }
      const savedRight = window.localStorage.getItem(RIGHT_PANEL_OPEN_KEY);
      if (savedRight === "false") {
        setIsRightPanelOpen(false);
        setRightSettledClosed(true);
      }
    } catch {
      // ignore localStorage failures
    }
  }, []);

  useEffect(() => {
    if (isRightPanelOpen) {
      setRightSettledClosed(false);
    }
  }, [isRightPanelOpen]);

  const setSidebarOpen = useCallback((updater: boolean | ((prev: boolean) => boolean)) => {
    setIsSidebarOpen((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      try {
        window.localStorage.setItem(SIDEBAR_OPEN_KEY, String(next));
      } catch {
        // ignore localStorage failures
      }
      return next;
    });
  }, []);

  const toggleRightPanel = useCallback(() => {
    setIsRightPanelOpen((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(RIGHT_PANEL_OPEN_KEY, String(next));
      } catch {
        // ignore localStorage failures
      }
      return next;
    });
  }, []);

  const handleClearStatus = useCallback(() => {
    onStatusChange(null);
  }, [onStatusChange]);

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

  // Close mobile drawers when switching drills or changing viewMode
  useEffect(() => {
    setIsSideDrawerOpen(false);
    setIsSidebarDrawerOpen(false);
  }, [selectedDrillId, viewMode]);

  const drawerActive = isSideDrawerOpen;
  const hasPagination = Boolean(currentDrill && currentDrill.problems.length > 0);

  return (
    <div className="min-h-screen lg:h-screen lg:overflow-hidden flex bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 transition-colors">
      {/* >=1024px: Full-height docked Left Sidebar (width 287 <-> 0) */}
      <StudioSidebar
        isOpen={isSidebarOpen}
        onToggle={() => setSidebarOpen((prev) => !prev)}
        workspace={workspace}
        pillWorkspace={pillWorkspace}
        onSelectWorkspace={setPillWorkspace}
        mathHref={mathHref}
        codeHref={codeHref}
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

      {/* Right of Left Sidebar: Top Bar + Below-Top-Bar split (Center canvas + Right Panel) */}
      <div className="flex-1 min-w-0 flex flex-col lg:h-full lg:overflow-hidden">
        {/* Provide sr-only h1 when no active drill or not-found card renders a visible h1 */}
        {viewMode === "quiz" && !currentDrill && !drillNotFound && (
          <h1 className="sr-only">Practice Studio</h1>
        )}

        <StudioHeader
          workspace={workspace}
          currentDrill={currentDrill}
          selectedDrillId={selectedDrillId}
          theme={theme}
          onToggleTheme={onToggleTheme}
          onResetAll={onResetAll}
          onOpenGenPopover={() => onShowGenPopoverChange(true)}
          isSidebarOpen={isSidebarOpen}
          onOpenDesktopSidebar={() => setSidebarOpen(true)}
          onOpenSidebarDrawer={() => setIsSidebarDrawerOpen(true)}
          isRightPanelOpen={isRightPanelOpen}
          onToggleRightPanel={toggleRightPanel}
          onOpenSideDrawer={() => setIsSideDrawerOpen(true)}
          sidePanelCount={sidePanelCount}
        />

        {/* Below Top Bar: Center Pane + collapsible Right Panel (visible in both quiz & review views) */}
        <div className="flex-1 min-h-0 flex">
          <div className="flex-1 min-w-0 flex flex-col bg-white dark:bg-zinc-900">
            {showPaginationBar && hasPagination && currentDrill && (
              <div className="shrink-0 border-b border-zinc-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900 px-3 sm:px-5 py-1.5">
                <QuizPaginationBar
                  compact
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
            )}

            <div className="flex-1 lg:overflow-y-auto px-4 sm:px-8 py-5 sm:py-6">
              <main className="mx-auto w-full max-w-[720px]">{children}</main>
            </div>
          </div>

          <m.aside
            aria-label="Due today and weak spots"
            aria-hidden={!isRightPanelOpen || undefined}
            initial={false}
            animate={{
              width: isRightPanelOpen ? 276 : 0,
              opacity: isRightPanelOpen ? 1 : 0,
            }}
            transition={settle}
            onAnimationComplete={() => {
              if (!isRightPanelOpen) setRightSettledClosed(true);
            }}
            className={cn(
              "hidden lg:block shrink-0 overflow-hidden bg-white dark:bg-zinc-900 lg:sticky lg:top-0 lg:overflow-y-auto lg:overscroll-contain motion-reduce:transition-none",
              isRightPanelOpen &&
                "border-l border-zinc-200/80 dark:border-zinc-800/80",
              !isRightPanelOpen && "pointer-events-none select-none",
              rightSettledClosed && !isRightPanelOpen && "invisible"
            )}
          >
            <div className="w-[276px] p-4">
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
            </div>
          </m.aside>
        </div>
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

      {/* Mobile / Tablet (<1024px): Left navigation sidebar Drawer */}
      <Drawer
        open={isSidebarDrawerOpen}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setIsSidebarDrawerOpen(false);
          }
        }}
      >
        <DrawerContent
          side="left"
          overlayClassName="lg:hidden"
          aria-modal="true"
          aria-label="Practice navigation"
          aria-describedby={sidebarDrawerDescId}
          onOpenAutoFocus={() => {
            sidebarDrawerPrevFocusRef.current =
              document.activeElement instanceof HTMLElement
                ? document.activeElement
                : null;
          }}
          onCloseAutoFocus={(e) => {
            e.preventDefault();
            const prev = sidebarDrawerPrevFocusRef.current;
            sidebarDrawerPrevFocusRef.current = null;
            if (prev && prev.isConnected) {
              prev.focus();
            }
          }}
          className="lg:hidden p-0 overflow-hidden bg-surface-panel flex flex-col"
        >
          <DrawerTitle className="sr-only">Practice navigation</DrawerTitle>
          <DrawerDescription id={sidebarDrawerDescId} className="sr-only">
            Switch workspace or browse drills and labs.
          </DrawerDescription>
          <StudioSidebar
            embedded
            workspace={workspace}
            pillWorkspace={pillWorkspace}
            onSelectWorkspace={setPillWorkspace}
            mathHref={mathHref}
            codeHref={codeHref}
            currentDrill={currentDrill}
            drills={drills}
            labs={labs}
            dueUnitCodes={dueUnitCodes}
            selectedDrillId={selectedDrillId}
            drillSearch={drillSearch}
            onSearchChange={onSearchChange}
            drillFilter={drillFilter}
            onFilterChange={onFilterChange}
            onSelectDrill={(id) => {
              setIsSidebarDrawerOpen(false);
              onSelectDrill(id);
            }}
            onResetDrill={onResetDrill}
            onDeleteDrill={onDeleteDrill}
            onCloseDrawer={() => setIsSidebarDrawerOpen(false)}
          />
        </DrawerContent>
      </Drawer>

      {/* Mobile / Tablet (<1024px): Right Due today & weak spots Drawer */}
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
              document.activeElement instanceof HTMLElement
                ? document.activeElement
                : null;
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
