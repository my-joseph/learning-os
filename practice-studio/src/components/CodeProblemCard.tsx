"use client";

import React, { useState } from "react";
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
  ExternalLink,
  Code2,
  FileCheck,
  Copy,
  Check,
  FolderOpen,
  Sparkles,
} from "lucide-react";
import { Problem, MistakeTag, CheckResult, TestRunReport } from "@/types/drill";
import { NotionBadge } from "./NotionBadge";
import { VSCodeBlock } from "./VSCodeBlock";
import { FormattedText } from "./FormattedText";

interface CodeProblemCardProps {
  problem: Problem;
  index: number;
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  onInputChange: (val: string) => void;
  onCheckAnswer: () => void;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onResetProblem: () => void;
}

export const CodeProblemCard: React.FC<CodeProblemCardProps> = ({
  problem,
  index,
  mistakeTags,
  activeStep,
  onInputChange,
  onCheckAnswer,
  onToggleStepHighlight,
  onMarkDivergedStep,
  onSetScore,
  onToggleMistakeTag,
  onResetProblem,
}) => {
  const [showHint, setShowHint] = useState(false);
  const [showSolution, setShowSolution] = useState(false);

  // Kata / Function implementation state
  const isKata =
    problem.codeType === "kata" ||
    problem.codeType === "implement" ||
    problem.codeType === "refactor";

  const [userCode, setUserCode] = useState<string>(
    problem.state?.userCode || problem.starterCode || problem.codeSnippet || ""
  );
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [isResettingCode, setIsResettingCode] = useState(false);
  const [testReport, setTestReport] = useState<TestRunReport | null>(
    problem.state?.lastTestReport || null
  );
  const [isReloadingFromDisk, setIsReloadingFromDisk] = useState(false);
  const [copiedCmd, setCopiedCmd] = useState(false);
  const [copiedPath, setCopiedPath] = useState(false);
  const [showAiReview, setShowAiReview] = useState(false);

  const workspacePath = problem.workspaceFile || "";
  const workspaceDir = workspacePath.includes("/")
    ? workspacePath.substring(0, workspacePath.lastIndexOf("/"))
    : ".";
  const filename = workspacePath.includes("/")
    ? workspacePath.substring(workspacePath.lastIndexOf("/") + 1)
    : workspacePath || "solution.js";

  const terminalCommand = `cd ${workspaceDir} && npm test`;

  const handleCopyCmd = () => {
    navigator.clipboard.writeText(terminalCommand);
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 1500);
  };

  const handleCopyPath = () => {
    navigator.clipboard.writeText(workspacePath);
    setCopiedPath(true);
    setTimeout(() => setCopiedPath(false), 1500);
  };

  // Sync userCode when problem changes
  React.useEffect(() => {
    setUserCode(problem.state?.userCode || problem.starterCode || problem.codeSnippet || "");
    setTestReport(problem.state?.lastTestReport || null);
  }, [problem.id, problem.state?.userCode, problem.starterCode, problem.codeSnippet, problem.state?.lastTestReport]);

  const score = problem.state.score;
  const lastCheck: CheckResult | null | undefined = problem.state.lastCheck;
  const isFindBug =
    problem.codeType === "find-bug" || problem.answerSpec?.type === "line_number";

  // If find-bug, parse selected line number from userInput
  const selectedLineNumber = isFindBug
    ? parseInt(problem.state.userInput.replace(/\D/g, ""), 10) || null
    : null;

  const totalLines = problem.codeSnippet
    ? problem.codeSnippet.trim().split("\n").length
    : 10;

  // Reset entire question including code
  const handleResetEntireProblem = async () => {
    const starter = problem.starterCode || problem.codeSnippet || "";
    setUserCode(starter);
    setTestReport(null);
    onResetProblem();
  };

  // Reset code block specifically back to starter template
  const handleResetCode = async () => {
    const starter = problem.starterCode || problem.codeSnippet || "";
    const ok = window.confirm("Reset this code block back to the initial starter code?");
    if (!ok) return;

    setIsResettingCode(true);
    setUserCode(starter);
    setTestReport(null);
    onInputChange(starter);

    // If local workspace file exists, reset the file on disk too!
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

  // Run tests for Kata problems
  const handleRunTests = async () => {
    setIsRunningTests(true);
    try {
      const res = await fetch("/api/run-tests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userCode,
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
        visibleResults: [{ name: "Network Error", passed: false, error: errMsg }],
        hiddenPassed: 0,
        hiddenTotal: problem.hiddenTests?.length || 0,
        executionTimeMs: 0,
      });
    } finally {
      setIsRunningTests(false);
    }
  };

  // Reload code from local file edited in VS Code / Cursor
  const handleReloadFromDisk = async () => {
    if (!problem.workspaceFile) return;
    setIsReloadingFromDisk(true);
    try {
      const res = await fetch(`/api/workspace?file=${encodeURIComponent(problem.workspaceFile)}`);
      const data = await res.json();
      if (data.content) {
        setUserCode(data.content);
      }
    } catch {
      // ignore reload error
    } finally {
      setIsReloadingFromDisk(false);
    }
  };

  return (
    <article className="bg-[#121622] border border-[#263147] rounded-2xl p-5 mb-6 shadow-xl">
      {/* Top Header */}
      <div className="flex flex-wrap justify-between items-center gap-2 mb-3 pb-3 border-b border-[#263147]">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-bold text-base text-indigo-300 flex items-center gap-2">
            <span
              className={`px-2 py-0.5 rounded-md text-xs font-mono font-semibold uppercase ${
                isKata
                  ? "bg-emerald-950/70 text-emerald-300 border border-emerald-700/40"
                  : "bg-indigo-950/70 text-indigo-300 border border-indigo-700/40"
              }`}
            >
              {isKata ? "KATA" : "CODE"}
            </span>
            Problem {index + 1}{" "}
            <span className="text-slate-400 font-normal">({problem.id})</span>
          </span>

          {problem.context && (
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 font-mono">
              <FormattedText text={problem.context} />
            </span>
          )}

          {problem.referenceBadges?.map((b) => (
            <NotionBadge key={b.code} badge={b} />
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            title="Reset this question"
            onClick={handleResetEntireProblem}
            className="p-1 rounded-md text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#1b2234] text-slate-300 border border-[#2b3752]">
            Level {problem.level} · {problem.levelLabel}
          </span>
        </div>
      </div>

      {/* Problem Prompt */}
      <div className="text-sm md:text-base text-slate-100 mb-4 leading-relaxed font-sans">
        <FormattedText text={problem.prompt} />
      </div>

      {/* ========================================================================= */}
      {/* CASE A: 100% LOCAL IDE MISSION CONTROL (VS Code & Cursor Execution)      */}
      {/* ========================================================================= */}
      {isKata ? (
        <div className="mb-5 space-y-4">
          {/* Mission Control Cockpit Banner */}
          <div className="p-4 bg-gradient-to-r from-[#131b2e] via-[#161f36] to-[#121726] border border-[#263554] rounded-2xl shadow-lg">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-500/10 text-sky-300 border border-sky-500/30 text-xs font-mono font-semibold">
                  <Terminal className="w-3.5 h-3.5 text-sky-400" />
                  100% Local IDE Execution Mandate
                </span>
                <span className="text-xs text-slate-400 font-sans hidden sm:inline">
                  • Write and debug exclusively in your editor
                </span>
              </div>

              {/* Path copy */}
              {workspacePath && (
                <button
                  type="button"
                  onClick={handleCopyPath}
                  title="Click to copy file path"
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0f1422] hover:bg-[#1a233a] border border-[#232f48] text-slate-300 text-[11px] font-mono transition-colors"
                >
                  <FolderOpen className="w-3 h-3 text-sky-400" />
                  <span className="truncate max-w-[200px] md:max-w-xs">{workspacePath}</span>
                  {copiedPath ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-400" />}
                </button>
              )}
            </div>

            {/* Hero Launch Buttons Row */}
            <div className="flex flex-wrap items-center gap-2.5">
              {problem.vscodeUrl && (
                <a
                  href={problem.vscodeUrl}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs md:text-sm font-semibold transition-all shadow-md hover:shadow-blue-500/20 active:scale-[0.98]"
                >
                  <ExternalLink className="w-4 h-4" />
                  Launch in VS Code
                </a>
              )}

              {problem.cursorUrl && (
                <a
                  href={problem.cursorUrl}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs md:text-sm font-semibold transition-all shadow-md hover:shadow-cyan-500/20 active:scale-[0.98]"
                >
                  <ExternalLink className="w-4 h-4" />
                  Launch in Cursor
                </a>
              )}

              <button
                type="button"
                onClick={handleReloadFromDisk}
                disabled={isReloadingFromDisk}
                title="Sync and read latest saved code from local disk"
                className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-[#1c2438] hover:bg-[#25304a] text-slate-200 border border-[#2b3a5a] text-xs font-semibold transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${isReloadingFromDisk ? "animate-spin" : ""}`} />
                {isReloadingFromDisk ? "Reading Disk..." : "Sync from Disk"}
              </button>

              <button
                type="button"
                onClick={handleResetCode}
                disabled={isResettingCode}
                title="Reset local file on disk back to starter code"
                className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-[#1c2438] hover:bg-rose-500/10 hover:text-rose-300 text-slate-400 border border-[#2b3a5a] text-xs font-medium transition-colors disabled:opacity-50"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${isResettingCode ? "animate-spin" : ""}`} />
                Reset Starter
              </button>
            </div>

            {/* Quick Terminal Command Snippet */}
            <div className="mt-3.5 pt-3 border-t border-[#1e2a44] flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 font-mono text-xs text-slate-300 overflow-x-auto">
                <span className="text-emerald-400 font-bold select-none">$</span>
                <code className="text-sky-300">{terminalCommand}</code>
              </div>
              <button
                type="button"
                onClick={handleCopyCmd}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#0f1422] hover:bg-[#1f2b45] text-slate-300 text-[11px] font-mono border border-[#232f48] transition-colors"
              >
                {copiedCmd ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-400" />}
                {copiedCmd ? "Copied Command!" : "Copy Command"}
              </button>
            </div>
          </div>

          {/* Acceptance Criteria & Behavioral Requirements */}
          {problem.visibleTests && problem.visibleTests.length > 0 && (
            <div className="p-4 bg-[#111624] border border-[#222c42] rounded-2xl">
              <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-[#1b2336]">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <FileCheck className="w-4 h-4 text-emerald-400" />
                  Acceptance Criteria & Test Matrix ({problem.visibleTests.length} Scenarios)
                </span>
                <span className="text-[11px] text-slate-400 font-mono">
                  Functional Behavioral Suite
                </span>
              </div>
              <div className="space-y-2">
                {problem.visibleTests.map((t, idx) => (
                  <div key={t.id || idx} className="p-2.5 bg-[#151b2c] border border-[#1f283e] rounded-xl flex items-start gap-2.5 text-xs">
                    <span className="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-mono font-bold text-[10px] shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <div className="flex-1 font-mono">
                      <div className="text-slate-200 font-semibold mb-1">{t.name}</div>
                      <pre className="text-[11px] text-slate-400 overflow-x-auto whitespace-pre bg-black/30 p-2 rounded border border-white/5">
                        <code>{t.testCode.trim()}</code>
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Current Code on Disk Preview (Read-Only VSCodeBlock) */}
          <div className="border border-[#222c42] rounded-2xl overflow-hidden bg-[#1e1e1e] shadow-md">
            <div className="px-3.5 py-2 bg-[#252526] border-b border-[#1f1f1f] text-xs font-mono text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Code2 className="w-3.5 h-3.5 text-sky-400" />
                Live Disk Preview: <strong className="text-white">{filename}</strong> (Read-Only)
              </span>
              <span className="text-[11px] text-slate-400">
                Edit in VS Code ➔ Click &quot;Run Tests&quot; or &quot;Sync from Disk&quot;
              </span>
            </div>
            <VSCodeBlock
              code={userCode || problem.starterCode || "// Open file in VS Code to begin implementing..."}
              language={problem.language || "javascript"}
              filename={filename}
            />
          </div>

          {/* Action Row */}
          <div className="flex flex-wrap items-center gap-2.5 pt-1">
            <button
              type="button"
              onClick={handleRunTests}
              disabled={isRunningTests}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs md:text-sm font-semibold transition-all shadow-md hover:shadow-emerald-500/20 active:scale-[0.98] flex items-center gap-2 disabled:opacity-50"
            >
              {isRunningTests ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Executing Local Tests...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  Run Tests (Local Node)
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => setShowAiReview(!showAiReview)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#1c2438] hover:bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              {showAiReview ? "Hide AI Review Guide" : "Request AI Architectural Review"}
            </button>

            <button
              type="button"
              onClick={() => setShowHint(!showHint)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#1c2438] hover:bg-amber-500/10 text-slate-300 hover:text-amber-300 border border-[#2b3a5a] text-xs font-medium transition-colors"
            >
              <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
              Checkpoint Hint
            </button>

            <button
              type="button"
              onClick={() => setShowSolution(!showSolution)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#1c2438] hover:bg-slate-700/50 text-slate-300 hover:text-white border border-[#2b3a5a] text-xs font-medium transition-colors"
            >
              {showSolution ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              {showSolution ? "Hide Reference" : "Reveal Canonical Reference"}
            </button>
          </div>

          {/* AI Code Review Guided Prompt Box */}
          {showAiReview && (
            <div className="p-4 bg-gradient-to-br from-indigo-950/40 via-[#161a2b] to-[#121624] border border-indigo-500/40 rounded-2xl text-xs md:text-sm text-indigo-100 shadow-md">
              <div className="flex items-center gap-2 font-semibold text-indigo-300 mb-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Senior AI Code Review & Architectural Guided Prompt
              </div>
              <p className="text-xs text-slate-300 leading-relaxed mb-3">
                After your automated tests pass, copy this prompt and send it to your AI coding assistant (Antigravity, Claude, or Cursor) in VS Code to receive a comprehensive Pull Request Architecture Review:
              </p>
              <div className="p-3 bg-black/50 border border-indigo-500/20 rounded-xl font-mono text-xs text-indigo-200 select-all whitespace-pre-wrap leading-relaxed">
                {`Please act as a Senior Tech Lead and perform a Pull Request Code Review on my implementation in file \`${workspacePath}\` for Unit ${problem.references?.[0] || "PRG"}.
Review my code against:
1. Separation of Concerns & Clean Code standards
2. Boundary invariants, edge cases, and error handling
3. Design Patterns & potential refactoring to make the architecture more maintainable and decoupled.`}
              </div>
            </div>
          )}

          {/* Test Runner Results Panel */}
          {testReport && (
            <div
              className={`p-4 rounded-xl border mb-4 text-xs md:text-sm ${
                testReport.allPassed
                  ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-200"
                  : "bg-rose-950/40 border-rose-500/40 text-rose-200"
              }`}
            >
              {/* Report Header */}
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2 border-b border-slate-700/50">
                <div className="flex items-center gap-2 font-semibold">
                  {testReport.allPassed ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <XCircle className="w-5 h-5 text-rose-400" />
                  )}
                  <span>
                    {testReport.allPassed
                      ? "All Test Cases Passed! (100% Score)"
                      : `Tests Failed: ${testReport.passedCount} / ${testReport.totalCount} Passed`}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                  <span>Duration: {testReport.executionTimeMs}ms</span>
                  {testReport.hiddenTotal > 0 && (
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      Hidden Cases: {testReport.hiddenPassed}/{testReport.hiddenTotal} passed
                    </span>
                  )}
                </div>
              </div>

              {/* Individual Visible Test Results */}
              <div className="space-y-2">
                {testReport.visibleResults?.map((res, i) => (
                  <div
                    key={i}
                    className={`p-2.5 rounded-lg border font-mono text-xs ${
                      res.passed
                        ? "bg-emerald-900/30 border-emerald-700/40 text-emerald-300"
                        : "bg-rose-900/30 border-rose-700/40 text-rose-300"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span>{res.passed ? "✔" : "✖"}</span>
                        <strong>{res.name}</strong>
                      </div>
                      {typeof res.durationMs === "number" && (
                        <span className="text-[11px] opacity-75">{res.durationMs}ms</span>
                      )}
                    </div>
                    {res.error && (
                      <div className="mt-1.5 p-2 bg-black/40 rounded text-[11px] text-rose-200 overflow-x-auto whitespace-pre">
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
        /* CASE B: MENTAL MODEL / READING PROBLEM (Predict Output / Find Bug)       */
        /* ========================================================================= */
        <>
          {/* VS Code Dark+ Code Viewer */}
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

          {/* Quick Line Selector Pills for Find-Bug */}
          {isFindBug && (
            <div className="mb-4 p-3 bg-[#171d2c] border border-[#263147] rounded-xl">
              <div className="text-xs text-slate-400 mb-2 flex items-center justify-between">
                <span>Select the defective line (click in code block above or choose here):</span>
                {selectedLineNumber && (
                  <span className="font-semibold text-sky-400">
                    Selected: Line {selectedLineNumber}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {Array.from({ length: totalLines }, (_, i) => i + 1).map((lineNum) => {
                  const isSelected = selectedLineNumber === lineNum;
                  return (
                    <button
                      key={lineNum}
                      type="button"
                      onClick={() => onInputChange(String(lineNum))}
                      className={`px-2.5 py-1 rounded text-xs font-mono font-medium border transition-colors ${
                        isSelected
                          ? "bg-sky-600 text-white border-sky-400 shadow-sm"
                          : "bg-[#1f273b] text-slate-300 border-[#2b3752] hover:border-sky-400 hover:text-white"
                      }`}
                    >
                      L{lineNum}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Terminal Output Predictor Input */}
          {!isFindBug && (
            <div className="mb-4">
              <div className="text-xs text-slate-400 mb-1.5 flex items-center gap-1.5 font-mono">
                <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                <span>Terminal Output Prediction:</span>
              </div>
              <div className="flex items-center gap-2 bg-[#0c1017] border border-[#263147] rounded-lg px-3 py-2">
                <span className="font-mono text-emerald-400 font-bold select-none text-xs md:text-sm">
                  &gt;
                </span>
                <input
                  type="text"
                  value={problem.state.userInput}
                  onChange={(e) => onInputChange(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") onCheckAnswer();
                  }}
                  placeholder={problem.inputHint || "Type predicted output..."}
                  className="flex-1 bg-transparent font-mono text-xs md:text-sm text-slate-100 focus:outline-none placeholder:text-slate-500"
                />
              </div>
            </div>
          )}

          {/* Action Row */}
          <div className="flex flex-wrap gap-2.5 items-center mb-4">
            <button
              type="button"
              onClick={onCheckAnswer}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs md:text-sm font-semibold transition-colors shadow-sm flex items-center gap-1.5"
            >
              Check Answer
            </button>

            <button
              type="button"
              onClick={() => setShowHint(!showHint)}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#1a2133] hover:bg-amber-500/10 text-slate-300 hover:text-amber-300 border border-[#2b3752] text-xs font-medium transition-colors"
            >
              <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
              Checkpoint Hint
            </button>

            <button
              type="button"
              onClick={() => setShowSolution(!showSolution)}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#1a2133] hover:bg-indigo-600/20 text-slate-300 hover:text-white border border-[#2b3752] text-xs font-medium transition-colors"
            >
              {showSolution ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              {showSolution ? "Hide Solution" : "Reveal Step-by-Step Breakdown"}
            </button>
          </div>

          {/* Answer Verdict & Diagnostics Banner */}
          {lastCheck && (
            <div
              className={`p-3.5 rounded-xl border mb-4 text-xs md:text-sm ${
                lastCheck.verdict === "correct"
                  ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-200"
                  : lastCheck.verdict === "partial"
                  ? "bg-amber-950/40 border-amber-500/40 text-amber-200"
                  : "bg-rose-950/40 border-rose-500/40 text-rose-200"
              }`}
            >
              <div className="flex items-center gap-2 font-semibold mb-1">
                {lastCheck.verdict === "correct" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : lastCheck.verdict === "partial" ? (
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400" />
                )}
                <span>{lastCheck.message}</span>
              </div>

              {lastCheck.components && lastCheck.components.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t border-slate-700/50">
                  {lastCheck.components.map((c, i) => (
                    <span
                      key={i}
                      className={`text-xs px-2 py-0.5 rounded font-mono ${
                        c.ok
                          ? "bg-emerald-900/60 text-emerald-300 border border-emerald-700/50"
                          : "bg-rose-900/60 text-rose-300 border border-rose-700/50"
                      }`}
                    >
                      {c.label}: {c.ok ? "PASS" : "FAIL"}
                    </span>
                  ))}
                </div>
              )}

              {lastCheck.diagnostics && lastCheck.diagnostics.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-700/50 text-xs text-slate-300 space-y-1">
                  {lastCheck.diagnostics.map((d, i) => (
                    <div key={i} className="flex items-start gap-1.5">
                      <span className="font-mono text-amber-400 uppercase font-semibold">
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
        <div className="bg-[#141b2b] border border-amber-500/30 rounded-xl p-3.5 mb-4 text-xs md:text-sm text-amber-200">
          <strong className="text-amber-400 font-semibold block mb-1">
            Mental Model Checkpoint:
          </strong>
          <FormattedText text={problem.checkpointHint} />
        </div>
      )}

      {/* Step-by-Step Breakdown or Canonical Solution */}
      {showSolution && (
        <div className="bg-[#0e121a] border border-[#263147] rounded-xl p-4 mb-4">
          <div className="flex justify-between items-center mb-3 pb-2 border-b border-[#1f273b]">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              {isKata ? "Canonical Reference Solution" : "Step-by-Step Runtime Breakdown"}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Verified Target:{" "}
              <strong className="text-emerald-400">{problem.answerDisplay}</strong>
            </span>
          </div>

          {isKata && problem.solutionCode ? (
            <div className="p-3 bg-[#151924] border border-[#232b3d] rounded-lg">
              <pre className="text-xs md:text-sm font-mono text-emerald-300 overflow-x-auto whitespace-pre">
                <code>{problem.solutionCode}</code>
              </pre>
            </div>
          ) : (
            <div className="space-y-3">
              {problem.steps.map((st, sIdx) => {
                const isDiverged = problem.state.divergedStep === sIdx;
                const isActive = activeStep === sIdx;

                return (
                  <div
                    key={sIdx}
                    onClick={() => onToggleStepHighlight(sIdx)}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      isDiverged
                        ? "bg-rose-950/30 border-rose-500/50"
                        : isActive
                        ? "bg-indigo-950/40 border-indigo-400 ring-1 ring-indigo-500/40"
                        : "bg-[#141925] border-[#222a3d] hover:border-slate-600"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-xs font-bold text-indigo-300 font-mono">
                        Phase {sIdx + 1}:
                      </span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onMarkDivergedStep(sIdx);
                        }}
                        className={`text-[11px] px-2 py-0.5 rounded transition-colors ${
                          isDiverged
                            ? "bg-rose-500 text-white font-semibold"
                            : "text-slate-400 hover:text-rose-300 bg-[#1e2538]"
                        }`}
                      >
                        {isDiverged ? "Marked as Diverged" : "Mark as where I diverged"}
                      </button>
                    </div>
                    <p className="text-xs md:text-sm text-slate-200 leading-relaxed">
                      <FormattedText text={st.explain} />
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Manual Scoring and Mistake Tagging */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#263147] text-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400 mr-1">Score:</span>
          {[
            { val: 1, label: "1.0 (Full)", cls: "bg-emerald-600 hover:bg-emerald-500 text-white" },
            { val: 0.5, label: "0.5 (Half)", cls: "bg-amber-600 hover:bg-amber-500 text-white" },
            { val: 0, label: "0 (Miss)", cls: "bg-rose-600 hover:bg-rose-500 text-white" },
          ].map((btn) => (
            <button
              key={btn.val}
              type="button"
              onClick={() => onSetScore(btn.val)}
              className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                score === btn.val
                  ? "ring-2 ring-white " + btn.cls
                  : "bg-[#1b2234] text-slate-400 hover:text-white"
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>

        {/* Mistake Category Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-slate-400 mr-1">Mistake Tags:</span>
          {mistakeTags.map((t) => {
            const hasTag = problem.state.mistakes.includes(t.id);
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => onToggleMistakeTag(t.id)}
                className={`px-2 py-0.5 rounded-full text-[11px] font-medium border transition-colors ${
                  hasTag
                    ? "bg-rose-500/20 text-rose-300 border-rose-500/50 font-semibold"
                    : "bg-[#161d2c] text-slate-400 border-[#263147] hover:border-slate-500"
                }`}
              >
                {t.label}
              </button>
            );
          })}
        </div>
      </div>
    </article>
  );
};
