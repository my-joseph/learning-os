"use client";

import React, { useEffect, useId, useMemo, useRef, useState } from "react";
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
  type PickerTopicGroup,
  type TreeNavKey,
  type VisibleTreeRow,
} from "@/lib/drillGrouping";
import { isLabId, subjectOf, type Workspace } from "@/lib/routes";
import { statusTone } from "@/lib/statusTone";
import { ListRow } from "@/components/ui/ListRow";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Badge } from "@/components/ui/shadcn/Badge";
import { plainTitle } from "@/lib/titleText";
import { DrillFilter } from "@/hooks/types";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/shadcn/Tabs";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/shadcn/Popover";

import { DrillRowActions } from "./DrillRowActions";

const noop = () => {};

type PickerTab = "drills" | "labs";
export type PrgSidebarSection = "labs" | "drills";

export const PRG_SECTION_STORAGE_KEYS: Record<PrgSidebarSection, string> = {
  labs: "practice-studio:prg-sidebar-section:labs",
  drills: "practice-studio:prg-sidebar-section:drills",
};

/** Read a PRG sidebar section's expanded state from localStorage (defaults to true). */
export function readSidebarSectionExpanded(section: PrgSidebarSection): boolean {
  if (typeof window === "undefined") return true;
  try {
    const saved = window.localStorage.getItem(PRG_SECTION_STORAGE_KEYS[section]);
    if (saved === "false") return false;
    return true;
  } catch {
    return true;
  }
}

/** Persist a PRG sidebar section's expanded state safely to localStorage. */
export function writeSidebarSectionExpanded(
  section: PrgSidebarSection,
  expanded: boolean
): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(PRG_SECTION_STORAGE_KEYS[section], String(expanded));
  } catch {
    // ignore localStorage access/quota failures
  }
}

function CollapsibleSidebarSection({
  section,
  label,
  expanded,
  onToggle,
  panelId,
  children,
}: {
  section: PrgSidebarSection;
  label: string;
  expanded: boolean;
  onToggle: () => void;
  panelId: string;
  children: React.ReactNode;
}) {
  return (
    <div data-sidebar-section={section} className="space-y-space-0_5">
      <SectionHeader expanded={expanded} controls={panelId} onClick={onToggle}>
        {label}
      </SectionHeader>
      <div id={panelId} hidden={!expanded}>
        <Reveal show={expanded}>
          <div className="space-y-space-0_5 pt-space-0_5">{children}</div>
        </Reveal>
      </div>
    </div>
  );
}

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
  drillSearch?: string;
  onSearchChange?: (value: string) => void;
  drillFilter?: DrillFilter;
  onFilterChange?: (filter: DrillFilter) => void;
  onSelectDrill: (drillId: string) => void;
  onResetDrill?: (drillId: string) => void;
  onDeleteDrill?: (drillId: string) => void;
}

function statusDotClass(status: PickerStatus): string {
  switch (status) {
    case "Graded":
      return statusTone.correct.dot;
    case "In Progress":
      return "bg-accent";
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
      className="inline-flex items-center justify-center size-space-3_5 shrink-0"
      title={label}
    >
      <span
        className={`size-space-2 rounded-full ${statusDotClass(status)}`}
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
        className="size-space-3_5 p-0 rounded-none gap-0 inline-flex items-center justify-center shrink-0"
        title={hasNotes ? "Due today · has notes" : "Due today"}
      >
        <MessageSquare
          className="size-space-3 text-foreground fill-current"
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
        className="size-space-3_5 p-0 rounded-none gap-0 inline-flex items-center justify-center shrink-0"
        title="Has notes or mistake tags"
      >
        <MessageSquare
          className="size-space-3 text-foreground-faint"
          aria-hidden="true"
        />
        <span className="sr-only">Has notes</span>
      </Badge>
    );
  }
  return null;
}

function HoverRowCode({ code, isSidebar = false }: { code: string; isSidebar?: boolean }) {
  // Zero-width anchor: the code floats over the end of the title on hover, so the row never
  // changes width (no jitter) and nothing is reserved when not hovered.
  return (
    <span className="relative w-0 shrink-0 self-stretch">
      <span
        data-sidebar-row-code={isSidebar || undefined}
        aria-hidden={isSidebar || undefined}
        className={`pointer-events-none absolute right-space-1_5 top-1/2 -translate-y-1/2 hidden ${isSidebar ? "" : "group-hover:block group-focus-visible:block "}whitespace-nowrap rounded px-space-1 bg-surface-hover font-display text-2xs text-muted tabular-nums`}
      >
        {code}
      </span>
    </span>
  );
}

