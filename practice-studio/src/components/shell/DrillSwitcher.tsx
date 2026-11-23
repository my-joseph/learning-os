"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, m } from "motion/react";
import { popover, presence, settle } from "@/lib/motion";
import { Reveal } from "@/components/motion/Reveal";
import {
  Check,
  ChevronDown,
  ChevronRight,
  ChevronsDownUp,
  ChevronsUpDown,
  Layers,
  MessageSquare,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import type { LabListItem } from "@/lib/labModel";
import {
  buildPickerSections,
  buildVisibleTreeRows,
  collectAllTreeCodes,
  extractChapterShortCode,
  extractLeafHoverCode,
  extractShortCode,
  filterPickerItems,
  findFirstLeafNodeId,
  formatFullRowCode,
  getPickerStatusLabel,
  normalizeDrillPickerItems,
  normalizeLabPickerItems,
  resolveTreeKeyAction,
  type PickerItem,
  type PickerStatus,
  type TreeNavKey,
  type VisibleTreeRow,
} from "@/lib/drillGrouping";
import { isLabId, subjectOf, type Workspace } from "@/lib/routes";
import { statusTone } from "@/lib/statusTone";
import { Badge } from "@/components/ui/shadcn/Badge";
import { plainTitle } from "@/lib/titleText";
import { DrillFilter } from "@/hooks/types";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/shadcn/Tabs";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/shadcn/Popover";

type PickerTab = "drills" | "labs";

interface DrillSwitcherProps {
  mode?: "dropdown" | "sidebar";
  searchInputRef?: React.RefObject<HTMLInputElement | null>;
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  switcherRef?: React.RefObject<HTMLDivElement>;
  workspace?: Workspace;
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
}

function statusDotClass(status: PickerStatus): string {
  switch (status) {
    case "Graded":
      return statusTone.correct.dot;
    case "In Progress":
      return "bg-indigo-600 dark:bg-indigo-400";
    case "Needs Retry":
      return statusTone.wrong.dot;
    default:
      return statusTone.notTried.dot;
  }
}

function StatusDot({ status }: { status: PickerStatus }) {
  const label = getPickerStatusLabel(status);
  return (
    <span
      className="inline-flex items-center justify-center w-3.5 h-3.5 shrink-0"
      title={label}
    >
      <span
        className={`w-2 h-2 rounded-full ${statusDotClass(status)}`}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </span>
  );
}

function NoteBadge({
  hasNotes,
  isDueToday,
}: {
  hasNotes: boolean;
  isDueToday: boolean;
}) {
  if (isDueToday) {
    return (
      <Badge
        variant="status"
        className="w-3.5 h-3.5 p-0 rounded-none text-[0px] gap-0 inline-flex items-center justify-center shrink-0"
        title={hasNotes ? "Due today · has notes" : "Due today"}
      >
        <MessageSquare
          className="w-3 h-3 text-zinc-900 dark:text-zinc-100 fill-zinc-900 dark:fill-zinc-100"
          aria-hidden="true"
        />
        <span className="sr-only">Due today</span>
      </Badge>
    );
  }
  if (hasNotes) {
    return (
      <Badge
        variant="status"
        className="w-3.5 h-3.5 p-0 rounded-none text-[0px] gap-0 inline-flex items-center justify-center shrink-0"
        title="Has notes or mistake tags"
      >
        <MessageSquare
          className="w-3 h-3 text-zinc-400 dark:text-zinc-500"
          aria-hidden="true"
        />
        <span className="sr-only">Has notes</span>
      </Badge>
    );
  }
  return null;
}

function HoverRowCode({ code }: { code: string }) {
  // Zero-width anchor: the code floats over the end of the title on hover, so the row never
  // changes width (no jitter) and nothing is reserved when not hovered.
  return (
    <span className="relative w-0 shrink-0 self-stretch">
      <span className="pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2 hidden group-hover:block group-focus-visible:block whitespace-nowrap rounded px-1 bg-zinc-100 dark:bg-zinc-800 font-display text-[11px] text-zinc-500 dark:text-zinc-400 tabular-nums">
        {code}
      </span>
    </span>
  );
}

function CountPill({ count }: { count: number }) {
  return (
    <Badge variant="status" className="text-[11px] font-display tabular-nums text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded-full shrink-0">
      {count}
    </Badge>
  );
}

const BRANCH_ROW_CLASS =
  "group w-full flex items-center gap-1.5 px-1.5 py-1.5 rounded-md text-left transition-colors focus:outline-none hover:bg-zinc-100/80 dark:hover:bg-zinc-800/60 focus-visible:bg-zinc-100 dark:focus-visible:bg-zinc-800/80 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500/70 dark:focus-visible:ring-indigo-400/70";

const FILTER_OPTIONS: readonly { id: DrillFilter; label: string }[] = [
  { id: "ALL", label: "All" },
  { id: "UNFINISHED", label: "Unfinished" },
  { id: "GRADED", label: "Graded" },
];

const STATUS_LEGEND: readonly { status: PickerStatus; label: string }[] = [
  { status: "Ready", label: "Not started" },
  { status: "In Progress", label: "In progress" },
  { status: "Graded", label: "Graded" },
  { status: "Needs Retry", label: "Needs retry" },
];

/** Searchable, keyboard-navigable Topic -> Chapter -> Unit -> Leaf tree picker for drills and labs. */
export const DrillSwitcher: React.FC<DrillSwitcherProps> = ({
  mode = "dropdown",
  searchInputRef: externalSearchInputRef,
  isOpen,
  onToggle,
  onClose,
  switcherRef,
  workspace,
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
}) => {
  const isSidebar = mode === "sidebar";
  const isCodeWorkspace =
    workspace === "code" ||
    (workspace === undefined && (labs.length > 0 || subjectOf(selectedDrillId) === "code"));

  const defaultTab: PickerTab =
    isCodeWorkspace && isLabId(selectedDrillId) ? "labs" : "drills";

  const [activeTab, setActiveTab] = useState<PickerTab>(defaultTab);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);

  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const internalSearchInputRef = useRef<HTMLInputElement | null>(null);
  const searchInputRef = externalSearchInputRef ?? internalSearchInputRef;
  const bindSearchInputRef = (el: HTMLInputElement | null) => {
    internalSearchInputRef.current = el;
    if (externalSearchInputRef && "current" in externalSearchInputRef) {
      (externalSearchInputRef as React.MutableRefObject<HTMLInputElement | null>).current = el;
    }
  };
  const viewButtonRef = useRef<HTMLButtonElement | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const currentTreeRef = useRef<HTMLButtonElement | null>(null);
  const nodeRefs = useRef<Map<string, HTMLButtonElement | null>>(new Map());
  const wasOpenRef = useRef(isOpen);
  const prevSelectedIdRef = useRef(selectedDrillId);

  const dueUnitSet = useMemo(() => new Set(dueUnitCodes), [dueUnitCodes]);

  const currentDrillHasNotes = useMemo(() => {
    if (!currentDrill) return null;
    const hasProblemNotes = currentDrill.problems.some(
      (p) =>
        Boolean(p.state?.mistakeNote && p.state.mistakeNote.trim()) ||
        (Array.isArray(p.state?.mistakes) && p.state.mistakes.length > 0)
    );
    const hasCategories =
      Array.isArray(currentDrill.sessionSummary?.mistakeCategories) &&
      currentDrill.sessionSummary.mistakeCategories.length > 0;
    return hasProblemNotes || hasCategories;
  }, [currentDrill]);

  const drillItems = useMemo(() => normalizeDrillPickerItems(drills), [drills]);
  const labItems = useMemo(() => normalizeLabPickerItems(labs), [labs]);

  const activeItems = useMemo(
    () => (isCodeWorkspace && activeTab === "labs" ? labItems : drillItems),
    [isCodeWorkspace, activeTab, labItems, drillItems]
  );

  const otherTabMatchCount = useMemo(() => {
    if (!isCodeWorkspace || !drillSearch.trim()) return 0;
    const otherItems = activeTab === "labs" ? drillItems : labItems;
    return filterPickerItems(otherItems, drillSearch, drillFilter).length;
  }, [isCodeWorkspace, activeTab, drillItems, labItems, drillSearch, drillFilter]);

  const sections = useMemo(
    () =>
      buildPickerSections({
        items: activeItems,
        currentId: selectedDrillId,
        recentIds: [],
        search: drillSearch,
        filter: drillFilter,
      }),
    [activeItems, selectedDrillId, drillSearch, drillFilter]
  );

  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(
    () => new Set(sections.defaultExpandedTopics)
  );
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(
    () => new Set(sections.defaultExpandedChapters)
  );
  const [expandedUnits, setExpandedUnits] = useState<Set<string>>(
    () => new Set(sections.defaultExpandedUnits)
  );

  const allTreeCodes = useMemo(
    () => collectAllTreeCodes(sections.topicGroups),
    [sections.topicGroups]
  );

  const visibleTreeRows = useMemo(
    () =>
      buildVisibleTreeRows({
        topicGroups: sections.topicGroups,
        currentId: selectedDrillId,
        expandedTopics,
        expandedChapters,
        expandedUnits,
        dueUnitCodes: dueUnitSet,
        currentHasNotesOverride: currentDrillHasNotes,
      }),
    [
      sections.topicGroups,
      selectedDrillId,
      expandedTopics,
      expandedChapters,
      expandedUnits,
      dueUnitSet,
      currentDrillHasNotes,
    ]
  );

  const rowByNodeId = useMemo(() => {
    const map = new Map<string, VisibleTreeRow>();
    for (const row of visibleTreeRows) {
      map.set(row.nodeId, row);
    }
    return map;
  }, [visibleTreeRows]);

  // Sync tab when opening or switching drills, reset View popover on close.
  useEffect(() => {
    const justOpened = isOpen && !wasOpenRef.current;
    const drillChanged = prevSelectedIdRef.current !== selectedDrillId;
    wasOpenRef.current = isOpen;
    prevSelectedIdRef.current = selectedDrillId;

    if (!isOpen) {
      setIsViewOpen(false);
      return;
    }

    if (justOpened || drillChanged) {
      const nextTab: PickerTab =
        isCodeWorkspace && isLabId(selectedDrillId) ? "labs" : "drills";
      setActiveTab(nextTab);
    }
  }, [isOpen, isCodeWorkspace, selectedDrillId]);

  const defaultTopicsKey = sections.defaultExpandedTopics.join("|");
  const defaultChaptersKey = sections.defaultExpandedChapters.join("|");
  const defaultUnitsKey = sections.defaultExpandedUnits.join("|");

  // Expand matching branches on search, initial data arrival, or open/tab/drill/filter change.
  useEffect(() => {
    if (!isOpen) return;
    setExpandedTopics(new Set(sections.defaultExpandedTopics));
    setExpandedChapters(new Set(sections.defaultExpandedChapters));
    setExpandedUnits(new Set(sections.defaultExpandedUnits));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    isOpen,
    activeTab,
    selectedDrillId,
    drillSearch,
    drillFilter,
    defaultTopicsKey,
    defaultChaptersKey,
    defaultUnitsKey,
  ]);

  // Keep active keyboard node aligned with search results or visible rows.
  useEffect(() => {
    if (!isOpen) return;
    if (sections.isSearching) {
      setActiveNodeId(findFirstLeafNodeId(visibleTreeRows));
    } else if (activeNodeId && !rowByNodeId.has(activeNodeId)) {
      setActiveNodeId(null);
    }
  }, [isOpen, sections.isSearching, visibleTreeRows, rowByNodeId, activeNodeId]);

  // Autofocus search and scroll the current drill row into view on dropdown open.
  useEffect(() => {
    if (!isOpen || isSidebar) return;
    const rafId = window.requestAnimationFrame(() => {
      searchInputRef.current?.focus();
      currentTreeRef.current?.scrollIntoView({ block: "nearest" });
    });
    return () => window.cancelAnimationFrame(rafId);
  }, [isOpen, isSidebar, searchInputRef]);

  // Close on Escape even if focus is outside the search input (dropdown mode only).
  useEffect(() => {
    if (!isOpen || isSidebar) return;
    const handleWindowKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        if (isViewOpen) {
          setIsViewOpen(false);
          viewButtonRef.current?.focus();
        } else {
          onClose();
          triggerRef.current?.focus();
        }
      }
    };
    window.addEventListener("keydown", handleWindowKeyDown);
    return () => window.removeEventListener("keydown", handleWindowKeyDown);
  }, [isOpen, isSidebar, isViewOpen, onClose]);

  const handlePick = (id: string) => {
    if (drillSearch) {
      onSearchChange("");
    }
    setIsViewOpen(false);
    onSelectDrill(id);
    onClose();
  };

  const setBranchExpanded = (
    kind: "topic" | "chapter" | "unit",
    code: string,
    mode: "toggle" | "expand" | "collapse"
  ) => {
    const updater = (prev: Set<string>) => {
      const next = new Set(prev);
      const has = next.has(code);
      if (mode === "expand" || (mode === "toggle" && !has)) {
        next.add(code);
      } else if (mode === "collapse" || (mode === "toggle" && has)) {
        next.delete(code);
      }
      return next;
    };
    if (kind === "topic") setExpandedTopics(updater);
    else if (kind === "chapter") setExpandedChapters(updater);
    else setExpandedUnits(updater);
  };

  const handleExpandAll = () => {
    setExpandedTopics(new Set(allTreeCodes.topicCodes));
    setExpandedChapters(new Set(allTreeCodes.chapterCodes));
    setExpandedUnits(new Set(allTreeCodes.unitCodes));
  };

  const handleCollapseAll = () => {
    setExpandedTopics(new Set());
    setExpandedChapters(new Set());
    setExpandedUnits(new Set());
    setActiveNodeId(null);
  };

  const focusTreeNode = (nodeId: string) => {
    setActiveNodeId(nodeId);
    const el = nodeRefs.current.get(nodeId);
    if (el) {
      el.focus();
      el.scrollIntoView({ block: "nearest" });
    }
  };

  const handlePopoverKeyDown = (e: React.KeyboardEvent) => {
    const target = e.target as HTMLElement | null;
    const inSearchInput = target === searchInputRef.current;

    if (e.key === "Escape") {
      if (isViewOpen) {
        e.preventDefault();
        e.stopPropagation();
        setIsViewOpen(false);
        viewButtonRef.current?.focus();
      } else if (!isSidebar) {
        e.preventDefault();
        e.stopPropagation();
        onClose();
        triggerRef.current?.focus();
      }
      return;
    }

    if (
      e.key !== "ArrowDown" &&
      e.key !== "ArrowUp" &&
      e.key !== "ArrowRight" &&
      e.key !== "ArrowLeft" &&
      e.key !== "Enter"
    ) {
      return;
    }

    // Keep text caret navigation inside the search box.
    if (inSearchInput && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
      return;
    }

    // Tabs own arrow-key navigation; do not send those keys to the curriculum tree.
    if (target?.closest('[role="tablist"]')) return;

    // Let non-treeitem toolbar buttons (Tabs, Expand/Collapse, View, Clear) handle their own Enter.
    const isTreeItemTarget = target?.getAttribute("role") === "treeitem";
    if (e.key === "Enter" && !inSearchInput && !isTreeItemTarget) {
      return;
    }

    if (inSearchInput && e.key === "Enter") {
      const targetNodeId =
        activeNodeId && rowByNodeId.has(activeNodeId)
          ? activeNodeId
          : sections.isSearching
          ? findFirstLeafNodeId(visibleTreeRows)
          : null;
      const targetRow = targetNodeId ? rowByNodeId.get(targetNodeId) : undefined;
      if (targetRow?.kind === "leaf") {
        e.preventDefault();
        handlePick(targetRow.item.id);
      }
      return;
    }

    const action = resolveTreeKeyAction(visibleTreeRows, activeNodeId, e.key as TreeNavKey);
    if (action.type === "none") return;

    e.preventDefault();
    if (action.type === "focus") {
      focusTreeNode(action.nodeId);
    } else if (action.type === "expand") {
      setBranchExpanded(action.nodeKind, action.code, "expand");
    } else if (action.type === "collapse") {
      setBranchExpanded(action.nodeKind, action.code, "collapse");
    } else if (action.type === "toggle") {
      setBranchExpanded(action.nodeKind, action.code, "toggle");
    } else if (action.type === "select") {
      handlePick(action.itemId);
    }
  };

  const registerNodeRef = (nodeId: string, el: HTMLButtonElement | null) => {
    if (el) {
      nodeRefs.current.set(nodeId, el);
    } else {
      nodeRefs.current.delete(nodeId);
    }
  };

  const currentPinnedItem =
    !sections.isSearching && sections.currentItem ? sections.currentItem : null;
  const currentPinnedHasNotes = currentPinnedItem
    ? currentPinnedItem.hasNotes || Boolean(currentDrillHasNotes)
    : false;
  const currentPinnedIsDue = currentPinnedItem
    ? dueUnitSet.has(currentPinnedItem.unitCode)
    : false;

  const isTreeEmpty = sections.topicGroups.length === 0;
  const isFilterActive = drillFilter !== "ALL";

  const expandCollapseButtons = (
    <>
      <button
        type="button"
        onClick={handleExpandAll}
        disabled={isTreeEmpty}
        className={`inline-flex items-center gap-1 ${
          isSidebar ? "px-1.5 min-h-[44px] lg:min-h-0" : "px-2"
        } py-1 rounded-md border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800/70 disabled:opacity-40 text-[11px] font-medium text-zinc-700 dark:text-zinc-300 transition-colors whitespace-nowrap`}
      >
        <ChevronsUpDown className="w-3 h-3 text-zinc-400 shrink-0" aria-hidden="true" />
        <span>Expand all</span>
      </button>
      <button
        type="button"
        onClick={handleCollapseAll}
        disabled={isTreeEmpty}
        className={`inline-flex items-center gap-1 ${
          isSidebar ? "px-1.5 min-h-[44px] lg:min-h-0" : "px-2"
        } py-1 rounded-md border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800/70 disabled:opacity-40 text-[11px] font-medium text-zinc-700 dark:text-zinc-300 transition-colors whitespace-nowrap`}
      >
        <ChevronsDownUp className="w-3 h-3 text-zinc-400 shrink-0" aria-hidden="true" />
        <span>Collapse all</span>
      </button>
    </>
  );

  const branchRowCls = isSidebar
    ? `${BRANCH_ROW_CLASS} min-h-[44px] lg:min-h-0`
    : BRANCH_ROW_CLASS;

  const renderLeafRow = (
    item: PickerItem,
    label: string,
    level: 3 | 4,
    nodeId: string
  ) => {
    const isCurrent = item.id === selectedDrillId;
    const isSearchTarget = sections.isSearching && activeNodeId === nodeId;
    const hoverCode = extractLeafHoverCode(item);
    const fullCode = formatFullRowCode(item);
    const hasNotes =
      isCurrent && currentDrillHasNotes !== null
        ? item.hasNotes || currentDrillHasNotes
        : item.hasNotes;
    const isDueToday = dueUnitSet.has(item.unitCode);

    return (
      <button
        key={nodeId}
        ref={(el) => {
          registerNodeRef(nodeId, el);
          if (isCurrent) {
            currentTreeRef.current = el;
          }
        }}
        type="button"
        role="treeitem"
        aria-level={level}
        aria-selected={isCurrent}
        aria-current={isCurrent ? "true" : undefined}
        title={fullCode}
        onClick={() => {
          setActiveNodeId(nodeId);
          handlePick(item.id);
        }}
        className={`group w-full text-left px-1.5 py-1.5 ${
          isSidebar ? "min-h-[44px] lg:min-h-0 " : ""
        }rounded-md transition-colors flex items-center gap-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600/70 dark:focus-visible:ring-indigo-400/70 ${
          isCurrent
            ? "bg-indigo-50 dark:bg-indigo-500/10 ring-1 ring-inset ring-indigo-500/50 dark:ring-indigo-400/50"
            : isSearchTarget
            ? "bg-zinc-100 dark:bg-zinc-800/80 ring-2 ring-inset ring-indigo-500/70 dark:ring-indigo-400/70"
            : "hover:bg-zinc-100/80 dark:hover:bg-zinc-800/60 focus-visible:bg-zinc-100 dark:focus-visible:bg-zinc-800/80"
        }`}
      >
        <StatusDot status={item.practiceStatus} />
        <NoteBadge hasNotes={hasNotes} isDueToday={isDueToday} />
        <span
          className={`text-xs truncate min-w-0 flex-1 ${
            isCurrent
              ? "font-medium text-zinc-900 dark:text-zinc-100"
              : "text-zinc-700 dark:text-zinc-300"
          }`}
        >
          {plainTitle(label)}
        </span>
        <HoverRowCode code={hoverCode} />
      </button>
    );
  };

  const pickerBody = (
    <>
            {/* Top Search Input */}
            <div className="shrink-0 flex items-center gap-2 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-1.5 mb-2 transition-colors focus-within:border-indigo-600 dark:focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-600/20 dark:focus-within:ring-indigo-400/25">
              <Search className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
              <input
                ref={bindSearchInputRef}
                type="text"
                value={drillSearch}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder={
                  isCodeWorkspace
                    ? "Search drills, labs, chapters, or IDs..."
                    : "Search units, chapters, or drill IDs..."
                }
                aria-label="Search practice drills"
                className={`w-full bg-transparent text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none ${
                  isSidebar ? "min-h-[28px] lg:min-h-0" : ""
                }`}
                autoFocus={!isSidebar}
              />
              {drillSearch && (
                <button
                  type="button"
                  onClick={() => {
                    onSearchChange("");
                    searchInputRef.current?.focus();
                  }}
                  aria-label="Clear search"
                  className={
                    isSidebar
                      ? "inline-flex items-center justify-center min-h-[36px] min-w-[36px] lg:min-h-0 lg:min-w-0 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                      : "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                  }
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Header Actions: Drills|Labs Tabs (Programming) + Expand all / Collapse all + View */}
            <div className="shrink-0 flex flex-wrap items-center justify-between gap-1.5 pb-2 mb-2 border-b border-zinc-200 dark:border-zinc-800">
              {isCodeWorkspace ? (
                <Tabs
                  value={activeTab}
                  activationMode="manual"
                  onValueChange={(value) => {
                    setActiveTab(value as PickerTab);
                    setActiveNodeId(null);
                  }}
                >
                  <TabsList
                    aria-label="Practice type"
                    className="relative grid h-auto min-h-0 grid-cols-2 items-center rounded-lg bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-800 p-0.5"
                  >
                    <m.span
                      aria-hidden
                      className="absolute top-0.5 bottom-0.5 left-0.5 w-[calc(50%-2px)] rounded-md bg-white dark:bg-zinc-900 shadow-sm"
                      initial={false}
                      animate={{ x: activeTab === "labs" ? "100%" : "0%" }}
                      transition={settle}
                    />
                    {[
                      { id: "drills" as const, label: "Drills", count: drills.length },
                      { id: "labs" as const, label: "Labs", count: labs.length },
                    ].map((tab) => {
                      return (
                        <TabsTrigger
                          key={tab.id}
                          value={tab.id}
                          aria-controls={undefined}
                          className={`relative z-10 inline-flex ${
                            isSidebar ? "min-h-[44px] lg:min-h-0" : "min-h-0"
                          } items-center justify-center gap-1.5 rounded-md bg-transparent px-2.5 py-1 text-xs font-medium text-zinc-500 shadow-none transition-colors whitespace-nowrap hover:text-zinc-900 data-[state=active]:bg-transparent data-[state=active]:text-zinc-900 data-[state=active]:shadow-none dark:text-zinc-400 dark:hover:text-zinc-200 dark:data-[state=active]:text-zinc-100`}
                        >
                          <span>{tab.label}</span>
                          <span className="text-[11px] font-display tabular-nums text-zinc-500 dark:text-zinc-400">
                            {tab.count}
                          </span>
                        </TabsTrigger>
                      );
                    })}
                  </TabsList>
                </Tabs>
              ) : (
                <div className={`inline-flex items-center ${isSidebar ? "gap-1" : "gap-1.5"}`}>
                  {expandCollapseButtons}
                </div>
              )}

              <div className={`flex items-center ${isSidebar ? "gap-1" : "gap-1.5"}`}>
                {isCodeWorkspace && expandCollapseButtons}

                {/* View Button + Popover */}
                <Popover open={isViewOpen} onOpenChange={setIsViewOpen}>
                  <div className="relative">
                    <PopoverTrigger asChild>
                      <button
                        ref={viewButtonRef}
                        type="button"
                        aria-expanded={isViewOpen}
                        className={`inline-flex items-center gap-1 ${
                          isSidebar ? "px-1.5 min-h-[44px] lg:min-h-0 " : "px-2 "
                        }py-1 rounded-md border text-[11px] font-medium transition-colors whitespace-nowrap ${
                          isViewOpen || isFilterActive
                            ? "border-indigo-500/50 bg-indigo-50/70 dark:bg-indigo-500/10 text-zinc-900 dark:text-zinc-100"
                            : "border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800/70 text-zinc-700 dark:text-zinc-300"
                        }`}
                      >
                        <SlidersHorizontal
                          className="w-3 h-3 text-zinc-500 dark:text-zinc-400 shrink-0"
                          aria-hidden="true"
                        />
                        <span>View</span>
                        {isFilterActive && (
                          <span
                            className="w-1.5 h-1.5 rounded-full bg-indigo-600 dark:bg-indigo-400"
                            aria-hidden="true"
                          />
                        )}
                      </button>
                    </PopoverTrigger>

                    <PopoverContent
                      align="end"
                      side="bottom"
                      sideOffset={6}
                      collisionPadding={8}
                      data-picker-popover="true"
                      aria-label="View filters"
                      onKeyDown={(e) => {
                        if (e.key === "Escape") e.stopPropagation();
                      }}
                      onEscapeKeyDown={(e) => e.stopPropagation()}
                      className="w-52 rounded-xl p-2.5 z-[60] space-y-2.5"
                    >
                      <div className="space-y-1">
                        <div className="px-1 text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                          Status
                        </div>
                        <div
                          role="group"
                          aria-label="Filter by status"
                          className="space-y-0.5"
                        >
                          {FILTER_OPTIONS.map((opt) => {
                            const isActive = drillFilter === opt.id;
                            return (
                              <button
                                key={opt.id}
                                type="button"
                                aria-pressed={isActive}
                                onClick={() => {
                                  onFilterChange(opt.id);
                                  setIsViewOpen(false);
                                }}
                                className={`w-full flex items-center justify-between px-2 py-1 rounded-md text-xs transition-colors ${
                                  isActive
                                    ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 font-medium"
                                    : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800/60"
                                }`}
                              >
                                <span>{opt.label}</span>
                                {isActive && (
                                  <Check
                                    className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400"
                                    aria-hidden="true"
                                  />
                                )}
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      <div className="pt-2 border-t border-zinc-200 dark:border-zinc-800 space-y-1.5">
                        <div className="px-1 text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                          Legend
                        </div>
                        <div className="grid grid-cols-2 gap-x-2 gap-y-1 px-1">
                          {STATUS_LEGEND.map((entry) => (
                            <div
                              key={entry.status}
                              className="flex items-center gap-1.5 text-[11px] text-zinc-600 dark:text-zinc-400"
                            >
                              <span
                                className={`w-2 h-2 rounded-full shrink-0 ${statusDotClass(
                                  entry.status
                                )}`}
                                aria-hidden="true"
                              />
                              <span className="truncate">{entry.label}</span>
                            </div>
                          ))}
                        </div>
                        <div className="grid grid-cols-2 gap-x-2 gap-y-1 px-1 pt-1 border-t border-zinc-100 dark:border-zinc-800/70">
                          <div className="flex items-center gap-1.5 text-[11px] text-zinc-600 dark:text-zinc-400">
                            <MessageSquare
                              className="w-3 h-3 text-zinc-400 dark:text-zinc-500 shrink-0"
                              aria-hidden="true"
                            />
                            <span className="truncate">Notes</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-[11px] text-zinc-600 dark:text-zinc-400">
                            <MessageSquare
                              className="w-3 h-3 text-zinc-900 dark:text-zinc-100 fill-zinc-900 dark:fill-zinc-100 shrink-0"
                              aria-hidden="true"
                            />
                            <span className="truncate">Due today</span>
                          </div>
                        </div>
                      </div>
                    </PopoverContent>
                  </div>
                </Popover>
              </div>
            </div>

            {/* Pinned Current Row */}
            {currentPinnedItem && (
              <div className="shrink-0 pb-2 mb-2 border-b border-zinc-200 dark:border-zinc-800 space-y-1">
                <div className="px-1 text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                  Current
                </div>
                <button
                  type="button"
                  onClick={() => handlePick(currentPinnedItem.id)}
                  title={formatFullRowCode(currentPinnedItem)}
                  className={`group w-full text-left px-1.5 py-1.5 ${
                    isSidebar ? "min-h-[44px] lg:min-h-0 " : ""
                  }rounded-lg bg-indigo-50 dark:bg-indigo-500/10 ring-1 ring-indigo-500/40 dark:ring-indigo-400/40 hover:bg-indigo-50/90 dark:hover:bg-indigo-500/15 transition-colors flex items-center gap-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/70 dark:focus-visible:ring-indigo-400/70`}
                >
                  <StatusDot status={currentPinnedItem.practiceStatus} />
                  <NoteBadge
                    hasNotes={currentPinnedHasNotes}
                    isDueToday={currentPinnedIsDue}
                  />
                  <span className="text-xs font-medium text-zinc-900 dark:text-zinc-100 truncate min-w-0 flex-1">
                    {currentPinnedItem.setLabel
                      ? `${plainTitle(currentPinnedItem.title)} · ${currentPinnedItem.setLabel}`
                      : plainTitle(currentPinnedItem.title)}
                  </span>
                  <HoverRowCode code={extractLeafHoverCode(currentPinnedItem)} />
                </button>
              </div>
            )}

            {/* Scrollable Curriculum Tree */}
            <div
              ref={scrollContainerRef}
              className="flex-1 min-h-0 overflow-y-auto overscroll-contain pr-1"
            >
              {isTreeEmpty ? (
                <div className="py-8 text-center space-y-2">
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {isCodeWorkspace && activeTab === "labs"
                      ? "No labs match the current search or filter."
                      : "No drills match the current search or filter."}
                  </p>
                  {otherTabMatchCount > 0 && (
                    <button
                      type="button"
                      onClick={() => {
                        setActiveTab(activeTab === "labs" ? "drills" : "labs");
                        setActiveNodeId(null);
                      }}
                      className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                      Show {otherTabMatchCount} matching{" "}
                      {activeTab === "labs"
                        ? otherTabMatchCount === 1
                          ? "drill"
                          : "drills"
                        : otherTabMatchCount === 1
                        ? "lab"
                        : "labs"}
                    </button>
                  )}
                </div>
              ) : (
                <div
                  role="tree"
                  aria-label="Practice curriculum"
                  className="space-y-0.5 py-0.5"
                >
                  {sections.topicGroups.map((topic) => {
                    const topicNodeId = `topic:${topic.topicCode}`;
                    const isTopicExpanded = expandedTopics.has(topic.topicCode);
                    const showTopicCode = topic.topicTitle !== topic.topicCode;

                    return (
                      <div key={topic.topicCode}>
                        <button
                          ref={(el) => registerNodeRef(topicNodeId, el)}
                          type="button"
                          role="treeitem"
                          aria-level={1}
                          aria-expanded={isTopicExpanded}
                          aria-selected={false}
                          title={topic.topicCode}
                          onClick={() => {
                            setActiveNodeId(topicNodeId);
                            setBranchExpanded("topic", topic.topicCode, "toggle");
                          }}
                          className={branchRowCls}
                        >
                          <ChevronRight
                            className={`w-3.5 h-3.5 text-zinc-400 shrink-0 transition-transform duration-150 ${
                              isTopicExpanded ? "rotate-90" : ""
                            }`}
                            aria-hidden="true"
                          />
                          <Layers
                            className="w-3.5 h-3.5 text-zinc-400 dark:text-zinc-500 shrink-0"
                            aria-hidden="true"
                          />
                          <span className="text-xs font-medium text-zinc-900 dark:text-zinc-100 truncate min-w-0 flex-1">
                            {plainTitle(topic.topicTitle)}
                          </span>
                          {showTopicCode && <HoverRowCode code={topic.topicCode} />}
                        </button>

                        <Reveal show={isTopicExpanded}>
                          <div
                            role="group"
                            className="ml-3 pl-2 border-l border-zinc-200 dark:border-zinc-800 space-y-0.5 py-0.5"
                          >
                            {topic.chapters.map((chapter) => {
                              const chapterNodeId = `chapter:${chapter.chapterCode}`;
                              const isChapterExpanded = expandedChapters.has(
                                chapter.chapterCode
                              );
                              const chapterShortCode = extractChapterShortCode(
                                chapter.chapterCode
                              );
                              const showChapterCode =
                                chapter.chapterTitle !== chapterShortCode;

                              return (
                                <div key={chapter.chapterCode}>
                                  <button
                                    ref={(el) => registerNodeRef(chapterNodeId, el)}
                                    type="button"
                                    role="treeitem"
                                    aria-level={2}
                                    aria-expanded={isChapterExpanded}
                                    aria-selected={false}
                                    title={chapter.chapterCode}
                                    onClick={() => {
                                      setActiveNodeId(chapterNodeId);
                                      setBranchExpanded(
                                        "chapter",
                                        chapter.chapterCode,
                                        "toggle"
                                      );
                                    }}
                                    className={branchRowCls}
                                  >
                                    <ChevronRight
                                      className={`w-3.5 h-3.5 text-zinc-400 shrink-0 transition-transform duration-150 ${
                                        isChapterExpanded ? "rotate-90" : ""
                                      }`}
                                      aria-hidden="true"
                                    />
                                    <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300 truncate min-w-0 flex-1">
                                      {plainTitle(chapter.chapterTitle)}
                                    </span>
                                    {showChapterCode && (
                                      <HoverRowCode code={chapterShortCode} />
                                    )}
                                    <CountPill count={chapter.itemCount} />
                                  </button>

                                  <Reveal show={isChapterExpanded}>
                                    <div
                                      role="group"
                                      className="ml-3 pl-2 border-l border-zinc-200 dark:border-zinc-800 space-y-0.5 py-0.5"
                                    >
                                      {chapter.entries.map((entry) => {
                                        if (entry.kind === "single") {
                                          return renderLeafRow(
                                            entry.item,
                                            entry.item.title,
                                            3,
                                            `leaf:${entry.item.id}`
                                          );
                                        }

                                        if (entry.inlineInChapter) {
                                          return entry.items.map((setEntry) =>
                                            renderLeafRow(
                                              setEntry.item,
                                              setEntry.setLabel,
                                              3,
                                              `leaf:${setEntry.item.id}`
                                            )
                                          );
                                        }

                                        const unitNodeId = `unit:${entry.unitCode}`;
                                        const isUnitExpanded = expandedUnits.has(
                                          entry.unitCode
                                        );
                                        const unitShortCode = extractShortCode({
                                          kind: "drill",
                                          id: entry.unitCode,
                                          unitCode: entry.unitCode,
                                        });

                                        return (
                                          <div key={entry.key}>
                                            <button
                                              ref={(el) =>
                                                registerNodeRef(unitNodeId, el)
                                              }
                                              type="button"
                                              role="treeitem"
                                              aria-level={3}
                                              aria-expanded={isUnitExpanded}
                                              aria-selected={false}
                                              title={entry.unitCode}
                                              onClick={() => {
                                                setActiveNodeId(unitNodeId);
                                                setBranchExpanded(
                                                  "unit",
                                                  entry.unitCode,
                                                  "toggle"
                                                );
                                              }}
                                              className={branchRowCls}
                                            >
                                              <ChevronRight
                                                className={`w-3.5 h-3.5 text-zinc-400 shrink-0 transition-transform duration-150 ${
                                                  isUnitExpanded ? "rotate-90" : ""
                                                }`}
                                                aria-hidden="true"
                                              />
                                              <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300 truncate min-w-0 flex-1">
                                                {plainTitle(entry.unitTitle)}
                                              </span>
                                              <HoverRowCode code={unitShortCode} />
                                              <CountPill count={entry.items.length} />
                                            </button>

                                            <Reveal show={isUnitExpanded}>
                                              <div
                                                role="group"
                                                className="ml-3 pl-2 border-l border-zinc-200 dark:border-zinc-800 space-y-0.5 py-0.5"
                                              >
                                                {entry.items.map((setEntry) =>
                                                  renderLeafRow(
                                                    setEntry.item,
                                                    setEntry.setLabel,
                                                    4,
                                                    `leaf:${setEntry.item.id}`
                                                  )
                                                )}
                                              </div>
                                            </Reveal>
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </Reveal>
                                </div>
                              );
                            })}
                          </div>
                        </Reveal>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
    </>
  );

  if (isSidebar) {
    return (
      <div
        ref={switcherRef}
        onKeyDown={handlePopoverKeyDown}
        className="flex-1 min-h-0 flex flex-col px-2.5 pt-2.5 pb-1.5"
      >
        {pickerBody}
      </div>
    );
  }

  return (
    <div className="sm:relative min-w-0 flex-1 sm:flex-initial" ref={switcherRef}>
      <button
        ref={triggerRef}
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        aria-label="Switch practice drill"
        className="w-full sm:w-auto inline-flex items-center justify-between gap-2 h-9 px-3 rounded-lg bg-zinc-100/80 dark:bg-zinc-800/70 hover:bg-zinc-200/70 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 text-left transition-colors min-w-0"
      >
        <span className="text-xs sm:text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate max-w-[220px] sm:max-w-[300px] md:max-w-[360px]">
          {currentDrill
            ? plainTitle(currentDrill.unitTitle) || currentDrill.unitCode
            : "Select practice drill"}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-zinc-500 dark:text-zinc-400 shrink-0 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <m.div
            variants={popover}
            {...presence}
            style={{ transformOrigin: "top left" }}
            role="dialog"
            aria-label="Practice drill picker"
            onKeyDown={handlePopoverKeyDown}
            className="absolute left-0 right-0 top-full mt-2 max-w-[460px] sm:right-auto sm:w-[min(calc(100vw-2.75rem),460px)] max-h-[72vh] flex flex-col overflow-hidden bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-lg p-3 z-50"
          >
            {pickerBody}
          </m.div>
        )}
      </AnimatePresence>
    </div>
  );
};
