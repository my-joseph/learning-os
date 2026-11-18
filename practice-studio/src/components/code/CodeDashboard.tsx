"use client";

import React, { useState, useEffect } from "react";
import { Reveal } from "@/components/motion/Reveal";
import {
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Copy,
  Flag,
  Loader2,
  PenLine,
  RotateCcw,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import {
  Problem,
  MistakeTag,
  CheckResult,
  TestRunReport,
} from "@/types/drill";
import { VSCodeBlock } from "@/components/VSCodeBlock";
import { FormattedText } from "@/components/FormattedText";
import { canShowReferenceSolution } from "@/lib/reviewGuard";
import {
  getPrgScore,
  getReviewRequest,
  hasCheckpointHint,
  isContextSlug,
} from "@/lib/studioRules";
import {
  choosePrimaryAction,
  deriveCodeStatus,
  isWorkspaceProblem,
  LayerCheckStatus,
  resolveIdeLinks,
  ReviewRunResult,
  ReviewStatus,
} from "@/lib/codeStatus";

export interface CodeDashboardProps {
  problem: Problem;
  drillId?: string;
  index: number;
  totalQuestions?: number;
  drillTitle?: string;
  labReadme?: string;
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  onInputChange: (val: string) => void;
  onCheckAnswer: () => Promise<void> | void;
  onSkip?: () => void;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number | null) => void;
  onTestReportChange?: (report: TestRunReport) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
  onResetProblem: () => void;
  onHintRevealed?: () => void;
  onSetupRevealed?: () => void;
  onSolutionRevealed?: () => void;
  onPrevQuestion?: () => void;
  onNextQuestion?: () => void;
  onOpenReview?: () => void;
}

const DEFAULT_EXPLAIN_QUESTION =
  "Why does your solution work, and what input or change would break a weaker version?";

const getSafePlaceholder = (hint?: string, problem?: Problem): string => {
  if (problem?.placeholder) return problem.placeholder;
  return hint || "Enter predicted terminal output (press Enter to check)...";
};

function statusSymbolColor(status: LayerCheckStatus | ReviewStatus): string {
  if (status === "pass") {
    return "text-emerald-700 dark:text-emerald-400 font-semibold";
  }
  if (status === "fail" || status === "revise") {
    return "text-rose-600 dark:text-rose-400 font-semibold";
  }
  return "text-zinc-400 dark:text-zinc-500";
}

function formatReviewDate(iso?: string): string {
  if (!iso) return "";
  const trimmed = iso.trim();
  if (trimmed.length >= 16 && trimmed.includes("T")) {
    return trimmed.slice(0, 16).replace("T", " ");
  }
  return trimmed;
}