function CountPill({ count, isSidebar = false }: { count: number; isSidebar?: boolean }) {
  return (
    <Badge
      variant="status"
      className={`text-2xs font-display tabular-nums text-muted ${
        isSidebar ? "bg-transparent" : "bg-surface-hover"
      } px-space-1_5 py-space-0_5 rounded-full shrink-0`}
    >
      {count}
    </Badge>
  );
}

const BRANCH_ROW_CLASS =
  "group w-full flex items-center gap-space-1_5 px-space-1_5 py-space-1_5 rounded-md text-left transition-colors focus:outline-none hover:bg-surface-hover/80 dark:hover:bg-surface-hover/60 focus-visible:bg-surface-hover dark:focus-visible:bg-surface-hover/80 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500/70 dark:focus-visible:ring-indigo-400/70";

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
  drillSearch = "",
  onSearchChange = noop,
  drillFilter = "ALL",
  onFilterChange = noop,
  onSelectDrill,
  onResetDrill = () => {},
  onDeleteDrill = () => {},
}) => {
  const isSidebar = mode === "sidebar";
  const isCodeWorkspace =
    workspace === "code" ||
    (workspace === undefined && (labs.length > 0 || subjectOf(selectedDrillId) === "code"));
  const isUnifiedCodeSidebar = isSidebar && isCodeWorkspace;

  const defaultTab: PickerTab =
    isCodeWorkspace && isLabId(selectedDrillId) ? "labs" : "drills";

  const [activeTab, setActiveTab] = useState<PickerTab>(defaultTab);
  const [isLabsSectionExpanded, setIsLabsSectionExpanded] = useState(true);
  const [isDrillsSectionExpanded, setIsDrillsSectionExpanded] = useState(true);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const [openActionNodeId, setOpenActionNodeId] = useState<string | null>(null);
  const labsPanelId = useId();
  const drillsPanelId = useId();

  useEffect(() => {
    if (!isUnifiedCodeSidebar) return;
    setIsLabsSectionExpanded(readSidebarSectionExpanded("labs"));
    setIsDrillsSectionExpanded(readSidebarSectionExpanded("drills"));
  }, [isUnifiedCodeSidebar]);

  const toggleSection = (section: PrgSidebarSection) => {
    if (section === "labs") {
      setIsLabsSectionExpanded((prev) => {
        const next = !prev;
        writeSidebarSectionExpanded("labs", next);
        return next;
      });
    } else {
      setIsDrillsSectionExpanded((prev) => {
        const next = !prev;
        writeSidebarSectionExpanded("drills", next);
        return next;
      });
    }
  };

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
  const currentTreeRef = useRef<HTMLElement | null>(null);
  const nodeRefs = useRef(new Map<string, HTMLElement>());
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

  const labSections = useMemo(
    () =>
      isUnifiedCodeSidebar
        ? buildPickerSections({
            items: labItems,
            currentId: selectedDrillId,
            recentIds: [],
            search: drillSearch,
            filter: drillFilter,
          })
        : null,
    [isUnifiedCodeSidebar, labItems, selectedDrillId, drillSearch, drillFilter]
  );

  const activeItems = useMemo(
    () =>
      isUnifiedCodeSidebar
        ? drillItems
        : isCodeWorkspace && activeTab === "labs"
          ? labItems
          : drillItems,
    [isUnifiedCodeSidebar, isCodeWorkspace, activeTab, labItems, drillItems]
  );

  const otherTabMatchCount = useMemo(() => {
    if (isUnifiedCodeSidebar || !isCodeWorkspace || !drillSearch.trim()) return 0;
    const otherItems = activeTab === "labs" ? drillItems : labItems;
    return filterPickerItems(otherItems, drillSearch, drillFilter).length;
  }, [isUnifiedCodeSidebar, isCodeWorkspace, activeTab, drillItems, labItems, drillSearch, drillFilter]);

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

  const isFilterActive = drillFilter !== "ALL";
  const isFilteringOrSearching = sections.isSearching || isFilterActive;
  const labTopicCount = labSections?.topicGroups.length ?? 0;
  const showLabsSection =
    isUnifiedCodeSidebar && (!isFilteringOrSearching || labTopicCount > 0);
  const showDrillsSection =
    isUnifiedCodeSidebar && (!isFilteringOrSearching || sections.topicGroups.length > 0);
  const effectiveLabsExpanded = sections.isSearching
    ? labTopicCount > 0
    : isLabsSectionExpanded;
  const effectiveDrillsExpanded = sections.isSearching
    ? sections.topicGroups.length > 0
    : isDrillsSectionExpanded;

  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(
    () => new Set(sections.defaultExpandedTopics)
  );
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(
    () => new Set(sections.defaultExpandedChapters)
  );
  const [expandedUnits, setExpandedUnits] = useState<Set<string>>(
    () => new Set(sections.defaultExpandedUnits)
  );
  const [expandedLabTopics, setExpandedLabTopics] = useState<Set<string>>(
    () => new Set(labSections?.defaultExpandedTopics ?? [])
  );
  const [expandedLabChapters, setExpandedLabChapters] = useState<Set<string>>(
    () => new Set(labSections?.defaultExpandedChapters ?? [])
  );
  const [expandedLabUnits, setExpandedLabUnits] = useState<Set<string>>(
    () => new Set(labSections?.defaultExpandedUnits ?? [])
  );

  const allTreeCodes = useMemo(
    () => collectAllTreeCodes(sections.topicGroups),
    [sections.topicGroups]
  );

  const visibleTreeRows = useMemo(() => {
    if (isUnifiedCodeSidebar) {
      const rows: VisibleTreeRow[] = [];
      if (showLabsSection && effectiveLabsExpanded && labSections) {
        rows.push(
          ...buildVisibleTreeRows({
            topicGroups: labSections.topicGroups,
            currentId: selectedDrillId,
            expandedTopics: expandedLabTopics,
            expandedChapters: expandedLabChapters,
            expandedUnits: expandedLabUnits,
            dueUnitCodes: dueUnitSet,
            currentHasNotesOverride: currentDrillHasNotes,
            nodeIdPrefix: "lab:",
          })
        );
      }
      if (showDrillsSection && effectiveDrillsExpanded) {
        rows.push(
          ...buildVisibleTreeRows({
            topicGroups: sections.topicGroups,
            currentId: selectedDrillId,
            expandedTopics,
            expandedChapters,
            expandedUnits,
            dueUnitCodes: dueUnitSet,
            currentHasNotesOverride: currentDrillHasNotes,
          })
        );
      }
      return rows;
    }
    return buildVisibleTreeRows({
      topicGroups: sections.topicGroups,
      currentId: selectedDrillId,
      expandedTopics,
      expandedChapters,
      expandedUnits,
      dueUnitCodes: dueUnitSet,
      currentHasNotesOverride: currentDrillHasNotes,
    });
  }, [
    isUnifiedCodeSidebar,
    showLabsSection,
    effectiveLabsExpanded,
    labSections,
    expandedLabTopics,
    expandedLabChapters,
    expandedLabUnits,
    showDrillsSection,
    effectiveDrillsExpanded,
    sections.topicGroups,
    selectedDrillId,
    expandedTopics,
    expandedChapters,
    expandedUnits,
    dueUnitSet,
    currentDrillHasNotes,
  ]);

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
  const defaultLabTopicsKey = (labSections?.defaultExpandedTopics ?? []).join("|");
  const defaultLabChaptersKey = (labSections?.defaultExpandedChapters ?? []).join("|");
  const defaultLabUnitsKey = (labSections?.defaultExpandedUnits ?? []).join("|");

  // Expand matching branches on search, initial data arrival, or open/tab/drill/filter change.
  useEffect(() => {
    if (!isOpen) return;
    setExpandedTopics(new Set(sections.defaultExpandedTopics));
    setExpandedChapters(new Set(sections.defaultExpandedChapters));
    setExpandedUnits(new Set(sections.defaultExpandedUnits));
    if (labSections) {
      setExpandedLabTopics(new Set(labSections.defaultExpandedTopics));
      setExpandedLabChapters(new Set(labSections.defaultExpandedChapters));
      setExpandedLabUnits(new Set(labSections.defaultExpandedUnits));
    }
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
    defaultLabTopicsKey,
    defaultLabChaptersKey,
    defaultLabUnitsKey,
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
    mode: "toggle" | "expand" | "collapse",
    scope: "drills" | "labs" = "drills"
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
    if (scope === "labs") {
      if (kind === "topic") setExpandedLabTopics(updater);
      else if (kind === "chapter") setExpandedLabChapters(updater);
      else setExpandedLabUnits(updater);
      return;
    }
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
    const actionScope = activeNodeId?.startsWith("lab:") ? "labs" : "drills";
    if (action.type === "focus") {
      focusTreeNode(action.nodeId);
    } else if (action.type === "expand") {
      setBranchExpanded(action.nodeKind, action.code, "expand", actionScope);
    } else if (action.type === "collapse") {
      setBranchExpanded(action.nodeKind, action.code, "collapse", actionScope);
    } else if (action.type === "toggle") {
      setBranchExpanded(action.nodeKind, action.code, "toggle", actionScope);
    } else if (action.type === "select") {
      handlePick(action.itemId);
    }
  };

  const registerNodeRef = (nodeId: string, el: HTMLElement | null) => {
    if (el) {
      nodeRefs.current.set(nodeId, el);
    } else {
      nodeRefs.current.delete(nodeId);
    }
  };

  const currentPinnedItem =
    !isSidebar && !sections.isSearching && sections.currentItem ? sections.currentItem : null;
  const currentPinnedHasNotes = currentPinnedItem
    ? currentPinnedItem.hasNotes || Boolean(currentDrillHasNotes)
    : false;
  const currentPinnedIsDue = currentPinnedItem
    ? dueUnitSet.has(currentPinnedItem.unitCode)
    : false;

  const isTreeEmpty = isUnifiedCodeSidebar
    ? !showLabsSection && !showDrillsSection
    : sections.topicGroups.length === 0;

  const expandCollapseButtons = (
    <>
      <button
        type="button"
        onClick={handleExpandAll}
        disabled={isTreeEmpty}
        className={`inline-flex items-center gap-space-1 ${
          isSidebar
            ? "px-space-2 min-h-touch lg:min-h-control-md bg-surface-raised dark:bg-surface-raised/60 hover:bg-surface-hover dark:hover:bg-surface-selected/40"
            : "px-space-2 bg-surface-raised hover:bg-background dark:hover:bg-surface-hover/70"
        } py-space-1 rounded-md border border-border disabled:opacity-40 ${isSidebar ? "text-sm" : "text-2xs"} font-medium text-foreground-control transition-colors whitespace-nowrap`}
      >
        <ChevronsUpDown className={`${isSidebar ? "size-space-3_5" : "size-space-3"} text-foreground-faint dark:text-muted shrink-0`} aria-hidden="true" />
        <span>Expand all</span>
      </button>
      <button
        type="button"
        onClick={handleCollapseAll}
        disabled={isTreeEmpty}
        className={`inline-flex items-center gap-space-1 ${
          isSidebar
            ? "px-space-2 min-h-touch lg:min-h-control-md bg-surface-raised dark:bg-surface-raised/60 hover:bg-surface-hover dark:hover:bg-surface-selected/40"
            : "px-space-2 bg-surface-raised hover:bg-background dark:hover:bg-surface-hover/70"
        } py-space-1 rounded-md border border-border disabled:opacity-40 ${isSidebar ? "text-sm" : "text-2xs"} font-medium text-foreground-control transition-colors whitespace-nowrap`}
      >
        <ChevronsDownUp className={`${isSidebar ? "size-space-3_5" : "size-space-3"} text-foreground-faint dark:text-muted shrink-0`} aria-hidden="true" />
        <span>Collapse all</span>
      </button>
    </>
  );

  const renderBranchRow = (
    kind: "topic" | "chapter" | "unit",
    code: string,
    title: string,
    expanded: boolean,
    scope: "drills" | "labs",
    hoverCode?: string,
    count?: number
  ) => {
    const depth = kind === "topic" ? 1 : kind === "chapter" ? 2 : 3;
    const nodeId = `${scope === "labs" ? "lab:" : ""}${kind}:${code}`;
    const rowProps = {
      role: "treeitem",
      "aria-level": depth,
      "aria-expanded": expanded,
      "aria-selected": false,
      title: code,
      onClick: () => {
        setActiveNodeId(nodeId);
        setBranchExpanded(kind, code, "toggle", scope);
      },
      ref: (el: HTMLElement | null) => registerNodeRef(nodeId, el),
    };
    const leading = (
      <>
        <ChevronRight
          className={`size-space-3_5 shrink-0 text-foreground-faint transition-transform duration-color motion-reduce:transition-none dark:text-muted ${expanded ? "rotate-90" : ""}`}
          aria-hidden="true"
        />
        {kind === "topic" && (
          <Layers className="size-space-3_5 shrink-0 text-foreground-faint" aria-hidden="true" />
        )}
      </>
    );
    const trailing = (
      <>
        {hoverCode && <HoverRowCode code={hoverCode} isSidebar={isSidebar} />}
        {count !== undefined && <CountPill count={count} isSidebar={isSidebar} />}
      </>
    );

    return (
      <div className={`flex items-center gap-space-0_5 ${isSidebar ? "h-control-sm" : "group"}`}>
        {isSidebar ? (
          <ListRow
            {...rowProps}
            data-sidebar-row={kind}
            variant="tree"
            treeDepth={depth}
            className={kind === "topic" ? "text-foreground" : undefined}
            emphasis="medium"
            leading={leading}
            label={plainTitle(title)}
            trailing={trailing}
          />
        ) : (
          <button {...rowProps} type="button" className={`${BRANCH_ROW_CLASS} flex-1`}>
            {leading}
            <span className={`text-xs font-medium truncate min-w-0 flex-1 ${kind === "topic" ? "text-foreground" : "text-foreground-control"}`}>
              {plainTitle(title)}
            </span>
            {trailing}
          </button>
        )}
      </div>
    );
  };

  const renderLeafRow = (
    item: PickerItem,
    label: string,
    level: 1 | 3 | 4,
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
    const rowProps = {
      role: "treeitem",
      "aria-level": level,
      "aria-selected": isCurrent,
      "aria-current": isCurrent ? "true" as const : undefined,
      title: fullCode,
      onClick: () => {
        setActiveNodeId(nodeId);
        handlePick(item.id);
      },
      ref: (el: HTMLElement | null) => {
        registerNodeRef(nodeId, el);
        if (isCurrent) currentTreeRef.current = el;
      },
    };
    const leading = (
      <>
        <StatusDot status={item.practiceStatus} />
        <NoteBadge hasNotes={hasNotes} isDueToday={isDueToday} />
      </>
    );
    const trailing = <HoverRowCode code={hoverCode} isSidebar={isSidebar} />;

    if (isSidebar) {
      return (
        <ListRow
          {...rowProps}
          key={nodeId}
          variant="tree"
          treeDepth={level}
          selected={isCurrent}
          emphasis={isCurrent ? "medium" : "normal"}
          leading={leading}
          label={plainTitle(label)}
          trailing={trailing}
          treeLeaf={{
            actionOpen: openActionNodeId === item.id,
            highlighted: isSearchTarget,
            surfaceProps: {
              "data-sidebar-leaf": item.id,
              "data-sidebar-row": `leaf-${level}`,
            },
            action: item.kind === "drill" && (
              <DrillRowActions
                nodeId={item.id}
                onReset={onResetDrill}
                onDelete={onDeleteDrill}
                open={openActionNodeId === item.id}
                onOpenChange={(open) => setOpenActionNodeId(open ? item.id : null)}
              />
            ),
          }}
        />
      );
    }

    return (
      <div key={nodeId} className="group/leaf flex min-w-0 items-center gap-space-0_5">
        <button
          {...rowProps}
          type="button"
          className={`group flex w-full min-w-0 items-center gap-space-1_5 overflow-hidden rounded-md px-space-1_5 py-space-1_5 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent/70 ${
            isCurrent
              ? "bg-indigo-50 dark:bg-indigo-500/10 ring-1 ring-inset ring-indigo-500/50 dark:ring-accent/50"
              : isSearchTarget
                ? "bg-surface-hover dark:bg-surface-hover/80 ring-2 ring-inset ring-indigo-500/70 dark:ring-accent/70"
                : "hover:bg-surface-hover/80 dark:hover:bg-surface-hover/60 focus-visible:bg-surface-hover dark:focus-visible:bg-surface-hover/80"
          }`}
        >
          {leading}
          <span className={`text-xs truncate min-w-0 flex-1 ${isCurrent ? "font-medium text-foreground" : "text-foreground-control"}`}>
            {plainTitle(label)}
          </span>
          {trailing}
        </button>
      </div>
    );
  };

  const pickerBody = (
    <>
            {!isSidebar && (
              <div className="mb-space-2 flex shrink-0 items-center gap-space-2 rounded-lg border border-border bg-surface-panel px-space-2_5 py-space-1_5 transition-colors focus-within:border-indigo-600 focus-within:ring-2 focus-within:ring-indigo-600/20 dark:bg-surface-raised dark:focus-within:border-indigo-400 dark:focus-within:ring-indigo-400/25">
                <Search className="size-space-3_5 shrink-0 text-foreground-faint dark:text-muted" />
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
                  className="w-full bg-transparent text-xs text-foreground placeholder:text-foreground-faint dark:placeholder:text-muted focus:outline-none"
                  autoFocus
                />
                {drillSearch && (
                  <button
                    type="button"
                    onClick={() => {
                      onSearchChange("");
                      searchInputRef.current?.focus();
                    }}
                    aria-label="Clear search"
                    className="text-foreground-faint hover:text-foreground-subtle dark:text-muted dark:hover:text-foreground-menu"
                  >
                    <X className="size-space-3_5" />
                  </button>
                )}
              </div>
            )}

            {/* Legacy dropdown mode keeps Tabs + global tree controls; sidebar uses unified scrolling sections. */}
            {!isSidebar && <div className="shrink-0 flex flex-wrap items-center justify-between gap-space-1_5 pb-space-2 mb-space-2 border-b border-border">
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
                    className={`relative grid h-auto min-h-0 grid-cols-2 items-center rounded-lg border border-border p-space-0_5 ${
                      isSidebar
                        ? "bg-surface-selected/70 dark:bg-surface-raised/75"
                        : "bg-surface-selected/70 dark:bg-surface-panel"
                    }`}
                  >
                    <m.span
                      aria-hidden
                      className="absolute top-space-0_5 bottom-space-0_5 left-space-0_5 w-[calc(50%-var(--space-0-5))] rounded-md shadow-ui-sm bg-surface-raised dark:bg-surface-selected/80"
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
                          className={`relative z-local inline-flex ${
                            isSidebar ? "h-8" : "min-h-0"
                          } items-center justify-center gap-space-1_5 rounded-md bg-transparent px-space-2_5 py-space-1 ${isSidebar ? "text-sm" : "text-xs"} font-medium text-muted shadow-none transition-colors whitespace-nowrap hover:text-foreground data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none dark:hover:text-foreground-menu`}
                        >
                          <span>{tab.label}</span>
                          <span className="text-2xs font-display tabular-nums text-muted">
                            {tab.count}
                          </span>
                        </TabsTrigger>
                      );
                    })}
                  </TabsList>
                </Tabs>
              ) : (
                <div className={`inline-flex items-center ${isSidebar ? "gap-space-1" : "gap-space-1_5"}`}>
                  {expandCollapseButtons}
                </div>
              )}

              {!isSidebar && <div className="flex shrink-0 items-center gap-space-1_5">
                {isCodeWorkspace && expandCollapseButtons}

                {/* View Button + Popover */}
                <Popover open={isViewOpen} onOpenChange={setIsViewOpen}>
                  <div className="relative">
                    <PopoverTrigger asChild>
                      <button
                        ref={viewButtonRef}
                        type="button"
                        aria-expanded={isViewOpen}
                        className={`inline-flex items-center gap-space-1 ${
                          isSidebar ? "px-space-2 min-h-touch lg:min-h-control-md " : "px-space-2 "
                        }py-space-1 rounded-md border ${isSidebar ? "text-sm" : "text-2xs"} font-medium transition-colors whitespace-nowrap ${
                          isViewOpen || isFilterActive
                            ? "border-indigo-500/50 bg-indigo-50/70 dark:bg-indigo-500/10 text-foreground"
                            : isSidebar
                            ? "border-border bg-surface-raised dark:bg-surface-raised/60 hover:bg-surface-hover dark:hover:bg-surface-selected/40 text-foreground-control"
                            : "border-border bg-surface-raised hover:bg-background dark:hover:bg-surface-hover/70 text-foreground-control"
                        }`}
                      >
                        <SlidersHorizontal
                          className={`${isSidebar ? "size-space-3_5" : "size-space-3"} text-muted shrink-0`}
                          aria-hidden="true"
                        />
                        <span>View</span>
                        {isFilterActive && (
                          <span
                            className="size-space-1_5 rounded-full bg-accent"
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
                      className="w-space-52 rounded-xl p-space-2_5 z-tooltip space-y-space-2_5"
                    >
                      <div className="space-y-space-1">
                        <div className="px-space-1 text-2xs font-medium text-muted">
                          Status
                        </div>
                        <div
                          role="group"
                          aria-label="Filter by status"
                          className="space-y-space-0_5"
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
                                className={`w-full flex items-center justify-between px-space-2 py-space-1 rounded-md text-xs transition-colors ${
                                  isActive
                                    ? "bg-surface-hover text-foreground font-medium"
                                    : "text-foreground-subtle hover:bg-background dark:hover:bg-surface-hover/60"
                                } ${isSidebar ? "text-sm min-h-control-md" : "text-xs"}`}
                              >
                                <span>{opt.label}</span>
                                {isActive && (
                                  <Check
                                    className="size-space-3_5 text-accent"
                                    aria-hidden="true"
                                  />
                                )}
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      <div className="pt-space-2 border-t border-border space-y-space-1_5">
                        <div className="px-space-1 text-2xs font-medium text-muted">
                          Legend
                        </div>
                        <div className="grid grid-cols-2 gap-x-space-2 gap-y-space-1 px-space-1">
                          {STATUS_LEGEND.map((entry) => (
                            <div
                              key={entry.status}
                              className="flex items-center gap-space-1_5 text-2xs text-foreground-subtle"
                            >
                              <span
                                className={`size-space-2 rounded-full shrink-0 ${statusDotClass(
                                  entry.status
                                )}`}
                                aria-hidden="true"
                              />
                              <span className="truncate">{entry.label}</span>
                            </div>
                          ))}
                        </div>
                        <div className="grid grid-cols-2 gap-x-space-2 gap-y-space-1 px-space-1 pt-space-1 border-t border-surface-hover dark:border-border/70">
                          <div className="flex items-center gap-space-1_5 text-2xs text-foreground-subtle">
                            <MessageSquare
                              className="size-space-3 text-foreground-faint shrink-0"
                              aria-hidden="true"
                            />
                            <span className="truncate">Notes</span>
                          </div>
                          <div className="flex items-center gap-space-1_5 text-2xs text-foreground-subtle">
                            <MessageSquare
                              className="size-space-3 text-foreground fill-current shrink-0"
                              aria-hidden="true"
                            />
                            <span className="truncate">Due today</span>
                          </div>
                        </div>
                      </div>
                    </PopoverContent>
                  </div>
                </Popover>
              </div>}
            </div>}

            {/* Pinned Current Row */}
            {currentPinnedItem && (
              <div className="shrink-0 pb-space-2 mb-space-2 border-b border-border space-y-space-1">
                <div className="px-space-1 text-2xs font-medium text-muted">
                  Current
                </div>
                <button
                  type="button"
                  onClick={() => handlePick(currentPinnedItem.id)}
                  title={formatFullRowCode(currentPinnedItem)}
                  className={`group w-full text-left px-space-1_5 py-space-1_5 ${
                    isSidebar
                      ? "min-h-touch lg:min-h-control-md rounded-lg bg-surface-selected/70 dark:bg-surface-selected/60 hover:bg-surface-selected/90 dark:hover:bg-surface-selected/70"
                      : "rounded-lg bg-indigo-50 dark:bg-indigo-500/10 ring-1 ring-indigo-500/40 dark:ring-indigo-400/40 hover:bg-indigo-50/90 dark:hover:bg-indigo-500/15"
                  } transition-colors flex items-center gap-space-1_5 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/70 dark:focus-visible:ring-indigo-400/70`}
                >
                  <StatusDot status={currentPinnedItem.practiceStatus} />
                  <NoteBadge
                    hasNotes={currentPinnedHasNotes}
                    isDueToday={currentPinnedIsDue}
                  />
                  <span className={`${isSidebar ? "text-sm" : "text-xs"} font-medium text-foreground truncate min-w-0 flex-1`}>
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
              className="flex-1 min-h-0 overflow-y-auto overscroll-contain pr-space-1"
            >
              {isTreeEmpty ? (
                <div className="py-space-8 text-center space-y-space-2">
                  <p className={`${isSidebar ? "text-sm" : "text-xs"} text-muted`}>
                    {isSidebar && !isFilteringOrSearching
                      ? "No drills yet"
                      : isUnifiedCodeSidebar
                      ? "No drills or labs match the current search or filter."
                      : isCodeWorkspace && activeTab === "labs"
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
                      className={`${isSidebar ? "text-sm" : "text-xs"} font-medium text-accent hover:underline`}
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
                  data-sidebar-tree={isSidebar || undefined}
                  className={`${isUnifiedCodeSidebar ? "space-y-space-3" : "space-y-space-0_5"} py-space-0_5`}
                >
                  {(() => {
                    const renderTopicGroups = (
                      groups: readonly PickerTopicGroup[],
                      scope: "drills" | "labs" = "drills"
                    ) => {
                      const isLabsScope = scope === "labs";
                      const activeExpandedTopics = isLabsScope
                        ? expandedLabTopics
                        : expandedTopics;
                      const activeExpandedChapters = isLabsScope
                        ? expandedLabChapters
                        : expandedChapters;
                      const activeExpandedUnits = isLabsScope
                        ? expandedLabUnits
                        : expandedUnits;

                      return groups.map((topic) => {
                        const isTopicExpanded = activeExpandedTopics.has(topic.topicCode);
                        const showTopicCode = topic.topicTitle !== topic.topicCode;

                        return (
                          <div key={topic.topicCode} className={`flex flex-col ${isSidebar ? "w-full" : "group"}`}>
                            {renderBranchRow("topic", topic.topicCode, topic.topicTitle, isTopicExpanded, scope,
                              showTopicCode ? topic.topicCode : undefined)}

                            <Reveal show={isTopicExpanded}>
                              <div
                                role="group"
                                className={`${isSidebar ? "w-full " : "ml-space-3 "}space-y-space-0_5 py-space-0_5`}
                              >
                                {topic.chapters.map((chapter) => {
                                  const isChapterExpanded = activeExpandedChapters.has(
                                    chapter.chapterCode
                                  );
                                  const chapterShortCode = extractChapterShortCode(
                                    chapter.chapterCode
                                  );
                                  const showChapterCode =
                                    chapter.chapterTitle !== chapterShortCode;

                                  return (
                                    <div key={chapter.chapterCode} className={`flex flex-col ${isSidebar ? "w-full" : "group"}`}>
                                      {renderBranchRow("chapter", chapter.chapterCode, chapter.chapterTitle, isChapterExpanded, scope,
                                        showChapterCode ? chapterShortCode : undefined, chapter.itemCount)}

                                      <Reveal show={isChapterExpanded}>
                                        <div
                                          role="group"
                                          className={`${isSidebar ? "w-full " : "ml-space-3 "}space-y-space-0_5 py-space-0_5`}
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

                                            const isUnitExpanded = activeExpandedUnits.has(
                                              entry.unitCode
                                            );
                                            const unitShortCode = extractShortCode({
                                              kind: "drill",
                                              id: entry.unitCode,
                                              unitCode: entry.unitCode,
                                            });

                                            return (
                                              <div key={entry.key} className={`flex flex-col ${isSidebar ? "w-full" : "group"}`}>
                                                {renderBranchRow("unit", entry.unitCode, entry.unitTitle, isUnitExpanded, scope,
                                                  unitShortCode, entry.items.length)}

                                                <Reveal show={isUnitExpanded}>
                                                  <div
                                                    role="group"
                                                    className={`${isSidebar ? "w-full " : "ml-space-3 "}space-y-space-0_5 py-space-0_5`}
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
                      });
                    };

                    if (!isUnifiedCodeSidebar) {
                      return renderTopicGroups(sections.topicGroups);
                    }

                    return (
                      <>
                        {showLabsSection && (
                          <CollapsibleSidebarSection
                            section="labs"
                            label="Labs"
                            expanded={effectiveLabsExpanded}
                            onToggle={() => {
                              if (!sections.isSearching) {
                                toggleSection("labs");
                              }
                            }}
                            panelId={labsPanelId}
                          >
                            {labTopicCount === 0 ? (
                              <p className="px-space-1_5 py-space-1_5 text-xs text-foreground-faint">
                                No labs yet
                              </p>
                            ) : (
                              <div className="space-y-space-0_5">
                                {renderTopicGroups(labSections?.topicGroups ?? [], "labs")}
                              </div>
                            )}
                          </CollapsibleSidebarSection>
                        )}
                        {showDrillsSection && (
                          <CollapsibleSidebarSection
                            section="drills"
                            label="Drills"
                            expanded={effectiveDrillsExpanded}
                            onToggle={() => {
                              if (!sections.isSearching) {
                                toggleSection("drills");
                              }
                            }}
                            panelId={drillsPanelId}
                          >
                            {sections.topicGroups.length === 0 ? (
                              <p className="px-space-1_5 py-space-1_5 text-xs text-foreground-faint">
                                No drills yet
                              </p>
                            ) : (
                              <div className="space-y-space-0_5">
                                {renderTopicGroups(sections.topicGroups)}
                              </div>
                            )}
                          </CollapsibleSidebarSection>
                        )}
                      </>
                    );
                  })()}
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
        className="flex-1 min-h-0 flex flex-col px-space-2_5 pt-space-2_5 pb-space-1_5"
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
        className="w-full sm:w-auto inline-flex items-center justify-between gap-space-2 h-control-md px-space-3 rounded-lg bg-surface-hover/80 dark:bg-surface-hover/70 hover:bg-surface-selected/70 dark:hover:bg-surface-hover border border-border text-left transition-colors min-w-0"
      >
        <span className="text-xs sm:text-sm font-medium text-foreground truncate max-w-picker-title-sm sm:max-w-picker-title-md md:max-w-picker-title-lg">
          {currentDrill
            ? plainTitle(currentDrill.unitTitle) || currentDrill.unitCode
            : "Select practice drill"}
        </span>
        <ChevronDown
          className={`size-space-4 text-muted shrink-0 transition-transform duration-panel ${
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
            className="absolute left-0 right-0 top-full mt-space-2 max-w-picker sm:right-auto sm:w-[min(calc(100vw-var(--space-11)),var(--width-picker))] max-h-picker flex flex-col overflow-hidden bg-surface-raised border border-border rounded-xl shadow-ui-lg p-space-3 z-overlay"
          >
            {pickerBody}
          </m.div>
        )}
      </AnimatePresence>
    </div>
  );
};
