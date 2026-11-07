"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { Plus, RefreshCw, Send, CheckCircle2, AlertCircle, RotateCcw, ChevronLeft, ChevronRight } from "lucide-react";
import {
  DrillDocument,
  DrillListItem,
  CheckResult,
} from "@/types/drill";
import { ProblemCard } from "@/components/ProblemCard";
import { QuizPaginationBar } from "@/components/QuizPaginationBar";

export default function PracticeStudioPage() {
  const [drills, setDrills] = useState<DrillListItem[]>([]);
  const [currentDrill, setCurrentDrill] = useState<DrillDocument | null>(null);
  const [selectedDrillId, setSelectedDrillId] = useState<string>("");
  const [activeSteps, setActiveSteps] = useState<{ [probId: string]: number | null }>({});
  const [currentProblemIndex, setCurrentProblemIndex] = useState<number>(0);
  const [viewMode, setViewMode] = useState<"quiz" | "all">("quiz");

  // Pre-Gen Config State
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

  // Load available drills list
  const loadDrillsList = useCallback(async (preferredId?: string) => {
    try {
      const res = await fetch("/api/drills");
      const data = await res.json();
      const list: DrillListItem[] = data.drills || [];
      setDrills(list);

      if (list.length > 0) {
        const targetId = preferredId || list[0].drillId;
        setSelectedDrillId(targetId);
        loadDrill(targetId);
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setStatus({ text: `Failed to fetch drills list: ${errMsg}`, type: "fail" });
    }
  }, []);

  // Load a single drill document by ID
  const loadDrill = async (id: string) => {
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
            lastCheck: p.state?.lastCheck || null,
            lastTestReport: p.state?.lastTestReport || null,
          },
        })),
      };
      setCurrentDrill(normalizedDoc);
      setCurrentProblemIndex(0);

      // sync top config
      if (doc.config) {
        setCfgCount(doc.config.questionCount || 5);
        setCfgDifficulty(doc.config.difficulty || "ALL");
      }
      setActiveSteps({});
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setStatus({ text: `Failed to load drill ${id}: ${errMsg}`, type: "fail" });
    }
  };

  useEffect(() => {
    loadDrillsList();
  }, [loadDrillsList]);

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
        text: `Generated & verified ${data.drillId} with ${cfgCount} questions!`,
        type: "pass",
      });
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

      // update problem state
      const updatedProblems = currentDrill.problems.map((prob) => {
        if (prob.id !== probId) return prob;

        let autoScore = prob.state.score;
        if (result.verdict === "correct") autoScore = 1;
        else if (result.verdict === "equivalent_not_in_form" || result.verdict === "partial") autoScore = 0.5;
        else if (result.verdict === "incorrect") autoScore = 0;

        const newMistakes = new Set(prob.state.mistakes);
        const diagCodes = new Set((result.diagnostics || []).map((d) => d.code));
        (currentDrill.mistakeTags || []).forEach((tag) => {
          if (tag.autoFrom?.some((c) => diagCodes.has(c))) {
            newMistakes.add(tag.id);
          }
        });
        if (result.verdict === "incorrect" && prob.commonTrapTag && newMistakes.size === 0) {
          newMistakes.add(prob.commonTrapTag);
        }

        return {
          ...prob,
          state: {
            ...prob.state,
            score: autoScore,
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
        p.id === probId ? { ...p, state: { ...p.state, score } } : p
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

  // Skip Problem (User does not know concept yet - avoid blind guessing)
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
              verdict: "skipped" as any,
              message: "Skipped (Concept Gap / Unsure) — Review step-by-step solution below to solidify mental model.",
              components: [],
              diagnostics: [],
            },
          },
        };
      }),
    };
    setCurrentDrill(updated);
    triggerAutoSave(updated);
    setStatus({
      text: `Question ${probId} marked as Skipped (Concept Gap). Step-by-step solution expanded.`,
      type: "warn",
    });
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
    triggerAutoSave(updated);
    setStatus({
      text: `Reset ${currentDrill.drillId} to initial state. Ready for a new practice run!`,
      type: "pass",
    });
  };

  // Quiz Pagination Navigation Handlers
  const handlePrevQuestion = () => {
    setCurrentProblemIndex((prev) => (prev > 0 ? prev - 1 : prev));
  };

  const handleNextQuestion = () => {
    if (!currentDrill) return;
    setCurrentProblemIndex((prev) => (prev < currentDrill.problems.length - 1 ? prev + 1 : prev));
  };

  const handleSelectQuestion = (idx: number) => {
    setCurrentProblemIndex(idx);
    if (viewMode === "all" && currentDrill?.problems[idx]) {
      const el = document.getElementById(`problem-${currentDrill.problems[idx].id}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  };

  // Keyboard navigation for arrow keys in Quiz Mode
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) {
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
  }, [viewMode, currentDrill]);

  // Compute live score
  const liveScore = currentDrill
    ? currentDrill.problems.reduce((acc, p) => acc + (p.state?.score || 0), 0)
    : 0;
  const maxScore = currentDrill?.problems.length || 0;
  const accuracyPct = maxScore > 0 ? Math.round((liveScore / maxScore) * 1000) / 10 : 0;
  const skippedCount = currentDrill
    ? currentDrill.problems.filter((p) => p.state?.skipped).length
    : 0;

  // Sync to Notion
  const handleSyncToNotion = async () => {
    if (!currentDrill) return;
    setIsSyncing(true);
    setStatus({
      text: `Syncing ${currentDrill.drillId} (${liveScore}/${maxScore}${skippedCount > 0 ? ` · ${skippedCount} skipped` : ""}) to Notion...`,
      type: "warn",
    });

    const tagMap = new Map((currentDrill.mistakeTags || []).map((t) => [t.id, t.name]));
    const mistakeNames = new Set<string>();
    const divergedList: string[] = [];
    const skippedProblems: string[] = [];

    currentDrill.problems.forEach((p) => {
      if (p.state?.skipped) {
        skippedProblems.push(`${p.id} (${p.context || p.category})`);
        divergedList.push(`${p.id} [SKIPPED - Concept Gap]`);
      }
      (p.state?.mistakes || []).forEach((tid) => {
        const rawName = tagMap.get(tid) || tid;
        mistakeNames.add(rawName.replace(/,/g, " /").trim());
      });
      if (typeof p.state?.divergedStep === "number") {
        const st = p.steps[p.state.divergedStep];
        divergedList.push(`${p.id} (Step ${p.state.divergedStep + 1}: ${st ? st.explain : "Diverged"})`);
      } else if (p.state?.score !== null && p.state?.score !== undefined && p.state.score < 1 && (p.state?.mistakes || []).length > 0 && !p.state?.skipped) {
        divergedList.push(`${p.id} (${(p.state?.mistakes || []).map((t) => tagMap.get(t) || t).join(", ")})`);
      }
    });

    const fullDocToSync: DrillDocument = {
      ...currentDrill,
      sessionSummary: {
        practiceStatus: maxScore > 0 && liveScore / maxScore >= 0.8 ? "Graded" : "Needs Retry",
        score: liveScore,
        maxScore,
        accuracyPct,
        skippedCount: skippedProblems.length,
        skippedProblems,
        mistakeCategories: Array.from(mistakeNames),
        divergedStepsSummary: divergedList.length > 0 ? divergedList.join(" | ") : "No diverged steps logged.",
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

      setStatus({
        text: `Synced to Notion! Updated ${currentDrill.drillId} (${liveScore}/${maxScore} · ${accuracyPct}%) in Learning Practice & Drills and logged to ${currentDrill.unitCode}.`,
        type: "pass",
      });
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setStatus({ text: `Notion Sync error: ${errMsg}`, type: "fail" });
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0d1017] text-slate-100 p-4 md:p-6 lg:p-8">
      <div className="max-w-5xl mx-auto">
        {/* Top Sticky Bar */}
        <header className="sticky top-3 z-50 bg-[#151924]/90 backdrop-blur-md border border-[#2c354d] rounded-2xl p-4 mb-6 shadow-xl flex flex-wrap items-center justify-between gap-4">
          {/* Pre-Gen Config */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              1. Pre-Generation Config
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={cfgUnit}
                onChange={(e) => setCfgUnit(e.target.value)}
                className="bg-[#1d2333] border border-[#2c354d] rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
              >
                <optgroup label="JavaScript &amp; TypeScript (PRG-T01)">
                  <option value="PRG-T01-C01">PRG-T01-C01 · JS Deep Dive (Mental Model &amp; Prediction)</option>
                  <option value="PRG-T01-C03">PRG-T01-C03 · Utility Toolkit (Coding Katas &amp; VS Code)</option>
                </optgroup>
                <optgroup label="Mathematics (MTH-T01 / T02)">
                  <option value="MTH-T02-C01-U01">MTH-T02-C01-U01 · Complex Numbers</option>
                  <option value="MTH-T01-C12">MTH-T01-C12 · Math Models &amp; Geometry</option>
                </optgroup>
              </select>

              <select
                value={cfgCount}
                onChange={(e) => setCfgCount(Number(e.target.value))}
                className="bg-[#1d2333] border border-[#2c354d] rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value={5}>5 Qs</option>
                <option value={10}>10 Qs</option>
                <option value={15}>15 Qs</option>
                <option value={20}>20 Qs</option>
              </select>

              <select
                value={cfgDifficulty}
                onChange={(e) => setCfgDifficulty(e.target.value)}
                className="bg-[#1d2333] border border-[#2c354d] rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value="ALL">Mixed Exam Mode (L1–L4)</option>
                <option value="1">Level 1 — Foundation</option>
                <option value="2">Level 2 — Standard Exam</option>
                <option value="3">Level 3 — Trap &amp; Diagnostic</option>
                <option value="4">Level 4 — Applied Synthesis</option>
              </select>

              <button
                type="button"
                onClick={handleGenerateDrill}
                disabled={isGenerating}
                className="inline-flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors shadow-sm"
              >
                {isGenerating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                Generate New .json Set
              </button>
            </div>
          </div>

          <div className="hidden md:block w-px h-10 bg-[#2c354d]" />

          {/* Active Drill & Notion Sync */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              2. Active Drill File (.json) &amp; Notion Sync
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={selectedDrillId}
                onChange={(e) => {
                  setSelectedDrillId(e.target.value);
                  loadDrill(e.target.value);
                }}
                className="bg-[#1d2333] border border-[#2c354d] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 max-w-[220px] truncate"
              >
                {drills.map((d) => (
                  <option key={d.drillId} value={d.drillId}>
                    {d.drillId} · {d.unitCode} ({d.questionCount} Qs)
                  </option>
                ))}
              </select>

              <span className="text-xs font-bold px-2.5 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Score: {liveScore} / {maxScore} ({accuracyPct}%)
              </span>

              {skippedCount > 0 && (
                <span className="text-xs font-bold px-2.5 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  Skipped: {skippedCount}
                </span>
              )}

              <button
                type="button"
                onClick={handleResetAll}
                title="Reset all questions and score"
                className="inline-flex items-center gap-1 bg-[#1d2333] hover:bg-rose-500/20 text-slate-300 hover:text-rose-300 font-semibold text-xs px-2.5 py-1.5 rounded-lg border border-[#2c354d] hover:border-rose-500/40 transition-colors shadow-sm"
              >
                <RotateCcw className="w-3.5 h-3.5 text-rose-400" />
                Reset All
              </button>

              <button
                type="button"
                onClick={handleSyncToNotion}
                disabled={isSyncing || !currentDrill}
                className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-slate-950 font-bold text-xs px-3.5 py-1.5 rounded-lg transition-colors shadow-sm"
              >
                {isSyncing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                Grade &amp; Sync to Notion
              </button>
            </div>
          </div>
        </header>

        {/* Status Notification Banner */}
        {status && (
          <div
            className={`p-3 rounded-xl mb-5 text-sm flex items-center justify-between border ${
              status.type === "pass"
                ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                : status.type === "fail"
                ? "bg-rose-500/10 text-rose-300 border-rose-500/30"
                : "bg-amber-500/10 text-amber-300 border-amber-500/30"
            }`}
          >
            <div className="flex items-center gap-2">
              {status.type === "pass" ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ) : (
                <AlertCircle className="w-4 h-4 text-amber-400" />
              )}
              <span dangerouslySetInnerHTML={{ __html: status.text }} />
            </div>
            <button
              type="button"
              onClick={() => setStatus(null)}
              className="text-xs text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        )}

        {/* Header Metadata Card */}
        {currentDrill && (
          <section className="bg-gradient-to-br from-[#181f30] to-[#121622] border border-[#2c354d] rounded-2xl p-5 mb-6 shadow-sm">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                {currentDrill.drillId}
              </span>
              {currentDrill.unitNotionUrl && (
                <a
                  href={currentDrill.unitNotionUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/30 hover:bg-sky-500/20 transition-colors"
                >
                  ↗ Notion Unit: {currentDrill.unitCode} · {currentDrill.unitTitle}
                </a>
              )}
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#1d2333] text-slate-400 border border-[#2c354d]">
                {currentDrill.problems.length} Questions ({currentDrill.config?.difficultyMode || "Mixed"})
              </span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#1d2333] text-slate-500 border border-[#2c354d]">
                File: {currentDrill.localFilePath}
              </span>
            </div>
            <div className="flex items-center gap-2 mb-1.5">
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono uppercase tracking-wider ${
                  currentDrill.subject === "PRG"
                    ? "bg-sky-500/10 text-sky-400 border border-sky-500/30"
                    : "bg-indigo-500/10 text-indigo-400 border border-indigo-500/30"
                }`}
              >
                {currentDrill.subject === "PRG" ? "Programming Workspace" : "Mathematics Workspace"}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {currentDrill.drillId} · {currentDrill.config?.questionCount} Questions
              </span>
            </div>
            <h1 className="text-xl font-bold text-white mb-1">
              {currentDrill.unitTitle} ({currentDrill.unitCode}) — Practice &amp; Diagnostics Studio
            </h1>
            <p className="text-xs text-slate-400">
              {currentDrill.subject === "PRG"
                ? "Trace JavaScript runtime behavior in the VS Code editor, click lines to identify bugs or predict Call Stack & Microtask outputs, mark where your mental model diverged, and sync progress directly to Notion."
                : "Solve on physical scratch paper, verify intermediate checkpoints, click any derivation step to highlight equation & explanation together, mark your diverged step, and sync scores directly to Notion."}
            </p>
          </section>
        )}

        {/* Quiz Pagination Navigation Bar */}
        {currentDrill && currentDrill.problems.length > 0 && (
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
        )}

        {/* Problems Main Area */}
        <main className="space-y-5">
          {viewMode === "quiz" && currentDrill && currentDrill.problems[currentProblemIndex] ? (
            <div>
              {/* Single Problem Focus in Quiz Mode */}
              {(() => {
                const prob = currentDrill.problems[currentProblemIndex];
                const idx = currentProblemIndex;
                return (
                  <div key={prob.id} className="animate-in fade-in duration-150">
                    <ProblemCard
                      problem={prob}
                      index={idx}
                      subject={currentDrill.subject}
                      mistakeTags={currentDrill.mistakeTags || []}
                      activeStep={activeSteps[prob.id] ?? null}
                      onInputChange={(val) => handleInputChange(prob.id, val)}
                      onCheckAnswer={() => handleCheckAnswer(prob.id)}
                      onSkip={() => handleSkipProblem(prob.id)}
                      onToggleStepHighlight={(stepIdx) => handleToggleStepHighlight(prob.id, stepIdx)}
                      onMarkDivergedStep={(stepIdx) => handleMarkDivergedStep(prob.id, stepIdx)}
                      onSetScore={(score) => handleSetScore(prob.id, score)}
                      onToggleMistakeTag={(tagId) => handleToggleMistakeTag(prob.id, tagId)}
                      onResetProblem={() => handleResetProblem(prob.id)}
                    />

                    {/* Bottom Question Navigation Footer */}
                    <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-[#141926]/90 border border-[#2b3752] rounded-2xl shadow-lg mt-4">
                      <button
                        type="button"
                        onClick={handlePrevQuestion}
                        disabled={currentProblemIndex === 0}
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs md:text-sm font-semibold bg-[#1c2438] hover:bg-[#25304a] disabled:opacity-40 disabled:hover:bg-[#1c2438] text-slate-200 border border-[#2c3852] transition-colors"
                      >
                        <ChevronLeft className="w-4 h-4" />
                        <span>Previous Question</span>
                        <kbd className="hidden sm:inline-block text-[10px] bg-[#10141f] text-slate-400 px-1.5 py-0.5 rounded border border-[#2c3852]">←</kbd>
                      </button>

                      <div className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
                        <span>Question</span>
                        <strong className="text-white bg-[#1c2438] px-2 py-0.5 rounded border border-[#2c3852]">{currentProblemIndex + 1}</strong>
                        <span>of</span>
                        <strong className="text-slate-300">{currentDrill.problems.length}</strong>
                      </div>

                      <button
                        type="button"
                        onClick={handleNextQuestion}
                        disabled={currentProblemIndex === currentDrill.problems.length - 1}
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs md:text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white transition-colors shadow-sm"
                      >
                        <span>Next Question</span>
                        <kbd className="hidden sm:inline-block text-[10px] bg-indigo-900/60 text-indigo-200 px-1.5 py-0.5 rounded border border-indigo-400/40">→</kbd>
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })()}
            </div>
          ) : (
            /* All Problems in Scroll Mode */
            currentDrill?.problems.map((prob, idx) => (
              <div key={prob.id} id={`problem-${prob.id}`}>
                <ProblemCard
                  problem={prob}
                  index={idx}
                  subject={currentDrill.subject}
                  mistakeTags={currentDrill.mistakeTags || []}
                  activeStep={activeSteps[prob.id] ?? null}
                  onInputChange={(val) => handleInputChange(prob.id, val)}
                  onCheckAnswer={() => handleCheckAnswer(prob.id)}
                  onSkip={() => handleSkipProblem(prob.id)}
                  onToggleStepHighlight={(stepIdx) => handleToggleStepHighlight(prob.id, stepIdx)}
                  onMarkDivergedStep={(stepIdx) => handleMarkDivergedStep(prob.id, stepIdx)}
                  onSetScore={(score) => handleSetScore(prob.id, score)}
                  onToggleMistakeTag={(tagId) => handleToggleMistakeTag(prob.id, tagId)}
                  onResetProblem={() => handleResetProblem(prob.id)}
                />
              </div>
            ))
          )}
        </main>
      </div>
    </div>
  );
}
