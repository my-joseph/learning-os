"use client";

import { Heading } from "@/components/ui/Heading";
import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Reveal } from "@/components/motion/Reveal";
import {
  ArrowUpRight,
  Check,
  ChevronDown,
  ChevronRight,
  Copy,
  Loader2,
} from "lucide-react";
import {
  Problem,
  MistakeTag,
  CheckResult,
  TestRunReport,
} from "@/types/drill";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { FormattedText } from "@/components/FormattedText";
import {
  getExtensionForLanguage,
  inferShikiLanguageFromFilename,
} from "@/lib/shiki";
import { AnswerResultCard } from "@/components/AnswerResultCard";
import { ChoiceOptionGroup } from "@/components/ChoiceOptionGroup";
import { QuestionTimer } from "@/components/QuestionTimer";
import {
  InlineCheckButton,
  PlainAnswerField,
} from "@/components/workspace/PlainAnswerField";
import {
  CheckpointHintDisclosure,
  ProblemAssistSection,
} from "@/components/workspace/ProblemAssistSection";
import { ProblemNavFooter } from "@/components/workspace/ProblemNavFooter";
import { ProblemSelfEval } from "@/components/workspace/ProblemSelfEval";
import { useChoiceController } from "@/components/workspace/useChoiceController";
import {
  canShowReferenceSolution,
  cycleReviews,
  hasSubstantiveAttempt,
} from "@/lib/reviewGuard";
import {
  isLockedAfterCorrect,
  maxAllowedSelfScore,
  scoreProblem,
} from "@/lib/scoring";
import { statusTone } from "@/lib/statusTone";
import { statusSymbolClass, type StatusSymbolKind } from "@/lib/statusSymbol";
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
  maskHiddenTestFailures,
  resolveIdeLinks,
  ReviewRunResult,
  sanitizeCodeCheckError,
} from "@/lib/codeStatus";
import { isCurriculumId, plainTitle } from "@/lib/titleText";
import { ListDot } from "@/components/ui/ListDot";
import { CopyButton } from "@/components/ui/CopyButton";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/shadcn/Collapsible";
import type { SkipOptions } from "@/hooks/types";

export interface CodeDashboardProps {
  problem: Problem;
  drillId?: string;
  index: number;
  totalQuestions?: number;
  drillTitle?: string;
  labReadme?: string;
  mistakeTags: MistakeTag[];
  onInputChange: (val: string) => void;
  onCheckAnswer: (inputOverride?: string) => Promise<void> | void;
  onSkip?: (opts?: SkipOptions) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number | null) => void;
  onTestReportChange?: (report: TestRunReport, score?: number | null) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
  onResetProblem: () => void;
  onHintRevealed?: () => void;
  onSolutionRevealed?: () => void;
  onPrevQuestion?: () => void;
  onNextQuestion?: () => void;
  onOpenReview?: () => void;
  questionTimerMs?: number;
  totalTimerMs?: number;
  isTimerPaused?: boolean;
  onToggleTimerPause?: () => void;
  openInDrillHref?: string;
  reviewSupplement?: React.ReactNode;
  isReviewSession?: boolean;
  isCorrectOnRetry?: boolean;
  reviewUnitTitle?: string;
  reviewScheduleNote?: string | null;
  nextCardLabel?: string;
  lastQuestionNavLabel?: string;
  initialExpandedVisibleTests?: number[];
  frameless?: boolean;
}

const DEFAULT_EXPLAIN_QUESTION =
  "Why does your solution work, and what input or change would break a weaker version?";

const getSafePlaceholder = (hint?: string, problem?: Problem): string => {
  if (problem?.placeholder) return problem.placeholder;
  return hint || "Enter predicted output…";
};

