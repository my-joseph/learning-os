"use client";

import React, { useState, useEffect } from "react";
import {
  ChevronDown,
  ChevronUp,
  Lightbulb,
  RotateCcw,
  Terminal,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  RefreshCw,
  Code2,
  FileCode2,
  FileCheck,
  Check,
  FolderOpen,
  HelpCircle,
  Zap,
  Bug,
  SearchCode,
  Wrench,
  Blocks,
  X,
  PenLine,
  Flag,
  Loader2,
} from "lucide-react";
import {
  Problem,
  MistakeTag,
  CheckResult,
  TestRunReport,
  EngineeringArchetype,
} from "@/types/drill";
import { VSCodeBlock } from "./VSCodeBlock";
import { FormattedText } from "./FormattedText";

const ARCHETYPE_CONFIG: Record<
  EngineeringArchetype,
  { label: string; description: string; badgeClass: string; Icon: React.ComponentType<{ className?: string }> }
> = {
  "problem-solving": {
    label: "Problem Solving",
    description: "Algorithm & Logic Problem Solving",
    badgeClass:
      "bg-emerald-50 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-600/40",
    Icon: Zap,
  },
  debugging: {
    label: "Debugging",
    description: "Analyze and Fix Runtime or Logic Bugs",
    badgeClass:
      "bg-rose-50 dark:bg-rose-950/80 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-600/40",
    Icon: Bug,
  },
  "code-tracing": {
    label: "Code Tracing",
    description: "Trace Execution & Predict Output",
    badgeClass:
      "bg-amber-50 dark:bg-amber-950/80 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-600/40",
    Icon: SearchCode,
  },
  refactoring: {
    label: "Refactoring",
    description: "Refactor Structure & Extend Capability",
    badgeClass:
      "bg-purple-50 dark:bg-purple-950/80 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-600/40",
    Icon: Wrench,
  },
  "project-based": {
    label: "Project-Based",
    description: "Build Real-World System to Specification",
    badgeClass:
      "bg-blue-50 dark:bg-blue-950/80 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-600/40",
    Icon: Blocks,
  },
};

interface CodeProblemCardProps {
  problem: Problem;
  index: number;
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  onInputChange: (val: string) => void;
  onCheckAnswer: () => Promise<void> | void;
  onSkip?: () => void;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
  onResetProblem: () => void;
}

const getSafePlaceholder = (hint?: string, problem?: Problem): string => {
  if (!hint) return "Enter predicted terminal output (press Enter to check)...";

  const acceptedList: string[] = [];
  if (problem?.answerSpec?.accepted) {
    for (const a of problem.answerSpec.accepted) {
      if (typeof a === "string" && a.trim()) {
        acceptedList.push(a.toLowerCase().trim());
      }
    }
  }
  if (problem?.answerPlain && typeof problem.answerPlain === "string") {
    acceptedList.push(problem.answerPlain.toLowerCase().trim());
  }
  if (problem?.answerDisplay && typeof problem.answerDisplay === "string") {
    acceptedList.push(problem.answerDisplay.toLowerCase().trim());
  }

  const lowerHint = hint.toLowerCase();
  const hasLeak = acceptedList.some((ans) => ans.length >= 2 && lowerHint.includes(ans));

  if (!hasLeak) return hint;

  const stripped = hint.replace(/\s*\([^)]*e\.g\.[^)]*\)/gi, "").trim();
  if (stripped && !acceptedList.some((ans) => ans.length >= 2 && stripped.toLowerCase().includes(ans))) {
    return stripped;
  }

  return "Enter predicted terminal output (press Enter to check)...";
};

