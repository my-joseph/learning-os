"use client";

import React, { useState, useEffect, useCallback, useRef, useMemo } from "react";
import {
  Plus,
  RefreshCw,
  Send,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Sun,
  Moon,
  Search,
  ClipboardCheck,
  ArrowUpRight,
  Sigma,
  Terminal,
  Clock,
  PenLine,
  Flag,
  X,
  ArrowLeft,
  Check,
} from "lucide-react";
import {
  DrillDocument,
  DrillListItem,
  CheckResult,
} from "@/types/drill";
import { ProblemCard } from "@/components/ProblemCard";
import { QuizPaginationBar } from "@/components/QuizPaginationBar";
import { FormattedText } from "@/components/FormattedText";

export default function PracticeStudioPage() {
  const [drills, setDrills] = useState<DrillListItem[]>([]);
  const [currentDrill, setCurrentDrill] = useState<DrillDocument | null>(null);
  const [selectedDrillId, setSelectedDrillId] = useState<string>("");
  const [activeSteps, setActiveSteps] = useState<{ [probId: string]: number | null }>({});
  const [currentProblemIndex, setCurrentProblemIndex] = useState<number>(0);
  const [viewMode, setViewMode] = useState<"quiz" | "review">("quiz");
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [isLoadingDrill, setIsLoadingDrill] = useState<boolean>(true);

  // Popover states (Progressive Disclosure)
  const [showDrillSwitcher, setShowDrillSwitcher] = useState(false);
  const [showGenPopover, setShowGenPopover] = useState(false);
  const [drillSearch, setDrillSearch] = useState("");
  const [drillFilter, setDrillFilter] = useState<"ALL" | "UNFINISHED" | "GRADED" | "MATH" | "PRG">("ALL");

  // Pre-Sync Review custom status override
  const [statusOverride, setStatusOverride] = useState<"Graded" | "Needs Retry" | null>(null);

  // Auto-hide sticky header on scroll down, reveal on scroll up
  const [showHeader, setShowHeader] = useState(true);
  const lastScrollYRef = useRef(0);

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
        setShowGenPopover(false);
      } else if (diff < -8) {
        setShowHeader(true);
      }

      lastScrollYRef.current = currentScrollY;
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const switcherRef = useRef<HTMLDivElement | null>(null);
  const genPopoverRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("practice_studio_theme") as "light" | "dark" | null;
      const initial = saved || "dark";
      setTheme(initial);
      if (initial === "light") {
        document.documentElement.classList.add("light");
        document.documentElement.classList.remove("dark");
      } else {
        document.documentElement.classList.add("dark");
        document.documentElement.classList.remove("light");
      }
    } catch {}
  }, []);

  // Close popovers on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (switcherRef.current && !switcherRef.current.contains(e.target as Node)) {
        setShowDrillSwitcher(false);
      }
      if (genPopoverRef.current && !genPopoverRef.current.contains(e.target as Node)) {
        setShowGenPopover(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleToggleTheme = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    try {
      localStorage.setItem("practice_studio_theme", next);
    } catch {}
    if (next === "light") {
      document.documentElement.classList.add("light");
      document.documentElement.classList.remove("dark");
    } else {
      document.documentElement.classList.add("dark");
      document.documentElement.classList.remove("light");
    }
  };

  // Pre-Gen Config State (Tucked inside + Generate Popover)
  const [cfgUnit, setCfgUnit] = useState("MTH-T02-C01-U01");
  const [cfgCount, setCfgCount] = useState(5);
  const [cfgDifficulty, setCfgDifficulty] = useState("ALL");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  // Status message
  const [status, setStatus] = useState<{
    text: string;
    type: "pass" | "warn" | "fail";
  } | null>(null);

  const saveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Load a single drill document by ID
  const loadDrill = useCallback(async (id: string) => {
    setIsLoadingDrill(true);
    try {
      const res = await fetch(`/api/drill?id=${encodeURIComponent(id)}`);
      if (!res.ok) throw new Error("Could not load drill");
      const doc: DrillDocument = await res.json();
      const normalizedDoc: DrillDocument = {
        ...doc,
        problems: (doc.problems || []).map((p) => ({
          ...p,
          state: {
            userInput: p.state?.userInput || "",
            userCode: p.state?.userCode || p.starterCode || p.codeSnippet || "",
            score: p.state?.score ?? null,
            divergedStep: p.state?.divergedStep ?? null,
            mistakes: p.state?.mistakes || [],
            mistakeNote: p.state?.mistakeNote || "",
            skipped: p.state?.skipped || false,
            lastCheck: p.state?.lastCheck || null,
            lastTestReport: p.state?.lastTestReport || null,
          },
        })),
      };
      setCurrentDrill(normalizedDoc);
      setCurrentProblemIndex(0);
      setViewMode("quiz");
      setStatusOverride(null);

      if (doc.unitCode) {
        setCfgUnit(doc.unitCode);
      }
      if (doc.config) {
        setCfgCount(doc.config.questionCount || 5);
        setCfgDifficulty(doc.config.difficulty || "ALL");
      }
      setActiveSteps({});
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setStatus({ text: `Failed to load drill ${id}: ${errMsg}`, type: "fail" });
    } finally {
      setIsLoadingDrill(false);
    }
  }, []);

  // Load available drills list
  const loadDrillsList = useCallback(
    async (preferredId?: string) => {
      try {
        const res = await fetch("/api/drills");
        const data = await res.json();
        const list: DrillListItem[] = data.drills || [];
        setDrills(list);

        if (list.length > 0) {
          const targetId = preferredId || selectedDrillId || list[0].drillId;
          setSelectedDrillId(targetId);
          await loadDrill(targetId);
        } else {
          setIsLoadingDrill(false);
        }
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err);
        setStatus({ text: `Failed to fetch drills list: ${errMsg}`, type: "fail" });
        setIsLoadingDrill(false);
      }
    },
    [loadDrill, selectedDrillId]
  );

  useEffect(() => {
    loadDrillsList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Pre-Generation trigger
  const handleGenerateDrill = async () => {
    setIsGenerating(true);
    const engineLabel = cfgUnit.startsWith("PRG-") ? "Node.js" : "SymPy";
    setStatus({
      text: `Generating and verifying ${cfgCount} questions with ${engineLabel}...`,
      type: "warn",
    });

    try {
      const res = await fetch("/api/generate-drill", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          unitCode: cfgUnit,
          count: cfgCount,
          difficulty: cfgDifficulty,
        }),
      });

      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Generation failed");

      setStatus({
        text: `Generated & verified ${data.drillId} (${cfgCount} questions)!`,
        type: "pass",
      });
      setShowGenPopover(false);
      await loadDrillsList(data.drillId);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setStatus({ text: `Generation error: ${errMsg}`, type: "fail" });
    } finally {
      setIsGenerating(false);
    }
  };

  // Debounced Auto-Save to local JSON
  const triggerAutoSave = (updatedDoc: DrillDocument) => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(async () => {
      try {
        await fetch("/api/save-state", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updatedDoc),
        });
      } catch {
        // silent fail on transient autosave
      }
    }, 400);
  };

  // Check Answer Handler (SymPy API)
  const handleCheckAnswer = async (probId: string) => {
    if (!currentDrill) return;
    const p = currentDrill.problems.find((item) => item.id === probId);
    if (!p) return;

    const inputVal = p.state.userInput.trim();
    if (!inputVal) return;

    try {
      const res = await fetch("/api/check-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject: currentDrill.subject,
          answerSpec: p.answerSpec,
          input: inputVal,
        }),
      });

      const result: CheckResult = await res.json();

      const updatedProblems = currentDrill.problems.map((prob) => {
        if (prob.id !== probId) return prob;

        let autoScore = prob.state.score;
        if (result.verdict === "correct") autoScore = 1;
        else if (result.verdict === "equivalent_not_in_form" || result.verdict === "partial")
          autoScore = 0.5;
        else if (result.verdict === "incorrect") autoScore = 0;

        const newMistakes = new Set(prob.state.mistakes);
        const diagCodes = new Set((result.diagnostics || []).map((d) => d.code));
        (currentDrill.mistakeTags || []).forEach((tag) => {
          if (tag.autoFrom?.some((c) => diagCodes.has(c))) {
            newMistakes.add(tag.id);
          }
        });
        if (result.verdict === "incorrect") {
          let chosenOptionTrapTag: string | undefined;
          if (prob.answerSpec?.type === "choice" && Array.isArray(prob.answerSpec.options)) {
            const chosen = prob.answerSpec.options.find(
              (o) => String(o.id).trim() === String(inputVal).trim()
            );
            if (chosen && chosen.trapTag) {
              chosenOptionTrapTag = chosen.trapTag;
            }
          }

          if (chosenOptionTrapTag) {
            newMistakes.add(chosenOptionTrapTag);
          } else if (prob.commonTrapTag && newMistakes.size === 0) {
            newMistakes.add(prob.commonTrapTag);
          }
        }

        return {
          ...prob,
          state: {
            ...prob.state,
            score: autoScore,
            skipped: false,
            mistakes: Array.from(newMistakes),
            lastCheck: result,
          },
        };
      });

      const updatedDoc: DrillDocument = {
        ...currentDrill,
        problems: updatedProblems,
      };

      setCurrentDrill(updatedDoc);
      triggerAutoSave(updatedDoc);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setStatus({ text: `SymPy Check error: ${errMsg}`, type: "fail" });
    }
  };

  // Update Problem Input
  const handleInputChange = (probId: string, val: string) => {
    if (!currentDrill) return;
    const updated = {
      ...currentDrill,
      problems: currentDrill.problems.map((p) =>
        p.id === probId ? { ...p, state: { ...p.state, userInput: val } } : p
      ),
    };
    setCurrentDrill(updated);
    triggerAutoSave(updated);
  };

  // Update Custom Mistake Note (Flow 3.2)
  const handleMistakeNoteChange = (probId: string, note: string) => {
    if (!currentDrill) return;
    const updated = {
      ...currentDrill,
      problems: currentDrill.problems.map((p) =>
        p.id === probId ? { ...p, state: { ...p.state, mistakeNote: note } } : p
      ),
    };
    setCurrentDrill(updated);
    triggerAutoSave(updated);
  };

  // Toggle Step Highlight
  const handleToggleStepHighlight = (probId: string, stepIdx: number) => {
    setActiveSteps((prev) => ({
      ...prev,
      [probId]: prev[probId] === stepIdx ? null : stepIdx,
    }));
  };

  // Mark Diverged Step
  const handleMarkDivergedStep = (probId: string, stepIdx: number) => {
    if (!currentDrill) return;
    const updated = {
      ...currentDrill,
      problems: currentDrill.problems.map((p) => {
        if (p.id !== probId) return p;
        const isCurrent = p.state.divergedStep === stepIdx;
        const newDiverged = isCurrent ? null : stepIdx;
        const mistakes = new Set(p.state.mistakes);
        if (p.commonTrapTag && !isCurrent) mistakes.add(p.commonTrapTag);

        return {
          ...p,
          state: {
            ...p.state,
            divergedStep: newDiverged,
            score: p.state.score === null || p.state.score === 1 ? 0.5 : p.state.score,
            mistakes: Array.from(mistakes),
          },
        };
      }),
    };
    setCurrentDrill(updated);
    triggerAutoSave(updated);
  };

  // Set Manual Score
  const handleSetScore = (probId: string, score: number) => {
    if (!currentDrill) return;
    const updated = {
      ...currentDrill,
      problems: currentDrill.problems.map((p) =>
        p.id === probId ? { ...p, state: { ...p.state, score, skipped: false } } : p
      ),
    };
    setCurrentDrill(updated);
    triggerAutoSave(updated);
  };

  // Toggle Mistake Tag
  const handleToggleMistakeTag = (probId: string, tagId: string) => {
    if (!currentDrill) return;
    const updated = {
      ...currentDrill,
      problems: currentDrill.problems.map((p) => {
        if (p.id !== probId) return p;
        const list = p.state.mistakes || [];
        const next = list.includes(tagId)
          ? list.filter((t) => t !== tagId)
          : [...list, tagId];
        return {
          ...p,
          state: { ...p.state, mistakes: next },
        };
      }),
    };
    setCurrentDrill(updated);
    triggerAutoSave(updated);
  };

  // Skip Problem
  const handleSkipProblem = (probId: string) => {
    if (!currentDrill) return;
    const updated: DrillDocument = {
      ...currentDrill,
      problems: currentDrill.problems.map((p) => {
        if (p.id !== probId) return p;
        const autoTags = p.commonTrapTag ? [p.commonTrapTag] : [];
        return {
          ...p,
          state: {
            ...p.state,
            userInput: p.state.userInput || "(Skipped)",
            score: 0,
            skipped: true,
            mistakes: Array.from(new Set([...(p.state.mistakes || []), ...autoTags])),
            lastCheck: {
              verdict: "skipped",
              message:
                "Skipped (Concept Gap / Unsure) — Review step-by-step solution below to solidify mental model.",
              components: [],
              diagnostics: [],
            },
          },
        };
      }),
    };
    setCurrentDrill(updated);
    triggerAutoSave(updated);
  };

  // Reset Single Problem
  const handleResetProblem = (probId: string) => {
    if (!currentDrill) return;
    const updated = {
      ...currentDrill,
      problems: currentDrill.problems.map((p) => {
        if (p.id !== probId) return p;
        return {
          ...p,
          state: {
            userInput: "",
            userCode: p.starterCode || p.codeSnippet || "",
            score: null,
            divergedStep: null,
            mistakes: [],
            mistakeNote: "",
            skipped: false,
            lastCheck: null,
            lastTestReport: null,
          },
        };
      }),
    };
    setCurrentDrill(updated);
    triggerAutoSave(updated);
  };

  // Reset Entire Drill
  const handleResetAll = () => {
    if (!currentDrill) return;
    const ok = window.confirm(`Reset all questions in ${currentDrill.drillId} to start over?`);
    if (!ok) return;

    const updated: DrillDocument = {
      ...currentDrill,
      problems: currentDrill.problems.map((p) => ({
        ...p,
        state: {
          userInput: "",
          userCode: p.starterCode || p.codeSnippet || "",
          score: null,
          divergedStep: null,
          mistakes: [],
          mistakeNote: "",
          skipped: false,
          lastCheck: null,
          lastTestReport: null,
        },
      })),
      sessionSummary: {
        ...currentDrill.sessionSummary,
        score: 0,
        accuracyPct: 0,
        practiceStatus: "Ready",
        mistakeCategories: [],
        divergedStepsSummary: "",
        attemptDate: null,
      },
    };
    setCurrentDrill(updated);
    setCurrentProblemIndex(0);
    setViewMode("quiz");
    triggerAutoSave(updated);
    setStatus({
      text: `Reset ${currentDrill.drillId} to initial state.`,
      type: "pass",
    });
  };

  // Navigation Handlers
  const handlePrevQuestion = useCallback(() => {
    setCurrentProblemIndex((prev) => (prev > 0 ? prev - 1 : prev));
  }, []);

  const handleNextQuestion = useCallback(() => {
    setCurrentProblemIndex((prev) => {
      const maxIdx = (currentDrill?.problems.length ?? 1) - 1;
      return prev < maxIdx ? prev + 1 : prev;
    });
  }, [currentDrill]);

  const handleSelectQuestion = (idx: number) => {
    setCurrentProblemIndex(idx);
    if (viewMode !== "quiz") {
      setViewMode("quiz");
    }
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT")) {
        return;
      }
      if (viewMode !== "quiz") return;
      if (e.key === "ArrowLeft") {
        handlePrevQuestion();
      } else if (e.key === "ArrowRight") {
        handleNextQuestion();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [viewMode, handlePrevQuestion, handleNextQuestion]);

  // Compute live score & summary preview
  const liveScore = currentDrill
    ? currentDrill.problems.reduce((acc, p) => acc + (p.state?.score || 0), 0)
    : 0;
  const maxScore = currentDrill?.problems.length || 0;
  const accuracyPct = maxScore > 0 ? Math.round((liveScore / maxScore) * 1000) / 10 : 0;
  const skippedCount = currentDrill
    ? currentDrill.problems.filter((p) => p.state?.skipped).length
    : 0;

  const computedPracticeStatus: "Graded" | "Needs Retry" =
    statusOverride || (maxScore > 0 && liveScore / maxScore >= 0.8 ? "Graded" : "Needs Retry");

  // Filtered Drills for Smart Drill Switcher
  const filteredDrills = useMemo(() => {
    return drills.filter((d) => {
      if (drillFilter === "UNFINISHED" && d.practiceStatus === "Graded") return false;
      if (drillFilter === "GRADED" && d.practiceStatus !== "Graded") return false;
      if (drillFilter === "MATH" && d.subject !== "MATH") return false;
      if (drillFilter === "PRG" && d.subject !== "PRG") return false;

      if (!drillSearch.trim()) return true;
      const q = drillSearch.toLowerCase();
      return (
        d.drillId.toLowerCase().includes(q) ||
        d.unitCode.toLowerCase().includes(q) ||
        (d.unitTitle || "").toLowerCase().includes(q)
      );
    });
  }, [drills, drillFilter, drillSearch]);

  // Build summary payload & Sync to Notion (called from Pre-Sync Review confirmation)
  const handleConfirmSyncToNotion = async () => {
    if (!currentDrill) return;
    setIsSyncing(true);
    setStatus({
      text: `Syncing ${currentDrill.drillId} (${liveScore}/${maxScore}) to Notion...`,
      type: "warn",
    });

    const tagMap = new Map((currentDrill.mistakeTags || []).map((t) => [t.id, t.name]));
    const mistakeNames = new Set<string>();
    const divergedList: string[] = [];
    const skippedProblems: string[] = [];

    currentDrill.problems.forEach((p) => {
      const parts: string[] = [];
      if (p.state?.skipped) {
        skippedProblems.push(`${p.id} (${p.context || p.category})`);
        parts.push("SKIPPED - Concept Gap");
      }
      (p.state?.mistakes || []).forEach((tid) => {
        const rawName = tagMap.get(tid) || tid;
        mistakeNames.add(rawName.replace(/,/g, " /").trim());
      });
      if (typeof p.state?.divergedStep === "number") {
        const st = p.steps[p.state.divergedStep];
        parts.push(`Step ${p.state.divergedStep + 1}: ${st ? st.explain : "Diverged"}`);
      } else if (
        p.state?.score !== null &&
        p.state?.score !== undefined &&
        p.state.score < 1 &&
        (p.state?.mistakes || []).length > 0 &&
        !p.state?.skipped
      ) {
        parts.push((p.state?.mistakes || []).map((t) => tagMap.get(t) || t).join(", "));
      }
      if (p.state?.mistakeNote && p.state.mistakeNote.trim()) {
        parts.push(`Note: ${p.state.mistakeNote.trim()}`);
      }
      if (parts.length > 0) {
        divergedList.push(`${p.id} (${parts.join(" · ")})`);
      }
    });

    const fullDocToSync: DrillDocument = {
      ...currentDrill,
      sessionSummary: {
        practiceStatus: computedPracticeStatus,
        score: liveScore,
        maxScore,
        accuracyPct,
        skippedCount: skippedProblems.length,
        skippedProblems,
        mistakeCategories: Array.from(mistakeNames),
        divergedStepsSummary:
          divergedList.length > 0 ? divergedList.join(" | ") : "No diverged steps logged.",
        attemptDate: new Date().toISOString().slice(0, 10),
      },
    };

    try {
      const res = await fetch("/api/sync-notion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(fullDocToSync),
      });

      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Notion Sync failed");

      setCurrentDrill(fullDocToSync);
      setStatus({
        text: `Synced ${currentDrill.drillId} (${liveScore}/${maxScore} · ${accuracyPct}%) to Notion Database & ${currentDrill.unitCode} Mistake Log!`,
        type: "pass",
      });
      await loadDrillsList(currentDrill.drillId);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setStatus({ text: `Notion Sync error: ${errMsg}`, type: "fail" });
    } finally {
      setIsSyncing(false);
    }
  };

  const isLastQuestion =
    currentDrill && currentProblemIndex === currentDrill.problems.length - 1;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0d1017] text-slate-900 dark:text-slate-100 p-3 md:p-5 lg:p-6 transition-colors">
      <div className="max-w-5xl mx-auto">
        {/* ===================================================================== */}
        {/* SINGLE UNIFIED STICKY WORKSPACE BAR (Strictly 2 Rows, Auto-hides)     */}
        {/* ===================================================================== */}
        <header
          className={`sticky top-2 z-50 bg-white/95 dark:bg-[#151924]/95 backdrop-blur-md border border-slate-200 dark:border-[#2c354d] rounded-2xl p-3.5 mb-5 shadow-md transition-all duration-300 ease-in-out ${
            showHeader
              ? "translate-y-0 opacity-100"
              : "-translate-y-[130%] opacity-0 pointer-events-none"
          }`}
        >
          {/* Row 1: Smart Drill Switcher + Notion Unit + [+ Generate] | Score + Reset + Theme */}
          <div className="flex items-center justify-between gap-3">
            {/* Left Zone: Smart Drill Switcher & Generate Popover */}
            <div className="flex items-center gap-2.5 min-w-0">
              {/* Smart Drill Switcher */}
              <div className="relative" ref={switcherRef}>
                <button
                  type="button"
                  onClick={() => setShowDrillSwitcher(!showDrillSwitcher)}
                  className="inline-flex items-center gap-3 min-h-[48px] py-2 px-3.5 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-slate-200/70 dark:hover:bg-[#252e42] border border-slate-200 dark:border-[#2c354d] text-left transition-colors"
                >
                  {currentDrill?.subject === "PRG" ? (
                    <Terminal className="w-4 h-4 text-sky-600 dark:text-sky-400 shrink-0" />
                  ) : (
                    <Sigma className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
                  )}
                  <div className="min-w-0 space-y-0.5">
                    <div className="text-xs md:text-sm font-bold leading-snug text-slate-900 dark:text-white truncate max-w-[240px] sm:max-w-[360px] md:max-w-[440px]">
                      {currentDrill
                        ? `${currentDrill.unitTitle} (${currentDrill.unitCode})`
                        : "Select Practice Drill"}
                    </div>
                    {currentDrill && (
                      <div className="text-[11px] font-mono leading-tight text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                        <span>{currentDrill.drillId}</span>
                        <span>·</span>
                        <span>{currentDrill.problems.length} Qs</span>
                      </div>
                    )}
                  </div>
                  <ChevronDown className="w-4 h-4 text-slate-500 dark:text-slate-400 shrink-0 ml-0.5" />
                </button>

                {/* Searchable & Filterable Drill Popover */}
                {showDrillSwitcher && (
                  <div className="absolute left-0 mt-2 w-[380px] sm:w-[480px] bg-white dark:bg-[#161c2a] border border-slate-200 dark:border-[#2c354d] rounded-2xl shadow-2xl p-3.5 z-50">
                    {/* Search Input */}
                    <div className="flex items-center gap-2 bg-slate-100 dark:bg-[#10141f] border border-slate-200 dark:border-[#2c354d] rounded-xl px-3 py-2 mb-3">
                      <Search className="w-4 h-4 text-slate-400 shrink-0" />
                      <input
                        type="text"
                        value={drillSearch}
                        onChange={(e) => setDrillSearch(e.target.value)}
                        placeholder="Search by unit title, subject code (MTH, PRG), or drill ID..."
                        className="w-full bg-transparent text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none"
                        autoFocus
                      />
                      {drillSearch && (
                        <button
                          type="button"
                          onClick={() => setDrillSearch("")}
                          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>

                    {/* Filter Pills */}
                    <div className="flex flex-wrap items-center gap-1.5 mb-3 pb-2.5 border-b border-slate-200 dark:border-[#252f45] text-xs">
                      {[
                        { id: "ALL", label: "All" },
                        { id: "UNFINISHED", label: "Unfinished" },
                        { id: "GRADED", label: "Synced" },
                        { id: "MATH", label: "MATH" },
                        { id: "PRG", label: "PRG" },
                      ].map((tab) => (
                        <button
                          key={tab.id}
                          type="button"
                          onClick={() =>
                            setDrillFilter(
                              tab.id as "ALL" | "UNFINISHED" | "GRADED" | "MATH" | "PRG"
                            )
                          }
                          className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                            drillFilter === tab.id
                              ? "bg-indigo-600 text-white"
                              : "bg-slate-100 dark:bg-[#1d2436] text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-[#263047]"
                          }`}
                        >
                          {tab.label}
                        </button>
                      ))}
                    </div>

                    {/* Drills List */}
                    <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
                      {filteredDrills.length === 0 ? (
                        <div className="py-6 text-center text-xs text-slate-500 dark:text-slate-400">
                          No drills match the selected filter.
                        </div>
                      ) : (
                        filteredDrills.map((d) => {
                          const isSelected = d.drillId === selectedDrillId;
                          const isGraded = d.practiceStatus === "Graded";
                          const isInProgress = d.practiceStatus === "In Progress";

                          return (
                            <button
                              key={d.drillId}
                              type="button"
                              onClick={() => {
                                setSelectedDrillId(d.drillId);
                                loadDrill(d.drillId);
                                setShowDrillSwitcher(false);
                              }}
                              className={`w-full text-left p-3 rounded-xl border transition-all flex items-start justify-between gap-3 ${
                                isSelected
                                  ? "bg-indigo-50 dark:bg-indigo-600/20 border-indigo-500"
                                  : "bg-slate-50/70 dark:bg-[#1b2233] hover:bg-slate-100 dark:hover:bg-[#232c42] border-slate-200/80 dark:border-[#2a344d]"
                              }`}
                            >
                              <div className="min-w-0 flex-1 space-y-1">
                                <div className="flex items-center gap-1.5">
                                  <span
                                    className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                                      d.subject === "PRG"
                                        ? "bg-sky-100 dark:bg-sky-500/20 text-sky-700 dark:text-sky-300"
                                        : "bg-indigo-100 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300"
                                    }`}
                                  >
                                    {d.subject || "MATH"}
                                  </span>
                                  <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                                    {d.unitTitle}
                                  </span>
                                </div>
                                <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                                  {d.drillId} · {d.unitCode} · {d.questionCount} Qs
                                </div>
                              </div>

                              <div className="flex flex-col items-end shrink-0 gap-1">
                                <span
                                  className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                                    isGraded
                                      ? "bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-500/30"
                                      : isInProgress
                                      ? "bg-amber-50 dark:bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-500/30"
                                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700"
                                  }`}
                                >
                                  {isGraded ? (
                                    <CheckCircle2 className="w-3 h-3" />
                                  ) : (
                                    <Clock className="w-3 h-3" />
                                  )}
                                  <span>{d.practiceStatus || "Ready"}</span>
                                </span>
                                <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                                  Score: {d.score ?? 0}/{d.maxScore ?? d.questionCount}
                                </span>
                              </div>
                            </button>
                          );
                        })
                      )}
                    </div>
                  </div>
                )}
              </div>

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

              {/* Tucked Pre-Generation Config Popover (+ Generate) */}
              <div className="relative shrink-0" ref={genPopoverRef}>
                <button
                  type="button"
                  onClick={() => setShowGenPopover(!showGenPopover)}
                  className="inline-flex items-center gap-1.5 h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-indigo-50 dark:hover:bg-indigo-600/20 text-slate-700 dark:text-slate-200 hover:text-indigo-700 dark:hover:text-indigo-300 border border-slate-200 dark:border-[#2c354d] text-xs font-semibold transition-colors"
                  title="Generate a new verified drill set"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Generate</span>
                </button>

                {showGenPopover && (
                  <div className="absolute left-0 mt-2 w-80 bg-white dark:bg-[#161c2a] border border-slate-200 dark:border-[#2c354d] rounded-2xl shadow-2xl p-4 z-50 space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-200 dark:border-[#252f45] pb-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                        Generate New Drill Set (.json)
                      </span>
                      <button
                        type="button"
                        onClick={() => setShowGenPopover(false)}
                        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="space-y-2.5 text-xs">
                      <div>
                        <label className="block text-slate-600 dark:text-slate-400 mb-1 font-medium">
                          Target Unit
                        </label>
                        <select
                          value={cfgUnit}
                          onChange={(e) => setCfgUnit(e.target.value)}
                          className="w-full bg-slate-50 dark:bg-[#1d2333] border border-slate-200 dark:border-[#2c354d] rounded-lg px-2.5 py-2 text-xs text-slate-900 dark:text-slate-200"
                        >
                          <optgroup label="JavaScript & TypeScript (PRG-T01)">
                            <option value="PRG-T01-C01">
                              PRG-T01-C01 · JS Deep Dive (Mental Model)
                            </option>
                            <option value="PRG-T01-C03">
                              PRG-T01-C03 · Utility Toolkit (VS Code Katas)
                            </option>
                          </optgroup>
                          <optgroup label="Prealgebra (MTH-T01)">
                            <option value="MTH-T01-C01">MTH-T01-C01 · Whole Numbers</option>
                            <option value="MTH-T01-C02">MTH-T01-C02 · The Language of Algebra</option>
                            <option value="MTH-T01-C03">MTH-T01-C03 · Integers</option>
                            <option value="MTH-T01-C04">MTH-T01-C04 · Fractions</option>
                            <option value="MTH-T01-C05">MTH-T01-C05 · Decimals</option>
                            <option value="MTH-T01-C06">MTH-T01-C06 · Percents</option>
                            <option value="MTH-T01-C07">MTH-T01-C07 · Proportional &amp; Ratio</option>
                            <option value="MTH-T01-C08">MTH-T01-C08 · Exponents</option>
                            <option value="MTH-T01-C09">MTH-T01-C09 · Roots</option>
                            <option value="MTH-T01-C10">MTH-T01-C10 · Properties of Real Numbers</option>
                            <option value="MTH-T01-C11">MTH-T01-C11 · Solving Linear Equations</option>
                            <option value="MTH-T01-C12">MTH-T01-C12 · Math Models &amp; Geometry</option>
                            <option value="MTH-T01-C13">MTH-T01-C13 · Polynomials</option>
                            <option value="MTH-T01-C14">MTH-T01-C14 · Graphs</option>
                          </optgroup>
                          <optgroup label="Algebra &amp; Trigonometry (MTH-T02)">
                            <option value="MTH-T02-C01-U01">
                              MTH-T02-C01-U01 · Complex Numbers
                            </option>
                          </optgroup>
                        </select>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-slate-600 dark:text-slate-400 mb-1 font-medium">
                            Question Count
                          </label>
                          <select
                            value={cfgCount}
                            onChange={(e) => setCfgCount(Number(e.target.value))}
                            className="w-full bg-slate-50 dark:bg-[#1d2333] border border-slate-200 dark:border-[#2c354d] rounded-lg px-2.5 py-2 text-xs text-slate-900 dark:text-slate-200"
                          >
                            <option value={5}>5 Questions</option>
                            <option value={10}>10 Questions</option>
                            <option value={15}>15 Questions</option>
                            <option value={20}>20 Questions</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-slate-600 dark:text-slate-400 mb-1 font-medium">
                            Difficulty
                          </label>
                          <select
                            value={cfgDifficulty}
                            onChange={(e) => setCfgDifficulty(e.target.value)}
                            className="w-full bg-slate-50 dark:bg-[#1d2333] border border-slate-200 dark:border-[#2c354d] rounded-lg px-2.5 py-2 text-xs text-slate-900 dark:text-slate-200"
                          >
                            <option value="ALL">Mixed (L1–L4)</option>
                            <option value="1">Level 1</option>
                            <option value="2">Level 2</option>
                            <option value="3">Level 3</option>
                            <option value="4">Level 4</option>
                          </select>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={handleGenerateDrill}
                        disabled={isGenerating}
                        className="w-full inline-flex items-center justify-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold h-9 rounded-xl transition-colors shadow-sm"
                      >
                        {isGenerating ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Plus className="w-3.5 h-3.5" />
                        )}
                        <span>{isGenerating ? "Generating..." : "Generate Verified Set"}</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right Zone: Live Score + Reset + Theme (Strictly single line, no redundant Review & Sync button) */}
            <div className="flex items-center gap-2 shrink-0">
              <span className="inline-flex items-center h-9 text-xs font-bold px-3 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30 whitespace-nowrap">
                Score: {liveScore} / {maxScore} ({accuracyPct}%)
              </span>

              <button
                type="button"
                onClick={handleResetAll}
                title="Reset all questions in this drill"
                className="inline-flex items-center justify-center w-9 h-9 bg-slate-100 dark:bg-[#1d2333] hover:bg-rose-50 dark:hover:bg-rose-500/20 text-slate-600 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-300 rounded-xl border border-slate-200 dark:border-[#2c354d] transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={handleToggleTheme}
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
          {currentDrill && currentDrill.problems.length > 0 && (
            <div className="mt-2.5">
              <QuizPaginationBar
                totalQuestions={currentDrill.problems.length}
                currentIndex={currentProblemIndex}
                problems={currentDrill.problems}
                viewMode={viewMode}
                onSelectQuestion={handleSelectQuestion}
                onPrev={handlePrevQuestion}
                onNext={handleNextQuestion}
                onToggleViewMode={(mode) => setViewMode(mode)}
              />
            </div>
          )}
        </header>

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
              onClick={() => setStatus(null)}
              className="inline-flex items-center justify-center w-7 h-7 rounded-lg text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* ===================================================================== */}
        {/* MAIN WORKSPACE AREA: LOADING / QUIZ FOCUS / PRE-SYNC REVIEW           */}
        {/* ===================================================================== */}
        <main>
          {isLoadingDrill ? (
            <div className="bg-white dark:bg-[#151924] border border-slate-200 dark:border-[#2c354d] rounded-2xl p-8 space-y-4 animate-pulse">
              <div className="h-6 w-1/3 bg-slate-200 dark:bg-slate-800 rounded-lg" />
              <div className="h-4 w-2/3 bg-slate-200 dark:bg-slate-800 rounded-lg" />
              <div className="h-28 w-full bg-slate-100 dark:bg-[#10141f] rounded-xl" />
              <div className="h-10 w-1/2 bg-slate-200 dark:bg-slate-800 rounded-xl" />
            </div>
          ) : !currentDrill ? (
            <div className="bg-white dark:bg-[#151924] border border-slate-200 dark:border-[#2c354d] rounded-2xl p-10 text-center space-y-3">
              <p className="text-base font-semibold text-slate-800 dark:text-slate-200">
                No Practice Drill Selected
              </p>
              <button
                type="button"
                onClick={() => setShowGenPopover(true)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold"
              >
                <Plus className="w-4 h-4" />
                <span>Generate New Drill Set</span>
              </button>
            </div>
          ) : viewMode === "quiz" && currentDrill.problems[currentProblemIndex] ? (
            /* ================================================================= */
            /* MODE 1: SINGLE QUESTION FOCUS MODE                                */
            /* ================================================================= */
            <div>
              {(() => {
                const prob = currentDrill.problems[currentProblemIndex];
                const idx = currentProblemIndex;
                return (
                  <div key={prob.id}>
                    <ProblemCard
                      problem={prob}
                      index={idx}
                      subject={currentDrill.subject}
                      mistakeTags={currentDrill.mistakeTags || []}
                      activeStep={activeSteps[prob.id] ?? null}
                      onInputChange={(val) => handleInputChange(prob.id, val)}
                      onCheckAnswer={() => handleCheckAnswer(prob.id)}
                      onSkip={() => handleSkipProblem(prob.id)}
                      onToggleStepHighlight={(stepIdx) =>
                        handleToggleStepHighlight(prob.id, stepIdx)
                      }
                      onMarkDivergedStep={(stepIdx) => handleMarkDivergedStep(prob.id, stepIdx)}
                      onSetScore={(score) => handleSetScore(prob.id, score)}
                      onToggleMistakeTag={(tagId) => handleToggleMistakeTag(prob.id, tagId)}
                      onMistakeNoteChange={(note) => handleMistakeNoteChange(prob.id, note)}
                      onResetProblem={() => handleResetProblem(prob.id)}
                    />

                    {/* Bottom Question Navigation Footer */}
                    <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-white dark:bg-[#141926] border border-slate-200 dark:border-[#2b3752] rounded-2xl shadow-sm mt-4">
                      <button
                        type="button"
                        onClick={handlePrevQuestion}
                        disabled={currentProblemIndex === 0}
                        className="inline-flex items-center gap-1.5 h-10 px-4 rounded-xl text-sm font-semibold bg-slate-100 dark:bg-[#1c2438] hover:bg-slate-200 dark:hover:bg-[#25304a] disabled:opacity-40 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-[#2c3852] transition-colors"
                      >
                        <ChevronLeft className="w-4 h-4" />
                        <span>Previous Question</span>
                      </button>

                      <div className="text-xs font-mono text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                        <span>Question</span>
                        <strong className="text-slate-900 dark:text-white bg-slate-100 dark:bg-[#1c2438] px-2.5 py-1 rounded-lg border border-slate-200 dark:border-[#2c3852]">
                          {currentProblemIndex + 1}
                        </strong>
                        <span>of</span>
                        <strong className="text-slate-700 dark:text-slate-300">
                          {currentDrill.problems.length}
                        </strong>
                      </div>

                      {isLastQuestion ? (
                        <button
                          type="button"
                          onClick={() => setViewMode("review")}
                          className="inline-flex items-center gap-2 h-10 px-5 rounded-xl text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors shadow-sm"
                        >
                          <ClipboardCheck className="w-4 h-4" />
                          <span>Review &amp; Sync to Notion</span>
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={handleNextQuestion}
                          className="inline-flex items-center gap-1.5 h-10 px-5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors shadow-sm"
                        >
                          <span>Next Question</span>
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })()}
            </div>
          ) : (
            /* ================================================================= */
            /* MODE 2: PRE-SYNC REVIEW & EDIT VIEW (Flow 3.3)                    */
            /* ================================================================= */
            <section className="bg-white dark:bg-[#151924] border border-slate-200 dark:border-[#2c354d] rounded-2xl p-5 md:p-6 shadow-sm space-y-5">
              {/* Review Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200 dark:border-[#2c354d]">
                <div>
                  <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
                    <ClipboardCheck className="w-4 h-4" />
                    <span>Pre-Sync Verification &amp; Mistake Log Review</span>
                  </div>
                  <h1 className="text-lg md:text-xl font-bold text-slate-900 dark:text-white">
                    Review &amp; Edit Session Before Notion Sync ({currentDrill.drillId})
                  </h1>
                </div>

                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    onClick={() => setViewMode("quiz")}
                    className="inline-flex items-center gap-1.5 h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-slate-200 dark:hover:bg-[#25304a] text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-[#2c354d] text-xs md:text-sm font-semibold transition-colors"
                  >
                    <ArrowLeft className="w-4 h-4" />
                    <span>Back to Questions</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleConfirmSyncToNotion}
                    disabled={isSyncing}
                    className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs md:text-sm font-bold transition-colors shadow-sm"
                  >
                    {isSyncing ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Syncing to Notion...</span>
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        <span>Confirm &amp; Sync to Notion</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Session Summary Overview Box */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 p-4 bg-slate-50 dark:bg-[#10141f] border border-slate-200 dark:border-[#2c354d] rounded-xl text-xs">
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block mb-1">
                    Unit &amp; Drill ID
                  </span>
                  <strong className="text-sm text-slate-900 dark:text-white block">
                    {currentDrill.unitTitle}
                  </strong>
                  <span className="font-mono text-slate-500 dark:text-slate-400">
                    {currentDrill.drillId} · {currentDrill.unitCode}
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 dark:text-slate-400 block mb-1">
                    Total Score &amp; Accuracy
                  </span>
                  <strong className="text-base text-emerald-600 dark:text-emerald-400 font-mono">
                    {liveScore} / {maxScore} ({accuracyPct}%)
                  </strong>
                  <span className="block text-slate-500 dark:text-slate-400">
                    Skipped: {skippedCount} questions
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 dark:text-slate-400 block mb-1">
                    Practice Status (Editable)
                  </span>
                  <div className="flex items-center gap-1.5 mt-1">
                    {(["Graded", "Needs Retry"] as const).map((st) => (
                      <button
                        key={st}
                        type="button"
                        onClick={() => setStatusOverride(st)}
                        className={`h-8 px-2.5 rounded-lg text-xs font-semibold border transition-colors ${
                          computedPracticeStatus === st
                            ? st === "Graded"
                              ? "bg-emerald-600 text-white border-emerald-600"
                              : "bg-amber-600 text-white border-amber-600"
                            : "bg-white dark:bg-[#1d2333] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-[#2c354d]"
                        }`}
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="text-slate-500 dark:text-slate-400 block mb-1">
                    Target Notion Destination
                  </span>
                  <span className="text-slate-800 dark:text-slate-200 font-medium block">
                    1. Learning Practice &amp; Drills DB
                  </span>
                  <span className="text-slate-600 dark:text-slate-400 block">
                    2. Unit Page ({currentDrill.unitCode}) Log
                  </span>
                </div>
              </div>

              {/* Editable Question-by-Question Review Table/Cards */}
              <div className="space-y-3">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                  Question-by-Question Breakdown (Click to adjust scores, Mistake Tags, or custom notes)
                </div>

                {currentDrill.problems.map((prob, idx) => {
                  const pScore = prob.state.score;
                  const isSkipped = Boolean(prob.state.skipped);

                  // Status-based soft background & border tint for rapid visual scanning
                  let statusCardCls =
                    "bg-slate-50/80 dark:bg-[#10141f] border-slate-200 dark:border-[#2c354d]";
                  if (!isSkipped && pScore === 1) {
                    statusCardCls =
                      "bg-emerald-50/75 dark:bg-emerald-950/25 border-emerald-200 dark:border-emerald-500/35";
                  } else if (!isSkipped && pScore === 0.5) {
                    statusCardCls =
                      "bg-amber-50/75 dark:bg-amber-950/25 border-amber-200 dark:border-amber-500/35";
                  } else if (!isSkipped && pScore === 0) {
                    statusCardCls =
                      "bg-rose-50/75 dark:bg-rose-950/25 border-rose-200 dark:border-rose-500/35";
                  }

                  return (
                    <div
                      key={prob.id}
                      className={`p-4 border rounded-xl space-y-3 transition-colors ${statusCardCls}`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div className="flex-1 min-w-[240px]">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <button
                              type="button"
                              onClick={() => {
                                setCurrentProblemIndex(idx);
                                setViewMode("quiz");
                              }}
                              className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline font-mono"
                            >
                              <span>
                                Question {idx + 1} ({prob.id})
                              </span>
                              <ArrowUpRight className="w-3.5 h-3.5" />
                            </button>
                            {isSkipped && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 font-medium">
                                Skipped
                              </span>
                            )}
                            {typeof prob.state.divergedStep === "number" && (
                              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300 font-medium">
                                <Flag className="w-3 h-3" />
                                Diverged at Step {prob.state.divergedStep + 1}
                              </span>
                            )}
                          </div>
                          <div className="text-xs md:text-sm text-slate-700 dark:text-slate-300 line-clamp-2">
                            <FormattedText text={prob.prompt} />
                          </div>
                          <div className="mt-1.5 text-xs font-mono text-slate-500 dark:text-slate-400">
                            Your Answer:{" "}
                            <strong className="text-slate-800 dark:text-slate-200">
                              {prob.state.userInput ||
                                (prob.state.lastTestReport
                                  ? `${prob.state.lastTestReport.passedCount}/${prob.state.lastTestReport.totalCount} Tests Passed`
                                  : "(Unanswered)")}
                            </strong>{" "}
                            · Verified Answer:{" "}
                            <strong className="text-emerald-700 dark:text-emerald-400">
                              {prob.answerPlain || prob.answerDisplay}
                            </strong>
                          </div>
                        </div>

                        {/* Inline Score Selector */}
                        <div className="flex items-center gap-1.5 shrink-0">
                          <span className="text-xs text-slate-500 dark:text-slate-400 mr-1">
                            Score:
                          </span>
                          {[
                            {
                              val: 1,
                              label: "1.0",
                              cls: "bg-emerald-600 text-white border-emerald-600",
                            },
                            {
                              val: 0.5,
                              label: "0.5",
                              cls: "bg-amber-600 text-white border-amber-600",
                            },
                            {
                              val: 0,
                              label: "0",
                              cls: "bg-rose-600 text-white border-rose-600",
                            },
                          ].map((btn) => (
                            <button
                              key={btn.val}
                              type="button"
                              onClick={() => handleSetScore(prob.id, btn.val)}
                              className={`h-8 px-2.5 rounded-lg text-xs font-semibold border transition-colors ${
                                pScore === btn.val
                                  ? btn.cls
                                  : "bg-white/90 dark:bg-[#1d2333] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-[#2c354d]"
                              }`}
                            >
                              {btn.label}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Inline Mistake Tags & Custom Mistake Note */}
                      <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-200/70 dark:border-[#1f283d]">
                        <span className="text-xs text-slate-500 dark:text-slate-400 mr-1">
                          Mistake Tags:
                        </span>
                        {(currentDrill.mistakeTags || []).map((t) => {
                          const hasTag = prob.state.mistakes.includes(t.id);
                          return (
                            <button
                              key={t.id}
                              type="button"
                              onClick={() => handleToggleMistakeTag(prob.id, t.id)}
                              className={`min-h-[28px] py-1 px-3 rounded-full text-xs font-medium border transition-colors inline-flex items-center ${
                                hasTag
                                  ? "bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-500/50 font-semibold"
                                  : "bg-white/90 dark:bg-[#1d2333] text-slate-600 dark:text-slate-400 border-slate-200 dark:border-[#2c354d]"
                              }`}
                            >
                              <FormattedText text={t.label} />
                            </button>
                          );
                        })}
                      </div>

                      <div className="flex items-center gap-2 bg-white/90 dark:bg-[#151924] border border-slate-200 dark:border-[#2c354d] rounded-lg px-3 py-1.5">
                        <PenLine className="w-3.5 h-3.5 text-rose-500 dark:text-rose-400 shrink-0" />
                        <input
                          type="text"
                          value={prob.state.mistakeNote || ""}
                          onChange={(e) => handleMistakeNoteChange(prob.id, e.target.value)}
                          placeholder={`Add custom mistake note for Question ${idx + 1} (editable before sync)...`}
                          className="w-full bg-transparent text-xs text-slate-800 dark:text-slate-200 placeholder:text-slate-400 focus:outline-none"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Bottom Confirm Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-200 dark:border-[#2c354d]">
                <button
                  type="button"
                  onClick={() => setViewMode("quiz")}
                  className="inline-flex items-center gap-1.5 h-10 px-4 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-slate-200 dark:hover:bg-[#25304a] text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-[#2c354d] text-sm font-semibold transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to Practice</span>
                </button>

                <button
                  type="button"
                  onClick={handleConfirmSyncToNotion}
                  disabled={isSyncing}
                  className="inline-flex items-center gap-2 h-10 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-bold transition-colors shadow-sm"
                >
                  {isSyncing ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Syncing to Notion...</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      <span>
                        Confirm &amp; Sync to Notion ({liveScore}/{maxScore} · {accuracyPct}%)
                      </span>
                    </>
                  )}
                </button>
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
