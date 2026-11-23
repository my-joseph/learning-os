"use client";

import React, { useState } from "react";
import { StudioSidebar } from "@/components/shell/StudioSidebar";
import type { LabListItem } from "@/lib/labModel";
import type { DrillFilter } from "@/hooks/types";
import type { Workspace } from "@/lib/routes";
import type { DrillListItem } from "@/types/drill";

const drills: DrillListItem[] = [
  {
    drillId: "DRL-MTH-T01-C01-01",
    subject: "MATH",
    topicCode: "MTH-T01",
    topicTitle: "Prealgebra",
    chapterCode: "MTH-T01-C01",
    chapterTitle: "Numbers and Operations",
    unitCode: "MTH-T01-C01",
    unitTitle: "Numbers and Operations",
    createdAt: "2026-11-24",
    questionCount: 4,
    difficultyMode: "Mixed",
    practiceStatus: "In Progress",
    score: 2,
    maxScore: 4,
    answeredCount: 2,
    localFilePath: "",
  },
  {
    drillId: "DRL-MTH-T01-C01-02",
    subject: "MATH",
    topicCode: "MTH-T01",
    topicTitle: "Prealgebra",
    chapterCode: "MTH-T01-C01",
    chapterTitle: "Numbers and Operations",
    unitCode: "MTH-T01-C01",
    unitTitle: "Numbers and Operations",
    createdAt: "2026-11-24",
    questionCount: 4,
    difficultyMode: "Mixed",
    practiceStatus: "Ready",
    score: 0,
    maxScore: 4,
    answeredCount: 0,
    localFilePath: "",
  },
  {
    drillId: "DRL-MTH-T01-C02-U01-01",
    subject: "MATH",
    topicCode: "MTH-T01",
    topicTitle: "Prealgebra",
    chapterCode: "MTH-T01-C02",
    chapterTitle: "Fractions",
    unitCode: "MTH-T01-C02-U01",
    unitTitle: "Equivalent Fractions",
    createdAt: "2026-11-24",
    questionCount: 4,
    difficultyMode: "Mixed",
    practiceStatus: "Ready",
    score: 0,
    maxScore: 4,
    answeredCount: 0,
    localFilePath: "",
  },
  {
    drillId: "DRL-PRG-T01-C01-U01-01",
    subject: "PRG",
    topicCode: "PRG-T01",
    topicTitle: "JavaScript Foundations",
    chapterCode: "PRG-T01-C01",
    chapterTitle: "Values and Variables",
    unitCode: "PRG-T01-C01-U01",
    unitTitle: "Primitive Values",
    createdAt: "2026-11-24",
    questionCount: 3,
    difficultyMode: "Mixed",
    practiceStatus: "Ready",
    score: 0,
    maxScore: 3,
    answeredCount: 0,
    localFilePath: "",
  },
];

const labs: LabListItem[] = [
  {
    id: "LAB-PRG-T01-C01-01",
    labId: "LAB-PRG-T01-C01-01",
    title: "Variable Inventory",
    unitCode: "PRG-T01-C01",
    chapterCode: "PRG-T01-C01",
    chapterTitle: "Values and Variables",
    topicCode: "PRG-T01",
    topicTitle: "JavaScript Foundations",
    unitsUsed: [],
    kind: "chapter-lab",
    milestoneCount: 2,
    practiceStatus: "Ready",
    passedCount: 0,
    reviseCount: 0,
    score: 0,
    maxScore: 2,
    progress: {
      passedCount: 0,
      reviseCount: 0,
      notStartedCount: 2,
      totalCount: 2,
      practiceStatus: "Ready",
      score: 0,
      maxScore: 2,
      updatedAt: null,
      milestones: {},
    },
  },
];

export default function SidebarFixturePage() {
  const [workspace, setWorkspace] = useState<Workspace>("math");
  const [selectedDrillId, setSelectedDrillId] = useState("DRL-MTH-T01-C01-01");
  const [drillSearch, setDrillSearch] = useState("");
  const [drillFilter, setDrillFilter] = useState<DrillFilter>("ALL");
  const props = {
    workspace,
    pillWorkspace: workspace,
    onSelectWorkspace: (next: Workspace) => {
      setWorkspace(next);
      if (next === "code") setSelectedDrillId("DRL-PRG-T01-C01-U01-01");
      else setSelectedDrillId("DRL-MTH-T01-C01-01");
    },
    mathHref: "#math",
    codeHref: "#code",
    currentDrill: null,
    drills,
    labs,
    selectedDrillId,
    drillSearch,
    onSearchChange: setDrillSearch,
    drillFilter,
    onFilterChange: setDrillFilter,
    onSelectDrill: setSelectedDrillId,
  };

  return (
    <main className="min-h-screen bg-white dark:bg-zinc-900">
      <div className="hidden h-screen lg:flex">
        <StudioSidebar {...props} />
      </div>
      <div className="h-screen lg:hidden">
        <StudioSidebar {...props} embedded />
      </div>
    </main>
  );
}