/** Vitest-style count: "1 failed | 13 passed (14)", or "13 passed (13)" when nothing failed. */
function formatTestCounts({ passed, total }: { passed: number; total: number }): string {
  const failed = total - passed;
  return `${failed > 0 ? `${failed} failed | ` : ""}${passed} passed (${total})`;
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
  onInputChange,
  onCheckAnswer,
  onSkip,
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
  questionTimerMs,
  totalTimerMs,
  isTimerPaused = false,
  onToggleTimerPause,
  openInDrillHref,
  reviewSupplement,
  isReviewSession = false,
  isCorrectOnRetry = false,
  reviewUnitTitle,
  reviewScheduleNote = null,
  nextCardLabel,
  lastQuestionNavLabel,
  initialExpandedVisibleTests,
  frameless = false,
}) => {
  const isLab = drillId.startsWith("LAB-") || /^M\d+$/i.test(problem.id);
  const isKata = isLab || isWorkspaceProblem(problem);
  const referenceAllowed = canShowReferenceSolution(problem.state);
  const { filename, vscodeFolderUrl, vscodeUrl } = resolveIdeLinks(problem);
  const snippetLanguage =
    problem.language || inferShikiLanguageFromFilename(filename) || "javascript";

  const [userCode, setUserCode] = useState<string>(
    problem.state?.userCode || problem.starterCode || problem.codeSnippet || ""
  );
  const [testReport, setTestReport] = useState<TestRunReport | null>(
    problem.state?.lastTestReport || null
  );
  const [reviewRun, setReviewRun] = useState<ReviewRunResult | null>(null);
  const [checkError, setCheckError] = useState<string | null>(null);
  const [isRunningChecks, setIsRunningChecks] = useState(false);

  // Collapsible sections (closed by default)
  const [openHistory, setOpenHistory] = useState(false);
  const [openExplain, setOpenExplain] = useState(false);
  const [openReference, setOpenReference] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [expandedVisibleTests, setExpandedVisibleTests] = useState<Set<number>>(
    () => new Set(initialExpandedVisibleTests ?? [])
  );

  // In-browser question state
  const [isChecking, setIsChecking] = useState(false);
  const autoOpenSolution = isReviewSession
    ? problem.state.lastCheck?.verdict === "correct"
    : hasSubstantiveAttempt(problem.state);
  const [showSolution, setShowSolution] = useState(autoOpenSolution);
  const [revealedSolutionCode, setRevealedSolutionCode] = useState<string | undefined>(
    problem.solutionCode
  );
  const [isLoadingReference, setIsLoadingReference] = useState(false);
  const answerInputRef = useRef<HTMLInputElement | null>(null);
  const stepsRef = useRef<HTMLDivElement | null>(null);

  const {
    isChoice,
    choiceOptions,
    checkingOptionId,
    choiceLocked,
    choiceResultStatus,
    handleChoiceSelect,
    unlockChoiceRetry,
    resetChoiceState,
  } = useChoiceController({
    problem,
    isChecking,
    setIsChecking,
    onInputChange,
    onCheckAnswer,
    enabled: !isKata,
  });

  useEffect(() => {
    setUserCode(problem.state?.userCode || problem.starterCode || problem.codeSnippet || "");
    setTestReport(problem.state?.lastTestReport || null);
    setReviewRun(null);
    setCheckError(null);
    setOpenHistory(false);
    setOpenExplain(false);
    setOpenReference(false);
    setShowHint(false);
    setShowSolution(autoOpenSolution);
    setRevealedSolutionCode(problem.solutionCode);
  }, [
    problem.id,
    problem.state?.userCode,
    problem.starterCode,
    problem.codeSnippet,
    problem.state?.lastTestReport,
    problem.solutionCode,
    autoOpenSolution,
  ]);

  const effectiveState = {
    ...problem.state,
    lastTestReport: testReport ?? problem.state?.lastTestReport ?? null,
  };

  const layeredStatus = deriveCodeStatus(effectiveState, reviewRun, filename);
  const { tests, testsCount, lint, types, failures } = layeredStatus;
  const checkDiagnostic = sanitizeCodeCheckError(checkError);
  const checksPassed = tests !== "fail" && lint !== "fail" && types !== "fail" && failures.length === 0;
  const hasRunChecks = Boolean(checkDiagnostic) || tests !== "not_run" || lint !== "not_run" || types !== "not_run";
  const checkRows: { label: string; symbol: string; kind: StatusSymbolKind; detail?: string }[] = [
    {
      label: "Tests",
      symbol: layeredStatus.testsSymbol,
      kind: tests,
      detail: testsCount && tests !== "not_run" ? formatTestCounts(testsCount) : undefined,
    },
    { label: "Lint", symbol: layeredStatus.lintSymbol, kind: lint },
    { label: "Types", symbol: layeredStatus.typesSymbol, kind: types },
    {
      label: "Review",
      symbol: layeredStatus.reviewSymbol,
      kind: layeredStatus.review,
      detail: layeredStatus.reviewLabel,
    },
  ];
  const checkErrorLines = checkDiagnostic ? [checkDiagnostic] : failures;
  const checkTerminalText = [
    "$ npm run check",
    ...checkRows.map((r) =>
      `${r.symbol} ${r.label}${r.detail ? (r.label === "Tests" ? `  ${r.detail}` : ` (${r.detail})`) : ""}`
    ),
    ...(checkErrorLines.length ? ["", ...checkErrorLines] : []),
  ].join("\n");
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
          body: JSON.stringify({ drillId, problemId: problem.id, cycleStartedAt: problem.state.cycleStartedAt ?? null }),
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
            cycleStartedAt: problem.state.cycleStartedAt ?? null,
          }),
        });

        if (res.ok) {
          const report: TestRunReport = await res.json();
          setTestReport(report);
          if (onTestReportChange) {
            onTestReportChange(report);
          } else {
            onSetScore(getPrgScore(report, cycleReviews(problem.state), problem.state));
          }
          return;
        }
      }

      if (reviewRunData?.tests) {
        const t = reviewRunData.tests;
        const safeFailed = maskHiddenTestFailures(t.failed || []);
        const allPassed = t.total > 0 && t.passed === t.total && safeFailed.length === 0;
        const fallbackReport: TestRunReport = reviewRunData.testReport ?? {
          allPassed,
          score: t.total > 0 ? t.passed / t.total : 0,
          passedCount: t.passed,
          totalCount: t.total,
          visibleResults: safeFailed.map((name) => ({ name, passed: false })),
          hiddenPassed: 0,
          hiddenTotal: problem.hiddenTestCount ?? 0,
          executionTimeMs: 0,
        };
        setTestReport(fallbackReport);
        if (onTestReportChange) {
          onTestReportChange(fallbackReport);
        } else {
          onSetScore(getPrgScore(fallbackReport, cycleReviews(problem.state), problem.state));
        }
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setCheckError(sanitizeCodeCheckError(errMsg));
    } finally {
      setIsRunningChecks(false);
    }
  };

  const handleNextProblem = () => {
    if (isLastQuestion && onOpenReview) {
      onOpenReview();
    } else if (onNextQuestion) {
      onNextQuestion();
    }
  };

  const handleHintOpenChange = (nextOpen: boolean) => {
    if (nextOpen && !showHint && onHintRevealed) {
      onHintRevealed();
    }
    setShowHint(nextOpen);
  };

  const handleReferenceOpenChange = async (nextOpen: boolean) => {
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

  const answerLocked = !isKata && isLockedAfterCorrect(problem.state);

  const triggerWebCheck = async () => {
    if (answerLocked || !problem.state.userInput.trim() || isChecking) return;
    setIsChecking(true);
    try {
      await onCheckAnswer();
    } finally {
      setIsChecking(false);
    }
  };

  const score = scoreProblem(effectiveState, { isPrg: isKata }).score;
  const maxSelfScore = maxAllowedSelfScore(effectiveState, { isPrg: isKata });
  const lastCheck: CheckResult | null | undefined = problem.state.lastCheck;

  const handleTryAgain = () => {
    if (isChoice) {
      unlockChoiceRetry();
      return;
    }
    answerInputRef.current?.focus();
    answerInputRef.current?.select();
  };

  const handleShowStepsFromCard = () => {
    if (!showSolution) {
      if (onSolutionRevealed) {
        onSolutionRevealed();
      }
      setShowSolution(true);
    }
    requestAnimationFrame(() => {
      stepsRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  };

  const isFindBug =
    problem.codeType === "find-bug" || problem.answerSpec?.type === "line_number";
  const selectedLineNumber = isFindBug
    ? parseInt(problem.state.userInput.replace(/\D/g, ""), 10) || null
    : null;

  const reviews = cycleReviews(problem.state);
  const latestPassingReview = [...reviews].reverse().find((r) => r.verdict === "pass");
  const latestReview = reviews.length > 0 ? reviews[reviews.length - 1] : undefined;
  const explainSource = latestPassingReview || latestReview;
  const explainQuestion =
    explainSource?.explainQuestion?.trim() || DEFAULT_EXPLAIN_QUESTION;
  const recordedExplain = explainSource?.explain?.trim() || null;

  const hasAttempt = Boolean(
    testReport ||
      reviewRun ||
      hasSubstantiveAttempt(problem.state)
  );
  useEffect(() => {
    if (!isReviewSession) return;
    const frame = requestAnimationFrame(() => {
      if (hasAttempt) {
        document.querySelector<HTMLButtonElement>('[data-review-primary-action="true"]')?.focus();
      } else if (isChoice) {
        document.querySelector<HTMLButtonElement>('[role="radiogroup"] [role="radio"]')?.focus();
      } else {
        answerInputRef.current?.focus();
      }
    });
    return () => cancelAnimationFrame(frame);
  }, [problem.id, hasAttempt, isReviewSession, isChoice]);
  const stepsUnopenedUnattempted =
    !hasAttempt &&
    !showSolution &&
    !problem.state.solutionRevealedBeforeAnswer;

  const snippetInPrompt =
    Boolean(problem.codeSnippet) &&
    Boolean(problem.prompt) &&
    problem.prompt.includes(problem.codeSnippet!.trim().slice(0, 32));

  const displayTitle = plainTitle(drillTitle);
  const reviewTitle = plainTitle(reviewUnitTitle);

  return (
    <div className="mx-auto w-full max-w-[720px] space-y-4">
      {displayTitle && (
        <Heading>
          {isCurriculumId(displayTitle) ? (isLab ? "Lab" : "Programming drill") : displayTitle}
        </Heading>
      )}

      <article
        className={
          frameless
            ? "space-y-6"
            : "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-6"
        }
      >
        {/* 1. Brief: problem/milestone title + timer + prompt (text-base), then Visible tests */}
        <div className="space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1.5 text-xs font-normal text-zinc-500 dark:text-zinc-400">
            <h2 className="flex flex-wrap items-center gap-x-3 gap-y-1">
              {isReviewSession ? (
                <>
                  {reviewTitle && (
                    <span className={`text-foreground-control ${
                      isCurriculumId(reviewTitle) ? "font-mono" : ""
                    }`}>
                      {reviewTitle}
                    </span>
                  )}
                  {typeof problem.level === "number" && problem.level > 0 && (
                    <span
                      className="font-sans tabular-nums"
                      title={problem.levelLabel?.trim() || undefined}
                    >
                      Difficulty {problem.level}
                    </span>
                  )}
                </>
              ) : (
                <span className="font-sans tabular-nums">
                  {isLab ? `Milestone ${problem.id}` : `Problem ${index + 1}`}
                  {typeof totalQuestions === "number" && totalQuestions > 0
                    ? isLab
                      ? ` (${index + 1} of ${totalQuestions})`
                      : ` of ${totalQuestions}`
                    : ""}
                </span>
              )}
              {problem.entryPoint && (
                isLab ? (
                  <span className="text-zinc-700 dark:text-zinc-300">
                    {problem.entryPoint}
                  </span>
                ) : (
                  <code className="inline-code text-foreground-control">
                    {problem.entryPoint}
                  </code>
                )
              )}
              {!problem.entryPoint &&
                problem.context &&
                !isContextSlug(problem.context) && (
                  <span className="text-zinc-700 dark:text-zinc-300">
                    <FormattedText text={problem.context} density="compact" />
                  </span>
                )}
            </h2>
            <QuestionTimer
              questionMs={questionTimerMs ?? (problem.state?.durationMs || 0)}
              totalMs={totalTimerMs ?? (questionTimerMs ?? (problem.state?.durationMs || 0))}
              isPaused={isTimerPaused}
              onTogglePause={onToggleTimerPause}
            />
          </div>

          <div className="text-base leading-relaxed text-foreground min-w-0">
            <FormattedText text={problem.prompt} block />
          </div>
        </div>

        {problem.examples && problem.examples.length > 0 && (
          <section aria-label="Examples" className="space-y-3">
            <div className="space-y-3">
              {problem.examples.map((ex, exIdx) => (
                <div key={exIdx} className="space-y-1.5">
                  <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    Example {exIdx + 1}
                  </h4>
                  {ex.explanation && ex.explanation.trim() && (
                    <div className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
                      <FormattedText text={ex.explanation} density="compact" />
                    </div>
                  )}
                  <CodeBlock
                    variant="inline-example"
                    input={ex.input}
                    output={ex.output}
                    language="javascript"
                  />
                </div>
              ))}
            </div>
          </section>
        )}

        {problem.constraints && problem.constraints.length > 0 && (
          <section aria-label="Constraints" className="space-y-1.5">
            <h3 className="text-xs font-normal text-zinc-500 dark:text-zinc-400">
              Constraints
            </h3>
            <ul className="space-y-1 text-sm text-zinc-700 dark:text-zinc-300">
              {problem.constraints.map((constraint, cIdx) => (
                <li key={cIdx} className="flex items-start gap-2 leading-relaxed">
                  <ListDot kind="limit" />
                  <span className="leading-relaxed">
                    <FormattedText text={constraint} density="compact" />
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {isKata && openInDrillHref ? (
          <>
            {problem.codeSnippet && !snippetInPrompt && (
              <CodeBlock
                variant="full-file"
                code={problem.codeSnippet}
                language={snippetLanguage}
                filename={filename}
              />
            )}

            <Collapsible
              open={showHint}
              onOpenChange={handleHintOpenChange}
              className="space-y-3"
            >
              <div className="flex flex-wrap items-center gap-x-4 gap-y-0.5 sm:gap-y-2">
                <Link
                  href={openInDrillHref}
                  className="inline-flex items-center justify-center gap-2 min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 sm:h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-xs font-semibold transition-colors"
                >
                  <span>Open in drill</span>
                  <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
                </Link>

                {hasCheckpointHint(problem.checkpointHint) && (
                  <CollapsibleTrigger asChild>
                    <button
                      type="button"
                      className="inline-flex min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 items-center justify-center sm:justify-start gap-1 text-xs font-normal text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                    >
                      <ChevronDown
                        aria-hidden="true"
                        className={`w-3.5 h-3.5 transition-transform duration-200 motion-reduce:transition-none ${showHint ? "rotate-180" : ""}`}
                      />
                      <span>{showHint ? "Hide hint" : "Hint"}</span>
                    </button>
                  </CollapsibleTrigger>
                )}

                {onSkip && !hasAttempt && (
                  <button
                    type="button"
                    onClick={() => onSkip()}
                    className="inline-flex min-h-[44px] min-w-[44px] sm:min-h-[36px] sm:min-w-0 items-center justify-center gap-1 px-2 text-xs text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ml-auto"
                  >
                    <span>{isReviewSession ? "Skip · due tomorrow" : "Skip"}</span>
                  </button>
                )}
              </div>

              <CollapsibleContent>
                <CheckpointHintDisclosure
                  checkpointHint={problem.checkpointHint}
                  show={showHint}
                />
              </CollapsibleContent>
            </Collapsible>

            {reviewSupplement}
          </>
        ) : isKata ? (
          <>
            {problem.codeSnippet && !snippetInPrompt && (
              <CodeBlock
                variant="full-file"
                code={problem.codeSnippet}
                language={snippetLanguage}
                filename={filename}
              />
            )}

            {/* Visible tests: compact read-only list (names/descriptions + test command for labs) */}
            {((problem.visibleTests && problem.visibleTests.length > 0) ||
              (problem.visibleTestFiles && problem.visibleTestFiles.length > 0)) && (
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="text-xs font-normal text-zinc-500 dark:text-zinc-400">
                    Visible tests
                  </h3>
                  {(problem.visibleTestFiles?.length || problem.testCommand) && (
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-mono text-zinc-500 dark:text-zinc-400">
                      {[
                        ...(problem.visibleTestFiles || []),
                        ...(problem.testCommand ? [problem.testCommand] : []),
                      ].map((item, idx) => (
                        <span key={idx}>{item}</span>
                      ))}
                    </div>
                  )}
                </div>
                {problem.visibleTests && problem.visibleTests.length > 0 && (
                  <ul className="space-y-1 text-xs text-zinc-700 dark:text-zinc-300">
                    {problem.visibleTests.map((t, idx) =>
                      t.testCode ? (
                        <Collapsible
                          key={t.id || idx}
                          asChild
                          open={expandedVisibleTests.has(idx)}
                          onOpenChange={(nextOpen) => {
                            setExpandedVisibleTests((current) => {
                              const next = new Set(current);
                              if (nextOpen) next.add(idx);
                              else next.delete(idx);
                              return next;
                            });
                          }}
                        >
                          <li className="space-y-1">
                            <div className="flex items-start gap-2">
                              <ListDot className="mt-3 sm:mt-0" />
                              <CollapsibleTrigger asChild>
                                <button
                                  type="button"
                                  aria-controls={`visible-test-code-${idx}`}
                                  className="inline-flex min-h-[44px] py-3 sm:min-h-0 sm:py-0 min-w-0 items-start sm:items-center gap-1 rounded-sm text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                                >
                                  <span>
                                    <FormattedText text={t.name} density="compact" />
                                  </span>
                                  <ChevronDown
                                    aria-hidden="true"
                                    className={`mt-0.5 sm:mt-0 h-3.5 w-3.5 shrink-0 text-zinc-400 transition-transform duration-200 motion-reduce:transition-none ${expandedVisibleTests.has(idx) ? "rotate-180" : ""}`}
                                  />
                                </button>
                              </CollapsibleTrigger>
                            </div>
                            <CollapsibleContent
                              id={`visible-test-code-${idx}`}
                              className="ml-space-4"
                            >
                              <CodeBlock
                                variant="wrapped"
                                code={t.testCode}
                                language={snippetLanguage}
                              />
                            </CollapsibleContent>
                          </li>
                        </Collapsible>
                      ) : (
                        <li key={t.id || idx} className="space-y-1">
                          <div className="flex items-start gap-2">
                            <ListDot />
                            <span>
                              <FormattedText text={t.name} density="compact" />
                            </span>
                          </div>
                        </li>
                      )
                    )}
                  </ul>
                )}
              </div>
            )}

            {/* 2. Status line: Tests, Lint, Types, Review */}
            <div className="space-y-2.5">
              <div role="status" aria-label="Check and review status">
                <CodeBlock
                  variant="terminal"
                  code={checkTerminalText}
                  status={hasRunChecks ? {
                    label: checkDiagnostic ? "Could not run checks" : checksPassed ? "Checks passed" : "Checks failed",
                    passed: !checkDiagnostic && checksPassed,
                  } : undefined}
                >
                  <span className="text-muted">$ </span>npm run check
                  {checkRows.map((row) => (
                    <React.Fragment key={row.label}>
                      {"\n"}
                      <span className={statusSymbolClass(row.kind)}>{row.symbol}</span>
                      {` ${row.label}`}
                      {row.label === "Tests" && testsCount && tests !== "not_run" ? (
                        <>
                          {"  "}
                          {testsCount.total - testsCount.passed > 0 && (
                            <><span className={statusTone.wrong.text}>{`${testsCount.total - testsCount.passed} failed`}</span>{" | "}</>
                          )}
                          <span className={statusTone.correct.text}>{`${testsCount.passed} passed`}</span>
                          <span className="text-muted">{` (${testsCount.total})`}</span>
                        </>
                      ) : row.detail && <span className="text-muted">{` (${row.detail})`}</span>}
                    </React.Fragment>
                  ))}
                  {!hasRunChecks && (
                    <>{"\n\n"}<span className="text-muted">Not run yet. Run checks to see results here.</span></>
                  )}
                  {checkErrorLines.length > 0 && (
                    <>
                      {"\n"}
                      {checkErrorLines.map((line, i) => (
                        <React.Fragment key={i}>
                          {"\n"}
                          <span className={statusTone.wrong.text}>{line}</span>
                        </React.Fragment>
                      ))}
                    </>
                  )}
                </CodeBlock>
              </div>
            </div>

            {/* 3. One primary action + Secondary text buttons */}
            <Collapsible
              open={showHint}
              onOpenChange={handleHintOpenChange}
              className="space-y-2.5"
            >
              <div className="flex flex-wrap items-center gap-x-4 gap-y-0.5 sm:gap-y-2">
                {primaryAction.kind === "open_vscode" && (
                  <a
                    href={vscodeFolderUrl || "#"}
                    onClick={ensureWorkspaceOnDisk}
                    className="inline-flex items-center justify-center gap-2 min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 sm:h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-xs font-semibold transition-colors"
                  >
                    <span>Open in VS Code</span>
                  </a>
                )}

                {primaryAction.kind === "copy_review" && (
                  <CopyButton
                    text={reviewRequestText}
                    className="inline-flex items-center justify-center gap-2 min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 sm:h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-xs font-semibold transition-colors"
                    timeoutMs={1500}
                    copiedContent={
                      <>
                        <Check className="w-4 h-4" />
                        <span>Copied</span>
                      </>
                    }
                  >
                    <>
                      <Copy className="w-4 h-4" />
                      <span>Copy review request</span>
                    </>
                  </CopyButton>
                )}

                {primaryAction.kind === "next_problem" && (
                  <button
                    type="button"
                    onClick={handleNextProblem}
                    className="inline-flex items-center justify-center gap-2 min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 sm:h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-xs font-semibold transition-colors"
                  >
                    <span>{isLab ? "Next milestone" : "Next problem"}</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                )}

                {/* Secondary text buttons */}
                <button
                  type="button"
                  onClick={handleRunChecks}
                  disabled={isRunningChecks}
                  className="inline-flex items-center justify-center sm:justify-start gap-1.5 min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 text-xs font-normal text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 disabled:opacity-50 transition-colors"
                >
                  {isRunningChecks ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                      <span>Running checks…</span>
                    </>
                  ) : (
                    <span>Run checks</span>
                  )}
                </button>

                {primaryAction.kind !== "open_vscode" && vscodeFolderUrl && (
                  <a
                    href={vscodeFolderUrl}
                    onClick={ensureWorkspaceOnDisk}
                    className="inline-flex items-center justify-center sm:justify-start gap-1 min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 text-xs font-normal text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
                  >
                    <span>Open in VS Code</span>
                  </a>
                )}

                {vscodeUrl && problem.mainFile && (
                  <a
                    href={vscodeUrl}
                    className="inline-flex items-center justify-center sm:justify-start gap-1 min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
                  >
                    <span>Open <code className="inline-code">{problem.mainFile}</code></span>
                  </a>
                )}

                {hasCheckpointHint(problem.checkpointHint) && (
                  <CollapsibleTrigger asChild>
                    <button
                      type="button"
                      className="inline-flex min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 items-center justify-center sm:justify-start gap-1 text-xs font-normal text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                    >
                      <ChevronDown
                        aria-hidden="true"
                        className={`w-3.5 h-3.5 transition-transform duration-200 motion-reduce:transition-none ${showHint ? "rotate-180" : ""}`}
                      />
                      <span>{showHint ? "Hide hint" : "Hint"}</span>
                    </button>
                  </CollapsibleTrigger>
                )}
              </div>

              {primaryAction.kind === "copy_review" && drillId && (
                <div className="text-xs font-sans text-zinc-500 dark:text-zinc-400">
                  {reviewRequestText}
                </div>
              )}

              <CollapsibleContent>
                <CheckpointHintDisclosure
                  checkpointHint={problem.checkpointHint}
                  show={showHint}
                />
              </CollapsibleContent>
            </Collapsible>

            {/* 5. Collapsible sections (closed by default): Review history, Explain, Reference */}
            <div className="divide-y divide-zinc-200 dark:divide-zinc-800 border-t border-zinc-200 dark:border-zinc-800">
              {/* Review history */}
              <Collapsible
                open={openHistory}
                onOpenChange={setOpenHistory}
                className="py-2.5"
              >
                <CollapsibleTrigger asChild>
                  <button
                    type="button"
                    className="w-full min-h-[44px] sm:min-h-0 flex items-center justify-between text-left text-xs font-normal text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 py-1 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                  >
                    <span>
                      Review history
                      {reviews.length > 0 ? ` (${reviews.length})` : ""}
                    </span>
                    <ChevronDown
                      aria-hidden="true"
                      className={`w-4 h-4 text-zinc-400 transition-transform duration-200 motion-reduce:transition-none ${openHistory ? "rotate-180" : ""}`}
                    />
                  </button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <Reveal show={Boolean(openHistory)}>
                    {openHistory && (
                      <div className="pt-2 pb-1 space-y-3 text-xs text-zinc-600 dark:text-zinc-400">
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
                                  ? statusTone.correct.border
                                  : statusTone.wrong.border
                              }`}
                            >
                              <div className="flex flex-wrap items-center gap-2 text-xs font-sans">
                                <span className="font-sans tabular-nums font-semibold text-zinc-900 dark:text-zinc-100">
                                  #{r.attempt ?? rIdx + 1} {r.verdict}
                                </span>
                                {r.at && (
                                  <span className="text-zinc-500 dark:text-zinc-400">
                                    {formatReviewDate(r.at)}
                                  </span>
                                )}
                                {r.tests && (
                                  <span className="text-zinc-500 dark:text-zinc-400">
                                    tests{" "}
                                    <span className="font-sans tabular-nums">
                                      {r.tests.passed}/{r.tests.total}
                                    </span>
                                  </span>
                                )}
                              </div>
                              {r.findings && r.findings.length > 0 ? (
                                <ul className="space-y-1 text-xs text-zinc-700 dark:text-zinc-300 font-sans">
                                  {r.findings.map((f, fIdx) => (
                                    <li key={fIdx} className="flex items-start gap-2">
                                      <ListDot kind="info" />
                                      <span className="min-w-0 break-words">
                                        <code className="inline-code">{f.check}</code> ({f.severity}
                                        {f.line ? `, line ${f.line}` : ""}
                                        {f.disputed ? ", disputed" : ""}): {f.note}
                                      </span>
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
                </CollapsibleContent>
              </Collapsible>

              {/* Explain */}
              <Collapsible
                open={openExplain}
                onOpenChange={setOpenExplain}
                className="py-2.5"
              >
                <CollapsibleTrigger asChild>
                  <button
                    type="button"
                    className="w-full min-h-[44px] sm:min-h-0 flex items-center justify-between text-left text-xs font-normal text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 py-1 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                  >
                    <span>Explain</span>
                    <ChevronDown
                      aria-hidden="true"
                      className={`w-4 h-4 text-zinc-400 transition-transform duration-200 motion-reduce:transition-none ${openExplain ? "rotate-180" : ""}`}
                    />
                  </button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <Reveal show={Boolean(openExplain)}>
                    {openExplain && (
                      <div className="pt-2 pb-1 space-y-2 text-xs">
                        <div className="text-zinc-700 dark:text-zinc-300">
                          <FormattedText text={explainQuestion} density="compact" />
                        </div>
                        {recordedExplain ? (
                          <div className={`border-l-2 ${statusTone.correct.border} pl-3 py-0.5 text-zinc-800 dark:text-zinc-200`}>
                            <FormattedText text={recordedExplain} density="compact" />
                          </div>
                        ) : (
                          <p className="text-xs text-zinc-500 dark:text-zinc-400">
                            Ask Claude to review your code, e.g.{" "}
                            <code className="inline-code">
                              {drillId ? reviewRequestText : `ตรวจโค้ด <ID> ${problem.id}`}
                            </code>
                          </p>
                        )}
                      </div>
                    )}
                  </Reveal>
                </CollapsibleContent>
              </Collapsible>

              {/* Reference (drills) or Lab README (labs; _reference is never served) */}
              {isLab ? (
                labReadme ? (
                  <Collapsible
                    open={openReference}
                    onOpenChange={setOpenReference}
                    className="py-2.5"
                  >
                    <CollapsibleTrigger asChild>
                      <button
                        type="button"
                        className="w-full min-h-[44px] sm:min-h-0 flex items-center justify-between text-left text-xs font-normal text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 py-1 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                      >
                        <span>Lab README</span>
                        <ChevronDown
                          aria-hidden="true"
                          className={`w-4 h-4 text-zinc-400 transition-transform duration-200 motion-reduce:transition-none ${openReference ? "rotate-180" : ""}`}
                        />
                      </button>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <Reveal show={Boolean(openReference)}>
                        {openReference && (
                          <div className="pt-2 pb-1 text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">
                            <FormattedText text={labReadme} />
                          </div>
                        )}
                      </Reveal>
                    </CollapsibleContent>
                  </Collapsible>
                ) : null
              ) : (
                <Collapsible
                  open={openReference}
                  onOpenChange={(nextOpen) => void handleReferenceOpenChange(nextOpen)}
                  className="py-2.5"
                >
                  <CollapsibleTrigger asChild>
                    <button
                      type="button"
                      className="w-full min-h-[44px] sm:min-h-0 flex items-center justify-between text-left text-xs font-normal text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 py-1 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                    >
                      <span>Reference</span>
                      <span className="inline-flex items-center gap-2">
                        {!referenceAllowed && (
                          <span className="text-xs font-normal text-zinc-500 dark:text-zinc-400">
                            Unlocks after review passes
                          </span>
                        )}
                        <ChevronDown
                          aria-hidden="true"
                          className={`w-4 h-4 text-zinc-400 transition-transform duration-200 motion-reduce:transition-none ${openReference ? "rotate-180" : ""}`}
                        />
                      </span>
                    </button>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <Reveal show={Boolean(openReference)}>
                      {openReference && (
                        <div className="pt-2 pb-1">
                          {!referenceAllowed ? (
                            <p className="text-xs text-zinc-500 dark:text-zinc-400">
                              Unlocks after review passes
                            </p>
                          ) : isLoadingReference ? (
                            <p className="text-xs text-zinc-500 dark:text-zinc-400">
                              Loading reference…
                            </p>
                          ) : problem.solutionCode || revealedSolutionCode ? (
                            <CodeBlock
                              variant="full-file"
                              code={(problem.solutionCode || revealedSolutionCode)!}
                              language={snippetLanguage}
                              filename={`reference-${filename}`}
                            />
                          ) : (
                            <p className="text-xs text-zinc-500 dark:text-zinc-400">
                              Reference solution unavailable.
                            </p>
                          )}
                        </div>
                      )}
                    </Reveal>
                  </CollapsibleContent>
                </Collapsible>
              )}
            </div>
          </>
        ) : (
          /* =================================================================== */
          /* In-browser PRG problem types (predict_output / choice / line_number)*/
          /* =================================================================== */
          <>
            {problem.codeSnippet && (
              <CodeBlock
                variant="full-file"
                code={problem.codeSnippet}
                language={snippetLanguage}
                filename={`challenge-${problem.id.toLowerCase()}.${getExtensionForLanguage(
                  snippetLanguage
                )}`}
                selectableLines={isFindBug && !answerLocked}
                selectedLine={selectedLineNumber}
                onSelectLine={(lineNum) => {
                  if (!answerLocked) onInputChange(String(lineNum));
                }}
              />
            )}

            {isChoice && choiceOptions && (
              <ChoiceOptionGroup
                options={choiceOptions}
                selectedValue={problem.state.userInput}
                onSelect={(optId) => void handleChoiceSelect(optId)}
                disabled={choiceLocked}
                checkingOptionId={checkingOptionId}
                resultStatus={choiceResultStatus}
                layout="stack"
              />
            )}

            <div className="space-y-3">
              {!isChoice &&
                (isFindBug ? (
                  <div className="flex items-center">
                    <InlineCheckButton
                      onClick={triggerWebCheck}
                      disabled={answerLocked || isChecking || !problem.state.userInput.trim()}
                      isChecking={isChecking}
                      embedded={false}
                    />
                  </div>
                ) : (
                  <PlainAnswerField
                    code
                    inputRef={answerInputRef}
                    value={problem.state.userInput}
                    onChange={onInputChange}
                    onCheck={() => void triggerWebCheck()}
                    placeholder={getSafePlaceholder(problem.inputHint, problem)}
                    aria-label={isReviewSession
                      ? `Answer for ${isLab ? "milestone" : "problem"} ${index + 1} of ${totalQuestions ?? 1}`
                      : `Answer for ${isLab ? "milestone" : "problem"} ${problem.id}`}
                    isChecking={isChecking}
                    locked={answerLocked}
                  />
                ))}

              <AnswerResultCard
                lastCheck={lastCheck}
                state={problem.state}
                problem={problem}
                mistakeTags={mistakeTags}
                isReviewSession={isReviewSession}
                isCorrectOnRetry={isCorrectOnRetry}
                isLastQuestion={isReviewSession ? false : isLastQuestion}
                nextLabel={nextCardLabel ?? (isLab ? "Next milestone" : "Next problem")}
                scheduleNote={isReviewSession ? reviewScheduleNote : null}
                onNextQuestion={onNextQuestion}
                onOpenReview={onOpenReview}
                onTryAgain={handleTryAgain}
                onShowSteps={handleShowStepsFromCard}
              />
            </div>

            {reviewSupplement}

            <ProblemAssistSection
              problem={problem}
              hasAttempt={hasAttempt}
              showHint={showHint}
              onToggleHint={() => {
                if (!showHint && onHintRevealed) {
                  onHintRevealed();
                }
                setShowHint(!showHint);
              }}
              showSolution={showSolution}
              onToggleSolution={() => {
                if (!showSolution && onSolutionRevealed) {
                  onSolutionRevealed();
                }
                setShowSolution(!showSolution);
              }}
              stepsUnopenedUnattempted={stepsUnopenedUnattempted}
              hideShowStepsButton={!hasAttempt}
              stepsRef={stepsRef}
              showStepsHeader={false}
              onMarkDivergedStep={onMarkDivergedStep}
              onReset={() => {
                resetChoiceState();
                onResetProblem();
              }}
              onSkip={
                onSkip
                  ? () => {
                      const countHint = Boolean(!isReviewSession && !showHint && onHintRevealed);
                      if (!isReviewSession) {
                        setShowHint(true);
                        setShowSolution(true);
                      }
                      onSkip({ countHint });
                    }
                  : undefined
              }
              skipLabel={isReviewSession ? "Skip · due tomorrow" : "Skip"}
            />
          </>
        )}

        {/* Mistake tags & note after an attempt */}
        <ProblemSelfEval
          hasAttempt={hasAttempt}
          showSelfScore={!isKata && !(isReviewSession && problem.state.skipped)}
          maxScore={maxSelfScore}
          skipped={Boolean(problem.state.skipped)}
          score={score}
          mistakes={problem.state.mistakes}
          mistakeNote={problem.state.mistakeNote}
          mistakeTags={mistakeTags}
          noteAriaLabel={`Note for ${isLab ? "milestone" : "problem"} ${problem.id}`}
          onSetScore={onSetScore}
          onToggleMistakeTag={onToggleMistakeTag}
          onMistakeNoteChange={onMistakeNoteChange}
        />
      </article>

      {/* Quiet question navigation footer */}
      <ProblemNavFooter
        index={index}
        isLastQuestion={isLastQuestion}
        onPrevQuestion={onPrevQuestion}
        onNextQuestion={onNextQuestion}
        onOpenReview={onOpenReview}
        lastQuestionLabel={lastQuestionNavLabel}
        nextDisabled={isReviewSession && !(isKata && Boolean(openInDrillHref)) && !hasAttempt}
        hideNext={isReviewSession && hasAttempt}
      />
    </div>
  );
};