/** Clean Programming workspace dashboard following docs/studio_design.md. */
export const CodeDashboard: React.FC<CodeDashboardProps> = ({
  problem,
  drillId = "",
  index,
  totalQuestions,
  drillTitle,
  labReadme,
  mistakeTags,
  activeStep,
  onInputChange,
  onCheckAnswer,
  onSkip,
  onToggleStepHighlight,
  onMarkDivergedStep,
  onSetScore,
  onTestReportChange,
  onToggleMistakeTag,
  onMistakeNoteChange,
  onResetProblem,
  onHintRevealed,
  onSolutionRevealed,
  onPrevQuestion,
  onNextQuestion,
  onOpenReview,
}) => {
  const isLab = drillId.startsWith("LAB-") || /^M\d+$/i.test(problem.id);
  const isKata = isLab || isWorkspaceProblem(problem);
  const referenceAllowed = canShowReferenceSolution(problem.state);
  const { filename, vscodeFolderUrl, cursorFolderUrl, vscodeUrl } = resolveIdeLinks(problem);

  const [userCode, setUserCode] = useState<string>(
    problem.state?.userCode || problem.starterCode || problem.codeSnippet || ""
  );
  const [testReport, setTestReport] = useState<TestRunReport | null>(
    problem.state?.lastTestReport || null
  );
  const [reviewRun, setReviewRun] = useState<ReviewRunResult | null>(null);
  const [checkError, setCheckError] = useState<string | null>(null);
  const [isRunningChecks, setIsRunningChecks] = useState(false);
  const [copiedReview, setCopiedReview] = useState(false);

  // Collapsible sections (closed by default)
  const [openHistory, setOpenHistory] = useState(false);
  const [openExplain, setOpenExplain] = useState(false);
  const [openReference, setOpenReference] = useState(false);
  const [showHint, setShowHint] = useState(false);

  // In-browser question state
  const [isChecking, setIsChecking] = useState(false);
  const [showSolution, setShowSolution] = useState(Boolean(problem.state.lastCheck));
  const [revealedSolutionCode, setRevealedSolutionCode] = useState<string | undefined>(
    problem.solutionCode
  );
  const [isLoadingReference, setIsLoadingReference] = useState(false);

  useEffect(() => {
    setUserCode(problem.state?.userCode || problem.starterCode || problem.codeSnippet || "");
    setTestReport(problem.state?.lastTestReport || null);
    setReviewRun(null);
    setCheckError(null);
    setOpenHistory(false);
    setOpenExplain(false);
    setOpenReference(false);
    setShowHint(false);
    setShowSolution(Boolean(problem.state.lastCheck));
    setRevealedSolutionCode(problem.solutionCode);
  }, [
    problem.id,
    problem.state?.userCode,
    problem.starterCode,
    problem.codeSnippet,
    problem.state?.lastTestReport,
    problem.state.lastCheck,
    problem.solutionCode,
  ]);

  const effectiveState = {
    ...problem.state,
    lastTestReport: testReport ?? problem.state?.lastTestReport ?? null,
  };

  const layeredStatus = deriveCodeStatus(effectiveState, reviewRun, filename);
  const primaryAction = choosePrimaryAction(layeredStatus, drillId, problem.id);
  const reviewRequestText = getReviewRequest(drillId, problem.id);

  const isLastQuestion =
    typeof totalQuestions === "number" && totalQuestions > 0 && index === totalQuestions - 1;

  const ensureWorkspaceOnDisk = () => {
    if (!drillId || isLab) return;
    void fetch("/api/workspace", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ drillId }),
    }).catch(() => {});
  };

  const handleRunChecks = async () => {
    setIsRunningChecks(true);
    setCheckError(null);
    try {
      let latestCode = userCode;
      if (problem.workspaceFile && drillId && !isLab) {
        const materializeRes = await fetch("/api/workspace", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ drillId }),
        });
        if (!materializeRes.ok) {
          throw new Error("Could not create the local workspace.");
        }
        const diskRes = await fetch(
          `/api/workspace?file=${encodeURIComponent(problem.workspaceFile)}&drillId=${encodeURIComponent(drillId)}`
        );
        if (diskRes.ok) {
          const diskData = await diskRes.json();
          if (typeof diskData.content === "string") {
            latestCode = diskData.content;
            setUserCode(latestCode);
          }
        } else if (!drillId) {
          throw new Error("Could not read the workspace file from disk.");
        }
      }

      let reviewRunData: ReviewRunResult | null = null;
      if (drillId) {
        const revRes = await fetch("/api/review-run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ drillId, problemId: problem.id }),
        });
        const revJson = await revRes.json();
        if (!revRes.ok) {
          throw new Error(revJson.error || "Could not run checks.");
        }
        reviewRunData = revJson as ReviewRunResult;
        setReviewRun(reviewRunData);
      }

      if (!isLab) {
        const res = await fetch("/api/run-tests", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            drillId,
            problemId: problem.id,
            userCode: problem.workspaceFile ? undefined : latestCode,
            workspaceFile: problem.workspaceFile,
          }),
        });

        if (res.ok) {
          const report: TestRunReport = await res.json();
          setTestReport(report);
          onTestReportChange?.(report);
          onSetScore(getPrgScore(report, problem.state.reviews));
          return;
        }
      }

      if (reviewRunData?.tests) {
        const t = reviewRunData.tests;
        const allPassed = t.total > 0 && t.passed === t.total && t.failed.length === 0;
        const fallbackReport: TestRunReport = {
          allPassed,
          score: t.total > 0 ? t.passed / t.total : 0,
          passedCount: t.passed,
          totalCount: t.total,
          visibleResults: t.failed.map((name) => ({ name, passed: false })),
          hiddenPassed: 0,
          hiddenTotal: problem.hiddenTestCount ?? 0,
          executionTimeMs: 0,
        };
        setTestReport(fallbackReport);
        onTestReportChange?.(fallbackReport);
        onSetScore(getPrgScore(fallbackReport, problem.state.reviews));
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setCheckError(errMsg);
    } finally {
      setIsRunningChecks(false);
    }
  };

  const handleCopyReviewRequest = () => {
    void navigator.clipboard.writeText(reviewRequestText);
    setCopiedReview(true);
    setTimeout(() => setCopiedReview(false), 1500);
  };

  const handleNextProblem = () => {
    if (isLastQuestion && onOpenReview) {
      onOpenReview();
    } else if (onNextQuestion) {
      onNextQuestion();
    }
  };

  const handleToggleReference = async () => {
    const nextOpen = !openReference;
    setOpenReference(nextOpen);
    if (
      nextOpen &&
      referenceAllowed &&
      !problem.solutionCode &&
      !revealedSolutionCode &&
      drillId
    ) {
      setIsLoadingReference(true);
      try {
        const res = await fetch(
          `/api/reveal?drill=${encodeURIComponent(drillId)}&q=${encodeURIComponent(problem.id)}&part=solution`
        );
        if (res.ok) {
          const data = await res.json();
          if (typeof data.solutionCode === "string") {
            setRevealedSolutionCode(data.solutionCode);
          }
        }
      } catch {
        // ignore transient reveal error
      } finally {
        setIsLoadingReference(false);
      }
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

  const score = problem.state.score;
  const lastCheck: CheckResult | null | undefined = problem.state.lastCheck;
  const isFindBug =
    problem.codeType === "find-bug" || problem.answerSpec?.type === "line_number";
  const selectedLineNumber = isFindBug
    ? parseInt(problem.state.userInput.replace(/\D/g, ""), 10) || null
    : null;

  const reviews = problem.state.reviews || [];
  const latestPassingReview = [...reviews].reverse().find((r) => r.verdict === "pass");
  const latestReview = reviews.length > 0 ? reviews[reviews.length - 1] : undefined;
  const explainSource = latestPassingReview || latestReview;
  const explainQuestion =
    explainSource?.explainQuestion?.trim() || DEFAULT_EXPLAIN_QUESTION;
  const recordedExplain = explainSource?.explain?.trim() || null;

  const hasAttempt = Boolean(
    testReport ||
      reviewRun ||
      reviews.length > 0 ||
      problem.state.lastCheck ||
      problem.state.skipped ||
      (problem.state.attempts && problem.state.attempts.length > 0) ||
      problem.state.score !== null
  );

  const snippetInPrompt =
    Boolean(problem.codeSnippet) &&
    Boolean(problem.prompt) &&
    problem.prompt.includes(problem.codeSnippet!.trim().slice(0, 32));

  return (
    <div className="mx-auto w-full max-w-[720px] space-y-4">
      {drillTitle && (
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight px-0.5">
          {drillTitle}
        </h1>
      )}

      <article className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-6">
        {/* 1. Brief: problem/milestone title + prompt (text-lg), then Visible tests */}
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2 text-sm font-medium text-zinc-500 dark:text-zinc-400">
            <h2 className="flex flex-wrap items-center gap-2">
              <span>
                {isLab ? `Milestone ${problem.id}` : `Problem ${index + 1}`}
                {typeof totalQuestions === "number" && totalQuestions > 0
                  ? isLab
                    ? ` (${index + 1} of ${totalQuestions})`
                    : ` of ${totalQuestions}`
                  : ""}
              </span>
              {problem.entryPoint && (
                <>
                  <span aria-hidden="true">·</span>
                  {isLab ? (
                    <span className="text-zinc-700 dark:text-zinc-300">
                      {problem.entryPoint}
                    </span>
                  ) : (
                    <code className="font-mono text-zinc-700 dark:text-zinc-300">
                      {problem.entryPoint}
                    </code>
                  )}
                </>
              )}
              {!problem.entryPoint &&
                problem.context &&
                !isContextSlug(problem.context) && (
                  <>
                    <span aria-hidden="true">·</span>
                    <span className="text-zinc-700 dark:text-zinc-300">
                      <FormattedText text={problem.context} />
                    </span>
                  </>
                )}
            </h2>
          </div>

          <div className="text-lg leading-relaxed text-zinc-900 dark:text-zinc-100">
            <FormattedText text={problem.prompt} />
          </div>
        </div>

        {isKata ? (
          <>
            {problem.codeSnippet && !snippetInPrompt && (
              <VSCodeBlock
                code={problem.codeSnippet}
                language={problem.language || "javascript"}
                filename={filename}
              />
            )}

            {/* Visible tests: compact read-only list (names/descriptions + test command for labs) */}
            {((problem.visibleTests && problem.visibleTests.length > 0) ||
              (problem.visibleTestFiles && problem.visibleTestFiles.length > 0)) && (
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
                    Visible tests
                  </h3>
                  {(problem.visibleTestFiles?.length || problem.testCommand) && (
                    <span className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
                      {[
                        ...(problem.visibleTestFiles || []),
                        ...(problem.testCommand ? [problem.testCommand] : []),
                      ].join(" · ")}
                    </span>
                  )}
                </div>
                {problem.visibleTests && problem.visibleTests.length > 0 && (
                  <ul className="space-y-1 text-sm text-zinc-700 dark:text-zinc-300">
                    {problem.visibleTests.map((t, idx) => (
                      <li key={t.id || idx} className="flex items-baseline gap-2">
                        <span
                          className="text-zinc-400 dark:text-zinc-500 font-mono text-xs select-none"
                          aria-hidden="true"
                        >
                          •
                        </span>
                        <span>
                          <FormattedText text={t.name} />
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* 2. Status line: Tests · Lint · Types · Review */}
            <div className="space-y-2.5">
              <div
                role="status"
                aria-label="Check and review status"
                className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm font-mono py-2.5 px-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800"
              >
                <span>
                  <span className="text-zinc-600 dark:text-zinc-400">Tests </span>
                  <span className={statusSymbolColor(layeredStatus.tests)}>
                    {layeredStatus.testsSymbol}
                  </span>
                  {layeredStatus.testsCount && layeredStatus.tests !== "not_run" && (
                    <span className="text-xs text-zinc-500 dark:text-zinc-400 ml-1">
                      ({layeredStatus.testsCount.passed}/{layeredStatus.testsCount.total})
                    </span>
                  )}
                </span>
                <span className="text-zinc-300 dark:text-zinc-700" aria-hidden="true">
                  ·
                </span>
                <span>
                  <span className="text-zinc-600 dark:text-zinc-400">Lint </span>
                  <span className={statusSymbolColor(layeredStatus.lint)}>
                    {layeredStatus.lintSymbol}
                  </span>
                </span>
                <span className="text-zinc-300 dark:text-zinc-700" aria-hidden="true">
                  ·
                </span>
                <span>
                  <span className="text-zinc-600 dark:text-zinc-400">Types </span>
                  <span className={statusSymbolColor(layeredStatus.types)}>
                    {layeredStatus.typesSymbol}
                  </span>
                </span>
                <span className="text-zinc-300 dark:text-zinc-700" aria-hidden="true">
                  ·
                </span>
                <span>
                  <span className="text-zinc-600 dark:text-zinc-400">Review </span>
                  <span className={statusSymbolColor(layeredStatus.review)}>
                    {layeredStatus.reviewSymbol}
                  </span>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400 ml-1">
                    ({layeredStatus.reviewLabel})
                  </span>
                </span>
              </div>

              {(checkError || layeredStatus.failures.length > 0) && (
                <ul
                  aria-label="Check failures"
                  className="border-l-2 border-rose-600 dark:border-rose-400 pl-3.5 py-1 space-y-1 font-mono text-xs text-zinc-800 dark:text-zinc-200"
                >
                  {checkError && <li>{checkError}</li>}
                  {layeredStatus.failures.map((line, idx) => (
                    <li key={idx}>{line}</li>
                  ))}
                </ul>
              )}
            </div>

            {/* 3. One primary action + Secondary text buttons */}
            <div className="space-y-2.5">
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                {primaryAction.kind === "open_vscode" && (
                  <a
                    href={vscodeFolderUrl || "#"}
                    onClick={ensureWorkspaceOnDisk}
                    className="inline-flex items-center justify-center gap-2 h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-400 text-white text-sm font-semibold transition-colors"
                  >
                    <span>Open in VS Code</span>
                  </a>
                )}

                {primaryAction.kind === "copy_review" && (
                  <button
                    type="button"
                    onClick={handleCopyReviewRequest}
                    className="inline-flex items-center justify-center gap-2 h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-400 text-white text-sm font-semibold transition-colors"
                  >
                    {copiedReview ? (
                      <>
                        <Check className="w-4 h-4" />
                        <span>Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        <span>Copy review request</span>
                      </>
                    )}
                  </button>
                )}

                {primaryAction.kind === "next_problem" && (
                  <button
                    type="button"
                    onClick={handleNextProblem}
                    className="inline-flex items-center justify-center gap-2 h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-400 text-white text-sm font-semibold transition-colors"
                  >
                    <span>Next problem</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                )}

                {/* Secondary text buttons */}
                <button
                  type="button"
                  onClick={handleRunChecks}
                  disabled={isRunningChecks}
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 disabled:opacity-50 transition-colors"
                >
                  {isRunningChecks ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Running checks…</span>
                    </>
                  ) : (
                    <span>Run checks</span>
                  )}
                </button>

                {cursorFolderUrl && (
                  <a
                    href={cursorFolderUrl}
                    onClick={ensureWorkspaceOnDisk}
                    className="inline-flex items-center gap-1 text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
                  >
                    <span>Open in Cursor</span>
                  </a>
                )}

                {primaryAction.kind !== "open_vscode" && vscodeFolderUrl && (
                  <a
                    href={vscodeFolderUrl}
                    onClick={ensureWorkspaceOnDisk}
                    className="inline-flex items-center gap-1 text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
                  >
                    <span>Open in VS Code</span>
                  </a>
                )}

                {vscodeUrl && problem.mainFile && (
                  <a
                    href={vscodeUrl}
                    className="inline-flex items-center gap-1 text-sm font-mono text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
                  >
                    <span>Open {problem.mainFile}</span>
                  </a>
                )}

                {hasCheckpointHint(problem.checkpointHint) && <button
                  type="button"
                  onClick={() => {
                    if (!showHint && onHintRevealed) {
                      onHintRevealed();
                    }
                    setShowHint(!showHint);
                  }}
                  aria-expanded={showHint}
                  className="inline-flex items-center gap-1 text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
                >
                  <span>{showHint ? "Hide hint" : "Hint"}</span>
                </button>}
              </div>

              {primaryAction.kind === "copy_review" && drillId && (
                <div className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
                  {reviewRequestText}
                </div>
              )}

              <Reveal show={Boolean(showHint && hasCheckpointHint(problem.checkpointHint))}>
              {showHint && hasCheckpointHint(problem.checkpointHint) && (
                <div className="border-l-2 border-amber-600 dark:border-amber-400 pl-3.5 py-1 text-sm text-zinc-700 dark:text-zinc-300">
                  <FormattedText text={problem.checkpointHint} />
                </div>
              )}
              </Reveal>
            </div>

            {/* 5. Collapsible sections (closed by default): Review history, Explain, Reference */}
            <div className="divide-y divide-zinc-200 dark:divide-zinc-800 border-t border-zinc-200 dark:border-zinc-800">
              {/* Review history */}
              <div className="py-2.5">
                <button
                  type="button"
                  onClick={() => setOpenHistory(!openHistory)}
                  aria-expanded={openHistory}
                  className="w-full flex items-center justify-between text-left text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 py-1 transition-colors"
                >
                  <span>
                    Review history
                    {reviews.length > 0 ? ` (${reviews.length})` : ""}
                  </span>
                  <ChevronDown className={`w-4 h-4 text-zinc-400 transition-transform duration-200 ${openHistory ? "rotate-180" : ""}`} />
                </button>
                <Reveal show={Boolean(openHistory)}>
                {openHistory && (
                  <div className="pt-2 pb-1 space-y-3 text-sm text-zinc-600 dark:text-zinc-400">
                    {reviews.length === 0 ? (
                      <p className="text-zinc-500 dark:text-zinc-400">
                        No reviews recorded yet.
                      </p>
                    ) : (
                      reviews.map((r, rIdx) => (
                        <div
                          key={r.attempt || rIdx}
                          className={`border-l-2 pl-3 py-0.5 space-y-1 ${
                            r.verdict === "pass"
                              ? "border-emerald-700 dark:border-emerald-400"
                              : "border-rose-600 dark:border-rose-400"
                          }`}
                        >
                          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                            <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                              #{r.attempt ?? rIdx + 1} {r.verdict}
                            </span>
                            {r.at && (
                              <span className="text-zinc-500 dark:text-zinc-400">
                                {formatReviewDate(r.at)}
                              </span>
                            )}
                            {r.tests && (
                              <span className="text-zinc-500 dark:text-zinc-400">
                                tests {r.tests.passed}/{r.tests.total}
                              </span>
                            )}
                          </div>
                          {r.findings && r.findings.length > 0 ? (
                            <ul className="space-y-1 text-xs text-zinc-700 dark:text-zinc-300 font-mono">
                              {r.findings.map((f, fIdx) => (
                                <li key={fIdx}>
                                  {f.check} ({f.severity}
                                  {f.line ? `, line ${f.line}` : ""}
                                  {f.disputed ? ", disputed" : ""}): {f.note}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-xs text-zinc-500 dark:text-zinc-400">
                              No rubric findings.
                            </p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}
                </Reveal>
              </div>

              {/* Explain */}
              <div className="py-2.5">
                <button
                  type="button"
                  onClick={() => setOpenExplain(!openExplain)}
                  aria-expanded={openExplain}
                  className="w-full flex items-center justify-between text-left text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 py-1 transition-colors"
                >
                  <span>Explain</span>
                  <ChevronDown className={`w-4 h-4 text-zinc-400 transition-transform duration-200 ${openExplain ? "rotate-180" : ""}`} />
                </button>
                <Reveal show={Boolean(openExplain)}>
                {openExplain && (
                  <div className="pt-2 pb-1 space-y-2 text-sm">
                    <p className="text-zinc-700 dark:text-zinc-300">
                      <FormattedText text={explainQuestion} />
                    </p>
                    {recordedExplain ? (
                      <div className="border-l-2 border-emerald-700 dark:border-emerald-400 pl-3 py-0.5 text-zinc-800 dark:text-zinc-200">
                        <FormattedText text={recordedExplain} />
                      </div>
                    ) : (
                      <p className="text-xs text-zinc-500 dark:text-zinc-400">
                        Answer through the review-code skill after your review passes.
                      </p>
                    )}
                  </div>
                )}
                </Reveal>
              </div>

              {/* Reference (drills) or Lab README (labs; _reference is never served) */}
              {isLab ? (
                labReadme ? (
                  <div className="py-2.5">
                    <button
                      type="button"
                      onClick={() => setOpenReference(!openReference)}
                      aria-expanded={openReference}
                      className="w-full flex items-center justify-between text-left text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 py-1 transition-colors"
                    >
                      <span>Lab README</span>
                      <ChevronDown className={`w-4 h-4 text-zinc-400 transition-transform duration-200 ${openReference ? "rotate-180" : ""}`} />
                    </button>
                    <Reveal show={Boolean(openReference)}>
                    {openReference && (
                      <div className="pt-2 pb-1 text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed">
                        <FormattedText text={labReadme} />
                      </div>
                    )}
                    </Reveal>
                  </div>
                ) : null
              ) : (
                <div className="py-2.5">
                  <button
                    type="button"
                    onClick={handleToggleReference}
                    aria-expanded={openReference}
                    className="w-full flex items-center justify-between text-left text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 py-1 transition-colors"
                  >
                    <span>Reference</span>
                    <span className="inline-flex items-center gap-2">
                      {!referenceAllowed && (
                        <span className="text-xs font-normal text-zinc-500 dark:text-zinc-400">
                          Unlocks after review passes
                        </span>
                      )}
                      <ChevronDown className={`w-4 h-4 text-zinc-400 transition-transform duration-200 ${openReference ? "rotate-180" : ""}`} />
                    </span>
                  </button>
                  <Reveal show={Boolean(openReference)}>
                  {openReference && (
                    <div className="pt-2 pb-1">
                      {!referenceAllowed ? (
                        <p className="text-sm text-zinc-500 dark:text-zinc-400">
                          Unlocks after review passes
                        </p>
                      ) : isLoadingReference ? (
                        <p className="text-sm text-zinc-500 dark:text-zinc-400">
                          Loading reference…
                        </p>
                      ) : problem.solutionCode || revealedSolutionCode ? (
                        <VSCodeBlock
                          code={(problem.solutionCode || revealedSolutionCode)!}
                          language={problem.language || "javascript"}
                          filename={`reference-${filename}`}
                        />
                      ) : (
                        <p className="text-sm text-zinc-500 dark:text-zinc-400">
                          Reference solution unavailable.
                        </p>
                      )}
                    </div>
                  )}
                  </Reveal>
                </div>
              )}
            </div>
          </>
        ) : (
          /* =================================================================== */
          /* In-browser PRG problem types (predict_output / choice / line_number)*/
          /* =================================================================== */
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

            {problem.answerSpec.type === "choice" && problem.answerSpec.options && (
              <div className="grid grid-cols-1 gap-2">
                {problem.answerSpec.options.map((opt) => {
                  const isSelected = problem.state.userInput === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => onInputChange(opt.id)}
                      className={`w-full text-left p-3.5 rounded-xl border transition-colors flex items-start gap-3 ${
                        isSelected
                          ? "bg-zinc-100 dark:bg-zinc-800 border-indigo-600 dark:border-indigo-500 text-zinc-900 dark:text-zinc-100"
                          : "bg-zinc-50 dark:bg-zinc-950 hover:border-zinc-400 dark:hover:border-zinc-600 border-zinc-200 dark:border-zinc-800 text-zinc-800 dark:text-zinc-200"
                      }`}
                    >
                      <span
                        className={`inline-flex items-center justify-center w-6 h-6 rounded-md text-xs font-mono font-semibold shrink-0 ${
                          isSelected
                            ? "bg-indigo-600 dark:bg-indigo-500 text-white"
                            : "bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-800"
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
            )}

            <div className="space-y-3">
              <div className="flex items-center gap-2.5">
                {!isFindBug && problem.answerSpec.type !== "choice" && (
                  <input
                    type="text"
                    value={problem.state.userInput}
                    onChange={(e) => onInputChange(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        void triggerWebCheck();
                      }
                    }}
                    placeholder={getSafePlaceholder(problem.inputHint, problem)}
                    aria-label={`Answer for question ${problem.id}`}
                    className="flex-1 min-w-0 h-11 font-mono text-sm bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 border border-zinc-300 dark:border-zinc-700 rounded-xl px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-600/25 dark:focus:ring-indigo-500/30 focus:border-indigo-600 dark:focus:border-indigo-500 placeholder:text-zinc-400 dark:placeholder:text-zinc-500"
                  />
                )}

                <button
                  type="button"
                  onClick={triggerWebCheck}
                  disabled={isChecking || !problem.state.userInput.trim()}
                  className="inline-flex items-center justify-center gap-2 h-11 px-5 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-400 disabled:opacity-40 text-white text-sm font-semibold transition-colors shrink-0"
                >
                  {isChecking ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Checking…</span>
                    </>
                  ) : (
                    <span>
                      {isFindBug && selectedLineNumber
                        ? `Check Line ${selectedLineNumber}`
                        : "Check"}
                    </span>
                  )}
                </button>
              </div>

              <Reveal show={Boolean(lastCheck)}>
              {lastCheck && (
                <div
                  role="status"
                  className={`border-l-2 pl-3.5 py-1 space-y-1.5 text-sm ${
                    lastCheck.verdict === "correct"
                      ? "border-emerald-700 dark:border-emerald-400"
                      : lastCheck.verdict === "partial" ||
                        problem.state.skipped ||
                        (lastCheck.verdict as string) === "skipped"
                      ? "border-amber-600 dark:border-amber-400"
                      : "border-rose-600 dark:border-rose-400"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {lastCheck.verdict === "correct" ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-700 dark:text-emerald-400 shrink-0 mt-0.5" />
                    ) : lastCheck.verdict === "partial" ||
                      problem.state.skipped ||
                      (lastCheck.verdict as string) === "skipped" ? (
                      <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
                    )}
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">
                      <FormattedText text={lastCheck.message} />
                    </span>
                  </div>

                  {lastCheck.components && lastCheck.components.length > 0 && (
                    <div className="flex flex-wrap gap-3 pl-6">
                      {lastCheck.components.map((c, i) => (
                        <span
                          key={i}
                          className={`text-xs font-mono ${
                            c.ok
                              ? "text-emerald-700 dark:text-emerald-400"
                              : "text-rose-600 dark:text-rose-400"
                          }`}
                        >
                          <FormattedText text={c.label} />: {c.ok ? "✓" : "✗"}
                        </span>
                      ))}
                    </div>
                  )}

                  {lastCheck.diagnostics && lastCheck.diagnostics.length > 0 && (
                    <div className="pl-6 text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
                      {lastCheck.diagnostics.map((d, i) => (
                        <div key={i}>
                          <FormattedText text={d.message} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              </Reveal>
            </div>

            <div className="space-y-3 pt-1">
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-zinc-500 dark:text-zinc-400">
                {hasAttempt && (
                  <button
                    type="button"
                    onClick={onResetProblem}
                    className="inline-flex items-center gap-1.5 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Try again</span>
                  </button>
                )}

                {hasCheckpointHint(problem.checkpointHint) && <button
                  type="button"
                  onClick={() => {
                    if (!showHint && onHintRevealed) {
                      onHintRevealed();
                    }
                    setShowHint(!showHint);
                  }}
                  aria-expanded={showHint}
                  className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
                >
                  <span>{showHint ? "Hide hint" : "Hint"}</span>
                </button>}

                <button
                  type="button"
                  onClick={() => {
                    if (!showSolution && onSolutionRevealed) {
                      onSolutionRevealed();
                    }
                    setShowSolution(!showSolution);
                  }}
                  aria-expanded={showSolution}
                  className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
                >
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${showSolution ? "rotate-180" : ""}`} />
                  <span>{showSolution ? "Hide steps" : "Show steps"}</span>
                </button>

                {onSkip && !hasAttempt && (
                  <button
                    type="button"
                    onClick={() => {
                      if (!showHint && onHintRevealed) {
                        onHintRevealed();
                      }
                      setShowHint(true);
                      setShowSolution(true);
                      onSkip();
                    }}
                    className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors ml-auto"
                  >
                    <span>Skip</span>
                  </button>
                )}
              </div>

              <Reveal show={Boolean(showHint && hasCheckpointHint(problem.checkpointHint))}>
              {showHint && hasCheckpointHint(problem.checkpointHint) && (
                <div className="border-l-2 border-amber-600 dark:border-amber-400 pl-3.5 py-1 text-sm text-zinc-700 dark:text-zinc-300">
                  <FormattedText text={problem.checkpointHint} />
                </div>
              )}
              </Reveal>

              <Reveal show={Boolean(showSolution)}>
              {showSolution && (
                <div className="bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-2.5">
                  {(problem.steps || []).map((st, sIdx) => {
                    const isDiverged = problem.state.divergedStep === sIdx;
                    const isActive = activeStep === sIdx;
                    return (
                      <div
                        key={sIdx}
                        onClick={() => onToggleStepHighlight(sIdx)}
                        className={`p-3 rounded-xl border cursor-pointer transition-colors ${
                          isDiverged
                            ? "border-rose-600 dark:border-rose-400"
                            : isActive
                            ? "border-indigo-600 dark:border-indigo-500"
                            : "bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
                            Step {sIdx + 1}
                          </span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              onMarkDivergedStep(sIdx);
                            }}
                            className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border ${
                              isDiverged
                                ? "border-rose-600 dark:border-rose-400 text-rose-600 dark:text-rose-400 font-semibold"
                                : "border-zinc-200 dark:border-zinc-800 text-zinc-500 dark:text-zinc-400"
                            }`}
                          >
                            <Flag className="w-3 h-3 shrink-0" />
                            <span>
                              {isDiverged ? `Diverged at step ${sIdx + 1}` : "Mark diverged"}
                            </span>
                          </button>
                        </div>
                        <div className="text-sm text-zinc-800 dark:text-zinc-200 leading-relaxed">
                          <FormattedText text={st.explain} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
              </Reveal>
            </div>
          </>
        )}

        {/* Mistake tags & note after an attempt */}
        {hasAttempt && (
          <div className="pt-4 border-t border-zinc-200 dark:border-zinc-800 space-y-3 text-xs text-zinc-500 dark:text-zinc-400">
            <div className="flex flex-wrap items-center justify-between gap-3">
              {!isKata && (
                <div className="flex items-center gap-1.5">
                  <span className="mr-1">Self-score:</span>
                  {[
                    {
                      val: 1,
                      label: "1.0",
                      activeCls:
                        "border-emerald-700 dark:border-emerald-400 text-emerald-700 dark:text-emerald-400 font-semibold bg-zinc-50 dark:bg-zinc-950",
                    },
                    {
                      val: 0.5,
                      label: "0.5",
                      activeCls:
                        "border-amber-600 dark:border-amber-400 text-amber-600 dark:text-amber-400 font-semibold bg-zinc-50 dark:bg-zinc-950",
                    },
                    {
                      val: 0,
                      label: "0",
                      activeCls:
                        "border-rose-600 dark:border-rose-400 text-rose-600 dark:text-rose-400 font-semibold bg-zinc-50 dark:bg-zinc-950",
                    },
                  ].map((btn) => (
                    <button
                      key={btn.val}
                      type="button"
                      onClick={() => onSetScore(btn.val)}
                      className={`h-7 px-2.5 rounded-lg font-mono border transition-colors ${
                        score === btn.val
                          ? btn.activeCls
                          : "bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600"
                      }`}
                    >
                      {btn.label}
                    </button>
                  ))}
                </div>
              )}

              {mistakeTags.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="mr-1">Mistake:</span>
                  {mistakeTags.map((t) => {
                    const hasTag = problem.state.mistakes.includes(t.id);
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => onToggleMistakeTag(t.id)}
                        className={`min-h-[28px] py-1 px-2.5 rounded-full text-xs border transition-colors inline-flex items-center ${
                          hasTag
                            ? "border-rose-600 dark:border-rose-400 text-rose-700 dark:text-rose-300 bg-zinc-50 dark:bg-zinc-950 font-semibold"
                            : "bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600"
                        }`}
                      >
                        <FormattedText text={t.label} />
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-3 py-2">
              <PenLine className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
              <input
                type="text"
                value={problem.state.mistakeNote || ""}
                onChange={(e) => onMistakeNoteChange(e.target.value)}
                placeholder="Note what went wrong (optional)…"
                className="w-full bg-transparent text-xs text-zinc-800 dark:text-zinc-200 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:outline-none"
              />
            </div>
          </div>
        )}
      </article>

      {/* Quiet question navigation footer */}
      {(onPrevQuestion || onNextQuestion || onOpenReview) && (
        <div className="flex items-center justify-between px-1 text-sm text-zinc-500 dark:text-zinc-400">
          <button
            type="button"
            onClick={onPrevQuestion}
            disabled={index === 0}
            className="inline-flex items-center gap-1 py-1.5 hover:text-zinc-900 dark:hover:text-zinc-100 disabled:opacity-30 disabled:pointer-events-none transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          {isLastQuestion && onOpenReview ? (
            <button
              type="button"
              onClick={onOpenReview}
              className="inline-flex items-center gap-1 py-1.5 font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              <span>Review &amp; Sync</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={onNextQuestion}
              disabled={isLastQuestion}
              className="inline-flex items-center gap-1 py-1.5 hover:text-zinc-900 dark:hover:text-zinc-100 disabled:opacity-30 disabled:pointer-events-none transition-colors"
            >
              <span>Next</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}
    </div>
  );
};