export const CodeProblemCard: React.FC<CodeProblemCardProps> = ({
  problem,
  index,
  mistakeTags,
  activeStep,
  onInputChange,
  onCheckAnswer,
  onSkip,
  onToggleStepHighlight,
  onMarkDivergedStep,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
  onResetProblem,
}) => {
  const [showHint, setShowHint] = useState(false);
  const [showSolution, setShowSolution] = useState(Boolean(problem.state.lastCheck));
  const [showDiskPreview, setShowDiskPreview] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  const effectiveArchetype: EngineeringArchetype =
    problem.archetype ||
    (problem.codeType === "debugging" || problem.codeType === "find-bug"
      ? "debugging"
      : problem.codeType === "code-tracing" || problem.codeType === "predict-output"
      ? "code-tracing"
      : problem.codeType === "refactoring" || problem.codeType === "refactor"
      ? "refactoring"
      : problem.codeType === "project-based"
      ? "project-based"
      : "problem-solving");

  const archetypeMeta =
    ARCHETYPE_CONFIG[effectiveArchetype] || ARCHETYPE_CONFIG["problem-solving"];
  const ArchetypeIcon = archetypeMeta.Icon;

  const isIdeExecution =
    Boolean(problem.workspaceFile) ||
    Boolean(problem.visibleTests && problem.visibleTests.length > 0) ||
    problem.codeType === "kata" ||
    problem.codeType === "implement" ||
    problem.codeType === "refactor" ||
    effectiveArchetype === "problem-solving" ||
    effectiveArchetype === "debugging" ||
    effectiveArchetype === "refactoring" ||
    effectiveArchetype === "project-based";

  const isKata = isIdeExecution;

  const [userCode, setUserCode] = useState<string>(
    problem.state?.userCode || problem.starterCode || problem.codeSnippet || ""
  );
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [isResettingCode, setIsResettingCode] = useState(false);
  const [testReport, setTestReport] = useState<TestRunReport | null>(
    problem.state?.lastTestReport || null
  );
  const [copiedCmd, setCopiedCmd] = useState(false);

  const workspacePath = problem.workspaceFile || "";
  const workspaceDir =
    problem.workspaceDir ||
    (workspacePath.includes("/")
      ? workspacePath.substring(0, workspacePath.lastIndexOf("/"))
      : ".");
  const filename = workspacePath.includes("/")
    ? workspacePath.substring(workspacePath.lastIndexOf("/") + 1)
    : workspacePath || "solution.js";

  const terminalCommand = `cd ${workspaceDir} && npm test`;

  // Explicit folder URL: MUST target directory to ensure package.json & terminal open in workspace
  const vscodeFolderUrl =
    problem.vscodeFolderUrl ||
    (problem.workspaceDir ? `vscode://file/${problem.workspaceDir}` : "") ||
    (workspaceDir && workspaceDir !== "."
      ? `vscode://file/${workspaceDir.startsWith("/") ? workspaceDir : "/" + workspaceDir}`
      : "");

  // Optional direct file URL for jumping into the source file
  const vscodeFileUrl =
    problem.vscodeUrl ||
    (problem.workspaceFile
      ? `vscode://file/${problem.workspaceFile.startsWith("/") ? problem.workspaceFile : "/" + problem.workspaceFile}`
      : "");

  const handleCopyCmd = () => {
    navigator.clipboard.writeText(terminalCommand);
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 1500);
  };

  useEffect(() => {
    setUserCode(problem.state?.userCode || problem.starterCode || problem.codeSnippet || "");
    setTestReport(problem.state?.lastTestReport || null);
    setShowSolution(Boolean(problem.state.lastCheck));
  }, [
    problem.id,
    problem.state?.userCode,
    problem.starterCode,
    problem.codeSnippet,
    problem.state?.lastTestReport,
    problem.state.lastCheck,
  ]);

  const score = problem.state.score;
  const lastCheck: CheckResult | null | undefined = problem.state.lastCheck;
  const isFindBug =
    problem.codeType === "find-bug" || problem.answerSpec?.type === "line_number";

  const selectedLineNumber = isFindBug
    ? parseInt(problem.state.userInput.replace(/\D/g, ""), 10) || null
    : null;

  const handleResetEntireProblem = async () => {
    const starter = problem.starterCode || problem.codeSnippet || "";
    setUserCode(starter);
    setTestReport(null);
    onResetProblem();
  };

  const handleResetCode = async () => {
    const starter = problem.starterCode || problem.codeSnippet || "";
    const ok = window.confirm("Reset local file on disk back to initial starter code?");
    if (!ok) return;

    setIsResettingCode(true);
    setUserCode(starter);
    setTestReport(null);
    onInputChange(starter);

    if (problem.workspaceFile) {
      try {
        await fetch("/api/workspace", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ file: problem.workspaceFile, content: starter }),
        });
      } catch {
        // ignore disk write error
      }
    }
    setIsResettingCode(false);
  };

  // Unified One-Click Sync from Disk + Run Tests (Flow 3.1)
  const handleSyncAndRunTests = async () => {
    setIsRunningTests(true);
    try {
      let latestCode = userCode;
      if (problem.workspaceFile) {
        try {
          const diskRes = await fetch(
            `/api/workspace?file=${encodeURIComponent(problem.workspaceFile)}`
          );
          if (diskRes.ok) {
            const diskData = await diskRes.json();
            if (typeof diskData.content === "string" && diskData.content.trim()) {
              latestCode = diskData.content;
              setUserCode(latestCode);
            }
          }
        } catch {
          // fallback to current userCode
        }
      }

      const res = await fetch("/api/run-tests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userCode: latestCode,
          workspaceFile: problem.workspaceFile,
          visibleTests: problem.visibleTests || [],
          hiddenTests: problem.hiddenTests || [],
        }),
      });

      const report: TestRunReport = await res.json();
      setTestReport(report);

      if (typeof report.score === "number") {
        onSetScore(report.score);
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setTestReport({
        allPassed: false,
        score: 0,
        passedCount: 0,
        totalCount: (problem.visibleTests?.length || 0) + (problem.hiddenTests?.length || 0),
        visibleResults: [{ name: "Execution Error", passed: false, error: errMsg }],
        hiddenPassed: 0,
        hiddenTotal: problem.hiddenTests?.length || 0,
        executionTimeMs: 0,
      });
    } finally {
      setIsRunningTests(false);
    }
  };

  const triggerWebCheck = async () => {
    if (!problem.state.userInput.trim() || isChecking) return;
    setIsChecking(true);
    try {
      await onCheckAnswer();
      setShowSolution(true);
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <article className="bg-white dark:bg-[#151924] border border-slate-200 dark:border-[#2c354d] rounded-2xl p-5 md:p-6 shadow-sm">
      {/* Top Header */}
      <div className="flex flex-wrap justify-between items-center gap-2 mb-4 pb-3 border-b border-slate-200 dark:border-[#2c354d]">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`px-2.5 py-0.5 rounded-md text-xs font-mono font-semibold uppercase border inline-flex items-center gap-1.5 ${archetypeMeta.badgeClass}`}
            title={archetypeMeta.description}
          >
            <ArchetypeIcon className="w-3.5 h-3.5" />
            <span>{archetypeMeta.label}</span>
          </span>

          <span className="font-bold text-base text-slate-900 dark:text-white">
            Problem {index + 1}{" "}
            <span className="text-slate-500 dark:text-slate-400 font-normal text-sm">
              ({problem.id})
            </span>
          </span>

          {problem.context && (
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-50 dark:bg-cyan-500/10 text-cyan-800 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-500/30">
              <FormattedText text={problem.context} />
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {problem.state.skipped && (
            <span className="text-xs px-2.5 py-1 rounded-full bg-amber-50 dark:bg-amber-500/10 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-500/30 font-medium">
              Skipped
            </span>
          )}
          <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 dark:bg-[#1d2333] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-[#2c354d] font-medium">
            Level {problem.level}
          </span>
          <button
            type="button"
            title="Reset this question"
            onClick={handleResetEntireProblem}
            className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-slate-500 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 border border-transparent hover:border-rose-200 dark:hover:border-rose-500/30 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Problem Prompt */}
      <div className="text-base text-slate-800 dark:text-slate-100 mb-4 leading-relaxed font-sans">
        <FormattedText text={problem.prompt} />
      </div>

      {/* ========================================================================= */}
      {/* CASE A: VS CODE EXECUTION MODE (Flow 3.1)                                 */}
      {/* ========================================================================= */}
      {isKata ? (
        <div className="mb-4 space-y-4">
          {/* Acceptance Criteria & Behavioral Requirements */}
          {problem.visibleTests && problem.visibleTests.length > 0 && (
            <div className="p-4 bg-slate-50 dark:bg-[#10141f] border border-slate-200 dark:border-[#2c354d] rounded-2xl">
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-200 dark:border-[#232b3e]">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <FileCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  Acceptance Criteria &amp; Test Cases ({problem.visibleTests.length})
                </span>
                {workspacePath && (
                  <span className="text-xs font-mono text-slate-500 dark:text-slate-400 truncate max-w-xs">
                    {workspacePath}
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {problem.visibleTests.map((t, idx) => (
                  <div
                    key={t.id || idx}
                    className="p-3 bg-white dark:bg-[#151b2c] border border-slate-200 dark:border-[#1f283e] rounded-xl flex items-start gap-2.5 text-xs"
                  >
                    <span className="w-5 h-5 rounded-full bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30 flex items-center justify-center font-mono font-bold shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <div className="flex-1 font-mono min-w-0">
                      <div className="text-slate-800 dark:text-slate-200 font-semibold mb-1">
                        {t.name}
                      </div>
                      <pre className="text-xs text-slate-600 dark:text-slate-300 overflow-x-auto whitespace-pre bg-slate-50 dark:bg-[#0d111c] p-2.5 rounded-lg border border-slate-200/80 dark:border-white/5">
                        <code>{t.testCode.trim()}</code>
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clean VS Code + Test Runner Action Bar */}
          <div className="p-4 bg-slate-50 dark:bg-[#10141f] border border-slate-200 dark:border-[#2c354d] rounded-2xl flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5">
              {vscodeFolderUrl && (
                <a
                  href={vscodeFolderUrl}
                  title="Open workspace in VS Code (loads package.json and terminal in workspace)"
                  className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-all shadow-sm"
                >
                  <FolderOpen className="w-4 h-4" />
                  <span>Open in VS Code</span>
                </a>
              )}

              {vscodeFileUrl && vscodeFileUrl !== vscodeFolderUrl && (
                <a
                  href={vscodeFileUrl}
                  title={`Open ${filename} directly in editor`}
                  className="inline-flex items-center gap-1.5 h-10 px-3 rounded-xl bg-white dark:bg-[#1d2333] hover:bg-slate-100 dark:hover:bg-[#25304a] text-slate-700 dark:text-slate-300 text-xs font-mono border border-slate-200 dark:border-[#2c354d] transition-colors"
                >
                  <FileCode2 className="w-3.5 h-3.5 text-blue-500" />
                  <span>Open File</span>
                </a>
              )}

              <button
                type="button"
                onClick={handleSyncAndRunTests}
                disabled={isRunningTests}
                className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition-all shadow-sm disabled:opacity-50"
              >
                {isRunningTests ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Syncing &amp; Running Tests...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" />
                    <span>Sync &amp; Run Tests (Submit)</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleCopyCmd}
                title={`Copy terminal command: ${terminalCommand}`}
                className="inline-flex items-center gap-1.5 h-10 px-3 rounded-xl bg-white dark:bg-[#1d2333] hover:bg-slate-100 dark:hover:bg-[#25304a] text-slate-700 dark:text-slate-300 text-xs font-mono border border-slate-200 dark:border-[#2c354d] transition-colors"
              >
                <Terminal className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>{copiedCmd ? "Copied npm test!" : "Copy npm test"}</span>
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => setShowDiskPreview(!showDiskPreview)}
                className="inline-flex items-center gap-1.5 h-9 px-3 rounded-xl bg-white dark:bg-[#1d2333] hover:bg-slate-100 dark:hover:bg-[#25304a] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-[#2c354d] text-xs font-medium transition-colors"
              >
                <Code2 className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />
                <span>{showDiskPreview ? "Hide Disk File" : `View ${filename}`}</span>
              </button>

              <button
                type="button"
                onClick={() => setShowHint(!showHint)}
                className="inline-flex items-center gap-1.5 h-9 px-3 rounded-xl bg-white dark:bg-[#1d2333] hover:bg-amber-50 dark:hover:bg-amber-500/10 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-[#2c354d] text-xs font-medium transition-colors"
              >
                <Lightbulb className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
                <span>Hint</span>
              </button>

              <button
                type="button"
                onClick={() => setShowSolution(!showSolution)}
                className="inline-flex items-center gap-1.5 h-9 px-3 rounded-xl bg-white dark:bg-[#1d2333] hover:bg-slate-100 dark:hover:bg-[#25304a] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-[#2c354d] text-xs font-medium transition-colors"
              >
                {showSolution ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                <span>{showSolution ? "Hide Reference" : "Reference Solution"}</span>
              </button>

              <button
                type="button"
                onClick={handleResetCode}
                disabled={isResettingCode}
                title="Reset local file on disk back to starter code"
                className="inline-flex items-center gap-1 h-9 px-2.5 rounded-xl bg-white dark:bg-[#1d2333] hover:bg-rose-50 dark:hover:bg-rose-500/10 text-slate-500 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-300 border border-slate-200 dark:border-[#2c354d] text-xs font-medium transition-colors disabled:opacity-50"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${isResettingCode ? "animate-spin" : ""}`} />
                <span>Reset Starter</span>
              </button>
            </div>
          </div>

          {/* Optional Collapsed Disk File Preview */}
          {showDiskPreview && (
            <VSCodeBlock
              code={userCode || problem.starterCode || "// Open file in VS Code to begin implementing..."}
              language={problem.language || "javascript"}
              filename={filename}
            />
          )}

          {/* Test Runner Results Panel */}
          {testReport && (
            <div
              className={`p-4 rounded-xl border text-xs md:text-sm ${
                testReport.allPassed
                  ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-500/40 text-emerald-900 dark:text-emerald-200"
                  : "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-500/40 text-rose-900 dark:text-rose-200"
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2 border-b border-emerald-200/60 dark:border-slate-700/50">
                <div className="flex items-center gap-2 font-semibold">
                  {testReport.allPassed ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <XCircle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
                  )}
                  <span>
                    {testReport.allPassed
                      ? "All Test Cases Passed! (Score Updated to 1.0)"
                      : `Tests Failed: ${testReport.passedCount} / ${testReport.totalCount} Passed`}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono text-slate-600 dark:text-slate-400">
                  <span>Duration: {testReport.executionTimeMs}ms</span>
                  {testReport.hiddenTotal > 0 && (
                    <span className="px-2 py-0.5 rounded bg-white/80 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                      Hidden: {testReport.hiddenPassed}/{testReport.hiddenTotal} passed
                    </span>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                {testReport.visibleResults?.map((res, i) => (
                  <div
                    key={i}
                    className={`p-2.5 rounded-lg border font-mono text-xs ${
                      res.passed
                        ? "bg-white/80 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-700/40 text-emerald-800 dark:text-emerald-300"
                        : "bg-white/80 dark:bg-rose-900/30 border-rose-200 dark:border-rose-700/40 text-rose-800 dark:text-rose-300"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {res.passed ? (
                          <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                        ) : (
                          <X className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400 shrink-0" />
                        )}
                        <strong>{res.name}</strong>
                      </div>
                      {typeof res.durationMs === "number" && (
                        <span className="text-xs opacity-75">{res.durationMs}ms</span>
                      )}
                    </div>
                    {res.error && (
                      <div className="mt-1.5 p-2 bg-rose-50 dark:bg-black/40 rounded text-xs text-rose-800 dark:text-rose-200 overflow-x-auto whitespace-pre border border-rose-200/60 dark:border-transparent">
                        {res.error}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* ========================================================================= */
        /* CASE B: WEB CODE READING / PREDICT OUTPUT / FIND BUG                      */
        /* ========================================================================= */
        <>
          {problem.codeSnippet && (
            <VSCodeBlock
              code={problem.codeSnippet}
              language={problem.language || "javascript"}
              filename={`challenge-${problem.id.toLowerCase()}.js`}
              selectableLines={isFindBug}
              selectedLine={selectedLineNumber}
              onSelectLine={(lineNum) => {
                onInputChange(String(lineNum));
              }}
            />
          )}

          {/* Multiple Choice Selection */}
          {problem.answerSpec.type === "choice" && problem.answerSpec.options && (
            <div className="mb-4">
              <div className="grid grid-cols-1 gap-2.5">
                {problem.answerSpec.options.map((opt) => {
                  const isSelected = problem.state.userInput === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => onInputChange(opt.id)}
                      className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-start gap-3 ${
                        isSelected
                          ? "bg-indigo-50 dark:bg-indigo-600/20 border-indigo-500 text-slate-900 dark:text-white shadow-sm"
                          : "bg-slate-50 dark:bg-[#111726]/80 hover:bg-slate-100 dark:hover:bg-[#161f33] border-slate-200 dark:border-[#263147] text-slate-800 dark:text-slate-200"
                      }`}
                    >
                      <span
                        className={`inline-flex items-center justify-center w-6 h-6 rounded-md text-xs font-bold shrink-0 transition-colors ${
                          isSelected
                            ? "bg-indigo-600 text-white"
                            : "bg-white dark:bg-[#1d263b] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-[#2b3752]"
                        }`}
                      >
                        {opt.id}
                      </span>
                      <div className="flex-1 text-sm pt-0.5 leading-relaxed">
                        <FormattedText text={opt.label} />
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Terminal Output Predictor Input */}
          {!isFindBug && problem.answerSpec.type !== "choice" && (
            <div className="mb-4">
              <div className="text-xs text-slate-600 dark:text-slate-400 mb-1.5 flex items-center gap-1.5 font-mono">
                <Terminal className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Terminal Output Prediction:</span>
              </div>
              <div className="flex items-center gap-2 bg-white dark:bg-[#0c1017] border border-slate-300 dark:border-[#263147] rounded-xl px-3.5 py-2 focus-within:ring-2 focus-within:ring-indigo-500/30 focus-within:border-indigo-500">
                <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold select-none text-sm">
                  &gt;
                </span>
                <input
                  type="text"
                  value={problem.state.userInput}
                  onChange={(e) => onInputChange(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      triggerWebCheck();
                    }
                  }}
                  placeholder={getSafePlaceholder(problem.inputHint, problem)}
                  className="flex-1 bg-transparent font-mono text-sm text-slate-900 dark:text-slate-100 focus:outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500"
                />
              </div>
            </div>
          )}

          {/* Action Row */}
          <div className="flex flex-wrap gap-2.5 items-center mb-4">
            <button
              type="button"
              onClick={triggerWebCheck}
              disabled={isChecking || !problem.state.userInput.trim()}
              className="inline-flex items-center gap-1.5 h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold transition-colors shadow-sm"
            >
              {isChecking ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Checking...</span>
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>
                    {isFindBug && selectedLineNumber
                      ? `Check Line ${selectedLineNumber}`
                      : "Check Answer"}
                  </span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => setShowHint(!showHint)}
              className="inline-flex items-center gap-1.5 h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#1a2133] hover:bg-amber-50 dark:hover:bg-amber-500/10 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-[#2b3752] text-sm font-medium transition-colors"
            >
              <Lightbulb className="w-4 h-4 text-amber-500 dark:text-amber-400" />
              <span>Hint</span>
            </button>

            <button
              type="button"
              onClick={() => setShowSolution(!showSolution)}
              className="inline-flex items-center gap-1.5 h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#1a2133] hover:bg-slate-200/70 dark:hover:bg-indigo-600/20 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-[#2b3752] text-sm font-medium transition-colors"
            >
              {showSolution ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              <span>{showSolution ? "Hide Breakdown" : "Step-by-Step Breakdown"}</span>
            </button>

            {onSkip && (
              <button
                type="button"
                onClick={() => {
                  setShowHint(true);
                  setShowSolution(true);
                  onSkip();
                }}
                className="inline-flex items-center gap-1.5 h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#1a2133] hover:bg-rose-50 dark:hover:bg-rose-500/15 text-slate-600 dark:text-slate-300 hover:text-rose-700 dark:hover:text-rose-300 border border-slate-200 dark:border-[#2b3752] text-sm font-medium transition-colors"
              >
                <HelpCircle className="w-4 h-4 text-rose-500 dark:text-rose-400" />
                <span>Skip</span>
              </button>
            )}
          </div>

          {/* Answer Verdict & Diagnostics Banner */}
          {lastCheck && (
            <div
              className={`p-3.5 rounded-xl border mb-4 text-sm ${
                lastCheck.verdict === "correct"
                  ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-500/40 text-emerald-900 dark:text-emerald-200"
                  : lastCheck.verdict === "partial" || problem.state.skipped || (lastCheck.verdict as string) === "skipped"
                  ? "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-500/40 text-amber-900 dark:text-amber-200"
                  : "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-500/40 text-rose-900 dark:text-rose-200"
              }`}
            >
              <div className="flex items-center gap-2 font-semibold mb-1">
                {lastCheck.verdict === "correct" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                ) : lastCheck.verdict === "partial" || problem.state.skipped || (lastCheck.verdict as string) === "skipped" ? (
                  <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
                )}
                <span>{lastCheck.message}</span>
              </div>

              {lastCheck.components && lastCheck.components.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t border-slate-200/60 dark:border-slate-700/50">
                  {lastCheck.components.map((c, i) => (
                    <span
                      key={i}
                      className={`text-xs px-2 py-0.5 rounded font-mono ${
                        c.ok
                          ? "bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300"
                          : "bg-rose-100 dark:bg-rose-900/60 text-rose-800 dark:text-rose-300"
                      }`}
                    >
                      {c.label}: {c.ok ? "PASS" : "FAIL"}
                    </span>
                  ))}
                </div>
              )}

              {lastCheck.diagnostics && lastCheck.diagnostics.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-200/60 dark:border-slate-700/50 text-xs text-slate-700 dark:text-slate-300 space-y-1">
                  {lastCheck.diagnostics.map((d, i) => (
                    <div key={i} className="flex items-start gap-1.5">
                      <span className="font-mono text-amber-700 dark:text-amber-400 uppercase font-semibold">
                        [{d.code}]:
                      </span>
                      <span>{d.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Checkpoint Hint Accordion */}
      {showHint && (
        <div className="bg-amber-50 dark:bg-[#141b2b] border border-amber-200 dark:border-amber-500/30 rounded-xl p-3.5 mb-4 text-sm text-amber-900 dark:text-amber-200">
          <strong className="text-amber-700 dark:text-amber-400 font-semibold block mb-1">
            Mental Model Checkpoint:
          </strong>
          <FormattedText text={problem.checkpointHint} />
        </div>
      )}

      {/* Step-by-Step Breakdown or Canonical Solution */}
      {showSolution && (
        <div className="bg-slate-50 dark:bg-[#0e121a] border border-slate-200 dark:border-[#263147] rounded-xl p-4 mb-4">
          <div className="flex flex-wrap justify-between items-center gap-2 mb-3 pb-2 border-b border-slate-200 dark:border-[#1f273b]">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              {isKata ? "Canonical Reference Solution" : "Step-by-Step Runtime Breakdown"}
            </span>
            <span className="text-xs text-slate-600 dark:text-slate-400 font-mono">
              Verified Target:{" "}
              <strong className="text-emerald-700 dark:text-emerald-400">
                {problem.answerDisplay}
              </strong>
            </span>
          </div>

          {isKata && problem.solutionCode ? (
            <VSCodeBlock
              code={problem.solutionCode}
              language={problem.language || "javascript"}
              filename={`reference-${filename}`}
            />
          ) : (
            <div className="space-y-2.5">
              {problem.steps.map((st, sIdx) => {
                const isDiverged = problem.state.divergedStep === sIdx;
                const isActive = activeStep === sIdx;

                return (
                  <div
                    key={sIdx}
                    onClick={() => onToggleStepHighlight(sIdx)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-colors ${
                      isDiverged
                        ? "bg-rose-50 dark:bg-rose-950/30 border-rose-500/60"
                        : isActive
                        ? "bg-indigo-50 dark:bg-indigo-950/40 border-indigo-400 ring-1 ring-indigo-500/40"
                        : "bg-white dark:bg-[#141925] border-slate-200 dark:border-[#222a3d] hover:border-slate-400 dark:hover:border-slate-600"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="text-xs font-bold text-indigo-700 dark:text-indigo-300 font-mono">
                        Phase {sIdx + 1}:
                      </span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onMarkDivergedStep(sIdx);
                        }}
                        className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg transition-colors border ${
                          isDiverged
                            ? "bg-rose-600 text-white border-rose-600 font-semibold"
                            : "text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-500/10 border-rose-200 dark:border-rose-500/30 hover:bg-rose-100"
                        }`}
                      >
                        <Flag className="w-3 h-3 shrink-0" />
                        <span>{isDiverged ? `Diverged at Phase ${sIdx + 1}` : "Mark Diverged"}</span>
                      </button>
                    </div>
                    <div className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
                      <FormattedText text={st.explain} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Unified Scoring, Mistake Tags & Custom Mistake Note Footer */}
      <div className="pt-3.5 border-t border-slate-200 dark:border-[#263147] space-y-3 text-xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-600 dark:text-slate-400 font-medium mr-1">Score:</span>
            {[
              { val: 1, label: "1.0", activeCls: "bg-emerald-600 text-white border-emerald-600" },
              { val: 0.5, label: "0.5", activeCls: "bg-amber-600 text-white border-amber-600" },
              { val: 0, label: "0", activeCls: "bg-rose-600 text-white border-rose-600" },
            ].map((btn) => (
              <button
                key={btn.val}
                type="button"
                onClick={() => onSetScore(btn.val)}
                className={`h-8 px-3 rounded-lg font-semibold border transition-all ${
                  score === btn.val
                    ? `${btn.activeCls} ring-2 ring-indigo-500/40 shadow-sm`
                    : "bg-slate-100 dark:bg-[#1b2234] text-slate-700 dark:text-slate-300 border-slate-200 dark:border-[#2c354d] hover:border-slate-400"
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-slate-600 dark:text-slate-400 font-medium mr-1">Mistake Tags:</span>
            {mistakeTags.map((t) => {
              const hasTag = problem.state.mistakes.includes(t.id);
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => onToggleMistakeTag(t.id)}
                  className={`min-h-[32px] py-1 px-3 rounded-full text-xs font-medium border transition-colors inline-flex items-center ${
                    hasTag
                      ? "bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-500/50 font-semibold"
                      : "bg-slate-100 dark:bg-[#161d2c] text-slate-600 dark:text-slate-400 border-slate-200 dark:border-[#263147] hover:border-slate-400"
                  }`}
                >
                  <FormattedText text={t.label} />
                </button>
              );
            })}
          </div>
        </div>

        {/* Custom Mistake Note Input */}
        <div className="flex items-center gap-2 bg-slate-50 dark:bg-[#10141f] border border-slate-200 dark:border-[#263147] rounded-xl px-3 py-2 focus-within:border-rose-400 dark:focus-within:border-rose-500/60 transition-colors">
          <PenLine className="w-4 h-4 text-rose-500 dark:text-rose-400 shrink-0" />
          <input
            type="text"
            value={problem.state.mistakeNote || ""}
            onChange={(e) => onMistakeNoteChange(e.target.value)}
            placeholder="Add custom mistake note (e.g., missed empty array edge case, forgot to return value)..."
            className="w-full bg-transparent text-xs md:text-sm text-slate-800 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none"
          />
        </div>
      </div>
    </article>
  );
};
